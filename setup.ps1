param([string]$Python = 'python', [switch]$InstallCosy, [switch]$InstallEnglish, [switch]$EnglishOnly)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
$ProjectRoot = $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
& $Python -c 'import sys; assert sys.version_info[:2] == (3,12), "Python 3.12 is required"'
if ($LASTEXITCODE -ne 0) { throw 'Select Python 3.12 with -Python PATH.' }
$env:PYTHONUTF8 = '1'
$env:PIP_CACHE_DIR = Join-Path $ProjectRoot 'cache\pip'
$env:PIP_DEFAULT_TIMEOUT = '120'
$env:PIP_RETRIES = '5'

function Install-Environment([string]$Folder, [string]$Requirements) {
    $VenvPython = Join-Path $ProjectRoot "$Folder\Scripts\python.exe"
    if (!(Test-Path -LiteralPath $VenvPython)) { & $Python -m venv (Join-Path $ProjectRoot $Folder) }
    & $VenvPython -m pip install --index-url 'https://pypi.org/simple' 'setuptools<81' wheel
    if ($LASTEXITCODE -ne 0) { throw 'Build tools installation failed.' }
    & $VenvPython -m pip install 'torch==2.6.0' 'torchaudio==2.6.0' --index-url 'https://download.pytorch.org/whl/cu124'
    if ($LASTEXITCODE -ne 0) { throw 'CUDA PyTorch installation failed.' }
    & $VenvPython -m pip install --index-url 'https://pypi.org/simple' --no-build-isolation -r (Join-Path $ProjectRoot $Requirements)
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    & $VenvPython -c 'import torch; assert torch.cuda.is_available(), "CUDA is unavailable"; print(torch.cuda.get_device_name())'
    if ($LASTEXITCODE -ne 0) { throw 'CUDA verification failed.' }
}

if (!$EnglishOnly) {
    Install-Environment '.venv' 'requirements-qwen.lock.txt'
    & $Python (Join-Path $ProjectRoot 'download_models.py') 'Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign'
    if ($LASTEXITCODE -ne 0) { throw 'VoiceDesign download failed.' }
    & $Python (Join-Path $ProjectRoot 'download_models.py') 'Qwen/Qwen3-TTS-12Hz-0.6B-Base'
    if ($LASTEXITCODE -ne 0) { throw 'Base download failed.' }
}

if ($InstallCosy) {
    Install-Environment '.venv-cosy' 'requirements-cosy.lock.txt'
    & $Python (Join-Path $ProjectRoot 'fetch_engines.py')
    if ($LASTEXITCODE -ne 0) { throw 'Official engine source download failed.' }
    & $Python (Join-Path $ProjectRoot 'download_models.py') 'FunAudioLLM/Fun-CosyVoice3-0.5B-2512'
    if ($LASTEXITCODE -ne 0) { throw 'CosyVoice download failed.' }
    '{"installed":true,"validation":"Generate a short reference-based clip on this computer first."}' | Set-Content -LiteralPath (Join-Path $ProjectRoot 'models\cosyvoice.ready.json') -Encoding utf8
}
if ($InstallEnglish -or $EnglishOnly) {
    Install-Environment '.venv-english' 'requirements-english.lock.txt'
    $EnglishPython=Join-Path $ProjectRoot '.venv-english\Scripts\python.exe'
    # Official Chatterbox declares a floating Perth Git URL. The lock installs
    # pinned Perth first; --no-deps here prevents replacing it with master.
    & $EnglishPython -m pip install --no-deps 'https://github.com/resemble-ai/chatterbox/archive/5de7a54aa4e5e2baadb0182dde554908b48b85c2.zip'
    if ($LASTEXITCODE -ne 0) { throw 'Chatterbox installation failed.' }
    & $EnglishPython -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'English dependency verification failed.' }
    foreach($ModelKey in @('chatter','kokoro')) {
        & $Python (Join-Path $ProjectRoot 'download_extra_models.py') $ModelKey
        if ($LASTEXITCODE -ne 0) { throw "Model download failed: $ModelKey" }
        & $EnglishPython (Join-Path $ProjectRoot 'verify_english_install.py') $ModelKey
        if ($LASTEXITCODE -ne 0) { throw "Engine verification failed: $ModelKey" }
    }
}
& (Join-Path $ProjectRoot 'build_launcher.ps1')
Write-Output 'Installed. Double-click Vizra-Voice-Studio.exe (or start.bat).'
