"""No inference: verify imports, CUDA, and the complete offline asset manifest."""
import os,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
key=sys.argv[1]
if key not in ('chatter','kokoro'):raise ValueError('Unknown engine')
import torch
if not torch.cuda.is_available():raise RuntimeError('CUDA is unavailable')
if key=='chatter':
    from chatterbox.tts_turbo import ChatterboxTurboTTS
    folder=ROOT/'models'/'chatterbox-turbo'
else:
    import spacy
    from kokoro import KPipeline,KModel
    if not spacy.util.is_package('en_core_web_sm'):raise RuntimeError('Missing en_core_web_sm offline asset')
    folder=ROOT/'models'/'Kokoro-82M'
manifest=json.loads((folder/'download_manifest.json').read_text(encoding='utf-8'))
for file in manifest['files']:
    path=folder/file['rfilename']
    if not path.is_file() or path.stat().st_size!=file['size']:raise RuntimeError('Missing model asset: '+str(path))
(ROOT/'models'/(key+'.ready.json')).write_text(json.dumps({'installed':True,'revision':manifest['revision'],'inference_tested_on_this_machine':False}),encoding='utf-8')
print(key,'ready; generate a short test clip before production')
