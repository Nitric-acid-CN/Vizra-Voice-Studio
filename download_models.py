import urllib.request, urllib.parse, json, pathlib, hashlib, time, sys
repo = sys.argv[1] if len(sys.argv)>1 else 'Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign'
root = pathlib.Path(__file__).resolve().parent/'models'/repo.split('/')[-1]
base = 'https://modelscope.cn/api/v1/models/' + repo + '/repo/'
data = json.load(urllib.request.urlopen(base+'files?Recursive=true', timeout=90))
root.mkdir(parents=True, exist_ok=True)
(root/'download_manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
for item in data['Data']['Files']:
    if item['Type'] != 'blob': continue
    if 'CosyVoice3' in repo and (item['Path'] in ['llm.rl.pt','flow.decoder.estimator.fp32.onnx','speech_tokenizer_v3.batch.onnx'] or item['Path'].startswith('asset/')):continue
    path = (root/item['Path']).resolve()
    if not path.is_relative_to(root.resolve()): raise RuntimeError('Invalid model path')
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.stat().st_size == item['Size']: continue
    url = base+'?Revision=master&FilePath='+urllib.parse.quote(item['Path'])
    for attempt in range(4):
        try:
            tmp = path.with_name(path.name+'.part')
            offset = tmp.stat().st_size if tmp.exists() else 0
            req=urllib.request.Request(url,headers={'Range':f'bytes={offset}-'} if offset else {})
            with urllib.request.urlopen(req,timeout=120) as response:
                if response.status != 206: offset=0
                print('Downloading',item['Path'],item['Size'],'offset',offset,flush=True)
                with tmp.open('ab' if offset else 'wb') as out:
                    last=time.time()
                    while block:=response.read(4*1024*1024):
                        out.write(block)
                        if time.time()-last>30:
                            print(item['Path'],out.tell(),flush=True); last=time.time()
            if tmp.stat().st_size != item['Size']: raise RuntimeError('size mismatch')
            digest=hashlib.file_digest(tmp.open('rb'),'sha256').hexdigest()
            if digest != item['Sha256']: raise RuntimeError('SHA256 mismatch')
            tmp.replace(path); print('Verified',item['Path'],flush=True); break
        except Exception as e:
            print('Retry',attempt,str(e),flush=True)
            if attempt==3: raise
            time.sleep(3)
print('MODEL DOWNLOAD COMPLETE',flush=True)
