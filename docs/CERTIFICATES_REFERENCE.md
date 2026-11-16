# Сертификат: действующая композиция

04.11.2026, ITERATION_12_DETAILS.md.

На ПК подарки3×2, сертификат справа; отношение ширины подарков к сертификатуφ. Четыре строки subgrid содержат пары «квадрат/подпись», сертификат заканчивается на последнем квадрате без подписи. contain:size не позволяет содержимому сертификата менять высоту строк. До960px сертификат ниже подарков; фиксированный зазор учитывает overhang.

Порядок: сцена с картами → заголовок → описание → широкая кнопка. Карты крупнее и заходят выше синей поверхности; их transform не участвует в потоке. overhang=round4(24×√φ)=32px, anchorY=50%−overhang. Ширина min(72%,300px,(100cqh+2×overhang)/2). Допустимая виртуальная сцена: от scene.top−2×overhang до scene.bottom. FanY ограничен остатком этой области после поворота карты и защитного поля.

Действующие источники SF: src/site/js/site-immersive.js, src/site/css/site-system.css:88–101, tools/site_render.py certificates(), content/site/certificates.json в J:/Projects/Shaver Family (Website). Архивный неактивный site-certificate.js не используется.

certificates.ts подключён один раз. Scroll-fan: min+range×sin(π×passage)². Fine-pointer меняет наклон; нажатие замораживает движение; click/Enter/Space выдвигают выбранную сторону. Вне viewport/скрытой вкладки rAF останавливается. Reduced motion оставляет фиксированный веер без наклона. Текст/кнопка и соседние разделы не двигаются.

Фактические проверки: tests/iteration12-browser.py, tests/layout-browser.py, tests/template-browser.py. Геометрия overlay, отсутствие пересечения с заголовком/описанием/кнопкой, низ по подаркам, стабильность следующего раздела. Числа и изображения — docs/QA.md.
