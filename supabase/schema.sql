-- JobScout private data (Supabase). Run once in Supabase: SQL Editor > New query > paste > Run.
-- Safe to run again: it only creates what is missing.
-- Row-level security: every row belongs to the logged-in user (auth.uid()), and nobody
-- else can read or change it, even though the page and its public key are public.

-- Jobs hidden on the board (job id = "<source>/<board>/<id>", as in matches.json).
create table if not exists public.hidden_jobs (
  user_id    uuid not null default auth.uid() references auth.users on delete cascade,
  job_id     text not null,
  created_at timestamptz not null default now(),
  primary key (user_id, job_id)
);

-- Applications: one row per job Andrea actually applied to (docs/TRACKER-SPEC.md).
create table if not exists public.applications (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null default auth.uid() references auth.users on delete cascade,
  job_id        text,                 -- set when the job came from the board
  link          text,
  company       text not null,
  title         text not null,
  location      text,
  source        text not null default 'scan',     -- scan / linkedin / referral / other
  stage         text not null default 'applied',  -- applied / interviewing / offer / closed
  closed_reason text,                 -- rejected / withdrawn / no answer / accepted
  applied_on    date not null default current_date,
  cv_version    text,
  contact_name  text,
  contact_email text,
  next_step     text,
  next_due      date,
  interviews    jsonb not null default '[]',      -- [{date, type, with, notes, outcome}]
  offer         text,
  notes         text,
  timeline      jsonb not null default '[]',      -- [{date, text}]
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

alter table public.hidden_jobs  enable row level security;
alter table public.applications enable row level security;

drop policy if exists "own rows" on public.hidden_jobs;
create policy "own rows" on public.hidden_jobs
  for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists "own rows" on public.applications;
create policy "own rows" on public.applications
  for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Live sync: tell the page when a row changes on another device.
do $$ begin
  alter publication supabase_realtime add table public.hidden_jobs, public.applications;
exception when duplicate_object then null;
end $$;
