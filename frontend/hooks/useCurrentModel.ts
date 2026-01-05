import { useAISettings } from "@/lib/api"

interface AIModel {
  id: string
  name: string
  logoKey: keyof typeof import("@/lib/logos").logos
  description: string
  provider: string
}

const AI_MODELS: AIModel[] = [
  {
    id: "x-ai/grok-4",
    name: "Grok 4",
    logoKey: "grok",
    description: "New generation Grok 4 : quick and contextual responses, optimized for multimodal creativity.",
    provider: "xAI"
  },
  {
    id: "x-ai/grok-4-fast",
    name: "Grok 4 Fast",
    logoKey: "grok",
    description: "Fast version of Grok 4, balancing cost and speed for daily usage.",
    provider: "xAI"
  },
  {
    id: "openai/gpt-4o",
    name: "GPT-4o",
    logoKey: "openai",
    description: "GPT-4o offers high-end OpenAI precision with advanced multimodal reasoning.",
    provider: "OpenAI"
  },
  {
    id: "openai/gpt-4o-mini",
    name: "GPT-4o mini",
    logoKey: "openai",
    description: "Mini version of GPT-4o : excellent text performance at a reduced cost.",
    provider: "OpenAI"
  },
  {
    id: "openai/gpt-5",
    name: "GPT-5",
    logoKey: "openai",
    description: "Featured GPT-5 : extreme contextual depth, designed for critical workloads.",
    provider: "OpenAI"
  },
  {
    id: "openai/gpt-5-mini",
    name: "GPT-5 mini",
    logoKey: "openai",
    description: "Mini variant of GPT-5 : speed and robustness for massive integrations.",
    provider: "OpenAI"
  },
  {
    id: "anthropic/claude-3.5-sonnet",
    name: "Claude 3.5 Sonnet",
    logoKey: "claude",
    description: "Claude 3.5 Sonnet combines style and logic : ideal for assistants and creative content.",
    provider: "Anthropic"
  },
  {
    id: "anthropic/claude-sonnet-4",
    name: "Claude 4 Sonnet",
    logoKey: "claude",
    description: "Claude 4 Sonnet provides reliable reasoning with great tone consistency.",
    provider: "Anthropic"
  },
  {
    id: "anthropic/claude-sonnet-4.5",
    name: "Claude 4.5 Sonnet",
    logoKey: "claude",
    description: "Evolution Sonnet 4.5 : best contextual responses and premium stability.",
    provider: "Anthropic"
  },
  {
    id: "google/gemini-2.5-flash",
    name: "Gemini 2.5 Flash",
    logoKey: "googleGemini",
    description: "Gemini 2.5 Flash : ideal for rapid multimodal responses (text, image, audio).",
    provider: "Google"
  },
  {
    id: "google/gemini-2.5-pro",
    name: "Gemini 2.5 Pro",
    logoKey: "googleGemini",
    description: "Gemini 2.5 Pro : Google's ultra-complete model for analytics and multimedia generation.",
    provider: "Google"
  }
]

export const useCurrentModel = () => {
  const { settings, isLoading } = useAISettings()
  
  const currentModel = AI_MODELS.find(model => model.id === settings?.ai_model)
  
  return {
    currentModel,
    modelId: settings?.ai_model,
    isLoading,
    allModels: AI_MODELS
  }
}
