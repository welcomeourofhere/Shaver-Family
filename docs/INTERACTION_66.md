# Взаимодействия и feedback — QA66

16.11.2026. Независимая проверка изменений root. В рамках этого аудита продуктовые исходники не редактировались. Сценарий — `tests/new66interactions.py`; результат локальный, HMR не подменяет приёмку замороженного релиза.

Итог после двух исправлений root: **27/27 PASS, pageErrors0**, `tmp/planning/iteration66/interactions/hmr-final-27/results.json`. Все браузеры этого прогона закрыты. Тест и этот отчёт готовы к sourcefreeze; frozen-повтор будет отдельным label.

## Frozen native b52

После sourcefreeze тот же сценарий выполнен на неизменяемой native-оболочке **b52f95a4bd6aebbe049d**, `http://127.0.0.1:4370/`:

`python -X utf8 tests/new66interactions.py --origin http://127.0.0.1:4370/ --label b52-native`

**27/27 PASS, pageErrors0.** Доказательство — `tmp/planning/iteration66/interactions/b52-native/results.json`. Повтор включает actual trusted CDP touch, mouse drag, клавиатурную отмену и позднее отпускание, corrected short-touch→mouse/wheel, master booking только по маршруту и rapid Hero с удержанным decode. Product source и frozen-оболочка не менялись; браузер закрыт перед следующей задачей.

Это всё ещё локальный native-wrapper без сторонних скриптов Тильды. Реальная запись/оплата, физическая обратная связь и публичная доставка не проверялись. Последующее поручение владельца о возврате исходного favicon находится за пределами b52; перенос этой приёмки на новый кандидат требует отдельной сверки клиентских bundles и изменённого head владельцем релиза.

## Повтор clean-CI d72

После изменения границ chunks сценарий повторён на `http://127.0.0.1:4382/`, build`d72a049b273131f61090`, label`d72-native`: **27/27PASS,pageErrors0**. Доказательство — `tmp/planning/iteration66/interactions/d72-native/results.json`. Все actual drag/key/cancel, short-touch mouse/wheel и held-decode проверки выполнены вновь, а не перенесены по предположению идентичности.

Лаборатория затем подтвердила отдельный expensive adaptive-floating hotpath; этот результат и его будущий performance-fix — `BENCHMARK_66.md`. Подготовленный позднее fix audio/floating ещё требует отдельного focused-повтора и не объявляется пройденным по этим27 старым samples.

## Владельцы и проверяемый договор

| Владелец | Договор |
| --- | --- |
| `feedback.ts` | Только trusted события, не более одного принятого сигнала для одного Event. Обычная активация обрабатывается после DOM-отмены на window-bubble. Общие громкость `.18`, интервал48ms и роли tap/select/open/close. |
| `rail-selection.ts` | Выбор, native snap, счётчик и controls читают одного владельца. Accepted touch получает один select после смены индекса; отмена/вертикальный scroll/мышь не получают touch-вибрацию. |
| `native-rail-drag.ts` | Звук только для принятого mouse release, который меняет выбор. Отмена и поздний click после удержания подавляются. Мышь не вибрирует. |
| `service-deck.ts` | Swipe/клавиатура явно запрашивают selection; обычный tab click обслуживает общий feedback. Повторное нажатие уже открытой строки отменено и молчит. |
| `team.ts` / `Masters.astro` | Клавиатурный выбор меняет мастера и получает один select. Первое нажатие соседней карточки выбирает её, отдельная discovery-кнопка открывает знакомство. Запись сохраняет маршрут выбранного мастера. |
| `hero-news.ts` | Controls/клавиатура/жесты имеют ручной accepted-feedback. Выбор и синхронные active/aria/inert/counter/link меняются до завершения decode. |

Вибрация разрешена только trusted touch/pen и отключена при reduced motion. В конфигурации одна короткая просьба к API на роль: tap `[8]`,select `[10]`,open `[12]`,close `[6]`. `navigator.vibrate(0)` — остановка, она отдельно учитывается в отчёте и не считается положительной вибрацией.

## Воспроизведение

`python -X utf8 tests/new66interactions.py --origin http://127.0.0.1:4321/ --label NEW_LABEL`

Новый label создаёт отдельную папку и не перезаписывает прежние доказательства. Chromium запускается отдельным Chrome-контекстом; CDP `Input.dispatchTouchEvent` создаёт trusted input. Mouse и keyboard используют настоящий ввод браузера. Spy установлен до выполнения модулей только в главном документе: он фиксирует вызовы audio.play/vibrate, а не физический звук или работу вибромотора. Fixture-кнопка/checkbox явно добавлены только для проверки generic/cancelled/native-label путей. Сервисные карточки, мастера, menu и Hero проверяются на реальном текущем DOM сайта.

Внешние запросы заблокированы. Hero получает локальный JSON fallback с существующими локальными изображениями и изолированными id9000–9009. Новые публичные данные и правила стоп-листа этим тестом не проверяются. YCLIENTS iframe проверяется только по маршруту; заявка, платёж или реальная запись не отправляются.

Проверяемые сценарии:

- touch→mouse→keyboard: один audio cue у действия, haptic только у touch;
- trusted prevented click, programmatic click, hover, native label forwarding;
- reduced motion сохраняет звук и убирает вибрацию;
- mute, действия в выключенном состоянии, сохранение после reload, unmute;
- service tab touch, стрелки клавиатуры, повторное нажатие открытой строки, accepted/cancelled swipe;
- team keyboard, rail button и завершение доводки, accepted/cancelled touch, вертикальная прокрутка;
- короткий touch без выбора с последующей независимой mouse/wheel активацией;
- mouse drag, отмена удержания клавишей и позднее отпускание;
- соседняя карточка→выбор→открытие знакомства→закрытие, маршрут записи и Escape;
- шесть последовательных выборов Hero при искусственно удержанном `image.decode()`, затем отпускание всех decode и ещё клавиатурное переключение;
- Hero touch-button на ширине ПК и keyboard при reduced motion.

## Найденные ошибки

**Устаревший touch-feedback мог вибрировать при следующем mouse click.** Доказанный RED: `hmr-short-touch`,25PASS/1FAIL,pageErrors0. После15px touch индекс остаётся0, сигналов нет. В течение следующей секунды mouse next control вызывает `goTo→publish→confirmTouch`, подтверждая сохранённый старый TouchEvent. Spy получил select audio1 иvibrate `[10]`1 при исключительно mouse вводе нового действия.

Root добавил инвалидирование ожидания при новом document pointerdown/keydown. Повтор `hmr-short-touch-fixed` —26/26PASS,pageErrors0: mouse больше не вибрирует, native accepted touch по-прежнему получает один сигнал.

**Тот же stale touch сохранялся для wheel.** Дополнительный RED: `hmr-wheel`,26PASS/1FAIL,pageErrors0. После такого же короткого touch горизонтальный `page.mouse.wheel(360,0)` переключает native rail и ошибочно запрашивает audio select иvibrate `[10]`. Сброс только pointerdown/keydown этот путь не покрывает. Передано root: ожидание нужно также отменять в существующем wheel-владельце, сохраняя тишину прокрутки.

Root очистил ожидание в существующем wheel-обработчике, ResizeObserver при изменившейся ширине и compact-change; keydown также выполняется в capture до обработчиков компонентов. Итоговый `hmr-final-27` подтвердил исправление mouse и wheel, сохранил единичные accepted touch-сигналы. Spy этого прогона фиксирует и сам trusted wheel сdeltaX/deltaY.

**Node import:** `structure.test.mjs` импортирует `about.ts→native-rail-drag.ts`; новый extensionless `./feedback` не разрешался Node ESM. Это `ERR_MODULE_NOT_FOUND`, а не выход к document вне браузера. Передано root; исправление на `./feedback.ts` внесено им. Общий Node-прогон принадлежит root.

Узкий повтор `node --test tests/structure.test.mjs tests/mobile-navigation.test.mjs` после исправления —10/10PASS. Отдельный `feedback.test.mjs` —5/5PASS; это не заменяет общий Node-прогон root.

## Доказательства и осмотр

Основной набор до дополнительного short-touch кейса: `tmp/planning/iteration66/interactions/hmr-final/results.json` —25/25PASS,pageErrors0. Проверка исправленного mouse-edge: `hmr-short-touch-fixed/results.json` —26/26PASS,pageErrors0. Более поздние label сохраняют дальнейшее расширение, а не перезаписывают эти результаты.

В held-decode сценарии индекс, счётчик, активная карточка и ссылка соответствуют каждому из шести действий, пока decode всё ещё pending. Завершение старых promises не возвращает предыдущий выбор. Это причинная проверка блокировки, не замер FPS, INP или «всех скоростей». Просмотрен сохранённый кадр Hero после decode: одна активная фотография, одна подложка и общие нижние controls; полный визуальный аудит сайта этим сценарием не заменяется.

Ранние технические сбои harness исправлены отдельно от продукта: ограничитель координаты попадал выше нижней кнопки; удалённые fixture-media блокировались после удалённого JSON вместо использования local fallback; spy в заблокированном iframe получал denied-localStorage и ограничен главным документом. Их не регистрировали как продуктовые ошибки.

## Границы

### Повтор после lazy audio и floating-fix

Frozen native-кандидат `cc4409df87d6120375e6`, `http://127.0.0.1:4383/`: `tmp/planning/iteration66/interactions/cc44-native/results.json` — **27/27 PASS, pageErrors0**. Этот повтор выполнен после переноса подготовки audio на первое пользовательское действие. Trusted touch, mouse, keyboard, mute/reduced motion, отмена/drag и held-decode Hero сохранили договор. Результат относится к этому кандидату; прежние cross-engine platform-прогоны автоматически на новую сборку не переносятся.

Физические телефоны и Safari не проверялись. API spy не доказывает слышимость звука, силу/наличие вибрации, правила аппаратного браузера или доступность аудио на реальном устройстве. Скринридер не запускался; keyboard/focus/aria проверялись через браузер, это не AT-приёмка. Сценарий не профилирует производительность и не создаёт внешних обращений/записей. После общего sourcefreeze нужно повторить на frozen native-wrapper с новым label.
