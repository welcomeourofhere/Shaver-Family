"""Fetch a portable libcdr converter from official MSYS2, verify hashes, extract bin only."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tmp/vector-export-tools"
# Package URLs and SHA-256 published by packages.msys2.org, verified 2026-11-04.
PACKAGES = [
    ("libcdr-0.1.9-1", "5a1616e3411914b50a04828449b42e1039e04ded8345aa1abd272e417b6f7e38"),
    ("librevenge-0.0.6-1", "c614473fdacab65f941ed23ea29c5f13582dfc2355f07d3cf6079258589b192f"),
    ("icu-78.3-4", "db9282bbd0a2e74c31d66af6bd89eb68d647a09f721eef4c661768588dca4324"),
    ("lcms2-2.20-1", "4e1d12047e72c63832f2b50c2fc87c7ec9d2e5a8bd40ce6e820ccbeedf2e7b8f"),
    ("zlib-1.3.2-3", "130e6ef04c654fc2150a177600aa5ed0035087665a893479d2c85ba7485d5704"),
    ("libgcc-16.2.0-6", "80b2497f019977dd9528b1abc8621b1328a0115ab1f724047ccbb56bf323f11d"),
    ("libstdc++-16.2.0-6", "33c5e58a85a538cf843a8672991cce591f0231d66da3b66a57629712d64be17f"),
    ("libwinpthread-14.0.0.r598.ge3d18511f-1", "c35d6be83d141c8cfbb61f1637dd4b53aac8f5562d766aa26d0741c40bad4e4d"),
]


def fetch(package):
    name, expected = package
    filename = f"mingw-w64-ucrt-x86_64-{name}-any.pkg.tar.zst"
    url = "https://mirror.msys2.org/mingw/ucrt64/" + urllib.parse.quote(filename)
    path = OUT / filename
    if not path.exists():
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"Hash mismatch: {name}")
        path.write_bytes(data)
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"Cached package hash mismatch: {name}")
    return {"name": name, "url": url, "sha256": expected, "path": path}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        packages = list(pool.map(fetch, PACKAGES))
    binary_dir = OUT / "bin"
    binary_dir.mkdir(exist_ok=True)
    for package in packages:
        path = package.pop("path")
        members = subprocess.check_output(["tar", "-tf", str(path)], text=True).splitlines()
        for member in members:
            parts = PurePosixPath(member).parts
            if len(parts) != 3 or parts[:2] != ("ucrt64", "bin") or not member.endswith((".exe", ".dll")):
                continue
            output = (binary_dir / parts[2]).resolve()
            if not output.is_relative_to(binary_dir.resolve()):
                raise ValueError("Unsafe archive member")
            output.write_bytes(subprocess.check_output(["tar", "-xOf", str(path), member]))
        print("Verified and extracted", package["name"])
    (OUT / "packages.json").write_text(json.dumps(packages, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
