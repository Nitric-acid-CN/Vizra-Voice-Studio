"""First-install UI, using the user's Python 3.12 and isolated environments."""
import os,sys,subprocess,threading,queue,tkinter as tk
from tkinter import ttk,messagebox
from pathlib import Path
ROOT=Path(__file__).resolve().parent
window=tk.Tk();window.title('Vizra Voice Studio · 首次安装');window.geometry('760x540')
ttk.Label(window,text='安装本地配音工作台',font=('Microsoft YaHei UI',17,'bold')).pack(anchor='w',padx=22,pady=(20,8))
ttk.Label(window,text='需要 Python 3.12、NVIDIA 驱动和网络。文件保存在本目录；不会改动其他项目的环境。',wraplength=710).pack(anchor='w',padx=22)
options=ttk.Frame(window);options.pack(fill='x',padx=22,pady=14)
ttk.Label(options,text='基础安装：Qwen 声音设计 + 参考克隆').grid(row=0,column=0,sticky='w')
cosy=tk.BooleanVar(value=False);english=tk.BooleanVar(value=True)
ttk.Checkbutton(options,text='选装 CosyVoice（中文 / 英文克隆）',variable=cosy).grid(row=1,column=0,sticky='w',pady=5)
ttk.Checkbutton(options,text='选装 Chatterbox + Kokoro（英文配音）',variable=english).grid(row=2,column=0,sticky='w')
status=tk.StringVar(value='基础及英文建议预留 25GB，全部引擎建议 40GB。后续启动复用本地模型。')
ttk.Label(window,textvariable=status,wraplength=710).pack(anchor='w',padx=22)
log=tk.Text(window,height=14,wrap='word',font=('Consolas',9),state='disabled');log.pack(fill='both',expand=True,padx=22,pady=12)
messages=queue.Queue();process=None;running=False
def install():
    global running
    if running:return
    if sys.version_info[:2]!=(3,12):messagebox.showerror('Python 版本','请选择 Python 3.12 运行安装器。');return
    running=True;start.configure(state='disabled');launch.configure(state='disabled')
    status.set('正在安装；模型下载可能较慢，可以查看下面的进度。')
    flags=['-InstallCosy'] if cosy.get() else []
    if english.get():flags.append('-InstallEnglish')
    def work():
        global process
        base_python=str(Path(sys.executable).with_name('python.exe'))
        command=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'setup.ps1'),'-Python',base_python,*flags]
        try:
            process=subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW,env={**os.environ,'PYTHONUTF8':'1','PYTHONUNBUFFERED':'1'})
            for line in process.stdout:messages.put(('log',line))
            messages.put(('done',process.wait()))
        except Exception as error:messages.put(('log',str(error)+'\n'));messages.put(('done',1))
    threading.Thread(target=work,daemon=True).start()
def open_studio():
    exe=ROOT/'Vizra-Voice-Studio.exe'
    if exe.exists():os.startfile(str(exe));window.destroy()
def close():
    if running and process and process.poll() is None:
        if not messagebox.askyesno('停止安装','停止当前安装？已下载的文件会保留，下次可以重试。'):return
        subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    window.destroy()
def pump():
    global running
    while not messages.empty():
        kind,value=messages.get()
        if kind=='log':log.configure(state='normal');log.insert('end',value);log.see('end');log.configure(state='disabled')
        else:
            running=False;start.configure(state='normal')
            status.set('安装完成，可以启动工作台。首次生成会加载模型。' if value==0 else '安装未完成。请查看日志，修复后可重新安装，已下载文件会复用。')
            launch.configure(state='normal' if value==0 else 'disabled')
    window.after(150,pump)
buttons=ttk.Frame(window);buttons.pack(fill='x',padx=22,pady=(0,18))
start=ttk.Button(buttons,text='开始安装',command=install);start.pack(side='left')
launch=ttk.Button(buttons,text='启动工作台',command=open_studio,state='disabled');launch.pack(side='left',padx=10)
ttk.Button(buttons,text='关闭',command=close).pack(side='right')
window.protocol('WM_DELETE_WINDOW',close);window.after(150,pump);window.mainloop()
