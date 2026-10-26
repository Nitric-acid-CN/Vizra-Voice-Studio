"""Download a pinned allowlist of official files, verify LFS SHA256, resume."""
import argparse,hashlib,json,time,urllib.request,urllib.parse,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODELS={
 'chatter':('ResembleAI/chatterbox-turbo','749d1c1a46eb10492095d68fbcf55691ccf137cd','chatterbox-turbo',('ve.safetensors','t3_turbo_v1.safetensors','s3gen_meanflow.safetensors','conds.pt','added_tokens.json','merges.txt','special_tokens_map.json','tokenizer_config.json','vocab.json','README.md')),
 'kokoro':('hexgrad/Kokoro-82M','f3ff3571791e39611d31c381e3a41a3af07b4987','Kokoro-82M',('config.json','kokoro-v1_0.pth','README.md','VOICES.md','voices/am_michael.pt','voices/am_adam.pt','voices/am_eric.pt','voices/af_heart.pt','voices/bm_george.pt','voices/bf_emma.pt')),
}
def fetch(key):
    repo,revision,folder,files=MODELS[key];dest=ROOT/'models'/folder;dest.mkdir(parents=True,exist_ok=True)
    api=f'https://huggingface.co/api/models/{repo}/revision/{revision}?blobs=true'
    info=json.load(urllib.request.urlopen(api,timeout=60));siblings={x['rfilename']:x for x in info['siblings']}
    for name in files:
        meta=siblings[name];size=meta['size'];sha=meta.get('lfs',{}).get('sha256')
        path=dest/name;path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and path.stat().st_size==size:
            if not sha or hashlib.file_digest(path.open('rb'),'sha256').hexdigest()==sha:continue
        url=f'https://huggingface.co/{repo}/resolve/{revision}/'+urllib.parse.quote(name)
        part=path.with_name(path.name+'.part')
        for attempt in range(4):
            try:
                offset=part.stat().st_size if part.exists() else 0
                if offset>=size:part.unlink();offset=0
                request=urllib.request.Request(url,headers={'Range':f'bytes={offset}-'} if offset else {})
                with urllib.request.urlopen(request,timeout=90) as response:
                    append=response.status==206 and response.headers.get('Content-Range','').startswith(f'bytes {offset}-')
                    print('Downloading',key,name,'resume',offset if append else 0,'/',size,flush=True)
                    with part.open('ab' if append else 'wb') as stream:
                        last=time.monotonic()
                        while block:=response.read(2*1024*1024):
                            stream.write(block)
                            if time.monotonic()-last>30:print(name,stream.tell(),'/',size,flush=True);last=time.monotonic()
                if part.stat().st_size!=size:raise RuntimeError('Size mismatch: '+name)
                if sha and hashlib.file_digest(part.open('rb'),'sha256').hexdigest()!=sha:
                    part.unlink();raise RuntimeError('SHA256 mismatch: '+name)
                part.replace(path);break
            except Exception as error:
                print('Retry',attempt+1,name,str(error),flush=True)
                if attempt==3:raise
                time.sleep(2)
    manifest={'repo':repo,'revision':revision,'files':[siblings[name] for name in files]}
    (dest/'download_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('VERIFIED',key,revision,flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('model',choices=MODELS);args=parser.parse_args();fetch(args.model)
