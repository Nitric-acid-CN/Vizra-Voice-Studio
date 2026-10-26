"""Minimal local UI. Model routing and long-form jobs live in workbench_core."""
from workbench_core import *
from studio_theme import CSS
import studio_actions as actions
from studio_actions import *
from project_management import ask_delete_project,confirm_delete_project
from relocation import repair_output_paths
from model_catalog import PRESET_VOICES
from local_web import local_web_options

CSS+='''
#sidebar{min-width:175px!important;max-width:190px!important;padding:26px 16px!important;gap:20px!important}#workspace{padding:22px 28px 32px!important;gap:20px!important}#toolbar{align-items:center!important;padding:0 4px 14px!important;border-bottom:1px solid #dfe5ef;margin-bottom:0!important;gap:18px!important}#toolbar .app-title{font-size:20px;margin:0}#toolbar .form{background:transparent!important}#toolbar label>span{color:#52617c!important}#toolbar .block{background:transparent!important}.prose h2{font-size:18px!important;margin:0!important}.panel-sub,.quiet{color:#65748f!important}.intro{font-size:12px;color:#66758e!important}.section-label{font-size:14px;font-weight:600;color:#36445f;margin:0 0 4px}.gradio-container textarea{line-height:1.9!important}.count-label{margin-top:0!important;line-height:1.8!important;color:#64728a!important}.nav-radio>div{gap:6px!important}.gradio-container .block label>span{line-height:1.8!important}.run-row{gap:10px!important}.run-row button.primary{min-height:48px!important}.run-row button.stop{min-height:48px!important}#model-selector{min-width:280px!important}#formal-script,#formal-settings,#draw-settings,#draw-results{padding:20px!important;gap:14px!important}#formal-settings{max-width:100%!important}#draw-settings .form,#draw-results .form,#formal-settings .form,#formal-script .form{background:transparent!important}.gradio-container .audio-panel{min-height:125px!important}.compact-status textarea{min-height:48px!important;font-size:12px!important}.gradio-container #formal-segments{padding:18px!important}#formal-segments th:nth-child(2),#formal-segments td:nth-child(2){width:55%!important;min-width:260px!important}#workspace .form{border:0!important}.workflow-radio>div{gap:6px!important}.workflow-radio label{border-radius:8px!important;padding:9px 14px!important}.workflow-radio label.selected{background:#edf1ff!important}.brand small{letter-spacing:1px!important}#workspace .html-container{overflow:visible!important}#workspace .prose{overflow:visible!important}#toolbar .column{min-width:0!important}@media(max-width:900px){#sidebar{min-width:155px!important;max-width:170px!important}#workspace{padding:18px!important}}@media(max-width:650px){#sidebar{max-width:100%!important;min-height:auto!important}#toolbar{flex-wrap:wrap!important}#model-selector{min-width:100%!important}}
'''
CSS+='''.segment-grid table th,.segment-grid table td{border:0!important;border-bottom:1px solid #e9edf5!important}.segment-grid table tr:last-child td{border-bottom:0!important}'''
CSS+='''
.control-row,.save-row{align-items:flex-end!important;gap:12px!important}.control-row>button,.save-row>button{align-self:flex-end!important;margin-bottom:8px!important;min-height:42px!important}.control-row>.form{min-width:0!important}.action-row{align-items:stretch!important;gap:12px!important}.action-row>button,.action-row>a{min-height:42px!important;height:42px!important;box-sizing:border-box!important;display:flex!important;align-items:center!important;justify-content:center!important}
'''
CSS+='''#toolbar>.form{flex:0 0 360px!important;width:360px!important;min-width:0!important;max-width:360px!important;margin-left:auto!important}#toolbar{justify-content:space-between!important}#model-selector{min-width:0!important;width:100%!important;max-width:100%!important}.save-row{align-items:flex-end!important;gap:12px!important}.save-row>button{margin-bottom:8px!important}.inline-message{font-size:12px!important;color:#66748d!important;line-height:1.8!important;margin:0!important}.inline-message .prose{font-size:12px!important}.inline-message:empty{display:none!important}@media(max-width:650px){#toolbar>.form{flex:1 1 100%!important;width:100%!important;max-width:100%!important}}'''
CSS+='''
.row-event-input{display:none!important}.segment-grid{width:100%;overflow-x:auto;border:1px solid #e0e6f1;border-radius:12px;background:white}.segment-grid table{width:100%;border-collapse:collapse;min-width:800px;font-size:13px}.segment-grid th{background:#f5f7fc;color:#65738d;font-weight:500;text-align:left;padding:13px 10px;white-space:nowrap}.segment-grid td{padding:14px 10px;border-top:1px solid #e9edf5;vertical-align:middle;color:#52617a}.segment-grid tbody tr:hover{background:#fafbff}.segment-grid td:first-child{font-variant-numeric:tabular-nums;color:#7d8ca7}.segment-grid th:nth-child(2),.segment-grid td:nth-child(2){width:52%!important;min-width:240px!important}.segment-grid .segment-edit-text{background:none!important;border:0!important;box-shadow:none!important;text-align:left;line-height:1.8;padding:0!important;font-weight:400;color:#253553;cursor:text;white-space:pre-wrap;overflow-wrap:anywhere}.segment-grid .segment-actions{white-space:nowrap}.segment-grid .segment-actions button{padding:7px 10px;border:1px solid #dce3f2;border-radius:7px;background:#fff;color:#5369c5;font-size:12px;cursor:pointer;margin:0 3px}.segment-grid .segment-actions button:hover{background:#eef2ff}.segment-grid .segment-actions button[aria-pressed=true]{background:#e8edff;color:#4056b8}.segment-grid .segment-actions button:disabled{opacity:.38;cursor:default}.segment-grid .segment-actions button:focus-visible,.segment-grid .segment-edit-text:focus-visible{outline:2px solid #7086ed;outline-offset:2px}
'''

CSS+='''@keyframes row-spin{to{transform:rotate(360deg)}}.row-spinner{display:inline-block;width:12px;height:12px;border:2px solid #d9e1fc;border-top-color:#5a72db;border-radius:50%;animation:row-spin .8s linear infinite;vertical-align:middle}.segment-grid textarea{box-sizing:border-box!important;width:100%!important;min-height:74px!important;line-height:1.8!important;padding:8px!important;border:1px solid #e0e6f2!important;border-radius:7px!important;resize:vertical;font-size:13px!important;background:#fafbff!important}.segment-grid select{min-width:84px;height:36px;border:1px solid #dce3f2;border-radius:7px;background:white;padding:0 8px;color:#425778}.segment-grid .row-status{min-width:96px;white-space:nowrap}.export-state{padding:12px 4px;color:#5c6c89;font-size:13px;line-height:1.8}'''

def choices_models():
    values=available_models(ROOT)
    if PREVIEW and MODEL_COSY not in values:values.append(MODEL_COSY)
    return values

def navigation(value):
    return gr.update(visible=value=='音色抽卡'),gr.update(visible=value=='正式配音'),gr.update(visible=value=='音色库')

def selected_model(value,current_language='Chinese'):
    remember_model(value)
    spec=get_model(value);design=spec.voice_mode=='design'
    languages=[('中文','Chinese'),('英文','English')]
    language=current_language if current_language in spec.languages else spec.languages[0]
    hint='抽卡请选择 VoiceDesign；当前模型请在“正式配音”中选择'+('预设音色。' if spec.voice_mode=='preset' else '参考音色。')
    return (gr.update(visible=spec.sampling),gr.update(visible=design),gr.update(visible=spec.voice_mode=='reference'),gr.update(interactive=design),gr.update(visible=not design,value=hint),gr.update(visible=spec.voice_mode=='preset'),gr.update(choices=[item for item in languages if item[1] in spec.languages],value=language))

def effective_reference(model,reference,preset):
    return preset if get_model(model).voice_mode=='preset' else reference

def generate_narration(workflow,project,title,script,reference,language,temperature,gap,limit,model,description,preset):
    yield from run_workflow(workflow,project,title,script,effective_reference(model,reference,preset),language,temperature,gap,limit,model,description)

def redo_row(project,request,reference,language,temperature,model,description,preset):
    yield from handle_segment_row(project,request,effective_reference(model,reference,preset),language,temperature,model,description)

def save_preset(value):
    if value in dict(PRESET_VOICES).values():
        with FILE_LOCK:
            state=read_preferences();state['last_preset']=value;save_json(OUT/'preferences.json',state)

def model_status():
    installed=set(available_models(ROOT))
    return '\n'.join('- '+spec.label+'：'+('已安装' if spec.label in installed else '未安装') for spec in MODELS)+'\n\n首次安装请运行 setup.ps1；日常推理使用本地文件，每次只加载一个模型。'

def new_narration():
    if PROJECT_BUSY:raise gr.Error('请先完成或停止当前生成，再新建项目。')
    return (gr.update(value=None),'','',rows_for({'segments':[]}),None,None,'输入文案后点击“生成全部片段”。')

def workflow_mode(value):
    return gr.update(value='创建分段' if value=='分段制作' else '生成整篇'),gr.update(open=value=='分段制作')

def open_project_ui(path):
    result=list(open_long(path));_,data=actions.s.read_project(path)
    result[-1]=actions.export_state(data)
    wave=actions.final_path(path)
    result[10]=str(wave) if wave.exists() and '需要' not in result[-1] else None
    key=data.get('engine','clone');label=get_model(key).label
    return (*result,gr.update(value=label),data.get('description',''),gr.update(value=data.get('reference') if key=='kokoro' else PRESET_VOICES[0][1]))

def build_ui():
    repair_output_paths(ROOT)
    saved_voice=last_favorite();saved_audio,saved_info,saved_text=voice_details(saved_voice) if saved_voice else (None,'','')
    saved_model=last_model();saved_spec=get_model(saved_model);initial_view='音色抽卡' if saved_model==MODEL_DESIGN else '正式配音'
    theme=gr.themes.Soft(primary_hue='indigo',neutral_hue='slate',font=['Microsoft YaHei UI','Arial','sans-serif'],font_mono=['Consolas','monospace'])
    row_js=Path(__file__).with_name('segment_table.js').read_text(encoding='utf-8')
    with gr.Blocks(title='Vizra Voice Studio',theme=theme,css=CSS,js=row_js) as demo:
        with gr.Row(elem_id='app-shell'):
            with gr.Column(scale=1,min_width=175,elem_id='sidebar'):
                gr.HTML('<div class="brand"><div class="brand-mark">V</div><div><strong>VIZRA</strong><small>VOICE STUDIO</small></div></div>')
                nav=gr.Radio(['音色抽卡','正式配音','音色库'],value=initial_view,show_label=False,elem_classes=['nav-radio'])
            with gr.Column(scale=7,elem_id='workspace'):
                with gr.Row(elem_id='toolbar'):
                    gr.HTML('<div class="app-title">配音工作台</div>')
                    model=gr.Dropdown(choices=choices_models(),value=saved_model,label='推理模型',elem_id='model-selector',scale=2)
                with gr.Column(visible=initial_view=='音色抽卡') as draw_view:
                    with gr.Row(elem_classes=['surface-row']):
                        with gr.Column(scale=5,min_width=330,elem_id='draw-settings'):
                            gr.HTML('<div class="section-label">声音描述</div>')
                            description=gr.Textbox(value='',placeholder='输入想要的声音特征、说话风格与情绪',show_label=False,lines=4,max_lines=5)
                            dtext=gr.Textbox(value='',placeholder='输入一小段用于试听的文字',label='试听短句',lines=2,max_lines=3)
                            with gr.Row():
                                dlang=gr.Dropdown([('中文','Chinese'),('英文','English')],value='Chinese',label='语言')
                                count=gr.Dropdown([1,3,5],value=3,label='候选数量')
                            with gr.Accordion('高级设置',open=False):
                                dtemp=gr.Slider(.3,1.2,value=.9,step=.05,label='采样温度')
                            draw_status=gr.Textbox(show_label=False,interactive=False,lines=2,value='',elem_classes=['compact-status'])
                        with gr.Column(scale=5,min_width=330,elem_id='draw-results'):
                            with gr.Row(elem_classes=['run-row']):
                                draw=gr.Button('生成候选',variant='primary',scale=3,interactive=saved_model==MODEL_DESIGN)
                                draw_stop=gr.Button('停止',variant='stop',scale=1,min_width=80)
                            draw_hint=gr.Markdown('抽卡请选择 VoiceDesign；当前模型请在“正式配音”中选择'+('预设音色。' if saved_spec.voice_mode=='preset' else '参考音色。'),visible=saved_model!=MODEL_DESIGN,elem_classes=['inline-message'])
                            candidate=gr.Dropdown(choices=audio_choices(),value=None,label='候选声音',filterable=True)
                            audio=gr.Audio(label='试听',type='filepath',interactive=False,elem_classes=['audio-panel'])
                            info=gr.Markdown('',elem_classes=['inline-message'])
                            with gr.Row(elem_classes=['save-row']):
                                name=gr.Textbox(label='音色名称',placeholder='给喜欢的声音取个名字',scale=3)
                                collect=gr.Button('保存音色',scale=1,min_width=100)
                            collect_status=gr.Markdown('',elem_classes=['inline-message'])
                            with gr.Accordion('候选记录',open=False):
                                refresh_candidates=gr.Button('刷新候选列表',size='sm')
                                ctext=gr.Textbox(label='对应文案',interactive=False,lines=2)
                                cdesc=gr.Textbox(label='音色描述',interactive=False,lines=2)
                with gr.Column(visible=initial_view=='正式配音') as formal_view:
                    with gr.Row(elem_classes=['surface-row']):
                        with gr.Column(scale=6,min_width=380,elem_id='formal-script'):
                            workflow=gr.State('生成全部')
                            script=gr.Textbox(label='配音文案',placeholder='输入配音文案，每行一段；超长行会自动拆分',lines=10,max_lines=14)
                            counter=gr.Markdown('',elem_classes=['count-label'])
                            language=gr.Dropdown([('中文','Chinese'),('英文','English')] if 'Chinese' in saved_spec.languages else [('英文','English')],value=saved_spec.languages[0],label='配音语言')
                            with gr.Accordion('输出与高级设置',open=False):
                                title=gr.Textbox(label='作品名称',value='',placeholder='输入作品名称（选填）')
                                gap=gr.Slider(0,2,value=.3,step=.05,label='片段间静音（秒）')
                                limit=gr.Slider(40,160,value=100,step=10,label='超长行拆分上限（字符）')
                                temperature=gr.Slider(.3,1.2,value=.9,step=.05,label='采样温度',visible=saved_spec.sampling)
                        with gr.Column(scale=5,min_width=330,elem_id='formal-settings'):
                            with gr.Row(elem_classes=['run-row']):
                                produce=gr.Button('生成全部片段',variant='primary',scale=3)
                                formal_stop=gr.Button('停止',variant='stop',scale=1,min_width=80)
                            with gr.Group(visible=saved_model==MODEL_DESIGN) as formal_design:
                                formal_description=gr.Textbox(label='声音描述',placeholder='输入想要的声音特征、说话风格与情绪',lines=3)
                                gr.Markdown('VoiceDesign 按描述生成，分段音色可能变化；要复用收藏音色，请选 Base 或 CosyVoice。',elem_classes=['inline-message'])
                            with gr.Group(visible=saved_spec.voice_mode=='preset') as formal_preset:
                                preset_voice=gr.Dropdown(choices=list(PRESET_VOICES),value=read_preferences().get('last_preset',PRESET_VOICES[0][1]),label='预设音色')
                            with gr.Group(visible=saved_spec.voice_mode=='reference') as formal_reference:
                                reference=gr.Dropdown(choices=favorite_choices(),value=saved_voice,label='使用音色')
                                with gr.Accordion('试听参考声音',open=False):
                                    ref_audio=gr.Audio(value=saved_audio,show_label=False,type='filepath',interactive=False)
                                    refresh_reference=gr.Button('刷新音色库',size='sm')
                            final_audio=gr.Audio(label='配音结果',type='filepath',interactive=False,elem_classes=['audio-panel'])
                            with gr.Row(elem_classes=['action-row']):
                                preview_final=gr.Button('试听整篇')
                                final_file=gr.DownloadButton('下载 WAV',value=None)
                                open_final_folder=gr.Button('打开导出文件夹',min_width=120)
                            formal_status=gr.Textbox(show_label=False,interactive=False,lines=2,value='',elem_classes=['compact-status'])
                    with gr.Accordion('项目与配音片段',open=True,elem_id='formal-segments') as segment_panel:
                        with gr.Row(elem_classes=['control-row']):
                            project=gr.Dropdown(choices=project_choices(),value=None,label='已保存项目',scale=4)
                            refresh_project=gr.Button('刷新',scale=1,min_width=80)
                            new_project_button=gr.Button('新建',scale=1,min_width=80)
                            delete_project_button=gr.Button('删除项目',variant='stop',scale=1,min_width=100)
                        delete_confirmation=gr.State(None)
                        with gr.Group(visible=False) as delete_project_panel:
                            delete_project_message=gr.Markdown('')
                            with gr.Row(elem_classes=['action-row']):
                                confirm_project_button=gr.Button('确认删除本地文件',variant='stop')
                                cancel_project_button=gr.Button('取消')
                        gr.HTML('<div class="section-label">配音片段 · 按顺序拼接</div>')
                        table=gr.HTML(rows_for({'segments':[]}),elem_id='segment-table')
                        row_edit_request=gr.Textbox(show_label=False,elem_id='segment-row-edit',elem_classes=['row-event-input'])
                        row_redo_request=gr.Textbox(show_label=False,elem_id='segment-row-redo',elem_classes=['row-event-input'])
                        segment=gr.Dropdown(choices=[],visible=False)
                        with gr.Column(visible=False,elem_id='segment-editor') as segment_editor:
                            versions=gr.Dropdown(choices=[],label='历史版本')
                            with gr.Row():
                                with gr.Column(scale=3):
                                    segment_text=gr.Textbox(label='本段说了什么',placeholder='点击表格中的文案进行修改',lines=3)
                                    redo=gr.Button('生成 / 重做这一段',variant='primary')
                                with gr.Column(scale=2):
                                    segment_audio=gr.Audio(label='历史版本试听',type='filepath',interactive=False)
                                    choose=gr.Button('使用此版本')
                        with gr.Row(elem_classes=['action-row']):
                            merge=gr.Button('拼接 / 更新整篇',variant='primary')
                            delete_final_button=gr.Button('删除整篇',variant='stop')
                            open_project_folder=gr.Button('打开项目文件夹')
                with gr.Column(visible=False) as library_view:
                    with gr.Row(elem_classes=['surface-row']):
                        with gr.Column(scale=1,min_width=330,elem_id='library-saved'):
                            gr.HTML('<div class="section-label">我的声音</div>')
                            library=gr.Dropdown(choices=favorite_choices(),value=saved_voice,label='已保存音色')
                            library_audio=gr.Audio(value=saved_audio,label='参考片段',type='filepath',interactive=False,elem_classes=['audio-panel'])
                            library_text=gr.Textbox(value=saved_text,label='对应文案',lines=4,interactive=False)
                            library_info=gr.Markdown(saved_info,elem_classes=['inline-message'])
                            with gr.Row(elem_classes=['control-row']):
                                rename_text=gr.Textbox(label='新名称',placeholder='输入新音色名称',scale=3)
                                rename_button=gr.Button('重命名',scale=1,min_width=85)
                            with gr.Row(elem_classes=['action-row']):
                                delete_voice_button=gr.Button('删除音色',variant='stop')
                                undo_voice_button=gr.Button('撤销删除')
                                refresh_library=gr.Button('刷新列表',size='sm')
                            manage_status=gr.Markdown('',elem_classes=['inline-message'])
                        with gr.Column(scale=1,min_width=330,elem_id='library-import'):
                            gr.HTML('<div class="section-label">导入参考人声</div>')
                            uploaded=gr.Audio(label='参考音频 · 建议 6～15 秒',type='filepath',sources=['upload'])
                            imported_name=gr.Textbox(label='音色名称',placeholder='输入音色名称')
                            imported_text=gr.Textbox(label='片段实际说出的文字',placeholder='输入参考音频中实际说出的文字',lines=3)
                            import_button=gr.Button('保存音色',variant='primary')
                            import_status=gr.Markdown('',elem_classes=['inline-message'])
                    with gr.Accordion('模型与使用说明',open=False):
                        model_info=gr.Markdown(model_status())
                        refresh_models=gr.Button('刷新模型列表',size='sm')
                        open_voices=gr.Button('打开音色文件夹',size='sm')
                        gr.Markdown('文案每行一段，生成后自动拼接。VoiceDesign 按描述设计声音；Base、CosyVoice 和 Chatterbox 使用参考音频；Kokoro 使用预设声音。参考声音跨模型的相似度和跨语言口音需要试听确认。')

        views=[draw_view,formal_view,library_view]
        nav.input(navigation,nav,views,queue=False)
        model.change(selected_model,[model,language],[temperature,formal_design,formal_reference,draw,draw_hint,formal_preset,language],queue=False)
        preset_voice.input(save_preset,preset_voice,queue=False)
        refresh_models.click(lambda:(gr.update(choices=choices_models()),model_status()),outputs=[model,model_info],queue=False)
        open_voices.click(lambda:open_local_folder(None,'favorites'),outputs=manage_status,queue=False)
        candidate.input(candidate_details,candidate,[audio,info,ctext,cdesc],queue=False)
        refresh_candidates.click(lambda:gr.update(choices=audio_choices()),outputs=candidate,queue=False)
        draw_event=draw.click(draw_voices,[dtext,description,dlang,dtemp,count],[candidate,audio,info,draw_status,ctext,cdesc],concurrency_id='gpu',concurrency_limit=1)
        collect.click(collect_voice,[candidate,name],[collect_status,reference,library])
        reference.change(reference_preview,reference,ref_audio,queue=False)
        refresh_reference.click(lambda:gr.update(choices=favorite_choices()),outputs=reference,queue=False)
        library.change(library_selection,library,[library_audio,library_info,library_text,reference],queue=False)
        management_outputs=[manage_status,library,reference,library_audio,library_info,library_text]
        rename_button.click(rename_saved_voice,[library,rename_text],management_outputs,queue=False)
        delete_voice_button.click(delete_saved_voice,library,management_outputs,queue=False)
        undo_voice_button.click(undo_delete_voice,outputs=management_outputs,queue=False)
        refresh_library.click(lambda:gr.update(choices=favorite_choices()),outputs=library,queue=False)
        import_button.click(import_voice,[uploaded,imported_text,imported_name],[import_status,reference,library])
        script.change(script_count,[script,limit],counter,queue=False)
        limit.input(script_count,[script,limit],counter,queue=False)
        project_outputs=[project,table,segment,segment_text,versions,segment_audio,final_audio,final_file,formal_status]
        produce_event=produce.click(generate_narration,[workflow,project,title,script,reference,language,temperature,gap,limit,model,formal_description,preset_voice],project_outputs,concurrency_id='gpu',concurrency_limit=1)
        project.input(open_project_ui,project,[title,script,reference,language,table,segment,segment_text,versions,segment_audio,final_audio,final_file,formal_status,model,formal_description,preset_voice])
        refresh_project.click(lambda:gr.update(choices=project_choices()),outputs=project,queue=False)
        new_project_button.click(new_narration,outputs=[project,title,script,table,final_audio,final_file,formal_status],queue=False)
        delete_project_button.click(ask_delete_project,project,[delete_project_message,delete_project_panel,delete_confirmation],queue=False)
        cancel_project_button.click(lambda:(gr.update(visible=False),None),outputs=[delete_project_panel,delete_confirmation],queue=False)
        confirm_project_button.click(confirm_delete_project,[project,delete_confirmation],[project,table,segment,segment_text,versions,segment_audio,final_audio,final_file,formal_status,delete_project_panel,delete_confirmation],queue=False).then(fn=None,inputs=[],outputs=[],js="() => { window.__vizraSegmentPlayer?.pause(); return []; }",queue=False)
        segment.input(load_segment,[project,segment],[segment_text,versions,segment_audio])
        row_edit_request.input(row_update,[project,row_edit_request],[table,final_file,formal_status],queue=False)
        row_redo_event=row_redo_request.input(redo_row,[project,row_redo_request,reference,language,temperature,model,formal_description,preset_voice],[segment,segment_text,versions,segment_audio,table,final_audio,final_file,script,formal_status,segment_editor],concurrency_id='gpu',concurrency_limit=1)
        row_redo_event.then(fn=None,inputs=[],outputs=[],js="() => { window.dispatchEvent(new Event('vizra-row-done')); return []; }",queue=False)
        row_redo_event.failure(fn=None,inputs=[],outputs=[],js="() => { window.dispatchEvent(new Event('vizra-row-done')); return []; }",queue=False)
        redo_event=redo.click(redo_segment,[project,segment,segment_text,reference,language,temperature,model,formal_description],[segment_audio,versions,table,final_audio,final_file,script,formal_status],concurrency_id='gpu',concurrency_limit=1)
        choose.click(pick_version,[project,segment,versions],[segment_audio,table,final_audio,final_file,formal_status])
        merge.click(merge_controls,[project,gap],[final_audio,final_file,formal_status,table])
        delete_final_button.click(clear_final,project,[final_audio,final_file,formal_status,table])
        open_project_folder.click(lambda p:open_local_folder(p,'project'),project,formal_status,queue=False)
        open_final_folder.click(lambda p:open_local_folder(p,'final'),project,formal_status,queue=False)
        preview_final.click(listen_final,project,final_audio,queue=False)
        for stop,status in [(draw_stop,draw_status),(formal_stop,formal_status)]:stop.click(ENGINE.stop,outputs=status,queue=False,cancels=[draw_event,produce_event,redo_event,row_redo_event]).then(fn=None,inputs=[],outputs=[],js="() => { window.dispatchEvent(new Event('vizra-stop')); return []; }",queue=False)
    return demo

if __name__=='__main__':
    from filelock import FileLock,Timeout
    preview_port=os.environ.get('VIZRA_PREVIEW_PORT')
    if not preview_port:
        INSTANCE_LOCK=FileLock(str(ROOT/'cache'/'server.lock'))
        try:INSTANCE_LOCK.acquire(timeout=0)
        except Timeout:
            import webbrowser
            webbrowser.open(f"http://127.0.0.1:{CONFIG.get('port',7860)}");sys.exit(0)
        save_json(ROOT/'cache'/'server.json',dict(pid=os.getpid(),script=str(Path(__file__).resolve())))
    demo=build_ui();demo.queue(default_concurrency_limit=1,max_size=8)
    demo.launch(server_name='127.0.0.1',server_port=int(preview_port or CONFIG.get('port',7860)),share=False,inbrowser=not bool(preview_port) and os.environ.get('VIZRA_OPEN_BROWSER','1')=='1',allowed_paths=[str(OUT)],show_error=True,app_kwargs=local_web_options())
