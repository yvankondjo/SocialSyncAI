-- Migration pour ajouter l'idempotence aux messages WhatsApp/Instagram
-- OBLIGATOIRE pour éviter les doublons de webhooks

-- 1. Nettoyer d'abord les éventuels doublons existants (si ils existent)
WITH duplicates AS (
    SELECT 
        external_message_id,
        MIN(id) as keep_id
    FROM conversation_messages 
    WHERE external_message_id IS NOT NULL 
    AND external_message_id != ''
    GROUP BY external_message_id 
    HAVING COUNT(*) > 1
)
DELETE FROM conversation_messages 
WHERE external_message_id IN (
    SELECT external_message_id FROM duplicates
) 
AND id NOT IN (
    SELECT keep_id FROM duplicates
);

-- 2. Ajouter la contrainte UNIQUE sur external_message_id
ALTER TABLE conversation_messages 
ADD CONSTRAINT unique_external_message_id UNIQUE (external_message_id);

-- 3. Ajouter un index pour performance (déjà inclus par UNIQUE, mais explicite)
-- CREATE INDEX CONCURRENTLY idx_conversation_messages_external_id ON conversation_messages(external_message_id);

-- 4. Optionnel : Ajouter colonnes pour traçabilité webhook
ALTER TABLE conversation_messages 
ADD COLUMN webhook_received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN webhook_payload JSONB DEFAULT '{}';

-- 5. Index pour recherche rapide des messages non traités
CREATE INDEX idx_conversation_messages_webhook_received ON conversation_messages(webhook_received_at);

-- 6. Commentaire explicatif
COMMENT ON CONSTRAINT unique_external_message_id ON conversation_messages IS 
'Garantit l''idempotence - empêche les doublons de webhooks WhatsApp/Instagram';

COMMENT ON COLUMN conversation_messages.webhook_received_at IS 
'Timestamp de réception du webhook (pour audit et debugging)';

COMMENT ON COLUMN conversation_messages.webhook_payload IS 
'Payload complet du webhook reçu (pour audit et debugging)';
