import { redirect } from 'next/navigation'

export default function HomePage() {
  // Redirection vers le dashboard
  redirect('/dashboard')
}