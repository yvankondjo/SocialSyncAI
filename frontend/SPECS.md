# SocialSync Frontend – Spécifications & Conventions

## Objectif
Application Next.js 14 (App Router) avec Sidebar persistante, Auth Supabase, données via API backend, UI avec Tailwind v4 + shadcn/ui.

## Architecture
```
app/
  ├─ auth/                 # pages publiques
  ├─ dashboard/            # espace authentifié avec sidebar persistante
  │   ├─ layout.tsx        # <Sidebar/> + <AuthGuard/> + {children}
  │   ├─ page.tsx          # Dashboard principal
  │   ├─ inbox/page.tsx
  │   ├─ calendar/page.tsx
  │   ├─ media/page.tsx
  │   ├─ social-accounts/page.tsx
  │   └─ ai-studio/
  │       ├─ layout.tsx
  │       ├─ page.tsx (redirect -> prompt-tuning)
  │       ├─ prompt-tuning/page.tsx
  │       ├─ data/page.tsx
  │       └─ qa-examples/page.tsx
components/
  ├─ sidebar/Sidebar.tsx, NavItem.tsx
  ├─ dashboard-page.tsx, inbox-page.tsx, calendar-page.tsx, media-page.tsx,
  ├─ social-accounts-page.tsx, design-studio-page.tsx
hooks/
  ├─ useAuth.ts, useSidebarStore.ts
lib/
  ├─ api.ts, supabase.ts
```

## Sidebar persistante
- Etats: expanded (~280px), collapsed (~72px), mobile (Sheet)
- Persistance: Zustand + localStorage (`socialsync-sidebar`)
- Accessibilité: `aria-label`, `aria-current`, focus visible
- Tooltips shadcn/ui en mode collapsed
- Active state: `usePathname()`, match strict et préfixe pour sous-routes
- Transitions: `transition-all duration-300 ease-in-out`

## Routing
- Espace privé sous `/dashboard/*`
- Page d’accueil `/` -> redirect vers `/dashboard`
- AI Studio: `/dashboard/ai-studio/*` avec layout dédié

## Auth
- Supabase (OAuth Google) via `useAuth()` + `AuthGuard`
- Redirection automatique vers `/auth` si non authentifié
- Déconnexion via menu utilisateur (Sidebar / Dropdown)

## Données
- `lib/api.ts`: client fetch avec Bearer JWT (token Supabase)
- Services: SocialAccounts, Conversations, Analytics
- Dashboard calcule KPIs depuis les vraies API (conversations + analytics)

## UI
- Tailwind v4 + shadcn/ui
- Icônes: `lucide-react`
- Palette SocialSync (tokens Tailwind existants)
- Transitions UI sobres, pas de layout shift

## Performance & DX
- Hot reload optimisé (`next.config.mjs`: watchOptions/poll + `--turbo`)
- Éviter console.log en prod; garder uniquement logs utiles
- Imports propres, pas d’imports inutilisés

## Responsiveness
- ≥ lg: Sidebar fixe
- < lg: Sheet/Drawer avec bouton hamburger

## Conventions de code
- Noms explicites (Clean Code)
- Types explicites pour API publiques
- Limiter l’imbrication, early-returns, gestion d’erreurs claire
- Pas de commentaires superflus, seulement “pourquoi”

## Tests (à prévoir)
- Vérifier 3 états de Sidebar + mobile
- Vérifier persistance état collapsed
- Vérifier redirections AuthGuard

## Backlog (prochaines étapes)
- Hover-expand temporaire en mode collapsed
- Breadcrumbs dans les modules profonds
- i18n (next-intl) en/fr
- E2E Playwright des flux critiques
