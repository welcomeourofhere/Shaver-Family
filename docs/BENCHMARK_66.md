# Лабораторное сравнение E и66

16.11.2026. Принятый основной набор —24 samples:18 cold-load и6 подходов к настоящей карте. Отдельный каузальный ON/OFF-набор —6 диагностических samples. **В исходном CI66 обнаружен и подтверждён дорогой adaptive floating hotpath.** Root подготовил исправление; его последующая проверка учитывается отдельно и не подменяется этими цифрами.

Это Chrome на Windows с локальными native-оболочками, а не полевая статистика, физический телефон или измерение FPS. В локальном сервере CSS/HTML передаются **без gzip**. Абсолютный slowphone LCP3.3s нельзя приписывать опубликованной Cloud/Tilda-доставке.

## Версии, условия и доказательства

- E: build`945ad6ddd3e70d5cc3c4`, `http://127.0.0.1:4381/`, `tmp/planning/iteration66/baseline-E/site`.
- CI66: build`d72a049b273131f61090`, `http://127.0.0.1:4382/`, `tmp/planning/iteration66/ci-native/site`.
- Каждый cold sample использует новый контекст, выключенный HTTP-cache, light theme, DPR1, normal motion и8s окно. Desktop1440×900 и phone390×844 — без throttle. Slowphone —390×844, CPU×4, CDP latency150ms, download200000B/s, upload93750B/s.
- После cold-снимка выполняются безопасные взаимодействия: две клавиши Hero на ПК либо trusted CDP touch открытия меню и Escape на телефоне. Формы записи, оплаты и сообщений не отправляются.
- Map —1440×900, CPU×4 и те же сетевые ограничения. Реальный wheel-путь от About к карте и12s окно; родной iframe/SDK не подменяется. Сохраняются фактические сетевые ресурсы, геометрия, main-target CPU и интервалы rAF-callback. Это не аппаратные кадры и не FPS.
- Аналитика отклонена. GitHub endpoint одинаково блокируется, чтобы каждая сборка использовала свой замороженный local fallback. Первые два news payload вместе с медиа совпадают; хвост списков различается из-за согласованного стоп-листа. ID и контент в основном benchmark не переписывались.
- Порядок в каждой группе чередуется: E→66,66→E,E→66. В3-map-паре используется такой же порядок. Контент провайдера и DNS остаются внешними переменными.

Сценарий: `tests/new66benchmark.py`. Принятый отчёт с полными ресурсами — `tmp/planning/iteration66/benchmark/d72-accepted/results.json`.

Первый запуск `d72-paired` прерван после обнаруженного параллельного browser job;12 частичных samples помечены `CONTAMINATED.json` и **полностью исключены**. Во втором запуске `d72-paired-isolated` собраны24 samples. В10:44:36UTC root сообщил о возможном HMR от изменения favicon-link order. Окно±5s пересекло только map66 run2 (10:44:26.290–46.514UTC); целиком обе версии maprun2 заменены новым `d72-map2-replacement` после согласованного ACK. Приняты ровно22 исходных+2 заменяющих samples. Исходные файлы не переименованы и не перезаписаны; provenance и SHA обоих отчётов включены в accepted JSON. Замороженные папки до/после неизменны.

Команды воспроизведения:

```powershell
python -X utf8 tests/new66benchmark.py --label NEW_LABEL
python -X utf8 tests/new66benchmark.py --label NEW_PAIR --map-run 2
python -X utf8 tests/new66benchmark.py --label NEW_ACCEPTED --merge-replacement ORIGINAL/results.json REPLACEMENT/results.json
```

Повтор пары разрешён только для явно зафиксированного вмешательства, не для выбора более приятного результата.

## Cold-load и взаимодействия

| Профиль | LCP E,ms, три пары | LCP66,ms, те же пары | Медианы E→66 | Медиана парной разницы66−E |
| --- | --- | --- | --- | --- |
| Desktop |336,368,272|236,260,240|336→240|−100ms|
| Phone |140,112,108|108,116,116|112→116|+4ms|
| Slowphone |3244,3228,3260|3268,3300,3332|3244→3300|+72ms|

Между медианами slowphone разница+56ms; это малый локальный эффект на трёх samples, не основание обещать полевое улучшение/ухудшение. На desktop все три пары быстрее, на обычном phone знак смешанный. Нельзя переносить эти локальные миллисекунды на p75 или реальный мобильный интернет.

CLS по стандартному max session-window (пауза1s/окно5s, без recent input) —0 во всех18 cold samples. Long tasks cold slowphone: E6/7/8 с суммой609/656/814ms;66 —6/6/8 с599/610/905ms. Это не доказывает общего выигрыша: у66 есть более тяжёлый третий sample.

| Профиль | Completed non-video body E |66 | Разница | Наибольшая EventTiming duration E→66 |
| --- | ---: | ---: | ---: | ---: |
| Desktop |1675518B|1736817B|+61299B|48→40ms|
| Phone |952813B|1015531B|+62718B|72→40ms|
| Slowphone |952813B|1015531B|+62718B|232→264ms|

EventTiming — ограниченные две лабораторные активации после8s, не field INP. Минимальный observer threshold16ms и квантование сохраняются; отсутствие записи не значит нулевую задержку. На slowphone максимум input delay около35ms в обеих версиях; значительная часть общей duration приходится на presentation/style, а не на один JS-handler. Все18 взаимодействий выполнены, own resource failures и own page errors отсутствуют.

В дополнительном startup payload66 **53450B — четыре заранее подготавливаемых audio**, оставшиеся≈9.3KB приходятся на HTML/CSS/JS. Аудио начинает грузиться после инициализации модулей, позже LCP; его отложенная подготовка уменьшает startup traffic, но сама по себе не объясняет/не исправляет3.3s LCP. После первого взаимодействия эти байты могут понадобиться: это перенос работы по необходимости, а не обещание уменьшения bytes за весь визит.

## Что именно задерживает slowphone LCP

На телефоне LCP — **текст `.hero-heading-mobile`**, а не фотография/видео. На ПК — первый news image`1962-54573c1a6e43-1086.webp`. Первые LCP-ресурсы сопоставимы между сборками.

Показательный paired run2: E FCP=LCP3228ms,66 FCP=LCP3300ms. Molot15392B заканчивается примерно на0.96s; последняя блокирующая CSS около88.8KB — на3.11s. HTML446232B продолжает приходить примерно до5.09s. CSS и модульные запросы конкурируют за общий throttled transport; это не причина начинать новую обработку изображений.

Двадцать ресурсов, завершившихся перед LCP, полный waterfall и MIME/размеры находятся в `tmp/planning/iteration66/benchmark/d72-static/static.json`, `criticalPathWaterfalls`. Это waterfall диагностика, не полный dependency trace и не измерение публичного origin.

### CSS и реальный gzip

| CSS | Local raw bytes | Существующий Cloud gzip payload |
| --- | ---: | ---: |
| `_legal_.DFGN5hhf.css` |73970B|10407B|
| `index.D1f90YIt.css` |88837B|12628B|
| `index.BGAJ6RIl.css` |7756B|1612B|
| `index.CdSm5Ith.css` |7812B|1416B|
| **Все четыре** |**178375B**|**26063B**|

Cloud content до gzip178847B:472B разницы с local fixture возникают из-за CDN URLrewrite. Размеры gzip взяты из уже созданного manifest и сверены с размером/SHA payload, новая компрессия не выполнялась.

Export guard`:not(#soyuz-export-style-a#soyuz-export-style-b)` занимает56160B raw, около31.5%. Это стоимость isolation в распакованном CSS, а не столько же сетевых байтов: повторяющийся guard хорошо упакован в существующий gzip. Из1060 различных contextual rules найдено0 точных cross-file duplicates. Имя`_legal_` обозначает общий chunk SiteFrame/system/header/footer, а не ошибочное подключение всей оферты.

Удалять guard или откладывать общий chunk по имени нельзя: это нарушает экспортный/первый-render договор. Для дальнейшей работы рассматриваются доказанное разделение above-fold/ниже расположенных правил и конкуренция module preloads, с проверкой уже gzip-доставки; обещания выигрыша по одному raw local числу нет.

## Подход к реальной карте

| Run | rAF callback p95 E→66 | Самый большой callback gap E→66 | Gaps>50ms E→66 | Main-target ScriptDuration E→66 |
| --- | --- | --- | --- | --- |
|1|16.6→20.9ms|75.0→37.6ms|1→0|801.5→2260.6ms|
|2, заменённая пара|12.5→20.7ms|41.7→70.9ms|0→1|792.8→2199.1ms|
|3|12.5→16.7ms|29.1→33.4ms|0→0|752.6→2025.9ms|

У обеих версий медиана количества gaps>50ms равна0, main-frame LongTask observer в этом12s окне не зарегистрировал задач>50ms. Это **не означает отсутствие коротких дорогих callbacks**: суммарная ScriptDuration66 стабильно выше примерно на1.3–1.46s, а callback-p95 хуже в каждой паре.

Положение и высота карты во всех samples стабильны; top10729.64px/height673.08px. Ширина меняется по утверждённой геометрии: E684px,66≈704.55px. Все6 provider documents загрузились. На каждой стороне отдельно видны одинаковые внешние adsync проблемы: DNS`events.myweb3id.io` и HTTP400`prebid.admatic.com.tr`. Они не записаны как own code failures. Provider traffic в окне около3.26–3.29MB, с внешней вариативностью; общий map-byte delta не является чистой оценкой кода сайта.

Последние изображения `map-E/66-1..3.png` находятся в raw/replacement каталогах. Это конечные кадры. Они и callback gaps не доказывают отсутствие физических compositor-flashes, Safari/Liquid Glass или мерцания на телефоне.

## Каузальная проверка floating

Чтобы отделить новый UI от provider, выполнены3paired OFF/ON только на неизменном CI66. В response fixture изменяется **единственное условие adaptive-блока** compiled`SiteSettings.LAHz_pht.js`: `v.length`→`false`. ON отдаёт byte-identical original тем же fixture-транспортом. Настройки, back-to-top и остальные модули сохраняются; source/package не редактируются. Исходный SHA`65385466e01b663b921a6f0d0fbc0a2f00ac1c8e14b79d32245003528c120100`, AST guard позиции1296–1304. Каждый sample подтверждает ровно один fixture-hit.

CDP CPUProfiler получает script/executionContext/frameId. В attribution включаются только main-frame scripts; iframe/provider не выдаются за собственный hotpath. Native/style cost в стеке adaptive-функций учитывается inclusive, поэтому это не только их leaf JS.

| Медиана трёх samples | OFF | ON |
| --- | ---: | ---: |
| Main-target ScriptDuration |771.2ms|2230.0ms|
| rAF callback p95 |12.6ms|20.8ms|
| Main-frame adaptive inclusive sampled time |0ms|1550.8ms|

Это подтверждает причинный вклад adaptive floating, а не просто корреляцию разных версий карты. Файлы — `tmp/planning/iteration66/benchmark/d72-floating-causal/results.json` и `profile-on/off-1..3.json`. В каждой группе provider document3/3, own failures0, папки неизменны. Profiler/debugger добавляют одинаковую диагностическую нагрузку обеим сторонам; эти цифры не смешиваются с исходными24samples.

Root подготовил read-all-before-write, cacheφ, максимум80ms между обновлениями с trailing и устранение повторных записей одинакового selectionSurface. Проверка исправленного кандидата должна идти отдельным набором; исходный d72 не объявляется исправленным задним числом.

Исправленный frozen native-кандидат `cc4409df87d6120375e6` на4383 прошёл функциональный gate: CORE27/27 и floating QA в200 позициях (400 состояний кнопок,390 видимых) при961/1024/1100/1280/1440px в обеих темах. Контраст, palette/surface,3 настройки, смена темы, Escape и возврат фокуса — без findings/page errors. Доказательство: `artifacts/iteration66/footer-utilities/cc44-floating/report.json`. Для frozen-проверки создан QA-only runner с теми же assertions, который сверяет37 compiled JS/CSS вместо изменяемых параллельными агентами исходников: их SHA до/после равны; provenance — `tmp/planning/iteration66/cc44-floating-runner-provenance.json`.

Это функциональный gate, не атрибуция выигрыша. AST-fixture исправленного кандидата подготовлен без браузера: `SiteSettings...BCbRJdfm.js`, SHA`8ba7669b5a7bcf5f66b6fce34bc587b68d0b3e980da09fd27cd7c0638eec25df`, единственное условие`E.length`.

### Атрибуция исправленного cc44

После отдельного strict ACK root и подтверждения SEO-agent о закрытых browsers выполнены **6 новых samples,3пары OFF/ON** тем же протоколом на4383. Во время слота root/агенты не запускали browser/build/source writes. Это узкая проверка исправления cc44, а не финальная проверка следующих изменений Works/контактов/подвала.

| Run | Main-target ScriptDuration OFF→ON | Adaptive inclusive OFF→ON | rAF callback p95 OFF→ON | Gaps>50ms OFF→ON |
| --- | --- | --- | --- | --- |
|1|847.0→1234.3ms|0→419.8ms|16.7→20.9ms|3→1|
|2|801.4→1026.0ms|0→256.3ms|12.5→16.6ms|0→0|
|3|807.4→1106.2ms|0→297.3ms|12.5→16.7ms|1→0|
|Медиана|807.4→1106.2ms|0→297.3ms|12.5→16.7ms|1→0|

У исправленного adaptive-блока sampled main-frame inclusive time снизилось с прежней медианы1550.8ms до297.3ms, примерно на**81%** в этих диагностических наборах. Остаточный вклад не равен нулю: ON остаётся дороже OFF примерно на299ms ScriptDuration за12s, а callback p95 выше примерно на4.2ms. Отсутствие main-frame задач>50ms и меньшая медиана gaps не превращаются в обещание отсутствия всех задержек или физического мерцания.

Во всех6 случаях карта загрузилась, геометрия before/after стабильна, own resource/page errors0, frozen-folder SHA до/после совпадают. Сохранились отдельные внешние adsync DNS/HTTP400 проблемы, одинаковые по категории с прежним набором. Конечные кадры третьей пары `map-off-3.png`/`map-on-3.png` осмотрены: сайт/карта отрисованы; адаптивные кнопки сохраняют узнаваемые иконки и меняют поверхность. Кадры не являются filmstrip или аппаратной приёмкой мерцания. Прокрутка следует одному адаптивному wheel-протоколу с50px допуском остановки, а не побитно одинаковой траектории.

Доказательства — `tmp/planning/iteration66/benchmark/cc44-floating-causal/results.json`, шесть `profile-off/on-N.json` и шесть отдельных `map-off/on-N.png`. Для новых A/B кадров QA harness исправлен: разные варианты больше не записывают одно имя `map-66-N.png`; прежние JSON/profile и старые каталоги не переписаны. Attribution по frame/context и response-only guard остались прежними.

## Что не заявляется

Нет field p75/INP, CrUX, физического телефона/Safari, аппаратного FPS или измерения публичного TLS/CDN. Громкость и реальная вибрация здесь не калибруются. Не менялись изображения, компрессия, SDK карты, provider HTML или production-пакет. Лаборатория показывает конкретный UI hotpath и приоритеты проверки; она не доказывает, что абсолютно все сценарии сайта быстрее.
