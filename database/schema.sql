-- Telegram Shorts database schema
create table if not exists users (
    id bigint primary key,
    username text,
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

create index if not exists idx_videos_created_at on videos (created_at desc);
create index if not exists idx_videos_user_id on videos (user_id);
create index if not exists idx_video_views_video_id on video_views (video_id);
create index if not exists idx_comments_video_id on comments (video_id);
create index if not exists idx_follows_following_id on follows (following_id);
