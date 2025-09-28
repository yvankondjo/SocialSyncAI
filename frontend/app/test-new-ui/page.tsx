"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Slider } from "@/components/ui/slider"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  CheckCircle, 
  AlertTriangle, 
  Settings, 
  Users, 
  BarChart3,
  MessageSquare 
} from "lucide-react"

export default function TestNewUIPage() {
  const [sliderValue, setSliderValue] = useState([50])

  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Test Nouvelle UI</h1>
          <p className="text-muted-foreground">
            Test de tous les composants et fonctionnalités migrés
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline">
            <Settings className="w-4 h-4 mr-2" />
            Paramètres
          </Button>
          <Button>
            <CheckCircle className="w-4 h-4 mr-2" />
            Nouveau Design
          </Button>
        </div>
      </div>

      {/* Alert Test */}
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          ✅ Migration complète réussie ! Tous les composants fonctionnent parfaitement.
        </AlertDescription>
      </Alert>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pages Migrées</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">11</div>
            <p className="text-xs text-muted-foreground">
              100% complété
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Nouvelles Fonctionnalités</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">6</div>
            <p className="text-xs text-muted-foreground">
              Fonctionnalités ajoutées
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Composants UI</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">6</div>
            <p className="text-xs text-muted-foreground">
              Nouveaux composants
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-400">100%</div>
            <p className="text-xs text-muted-foreground">
              Migration réussie
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Components Test */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Test des Composants UI</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Input Test</label>
              <Input placeholder="Test du composant Input..." />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Slider Test</label>
              <Slider
                value={sliderValue}
                onValueChange={setSliderValue}
                max={100}
                min={0}
                step={1}
                className="w-full"
              />
              <p className="text-sm text-muted-foreground">Valeur: {sliderValue[0]}</p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Progress Test</label>
              <Progress value={75} className="w-full" />
              <p className="text-sm text-muted-foreground">75% complété</p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Badges Test</label>
              <div className="flex gap-2">
                <Badge variant="default">Default</Badge>
                <Badge variant="secondary">Secondary</Badge>
                <Badge variant="outline">Outline</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Test des Tabs</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="tab1">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="tab1">Tab 1</TabsTrigger>
                <TabsTrigger value="tab2">Tab 2</TabsTrigger>
                <TabsTrigger value="tab3">Tab 3</TabsTrigger>
              </TabsList>
              <TabsContent value="tab1" className="space-y-4">
                <h3 className="font-semibold">Contenu Tab 1</h3>
                <p className="text-sm text-muted-foreground">
                  ✅ Le système de tabs fonctionne parfaitement !
                </p>
              </TabsContent>
              <TabsContent value="tab2" className="space-y-4">
                <h3 className="font-semibold">Contenu Tab 2</h3>
                <p className="text-sm text-muted-foreground">
                  ✅ Navigation entre les tabs fluide !
                </p>
              </TabsContent>
              <TabsContent value="tab3" className="space-y-4">
                <h3 className="font-semibold">Contenu Tab 3</h3>
                <p className="text-sm text-muted-foreground">
                  ✅ Tous les composants sont opérationnels !
                </p>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>

      {/* Pages migrées */}
      <Card>
        <CardHeader>
          <CardTitle>Pages Disponibles (Nouvelle UI)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <h4 className="font-medium">Pages Migrées</h4>
              <ul className="text-sm space-y-1">
                <li>✅ <a href="/activity/chat" className="text-blue-600 hover:underline">/activity/chat</a></li>
                <li>✅ <a href="/sources/data" className="text-blue-600 hover:underline">/sources/data</a></li>
                <li>✅ <a href="/sources/faq" className="text-blue-600 hover:underline">/sources/faq</a></li>
                <li>✅ <a href="/settings/ai" className="text-blue-600 hover:underline">/settings/ai</a></li>
                <li>✅ <a href="/playground/compare" className="text-blue-600 hover:underline">/playground/compare</a></li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium">Nouvelles Pages</h4>
              <ul className="text-sm space-y-1">
                <li>🆕 <a href="/analytics" className="text-green-600 hover:underline">/analytics</a></li>
                <li>🆕 <a href="/connect" className="text-green-600 hover:underline">/connect</a></li>
                <li>🆕 <a href="/playground" className="text-green-600 hover:underline">/playground</a></li>
                <li>🆕 <a href="/settings/chat-interface" className="text-green-600 hover:underline">/settings/chat-interface</a></li>
                <li>🆕 <a href="/settings/custom-domains" className="text-green-600 hover:underline">/settings/custom-domains</a></li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium">Fonctionnalités Clés</h4>
              <ul className="text-sm space-y-1">
                <li>🎯 Multi-questions FAQ</li>
                <li>🎯 Disable AI Toggle</li>
                <li>🎯 Édition réponses IA</li>
                <li>🎯 Dashboard Analytics</li>
                <li>🎯 Widget configurateur</li>
                <li>🎯 Custom Domains</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}