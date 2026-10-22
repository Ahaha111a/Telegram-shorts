-- Safe, additive migration: preserves all existing comments and relationships.
begin;
alter table comments add column if not exists parent_id bigint references comments(id) on delete cascade;
alter table comments add column if not exists is_pinned boolean not null default false;
alter table comments add column if not exists updated_at timestamptz;
create table if not exists comment_likes (
  comment_id bigint not null references comments(id) on delete cascade,
  user_id bigint not null references users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (comment_id, user_id)
);
create index if not exists idx_comments_parent_id on comments(parent_id);
commit;
