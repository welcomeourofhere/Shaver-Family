# Переключение устройств, skip-link и цвет браузера — проход67

## Опубликованный baseline5d

Проверялся реальный `https://soyuz.hair/`, пакет `5d36176754bbdd000991`, Chrome на Windows. CDP менял **device metrics, touch emulation и UA** в одном документе; физический Android не использовался. Сертификаты/заявки не создавались.

Общую поломку адаптива воспроизвести не удалось. Последовательность desktop1440→phone390→tablet820→desktop1440→phone430 меняла media queries, Hero, header/dock и reviews phone↔module. Выход страницы не появился. Отдельный свежий контекст прошёл mobile390 с открытым меню→desktop1440 (меню закрывается, scroll lock снимается)→mobile430 с новым открытием→landscape932×430→desktop1440. Источники: `artifacts/iteration66/device-repro/production5d.json` и `focus-resize-production5d.json`.

В первом предварительном focus/resize-пробнике был один timeout5s после нажатия меню. Состояние владельца/сети в тот момент не записывалось; повтор с инструментированием прошёл. Причина первого сбоя **не установлена**, он не превращён в PASS повтором. Ограничение сохранено в `attempt1-menu-timeout.json`. В первом общем пробнике скриншоты Playwright могли восстанавливать viewport своего контекста после снимка; последующий цикл использовал прямой CDP capture и не содержит этого побочного действия.

Глобальная перезагрузка, новый resize-оркестратор и переинициализация компонентов не добавлялись: существующие media queries/owners уже реагируют. Следующий compiled-проход должен повторить тот же цикл; актуальный harness дополнительно проверяет неизменный `performance.timeOrigin`, а не число NavigationTiming entries, которое само по себе не доказывает отсутствие reload.

## Причина и исправление skip-link

`.skip:focus` показывал ссылку при любом фокусе. Даже после указателя программный `focus()` в Chrome может совпадать с `:focus-visible`. При этом существующий `setInput(false)` в motion.ts возвращался при первом pointerdown: внутренний boolean уже false, но `data-input-modality` ещё отсутствовал. Поэтому одного перехода на `:focus-visible` недостаточно.

Теперь общий motion-owner публикует первую фактическую modality, затем пропускает повторную одинаковую запись. Ссылка показывается по `:focus-visible`, а при известном pointer-вводе остаётся за верхней границей. Нового независимого tracker нет. Tab/Shift+Tab по-прежнему открывают её; без JavaScript native keyboard-сценарий сохранён. Main в home/story/404 получил `tabindex=-1`: Enter переводит реальный фокус к содержимому, а не оставляет его на BODY. Ни ссылка, ни клавиатурный доступ не удалялись.

## Мета браузера

На actual5d был один theme-color с корректным `--surface`; постоянный color-scheme оставался `light dark` при любом ручном выборе. Shaver Family использует синхронизацию effective theme и удаление дублей. Его body-background не переносился: СОЮЗ сохраняет собственный прозрачный host-canvas контракт.

Новый `browser-theme.ts` — один владелец записи theme-color/color-scheme. Document вызывает ту же функцию parser-time, сериализуя самодостаточную функцию без eval; theme.ts вызывает её при ручном/системном переключении. В head остаётся одна пара без media-дубликатов: фактический light/dark и цвет из CSS `--surface`. Body, #allrecords, #t-header, #t-footer и корневой фон не перекрашиваются JS.

Это исправление согласованности метаданных, **не подтверждение цвета физической панели Android**. Официальная документация Chrome описывает theme-color для toolbar; современный edge-to-edge также включает отдельные системные и браузерные поверхности: [theme-color](https://developer.chrome.com/blog/support-for-theme-color-in-chrome-39-for-android), [edge-to-edge](https://developer.chrome.com/docs/css-ui/edge-to-edge), [root color-scheme](https://developer.chrome.com/docs/modern-web-guidance/guides/visual-design/dark-mode). CDP не рисует настоящую Android address bar, а аппаратный этап исключён владельцем.

## Проверки исходника

- Node: `67browser-theme.test.mjs` + `mobile-navigation.test.mjs` + `structure.test.mjs` — **11/11 PASS**. Проверяются дубли/отсутствующие meta, смена effective theme и отсутствие записи canvas-стилей.
- `new67device-switch.py --origin http://127.0.0.1:4321/ --label hmr67-b` — **21/21 PASS**, pageErrors0, source SHA unchanged:16 CDP-состояний в обеих темах, реальные trusted-touch открытия меню, OS/manual/duplicate-meta, pointer/Tab/Enter и no-JS skip. Браузеры закрыты. Снимки light desktop-return и dark phone осмотрены.
- `new66mobile-platform.py --checks bootstrap --engine chromium --label hmr67-theme-bootstrap-a` — **10/10 PASS**. Пять сочетаний OS/saved/invalid choice, module scripts заблокированы: parser-time тема, meta, viewport-fit и доступный zoom. Ожидание color-scheme обновлено на фактически выбранную тему.

Первый HMR67-a не получил SSR-страницу за30s; независимый HTTP/ тоже не отвечал, favicon отдавался200. Это до выполнения UI-кейсов, не productPASS/FAIL: `artifacts/iteration67/device-switch/hmr67-a/HARNESS_FAILURE.json`. После root-изменения watcher ignored и перезапуска HMR SSR восстановился; вклад restart/ignore отдельно не разделялся.

Результаты HMR не переименованы в релизные. Compiled/native/Tilda-публикация нового батча, Firefox/WebKit и физическая browser chrome этим проходом не подтверждены. Cold/SY003/009-harness подготовлен, но не запускался: задача была переориентирована до нового кандидата.
