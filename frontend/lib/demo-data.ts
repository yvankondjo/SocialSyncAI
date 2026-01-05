export type DemoDateRange = '7d' | '30d' | '90d';

export const demoEnabled = process.env.NEXT_PUBLIC_USE_DEMO === 'true';

export const demoAnalytics = {
  kpis: {
    conversations: {
      value: 4821,
      trend: 18.7,
      isPositive: true,
      trendLabel: 'vs last month',
    },
    avgResponseTime: {
      value: '1m 47s',
      trend: -21.4,
      isPositive: true,
      trendLabel: 'improvement',
    },
    resolutionRate: {
      value: '96.8%',
      trend: 4.2,
      isPositive: true,
      trendLabel: 'vs last month',
    },
    satisfaction: {
      value: '4.9/5',
      trend: 3.6,
      isPositive: true,
      trendLabel: 'from CSAT surveys',
    },
  },
  conversationsOverTime: [
    { date: 'Sep 1', conversations: 138 },
    { date: 'Sep 5', conversations: 162 },
    { date: 'Sep 10', conversations: 209 },
    { date: 'Sep 15', conversations: 231 },
    { date: 'Sep 20', conversations: 255 },
    { date: 'Sep 25', conversations: 278 },
    { date: 'Sep 30', conversations: 302 },
  ],
  responseTimeDistribution: [
    { hour: '00h', avgSeconds: 165 },
    { hour: '04h', avgSeconds: 132 },
    { hour: '08h', avgSeconds: 88 },
    { hour: '12h', avgSeconds: 94 },
    { hour: '16h', avgSeconds: 112 },
    { hour: '20h', avgSeconds: 142 },
  ],
  sentiment: [
    { label: 'Positive', value: 71, color: '#10b981' },
    { label: 'Neutral', value: 19, color: '#fbbf24' },
    { label: 'Negative', value: 10, color: '#ef4444' },
  ],
  topTopics: [
    { topic: 'Delivery updates', count: 418 },
    { topic: 'Product availability', count: 362 },
    { topic: 'Returns & refunds', count: 296 },
    { topic: 'Influencer program', count: 214 },
    { topic: 'Bulk orders', count: 187 },
  ],
  topQuestions: [
    { question: 'Where is my order?', count: 146 },
    { question: 'Do you ship internationally?', count: 123 },
    { question: 'How can I change my delivery address?', count: 97 },
    { question: 'What sizes are in stock?', count: 86 },
    { question: 'Can I talk to a stylist?', count: 54 },
  ],
  recentActivity: [
    {
      id: 'act-1',
      type: 'conversation',
      title: 'New WhatsApp escalation – Premium customer',
      time: '2 minutes ago',
      status: 'escalated',
    },
    {
      id: 'act-2',
      type: 'resolution',
      title: 'Instagram DM resolved – Styling advice',
      time: '7 minutes ago',
      status: 'resolved',
    },
    {
      id: 'act-3',
      type: 'conversation',
      title: 'New Instagram Story reply from @celine.paris',
      time: '18 minutes ago',
      status: 'active',
    },
    {
      id: 'act-4',
      type: 'feedback',
      title: 'CSAT survey submitted – 5⭐ rating',
      time: '35 minutes ago',
      status: 'positive',
    },
  ],
};

export const demoConversations = {
  list: [
    {
      id: 'conv-001',
      customer_name: 'Emma Laurent',
      customer_identifier: 'emma.laurent',
      channel: 'instagram',
      customer_avatar_url: '/demo/avatars/emma.png',
      last_message_snippet:
        "J'aimerais une tenue pour un shooting à Marrakech…",
      last_message_at: new Date().toISOString(),
      unread_count: 2,
      ai_mode: 'ON',
      social_account_id: 'acc-instagram-main',
    },
    {
      id: 'conv-002',
      customer_name: 'Carlos Jiménez',
      customer_identifier: '+34 630 98 12 54',
      channel: 'whatsapp',
      customer_avatar_url: '/demo/avatars/carlos.png',
      last_message_snippet: 'Puedo recibir mi pedido antes del viernes?',
      last_message_at: new Date(Date.now() - 3600_000).toISOString(),
      unread_count: 0,
      ai_mode: 'ON',
      social_account_id: 'acc-whatsapp-latam',
    },
    {
      id: 'conv-003',
      customer_name: 'Sophie Müller',
      customer_identifier: 'sophie.mueller',
      channel: 'instagram',
      customer_avatar_url: '/demo/avatars/sophie.png',
      last_message_snippet: 'Hi! Do you have vegan leather jackets in stock?',
      last_message_at: new Date(Date.now() - 7200_000).toISOString(),
      unread_count: 1,
      ai_mode: 'OFF',
      social_account_id: 'acc-instagram-main',
    },
    {
      id: 'conv-004',
      customer_name: 'Yasmine Chen',
      customer_identifier: 'yasmine.chen',
      channel: 'instagram',
      customer_avatar_url: '/demo/avatars/yasmine.png',
      last_message_snippet: 'Je cherche une robe noire pour samedi, help!',
      last_message_at: new Date(Date.now() - 1800_000).toISOString(),
      unread_count: 0,
      ai_mode: 'ON',
      social_account_id: 'acc-instagram-main',
    },
    {
      id: 'conv-005',
      customer_name: 'Noah Becker',
      customer_identifier: '+49 01573 123456',
      channel: 'whatsapp',
      customer_avatar_url: '/demo/avatars/noah.png',
      last_message_snippet: 'Kann ich den Stoff fühlen, bevor ich bestelle?',
      last_message_at: new Date(Date.now() - 2600_000).toISOString(),
      unread_count: 3,
      ai_mode: 'ON',
      social_account_id: 'acc-whatsapp-latam',
    },
  ],
  messages: {
    'conv-001': [
      {
        id: 'msg-001-1',
        conversation_id: 'conv-001',
        content:
          'Coucou, je cherche une tenue bohème pour un shooting à Marrakech. Vous avez des idées?',
        direction: 'inbound',
        created_at: new Date(Date.now() - 1800_000).toISOString(),
        message_type: 'text',
      },
      {
        id: 'msg-001-2',
        conversation_id: 'conv-001',
        content:
          'Bonjour Emma ☀️ Marrakech est parfaite pour des tons terre cuite. Je vous propose notre robe Sahara en lin et le kimono Atlas pour les fins de journée. Voulez-vous que je vous envoie les tailles dispo?',
        direction: 'outbound',
        created_at: new Date(Date.now() - 1500_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
      {
        id: 'msg-001-3',
        conversation_id: 'conv-001',
        content: 'Oui stp 🙏 Je fais du 36 habituellement',
        direction: 'inbound',
        created_at: new Date(Date.now() - 900_000).toISOString(),
        message_type: 'text',
      },
      {
        id: 'msg-001-4',
        conversation_id: 'conv-001',
        content:
          'Nous avons du 34 au 40 en stock. Une styliste peut vous faire un lookbook express si vous le souhaitez 💫',
        direction: 'outbound',
        created_at: new Date(Date.now() - 600_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
      {
        id: 'msg-001-5',
        conversation_id: 'conv-001',
        content: JSON.stringify([
          {
            type: 'image_url',
            image_url: {
              url: 'https://images.unsplash.com/photo-1553028826-ccdfc006d1b5?auto=format&fit=crop&w=600&q=80',
            },
          },
          { type: 'text', text: "Voici la photo d'inspiration pour Marrakech" },
        ]),
        direction: 'inbound',
        created_at: new Date(Date.now() - 540_000).toISOString(),
        message_type: 'image',
      },
      {
        id: 'msg-001-6',
        conversation_id: 'conv-001',
        content:
          'Magnifique inspiration ! Notre palette Terracotta correspond parfaitement. Je vous propose trois silhouettes adaptées au shooting.',
        direction: 'outbound',
        created_at: new Date(Date.now() - 480_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
      {
        id: 'msg-001-7',
        conversation_id: 'conv-001',
        content: JSON.stringify([
          {
            type: 'audio',
            url: 'https://cdn.conversai.ai/demo/audio/lookbook-emma.mp3',
          },
          { type: 'text', text: 'Voice note - mes attentes pour le shooting' },
        ]),
        direction: 'inbound',
        created_at: new Date(Date.now() - 420_000).toISOString(),
        message_type: 'audio',
      },
      {
        id: 'msg-001-8',
        conversation_id: 'conv-001',
        content:
          'Merci pour le vocal ! Je note: ambiance terracotta, focale sur les textures. J’envoie la sélection finale dans quelques minutes.',
        direction: 'outbound',
        created_at: new Date(Date.now() - 360_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
    ],
    'conv-002': [
      {
        id: 'msg-002-1',
        conversation_id: 'conv-002',
        content:
          'Hola! ¿Puede llegar mi pedido antes del viernes? Es para un regalo.',
        direction: 'inbound',
        created_at: new Date(Date.now() - 7200_000).toISOString(),
        message_type: 'text',
      },
      {
        id: 'msg-002-2',
        conversation_id: 'conv-002',
        content:
          'Hola Carlos 👋 Revisé tu pedido y está listo para envío express. Llega el jueves antes de las 14h. Te avisamos cuando salga ✨',
        direction: 'outbound',
        created_at: new Date(Date.now() - 6900_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
      {
        id: 'msg-002-3',
        conversation_id: 'conv-002',
        content: 'Genial, muchas gracias!',
        direction: 'inbound',
        created_at: new Date(Date.now() - 6600_000).toISOString(),
        message_type: 'text',
      },
      {
        id: 'msg-002-4',
        conversation_id: 'conv-002',
        content: JSON.stringify([
          {
            type: 'image_url',
            image_url: {
              url: 'https://images.unsplash.com/photo-1600180758890-6d3abcf7588f?auto=format&fit=crop&w=600&q=80',
            },
          },
          {
            type: 'text',
            text: 'Aquí la foto del producto que necesito cambiar',
          },
        ]),
        direction: 'inbound',
        created_at: new Date(Date.now() - 6400_000).toISOString(),
        message_type: 'image',
      },
      {
        id: 'msg-002-5',
        conversation_id: 'conv-002',
        content:
          'Gracias por la foto. Confirmo que tenemos stock en la talla M. ¿Deseas que reserve uno para tu recogida en nuestra boutique de Barcelona?',
        direction: 'outbound',
        created_at: new Date(Date.now() - 6200_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
      {
        id: 'msg-002-6',
        conversation_id: 'conv-002',
        content: JSON.stringify([
          {
            type: 'audio',
            url: 'https://cdn.conversai.ai/demo/audio/confirmacion-whatsapp.mp3',
          },
          { type: 'text', text: 'Nota de voz: prefiero recogerlo el jueves' },
        ]),
        direction: 'inbound',
        created_at: new Date(Date.now() - 6000_000).toISOString(),
        message_type: 'audio',
      },
      {
        id: 'msg-002-7',
        conversation_id: 'conv-002',
        content:
          'Perfecto, queda reservado para el jueves a las 17h. Te envío un QR por DM para agilizar la recogida.',
        direction: 'outbound',
        created_at: new Date(Date.now() - 5800_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
    ],
    'conv-003': [
      {
        id: 'msg-003-1',
        conversation_id: 'conv-003',
        content: 'Hi! Do you have vegan leather jackets in stock?',
        direction: 'inbound',
        created_at: new Date(Date.now() - 5400_000).toISOString(),
        message_type: 'text',
      },
      {
        id: 'msg-003-2',
        conversation_id: 'conv-003',
        content:
          'Hello Sophie! Yes, our Oslo vegan leather jacket is back in stock in XS to L. The texture is matte and breathable—perfect for autumn. Want me to place one on hold?',
        direction: 'outbound',
        created_at: new Date(Date.now() - 4800_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
      {
        id: 'msg-003-3',
        conversation_id: 'conv-003',
        content: JSON.stringify([
          {
            type: 'image_url',
            image_url: {
              url: 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=600&q=80',
            },
          },
        ]),
        direction: 'inbound',
        created_at: new Date(Date.now() - 4500_000).toISOString(),
        message_type: 'image',
      },
      {
        id: 'msg-003-4',
        conversation_id: 'conv-003',
        content:
          'C’est superbe ! Pour matcher cet esprit, je recommande notre veste Oslo + pantalon Berlin. Je peux préparer un essayage virtuel ?',
        direction: 'outbound',
        created_at: new Date(Date.now() - 4350_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
      {
        id: 'msg-003-5',
        conversation_id: 'conv-003',
        content: 'I love it! Can you hold the size S until tomorrow?',
        direction: 'inbound',
        created_at: new Date(Date.now() - 4200_000).toISOString(),
        message_type: 'text',
      },
      {
        id: 'msg-003-6',
        conversation_id: 'conv-003',
        content:
          "Absolutely—I've reserved it under your name. You'll receive a confirmation shortly with a voice note from the stylist.",
        direction: 'outbound',
        created_at: new Date(Date.now() - 3900_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
      {
        id: 'msg-003-7',
        conversation_id: 'conv-003',
        content: JSON.stringify([
          {
            type: 'audio',
            url: 'https://cdn.conversai.ai/demo/audio/stylist-sophie.mp3',
          },
          { type: 'text', text: 'Voice note: could we try another color?' },
        ]),
        direction: 'inbound',
        created_at: new Date(Date.now() - 3600_000).toISOString(),
        message_type: 'audio',
      },
      {
        id: 'msg-003-8',
        conversation_id: 'conv-003',
        content:
          'Bien sûr ! Je garde aussi un exemplaire caramel en réserve et je vous envoie les photos dans la foulée.',
        direction: 'outbound',
        created_at: new Date(Date.now() - 3300_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
    ],
    'conv-004': [
      {
        id: 'msg-004-1',
        conversation_id: 'conv-004',
        content:
          'Bonjour, avez-vous une robe noire disponible pour samedi soir ?',
        direction: 'inbound',
        created_at: new Date(Date.now() - 3000_000).toISOString(),
        message_type: 'text',
      },
      {
        id: 'msg-004-2',
        conversation_id: 'conv-004',
        content: JSON.stringify([
          {
            type: 'image_url',
            image_url: {
              url: 'https://images.unsplash.com/photo-1514996937319-344454492b37?auto=format&fit=crop&w=600&q=80',
            },
          },
          { type: 'text', text: 'Voici un modèle qui pourrait vous plaire' },
        ]),
        direction: 'inbound',
        created_at: new Date(Date.now() - 2760_000).toISOString(),
        message_type: 'image',
      },
      {
        id: 'msg-004-3',
        conversation_id: 'conv-004',
        content:
          'Merci pour l’inspi ! Je peux vous proposer notre robe Nuit Noire disponible en 38 et 40, prêts pour samedi.',
        direction: 'outbound',
        created_at: new Date(Date.now() - 2640_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
      {
        id: 'msg-004-4',
        conversation_id: 'conv-004',
        content: JSON.stringify([
          {
            type: 'audio',
            url: 'https://cdn.conversai.ai/demo/audio/robe-noire-tip.mp3',
          },
          { type: 'text', text: 'J’hésite entre 38 et 40, voici mes mesures' },
        ]),
        direction: 'inbound',
        created_at: new Date(Date.now() - 2520_000).toISOString(),
        message_type: 'audio',
      },
      {
        id: 'msg-004-5',
        conversation_id: 'conv-004',
        content:
          'Merci Yasmine, je prévois les deux tailles et un fitting express à 14h. Tu recevras un QR d’accès VIP dans la soirée.',
        direction: 'outbound',
        created_at: new Date(Date.now() - 2280_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
    ],
    'conv-005': [
      {
        id: 'msg-005-1',
        conversation_id: 'conv-005',
        content: 'Kann ich den Stoff fühlen, bevor ich bestelle?',
        direction: 'inbound',
        created_at: new Date(Date.now() - 2600_000).toISOString(),
        message_type: 'text',
      },
      {
        id: 'msg-005-2',
        conversation_id: 'conv-005',
        content: JSON.stringify([
          {
            type: 'image_url',
            image_url: {
              url: 'https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=600&q=80',
            },
          },
          { type: 'text', text: 'Sample tactile pack' },
        ]),
        direction: 'inbound',
        created_at: new Date(Date.now() - 2400_000).toISOString(),
        message_type: 'image',
      },
      {
        id: 'msg-005-3',
        conversation_id: 'conv-005',
        content:
          'Danke! Wir haben ein Sample-Pack mit 5 Stoffen. Soll ich es per Kurier nach Berlin schicken?',
        direction: 'outbound',
        created_at: new Date(Date.now() - 2280_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
      {
        id: 'msg-005-4',
        conversation_id: 'conv-005',
        content: JSON.stringify([
          {
            type: 'audio',
            url: 'https://cdn.conversai.ai/demo/audio/sample-pack-de.mp3',
          },
          { type: 'text', text: 'Audio: bitte Größe XL berücksichtigen' },
        ]),
        direction: 'inbound',
        created_at: new Date(Date.now() - 2100_000).toISOString(),
        message_type: 'audio',
      },
      {
        id: 'msg-005-5',
        conversation_id: 'conv-005',
        content:
          'Perfekt, ich packe zusätzlich zwei XL-Samples ein und der Kurier passe um 18h vorbei.',
        direction: 'outbound',
        created_at: new Date(Date.now() - 1980_000).toISOString(),
        message_type: 'text',
        is_from_agent: true,
      },
    ],
  },
};

export const demoKnowledgeBase = {
  documents: [
    {
      id: 'doc-atelier-guide',
      title: "Atelier – Guide d'entretien premium",
      status: 'indexed',
      embed_model: 'text-embedding-3-large',
      lang_code: 'fr',
      created_at: new Date(Date.now() - 86400_000 * 28).toISOString(),
      updated_at: new Date(Date.now() - 86400_000 * 3).toISOString(),
      last_ingested_at: new Date(Date.now() - 86400_000 * 3).toISOString(),
      object_name: 'atelier/guide-entretien.pdf',
      storage_object_id: 'storage-atelier-guide',
      user_id: 'demo-user',
      tsconfig: '{}',
      last_embedded_at: new Date(Date.now() - 86400_000 * 3).toISOString(),
      is_deleted: false,
    },
    {
      id: 'doc-stylebook-ss25',
      title: 'Lookbook SS25 – Collection Riviera',
      status: 'processing',
      embed_model: 'text-embedding-3-small',
      lang_code: 'en',
      created_at: new Date(Date.now() - 86400_000 * 5).toISOString(),
      updated_at: new Date(Date.now() - 86400_000 * 1).toISOString(),
      last_ingested_at: null,
      object_name: 'stylebook/ss25.pdf',
      storage_object_id: 'storage-stylebook-ss25',
      user_id: 'demo-user',
      tsconfig: '{}',
      last_embedded_at: null,
      is_deleted: false,
    },
    {
      id: 'doc-livraison-eu',
      title: 'Politique de livraison Europe',
      status: 'indexed',
      embed_model: 'text-embedding-3-large',
      lang_code: 'fr',
      created_at: new Date(Date.now() - 86400_000 * 40).toISOString(),
      updated_at: new Date(Date.now() - 86400_000 * 10).toISOString(),
      last_ingested_at: new Date(Date.now() - 86400_000 * 10).toISOString(),
      object_name: 'policies/livraison-eu.pdf',
      storage_object_id: 'storage-livraison-eu',
      user_id: 'demo-user',
      tsconfig: '{}',
      last_embedded_at: new Date(Date.now() - 86400_000 * 10).toISOString(),
      is_deleted: false,
    },
    {
      id: 'doc-returns-policy',
      title: 'Returns & Exchanges – Premium Clients',
      status: 'error',
      embed_model: 'text-embedding-3-small',
      lang_code: 'en',
      created_at: new Date(Date.now() - 86400_000 * 20).toISOString(),
      updated_at: new Date(Date.now() - 86400_000 * 2).toISOString(),
      last_ingested_at: null,
      object_name: 'policies/returns-premium.pdf',
      storage_object_id: 'storage-returns-premium',
      user_id: 'demo-user',
      tsconfig: '{}',
      last_embedded_at: null,
      is_deleted: false,
    },
  ],
};

export const demoFaq = {
  entries: [
    {
      id: 'faq-ship-1',
      questions: ['Do you ship worldwide?', "Livrez-vous à l'international ?"],
      answer:
        'Yes! We deliver to 32 countries in Europe, North America and the Middle East. Express delivery (48h) is available for premium members in Paris, Madrid, London and Dubai.',
      context: ['shipping', 'delivery', 'membership'],
      is_active: true,
      updated_at: new Date(Date.now() - 86400_000 * 2).toISOString(),
      created_at: new Date(Date.now() - 86400_000 * 40).toISOString(),
    },
    {
      id: 'faq-stylist',
      questions: [
        'How can I book a stylist session?',
        'Puis-je parler à une styliste?',
      ],
      answer:
        'Our styling team is available Monday to Saturday, 10h-20h CET. Send “Stylist” on WhatsApp and the AI will pre-qualify your needs before scheduling a human stylist in under 15 minutes.',
      context: ['styling', 'concierge'],
      is_active: true,
      updated_at: new Date(Date.now() - 86400_000 * 5).toISOString(),
      created_at: new Date(Date.now() - 86400_000 * 60).toISOString(),
    },
    {
      id: 'faq-returns',
      questions: ['What is the return policy for limited editions?'],
      answer:
        'Limited editions can be returned within 7 days in their original packaging. A concierge picks the item at your address within 24h inside Paris and Madrid.',
      context: ['returns', 'limited'],
      is_active: false,
      updated_at: new Date(Date.now() - 86400_000 * 12).toISOString(),
      created_at: new Date(Date.now() - 86400_000 * 70).toISOString(),
    },
  ],
};

export const demoSocialAccounts = [
  {
    id: 'acc-instagram-main',
    platform: 'instagram',
    username: 'conversai.paris',
    account_id: '17841456789012345',
    display_name: 'SocialSyncAI Paris',
    profile_url: 'https://instagram.com/conversai.paris',
    access_token: 'demo-token',
    refresh_token: 'demo-refresh',
    token_expires_at: new Date(Date.now() + 86400_000 * 30).toISOString(),
    is_active: true,
    user_id: 'demo-user',
    created_at: new Date(Date.now() - 86400_000 * 120).toISOString(),
    updated_at: new Date().toISOString(),
    status: 'connected',
    status_message: 'Active',
  },
  {
    id: 'acc-whatsapp-latam',
    platform: 'whatsapp',
    username: '+34630981254',
    account_id: '551987654321',
    display_name: 'SocialSyncAI Latam',
    profile_url: 'https://wa.me/34630981254',
    access_token: 'demo-token',
    refresh_token: 'demo-refresh',
    token_expires_at: new Date(Date.now() + 86400_000 * 15).toISOString(),
    is_active: true,
    user_id: 'demo-user',
    created_at: new Date(Date.now() - 86400_000 * 90).toISOString(),
    updated_at: new Date().toISOString(),
    status: 'connected',
    status_message: 'Connected',
  },
  {
    id: 'acc-instagram-private',
    platform: 'instagram',
    username: 'club.conversai',
    account_id: '17845678901234567',
    display_name: 'SocialSyncAI Private Club',
    profile_url: 'https://instagram.com/club.conversai',
    access_token: 'demo-token',
    refresh_token: 'demo-refresh',
    token_expires_at: new Date(Date.now() - 86400_000 * 2).toISOString(),
    is_active: false,
    user_id: 'demo-user',
    created_at: new Date(Date.now() - 86400_000 * 200).toISOString(),
    updated_at: new Date(Date.now() - 86400_000 * 2).toISOString(),
    status: 'expired',
    status_message: 'Token expired',
  },
];

export const demoStats = {
  conversations: {
    automated: 348,
    escalated: 42,
    averageHandleTime: '6m 15s',
  },
  knowledge: {
    totalDocuments: demoKnowledgeBase.documents.length,
    indexed: demoKnowledgeBase.documents.filter(doc => doc.status === 'indexed')
      .length,
    processing: demoKnowledgeBase.documents.filter(
      doc => doc.status === 'processing'
    ).length,
    errors: demoKnowledgeBase.documents.filter(doc => doc.status === 'error')
      .length,
  },
  faq: {
    total: demoFaq.entries.length,
    active: demoFaq.entries.filter(faq => faq.is_active).length,
    inactive: demoFaq.entries.filter(faq => !faq.is_active).length,
    totalQuestions: demoFaq.entries.reduce(
      (total, faq) => total + faq.questions.length,
      0
    ),
  },
};

export const formatDemoTime = (dateString: string) => {
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) {
    return dateString;
  }

  return `${date.getHours().toString().padStart(2, '0')}:${date
    .getMinutes()
    .toString()
    .padStart(2, '0')} ${date.getDate().toString().padStart(2, '0')}/${(
    date.getMonth() + 1
  )
    .toString()
    .padStart(2, '0')}`;
};
