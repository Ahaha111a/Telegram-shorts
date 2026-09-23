import React from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const tg = window.Telegram?.WebApp;

function App() {
  React.useEffect(() => {
    if (tg) {
      tg.ready();
      tg.expand();
    }
  }, []);

  return (
    <main className="app">
      <section className="short">
        <div className="top">
          <strong>Telegram Shorts</strong>
          <button className="icon-button" aria-label="Настройки">⋯</button>
        </div>

        <div className="center">
          <div className="play">▶</div>
          <h1>Telegram Shorts</h1>
          <p>Вертикальная лента коротких видео</p>
          <button className="primary">Начать просмотр</button>
        </div>

        <div className="actions">
          <button>♡<span>Лайк</span></button>
          <button>💬<span>Комментарии</span></button>
          <button>↗<span>Поделиться</span></button>
          <button>👤<span>Профиль</span></button>
        </div>

        <div className="caption">
          <b>@telegram_shorts</b>
          <p>Добро пожаловать в первую версию Telegram Shorts.</p>
          <small>#TelegramShorts #shorts</small>
        </div>

        <nav className="bottom">
          <button className="active">⌂<span>Главная</span></button>
          <button>⌕<span>Поиск</span></button>
          <button className="create">＋</button>
          <button>♡<span>Подписки</span></button>
          <button>◯<span>Профиль</span></button>
        </nav>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
