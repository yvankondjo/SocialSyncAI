'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Plus, MoreHorizontal, RefreshCw, Loader2 } from 'lucide-react';
import { SocialAccount } from '../types/socialAccount';
import { SocialAccountsApi } from '../services/socialAccountsApi';
import { createClient } from '@/lib/supabase/client';
import { useRouter, useSearchParams } from 'next/navigation';

interface SocialProfile {
  id: string;
  platform: string;
  username: string;
  followers: string;
  engagement: string;
  status: 'connected' | 're-auth' | 'error' | 'disconnected';
  lastSync: string;
  tokenValid: boolean;
  tokenExpiry: string;
  logo: string;
  bgColor: string;
}

// Helper functions
const getPlatformConfig = (platform: string) => {
  const configs = {
    twitter: { logo: '/logos/x.svg', bgColor: 'bg-blue-50' },
    instagram: { logo: '/logos/instagram.svg', bgColor: 'bg-pink-50' },
    youtube: { logo: '/logos/youtube.svg', bgColor: 'bg-red-50' },
    tiktok: { logo: '/logos/tiktok.svg', bgColor: 'bg-gray-50' },
    reddit: { logo: '/logos/reddit.svg', bgColor: 'bg-orange-50' },
    facebook: { logo: '/logos/facebook.svg', bgColor: 'bg-blue-50' },
    linkedin: { logo: '/logos/linkedin.svg', bgColor: 'bg-blue-50' },
    whatsapp: { logo: '/logos/whatsapp.svg', bgColor: 'bg-green-50' }
  };
  return configs[platform as keyof typeof configs] || { logo: '/logos/default.svg', bgColor: 'bg-gray-50' };
};

const getTokenStatus = (tokenExpiresAt?: string) => {
  if (!tokenExpiresAt) return { valid: false, expiry: 'Unknown' };
  
  const expiryDate = new Date(tokenExpiresAt);
  const now = new Date();
  const diffTime = expiryDate.getTime() - now.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays < 0) return { valid: false, expiry: 'Expired' };
  if (diffDays < 7) return { valid: false, expiry: `${diffDays} days` };
  return { valid: true, expiry: `${diffDays} days` };
};

const getLastSyncText = (updatedAt: string) => {
  const lastUpdate = new Date(updatedAt);
  const now = new Date();
  const diffTime = now.getTime() - lastUpdate.getTime();
  const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffDays > 0) return `${diffDays} days ago`;
  if (diffHours > 0) return `${diffHours} hours ago`;
  return 'Just now';
};

const transformToSocialProfile = (account: SocialAccount): SocialProfile => {
  const platformConfig = getPlatformConfig(account.platform);
  const tokenStatus = getTokenStatus(account.token_expires_at);
  
  let status: 'connected' | 're-auth' | 'error' | 'disconnected' = 'disconnected';
  if (account.is_active) {
    status = tokenStatus.valid ? 'connected' : 're-auth';
  } else {
    status = 'error';
  }
  
  return {
    id: account.id,
    platform: account.platform,
    username: account.username,
    followers: 'N/A', // Ces données nécessiteraient une API supplémentaire
    engagement: 'N/A', // Ces données nécessiteraient une API supplémentaire
    status,
    lastSync: getLastSyncText(account.updated_at),
    tokenValid: tokenStatus.valid,
    tokenExpiry: tokenStatus.expiry,
    logo: platformConfig.logo,
    bgColor: platformConfig.bgColor
  };
};

const availablePlatforms = [
  { name: 'Instagram', logo: '/logos/instagram.svg', key: 'instagram' },
  { name: 'TikTok', logo: '/logos/tiktok.svg', key: 'tiktok' },
  { name: 'YouTube', logo: '/logos/youtube.svg', key: 'youtube' },
  { name: 'X (Twitter)', logo: '/logos/x.svg', key: 'twitter' },
  { name: 'Reddit', logo: '/logos/reddit.svg', key: 'reddit' },
  { name: 'Facebook', logo: '/logos/facebook.svg', key: 'facebook' },
  { name: 'LinkedIn', logo: '/logos/linkedin.svg', key: 'linkedin' },
  { name: 'WhatsApp', logo: '/logos/whatsapp.svg', key: 'whatsapp' }
];

const SocialProfileCard = ({ 
  profile, 
  onResync, 
  onReauth 
}: { 
  profile: SocialProfile;
  onResync: (accountId: string) => void;
  onReauth: (platform: string) => void;
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'text-green-600';
      case 're-auth': return 'text-orange-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'connected': return 'Connected';
      case 're-auth': return 'Re-auth';
      case 'error': return 'Error';
      default: return 'Disconnected';
    }
  };

  const getTokenStatus = (tokenValid: boolean) => {
    return tokenValid ? 'text-green-600' : 'text-red-600';
  };

  return (
    <div className={`${profile.bgColor} rounded-xl p-6 border border-gray-200`}>
      {/* Header with logo and platform name */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Image src={profile.logo} alt={profile.platform} width={32} height={32} className="mr-3" />
          <h3 className="font-semibold text-gray-800 capitalize">{profile.platform}</h3>
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8">
          <MoreHorizontal size={16} />
        </Button>
      </div>

      {/* Username */}
      <p className="text-sm text-gray-600 mb-6">{profile.username}</p>

      {/* Status and Last Sync */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <div className={`w-2 h-2 rounded-full mr-2 ${profile.status === 'connected' ? 'bg-green-500' : profile.status === 're-auth' ? 'bg-orange-500' : 'bg-red-500'}`}></div>
          <span className={`text-sm font-medium ${getStatusColor(profile.status)}`}>
            {getStatusText(profile.status)}
          </span>
        </div>
        <span className="text-xs text-gray-500">{profile.lastSync}</span>
      </div>

      {/* Token Status */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500">Token valid for</span>
        <span className={`text-xs font-medium ${getTokenStatus(profile.tokenValid)}`}>
          {profile.tokenExpiry}
        </span>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 mt-4">
        <Button 
          variant="outline" 
          size="sm" 
          className="flex-1 text-xs"
          onClick={() => onResync(profile.id)}
        >
          <RefreshCw size={12} className="mr-1" />
          Re-sync
        </Button>
        {profile.status !== 'connected' && (
          <Button 
            size="sm" 
            className="flex-1 text-xs gradient-bg text-white"
            onClick={() => onReauth(profile.platform)}
          >
            Re-auth
          </Button>
        )}
      </div>
    </div>
  );
};

const AddProfileCard = ({ onClick }: { onClick: () => void }) => (
  <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 flex flex-col items-center justify-center text-center min-h-[300px] hover:border-gray-400 transition-colors">
    <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
      <Plus size={24} className="text-gray-400" />
    </div>
    <h3 className="font-semibold text-gray-800 mb-2">Add Social Profile</h3>
    <p className="text-sm text-gray-500 mb-4">Enhance your presence</p>
    <Button 
      onClick={onClick}
      className="gradient-bg text-white"
    >
      Connect Profile
    </Button>
  </div>
);

const AccountsPage = () => {
  const [profiles, setProfiles] = useState<SocialProfile[]>([]);
  const [isModalOpen, setModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const router = useRouter();
  const supabase = createClient();
  const search = useSearchParams();

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' || event === 'INITIAL_SESSION') {
        if (session) {
          loadSocialAccounts();
        } else {
          router.push('/');
        }
      } else if (event === 'SIGNED_OUT') {
        router.push('/');
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [router, supabase]);

  const openModal = () => setModalOpen(true);
  const closeModal = () => setModalOpen(false);

  const loadSocialAccounts = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const accounts = await SocialAccountsApi.getSocialAccounts();
      const transformedProfiles = accounts.map(transformToSocialProfile);
      setProfiles(transformedProfiles);
    } catch (err) {
      console.error('Error loading social accounts:', err);
      setError('Impossible de charger les comptes sociaux. Veuillez réessayer.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnect = async (platform: string) => {
    try {
      setIsConnecting(true);
      const { authorization_url } = await SocialAccountsApi.getConnectUrl(platform);
      window.location.href = authorization_url;
    } catch (err) {
      console.error('Error getting connect URL:', err);
      setError('Impossible de se connecter à cette plateforme. Veuillez réessayer.');
      setIsConnecting(false);
    }
  };

  const handleResync = async (accountId: string) => {
    // Cette fonctionnalité nécessiterait une endpoint API pour re-synchroniser
    console.log('Resync account:', accountId);
    loadSocialAccounts(); // Recharger les données
  };

  const handleReauth = async (platform: string) => {
    await handleConnect(platform);
  };

  useEffect(() => {
    loadSocialAccounts();
  }, []);

  useEffect(() => {
    if (search.get('openModal') === '1') {
      setModalOpen(true);
    }
  }, [search]);

  return (
    <main className="flex-1 overflow-y-auto p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold text-gray-800">Profils Sociaux</h1>
          <Button 
            onClick={loadSocialAccounts}
            variant="outline"
            disabled={isLoading}
          >
            <RefreshCw size={16} className={`mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Actualiser
          </Button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            <div className="flex items-start">
              <div className="flex-1">
                <p className="font-medium mb-2">Erreur lors de la récupération des comptes</p>
                <p className="text-sm mb-3">{error}</p>
                {error.includes('401') && (
                  <div className="text-sm bg-red-100 p-3 rounded border">
                    <p className="font-medium mb-2">Cela signifie que vous n&apos;êtes pas authentifié.</p>
                    <ol className="list-decimal list-inside space-y-1">
                      <li>Assurez-vous d&apos;être connecté.</li>
                      <li>Si vous êtes connecté, votre session a peut-être expiré. Essayez de vous reconnecter.</li>
                    </ol>
                  </div>
                )}
                 {error.includes('se connecter au serveur') && (
                  <div className="text-sm bg-red-100 p-3 rounded border">
                    <p className="font-medium mb-2">Pour résoudre ce problème :</p>
                    <ol className="list-decimal list-inside space-y-1">
                      <li>Vérifiez que le backend FastAPI est démarré sur le port 8001</li>
                      <li>Démarrez le backend avec : <code className="bg-red-200 px-1 rounded">cd backend && uvicorn app.main:app --reload --port 8001</code></li>
                      <li>Vérifiez que l&apos;URL API est correcte : <code className="bg-red-200 px-1 rounded">http://localhost:8001</code></li>
                    </ol>
                  </div>
                )}
              </div>
            </div>
            <Button 
              onClick={loadSocialAccounts}
              variant="outline"
              size="sm"
              className="mt-3"
            >
              Réessayer
            </Button>
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            <span className="ml-2 text-gray-600">Chargement des comptes...</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {profiles.map(profile => (
              <SocialProfileCard 
                key={profile.id} 
                profile={profile}
                onResync={handleResync}
                onReauth={handleReauth}
              />
            ))}
            <AddProfileCard onClick={openModal} />
          </div>
        )}
      </div>

      {/* Enhanced modal with logos and interactive buttons */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={closeModal}>
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4" onClick={e => e.stopPropagation()}>
            <h2 className="text-xl font-bold mb-2">Connecter un Nouveau Profil</h2>
            <p className="text-gray-600 mb-6">Choisissez une plateforme pour connecter votre compte de média social</p>
            
            {error && !isLoading && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg mb-4 text-sm">
                {error}
              </div>
            )}
            
            <div className="space-y-3">
              {availablePlatforms.map(platform => {
                const isAlreadyConnected = profiles.some(p => p.platform === platform.key);
                
                return (
                  <Button
                    key={platform.name}
                    onClick={() => handleConnect(platform.key)}
                    variant="outline"
                    disabled={isConnecting || isAlreadyConnected}
                    className="w-full h-16 p-4 justify-start hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50"
                  >
                    <Image 
                      src={platform.logo} 
                      alt={platform.name} 
                      width={32} 
                      height={32} 
                      className="mr-4" 
                    />
                    <div className="text-left">
                      <p className="font-semibold text-gray-800">{platform.name}</p>
                      <p className="text-sm text-gray-500">
                        {isAlreadyConnected ? 'Déjà connecté' : `Connecter votre compte ${platform.name.toLowerCase()}`}
                      </p>
                    </div>
                    <div className="ml-auto text-gray-400">
                      {isConnecting ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : isAlreadyConnected ? (
                        '✓'
                      ) : (
                        '→'
                      )}
                    </div>
                  </Button>
                );
              })}
            </div>
            
            <div className="flex gap-3 mt-6">
              <Button 
                onClick={closeModal} 
                variant="outline" 
                className="flex-1"
                disabled={isConnecting}
              >
                Annuler
              </Button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
};

export default AccountsPage;