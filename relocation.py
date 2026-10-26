"""Repair application-owned output paths after restoring a backup elsewhere."""
import json,re
from pathlib import Path

def repair_output_paths(root):
    root=Path(root).resolve();output=root/'outputs';prefixes=set()
    files=list(output.rglob('*.json'))
    def discover(value):
        if isinstance(value,str):
            match=re.match(r'^([A-Za-z]:[\\/].*?)[\\/]outputs[\\/]',value)
            if match and Path(match.group(1)).resolve()!=root:prefixes.add(match.group(1))
        elif isinstance(value,dict):
            for item in value.values():discover(item)
        elif isinstance(value,list):
            for item in value:discover(item)
    data=[]
    for file in files:
        try:item=json.loads(file.read_text(encoding='utf-8'))
        except (OSError,ValueError):continue
        data.append((file,item));discover(item)
    def replace(value):
        if isinstance(value,str):
            for prefix in prefixes:
                if value.lower().startswith(prefix.lower()+'\\') or value.lower().startswith(prefix.lower()+'/'):return str(root)+value[len(prefix):]
        elif isinstance(value,dict):return {key:replace(item) for key,item in value.items()}
        elif isinstance(value,list):return [replace(item) for item in value]
        return value
    for file,item in data:
        updated=replace(item)
        if updated!=item:
            temporary=file.with_suffix('.json.tmp');temporary.write_text(json.dumps(updated,ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(file)
