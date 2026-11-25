<#
.SYNOPSIS
  Self-contained runner for Shot 01 (01_hilltop, 240 frames @ 24fps, 1080x1920, seamless loop).
.USAGE
  powershell -ExecutionPolicy Bypass -File ep1\01_hilltop\src\run_full.ps1 -Version v1
#>
param(
    [string]$Version = "v1",
    [string]$Frames = "all",
    [double]$Scale = 1.0
)

$ErrorActionPreference = "Stop"
$srcDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$shotDir = Split-Path -Parent $srcDir
$projDir = Split-Path -Parent (Split-Path -Parent $shotDir)
$bgDir = Join-Path $shotDir "bg"
$verDir = Join-Path $shotDir $Version
$celDir = Join-Path $verDir "cel"
$compDir = Join-Path $verDir "comp"
$qaDir = Join-Path $verDir "qa"
$qaScript = Join-Path $projDir "..\.agents\skills\motion2d\scripts\qa_frames.py"

if (Test-Path $compDir) {
    throw "Refusing to overwrite existing output directory: $compDir. Bump -Version (e.g. v2)."
}

New-Item -ItemType Directory -Force -Path $verDir, $celDir, $compDir, $qaDir | Out-Null

Write-Host "== [1/5] Paint multi-plane sky, cumulus clouds, and grass ridge =="
python "$srcDir\paint_bg01.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "== [2/5] Build character passes (on twos) =="
python "$srcDir\build_s01.py" $celDir $Scale $Frames
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "== [3/5] Composite HDR + CRT halftone frames =="
python "$srcDir\comp_s01.py" $celDir $bgDir $compDir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "== [4/5] Run motion2d QA contact sheet & 1:1 crops =="
$cropFile = Join-Path $celDir "probe_crops.json"
if (-not (Test-Path $cropFile)) { $cropFile = Join-Path $celDir "meta.json" }
python $qaScript $compDir --crops $cropFile --n 12 --out $qaDir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($Frames -eq "all") {
    Write-Host "== [5/5] Encode CRF-14 master + CRF-18 IG deliver =="
    $masterMp4 = Join-Path $verDir "01_hilltop_$Version.mp4"
    $igMp4 = Join-Path $verDir "01_hilltop_${Version}_IG.mp4"
    ffmpeg -y -framerate 24 -i "$compDir\%03d.png" -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p $masterMp4
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    ffmpeg -y -i $masterMp4 -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p $igMp4
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Delivered: $masterMp4 and $igMp4"
} else {
    Write-Host "Probe $Version complete -> $qaDir\contact.jpg"
}

