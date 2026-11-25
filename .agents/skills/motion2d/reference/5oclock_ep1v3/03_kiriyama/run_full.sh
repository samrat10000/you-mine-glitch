cd "$(dirname "$0")"
rm -rf full fullc
python3 build_s03.py full 1.0 all > full_build.log 2>&1 && python3 comp_s03.py full fullc > full_comp.log 2>&1 && \
ffmpeg -y -loglevel error -framerate 24 -i fullc/%03d.png -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p 03_kiriyama_v2.mp4 && echo DONE
