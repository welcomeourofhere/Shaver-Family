# Постоянная нативная полоса прокрутки

Последнее уточнение владельца отменяет скрытие при бездействии и механизм proximity/fade. Действующий вариант — простая постоянная нативная полоса. Предыдущие результаты proximity не являются приёмкой текущего решения.

## Реализация

- Канонический `--scrollbar-size` в design.json равен4px. В Chromium/WebKit вертикальная ширина и горизонтальная высота составляют4px.
- Ползунок цельный: `border:0`, обычное полное скругление. Красный цвет берётся из существующего `--scrollbar-thumb`, при наведении меняется только `background-color` на `--blue`. Ширина и поля при hover не меняются, заливка доходит до правого края.
- У `.surface-content` нативный track имеет верхний/нижний отступ по `--radius-card`. Он сохраняет целые caps внутри существующего скругления MaterialSurface; внешняя ширина, контент и положение окна не меняются. Маски, имитация второго scrollbar и JavaScript для полосы отсутствуют.
- `scrollbars.ts`, его импорт из Document, `--scrollbar-idle-delay`, alpha/tint-регистрации и все их consumers удалены. У областей чтения остаётся `currentColor`, соответствующий контрастному цвету текста карточки. Временное скрытие при переходе самого чтения не является скрытием по бездействию и остаётся у reading-transition.
- Размер native hit area теперь действительно4px в Chromium/WebKit. Он уже прежнего8px; перетаскивание проверено, дополнительный кастомный контрол не добавлялся.

Firefox получает стандартный `scrollbar-width:thin` и цвет из существующей палитры. Стандарт не принимает произвольную ширину в пикселях; native толщину, hover и поведение overlay определяют браузер/ОС. Это ограничение native fallback, а не обещание идентичного4px/синего hover. См. [MDN scrollbar-width](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/scrollbar-width) и [MDN scrollbar-color](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/scrollbar-color).

## Свежая проверка

`tests/iteration65-scrollbars.py` принимает `--engine chromium|firefox|webkit` и `--origin`. Текущие отчёты имеют префикс `permanent-` в `tmp/planning/iteration65/scrollbars/`.

- Chromium:5сценариев PASS. Во всех четырёх сочетаниях темы/motion реальные PNG показывают4px normal и hover у viewport и cookie-окна, целые симметричные caps, крайний правый пиксель заливки и отсутствие расширения. Полоса сохраняется после1.3s бездействия и1.2s удержания. Проверены настоящий native drag, wheel, End/Home и отдельная native touch-прокрутка через Chrome input. Это не физический телефон.
- WebKit:4сценария PASS с теми же проверками контура/idle/hold/native drag/wheel/keyboard. После screenshot стенд заново читает геометрию окна: Windows WebKit может восстанавливать её после снимка с отличием в2px. Ошибку тестового захвата удалось отличить от source: минимальный HTML и actual cookie одинаково прокручиваются всеми четырьмя пикселями native thumb. Production обход для драйвера не добавлялся.
- Firefox:4сценария native-совместимости PASS в headed-браузере. Проверены настоящие native полоса и drag внутри cookie-окна, wheel, End/Home и стабильность961px. Headless Firefox принудительно скрывает полосы даже поверх CSS `thin!important`, поэтому он непригоден для этого визуального теста. В headed-режиме в стенде включён native overlay always-visible testing preference; viewport-полоса всё равно не попала в PNG. В отчёте это явно `nativeOverlayNotCaptured`, а не доказательство отсутствующей полосы сайта. Синий hover и точный4px-контур viewport для Firefox не объявляются проверенными. Поведение тестовой оболочки описано в [Playwright issue18683](https://github.com/microsoft/playwright/issues/18683) и [Mozilla bug1989011](https://bugzilla.mozilla.org/show_bug.cgi?id=1989011).
- Во всех трёх движках проверены обе темы, normal/reduced motion и десять последовательных кадров на каждой ширине959/960/961/962/964/968: режим и clientWidth стабильны, горизонтального выхода нет.
- `design.test.mjs` и `style-contract.test.mjs`:3/3PASS после очистки зависимостей.

Это локальная приёмка HMR. Публичную доставку подтверждает отдельный основной release-проход. Физические устройства и Safari на устройстве в эту проверку не входят.

Остальные JSON/PNG и probe-скрипты в этой временной папке относятся к диагностике или отклонённому proximity-варианту. Активный тест содержит только постоянный scrollbar; они не включены в текущую приёмку.
