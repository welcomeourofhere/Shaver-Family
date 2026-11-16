"""Add the standard no-break-space mapping to derived Manrope web copies.

Original files, glyph contours, instructions, advances and kerning stay intact.
Uses the same pinned build-only fontTools as prepare-display-font.py.
"""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.local/font-tools'))
from fontTools.ttLib import TTFont
from importlib.util import spec_from_file_location,module_from_spec
spec=spec_from_file_location('display_font',ROOT/'scripts/prepare-display-font.py');display=module_from_spec(spec);spec.loader.exec_module(display)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    rows=[]
    for weight in ['Regular','Medium','SemiBold']:
        source=ROOT/f'public/fonts/Manrope-{weight}.woff2';output=ROOT/f'public/fonts/Manrope-{weight}-UI.woff2'
        font=TTFont(source,recalcTimestamp=False);outlines=display.outline_signature(font);metrics=dict(font['hmtx'].metrics);cmap=font.getBestCmap().copy()
        for table in font['cmap'].tables:
            if table.isUnicode():table.cmap[0xA0]=table.cmap[0x20]
        for record in font['name'].names:
            value={1:'Manrope SOYUZ UI',3:f'ManropeSOYUZUI-{weight}',4:f'Manrope SOYUZ UI {weight}',6:f'ManropeSOYUZUI-{weight}',16:'Manrope SOYUZ UI'}.get(record.nameID)
            if value:record.string=value.encode(record.getEncoding())
        font.save(output);verified=TTFont(output)
        assert display.outline_signature(verified)==outlines and dict(verified['hmtx'].metrics)==metrics
        assert verified.getBestCmap()=={**cmap,0xA0:cmap[0x20]}
        rows.append({'source':str(source.relative_to(ROOT).as_posix()),'sourceSha256':sha(source),'output':str(output.relative_to(ROOT).as_posix()),'sha256':sha(output),'outlineSignature':outlines,'outlinesAndAdvancesUnchanged':True})
    (ROOT/'content/body-fonts.json').write_text(json.dumps({'generator':'scripts/prepare-body-fonts.py','fontToolsVersion':'4.68.0','operation':'Map U+00A0 to the existing U+0020 space glyph in Unicode cmaps; rename derived internal family; retain copyright, outlines, advances, instructions and kerning.','fonts':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Prepared three Manrope UI copies; original glyphs/metrics and all prior Unicode mappings verified unchanged.')
if __name__=='__main__':main()
