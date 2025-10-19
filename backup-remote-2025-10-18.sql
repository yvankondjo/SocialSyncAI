

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE EXTENSION IF NOT EXISTS "pg_net" WITH SCHEMA "extensions";






CREATE SCHEMA IF NOT EXISTS "private";


ALTER SCHEMA "private" OWNER TO "postgres";


COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pg_trgm" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "unaccent" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "vector" WITH SCHEMA "extensions";






CREATE TYPE "public"."social_platform" AS ENUM (
    'facebook',
    'twitter',
    'instagram',
    'linkedin',
    'youtube',
    'tiktok',
    'whatsapp',
    'reddit',
    'x'
);


ALTER TYPE "public"."social_platform" OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "private"."chunks_tsv_update"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public', 'extensions'
    AS $$
BEGIN
  NEW.tsv := to_tsvector(NEW.tsconfig::regconfig, unaccent(NEW.content));
  RETURN NEW;
END;
$$;


ALTER FUNCTION "private"."chunks_tsv_update"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "private"."decrement_storage_usage"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    size_mb NUMERIC(10, 2);
    owner_id UUID;
BEGIN
    -- Déterminer la taille en MB et le propriétaire
    IF TG_TABLE_NAME = 'knowledge_documents' THEN
        size_mb := OLD.file_size_bytes / (1024.0 * 1024.0);
        owner_id := OLD.user_id;
    ELSIF TG_TABLE_NAME = 'faq_qa' THEN
        size_mb := OLD.text_size_bytes / (1024.0 * 1024.0);
        owner_id := OLD.user_id;
    END IF;

    -- Décrémenter storage_used_mb (ne pas descendre sous 0)
    UPDATE public.user_subscriptions
    SET storage_used_mb = GREATEST(0, storage_used_mb - size_mb),
        updated_at = NOW()
    WHERE user_id = owner_id;

    RETURN OLD;
END;
$$;


ALTER FUNCTION "private"."decrement_storage_usage"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "private"."faq_tsv_update"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public', 'extensions'
    AS $$
BEGIN
  NEW.tsv := to_tsvector(NEW.tsconfig::regconfig, unaccent(NEW.content));
  RETURN NEW;
END;
$$;


ALTER FUNCTION "private"."faq_tsv_update"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "private"."handle_storage_update"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
declare
  document_id uuid;
  result int;
begin
IF NEW.bucket_id <> 'kb' THEN
    RETURN NULL;
  END IF;
  insert into knowledge_documents (title, storage_object_id, user_id,bucket_id,object_name,tsconfig,lang_code,status,file_size_bytes)
    values (new.path_tokens[2], new.id, new.owner, new.bucket_id, new.name, 'pg_catalog.simple', 'simple', 'processing', COALESCE((new.metadata->>'size')::BIGINT, 0))
    returning id into document_id;

  select
    net.http_post(
      url := backend_url() || '/api/functions/v1/process',
      headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'Authorization', current_setting('request.headers')::json->>'authorization'
      ),
      body := jsonb_build_object(
        'document_id', document_id
      )
    )
  into result;

  return null;
end;
$$;


ALTER FUNCTION "private"."handle_storage_update"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "private"."increment_storage_usage"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    size_mb NUMERIC(10, 2);
    owner_id UUID;
BEGIN
    -- Déterminer la taille en MB et le propriétaire
    IF TG_TABLE_NAME = 'knowledge_documents' THEN
        size_mb := NEW.file_size_bytes / (1024.0 * 1024.0);
        owner_id := NEW.user_id;
    ELSIF TG_TABLE_NAME = 'faq_qa' THEN
        size_mb := NEW.text_size_bytes / (1024.0 * 1024.0);
        owner_id := NEW.user_id;
    END IF;

    -- Incrémenter storage_used_mb
    UPDATE public.user_subscriptions
    SET storage_used_mb = storage_used_mb + size_mb,
        updated_at = NOW()
    WHERE user_id = owner_id;

    RETURN NEW;
END;
$$;


ALTER FUNCTION "private"."increment_storage_usage"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "private"."safe_regconfig"("_lang" "text") RETURNS "regconfig"
    LANGUAGE "sql" IMMUTABLE
    SET "search_path" TO ''
    AS $$
  SELECT COALESCE(
           NULLIF(_lang, '')::regconfig,   -- try to cast the supplied text
           'simple'::regconfig            -- fallback if null or empty
         );
$$;


ALTER FUNCTION "private"."safe_regconfig"("_lang" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "private"."sync_chunk_tsconfig"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public', 'extensions'
    AS $$
BEGIN
  -- Synchronise tsconfig et lang_code depuis le document parent (une seule vérification)
    SELECT d.tsconfig, d.lang_code
    INTO NEW.tsconfig, NEW.lang_code
    FROM knowledge_documents d
    WHERE d.id = NEW.document_id;
  RETURN NEW;
END;
$$;


ALTER FUNCTION "private"."sync_chunk_tsconfig"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "private"."update_user_doc_languages"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public', 'extensions'
    AS $$
DECLARE
    user_id_val UUID;
    new_lang TEXT;
    current_langs TEXT[];
BEGIN
    -- Récupérer l'user_id du document
    user_id_val := NEW.user_id;
    new_lang := NEW.lang_code;
    
    -- Récupérer les langues actuelles pour cet utilisateur
    SELECT COALESCE(doc_lang, '{}') INTO current_langs
    FROM ai_settings 
    WHERE user_id = user_id_val;
    
    -- If the new language is not already in the list, add it
    IF new_lang IS NOT NULL AND new_lang != 'simple' AND NOT (new_lang = ANY(current_langs)) THEN
        current_langs := array_append(current_langs, new_lang);
        
        -- Update the existing ai_settings entry
        UPDATE ai_settings 
        SET doc_lang = current_langs, updated_at = NOW()
        WHERE user_id = user_id_val;
    END IF;
    
    RETURN NEW;
END;
$$;


ALTER FUNCTION "private"."update_user_doc_languages"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "private"."uuid_or_null"("str" "text") RETURNS "uuid"
    LANGUAGE "plpgsql"
    SET "search_path" TO ''
    AS $$
BEGIN
  RETURN str::uuid;  -- try cast
EXCEPTION WHEN invalid_text_representation THEN
  RETURN NULL;
END;$$;


ALTER FUNCTION "private"."uuid_or_null"("str" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."apply_trial_credits"("p_user_id" "uuid", "p_subscription_id" "text", "p_trial_credits" integer, "p_trial_end" timestamp with time zone) RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
BEGIN
  UPDATE public.user_credits
  SET
    subscription_id = p_subscription_id,
    plan_credits    = p_trial_credits,
    credits_balance = p_trial_credits,
    next_reset_at   = p_trial_end
  WHERE user_id = p_user_id;
END;
$$;


ALTER FUNCTION "public"."apply_trial_credits"("p_user_id" "uuid", "p_subscription_id" "text", "p_trial_credits" integer, "p_trial_end" timestamp with time zone) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."backend_url"() RETURNS "text"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
declare
  secret_value text;
begin
  select decrypted_secret into secret_value from vault.decrypted_secrets where name = 'backend_url';
  return secret_value;
end;
$$;


ALTER FUNCTION "public"."backend_url"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."cleanup_orphaned_storage_references"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
begin
    IF OLD.bucket_id <> 'message' then
    RETURN NULL;
    END IF;
    delete from conversation_messages
    WHere storage_object_name=OLD.name AND storage_object_name IS NOT null;

    RETURN OLD;

END;
$$;


ALTER FUNCTION "public"."cleanup_orphaned_storage_references"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."consume_credits"("p_user_id" "uuid", "p_amount" integer) RETURNS boolean
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
DECLARE v_balance int;
BEGIN
  IF p_amount <= 0 THEN
    RAISE EXCEPTION 'amount must be > 0';
  END IF;

  -- Verrou ligne
  SELECT credits_balance INTO v_balance
  FROM public.user_credits
  WHERE user_id = p_user_id
  FOR UPDATE;

  IF v_balance IS NULL THEN
    RAISE EXCEPTION 'user_credits not found';
  END IF;

  IF v_balance < p_amount THEN
    RETURN false; -- pas assez de crédits
  END IF;

  UPDATE public.user_credits
  SET credits_balance = credits_balance - p_amount
  WHERE user_id = p_user_id;

  RETURN true;
END;
$$;


ALTER FUNCTION "public"."consume_credits"("p_user_id" "uuid", "p_amount" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."delete_user"("p_user_id" "uuid") RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
DECLARE
  v_user_exists boolean;
BEGIN
  -- Vérifier que l'utilisateur existe et appartient à l'utilisateur authentifié
  SELECT EXISTS(
    SELECT 1 FROM users
    WHERE id = p_user_id
      AND id = auth.uid()
  ) INTO v_user_exists;

  IF NOT v_user_exists THEN
    RAISE EXCEPTION 'User not found or access denied';
  END IF;

  -- Suppression en cascade (sera gérée par les FK constraints)
  DELETE FROM users WHERE id = p_user_id;
END;
$$;


ALTER FUNCTION "public"."delete_user"("p_user_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_new_user"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
begin
  insert into public.users (id, email, full_name)
  values (
    new.id, 
    new.email, -- Utilise directement new.email
    new.raw_user_meta_data->>'full_name'-- Peut être NULL
  );
  return new;
end;
$$;


ALTER FUNCTION "public"."handle_new_user"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_new_user_credits"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
    INSERT INTO public.user_credits (user_id, credits_balance)
    VALUES (NEW.id, 0)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."handle_new_user_credits"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."hybrid_knowledge_chunks_search_v2"("p_user_id" "uuid", "query_text" "text", "query_embedding" "extensions"."vector", "query_lang" "text" DEFAULT 'simple'::"text", "match_count" integer DEFAULT 10, "rrf_k" integer DEFAULT 10, "similarity_threshold" double precision DEFAULT 0.6) RETURNS json
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'extensions', 'public'
    AS $$
DECLARE
  query_config regconfig := CASE
    WHEN query_lang = 'french'  THEN 'pg_catalog.french'::regconfig
    WHEN query_lang = 'english' THEN 'pg_catalog.english'::regconfig
    WHEN query_lang = 'spanish' THEN 'pg_catalog.spanish'::regconfig
    ELSE 'pg_catalog.simple'::regconfig
  END;
  query_tsquery tsquery := to_tsquery(query_config, unaccent(query_text));
  score_threshold FLOAT := 0.001;
BEGIN
  RETURN (
    WITH text_results AS (
      SELECT
        c.id,
        c.content,
        ts_rank(c.tsv, query_tsquery) AS score_fts,
        ROW_NUMBER() OVER (ORDER BY ts_rank(c.tsv, query_tsquery) DESC) AS rank_fts
      FROM knowledge_chunks c
      JOIN knowledge_documents d ON c.document_id = d.id
      WHERE d.is_deleted = FALSE
        AND d.user_id = p_user_id
        AND c.lang_code = query_lang
        AND c.tsv @@ query_tsquery
        AND ts_rank(c.tsv, query_tsquery) >= score_threshold
      ORDER BY score_fts DESC
      LIMIT match_count * 2
    ),
    vector_results AS (
      SELECT
        c.id,
        c.content,
        (-(c.embedding <#> query_embedding)) AS score_vec,   -- inner product positif
        ROW_NUMBER() OVER (ORDER BY (-(c.embedding <#> query_embedding)) DESC) AS rank_vec
      FROM knowledge_chunks c
      JOIN knowledge_documents d ON c.document_id = d.id
      WHERE d.is_deleted = FALSE
        AND d.user_id = p_user_id
        AND (-(c.embedding <#> query_embedding)) >= similarity_threshold
      ORDER BY score_vec DESC
      LIMIT match_count * 2
    ),
    combined AS (
      SELECT
        COALESCE(t.content, v.content) AS content,
        (COALESCE(1.0 / (t.rank_fts + rrf_k), 0)* t.score_fts
       + COALESCE(1.0 / (v.rank_vec + rrf_k), 0)* v.score_vec) AS rrf_score
      FROM text_results t
      FULL OUTER JOIN vector_results v ON t.id = v.id
    ),
    final_results AS (
      SELECT content, rrf_score
      FROM combined
      WHERE rrf_score > 0
      ORDER BY rrf_score DESC
      LIMIT match_count
    )
    SELECT COALESCE(
      json_agg(json_build_object('content', content, 'score', rrf_score) ORDER BY rrf_score DESC),
      '[]'::json
    )
    FROM final_results
  );
END;
$$;


ALTER FUNCTION "public"."hybrid_knowledge_chunks_search_v2"("p_user_id" "uuid", "query_text" "text", "query_embedding" "extensions"."vector", "query_lang" "text", "match_count" integer, "rrf_k" integer, "similarity_threshold" double precision) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."mark_conversation_as_read"("conversation_uuid" "uuid") RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
BEGIN
  -- Vérifier que l'utilisateur possède bien cette conversation
  IF NOT EXISTS (
    SELECT 1 FROM conversations c
    JOIN social_accounts sa ON sa.id = c.social_account_id
    WHERE c.id = conversation_uuid
    AND sa.user_id = auth.uid()
  ) THEN
    RAISE EXCEPTION 'Conversation not found or access denied';
  END IF;

  UPDATE conversations
  SET unread_count = 0
  WHERE id = conversation_uuid;
END;
$$;


ALTER FUNCTION "public"."mark_conversation_as_read"("conversation_uuid" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."mark_conversation_as_read"("p_conversation_id" "uuid", "p_user_id" "uuid") RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
BEGIN
  UPDATE conversations
  SET is_read = true,
      updated_at = NOW()
  WHERE id = p_conversation_id
    AND user_id = p_user_id;

  -- Marquer aussi les messages comme lus
  UPDATE conversation_messages
  SET is_read = true
  WHERE conversation_id = p_conversation_id;
END;
$$;


ALTER FUNCTION "public"."mark_conversation_as_read"("p_conversation_id" "uuid", "p_user_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."mark_document_failed"("document_uuid" "uuid", "error_message" "text" DEFAULT NULL::"text") RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
BEGIN
  UPDATE knowledge_documents
  SET
    status = 'failed',
    updated_at = NOW()
  WHERE id = document_uuid;

  -- Log de l'erreur si un message est fourni
  IF error_message IS NOT NULL THEN
    RAISE LOG 'Document % marqué comme failed: %', document_uuid, error_message;
  END IF;
END;
$$;


ALTER FUNCTION "public"."mark_document_failed"("document_uuid" "uuid", "error_message" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."reset_cycle_credits"("p_subscription_id" "text", "p_plan_credits" integer, "p_period_end" timestamp with time zone) RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
BEGIN
  UPDATE public.user_credits uc
  SET
    plan_credits    = p_plan_credits,
    credits_balance = p_plan_credits,
    next_reset_at   = p_period_end
  WHERE uc.subscription_id = p_subscription_id;
END;
$$;


ALTER FUNCTION "public"."reset_cycle_credits"("p_subscription_id" "text", "p_plan_credits" integer, "p_period_end" timestamp with time zone) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."resolve_plan_credits"("p_subscription_id" "text") RETURNS integer
    LANGUAGE "sql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
  SELECT COALESCE(
    NULLIF((pr.metadata->>'credits_per_cycle')::int, NULL),
    NULLIF((pd.metadata->>'credits_per_cycle')::int, NULL),
    NULLIF((pd.metadata->>'credits_monthly')::int, NULL),
    1000
  ) AS plan_credits
  FROM public.subscriptions s
  LEFT JOIN public.prices pr ON pr.id = s.price_id
  LEFT JOIN public.products pd ON pd.id = pr.product_id
  WHERE s.id = p_subscription_id
  LIMIT 1;
$$;


ALTER FUNCTION "public"."resolve_plan_credits"("p_subscription_id" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."set_published_at"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
BEGIN
  IF NEW.status = 'published' AND NEW.published_at IS NULL THEN
    NEW.published_at = NOW();
  END IF;
  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."set_published_at"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."supabase_url"() RETURNS "text"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
declare
  secret_value text;
begin
  select decrypted_secret into secret_value from vault.decrypted_secrets where name = 'supabase_url';
  return secret_value;
end;
$$;


ALTER FUNCTION "public"."supabase_url"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."text_faq_search_v2"("p_user_id" "uuid", "query_text" "text", "query_lang" "text" DEFAULT 'simple'::"text", "match_count" integer DEFAULT 10) RETURNS json
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
DECLARE
  score_threshold FLOAT := 0.001;
  query_config regconfig := CASE
    WHEN query_lang = 'french'  THEN 'pg_catalog.french'::regconfig
    WHEN query_lang = 'english' THEN 'pg_catalog.english'::regconfig
    WHEN query_lang = 'spanish' THEN 'pg_catalog.spanish'::regconfig
    ELSE 'pg_catalog.simple'::regconfig
  END;
  query_tsquery tsquery := to_tsquery(query_config, unaccent(query_text));
BEGIN
  RETURN (
    WITH ranked AS (
      SELECT
        c.content,
        ts_rank(c.tsv, query_tsquery) AS score
      FROM faq_qa c
      WHERE c.lang_code = query_lang
        AND c.user_id = p_user_id
        AND c.tsv @@ query_tsquery
        AND ts_rank(c.tsv, query_tsquery) >= score_threshold
      ORDER BY score DESC
      LIMIT match_count
    )
    SELECT COALESCE(
      json_agg(json_build_object('content', content, 'score', score) ORDER BY score DESC),
      '[]'::json
    )
    FROM ranked
  );
END;
$$;


ALTER FUNCTION "public"."text_faq_search_v2"("p_user_id" "uuid", "query_text" "text", "query_lang" "text", "match_count" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."text_knowledge_chunks_search_v2"("p_user_id" "uuid", "query_text" "text", "query_lang" "text" DEFAULT 'simple'::"text", "match_count" integer DEFAULT 10) RETURNS json
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
DECLARE
  query_config regconfig := CASE
    WHEN query_lang = 'french'  THEN 'pg_catalog.french'::regconfig
    WHEN query_lang = 'english' THEN 'pg_catalog.english'::regconfig
    WHEN query_lang = 'spanish' THEN 'pg_catalog.spanish'::regconfig
    ELSE 'pg_catalog.simple'::regconfig
  END;
  query_tsquery tsquery := to_tsquery(query_config, unaccent(query_text));
  score_threshold FLOAT := 0.001;
BEGIN
  RETURN (
    WITH ranked AS (
      SELECT
        c.content,
        ts_rank(c.tsv, query_tsquery) AS score
      FROM knowledge_chunks c
      JOIN knowledge_documents d ON c.document_id = d.id
      WHERE d.is_deleted = FALSE
        AND d.user_id = p_user_id
        AND c.lang_code = query_lang
        AND c.tsv @@ query_tsquery
        AND ts_rank(c.tsv, query_tsquery) >= score_threshold
      ORDER BY score DESC
      LIMIT match_count
    )
    SELECT COALESCE(
      json_agg(json_build_object('content', content, 'score', score) ORDER BY score DESC),
      '[]'::json
    )
    FROM ranked
  );
END;
$$;


ALTER FUNCTION "public"."text_knowledge_chunks_search_v2"("p_user_id" "uuid", "query_text" "text", "query_lang" "text", "match_count" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."text_unified_retrieve"("query_text" "text", "query_embedding" "extensions"."vector", "query_lang" "text" DEFAULT 'simple'::"text", "match_count" integer DEFAULT 10, "rrf_k" integer DEFAULT 10) RETURNS json
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
BEGIN
  RETURN (
    WITH chunk_data AS (
      SELECT elem->>'content' AS content, (elem->>'score')::REAL AS score
      FROM jsonb_array_elements(
        COALESCE((SELECT hybrid_knowledge_chunks_search(query_text, query_embedding, query_lang, match_count, rrf_k))::jsonb, '[]'::jsonb)
      ) AS elem
    ),
    faq_data AS (
      SELECT elem->>'content' AS content, (elem->>'score')::REAL AS score
      FROM jsonb_array_elements(
        COALESCE((SELECT text_faq_search(query_text, query_lang, match_count))::jsonb, '[]'::jsonb)
      ) AS elem
    ),
    unified_results AS (
      SELECT content, score
      FROM chunk_data
      UNION ALL
      SELECT content, score
      FROM faq_data
      ORDER BY score DESC
      LIMIT match_count
    ),
    ranked AS (
      SELECT content, ROW_NUMBER() OVER (ORDER BY score DESC) AS global_rank
      FROM unified_results
    )
    SELECT COALESCE(json_agg(json_build_object('content', content, 'score', 1.0 / (global_rank + rrf_k))), '[]'::json)
    FROM ranked
  );
END;
$$;


ALTER FUNCTION "public"."text_unified_retrieve"("query_text" "text", "query_embedding" "extensions"."vector", "query_lang" "text", "match_count" integer, "rrf_k" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."text_unified_retrieve_v2"("p_user_id" "uuid", "query_text" "text", "query_embedding" "extensions"."vector", "query_lang" "text" DEFAULT 'simple'::"text", "match_count" integer DEFAULT 10, "rrf_k" integer DEFAULT 10, "similarity_threshold" double precision DEFAULT 0.6) RETURNS json
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
DECLARE
  score_threshold FLOAT := 0.001;
BEGIN
  RETURN (
    WITH chunk_data AS (
      SELECT elem->>'content' AS content, (elem->>'score')::REAL AS score
      FROM jsonb_array_elements(
        COALESCE((SELECT hybrid_knowledge_chunks_search_v2(p_user_id, query_text, query_embedding, query_lang, match_count, rrf_k, similarity_threshold))::jsonb, '[]'::jsonb)
      ) AS elem
    ),
    faq_data AS (
      SELECT elem->>'content' AS content, (elem->>'score')::REAL AS score
      FROM jsonb_array_elements(
        COALESCE((SELECT text_faq_search_v2(p_user_id, query_text, query_lang, match_count))::jsonb, '[]'::jsonb)
      ) AS elem
    ),
    unified_results AS (
      SELECT content, score
      FROM chunk_data
      UNION ALL
      SELECT content, score
      FROM faq_data
      WHERE score >= score_threshold
      ORDER BY score DESC
      LIMIT match_count
    ),
    ranked AS (
      SELECT content, ROW_NUMBER() OVER (ORDER BY score DESC) AS global_rank
      FROM unified_results
    ),
    final_ranked AS (
      SELECT content, (1.0 / (global_rank + rrf_k)) AS final_score
      FROM ranked
    )
    SELECT COALESCE(json_agg(json_build_object('content', content, 'score', final_score) ORDER BY final_score DESC), '[]'::json)
    FROM final_ranked
  );
END;
$$;


ALTER FUNCTION "public"."text_unified_retrieve_v2"("p_user_id" "uuid", "query_text" "text", "query_embedding" "extensions"."vector", "query_lang" "text", "match_count" integer, "rrf_k" integer, "similarity_threshold" double precision) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_ai_rules_updated_at"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_ai_rules_updated_at"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_conversation_last_message"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
BEGIN
  UPDATE conversations
  SET
    last_message_at = NEW.created_at,
    unread_count = CASE
      WHEN NEW.direction = 'inbound' AND NEW.is_from_agent = false
      THEN unread_count + 1
      ELSE unread_count
    END
  WHERE id = NEW.conversation_id;
  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_conversation_last_message"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_conversatios_message_groups_updated_at"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    SET "search_path" TO 'public'
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_conversatios_message_groups_updated_at"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_message_groups_updated_at"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    SET "search_path" TO 'public'
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_message_groups_updated_at"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_scheduled_posts_updated_at"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_scheduled_posts_updated_at"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_updated_at_column"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_updated_at_column"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."vector_knowledge_chunks_search_v2"("p_user_id" "uuid", "query_text" "text", "query_embedding" "extensions"."vector", "match_count" integer DEFAULT 10) RETURNS json
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
DECLARE
  similarity_threshold FLOAT := 0.6; -- ex: garder si a·b >= 0.6
BEGIN
  RETURN (
    WITH ranked AS (
      SELECT
        c.content,
        -(c.embedding <#> query_embedding) AS score  -- inner product (positif)
      FROM knowledge_chunks c
      JOIN knowledge_documents d ON c.document_id = d.id
      WHERE d.is_deleted = FALSE
        AND d.user_id = p_user_id
        AND (-(c.embedding <#> query_embedding)) >= similarity_threshold
      ORDER BY score DESC
      LIMIT match_count
    )
    SELECT COALESCE(
      json_agg(json_build_object('content', content, 'score', score) ORDER BY score DESC),
      '[]'::json
    )
    FROM ranked
  );
END;
$$;


ALTER FUNCTION "public"."vector_knowledge_chunks_search_v2"("p_user_id" "uuid", "query_text" "text", "query_embedding" "extensions"."vector", "match_count" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."zero_credits_on_cancel"("p_subscription_id" "text") RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
BEGIN
  UPDATE public.user_credits
  SET
    credits_balance = 0,
    next_reset_at   = NULL,
    subscription_id = NULL
  WHERE subscription_id = p_subscription_id;
END;
$$;


ALTER FUNCTION "public"."zero_credits_on_cancel"("p_subscription_id" "text") OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."ai_decisions" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "message_id" "uuid",
    "decision" "text",
    "confidence" numeric(4,3),
    "reason" "text",
    "matched_rule" "text",
    "message_text" "text",
    "snapshot_json" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "ai_decisions_decision_check" CHECK (("decision" = ANY (ARRAY['respond'::"text", 'ignore'::"text", 'escalate'::"text"])))
);


ALTER TABLE "public"."ai_decisions" OWNER TO "postgres";


COMMENT ON TABLE "public"."ai_decisions" IS 'Log of AI decisions for traceability';



COMMENT ON COLUMN "public"."ai_decisions"."decision" IS 'AI decision: respond, ignore, or escalate';



COMMENT ON COLUMN "public"."ai_decisions"."confidence" IS 'Confidence score from 0.000 to 1.000';



COMMENT ON COLUMN "public"."ai_decisions"."reason" IS 'Human-readable reason for the decision';



COMMENT ON COLUMN "public"."ai_decisions"."matched_rule" IS 'Which rule triggered this decision';



CREATE TABLE IF NOT EXISTS "public"."ai_models" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" "text" NOT NULL,
    "provider" "text" NOT NULL,
    "openrouter_id" "text" NOT NULL,
    "credit_cost" numeric(10,2) NOT NULL,
    "model_type" "text" DEFAULT 'fast'::"text",
    "supports_text" boolean DEFAULT true,
    "supports_images" boolean DEFAULT false,
    "supports_audio" boolean DEFAULT false,
    "max_context_tokens" integer,
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "logo_key" "text",
    "description" "text",
    CONSTRAINT "ai_models_credit_cost_check" CHECK (("credit_cost" > (0)::numeric)),
    CONSTRAINT "ai_models_model_type_check" CHECK (("model_type" = ANY (ARRAY['fast'::"text", 'advanced'::"text", 'affordable'::"text"])))
);


ALTER TABLE "public"."ai_models" OWNER TO "postgres";


COMMENT ON TABLE "public"."ai_models" IS 'Modèles AI disponibles avec leurs caractéristiques et coûts';



COMMENT ON COLUMN "public"."ai_models"."openrouter_id" IS 'ID exact du modèle dans OpenRouter (ex: openai/gpt-4o-mini)';



COMMENT ON COLUMN "public"."ai_models"."credit_cost" IS 'Coût en crédits par appel au modèle';



COMMENT ON COLUMN "public"."ai_models"."logo_key" IS 'Nom du fichier logo (ex: openai-logo.svg)';



COMMENT ON COLUMN "public"."ai_models"."description" IS 'Description marketing du modèle';



CREATE TABLE IF NOT EXISTS "public"."ai_rules" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "instructions" "text",
    "ignore_examples" "text"[],
    "ai_control_enabled" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."ai_rules" OWNER TO "postgres";


COMMENT ON TABLE "public"."ai_rules" IS 'Simple AI control rules per user (instructions + ignore examples)';



COMMENT ON COLUMN "public"."ai_rules"."instructions" IS 'Free-text instructions for AI (e.g. "- Avoid spam\n- Be polite")';



COMMENT ON COLUMN "public"."ai_rules"."ignore_examples" IS 'Array of example messages to NOT respond to';



COMMENT ON COLUMN "public"."ai_rules"."ai_control_enabled" IS 'Master toggle: if false, AI never responds automatically';



CREATE TABLE IF NOT EXISTS "public"."ai_settings" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "system_prompt" "text" NOT NULL,
    "ai_model" "text" DEFAULT 'anthropic/claude-3.5-haiku'::"text",
    "temperature" numeric(3,2) DEFAULT 0.20,
    "top_p" numeric(3,2) DEFAULT 1.00,
    "lang" "text" DEFAULT 'en'::"text",
    "tone" "text" DEFAULT 'friendly'::"text",
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "doc_lang" "text"[] DEFAULT '{}'::"text"[]
);


ALTER TABLE "public"."ai_settings" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."analytics" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "content_id" "uuid" NOT NULL,
    "platform" "public"."social_platform" NOT NULL,
    "likes" integer DEFAULT 0,
    "shares" integer DEFAULT 0,
    "comments" integer DEFAULT 0,
    "impressions" integer DEFAULT 0,
    "reach" integer DEFAULT 0,
    "engagement_rate" numeric(5,2) DEFAULT 0,
    "clicks" integer DEFAULT 0,
    "conversions" integer DEFAULT 0,
    "raw_metrics" "jsonb",
    "recorded_at" timestamp with time zone DEFAULT "now"(),
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."analytics" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."analytics_history" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "content_id" "uuid" NOT NULL,
    "platform" "public"."social_platform" NOT NULL,
    "likes" integer DEFAULT 0,
    "shares" integer DEFAULT 0,
    "comments" integer DEFAULT 0,
    "impressions" integer DEFAULT 0,
    "reach" integer DEFAULT 0,
    "clicks" integer DEFAULT 0,
    "conversions" integer DEFAULT 0,
    "engagement_rate" numeric(5,2) DEFAULT 0,
    "recorded_at" timestamp with time zone NOT NULL,
    "user_id" "uuid" NOT NULL,
    "raw_metrics" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."analytics_history" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."checkpoint_blobs" (
    "thread_id" "text" NOT NULL,
    "checkpoint_ns" "text" DEFAULT ''::"text" NOT NULL,
    "channel" "text" NOT NULL,
    "version" "text" NOT NULL,
    "type" "text" NOT NULL,
    "blob" "bytea"
);


ALTER TABLE "public"."checkpoint_blobs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."checkpoint_migrations" (
    "v" integer NOT NULL
);


ALTER TABLE "public"."checkpoint_migrations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."checkpoint_writes" (
    "thread_id" "text" NOT NULL,
    "checkpoint_ns" "text" DEFAULT ''::"text" NOT NULL,
    "checkpoint_id" "text" NOT NULL,
    "task_id" "text" NOT NULL,
    "idx" integer NOT NULL,
    "channel" "text" NOT NULL,
    "type" "text",
    "blob" "bytea" NOT NULL,
    "task_path" "text" DEFAULT ''::"text" NOT NULL
);


ALTER TABLE "public"."checkpoint_writes" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."checkpoints" (
    "thread_id" "text" NOT NULL,
    "checkpoint_ns" "text" DEFAULT ''::"text" NOT NULL,
    "checkpoint_id" "text" NOT NULL,
    "parent_checkpoint_id" "text",
    "type" "text",
    "checkpoint" "jsonb" NOT NULL,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb" NOT NULL
);


ALTER TABLE "public"."checkpoints" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."conversation_messages" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "conversation_id" "uuid" NOT NULL,
    "external_message_id" character varying(255),
    "direction" character varying(20) NOT NULL,
    "message_type" character varying(50) DEFAULT 'text'::character varying,
    "content" "text" NOT NULL,
    "media_type" character varying(50),
    "sender_id" character varying(255),
    "sender_name" character varying(255),
    "sender_avatar_url" character varying(500),
    "status" character varying(50) DEFAULT 'sent'::character varying,
    "is_from_agent" boolean DEFAULT false,
    "agent_id" "uuid",
    "reply_to_message_id" "uuid",
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "storage_object_name" character varying(1000)
);


ALTER TABLE "public"."conversation_messages" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."conversations" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "social_account_id" "uuid" NOT NULL,
    "external_conversation_id" character varying(255),
    "customer_identifier" character varying(255) NOT NULL,
    "customer_name" character varying(255),
    "customer_avatar_url" character varying(500),
    "status" character varying(50) DEFAULT 'open'::character varying,
    "priority" character varying(20) DEFAULT 'normal'::character varying,
    "assigned_to" "uuid",
    "tags" "text"[],
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "last_message_at" timestamp with time zone,
    "unread_count" integer DEFAULT 0,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "automation_disabled" boolean DEFAULT false,
    "ai_mode" "text" DEFAULT 'ON'::"text" NOT NULL,
    CONSTRAINT "conversations_ai_mode_check" CHECK (("ai_mode" = ANY (ARRAY['ON'::"text", 'OFF'::"text"])))
);


ALTER TABLE "public"."conversations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."credit_transactions" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "transaction_type" "text" NOT NULL,
    "credits_amount" integer NOT NULL,
    "credits_balance_after" integer NOT NULL,
    "reason" "text" NOT NULL,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "credit_transactions_credits_balance_after_check" CHECK (("credits_balance_after" >= 0)),
    CONSTRAINT "credit_transactions_transaction_type_check" CHECK (("transaction_type" = ANY (ARRAY['deduction'::"text", 'refund'::"text", 'purchase'::"text", 'monthly_reset'::"text", 'trial_grant'::"text", 'bonus'::"text"])))
);


ALTER TABLE "public"."credit_transactions" OWNER TO "postgres";


COMMENT ON TABLE "public"."credit_transactions" IS 'Historique complet de toutes les transactions de crédits';



COMMENT ON COLUMN "public"."credit_transactions"."credits_amount" IS 'Montant de crédits (positif pour ajout, négatif pour déduction)';



COMMENT ON COLUMN "public"."credit_transactions"."metadata" IS 'Données supplémentaires: model, conversation_id, calls_count, etc.';



CREATE TABLE IF NOT EXISTS "public"."customers" (
    "id" "uuid" NOT NULL,
    "stripe_customer_id" "text",
    "whop_customer_id" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."customers" OWNER TO "postgres";


COMMENT ON TABLE "public"."customers" IS 'Mapping utilisateurs vers IDs clients Stripe/Whop';



COMMENT ON COLUMN "public"."customers"."id" IS 'UUID de auth.users';



COMMENT ON COLUMN "public"."customers"."stripe_customer_id" IS 'ID client dans Stripe (cus_xxx)';



COMMENT ON COLUMN "public"."customers"."whop_customer_id" IS 'ID client dans Whop';



CREATE TABLE IF NOT EXISTS "public"."faq_qa" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "title" "text",
    "answer" "text" NOT NULL,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "tsconfig" "text" DEFAULT '"simple"'::"regconfig" NOT NULL,
    "lang_code" "text" DEFAULT 'simple'::"text" NOT NULL,
    "questions" "text"[] DEFAULT '{}'::"text"[] NOT NULL,
    "text_size_bytes" integer DEFAULT 0,
    CONSTRAINT "faq_qa_text_size_bytes_check" CHECK (("text_size_bytes" >= 0))
);


ALTER TABLE "public"."faq_qa" OWNER TO "postgres";


COMMENT ON COLUMN "public"."faq_qa"."text_size_bytes" IS 'Taille du texte (questions + answer) en bytes';



CREATE TABLE IF NOT EXISTS "public"."knowledge_chunks" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "document_id" "uuid" NOT NULL,
    "chunk_index" integer NOT NULL,
    "content" "text" NOT NULL,
    "tsv" "tsvector",
    "token_count" integer,
    "start_char" integer,
    "end_char" integer,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "tsconfig" "text" DEFAULT '"simple"'::"regconfig" NOT NULL,
    "lang_code" "text" DEFAULT 'simple'::"text" NOT NULL,
    "embedding" "extensions"."vector"(768)
);


ALTER TABLE "public"."knowledge_chunks" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."knowledge_documents" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "title" "text",
    "storage_object_id" "uuid",
    "last_ingested_at" timestamp with time zone DEFAULT "now"(),
    "last_embedded_at" timestamp with time zone,
    "embed_model" "text" DEFAULT 'gemini-embedding-001'::"text",
    "is_deleted" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "tsconfig" "text" DEFAULT '"simple"'::"regconfig" NOT NULL,
    "lang_code" "text" DEFAULT 'simple'::"text" NOT NULL,
    "status" "text" NOT NULL,
    "bucket_id" "text",
    "object_name" "text",
    "file_size_bytes" bigint DEFAULT 0,
    CONSTRAINT "knowledge_documents_file_size_bytes_check" CHECK (("file_size_bytes" >= 0)),
    CONSTRAINT "knowledge_documents_status_check" CHECK (("status" = ANY (ARRAY['processing'::"text", 'indexed'::"text", 'failed'::"text"])))
);


ALTER TABLE "public"."knowledge_documents" OWNER TO "postgres";


COMMENT ON COLUMN "public"."knowledge_documents"."file_size_bytes" IS 'Taille du fichier en bytes';



CREATE TABLE IF NOT EXISTS "public"."post_runs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "scheduled_post_id" "uuid" NOT NULL,
    "started_at" timestamp with time zone,
    "finished_at" timestamp with time zone,
    "status" "text",
    "error" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "post_runs_status_check" CHECK (("status" = ANY (ARRAY['success'::"text", 'failed'::"text"])))
);


ALTER TABLE "public"."post_runs" OWNER TO "postgres";


COMMENT ON TABLE "public"."post_runs" IS 'Execution history for scheduled posts (attempts, errors, etc.)';



CREATE TABLE IF NOT EXISTS "public"."prices" (
    "id" "text" NOT NULL,
    "product_id" "text",
    "active" boolean DEFAULT true,
    "description" "text",
    "unit_amount" bigint,
    "currency" "text" DEFAULT 'eur'::"text",
    "type" "text" DEFAULT 'recurring'::"text",
    "interval" "text",
    "interval_count" integer DEFAULT 1,
    "trial_period_days" integer DEFAULT 0,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "prices_currency_check" CHECK (("char_length"("currency") = 3)),
    CONSTRAINT "prices_interval_check" CHECK (("interval" = ANY (ARRAY['day'::"text", 'week'::"text", 'month'::"text", 'year'::"text"]))),
    CONSTRAINT "prices_interval_count_check" CHECK (("interval_count" > 0)),
    CONSTRAINT "prices_type_check" CHECK (("type" = ANY (ARRAY['one_time'::"text", 'recurring'::"text"]))),
    CONSTRAINT "prices_unit_amount_check" CHECK (("unit_amount" >= 0))
);


ALTER TABLE "public"."prices" OWNER TO "postgres";


COMMENT ON TABLE "public"."prices" IS 'Prix sync depuis Stripe';



COMMENT ON COLUMN "public"."prices"."id" IS 'ID prix Stripe (price_xxx)';



COMMENT ON COLUMN "public"."prices"."unit_amount" IS 'Montant en centimes (999 pour 9.99€)';



CREATE TABLE IF NOT EXISTS "public"."products" (
    "id" "text" NOT NULL,
    "active" boolean DEFAULT true,
    "name" "text" NOT NULL,
    "description" "text",
    "image" "text",
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "source" "text" DEFAULT 'stripe'::"text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "products_source_check" CHECK (("source" = ANY (ARRAY['stripe'::"text", 'whop'::"text"])))
);


ALTER TABLE "public"."products" OWNER TO "postgres";


COMMENT ON TABLE "public"."products" IS 'Produits sync depuis Stripe et Whop';



COMMENT ON COLUMN "public"."products"."id" IS 'ID produit (prod_xxx Stripe ou ID Whop)';



COMMENT ON COLUMN "public"."products"."metadata" IS 'Configuration métier (crédits, features, etc.)';



COMMENT ON COLUMN "public"."products"."source" IS 'Origine: stripe ou whop';



CREATE OR REPLACE VIEW "public"."rag_chunks" WITH ("security_invoker"='on') AS
 SELECT "kc"."id",
    "kc"."document_id",
    "kd"."user_id",
    "kd"."title",
    "kd"."storage_object_id",
    "kd"."object_name",
    "kd"."bucket_id",
    "kc"."chunk_index",
    "kc"."tsconfig",
    "kc"."lang_code",
    "kc"."content",
    "kc"."tsv",
    "kc"."embedding",
    "kc"."metadata",
    "kc"."start_char",
    "kc"."end_char",
    "kd"."status"
   FROM ("public"."knowledge_chunks" "kc"
     JOIN "public"."knowledge_documents" "kd" ON (("kd"."id" = "kc"."document_id")))
  WHERE (("kd"."is_deleted" = false) AND ("kd"."status" = 'indexed'::"text"));


ALTER VIEW "public"."rag_chunks" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."scheduled_posts" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "channel_id" "uuid" NOT NULL,
    "platform" "text" NOT NULL,
    "content_json" "jsonb" NOT NULL,
    "publish_at" timestamp with time zone NOT NULL,
    "rrule" "text",
    "status" "text" DEFAULT 'queued'::"text",
    "platform_post_id" "text",
    "error_message" "text",
    "retry_count" integer DEFAULT 0,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "scheduled_posts_platform_check" CHECK (("platform" = ANY (ARRAY['whatsapp'::"text", 'instagram'::"text"]))),
    CONSTRAINT "scheduled_posts_publish_at_future" CHECK (("publish_at" > "created_at")),
    CONSTRAINT "scheduled_posts_retry_count_check" CHECK (("retry_count" >= 0)),
    CONSTRAINT "scheduled_posts_status_check" CHECK (("status" = ANY (ARRAY['queued'::"text", 'publishing'::"text", 'published'::"text", 'failed'::"text", 'cancelled'::"text"])))
);


ALTER TABLE "public"."scheduled_posts" OWNER TO "postgres";


COMMENT ON TABLE "public"."scheduled_posts" IS 'Scheduled posts for publication on social media platforms';



COMMENT ON COLUMN "public"."scheduled_posts"."content_json" IS 'Post content structure: {text: string, media: [{type: string, url: string}]}';



COMMENT ON COLUMN "public"."scheduled_posts"."rrule" IS 'Recurrence rule in iCal format (RFC 5545) for recurring posts';



COMMENT ON COLUMN "public"."scheduled_posts"."status" IS 'queued: waiting, publishing: in progress, published: success, failed: error, cancelled: user cancelled';



COMMENT ON COLUMN "public"."scheduled_posts"."platform_post_id" IS 'ID returned by platform API after successful publication';



CREATE TABLE IF NOT EXISTS "public"."secret_value" (
    "decrypted_secret" "text" COLLATE "pg_catalog"."C"
);


ALTER TABLE "public"."secret_value" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."social_accounts" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "platform" "public"."social_platform" NOT NULL,
    "account_id" character varying(255) NOT NULL,
    "username" character varying(100) NOT NULL,
    "display_name" character varying(255),
    "profile_url" character varying(500),
    "access_token" "text",
    "refresh_token" "text",
    "token_expires_at" timestamp with time zone,
    "is_active" boolean DEFAULT true,
    "user_id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."social_accounts" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."subscriptions" (
    "id" "text" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "status" "text",
    "source" "text" DEFAULT 'stripe'::"text",
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "price_id" "text",
    "quantity" integer DEFAULT 1,
    "cancel_at_period_end" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "current_period_start" timestamp with time zone DEFAULT "now"(),
    "current_period_end" timestamp with time zone DEFAULT "now"(),
    "ended_at" timestamp with time zone,
    "cancel_at" timestamp with time zone,
    "canceled_at" timestamp with time zone,
    "trial_start" timestamp with time zone,
    "trial_end" timestamp with time zone,
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "subscriptions_quantity_check" CHECK (("quantity" > 0)),
    CONSTRAINT "subscriptions_source_check" CHECK (("source" = ANY (ARRAY['stripe'::"text", 'whop'::"text"]))),
    CONSTRAINT "subscriptions_status_check" CHECK (("status" = ANY (ARRAY['trialing'::"text", 'active'::"text", 'canceled'::"text", 'incomplete'::"text", 'incomplete_expired'::"text", 'past_due'::"text", 'unpaid'::"text", 'paused'::"text"])))
);


ALTER TABLE "public"."subscriptions" OWNER TO "postgres";


COMMENT ON TABLE "public"."subscriptions" IS 'Abonnements sync depuis Stripe et Whop';



COMMENT ON COLUMN "public"."subscriptions"."id" IS 'ID abonnement (sub_xxx Stripe ou ID Whop)';



COMMENT ON COLUMN "public"."subscriptions"."source" IS 'Origine: stripe ou whop';



CREATE TABLE IF NOT EXISTS "public"."support_escalations" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "conversation_id" "uuid" NOT NULL,
    "message" "text" NOT NULL,
    "confidence" double precision NOT NULL,
    "reason" "text",
    "notified" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."support_escalations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_credits" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "credits_balance" integer DEFAULT 0,
    "subscription_id" "text",
    "plan_credits" integer DEFAULT 0,
    "storage_used_mb" double precision DEFAULT 0,
    "next_reset_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "user_credits_credits_balance_check" CHECK (("credits_balance" >= 0)),
    CONSTRAINT "user_credits_plan_credits_check" CHECK (("plan_credits" >= 0)),
    CONSTRAINT "user_credits_storage_used_mb_check" CHECK (("storage_used_mb" >= (0)::double precision))
);


ALTER TABLE "public"."user_credits" OWNER TO "postgres";


COMMENT ON TABLE "public"."user_credits" IS 'Soldes de crédits utilisateurs (logique métier)';



COMMENT ON COLUMN "public"."user_credits"."credits_balance" IS 'Solde actuel de crédits disponibles';



COMMENT ON COLUMN "public"."user_credits"."subscription_id" IS 'Lien vers abonnement actif (Stripe/Whop)';



COMMENT ON COLUMN "public"."user_credits"."plan_credits" IS 'Nombre de crédits du plan actuel (pour reset)';



CREATE TABLE IF NOT EXISTS "public"."users" (
    "id" "uuid" NOT NULL,
    "email" character varying(255) NOT NULL,
    "full_name" character varying(255),
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."users" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."web_widgets" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "name" character varying(255) NOT NULL,
    "widget_key" character varying(100) NOT NULL,
    "allowed_domains" "text"[],
    "settings" "jsonb" DEFAULT '{}'::"jsonb",
    "is_active" boolean DEFAULT true,
    "social_account_id" "uuid",
    "api_endpoint" character varying(500),
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."web_widgets" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."webhook_events" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "stripe_event_id" "text",
    "whop_event_id" "text",
    "event_type" "text" NOT NULL,
    "source" "text" NOT NULL,
    "processed_at" timestamp with time zone DEFAULT "now"(),
    "payload" "jsonb" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "webhook_events_source_check" CHECK (("source" = ANY (ARRAY['stripe'::"text", 'whop'::"text"])))
);


ALTER TABLE "public"."webhook_events" OWNER TO "postgres";


COMMENT ON TABLE "public"."webhook_events" IS 'Historique webhooks traités (idempotence)';



COMMENT ON COLUMN "public"."webhook_events"."stripe_event_id" IS 'ID événement Stripe pour éviter doublons';



COMMENT ON COLUMN "public"."webhook_events"."whop_event_id" IS 'ID événement Whop pour éviter doublons';



ALTER TABLE ONLY "public"."ai_decisions"
    ADD CONSTRAINT "ai_decisions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."ai_models"
    ADD CONSTRAINT "ai_models_openrouter_id_key" UNIQUE ("openrouter_id");



ALTER TABLE ONLY "public"."ai_models"
    ADD CONSTRAINT "ai_models_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."ai_rules"
    ADD CONSTRAINT "ai_rules_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."ai_rules"
    ADD CONSTRAINT "ai_rules_user_id_key" UNIQUE ("user_id");



ALTER TABLE ONLY "public"."ai_settings"
    ADD CONSTRAINT "ai_settings_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."ai_settings"
    ADD CONSTRAINT "ai_settings_user_id_key" UNIQUE ("user_id");



ALTER TABLE ONLY "public"."analytics_history"
    ADD CONSTRAINT "analytics_history_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."analytics"
    ADD CONSTRAINT "analytics_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."checkpoint_blobs"
    ADD CONSTRAINT "checkpoint_blobs_pkey" PRIMARY KEY ("thread_id", "checkpoint_ns", "channel", "version");



ALTER TABLE ONLY "public"."checkpoint_migrations"
    ADD CONSTRAINT "checkpoint_migrations_pkey" PRIMARY KEY ("v");



ALTER TABLE ONLY "public"."checkpoint_writes"
    ADD CONSTRAINT "checkpoint_writes_pkey" PRIMARY KEY ("thread_id", "checkpoint_ns", "checkpoint_id", "task_id", "idx");



ALTER TABLE ONLY "public"."checkpoints"
    ADD CONSTRAINT "checkpoints_pkey" PRIMARY KEY ("thread_id", "checkpoint_ns", "checkpoint_id");



ALTER TABLE ONLY "public"."conversation_messages"
    ADD CONSTRAINT "conversation_messages_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_social_account_id_external_conversation_id_key" UNIQUE ("social_account_id", "external_conversation_id");



ALTER TABLE ONLY "public"."credit_transactions"
    ADD CONSTRAINT "credit_transactions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."customers"
    ADD CONSTRAINT "customers_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."customers"
    ADD CONSTRAINT "customers_stripe_customer_id_key" UNIQUE ("stripe_customer_id");



ALTER TABLE ONLY "public"."faq_qa"
    ADD CONSTRAINT "faq_qa_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."knowledge_chunks"
    ADD CONSTRAINT "knowledge_chunks_document_id_chunk_index_key" UNIQUE ("document_id", "chunk_index");



ALTER TABLE ONLY "public"."knowledge_chunks"
    ADD CONSTRAINT "knowledge_chunks_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."knowledge_documents"
    ADD CONSTRAINT "knowledge_documents_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."post_runs"
    ADD CONSTRAINT "post_runs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."prices"
    ADD CONSTRAINT "prices_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."products"
    ADD CONSTRAINT "products_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."scheduled_posts"
    ADD CONSTRAINT "scheduled_posts_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."social_accounts"
    ADD CONSTRAINT "social_accounts_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."social_accounts"
    ADD CONSTRAINT "social_accounts_platform_account_id_key" UNIQUE ("platform", "account_id");



ALTER TABLE ONLY "public"."social_accounts"
    ADD CONSTRAINT "social_accounts_user_id_platform_key" UNIQUE ("user_id", "platform");



ALTER TABLE ONLY "public"."subscriptions"
    ADD CONSTRAINT "subscriptions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."support_escalations"
    ADD CONSTRAINT "support_escalations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."conversation_messages"
    ADD CONSTRAINT "unique_external_message_id" UNIQUE ("external_message_id");



ALTER TABLE ONLY "public"."user_credits"
    ADD CONSTRAINT "user_credits_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_credits"
    ADD CONSTRAINT "user_credits_user_id_key" UNIQUE ("user_id");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."web_widgets"
    ADD CONSTRAINT "web_widgets_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."web_widgets"
    ADD CONSTRAINT "web_widgets_widget_key_key" UNIQUE ("widget_key");



ALTER TABLE ONLY "public"."webhook_events"
    ADD CONSTRAINT "webhook_events_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."webhook_events"
    ADD CONSTRAINT "webhook_events_stripe_event_id_key" UNIQUE ("stripe_event_id");



ALTER TABLE ONLY "public"."webhook_events"
    ADD CONSTRAINT "webhook_events_whop_event_id_key" UNIQUE ("whop_event_id");



CREATE INDEX "checkpoint_blobs_thread_id_idx" ON "public"."checkpoint_blobs" USING "btree" ("thread_id");



CREATE INDEX "checkpoint_writes_thread_id_idx" ON "public"."checkpoint_writes" USING "btree" ("thread_id");



CREATE INDEX "checkpoints_thread_id_idx" ON "public"."checkpoints" USING "btree" ("thread_id");



CREATE INDEX "idx_ai_decisions_decision" ON "public"."ai_decisions" USING "btree" ("decision", "created_at" DESC);



CREATE INDEX "idx_ai_decisions_message" ON "public"."ai_decisions" USING "btree" ("message_id");



CREATE INDEX "idx_ai_decisions_user" ON "public"."ai_decisions" USING "btree" ("user_id", "created_at" DESC);



CREATE INDEX "idx_ai_models_is_active" ON "public"."ai_models" USING "btree" ("is_active");



CREATE INDEX "idx_ai_models_openrouter_id" ON "public"."ai_models" USING "btree" ("openrouter_id");



CREATE INDEX "idx_ai_rules_user" ON "public"."ai_rules" USING "btree" ("user_id");



CREATE INDEX "idx_analytics_content_id" ON "public"."analytics" USING "btree" ("content_id");



CREATE INDEX "idx_analytics_history_content_id" ON "public"."analytics_history" USING "btree" ("content_id");



CREATE INDEX "idx_analytics_history_recorded_at" ON "public"."analytics_history" USING "btree" ("recorded_at");



CREATE INDEX "idx_analytics_history_user_id" ON "public"."analytics_history" USING "btree" ("user_id");



CREATE INDEX "idx_analytics_platform" ON "public"."analytics" USING "btree" ("platform");



CREATE INDEX "idx_analytics_recorded_at" ON "public"."analytics" USING "btree" ("recorded_at");



CREATE INDEX "idx_conversation_messages_agent" ON "public"."conversation_messages" USING "btree" ("agent_id");



CREATE INDEX "idx_conversation_messages_conversation" ON "public"."conversation_messages" USING "btree" ("conversation_id");



CREATE INDEX "idx_conversation_messages_created_at" ON "public"."conversation_messages" USING "btree" ("created_at");



CREATE INDEX "idx_conversation_messages_direction" ON "public"."conversation_messages" USING "btree" ("direction");



CREATE INDEX "idx_conversation_messages_status" ON "public"."conversation_messages" USING "btree" ("status");



CREATE INDEX "idx_conversations_assigned_to" ON "public"."conversations" USING "btree" ("assigned_to");



CREATE INDEX "idx_conversations_automation_disabled" ON "public"."conversations" USING "btree" ("automation_disabled") WHERE ("automation_disabled" = true);



CREATE INDEX "idx_conversations_customer" ON "public"."conversations" USING "btree" ("customer_identifier");



CREATE INDEX "idx_conversations_last_message" ON "public"."conversations" USING "btree" ("last_message_at");



CREATE INDEX "idx_conversations_priority" ON "public"."conversations" USING "btree" ("priority");



CREATE INDEX "idx_conversations_social_account" ON "public"."conversations" USING "btree" ("social_account_id");



CREATE INDEX "idx_conversations_status" ON "public"."conversations" USING "btree" ("status");



CREATE INDEX "idx_credit_transactions_created_at" ON "public"."credit_transactions" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_credit_transactions_type" ON "public"."credit_transactions" USING "btree" ("transaction_type");



CREATE INDEX "idx_credit_transactions_user_created" ON "public"."credit_transactions" USING "btree" ("user_id", "created_at" DESC);



CREATE INDEX "idx_credit_transactions_user_id" ON "public"."credit_transactions" USING "btree" ("user_id");



CREATE INDEX "idx_faq_lang" ON "public"."faq_qa" USING "btree" ("lang_code");



CREATE INDEX "idx_faq_qa_active" ON "public"."faq_qa" USING "btree" ("is_active");



CREATE INDEX "idx_faq_qa_lang" ON "public"."faq_qa" USING "btree" ("lang_code");



CREATE INDEX "idx_faq_qa_user" ON "public"."faq_qa" USING "btree" ("user_id");



CREATE INDEX "idx_kc_doc" ON "public"."knowledge_chunks" USING "btree" ("document_id");



CREATE INDEX "idx_kc_embed" ON "public"."knowledge_chunks" USING "hnsw" ("embedding" "extensions"."vector_cosine_ops");



CREATE INDEX "idx_kc_lang" ON "public"."knowledge_chunks" USING "btree" ("lang_code");



CREATE INDEX "idx_kc_tsv" ON "public"."knowledge_chunks" USING "gin" ("tsv");



CREATE INDEX "idx_kd_lang" ON "public"."knowledge_documents" USING "btree" ("lang_code");



CREATE INDEX "idx_kd_user" ON "public"."knowledge_documents" USING "btree" ("user_id");



CREATE INDEX "idx_post_runs_scheduled_post" ON "public"."post_runs" USING "btree" ("scheduled_post_id", "created_at" DESC);



CREATE INDEX "idx_prices_active" ON "public"."prices" USING "btree" ("active");



CREATE INDEX "idx_prices_product_id" ON "public"."prices" USING "btree" ("product_id");



CREATE INDEX "idx_products_active" ON "public"."products" USING "btree" ("active");



CREATE INDEX "idx_products_source" ON "public"."products" USING "btree" ("source");



CREATE INDEX "idx_scheduled_posts_channel" ON "public"."scheduled_posts" USING "btree" ("channel_id", "created_at" DESC);



CREATE INDEX "idx_scheduled_posts_platform" ON "public"."scheduled_posts" USING "btree" ("platform", "status");



CREATE INDEX "idx_scheduled_posts_publish" ON "public"."scheduled_posts" USING "btree" ("publish_at", "status") WHERE ("status" = ANY (ARRAY['queued'::"text", 'publishing'::"text"]));



CREATE INDEX "idx_scheduled_posts_user" ON "public"."scheduled_posts" USING "btree" ("user_id", "created_at" DESC);



CREATE INDEX "idx_social_accounts_platform" ON "public"."social_accounts" USING "btree" ("platform");



CREATE INDEX "idx_social_accounts_user_id" ON "public"."social_accounts" USING "btree" ("user_id");



CREATE INDEX "idx_subscriptions_price_id" ON "public"."subscriptions" USING "btree" ("price_id");



CREATE INDEX "idx_subscriptions_source" ON "public"."subscriptions" USING "btree" ("source");



CREATE INDEX "idx_subscriptions_status" ON "public"."subscriptions" USING "btree" ("status");



CREATE INDEX "idx_subscriptions_user_id" ON "public"."subscriptions" USING "btree" ("user_id");



CREATE INDEX "idx_user_credits_subscription_id" ON "public"."user_credits" USING "btree" ("subscription_id");



CREATE INDEX "idx_user_credits_user_id" ON "public"."user_credits" USING "btree" ("user_id");



CREATE INDEX "idx_users_email" ON "public"."users" USING "btree" ("email");



CREATE INDEX "idx_web_widgets_active" ON "public"."web_widgets" USING "btree" ("is_active");



CREATE INDEX "idx_web_widgets_user_id" ON "public"."web_widgets" USING "btree" ("user_id");



CREATE INDEX "idx_web_widgets_widget_key" ON "public"."web_widgets" USING "btree" ("widget_key");



CREATE INDEX "idx_webhook_events_source" ON "public"."webhook_events" USING "btree" ("source");



CREATE INDEX "idx_webhook_events_stripe_id" ON "public"."webhook_events" USING "btree" ("stripe_event_id");



CREATE INDEX "idx_webhook_events_type" ON "public"."webhook_events" USING "btree" ("event_type");



CREATE INDEX "idx_webhook_events_whop_id" ON "public"."webhook_events" USING "btree" ("whop_event_id");



CREATE OR REPLACE TRIGGER "ai_rules_updated_at" BEFORE UPDATE ON "public"."ai_rules" FOR EACH ROW EXECUTE FUNCTION "public"."update_ai_rules_updated_at"();



CREATE OR REPLACE TRIGGER "scheduled_posts_updated_at" BEFORE UPDATE ON "public"."scheduled_posts" FOR EACH ROW EXECUTE FUNCTION "public"."update_scheduled_posts_updated_at"();



CREATE OR REPLACE TRIGGER "storage_decrement_faq_qa" AFTER DELETE ON "public"."faq_qa" FOR EACH ROW EXECUTE FUNCTION "private"."decrement_storage_usage"();



CREATE OR REPLACE TRIGGER "storage_decrement_knowledge_documents" AFTER DELETE ON "public"."knowledge_documents" FOR EACH ROW EXECUTE FUNCTION "private"."decrement_storage_usage"();



CREATE OR REPLACE TRIGGER "storage_increment_faq_qa" AFTER INSERT ON "public"."faq_qa" FOR EACH ROW EXECUTE FUNCTION "private"."increment_storage_usage"();



CREATE OR REPLACE TRIGGER "storage_increment_knowledge_documents" AFTER INSERT ON "public"."knowledge_documents" FOR EACH ROW EXECUTE FUNCTION "private"."increment_storage_usage"();



CREATE OR REPLACE TRIGGER "trg_01_sync_chunk_tsconfig" BEFORE INSERT OR UPDATE ON "public"."knowledge_chunks" FOR EACH ROW EXECUTE FUNCTION "private"."sync_chunk_tsconfig"();



CREATE OR REPLACE TRIGGER "trg_02_chunks_tsv_update" BEFORE INSERT OR UPDATE OF "content", "tsconfig" ON "public"."knowledge_chunks" FOR EACH ROW EXECUTE FUNCTION "private"."chunks_tsv_update"();



CREATE OR REPLACE TRIGGER "trg_update_conversation_last_message" AFTER INSERT ON "public"."conversation_messages" FOR EACH ROW EXECUTE FUNCTION "public"."update_conversation_last_message"();



CREATE OR REPLACE TRIGGER "trg_update_doc_lang" AFTER INSERT ON "public"."knowledge_documents" FOR EACH ROW EXECUTE FUNCTION "private"."update_user_doc_languages"();



CREATE OR REPLACE TRIGGER "trg_update_doc_lang_update" AFTER UPDATE OF "lang_code" ON "public"."knowledge_documents" FOR EACH ROW WHEN (("old"."lang_code" IS DISTINCT FROM "new"."lang_code")) EXECUTE FUNCTION "private"."update_user_doc_languages"();



CREATE OR REPLACE TRIGGER "update_ai_models_updated_at" BEFORE UPDATE ON "public"."ai_models" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_analytics_updated_at" BEFORE UPDATE ON "public"."analytics" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_conversation_messages_updated_at" BEFORE UPDATE ON "public"."conversation_messages" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_conversations_updated_at" BEFORE UPDATE ON "public"."conversations" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_customers_updated_at" BEFORE UPDATE ON "public"."customers" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_faq_qa_updated_at" BEFORE UPDATE ON "public"."faq_qa" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_knowledge_chunks_updated_at" BEFORE UPDATE ON "public"."knowledge_chunks" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_knowledge_documents_updated_at" BEFORE UPDATE ON "public"."knowledge_documents" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_prices_updated_at" BEFORE UPDATE ON "public"."prices" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_products_updated_at" BEFORE UPDATE ON "public"."products" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_social_accounts_updated_at" BEFORE UPDATE ON "public"."social_accounts" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_subscriptions_updated_at" BEFORE UPDATE ON "public"."subscriptions" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_user_credits_updated_at" BEFORE UPDATE ON "public"."user_credits" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_users_updated_at" BEFORE UPDATE ON "public"."users" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_web_widgets_updated_at" BEFORE UPDATE ON "public"."web_widgets" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



ALTER TABLE ONLY "public"."ai_decisions"
    ADD CONSTRAINT "ai_decisions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."ai_rules"
    ADD CONSTRAINT "ai_rules_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."ai_settings"
    ADD CONSTRAINT "ai_settings_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."analytics_history"
    ADD CONSTRAINT "analytics_history_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."conversation_messages"
    ADD CONSTRAINT "conversation_messages_agent_id_fkey" FOREIGN KEY ("agent_id") REFERENCES "public"."users"("id");



ALTER TABLE ONLY "public"."conversation_messages"
    ADD CONSTRAINT "conversation_messages_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."conversation_messages"
    ADD CONSTRAINT "conversation_messages_reply_to_message_id_fkey" FOREIGN KEY ("reply_to_message_id") REFERENCES "public"."conversation_messages"("id");



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_assigned_to_fkey" FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_social_account_id_fkey" FOREIGN KEY ("social_account_id") REFERENCES "public"."social_accounts"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."credit_transactions"
    ADD CONSTRAINT "credit_transactions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."customers"
    ADD CONSTRAINT "customers_id_fkey" FOREIGN KEY ("id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."faq_qa"
    ADD CONSTRAINT "faq_qa_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."knowledge_chunks"
    ADD CONSTRAINT "knowledge_chunks_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "public"."knowledge_documents"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."knowledge_documents"
    ADD CONSTRAINT "knowledge_documents_storage_object_id_fkey" FOREIGN KEY ("storage_object_id") REFERENCES "storage"."objects"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."knowledge_documents"
    ADD CONSTRAINT "knowledge_documents_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."post_runs"
    ADD CONSTRAINT "post_runs_scheduled_post_id_fkey" FOREIGN KEY ("scheduled_post_id") REFERENCES "public"."scheduled_posts"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."prices"
    ADD CONSTRAINT "prices_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."products"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."scheduled_posts"
    ADD CONSTRAINT "scheduled_posts_channel_id_fkey" FOREIGN KEY ("channel_id") REFERENCES "public"."social_accounts"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."scheduled_posts"
    ADD CONSTRAINT "scheduled_posts_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."social_accounts"
    ADD CONSTRAINT "social_accounts_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."subscriptions"
    ADD CONSTRAINT "subscriptions_price_id_fkey" FOREIGN KEY ("price_id") REFERENCES "public"."prices"("id");



ALTER TABLE ONLY "public"."subscriptions"
    ADD CONSTRAINT "subscriptions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."support_escalations"
    ADD CONSTRAINT "support_escalations_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."support_escalations"
    ADD CONSTRAINT "support_escalations_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."user_credits"
    ADD CONSTRAINT "user_credits_subscription_id_fkey" FOREIGN KEY ("subscription_id") REFERENCES "public"."subscriptions"("id");



ALTER TABLE ONLY "public"."user_credits"
    ADD CONSTRAINT "user_credits_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_id_fkey" FOREIGN KEY ("id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."web_widgets"
    ADD CONSTRAINT "web_widgets_social_account_id_fkey" FOREIGN KEY ("social_account_id") REFERENCES "public"."social_accounts"("id");



ALTER TABLE ONLY "public"."web_widgets"
    ADD CONSTRAINT "web_widgets_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



CREATE POLICY "Public read prices" ON "public"."prices" FOR SELECT USING (true);



CREATE POLICY "Public read products" ON "public"."products" FOR SELECT USING (true);



CREATE POLICY "Service role can insert ai_decisions" ON "public"."ai_decisions" FOR INSERT WITH CHECK (true);



CREATE POLICY "Service role can manage post_runs" ON "public"."post_runs" USING (true) WITH CHECK (true);



CREATE POLICY "Users can delete own ai_rules" ON "public"."ai_rules" FOR DELETE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can delete own scheduled_posts" ON "public"."scheduled_posts" FOR DELETE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can insert own ai_rules" ON "public"."ai_rules" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can insert own scheduled_posts" ON "public"."scheduled_posts" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can only acess their own ai_settings" ON "public"."ai_settings" TO "authenticated" USING (("user_id" = "auth"."uid"())) WITH CHECK (("user_id" = "auth"."uid"()));



CREATE POLICY "Users can update own ai_rules" ON "public"."ai_rules" FOR UPDATE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can update own scheduled_posts" ON "public"."scheduled_posts" FOR UPDATE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view own ai_decisions" ON "public"."ai_decisions" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view own ai_rules" ON "public"."ai_rules" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view own post_runs" ON "public"."post_runs" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM "public"."scheduled_posts"
  WHERE (("scheduled_posts"."id" = "post_runs"."scheduled_post_id") AND ("scheduled_posts"."user_id" = "auth"."uid"())))));



CREATE POLICY "Users can view own scheduled_posts" ON "public"."scheduled_posts" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users control their FAQ" ON "public"."faq_qa" TO "authenticated" USING ((( SELECT "auth"."uid"() AS "uid") = "user_id")) WITH CHECK ((( SELECT "auth"."uid"() AS "uid") = "user_id"));



CREATE POLICY "Users control their analytics history" ON "public"."analytics_history" USING (("auth"."uid"() = "user_id")) WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users control their conversations" ON "public"."conversations" USING ((EXISTS ( SELECT 1
   FROM "public"."social_accounts" "sa"
  WHERE (("sa"."id" = "conversations"."social_account_id") AND ("sa"."user_id" = "auth"."uid"()))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM "public"."social_accounts" "sa"
  WHERE (("sa"."id" = "conversations"."social_account_id") AND ("sa"."user_id" = "auth"."uid"())))));



CREATE POLICY "Users control their knowledge chunks" ON "public"."knowledge_chunks" TO "authenticated" USING ((EXISTS ( SELECT 1
   FROM "public"."knowledge_documents" "d"
  WHERE (("d"."id" = "knowledge_chunks"."document_id") AND ("d"."user_id" = ( SELECT "auth"."uid"() AS "uid")))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM "public"."knowledge_documents" "d"
  WHERE (("d"."id" = "knowledge_chunks"."document_id") AND ("d"."user_id" = ( SELECT "auth"."uid"() AS "uid"))))));



CREATE POLICY "Users control their knowledge documents" ON "public"."knowledge_documents" TO "authenticated" USING ((( SELECT "auth"."uid"() AS "uid") = "user_id")) WITH CHECK ((( SELECT "auth"."uid"() AS "uid") = "user_id"));



CREATE POLICY "Users control their messages" ON "public"."conversation_messages" USING ((EXISTS ( SELECT 1
   FROM ("public"."conversations" "c"
     JOIN "public"."social_accounts" "sa" ON (("sa"."id" = "c"."social_account_id")))
  WHERE (("c"."id" = "conversation_messages"."conversation_id") AND ("sa"."user_id" = "auth"."uid"()))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM ("public"."conversations" "c"
     JOIN "public"."social_accounts" "sa" ON (("sa"."id" = "c"."social_account_id")))
  WHERE (("c"."id" = "conversation_messages"."conversation_id") AND ("sa"."user_id" = "auth"."uid"())))));



CREATE POLICY "Users control their profile" ON "public"."users" USING (("auth"."uid"() = "id")) WITH CHECK (("auth"."uid"() = "id"));



CREATE POLICY "Users control their social accounts" ON "public"."social_accounts" USING (("auth"."uid"() = "user_id")) WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users control their widgets" ON "public"."web_widgets" USING (("auth"."uid"() = "user_id")) WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users manage own credits" ON "public"."user_credits" USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users manage their ai_settings" ON "public"."ai_settings" USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users manage their escalations" ON "public"."support_escalations" USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users view own customer data" ON "public"."customers" USING (("auth"."uid"() = "id"));



CREATE POLICY "Users view own subscriptions" ON "public"."subscriptions" FOR SELECT USING (("auth"."uid"() = "user_id"));



ALTER TABLE "public"."ai_decisions" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."ai_models" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "ai_models_select_all" ON "public"."ai_models" FOR SELECT USING (("is_active" = true));



ALTER TABLE "public"."ai_rules" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."ai_settings" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."analytics" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."analytics_history" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."checkpoint_blobs" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."checkpoint_migrations" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."checkpoint_writes" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."checkpoints" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."conversation_messages" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."conversations" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."credit_transactions" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "credit_transactions_select_own" ON "public"."credit_transactions" FOR SELECT USING (("auth"."uid"() = "user_id"));



ALTER TABLE "public"."customers" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."faq_qa" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."knowledge_chunks" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."knowledge_documents" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."post_runs" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."prices" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."products" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."scheduled_posts" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."secret_value" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."social_accounts" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."subscriptions" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."support_escalations" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."user_credits" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."users" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."web_widgets" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."webhook_events" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";









GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";
























































































































































































































































































































































































































































































































































































































GRANT ALL ON FUNCTION "public"."apply_trial_credits"("p_user_id" "uuid", "p_subscription_id" "text", "p_trial_credits" integer, "p_trial_end" timestamp with time zone) TO "anon";
GRANT ALL ON FUNCTION "public"."apply_trial_credits"("p_user_id" "uuid", "p_subscription_id" "text", "p_trial_credits" integer, "p_trial_end" timestamp with time zone) TO "authenticated";
GRANT ALL ON FUNCTION "public"."apply_trial_credits"("p_user_id" "uuid", "p_subscription_id" "text", "p_trial_credits" integer, "p_trial_end" timestamp with time zone) TO "service_role";



GRANT ALL ON FUNCTION "public"."backend_url"() TO "anon";
GRANT ALL ON FUNCTION "public"."backend_url"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."backend_url"() TO "service_role";



GRANT ALL ON FUNCTION "public"."cleanup_orphaned_storage_references"() TO "anon";
GRANT ALL ON FUNCTION "public"."cleanup_orphaned_storage_references"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."cleanup_orphaned_storage_references"() TO "service_role";



GRANT ALL ON FUNCTION "public"."consume_credits"("p_user_id" "uuid", "p_amount" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."consume_credits"("p_user_id" "uuid", "p_amount" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."consume_credits"("p_user_id" "uuid", "p_amount" integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."delete_user"("p_user_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."delete_user"("p_user_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."delete_user"("p_user_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_new_user_credits"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_new_user_credits"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_new_user_credits"() TO "service_role";






GRANT ALL ON FUNCTION "public"."mark_conversation_as_read"("conversation_uuid" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."mark_conversation_as_read"("conversation_uuid" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."mark_conversation_as_read"("conversation_uuid" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."mark_conversation_as_read"("p_conversation_id" "uuid", "p_user_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."mark_conversation_as_read"("p_conversation_id" "uuid", "p_user_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."mark_conversation_as_read"("p_conversation_id" "uuid", "p_user_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."mark_document_failed"("document_uuid" "uuid", "error_message" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."mark_document_failed"("document_uuid" "uuid", "error_message" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."mark_document_failed"("document_uuid" "uuid", "error_message" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."reset_cycle_credits"("p_subscription_id" "text", "p_plan_credits" integer, "p_period_end" timestamp with time zone) TO "anon";
GRANT ALL ON FUNCTION "public"."reset_cycle_credits"("p_subscription_id" "text", "p_plan_credits" integer, "p_period_end" timestamp with time zone) TO "authenticated";
GRANT ALL ON FUNCTION "public"."reset_cycle_credits"("p_subscription_id" "text", "p_plan_credits" integer, "p_period_end" timestamp with time zone) TO "service_role";



GRANT ALL ON FUNCTION "public"."resolve_plan_credits"("p_subscription_id" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."resolve_plan_credits"("p_subscription_id" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."resolve_plan_credits"("p_subscription_id" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."set_published_at"() TO "anon";
GRANT ALL ON FUNCTION "public"."set_published_at"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."set_published_at"() TO "service_role";



GRANT ALL ON FUNCTION "public"."supabase_url"() TO "anon";
GRANT ALL ON FUNCTION "public"."supabase_url"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."supabase_url"() TO "service_role";



GRANT ALL ON FUNCTION "public"."text_faq_search_v2"("p_user_id" "uuid", "query_text" "text", "query_lang" "text", "match_count" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."text_faq_search_v2"("p_user_id" "uuid", "query_text" "text", "query_lang" "text", "match_count" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."text_faq_search_v2"("p_user_id" "uuid", "query_text" "text", "query_lang" "text", "match_count" integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."text_knowledge_chunks_search_v2"("p_user_id" "uuid", "query_text" "text", "query_lang" "text", "match_count" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."text_knowledge_chunks_search_v2"("p_user_id" "uuid", "query_text" "text", "query_lang" "text", "match_count" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."text_knowledge_chunks_search_v2"("p_user_id" "uuid", "query_text" "text", "query_lang" "text", "match_count" integer) TO "service_role";









GRANT ALL ON FUNCTION "public"."update_ai_rules_updated_at"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_ai_rules_updated_at"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_ai_rules_updated_at"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_conversation_last_message"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_conversation_last_message"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_conversation_last_message"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_conversatios_message_groups_updated_at"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_conversatios_message_groups_updated_at"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_conversatios_message_groups_updated_at"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_message_groups_updated_at"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_message_groups_updated_at"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_message_groups_updated_at"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_scheduled_posts_updated_at"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_scheduled_posts_updated_at"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_scheduled_posts_updated_at"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "service_role";






GRANT ALL ON FUNCTION "public"."zero_credits_on_cancel"("p_subscription_id" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."zero_credits_on_cancel"("p_subscription_id" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."zero_credits_on_cancel"("p_subscription_id" "text") TO "service_role";






























GRANT ALL ON TABLE "public"."ai_decisions" TO "anon";
GRANT ALL ON TABLE "public"."ai_decisions" TO "authenticated";
GRANT ALL ON TABLE "public"."ai_decisions" TO "service_role";



GRANT ALL ON TABLE "public"."ai_models" TO "anon";
GRANT ALL ON TABLE "public"."ai_models" TO "authenticated";
GRANT ALL ON TABLE "public"."ai_models" TO "service_role";



GRANT ALL ON TABLE "public"."ai_rules" TO "anon";
GRANT ALL ON TABLE "public"."ai_rules" TO "authenticated";
GRANT ALL ON TABLE "public"."ai_rules" TO "service_role";



GRANT ALL ON TABLE "public"."ai_settings" TO "anon";
GRANT ALL ON TABLE "public"."ai_settings" TO "authenticated";
GRANT ALL ON TABLE "public"."ai_settings" TO "service_role";



GRANT ALL ON TABLE "public"."analytics" TO "anon";
GRANT ALL ON TABLE "public"."analytics" TO "authenticated";
GRANT ALL ON TABLE "public"."analytics" TO "service_role";



GRANT ALL ON TABLE "public"."analytics_history" TO "anon";
GRANT ALL ON TABLE "public"."analytics_history" TO "authenticated";
GRANT ALL ON TABLE "public"."analytics_history" TO "service_role";



GRANT ALL ON TABLE "public"."checkpoint_blobs" TO "anon";
GRANT ALL ON TABLE "public"."checkpoint_blobs" TO "authenticated";
GRANT ALL ON TABLE "public"."checkpoint_blobs" TO "service_role";



GRANT ALL ON TABLE "public"."checkpoint_migrations" TO "anon";
GRANT ALL ON TABLE "public"."checkpoint_migrations" TO "authenticated";
GRANT ALL ON TABLE "public"."checkpoint_migrations" TO "service_role";



GRANT ALL ON TABLE "public"."checkpoint_writes" TO "anon";
GRANT ALL ON TABLE "public"."checkpoint_writes" TO "authenticated";
GRANT ALL ON TABLE "public"."checkpoint_writes" TO "service_role";



GRANT ALL ON TABLE "public"."checkpoints" TO "anon";
GRANT ALL ON TABLE "public"."checkpoints" TO "authenticated";
GRANT ALL ON TABLE "public"."checkpoints" TO "service_role";



GRANT ALL ON TABLE "public"."conversation_messages" TO "anon";
GRANT ALL ON TABLE "public"."conversation_messages" TO "authenticated";
GRANT ALL ON TABLE "public"."conversation_messages" TO "service_role";



GRANT ALL ON TABLE "public"."conversations" TO "anon";
GRANT ALL ON TABLE "public"."conversations" TO "authenticated";
GRANT ALL ON TABLE "public"."conversations" TO "service_role";



GRANT ALL ON TABLE "public"."credit_transactions" TO "anon";
GRANT ALL ON TABLE "public"."credit_transactions" TO "authenticated";
GRANT ALL ON TABLE "public"."credit_transactions" TO "service_role";



GRANT ALL ON TABLE "public"."customers" TO "anon";
GRANT ALL ON TABLE "public"."customers" TO "authenticated";
GRANT ALL ON TABLE "public"."customers" TO "service_role";



GRANT ALL ON TABLE "public"."faq_qa" TO "anon";
GRANT ALL ON TABLE "public"."faq_qa" TO "authenticated";
GRANT ALL ON TABLE "public"."faq_qa" TO "service_role";



GRANT ALL ON TABLE "public"."knowledge_chunks" TO "anon";
GRANT ALL ON TABLE "public"."knowledge_chunks" TO "authenticated";
GRANT ALL ON TABLE "public"."knowledge_chunks" TO "service_role";



GRANT ALL ON TABLE "public"."knowledge_documents" TO "anon";
GRANT ALL ON TABLE "public"."knowledge_documents" TO "authenticated";
GRANT ALL ON TABLE "public"."knowledge_documents" TO "service_role";



GRANT ALL ON TABLE "public"."post_runs" TO "anon";
GRANT ALL ON TABLE "public"."post_runs" TO "authenticated";
GRANT ALL ON TABLE "public"."post_runs" TO "service_role";



GRANT ALL ON TABLE "public"."prices" TO "anon";
GRANT ALL ON TABLE "public"."prices" TO "authenticated";
GRANT ALL ON TABLE "public"."prices" TO "service_role";



GRANT ALL ON TABLE "public"."products" TO "anon";
GRANT ALL ON TABLE "public"."products" TO "authenticated";
GRANT ALL ON TABLE "public"."products" TO "service_role";



GRANT ALL ON TABLE "public"."rag_chunks" TO "anon";
GRANT ALL ON TABLE "public"."rag_chunks" TO "authenticated";
GRANT ALL ON TABLE "public"."rag_chunks" TO "service_role";



GRANT ALL ON TABLE "public"."scheduled_posts" TO "anon";
GRANT ALL ON TABLE "public"."scheduled_posts" TO "authenticated";
GRANT ALL ON TABLE "public"."scheduled_posts" TO "service_role";



GRANT ALL ON TABLE "public"."secret_value" TO "anon";
GRANT ALL ON TABLE "public"."secret_value" TO "authenticated";
GRANT ALL ON TABLE "public"."secret_value" TO "service_role";



GRANT ALL ON TABLE "public"."social_accounts" TO "anon";
GRANT ALL ON TABLE "public"."social_accounts" TO "authenticated";
GRANT ALL ON TABLE "public"."social_accounts" TO "service_role";



GRANT ALL ON TABLE "public"."subscriptions" TO "anon";
GRANT ALL ON TABLE "public"."subscriptions" TO "authenticated";
GRANT ALL ON TABLE "public"."subscriptions" TO "service_role";



GRANT ALL ON TABLE "public"."support_escalations" TO "anon";
GRANT ALL ON TABLE "public"."support_escalations" TO "authenticated";
GRANT ALL ON TABLE "public"."support_escalations" TO "service_role";



GRANT ALL ON TABLE "public"."user_credits" TO "anon";
GRANT ALL ON TABLE "public"."user_credits" TO "authenticated";
GRANT ALL ON TABLE "public"."user_credits" TO "service_role";



GRANT ALL ON TABLE "public"."users" TO "anon";
GRANT ALL ON TABLE "public"."users" TO "authenticated";
GRANT ALL ON TABLE "public"."users" TO "service_role";



GRANT ALL ON TABLE "public"."web_widgets" TO "anon";
GRANT ALL ON TABLE "public"."web_widgets" TO "authenticated";
GRANT ALL ON TABLE "public"."web_widgets" TO "service_role";



GRANT ALL ON TABLE "public"."webhook_events" TO "anon";
GRANT ALL ON TABLE "public"."webhook_events" TO "authenticated";
GRANT ALL ON TABLE "public"."webhook_events" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";






























RESET ALL;
