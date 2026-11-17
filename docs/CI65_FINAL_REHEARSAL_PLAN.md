# Воспроизводимость СОЮЗа — текущее состояние68

17.11.2026: опубликован **J `6654da5cca6b9b5117b5`**, source `a90b33c9138ae59af05fa45b1ec8107feeea065f`, CI44023921791 SUCCESS. Cloud583,Тильда13EXACT,публичные HTTP13/canvas18/map-hours34/cold6/SDK прошли; настоящий Yandex pin принят вручную. Первые визиты: CLS0 вместо0,036329, LCP2492→1900ms; timespan TBT223→306ms требует диагностики, общего ускорения нет. Точная область, отрицательная серия/измеритель и открытые границы — [RELEASE_68.md](RELEASE_68.md). Общая цель не закрыта.

## Предыдущие срезы — история до окончательной приёмки J

17.11.2026. Публичный выпуск **I `935b93ae952b78c8d373`**: 13 публикаций shared-first и точный readback, 583 Cloud-ресурса; public HTTP13 (11 HTML + robots/sitemap), canvas18/18, настоящий SDK transport, карта и маршрут подтверждены в указанной области. Источник `70e295f84703833fc90ff78a9aa35f9e8e7695d7`, Actions **44014378421 SUCCESS**; документация/локальный Git `679cc790772f42f58742f1db9f251d2798479b55`. Точные артефакты и ограничения — [RELEASE_67.md](RELEASE_67.md).

Кандидат **J `6654da5cca6b9b5117b5`** исправляет скачок Hero при первом cookie-уведомлении и размещает HTML единственной панели раньше содержимого. Он собран чисто (183 Node, Astro142/0/0/0, runtime/release, 16 Python-наборов/93 проверки), Cloud583 проверен; оставшаяся QA/source/CI и публикация ещё не завершены. Действующий реестр публикации сохраняет I. Полный аудит требований и открытые внешние пункты — [GOAL_COMPLETION_AUDIT_68.md](GOAL_COMPLETION_AUDIT_68.md), ход — [ITERATION_68.md](ITERATION_68.md).

Старые незакрытые строки actualE/sourceE ниже относятся к этапу65 и заменены подтверждённой приёмкой I, а не повторно открытыми дефектами. Получение Google sitemap, доступная отправка Яндексу, кабинетная ingestion и полевая индексация остаются отдельными открытыми частями. Физические телефоны исключены владельцем.

## История этапа65 — сохранённые результаты

16.11.2026, опубликован выпуск65 E `945ad6ddd3e70d5cc3c4`, manifest SHA256 `e9af475c845d1adebf868b28361b745811612b78bfb3901161a50605dbf1dabb`. Через официальный MCP опубликованы13/13 страниц, shared перед content; после публикации13/13 HEAD/code прочитаны с точным совпадением. Cloud421/421 проверен, root registry указываетE. NativeE18 прошёл с прозрачными body/#allrecords/#t-header/#t-footer и тремя footer-pixel проверками в каждом случае. ActualE18/18 technical HTTPS GREEN; Header3/3 сохранил gap8px, radius20px, фон#252525 и8px status-dot. После добавленного владельцем исключения Happ/Xray основной https://soyuz.hair также прошёл18/18 усиленных canvas/footercorner cases в3движках, обе темы и390/961/1440px; HTTP12/12PASS,177currentresources. Доказательства: HOST_CANVAS_65D.md и tmp/planning/iteration65/host-canvas/E-main-public/. Финальные sourceE commit/Actions и локальный Git adoption ожидаются; remote пока509fed9…/Actions43800396980success.

## Независимая среда и сохранённая история

Каталог `.local/ci65-final` существует и использует собственные node_modules/.venv. Зависимости основного проекта не копировались и не подменялись symlink. `.local/release65/ci65-final-environment.json` фиксирует Node24.22.1, pnpm10.34.9, Astro5.18.2, TypeScript5.9.3, Python3.12.10, beautifulsoup4 4.14.3, tinycss2 1.5.1, fonttools4.68.0, brotli1.2.0, Pillow12.3.0 и zlib1.3.1. Build scripts разрешены дляesbuild/sharp; agent-browser install script выключен.

B `cc3db610afd8e81ca768` был толькоbootstrap:424wire-объекта,384пути public,376восстановленных файлов,0лишних. Первыйruntime остановился на неактивном `public/reference/gift-1.svg`. Root перенёс provenance-case вlocalCases, сохранив runtime-проверку собранной заглушки. После этого окончательный combined source прошёл полный clean CI. Snapshot `.local/release65/ci65-final-snapshot.json` содержит627путей и SHA256 `517c48d59e855e9d5cc26fa025667bed8fe99a3534a3ce38ed6f005a69ac4851`. Старые attempt1 и промежуточный phase final-focus-and-MIME-v4 остаются историей, а не текущим блокером.

Public source graph384, SHA256 `723f4e36f700317ba3e7d01bc0a32f85ea12dbb5be370169262a3913c5a9a211`, не расширялся оригиналами/preview. Production-only whitelist исключает.local,tmp,dist,node_modules,deploy/out,корневыеarchive/artifacts иsrc/pages/previews. Public восстанавливается из принятого lock и точного набора авторскихSVG/лицензий. Обе лицензииLucide и `deploy/project-head.html` сохранены. Текущий Git-контракт `* -text` сохраняет authored bytes без отключения diff; stage допускается только по проверенному source pathspec, безadd-A.

## ВыполненныйC и исправление экспортных метаданных

Clean CI создалC `7a129e64e8086a5face7`:121Astro/0,99runtime assertions,4release assertions,9Python suites/41PASS.11content+2shared,421asset,57 320 419wire-байт. Root принял копию побайтно. Фактические case filters и argv сохранены безenv/секретов; inventory35runtime/7local/9Python исключает ошибочный provenance из runtime.

Позже выявлен CRLF-дефект: read_text скрывал отличие actual HEAD/body bytes от нормализованногоSHA. Экспортёр теперь записывает canonical UTF-8 LF; byte-level assertions и actual package helper проверяют записанные байты. УточнениеaltSource обозначает постеры какartwork без подмены бинарных оригиналов. C также выявил реальный дефект тёмной темы на Тильде: opaque body/#allrecords. Поэтому C не является финальной host-приёмкой, даже при зелёном прежнем native QA.

## ИсторияD — host-only delta и ограниченная проверка

Фактический новый отчёт — `.local/release65/ci65D-20261116T061827Z/D-candidate.json`; steps — соседнийgates.json. Этот срез содержит633исходных пути, source payload SHA256 `0208059e85140b7eb34dfaaa51f44a282c1073641a7ed214920fe339e43d88e1`. Последующие CURRENT-docs учитываются отдельно и не приписываются этому payload.

| Gate | РезультатD |
|---|---|
|Ownership|35runtime/7local/9Python, exit0|
|Source boundary|384public-пути, exit0; оригиналы иpreview не добавлены|
|Release assertions|4PASS|
|Prepare/package|9Python suites/46PASS, canonical actual-byte HEAD/body hashes|
|Host reset|13HEAD содержат transparent reset дляbody/#allrecords|
|Compiled inputs|421sourceSHA/client inputs C=D;13body семантически совпадают с учётомuuid/build-prefix|
|Astro/build|Не запускались повторно для host-only delta; это не новый121Astro/99runtime прогонD|
|Пакет|D d4040c957966781f777c,11content+2shared,421wire,57 320 426байт|
|Root adoption|Побайтная копия принята; ранний uploaded:false вD-adoption.json — срез до последующих внешних действий|
|Opaque fixture|18/18PASS|
|ActualD browser|Исторические body-canvas18/18PASS:3движка ×390/961/1440 ×2темы. Внешнийt-footer не был покрыт; позднее найден светлый угол. Это не финальная host-приёмка|
|Actual Header|3/3PASS: фон#252525,радиус20px,gap8px,красныйclosed-dot8px; root просмотрелFirefox-скрин|

C37native jobs, ручные3-engine/touch, настоящий SDK transport и24лабораторных benchmark samples сохраняются как доказательства с их исходной средой и версией. Точное равенство compiled inputs позволяет не повторять клиентскую сборку, но не превращает замерыC в замерыD. SDK HTML доставлялся synthetic fixture; это не подтверждает публичный HTTPS или ingestion кабинетов. Физические устройства исключены владельцем.

## E — текущий опубликованный host-fix

D `d4040c957966781f777c` исправил opaque body/#allrecords, но его18/18 actual canvas и Header3/3 не покрыли внешние светлые углы native#t-footer в тёмной теме. Этот дефект найден финальным просмотром; D остаётся ограниченной историей, а не итоговой host-приёмкой. E расширяет единственный HOST_CSS reset на body/#allrecords/#t-header/#t-footer. Все421 compiled inputs совпадают сD;13body точно совпадают после замены build-prefix,13HEAD отличаются только расширенным reset. C37native jobs, SDK transport и24benchmark samples сохраняют исходную область и не называются новыми измерениямиE.

Clean CI E: ownership35/7/9,source384,release4,9Python/46PASS. ПовторныйAstro build для этого host-only delta не заявлен. NativeE18GREEN проверяет прозрачность всех4wrapper и3footerpixels в каждом случае. Official publish13/13 и13postpublishHEAD/codeEXACT завершены, Cloud421/421, registryE. ActualE18/18 technical HTTPS GREEN; Header3/3 сохранил gap8px, radius20px, фон#252525 и8px status-dot. После добавленного владельцем исключения Happ/Xray основной https://soyuz.hair также прошёл18/18 усиленных canvas/footercorner cases в3движках, обе темы и390/961/1440px; HTTP12/12PASS,177currentresources. Доказательства: HOST_CANVAS_65D.md и tmp/planning/iteration65/host-canvas/E-main-public/.

## MIME, доставка и публикация

Canonical MIMEv4 задаёт font/woff2,font/woff,font/ttf,font/otf,image/webp,image/jpeg,image/png,image/avif независимо от Windows mimetypes. MIME входит в build digest и immutable identity `SHA256(MIME + NUL + source bytes)`. Исправленный MIME получает новыйURL, старый immutable объект не перезаписывается. Gzip использует пустойfilename,mtime0,OS255; zlibVersion входит вdigest. Относительные newsJSON/image ссылки сохраняют общий build-prefix. ЭкспортёрD имеет revision5 дляcanonical LF/host reset; это не отменяет MIMEv4-контракт.

Root подтвердилCloud421/421wire SHA,MIME,encoding/cache. Девять отдельных MIME/CORS-запросов дляfont/woff2,font/ttf,image/webp по3origins прошли в своей проверенной области. Точный E перенесён в13nativeHEAD/T123 через официальныйMCP, shared опубликованы перед11content. Postpublish13/13HEAD/code exact; registry теперьE. Actual technical HTTP12cases прошли:11страниц+unknown404, currentEasset closure, Twitter/lang/alt/canonical. ActualD canvas18/18 и Header3/3 в HOST_CANVAS_65D.md остаются ограниченной историей: затем найден внешний светлыйt-footer. ActualE18/18 technical HTTPS GREEN; Header3/3 сохранил gap8px, radius20px, фон#252525 и8px status-dot. После добавленного владельцем исключения Happ/Xray основной https://soyuz.hair также прошёл18/18 усиленных canvas/footercorner cases в3движках, обе темы и390/961/1440px; HTTP12/12PASS,177currentresources. Доказательства: HOST_CANVAS_65D.md и tmp/planning/iteration65/host-canvas/E-main-public/.

## Осталось закрыть

- [x] СохранитьD18/Header3 как bounded history с найденным footer-дефектом; D не финальная host-приёмка.
- [x] ActualE18/18 technical HTTPS GREEN; Header3/3 сохранил gap8px, radius20px, фон#252525 и8px status-dot. После добавленного владельцем исключения Happ/Xray основной https://soyuz.hair также прошёл18/18 усиленных canvas/footercorner cases в3движках, обе темы и390/961/1440px; HTTP12/12PASS,177currentresources. Доказательства: HOST_CANVAS_65D.md и tmp/planning/iteration65/host-canvas/E-main-public/.
- [ ] Зафиксировать окончательный исходныйE в изолированной codex/soyuz-release, получить собственный Actions-result и подключить локальныйGit к точному source snapshot. Пока remote509fed9… и run43800396980success относятся к первому срезу; SF main не менялся.
- [x] Повторить поисковыеUI: GSCsitemap16Nov принят, но «Не получено»,0URL; Яндексfreshreadonly/Adddisabled, sitemap не отправлен.
- [ ] Дождаться внешнего полученияGoogle sitemap/разрешить доступную отправкуЯндекса и зафиксировать результат без обещанияиндексации. GSC LIVE09:10:23/RequestIndexpriorityqueue не доказывает already indexed.
- [x] Владелец самостоятельно добавил сайт в исключения Happ/Xray. После этого основной HTTPS прошёл HTTP12/12 и18/18 browser canvas/footercorner cases в3движках. Агент не менял VPN, DNS или проверку сертификата. Прежний timeout сохранён как история маршрута, а не текущий отказ сайта.

Исторические snapshot и журналы не переписываются. GitHubCI, Cloud upload, native fixture, actual technical HTTP и публичная браузерная приёмка остаются разными доказательствами. Реальные записи/покупки не создаются.
