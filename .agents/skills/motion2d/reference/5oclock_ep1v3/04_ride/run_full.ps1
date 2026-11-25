# Shot 04 "Sam rides home": full render on the home Asus. Run from this folder.
# Writes into new folders full\ and fullc\ (they must not exist yet; rename old ones first).
$here = Split-Path -Parent $MyInvocation.MyCommand.Path; Set-Location $here
$out = Join-Path $here "full"; $comp = Join-Path $here "fullc"
$bl = "C:\Users\cross\Downloads\xc\blender501\blender.exe"
Start-Process -FilePath $bl -ArgumentList @("-b", "--python", "build_s04.py", "--", $out, "1.0", "all") -NoNewWindow -Wait -RedirectStandardOutput "full_build.log" -RedirectStandardError "full_build_err.log"
python paint_bg04.py (Join-Path $out "meta.json") *> paint.log
python comp_s04.py $out $comp *> full_comp.log
ffmpeg -y -loglevel error -framerate 24 -i (Join-Path $comp "%03d.png") -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p 04_ride_v4.mp4
Write-Output "DONE"
