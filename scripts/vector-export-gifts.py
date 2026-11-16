"""Extract six original gift drawings from a native CorelDRAW SVG export.

Input is exported from a writable copy of the CDR through CorelDRAW's UI.
No tracing, replacement artwork, source-library edits or bitmap embeds.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("J:/Brandbooks/brand book СОЮЗ Барбершоп 2025/06_Цифровое пространство/Иконки/Набор иконок.cdr")
EXPECTED_SOURCE_SHA256 = "25487e12a42730517f97fe25ee54ff4ad5d7a9400171838d769ad1d0172bb664"
NATIVE = ROOT / "tmp/vector-export-tools/native-icons.svg"
WORK = ROOT / "tmp/vector-export-gifts"
OUT = ROOT / "public/reference"
NS = "http://www.w3.org/2000/svg"
S = "{" + NS + "}"
X = "{http://www.w3.org/1999/xlink}"
ET.register_namespace("", NS)
ET.register_namespace("xlink", X[1:-1])
# Direct children of the original Corel layer, visually verified against its thumbnail.
SELECTIONS = [
    (1, "Фирменный стикерпак", [46], (6600.01, 0)),
    (2, "Памятный магнит", [35, 37, 38, 40], (5500.01, 0)),
    (3, "Полезный брелок", [33], (4400.01, 1100)),
    (4, "Ароматизатор в машину", [31], (3300, 1100)),
    (5, "Секретный подарок", [24], (1100, 1100)),
    (6, "Укладочное средство", [27], (2200, 1100)),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def references(element):
    result = set()
    for node in element.iter():
        for key, value in node.attrib.items():
            result.update(re.findall(r"url\(#([^)]+)\)", value))
            if key in ("href", X + "href") and value.startswith("#"):
                result.add(value[1:])
    return result


def verify(svg):
    allowed = {"svg", "defs", "g", "path", "rect", "polygon", "polyline", "line", "circle", "ellipse", "linearGradient", "radialGradient", "stop", "clipPath", "mask"}
    ids = {node.get("id") for node in svg.iter() if node.get("id")}
    assert len(ids) == sum(bool(node.get("id")) for node in svg.iter()), "Duplicate SVG definition id"
    counts = {}
    for node in svg.iter():
        name = node.tag.split("}")[-1]
        assert name in allowed, f"Unexpected/non-vector SVG element: {name}"
        counts[name] = counts.get(name, 0) + 1
        for key, value in node.attrib.items():
            assert not key.lower().startswith("on"), "Event handler in SVG"
            assert "data:" not in value and "http:" not in value and "https:" not in value
            if key in ("href", X + "href"):
                assert value.startswith("#") and value[1:] in ids
        assert references(node).issubset(ids), "Missing local definition"
    assert counts.get("path", 0) > 0
    assert svg.get("viewBox")
    return counts


def main():
    assert digest(SOURCE) == EXPECTED_SOURCE_SHA256, "Source CDR changed; inspect before re-exporting"
    native = ET.parse(NATIVE).getroot()
    layer = list(native)[1]
    native_defs = native.find(S + "defs")
    style = native_defs.find(S + "style")
    rules = dict(re.findall(r"\.([\w-]+)\s*\{([^}]+)\}", style.text or ""))
    # Inline the native CSS declarations without changing their values.
    for node in native.iter():
        classes = node.attrib.pop("class", "").split()
        if classes:
            node.set("style", ";".join(rules.get(name, "") for name in classes) + ";" + node.get("style", ""))
    definitions = {node.get("id"): node for node in native_defs.iter() if node.get("id")}
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    prepared = []
    manifest = {"status": "verified-native-vector-export", "source": str(SOURCE), "sourceSha256": digest(SOURCE), "nativeExport": str(NATIVE.relative_to(ROOT)), "nativeExportSha256": digest(NATIVE), "method": "CorelDRAW native SVG 1.1 export via UI from a writable CDR copy; original source drawings and gradients extracted without tracing", "omitted": "Original tile backgrounds and Corel raster-only soft-shadow layers excluded. The complete vector object bodies, fills, gradients and geometry are retained.", "icons": []}
    for number, title, indices, origin in SELECTIONS:
        svg = ET.Element(S + "svg", {"version": "1.1", "viewBox": f"{origin[0]} {origin[1]} 1000 1000", "width": "1000", "height": "1000", "fill-rule": "evenodd", "clip-rule": "evenodd"})
        defs = ET.SubElement(svg, S + "defs")
        artwork = ET.SubElement(svg, S + "g")
        source_ids = []
        removed_images = 0
        for index in indices:
            original = layer[index]
            source_ids.append(original.get("id") or f"layer-child-{index}")
            node = copy.deepcopy(original)
            parents = {child: parent for parent in node.iter() for child in parent}
            for image in list(node.iter(S + "image")):
                parents[image].remove(image)
                removed_images += 1
            artwork.append(node)
        required = references(artwork)
        included = set()
        while required - included:
            key = sorted(required - included)[0]
            node = copy.deepcopy(definitions[key])
            assert not list(node.iter(S + "image")), "Raster-dependent definition requires manual inspection"
            defs.append(node)
            included.update(child.get("id") for child in node.iter() if child.get("id"))
            required.update(references(node))
        verify(svg)
        candidate = WORK / f"gift-{number}-stage.svg"
        ET.ElementTree(svg).write(candidate, encoding="utf-8", xml_declaration=True)
        prepared.append((number, title, indices, source_ids, origin, svg, candidate, removed_images))

    # Existing project dependency sharp measures alpha bounds; it does not trace or rewrite paths.
    js = """import sharp from 'sharp';
const files = JSON.parse(process.argv[1]); const result=[];
for (const file of files) { const {data, info} = await sharp(file).ensureAlpha().raw().toBuffer({resolveWithObject:true});
let left=info.width, top=info.height, right=0, bottom=0;
for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++)if(data[(y*info.width+x)*4+3]){left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x+1);bottom=Math.max(bottom,y+1);}
result.push([left,top,right,bottom]);} process.stdout.write(JSON.stringify(result));"""
    bounds = json.loads(subprocess.check_output(["node", "--input-type=module", "-e", js, json.dumps([str(item[6]) for item in prepared])], cwd=ROOT, text=True))
    for item, box in zip(prepared, bounds):
        number, title, indices, source_ids, origin, svg, candidate, removed_images = item
        left, top, right, bottom = box
        assert 0 < right - left < 900 and 0 < bottom - top < 900, "Unexpected object bounds/background"
        width, height = right - left + 4, bottom - top + 4
        svg.set("viewBox", f"{origin[0] + left - 2:.2f} {origin[1] + top - 2:.2f} {width} {height}")
        svg.set("width", str(width))
        svg.set("height", str(height))
        counts = verify(svg)
        target = OUT / f"gift-{number}.svg"
        ET.ElementTree(svg).write(target, encoding="utf-8", xml_declaration=True)
        manifest["icons"].append({"id": number, "title": title, "url": f"/reference/gift-{number}.svg", "sourceLayerChildIndices": indices, "sourceElementIds": source_ids, "viewBox": svg.get("viewBox"), "width": width, "height": height, "bytes": target.stat().st_size, "sha256": digest(target), "elementCounts": counts, "embeddedImages": 0, "externalReferences": 0, "omittedRasterShadowElementsInsideBody": removed_images})
    (ROOT / "content/gift-vector-sources.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Verified six original SVG drawings: paths, original fills/gradients, tight viewBox, no bitmap or external reference.")


if __name__ == "__main__":
    main()
