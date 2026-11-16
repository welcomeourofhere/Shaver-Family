# Приёмка native C, проход65

16.11.2026. Итог локальной функциональной и визуальной приёмки: **PASS**. Это не публикация, не полевой benchmark и не проверка физических устройств. Все браузеры этого прохода закрыты; root получил отдельный сигнал BROWSER-FREE до начала benchmark.

## Неизменяемый кандидат

- Build: `7a129e64e8086a5face7`; canonical manifest SHA-256: `4fc48e7fe8437007a89641332a825cbfe70c042f8fcdc5d6c8cbc56866a34958`.
- Native origin: `http://127.0.0.1:4395/`; fixture: `tmp/candidate65-native/dist`.
- Ровно11маршрутов,2общие оболочки header/footer и421runtime-ассет. В native-дереве432файла.
- Tree SHA-256 до и после QA: `644fc44a78152c51d7a25f5b308fdcf1cba03eaa01637146c515ee75a36ef368`.
- Повторная полная сверка с `tmp/candidate65-native-canonical/dist`:432/432файла побайтно идентичны. Исправление LF в метаданных exporter не изменило проверенный native HTML/CSS/JS/ассеты.
- Доказательства: `tmp/planning/iteration65/nativeC/provenance.json` и `final-provenance.json`. Preview-маршруты и частная14-page сборка не использовались как кандидат C.

##37автоматических заданий

Задания выполнялись последовательно. Сохранённые успешные префиксы не повторялись после диагностики тестовых предусловий. Итог состоит из shell-PASS в первом запуске, успешного префикса attempt2 и оставшегося успешного attempt3. Исторические неуспешные попытки сохранены, их нельзя объявлять успешными задним числом.

| Проверка | Объём итоговой приёмки |
|---|---|
| Общая оболочка и gifts-placeholder |1Chromium job,20случаев |
| Header и общие popup |3движка;16размер/тема/масштаб-состояний на движок плюс reduced-motion и задержанный реальный Header-module;54контекста суммарно |
| График работы |60случаев:3движка×20;3статуса, обе темы,320–1440,200%текста, Escape/focus |
| Низкая высота меню |24случая:3×8; последняя ссылка, native wheel/scrollport,200%текста и клавиатурный переход |
| Подвал и личные контакты |66случаев:3×22, каждый с обычным и увеличенным текстом;320–1920 |
| Hero controls |3движка×20основных состояний плюс полный цикл10изображений, coloured surfaces, held drag/cancel, keyboard/playback и compact без запросов ленты |
| Истории и service-summary |36групп размеров/тем:3×12; в каждой все6знакомств, intrinsic cover, X, короткие высоты; цены и названия услуг при200%текста |
| Общий modal scroll owner |150случаев:3движка×2темы×25;6поз фона, nested menu→cookie, root gutter/MQ, реальные wheel/thumb попытки, PageDown/ArrowDown, resize/bodyY restore, sticky About, overlay/docked booking fixture |
| Cookie |3полных harness; до выбора SDK не исполняется, раздельные сервисы, отказ/повтор/отзыв, pending SDK/cross-tab/storage errors, safe events/URL, nested menu,6макетов и общий FAQ-disclosure |
| Нативные scrollbar |Chromium/WebKit:4px, полные caps, неизменная ширина hover, drag/wheel/keyboard, край окна,959–968; Firefox: native thin/overlay compatibility; отдельный Chromium trusted-touch |
| Отзывы |1job с3движками,39сценариев: все8до960, плотный desktop-поднабор, максимум2grid-единицы, стабильный первый batch, held drag,961px, no-JS |
| Utility icons |1job с3движками,12контекстов;390/1440, обе темы,24px на48px controls, hover/muted/keyboard theme |
| Дополнительный Chromium fit |4jobs: team40cases/480labels/24keyboard-and-caption journeys; Hero text; certificate mirror с7номиналами; certificate/FAQ20normal/text200 состояний |

Итого:1shell +30per-engine jobs +2внутренне3-engine suites +4fit suites =37jobs. Логи и результаты находятся только под `tmp/planning/iteration65/nativeC/`: `run-attempt1-selector-failure.json`, `run-attempt2.json`, `run-attempt3.json`, `logs*`, вложенные `tmp/planning/iteration65/` и `artifacts/iteration65/`.

## Реальные manual UI и ввод

- Самостоятельно просмотрены18Header-status кадров: open/closing/closed ×light/dark ×Chromium/Firefox/WebKit. Цветные точки зелёная/жёлтая/красная, единая форма popup,8px граница, шрифт и внутренние отступы согласованы. Контрольные часы UTC08:00/17:33/00:33 от16.11.2026. Листы из реальных кадров: `nativeC/manual-review/header-status-{engine}.png`.
- Самостоятельно просмотрены свежие common More/phone/hours popup, включая1024px text200, normal footer light/dark и личные карточки320/768/1440. Полные названия трёх документов, ритм колонок, портреты, иконки и контакты доставлены. Нативный map-provider в manual заблокирован; серое/ошибочное содержимое iframe на этих кадрах не является доказательством работы или неисправности живой карты.
- Все4новых service-постера действительно отрисованы и самостоятельно просмотрены: Честная цена, Экспресс-массаж, Комплекс№3 и Премиум-стрижка. Файлы: `manual-final/chromium-{theme}-service-{serviceId}.png`, по4в каждой теме. Новая генерация или замена исходников в этом проходе не выполнялась.
- Loader проверен на11реальных позах через125ms при удержанном запросе iframe: normal1440 анимируется во всех3движках, reduced390 имеет одну позу; центр отличается от центра booking-panel менее чем на1px. Firefox normal дал11различных поз, WebKit10; у Chromium проверен порог больше2. Каждый cold-loader получил свежий контекст. Формы поставщика заменены явным HTML-макетом без заявки.
- Сертификат проверен настоящим открытием новой вкладки на390/1440 в обеих темах во всех3движках. Адрес `https://o16013.yclients.ru/certificates`, booking-drawer не открывается. Оплата не создавалась.
-66route-smoke случаев:11маршрутов×390light/1440dark×3движка; один header/footer/h1, корректный title, отсутствие horizontal overflow/pageerror. Canonical сверялся с manifest/Tilda page settings; native custom-HEAD намеренно не воспроизводит автоматически создаваемый Тильдой canonical-link. Живой SEO head остаётся отдельной публичной проверкой.
-6trusted-touch случаев Chromium/CDP:390/768/960 ×normal/reduced; полный цикл всех категорий услуг, отмена и вертикальная прокрутка без случайного переключения/открытия окна. Это браузерный trusted-input, не физический телефон.

Manual-кадры: `nativeC/manual-final/` (Chromium UI) и `nativeC/manual-remaining/` (Firefox/WebKit UI и все66маршрутов). Ledger оставшейся фазы: `manual-remaining/capture-index.json`. Chromium UI успешно дошёл до route-smoke; первая остановка была на неверном тестовом предположении о canonical, после всех UI-assert. Его36кадров и первоначальный log сохранены. Touch: `nativeC/service-touch/result.json` и `service-touch.log`.

## Исправленные тестовые предусловия, без app-patch

Исходные production, fixture и `tests/` при C-приёмке не менялись. Harness-файлы скопированы без изменений в отдельный временный QA-root, чтобы не перезаписывать прежние доказательства. Затем изменены только3temporary-копии; исходные/новые SHA и точный diff записаны в `native-harness-adaptations.json`.

1. Native exporter правильно превращает `#faq`/`#contacts` в `/#faq`/`/#contacts`. Два прежних private-build селектора требовали буквальный local fragment. Temporary selector принимает suffix, одновременно проверяя same-origin, путь `/` и точный hash. Click и последующий landing не обходятся.
2. WebKit в длинном контекстном прогоне остановил доставку всех rAF при `visibility=visible`, `hidden=false`, `hasFocus=true`: Hero/About/Reviews/MobileNav/action-label остались в очереди после ResizeObserver. Canvas был правильным:305px при font32, доступно274px; последний source-update оставался на font16. Отсюда в принудительном DOM-снимке phone Евгения вышел до962–963px. Тот же эффект воспроизведён на source4366, поэтому native CSS export не был причиной. После реального foreground/rAF root вернулся к956–957 и helper выбрал «Тел.».
3. Финальный footer-harness явно активирует renderer и получает2кадра **до** изменения размера текста. После изменения остаются прежние500ms и прежний width-assert; ожидания конкретной метки после failure нет. Полный22-case foreground trace и окончательный22-case C-native прогон PASS. Никакой overflow:hidden, новый app-таймер или локальная компенсация в сайт не добавлены.
4. Два дополнительных ошибочных предположения temporary manual-helper сохранены в истории: уже загруженный iframe правильно переиспользуется без повторного loader; canonical автоматически создаёт Тильда из page settings, а не native custom-HEAD. Исправлены только условия manual-проверки, успешные37jobs не повторялись.

Диагностика rAF/исходные false failures: `nativeC/debug-footer/`, `trace-footer/`, `raf-footer/`, `front-footer/`. Эти остановки не маскируются под production-баги или успешные исходные попытки.

## Граница результата

Новых подтверждённых production-дефектов в C-приёмке не осталось. Замечена неблокирующая историческая provenance-подпись `main-honest-price.altSource` про прежнее переиспользование mens-cut; актуальный новый постер показан правильно, подпись в UI не выводится, runtime в процессе QA не менялся.

Не входят в этот PASS: публикация Тильды, её сторонние скрипты, живой canonical/SEO head и фактические counters/provider, полевые метрики, физические устройства. Эти этапы принадлежат отдельным release/benchmark-проверкам root. Пользовательские Chrome/REG.RU и другие окна не закрывались; закрыты только созданные QA-браузеры.
