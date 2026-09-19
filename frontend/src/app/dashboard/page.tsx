// Server component - fetches auth state, passes to client

import { createClient } from '@/lib/supabase/server'
import DashboardClient from './DashboardClient'

export default async function DashboardPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const isLoggedIn = !!user
  const userEmail = user?.email ?? null

  return <DashboardClient isLoggedIn={isLoggedIn} userEmail={userEmail} />
}