"""Model routing. Adapters run in separate environments and share a WAV protocol."""
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ModelSpec:
    key:str
    label:str
    mode:str
    environment:str
    worker:str
    model_folder:str
    languages:tuple=('Chinese','English')
    voice_mode:str='reference'
    sampling:bool=True

MODELS=(
    ModelSpec('design','Qwen · VoiceDesign 1.7B','draw','.venv','worker.py','Qwen3-TTS-12Hz-1.7B-VoiceDesign',voice_mode='design'),
    ModelSpec('clone','Qwen · Base 0.6B','narration','.venv','worker.py','Qwen3-TTS-12Hz-0.6B-Base'),
    ModelSpec('cosy','CosyVoice 3 · 0.5B','narration','.venv-cosy','worker_cosy.py','Fun-CosyVoice3-0.5B-2512',sampling=False),
    ModelSpec('chatter','Chatterbox Turbo · 英文克隆','narration','.venv-english','worker_english.py','chatterbox-turbo',languages=('English',)),
    ModelSpec('kokoro','Kokoro 82M · 英文预设','narration','.venv-english','worker_english.py','Kokoro-82M',languages=('English',),voice_mode='preset',sampling=False),
)

PRESET_VOICES=(('美式男声 · Michael','am_michael'),('美式男声 · Adam','am_adam'),('美式男声 · Eric','am_eric'),('美式女声 · Heart','af_heart'),('英式男声 · George','bm_george'),('英式女声 · Emma','bf_emma'))

def validate_selection(value,language,reference=None,description=''):
    spec=get_model(value)
    if language not in spec.languages:raise ValueError(spec.label+' 目前仅支持英文，请选择英文或更换模型。')
    if spec.voice_mode=='design' and not description.strip():raise ValueError('请输入声音描述。')
    if spec.voice_mode=='reference' and not reference:raise ValueError('请先选择一个收藏音色。')
    if spec.voice_mode=='preset' and reference not in dict(PRESET_VOICES).values():raise ValueError('请选择一个预设音色。')
    return spec

def get_model(value):
    for spec in MODELS:
        if value in (spec.key,spec.label):return spec
    raise ValueError('未知模型：'+str(value))

def available_models(root):
    root=Path(root);result=[]
    for spec in MODELS:
        if not (root/'models'/spec.model_folder).is_dir():continue
        if spec.key=='cosy' and not (root/'models'/'cosyvoice.ready.json').is_file():continue
        if spec.key in ('chatter','kokoro') and not (root/'models'/(spec.key+'.ready.json')).is_file():continue
        if not (root/spec.environment/'Scripts'/'python.exe').is_file():continue
        result.append(spec.label)
    return result
