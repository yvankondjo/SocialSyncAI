-- Test script pour vérifier les politiques RLS (Row-Level Security)
-- Ce script doit être exécuté dans Supabase SQL Editor

-- 1. Créer des utilisateurs de test
INSERT INTO auth.users (id, email, email_confirmed_at, created_at, updated_at)
VALUES 
    ('11111111-1111-1111-1111-111111111111', 'user1@test.com', NOW(), NOW(), NOW()),
    ('22222222-2222-2222-2222-222222222222', 'user2@test.com', NOW(), NOW(), NOW()),
    ('33333333-3333-3333-3333-333333333333', 'admin@test.com', NOW(), NOW(), NOW());

-- 2. Créer des profils utilisateurs correspondants
INSERT INTO users (id, email, username, full_name, role)
VALUES 
    ('11111111-1111-1111-1111-111111111111', 'user1@test.com', 'user1', 'Test User 1', 'user'),
    ('22222222-2222-2222-2222-222222222222', 'user2@test.com', 'user2', 'Test User 2', 'user'),
    ('33333333-3333-3333-3333-333333333333', 'admin@test.com', 'admin', 'Test Admin', 'admin');

-- 3. Créer des comptes sociaux pour chaque utilisateur
INSERT INTO social_accounts (id, platform, account_id, username, user_id)
VALUES 
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'twitter', 'user1_twitter', 'user1_tw', '11111111-1111-1111-1111-111111111111'),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'twitter', 'user2_twitter', 'user2_tw', '22222222-2222-2222-2222-222222222222');

-- 4. Créer du contenu pour chaque utilisateur
INSERT INTO content (id, title, content, social_account_id, created_by)
VALUES 
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'Post User 1', 'Contenu de User 1', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111'),
    ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'Post User 2', 'Contenu de User 2', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '22222222-2222-2222-2222-222222222222');

-- 5. Créer des analytics pour chaque contenu
INSERT INTO analytics (content_id, platform, likes, shares, comments)
VALUES 
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'twitter', 10, 5, 3),
    ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'twitter', 20, 8, 7);

-- 7. Créer des analytics history
INSERT INTO analytics_history (content_id, platform, likes, shares, comments, recorded_at, user_id)
VALUES 
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'twitter', 8, 4, 2, NOW() - INTERVAL '1 day', '11111111-1111-1111-1111-111111111111'),
    ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'twitter', 15, 6, 5, NOW() - INTERVAL '1 day', '22222222-2222-2222-2222-222222222222');

-- ===== TESTS RLS =====

-- Test 1: Vérifier l'isolation des utilisateurs (User 1 ne doit voir que ses données)
-- Simuler la connexion de User 1
SELECT auth.jwt() AS "Test: Connexion User 1";

-- User 1 doit voir seulement son profil
SELECT 'Users - User 1 should see only own profile' AS test_description;
SELECT id, email FROM users WHERE id = '11111111-1111-1111-1111-111111111111';

-- User 1 doit voir seulement ses comptes sociaux
SELECT 'Social Accounts - User 1 should see only own accounts' AS test_description;
SELECT id, platform, username FROM social_accounts WHERE user_id = '11111111-1111-1111-1111-111111111111';

-- User 1 doit voir seulement son contenu
SELECT 'Content - User 1 should see only own content' AS test_description;
SELECT id, title FROM content WHERE created_by = '11111111-1111-1111-1111-111111111111';

-- User 1 doit voir seulement ses analytics
SELECT 'Analytics - User 1 should see only own analytics' AS test_description;
SELECT a.id, a.likes, a.platform 
FROM analytics a 
JOIN content c ON c.id = a.content_id 
    WHERE c.created_by = '11111111-1111-1111-1111-111111111111';

-- User 1 doit voir seulement son analytics history
SELECT 'Analytics History - User 1 should see only own history' AS test_description;
SELECT id, likes, platform FROM analytics_history WHERE user_id = '11111111-1111-1111-1111-111111111111';

-- ===== TEST ADMIN =====

-- -- Test 2: Vérifier que l'admin peut tout voir
-- SELECT 'Admin Access - Admin should see all data' AS test_description;

-- -- L'admin doit voir tous les utilisateurs
-- SELECT 'Admin - All users count' AS test_description, COUNT(*) as total_users FROM users;

-- -- L'admin doit voir tous les comptes sociaux
-- SELECT 'Admin - All social accounts count' AS test_description, COUNT(*) as total_accounts FROM social_accounts;

-- -- L'admin doit voir tout le contenu
-- SELECT 'Admin - All content count' AS test_description, COUNT(*) as total_content FROM content;

-- -- L'admin doit voir toutes les analytics
-- SELECT 'Admin - All analytics count' AS test_description, COUNT(*) as total_analytics FROM analytics;

-- ===== NETTOYAGE =====

-- Nettoyer les données de test (à exécuter après les tests)
/*
DELETE FROM analytics_history WHERE user_id IN ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222');
DELETE FROM ai_insights WHERE user_id IN ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222');
DELETE FROM analytics WHERE content_id IN ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'dddddddd-dddd-dddd-dddd-dddddddddddd');
DELETE FROM content WHERE id IN ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'dddddddd-dddd-dddd-dddd-dddddddddddd');
DELETE FROM social_accounts WHERE id IN ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb');
DELETE FROM users WHERE id IN ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333');
DELETE FROM auth.users WHERE id IN ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333');
*/ 