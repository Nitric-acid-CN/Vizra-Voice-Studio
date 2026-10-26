"""Official CosyVoice3 adapter. Uses its own venv, one persistent GPU process."""
import os,sys,json,time,threading,traceback,hashlib,random,io
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.update(HF_HOME=str(ROOT/'cache'/'huggingface'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
sys.path[:0]=[str(ROOT/'engines'/'CosyVoice-main'),str(ROOT/'engines'/'Matcha-TTS-dd9105b34bf2be2230f4aa1e4769fb586a3c824e')]
if len(sys.argv)>3:
    def watch_parent():
        import psutil
        while psutil.pid_exists(int(sys.argv[3])):time.sleep(2)
        os._exit(0)
    threading.Thread(target=watch_parent,daemon=True).start()
import torch,numpy as np,soundfile as sf
from accelerate import init_empty_weights
torch.set_num_threads(4)
if not torch.cuda.is_available():raise RuntimeError('CosyVoice 需要可用的 CUDA。')
from safe_reader import enable_windows_safe_reader
enable_windows_safe_reader()
import cosyvoice.cli.cosyvoice as official_cosy
import yaml
from transformers import Qwen2Config,Qwen2ForCausalLM
from cosyvoice.llm.llm import Qwen2Encoder
from cosyvoice.cli.model import CosyVoice3Model
# llm.pt contains the complete backbone. Avoid materializing the redundant
# pretrained backbone checkpoint before immediately overwriting all its weights.
def init_backbone(self,pretrain_path):
    torch.nn.Module.__init__(self)
    config=Qwen2Config.from_pretrained(pretrain_path,local_files_only=True)
    previous=torch.get_default_dtype()
    try:
        torch.set_default_dtype(torch.float16)
        self.model=Qwen2ForCausalLM(config)
    finally:torch.set_default_dtype(previous)
Qwen2Encoder.__init__=init_backbone
def memory_bounded_load(self,llm_model,flow_model,hift_model):
    state=torch.load(llm_model,map_location='cpu',weights_only=True,mmap=True)
    self.llm.load_state_dict(state,strict=True,assign=True);del state
    self.llm.to(device=self.device,dtype=torch.float16).eval()
    state=torch.load(flow_model,map_location='cpu',weights_only=True,mmap=True)
    self.flow.load_state_dict(state,strict=True,assign=True);del state
    self.flow.to(self.device).eval()
    state={k.replace('generator.',''):v for k,v in torch.load(hift_model,map_location='cpu',weights_only=True,mmap=True).items()}
    self.hift.load_state_dict(state,strict=True,assign=True);del state
    self.hift.to(self.device).eval()
CosyVoice3Model.load=memory_bounded_load
# Instantiate only inference nodes from the official configuration. Training
# discriminators and dataset processors are not needed for local synthesis.
original_yaml_loader=official_cosy.load_hyperpyyaml
INFERENCE_KEYS={'sample_rate','llm_input_size','llm_output_size','spk_embed_dim','qwen_pretrain_path','token_frame_rate','token_mel_ratio','chunk_size','num_decoding_left_chunks','llm','flow','hift','get_tokenizer','allowed_special','feat_extractor'}
def inference_yaml(stream,*args,**kwargs):
    node=yaml.compose(stream.read())
    node.value=[(key,value) for key,value in node.value if key.value in INFERENCE_KEYS or key.value.startswith('__set_seed')]
    with init_empty_weights(include_buffers=False):
        return original_yaml_loader(io.StringIO(yaml.serialize(node)),*args,**kwargs)
official_cosy.load_hyperpyyaml=inference_yaml
AutoModel=official_cosy.AutoModel
model=AutoModel(model_dir=str(ROOT/'models'/'Fun-CosyVoice3-0.5B-2512'),load_trt=False,load_vllm=False,fp16=True)
model.model.llm.half()
torch.cuda.empty_cache()
if next(model.model.llm.parameters()).device.type!='cuda':raise RuntimeError('CosyVoice 未加载到 GPU。')
jobs=Path(sys.argv[2]);jobs.mkdir(parents=True,exist_ok=True)
print('MODEL READY CosyVoice3 CUDA FP16',flush=True)
cached_reference=None
while True:
    files=sorted(jobs.glob('*.request.json'))
    if not files:time.sleep(.15);continue
    request=files[0]
    try:
        req=json.loads(request.read_text(encoding='utf-8'));seed=req['seed']
        random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
        torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.perf_counter()
        prompt='You are a helpful assistant.<|endofprompt|>'+req['reference_text']
        reference=(req['reference_audio'],req['reference_text'])
        if reference!=cached_reference:
            model.frontend.spk2info.clear()
            model.add_zero_shot_spk(prompt,req['reference_audio'],'studio_reference')
            cached_reference=reference
        pieces=[]
        with torch.inference_mode():
            for item in model.inference_zero_shot(req['text'],'','',zero_shot_spk_id='studio_reference',stream=False,speed=1.0,text_frontend=False):
                pieces.append(item['tts_speech'].detach().float().cpu().numpy().reshape(-1))
        torch.cuda.synchronize();elapsed=time.perf_counter()-start
        if not pieces:raise RuntimeError('CosyVoice 没有返回音频。')
        x=np.concatenate(pieces);sr=model.sample_rate
        if not np.isfinite(x).all() or len(x)<sr*.25 or np.max(np.abs(x))<.001:raise RuntimeError('CosyVoice 返回的音频异常。')
        path=Path(req['path']);path.parent.mkdir(parents=True,exist_ok=True)
        temporary=path.with_suffix('.tmp.wav');sf.write(temporary,x,sr,subtype='PCM_16');temporary.replace(path)
        metadata={**req,'model':'FunAudioLLM/Fun-CosyVoice3-0.5B-2512','created':time.strftime('%Y-%m-%d %H:%M:%S'),'sample_rate':sr,'duration_seconds':len(x)/sr,'inference_seconds':elapsed,'peak_allocated_mib':torch.cuda.max_memory_allocated()/2**20,'peak_reserved_mib':torch.cuda.max_memory_reserved()/2**20,'device':'cuda:0','dtype':'LLM float16; flow/HiFT float32 with official float16 autocast','parameters':{'stream':False,'speed':1.0,'text_frontend':False},'reference_preprocessing':'official ONNX CPU; LLM/flow/vocoder CUDA'}
        path.with_suffix('.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
        result={'ok':True,'metadata':metadata}
    except Exception as exc:
        traceback.print_exc();result={'ok':False,'error':str(exc)}
    dest=request.with_name(request.name.replace('.request.json','.result.json'));tmp=dest.with_suffix('.tmp')
    tmp.write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8');tmp.replace(dest);request.unlink(missing_ok=True)
