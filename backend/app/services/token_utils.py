"""
Token Utils - Module centralisé pour la gestion des tokens
============================================================

Ce module fournit des utilitaires pour:
- Comptage précis des tokens avec tiktoken
- Mapping des context windows des LLMs
- Vérification des limites de messages

Utilisé par: rag_agent.py, response_manager.py, et autres services
"""

import logging
from typing import Dict, List, Any, Union

import tiktoken

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# ENCODAGE TIKTOKEN
# ═══════════════════════════════════════════════════════════════════════════════

# Utiliser cl100k_base - encodage standard pour GPT-4, GPT-3.5-turbo et la plupart des modèles
_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """
    Compte précisément les tokens d'un texte avec tiktoken.
    
    Args:
        text: Le texte à analyser
    
    Returns:
        Nombre exact de tokens
    """
    if not text:
        return 0
    try:
        return len(_ENCODING.encode(text))
    except Exception as e:
        logger.warning(f"Erreur tiktoken, fallback estimation: {e}")
        return len(text) // 4  # Estimation: ~4 chars par token


def count_message_tokens(content: Union[str, List, Dict]) -> int:
    """
    Compte les tokens d'un contenu de message avec overhead de formatage.
    Gère les contenus string, list (multimodal), et dict.
    
    Args:
        content: Contenu du message (str, list ou dict)
    
    Returns:
        Nombre de tokens incluant l'overhead de structure
    """
    # Overhead de structure par message (role, séparateurs, etc.)
    MESSAGE_OVERHEAD = 4
    
    if isinstance(content, str):
        return count_tokens(content) + MESSAGE_OVERHEAD
    
    elif isinstance(content, list):
        # Contenu multimodal (texte + images, etc.)
        total = MESSAGE_OVERHEAD
        for item in content:
            if isinstance(item, str):
                total += count_tokens(item)
            elif isinstance(item, dict):
                # Pour les items dict (ex: {"type": "text", "text": "..."})
                text = item.get("text", "") or str(item)
                total += count_tokens(text)
        return total
    
    elif isinstance(content, dict):
        text = content.get("text", "") or content.get("content", "") or str(content)
        return count_tokens(text) + MESSAGE_OVERHEAD
    
    return MESSAGE_OVERHEAD


def count_messages_tokens(messages: List[Any]) -> int:
    """
    Compte le total des tokens pour une liste de messages LangChain.
    
    Args:
        messages: Liste de messages (HumanMessage, AIMessage, etc.)
    
    Returns:
        Nombre total de tokens
    """
    total = 0
    
    for message in messages:
        # Extraire le contenu
        content = getattr(message, 'content', '')
        total += count_message_tokens(content)
        
        # Role token
        role_map = {
            'HumanMessage': 'user',
            'AIMessage': 'assistant', 
            'SystemMessage': 'system',
            'ToolMessage': 'tool'
        }
        role = role_map.get(message.__class__.__name__, 'user')
        total += count_tokens(role)
        
        # Name si présent
        if hasattr(message, 'name') and message.name:
            total += count_tokens(message.name)
    
    # Tokens de priming pour la réponse
    total += 2
    
    return total


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT WINDOWS DES LLMs - Mise à jour régulière recommandée
# ═══════════════════════════════════════════════════════════════════════════════

MODEL_CONTEXT_WINDOWS: Dict[str, int] = {
    # OpenAI Models
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4-turbo-preview": 128000,
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-3.5-turbo": 16385,
    "gpt-3.5-turbo-16k": 16385,
    "o1": 200000,
    "o1-mini": 128000,
    "o1-preview": 128000,
    "o3-mini": 200000,
    
    # Anthropic Models (via OpenRouter)
    "anthropic/claude-3.5-sonnet": 200000,
    "anthropic/claude-3-5-sonnet-20241022": 200000,
    "anthropic/claude-sonnet-4": 200000,
    "anthropic/claude-3-opus": 200000,
    "anthropic/claude-3-sonnet": 200000,
    "anthropic/claude-3-haiku": 200000,
    "anthropic/claude-2.1": 100000,
    "anthropic/claude-2": 100000,
    "claude-3.5-sonnet": 200000,
    "claude-sonnet-4": 200000,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    
    # Google Models (via OpenRouter)
    "google/gemini-pro": 32768,
    "google/gemini-pro-1.5": 1000000,
    "google/gemini-1.5-pro": 1000000,
    "google/gemini-1.5-flash": 1000000,
    "google/gemini-2.0-flash": 1000000,
    "google/gemini-2.0-pro": 1000000,
    "gemini-pro": 32768,
    "gemini-1.5-pro": 1000000,
    "gemini-1.5-flash": 1000000,
    "gemini-2.0-flash": 1000000,
    
    # Meta Llama Models (via OpenRouter)
    "meta-llama/llama-3.1-405b-instruct": 128000,
    "meta-llama/llama-3.1-70b-instruct": 128000,
    "meta-llama/llama-3.1-8b-instruct": 128000,
    "meta-llama/llama-3.2-90b-vision-instruct": 128000,
    "meta-llama/llama-3.2-11b-vision-instruct": 128000,
    "meta-llama/llama-3.3-70b-instruct": 128000,
    
    # Mistral Models (via OpenRouter)
    "mistralai/mistral-large": 128000,
    "mistralai/mistral-medium": 32768,
    "mistralai/mistral-small": 32768,
    "mistralai/mixtral-8x7b-instruct": 32768,
    "mistralai/mixtral-8x22b-instruct": 65536,
    "mistralai/codestral-latest": 32768,
    
    # xAI Grok Models (via OpenRouter)
    "x-ai/grok-beta": 131072,
    "x-ai/grok-2": 131072,
    "x-ai/grok-2-vision": 32768,
    "x-ai/grok-4-fast:free": 131072,
    "x-ai/grok-4-fast": 131072,
    "xai/grok-beta": 131072,
    
    # Cohere Models
    "cohere/command-r": 128000,
    "cohere/command-r-plus": 128000,
    
    # DeepSeek Models
    "deepseek/deepseek-chat": 64000,
    "deepseek/deepseek-coder": 64000,
    "deepseek/deepseek-r1": 64000,
    
    # Qwen Models
    "qwen/qwen-2.5-72b-instruct": 32768,
    "qwen/qwen-2.5-coder-32b-instruct": 32768,
    
    # OpenRouter specific
    "openrouter/auto": 128000,
}

# Contexte par défaut si modèle non reconnu
DEFAULT_CONTEXT_WINDOW = 8192


def get_model_context_window(model_name: str) -> int:
    """
    Retourne la taille du context window pour un modèle donné.
    
    Args:
        model_name: Nom du modèle (ex: "gpt-4o", "anthropic/claude-3.5-sonnet")
    
    Returns:
        Taille du context window en tokens
    """
    if not model_name:
        return DEFAULT_CONTEXT_WINDOW
    
    # Correspondance exacte
    if model_name in MODEL_CONTEXT_WINDOWS:
        return MODEL_CONTEXT_WINDOWS[model_name]
    
    # Correspondance partielle (pour variantes avec suffixes)
    model_lower = model_name.lower()
    for key, value in MODEL_CONTEXT_WINDOWS.items():
        if key.lower() in model_lower or model_lower in key.lower():
            return value
    
    # Heuristiques basées sur le nom
    if "gpt-4o" in model_lower:
        return 128000
    if "gpt-4" in model_lower:
        return 8192
    if "claude" in model_lower:
        return 200000
    if "gemini" in model_lower:
        return 1000000
    if "llama" in model_lower:
        return 128000
    if "mistral" in model_lower or "mixtral" in model_lower:
        return 32768
    if "grok" in model_lower:
        return 131072
    if "deepseek" in model_lower:
        return 64000
    
    logger.warning(f"Modèle '{model_name}' non reconnu, contexte par défaut: {DEFAULT_CONTEXT_WINDOW}")
    return DEFAULT_CONTEXT_WINDOW


def get_max_input_tokens(model_name: str, ratio: float = 0.90) -> int:
    """
    Retourne le nombre maximum de tokens en entrée (90% du contexte par défaut).
    
    Args:
        model_name: Nom du modèle
        ratio: Pourcentage du contexte à utiliser (défaut: 0.90 = 90%)
    
    Returns:
        Nombre max de tokens en entrée
    """
    context_window = get_model_context_window(model_name)
    return int(context_window * ratio)


def is_message_too_long(token_count: int, model_name: str, ratio: float = 0.90) -> bool:
    """
    Vérifie si un message dépasse la limite de tokens.
    
    Args:
        token_count: Nombre de tokens du message
        model_name: Nom du modèle
        ratio: Pourcentage du contexte à utiliser (défaut: 0.90 = 90%)
    
    Returns:
        True si le message est trop long
    """
    max_tokens = get_max_input_tokens(model_name, ratio)
    return token_count > max_tokens


def get_model_info(model_name: str) -> Dict[str, Any]:
    """
    Retourne les informations complètes sur un modèle.
    
    Args:
        model_name: Nom du modèle
    
    Returns:
        Dict avec context_window, max_input_tokens (90%), etc.
    """
    context_window = get_model_context_window(model_name)
    max_input = int(context_window * 0.90)
    
    return {
        "model": model_name,
        "context_window": context_window,
        "max_input_tokens": max_input,
        "ratio": 0.90,
    }
