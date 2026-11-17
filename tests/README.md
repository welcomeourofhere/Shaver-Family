# Проверки прохода66

Последний текстовый подвал: `python -X utf8 tests/new66footer-text-columns.py --origin http://127.0.0.1:4321/ --label NEW_LABEL` —24width/theme/text200 cases,15Tabcontrols, sharedhours иnativebookingroute; обычные ссылки32pxПК/44pxcompact, кнопки44px/12px. Точный договор — `docs/FOOTER_TEXT_66.md`.

Слои кешбэка: `python -X utf8 tests/new66cashback-layers.py --origin http://127.0.0.1:4321/ --label NEW_LABEL` —16cases, foregroundpixels/sourceart и отдельная legacy-stylefixture без изменения продукта. Границы — `docs/CASHBACK_LAYER_66.md`. Эти проверки запускаются последовательно после sourcefreeze, без настоящих providers.

Регрессия переноса Header на второй ряд: `python -X utf8 tests/new66header-regression.py --origin http://127.0.0.1:PORT/ --label NEW_LABEL`. Запускать последовательно на неизменной compiled/native-оболочке после общей сборки. Набор покрывает 72 сочетания ширины/высоты/темы/размера текста, включая опасный диапазон 1039–1061 CSS px; 37 popup/keyboard-сценариев, общие 8 px gap/цвет/радиус и шесть состояний часов в обеих темах. Удвоение текста задано ролями компонента 13/16 → 26/32 px, без уменьшения полей и полной подписи записи. Сохраняются source hashes, реальные снимки и отдельные ошибки. История причины и принятый контракт — `docs/HEADER_REGRESSION_66.md`. Текущий HMR-проход не заменяет итоговую compiled-проверку.

Узкая проверка66 плаката подарков/сертификатов/стрелок: `python -X utf8 tests/new66gifts-poster.py --origin http://127.0.0.1:4321/ --label NEW_LABEL`. Запускать после sourcefreeze, внешние providers блокируются. Текущий worker2-контракт: на961/1100/1440px обе темы, clipping, отсутствие HTML-плашки и серые тона; на390/800/960px —0запросов скрытого рисунка до подвала. Покрытие/история и границы — `docs/GIFTS_POSTER_66.md`.

Новые: `new66interactions.py`, `new66mobile-platform.py`, `new66footer-utilities.py`, `new66benchmark.py`. Приёмка начинается на замороженной nativeоболочке. b52 и432CI различаются сборкой чанков: результаты повторяются, не переименовываются. Favicon проверяет `66seo-assets.test.mjs`, nativefallback — `66booking-fallback.test.mjs`.

# Актуальные проверки СОЮЗа

Проход69: `python -X utf8 tests/new69reviews-start.py --origin http://127.0.0.1:PORT/ --engine chromium --label NEW_LABEL` проверяет33сценария подготовки отзывов; повторить последовательно дляFirefox/WebKit. Проверяются первый подход/ввод, полный цикл карточек, чтение и прерывания, resize до/после подготовки,200%текста,обе темы/режима движения и noJS. Для точечной повторной проверки есть `--only-method resize-after reading-interrupt`; исходные отрицательные отчёты сохранять. Доступность карточек проверяется независимо от стратегии момента инициализации; после cleanup геометрические данные и inline styles не меняются от resize/scroll.

Парный lab остаётся у `new66benchmark.py`: `--startup-ms 10000 --seed 90210 --include-about-jump` добавляют одинаковое десятисекундное page-clock окно и наблюдение **до** перехода кAbout, чтобы учесть отложенную подготовку при прокрутке. TimespanTBT считается отFCP до конца окна, не является LighthouseTTI/полевымINP. До запуска подтвердить равенство полного замороженного news/media-графа и завершение прочих браузерных задач; подписиE/66 обозначают входыbaseline/candidate, фактические сборки определяются переданными папками и хешами плана.

Размеры постеров проверяет существующий `new67content-qa.py --origin URL --label NEW_LABEL --build BUILD --only posters --poster-dpr`:9сочетаний390/600/960px×DPR1/2/3, фактическийcurrentSrc/ширина варианта, готовые первые два изображения, отсутствие дальних запросов и trustedtouch. Локальный и настоящий HTTPS результаты хранить отдельно.

Граница фона Тильды65D проверяется отдельно: `python -X utf8 tests/iteration65-host-canvas.py --origin http://127.0.0.1:PORT/ --engine chromium --label LABEL` (затем Firefox/WebKit). Сценарий проверяет390/961/1440px и обе темы: фон `html` равен `--surface`, `body.t-body` и `#allrecords` прозрачны, видимый пиксель полотна совпадает с темой; сохраняет кадры промежутка страницы, контактов и подвала. LABEL всегда новый, существующие доказательства не перезаписываются. Сначала ожидается RED на отдельной оболочке неизменённогоC с непрозрачным фоном Тильды, затем GREEN наD; после публикации — тот же сценарий на настоящем HTTPS без подмены CSS/сетевых ответов. Это узкий платформенный регрессионный тест, а не повтор всей UI-приёмки.

Проход65 находится в подготовке к публикации. Последние уточнения владельца и визуальный аудит — `docs/VISUAL_AUDIT_65.md` и верхний раздел `docs/DESIGN_SYSTEM.md`. Старые варианты скрытия scrollbar, внутренних Hero-стрелок и названия «Интервью» не являются критериями новой приёмки. Заголовки тёмной темы жёлтые, scrollbar красный в обеих темах.

Обязательный общий порядок: `astro check`; private build и все Node-unit; release build с `SOYUZ_RELEASE=1` и metadata/analytics; `prepare-tilda-release.py`; Python unittest discover. Затем неизменяемая native-оболочка из этого manifest через `freeze-release-fixture.py`. Браузерные задания выполняются последовательно, с одной замороженной версией; HMR не используется для долгой итоговой приёмки, поскольку перезагрузка может прервать открытый сценарий. Активные проверки65: `iteration65-shell.py`, `iteration65-visual-fixes.py`, `iteration65-footer-contacts.py`, `iteration65-team-labels.py`, `iteration65-utility-icons.py`, `iteration65-hero-controls.py`, `iteration65-hero-text-fit.py`, `iteration65-certificate-mirror.py`, `iteration65-desktop-text-fit.py`, `iteration65-scrollbars.py`, `analytics-cookie65.py` и отдельные сценарии header/modal. Их CLI/URL задаются самими сценариями; точные применённые команды и JSON фиксируются в итоговом отчёте. Для актуального cookie-контракта66: `python -X utf8 tests/analytics-cookie65.py --build dist --engine chromium --label NEW_LABEL`; vendors подменяются, synthetic public hostname читает только указанную локальную сборку. Путь отказа проходит через настройки; точное покрытие — `docs/COOKIE_66.md`. Нативная оболочка не содержит сторонних скриптов Тильды и не доказывает публичную доставку.

Новая сборка после уточнений не равна промежуточному `a38bcf27b60562930f99`: его ресурсы проверены в Облаке, но страницы этого кандидата не публиковались. Чистый source/CI-прогон должен использовать новый финальный media-lock и доступные Cloud-ресурсы, а не старый rehearsal64.

Проход64: `node node_modules/astro/astro.js check`; private build и `node --test tests/*.test.mjs`; затем release build с `SOYUZ_RELEASE=1`, `node --test tests/metadata.test.mjs tests/analytics.test.mjs`, `python -X utf8 scripts/prepare-tilda-release.py`, Python unittest discover. Новые реальные сценарии — `iteration64-runtime.py --engine chromium|firefox|webkit` (normal/reduced loader, короткая высота About, меню), `iteration64-shell.py` с теми же engine (native shared wrappers и переходы), `iteration64-analytics.py` (vendor gate, отказ/повтор/отзыв, без исполнения сторонних counters). Полевая доставка проверяется отдельно. Бенчмарк — device-performance.py --phase64 --runs3, сохранённая source-export63 против кандидата при одинаковом статическом транспорте. Не выполнять browser jobs параллельно измерениям. Состояние доказательств и настройки — RELEASE_TRACKER.md/TILDA_SETTINGS_64.md.

Проход63: `astro check`; частная сборка и `node --test tests/*.test.mjs` (исторические тесты проверяют локальный noindex); `python -X utf8 tests/iteration63-news.py`; release-сборка с `SOYUZ_RELEASE=1` и `node --test tests/metadata.test.mjs tests/analytics.test.mjs`; `python -X utf8 scripts/prepare-tilda-release.py`; `python -X utf8 -m unittest discover -s tests -p release_package_test.py`. Проверка опубликованной Тильды — `python -X utf8 tests/iteration63-live.py`, результаты в tmp/planning/iteration63/live.json. Ожидание внешнего iframe и реальные новые вкладки — iteration63-booking.py. Полный исторический проход62 ниже не доказывает выпуск63 и сохраняет прежние ожидания ПК-сертификата; действующее поведение — новая вкладка на всех размерах. Фактические подтверждения — ITERATION_63.md.

Текущий проход62: docs/ITERATION_62.md, общая область — docs/SITE_REFINEMENT.md. Проверяются одна сборка и неизменность src/content/public. Новые сценарии: отдельные портреты/адаптив Честной цены, часы и цвета, скроллбары/нативная передача touch, лёгкий удерживаемый drag,4отзыва/раскрытие/канонические мастера, iframe сертификата на ПК/новая вкладка до960px.

Последовательность PowerShell после последней правки; каждый шаг должен завершиться с exitCode=0. Браузерные задания и особенно замеры выполняются последовательно:

```powershell
New-Item -ItemType Directory -Force tmp/planning/iteration62 | Out-Null
node node_modules/astro/astro.js check *> tmp/planning/iteration62/check.log
node node_modules/astro/astro.js build *> tmp/planning/iteration62/build.log
node --test tests/*.test.mjs *> tmp/planning/iteration62/unit.log
python -X utf8 -m unittest discover -s tests -p '*_test.py' *> tmp/planning/iteration62/python.log
python -X utf8 tests/iteration62-browser.py
python -X utf8 tests/iteration62-additions.py
python -X utf8 tests/iteration62-interviews.py
python -X utf8 tests/iteration62-news.py
python -X utf8 tests/device-regression.py --phase 62
python -X utf8 tests/iteration60-production.py --phase 62
python -X utf8 tests/iteration61-masters.py --phase 62
python -X utf8 tests/iteration61-interruptions.py --phase 62
node tests/device-legacy.mjs --phase 62
python -X utf8 tests/device-compatibility.py --phase 62 --label accepted
python -X utf8 tests/device-performance.py --phase 62 --runs 3
python -X utf8 tests/device-dock-performance.py --phase 62 --runs 3
python -X utf8 tests/iteration62-map-performance.py
python -X utf8 tests/iteration62-acceptance.py
```

`tmp/baseline62/dist` — неизменённый итог61. `--resume` общей регрессии допустим только для того же полного набора, исходников и dist; collector отклоняет другие хеши.119Node/26Python,108Astro/10страниц.131сценарий owner-corrections,48сценариев добавлений,72интервью и9новостей/тем в3движках; общий набор16команд/366сценариев,7целевых команд, мастера/прерывания,60современных и8старых профилей.18холодных/6dock-образцов и8подходов к настоящей карте. Последние числа — состав набора; успешное выполнение подтверждает только фактический `acceptance-summary.json`.

Старые UI/reading-сценарии проверяют раскрытый полный бенто;4карточки и сохранность первой группы отдельно проверяет additions.py. Без JavaScript показан полный список, как fallback FAQ; первоначальную геометрию режима с JavaScript проверяют неизменённые сценарии задержанных скриптов. Старый маршрут покупки через contact-dialog заменён проверкой ссылки; настоящие iframe/popup-клики, нижняя панель и переключение с записью проверяются additions.py в3движках. Provider fixture подтверждает маршрут/поведение, не живой каталог/оплату. Фактический ответ YCLIENTS и успешный GitHub-run фиксируются отдельно в ITERATION_62.md.

Исторический offer-performance61 не используется как приёмка62: по указанию владельца изменена удерживаемая прогрессия/шаг, поэтому позы намеренно различны. Непрерывность/возврат/отмена проверяются реальным drag и математикой; физическая калибровка spring не менялась. Нельзя выдавать старые1080→6чтений или оконные RAF-интервалы за новый общий FPS.

Legacy news fixture берёт фактический адрес из `site.newsFeedUrl`, отдаёт CORS `*` и те же проверенные WebP из public. Подмена только локального `/data/news.json` после переноса feed на GitHub проверяла блокировку стенда, а не отсутствие AbortSignal.any/timeout. Внешние запросы остальных legacy-сценариев остаются заблокированными.

## Сохранённый набор прохода61

Проход61 — предыдущий полный локальный обход. Общая цель и границы: docs/SITE_REFINEMENT.md; прежний результат: docs/ITERATION_61.md. Его сводка iteration61-acceptance.py относится к своей сборке. Исследовательский обход180состояний хранится отдельно и не подменяет новую приёмку dist.

Сохранённая последовательность61 в PowerShell:

```powershell
New-Item -ItemType Directory -Force tmp/planning/iteration61 | Out-Null
node node_modules/astro/astro.js check *> tmp/planning/iteration61/check.log
node node_modules/astro/astro.js build *> tmp/planning/iteration61/build.log
node --test tests/*.test.mjs *> tmp/planning/iteration61/unit.log
python -X utf8 -m unittest discover -s tests -p '*_test.py' *> tmp/planning/iteration61/python.log
python -X utf8 tests/device-regression.py --phase 61
python -X utf8 tests/iteration60-production.py --phase 61
python -X utf8 tests/iteration61-masters.py
python -X utf8 tests/iteration61-interruptions.py
node tests/device-legacy.mjs --phase 61
python -X utf8 tests/device-compatibility.py --phase 61 --label accepted
python -X utf8 tests/device-performance.py --phase 61 --runs 3
python -X utf8 tests/iteration61-offer-performance.py
python -X utf8 tests/device-dock-performance.py --phase 61 --runs 3
python -X utf8 tests/iteration61-acceptance.py
```

Сохраняются tmp/baseline61/dist (итог60) и tmp/baseline61-offers/dist (состояние до сокращения CSS-чтений). Эталон loader№04 wrapper обслуживает из artifacts/preloader-options сам. Браузерные задания и особенно лабораторные образцы выполняются последовательно. Все движки используют изолированные тестовые контексты. Настройка старых движков и трактовка метрик описаны ниже; физические телефоны исключены владельцем.

Ниже — сохранённые рецепты и результаты предыдущих проходов; их статус относится к дате соответствующей проверки.

Проход60 — предыдущая локальная функциональная приёмка:99Node/16Python,104файла Astro без диагностик,6страниц,366сценариев общей регрессии,30групп новых взаимодействий в Chrome/Firefox/WebKit и16адаптивных сочетаний. После check/build/unit выполняются `python -X utf8 tests/device-regression.py --phase 60` и `python -X utf8 tests/iteration60-production.py`. Нужна сохранённая `tmp/baseline60/dist`; wrapper сам обслуживает dist, baseline и исходную галерею loader№04. Результаты: tmp/planning/iteration60/{regression,targeted}/verification.json. `--suites` выбирает затронутые группы, `--resume` разрешён только для того же набора и неизменённых исходников/сборки. Интерпретация исторических планшетных свайпов и pointerId обновляется во временных копиях тестов. Область — docs/ITERATION_60.md; новая общая цель — docs/SITE_REFINEMENT.md.

Проход57 — сохранённая полная приёмка оптимизации, а не измерение новой сборки60.93Node,10Python,101файл Astro check без диагностик,5страниц,366сценариев регрессии,60проверок современных и8проверок старых движков,18холодных запусков и6образцов меню. Итог — tmp/planning/iteration57/acceptance-summary.json; контекст — docs/ITERATION_57.md. Физические телефоны пропущены владельцем и не запрашиваются повторно.

Команды выполняются последовательно:

```
node node_modules/astro/astro.js check
node node_modules/astro/astro.js build
node --test tests/*.test.mjs
python -X utf8 -m unittest discover -s tests -p '*_test.py'
node tests/device-legacy.mjs --phase 57
python -X utf8 tests/device-regression.py --phase 57
python -X utf8 tests/device-compatibility.py --phase 57 --label accepted
python -X utf8 tests/device-dock-performance.py --phase 57 --runs 3
python -X utf8 tests/device-performance.py --phase 57 --runs 3
python -X utf8 tests/device-acceptance.py --phase 57
```

Не запускай другие браузерные задания параллельно лабораторному замеру. Нужны сохранённый tmp/baseline57/dist, Python Playwright с Firefox/WebKit, установленные Chrome/Edge и галерея loader №04 на QA_GALLERY_URL (по умолчанию 127.0.0.1:4323). Старые движки использует отдельный Playwright 1.35.1 вне зависимостей сайта: QA_LEGACY_PLAYWRIGHT указывает каталог его пакета, по умолчанию — временный каталог ОС / soyuz-compat-browser-tools/node_modules/playwright. Бинарники WebKit 16.4 и Firefox 113 устанавливаются CLI этого инструмента. FontTools 4.68.0 — существующий build-only инструмент из scripts/requirements-fonts.txt; исходники шрифтов не заменяются. Генератор Manrope — scripts/prepare-body-fonts.py, проверка — font_resources_test.py.

Регрессия переиспользует исторические сценарии через временные файлы, не перезаписывая старые тесты/отчёты. `--resume` проверяет неизменность сборки и исходников. В ожиданиях заменена загрузка невидимых мобильных новостей; MutationObserver отключается между лентами, нажатие должно действительно попадать в свой контрол. Файлы только своей временной генерации удаляются по завершении. Единая сортировка компонентов пути используется при хешировании в Python и Node. После повторной сборки браузерные результаты нужно получать заново; итоговый сборщик отклоняет несогласованные хеши.

PerformanceObserver/CDP здесь дают локальные образцы, не полевые p75 и не аппаратный FPS. Текущая таблица completedNonVideoBytes включает HTML-документ; потоковые MP4 исключены. Браузерная матрица не выдаётся за физический Safari/Android, реальные заявки или публикацию.

Ниже исторические рецепты предыдущих проходов. Их формулировки текущей приёмки относятся к моменту своего запуска.

Исторический проход55. Выполни `node node_modules/astro/astro.js check`, `node node_modules/astro/astro.js build`, `node --test tests/*.test.mjs`, `python -X utf8 -m unittest discover -s tests -p vk_news_test.py`, затем `python -X utf8 tests/iteration55-production.py`. Текущий результат — 91Node/6Python, 100Astro-файлов без диагностик,5страниц и16браузерных команд/366сценариев; результаты — tmp/planning/iteration55/acceptance-summary.json.

Набор55 добавляет22сценария начальной компоновки/задержанных скриптов/favicon/Hero и10проверок индикатора при удержании мыши, а также3сценария wheel после выпуска reader у края (coarse pointer, мелкий шаг и reduced motion), затем объединяет rails/features/latest/design/feedback/UI/reading, layout/journeys, startup, dock/certificates,85touch, loader и сравнение36ПК-элементов на3ширинах. Короткий перечень получен автоматически из exitCode и PASS-строк `acceptance-summary.json`. Исторические проверки скопированы/адаптированы под явные изменения требований, а не продолжают требовать удалённые кнопку маршрута, About-вкладки, мобильные Hero-слайды или постоянное удержание страницы в отзывах.

`verification.json` содержит хеш dist до/после, хеши исходников, команды и логи. Исключены только ожидаемо изменяемые runtime-выходы `public/data/news.json` и `public/media/news/`; внутри dist эти файлы хешируются. При необходимости повторить только упавший хвост на том же dist допустим `--resume`, который проверяет совпадение хеша и исходников. После изменения продукта нужна новая сборка и применимые проверки. `--captures` сохраняет20снимков в `artifacts/iteration55` с отдельным capture-verification.json. QA_GALLERY_URL указывает сохранённую галерею loader№04, по умолчанию127.0.0.1:4323.

Локальные сценарии Chromium не подтверждают физический Safari/телефон/динамики/вибромотор, реальные заявки, активированное внешнее расписание или публикацию. Исследование Wordstat и учебный прайс имеют собственные даты/границы в docs/research и каталоге.

Ниже исторические рецепты: их формулировки «действующая/текущая приёмка» относятся только к моменту своего прохода. Для прохода55 действовал набор55; текущая приёмка описана выше.

Проход52 — действующая приёмка отзывов, чтения About и контактов. После `node node_modules/astro/astro.js check`, `node node_modules/astro/astro.js build`, `node --test tests/*.test.mjs` запусти `python -X utf8 tests/iteration52-production.py`. Wrapper последовательно выполняет9команд на неизменяемом dist:27UI,18сценариев чтения/адаптива,31layout,25journeys, ранний запуск, движение панели/сертификатов,100touch, общий loader и36сохраняемых ПК-элементов на3ширинах. Правила короткого текста/разнообразия/приоритета видео проверяются также unit-набором на множестве seed. Результаты — tmp/planning/iteration52, снимки — artifacts/iteration52. `--captures` делает реальные локальные снимки без изменения сборки. Старые тесты геометрии проходов50/51 с прежними шрифтами,600px-breakpoint и контактами не являются приёмкой новой композиции. Физический телефон/Safari и публикация отдельно.

Проход51 — отдельная галерея контактов, без замены главной: после `node node_modules/astro/astro.js check`, `node node_modules/astro/astro.js build`, `node --test tests/*.test.mjs` запусти `python -X utf8 tests/iteration51-production.py`. На frozen dist выполняются23сценария галереи и сравнение36ПК-элементов с baseline51 на3ширинах. Обновление20снимков — тот же wrapper с `--captures`, затем повторная сборка и проверка. Манифест картинок сохраняет геометрию, SHA256 файлов и исходников. Итог — tmp/planning/iteration51/verification.json; ограничения — docs/ITERATION_51.md. Полный набор прохода50 остаётся приёмкой основного сайта.

Проход50: node node_modules/astro/astro.js build, node node_modules/astro/astro.js check, node --test tests/*.test.mjs, затем python -X utf8 tests/iteration50-production.py. Wrapper обслуживает frozen dist/baseline49/галерею loader, выполняет14команд в одной QA-сессии без параллельных браузерных процессов. Новые наборы:42сценария отзывов (ровный прямоугольник/4цвета/большой блок только4колонки/короткий текст без scroll/прогресс на стыке/phone auto media без nested swipe/reduced motion/200%),11сценариев отдельного просмотра3×4карточек/6размеров/ползунков,32UI/10stress. Остальные команды проверяют редакционную вёрстку, layout/journeys, startup, движение меню/сертификатов,100touch, loader и36сохраняемых ПК-элементов на3ширинах. iteration50-motion выводит QA-вкладку на передний план перед rAF-сэмплированием; минимум кадров не ослаблен. Это не измерение FPS. Итог — tmp/planning/iteration50-verification.json, логи — tmp/planning/iteration50. Для тестовых исправлений без rebuild допустим --resume-from ИМЯ: SHA и успешный префикс должны совпадать. Новая сборка требует полного прогона. Фокусный набор отзывов QA_REVIEW_FOCUS пишет отдельный -focused.json и не заменяет полный. Снимки: node tests/iteration50-captures.mjs, QA_URL задаёт локальный сервер; artifacts/iteration50. Просмотр дополнительных блоков: /previews/review-extras/. Физический телефон/Safari/публикация/реальная запись остаются отдельными проверками.

Исторический проход49: `node node_modules/astro/astro.js check`, `node node_modules/astro/astro.js build`, `node --test tests/*.test.mjs`, затем `python -X utf8 tests/iteration49-production.py`. Набор обслуживает frozen dist и baseline48, использует отдельную сессию soyuz49-touch.12команд:35UI,16стресс-сценариев (повторная высота, бенто,200%контактов, fade края, локальное видео/ошибка), общий редакционный/layout/journey/ранний запуск/движение/100touch/loader и сравнение35ПК-элементов на3ширинах. Отзывы теперь бенто, поэтому они не участвуют в проверке соседней карточки карусели. Подмена фото услуг проверяется по стабильным service ID. Высота акций может следовать изменённому владельцем тексту; стили/ширины и остальные сохраняемые размеры сравниваются точно. Результат — tmp/planning/iteration49-verification.json, логи — tmp/planning/iteration49, снимки — artifacts/iteration49. Для продолжения после исправления только тестового ожидания допустим `--resume-from ИМЯ`: wrapper проверяет совпадение SHA индекса и успешный префикс; изменение сборки требует полного прогона. Для визуальных снимков текущего loopback-сервера: `node tests/iteration49-captures.mjs` с QA_URL.

Ниже — исторические рецепты и состав прежних проходов; старые production wrappers не являются приёмкой текущего дизайна.

Исторический проход47: после `node node_modules/astro/astro.js check`, сборки и unit-тестов запусти `python tests/iteration47-production.py`. Один замороженный dist и отдельная локальная галерея: покадровое сравнение с исходным №04, управляемые сетевые задержки/ошибки, кешированное фото, смена и отмена услуги, загрузка/таймаут записи и карты, reduced motion;40 ползунков новой десятки, независимость/сброс, mouse/touch/keyboard и200% текста. Затем прежние проверки начальной панели, интервью, адаптива, маршрутов, свайпов и ПК относительно `tmp/baseline47/dist`. Итог — `tmp/planning/iteration47-verification.json`; публикации и реальной записи нет. Для целевых проверок доступны `node tests/iteration47-loading.mjs` и `node tests/iteration47-gallery.mjs` с QA_URL/QA_GALLERY_URL.

Исторический проход46: после сборки запусти `python tests/iteration46-production.py`. Это полный набор для начальной панели до JavaScript/при замедленной загрузке, гибрида интервью, скоростей pointer/keyboard, каруселей и сравнения главной ПК с `tmp/baseline46/dist`. Для последующей изолированной доработки статьи доступен `QA_ARTICLE_FINAL_ONLY=1`: итог пишется в отдельный `tmp/planning/iteration46-final-verification.json`. Полный и финальный прогоны текущего прохода описаны в `docs/ITERATION_46.md`; они не подменяют друг друга.

Ниже сохранены наборы предыдущих проходов; их старые геометрические ожидания применяются только в актуализированной части.

Для прохода43: `python tests/iteration43-production.py` — полный прогон; `python tests/iteration43-final.py` — целевые проверки прерывания мышь→touch, фокуса панели, адаптива, маршрутов, движения панели и ПК. Оба обслуживают локальный dist; второй сравнивает ПК с `tmp/baseline43/dist`. Первичный полный прогон прохода43 выполнен до последующей правки фокуса; после неё выполнен финальный целевой набор. Сведения о нестабильном первом прогоне анимации панели — в `docs/ITERATION_43.md`.

Для мобильных правок прохода42 после сборки: `python tests/iteration42-production.py`. Последовательно выполняются18специализированных сценариев,31layout,25journeys,12motion,15touch и4сравнения ПК с baseline42. Результаты — iteration42-*.json; SHA256 готового dist проверяется до/после. Проверяются все девять коротких лозунгов, вес названия услуги, квадратные фото/общий disclosure/нижний RailControls About, содержимое под передней карточкой, отсутствие выделения текста и порядок/primary/тень панели. Для снимков готового dist: `python tests/iteration42-captures.py`.

Для мобильных акций прохода41 после сборки: `python tests/iteration41-production.py`. Набор проверяет13специализированных сценариев,31layout,25journeys,3native-motion,10touch и4сравнения ПК с baseline41. Результаты сохраняются отдельно в iteration41-*.json. Акции теперь относятся к native, а не custom swipe; общий touch-набор содержит100сценариев вместо исторических105. Нижняя панель и локальные стрелки должны синхронизировать крайние состояния.

Для точечной проверки ширины панели прохода40 после сборки: `python tests/iteration40-production.py`. Она запускает31layout,25journeys и4dock-motion сценария на неизменяемом dist. QA_REPORT_PREFIX сохраняет новые результаты отдельно в iteration40-*.json. Ширина проверяется сравнением с фактической shell, а safe-area — по внутренним контролам. Полный общий набор прохода39 ниже остаётся доступным для более широких изменений.

Для текущего контракта прохода39:

```
node node_modules/astro/astro.js check
node node_modules/astro/astro.js build
node --test tests/*.test.mjs
python tests/iteration39-production.py
```

Последняя команда сама обслуживает неизменяемый dist через loopback на свободном порту, последовательно запускает браузерные проверки и сохраняет SHA256/результаты в tmp/planning/iteration39-verification.json. Публикации и отправки внешних форм нет. Python использует установленный Pillow для проверки alpha оригинала; браузер — уже установленный agent-browser. Ничего устанавливать автоматически не требуется.

31сценарий компоновки/тем/клавиатуры/текста,25маршрутов/контрастов/safe-area/fine-pointer,30сценариев промежуточного движения,100touch-сценариев по новому контракту41,20проб иллюстрации,4сравнения ПК и10снимков. Угол/смещение сертификатов, прерывание pending decode и непрерывное закрытие меню жестом проверяются отдельно. Сценарии чтения личной записи не создают бронирование.

Общие unit-тесты проверяют данные/безопасные URL/оригинальные ресурсы/порядки/математику/типографику. Новая кнопочная разметка проверяется семантически: сохраняются три слота панели и текст заголовка, без требования старых CSS-классов или конкретного br.

iteration37-swipes.mjs продолжает быть общим touch-набором; телефонный контракт услуг обновлён на физический цикл стопки. Остальные iterationNN-файлы сохраняют исторические проверки своего прохода. Не запускай старый геометрический контракт как приёмку новых breakpoints. При новом дизайне обновляй соответствующее ожидание по прямому требованию владельца, сохраняя проверки функций/маршрутов/доступности.

Не запускай два touchBrowser одновременно: они используют сессию soyuz37-touch. Каждый проверяющий процесс создаёт собственную CDP target и закрывает её. Обычная CLI-сессия soyuz32 для ПК/снимков отделена. Первый daemon-open не должен удерживать унаследованные stdout/stderr.

Для диагностики отдельного текущего набора можно указать QA_URL или SWIPE_TEST_URL на локальный сервер. Проверки движения учитывают реальное время, поэтому не зависят от60/120Hz. Смена viewport не является touch-доказательством; используйте Input.dispatchTouchEvent и проверяйте trusted pointerType.

Физический телефон, Safari и отправка внешней формы остаются отдельными видами проверки и не выводятся из локального Chromium.
Для текущего прохода45 сначала собери сайт, затем запусти `python tests/iteration45-production.py`. Набор проверяет реальные соседние карточки и подсказки, увеличение каждого сертификата по кадрам без принудительного сужения, синхронность непрозрачности и геометрии панели, текущие сценарии статьи, меню, ширин, маршрутов, прерывания и фокуса. Итог и проверка неизменности dist — `tmp/planning/iteration45-verification.json`. Для визуальных снимков доступен `node tests/iteration45-captures.mjs` при запущенном локальном сайте.



Целевые проверки прохода 58: `python tests/iteration58-focus.py` и `python tests/iteration58-bento.py`, базовый адрес задаёт QA_URL. Проверяют новые свайпы услуг/чтение/цвет вопросов/логотип и среднюю сетку отзывов; не заменяют полную матрицу 57. Node-набор теперь содержит 94 теста. Итог — docs/ITERATION_58.md.


Проход59 — `python tests/iteration59-browser.py` (QA_ENGINE=chromium/firefox/webkit, QA_URL) и `python tests/iteration59-responsive.py` (QA_URL).98Node/12Python. Проверяются интервью Дарьи, часы, FAQ и многошаговый ПК-drag с возвратом/отменой. Ограничение качества публичного источника ВК описано в docs/ITERATION_59.md и не считается PASS полноразмерных оригиналов.


### Проход68: первый визит

`python -X utf8 tests/new68initial-layout.py --fixture tmp/frozen68-j/native --label unique-label --engine webkit` проверяет геометрию перед/после запуска compiled-модулей, cookie X и фокус на320/390/600 в обеих темах. Доставка — явно обозначенная public-host fixture, entry-gate не переписывает ESM dependencies; это не измерение производительности/публичного HTTPS. Engine также chromium/firefox; `--single` — один диагностический случай. Артефакты не перезаписываются.

`python -X utf8 tests/new68public-load.py --label unique-public-label` выполняет девять настоящих HTTPS-загрузок текущего published build из `deploy/tilda-pages.json` (3 профиля ×3 образца), фиксирует trace/network/LCP/CLS без форм и аккаунтов. Выполнять без параллельных браузеров/сборок. `python -X utf8 scripts/analyze-public-load.py --before path/results.json --after path/results.json --output new-analysis.json` проверяет одинаковые профили/версии браузера и вычисляет явно обозначенный FCP→10000ms timespan TBT; окно не заменяет Lighthouse TTI или полевой INP.
