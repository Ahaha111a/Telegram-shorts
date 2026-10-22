-- Additive and idempotent. Supports retrying failed Supabase Storage deletions.
begin;
create table if not exists storage_cleanup_jobs (
  id bigint generated always as identity primary key,
  object_path text not null unique,
  attempts integer not null default 0,
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_storage_cleanup_jobs_created_at on storage_cleanup_jobs(created_at);
commit;
