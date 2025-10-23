/**
 * ModelSelector Component
 * Dropdown for selecting AI model
 */

'use client';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { ChevronDown, Sparkles, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Model {
  id: string;
  name: string;
  description: string;
  badge?: string;
}

const AVAILABLE_MODELS: Model[] = [
  {
    id: 'openai/gpt-4o',
    name: 'GPT-4o',
    description: 'Most capable model, best for complex tasks',
    badge: 'Recommended',
  },
  {
    id: 'openai/gpt-4o-mini',
    name: 'GPT-4o Mini',
    description: 'Fast and efficient, great for most tasks',
  },
  {
    id: 'anthropic/claude-3.5-sonnet',
    name: 'Claude 3.5 Sonnet',
    description: 'Excellent for creative content',
  },
  {
    id: 'anthropic/claude-3-haiku',
    name: 'Claude 3 Haiku',
    description: 'Fast responses, good for quick tasks',
  },
];

interface ModelSelectorProps {
  selectedModel: string;
  onModelChange: (modelId: string) => void;
  disabled?: boolean;
}

export function ModelSelector({
  selectedModel,
  onModelChange,
  disabled = false,
}: ModelSelectorProps) {
  const currentModel = AVAILABLE_MODELS.find((m) => m.id === selectedModel) || AVAILABLE_MODELS[0];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          disabled={disabled}
          className="gap-2 font-normal"
        >
          <Sparkles className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">{currentModel.name}</span>
          <span className="sm:hidden">Model</span>
          <ChevronDown className="h-3.5 w-3.5 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel className="text-xs text-muted-foreground font-normal">
          Select AI Model
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {AVAILABLE_MODELS.map((model) => {
          const isSelected = model.id === selectedModel;
          return (
            <DropdownMenuItem
              key={model.id}
              onClick={() => onModelChange(model.id)}
              className={cn(
                'flex items-start gap-3 p-3 cursor-pointer',
                isSelected && 'bg-accent'
              )}
            >
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{model.name}</span>
                  {model.badge && (
                    <span className="text-xs px-1.5 py-0.5 rounded-md bg-primary/10 text-primary font-medium">
                      {model.badge}
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {model.description}
                </p>
              </div>
              {isSelected && (
                <Check className="h-4 w-4 text-primary flex-shrink-0 mt-0.5" />
              )}
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
