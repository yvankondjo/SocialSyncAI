-- ==================== MODIFICATIONS POUR WEBHOOKS MULTI-TENANT ====================

-- 1. Étendre l'enum des plateformes si nécessaire
ALTER TYPE social_platform ADD VALUE IF NOT EXISTS 'whatsapp_business';

-- 2. Modifier la table social_accounts pour les webhooks WhatsApp/Instagram
ALTER TABLE social_accounts 
    ADD COLUMN IF NOT EXISTS phone_number_id VARCHAR(100), -- ID unique Meta pour WhatsApp
    ADD COLUMN IF NOT EXISTS page_id VARCHAR(100), -- ID de page pour Instagram/Facebook
    ADD COLUMN IF NOT EXISTS app_secret VARCHAR(255), -- App Secret Meta (même pour tous)
    ADD COLUMN IF NOT EXISTS verify_token VARCHAR(255), -- Token de vérification webhook
    ADD COLUMN IF NOT EXISTS webhook_url VARCHAR(500), -- URL webhook personnalisée (optionnel)
    ADD COLUMN IF NOT EXISTS business_name VARCHAR(255), -- Nom de l'entreprise
    ADD COLUMN IF NOT EXISTS display_phone_number VARCHAR(20), -- Numéro affiché (+33...)
    ADD COLUMN IF NOT EXISTS webhook_events TEXT[], -- Événements webhook activés
    ADD COLUMN IF NOT EXISTS webhook_status VARCHAR(50) DEFAULT 'inactive', -- active, inactive, error
    ADD COLUMN IF NOT EXISTS last_webhook_at TIMESTAMP WITH TIME ZONE, -- Dernier webhook reçu
    ADD COLUMN IF NOT EXISTS webhook_metadata JSONB DEFAULT '{}'; -- Métadonnées webhook

-- 3. Contraintes et index pour le routage rapide
-- Index unique sur phone_number_id pour WhatsApp (clé de routage)
CREATE UNIQUE INDEX IF NOT EXISTS idx_social_accounts_phone_number_id 
    ON social_accounts(phone_number_id) 
    WHERE phone_number_id IS NOT NULL;

-- Index unique sur page_id pour Instagram (clé de routage)  
CREATE UNIQUE INDEX IF NOT EXISTS idx_social_accounts_page_id
    ON social_accounts(page_id)
    WHERE page_id IS NOT NULL;

-- Index pour le statut des webhooks
CREATE INDEX IF NOT EXISTS idx_social_accounts_webhook_status 
    ON social_accounts(webhook_status);

-- Index pour les plateformes avec webhooks
CREATE INDEX IF NOT EXISTS idx_social_accounts_platform_webhook 
    ON social_accounts(platform) 
    WHERE platform IN ('whatsapp', 'whatsapp_business', 'instagram');

-- 4. Contraintes de cohérence
-- WhatsApp Business doit avoir un phone_number_id
ALTER TABLE social_accounts 
    ADD CONSTRAINT IF NOT EXISTS chk_whatsapp_phone_number_id 
    CHECK (
        (platform IN ('whatsapp', 'whatsapp_business') AND phone_number_id IS NOT NULL) 
        OR platform NOT IN ('whatsapp', 'whatsapp_business')
    );

-- Instagram doit avoir un page_id
ALTER TABLE social_accounts 
    ADD CONSTRAINT IF NOT EXISTS chk_instagram_page_id 
    CHECK (
        (platform = 'instagram' AND page_id IS NOT NULL) 
        OR platform != 'instagram'
    );

-- 5. Table pour l'historique des webhooks (debugging et monitoring)
CREATE TABLE IF NOT EXISTS webhook_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    social_account_id UUID REFERENCES social_accounts(id) ON DELETE CASCADE,
    platform social_platform NOT NULL,
    webhook_type VARCHAR(50) NOT NULL, -- messages, deliveries, comments, mentions
    payload JSONB NOT NULL, -- Payload complet du webhook
    status VARCHAR(50) DEFAULT 'received', -- received, processed, error
    processing_time_ms INTEGER, -- Temps de traitement en millisecondes
    error_message TEXT, -- Message d'erreur si échec
    external_message_id VARCHAR(255), -- ID du message sur la plateforme
    customer_identifier VARCHAR(255), -- Numéro/username qui a envoyé
    user_id UUID REFERENCES users(id), -- Utilisateur concerné (dénormalisé pour perfs)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour webhook_logs
CREATE INDEX IF NOT EXISTS idx_webhook_logs_social_account 
    ON webhook_logs(social_account_id);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_platform 
    ON webhook_logs(platform);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_created_at 
    ON webhook_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_status 
    ON webhook_logs(status);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_user_id 
    ON webhook_logs(user_id);

-- 6. Fonctions utilitaires pour le routage

-- Fonction pour récupérer un utilisateur WhatsApp par phone_number_id
CREATE OR REPLACE FUNCTION get_whatsapp_user_by_phone_number_id(p_phone_number_id VARCHAR)
RETURNS TABLE (
    user_id UUID,
    social_account_id UUID,
    access_token TEXT,
    app_secret VARCHAR,
    verify_token VARCHAR,
    display_phone_number VARCHAR,
    business_name VARCHAR,
    username VARCHAR,
    is_active BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sa.user_id,
        sa.id as social_account_id,
        sa.access_token,
        sa.app_secret,
        sa.verify_token,
        sa.display_phone_number,
        sa.business_name,
        sa.username,
        sa.is_active
    FROM social_accounts sa
    WHERE sa.phone_number_id = p_phone_number_id
    AND sa.platform IN ('whatsapp', 'whatsapp_business')
    AND sa.is_active = true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Fonction pour récupérer un utilisateur Instagram par account_id (v23.0)
CREATE OR REPLACE FUNCTION get_instagram_user_by_business_account_id(p_account_id VARCHAR)
RETURNS TABLE (
    user_id UUID,
    social_account_id UUID,
    instagram_business_account_id VARCHAR,
    access_token TEXT,
    app_secret VARCHAR,
    verify_token VARCHAR,
    display_name VARCHAR,
    username VARCHAR,
    is_active BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sa.user_id,
        sa.id as social_account_id,
        sa.account_id as instagram_business_account_id,
        sa.access_token,
        sa.app_secret,
        sa.verify_token,
        sa.display_name,
        sa.username,
        sa.is_active
    FROM social_accounts sa
    WHERE sa.account_id = p_account_id
    AND sa.platform = 'instagram'
    AND sa.is_active = true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Maintenir la fonction page_id pour compatibilité (si encore nécessaire)
CREATE OR REPLACE FUNCTION get_instagram_user_by_page_id(p_page_id VARCHAR)
RETURNS TABLE (
    user_id UUID,
    social_account_id UUID,
    access_token TEXT,
    app_secret VARCHAR,
    verify_token VARCHAR,
    display_name VARCHAR,
    username VARCHAR,
    is_active BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sa.user_id,
        sa.id as social_account_id,
        sa.access_token,
        sa.app_secret,
        sa.verify_token,
        sa.display_name,
        sa.username,
        sa.is_active
    FROM social_accounts sa
    WHERE sa.page_id = p_page_id
    AND sa.platform = 'instagram'
    AND sa.is_active = true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Fonction pour logger un webhook
CREATE OR REPLACE FUNCTION log_webhook(
    p_social_account_id UUID,
    p_platform social_platform,
    p_webhook_type VARCHAR,
    p_payload JSONB,
    p_external_message_id VARCHAR DEFAULT NULL,
    p_customer_identifier VARCHAR DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    webhook_log_id UUID;
    account_user_id UUID;
BEGIN
    -- Récupérer l'user_id depuis social_account_id
    SELECT user_id INTO account_user_id 
    FROM social_accounts 
    WHERE id = p_social_account_id;
    
    -- Insérer le log
    INSERT INTO webhook_logs (
        social_account_id,
        platform,
        webhook_type,
        payload,
        external_message_id,
        customer_identifier,
        user_id,
        status
    ) VALUES (
        p_social_account_id,
        p_platform,
        p_webhook_type,
        p_payload,
        p_external_message_id,
        p_customer_identifier,
        account_user_id,
        'received'
    ) RETURNING id INTO webhook_log_id;
    
    -- Mettre à jour last_webhook_at
    UPDATE social_accounts 
    SET last_webhook_at = NOW()
    WHERE id = p_social_account_id;
    
    RETURN webhook_log_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Fonction pour marquer un webhook comme traité
CREATE OR REPLACE FUNCTION mark_webhook_processed(
    p_webhook_log_id UUID,
    p_processing_time_ms INTEGER DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
) RETURNS void AS $$
BEGIN
    UPDATE webhook_logs 
    SET 
        status = CASE WHEN p_error_message IS NULL THEN 'processed' ELSE 'error' END,
        processing_time_ms = p_processing_time_ms,
        error_message = p_error_message
    WHERE id = p_webhook_log_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 7. Vues utiles pour le monitoring

-- Vue des comptes avec webhooks actifs
CREATE OR REPLACE VIEW active_webhook_accounts AS
SELECT 
    sa.id,
    sa.user_id,
    u.email,
    sa.platform,
    sa.phone_number_id,
    sa.page_id,
    sa.business_name,
    sa.display_name,
    sa.webhook_status,
    sa.last_webhook_at,
    sa.webhook_events,
    sa.created_at
FROM social_accounts sa
JOIN users u ON u.id = sa.user_id
WHERE sa.platform IN ('whatsapp', 'whatsapp_business', 'instagram')
AND sa.is_active = true
ORDER BY sa.last_webhook_at DESC NULLS LAST;

-- Vue des statistiques de webhooks par utilisateur
CREATE OR REPLACE VIEW webhook_stats_by_user AS
SELECT 
    sa.user_id,
    u.email,
    sa.platform,
    sa.business_name,
    COUNT(*) as total_webhooks,
    COUNT(*) FILTER (WHERE wl.status = 'processed') as processed_webhooks,
    COUNT(*) FILTER (WHERE wl.status = 'error') as error_webhooks,
    AVG(wl.processing_time_ms) as avg_processing_time_ms,
    MAX(wl.created_at) as last_webhook_at
FROM social_accounts sa
JOIN users u ON u.id = sa.user_id
LEFT JOIN webhook_logs wl ON wl.social_account_id = sa.id
WHERE sa.platform IN ('whatsapp', 'whatsapp_business', 'instagram')
GROUP BY sa.user_id, u.email, sa.platform, sa.business_name
ORDER BY total_webhooks DESC;

-- 8. RLS pour webhook_logs
ALTER TABLE webhook_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their webhook logs" ON webhook_logs FOR SELECT USING (
    auth.uid() = user_id
);

CREATE POLICY "System can manage webhook logs" ON webhook_logs FOR ALL USING (
    -- Cette politique permettra à l'API d'insérer des logs
    -- En production, utiliser un rôle système spécifique
    true
);

-- 9. Triggers pour mise à jour automatique

-- Trigger pour mettre à jour updated_at sur social_accounts
CREATE TRIGGER update_social_accounts_updated_at 
    BEFORE UPDATE ON social_accounts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger pour mettre à jour webhook_status automatiquement
CREATE OR REPLACE FUNCTION update_webhook_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Si un webhook vient d'être reçu, marquer comme actif
    IF NEW.last_webhook_at > COALESCE(OLD.last_webhook_at, '1970-01-01'::timestamp) THEN
        NEW.webhook_status = 'active';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_webhook_status
    BEFORE UPDATE ON social_accounts
    FOR EACH ROW
    WHEN (NEW.last_webhook_at IS DISTINCT FROM OLD.last_webhook_at)
    EXECUTE FUNCTION update_webhook_status();

-- 10. Données de test pour le développement (optionnel)
-- À commenter/supprimer en production

/*
-- Exemple d'utilisateur WhatsApp pour les tests
INSERT INTO social_accounts (
    platform,
    account_id,
    username,
    display_name,
    phone_number_id,
    access_token,
    app_secret,
    verify_token,
    business_name,
    display_phone_number,
    webhook_events,
    webhook_status,
    user_id,
    is_active
) VALUES (
    'whatsapp_business',
    'wa_683178638221369',
    'restaurant_pierre',
    'Restaurant Chez Pierre',
    '683178638221369',
    'EAAI565Fri...', -- Token factice
    'abc123def456', -- App secret factice
    'my_verify_token_123',
    'Restaurant Chez Pierre',
    '+33765540003',
    ARRAY['messages', 'message_deliveries', 'message_reads'],
    'active',
    (SELECT id FROM users LIMIT 1), -- Premier utilisateur
    true
) ON CONFLICT (platform, account_id) DO NOTHING;
*/

COMMENT ON TABLE webhook_logs IS 'Historique de tous les webhooks reçus pour debugging et monitoring';
COMMENT ON FUNCTION get_whatsapp_user_by_phone_number_id IS 'Fonction de routage pour les webhooks WhatsApp basée sur phone_number_id';
COMMENT ON FUNCTION get_instagram_user_by_page_id IS 'Fonction de routage pour les webhooks Instagram basée sur page_id';
COMMENT ON FUNCTION log_webhook IS 'Logger un webhook reçu avec métadonnées';
COMMENT ON VIEW active_webhook_accounts IS 'Vue des comptes avec webhooks actifs pour monitoring';
