-- =========================================================
-- TABLE 1: expenses  (one row per receipt)
-- =========================================================
create table public.expenses (
    id            bigint generated always as identity primary key,  -- DB makes unique ids
    user_id       uuid not null default auth.uid()                   -- owner = logged-in user
                  references auth.users (id) on delete cascade,      -- FK to Supabase's users table
    merchant      text not null,
    expense_date  date not null,
    total         numeric(12,2) not null check (total > 0),          -- exact money, must be > 0
    tax           numeric(12,2) not null default 0 check (tax >= 0),
    category      text not null default 'Other',
    image_url     text,                                              -- can be empty (manual entries)
    created_at    timestamptz not null default now()
);

-- =========================================================
-- TABLE 2: expense_items  (line items of a receipt)
-- =========================================================
create table public.expense_items (
    id          bigint generated always as identity primary key,
    expense_id  bigint not null
                references public.expenses (id) on delete cascade,   -- delete receipt -> its items go too
    name        text not null,
    price       numeric(12,2) not null
);

-- =========================================================
-- TABLE 3: budgets  (monthly limit per category)
-- =========================================================
create table public.budgets (
    id             bigint generated always as identity primary key,
    user_id        uuid not null default auth.uid()
                   references auth.users (id) on delete cascade,
    category       text not null,
    monthly_limit  numeric(12,2) not null check (monthly_limit > 0),
    unique (user_id, category)                                       -- one budget per category per user
);

-- Indexes = a book's index: make "find my expenses" fast
create index on public.expenses (user_id, expense_date);
create index on public.expense_items (expense_id);

-- =========================================================
-- ROW LEVEL SECURITY
-- =========================================================
alter table public.expenses      enable row level security;
alter table public.expense_items enable row level security;
alter table public.budgets       enable row level security;

-- "You can only see / add / change / delete rows that are yours"
create policy "own expenses" on public.expenses
    for all to authenticated
    using      ((select auth.uid()) = user_id)     -- which rows you can READ / change / delete
    with check ((select auth.uid()) = user_id);    -- which rows you can WRITE

create policy "own budgets" on public.budgets
    for all to authenticated
    using      ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

-- Items don't have user_id themselves, so we check their parent receipt's owner
create policy "items of own expenses" on public.expense_items
    for all to authenticated
    using (exists (
        select 1 from public.expenses e
        where e.id = expense_id and e.user_id = (select auth.uid())
    ))
    with check (exists (
        select 1 from public.expenses e
        where e.id = expense_id and e.user_id = (select auth.uid())
    ));
