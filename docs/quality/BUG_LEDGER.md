# Telegram Shorts — журнал дефектов

Причины помечаются как подтверждённые только при наличии доказательства. Закрытый дефект сохраняется для регрессии.

| ID | Приоритет | Симптом | Причина/доказательство | Исправление/профилактика | Статус v13.1 |
|---|---|---|---|---|---|
| BUG-001 | P1 | Лайк ставит видео на паузу | Требует device reproduction; в коде есть изоляция действий | Проверять тап/двойной тап на Android после изменений жестов | NEEDS-RUNTIME-TEST |
| BUG-002 | P1 | Вкладки/навигация работают неправильно | Подтверждённая архитектурная проблема: нижние пункты были единственным путём к созданию и уведомлениям | Удалена нижняя панель; добавлены верхние кнопки с явными обработчиками | STATIC-FIXED, RUNTIME-OPEN |
| BUG-003 | P2 | Текст/иконки смещены | Визуальная причина не подтверждена без скриншотов | Проверить узкий экран и длинный текст; не менять общие CSS без регрессии | OPEN |
| BUG-004 | P2 | Счётчик лайков профиля смещён | Требует визуального воспроизведения | Сохранять tabular numerals/flex alignment; проверять на устройстве | OPEN |
| BUG-005 | P2 | Серая рамка username | В актуальном CSS у `.author-name` нет рамки, но требуется проверить реальный экран | Не добавлять border; проверить на устройстве | STATIC-CODE-OK, RUNTIME-OPEN |
| BUG-006 | P2 | История просмотров видна | В production HTML нет строки `history`; runtime навигацию надо проверить | Не добавлять историю и не удалять таблицу video_views | STATIC-CODE-OK, RUNTIME-OPEN |
| BUG-007 | P0 | Нижняя навигация всё ещё включена в production HTML | Подтверждено: `<nav class="bottom">`, CSS `.bottom` и делегированный `[data-nav]` handler присутствовали в main | Удалены markup, CSS и handler; действия перенесены в topbar; нижние отступы уменьшены | STATIC-FIXED, RUNTIME-OPEN |
| BUG-008 | P1 | Описание видео не сохраняется/не отображается | Не подтверждено на живой базе | Проверить публикацию и повторное открытие | OPEN |
| BUG-009 | P0 | initData без auth_date/с будущим временем мог пройти freshness check | Подтверждено: код раньше проверял возраст только если auth_date truthy | Обязательный auth_date, reject future >60s, reject >24h, duplicate parameter check, positive user id | STATIC-FIXED, RUNTIME-OPEN |

## Уроки против повторения
- Не считать удаление градиента эквивалентом удаления панели: проверять HTML, CSS, обработчики и отступы.
- Не считать наличие кода доказательством работы на устройстве.
- Проверять Telegram initData как подписанный временной пакет, а не только проверять hash.


| BUG-010 | P1 | Сильное затемнение снизу сохраняется | В v18 `.video-gradient` и `.viewer-overlay` уже были отключены CSS-правилами, поэтому повторное добавление CSS override не являлось достаточной диагностикой. В скриншоте затемнение видимо на разных кадрах; без живого DOM/кадра исходного видео нельзя окончательно доказать, это слой production HTML или содержимое видео. Также v18 зависел от `100dvh`, не от Telegram `viewportHeight`. | v19 удаляет `.video-gradient` из создаваемой разметки и синхронизирует высоту с Telegram WebApp viewport, с visualViewport/innerHeight fallback. Добавлен уникальный build marker для проверки фактически развернутого HTML. | FIXED-IN-CODE, DEPLOY-AND-DEVICE-OPEN |
| BUG-011 | P1 | Двойной тап ставит лайк и тут же снимает его | Подтверждено в браузерном тесте: один жест обрабатывался через `pointerup`, а затем повторно через безусловный `dblclick`; два POST оставляли исходное состояние | `dblclick` fallback ограничен legacy-средами без Pointer Events и без touch; проверены постановка и снятие лайка по одному POST на жест | FIXED-IN-CODE, DEVICE-OPEN |
| BUG-012 | P1 | Быстрые повторные лайки теряются или расходятся с сервером | Ранее `data-busy` блокировал новый запрос; API работает как toggle, поэтому параллельные запросы опасны | Добавлен сериализованный reconciler желаемого состояния: запросы выполняются по одному, итог согласуется с сервером, быстрые жесты не теряются | FIXED-IN-CODE, DEVICE-OPEN |
| BUG-013 | P2 | В просмотрщике сохранённых видео двойной тап не работал одинаково с лентой | Подтверждено по коду: overlay перехватывал события и не было обработчика двойного тапа | Overlay пропускает касания; добавлены жесты, центральная анимация и общий обработчик лайка | FIXED-IN-CODE, DEVICE-OPEN |

## Регрессионное правило для лайков
- Для одного двойного тапа должен быть ровно один логический toggle и один серверный запрос, если нет незавершённого запроса.
- Двойной тап на уже лайкнутом ролике снимает лайк; на нелайкнутом — ставит.
- Нажатие лайка не меняет состояние воспроизведения.
- Feed и saved viewer используют общий обработчик и синхронизируют состояние кнопок/счётчика.
- Проверять Pointer Events и не запускать одновременно второй `dblclick`-обработчик в современных браузерах.


## Audit follow-up — 2026-10-11
- [P1] Bottom shading: feed and saved-viewer overlays are explicitly transparent; check the actual Telegram WebView because any darkening baked into source media is not removable by CSS.
- [P1] Shared URLs: share action now requests `/api/share-link/{video_id}` and creates `https://t.me/{bot_username}?startapp=video_{id}`; requires Main Mini App configured in BotFather. The start parameter is resolved on app startup and opens the video viewer.
- [P1] Profile cover: profile and saved grids use `thumbnail_url` as the `poster`; if older uploads have no thumbnail, browser-generated first-frame behavior remains dependent on the video codec/browser.
- [P1] Swipe navigation: saved/profile/search video results share the vertical snap viewer; inactive videos use `preload=none`. Validate with real Telegram Android gestures and slow-network conditions.

## BUG-010 — тёмная область снизу видео / версия фронтенда
- Статус: исправление v20 подготовлено; требуется подтверждение на Android после deployment.
- Изменения: измерение viewport из визуального окна, полное отключение feed scrim/псевдоэлементов, абсолютный путь `dist`, `/health/build` и заголовок сборки.
- Проверка: открыть `/health/build`, убедиться в `v20.0.0`, затем проверить Mini App на устройстве.

## BUG-011 — прокрутка видео в профиле
- Статус: исправление v20 подготовлено; требуется подтверждение на Android.
- Причина в CSS v19: viewer наследовал размеры и overflow обычной bottom-sheet панели без определённой высоты для внутреннего scroll-контейнера.
- Исправление: полноэкранная панель, заданные высоты shell/track/item и scroll position, рассчитанная по фактической высоте item.

