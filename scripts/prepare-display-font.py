"""Create an unhinted web copy of the supplied Molot; outlines/advances stay intact.

python -m pip install --target .local/font-tools -r scripts/requirements-fonts.txt
python scripts/prepare-display-font.py
"""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.local/font-tools'))
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_a_s_p import table__g_a_s_p

def outline_signature(font):
    shapes={}
    for name in font.getGlyphOrder():
        glyph=font['glyf'][name]
        if glyph.numberOfContours:
            coords,ends,flags=glyph.getCoordinates(font['glyf'])
            shapes[name]=[list(coords),list(ends),list(flags)]
    return hashlib.sha256(json.dumps(shapes,sort_keys=True).encode()).hexdigest()

def main():
    source=ROOT/'public/fonts/Molot.ttf';out=ROOT/'public/fonts/Molot-UI.ttf'
    font=TTFont(source,recalcTimestamp=False)
    before=outline_signature(font);metrics=dict(font['hmtx'].metrics)
    font['glyf'].removeHinting()
    for tag in ('fpgm','prep','cvt ','hdmx','LTSH','VDMX'):
        if tag in font:del font[tag]
    font['head'].flags &= ~(8|16)
    font['gasp']=table__g_a_s_p('gasp');font['gasp'].gaspRange={65535:10}
    for record in font['name'].names:
        value={1:'Molot SOYUZ UI',3:'MolotSOYUZUI-Unhinted',4:'Molot SOYUZ UI',6:'MolotSOYUZUI'}.get(record.nameID)
        if value:record.string=value.encode(record.getEncoding())
    font.save(out)
    verified=TTFont(out)
    assert outline_signature(verified)==before and dict(verified['hmtx'].metrics)==metrics
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    manifest={'source':'public/fonts/Molot.ttf','sourceSha256':sha(source),'output':'public/fonts/Molot-UI.ttf','sha256':sha(out),'generator':'scripts/prepare-display-font.py','fontToolsVersion':'4.68.0','outlineSignature':before,'outlinesAndAdvancesUnchanged':True,'operation':'Remove legacy TrueType pixel-grid instructions and integer-ppem forcing; preserve original glyph contours, widths, kerning, Cyrillic accents and percent. Rename derived internal family, retain copyright.','capHeight':1434,'unitsPerEm':verified['head'].unitsPerEm}
    (ROOT/'content/display-font.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Prepared unhinted Molot UI: {out.stat().st_size} bytes; outlines and advances verified unchanged.')
if __name__=='__main__':main()
