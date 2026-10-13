# v19 — нижнее затемнение: устранение неоднозначности и viewport

## Что установлено по исходникам v18
- В конце `dist/index.html` v18 уже отключал `.feed > .slide > .video-gradient` через `display:none!important`, выключал overlay просмотрщика и псевдоэлементы на feed/slide/video/meta. Значит, ещё один похожий CSS override не является обоснованным исправлением.
- `renderFeed()` всё ещё создавал пустой `<div class="video-gradient"></div>` на каждом слайде. В v19 этот слой удалён непосредственно из шаблона, а не только скрыт стилями.
- v18 использовал `100dvh` как единственный источник высоты. Telegram Mini App имеет собственный `Telegram.WebApp.viewportHeight`, который может не совпадать с CSS `100dvh` на Android WebView. В v19 высота ленты и слайда обновляется из Telegram viewport, с `visualViewport.height` и `innerHeight` в качестве fallback, а также при `viewportChanged`, resize и повороте экрана.
- В HTML добавлен маркер `TELEGRAM_SHORTS_BUILD=v19.0.0`; он позволяет проверить, что сервер отдаёт именно новый файл, а не старую копию.

## Что это не доказывает
Статический аудит не может подтвердить, что Railway уже развернул этот ZIP, что Telegram открыл именно этот deployment, или что градиент не является частью самого видео. Нельзя объявлять дефект устранённым до проверки после публикации в Telegram на Android.

## Файлы
- `dist/index.html` — удалён DOM-слой градиента, добавлена синхронизация viewport и build marker.
- `package.json` — версия 19.0.0.
- `docs/quality/BUG_LEDGER.md` — обновлена причина/статус BUG-010.

## Проверки
- Проверить синтаксис JavaScript встроенного скрипта.
- Проверить, что шаблон feed больше не создаёт `.video-gradient`.
- Проверить наличие обработчика `viewportChanged` и build marker.
- После замены файла и deployment открыть Mini App заново. Если затемнение останется, следующий шаг — сравнить исходный URL видео и live HTML; не добавлять новые CSS override вслепую.
