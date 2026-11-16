# Релиз СОЮЗа: Implementation Plan

> **For agentic workers:** Use `executing-plans` to implement this plan task-by-task in the current checkout. Пользователь уже поручил выполнение; отдельное согласование выбора процесса не нужно.

**Goal:** Выпустить проверенный сайт СОЮЗа на soyuz.hair с общей шапкой/подвалом Тильды,3документами, воспроизводимой доставкой и работающими интеграциями.

**Architecture:** Astro-компоненты и JSON остаются источником. Экспорт разделяет общий shell и содержимое до публикации; Тильда вставляет отдельные header/footer нативно, ресурсы обслуживает версионированный префикс Яндекс Облака. Один runtime обслуживает общие действия, динамический JSON владеет новостями.

**Tech Stack:** Astro5, TypeScript, CSS/WAAPI/нативная прокрутка, Python standard library/BeautifulSoup/tinycss2, Playwright для изолированной QA, Tilda MCP, существующий AWS CLI, GitHub Actions.

**Spec:** `docs/RELEASE_SPEC_64.md`.

**Текущий срез E:** 16.11.2026, опубликован выпуск65 E `945ad6ddd3e70d5cc3c4`, manifest SHA256 `e9af475c845d1adebf868b28361b745811612b78bfb3901161a50605dbf1dabb`. Через официальный MCP опубликованы13/13 страниц, shared перед content; после публикации13/13 HEAD/code прочитаны с точным совпадением. Cloud421/421 проверен, root registry указываетE. NativeE18 прошёл с прозрачными body/#allrecords/#t-header/#t-footer и тремя footer-pixel проверками в каждом случае. ActualE18/18 technical HTTPS GREEN; Header3/3 сохранил gap8px, radius20px, фон#252525 и8px status-dot. После добавленного владельцем исключения Happ/Xray основной https://soyuz.hair также прошёл18/18 усиленных canvas/footercorner cases в3движках, обе темы и390/961/1440px; HTTP12/12PASS,177currentresources. Доказательства: HOST_CANVAS_65D.md и tmp/planning/iteration65/host-canvas/E-main-public/. Финальные sourceE commit/Actions и локальный Git adoption ожидаются; remote пока509fed9…/Actions43800396980success.

D `d4040c957966781f777c` исправил opaque body/#allrecords, но его18/18 actual canvas и Header3/3 не покрыли внешние светлые углы native#t-footer в тёмной теме. Этот дефект найден финальным просмотром; D остаётся ограниченной историей, а не итоговой host-приёмкой. E расширяет единственный HOST_CSS reset на body/#allrecords/#t-header/#t-footer. Все421 compiled inputs совпадают сD;13body точно совпадают после замены build-prefix,13HEAD отличаются только расширенным reset. C37native jobs, SDK transport и24benchmark samples сохраняют исходную область и не называются новыми измерениямиE.

## Global Constraints

- Продакшен Shaver Family19258126 и его файлы/аналитику не менять.
- Физические телефоны исключены владельцем; эмуляция не является проверкой физического Safari.
- Никаких реальных записей, покупок или сообщений другим людям.
- Исходники меняются в src/content; dist и доказательства создаются командами.
- Loader №04:1250ms,0/80/160/240ms, ease-in-out,2px,.3→1,44–65%.
- Кнопка: одна строка, минимум12px по бокам/44px область нажатия.
- Документы публикуются только с подтверждёнными реквизитами; секреты не выводятся.
- Уже принятыеHTTPS/поисковые настройки64 сохраняются; доставка65 проверяется отдельно. Получениеrobots или отправкаsitemap не приравниваются к индексации.

## Карта файлов и владельцев

| Область | Файлы | Ответственность |
|---|---|---|
| Загрузка | LoadingIndicator.astro, loading.css, loading.ts, Hero.astro, hero-news.ts | Единый loader/пауза/статус сети |
| Общая оболочка | Header.astro, Footer.astro, Document.astro, страницы index/masters/404, prepare-tilda-release.py | Один shell, готовый HTML, native header/footer |
| Навигация/движение | template.ts, header-menus.ts, page-motion.ts, modal-scroll-lock.ts, about.ts, about.css | Принятые действия, правильные якоря/закрепление, один modal/scroll owner |
| Документы | content/legal/, общий LegalDocument.astro/маршрут, legal.css | Проверенный текст/источники/печать |
| Доставка | deploy/production.json, tilda-pages.json, analytics.json, scripts/upload-tilda-assets.py, .github/workflows/ | Ограниченный адресат, хеши и проверяемый релиз |
| Приёмка | tests/iteration64-*.py, release_package_test.py, release-routes.py, docs/RELEASE_TRACKER.md | Воспроизведение, матрица, метрики, блокеры |

## Состояние после выпуска64 и приёмка65

Ниже completed/pending после публикацииE. История64/B/C/D сохраняется, включая ограниченностьD18 и найденныйfooter-дефект. Точный переносE завершён; actualE18,финальныйGit и внешние сетевые/поисковые этапы остаются открытыми.

### 1. Общая архитектура и настройки

- [x] Подтвердить реквизиты исполнителя и график11:00–22:00 у владельца.
- [x] Создать три полных документа,6интервью и404 из общих Astroкомпонентов.
- [x] Создать штатные2sharedстраницыТильды, назначить их всем11contentмаршрутам.
- [x] Проверить обычное движение/якоря/меню на nativewrapper стенде и public64.
- [x] Проверить валидныйHTTPS,домен,основныеHEAD/canonical/robots/sitemap,отдельныесчётчикибезnativeдублей.
- [x] Проверить actual technical HTTP для11маршрутов иunknown404, currentEasset closure,Twitter/lang/alt/canonical:12casesPASS.
- [x] СохранитьD actual body-canvas18/Header3 как bounded history: внешнийt-footer не покрыт, найденfooter-дефект.
- [ ] Завершить actualE18 на опубликованномtechnical HTTPS; основнойHTTPS израбочей сети этим не подменять.

### 2. Замечания владельца65

- [x] Найти общий конфликт exportCSS: встроенный и внешнийCSS проходят один protected_css.
- [x] Подключить самостоятельные messenger paths и общий закреплённыйLucide для utility glyphs, сохранить лицензии, убрать неразрешённыеSVGuse.
- [x] Подключить4утверждённых сервисных постера из соседнего чата для5serviceIDs с сохранённымиorigins/hashes.
- [x] Уточнить авторскиеaltSource: плакатная artwork не объявляется неподтверждённой фотографией мастера. Бинарные постеры этим metadata-only изменением не заменяются.
- [x] Вернуть компактный подвал с колонками разделов и полными названиями документов ниже, без «Аналитики»; локальная приёмкаroot включает66пар3движков.
- [x] Сохранить единые48px кнопки звук/тема/cookie рядом с «Контактами», жёлтую шестерёнку и синий «Наверх».
- [x] Hero наПК использует общий нижнийRailControls: счётчик/индикаторы/стрелки. В фото и текстовой плашке внутренних контролов нет; плашки непрозрачные брендовые, CTA появляется поhover/focus. Компактный Hero остаётсяvideo-only.
- [x] Верхние «Ещё»/телефон/часы используют один popup-owner, одинаковый фон/радиус и отступ8px, общий8px hover-bridge с проверенным350ms удержанием курсора в зазоре и клавиатурный входArrowDown. Content-fit выдерживает200% текста; доступная высота зависит от настоящегоshell.bottom и100dvh.
- [x] Часы11–22 показывают цветной status-dot, полужирный статус•обычный отсчёт; зелёный/open, жёлтый/последние120минут, красный/closed. Нижняя справка удалена, узкая адаптация сохраняет смысловые фрагменты.
- [x] Вместо6подарков показать однотонный серый «Появится позже» без скрытых изображений иblur; VisitGifts сохранён отдельно, сертификат активен.
- [x] Сертификаты зеркально скомпонованы без отражения изображений/текста; покупка открывается новой вкладкой на всех размерах.
- [x] ПК-отзывы используют плотный случайный поднабор без3–4-высотных полос, до960px все8 сразу доступны в карусели.
- [x] Постоянный нативный4px scrollbar имеет полный округлый контур; autohide отменён, красный цвет одинаков в темах, hover синий без изменения ширины.
- [x] Исправить WebKit961px scrollbar/MQ и modal-scroll конфликт у общих владельцев; локальный modal/resize freeze150/150 завершён.
- [x] Ограничить offscreenAbout paint без изменения композиции; завершить3парных trace без параллельной нагрузки. Отдельно зафиксировать провайдерную стоимость и границу лабораторного вывода.
- [x] Унифицировать «Знакомство» у мастеров и панели; центрировать плашку с20px полями без icon. Обложки интервью сохраняют4:3 и общий крестик при низком окне.
- [x] FAQ получает «Знание — сила!» только изheadlines.ts. Парные кавычки отображаются как«…» через общий typography-rules.
- [x] В тёмной теме оставить жёлтые заголовки, в светлой красные; не возвращать розовый замещающий токен.
- [x] Личные контакты используют две колонки при700–960px доступной ширины, равные8px поля фотографии и близкую группу телефон/Telegram; увеличенный текст переносит композицию.
- [x] Принять cookie dialog локально в3движках: раздельный выбор, отказ/отзыв,180дней, keyboard/Escape, nested menu,200% и правый край scrollport. «Данные и согласие» — общий оформленныйFAQ-аккордеон; редактура сохраняет существенные условия. SDK в этих проверках подменён.
- [x] Закрыть локальные Header54, короткие меню24 и часы60 сценариев. NativeC37jobs завершены отдельно; actualD technical canvas18/18 и Header3/3 также завершены в своей области.

### 3. Воспроизводимость и GitHub

- [x] Сохранить действующийnewsworker/API-поток без чтения/вывода ключа; измененияnews ограниченыsoyuz namespace.
- [x] Каноническийignore содержит9ID:1927,1935,1937,1941,1943,1945,1950,1955,1960.
- [x] Обновить локальныйfallback иfixture из проверенногоAPI-среза сSHA медиа:10постов/22уникальных варианта изображений, запрещённыхID нет; новости не встроены вHTML.
- [x] Подготовить production-only source-tree, собственныеnode_modules/.venv и bootstrapBcc3.627путей исходников сверены побайтно, public384 не расширен личными оригиналами/preview.
- [x] Разделить runtime иlocal provenance. Первый ошибочно выбранный gift-vector case переклассифицирован; последующий coldCI прошёл с фактическими case filters.
- [x] ПолучитьC из cleanCI:121Astro/0,99runtime,4release,9Python suites/41PASS; исходный public-граф384 совпадает сB.
- [x] Создать изолированную `codex/soyuz-release`, commit `509fed9…`; actual Actions `43800396980` завершилсяsuccess. SF main не сливался и не менялся.
- [x] Закрыть CRLF actual-byte metadata: canonical UTF-8 LF exporter, byte assertions и actual package helper; D package9Python/46PASS.
- [x] ДляD выполнить условный coldCI ownership35/7/9,source384,release4.421compiled sourceSHA/client inputsC=D,13bodysemantic совпадают с учётомuuid/prefix; повторныйAstro/build дляhost-only delta не запускался.
- [x] Подготовить byte-faithful Git attrs и точный canonicalsource whitelist, не нормализуяSVG/оригиналы и не добавляяlocaljunk.
- [ ] Зафиксировать окончательный sourceE на codex/soyuz-release, получить новыйactualActions и подключить локальныйGit к точному remote snapshot без checkout/измененияworktree. Прежнийrun не доказывает будущийcommit.

### 4. Выпуск и публичная приёмка

- [x] СоздатьC `7a129e64e8086a5face7` изcleanCI:11content+2shared,421assets,57 320 419wire-байт; побайтно принятьroot-копию. Исторические manifest и результатыC сохранены.
- [x] Закрыть CRLF metadata и уточнить честныйartwork altSource без подмены бинарных постеров. D actual HEAD/body hashes подтверждаются записанными байтами и package helper.
- [x] Исправить выявленную на реальной Тильде opaque-заливкуbody/#allrecords через общийHOSTCSS transparent reset. C после этого не считается финальной host-приёмкой.
- [x] Создать и побайтно принятьD `d4040c957966781f777c`:11content+2shared,421wire,57 320 426байт,13HEAD сreset. D-candidate/gates — .local/release65/ci65D-20261116T061827Z/; noAstroBuild явно сохранён.
- [x] ПрочитатьCloud421/421SHA/MIME/encoding/cache. Отдельные9MIME/CORS-запросов дляfont/woff2,font/ttf,image/webp по3origins прошли в указанной области.
- [x] Сохранить canonical MIMEv4 и MIME-aware immutable identity. НовыйMIME получает новыйURL; metadata старогоimmutable объекта не перезаписывается.421compiled sourceSHA/client inputsC=D не означает одинаковые байты всех wireURL с новымbuild-prefix.
- [x] Завершить37nativeC jobs, ручные3-engine/touch и настоящийSDK transport. SDK HTML доставлялсяsynthetic fixture; это не публичныйHTTPS и не подтверждение ingestion в кабинетах. События без реальной заявки/оплаты/PII.
- [x] Завершить24лабораторных benchmark samplesC с3образцами/профиль иbaseline. Они не называются замерамиD, fieldINP или доказательством физических устройств. Отдельные Aboutpaint trace сохраняют свою область.
- [x] ПринятьD-opaque fixture18/18. Это проверка reset встенде; последующий actualD браузерныйрезультат принят отдельно.
- [x] Сохранить историческийD13/13publish/postHEADcodeEXACT; после найденногоfooter-дефекта он заменёнE.
- [x] Расширить единственныйHOST_CSS reset наbody/#allrecords/#t-header/#t-footer; E compiled421=D,body13EXACTпослеprefix,HEAD13толькоreset.
- [x] Пройти cleanCI Eownership35/7/9,source384,release4,9Python46; nativeE18 со всеми4transparentwrapper и3footerpixels/caseGREEN.
- [x] ОпубликоватьE13/13officialMCP shared-first, получить13postHEAD/codeEXACT,Cloud421/421; registryE.
- [x] Проверить actual technical HTTP12cases:11маршрутов+unknown404,currentEasset closure,Twitter/lang/alt/canonical. ОсновнойGoogle LIVE-fetch подтверждён отдельно.
- [x] Сохранить actualD18 body-canvas иHeader3/3 вHOST_CANVAS_65D.md как ограниченнуюисторию; светлыеуглыt-footer найдены позже. Это не финальная host-приёмка.
- [x] ActualE18/18 technical HTTPS GREEN; Header3/3 сохранил gap8px, radius20px, фон#252525 и8px status-dot. После добавленного владельцем исключения Happ/Xray основной https://soyuz.hair также прошёл18/18 усиленных canvas/footercorner cases в3движках, обе темы и390/961/1440px; HTTP12/12PASS,177currentresources. Доказательства: HOST_CANVAS_65D.md и tmp/planning/iteration65/host-canvas/E-main-public/.
- [x] Зафиксировать новыйGSC robotsfetch168Б16.11.2026 02:34. LIVE16.11.2026 09:10:23 подтвердил главную доступнойGoogle,fetch успешен,crawlAllowed/indexAllowed,canonicalsoyuz.hair,videoDetected.
- [x] ВыполнитьRequestIndexSUCCESS с постановкой вpriorityqueue. Скрин artifacts/iteration65/search-console/index-request.jpg. Это не означает already indexed.
- [x] ПовторитьGSC/ЯндексUI: Google sitemap16Novпринят,но«Не получено»,0URL; Яндексfreshreadonly/Adddisabled,неотправлен.
- [ ] Закрыть внешнее получениеGoogle sitemap/доступную отправкуЯндекса без подменыобходаиндексацией.
- [x] Владелец самостоятельно добавил сайт в исключения Happ/Xray. После этого основной HTTPS прошёл HTTP12/12 и18/18 browser canvas/footercorner cases в3движках. Агент не менял VPN, DNS или проверку сертификата. Прежний timeout сохранён как история маршрута, а не текущий отказ сайта.
- [x] Актуализировать текущиеPROGRESS,RELEASE_TRACKER,CIplan,этотплан иtilda-import/checks под опубликованныйE с явнымиpending иDкакboundedhistory. Историческиеevidence не переписывать.
- [ ] После actualE18 иfinalsourceEcommit записать последние результаты вCURRENTdocs. Текущийremote509/старыйActions не объявлять финальным; nativeE18 не выдавать заactualE.

### 5. Условие завершения

Цель завершается после фактического выполнения обязательныхкритериев;отправленныйsitemapиуспешныйlocalbuildсами по себе не доказывают публичнуюприёмку. Физическиетелефоны исключенывладельцем,неблокируюттекущуюработу. Необработаннаявнешняязадержкасервисафискируетсяотдельно;остальныечастипродолжаются.
