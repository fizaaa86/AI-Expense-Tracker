from sqlalchemy import text

from db import engine

with engine.connect() as conn:
    print("✅ Connected to:", conn.execute(text("select version()")).scalar()[:30])

    print("\nTables in 'public' (name, RLS on?):")
    rows = conn.execute(text(
        "select tablename, rowsecurity from pg_tables "
        "where schemaname = 'public' order by tablename"
    ))
    for name, rls in rows:
        print(f"  {name:15} RLS = {rls}")

    users = conn.execute(text("select count(*) from auth.users")).scalar()
    print(f"\nUsers in Supabase Auth: {users}")
