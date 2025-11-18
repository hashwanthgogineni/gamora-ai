// src/components/Auth.tsx
import { useState } from 'react'
import { supabase } from '@/lib/supabase'
import { useNavigate, useLocation } from 'react-router-dom'
import { FcGoogle } from 'react-icons/fc'

export default function Auth() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as any)?.from || '/chat-main' // default back to chat-main after login

  // Sign up with email/password
  const handleSignUp = async () => {
    setLoading(true)
    const { error } = await supabase.auth.signUp({ email, password })
    setLoading(false)
    setError(error?.message ?? null)
    if (!error) alert('Check your email for a confirmation link!')
  }

  // Sign in with email/password
  const handleSignIn = async () => {
    setLoading(true)
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    setLoading(false)
    setError(error?.message ?? null)
    if (!error) {
      // redirect to chat or the page they came from
      navigate(from, { replace: true })
    }
  }

  // Google sign-in
  const handleGoogleSignIn = async () => {
    setLoading(true)
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin + '/chat-main' }
    })
    setLoading(false)
    setError(error?.message ?? null)
  }

  return (
    <div className="p-6 max-w-md mx-auto space-y-4 bg-card border border-card-border rounded-lg shadow">
      <h1 className="text-2xl font-bold text-center text-primary">Sign In / Sign Up</h1>

      <input
        className="w-full px-3 py-2 border border-card-border bg-background rounded-md focus:outline-none focus:ring-0 focus:border-card-border"
        placeholder="Email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <input
        className="w-full px-3 py-2 border border-card-border bg-background rounded-md focus:outline-none focus:ring-0 focus:border-card-border"
        placeholder="Password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      <div className="flex flex-col gap-2">
        <button
          onClick={handleSignIn}
          disabled={loading}
          className="w-full bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-md transition-colors"
        >
          {loading ? 'Loading...' : 'Sign In'}
        </button>

        <button
          onClick={handleSignUp}
          disabled={loading}
          className="w-full bg-gray-800 hover:bg-gray-900 text-white px-3 py-2 rounded-md transition-colors"
        >
          {loading ? 'Loading...' : 'Sign Up'}
        </button>

        <div className="relative my-2 flex items-center">
          <span className="flex-grow border-t border-card-border"></span>
          <span className="mx-2 text-xs text-muted-foreground">or</span>
          <span className="flex-grow border-t border-card-border"></span>
        </div>

        <button
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 border border-card-border bg-background rounded-md px-3 py-2 hover:bg-muted transition-colors"
        >
          <FcGoogle className="h-5 w-5" />
          Sign In with Google
        </button>
      </div>

      {error && <p className="text-red-500 text-sm text-center">{error}</p>}
    </div>
  )
}
