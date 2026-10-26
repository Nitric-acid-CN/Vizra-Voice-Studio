# 参与开发

项目面向 Windows 上制作中文、英文旁白的创作者，优先保持界面简单。
先提交小范围、可验证的改动。不要把用户音频、模型、虚拟环境或缓存提交进仓库。

## 开发与检查

Python 3.12，先按 README 安装主环境。运行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q .
```

测试使用隔离临时项目与合成测试信号，不代表真实模型音质评估。
CI 执行语法与 CPU 工作流检查，不下载模型，也不假装完成 CUDA 验证。

新增引擎应在 `model_catalog.py` 声明语言、音色类型、参数能力和独立环境，
通过请求 JSON → WAV/元数据 JSON 的协议接入。记录官方来源及固定版本，
实测成功后再建立 `models/<key>.ready.json` 标记并显示在模型列表中。
不能把“支持参考声音”写成“保证音色完全一致”。

修改分段、版本或导出时，验证其他片段保留、停止后可继续、拼接确实采用选中版本。
新增依赖先使用独立环境；不能升级用户其他项目的 PyTorch 或 CUDA。

## 报告问题

提供 Windows 版本、GPU/显存、模型、复现步骤和脱敏日志。无需上传私人音色。
请区分模型音质、安装失败、推理异常和工作台界面问题。
