import os,subprocess,webbrowser,tkinter as tk
from pathlib import Path
from tkinter import ttk,messagebox
from control import ROOT,URL,server_pid,stop_server

os.environ['PYTHONUTF8']='1'
window=tk.Tk();window.title('Vizra 配音工作台启动器');window.geometry('540x300');window.resizable(False,False)
status=tk.StringVar(value='正在检查工作台状态…')
ttk.Label(window,text='Vizra · 本地配音工作台',font=('Microsoft YaHei UI',16,'bold')).pack(pady=(22,12))
ttk.Label(window,text='本地中文 / 英文配音 · 模型按需加载').pack()
ttk.Label(window,textvariable=status,wraplength=420).pack(pady=16)

def open_page():webbrowser.open(URL)
def open_outputs():os.startfile(str(ROOT/'outputs'))
def start():
    if server_pid():open_page();return
    try:
        (ROOT/'logs').mkdir(exist_ok=True);(ROOT/'cache'/'temp').mkdir(parents=True,exist_ok=True)
        env={**os.environ,'TEMP':str(ROOT/'cache'/'temp'),'TMP':str(ROOT/'cache'/'temp'),'PYTHONUTF8':'1'}
        with (ROOT/'logs'/'web.log').open('a',encoding='utf-8') as log:
            subprocess.Popen([str(ROOT/'.venv'/'Scripts'/'python.exe'),'-u',str(ROOT/'studio.py')],cwd=ROOT,stdout=log,stderr=log,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        status.set('正在启动，浏览器会自动打开。首次加载模型在点击生成时进行。')
    except Exception as exc:messagebox.showerror('启动失败',str(exc))

def stop():
    try:stop_server();status.set('已关闭工作台，模型显存已释放。')
    except Exception as exc:messagebox.showerror('关闭失败',str(exc))

def close():stop();window.destroy()
buttons=ttk.Frame(window);buttons.pack(pady=6)
ttk.Button(buttons,text='启动工作台',command=start,width=12).grid(row=0,column=0,padx=5)
ttk.Button(buttons,text='打开网页',command=open_page,width=12).grid(row=0,column=1,padx=5)
ttk.Button(buttons,text='打开输出目录',command=open_outputs,width=12).grid(row=0,column=2,padx=5)
ttk.Button(buttons,text='关闭工作台',command=stop,width=12).grid(row=0,column=3,padx=5)
ttk.Label(window,text='关闭此启动器也会关闭工作台。文件、收藏和模型都会保留。',wraplength=420).pack(pady=16)
def refresh():
    status.set('工作台运行中 · '+URL if server_pid() else '工作台已关闭 · 点击“启动工作台”开始')
    window.after(2000,refresh)
window.protocol('WM_DELETE_WINDOW',close)
window.after(2000,refresh)
window.after(300,start)
window.mainloop()
