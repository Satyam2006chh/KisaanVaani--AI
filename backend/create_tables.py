import psycopg2, sys
from urllib.parse import quote_plus

pwd = quote_plus("Satyamchh@2006ABRA06062006")
ref = "gkulnrcroeblgjywpubh"

hosts = [
    # Session pooler (port 5432)
    f"host=aws-0-ap-south-1.pooler.supabase.com port=5432 dbname=postgres user=postgres.{ref} password=Satyamchh@2006ABRA06062006 sslmode=require connect_timeout=10",
    # Transaction pooler (port 6543)
    f"host=aws-0-ap-south-1.pooler.supabase.com port=6543 dbname=postgres user=postgres.{ref} password=Satyamchh@2006ABRA06062006 sslmode=require connect_timeout=10",
    # Direct connection
    f"host=db.{ref}.supabase.co port=5432 dbname=postgres user=postgres password=Satyamchh@2006ABRA06062006 sslmode=require connect_timeout=10",
]

SQL = """
create table if not exists public.users (
    id uuid default gen_random_uuid() primary key,
    phone text unique not null,
    name text default '',
    language text default 'hi-IN',
    district text default '',
    state text default '',
    created_at timestamptz default now(),
    last_login timestamptz default now()
);
create table if not exists public.messages (
    id uuid default gen_random_uuid() primary key,
    farmer_id text not null,
    session_id text default '',
    role text default 'user',
    content text default '',
    timestamp timestamptz default now()
);
alter table public.users enable row level security;
alter table public.messages enable row level security;
do $$ begin
  if not exists (select 1 from pg_policies where tablename='users' and policyname='allow_all_users') then
    create policy allow_all_users on public.users for all using (true) with check (true);
  end if;
end $$;
do $$ begin
  if not exists (select 1 from pg_policies where tablename='messages' and policyname='allow_all_messages') then
    create policy allow_all_messages on public.messages for all using (true) with check (true);
  end if;
end $$;
"""

conn = None
for dsn in hosts:
    try:
        conn = psycopg2.connect(dsn)
        sys.stdout.buffer.write(b"Connected via: " + dsn[:80].encode() + b"\n")
        break
    except Exception as e:
        sys.stdout.buffer.write(b"FAIL: " + str(e)[:120].encode() + b"\n")

if conn is None:
    sys.stdout.buffer.write(b"\nAll connections failed.\n")
else:
    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(SQL)
        sys.stdout.buffer.write(b"Tables created successfully!\n")
        cur.execute("select table_name from information_schema.tables where table_schema='public' and table_name in ('users','messages')")
        for row in cur.fetchall():
            sys.stdout.buffer.write(b"  Table OK: " + row[0].encode() + b"\n")
        cur.close()
        conn.close()
    except Exception as e:
        sys.stdout.buffer.write(b"SQL ERROR: " + str(e).encode() + b"\n")
