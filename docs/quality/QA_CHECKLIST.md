# Telegram Shorts — QA-чек-лист

Статусы: `PASS`, `FAIL`, `BLOCKED`, `NOT RUN`. Не ставить PASS без фактической проверки.

## A. Статика/структура
- [x] Python `bot.py` компилируется.
- [x] Inline JavaScript проходит `node --check`.
- [x] HTML разбирается без ошибок и повторяющихся ID.
- [x] В ZIP сохранены нужные пути и отсутствуют секреты.
- [x] Diff содержит только ожидаемые изменения.

## B. Навигация
- [x] Нижняя навигация удалена из HTML.
- [x] Стили нижней навигации и её делегированные обработчики удалены.
- [x] Верхние кнопки поиска, создания, уведомлений и профиля имеют обработчики.
- [ ] Все переходы проверены в реальном Telegram WebView.
- [ ] Нет зарезервированного нижнего пространства на разных экранах.

## C. Авторизация/безопасность
- [x] Подпись initData сравнивается constant-time.
- [x] Дубли параметров, отсутствие/некорректность auth_date, время в будущем и срок старше 24 ч отклоняются.
- [x] Telegram user id проверяется на положительное целое.
- [ ] Успешная и неуспешная авторизация проверена на живом Telegram.
- [ ] Проверено удаление чужого видео и чужого комментария.

## D. Лента и социальные действия
- [ ] Свайпы/тап/двойной тап проверены на Android.
- [ ] Лайк не ставит видео на паузу на реальном Android; в браузерном тесте проверен путь обработчика.
- [ ] Комментарии/ответы/лайки и счётчики согласованы с базой.
- [ ] Сохранённое/поиск/профиль открывают общий просмотрщик с действиями.
- [ ] Удаление требует подтверждения и корректно обновляет UI.

## E. Профиль/публикация/жалобы
- [ ] Видео профиля загружаются из API.
- [ ] Длинные имя, username, био и описание не ломают вёрстку.
- [ ] Видео загружается, MIME/размер проверяются сервером.
- [ ] Описание и хэштеги сохраняются.
- [ ] «Другое» требует пояснение.

## F. Визуальная приёмка
- [ ] Узкий Android-экран, безопасные зоны, клавиатура и длинные тексты проверены.
- [ ] Нет обрезаний, наложений и неработающих touch-зон.
- [ ] Реальный Telegram/Railway/Supabase сценарий выполнен либо явно помечен BLOCKED.

## Проверки v12, выполненные локально
- PASS: Python AST/compile.
- PASS: Node.js syntax check для inline JavaScript.
- PASS: HTMLParser structural parse; проверка уникальности ID.
- PASS: поиск нижней навигации, `data-nav` и зарезервированных CSS-ссылок.
- PASS: локальные проверки структуры ZIP и отсутствия `.env`.
- BLOCKED: реальный Telegram WebView, Railway, Supabase и визуальные скриншоты устройства.


## Проверки v13.1, выполненные локально

- PASS: `node --check` для inline JavaScript.
- PASS: `python -m py_compile bot.py`.
- PASS: HTML parse и проверка повторяющихся ID.
- PASS: headless Chromium с mock API — двойной тап в ленте ставит лайк ровно одним запросом.
- PASS: headless Chromium с mock API — следующий двойной тап снимает лайк ровно одним запросом.
- PASS: headless Chromium с mock API — двойной тап в просмотрщике сохранённых видео ставит лайк; кнопка снимает лайк.
- PASS: headless Chromium с задержкой mock API — два быстрых двойных тапа приводят к согласованному исходному состоянию без параллельных toggle-запросов.
- PASS: computed styles подтверждают, что `.video-gradient` и `.viewer-overlay` больше не содержат нижний чёрный стоп; overlay просмотрщика имеет `pointer-events:none`.
- BLOCKED: реальный Telegram WebView, физический Android, Railway и Supabase не подключались; проверка браузера с mock API не заменяет устройство.


## Regression cases added (must run on Telegram Android)
- [ ] Confirm no CSS overlay shades the lower video area in feed and saved viewer.
- [ ] Share a video, open the t.me startapp link, and verify the same video opens inside the Mini App (requires Main Mini App setup in BotFather).
- [ ] Swipe exactly once up/down in feed, profile, saved, and search viewers; confirm one item transition per swipe.
- [ ] Verify profile grid uses `thumbnail_url` posters and remains responsive with many videos.
- [ ] Test low-bandwidth loading, rapid tab switching, closing viewers, and return from background.
