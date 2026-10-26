param([switch]$Portable)
$ErrorActionPreference='Stop'
$AppRoot=$PSScriptRoot
$Compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if(!(Test-Path -LiteralPath $Compiler)){$Compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe'}
$BuildFolder=Join-Path $AppRoot 'cache\launcher-build'
New-Item -ItemType Directory -Path $BuildFolder -Force | Out-Null
$FallbackRoot=if($Portable){''}else{$AppRoot}
$Source=(Get-Content -LiteralPath (Join-Path $AppRoot 'Launcher.cs') -Raw).Replace('__INSTALL_ROOT__',$FallbackRoot)
$SourceFile=Join-Path $BuildFolder 'Launcher.cs'
Set-Content -LiteralPath $SourceFile -Value $Source -Encoding utf8
& $Compiler /nologo /target:winexe "/out:$(Join-Path $AppRoot 'Vizra-Voice-Studio.exe')" $SourceFile
if($LASTEXITCODE -ne 0){throw 'Launcher build failed.'}
