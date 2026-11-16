# СОЮЗ — soyuz.hair

Исходники сайта барбершопа СОЮЗ. Публичный сайт: https://soyuz.hair. Локальный HMR: dev.cmd → http://127.0.0.1:4321/. Исходники меняются в src/content; dist и deploy/out создаются сборкой.

Тильда: проект46815509,11страниц содержимого (включая404), отдельные общие header/footer. Ресурсы: Яндекс Облако, только shaver/Soyuz/releases/. Предыдущие версии сохраняются. Новости читаются при открытии сайта из действующего GitHub JSON; worker/расписание находятся в main/soyuz существующего репозитория.

Для выпуска предусмотрена изолированная ветка codex/soyuz-release в welcomeourofhere/Shaver-Family. Её дерево содержит только СОЮЗ; не сливать эту ветку в main Shaver Family. Факт отправки и результат CI фиксируются отдельно в docs/PROGRESS.md. Workflow проверяет сборку и сохраняет пакет; ключей Тильды/Облака и автоматической публикации в workflow нет.

## Восстановление и сборка

Node24, pnpm10, Python3.12. Публичные бинарные файлы восстанавливаются по deploy/media-lock.json с проверкой SHA-256. Локальные оригиналы и исторические материалы не перезаписываются.

```powershell
pnpm install --frozen-lockfile
python -m pip install beautifulsoup4==4.14.3 tinycss2==1.5.1 fonttools==4.68.0 brotli==1.2.0 Pillow==12.3.0
python scripts/bootstrap-public.py
node node_modules/astro/astro.js check
node node_modules/astro/astro.js build
node --test tests/*.test.mjs
```

Полный локальный набор проверяет также оригиналы фотографий, исходные иллюстрации, захваченные статьи и исторические макеты. Эти материалы остаются в локальном рабочем каталоге. Production-дерево для GitHub исключает `src/pages/previews/`, `public/previews/`, `archive/` и `artifacts/`; исходные варианты и их проверки сохраняются локально.

Состав CI задан в `tests/ci-suites.json`. Все runtime-файлы выполняются полностью; в смешанных файлах только явно названные сравнения с оригиналами относятся к локальному набору. `scripts/check-ci.mjs` требует владельца для каждого нового unit/Python-теста и не принимает пустой результат фильтра. `runtime-assets.test.mjs` проверяет используемые публичные изображения, видео и полный текст всех шести интервью без доступа к архиву. Перед сборкой CI проверяет SHA-256 всех восстановленных ресурсов по `deploy/media-lock.json`, после сборки — точные production-маршруты, локальные ссылки, метаданные и полный Tilda-пакет. В полном локальном дереве сохраняются также проверки 14 маршрутов с тремя страницами просмотра; production-дерево содержит 11 маршрутов из `deploy/production.json`.

Для production-клона после восстановления публичных ресурсов используются `node scripts/check-ci.mjs source`, `pnpm check`, `pnpm build` и `node scripts/check-ci.mjs runtime`. После release-сборки и подготовки пакета — `node scripts/check-ci.mjs release` и `node scripts/check-ci.mjs package`. Эти команды не публикуют сайт. Применимые браузерные проверки и границы измерений описаны в tests/README.md. Физические телефоны исключены владельцем; WebKit на Windows не доказывает Safari на iPhone.

```powershell
$env:SOYUZ_RELEASE='1'
node node_modules/astro/astro.js build
node --test tests/metadata.test.mjs tests/analytics.test.mjs
python scripts/prepare-tilda-release.py
python -m unittest discover -s tests -p '*_test.py'
```

Подготовка пакета не публикует сайт. upload-tilda-assets.py --apply пишет только разрешённый namespace существующим локальным профилем. T123 и HEAD берутся из точного manifest, затем проверяются чтением и публикуются средствами Тильды. Подробная карта настроек — docs/TILDA_SETTINGS_64.md; действующий контракт — docs/DESIGN_SYSTEM.md; состояние — docs/PROGRESS.md; план — docs/superpowers/plans/2026-11-15-soyuz-release.md.

Исходное production-дерево готовится командой `python scripts/prepare-source-tree.py`. Она явно исключает локальные previews, originals и сборки, сохраняет авторские SVG и создаёт Git tree payload в `.local/release65/`; `--materialize .local/<новая папка>` дополнительно создаёт чистый каталог для CI-проверки. Команда ничего не отправляет в GitHub и не удаляет файлы.

## Git и source-политика

Удалённый источник этого сайта — изолированная ветка `codex/soyuz-release` репозитория `welcomeourofhere/Shaver-Family`. Она содержит только СОЮЗ. Fetch/push ограничиваются этой веткой; `main` Shaver Family не меняется. Подключение локального Git выполняется отдельно после подтверждённого source-commit, без checkout/reset/clean рабочего каталога.

Канонический набор задаёт `scripts/prepare-source-tree.py:source_files()` вместе с `tests/ci-suites.json` и `deploy/media-lock.json`. Staging разрешён только по проверенному списку этих путей с последующей сверкой staged/tracked-набора. Нельзя использовать `git add -A` или `git add .`: `.gitignore` служит дополнительной защитой, а не заменой source-whitelist. В `public` разрешены только выбранные авторскиеSVG и лицензияLucide; правило «всеSVG» не применяется. При изменении канонического набора соответствующие исключения `.gitignore` сверяются заново.

`.gitattributes` использует `* -text`, чтобы API-payload, Git blobs и локальные авторские файлы сохраняли одинаковые байты, включаяCRLF. Это отключает EOL-конверсию, а не обычный текстовыйdiff. Массовая нормализация и `git add --renormalize` не входят в экспорт. КаноническиеLF-байты HEAD/body и их хеши отдельно обеспечивает exporter.

Оригиналы, previews, игры, исторические бинарные материалы и результаты сборок остаются локально. Публичные производные восстанавливаются через bootstrap по lock и SHA, без перезаписи отличающихся оригиналов. НеобходимыеMarkdown-документы из `docs/archive` остаются частью явно выбранного source-набора.

Успешный GitHub CI подтверждает проверку source/пакета, но не публикацию сайта. Cloud-перенос, HEAD/T123, readback и публикация Тильды выполняются отдельно из принятого manifest; запись build в локальном указателе не заменяет подтверждение публичной версии.
