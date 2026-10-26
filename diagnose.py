"""Read-only local installation report. Never imports weights or downloads files."""
import json,sys,subprocess,platform
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
from model_catalog import MODELS,available_models
def diagnose():
    result=dict(platform=platform.platform(),python=sys.version,root=str(ROOT),models=[])
    available=available_models(ROOT)
    for spec in MODELS:
        python=ROOT/spec.environment/'Scripts'/'python.exe'
        result['models'].append(dict(model=spec.label,installed=spec.label in available,environment_exists=python.exists(),languages=spec.languages,voice_mode=spec.voice_mode))
    try:result['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.free,driver_version','--format=csv,noheader'],text=True,timeout=10).strip()
    except (OSError,subprocess.SubprocessError) as error:result['gpu_error']=str(error)
    print(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':diagnose()
