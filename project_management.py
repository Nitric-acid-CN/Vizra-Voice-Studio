"""Confirmed local project deletion, scoped to its own files and linked exports."""
import os,json,hashlib,html
from pathlib import Path
import workbench_core as s

def project_files(path):
    raw=Path(path)
    if raw.parent.is_symlink() or raw.parent.is_junction():raise s.gr.Error('项目目录包含链接，不能自动删除。')
    p,data=s.read_project(path);folder=p.parent.resolve()
    if p.name!='project.json' or folder.parent!=(s.OUT/'segments').resolve():raise s.gr.Error('无效的项目目录。')
    if s.PROJECT_BUSY.get(str(p.resolve())):raise s.gr.Error('此项目正在生成，请先停止任务，再删除。')
    files=[];directories=[]
    for parent,names,filenames in os.walk(folder,followlinks=False):
        for name in names:
            child=Path(parent)/name
            if child.is_symlink() or child.is_junction():raise s.gr.Error('项目目录包含链接，不能自动删除。')
            if not child.resolve().is_relative_to(folder):raise s.gr.Error('项目路径超出范围。')
            directories.append(child)
        for name in filenames:
            child=Path(parent)/name
            if child.is_symlink() or not child.resolve().is_relative_to(folder):raise s.gr.Error('项目文件路径超出范围。')
            files.append(child)
    for meta in (s.OUT/'final').glob('*.json'):
        try:linked=json.loads(meta.read_text(encoding='utf-8')).get('project')
        except (OSError,ValueError):continue
        if not linked or Path(linked).resolve()!=p.resolve():continue
        for child in [meta,meta.with_suffix('.wav')]:
            if child.exists():
                if child.is_symlink() or child.resolve().parent!=(s.OUT/'final').resolve():raise s.gr.Error('导出文件路径超出范围。')
                files.append(child)
    signature=hashlib.sha256(json.dumps([(str(item),item.stat().st_size,item.stat().st_mtime_ns) for item in sorted(files)],ensure_ascii=False).encode('utf-8')).hexdigest()
    return p,data,files,directories,signature

def ask_delete_project(path):
    if not path:raise s.gr.Error('请先选择要删除的项目。')
    with s.FILE_LOCK:p,data,files,_,signature=project_files(path)
    message=f'**删除「{html.escape(data["name"])}」？**\n\n将永久删除本项目的 **{len(files)} 个本地文件**，包含分段音频、历史版本、项目信息和整篇导出。音色库收藏会保留。此操作无法撤销。'
    return message,s.gr.update(visible=True),dict(path=str(p),signature=signature)

def confirm_delete_project(current,confirmation):
    if not confirmation or str(Path(current or '').resolve())!=confirmation.get('path'):raise s.gr.Error('项目已切换，请重新确认删除。')
    if s.PREVIEW:raise s.gr.Error('预览模式不删除本地项目。')
    with s.FILE_LOCK:
        p,data,files,directories,signature=project_files(current)
        if signature!=confirmation.get('signature'):raise s.gr.Error('项目文件已有更新，请重新确认删除。')
        for file in files:file.unlink()
        for folder in sorted(directories,key=lambda p:len(p.parts),reverse=True):folder.rmdir()
        p.parent.rmdir()
    return (s.gr.update(choices=s.project_choices(),value=None),s.rows_for({'segments':[]}),s.gr.update(choices=[],value=None),'',s.gr.update(choices=[],value=None),None,None,None,f'已删除项目「{data["name"]}」的 {len(files)} 个本地文件。音色库收藏保留。',s.gr.update(visible=False),None)
