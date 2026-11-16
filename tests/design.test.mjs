import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import {createHash} from 'node:crypto';
import postcss from "postcss";
import design from "../src/config/design.ts";

test('utility glyphs retain pinned official Lucide geometry, notices and the shared hero chevron',()=>{
 const source=new URL('../content/third-party/lucide/',import.meta.url),metadata=JSON.parse(readFileSync(new URL('source.json',source),'utf8'));
 assert.equal(metadata.tag,'1.73.0');assert.equal(metadata.commit,'55782beff3a0133df79c417eb68f96e8f19e2404');
 const sprite=readFileSync(new URL('../public/brand/utility-icons.svg',import.meta.url),'utf8');
 for(const file of metadata.files){
  const body=readFileSync(new URL(file.name+'.svg',source));
  assert.equal(createHash('sha256').update(body).digest('hex'),file.sha256);
  assert.equal(file.url,`https://raw.githubusercontent.com/lucide-icons/lucide/${metadata.commit}/icons/${file.name}.svg`);
  const inner=body.toString().match(/<svg\b[^>]*>([\s\S]*?)<\/svg>/)[1].trim().replace(/>\s+</g,'><');assert.ok(sprite.includes(inner),file.name+' must use the official paths');
 }
 assert.equal((sprite.match(/stroke-width="2"/g)||[]).length,metadata.files.length);
 assert.doesNotMatch(sprite,/<(?:script|foreignObject|image|use)\b|\bon\w+=/i);
 assert.match(sprite,/<symbol id="utility-arrow-up"[^>]*><path d="m9 5 7 7-7 7" transform="rotate\(-90 12 12\)"/);
 const license=readFileSync(new URL('LICENSE',source));assert.equal(createHash('sha256').update(license).digest('hex'),metadata.licenseSha256);
 assert.deepEqual(readFileSync(new URL('../public/brand/lucide-LICENSE.txt',import.meta.url)),license);
 assert.match(license.toString(),/ISC License/);assert.match(license.toString(),/The MIT License \(MIT\)/);
});

test("layout and motion have one canonical source and use the measured SF contract", () => {
  assert.equal(design.base["--content-max"], "var(--size-1160)");
  assert.equal(
    design.base["--page-gutter"],
    "clamp(var(--size-10), 1.6667vw, var(--size-20))",
  );
  assert.equal(design.base["--deck-step"], "var(--size-12)");
  for(const token of ['--motion-ui','--motion-popover','--motion-context','--motion-window','--motion-dock']){
    const duration=parseFloat(design.base[token]);
    assert.ok(duration>=100&&duration<300,`${token}: frequent UI response must stay below 300ms`);
  }
  assert.ok(parseFloat(design.base['--motion-dock-exit'])<parseFloat(design.base['--motion-dock']));
  assert.match(design.base['--ease-spring'], /^linear\(/);
  assert.ok(Object.keys(design.base).every((key) => !key.startsWith("--feedback-")));
  const names = new Set([
    ...Object.keys(design.base),
    ...design.responsive.flatMap((r) => Object.keys(r.tokens)),
    "--deck-height-live",
    "--card-level",
    "--card-count",
    "--card-bg",
    "--card-fg",
    "--card-highlight",
    "--card-duration",
    "--portrait-position",
    "--mobile-nav-space",
  ]);
  // Component-local values must have an actual declaration, not an unchecked allowlist.
  for (const folder of ["components", "scripts", "styles"])
    for (const file of readdirSync(
      new URL("../src/" + folder, import.meta.url),
    )) {
      if (!/\.(astro|ts|css)$/.test(file)) continue;
      const source = readFileSync(
        new URL("../src/" + folder + "/" + file, import.meta.url),
        "utf8",
      );
      for (const match of source.matchAll(/(--[\w-]+)\s*:/g))
        names.add(match[1]);
      for (const match of source.matchAll(
        /setProperty\(\s*["'](--[\w-]+)["']/g,
      ))
        names.add(match[1]);
    }
  // Astro generates the responsive team roles; validate actual emitted declarations.
  const html = readFileSync(
    new URL("../dist/index.html", import.meta.url),
    "utf8",
  );
  for (const match of html.matchAll(/(--[\w-]+)\s*:/g)) names.add(match[1]);
  for (const file of readdirSync(
    new URL("../src/styles", import.meta.url),
  ).filter((f) => f.endsWith(".css"))) {
    const root = postcss.parse(
      readFileSync(new URL("../src/styles/" + file, import.meta.url), "utf8"),
    );
    root.walkDecls((decl) => {
      assert.doesNotMatch(
        decl.value,
        /(?<![\w-])[1-9]\d*(?:\.\d+)?(?:px|ms|deg)\b/,
        `${file} ${decl.prop}: ${decl.value}`,
      );
      assert.doesNotMatch(
        decl.value,
        /#[0-9a-f]{3,8}\b/i,
        `${file}: unowned color`,
      );
      for (const match of decl.value.matchAll(/var\((--[\w-]+)/g))
        assert.ok(names.has(match[1]), `${file}: missing ${match[1]}`);
    });
  }
});
test("built page has eleven illustration slots, one contextual action each and an opened native map", () => {
  const html = readFileSync(
    new URL("../dist/index.html", import.meta.url),
    "utf8",
  );
  assert.equal((html.match(/class="of-photo photo-frame"/g) || []).length, 11);
  assert.equal((html.match(/class="btn of-action"/g) || []).length, 11);
  assert.doesNotMatch(html, /data-of-open|of-eyebrow|of-icon|offer-dialog-/);
  assert.match(html, /src="https:\/\/yandex.ru\/map-widget/);
  assert.doesNotMatch(html, /data-load-map|Показать карту/);
  assert.equal((html.match(/data-dock-slot="[0-2]"/g) || []).length, 3);
  assert.match(html, /class="dock-shell"/);
  assert.doesNotMatch(html, /data-spatial|mobile-dock|mobile-cta/);
});
