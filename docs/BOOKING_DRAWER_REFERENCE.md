Актуализация после ответа владельца: подтверждён n2763199.yclients.ru; iframe использует b2763199.yclients.ru и полную высоту. Текущая проверка/ограничение провайдера — `docs/BOOKING_PROVIDER_QA.md`. Прежние проверки fallback ниже исторические.

# Боковая запись СОЮЗа

Локальная реализация от 04.11.2026. Ссылка на работающую запись СОЮЗа не подтверждена; по умолчанию панель предлагает ВК и телефон из `content/site.json`. Компонент не собирает персональные данные, не создаёт запись и не показывает фиктивное подтверждение.

## Источник механики

Изучены исходники `J:/Projects/Shaver Family (Website)/src/shared/js/015c-booking-widget-controller.js`, `src/shared/css/modules/039g-booking-widget-mobile.css`, `039h-booking-widget-docked.css` и корневые токены этого проекта. Использованы принципы правой панели, общего параметра ширины, отдельной широкой/узкой компоновки, возврата фокуса и защиты от устаревшего завершения анимации. Идентификаторы форм, SDK, CRM, тексты, ссылки и клиентские данные SHAVER FAMILY не перенесены.

Источники СОЮЗа `docs/CONTENT_SOURCES.md` и `docs/CRM_MOBILE_REFERENCE.md` фиксируют ошибки или неподтверждённость `n521588.yclients.com` и `n2266404.yclients.com`. Они не используются как адрес формы. Дополнительный внешний поиск или обращение к CRM в рамках этого компонента не выполнялись.

## Интеграция

В `index.astro` импортировать `BookingDrawer` и вывести `<BookingDrawer />` после обёртки `<div data-booking-page>…</div>`. Внутрь обёртки входят header, main, footer и нижняя навигация; сама панель остаётся снаружи. Компонент сам импортирует свой CSS и script. Корректировки фиксированного header под зарезервированную правую область выполняются в его общих стилях через `html[data-booking-layout="docked"][data-booking-state="open"]`.

CTA записи используют `data-booking`; прежние `data-contact`/`data-book` с этих CTA удалить. Контактные действия, не связанные с записью, могут сохранить прежний диалог. `openBooking` закрывает остальные открытые диалоги через существующий `closeDialog(dialog, true)`; исходный trigger сохраняется до закрытия меню. В общих обработчиках `<dialog>` исключить `[data-booking-drawer]`: его закрытием управляет `booking.ts`.

```astro
<button class="btn" data-booking data-service="Мужская стрижка">Записаться</button>
<button class="btn" data-booking data-master="Ирина" data-context="Запись к мастеру: Ирина">Записаться</button>
<button class="btn" data-booking data-promo="Первый визит · −50%">Выбрать время</button>
```

Для программного открытия доступен экспорт:

```ts
import { openBooking, closeBooking } from './booking';
void openBooking({ service: 'Мужская стрижка', master: 'Ирина', promo: 'Первый визит' }, trigger);
void closeBooking();
```

`openBooking` принимает также сам HTMLElement с перечисленными `data-*`. `context` имеет приоритет над сформированным списком; без него `service`, `master`, `promo` показываются отдельными строками. Это отображаемые названия, а не идентификаторы CRM. Контекст записывается через `textContent`, существует только в текущем DOM и не передаётся провайдеру/ВК. При выборе ВК пользователь сам сообщает детали администратору.

## Токены единой системы

Добавить в `src/config/design.json`:

| Токен | Значение | Назначение |
| --- | --- | --- |
| `--booking-width` | `480px` | Ширина панели и резерв страницы |
| `--booking-page-min` | `900px` | Минимум оставшейся ширины для docked |
| `--booking-z` | `1000` | Слой немодальной панели |
| `--booking-shadow` | `0 16px 40px #3c302925` | Тень панели |
| `--booking-scrim` | `var(--tone-0003)` | Подложка overlay |
| `--booking-load-timeout` | `15000ms` | Срок показа восстановления iframe |
| `--ease-drawer` | `cubic-bezier(.32,.72,0,1)` | Кривая движения |

Повторно используются `--motion-panel`, `--size-*`, `--control-*`, `--radius-control`, шрифты и цвета проекта. В `booking.css` нет ненулевых литералов `px`, `ms`, `deg` или hex. При reduced motion и клавиатурном действии панель переключается сразу. В обычном режиме WAAPI меняет только transform/opacity панели и opacity подложки; каждый следующий запрос начинает с текущего вычисленного кадра. Резерв ширины страницы переключается без анимации свойств layout.

## Контракт взаимодействия

| Действие/состояние | Результат |
| --- | --- |
| Нажать CTA | Панель справа, выбранный контекст и фокус на закрытии |
| Широкое окно, осталось не меньше `--booking-page-min` | Немодальная панель; справа резерв ширины; страница остаётся доступной |
| Узкое окно | Нативный modal dialog, подложка, блокировка прокрутки и изоляция фокуса; крайние Tab/Shift+Tab замыкаются явным обработчиком |
| Close / Escape / клик по подложке | Выход той же траекторией; возврат фокуса на видимый CTA |
| Повторное открытие во время закрытия | Отмена старого выхода и движение от текущего кадра |
| Другой CTA при открытой панели | Обновление контекста без перезагрузки формы |
| Изменение размера | Выбор docked/overlay без ухода на внешнюю страницу |
| Нет `bookingUrl` | Только контактная запись, без сетевого запроса к провайдеру |
| Есть подтверждённый HTTPS `bookingUrl` | iframe получает src только при первом открытии; закрытие не сбрасывает его состояние |
| Долгая загрузка/ошибка iframe | Повторить, открыть отдельно, ВК или телефон; успех записи не утверждается |

Кроссдоменный iframe самостоятельно обрабатывает клавиатуру внутри своей страницы; Escape внутри него нельзя гарантировать без сотрудничества провайдера. Кнопка закрытия остаётся вне iframe, доступна через Tab и из нативной модальной последовательности. Событие load не доказывает работоспособность приложения провайдера, наличие времени или успешную запись. Постоянный контактный выход доступен при любом состоянии.

## Проверки

Браузерная проверка выполнена на интегрированной локальной странице `http://127.0.0.1:4323/` в Chromium через установленный agent-browser:

- 1440px: docked, панель 480px, доступная страница 960px, прокрутка страницы разрешена.
- 1280px: modal overlay 480px; 390px и 320px: modal overlay во всю ширину, прокрутка фона блокируется.
- Все кнопки панели имеют hit не меньше 44px; текстовые подписи в одну строку, без переполнения, padding 24px на ПК и 18px на телефоне.
- Прошли Tab/Shift+Tab на границах, Escape, возврат фокуса на источник, переход из меню в запись и fallback на мобильную кнопку.
- Прошли контекст с HTML как безопасным текстом, close→open во время анимации, resize 1440→390→1280→1920→390 при открытой панели и очистка состояния после внешнего native close.
- Прошли клик по подложке и reduced motion: 0 активных анимаций панели. Неподтверждённый iframe отсутствует; в проверенных сценариях ошибок JavaScript не зарегистрировано.
- Отдельная проверка PostCSS подтвердила наличие всех используемых токенов и отсутствие ненулевых px/ms/deg/hex в `booking.css`.

Снимки `.artifacts/booking-drawer-desktop.png` и `.artifacts/booking-drawer-mobile.png` просмотрены. На широком снимке обнаружено пересечение элементов общей шапки из-за viewport breakpoint при суженной странице; передано владельцу `header.css`. Сама панель не пересекает свои элементы. Финальная сборка/общий check относятся к интеграции родительской задачи; на промежуточном общем check остаётся ошибка типов нового селектора диалогов в `template.ts`, ошибок `booking.ts` нет.

Небольшая повторяемая самопроверка в консоли локального Astro dev-сервера (не заполняет и не отправляет форму):

```js
const { openBooking, closeBooking } = await import('/src/scripts/booking.ts');
const drawer = document.querySelector('[data-booking-drawer]');
const trigger = [...document.querySelectorAll('[data-booking]')].find(x => x.getClientRects().length && !x.closest('dialog'));
trigger.focus();
await openBooking({ service: '<img src=x onerror=alert(1)>' }, trigger);
console.assert(drawer.open && document.activeElement.matches('[data-booking-close]'), 'Opening/focus');
console.assert(drawer.querySelector('[data-booking-selection]').textContent.includes('<img'), 'Context is text');
console.assert(!drawer.querySelector('[data-booking-selection] img'), 'No injected markup');
await Promise.all([closeBooking(), openBooking({ master: 'Ирина' }, trigger)]);
console.assert(drawer.open && document.documentElement.dataset.bookingState === 'open', 'Interrupted close');
await closeBooking(true);
console.assert(!drawer.open && document.activeElement === trigger, 'Close/focus return');
```

Форма провайдера не проверена: подтверждённый адрес отсутствует. Для неё нужна отдельная проверка iframe/CSP, загрузки, восстановления, мобильной клавиатуры и переходов провайдера; без создания реальной записи.
