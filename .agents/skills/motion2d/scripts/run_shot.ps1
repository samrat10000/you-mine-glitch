# Render one shot end to end at BelowNormal priority, timing each step. Run from the shot's src folder.
# usage: powershell -File run_shot.ps1 -Build build_sNN.py -Comp comp_sNN.py -Name NN_name_vN [-Frames all] [-Scale 1.0]
#        [-PaintCmd "paint_bgNN.py full\meta.json"] [-CompArgs "full fullc"]   (check each script's usage line)
param([string]$Build, [string]$Comp, [string]$Name, [string]$Frames = 'all', [string]$Scale = '1.0',
      [string]$PaintCmd = '', [string]$CompArgs = '', [string]$Blender = 'C:\Users\cross\Downloads\xc\blender501\blender.exe')
$ErrorActionPreference = 'Stop'; Set-Location (Get-Location)
foreach ($d in 'full', 'fullc') { if (Test-Path $d) { $i = 1; while (Test-Path "${d}_v$i") { $i++ }; Rename-Item $d "${d}_v$i"; "kept old $d as ${d}_v$i" } }
$out = Join-Path (Get-Location) 'full'; $comp = Join-Path (Get-Location) 'fullc'
function Low($exe, $argList, $log) {
  $t = Get-Date; $p = Start-Process $exe -ArgumentList $argList -NoNewWindow -PassThru -RedirectStandardOutput $log -RedirectStandardError "$log.err"
  $null = $p.Handle; $p.PriorityClass = 'BelowNormal'; $p.WaitForExit()
  "$log  $([math]::Round(((Get-Date) - $t).TotalSeconds, 1)) s  exit $($p.ExitCode)"
  if ($p.ExitCode -ne 0) { throw "$exe failed: see $log.err" }
  if (Select-String -Path $log, "$log.err" -Pattern 'Traceback' -Quiet) { throw "Traceback in $log" }
}
Low $Blender @('-b', '--python', $Build, '--', $out, $Scale, $Frames) build.log
"cels: $((Get-ChildItem $out -Filter cel_*.png).Count)"
if ($PaintCmd) { Low python ($PaintCmd -split ' ') paint.log }
$ca = if ($CompArgs) { $CompArgs -split ' ' } else { @($out, $comp) }
Low python (@($Comp) + $ca) comp.log
"comp frames: $((Get-ChildItem $comp -Filter *.png).Count)"
ffmpeg -y -loglevel error -framerate 24 -i "$comp\%03d.png" -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p "$Name.mp4"
"$Name.mp4  $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$Name.mp4") s  $((Get-Item "$Name.mp4").Length) bytes"
