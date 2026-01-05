import { useState, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import {
  demoAnalytics,
  demoConversations,
  demoEnabled,
  demoFaq,
  demoKnowledgeBase,
  demoSocialAccounts,
} from './demo-data';

const getApiBaseUrl = () => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  
  if (!apiUrl) {
    throw new Error('NEXT_PUBLIC_API_URL environment variable is not set. Please configure it in your environment variables.');
  }
  
  let normalizedUrl = apiUrl.trim();
  
  if (normalizedUrl.endsWith('/')) {
    normalizedUrl = normalizedUrl.slice(0, -1);
  }
  
  return normalizedUrl;
};

export class ApiClient {
  private static async getAuthHeaders(): Promise<HeadersInit> {
    const { supabase } = await import('./supabase');
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error('Non authentifié');
    }

    return {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${session.access_token}`,
    };
  }

  static async getPublic(endpoint: string): Promise<any> {
    const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API GET Public Error Details:', {
        status: response.status,
        statusText: response.statusText,
        endpoint,
        responseBody: errorText,
      });
      throw new Error(`Erreur API: ${response.status} - ${errorText}`);
    }

    return response.json();
  }

  static async get(endpoint: string): Promise<any> {
    if (demoEnabled) {
      if (
        endpoint.startsWith('/api/conversations') &&
        !endpoint.includes('/messages')
      ) {
        return {
          conversations: demoConversations.list,
          total: demoConversations.list.length,
        };
      }

      if (endpoint.startsWith('/api/social-accounts')) {
        return demoSocialAccounts;
      }

      if (endpoint.includes('/messages')) {
        const conversationId = endpoint.split('/')[3];
        const messages =
          (demoConversations.messages as any)[conversationId] || [];
        return {
          messages,
          total: messages.length,
        };
      }

      if (endpoint.startsWith('/api/analytics/trends')) {
        return {
          user_id: 'demo-user',
          period_days: 30,
          trends: demoAnalytics.conversationsOverTime.map(item => ({
            date: item.date,
            total_likes: Math.round(item.conversations * 1.8),
            total_shares: Math.round(item.conversations * 0.4),
            total_comments: Math.round(item.conversations * 0.7),
            total_impressions: item.conversations * 32,
            avg_engagement_rate: 4.2,
          })),
        };
      }

      if (endpoint.startsWith('/api/knowledge_documents')) {
        return demoKnowledgeBase.documents;
      }

      if (endpoint.startsWith('/api/faq-qa')) {
        return demoFaq.entries;
      }

      if (endpoint.startsWith('/api/ai-settings')) {
        return {
          id: 'demo-ai-settings',
          system_prompt:
            'You are SocialSyncAI, a multilingual luxury concierge that solves customer issues across Instagram & WhatsApp.',
          ai_model: 'anthropic/claude-3.5-sonnet',
          temperature: 0.2,
          top_p: 0.9,
          lang: 'fr',
          tone: 'premium',
          is_active: true,
          doc_lang: ['fr', 'en', 'es'],
        };
      }

      if (endpoint.startsWith('/api/ai-settings/templates')) {
        return {
          templates: {
            social: {
              system_prompt:
                'Social media co-pilot specialised in luxury fashion brands.',
            },
            ecommerce: {
              system_prompt:
                'E-commerce concierge for premium clients (returns, upsell, logistics).',
            },
            support: {
              system_prompt:
                'Tier-1 customer support assistant with escalation playbooks.',
            },
          },
        };
      }

      if (endpoint.startsWith('/api/subscriptions/me')) {
        return {
          id: 'demo-subscription',
          user_id: 'demo-user',
          plan: {
            id: 'professional',
            name: 'Professional',
            price_eur: 49,
            credits_included: 10000,
            max_ai_calls_per_batch: 5,
            storage_quota_mb: 1000,
            features: {
              images: true,
              audio: true,
              advanced_models: true,
            },
          },
          credits_balance: 8500,
          credits_included: 10000,
          status: 'active',
          current_period_start: new Date(
            Date.now() - 15 * 24 * 60 * 60 * 1000
          ).toISOString(),
          current_period_end: new Date(
            Date.now() + 15 * 24 * 60 * 60 * 1000
          ).toISOString(),
          days_until_renewal: 15,
          can_upgrade: true,
        };
      }

      if (endpoint.startsWith('/api/subscriptions/storage/usage')) {
        return {
          used_mb: 145.7,
          quota_mb: 1000,
          available_mb: 854.3,
          percentage_used: 14.6,
          is_full: false,
          is_approaching_limit: false,
        };
      }

      if (endpoint.startsWith('/api/subscriptions/models')) {
        return [
          {
            id: 'anthropic/claude-3.5-sonnet',
            name: 'Claude 3.5 Sonnet',
            provider: 'anthropic',
            credits_cost: 10,
            is_available: true,
            description: 'Most capable model for complex tasks',
          },
          {
            id: 'openai/gpt-4o',
            name: 'GPT-4o',
            provider: 'openai',
            credits_cost: 10,
            is_available: true,
            description: 'Latest GPT-4 model with vision',
          },
          {
            id: 'anthropic/claude-3.5-haiku',
            name: 'Claude 3.5 Haiku',
            provider: 'anthropic',
            credits_cost: 3,
            is_available: true,
            description: 'Fast and efficient for simple tasks',
          },
          {
            id: 'openai/gpt-4o-mini',
            name: 'GPT-4o Mini',
            provider: 'openai',
            credits_cost: 2,
            is_available: true,
            description: 'Compact model for quick responses',
          },
        ];
      }
    }

    const headers = await this.getAuthHeaders();
    const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API GET Error Details:', {
        status: response.status,
        statusText: response.statusText,
        endpoint,
        responseBody: errorText,
      });
      throw new Error(`Erreur API: ${response.status} - ${errorText}`);
    }

    return response.json();
  }

  static async post(endpoint: string, data: any): Promise<any> {
    if (demoEnabled) {
      if (endpoint === '/api/conversations/send-message') {
        const conversation = demoConversations.list[0];
        const fakeMessage = {
          id: `demo-${Date.now()}`,
          conversation_id: conversation?.id ?? 'demo',
          direction: 'outbound',
          content: data.content,
          message_type: data.message_type ?? 'text',
          created_at: new Date().toISOString(),
          is_from_agent: true,
        };

        if (conversation) {
          const conversationId = conversation.id as keyof typeof demoConversations.messages;
          const existingMessages = demoConversations.messages[conversationId] || [];
          demoConversations.messages[conversationId] = [
            ...existingMessages,
            fakeMessage,
          ];
        }

        return fakeMessage;
      }

      if (endpoint === '/api/faq-qa/') {
        const newEntry = {
          id: `faq-${Date.now()}`,
          questions: data.questions,
          answer: data.answer,
          context: data.metadata?.context ?? [],
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        demoFaq.entries.push(newEntry);
        return newEntry;
      }

      if (endpoint === '/api/ai-settings/reset') {
        return { status: 'ok' };
      }

      if (endpoint === '/api/ai-settings/test') {
        return {
          response: 'Demo response generated by SocialSyncAI demo agent.',
          response_time: 0.8,
          confidence: 0.92,
        };
      }
    }

    const headers = await this.getAuthHeaders();
    console.log('API POST Request:', { endpoint, data });
    const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API POST Error Details:', {
        status: response.status,
        statusText: response.statusText,
        endpoint,
        requestData: data,
        responseBody: errorText,
      });
      throw new Error(`Erreur API: ${response.status} - ${errorText}`);
    }

    return response.json();
  }

  static async patch(endpoint: string, data: any): Promise<any> {
    if (demoEnabled) {
      if (endpoint.endsWith('/read')) {
        return { status: 'ok' };
      }

      if (endpoint.endsWith('/ai_mode')) {
        return { status: 'ok', mode: data.mode };
      }

      if (endpoint.startsWith('/api/faq-qa/')) {
        return { ...data, updated_at: new Date().toISOString() };
      }

      if (endpoint === '/api/ai-settings/') {
        return {
          ...data,
          updated_at: new Date().toISOString(),
        };
      }
    }

    const headers = await this.getAuthHeaders();
    const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Erreur API: ${response.status}`);
    }

    return response.json();
  }

  static async put(endpoint: string, data: any): Promise<any> {
    const headers = await this.getAuthHeaders();
    const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Erreur API: ${response.status}`);
    }

    return response.json();
  }

  static async delete(endpoint: string): Promise<any> {
    if (demoEnabled) {
      if (endpoint.startsWith('/api/faq-qa/')) {
        const id = endpoint.split('/').pop();
        const index = demoFaq.entries.findIndex(entry => entry.id === id);
        if (index !== -1) {
          demoFaq.entries.splice(index, 1);
        }
        return { status: 'ok' };
      }

      if (endpoint.startsWith('/api/knowledge_documents/')) {
        const id = endpoint.split('/').pop();
        const index = demoKnowledgeBase.documents.findIndex(
          doc => doc.id === id
        );
        if (index !== -1) {
          demoKnowledgeBase.documents.splice(index, 1);
        }
        return { status: 'ok' };
      }
    }

    const headers = await this.getAuthHeaders();
    const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
      method: 'DELETE',
      headers,
    });

    if (!response.ok) {
      throw new Error(`Erreur API: ${response.status}`);
    }

    // Handle 204 No Content responses (no body to parse)
    if (response.status === 204) {
      return;
    }

    // Only parse JSON if there's content
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }

    return;
  }

  static async uploadFile(endpoint: string, formData: FormData): Promise<any> {
    const { supabase } = await import('./supabase');
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error('Non authentifié');
    }

    const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        // Ne pas définir Content-Type pour FormData, le navigateur le fait automatiquement avec boundary
      },
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API Upload Error:', {
        status: response.status,
        statusText: response.statusText,
        endpoint,
        responseBody: errorText,
      });
      throw new Error(`Erreur API: ${response.status} - ${errorText}`);
    }

    return response.json();
  }
}

// Types pour les comptes sociaux
export interface SocialAccount {
  id: string;
  platform: string;
  username: string;
  account_id: string;
  display_name?: string;
  profile_url?: string;
  access_token: string;
  refresh_token?: string;
  token_expires_at?: string;
  is_active: boolean;
  user_id: string;
  created_at: string;
  updated_at: string;
  status?: 'connected' | 'expired' | 'error' | 'pending_setup';
  status_message?: string;
}

// Types pour les conversations
export interface Conversation {
  id: string;
  channel: 'whatsapp' | 'instagram';
  customer_name?: string;
  customer_identifier: string;
  customer_avatar_url?: string;
  ai_mode?: 'ON' | 'OFF';
  last_message_at?: string;
  last_message_snippet: string;
  unread_count: number;
  social_account_id: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  direction: 'inbound' | 'outbound';
  content: string;
  message_type?: string;
  storage_object_name?: string;
  media_url?: string;
  media_type?: string;
  created_at: string;
  sender_id?: string;
  is_from_agent: boolean;
  is_edited?: boolean;
  metadata?: Record<string, any>;
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
}

export interface MessageListResponse {
  messages: Message[];
  total: number;
}

// Services pour les comptes sociaux
export interface SocialConnectConfig {
  authorization_url: string;
}

export class SocialAccountsService {
  static async getSocialAccounts(): Promise<{ accounts: SocialAccount[] }> {
    const accounts = await ApiClient.get('/api/social-accounts/');
    return { accounts: Array.isArray(accounts) ? accounts : [] };
  }

  static async getConnectUrl(platform: string): Promise<SocialConnectConfig> {
    return ApiClient.get(`/api/social-accounts/connect/${platform}`);
  }

  static async deleteSocialAccount(accountId: string): Promise<void> {
    return ApiClient.delete(`/api/social-accounts/${accountId}`);
  }
}

// Services pour les conversations
export class ConversationsService {
  static async getConversations(
    channel?: string,
    limit: number = 50
  ): Promise<ConversationListResponse> {
    const params = new URLSearchParams();
    if (channel && channel !== 'all') {
      params.append('channel', channel);
    }
    params.append('limit', limit.toString());

    return ApiClient.get(`/api/conversations?${params}`);
  }

  static async getMessages(
    conversationId: string,
    limit: number = 100
  ): Promise<MessageListResponse> {
    return ApiClient.get(
      `/api/conversations/${conversationId}/messages?limit=${limit}`
    );
  }

  static async sendMessage(
    customerName: string,
    platform: string,
    content: string,
    messageType: string = 'text'
  ): Promise<Message> {
    return ApiClient.post('/api/conversations/send-message', {
      customer_name: customerName,
      platform: platform,
      content,
      message_type: messageType,
    });
  }

  static async markAsRead(conversationId: string): Promise<void> {
    return ApiClient.patch(`/api/conversations/${conversationId}/read`, {});
  }

  static async updateAIMode(
    conversationId: string,
    mode: 'ON' | 'OFF'
  ): Promise<any> {
    return ApiClient.patch(`/api/conversations/${conversationId}/ai_mode`, {
      mode,
    });
  }
}

// Types pour les analytics
export interface AnalyticsTrend {
  date: string;
  total_likes: number;
  total_shares: number;
  total_comments: number;
  total_impressions: number;
  avg_engagement_rate: number;
}

export interface AnalyticsTrendsResponse {
  user_id: string;
  period_days: number;
  trends: AnalyticsTrend[];
}

// Services pour les analytics
// Moved to line 1155+ to avoid duplicate declaration

// Knowledge Documents
export interface KnowledgeDocument {
  id: string;
  title: string;
  storage_object_id: string;
  user_id: string;
  bucket_id?: string;
  object_name?: string;
  tsconfig: string;
  lang_code: string;
  status: string;
  last_ingested_at: string | null;
  last_embedded_at: string | null;
  embed_model: string | null;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export class KnowledgeDocumentsService {
  static async list(): Promise<KnowledgeDocument[]> {
    return ApiClient.get('/api/knowledge_documents/');
  }

  static async remove(documentId: string): Promise<KnowledgeDocument> {
    return ApiClient.delete(`/api/knowledge_documents/${documentId}`);
  }
}

// Types pour les FAQ Q&A
export interface FAQQA {
  id: string;
  user_id: string;
  title?: string;
  questions: string[];
  answer: string;
  metadata?: Record<string, any>;
  is_active?: boolean;
  created_at: string;
  updated_at: string;
  // Tags extraits depuis metadata.context côté frontend
  context?: string[];
  lastUpdated?: string;
  active?: boolean;
}

export interface FAQQACreate {
  title?: string;
  questions: string[];
  answer: string;
  metadata?: Record<string, any>;
  // Tags à inclure (seront mis dans metadata.context)
  context?: string[];
}

// Fonction utilitaire pour préparer les données de création avec tags
export function prepareFAQCreateData(data: FAQQACreate): any {
  const preparedData = { ...data };

  // Si des tags sont fournis, les mettre dans metadata.context
  if (data.context && data.context.length > 0) {
    preparedData.metadata = {
      ...preparedData.metadata,
      context: data.context,
    };
  }

  // Supprimer le champ context car il ne doit pas être envoyé directement
  delete preparedData.context;

  return preparedData;
}

export interface FAQQAUpdate extends Partial<FAQQACreate> {
  is_active?: boolean;
}

export interface FAQQASearch {
  query: string;
  limit?: number;
  offset?: number;
}

// Fonction utilitaire pour extraire les tags depuis metadata.context
export function extractTagsFromFAQ(faq: any): FAQQA {
  const faqData = { ...faq };

  // Extraire les tags depuis metadata.context si présent
  if (faqData.metadata && typeof faqData.metadata === 'object') {
    const metadata = faqData.metadata;
    if (metadata.context && Array.isArray(metadata.context)) {
      faqData.context = metadata.context;
    } else {
      faqData.context = [];
    }
  } else {
    faqData.context = [];
  }

  // S'assurer que questions est un tableau
  if (!Array.isArray(faqData.questions)) {
    faqData.questions = [];
  }

  // Mapper les champs pour la compatibilité frontend
  faqData.lastUpdated = faqData.updated_at;
  faqData.active = faqData.is_active;

  return faqData as FAQQA;
}

// Types pour la gestion des questions
export interface FAQQuestionsAddRequest {
  items: string[];
}

export interface FAQQuestionsUpdateRequest {
  updates: Array<{ index: number; value: string }>;
}

export interface FAQQuestionsDeleteRequest {
  indexes: number[];
}

// Services pour les FAQ Q&A
export class FAQQAService {
  static async list(): Promise<FAQQA[]> {
    const data = await ApiClient.get('/api/faq-qa/');
    return data.map(extractTagsFromFAQ);
  }

  static async get(faqId: string): Promise<FAQQA> {
    const data = await ApiClient.get(`/api/faq-qa/${faqId}`);
    return extractTagsFromFAQ(data);
  }

  static async create(data: FAQQACreate): Promise<FAQQA> {
    const preparedData = prepareFAQCreateData(data);
    const result = await ApiClient.post('/api/faq-qa/', preparedData);
    return extractTagsFromFAQ(result);
  }

  static async update(faqId: string, data: FAQQAUpdate): Promise<FAQQA> {
    // Préparer les données de mise à jour avec tags si nécessaire
    const preparedData = { ...data };
    if (data.context && data.context.length >= 0) {
      preparedData.metadata = {
        ...preparedData.metadata,
        context: data.context,
      };
      delete preparedData.context;
    }

    const result = await ApiClient.patch(`/api/faq-qa/${faqId}`, preparedData);
    return extractTagsFromFAQ(result);
  }

  static async toggle(
    faqId: string
  ): Promise<{ message: string; is_active: boolean }> {
    return ApiClient.patch(`/api/faq-qa/${faqId}/toggle`, {});
  }

  static async remove(faqId: string): Promise<void> {
    return ApiClient.delete(`/api/faq-qa/${faqId}`);
  }

  static async search(data: FAQQASearch): Promise<FAQQA[]> {
    return ApiClient.post('/api/faq-qa/search', data);
  }

  // Gestion des questions
  static async addQuestions(
    faqId: string,
    request: FAQQuestionsAddRequest
  ): Promise<{ message: string; questions: string[] }> {
    return ApiClient.post(`/api/faq-qa/${faqId}/questions:add`, request);
  }

  static async updateQuestions(
    faqId: string,
    request: FAQQuestionsUpdateRequest
  ): Promise<{ message: string; questions: string[] }> {
    return ApiClient.post(`/api/faq-qa/${faqId}/questions:update`, request);
  }

  static async deleteQuestions(
    faqId: string,
    request: FAQQuestionsDeleteRequest
  ): Promise<{ message: string; questions: string[] }> {
    return ApiClient.post(`/api/faq-qa/${faqId}/questions:delete`, request);
  }
}

// AI Settings Types
export interface AISettings {
  id?: string;
  system_prompt: string;
  ai_model: string;
  temperature: number;
  top_p: number;
  lang: string;
  tone: string;
  is_active: boolean;
  doc_lang: string[];
  ai_control_enabled?: boolean;
  ai_enabled_for_chats?: boolean;
  ai_enabled_for_comments?: boolean;
  flagged_keywords?: string[];
  flagged_phrases?: string[];
  instructions?: string | null;
  ignore_examples?: string[];
}

export interface AITestRequest {
  thread_id: string;
  messages: Array<{ role: string; content: string }>;
  settings: AISettings;
}

export interface AITestResponse {
  response: string;
  response_time: number;
  confidence: number;
}

// WhatsApp Service
export class WhatsAppService {
  static async sendTextMessage(request: {
    recipient: string;
    message: string;
  }): Promise<any> {
    return ApiClient.post('/api/whatsapp/send-text', request);
  }
}

// Instagram Service
export class InstagramService {
  static async sendDirectMessage(request: {
    recipient_username: string;
    message: string;
  }): Promise<any> {
    return ApiClient.post('/api/instagram/send-dm', request);
  }

  /**
   * Rafraîchit les URLs d'avatars Instagram pour toutes les conversations
   * (Les URLs Instagram expirent après 24-48h)
   */
  static async refreshAllAvatars(): Promise<{
    success: boolean;
    message: string;
    refreshed: number;
  }> {
    return ApiClient.post('/api/instagram/refresh-avatars', {});
  }

  /**
   * Rafraîchit l'URL d'avatar pour une conversation spécifique
   */
  static async refreshSingleAvatar(conversationId: string): Promise<{
    success: boolean;
    message: string;
    avatar_url: string;
  }> {
    return ApiClient.post(`/api/instagram/refresh-avatar/${conversationId}`, {});
  }
}

// AI Settings Service
export class AISettingsService {
  static async get(): Promise<AISettings> {
    return ApiClient.get('/api/ai-settings/');
  }

  static async update(settings: Partial<AISettings>): Promise<AISettings> {
    return ApiClient.put('/api/ai-settings/', settings);
  }

  static async test(testRequest: AITestRequest): Promise<AITestResponse> {
    return ApiClient.post('/api/ai-settings/test', testRequest);
  }

  static async getTemplates(): Promise<Record<string, any>> {
    const data = await ApiClient.get('/api/ai-settings/templates');
    return data.templates;
  }

  static async resetToTemplate(templateType: string): Promise<void> {
    return ApiClient.post('/api/ai-settings/reset', {
      template_type: templateType,
    });
  }
}

export function useAISettings() {
  const { toast } = useToast();
  const [settings, setSettings] = useState<AISettings | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await AISettingsService.get();
      setSettings(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      toast({
        title: 'Loading error',
        description: 'Unable to load AI settings.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const updateSettings = async (updatedSettings: Partial<AISettings>) => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await AISettingsService.update(updatedSettings);
      setSettings(data);

      toast({
        title: 'Settings saved',
        description: 'Your AI settings have been updated successfully.',
      });

      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      toast({
        title: 'Save error',
        description: 'Unable to save settings.',
        variant: 'destructive',
      });
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const testAIResponse = async (
    testRequest: AITestRequest
  ): Promise<AITestResponse> => {
    try {
      const data = await AISettingsService.test(testRequest);
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast({
        title: 'Test error',
        description: 'Unable to test AI response.',
        variant: 'destructive',
      });
      throw err;
    }
  };

  const getPromptTemplates = async () => {
    try {
      const data = await AISettingsService.getTemplates();
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast({
        title: 'Error',
        description: 'Unable to load templates.',
        variant: 'destructive',
      });
      throw err;
    }
  };

  const resetToTemplate = async (templateType: string) => {
    try {
      await AISettingsService.resetToTemplate(templateType);
      await fetchSettings(); // Reload settings

      toast({
        title: 'Template applied',
        description: `Settings have been reset with the ${templateType} template.`,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast({
        title: 'Error',
        description: 'Unable to apply template.',
        variant: 'destructive',
      });
      throw err;
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  return {
    settings,
    isLoading,
    error,
    fetchSettings,
    updateSettings,
    testAIResponse,
    getPromptTemplates,
    resetToTemplate,
  };
}

// ===== COMMENT MONITORING TYPES & SERVICES =====

export interface MonitoredPost {
  id: string
  user_id: string
  social_account_id: string
  platform_post_id: string
  platform: 'instagram' | 'facebook' | 'twitter'
  caption: string
  media_url?: string
  posted_at: string
  source: 'scheduled' | 'imported' | 'manual'
  monitoring_enabled: boolean
  monitoring_started_at?: string
  monitoring_ends_at?: string
  last_check_at?: string
  comments_count?: number
  days_remaining?: number
}

export interface MonitoringRules {
  auto_monitor_enabled: boolean
  auto_monitor_count: number
  monitoring_duration_days: number
}

export interface Comment {
  id: string
  post_id: string
  platform_comment_id: string
  author_name: string
  author_id: string
  author_avatar_url?: string
  text: string
  triage: 'respond' | 'ignore' | 'escalate'
  ai_decision_id?: string
  replied_at?: string
  ai_reply_text?: string
  created_at: string
  platform: 'instagram' | 'facebook' | 'twitter'
}

export interface CommentFilters {
  post_id?: string
  triage?: 'respond' | 'ignore' | 'escalate'
  platform?: string
  search?: string
  limit?: number
  offset?: number
}

export interface CommentsListResponse {
  comments: Comment[]
  total: number
}

// Services for Comment Monitoring
export class MonitoringService {
  static async syncPosts(): Promise<{ success: boolean; posts_imported: number }> {
    return ApiClient.post('/api/monitoring/sync', {})
  }

  static async getMonitoredPosts(): Promise<{ posts: MonitoredPost[] }> {
    return ApiClient.get('/api/monitoring/posts')
  }

  static async toggleMonitoring(postId: string): Promise<MonitoredPost> {
    const response = await ApiClient.patch(`/api/monitoring/posts/${postId}/toggle`, {})
    // Backend returns { success, post, message }, extract post
    return response.post
  }

  static async getRules(): Promise<MonitoringRules> {
    return ApiClient.get('/api/monitoring/rules')
  }

  static async updateRules(rules: MonitoringRules): Promise<MonitoringRules> {
    return ApiClient.put('/api/monitoring/rules', rules)
  }
}

export class CommentsService {
  static async getComments(filters?: CommentFilters): Promise<CommentsListResponse> {
    const params = new URLSearchParams()
    if (filters?.post_id) params.append('post_id', filters.post_id)
    if (filters?.triage) params.append('triage', filters.triage)
    if (filters?.platform) params.append('platform', filters.platform)
    if (filters?.search) params.append('search', filters.search)
    if (filters?.limit) params.append('limit', filters.limit.toString())
    if (filters?.offset) params.append('offset', filters.offset.toString())

    return ApiClient.get(`/api/comments?${params.toString()}`)
  }

  static async replyToComment(commentId: string, text: string): Promise<Comment> {
    return ApiClient.patch(`/api/comments/${commentId}/reply`, { text })
  }
}

// ===== ANALYTICS TYPES & SERVICES =====

export interface AnalyticsOverview {
  total_conversations: number
  total_messages: number
  ai_stats: {
    respond: number
    ignore: number
    escalate: number
    avg_confidence: number
  }
  total_escalations: number
  moderation_flags: number
  date_range: string
  start_date: string
  end_date: string
}

export interface ConversationTimelineItem {
  date: string
  conversations: number
  messages: number
}

export interface AIMetrics {
  distribution: {
    respond: number
    ignore: number
    escalate: number
  }
  confidence_over_time: Array<{
    date: string
    avg_confidence: number
    count: number
  }>
  top_rules: Array<{
    rule: string
    count: number
  }>
}

export interface Topic {
  topic_id: number
  topic_label: string
  topic_keywords: string[]
  message_count: number
  sample_messages: string[]
}

export class AnalyticsService {
  static async getOverview(dateRange: string = '30d'): Promise<AnalyticsOverview> {
    return ApiClient.get(`/api/analytics/overview?date_range=${dateRange}`)
  }

  static async getConversationsTimeline(dateRange: string = '30d'): Promise<ConversationTimelineItem[]> {
    return ApiClient.get(`/api/analytics/conversations-timeline?date_range=${dateRange}`)
  }

  static async getAIMetrics(dateRange: string = '30d'): Promise<AIMetrics> {
    return ApiClient.get(`/api/analytics/ai-metrics?date_range=${dateRange}`)
  }

  static async getTopics(dateRange: string = '30d'): Promise<Topic[]> {
    return ApiClient.get(`/api/analytics/topics?date_range=${dateRange}`)
  }

  static async getTrends(
    userId: string,
    days: number = 30
  ): Promise<AnalyticsTrendsResponse> {
    return ApiClient.get(`/api/analytics/trends/${userId}?days=${days}`);
  }
}

// Analytics hooks
export function useAnalyticsOverview(dateRange: string = '30d') {
  const { toast } = useToast()
  const [data, setData] = useState<AnalyticsOverview | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const result = await AnalyticsService.getOverview(dateRange)
      setData(result)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
      toast({
        title: 'Error loading analytics',
        description: errorMessage,
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [dateRange])

  return { data, isLoading, error, refetch: fetchData }
}

export function useConversationsTimeline(dateRange: string = '30d') {
  const { toast } = useToast()
  const [data, setData] = useState<ConversationTimelineItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const result = await AnalyticsService.getConversationsTimeline(dateRange)
      setData(result)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [dateRange])

  return { data, isLoading, error, refetch: fetchData }
}

export function useAIMetrics(dateRange: string = '30d') {
  const { toast } = useToast()
  const [data, setData] = useState<AIMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const result = await AnalyticsService.getAIMetrics(dateRange)
      setData(result)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [dateRange])

  return { data, isLoading, error, refetch: fetchData }
}

export function useTopics(dateRange: string = '30d') {
  const { toast } = useToast()
  const [data, setData] = useState<Topic[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const result = await AnalyticsService.getTopics(dateRange)
      setData(result)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [dateRange])

  return { data, isLoading, error, refetch: fetchData }
}
