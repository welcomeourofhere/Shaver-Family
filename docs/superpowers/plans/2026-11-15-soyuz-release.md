# Релиз СОЮЗа: Implementation Plan

> **For agentic workers:** Use `executing-plans` to implement this plan task-by-task in the current checkout. Пользователь уже поручил выполнение; отдельное согласование выбора процесса не нужно.

**Goal:** Выпустить проверенный сайт СОЮЗа на soyuz.hair с общей шапкой/подвалом Тильды,3документами, воспроизводимой доставкой и работающими интеграциями.

**Architecture:** Astro-компоненты и JSON остаются источником. Экспорт разделяет общий shell и содержимое до публикации; Тильда вставляет отдельные header/footer нативно, ресурсы обслуживает версионированный префикс Яндекс Облака. Один runtime обслуживает общие действия, динамический JSON владеет новостями.

**Tech Stack:** Astro5, TypeScript, CSS/WAAPI/нативная прокрутка, Python standard library/BeautifulSoup/tinycss2, Playwright для изолированной QA, Tilda MCP, существующий AWS CLI, GitHub Actions.

**Spec:** `docs/RELEASE_SPEC_64.md`.

## Global Constraints

- Продакшен Shaver Family19258126 и его файлы/аналитику не менять.
- Физические телефоны исключены владельцем; эмуляция не является проверкой физического Safari.
- Никаких реальных записей, покупок или сообщений другим людям.
- Исходники меняются в src/content; dist и доказательства создаются командами.
- Loader №04:1250ms,0/80/160/240ms, ease-in-out,2px,.3→1,44–65%.
- Кнопка: одна строка, минимум12px по бокам/44px область нажатия.
- Документы публикуются только с подтверждёнными реквизитами; секреты не выводятся.
- Поиск открывается после валидного HTTPS и публичной приёмки.

## Карта файлов и владельцев

| Область | Файлы | Ответственность |
|---|---|---|
| Загрузка | LoadingIndicator.astro, loading.css, loading.ts, Hero.astro, hero-news.ts | Единый loader/пауза/статус сети |
| Общая оболочка | Header.astro, Footer.astro, Document.astro, страницы index/masters/404, prepare-tilda-release.py | Один shell, готовый HTML, native header/footer |
| Навигация/движение | template.ts, header-menus.ts, page-motion.ts, about.ts, about.css | Принятые действия, правильные якоря/закрепление |
| Документы | content/legal/, новый общий LegalDocument.astro/маршрут, legal.css | Проверенный текст/источники/печать |
| Доставка | deploy/production.json, tilda-pages.json, analytics.json, scripts/upload-tilda-assets.py, .github/workflows/ | Ограниченный адресат, хеши и проверяемый релиз |
| Приёмка | tests/iteration64-*.py, release_package_test.py, release-routes.py, docs/RELEASE_TRACKER.md | Воспроизведение, матрица, метрики, блокеры |

## Состояние после выпуска64 и приёмка65

Ниже текущая последовательность. История начального воспроизведения64 сохранена в журналах tmp/planning/iteration64 и RELEASE_SPEC_64; checklist не продолжает считать уже выполненные внешние настройки отсутствующими.

### 1. Общая архитектура и настройки

- [x] Подтвердить реквизиты исполнителя и график11:00–22:00 у владельца.
- [x] Создать три полных документа,6интервью и404 из общих Astroкомпонентов.
- [x] Создать штатные2sharedстраницыТильды, назначить их всем11contentмаршрутам.
- [x] Проверить обычное движение/якоря/меню на nativewrapper стенде и public64.
- [x] Проверить валидныйHTTPS,домен,основныеHEAD/canonical/robots/sitemap,отдельныесчётчикибезnativeдублей.
- [ ] Повторить redirects/unknown404 и весь common-shell на финальном65 по фактическомуHTTPS.

### 2. Замечания владельца65

- [x] Найти общий конфликт exportCSS: inline/external получают одинаковую защиту специфичности.
- [x] Самостоятельные glyphpaths messenger/utility; убрать внешниеSVGuse/неразрешённыйсимволстрелки.
- [x] Взять4существующихутверждённыхпостера из соседнего чата, сохранитьorigins/hashes.
- [x] Вернуть компактную основу подвала, полные документы ниже, убратьАналитику.
- [x] Единые48px кнопки звук/тема/cookie,Контактывтомжеряду;жёлтаяшестерёнка/синийНаверх.
- [x] Heroбезкраевогозатемнения/blur;жёлтыестрелки→красныйhover;Наверхтакойжеконтурповёрнутый.
- [x] Часы:короткийстатус/отдельноевремя;нижняясекцияполностьюудаленапоследнимуточнением.
- [x] ПодаркискрытыизHTMLзаглушки;однотонныйсерыйplaceholder;сохранёнVisitGifts,сертификатактивен.
- [x] НоваяПКсеткаслучайногоподнаборабезэкстремальныхформатов;мобильныевсе8отзывов.
- [x] ИсправитьWebKit961pxscrollbarfeedbackвобщемвладельце.
- [x] ВоспроизвестиoffscreenAboutpaintприподходеккарте,сохранитьгеометриюиограничитьpaintвслоях.
- [ ] Завершить3парныхпрофилякарты/кадрыбезпараллельнойнагрузки;задокументироватьостаточнуюстоимостьпровайдера.
- [ ] Принятьcookieдиалогв3движках:раздельныйвыбор,отказ/отзыв,Tab/Escape,200%,правыйкрайscrollport.
- [ ] Общийprivatecheck/build/allunits,releasebuild/metadata/package;проверитьвсеизменениянаодномфинальномmanifest.

### 3. Воспроизводимость и GitHub

- [x] Действующийnewsworker/APIsecretбезчтенияключа;mainменяетсятольковsoyuznamespace.
- [x] Ignore1950/1941/1937/1943записан;workflow43755873259success,свежийpublicJSON10постовбезэтихID.
- [ ] Обновитьлокальныйfallback/fixtureизтого же проверенногоAPIJSONсSHAмедиа.
- [ ] Чистыйsource-tree:productionисходники/lockfile/runtimeassets;локальныеQApreview/originalsсохраняютсяотдельно.
- [ ] ПройтиCIrehearsalсbootstrap-public;явноразделитьruntimegatesилокальныйprovenance.
- [ ] Создатьизолированнуюcodex/soyuz-releaseветку,проверитьactualGitHubCI;несливатьвmainSF.

### 4. Выпуск и публичная приёмка

- [ ] Подготовить65manifestс11content+2sharedпарами;прочитатьpackage/nativefixture.
- [ ] ЗагрузитьCloudgraphвSoyuz/releases,прочитать100%SHA/MIME/gzip/immutableиCORSfont.
- [ ] Прочитатьтекущие13T123/HEAD,сохранитьточныйкандидат,прочитать13/13точныхсовпадений.
- [ ] Публиковатьsharedпередcontent;отдельнозафиксироватьpublishedbuildвtilda-pages.json.
- [ ] ПубличныйbrowserChrome/Firefox/WebKit:обетемы,320–1920,960/961,низкиевысоты,200%,normal/reduced,menus/contacts/reading/drag/interrupt/bookingloader/certnewtab.
- [ ] ПубличныйHTTP11маршрутов:1H1/metadata/canonical/lang/alt,redirects/404,10URLsitemapбезshared.
- [ ] ПовторитьactualGA4/Метрикаeventtransportпослеотдельногосогласия,безреальнойзаявки/покупки/PIIpayload.
- [ ] Сопоставимыйcoldloadbenchmark3образца/профиль и причиннаяпроверкаостаточногомедленногоLCP;невыдаватьлабораториюзаfieldINP.
- [ ] ПроверитьGSCfetchsitemap;Яндексreadonlyвнешнийстатуснеподменятьиндексацией.
- [ ] ОбновитьPROJECT_MAP/PROGRESS/RELEASE_TRACKER/DEVICE_OPTIMIZATION/TILDA_SETTINGSточнымиссылкаминадоказательства.

### 5. Условие завершения

Цель завершается после фактического выполнения обязательныхкритериев;отправленныйsitemapиуспешныйlocalbuildсами по себе не доказывают публичнуюприёмку. Физическиетелефоны исключенывладельцем,неблокируюттекущуюработу. Необработаннаявнешняязадержкасервисафискируетсяотдельно;остальныечастипродолжаются.
