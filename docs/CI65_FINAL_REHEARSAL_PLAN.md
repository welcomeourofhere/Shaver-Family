# Чистое воспроизведение CI65 — текущее состояние и оставшиеся gates

Обновлено16ноября2026 по фактическим файлам и сообщениям root. Clean CI **уже начат**, но финальный runtime/release/package ещё не принят. Опубликован только выпуск64 `db23e622f97223556f77`. Успешный локальный rehearsal не означает GitHub Actions, загрузку финального пакета или публикацию65.

## Что существует и выполнено

Фактический снимок — `.local/release65/ci65-final-snapshot.json`, а не файл в корне.local. Каталог `.local/ci65-final` существует. В нём собственные node_modules и.venv; рабочие зависимости основного проекта не копировались и не подменялись symlink.

Промежуточный пакетB `cc3db610afd8e81ca768` использован как проверенный bootstrap-вход. Его manifest содержит424 объекта доставки. Восстановленный public-граф содержит384 пути, лишних файлов0, хеши проверены; журналbootstrap сообщает384 pinned assets и376 восстановленных файлов. Это не финальный пакетC и не доказательство публикации65.

Снимок с phase `final-focus-and-MIME-v4` фиксирует627 исходных путей и побайтную сверку payload `github-tree.for-ci-refresh.json`, SHA256 `5f866b4a2cb111c845e1b0dedc5573112c9891c1c3f172ab1dbe7807b5a2c5db`. Входной media-lock имеетSHA256 `bdf2bd25ad15af71e19ae53a4748f8a66ef6d0ce3a0eedaa068316765290602a`, public source graph — `723f4e36f700317ba3e7d01bc0a32f85ea12dbb5be370169262a3913c5a9a211`. Эти значения относятся к сохранённому промежуточному снимку; заменять ими ожидаемый хеш следующего combined source нельзя.

Вsnapshot явно стоят `sourceRefreshRequired:true`, `finalCandidate:false`; он superseded последующими footer refresh и исправлением классификации gift-case. Завершены ownership, source boundary, Astro check и обычная сборка. Первый runtime остановился на проверке `all six gift illustrations are original vector objects with no embedded raster or external references`: она пыталась прочесть неотправляемый `public/reference/gift-1.svg`.

Root исправил `tests/ci-suites.json`: эта проверка неактивных сохранённых gift-оригиналов теперь localCases. Проверка собранного шаблона остаётся runtime. Само исправление классификации не является успешным повторным runtime; нужен свежий combined source и новый полный проход. Исходные подарки и исторические журналы не удалялись.

## Готовая независимая среда

`.local/release65/ci65-final-environment.json` подтверждает:

| Среда | Фактическая версия / граница |
|---|---|
|Node|24.22.1|
|pnpm|10.34.9, вызван через pnpm11 dlx pnpm@10.34.9|
|Astro / TypeScript|5.18.2 /5.9.3 из собственного node_modules|
|Python|3.12.10, собственная `.local/ci65-final/.venv`|
|Python packages|beautifulsoup4 4.14.3, tinycss2 1.5.1, fonttools 4.68.0, brotli 1.2.0, Pillow12.3.0|
|zlib|1.3.1|

Зависимости сохранены при проверенном refresh исходников. Повторная установка не нужна только ради новогоJS/CSS; изменение package/lock требует отдельной проверки и собственного frozen-lockfile install. Разрешённые build scripts — esbuild/sharp; agent-browser install script выключен.

## Что ожидается от root и clean CI

Окончательный combined source ожидает source-freeze общего modal/resize QA. После сигнала root нужно принять точные путь иSHA256 нового payload, побайтно сверить каждый авторский файл и контролируемо обновить существующий исходный срез с сохранением независимых зависимостей. Старые627путей и старыйSHA не считаются автоматически окончательными.

`prepare-source-tree.py --materialize` отказывает при существующем destination. Нельзя повторять старый шаг «каталог не существует», принудительно очищать текущий CI или молча перезаписывать отличный источник. Любой refresh получает новый отчёт о наборе путей/байтах. Сохранённые snapshot, attempt1 и прежние каталоги остаются историческими доказательствами.

Сверка исключает.local,tmp,dist,node_modules,deploy/out,archive,artifacts,src/pages/previews иpublic/previews из авторского набора. Public восстанавливается только из принятого lock плюс явно объявленные authored SVG/лицензии. Оригиналы фото/видео и неактивные provenance-ресурсы в cold CI не добавляются ради прохождения неверного runtime-case. Обе лицензииLucide и явный authored input `deploy/project-head.html` должны присутствовать. `.gitattributes` сохраняет байты public через-text, включая CRLF авторскихSVG.

## Оставшаяся последовательность

Каждая команда выполняется сcwd `.local/ci65-final`, получает новый отдельный журнал и допускает следующий шаг только приexit0. `SOYUZ_RELEASE` отсутствует в первой сборке и установлен только для второй. `PYTHON` в package-группе указывает на абсолютный путь собственного venv Python.

| Шаг | Команда | Требуемый результат |
|---|---|---|
|Сверка refreshed source|`node scripts/check-ci.mjs check`|Свежая ownership/classification, включая исключение локального gift-case.|
|Public boundary|`node scripts/check-ci.mjs source`|Каждый public sourceSha256 совпадает с принятым lock; запрещённых входов нет. Если lock изменился, сначала заново выполнить проверенный bootstrap.|
|Типы|`pnpm check`|Чистые Astro/TS исходники без previews.|
|Обычная сборка|`pnpm build`|Собственный dist текущего combined source.|
|Runtime|`node scripts/check-ci.mjs runtime`|Все выбранные runtime cases прошли; local provenance не замаскирован под runtime.|
|Release-сборка|`pnpm build` с `SOYUZ_RELEASE=1`|Release metadata и аналитика той же изолированной версии.|
|Release assertions|`node scripts/check-ci.mjs release`|Metadata/analytics assertions прошли.|
|СозданиеC|`.venv/Scripts/python.exe scripts/prepare-tilda-release.py`|Новый собственный `deploy/out/<build>` и локальный deploy/current нового CI.|
|Package gate|`node scripts/check-ci.mjs package` с `PYTHON=<абсолютный venv python>`|Все9 Python suites прошли по созданномуC.|

Фактический inventory сейчас —35 runtime suites,7 local provenance suites и9 Python suites; его повторно фиксирует свежийcheck. Все дальнейшие build-id, количества и хеши берутся из результатаC, а не копируются изB.

При runtime следует сохранить реальные argv spawnSync, включая anchored `--test-name-pattern`, через приватный preload, вызывающий исходный spawnSync без изменения результата. Пишутся только команды и аргументы, безenv/секретов. Сверить фактически выбранные и исключённые имена сAST `test(...)` и новым ci-suites.json. Сам check-ci требует ненулевойpass и ожидаемыеSubtest; один список конфигурации не заменяет выполненные тесты.

## MIMEv4 и immutable identity

ПакетC создаётся текущим экспортёромv4. Canonical CONTENT_TYPES задаёт font/woff2,font/woff,font/ttf,font/otf,image/webp,image/jpeg,image/png,image/avif и остальные типы без зависимости от Windows mimetypes. MIME участвует в build digest и в адресации бинарного представления `SHA256(MIME + NUL + source bytes)`.

Исправление MIME не перезаписывает metadata старого immutable объекта. Новая identity создаёт новыйURL правильного представления; неизменённые бинарные ресурсы затем стабильны между кодовыми сборками. NewsJSON и относительные `../media/news/` сохраняют общий build-префикс. Оригиналы и старые Cloud-объекты не удаляются.

Gzip использует GzipFile с пустым filename,mtime0,OSbyte255. Codec, включая zlibVersion, входит в digest. Поэтому новыйC не обязан совпастьbuild-id сB или с другой средойzlib; wire/content/source hashes и codec фиксируются отдельно. Подробнее — `EXPORT_CONTRACT_65.md`.

## ПриёмкаC и последующие внешние действия

Clean CI передаёт root собственный package manifest, build-id/codec, source payloadSHA, media-lockSHA, bootstrap boundary, actual-case filters, TAP summaries и журналы. До этогоC не принят и не называется опубликованным. Общие рабочие dist/deploy/current и published registry не заменяются результатом rehearsal автоматически.

После принятияC root отдельно выполняет Cloud upload/read-back всех wire hashes,MIME,CORS,encoding/cache; затем shared header/footer перед content,13native HEAD/T123 readback и публикаций, public UI/SEO/analytics QA. `prepare-tilda-update.py` готовит только проверяемый payload под.local сexpected-before hashes; сам он не публикует и не продвигает registry. Его9-suite package gate включает проверки неполной/чужой/дублированной Cloud-верификации и неверныхtargets.

ОбновлениеGSC от root: robotsreport после reload отображает https://soyuz.hair/robots.txt,16.11.2026 02:34,«Получен»,168Б,проблемы«-». Это подтверждает новыйfetchrobots после requestedrecrawl, не индексацию страниц и не публикацию65.
