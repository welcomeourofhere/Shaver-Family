"""Build the local offer illustrations from native brand vectors and new SVG shapes.

The native export and gift vectors are read only. Run --check to verify that the
checked-in illustrations and provenance manifest are reproducible.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "tmp/vector-export-tools/native-icons.svg"
EXPECTED_NATIVE = "7c5b8ee767899fb810c3389a9f2978007b60b248e58e67ad54c4b22e6019c7fc"
NS = "http://www.w3.org/2000/svg"
S = "{" + NS + "}"
X = "{http://www.w3.org/1999/xlink}"
ET.register_namespace("", NS)
ET.register_namespace("xlink", X[1:-1])

# These objects and their original gradients are selected from the first row set.
NATIVE_OBJECTS = {
    "first-visit": ("Ракета — первый старт", [43], (5500.01, 1100)),
    "loyalty": ("Подарочная коробка", [24], (1100, 1100)),
    "veterans": ("Объёмная пятиконечная звезда", [9, 10, 11], (0, 0)),
    "premium": ("Открытая банка укладочного средства", [27], (2200, 1100)),
}

# New artwork uses the source palette and faceted / gradient object construction.
# It is deliberately recorded as new artwork, never as a native brandbook export.
GRADIENTS = """
<linearGradient id="red" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#E13B38"/><stop offset=".5" stop-color="#C62C2A"/><stop offset="1" stop-color="#8D1D1D"/></linearGradient>
<linearGradient id="redSide" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#B72827"/><stop offset="1" stop-color="#8D1D1D"/></linearGradient>
<linearGradient id="blue" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#7588AA"/><stop offset=".45" stop-color="#52658C"/><stop offset="1" stop-color="#1E335C"/></linearGradient>
<linearGradient id="blueSide" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#52658C"/><stop offset="1" stop-color="#1E335C"/></linearGradient>
<linearGradient id="gold" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#FFE17A"/><stop offset=".45" stop-color="#FFCC29"/><stop offset="1" stop-color="#D47C08"/></linearGradient>
<linearGradient id="goldSide" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#E7A915"/><stop offset="1" stop-color="#B76B0D"/></linearGradient>
<linearGradient id="cream" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#FFF6E8"/><stop offset=".55" stop-color="#F6E8D3"/><stop offset="1" stop-color="#CCB28A"/></linearGradient>
<linearGradient id="creamSide" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#F6E8D3"/><stop offset="1" stop-color="#D7BF99"/></linearGradient>
"""

ARTWORK = {
    "coffee": ("Стакан кофе с собой", "New tapered takeaway cup, blue lid, cream sleeve and raised star; source palette and gradient direction.", """
<g transform="rotate(-8 256 270)">
 <path fill="url(#redSide)" d="M153 182h222l-24 241q-94 35-172-4z"/>
 <path fill="url(#red)" d="M141 180h222l-24 239q-88 30-174-3z"/>
 <path fill="#F05248" d="m151 189 19 214q7 10 17 12l-14-223z" opacity=".65"/>
 <path fill="url(#creamSide)" d="m153 256 202 4-8 89q-93 29-184-4z"/>
 <path fill="url(#cream)" d="M153 252q103 25 203 2l-7 80q-96 27-188-4z"/>
 <path fill="url(#blueSide)" d="M127 159q128-31 256 0v34q-128 38-256 0z"/>
 <ellipse fill="url(#blue)" cx="255" cy="158" rx="128" ry="31"/>
 <path fill="url(#blueSide)" d="M150 145v-24q105-33 210 0v24q-105 29-210 0z"/>
 <ellipse fill="url(#blue)" cx="255" cy="122" rx="105" ry="27"/>
 <path fill="#8F9DB8" d="M172 118q73-19 141-5" stroke="#8F9DB8" stroke-width="6" stroke-linecap="round"/>
 <path fill="#1E335C" d="M300 124q18-4 28 0l-1 8q-14-3-27 0z"/>
 <path fill="url(#red)" d="m255 267 11 22 25 4-18 18 4 25-22-12-23 12 4-25-18-18 25-4z"/>
 <path fill="#EF5A49" d="m255 267 0 37-12-15z"/>
</g>
<path fill="none" stroke="url(#creamSide)" stroke-width="10" stroke-linecap="round" d="M213 91c-23-23 24-32 2-55M278 86c-23-23 24-32 2-55"/>
"""),
    "cashback": ("Стопка монет и возвратная стрелка", "New stacked coins with thick rims, bevels and a curved return arrow; no numerals or offer conditions are embedded.", """
<g>
 <path fill="url(#goldSide)" d="M88 323v36c0 32 59 59 132 59s132-27 132-59v-36z"/>
 <ellipse fill="url(#gold)" cx="220" cy="323" rx="132" ry="59"/>
 <ellipse fill="none" stroke="#FFE684" stroke-width="7" cx="220" cy="321" rx="105" ry="42"/>
 <path fill="url(#goldSide)" d="M88 282v30c0 32 59 59 132 59s132-27 132-59v-30z"/>
 <ellipse fill="url(#gold)" cx="220" cy="282" rx="132" ry="59"/>
 <ellipse fill="none" stroke="#FFE684" stroke-width="7" cx="220" cy="280" rx="105" ry="42"/>
 <g transform="rotate(-18 307 229)">
  <path fill="url(#goldSide)" d="M217 148c-48 44-48 125 0 169l20 14c49 40 119 19 147-40s9-131-40-160c-43-27-91-16-127 17z"/>
  <ellipse fill="url(#gold)" cx="298" cy="222" rx="91" ry="113"/>
  <ellipse fill="none" stroke="#FFE684" stroke-width="8" cx="298" cy="222" rx="71" ry="91"/>
  <path fill="url(#red)" d="M333 188c-15-29-51-36-72-11l-11-8 2 48 39-21-13-5c11-10 28-7 36 7z"/>
  <path fill="url(#redSide)" d="M263 253c15 28 50 34 72 10l11 8-2-48-39 21 13 5c-12 11-28 7-36-7z"/>
 </g>
</g>
"""),
    "waxing": ("Восковая ванночка и аппликатор", "New open wax pot with golden wax and wooden applicator. It is not a cosmetic jar extracted from the source.", """
<g>
 <path fill="url(#blueSide)" d="M102 255v119c0 37 61 67 137 67s137-30 137-67V255z"/>
 <path fill="url(#blue)" d="M102 259v104c0 37 61 67 137 67V319z"/>
 <ellipse fill="url(#blue)" cx="239" cy="255" rx="137" ry="65"/>
 <ellipse fill="#1E335C" cx="239" cy="253" rx="119" ry="49"/>
 <ellipse fill="url(#gold)" cx="239" cy="258" rx="111" ry="41"/>
 <path fill="#FFE684" d="M153 247c21-16 64-24 98-17-43 0-64 11-72 19z"/>
 <path fill="url(#cream)" d="M174 332q65 20 130 0v45q-65 23-130 0z"/>
 <path fill="url(#gold)" d="M238 338c-6 16-22 31-22 43a22 22 0 0 0 44 0c0-12-16-27-22-43z"/>
 <g transform="rotate(28 326 183)">
  <rect fill="url(#creamSide)" x="310" y="65" width="43" height="222" rx="21"/>
  <rect fill="url(#cream)" x="301" y="61" width="43" height="222" rx="21"/>
  <path fill="url(#redSide)" d="M301 180q19 10 43 0v80q0 39-22 39t-21-39z"/>
  <path fill="url(#gold)" d="M301 182q19 10 43 0v68q0 31-22 31t-21-31z"/>
  <path fill="#FFE684" d="M309 195v57q0 12 5 16V197z"/>
 </g>
 <path fill="none" stroke="#7588AA" stroke-width="6" stroke-linecap="round" d="M124 306q35 18 66 20"/>
</g>
"""),
    "father-son": ("Два барберских кресла", "New adult and child barber chairs at different scales; red and blue upholstery, cream armrests and dimensional metal bases.", """
<g transform="translate(35 58)">
 <path fill="url(#blueSide)" d="M117 306h31v58h-31z"/>
 <ellipse fill="url(#blueSide)" cx="132" cy="368" rx="85" ry="24"/>
 <ellipse fill="url(#blue)" cx="132" cy="360" rx="85" ry="23"/>
 <rect fill="url(#creamSide)" x="115" y="283" width="34" height="62" rx="7"/>
 <rect fill="url(#redSide)" x="75" y="48" width="136" height="194" rx="28"/>
 <rect fill="url(#red)" x="62" y="42" width="136" height="194" rx="28"/>
 <path fill="#EF5147" d="M82 72q0-11 15-13h73q-35 6-73 69V77z"/>
 <rect fill="url(#redSide)" x="63" y="229" width="148" height="62" rx="17"/>
 <path fill="url(#red)" d="M43 226q78-31 166-3l-8 53q-72 26-151-1z"/>
 <path fill="url(#blueSide)" d="M42 198h13v83H42zm161-4h13v82h-13z"/>
 <path fill="url(#creamSide)" d="M25 187q18-10 39 0v23q-20 12-39 0zm162-4q18-10 39 0v23q-20 12-39 0z"/>
 <path fill="url(#cream)" d="M25 187q18-10 39 0v10q-20 9-39 0zm162-4q18-10 39 0v10q-20 9-39 0z"/>
 <path fill="url(#gold)" d="m128 116 9 19 20 3-15 15 4 21-18-10-18 10 4-21-15-15 20-3z"/>
 <path fill="url(#blueSide)" d="m77 279 99-2 28 37-111 11-15-9z"/>
 <path fill="url(#blue)" d="m78 279 96-1 20 26-101 10z"/>
</g>
<g transform="translate(272 170) scale(.69)">
 <path fill="url(#blueSide)" d="M117 306h31v58h-31z"/>
 <ellipse fill="url(#blueSide)" cx="132" cy="368" rx="85" ry="24"/>
 <ellipse fill="url(#blue)" cx="132" cy="360" rx="85" ry="23"/>
 <rect fill="url(#creamSide)" x="115" y="283" width="34" height="62" rx="7"/>
 <rect fill="url(#blueSide)" x="75" y="48" width="136" height="194" rx="28"/>
 <rect fill="url(#blue)" x="62" y="42" width="136" height="194" rx="28"/>
 <path fill="#8A9ABC" d="M82 72q0-11 15-13h73q-35 6-73 69V77z"/>
 <rect fill="url(#blueSide)" x="63" y="229" width="148" height="62" rx="17"/>
 <path fill="url(#blue)" d="M43 226q78-31 166-3l-8 53q-72 26-151-1z"/>
 <path fill="url(#blueSide)" d="M42 198h13v83H42zm161-4h13v82h-13z"/>
 <path fill="url(#creamSide)" d="M25 187q18-10 39 0v23q-20 12-39 0zm162-4q18-10 39 0v23q-20 12-39 0z"/>
 <path fill="url(#cream)" d="M25 187q18-10 39 0v10q-20 9-39 0zm162-4q18-10 39 0v10q-20 9-39 0z"/>
 <path fill="url(#gold)" d="m128 116 9 19 20 3-15 15 4 21-18-10-18 10 4-21-15-15 20-3z"/>
 <path fill="url(#blueSide)" d="m77 279 99-2 28 37-111 11-15-9z"/>
 <path fill="url(#blue)" d="m78 279 96-1 20 26-101 10z"/>
</g>
"""),
    "birthday": ("Праздничный торт со свечами", "New dimensional birthday cake with cream icing, three candles and blue serving plate.", """
<ellipse fill="url(#blueSide)" cx="256" cy="409" rx="178" ry="47"/>
<ellipse fill="url(#blue)" cx="256" cy="398" rx="178" ry="47"/>
<path fill="url(#redSide)" d="M113 252v129c0 34 64 61 143 61s143-27 143-61V252z"/>
<path fill="url(#red)" d="M113 252v120c0 34 64 61 143 61V263z"/>
<path fill="url(#creamSide)" d="M113 320q143 65 286 0v27q-143 66-286 0z"/>
<ellipse fill="url(#cream)" cx="256" cy="249" rx="143" ry="61"/>
<path fill="url(#cream)" d="M113 249c0 34 64 61 143 61s143-27 143-61v41c-11 20-20 12-24 32-5 23-24 25-29 1-4-20-17-5-29-3-14 2-13 30-28 29-14-1-14-27-28-27-16 0-14 19-27 19-15 0-11-26-26-30-15-4-24 8-32-6-9-17-21 1-33-11-10-10-21-4-30-17z"/>
<ellipse fill="none" stroke="#FFF6E8" stroke-width="7" cx="256" cy="246" rx="117" ry="41"/>
<g>
 <path fill="url(#redSide)" d="M174 147h22v95q-11 9-22 0z"/><ellipse fill="#E96751" cx="185" cy="147" rx="11" ry="5"/>
 <path fill="url(#blue)" d="M245 118h22v116q-11 9-22 0z"/><ellipse fill="#8A9ABC" cx="256" cy="118" rx="11" ry="5"/>
 <path fill="url(#red)" d="M316 151h22v91q-11 9-22 0z"/><ellipse fill="#E96751" cx="327" cy="151" rx="11" ry="5"/>
 <path fill="url(#gold)" d="M185 91c-7 19-23 28-18 42 5 17 29 17 35 0 5-14-11-23-17-42z"/>
 <path fill="url(#gold)" d="M256 57c-7 19-23 28-18 42 5 17 29 17 35 0 5-14-11-23-17-42z"/>
 <path fill="url(#gold)" d="M327 95c-7 19-23 28-18 42 5 17 29 17 35 0 5-14-11-23-17-42z"/>
 <path fill="#FFF0BB" d="M185 113c-9 10-11 17-6 22 7 6 15-3 10-11zM256 79c-9 10-11 17-6 22 7 6 15-3 10-11zM327 117c-9 10-11 17-6 22 7 6 15-3 10-11z"/>
</g>
"""),
    "referral": ("Две связанные клубные карты", "New pair of red and blue membership cards linked by a gold loop, representing a friend invitation and shared bonus.", """
<g transform="rotate(-13 212 229)">
 <rect fill="url(#redSide)" x="83" y="100" width="233" height="278" rx="25"/>
 <rect fill="url(#red)" x="73" y="92" width="233" height="278" rx="25"/>
 <path fill="#E64B40" d="M94 115h181L94 326z" opacity=".6"/>
 <path fill="url(#cream)" d="M104 270h80v12h-80zm0 26h139v10H104zm0 25h113v10H104z"/>
 <path fill="url(#gold)" d="m187 145 15 30 34 5-25 24 6 35-30-16-30 16 6-35-25-24 34-5z"/>
</g>
<g transform="rotate(12 325 291)">
 <rect fill="url(#blueSide)" x="212" y="174" width="233" height="267" rx="25"/>
 <rect fill="url(#blue)" x="201" y="166" width="233" height="267" rx="25"/>
 <path fill="#8293B2" d="M224 191h179L224 385z" opacity=".5"/>
 <path fill="url(#cream)" d="M232 337h80v12h-80zm0 26h139v10H232zm0 25h113v10H232z"/>
 <path fill="url(#gold)" d="m317 211 15 30 34 5-25 24 6 35-30-16-30 16 6-35-25-24 34-5z"/>
</g>
<path fill="none" stroke="url(#goldSide)" stroke-width="22" stroke-linecap="round" d="M265 170c3-57 71-66 87-19 9 29-6 46-29 42"/>
<path fill="none" stroke="url(#gold)" stroke-width="15" stroke-linecap="round" d="M262 165c3-57 71-66 87-19 9 29-6 46-29 42"/>
"""),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def references(element):
    result = set()
    for node in element.iter():
        for key, value in node.attrib.items():
            result.update(re.findall(r"url\(#([^)]+)\)", value))
            if key in ("href", X + "href"):
                assert value.startswith("#"), "External SVG reference"
                result.add(value[1:])
    return result


def verify(svg):
    allowed = {"svg", "defs", "g", "path", "rect", "polygon", "polyline", "line", "circle", "ellipse", "linearGradient", "radialGradient", "stop", "clipPath", "mask"}
    ids = [node.get("id") for node in svg.iter() if node.get("id")]
    assert len(ids) == len(set(ids)), "Duplicate SVG id"
    assert references(svg).issubset(set(ids)), "Unresolved local definition"
    counts = {}
    for node in svg.iter():
        name = node.tag.split("}")[-1]
        assert name in allowed, f"Non-vector SVG element: {name}"
        counts[name] = counts.get(name, 0) + 1
        for key, value in node.attrib.items():
            assert not key.lower().startswith("on"), "SVG event handler"
            assert not re.search(r"(?:https?:|data:|javascript:)", value, re.I)
    assert counts.get("path", 0) + counts.get("polygon", 0) > 0
    return counts


def serialize(svg):
    return ET.tostring(svg, encoding="utf-8", xml_declaration=True) + b"\n"


def prefix_ids(svg, prefix):
    ids = {node.get("id") for node in svg.iter() if node.get("id")}
    for node in svg.iter():
        for key, value in list(node.attrib.items()):
            if key == "id":
                node.set(key, prefix + value)
            else:
                value = re.sub(r"url\(#([^)]+)\)", lambda m: "url(#" + prefix + m[1] + ")", value)
                if key in ("href", X + "href") and value[1:] in ids:
                    value = "#" + prefix + value[1:]
                node.set(key, value)


def native_artworks():
    assert digest(NATIVE.read_bytes()) == EXPECTED_NATIVE, "Native export changed; inspect before using it"
    native = ET.parse(NATIVE).getroot()
    native_defs, layer = list(native)[:2]
    rules = dict(re.findall(r"\.([\w-]+)\s*\{([^}]+)\}", native_defs.find(S + "style").text or ""))
    for node in native.iter():
        classes = node.attrib.pop("class", "").split()
        if classes:
            node.set("style", ";".join(rules.get(name, "") for name in classes) + ";" + node.get("style", ""))
    definitions = {node.get("id"): node for node in native_defs.iter() if node.get("id")}
    prepared = {}
    for offer_id, (title, indices, origin) in NATIVE_OBJECTS.items():
        svg = ET.Element(S + "svg", {"viewBox": f"{origin[0]} {origin[1]} 1000 1000", "width": "1000", "height": "1000", "fill-rule": "evenodd", "clip-rule": "evenodd"})
        defs = ET.SubElement(svg, S + "defs")
        artwork = ET.SubElement(svg, S + "g")
        removed = 0
        for index in indices:
            node = copy.deepcopy(layer[index])
            parents = {child: parent for parent in node.iter() for child in parent}
            for bitmap in list(node.iter(S + "image")):
                parents[bitmap].remove(bitmap)
                removed += 1
            artwork.append(node)
        required, included = references(artwork), set()
        while required - included:
            key = sorted(required - included)[0]
            node = copy.deepcopy(definitions[key])
            assert not list(node.iter(S + "image")), "Raster-dependent native definition"
            defs.append(node)
            included.update(child.get("id") for child in node.iter() if child.get("id"))
            required.update(references(node))
        verify(svg)
        prepared[offer_id] = (svg, title, indices, origin, removed)

    # sharp is already installed by Astro and is used only to measure alpha bounds.
    js = """import sharp from 'sharp';
let input='';for await(const chunk of process.stdin)input+=chunk;const result=[];
for(const svg of JSON.parse(input)){const {data,info}=await sharp(Buffer.from(svg)).ensureAlpha().raw().toBuffer({resolveWithObject:true});
let l=info.width,t=info.height,r=0,b=0;for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++)if(data[(y*info.width+x)*4+3]){l=Math.min(l,x);t=Math.min(t,y);r=Math.max(r,x+1);b=Math.max(b,y+1);}result.push([l,t,r,b]);}
process.stdout.write(JSON.stringify(result));"""
    bounds = json.loads(subprocess.check_output(["node", "--input-type=module", "-e", js], input=json.dumps([serialize(item[0]).decode() for item in prepared.values()]), text=True, cwd=ROOT))
    for (offer_id, item), box in zip(prepared.items(), bounds):
        svg, title, indices, origin, removed = item
        left, top, right, bottom = box
        width, height = right - left, bottom - top
        assert 0 < width < 900 and 0 < height < 900, "Unexpected native object bounds"
        scale = 400 / max(width, height)
        x = (512 - width * scale) / 2 - (origin[0] + left) * scale
        y = (512 - height * scale) / 2 - (origin[1] + top) * scale
        svg.find(S + "g").set("transform", f"matrix({scale:.9f} 0 0 {scale:.9f} {x:.9f} {y:.9f})")
        svg.set("viewBox", "0 0 512 512")
        svg.set("width", "512")
        svg.set("height", "512")
        prepared[offer_id] = (svg, {"artworkType": "native-brandbook-vector", "object": title, "sourceLayerChildIndices": indices, "sourceElementIds": [layer[index].get("id") or f"layer-child-{index}" for index in indices], "modifications": "Original vector shapes, colors and gradient values retained; native CSS inlined; raster-only shadows removed; local IDs prefixed; object uniformly scaled and centered on a transparent square.", "omittedRasterShadowElementsInsideBody": removed})
    return prepared


def main():
    check = sys.argv[1:] == ["--check"]
    assert not sys.argv[1:] or check, "Usage: python scripts/prepare-offer-icons.py [--check]"
    native = native_artworks()
    catalog = json.loads((ROOT / "content/offers.json").read_text(encoding="utf-8"))
    offers = [offer for offer in catalog["offers"] if offer["id"] in catalog["metadata"]["sourceIds"]]
    source = json.loads((ROOT / "content/gift-vector-sources.json").read_text(encoding="utf-8"))
    manifest = {
        "status": "local-only-vector-illustrations-not-published",
        "source": source["source"],
        "sourceSha256": source["sourceSha256"],
        "nativeExport": NATIVE.relative_to(ROOT).as_posix(),
        "nativeExportSha256": EXPECTED_NATIVE,
        "generator": "scripts/prepare-offer-icons.py",
        "method": "Four native brandbook objects and six newly drawn offer-specific SVG illustrations. New artwork is explicitly identified per icon and is not presented as original brandbook artwork.",
        "palette": ["#C62C2A", "#FFCC29", "#52658C", "#1E335C", "#F6E8D3"],
        "canvas": {"width": 512, "height": 512, "viewBox": "0 0 512 512", "background": "transparent"},
        "icons": [],
    }
    assert {offer["id"] for offer in offers} == set(native) | set(ARTWORK), "Offer IDs and icon set differ"
    outputs = {}
    for offer in offers:
        offer_id = offer["id"]
        if offer_id in native:
            svg, provenance = native[offer_id]
        else:
            title, explanation, body = ARTWORK[offer_id]
            svg = ET.fromstring(f'<svg xmlns="{NS}" viewBox="0 0 512 512" width="512" height="512"><defs>{GRADIENTS}</defs>{body}</svg>')
            provenance = {"artworkType": "new-svg-illustration", "object": title, "authoring": "Drawn for the local SOYUZ offers in scripts/prepare-offer-icons.py using SVG paths and shapes; not extracted or traced from the brandbook.", "styleReference": ["public/reference/gift-5.svg", "public/reference/gift-6.svg", "tmp/vector-export-tools/native-icons.svg"], "construction": explanation, "sourceLayerChildIndices": [], "sourceElementIds": []}
        prefix_ids(svg, "offer-" + offer_id + "-")
        counts = verify(svg)
        payload = serialize(svg)
        relative = f"public/offer-icons/{offer_id}.svg"
        outputs[relative] = payload
        manifest["icons"].append({"id": offer_id, "title": offer["title"], "url": f"/offer-icons/{offer_id}.svg", "viewBox": "0 0 512 512", "width": 512, "height": 512, "bytes": len(payload), "sha256": digest(payload), "elementCounts": counts, "embeddedImages": 0, "externalReferences": 0, **provenance})
    outputs["content/offer-icon-sources.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    for relative, payload in outputs.items():
        target = ROOT / relative
        if check:
            assert target.read_bytes() == payload, f"Out-of-date generated file: {relative}"
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
    print(f"{'Verified' if check else 'Prepared'} 10 distinct SVG offer illustrations: 4 native, 6 newly drawn; 512x512, transparent, no raster or external references.")


if __name__ == "__main__":
    main()
