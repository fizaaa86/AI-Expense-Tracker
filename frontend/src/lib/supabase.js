import { createClient } from '@supabase/supabase-js'

// One shared Supabase connection for the whole app (it also remembers who is logged in)
export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
)
