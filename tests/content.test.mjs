import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
const team = JSON.parse(
  readFileSync(new URL("../content/team.json", import.meta.url)),
);
const source = JSON.parse(
  readFileSync(new URL("../content/team-sources.json", import.meta.url)),
);
test("SOYUZ team uses six actual training profiles and local portraits", () => {
  assert.equal(team.masters.length, 6);
  assert.deepEqual(
    team.masters.map((x) => x.name),
    [
      "Светлана Дёмина",
      "Соня Кид",
      "Милена Малышевская",
      "Дарья Мерзлякова",
      "Софья Шалагинова",
      "Любовь Шкляева",
    ],
  );
  for (const person of team.masters) {
    assert.equal(person.width, 600);
    assert.equal(person.height, 800);
    assert.match(person.image, /^\/media\/team\/souz-/);
    assert.ok(
      readFileSync(new URL("../public" + person.image, import.meta.url))
        .length > 1000,
    );
  }
  assert.ok(JSON.stringify(source).includes("2026-10-11"));
});
test("SOYUZ catalogue preserves training branch, ranges and source rows", () => {
  const bytes = readFileSync(
    new URL("../content/service-catalog.json", import.meta.url),
  );
  const catalog = JSON.parse(bytes),
    provenance = JSON.parse(
      readFileSync(
        new URL("../content/service-catalog-sources.json", import.meta.url),
      ),
    );
  assert.match(provenance.sourceSha256,/^[a-f0-9]{64}$/);
  assert.equal(provenance.branch,'souz');
  assert.equal(provenance.exportDate,'2026-09-17');
  assert.equal(catalog.metadata.status, "soyuz-training-catalogue");
  assert.deepEqual(
    catalog.categories.map((c) => c.services.length),
    [8, 6, 6, 7, 4],
  );
  assert.ok(
    catalog.categories.every((c) =>
      ["red", "blue", "yellow", "ink"].includes(c.color),
    ),
  );
  assert.doesNotMatch(
    JSON.stringify(catalog.categories),
    /биозавив|брейды|косы/i,
  );
  for (const category of catalog.categories) {
    for (const service of category.services) {
      assert.ok(
        service.description.length >= 20 && service.description.length <= 350,
      );
      assert.match(service.priceLabel, /₽/);
      assert.ok(service.price >= 0);
      assert.equal(service.source.branch,'souz');
      assert.ok(service.source.rows.length>0);
      assert.equal(service.price,service.source.priceFrom);
      assert.ok(service.source.priceTo>=service.source.priceFrom);
      assert.doesNotMatch(
        service.description,
        /https?:|shaver\s*family|шейвер\s*ф[эе]мили/i,
      );
    }
  }
  const services=catalog.categories.flatMap(category=>category.services);
  const pick=id=>services.find(service=>service.id===id);
  assert.equal(pick('main-267630').priceLabel,'2 300 ₽');
  assert.equal(pick('main-267602').duration,'60–90 мин');
  assert.equal(pick('main-15270008').duration,'120 мин');
  assert.equal(pick('extra-15747049').name,'10-этапный СПА-уход за кожей лица');
  assert.equal(pick('coloring-14360790').priceLabel,'1 500–2 500 ₽');
  assert.equal(pick('main-soyuz-head-beard'),undefined);
  assert.equal(catalog.archivedServices[0].id,'main-soyuz-head-beard');
  assert.equal(pick('main-honest-price').priceLabel,'от 500 ₽');
  assert.equal(pick('main-honest-price').name,'[Честная цена] Мужская стрижка');
  for(const id of['hair-beard-soyuz-head-shave','hair-beard-267649']){assert.equal(pick(id),undefined);assert.ok(catalog.archivedServices.some(service=>service.id===id))}
  assert.deepEqual(pick('main-honest-price').source.rows,[8,9,10]);
  assert.ok(services.filter(service=>service.name.startsWith('[Премиум]')).every(service=>service.description.includes('10-этапный')));
});

test("retained category reference photographs remain available locally", () => {
  const catalog=JSON.parse(readFileSync(new URL('../content/service-catalog.json',import.meta.url)));
  for(const category of catalog.categories)assert.ok(readFileSync(new URL('../public'+category.image,import.meta.url)).length>1000);
});
