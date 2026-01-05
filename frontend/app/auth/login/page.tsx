'use client'

import { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { supabase } from '@/lib/supabase'
import { logos } from '@/lib/logos'

export default function LoginPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event: any, session: any) => {
      if (session) {
        const redirect = searchParams?.get('redirect')
        if (redirect) {
          router.push(redirect)
        } else {
          router.push('/dashboard')
        }
      }
    })

    return () => subscription.unsubscribe()
  }, [router, searchParams])

  const getCallbackUrl = () => {
    const frontendUrl = process.env.NEXT_PUBLIC_FRONTEND_URL || process.env.NEXT_PUBLIC_APP_URL;
    
    if (frontendUrl) {
      return `${frontendUrl}/auth/callback`;
    }
    
    if (typeof window !== 'undefined') {
      return `${window.location.origin}/auth/callback`;
    }
    
    throw new Error('NEXT_PUBLIC_FRONTEND_URL or NEXT_PUBLIC_APP_URL must be set for OAuth callbacks');
  };

  const handleGoogleSignIn = async () => {
    try {
      const redirect = searchParams?.get('redirect')
      if (redirect) {
        localStorage.setItem('auth_redirect', redirect)
      }
      
      const callbackUrl = getCallbackUrl();
      
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: callbackUrl
        }
      })
      if (error) {
        console.error('Erreur de connexion Google:', error)
        alert('Erreur lors de la connexion avec Google')
      }
    } catch (err) {
      console.error('Erreur inattendue:', err)
      alert('Une erreur inattendue s\'est produite')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-violet-50 p-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            SocialSyncAI
          </h1>
          <p className="text-gray-600">
            Connectez-vous à votre compte pour gérer vos réseaux sociaux
          </p>
        </div>

        <div className="bg-white p-8 rounded-xl shadow-lg border">
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Connexion à SocialSyncAI
              </h2>
              <p className="text-gray-600 text-sm">
                Connectez-vous avec votre compte Google pour accéder à votre tableau de bord
              </p>
            </div>

            <div className="space-y-4">
              <Button
                onClick={handleGoogleSignIn}
                className="w-full bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 flex items-center justify-center space-x-3 py-3"
              >
                <img src={logos.google} alt="Google" className="w-5 h-5" />
                <span>Continuer avec Google</span>
              </Button>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">ou</span>
                </div>
              </div>

              <div className="text-center text-sm text-gray-600">
                En vous connectant, vous acceptez nos conditions d'utilisation
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

