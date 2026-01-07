drop index if exists "public"."idx_checkpoints_ns_created";

drop index if exists "public"."idx_checkpoints_thread_id";

alter table "public"."checkpoint_blobs" disable row level security;

alter table "public"."checkpoint_migrations" disable row level security;

alter table "public"."checkpoint_writes" disable row level security;

alter table "public"."checkpoints" drop column "created_at";

alter table "public"."checkpoints" disable row level security;

alter table "public"."social_accounts" alter column "profile_url" set data type text using "profile_url"::text;

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.handle_new_user_ai_settings()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
    -- Insert default AI settings for the new user
    INSERT INTO public.ai_settings (
        user_id,
        system_prompt,
        ai_model,
        temperature,
        top_p,
        lang,
        tone,
        is_active,
        doc_lang,
        ai_control_enabled,
        ai_enabled_for_chats,
        ai_enabled_for_comments,
        flagged_keywords,
        flagged_phrases,
        ignore_examples
    ) VALUES (
        NEW.id,
        'You are an AI assistant specialized in social media management.

Your responsibilities:
- Create engaging and viral content for social media
- Analyze trending hashtags and topics
- Optimize posts for each platform (Instagram, TikTok, Facebook, Twitter)
- Propose growth and engagement strategies
- Respond in a friendly and professional tone
- Provide creative and authentic advice',
        'openai/gpt-4o',
        0.20,
        1.00,
        'en',
        'friendly',
        true,
        '{}',
        true,
        true,
        true,
        '{}',
        '{}',
        '{}'
    )
    ON CONFLICT (user_id) DO NOTHING;
    
    RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.handle_new_user_credits()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
    -- Configuration du plan Starter (gratuit)
    starter_credits INTEGER := 100;
    starter_plan_credits INTEGER := 100;
    starter_storage_limit_mb DOUBLE PRECISION := 100.0;  -- 100 MB
BEGIN
    INSERT INTO public.user_credits (
        user_id,
        credits_balance,
        plan_credits,
        storage_used_mb,
        next_reset_at
    ) VALUES (
        NEW.id,
        starter_credits,
        starter_plan_credits,
        0,
        NOW() + INTERVAL '30 days'
    )
    ON CONFLICT (user_id) DO NOTHING;
    
    RETURN NEW;
END;
$function$
;

CREATE TRIGGER on_auth_user_created_ai_settings AFTER INSERT ON public.users FOR EACH ROW EXECUTE FUNCTION public.handle_new_user_ai_settings();

CREATE TRIGGER on_public_user_created_credits AFTER INSERT ON public.users FOR EACH ROW EXECUTE FUNCTION public.handle_new_user_credits();


