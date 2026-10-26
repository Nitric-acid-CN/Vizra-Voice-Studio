"""Isolated official Chatterbox/Kokoro inference. Local weights, serial jobs."""
import os,sys,json,time,threading,traceback,random
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.update(HF_HOME=str(ROOT/'cache'/'huggingface'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
import psutil
def parent_watch():
    while psutil.pid_exists(int(sys.argv[3])):time.sleep(2)
    os._exit(0)
threading.Thread(target=parent_watch,daemon=True).start()
import torch,numpy as np,soundfile as sf
torch.set_num_threads(4)
if not torch.cuda.is_available():raise RuntimeError('CUDA 不可用，已停止。')
kind=sys.argv[1];jobs=Path(sys.argv[2]);jobs.mkdir(parents=True,exist_ok=True)
if kind=='chatter':
    from chatterbox.tts_turbo import ChatterboxTurboTTS
    model=ChatterboxTurboTTS.from_local(ROOT/'models'/'chatterbox-turbo',device='cuda')
    if next(model.t3.parameters()).device.type!='cuda':raise RuntimeError('Chatterbox 未在 GPU 上加载。')
    rate=model.sr
elif kind=='kokoro':
    import spacy
    if not spacy.util.is_package('en_core_web_sm'):raise RuntimeError('缺少离线英文语言资源，请重新运行英文安装。')
    from kokoro import KModel,KPipeline
    folder=ROOT/'models'/'Kokoro-82M'
    model=KModel(config=str(folder/'config.json'),model=str(folder/'kokoro-v1_0.pth')).to('cuda').eval()
    pipelines={code:KPipeline(lang_code=code,model=model) for code in ('a','b')}
    rate=24000
else:raise RuntimeError('未知英文引擎。')
print('MODEL READY',kind,'cuda',flush=True)
while True:
    requests=sorted(jobs.glob('*.request.json'))
    if not requests:time.sleep(.15);continue
    request=requests[0]
    try:
        req=json.loads(request.read_text(encoding='utf-8'))
        if req['language']!='English':raise ValueError('该引擎只支持英文。')
        random.seed(req['seed']);np.random.seed(req['seed']);torch.manual_seed(req['seed'])
        torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.perf_counter()
        with torch.inference_mode():
            if kind=='chatter':
                params=dict(temperature=float(req['parameters']['temperature']),top_p=.95,top_k=1000,repetition_penalty=1.2)
                wav=model.generate(req['text'],audio_prompt_path=req['reference_audio'],**params).squeeze().cpu().numpy()
            else:
                voice=req['preset_voice'];params=dict(voice=voice,speed=1.0)
                voice_path=str(folder/'voices'/(voice+'.pt'))
                pieces=[item.audio.cpu().numpy() for item in pipelines[voice[0]](req['text'],voice=voice_path,speed=1.0)]
                wav=np.concatenate(pieces)
        torch.cuda.synchronize();elapsed=time.perf_counter()-start
        if not np.isfinite(wav).all() or len(wav)<rate*.25 or np.max(np.abs(wav))<.001:raise RuntimeError('音频为空或异常。')
        path=Path(req['path']);path.parent.mkdir(parents=True,exist_ok=True)
        tmp=path.with_suffix('.tmp.wav');sf.write(tmp,wav,rate,subtype='PCM_16');tmp.replace(path)
        metadata={**req,'model':'ResembleAI/chatterbox-turbo' if kind=='chatter' else 'hexgrad/Kokoro-82M','created':time.strftime('%Y-%m-%d %H:%M:%S'),'parameters':params,'sample_rate':rate,'duration_seconds':len(wav)/rate,'inference_seconds':elapsed,'peak_allocated_mib':torch.cuda.max_memory_allocated()/1024**2,'peak_reserved_mib':torch.cuda.max_memory_reserved()/1024**2,'device':'cuda:0','dtype':'float32','watermark':'official Perth watermark' if kind=='chatter' else None}
        path.with_suffix('.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8');result={'ok':True,'metadata':metadata}
    except Exception as error:
        traceback.print_exc();result={'ok':False,'error':str(error)}
    dest=request.with_name(request.name.replace('.request.json','.result.json'));tmp=dest.with_suffix('.tmp')
    tmp.write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8');tmp.replace(dest);request.unlink(missing_ok=True)
