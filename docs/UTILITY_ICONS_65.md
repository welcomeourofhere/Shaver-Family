# Служебные иконки СОЮЗа

16.11.2026 по прямому поручению владельца выбран единый набор Lucide. На дату проверки официальный последний выпуск — [1.73.0](https://github.com/lucide-icons/lucide/releases/tag/1.73.0), зафиксированный commit `55782beff3a0133df79c417eb68f96e8f19e2404`.

Официальная [страница лицензии](https://lucide.dev/license) указывает ISC для Lucide и MIT для перечисленных производных Feather, включая moon. В проекте сохранён полный [LICENSE зафиксированного commit](https://github.com/lucide-icons/lucide/blob/55782beff3a0133df79c417eb68f96e8f19e2404/LICENSE), обе части без сокращений. Набор целиком не обозначается ошибочно как MIT.

| Владелец/роль | Официальный SVG |
|---|---|
| Настройки cookie | [cookie.svg](https://github.com/lucide-icons/lucide/blob/55782beff3a0133df79c417eb68f96e8f19e2404/icons/cookie.svg) |
| Общие настройки | [settings.svg](https://github.com/lucide-icons/lucide/blob/55782beff3a0133df79c417eb68f96e8f19e2404/icons/settings.svg) |
| Светлая тема | [sun.svg](https://github.com/lucide-icons/lucide/blob/55782beff3a0133df79c417eb68f96e8f19e2404/icons/sun.svg) |
| Тёмная тема | [moon.svg](https://github.com/lucide-icons/lucide/blob/55782beff3a0133df79c417eb68f96e8f19e2404/icons/moon.svg) |
| Звук включён | [volume-2.svg](https://github.com/lucide-icons/lucide/blob/55782beff3a0133df79c417eb68f96e8f19e2404/icons/volume-2.svg) |
| Звук выключен | [volume-x.svg](https://github.com/lucide-icons/lucide/blob/55782beff3a0133df79c417eb68f96e8f19e2404/icons/volume-x.svg) |

Шесть исходных SVG, LICENSE и `source.json` с URL/SHA-256 сохранены в `content/third-party/lucide/`. Это публичные лицензированные исходники, необходимые для проверки поставщика, а не приватные фото или QA-артефакты. Общий `public/brand/utility-icons.svg` содержит их неизменённые path/circle и исходные fill/stroke/linecap/linejoin в группах. Геометрия24×24, stroke2. `UtilityGlyph.astro` остаётся единственным компонентом внедрения. Новой npm-зависимости и загрузки иконок с CDN нет.

Тема сохраняет существующие группы sun/moon и прежний `theme.ts`; звук сохраняет `FeedbackSettings` и `feedback.ts`. Для нового солнца убран прежний уменьшенный scale.83, необходимый старому заполненному рисунку. Видимое солнце теперь рисуется1:1, как остальные значки. Цвет, hover/focus и размер48px принадлежат прежним контролам. Стрелка «Наверх» сохранена как прежний Hero-chevron, повёрнутый вверх; ContactGlyph с фирменными мессенджерами не затронут.

Полные уведомления опубликованного пакета находятся в `public/brand/lucide-LICENSE.txt`; sprite содержит ссылку на них. Сборщик уже включает весь утверждённый `brand/`, поэтому лицензия попадает в пакет и новый media-lock штатным способом.

`design.test.mjs` проверяет хеши шести оригиналов, pinned URL, сохранение официальных path/circle в sprite, единый stroke, отсутствие исполняемых/внешних SVG-вставок, прежнюю стрелку и точную копию лицензии. `iteration65-utility-icons.py` проверяет реальные24px в48px контролах, светлую/тёмную темы, hover, выключенный звук и клавиатурный круг смены темы; источником служит отдельная frozen private-сборка. Результаты и кадры — `tmp/planning/iteration65/utility-icons.json` и `artifacts/iteration65/utility-icons/`. Это локальная проверка, без записи/оплаты или разрешения аналитики.
