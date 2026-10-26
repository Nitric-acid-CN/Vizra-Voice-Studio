# Vizra Voice Studio

**Turn a script into a voiceover you want to keep.**

[简体中文](../README.md) · English

[Download preview](https://github.com/Nitric-acid-CN/Vizra-Voice-Studio/releases) · [Workflow](#a-simple-workflow) · [Models](#choose-a-model) · [Test samples](samples/)

A local voiceover workspace for video creators. Explore a voice, save a reference, generate your script line by line, and redo only the parts you want to change. Export a lossless WAV for Premiere Pro or your favorite video editor.

**Preview 0.2.0 · Windows / NVIDIA first · Chinese interface · Chinese and English speech.**

The bilingual documentation does not mean the app interface is translated into English yet.

![Voiceover workspace using isolated test content](workbench.png)

| Explore | Create | Refine | Export |
| --- | --- | --- | --- |
| Audition short voice candidates and save a named reference | Paste a script; each nonempty line becomes a segment | Edit, listen, regenerate and choose versions in the same table | Merge into a 48kHz lossless WAV |

Built around official open-source TTS engines. This project provides the workflow, not a newly trained speech model. One model and one generation job run at a time. The web interface binds to `127.0.0.1`; your voices, scripts and projects stay on your computer.

## Get started

1. Install **Python 3.12** with the Python Launcher / PATH option, and an NVIDIA driver.
2. Download the **Windows preview ZIP** from [Releases](https://github.com/Nitric-acid-CN/Vizra-Voice-Studio/releases) and extract it to its own folder.
3. Open **Vizra-Voice-Studio.exe**. On first use, choose optional engines in the installation window and follow the progress log.
4. Once installed, use the same launcher to start the workspace, open its output folder, or stop the service.

The ZIP includes source and a small launcher, **not Python, model weights or a bundled runtime**. Initial setup needs internet access. After all required assets are installed, inference can run offline. Closing the launcher stops its service and releases the model; saved work remains on disk.

### Hardware

- Windows 10/11 x64; NVIDIA CUDA GPU. The tested machine has an RTX 3060 Laptop GPU with 6GB VRAM.
- Python 3.12; 16GB RAM recommended.
- Allow about 25GB free for the basic and English setup, or 40GB for all engines and caches.
- Model compatibility and memory use vary. A full clean-machine installation has not yet been verified on a second computer.

<details>
<summary>Install from source with PowerShell</summary>

Run these commands from the extracted project folder. If `python` is not Python 3.12, replace it with the full path to that interpreter.

```powershell
# Base setup: Qwen VoiceDesign and Base.
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -Python python

# Optional CosyVoice environment.
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -Python python -InstallCosy

# Add English engines to an existing installation.
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -Python python -EnglishOnly
```

Alternatively, open `setup_gui.pyw` with Python 3.12. The installer creates project-local environments and verifies CUDA; it does not upgrade other projects' Python, CUDA or PyTorch environments.

</details>

## A simple workflow

1. **Explore a voice.** Select Qwen VoiceDesign, enter a short audition line and a voice description, then generate 1, 3 or 5 candidates sequentially. Listen, name and save the one you like.
2. **Generate your narration.** Select a reference-based engine and a saved voice, then paste your script. Every nonempty line is a segment; long lines are split further at sentence or word boundaries. The script limit is 12,000 characters; start small while choosing a voice.
3. **Refine one part.** Edit the text directly in its table row and click regenerate. Other segments remain intact. Choose the take you want from that row's version menu.
4. **Update the full recording.** A changed segment marks the merged export as out of date. Merge again to replace the same full-length export, then download it or open its local folder.

Background generation does not automatically switch the audio you are auditioning. Finished segments are saved individually. With the same script, model and voice, interrupted projects can skip already completed segments when resumed.

Unsubmitted row edits are temporary browser drafts. Regenerate successfully before treating an edit as saved.

### Interface labels

| Chinese label | Meaning |
| --- | --- |
| 音色抽卡 | Explore voice candidates |
| 正式配音 | Narration workspace |
| 音色库 | Saved voice library |
| 生成全部片段 | Generate all segments |
| 重做 / 使用版本 | Regenerate / choose a version |
| 拼接 / 更新整篇 | Merge / update full narration |

## Choose a model

| Model | Languages exposed by this app | Voice source | Use case |
| --- | --- | --- | --- |
| Qwen VoiceDesign 1.7B | Chinese, English | Text description | Explore a new voice |
| Qwen Base 0.6B | Chinese, English | Reference audio and transcript | Reuse a saved voice |
| CosyVoice3 0.5B | Chinese, English | Reference audio and transcript | Try another cloning engine |
| Chatterbox-Turbo | English | Reference audio | English cloning; official Perth watermark retained |
| Kokoro 82M | English, US/UK presets | Six preset voices | Fast narration without a reference |

The interface shows controls relevant to the selected engine. VoiceDesign does not lock identity using a seed or a written description: save a sample and use a cloning engine for reuse. Reference-based synthesis also cannot guarantee identical identity, accent or delivery across models and languages. Audition the result before committing to a full script.

English narration requires an English script; automatic translation is not included.

## Tested on a 6GB GPU

English short-sentence results on an RTX 3060 Laptop 6GB, CUDA PyTorch 2.6.0+cu124:

| Model | Audio duration | Inference time | Peak allocated VRAM |
| --- | ---: | ---: | ---: |
| Qwen VoiceDesign | 5.36s | 11.41s | 4.05 GiB |
| Qwen Base | 5.04s | 12.18s | 2.36 GiB |
| CosyVoice3 | 6.68s | 5.81s | 3.28 GiB |
| Chatterbox-Turbo | 5.28s | 14.79s | 2.73 GiB |
| Kokoro | 7.05s | 1.52s | 0.67 GiB |

Times exclude model loading. Allocated VRAM excludes some CUDA overhead. These are measurements from one machine, not a guarantee for every script or GPU. English test outputs matched the input words in an offline ASR check; automated checks are not a naturalness rating.

Real GPU integration also passed a two-segment generation → first-segment retake → updated merge workflow. The untouched second segment retained its file hash. The final WAV was 48kHz/24-bit PCM with the requested inter-segment silence.

[Public WAV samples](samples/) · [Machine-readable results](validation.json) · [Detailed validation, Chinese](VALIDATION.md)

## Files and saved work

```text
outputs/
  candidates/       Voice auditions
  favorites/        Reference WAV files and voice metadata
  segments/         Projects, individual segments and take history
  final/            Full narration exports
  preferences.json  Last selected voice, model and preset
```

- Merged exports are properly resampled **48kHz, 24-bit PCM WAV**, not files with a relabeled sample rate.
- Deleting a merged export preserves the segments. Project deletion requires confirmation and removes its local segment files and associated exports, while preserving saved voices.
- Voice deletion is an undoable library removal; reference files remain to protect existing projects.
- Virtual environments are machine-specific. A folder backup is not a universal portable installation.

## Scope and contributing

This preview focuses on a simple narration workflow. It does not include a multi-track timeline, subtitle alignment, automatic video translation or transcription import. The app does not claim Mac/Linux support, perfect long-form speech or a locked cross-language identity.

Similar projects already cover broader workflows. See the [comparison](COMPARISON.md) for tradeoffs rather than treating this app as the only local TTS option.

The workbench code uses the [MIT license](../LICENSE). Engines, weights and dependencies retain their own terms; see [third-party notices](../THIRD_PARTY.md). Only purpose-generated public samples are included. Private voices, projects, model weights, caches and virtual environments are excluded from release archives.

[Contributing](../CONTRIBUTING.md) · [Privacy and security](../SECURITY.md)

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe diagnose.py
```

CI checks CPU workflow integrity, not GPU compatibility. Remove private information before sharing logs from `logs/`.
