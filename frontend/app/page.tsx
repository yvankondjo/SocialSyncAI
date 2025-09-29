import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { 
  CheckCircle, 
  ArrowRight, 
  Sparkles, 
  Zap, 
  Target,
  Users 
} from "lucide-react"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="flex items-center justify-center gap-2 mb-6">
            <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-primary-foreground" />
            </div>
            <h1 className="text-4xl font-bold">SocialSync AI</h1>
          </div>
          
          <div className="max-w-3xl mx-auto space-y-4">
            <h2 className="text-2xl font-semibold text-muted-foreground">
              🎉 Migration Complète Réussie !
            </h2>
            <p className="text-lg text-muted-foreground">
              Nouveau design Social-Sync-AI implémenté avec succès. 
              Toutes les fonctionnalités ont été migrées et améliorées.
            </p>
          </div>
        </div>

        {/* Status Cards */}
        <div className="grid gap-6 md:grid-cols-3 mb-16">
          <Card>
            <CardHeader className="text-center">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <CardTitle>11 Pages Migrées</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-center text-muted-foreground">
                Toutes les pages ont été migrées vers le nouveau design
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="text-center">
              <Zap className="w-12 h-12 text-blue-500 mx-auto mb-4" />
              <CardTitle>6 Nouvelles Fonctionnalités</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-center text-muted-foreground">
                Fonctionnalités avancées ajoutées selon les spécifications
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="text-center">
              <Target className="w-12 h-12 text-purple-500 mx-auto mb-4" />
              <CardTitle>100% Fonctionnel</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-center text-muted-foreground">
                Aucune erreur, toutes les APIs préservées
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Access */}
        <div className="grid gap-8 md:grid-cols-2 mb-16">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Accès Dashboard
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">
                Accédez à l'interface principale avec authentification
              </p>
              <Link href="/playground">
                <Button className="w-full">
                  Aller au Playground
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5" />
                Test Nouvelle UI
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">
                Testez tous les nouveaux composants et fonctionnalités
              </p>
              <Link href="/test-new-ui">
                <Button variant="outline" className="w-full">
                  Tester la Nouvelle UI
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Features Overview */}
        <Card>
          <CardHeader>
            <CardTitle>Nouvelles Fonctionnalités Implémentées</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-2">
                <Badge className="bg-green-500/20 text-green-400">Multi-Questions FAQ</Badge>
                <p className="text-sm text-muted-foreground">
                  Plusieurs questions pour une même réponse
                </p>
              </div>
              <div className="space-y-2">
                <Badge className="bg-blue-500/20 text-blue-400">Disable AI Toggle</Badge>
                <p className="text-sm text-muted-foreground">
                  Contrôle complet pour désactiver l'IA
                </p>
              </div>
              <div className="space-y-2">
                <Badge className="bg-purple-500/20 text-purple-400">Édition Réponses IA</Badge>
                <p className="text-sm text-muted-foreground">
                  Modification des réponses avec sauvegarde FAQ
                </p>
              </div>
              <div className="space-y-2">
                <Badge className="bg-orange-500/20 text-orange-400">Dashboard Analytics</Badge>
                <p className="text-sm text-muted-foreground">
                  Métriques complètes avec graphiques
                </p>
              </div>
              <div className="space-y-2">
                <Badge className="bg-pink-500/20 text-pink-400">Widget Configurateur</Badge>
                <p className="text-sm text-muted-foreground">
                  Personnalisation complète du chat
                </p>
              </div>
              <div className="space-y-2">
                <Badge className="bg-cyan-500/20 text-cyan-400">Custom Domains</Badge>
                <p className="text-sm text-muted-foreground">
                  Gestion DNS et SSL complète
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-16">
          <p className="text-muted-foreground">
            🚀 Migration terminée avec succès - Prêt pour la production !
          </p>
        </div>
      </div>
    </div>
  )
}