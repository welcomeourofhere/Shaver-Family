"""Export only the 29 selected, replaceable service photos from the owner photoset."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('J:/Brandbooks/brand book СОЮЗ Барбершоп 2025/07_Фотографии/Фотосет 2025 №1').resolve()
FILES=['170A0121.jpg','170A0294.jpg','170A1097.jpg','170A0100.jpg','170A0550.jpg','170A1317.jpg','170A0019.jpg','170A0756.jpg','170A0076.jpg','170A0491.jpg','170A1178.jpg','170A1349.jpg','170A1383.jpg','170A1287.jpg','170A1652.jpg','170A1209.jpg','170A1931.jpg','170A1242.jpg','170A0725.jpg','170A1875.jpg','170A0409.jpg','170A1507.jpg','170A1010.jpg','170A9999.jpg','170A1053.jpg','170A1722.jpg','170A1832.jpg','170A1962.jpg','170A0225.jpg']
def main():
    services=[s for c in json.loads((ROOT/'content/service-catalog.json').read_text(encoding='utf-8'))['categories'] for s in c['services']]
    assert len(services)==len(FILES)==len(set(FILES))
    sources=[(SOURCE/name).resolve(strict=True) for name in FILES]
    assert all(p.is_relative_to(SOURCE) and p.is_file() for p in sources)
    target=ROOT/'public/media/services';target.mkdir(parents=True,exist_ok=True)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    existing=json.loads((ROOT/"content/service-photos.json").read_text(encoding="utf-8"))["images"]
    entries={}
    for service,path in zip(services,sources):
        with Image.open(path) as raw:
            im=ImageOps.exif_transpose(raw).convert('RGB');variants=[]
            for width in (480,960):
                w=min(width,im.width);size=(w,round(im.height*w/im.width));out=target/f'{service["id"]}-{width}.webp'
                im.resize(size,Image.Resampling.LANCZOS).save(out,'WEBP',quality=82,method=6)
                variants.append({'url':'/'+out.relative_to(ROOT/'public').as_posix(),'width':size[0],'height':size[1],'sha256':sha(out),'bytes':out.stat().st_size})
            entries[service['id']]={'source':str(path),'sourceSha256':sha(path),'alt':existing[service['id']]['alt'],'altSource':existing[service['id']].get('altSource','owner'),'temporary':True,'variants':variants}
    (ROOT/'content/service-photos.json').write_text(json.dumps({'asOf':'2026-11-05','status':'owner-authorized-temporary-photos-replaceable-per-service','generator':'scripts/prepare-service-photos.py','images':entries},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Exported {len(entries)} distinct service photos, 58 responsive files.')
if __name__=='__main__':main()
