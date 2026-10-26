"""Only manages this workbench's own server process tree."""
import json,subprocess,os
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parent
URL='http://127.0.0.1:'+str(json.loads((ROOT/'config.json').read_text(encoding='utf-8')).get('port',7860))

def server_pid():
    try:
        data=json.loads((ROOT/'cache'/'server.json').read_text(encoding='utf-8'))
        p=psutil.Process(int(data['pid']))
        for arg in p.cmdline():
            candidate=Path(arg)
            if not candidate.is_absolute():candidate=Path(p.cwd())/candidate
            if candidate.resolve()==(ROOT/'studio.py').resolve():return p.pid
    except (OSError,ValueError,KeyError,psutil.Error):pass
    return None

def stop_server():
    pid=server_pid()
    if pid:
        subprocess.run(['taskkill','/PID',str(pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW,timeout=20)
    return bool(pid)

if __name__=='__main__':
    print('Workbench stopped.' if stop_server() else 'Workbench is already stopped.')
