"""Fetch pinned official upstream sources. Does not install packages or execute them."""
from pathlib import Path
import urllib.request,zipfile,io,json
ROOT=Path(__file__).resolve().parent
SOURCES=[('QwenAudio/CosyVoice','074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc','CosyVoice-main'),('shivammehta25/Matcha-TTS','dd9105b34bf2be2230f4aa1e4769fb586a3c824e','Matcha-TTS-dd9105b34bf2be2230f4aa1e4769fb586a3c824e')]
for repo,commit,folder in SOURCES:
    dest=(ROOT/'engines'/folder).resolve()
    if (dest/'cosyvoice').is_dir() or (dest/'matcha').is_dir():continue
    url=f'https://codeload.github.com/{repo}/zip/{commit}'
    print('Fetching',repo,commit,flush=True)
    data=urllib.request.urlopen(url,timeout=120).read()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member in archive.infolist():
            relative=Path(*Path(member.filename).parts[1:])
            if not relative.parts:continue
            target=(dest/relative).resolve()
            if not target.is_relative_to(dest):raise RuntimeError('Invalid archive path')
            if member.is_dir():target.mkdir(parents=True,exist_ok=True)
            else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.read(member))
(ROOT/'engines'/'sources.json').write_text(json.dumps(SOURCES,indent=2),encoding='utf-8')
