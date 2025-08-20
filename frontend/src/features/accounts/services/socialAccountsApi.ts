import { SocialAccount } from '../types/socialAccount';
import { createClient } from '@/lib/supabase/client';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class SocialAccountsApi {
  private static async getAuthHeaders(): Promise<HeadersInit> {
    try {
      const supabase = createClient();
      const { data: { session }, error: sessionError } = await supabase.auth.getSession();
      
      if (sessionError) {
        console.error('Erreur lors de la récupération de la session Supabase:', sessionError);
      }

      console.log('Session Supabase récupérée:', session);
      const token = session?.access_token;
      console.log('Token de session:', token ? '✅ Token trouvé' : '❌ Aucun token trouvé');
      
      return {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
      };
    } catch (error) {
      console.error('Error getting auth headers:', error);
      return {
        'Content-Type': 'application/json',
      };
    }
  }

  static async getSocialAccounts(): Promise<SocialAccount[]> {
    try {
      console.log('Fetching social accounts from:', `${API_BASE_URL}/api/social-accounts/`);
      const headers = await this.getAuthHeaders();
      console.log('Request headers:', headers);
      
      const response = await fetch(`${API_BASE_URL}/api/social-accounts/`, {
        method: 'GET',
        headers,
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`Failed to fetch social accounts: ${response.status} ${response.statusText} - ${errorText}`);
      }

      const data = await response.json();
      console.log('Received data:', data);
      return data;
    } catch (error) {
      console.error('Error fetching social accounts:', error);
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        throw new Error('Impossible de se connecter au serveur. Vérifiez que l\'API backend est démarrée.');
      }
      throw error;
    }
  }

  static async deleteSocialAccount(accountId: string): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/social-accounts/${accountId}`, {
        method: 'DELETE',
        headers: await this.getAuthHeaders(),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to delete social account: ${response.status} ${response.statusText} - ${errorText}`);
      }
    } catch (error) {
      console.error('Error deleting social account:', error);
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        throw new Error('Impossible de se connecter au serveur. Vérifiez que l\'API backend est démarrée.');
      }
      throw error;
    }
  }

  static async getConnectUrl(platform: string): Promise<{ authorization_url: string }> {
    try {
      console.log('Getting connect URL for platform:', platform);
      const response = await fetch(`${API_BASE_URL}/api/social-accounts/connect/${platform}`, {
        method: 'GET',
        headers: await this.getAuthHeaders(),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error getting connect URL:', errorText);
        throw new Error(`Failed to get connect URL: ${response.status} ${response.statusText} - ${errorText}`);
      }

      const data = await response.json();
      console.log('Connect URL response:', data);
      return data;
    } catch (error) {
      console.error('Error getting connect URL:', error);
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        throw new Error('Impossible de se connecter au serveur. Vérifiez que l\'API backend est démarrée.');
      }
      throw error;
    }
  }
}