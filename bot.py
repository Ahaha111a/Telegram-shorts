import os, asyncio, json, hmac, hashlib, time
from pathlib import Path
from urllib.parse import parse_qsl
import asyncpg
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

BOT_TOKEN=os.getenv("BOT_TOKEN")
DATABASE_URL=os.getenv("DATABASE_URL")
WEB_APP_URL=os.getenv("WEB_APP_URL","https://telegram-shorts-production.up.railway.app")
if not BOT_TOKEN: raise RuntimeError("BOT_TOKEN не найден")
if not DATABASE_URL: raise RuntimeError("DATABASE_URL не найден")
bot=Bot(BOT_TOKEN); dp=Dispatcher(); app=FastAPI(); db_pool=None

async def pool():
    global db_pool
    if db_pool is None: db_pool=await asyncpg.create_pool(DATABASE_URL,min_size=1,max_size=5)
    return db_pool

async def init_db():
    p=await pool()
    async with p.acquire() as c:
        await c.execute('''
        create table if not exists users(id bigint primary key,username text,first_name text,last_name text,avatar_url text,bio text,created_at timestamptz not null default now());
        create table if not exists videos(id bigint generated always as identity primary key,user_id bigint not null references users(id) on delete cascade,video_url text not null,thumbnail_url text,caption text,views_count bigint not null default 0,likes_count bigint not null default 0,comments_count bigint not null default 0,created_at timestamptz not null default now());
        create table if not exists video_views(id bigint generated always as identity primary key,video_id bigint not null references videos(id) on delete cascade,user_id bigint references users(id) on delete set null,viewed_at timestamptz not null default now());
        create table if not exists video_likes(video_id bigint not null references videos(id) on delete cascade,user_id bigint not null references users(id) on delete cascade,created_at timestamptz not null default now(),primary key(video_id,user_id));
        create table if not exists comments(id bigint generated always as identity primary key,video_id bigint not null references videos(id) on delete cascade,user_id bigint not null references users(id) on delete cascade,text text not null,created_at timestamptz not null default now());
        create table if not exists follows(follower_id bigint not null references users(id) on delete cascade,following_id bigint not null references users(id) on delete cascade,created_at timestamptz not null default now(),primary key(follower_id,following_id),check(follower_id<>following_id));
        create index if not exists idx_videos_created_at on videos(created_at desc);
        create index if not exists idx_videos_user_id on videos(user_id);
        create index if not exists idx_video_views_video_id on video_views(video_id);
        create index if not exists idx_comments_video_id on comments(video_id);
        create index if not exists idx_follows_following_id on follows(following_id);
        ''')
    print('Supabase: таблицы успешно проверены/созданы.')

async def save_user(u):
    p=await pool()
    async with p.acquire() as c:
        await c.execute('''insert into users(id,username,first_name,last_name,avatar_url) values($1,$2,$3,$4,$5)
        on conflict(id) do update set username=excluded.username,first_name=excluded.first_name,last_name=excluded.last_name,avatar_url=excluded.avatar_url''',int(u['id']),u.get('username'),u.get('first_name'),u.get('last_name'),u.get('photo_url'))

def validate(init_data):
    if not init_data: raise ValueError('Telegram initData отсутствует')
    d=dict(parse_qsl(init_data,keep_blank_values=True)); received=d.pop('hash',None)
    if not received: raise ValueError('В initData отсутствует hash')
    check='\n'.join(f'{k}={d[k]}' for k in sorted(d))
    secret=hmac.new(b'WebAppData',BOT_TOKEN.encode(),hashlib.sha256).digest()
    expected=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,received): raise ValueError('Неверная подпись Telegram initData')
    auth_date=int(d.get('auth_date','0'))
    if auth_date and time.time()-auth_date>86400: raise ValueError('Telegram initData устарел')
    u=json.loads(d.get('user','{}'))
    if 'id' not in u: raise ValueError('Данные пользователя отсутствуют')
    return u

@dp.message(CommandStart())
async def start(message:Message):
    await save_user({'id':message.from_user.id,'username':message.from_user.username,'first_name':message.from_user.first_name,'last_name':message.from_user.last_name,'photo_url':message.from_user.photo_url})
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🎬 Открыть Telegram Shorts',web_app=WebAppInfo(url=WEB_APP_URL))]])
    await message.answer('👋 Добро пожаловать в Telegram Shorts!\n\n🎬 Смотри короткие видео и открывай новые возможности.',reply_markup=kb)

@app.post('/api/auth')
async def auth(request:Request):
    try:
        u=validate((await request.json()).get('initData','')); await save_user(u)
        return {'ok':True,'user':{'id':int(u['id']),'username':u.get('username'),'first_name':u.get('first_name'),'last_name':u.get('last_name'),'photo_url':u.get('photo_url')}}
    except ValueError as e: return JSONResponse(status_code=401,content={'ok':False,'error':str(e)})
    except Exception as e:
        print('Auth error:',e); return JSONResponse(status_code=500,content={'ok':False,'error':'Ошибка сервера'})

DIST=Path('dist')
if (DIST/'assets').exists(): app.mount('/assets',StaticFiles(directory=DIST/'assets'),name='assets')
@app.get('/')
async def home():
    f=DIST/'index.html'; return FileResponse(f) if f.exists() else JSONResponse({'status':'ok','service':'Telegram Shorts'})
@app.get('/health')
async def health(): return {'status':'ok','service':'Telegram Shorts'}
async def run_bot(): await init_db(); print('Telegram Shorts bot запущен!'); await dp.start_polling(bot)
async def run_web():
    s=uvicorn.Server(uvicorn.Config(app,host='0.0.0.0',port=int(os.getenv('PORT','8080')),log_level='info')); await s.serve()
async def main(): await asyncio.gather(run_bot(),run_web())
if __name__=='__main__': asyncio.run(main())
