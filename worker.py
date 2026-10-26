"""One persistent CUDA model per process. The UI can terminate this process to stop."""
import os,sys,json,time,contextlib,traceback,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if len(sys.argv)>3:
    def watch_parent():
        import psutil
        parent=int(sys.argv[3])
        while psutil.pid_exists(parent):time.sleep(2)
        os._exit(0)
    threading.Thread(target=watch_parent,daemon=True).start()
os.environ.update(HF_HOME=str(ROOT/'cache'/'huggingface'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
protocol=sys.stdout
with contextlib.redirect_stdout(sys.stderr):
    import torch,numpy as np,soundfile as sf
    config=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
    torch.set_num_threads(int(config.get('inference_cpu_threads',4)))
    torch.set_num_interop_threads(1)
    from qwen_tts import Qwen3TTSModel
    from safe_reader import enable_windows_safe_reader
    enable_windows_safe_reader()
    kind=sys.argv[1]
    name={'design':'Qwen3-TTS-12Hz-1.7B-VoiceDesign','clone':'Qwen3-TTS-12Hz-0.6B-Base'}[kind]
    if not torch.cuda.is_available(): raise RuntimeError('CUDA 不可用，已停止；不会转到 CPU 推理。')
    dtype=torch.bfloat16 if kind=='clone' and torch.cuda.is_bf16_supported() else torch.float16
    model=Qwen3TTSModel.from_pretrained(str(ROOT/'models'/name),device_map='cuda:0',dtype=dtype,attn_implementation='sdpa',local_files_only=True)
    if next(model.model.parameters()).device.type!='cuda': raise RuntimeError('模型未加载到 GPU')
    jobs=Path(sys.argv[2]); jobs.mkdir(parents=True,exist_ok=True)
    print('MODEL READY',name,os.getpid(),'dtype',dtype,'attention',model.model.talker.config._attn_implementation,flush=True)
    while True:
        requests=sorted(jobs.glob('*.request.json'))
        if not requests:
            time.sleep(.15); continue
        request_path=requests[0]
        try:
            req=json.loads(request_path.read_text(encoding='utf-8')); torch.manual_seed(req['seed'])
            torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize()
            started=time.perf_counter(); params=req['parameters']
            if kind=='design':
                wavs,sr=model.generate_voice_design(text=req['text'],language=req['language'],instruct=req['description'],**params)
            else:
                wavs,sr=model.generate_voice_clone(text=req['text'],language=req['language'],ref_audio=req['reference_audio'],ref_text=req['reference_text'],x_vector_only_mode=False,**params)
            torch.cuda.synchronize(); elapsed=time.perf_counter()-started
            x=np.asarray(wavs[0]); path=Path(req['path'])
            if not np.isfinite(x).all() or len(x)<sr*.25 or np.max(np.abs(x))<.001: raise RuntimeError('生成音频为空或异常，请重试。')
            if len(x)/sr*12 >= params['max_new_tokens']-3: raise RuntimeError('已达到生成长度上限，结果可能截断。请将本段拆短后重试。')
            path.parent.mkdir(parents=True,exist_ok=True)
            tmp=path.with_suffix('.tmp.wav'); sf.write(tmp,x,sr,subtype='PCM_16'); tmp.replace(path)
            meta={**req,'model':'Qwen/'+name,'created':time.strftime('%Y-%m-%d %H:%M:%S'),'sample_rate':sr,'duration_seconds':len(x)/sr,'inference_seconds':elapsed,'peak_allocated_mib':torch.cuda.max_memory_allocated()/1024**2,'peak_reserved_mib':torch.cuda.max_memory_reserved()/1024**2,'device':str(next(model.model.parameters()).device),'dtype':str(dtype).replace('torch.',''),'attention':'sdpa'}
            path.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
            response={'ok':True,'metadata':meta}
        except Exception as exc:
            traceback.print_exc(); response={'ok':False,'error':str(exc)}
        result_path=request_path.with_name(request_path.name.replace('.request.json','.result.json'))
        tmp=result_path.with_suffix('.tmp');tmp.write_text(json.dumps(response,ensure_ascii=False),encoding='utf-8');tmp.replace(result_path)
        request_path.unlink(missing_ok=True)
