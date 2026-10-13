import os
import asyncio
import json
import hmac
import hashlib
import time
import re
import traceback
from pathlib import Path
from urllib.parse import parse_qsl, quote

import asyncpg
import httpx
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import uvicorn

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://telegram-shorts-production.up.railway.app")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
STORAGE_BUCKET = "videos"
MAX_VIDEO_SIZE = 50 * 1024 * 1024
ADMIN_TELEGRAM_IDS = {int(x.strip()) for x in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",") if x.strip().isdigit()}

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден")
if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL не найден")
if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY не найден")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()
db_pool = None


async def get_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=5,
            statement_cache_size=0,
            command_timeout=25,
        )
    return db_pool


async def init_db():
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        await connection.execute("""
        create table if not exists users (
            id bigint primary key,
            username text,
            custom_username text,
            first_name text,
            last_name text,
            avatar_url text,
            bio text,
            created_at timestamptz not null default now()
        );

        create table if not exists videos (
            id bigint generated always as identity primary key,
            user_id bigint not null references users(id) on delete cascade,
            video_url text not null,
            thumbnail_url text,
            caption text,
            views_count bigint not null default 0,
            likes_count bigint not null default 0,
            comments_count bigint not null default 0,
            is_deleted boolean not null default false,
            deleted_at timestamptz,
            created_at timestamptz not null default now()
        );

        create table if not exists video_views (
            id bigint generated always as identity primary key,
            video_id bigint not null references videos(id) on delete cascade,
            user_id bigint references users(id) on delete set null,
            viewed_at timestamptz not null default now()
        );

        create table if not exists video_likes (
            video_id bigint not null references videos(id) on delete cascade,
            user_id bigint not null references users(id) on delete cascade,
            created_at timestamptz not null default now(),
            primary key (video_id, user_id)
        );

        create table if not exists video_saves (
            video_id bigint not null references videos(id) on delete cascade,
            user_id bigint not null references users(id) on delete cascade,
            created_at timestamptz not null default now(),
            primary key (video_id, user_id)
        );

        create table if not exists video_watch_history (
            user_id bigint not null references users(id) on delete cascade,
            video_id bigint not null references videos(id) on delete cascade,
            watched_seconds numeric(10,2) not null default 0,
            completed boolean not null default false,
            last_watched_at timestamptz not null default now(),
            primary key (user_id, video_id)
        );

        create table if not exists comments (
            id bigint generated always as identity primary key,
            video_id bigint not null references videos(id) on delete cascade,
            user_id bigint not null references users(id) on delete cascade,
            text text not null,
            created_at timestamptz not null default now()
        );

        create table if not exists follows (
            follower_id bigint not null references users(id) on delete cascade,
            following_id bigint not null references users(id) on delete cascade,
            created_at timestamptz not null default now(),
            primary key (follower_id, following_id),
            check (follower_id <> following_id)
        );

        alter table users add column if not exists custom_username text;
        alter table videos add column if not exists is_deleted boolean not null default false;
        alter table videos add column if not exists deleted_at timestamptz;
        alter table videos add column if not exists hashtags text[] not null default '{}';
        create index if not exists idx_videos_hashtags on videos using gin (hashtags);
        create table if not exists reports (
            id bigint generated always as identity primary key,
            reporter_id bigint not null references users(id) on delete cascade,
            video_id bigint not null references videos(id) on delete cascade,
            reason text not null,
            details text,
            status text not null default 'open',
            created_at timestamptz not null default now(),
            resolved_at timestamptz,
            resolved_by bigint references users(id) on delete set null,
            unique (reporter_id, video_id)
        );

        create table if not exists video_preferences (
            user_id bigint not null references users(id) on delete cascade,
            video_id bigint not null references videos(id) on delete cascade,
            kind text not null,
            created_at timestamptz not null default now(),
            primary key (user_id, video_id, kind)
        );
        create table if not exists hidden_authors (
            user_id bigint not null references users(id) on delete cascade,
            author_id bigint not null references users(id) on delete cascade,
            created_at timestamptz not null default now(),
            primary key (user_id, author_id),
            check (user_id <> author_id)
        );
        create table if not exists user_blocks (
            blocker_id bigint not null references users(id) on delete cascade,
            blocked_id bigint not null references users(id) on delete cascade,
            created_at timestamptz not null default now(),
            primary key (blocker_id, blocked_id),
            check (blocker_id <> blocked_id)
        );
        create table if not exists user_reports (
            id bigint generated always as identity primary key,
            reporter_id bigint not null references users(id) on delete cascade,
            reported_user_id bigint not null references users(id) on delete cascade,
            reason text not null,
            details text,
            status text not null default 'open',
            created_at timestamptz not null default now()
        );
        create index if not exists idx_videos_created_at on videos (created_at desc);
        create index if not exists idx_videos_user_id on videos (user_id);
        create index if not exists idx_video_views_video_id on video_views (video_id);
        delete from video_views a using video_views b
        where a.id > b.id and a.video_id = b.video_id and a.user_id is not null
          and a.user_id = b.user_id;
        create unique index if not exists uq_video_views_user_video
            on video_views(video_id,user_id) where user_id is not null;
        create index if not exists idx_comments_video_id on comments (video_id);
        create index if not exists idx_video_saves_user_id on video_saves (user_id, created_at desc);
        create index if not exists idx_video_saves_video_id on video_saves (video_id);
        create table if not exists notifications (
            id bigint generated always as identity primary key,
            user_id bigint not null references users(id) on delete cascade,
            actor_id bigint references users(id) on delete cascade,
            type text not null,
            video_id bigint references videos(id) on delete cascade,
            created_at timestamptz not null default now(),
            is_read boolean not null default false
        );

        create index if not exists idx_follows_following_id on follows (following_id);
        create index if not exists idx_video_preferences_user_id on video_preferences (user_id, created_at desc);
        create index if not exists idx_hidden_authors_user_id on hidden_authors (user_id, created_at desc);
        create index if not exists idx_user_blocks_blocker_id on user_blocks (blocker_id, created_at desc);
        create index if not exists idx_user_reports_status_created_at on user_reports (status, created_at desc);
        create index if not exists idx_notifications_user_id on notifications (user_id, created_at desc);
        create index if not exists idx_reports_status_created_at on reports (status, created_at desc);
        """)
    print("Supabase: таблицы успешно проверены/созданы.")


async def init_storage():
    """Проверяет наличие Storage bucket и создаёт его только если его действительно нет.

    Supabase может вернуть HTTP 400 с code=BucketAlreadyExists вместо 409,
    поэтому проверяем bucket через GET и отдельно обрабатываем оба варианта.
    """
    base_url = SUPABASE_URL.rstrip("/")
    bucket_url = f"{base_url}/storage/v1/bucket/{STORAGE_BUCKET}"
    create_url = f"{base_url}/storage/v1/bucket"
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
    }
    payload = {"id": STORAGE_BUCKET, "name": STORAGE_BUCKET, "public": True}

    async with httpx.AsyncClient(timeout=20) as client:
        # Сначала проверяем bucket. Это делает запуск идемпотентным:
        # существующий bucket никогда не считается ошибкой.
        check = await client.get(bucket_url, headers=headers)
        if check.status_code == 200:
            print(f"Supabase Storage: bucket {STORAGE_BUCKET} уже существует.")
            return

        if check.status_code not in (404,):
            raise RuntimeError(
                f"Не удалось проверить Storage bucket: "
                f"{check.status_code} {check.text[:300]}"
            )

        # Bucket отсутствует — создаём его.
        create_headers = {**headers, "Content-Type": "application/json"}
        response = await client.post(
            create_url, headers=create_headers, json=payload
        )

        if response.status_code in (200, 201):
            print(f"Supabase Storage: bucket {STORAGE_BUCKET} создан.")
            return

        # При параллельном запуске другой процесс мог создать bucket
        # между GET и POST. Supabase в таком случае иногда отвечает 409,
        # а иногда 400 с code=BucketAlreadyExists. Оба случая безопасны.
        try:
            error_data = response.json()
        except ValueError:
            error_data = {}

        if (
            response.status_code == 409
            or error_data.get("code") == "BucketAlreadyExists"
            or error_data.get("message") == "The resource already exists"
        ):
            print(f"Supabase Storage: bucket {STORAGE_BUCKET} уже существует.")
            return

        raise RuntimeError(
            f"Не удалось создать Storage bucket: "
            f"{response.status_code} {response.text[:300]}"
        )


async def save_user_data(user_data):
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        await connection.execute(
            """
            insert into users (id, username, first_name, last_name, avatar_url)
            values ($1, $2, $3, $4, $5)
            on conflict (id) do update set
                username = case when users.custom_username is null then excluded.username else users.username end,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                avatar_url = excluded.avatar_url
            """,
            int(user_data["id"]),
            user_data.get("username"),
            user_data.get("first_name"),
            user_data.get("last_name"),
            user_data.get("photo_url"),
        )


async def save_user(message: Message):
    user = message.from_user
    await save_user_data({
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "photo_url": None,
    })


def validate_telegram_init_data(init_data: str):
    if not init_data:
        raise ValueError("Telegram initData отсутствует")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("В initData отсутствует hash")

    data_check_string = "\n".join(
        f"{key}={parsed[key]}" for key in sorted(parsed.keys())
    )

    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN.encode(),
        hashlib.sha256,
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Неверная подпись Telegram initData")

    auth_date = int(parsed.get("auth_date", "0"))
    if auth_date and time.time() - auth_date > 86400:
        raise ValueError("Telegram initData устарел")

    user_json = parsed.get("user")
    if not user_json:
        raise ValueError("Данные пользователя отсутствуют")

    user_data = json.loads(user_json)
    if "id" not in user_data:
        raise ValueError("Telegram user id отсутствует")

    return user_data


async def get_authenticated_user(request: Request):
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    try:
        user_data = validate_telegram_init_data(init_data)
        await save_user_data(user_data)
        return user_data
    except Exception as error:
        raise HTTPException(status_code=401, detail=str(error))


async def upload_to_storage(file: UploadFile, user_id: int):
    allowed_types = {
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "video/quicktime": ".mov",
    }
    extension = allowed_types.get(file.content_type)
    if not extension:
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются только MP4, WebM и MOV.",
        )

    content = await file.read()
    if len(content) > MAX_VIDEO_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Видео слишком большое. Максимум 50 МБ.",
        )

    filename = f"{user_id}/{int(time.time() * 1000)}{extension}"
    storage_path = quote(filename, safe="/")
    url = (
        f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/"
        f"{STORAGE_BUCKET}/{storage_path}"
    )
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Content-Type": file.content_type,
        "x-upsert": "false",
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, headers=headers, content=content)

    if response.status_code not in (200, 201):
        print(f"Storage upload error: {response.status_code} {response.text[:500]}")
        raise HTTPException(status_code=500, detail="Не удалось загрузить видео.")

    public_url = (
        f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/public/"
        f"{STORAGE_BUCKET}/{storage_path}"
    )
    return public_url


@dp.message(Command("id"))
async def id_handler(message: Message):
    await message.answer(f"🆔 Ваш Telegram ID: <code>{message.from_user.id}</code>", parse_mode="HTML")


@dp.message(CommandStart())
async def start_handler(message: Message):
    await save_user(message)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="🎬 Открыть Telegram Shorts",
                web_app=WebAppInfo(url=WEB_APP_URL),
            )
        ]]
    )

    await message.answer(
        "👋 Добро пожаловать в Telegram Shorts!\n\n"
        "🎬 Смотри короткие видео и открывай новые возможности.",
        reply_markup=keyboard,
    )


@app.post("/api/auth")
async def authenticate(request: Request):
    try:
        body = await request.json()
        user_data = validate_telegram_init_data(body.get("initData", ""))
        await save_user_data(user_data)

        return {
            "ok": True,
            "user": {
                "id": int(user_data["id"]),
                "username": user_data.get("username"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "photo_url": user_data.get("photo_url"),
            },
        }
    except ValueError as error:
        return JSONResponse(status_code=401, content={"ok": False, "error": str(error)})
    except Exception as error:
        print(f"Auth error: {error}")
        return JSONResponse(status_code=500, content={"ok": False, "error": "Ошибка сервера"})


@app.get("/api/me")
async def get_me(request: Request):
    user = await get_authenticated_user(request)
    pool = await get_db_pool()

    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            """
            select
                u.id, coalesce(u.custom_username,u.username) as username, u.first_name, u.last_name, u.avatar_url, u.bio,
                (select count(*) from videos v where v.user_id = u.id and not v.is_deleted) as videos_count,
                (select count(*) from follows f where f.following_id = u.id) as followers_count,
                (select count(*) from follows f where f.follower_id = u.id) as following_count,
                (select coalesce(sum(v.likes_count),0) from videos v where v.user_id=u.id and not v.is_deleted) as likes_count
            from users u
            where u.id = $1
            """,
            int(user["id"]),
        )

    return {"ok": True, "user": dict(row) if row else None, "is_admin": int(user["id"]) in ADMIN_TELEGRAM_IDS}


@app.get("/api/feed")
async def get_feed(request: Request, mode: str = "recommended", offset: int = 0, limit: int = 30):
    user = await get_authenticated_user(request)
    pool = await get_db_pool()
    user_id = int(user["id"])
    mode = mode if mode in {"recommended", "following", "latest"} else "recommended"
    offset = max(0, min(int(offset), 5000))
    limit = max(1, min(int(limit), 50))

    async with pool.acquire() as connection:
        if mode == "following":
            order_sql = "v.created_at desc"
            where_extra = "and exists (select 1 from follows ff where ff.follower_id=$1 and ff.following_id=v.user_id)"
        elif mode == "latest":
            order_sql = "v.created_at desc"
            where_extra = ""
        else:
            # Простая детерминированная рекомендация без отдельного ML-сервиса:
            # свежесть + просмотры + лайки + комментарии + подписки.
            order_sql = """(
                (extract(epoch from (now() - v.created_at)) / 3600.0) * -0.45
                + ln(1 + v.views_count) * 0.18
                + ln(1 + v.likes_count) * 0.70
                + ln(1 + v.comments_count) * 0.95
                + case when exists (select 1 from follows ff where ff.follower_id=$1 and ff.following_id=v.user_id) then 1.80 else 0 end
                + coalesce((
                    select sum(interest.weight)
                    from (
                        select unnest(iv.hashtags) as tag, count(*)::float * 0.22 as weight
                        from video_watch_history wh
                        join videos iv on iv.id=wh.video_id
                        where wh.user_id=$1 and wh.last_watched_at > now() - interval '30 days'
                        group by 1
                    ) interest
                    where interest.tag = any(v.hashtags)
                ), 0)
                + case when exists (select 1 from video_saves vsr where vsr.user_id=$1 and vsr.video_id=v.id) then 0.35 else 0 end
            ) desc, v.created_at desc"""
            where_extra = ""

        query = f"""
            select
                v.id, v.user_id, v.video_url, v.caption,
                v.views_count, v.likes_count, v.comments_count, v.hashtags, v.created_at,
                coalesce(u.custom_username,u.username) as username, u.first_name, u.last_name, u.avatar_url,
                exists(
                    select 1 from video_likes vl
                    where vl.video_id=v.id and vl.user_id=$1
                ) as liked,
                exists(
                    select 1 from video_saves vs
                    where vs.video_id=v.id and vs.user_id=$1
                ) as saved,
                (select count(*) from video_saves vsc where vsc.video_id=v.id) as saves_count
,
                exists(
                    select 1 from follows ff2
                    where ff2.follower_id=$1 and ff2.following_id=v.user_id
                ) as following
            from videos v
            join users u on u.id=v.user_id
            where not v.is_deleted
              and not exists (select 1 from video_preferences vp where vp.user_id=$1 and vp.video_id=v.id and vp.kind='not_interested')
              and not exists (select 1 from hidden_authors ha where ha.user_id=$1 and ha.author_id=v.user_id)
              and not exists (select 1 from user_blocks ub where ub.blocker_id=$1 and ub.blocked_id=v.user_id)
              and not exists (select 1 from user_blocks ub where ub.blocker_id=v.user_id and ub.blocked_id=$1)
              {where_extra}
            order by {order_sql}
            limit $2 offset $3
        """
        rows = await connection.fetch(query, user_id, limit, offset)

    return {"ok": True, "mode": mode, "offset": offset, "limit": limit, "videos": [dict(row) for row in rows]}


@app.get("/api/feed/following")
async def get_following_feed(request: Request, offset: int = 0, limit: int = 30):
    # Удобный отдельный endpoint для будущего переключателя «Подписки».
    request.scope["query_string"] = f"mode=following&offset={offset}&limit={limit}".encode()
    return await get_feed(request, mode="following", offset=offset, limit=limit)


def extract_hashtags(text: str):
    tags = []
    for raw in re.findall(r"(?<![\w])#([A-Za-zА-Яа-яЁё0-9_]{2,40})", text or ""):
        tag = raw.lower()
        if tag not in tags:
            tags.append(tag)
        if len(tags) >= 10:
            break
    return tags


@app.get("/api/videos/{video_id}")
async def get_video(video_id: int, request: Request):
    user = await get_authenticated_user(request)
    pool = await get_db_pool()
    uid = int(user["id"])
    async with pool.acquire() as connection:
        row = await connection.fetchrow("""
            select v.id,v.user_id,v.video_url,v.caption,v.views_count,v.likes_count,v.comments_count,v.hashtags,v.created_at,
                   coalesce(u.custom_username,u.username) as username,u.first_name,u.last_name,u.avatar_url,
                   exists(select 1 from video_likes vl where vl.video_id=v.id and vl.user_id=$1) as liked,
                   exists(select 1 from video_saves vs where vs.video_id=v.id and vs.user_id=$1) as saved,
                   (select count(*) from video_saves vsc where vsc.video_id=v.id) as saves_count,
                   exists(select 1 from follows f where f.follower_id=$1 and f.following_id=v.user_id) as following
            from videos v join users u on u.id=v.user_id
            where v.id=$2 and not v.is_deleted
              and not exists (select 1 from user_blocks ub where ub.blocker_id=$1 and ub.blocked_id=v.user_id)
              and not exists (select 1 from user_blocks ub where ub.blocker_id=v.user_id and ub.blocked_id=$1)
        """, uid, video_id)
    if not row:
        raise HTTPException(status_code=404, detail="Видео недоступно")
    return {"ok": True, "video": dict(row)}

@app.post("/api/videos/{video_id}/preference")
async def video_preference(video_id: int, request: Request):
    user = await get_authenticated_user(request)
    body = await request.json()
    kind = str(body.get("kind", "")).strip()
    if kind not in {"not_interested"}:
        raise HTTPException(status_code=400, detail="Неизвестное действие")
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        exists = await connection.fetchval("select 1 from videos where id=$1 and not is_deleted", video_id)
        if not exists: raise HTTPException(status_code=404, detail="Видео не найдено")
        await connection.execute("insert into video_preferences(user_id,video_id,kind) values($1,$2,$3) on conflict do nothing", int(user["id"]), video_id, kind)
    return {"ok": True}

@app.post("/api/users/{user_id}/hide")
async def hide_author(user_id: int, request: Request):
    user = await get_authenticated_user(request)
    uid = int(user["id"])
    if uid == user_id: raise HTTPException(status_code=400, detail="Нельзя скрыть себя")
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        exists = await connection.fetchval("select 1 from users where id=$1", user_id)
        if not exists: raise HTTPException(status_code=404, detail="Пользователь не найден")
        await connection.execute("insert into hidden_authors(user_id,author_id) values($1,$2) on conflict do nothing", uid, user_id)
    return {"ok": True}

@app.post("/api/users/{user_id}/block")
async def block_user(user_id: int, request: Request):
    user = await get_authenticated_user(request)
    uid = int(user["id"])
    if uid == user_id: raise HTTPException(status_code=400, detail="Нельзя заблокировать себя")
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        exists = await connection.fetchval("select 1 from users where id=$1", user_id)
        if not exists: raise HTTPException(status_code=404, detail="Пользователь не найден")
        await connection.execute("insert into user_blocks(blocker_id,blocked_id) values($1,$2) on conflict do nothing", uid, user_id)
        await connection.execute("delete from follows where (follower_id=$1 and following_id=$2) or (follower_id=$2 and following_id=$1)", uid, user_id)
    return {"ok": True, "blocked": True}

@app.post("/api/users/{user_id}/report")
async def report_user(user_id: int, request: Request):
    user = await get_authenticated_user(request)
    uid = int(user["id"])
    if uid == user_id: raise HTTPException(status_code=400, detail="Нельзя пожаловаться на себя")
    body = await request.json()
    reason = str(body.get("reason", "")).strip()[:80]
    details = str(body.get("details", "")).strip()[:500]
    if not reason: raise HTTPException(status_code=400, detail="Укажите причину")
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        exists = await connection.fetchval("select 1 from users where id=$1", user_id)
        if not exists: raise HTTPException(status_code=404, detail="Пользователь не найден")
        await connection.execute("insert into user_reports(reporter_id,reported_user_id,reason,details) values($1,$2,$3,$4)", uid, user_id, reason, details or None)
    return {"ok": True}

@app.post("/api/videos/upload")
async def upload_video(
    request: Request,
    video: UploadFile = File(...),
    caption: str = Form(default=""),
):
    user = await get_authenticated_user(request)
    user_id = int(user["id"])

    public_url = await upload_to_storage(video, user_id)
    clean_caption = caption.strip()[:500] if caption else ""
    tags = extract_hashtags(clean_caption)

    try:
        pool = await get_db_pool()
        async with pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                insert into videos (user_id, video_url, caption, hashtags)
                values ($1, $2, $3, $4)
                returning id, video_url, caption, hashtags, created_at
                """,
                user_id, public_url, clean_caption or None, tags,
            )
    except Exception:
        # Не оставляем файл-сироту в Storage, если запись в БД не создалась.
        try:
            marker = f"/storage/v1/object/public/{STORAGE_BUCKET}/"
            if marker in public_url:
                storage_path = public_url.split(marker, 1)[1]
                delete_url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/{STORAGE_BUCKET}/{quote(storage_path, safe='/')}"
                headers = {"Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}", "apikey": SUPABASE_SERVICE_ROLE_KEY}
                async with httpx.AsyncClient(timeout=20) as client:
                    await client.delete(delete_url, headers=headers)
        except Exception as cleanup_error:
            print(f"Storage cleanup warning: {cleanup_error}")
        raise

    return {"ok": True, "video": dict(row)}


@app.delete("/api/videos/{video_id}")
async def delete_video(video_id: int, request: Request):
    user = await get_authenticated_user(request)
    user_id = int(user["id"])
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            "select id, user_id, video_url, is_deleted from videos where id=$1",
            video_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Видео не найдено")
        if int(row["user_id"]) != user_id:
            raise HTTPException(status_code=403, detail="Можно удалить только своё видео")
        if row["is_deleted"]:
            return {"ok": True, "deleted": True}
        await connection.execute(
            "update videos set is_deleted=true, deleted_at=now() where id=$1",
            video_id,
        )

    try:
        marker = f"/storage/v1/object/public/{STORAGE_BUCKET}/"
        if marker in row["video_url"]:
            storage_path = row["video_url"].split(marker, 1)[1]
            delete_url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/{STORAGE_BUCKET}/{quote(storage_path, safe='/')}"
            headers = {"Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}", "apikey": SUPABASE_SERVICE_ROLE_KEY}
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.delete(delete_url, headers=headers)
            if response.status_code not in (200, 204, 404):
                print(f"Storage delete warning: {response.status_code} {response.text[:300]}")
    except Exception as error:
        print(f"Storage delete warning: {error}")

    return {"ok": True, "deleted": True}


@app.post("/api/videos/{video_id}/report")
async def report_video(video_id: int, request: Request):
    user = await get_authenticated_user(request)
    body = await request.json()
    reason = str(body.get("reason", "other")).strip()[:50]
    details = str(body.get("details", "")).strip()[:500] or None
    allowed_reasons = {"spam", "violence", "sexual", "harassment", "copyright", "other"}
    if reason not in allowed_reasons:
        raise HTTPException(status_code=400, detail="Недопустимая причина жалобы")
    if reason == "other" and not details:
        raise HTTPException(status_code=400, detail="Для причины «Другое» нужно указать причину")
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        exists = await connection.fetchval("select 1 from videos where id=$1 and not is_deleted", video_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Видео не найдено")
        row = await connection.fetchrow(
            """insert into reports(reporter_id, video_id, reason, details)
               values($1,$2,$3,$4)
               on conflict (reporter_id, video_id) do update set reason=excluded.reason, details=excluded.details, status='open', resolved_at=null, resolved_by=null
               returning id""",
            int(user["id"]), video_id, reason, details,
        )
    return {"ok": True, "report_id": row["id"]}


@app.post("/api/videos/{video_id}/view")
async def add_view(video_id: int, request: Request):
    user = await get_authenticated_user(request)
    user_id = int(user["id"])
    pool = await get_db_pool()

    async with pool.acquire() as connection:
        exists = await connection.fetchval("select 1 from videos where id=$1 and not is_deleted", video_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Видео не найдено")
        # Один view от одного пользователя на видео учитываем один раз,
        # чтобы быстрое переключение вкладок не раздувало счётчик.
        inserted = await connection.fetchval(
            """insert into video_views (video_id, user_id) values ($1, $2)
               on conflict do nothing returning id""",
            video_id, user_id,
        )
        if inserted:
            row = await connection.fetchrow(
                "update videos set views_count=views_count+1 where id=$1 returning views_count",
                video_id,
            )
        else:
            row = await connection.fetchrow("select views_count from videos where id=$1", video_id)
        await connection.execute(
            """insert into video_watch_history(user_id,video_id,watched_seconds,completed,last_watched_at)
               values($1,$2,0,false,now())
               on conflict(user_id,video_id) do update set last_watched_at=now()""",
            user_id, video_id,
        )

    return {"ok": True, "views_count": int(row["views_count"])}


@app.post("/api/videos/{video_id}/watch")
async def update_watch_history(video_id: int, request: Request):
    user = await get_authenticated_user(request)
    body = await request.json()
    watched_seconds = max(0.0, min(float(body.get("watched_seconds", 0) or 0), 3600.0))
    completed = bool(body.get("completed", False))
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        exists = await connection.fetchval("select 1 from videos where id=$1 and not is_deleted", video_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Видео не найдено")
        await connection.execute(
            """insert into video_watch_history(user_id,video_id,watched_seconds,completed,last_watched_at)
               values($1,$2,$3,$4,now())
               on conflict(user_id,video_id) do update set
                 watched_seconds=greatest(video_watch_history.watched_seconds, excluded.watched_seconds),
                 completed=video_watch_history.completed or excluded.completed,
                 last_watched_at=now()""",
            int(user["id"]), video_id, watched_seconds, completed,
        )
    return {"ok": True}


@app.get("/api/history")
async def get_history(request: Request, offset: int = 0, limit: int = 60):
    user = await get_authenticated_user(request)
    offset=max(0,min(int(offset),5000)); limit=max(1,min(int(limit),60))
    pool=await get_db_pool()
    async with pool.acquire() as connection:
        rows=await connection.fetch(
            """select v.id,v.user_id,v.video_url,v.caption,v.hashtags,v.views_count,v.likes_count,v.comments_count,
                      v.created_at, wh.watched_seconds, wh.completed, wh.last_watched_at,
                      u.username,u.first_name,u.last_name,u.avatar_url
               from video_watch_history wh
               join videos v on v.id=wh.video_id
               join users u on u.id=v.user_id
               where wh.user_id=$1 and not v.is_deleted
               order by wh.last_watched_at desc limit $2 offset $3""",
            int(user["id"]),limit,offset
        )
    return {"ok":True,"videos":[dict(x) for x in rows],"offset":offset,"limit":limit}


@app.post("/api/videos/{video_id}/like")
async def toggle_like(video_id: int, request: Request):
    user = await get_authenticated_user(request)
    user_id = int(user["id"])
    pool = await get_db_pool()

    async with pool.acquire() as connection:
        existing = await connection.fetchval(
            """
            select 1 from video_likes
            where video_id = $1 and user_id = $2
            """,
            video_id,
            user_id,
        )

        if existing:
            await connection.execute(
                "delete from video_likes where video_id = $1 and user_id = $2",
                video_id,
                user_id,
            )
            liked = False
        else:
            await connection.execute(
                """
                insert into video_likes (video_id, user_id)
                values ($1, $2)
                on conflict do nothing
                """,
                video_id,
                user_id,
            )
            liked = True

        row = await connection.fetchrow(
            """
            update videos
            set likes_count = (
                select count(*) from video_likes where video_id = $1
            )
            where id = $1
            returning likes_count, user_id
            """,
            video_id,
        )
        if row and liked and int(row["user_id"]) != user_id:
            await connection.execute(
                "insert into notifications(user_id,actor_id,type,video_id) values($1,$2,'like',$3)",
                int(row["user_id"]), user_id, video_id
            )

    if not row:
        raise HTTPException(status_code=404, detail="Видео не найдено")

    return {"ok": True, "liked": liked, "likes_count": row["likes_count"]}


@app.post("/api/videos/{video_id}/save")
async def toggle_save(video_id: int, request: Request):
    user = await get_authenticated_user(request)
    user_id = int(user["id"])
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        owner_id = await connection.fetchval("select user_id from videos where id=$1 and not is_deleted", video_id)
        if owner_id is None:
            raise HTTPException(status_code=404, detail="Видео не найдено")
        saved = await connection.fetchval("select 1 from video_saves where video_id=$1 and user_id=$2", video_id, user_id)
        if saved:
            await connection.execute("delete from video_saves where video_id=$1 and user_id=$2", video_id, user_id)
            is_saved = False
        else:
            await connection.execute("insert into video_saves(video_id,user_id) values($1,$2) on conflict do nothing", video_id, user_id)
            is_saved = True
        saves_count = await connection.fetchval("select count(*) from video_saves where video_id=$1", video_id)
        if is_saved and int(owner_id) != user_id:
            await connection.execute(
                "insert into notifications(user_id,actor_id,type,video_id) values($1,$2,'save',$3)",
                int(owner_id), user_id, video_id
            )
    return {"ok": True, "saved": is_saved, "saves_count": int(saves_count or 0)}

@app.get("/api/saved")
async def get_saved(request: Request, offset: int = 0, limit: int = 60):
    user = await get_authenticated_user(request)
    offset = max(0, min(int(offset), 5000)); limit = max(1, min(int(limit), 60))
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        rows = await connection.fetch("""
            select v.id,v.user_id,v.video_url,v.caption,v.hashtags,v.views_count,v.likes_count,v.comments_count,v.created_at,
                   coalesce(u.custom_username,u.username) as username,u.first_name,u.last_name,u.avatar_url, true as saved
            from video_saves s join videos v on v.id=s.video_id join users u on u.id=v.user_id
            where s.user_id=$1 and not v.is_deleted
            order by s.created_at desc limit $2 offset $3
        """, user["id"], limit, offset)
    return {"ok": True, "videos": [dict(x) for x in rows], "offset": offset, "limit": limit}

@app.get("/api/users/{user_id}/followers")
async def get_followers(user_id: int, request: Request, limit: int = 100):
    viewer = await get_authenticated_user(request); limit=max(1,min(int(limit),100)); pool=await get_db_pool()
    async with pool.acquire() as connection:
        rows=await connection.fetch("""select u.id,coalesce(u.custom_username,u.username) as username,u.first_name,u.last_name,u.avatar_url,
            exists(select 1 from follows fx where fx.follower_id=$1 and fx.following_id=u.id) as following
            from follows f join users u on u.id=f.follower_id where f.following_id=$2 order by f.created_at desc limit $3""", int(viewer["id"]), user_id, limit)
    return {"ok":True,"users":[dict(x) for x in rows]}

@app.get("/api/users/{user_id}/following")
async def get_following(user_id: int, request: Request, limit: int = 100):
    viewer = await get_authenticated_user(request); limit=max(1,min(int(limit),100)); pool=await get_db_pool()
    async with pool.acquire() as connection:
        rows=await connection.fetch("""select u.id,coalesce(u.custom_username,u.username) as username,u.first_name,u.last_name,u.avatar_url, true as following
            from follows f join users u on u.id=f.following_id where f.follower_id=$1 order by f.created_at desc limit $2""", user_id, limit)
    return {"ok":True,"users":[dict(x) for x in rows]}

@app.delete("/api/comments/{comment_id}")
async def delete_comment(comment_id: int, request: Request):
    user=await get_authenticated_user(request); pool=await get_db_pool()
    async with pool.acquire() as connection:
        row=await connection.fetchrow("delete from comments where id=$1 and user_id=$2 returning video_id", comment_id, int(user["id"]))
        if not row: raise HTTPException(status_code=404, detail="Комментарий не найден или уже удалён")
        await connection.execute("update videos set comments_count=greatest(comments_count-1,0) where id=$1", row["video_id"])
    return {"ok":True,"deleted":True}

@app.get("/api/notifications/unread-count")
async def unread_notifications(request: Request):
    user=await get_authenticated_user(request); pool=await get_db_pool()
    async with pool.acquire() as connection:
        count=await connection.fetchval("select count(*) from notifications where user_id=$1 and not is_read", int(user["id"]))
    return {"ok":True,"count":int(count or 0)}

@app.get("/api/profile/{user_id}")
async def get_profile(user_id: int, request: Request):
    viewer = await get_authenticated_user(request)
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        user_row = await connection.fetchrow("""select u.id,coalesce(u.custom_username,u.username) as username,u.first_name,u.last_name,u.avatar_url,u.bio,
          (select count(*) from videos v where v.user_id=u.id and not v.is_deleted) as videos_count,
          (select coalesce(sum(v.likes_count),0) from videos v where v.user_id=u.id and not v.is_deleted) as likes_count,
          (select count(*) from follows f where f.following_id=u.id) as followers_count,
          (select count(*) from follows f where f.follower_id=u.id) as following_count,
          exists(select 1 from follows f where f.follower_id=$1 and f.following_id=u.id) as following
          from users u where u.id=$2""", int(viewer["id"]), user_id)
        videos = await connection.fetch("select v.id,v.video_url,v.caption,v.hashtags,v.views_count,v.likes_count,v.comments_count,(select count(*) from video_saves s where s.video_id=v.id) as saves_count,v.created_at from videos v where v.user_id=$1 and not v.is_deleted order by v.created_at desc limit 60", user_id)
    if not user_row: raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"ok":True,"user":dict(user_row),"videos":[dict(v) for v in videos]}

@app.get("/api/search")
async def search(q: str = "", request: Request = None):
    if request is None:
        raise HTTPException(status_code=400, detail="Запрос не указан")
    await get_authenticated_user(request)
    query = q.strip()[:80]
    if not query:
        return {"ok": True, "users": [], "videos": [], "hashtags": []}
    pool = await get_db_pool()
    raw = query.lstrip("#").lower()
    pattern = f"%{query}%"
    async with pool.acquire() as connection:
        users = await connection.fetch(
            """select id,coalesce(custom_username,username) as username,first_name,last_name,avatar_url,
                (select count(*) from follows f where f.following_id=u.id) as followers_count
               from users u
               where coalesce(custom_username,username,'') ilike $1
                  or coalesce(first_name,'') ilike $1
                  or coalesce(last_name,'') ilike $1
               order by followers_count desc limit 20""",
            pattern,
        )
        videos = await connection.fetch(
            """select v.id,v.video_url,v.caption,v.hashtags,v.views_count,v.likes_count,
                u.id as user_id,coalesce(u.custom_username,u.username) as username,u.first_name,u.avatar_url
               from videos v join users u on u.id=v.user_id
               where not v.is_deleted
                 and (coalesce(v.caption,'') ilike $1 or coalesce(u.custom_username,u.username,'') ilike $1 or $2 = any(v.hashtags))
               order by v.created_at desc limit 20""",
            pattern, raw,
        )
        hashtag_rows = await connection.fetch(
            """select tag, count(*) as videos_count
               from (select unnest(hashtags) as tag from videos where not is_deleted) h
               where tag ilike $1
               group by tag order by videos_count desc, tag asc limit 20""",
            f"%{raw}%",
        )
    return {
        "ok": True,
        "users": [dict(x) for x in users],
        "videos": [dict(x) for x in videos],
        "hashtags": [dict(x) for x in hashtag_rows],
    }


@app.get("/api/hashtags/trending")
async def trending_hashtags(request: Request):
    await get_authenticated_user(request)
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        rows = await connection.fetch(
            """select tag, count(*) as videos_count
               from (select unnest(hashtags) as tag from videos where not is_deleted) h
               group by tag order by videos_count desc, tag asc limit 12"""
        )
    return {"ok": True, "hashtags": [dict(row) for row in rows]}


@app.patch("/api/me")
async def update_me(request: Request):
    user = await get_authenticated_user(request)
    body = await request.json()
    first_name = str(body.get("first_name", "")).strip()[:64]
    username = str(body.get("username", "")).strip().lstrip("@").lower()[:32]
    bio = str(body.get("bio", "")).strip()[:160]
    if username and not re.fullmatch(r"[a-zA-Z0-9_]{3,32}", username):
        raise HTTPException(status_code=400, detail="Username: только латинские буквы, цифры и _, от 3 до 32 символов")
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        if username:
            taken = await connection.fetchval(
                "select 1 from users where lower(coalesce(custom_username,username))=$1 and id<>$2",
                username, int(user["id"])
            )
            if taken:
                raise HTTPException(status_code=409, detail="Этот username уже занят")
        row = await connection.fetchrow(
            """update users set
                first_name=coalesce(nullif($1,''), first_name),
                custom_username=case when $2<>'' then $2 else custom_username end,
                bio=$3
               where id=$4
               returning id,coalesce(custom_username,username) as username,first_name,last_name,avatar_url,bio""",
            first_name, username, bio or None, int(user["id"])
        )
    return {"ok": True, "user": dict(row)}


@app.get("/api/videos/{video_id}/comments")
async def get_comments(video_id:int, request:Request):
    await get_authenticated_user(request); p=await get_db_pool()
    async with p.acquire() as c:
        rows=await c.fetch("""select c.id,c.text,c.created_at,u.id as user_id,u.username,u.first_name,u.avatar_url from comments c join users u on u.id=c.user_id where c.video_id=$1 and not exists (select 1 from videos v where v.id=c.video_id and v.is_deleted) order by c.created_at desc limit 100""",video_id)
    return {"ok":True,"comments":[dict(x) for x in rows]}

@app.post("/api/videos/{video_id}/comments")
async def add_comment(video_id:int, request:Request):
    user=await get_authenticated_user(request); text=str((await request.json()).get("text","")).strip()[:500]
    if not text: raise HTTPException(status_code=400,detail="Комментарий не может быть пустым")
    p=await get_db_pool()
    async with p.acquire() as c:
        owner=await c.fetchval("select user_id from videos where id=$1 and not is_deleted",video_id)
        if owner is None: raise HTTPException(status_code=404,detail="Видео не найдено")
        blocked=await c.fetchval("select 1 from user_blocks where (blocker_id=$1 and blocked_id=$2) or (blocker_id=$2 and blocked_id=$1)",int(user["id"]),int(owner))
        if blocked: raise HTTPException(status_code=403,detail="Взаимодействие с этим пользователем недоступно")
        row=await c.fetchrow("insert into comments(video_id,user_id,text) values($1,$2,$3) returning id,text,created_at",video_id,int(user["id"]),text)
        await c.execute("update videos set comments_count=comments_count+1 where id=$1",video_id)
        if int(owner)!=int(user["id"]): await c.execute("insert into notifications(user_id,actor_id,type,video_id) values($1,$2,'comment',$3)",int(owner),int(user["id"]),video_id)
    return {"ok":True,"comment":dict(row)}

@app.post("/api/users/{user_id}/follow")
async def toggle_follow(user_id:int, request:Request):
    user=await get_authenticated_user(request); follower=int(user["id"])
    if follower==user_id: raise HTTPException(status_code=400,detail="Нельзя подписаться на себя")
    p=await get_db_pool()
    async with p.acquire() as c:
        exists=await c.fetchval("select 1 from follows where follower_id=$1 and following_id=$2",follower,user_id)
        if exists:
            await c.execute("delete from follows where follower_id=$1 and following_id=$2",follower,user_id); following=False
        else:
            if await c.fetchval("select 1 from users where id=$1",user_id) is None: raise HTTPException(status_code=404,detail="Пользователь не найден")
            await c.execute("insert into follows(follower_id,following_id) values($1,$2) on conflict do nothing",follower,user_id); following=True
            await c.execute("insert into notifications(user_id,actor_id,type) values($1,$2,'follow')",user_id,follower)
        count=await c.fetchval("select count(*) from follows where following_id=$1",user_id)
    return {"ok":True,"following":following,"followers_count":count}

@app.get("/api/notifications")
async def get_notifications(request:Request):
    user=await get_authenticated_user(request); p=await get_db_pool()
    async with p.acquire() as c:
        rows=await c.fetch("""select n.id,n.type,n.video_id,n.created_at,n.is_read,u.username,u.first_name,u.avatar_url from notifications n left join users u on u.id=n.actor_id where n.user_id=$1 order by n.created_at desc limit 50""",int(user["id"]))
        await c.execute("update notifications set is_read=true where user_id=$1",int(user["id"]))
    return {"ok":True,"notifications":[dict(x) for x in rows]}


def require_admin(user_data):
    if not ADMIN_TELEGRAM_IDS:
        raise HTTPException(status_code=503, detail="Администратор ещё не настроен")
    if int(user_data["id"]) not in ADMIN_TELEGRAM_IDS:
        raise HTTPException(status_code=403, detail="Доступ только для администратора")


@app.get("/api/admin/reports")
async def admin_reports(request: Request):
    user = await get_authenticated_user(request)
    require_admin(user)
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        rows = await connection.fetch(
            """select r.id,r.video_id,r.reason,r.details,r.status,r.created_at,
                      r.reporter_id,u.username as reporter_username,
                      v.video_url,v.caption,v.user_id as owner_id
               from reports r
               join users u on u.id=r.reporter_id
               join videos v on v.id=r.video_id
               order by r.created_at desc limit 100"""
        )
    return {"ok": True, "reports": [dict(row) for row in rows]}


@app.post("/api/admin/videos/{video_id}/hide")
async def admin_hide_video(video_id: int, request: Request):
    user = await get_authenticated_user(request)
    require_admin(user)
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        row = await connection.fetchrow("select id from videos where id=$1", video_id)
        if not row:
            raise HTTPException(status_code=404, detail="Видео не найдено")
        await connection.execute("update videos set is_deleted=true, deleted_at=coalesce(deleted_at, now()) where id=$1", video_id)
        await connection.execute("update reports set status='resolved', resolved_at=now(), resolved_by=$1 where video_id=$2 and status='open'", int(user["id"]), video_id)
    return {"ok": True, "hidden": True}


@app.post("/api/admin/reports/{report_id}/resolve")
async def admin_resolve_report(report_id: int, request: Request):
    user = await get_authenticated_user(request)
    require_admin(user)
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        row = await connection.fetchrow("update reports set status='resolved', resolved_at=now(), resolved_by=$1 where id=$2 returning id", int(user["id"]), report_id)
        if not row:
            raise HTTPException(status_code=404, detail="Жалоба не найдена")
    return {"ok": True, "resolved": True}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled server error on {request.method} {request.url.path}: {exc}")
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"ok": False, "detail": "Временная ошибка сервера. Попробуйте ещё раз."})


@app.get("/health/db")
async def db_health_check():
    try:
        pool = await get_db_pool()
        async with pool.acquire() as connection:
            value = await connection.fetchval("select 1")
        return {"status":"ok","database":value == 1}
    except Exception as error:
        print(f"DB health error: {error}")
        return JSONResponse(status_code=503, content={"status":"error","database":False})


DIST_DIR = Path("dist")
if (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")


@app.get("/")
async def home():
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(
            index_file,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
            },
        )
    return JSONResponse({"status": "ok", "service": "Telegram Shorts"})


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Telegram Shorts"}


async def run_bot():
    print("Telegram Shorts bot запускается...")
    await init_db()
    await init_storage()
    print("Telegram Shorts bot запущен!")
    await dp.start_polling(bot)


async def run_web_server():
    port = int(os.getenv("PORT", "8080"))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(run_bot(), run_web_server())


if __name__ == "__main__":
    asyncio.run(main())
