"""Inline editing, version selection and explicit export state for the desktop UI."""
import json,time,html,os,re
from pathlib import Path
from urllib.parse import quote
import workbench_core as s

__all__=['rows_for','handle_segment_row','row_update','run_workflow','merge_project','listen_final','clear_final','open_local_folder']
_read=s.read_project;_create=s.create_long_project;_merge=s.merge_project;_produce=s.produce_long
ROW_STATE={}

def read_project(path):
    p,data=_read(path);data['_ui_project']=str(p);return p,data

def create_project(*args,**kwargs):
    p,data=_create(*args,**kwargs);data['_ui_project']=str(p);data['source_script']=data['script'];s.save_json(p,data);return p,data

def final_path(project):
    p,_=s.read_project(project)
    return s.OUT/'final'/(s.slug(p.parent.name)+'_narration.wav')

def source_records(data):
    result=[]
    for segment in data['segments']:
        value=segment.get('selected');p=Path(value) if value else None
        result.append([value,p.stat().st_size,p.stat().st_mtime_ns] if p and p.is_file() else [value,None,None])
    return result

def export_state(data):
    project=data.get('_ui_project')
    if not project:return '尚未拼接'
    wave=final_path(project)
    if not wave.exists():return '尚未拼接'
    try:meta=json.loads(wave.with_suffix('.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):return '需要重新拼接'
    if meta.get('source_records')!=source_records(data):return '片段已更新 · 需要重新拼接'
    return '整篇已更新 · '+meta.get('updated_at','')+' · 第 '+str(meta.get('export_revision',1))+' 次拼接'

def rows_for(data):
    rows=[];project=data.get('_ui_project','')
    for index,segment in enumerate(data['segments'],1):
        audio=segment.get('selected');ready=bool(audio and Path(audio).is_file())
        src='/gradio_api/file='+quote(str(Path(audio).resolve()),safe='/:') if ready else ''
        state=ROW_STATE.get((project,index),'已完成' if ready else '待生成')
        busy=state in ('等待中','生成中')
        status=('<span class="row-spinner" aria-hidden="true"></span> ' if busy else '')+html.escape(state)
        versions=[]
        for number,path in enumerate(segment.get('versions',[]),1):
            versions.append('<option value="'+html.escape(path,quote=True)+'" '+('selected' if path==audio else '')+'>v'+str(number).zfill(3)+'</option>')
        version='<select aria-label="第'+str(index)+'段版本" data-action="version" '+('disabled' if busy or not versions else '')+'>'+(''.join(versions) or '<option>—</option>')+'</select>'
        duration=f'{s.sf.info(audio).duration:.1f}s' if ready else '—'
        rows.append(f'<tr data-segment="{index}" data-token="{s.segment_table_token(data,index)}"><td>{index:02d}</td><td class="segment-copy"><textarea aria-label="第{index}段文案" rows="2" {"readonly" if busy else ""}>{html.escape(segment["text"])}</textarea></td><td class="row-status">{status}</td><td>{duration}</td><td>{version}</td><td class="segment-actions"><button type="button" data-action="play" data-src="{html.escape(src,quote=True)}" aria-label="试听第{index}段" {"" if ready else "disabled"}>▶ 试听</button><button type="button" data-action="redo" aria-label="重做第{index}段" {"disabled" if busy else ""}>↻ 重做</button></td></tr>')
    summary=html.escape(export_state(data))
    return '<div class="segment-grid" data-project="'+html.escape(project,quote=True)+'"><table><thead><tr><th>段落</th><th>文案（直接修改后点重做）</th><th>状态</th><th>时长</th><th>使用版本</th><th>操作</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div><div class="export-state" role="status">'+summary+'</div>'

def event_data(project,request):
    p,data=s.read_project(project)
    try:
        event=json.loads(request);index=int(event['index'])
        assert 1<=index<=len(data['segments'])
        assert event['token']==s.segment_table_token(data,index)
    except (ValueError,KeyError,TypeError,AssertionError):raise s.gr.Error('此片段已有更新，请重试。')
    return p,data,index,event

def row_update(project,request):
    p,data,index,event=event_data(project,request);segment=data['segments'][index-1]
    value=event.get('version')
    if value not in segment.get('versions',[]):raise s.gr.Error('无效的片段版本。')
    s.inside(value,p.parent)
    with s.FILE_LOCK:
        data.setdefault('source_script',data['script']);segment['selected']=value
        metadata=json.loads(Path(value).with_suffix('.json').read_text(encoding='utf-8'))
        segment['text']=metadata.get('text',segment['text'])
        data['script']='\n'.join(item['text'] for item in data['segments']);s.save_json(p,data)
    ROW_STATE.pop((str(p),index),None)
    return rows_for(data),None,f'第 {index} 段已使用所选版本。'+export_state(data)

def handle_segment_row(project,request,reference,language,temperature,selected_model,description):
    p,data,index,event=event_data(project,request)
    text=str(event.get('text',data['segments'][index-1]['text'])).strip()
    if not text or len(text)>200:raise s.gr.Error('单段请输入 1～200 字符。')
    key=(str(p),index)
    with s.project_task(p):
        with s.FILE_LOCK:
            data.setdefault('source_script',data['script']);s.save_json(p,data)
        ROW_STATE[key]='生成中'
        yield (*(s.gr.update() for _ in range(4)),rows_for(data),s.gr.update(),s.gr.update(),s.gr.update(),f'正在重做第 {index} 段…',s.gr.update())
        try:
            s.redo_segment(str(p),index,text,reference,language,temperature,selected_model,description)
        except Exception as error:
            ROW_STATE[key]='失败 · 可重试';_,data=s.read_project(p)
            yield (*(s.gr.update() for _ in range(4)),rows_for(data),s.gr.update(),s.gr.update(),s.gr.update(),f'第 {index} 段失败：{error}',s.gr.update())
            return
        finally:
            if ROW_STATE.get(key)=='生成中':ROW_STATE.pop(key,None)
        _,data=s.read_project(p)
        yield (*(s.gr.update() for _ in range(4)),rows_for(data),s.gr.update(),None,s.gr.update(),f'第 {index} 段已完成，已选用新版本。'+export_state(data),s.gr.update())

def merge_project(project,gap):
    if not 0<=float(gap)<=2:raise s.gr.Error('段落间静音应为 0～2 秒。')
    p,data=s.read_project(project);target=final_path(project);revision=0
    try:revision=json.loads(target.with_suffix('.json').read_text(encoding='utf-8')).get('export_revision',0)
    except (OSError,ValueError):pass
    with s.project_task(p):
        wave,_,_=_merge(project,gap);temporary=Path(wave)
        metadata=json.loads(temporary.with_suffix('.json').read_text(encoding='utf-8'))
        metadata.update(source_records=source_records(data),updated_at=time.strftime('%H:%M:%S'),export_revision=revision+1)
        os.replace(temporary,target)
        temporary.with_suffix('.json').unlink(missing_ok=True);s.save_json(target.with_suffix('.json'),metadata)
    return str(target),str(target),'拼接已更新（第 '+str(revision+1)+' 次）。再次拼接会替换同一个整篇 WAV，片段版本保留。'

def merge_controls(project,gap):
    audio,file,status=merge_project(project,gap);_,data=s.read_project(project)
    return audio,file,status,rows_for(data)

def listen_final(project):
    _,data=s.read_project(project);wave=final_path(project)
    if not wave.exists() or '需要' in export_state(data):raise s.gr.Error('整篇尚未更新，请先点击“拼接 / 更新整篇”。')
    return str(wave)

def clear_final(project):
    p,data=s.read_project(project)
    if s.PROJECT_BUSY.get(str(p)):raise s.gr.Error('项目正在生成，请完成或停止后再删除整篇。')
    removed=0
    with s.FILE_LOCK:
        for meta in (s.OUT/'final').glob('*.json'):
            try:linked=json.loads(meta.read_text(encoding='utf-8')).get('project')
            except (OSError,ValueError):continue
            if not linked or Path(linked).resolve()!=p.resolve():continue
            for file in [meta.with_suffix('.wav'),meta]:
                if file.exists():
                    s.inside(file,s.OUT/'final').unlink();removed+=1
    return None,None,f'已删除整篇导出（{removed} 个文件）。所有片段和历史版本保留。',rows_for(data)

def open_local_folder(project,category):
    if category=='project':folder=s.read_project(project)[0].parent if project else s.OUT/'segments'
    elif category in ('final','favorites','candidates'):folder=s.OUT/category
    else:raise s.gr.Error('无效的目录。')
    folder=folder.resolve()
    if not folder.is_relative_to(s.OUT.resolve()):raise s.gr.Error('目录超出工作台范围。')
    folder.mkdir(parents=True,exist_ok=True);os.startfile(str(folder))
    return '已打开：'+str(folder)

def run_workflow(workflow,project,title,script,reference,language,temperature,gap,limit,selected_model,description=''):
    if project:
        _,old=s.read_project(project)
        if script.strip() in (old.get('source_script',old['script']),old['script']):script=old['script']
    path=project;active=None
    try:
        for result in _produce(project,title,script,reference,language,temperature,gap,limit,selected_model,description):
            result=list(result)
            if isinstance(result[0],dict) and result[0].get('value'):path=result[0]['value']
            match=re.search(r'正在生成第 (\d+)',str(result[-1]))
            if active and '已完成' in str(result[-1]):ROW_STATE.pop((str(path),active),None);active=None
            if match:active=int(match.group(1));ROW_STATE[(str(path),active)]='生成中'
            if path:
                _,data=s.read_project(path);result[1]=rows_for(data)
            yield tuple(result)
    except Exception as error:
        if not path:raise
        if active:ROW_STATE[(str(path),active)]='失败 · 可重试'
        _,data=s.read_project(path)
        yield (s.gr.update(),rows_for(data),*(s.gr.update() for _ in range(6)),f'生成未完成：{error}。已完成片段保留，可修复后继续。')
    finally:
        if active and ROW_STATE.get((str(path),active))=='生成中':ROW_STATE.pop((str(path),active),None)

s.read_project=read_project;s.create_long_project=create_project;s.rows_for=rows_for;s.merge_project=merge_project;s.listen_final=listen_final
__all__.append('merge_controls')
