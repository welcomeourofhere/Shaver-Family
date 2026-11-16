# Общая блокировка страницы при модальном окне

Проход65,16.11.2026. Исследование и исправление локальные; этот документ сам по себе не означает публикацию.

## Причина

У корневого `html:has(dialog:modal)` менялся `overflow:hidden`. На WebKit961px это удаляло нативные4px и меняло результат `matchMedia('(max-width:960px)')`: перед открытием true/client957, при открытии false/client961, после закрытия true/client957. Общий слушатель dock корректно закрывал меню при выходе из компактного режима, поэтому случайная смена режима немедленно закрывала только что открытое меню. Это не ошибка локальной кнопки.

`overflow:clip` показал тот же переход. Один принудительный `overflow-y:scroll` сохранял ширину, но оставлял фон прокручиваемым. Перехват только wheel/pointer также недостаточен: WebKit перетаскивал нативный root thumb даже при preventDefault на pointerdown. Поэтому локальная задержка закрытия, отдельный WebKit-branch и сравнение с innerWidth не использованы.

Первый прототип фиксировал body со смещением top:-savedY и overflow:clip. Он сохранял обычный поток, однако реальный Firefox961px потерял sticky-позу заголовка About и первого слоя:104→−89.95px и215.03→41.08px. Clip не создавал scrollport для sticky. Итоговый вариант переносит сохранённую позицию в настоящий скрытый scrollport body; покомпонентных компенсаций поз и клонов нет.

## Владелец

`modal-scroll-lock.ts` наблюдает нативный атрибут open и проверяет действительный top-layer `dialog:modal`. При первом окне переносит root XY в body.scrollTop/Left. CSS фиксирует body через inset:0,height:100dvh,overflow:hidden. Это настоящий scrollport без собственного видимого бара; sticky About продолжает видеть реальную позицию прокрутки. Root всегда использует `overflow-y:scroll`, поэтому его прежний нативный gutter, в данном WebKit4px, и CSS/JS media queries сохраняются. У root во время lock нет доступного диапазона прокрутки, включая scrollbar-drag. Внутренние native scrollport окон не заменяются и не получают перехват wheel/touch/keyboard.

Последнее закрытое окно снимает фиксацию и синхронно возвращает фактические body XY с behavior instant. При resize браузер сам ограничивает позицию и применяет scroll anchoring к изменившемуся документу; getter и восстановление читают эту реальную позицию. Подтверждённый footer-пример Chromium10534→9265 после390→1440→961→960 сохраняет footer.top438.125px до/после закрытия. Старый исходный rootY восстанавливался до9353 и давал88px скачок. Открытие ещё одного окна при существующем modal не переносит позицию повторно. MutationObserver выполняет смену до следующего paint; покомпонентных таймеров и копий состояния dialog нет.

Фиксированное body временно обнуляет нативный window.scrollY. Только root/body scroll-события удерживаются общим владельцем, чтобы технический ноль не сбрасывал наблюдателей страницы. Scroll-события .surface-content и прочих внутренних элементов проходят. Читающие положение страницы About, шапка и back-to-top используют общий `pageScrollY`, который во время lock возвращает фактический body.scrollTop. About применяет его и к origin, и к глубине, включая resize. Идущий page-wheel прекращается при lock.

`motion.ts` подключает владельца раньше компонентов окон. Обычные details/popover верхнего меню не являются dialog:modal и не фиксируют страницу. Прежние html/dialog overflow-переключение, особое body overflow для mobile-menu и второй booking overlay overflow-lock удалены. `dock-surface` сохраняет прежний matchMedia-слушатель: настоящий выход из компактного режима по-прежнему закрывает меню. Booking docked использует немодальный show(), фон прокручивается; overlay сохраняет native modal до конца существующей анимации закрытия.

Заголовок длинного знакомства получает tabindex:-1/autofocus только в dialog. Проверка обнаружила, что прежний initial focus на X вне Surface оставлял PageDown без чтения во всех трёх движках. Новый начальный фокус внутри Surface даёт нативные PageDown/ArrowDown; отдельного обработчика клавиатурной прокрутки нет. Escape возвращает исходную карточку. Общий mobile-nav при закрытии не заменяет уже корректный фокус заголовка целевого раздела, а при скрытом после resize источнике находит видимую эквивалентную кнопку меню/настроек.

## Проверка

Первый frozen smoke — `tmp/planning/iteration65/modal-smoke.json`:9 случаев Chromium/Firefox/WebKit ×960/961/1440, reduced motion. Media query и clientWidth не меняются при modal,4позы About отличаются менее чем на1px, внешнее wheel не двигает фон, Escape возвращает точный Y. Это предварительный smoke, не полная приёмка.

Расширенная проверка — `tests/iteration65-modal-scroll.py`: обе темы, normal/reduced, верх/середина/низ, вложенное menu→cookie без unlock, root scrollbar grab attempt при видимом нативном gutter, Escape/фокус, последующая прокрутка страницы, resize960→961→960, переход по ссылке меню после закрытия, нативные PageDown/ArrowDown и wheel/scroll-события интервью, прогресс чтения отзывов после восстановления. Дополнительные строки проверяют overlay/docked booking, открытие/закрытие/прерывание и wheel в промежуточном закрытии, footer resize390×900→1440×1200→961×600→960×900, реальный sticky1440×1200. Для детерминированного closing checkpoint тест приостанавливает реальную WAAPI-анимацию на40%, проверяет wheel и затем реальное прерывание открытием; production timing не меняется. Iframe записи заменён явной локальной HTML-заглушкой без формы; заявок/оплат нет.

Итог:150/150 случаев PASS —Chromium/Firefox/WebKit ×light/dark по25, включая normal/reduced. Сводка: `tmp/planning/iteration65/modal-scroll-summary.json`, failures:[]. Все браузерные процессы после проверки закрыты. Снимки — `artifacts/iteration65/modal-scroll/`, JSON — `tmp/planning/iteration65/modal-scroll-{engine}-{theme}.json`. Вручную просмотрены финальные sticky Firefox/light1440,Chromium/dark1440 и WebKit/light961compact; итоговая поза сопоставлена с геометрическими проверками всех шести элементов. Физические устройства не использовались.

В существующем style-contract.test закреплён один fixed-body owner и ровно одно разрешённое body overflow:hidden у него; html/root и компонентные overflow-lock запрещены. Root overflow-y:scroll обязателен. Unit source contract поиска JS root/body overflow writes также остаётся. Текущие structure/navigation/style —12/12 PASS; Astro124файла без ошибок/предупреждений/подсказок. Браузерная проверка использует отдельную frozen-сборку4366, общий dist не менялся.
