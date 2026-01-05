export const logos = {
  google: '/logos/google.svg',
  youtube: '/logos/youtube.svg',
  discord: '/logos/discord.svg',
  email: '/logos/email.svg',
  linkedin: '/logos/linkedin.svg',
  facebook: '/logos/facebook.svg',
  whatsapp: '/logos/whatsapp.svg',
  reddit: '/logos/reddit.svg',
  tiktok: '/logos/tiktok.svg',
  twitter: '/logos/twitter.svg',
  instagram: '/logos/instagram.svg',
  all: '/logos/all.svg',
  allChannels: '/logos/all-channels.svg',
  x: '/logos/x.svg',
  // AI Provider Logos
  claude: '/logos/claude-logo.svg',
  openai: '/logos/openai-logo.svg',
  grok: '/logos/XAI-logo.svg',
  googleGemini: '/logos/Google-logo.svg',
  // Navigation logos
  activity: '/logos/logo-activity.svg',
  analytic: '/logos/logo-analytic.svg',
  connect: '/logos/logo-connect.svg',
  playground: '/logos/logo-playground.svg',
  settings: '/logos/logo-settings.svg',
  sources: '/logos/logo-sources.svg',
} as const;

export type LogoKey = keyof typeof logos;
