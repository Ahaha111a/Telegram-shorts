-- Telegram Shorts schema. Existing installations are migrated by bot.py.
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
alter table users add column if not exists custom_username text;
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
  hashtags text[] not null default '{}',
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
  primary key (video_id,user_id)
);
create table if not exists video_saves (
  video_id bigint not null references videos(id) on delete cascade,
  user_id bigint not null references users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (video_id,user_id)
);
create table if not exists video_watch_history (
  user_id bigint not null references users(id) on delete cascade,
  video_id bigint not null references videos(id) on delete cascade,
  watched_seconds numeric(10,2) not null default 0,
  completed boolean not null default false,
  last_watched_at timestamptz not null default now(),
  primary key (user_id,video_id)
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
  primary key (follower_id,following_id),
  check (follower_id<>following_id)
);
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
  unique (reporter_id,video_id)
);
create table if not exists notifications (
  id bigint generated always as identity primary key,
  user_id bigint not null references users(id) on delete cascade,
  actor_id bigint references users(id) on delete cascade,
  type text not null,
  video_id bigint references videos(id) on delete cascade,
  created_at timestamptz not null default now(),
  is_read boolean not null default false
);
create index if not exists idx_videos_created_at on videos(created_at desc);
create index if not exists idx_videos_user_id on videos(user_id);
create index if not exists idx_video_views_video_id on video_views(video_id);
create unique index if not exists uq_video_views_user_video on video_views(video_id,user_id) where user_id is not null;
create index if not exists idx_comments_video_id on comments(video_id);
create index if not exists idx_video_saves_user_id on video_saves(user_id,created_at desc);
create index if not exists idx_video_saves_video_id on video_saves(video_id);
create index if not exists idx_watch_history_user_time on video_watch_history(user_id,last_watched_at desc);
create index if not exists idx_watch_history_video on video_watch_history(video_id);
create index if not exists idx_videos_hashtags on videos using gin(hashtags);
create index if not exists idx_follows_following_id on follows(following_id);
create index if not exists idx_notifications_user_id on notifications(user_id,created_at desc);
create index if not exists idx_reports_status_created_at on reports(status,created_at desc);
