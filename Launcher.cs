using System;
using System.IO;
using System.Diagnostics;
using System.Runtime.InteropServices;
class Launcher {
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern int MessageBox(IntPtr hwnd,string message,string title,uint flags);
  static string FindPython() {
    foreach(string executable in new string[]{"py.exe","python.exe"}) {
      try {
        string args=(executable=="py.exe"?"-3.12 ":"")+"-c \"import sys; assert sys.version_info[:2] == (3,12); print(sys.executable)\"";
        using(Process process=Process.Start(new ProcessStartInfo{FileName=executable,Arguments=args,UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true})) {
          if(!process.WaitForExit(10000)){process.Kill();continue;}
          string path=process.StandardOutput.ReadToEnd().Trim();
          if(process.ExitCode==0 && File.Exists(path))return path;
        }
      } catch {}
    }
    return null;
  }
  [STAThread] static void Main() {
    string root=AppDomain.CurrentDomain.BaseDirectory;
    if(!File.Exists(Path.Combine(root,"launcher.pyw")) && Directory.Exists(@"__INSTALL_ROOT__"))root=@"__INSTALL_ROOT__";
    string python=Path.Combine(root,".venv","Scripts","pythonw.exe");
    string script=Path.Combine(root,"launcher.pyw");
    if(!File.Exists(python)){
      string installer=Path.Combine(root,"setup_gui.pyw");string basePython=FindPython();
      if(!File.Exists(installer)||basePython==null){MessageBox(IntPtr.Zero,"请将启动器与完整源码放在同一目录，并先安装 Python 3.12（勾选 Python Launcher / 添加到 PATH）。再次启动即可打开安装窗口。","Vizra · 首次安装",16);return;}
      string pythonw=Path.Combine(Path.GetDirectoryName(basePython),"pythonw.exe");
      Process.Start(new ProcessStartInfo{FileName=File.Exists(pythonw)?pythonw:basePython,Arguments="\""+installer+"\"",WorkingDirectory=root,UseShellExecute=false,CreateNoWindow=true});return;
    }
    if(!File.Exists(script)){MessageBox(IntPtr.Zero,"启动器需与完整源码放在同一目录。","Vizra 配音工作台",16);return;}
    try{Process.Start(new ProcessStartInfo {FileName=python,Arguments="\""+script+"\"",WorkingDirectory=root,UseShellExecute=false,CreateNoWindow=true});}
    catch(Exception e){MessageBox(IntPtr.Zero,e.Message,"启动失败",16);}
  }
}
