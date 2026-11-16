"""Reproduce the lighter playback copy; preserve all accepted/source videos.

python scripts/prepare-hero-video.py --ffmpeg ABSOLUTE_PATH_TO_FFMPEG
The encoder is a build tool, never a browser/runtime dependency.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ffmpeg',required=True);args=parser.parse_args()
    manifest=ROOT/'content/hero-media.json';media=json.loads(manifest.read_text(encoding='utf-8'))
    source=ROOT/media['output'];assert sha(source)==media['outputSha256']
    work=ROOT/'.local/hero-video-working.mp4';work.parent.mkdir(exist_ok=True)
    out=ROOT/'public/media/hero/soyuz-intro-720-efficient.mp4'
    command=[args.ffmpeg,'-hide_banner','-nostdin','-y','-i',str(source),'-map','0:v:0','-c:v','libx264','-preset','slow','-crf','23','-profile:v','main','-level:v','3.1','-pix_fmt','yuv420p','-fps_mode','passthrough','-an','-movflags','+faststart',str(work)]
    result=subprocess.run(command,capture_output=True,text=True);assert result.returncode==0,result.stderr
    result=subprocess.run([args.ffmpeg,'-hide_banner','-nostdin','-i',str(source),'-i',str(work),'-lavfi','[0:v]setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];[a][b]ssim','-an','-f','null','-'],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    quality=float(re.search(r'All:([\d.]+)',result.stderr)[1]);assert quality>=.985,quality
    assert work.stat().st_size<source.stat().st_size*.75
    work.replace(out)
    media['playback']={'url':'/media/hero/soyuz-intro-720-efficient.mp4','sha256':sha(out),'bytes':out.stat().st_size,**{key:media[key]for key in ['duration','width','height','fps','audio']},'codec':'H.264 Main level 3.1, yuv420p, faststart','encoder':'libx264 preset slow CRF23, passthrough timestamps','derivedFrom':media['output'],'sourceSha256':media['outputSha256'],'ssimAgainstAcceptedVideo':quality,'originalsPreserved':True,'generator':'scripts/prepare-hero-video.py'}
    manifest.write_text(json.dumps(media,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(media['playback'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
