import os,sys,json,time,re,shutil,secrets,threading,subprocess,atexit,glob
from model_catalog import get_model,validate_selection,PRESET_VOICES
from pathlib import Path
ROOT=Path(os.environ.get('VIZRA_WORKBENCH_ROOT',Path(__file__).resolve().parent))
_local_bypass=','.join(filter(None,[os.environ.get('NO_PROXY',os.environ.get('no_proxy','')),'127.0.0.1','localhost','::1']))
os.environ.update(NO_PROXY=_local_bypass,no_proxy=_local_bypass)
os.environ.update(GRADIO_ANALYTICS_ENABLED='False',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',HF_HOME=str(ROOT/'cache'/'huggingface'),GRADIO_TEMP_DIR=str(ROOT/'cache'/'gradio'))
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
import gradio as gr
OUT=ROOT/'outputs'
for folder in ['candidates','favorites','segments','final']: (OUT/folder).mkdir(parents=True,exist_ok=True)
(ROOT/'logs').mkdir(exist_ok=True)
CONFIG=json.loads((ROOT/'config.json').read_text(encoding='utf-8')) if (ROOT/'config.json').exists() else {}
TEXT=CONFIG.get('test_text',''); DESCRIPTION=CONFIG.get('voice_description','')
FILE_LOCK=threading.RLock()

def slug(value):
    value=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',str(value)).strip(' .')[:65]
    return value or 'untitled'

def save_json(path,data):
    path=Path(path); tmp=path.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8'); tmp.replace(path)

def version_path(folder,prefix):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    segment_id=re.match(r'^(segment_\d{3})_',prefix)
    pattern=segment_id.group(1)+'*_v*.wav' if segment_id else glob.escape(prefix)+'_v*.wav'
    versions=[int(m.group(1)) for p in folder.glob(pattern) if (m:=re.search(r'_v(\d+)\.wav$',p.name))]
    return folder/f'{prefix}_v{max(versions,default=0)+1:03d}.wav'

def inside(path,folder):
    p=Path(path).resolve()
    if not p.is_relative_to(Path(folder).resolve()) or not p.is_file(): raise gr.Error('无效的本地文件。')
    return p

class Engine:
    def __init__(self):
        self.process=None; self.kind=None; self.lock=threading.Lock(); self.guard=threading.RLock(); self.epoch=0; self.log=None;self.jobs=None
    def terminate_process(self):
        if self.process and self.process.poll() is None:
            subprocess.run(['taskkill','/PID',str(self.process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW,timeout=15)
            self.process.wait(timeout=10)
    def stop(self):
        with self.guard:
            self.epoch+=1
            self.terminate_process()
            self.process=None; self.kind=None
            if self.log: self.log.close(); self.log=None
        return '已停止推理并释放模型。已完成的音频会保留，下次生成时重新加载。'
    def generate(self,kind,text,description,language,temperature,folder,prefix,epoch,reference=None):
        if not text.strip(): raise gr.Error('请输入配音文本。')
        if len(text)>200: raise gr.Error('单段最多 200 字符，建议 40～120 字；请拆分长段落。')
        if kind=='design' and not description.strip(): raise gr.Error('请输入音色描述。')
        try:spec=validate_selection(kind,language,reference,description)
        except ValueError as error:raise gr.Error(str(error))
        if not (ROOT/spec.environment/'Scripts'/'python.exe').is_file():raise gr.Error('模型运行环境未安装，请运行 setup.ps1。')
        if not (ROOT/'models'/spec.model_folder).is_dir():raise gr.Error('模型文件未安装，请运行 setup.ps1。')
        with self.lock:
            with self.guard:
                if epoch!=self.epoch: raise gr.Error('生成已停止。')
                if not self.process or self.process.poll() is not None or self.kind!=kind:
                    self.terminate_process()
                    if self.log: self.log.close()
                    self.log=(ROOT/'logs'/'inference.log').open('a',encoding='utf-8')
                    self.jobs=ROOT/'cache'/'jobs'/secrets.token_hex(8);self.jobs.mkdir(parents=True)
                    self.process=subprocess.Popen([str(ROOT/get_model(kind).environment/'Scripts'/'python.exe'),'-u',str(ROOT/get_model(kind).worker),kind,str(self.jobs),str(os.getpid())],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=self.log,stderr=self.log,env={**os.environ,'PYTHONUTF8':'1','PYTHONFAULTHANDLER':'1'},creationflags=subprocess.CREATE_NO_WINDOW)
                    self.kind=kind
                proc=self.process
            with FILE_LOCK: path=version_path(folder,prefix)
            req=dict(text=text.strip(),description=description,language=language,parameters=dict(do_sample=True,temperature=float(temperature),top_p=1.0,top_k=50,repetition_penalty=1.05,max_new_tokens=768),seed=secrets.randbelow(2**31),path=str(path))
            if spec.voice_mode=='reference':
                if not reference: raise gr.Error('请选择收藏音色。')
                ref=inside(reference,OUT/'favorites'); meta=json.loads(ref.with_suffix('.json').read_text(encoding='utf-8'))
                req.update(reference_audio=str(ref),reference_text=meta['text'])
            elif spec.voice_mode=='preset':req['preset_voice']=reference
            request_id=secrets.token_hex(8);request=self.jobs/(request_id+'.request.json');result_path=self.jobs/(request_id+'.result.json')
            save_json(request,req); deadline=time.monotonic()+600
            while not result_path.exists():
                if epoch!=self.epoch:raise gr.Error('生成已停止。')
                if proc.poll() is not None:raise gr.Error(f'推理进程退出（{proc.returncode}），请查看 logs/inference.log。')
                if time.monotonic()>deadline:self.stop();raise gr.Error('推理超过 10 分钟，已停止；请拆短文本或查看日志。')
                time.sleep(.2)
            result=json.loads(result_path.read_text(encoding='utf-8')); result_path.unlink(missing_ok=True)
            if not result['ok']:
                self.stop()
                raise gr.Error(result['error'])
            return str(path),result['metadata']

ENGINE=Engine(); atexit.register(ENGINE.stop)

def summary(meta): return f"{meta['duration_seconds']:.2f} 秒音频 · 生成 {meta['inference_seconds']:.1f} 秒 · 峰值分配显存 {meta['peak_allocated_mib']/1024:.2f} GiB · {meta['model']}"


def save_favorite(paths,index,name):
    if not paths or not 1<=int(index)<=len(paths): raise gr.Error('请先生成并选择一个已有候选。')
    src=inside(paths[int(index)-1],OUT/'candidates')
    if not name.strip(): raise gr.Error('请给音色命名。')
    with FILE_LOCK:
        dest=version_path(OUT/'favorites','voice_'+slug(name))
        shutil.copy2(src,dest); meta=json.loads(src.with_suffix('.json').read_text(encoding='utf-8'))
        meta.update(favorite_name=name.strip(),source_audio=str(src),reference_audio=str(dest),saved_at=time.strftime('%Y-%m-%d %H:%M:%S'))
        save_json(dest.with_suffix('.json'),meta)
    update=gr.update(choices=favorite_choices(),value=str(dest))
    return '已保存参考音频和完整参数；使用 Base 模式复用音色，描述或种子本身不锁定音色。',update,gr.update(choices=favorite_choices(),value=str(dest))


def project_choices(): return [(p.parent.name,str(p)) for p in sorted((OUT/'segments').glob('*/project.json'))]
def read_project(path):
    p=inside(path,OUT/'segments'); return p,json.loads(p.read_text(encoding='utf-8'))
def segment_choices(data): return [(f"{i+1:03d} · {s['text'][:38]}",i+1) for i,s in enumerate(data['segments'])]


def load_segment(path,index):
    if not path or index is None:return '',gr.update(choices=[],value=None),None
    _,data=read_project(path); s=data['segments'][int(index)-1]
    versions=[(Path(v).name,v) for v in s['versions']]
    return s['text'],gr.update(choices=versions,value=s['selected']),s['selected']


def select_version(project,index,version):
    if not project or index is None or not version:return None,'请选择已有版本。'
    p,data=read_project(project);s=data['segments'][int(index)-1]
    if version not in s['versions']:raise gr.Error('版本不属于当前段落。')
    s['selected']=version;save_json(p,data)
    return version,'已选定此版本；合并时使用各段选定版本。'

def export48(path):
    if not path:raise gr.Error('请先选择音频。')
    p=inside(path,OUT); x,sr=sf.read(p,dtype='float32')
    from math import gcd
    if sr!=48000:
        g=gcd(sr,48000);x=resample_poly(x,48000//g,sr//g,axis=0)
    with FILE_LOCK:
        dest=version_path(OUT/'final',p.stem+'_48k'); sf.write(dest,x,48000,subtype='PCM_24')
    save_json(dest.with_suffix('.json'),dict(source=str(p),sample_rate=48000,subtype='PCM_24',resampling='scipy.signal.resample_poly',created=time.strftime('%Y-%m-%d %H:%M:%S')))
    return str(dest)

def merge_project(path,silence):
    if not path:raise gr.Error('请打开分段项目。')
    p,data=read_project(path); pieces=[];sources=[]
    for i,s in enumerate(data['segments']):
        if not s['selected']:raise gr.Error(f'第 {i+1} 段尚未生成或选定版本。')
        selected=inside(s['selected'],p.parent);x,sr=sf.read(selected,dtype='float32')
        if x.ndim>1:x=x.mean(axis=1)
        from math import gcd
        if sr!=48000:
            g=gcd(sr,48000);x=resample_poly(x,48000//g,sr//g)
        if pieces:pieces.append(np.zeros(round(float(silence)*48000),dtype=np.float32))
        pieces.append(x);sources.append(str(selected))
    with FILE_LOCK:
        dest=version_path(OUT/'final',slug(p.parent.name)+'_narration');sf.write(dest,np.concatenate(pieces),48000,subtype='PCM_24')
        save_json(dest.with_suffix('.json'),dict(project=str(p),sources=sources,gap_seconds=silence,sample_rate=48000,subtype='PCM_24'))
    return str(dest),str(dest),'已合并为 48kHz PCM 24-bit WAV，所有单段版本仍保留。'

import html,hashlib
from model_catalog import MODELS,get_model,available_models

SHORT_TEXT='这是我做的无线头追模块，用起来还挺顺手的。'
MODEL_DESIGN=get_model('design').label
MODEL_CLONE=get_model('clone').label
MODEL_COSY=get_model('cosy').label
PREVIEW=os.environ.get('VIZRA_UI_PREVIEW')=='1'
from contextlib import contextmanager
PROJECT_BUSY={}

@contextmanager
def project_task(path):
    key=str(Path(path).resolve())
    with FILE_LOCK:PROJECT_BUSY[key]=PROJECT_BUSY.get(key,0)+1
    try:yield
    finally:
        with FILE_LOCK:
            PROJECT_BUSY[key]-=1
            if not PROJECT_BUSY[key]:PROJECT_BUSY.pop(key,None)

def favorite_choices():
    items=[]
    for p in sorted((OUT/'favorites').glob('*.wav'),key=lambda p:p.stat().st_mtime,reverse=True):
        try:
            meta=json.loads(p.with_suffix('.json').read_text(encoding='utf-8'))
            if not meta.get('text','').strip() or meta.get('deleted_from_library'):continue
            items.append((meta.get('favorite_name',p.stem),p))
        except (OSError,ValueError):continue
    counts={name:sum(other==name for other,_ in items) for name,_ in items}
    return [(name+(' · '+p.stem.rsplit('_',1)[-1] if counts[name]>1 else ''),str(p)) for name,p in items]

def remember_favorite(path):
    if not path or PREVIEW:return
    p=inside(path,OUT/'favorites')
    if str(p) not in {value for _,value in favorite_choices()}:return
    with FILE_LOCK:
        state=read_preferences();state['last_favorite']=str(p)
        save_json(OUT/'preferences.json',state)

def read_preferences():
    try:return json.loads((OUT/'preferences.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):return {}

def remember_model(value):
    if PREVIEW:return
    label=get_model(value).label
    with FILE_LOCK:
        state=read_preferences();state['last_model']=label
        save_json(OUT/'preferences.json',state)

def last_model():
    value=read_preferences().get('last_model')
    return value if value in available_models(ROOT) else MODEL_DESIGN

def last_favorite():
    choices=favorite_choices();valid={p for _,p in choices}
    try:
        saved=json.loads((OUT/'preferences.json').read_text(encoding='utf-8')).get('last_favorite')
        if saved in valid:return saved
    except (OSError,ValueError):pass
    return choices[0][1] if choices else None

def reference_preview(path):
    if not path:return None
    remember_favorite(path)
    return voice_details(path)[0]

def library_selection(path):
    if path:remember_favorite(path)
    return (*voice_details(path),gr.update(value=path))

def library_management_result(message,path):
    audio,info,text=voice_details(path) if path else (None,'','')
    return message,gr.update(choices=favorite_choices(),value=path),gr.update(choices=favorite_choices(),value=path),audio,info,text

def rename_saved_voice(path,name):
    if not path:raise gr.Error('请先选择音色。')
    name=name.strip()
    if not name or len(name)>80:raise gr.Error('请输入 1～80 字符的音色名称。')
    p=inside(path,OUT/'favorites')
    with FILE_LOCK:
        meta=json.loads(p.with_suffix('.json').read_text(encoding='utf-8'))
        if meta.get('deleted_from_library'):raise gr.Error('该音色已删除，请先撤销删除。')
        meta['favorite_name']=name;save_json(p.with_suffix('.json'),meta)
    remember_favorite(str(p))
    return library_management_result('音色已重命名。',str(p))

def delete_saved_voice(path):
    if not path:raise gr.Error('请先选择要删除的音色。')
    p=inside(path,OUT/'favorites')
    with FILE_LOCK:
        meta=json.loads(p.with_suffix('.json').read_text(encoding='utf-8'))
        meta.update(deleted_from_library=True,deleted_at=time.strftime('%Y-%m-%d %H:%M:%S'))
        save_json(p.with_suffix('.json'),meta)
        state=read_preferences();state['last_deleted_voice']=str(p)
        choices=favorite_choices();fallback=choices[0][1] if choices else None
        state['last_favorite']=fallback;save_json(OUT/'preferences.json',state)
    return library_management_result('已从音色库删除，可撤销；旧项目的参考文件仍保留。',fallback)

def undo_delete_voice():
    state=read_preferences();path=state.get('last_deleted_voice')
    if not path:raise gr.Error('没有可撤销的音色删除。')
    p=inside(path,OUT/'favorites')
    with FILE_LOCK:
        meta=json.loads(p.with_suffix('.json').read_text(encoding='utf-8'))
        meta.pop('deleted_from_library',None);meta.pop('deleted_at',None)
        save_json(p.with_suffix('.json'),meta)
        state=read_preferences();state.pop('last_deleted_voice',None);state['last_favorite']=str(p)
        save_json(OUT/'preferences.json',state)
    return library_management_result('音色已恢复。',str(p))

def audio_choices():
    result=[]
    for p in sorted((OUT/'candidates').glob('*.wav'),key=lambda x:x.stat().st_mtime,reverse=True):
        try:
            m=json.loads(p.with_suffix('.json').read_text(encoding='utf-8'))
            if not str(m.get('model','')).endswith('VoiceDesign'):continue
            seconds=m.get('duration_seconds',sf.info(p).duration)
            result.append((f"{p.stem}  ·  {seconds:.1f}s  ·  {m.get('created','')[-8:]}",str(p)))
        except (OSError,ValueError,KeyError):pass
    return result

def candidate_details(path):
    if not path:return None,'选择列表中的候选，在右侧播放试听。','',''
    p=inside(path,OUT/'candidates');m=json.loads(p.with_suffix('.json').read_text(encoding='utf-8'))
    return str(p),f"{m.get('duration_seconds',sf.info(p).duration):.1f} 秒 · {m.get('created','')} · WAV",m.get('text',''),m.get('description','')

def draw_voices(text,description,language,temperature,count):
    if PREVIEW:raise gr.Error('这是界面预览，不会启动 GPU。')
    if len(text.strip())>80:raise gr.Error('抽卡只需短片段，请控制在 80 字符以内。')
    if not text.strip() or not description.strip():raise gr.Error('请填写试听短句和音色描述。')
    epoch=ENGINE.epoch;last=None
    yield gr.update(choices=audio_choices()),gr.update(),gr.update(),'正在加载 VoiceDesign，逐条生成候选。',gr.update(),gr.update()
    for i in range(int(count)):
        if ENGINE.epoch!=epoch:return
        last,meta=ENGINE.generate('design',text,description,language,temperature,OUT/'candidates','voice_card',epoch)
        yield gr.update(choices=audio_choices()),gr.update(),gr.update(),f'已完成 {i+1} / {int(count)} 个候选。可在列表中选择试听。',gr.update(),gr.update()

def collect_voice(path,name):
    if not path:raise gr.Error('先从候选列表中选中声音。')
    result=save_favorite([path],1,name)
    remember_favorite(result[1]['value'])
    choices=favorite_choices();update=gr.update(choices=choices,value=result[1]['value'])
    return f'已将「{name.strip()}」保存到音色库。',update,gr.update(choices=choices,value=result[1]['value'])

def voice_details(path):
    if not path:return None,'还没有选择音色。',''
    p=inside(path,OUT/'favorites');m=json.loads(p.with_suffix('.json').read_text(encoding='utf-8'))
    return str(p),f"{m.get('favorite_name',p.stem)} · {sf.info(p).duration:.1f} 秒参考音频",m.get('text','')

def import_voice(audio,text,name):
    if not audio or not text.strip() or not name.strip():raise gr.Error('请选择参考音频，填写它的准确文案和音色名称。')
    x,sr=sf.read(audio,dtype='float32')
    if x.ndim>1:x=x.mean(axis=1)
    duration=len(x)/sr
    if not 3<=duration<=30:raise gr.Error('请选择 3～30 秒的干净人声片段，建议 6～15 秒。')
    if not np.isfinite(x).all() or np.max(np.abs(x))<.001:raise gr.Error('参考音频为空或异常。')
    if len(text)>500:raise gr.Error('请只填写这段参考音频里实际说出的内容。')
    from math import gcd
    if sr!=24000:
        divisor=gcd(sr,24000);x=resample_poly(x,24000//divisor,sr//divisor);sr=24000
    with FILE_LOCK:
        dest=version_path(OUT/'favorites','voice_'+slug(name));sf.write(dest,x,sr,subtype='PCM_16')
        save_json(dest.with_suffix('.json'),dict(favorite_name=name.strip(),text=text.strip(),description='导入的参考人声',model='reference-audio',reference_audio=str(dest),created=time.strftime('%Y-%m-%d %H:%M:%S'),sample_rate=sr,duration_seconds=len(x)/sr,source='imported'))
    remember_favorite(str(dest))
    return '参考人声已保存。现在可以在正式配音中选择它。',gr.update(choices=favorite_choices(),value=str(dest)),gr.update(choices=favorite_choices(),value=str(dest))

def split_script(text,limit=100):
    from text_processing import split_narration
    try:return split_narration(text,limit)
    except ValueError as error:raise gr.Error(str(error))

def script_count(text,limit):
    if not text.strip():return ''
    try:return f'{len(text.strip())} 字符 · {len(split_script(text,limit))} 段 · 按换行分段，超长行自动拆分'
    except gr.Error as exc:return str(exc)

def rows_for(data):
    from urllib.parse import quote
    rows=[];token=segment_table_token(data)
    for i,s in enumerate(data['segments'],1):
        audio=s.get('selected');ready=bool(audio and Path(audio).is_file() and Path(audio).resolve().is_relative_to((OUT/'segments').resolve()))
        duration=f'{sf.info(audio).duration:.1f}s' if ready else '—'
        source=html.escape('/gradio_api/file='+quote(str(Path(audio).resolve()),safe='/:') ,quote=True) if ready else ''
        rows.append(f'<tr data-segment="{i}" data-token="{segment_table_token(data,i)}"><td>{i:02d}</td><td class="segment-copy"><button type="button" class="segment-edit-text" data-action="edit" title="修改这段文案">{html.escape(s["text"])}</button></td><td>{len(s["text"])}</td><td>{"已完成" if ready else "待生成"}</td><td>{duration}</td><td>{len(s.get("versions",[]))}</td><td class="segment-actions"><button type="button" data-action="play" data-src="{source}" aria-label="试听第{i}段" {"" if ready else "disabled"}>▶ 试听</button><button type="button" data-action="redo" aria-label="重做第{i}段">↻ 重做</button></td></tr>')
    return '<div class="segment-grid" data-token="'+token+'"><table><thead><tr><th>段落</th><th>文案</th><th>字数</th><th>状态</th><th>时长</th><th>版本</th><th>操作</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'

def segment_table_token(data,index=None):
    if index is not None:
        data={key:data.get(key) for key in ('name','created','engine','reference','description')}|{'segment':data['segments'][int(index)-1]}
    return hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()


def listen_final(project):
    if not project:raise gr.Error('请先创建或打开项目。')
    p,data=read_project(project)
    expected=[s.get('selected') for s in data['segments']]
    for wave in sorted((OUT/'final').glob(glob.escape(slug(p.parent.name))+'_narration_v*.wav'),key=lambda p:p.stat().st_mtime,reverse=True):
        try:
            meta=json.loads(wave.with_suffix('.json').read_text(encoding='utf-8'))
            if meta.get('project')==str(p) and meta.get('sources')==expected:return str(wave)
        except (OSError,ValueError):continue
    raise gr.Error('请先完成所有段落并拼接整篇。')

_merge_project_files=merge_project
def merge_project(path,silence):
    if not path:raise gr.Error('请先创建或打开项目。')
    with project_task(path):return _merge_project_files(path,silence)

def first_segment(data,index=1):
    index=int(index);s=data['segments'][index-1]
    return gr.update(choices=segment_choices(data),value=index),s['text'],gr.update(choices=[(Path(v).name,v) for v in s.get('versions',[])],value=s.get('selected')),s.get('selected')

def narration_voice(selected_model,reference,description):
    spec=get_model(selected_model)
    if spec.voice_mode=='preset':
        if reference not in dict(PRESET_VOICES).values():raise gr.Error('请选择一个预设音色。')
        return spec,reference,''
    if spec.key=='design':
        description=description.strip()
        if not description:raise gr.Error('请输入正式配音的声音描述。VoiceDesign 不使用参考音频克隆。')
        return spec,None,description
    if not reference:raise gr.Error('请先保存或导入一个参考音色，再开始正式配音。')
    inside(reference,OUT/'favorites')
    return spec,reference,''

def create_long_project(title,script,reference,language,limit,selected_model=MODEL_CLONE,description=''):
    spec,reference,description=narration_voice(selected_model,reference,description)
    try:validate_selection(spec.key,language,reference,description)
    except ValueError as error:raise gr.Error(str(error))
    parts=split_script(script,limit)
    folder=OUT/'segments'/(slug(title.strip() or '未命名旁白')+'_'+time.strftime('%Y%m%d_%H%M%S')+'_'+secrets.token_hex(2));folder.mkdir(parents=True)
    data=dict(name=title.strip() or '未命名旁白',created=time.strftime('%Y-%m-%d %H:%M:%S'),script=script.strip(),reference=reference,description=description,language=language,model=selected_model,engine=spec.key,segments=[dict(text=p,versions=[],selected=None) for p in parts])
    path=folder/'project.json';save_json(path,data)
    return path,data

def prepare_long(title,script,reference,language,limit,selected_model=MODEL_CLONE,description=''):
    path,data=create_long_project(title,script,reference,language,limit,selected_model,description)
    return (gr.update(choices=project_choices(),value=str(path)),rows_for(data),*first_segment(data),None,None,f'已保存 {len(data["segments"])} 段。可逐段生成，完成后按顺序拼接。')

def open_long(path):
    _,data=read_project(path)
    text=data.get('script','\n\n'.join(s['text'] for s in data['segments']))
    ref=data.get('reference')
    if ref and ref not in dict(PRESET_VOICES).values() and not Path(ref).exists():ref=None
    choices=favorite_choices()
    if ref in dict(PRESET_VOICES).values():ref=None
    if ref and ref not in {value for _,value in choices}:choices.append(('本项目保留的参考音色',ref))
    return data['name'],text,gr.update(choices=choices,value=ref),data.get('language','Chinese'),rows_for(data),*first_segment(data),None,None,'项目已打开，已完成的段落会保留。'

def produce_long(project,title,script,reference,language,temperature,gap,limit,selected_model=MODEL_CLONE,description=''):
    if PREVIEW:raise gr.Error('这是界面预览，不会启动 GPU。')
    spec,reference,description=narration_voice(selected_model,reference,description)
    try:validate_selection(spec.key,language,reference,description)
    except ValueError as error:raise gr.Error(str(error))
    parts=split_script(script,limit)
    path=None;data=None
    if project:
        p,existing=read_project(project)
        if existing.get('script')==script.strip() and existing.get('reference')==reference and existing.get('language')==language and existing.get('engine','clone')==spec.key and existing.get('description','')==description and [s['text'] for s in existing['segments']]==parts:path,data=p,existing
    if path is None:path,data=create_long_project(title,script,reference,language,limit,selected_model,description)
    with project_task(path):
        epoch=ENGINE.epoch;total=len(data['segments'])
        yield gr.update(choices=project_choices(),value=str(path)),rows_for(data),*(gr.update() for _ in range(5)),None,f'准备生成 {total} 段。'
        for i in range(total):
            if ENGINE.epoch!=epoch:return
            _,data=read_project(path);s=data['segments'][i]
            if s.get('selected') and Path(s['selected']).exists():continue
            yield gr.update(),rows_for(data),*(gr.update() for _ in range(6)),f'正在生成第 {i+1} / {total} 段… 已完成片段已保存。'
            wav,meta=ENGINE.generate(data.get('engine','clone'),s['text'],data.get('description',''),language,temperature,path.parent,segment_prefix(i+1,s['text']),epoch,reference)
            with FILE_LOCK:
                _,data=read_project(path);s=data['segments'][i];s['versions'].append(wav);s['selected']=wav;save_json(path,data)
            yield gr.update(),rows_for(data),*(gr.update() for _ in range(6)),f'已完成 {i+1} / {total} 段 · 本段 {meta["duration_seconds"]:.1f} 秒'
        if ENGINE.epoch!=epoch:return
        final,file,message=merge_project(str(path),gap)
        yield gr.update(),rows_for(data),*(gr.update() for _ in range(5)),file,'整篇已完成，可点击“试听整篇”或下载 WAV。'

def redo_segment(project,index,text,reference,language,temperature,selected_model=MODEL_CLONE,description=''):
    if not project:raise gr.Error('请先创建或打开项目。')
    with project_task(project):
        return _redo_segment(project,index,text,reference,language,temperature,selected_model,description)

def _redo_segment(project,index,text,reference,language,temperature,selected_model=MODEL_CLONE,description=''):
    if PREVIEW:raise gr.Error('这是界面预览，不会启动 GPU。')
    if not project or index is None:raise gr.Error('请先创建或打开项目。')
    p,data=read_project(project)
    if get_model(selected_model).key!=data.get('engine','clone'):raise gr.Error('本项目使用 '+data.get('model',MODEL_CLONE)+'，请先选择相同模型。')
    if data.get('language','Chinese')!=language:raise gr.Error('请使用本项目原语言；要更换语言，请新建项目。')
    spec,reference,description=narration_voice(selected_model,reference,description)
    if data.get('reference')!=reference:raise gr.Error('请使用本项目原参考音色；要换声音，请新建项目以免混用。')
    if data.get('description','')!=description:raise gr.Error('请使用本项目原声音描述；要换描述，请新建项目。')
    i=int(index)-1
    wav,meta=ENGINE.generate(data.get('engine','clone'),text,description,language,temperature,p.parent,segment_prefix(i+1,text),ENGINE.epoch,reference)
    _,data=read_project(p);data['segments'][i]['text']=text;data['segments'][i]['versions'].append(wav);data['segments'][i]['selected']=wav
    data['script']='\n\n'.join(s['text'] for s in data['segments']);save_json(p,data)
    return wav,gr.update(choices=[(Path(v).name,v) for v in data['segments'][i]['versions']],value=wav),rows_for(data),None,None,data['script'],'本段新版本已保存，其他段落保留。点击“重新拼接”更新整篇。'

def segment_prefix(index,text):
    excerpt=re.sub(r'[\s\[\]{}]+','',text)[:26]
    return f'segment_{int(index):03d}_'+slug(excerpt).strip('。！？!?，,；; ')

def run_workflow(workflow,*args):
    if workflow=='分段制作':
        project,title,script,reference,language,temperature,gap,limit,selected_model,*extra=args
        yield prepare_long(title,script,reference,language,limit,selected_model,*extra)
    else:yield from produce_long(*args)

def pick_version(project,index,version):
    audio,message=select_version(project,index,version);_,data=read_project(project)
    return audio,rows_for(data),None,None,message


