"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { RefreshCw, ChevronDown } from "lucide-react"
import { type MonitoringRules } from "@/lib/api"

interface MonitoringRulesPanelProps {
  rules: MonitoringRules
  onUpdate: (rules: MonitoringRules) => Promise<void>
  isSyncing: boolean
  onSync: () => Promise<void>
}

export function MonitoringRulesPanel({
  rules,
  onUpdate,
  isSyncing,
  onSync
}: MonitoringRulesPanelProps) {
  const [isOpen, setIsOpen] = useState(true)
  const [localRules, setLocalRules] = useState(rules)
  const [isUpdating, setIsUpdating] = useState(false)

  const handleUpdate = async () => {
    setIsUpdating(true)
    try {
      await onUpdate(localRules)
    } finally {
      setIsUpdating(false)
    }
  }

  const hasChanges =
    localRules.auto_monitor_enabled !== rules.auto_monitor_enabled ||
    localRules.auto_monitor_count !== rules.auto_monitor_count ||
    localRules.monitoring_duration_days !== rules.monitoring_duration_days ||
    localRules.ai_enabled_for_comments !== rules.ai_enabled_for_comments

  return (
    <Card className="bg-card border">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <button
            className="w-full p-4 flex items-center justify-between
                       hover:bg-muted/50 transition-colors rounded-lg
                       focus-visible:outline focus-visible:outline-2
                       focus-visible:outline-ring focus-visible:outline-offset-2"
            aria-expanded={isOpen}
            aria-label="Toggle monitoring settings"
          >
            <h3 className="font-semibold text-base">Monitoring Settings</h3>
            <ChevronDown
              className={`w-5 h-5 text-muted-foreground transition-transform duration-200 ${
                isOpen ? 'rotate-180' : ''
              }`}
              aria-hidden="true"
            />
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-4 pb-4 space-y-4">
            {/* Auto-monitor toggle */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-sm font-medium">Auto-monitor new posts</Label>
                <p id="auto-monitor-description" className="text-xs text-muted-foreground">
                  Automatically enable monitoring for new scheduled posts
                </p>
              </div>
              <Switch
                checked={localRules.auto_monitor_enabled}
                onCheckedChange={(checked) =>
                  setLocalRules(prev => ({ ...prev, auto_monitor_enabled: checked }))
                }
                aria-label="Enable automatic monitoring for new posts"
                aria-describedby="auto-monitor-description"
              />
            </div>

            {/* AI for comments toggle */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-sm font-medium">AI auto-replies on comments</Label>
                <p id="ai-comments-description" className="text-xs text-muted-foreground">
                  Enable AI to automatically respond to comments on monitored posts
                </p>
              </div>
              <Switch
                checked={localRules.ai_enabled_for_comments ?? true}
                onCheckedChange={(checked) =>
                  setLocalRules(prev => ({ ...prev, ai_enabled_for_comments: checked }))
                }
                aria-label="Enable AI auto-replies for comments"
                aria-describedby="ai-comments-description"
              />
            </div>

            {/* Monitor last X posts slider */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">Monitor last posts</Label>
                <span className="text-sm font-semibold text-primary">
                  {localRules.auto_monitor_count} posts
                </span>
              </div>
              <Slider
                value={[localRules.auto_monitor_count]}
                onValueChange={(value) =>
                  setLocalRules(prev => ({ ...prev, auto_monitor_count: value[0] }))
                }
                min={1}
                max={20}
                step={1}
                className="w-full"
                aria-label={`Monitor last ${localRules.auto_monitor_count} posts`}
                aria-valuetext={`${localRules.auto_monitor_count} posts`}
              />
              <p className="text-xs text-muted-foreground">
                Number of recent posts to keep under monitoring (1-20)
              </p>
            </div>

            {/* Monitoring duration input */}
            <div className="space-y-2">
              <Label htmlFor="duration" className="text-sm font-medium">
                Monitoring duration (days)
              </Label>
              <Input
                id="duration"
                type="number"
                min={1}
                max={30}
                value={localRules.monitoring_duration_days}
                onChange={(e) =>
                  setLocalRules(prev => ({
                    ...prev,
                    monitoring_duration_days: Math.max(1, Math.min(30, parseInt(e.target.value) || 7))
                  }))
                }
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                How many days to monitor each post for comments (1-30)
              </p>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-2 pt-2">
              <Button
                onClick={onSync}
                disabled={isSyncing}
                variant="default"
                className="flex-1"
                aria-label={isSyncing ? "Syncing Instagram posts" : "Sync Instagram posts"}
              >
                {isSyncing ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" aria-hidden="true" />
                    Syncing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2" aria-hidden="true" />
                    Sync Instagram Posts
                  </>
                )}
              </Button>

              {hasChanges && (
                <Button
                  onClick={handleUpdate}
                  disabled={isUpdating}
                  variant="outline"
                  aria-label={isUpdating ? "Saving settings" : "Save monitoring settings"}
                >
                  {isUpdating ? 'Saving...' : 'Save Settings'}
                </Button>
              )}
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  )
}
