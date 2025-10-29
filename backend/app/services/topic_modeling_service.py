"""
Topic Modeling Service using BERTopic + Gemini Embeddings
Handles model management and topic analysis

Architecture:
- Embeddings: Gemini gemini-embedding-001 (768 dims, task_type='clustering')
  Generated on-the-fly for new messages only (not stored)
- Models stored in Supabase Storage (.safetensors format)
- Topic naming: BERTopic's built-in representation_model using LangChain + Gemini
- Uses merge_models approach for incremental learning
- Daily fit + merge (Celery task at 3AM UTC)
- Top 10 topics stored in topic_analysis (overwritten daily)
"""

import os
import logging
import tempfile
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, timezone

import numpy as np
from pydantic import BaseModel, Field
from bertopic import BERTopic
from bertopic.representation import OpenAI
from openai import OpenAI as OpenAIClient

from app.db.session import get_db
from app.services.ingest_helpers import embed_texts

logger = logging.getLogger(__name__)

class TopicLabel(BaseModel):
    topic_id: int = Field(..., description="The ID of the topic")
    label: str = Field(..., description="The label of the topic")

class TopicModelingService:
    """Service for BERTopic-based topic modeling with Gemini"""

    def __init__(self, user_id: str):
        """
        Initialize Topic Modeling Service

        Args:
            user_id: User ID for scoping models and embeddings
        """
        self.user_id = user_id

        gemini_api_key = os.getenv("GEMINI_API_KEY")
        gemini_base_url = os.getenv("GEMINI_BASE_URL")
        if not gemini_api_key or not gemini_base_url:
            raise ValueError("GEMINI_API_KEY or GEMINI_BASE_URL not set")

        openai_client = OpenAIClient(
            api_key=gemini_api_key,
            base_url=gemini_base_url
        )

        self.representation_model = OpenAI(
            client=openai_client,
            model="gemini-2.5-flash",
            delay_in_seconds=1,
            chat=True
        )

        self.db = get_db()
        self.bucket_name = "bertopic-models"
        self.storage_prefix = f"{user_id}/"

    async def get_recent_messages_and_generate_embeddings(
        self,
        hours_lookback: Optional[int] = 24
    ) -> Tuple[List[str], np.ndarray, List[str]]:
        """
        Fetch recent inbound messages and generate embeddings on-the-fly

        Args:
            hours_lookback: Number of hours to look back (default: 24, None = all messages)

        Returns:
            Tuple of (message_ids, embeddings_array, message_texts)
        """
        try:
            date_end = datetime.now(timezone.utc)

            if hours_lookback is None:
                date_start = None
                logger.info(f"[TOPIC] Fetching ALL historical messages (no time limit)")
            else:
                date_start = date_end - timedelta(hours=hours_lookback)
                logger.info(f"[TOPIC] Fetching messages from {date_start} to {date_end}")

            accounts_result = self.db.table("social_accounts").select("id").eq("user_id", self.user_id).execute()

            if not accounts_result.data:
                logger.info(f"[TOPIC] No social accounts found for user {self.user_id}")
                return [], np.array([]), []

            social_account_ids = [acc["id"] for acc in accounts_result.data]

            conversations_result = self.db.table("conversations").select("id").in_("social_account_id", social_account_ids).execute()

            if not conversations_result.data:
                logger.info(f"[TOPIC] No conversations found for user {self.user_id}")
                return [], np.array([]), []

            conversation_ids = [conv["id"] for conv in conversations_result.data]

            # Step 3: Get messages for these conversations
            query = self.db.table("conversation_messages").select(
                "id, conversation_id, content"
            ).in_(
                "conversation_id", conversation_ids
            ).eq(
                "direction", "inbound"
            ).eq(
                "message_type", "text"
            )

            # Add time filters only if date_start is specified
            if date_start is not None:
                query = query.gte("created_at", date_start.isoformat())

            query = query.lte("created_at", date_end.isoformat()).order("created_at", desc=False)

            result = query.execute()

            if not result.data:
                timeframe = "all time" if hours_lookback is None else f"last {hours_lookback}h"
                logger.info(f"[TOPIC] No messages found in {timeframe}")
                return [], np.array([]), []

            message_ids = []
            message_texts = []
            for row in result.data:
                content = row.get("content") or row.get("text", "")
                if content and content.strip():
                    message_ids.append(str(row["id"]))
                    message_texts.append(content.strip())

            if len(message_texts) == 0:
                timeframe = "all time" if hours_lookback is None else f"last {hours_lookback}h"
                logger.info(f"[TOPIC] No valid text messages found in {timeframe} (all empty)")
                return [], np.array([]), []

            logger.info(f"[TOPIC] Found {len(message_texts)} valid messages")

            all_embeddings = []
            batch_size = 100

            for i in range(0, len(message_texts), batch_size):
                batch_texts = message_texts[i:i + batch_size]

                try:
                    batch_embeddings = embed_texts(
                        batch=batch_texts,
                        model='gemini-embedding-001',
                        task_type='clustering'
                    )
                    all_embeddings.extend(batch_embeddings)
                    logger.info(f"[TOPIC] Generated embeddings for batch {i//batch_size + 1}/{(len(message_texts)-1)//batch_size + 1}")

                except Exception as e:
                    logger.error(f"[TOPIC] Error generating embeddings for batch {i//batch_size + 1}: {e}")
                    raise

            embeddings_array = np.array(all_embeddings, dtype=np.float32)

            logger.info(f"[TOPIC] Generated {len(all_embeddings)} embeddings on-the-fly")
            return message_ids, embeddings_array, message_texts

        except Exception as e:
            logger.error(f"[TOPIC] Error fetching messages and generating embeddings: {e}")
            raise

    async def upload_model_to_storage(
        self,
        model: BERTopic,
        version: str
    ) -> str:
        """
        Upload BERTopic model to Supabase Storage

        Args:
            model: BERTopic model instance
            version: Version identifier (YYYYMMDD_HHMMSS format)

        Returns:
            Storage path where model was uploaded
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                model_path = os.path.join(temp_dir, "model")
                model.save(
                    model_path,
                    serialization="safetensors",
                    save_ctfidf=True,
                    save_embedding_model=False
                )

                files_to_upload = [
                    "model.safetensors",
                    "config.json"
                ]

                storage_path = f"{self.storage_prefix}{version}/"

                for filename in files_to_upload:
                    file_path = os.path.join(model_path, filename)

                    if not os.path.exists(file_path):
                        logger.warning(f"[TOPIC] File {filename} not found, skipping")
                        continue

                    with open(file_path, 'rb') as f:
                        file_data = f.read()

                    storage_file_path = f"{storage_path}{filename}"

                    self.db.storage.from_(self.bucket_name).upload(
                        path=storage_file_path,
                        file=file_data,
                        file_options={"content-type": "application/octet-stream"}
                    )

                    logger.info(f"[TOPIC] Uploaded {filename} to {storage_file_path}")

                logger.info(f"[TOPIC] Model uploaded successfully to {storage_path}")
                return storage_path

        except Exception as e:
            logger.error(f"[TOPIC] Error uploading model to storage: {e}")
            raise

    async def download_model_from_storage(
        self,
        version: str
    ) -> BERTopic:
        """
        Download BERTopic model from Supabase Storage

        Args:
            version: Version identifier (YYYYMMDD_HHMMSS format)

        Returns:
            BERTopic model instance
        """
        try:
            storage_path = f"{self.storage_prefix}{version}/"

            with tempfile.TemporaryDirectory() as temp_dir:
                model_dir = os.path.join(temp_dir, "model")
                os.makedirs(model_dir, exist_ok=True)

                files_to_download = [
                    "model.safetensors",
                    "config.json"
                ]

                for filename in files_to_download:
                    storage_file_path = f"{storage_path}{filename}"

                    try:
                        file_data = self.db.storage.from_(self.bucket_name).download(
                            storage_file_path
                        )

                        local_file_path = os.path.join(model_dir, filename)
                        with open(local_file_path, 'wb') as f:
                            f.write(file_data)

                        logger.info(f"[TOPIC] Downloaded {filename} from {storage_file_path}")

                    except Exception as e:
                        logger.error(f"[TOPIC] Error downloading {filename}: {e}")
                        raise

                model = BERTopic.load(model_dir, embedding_model=None)

                logger.info(f"[TOPIC] Model loaded successfully from {storage_path}")
                return model

        except Exception as e:
            logger.error(f"[TOPIC] Error downloading model from storage: {e}")
            raise

    # =====================================================
    # MODEL OPERATIONS (Fit, Merge, Transform)
    # =====================================================

    async def fit_initial_model(
        self,
        min_documents: int = 10
    ) -> Optional[str]:
        """
        Fit initial BERTopic model on ALL historical messages
        This is only called once when no model exists yet

        Args:
            min_documents: Minimum number of messages required (default: 10)

        Returns:
            Model version if successful, None otherwise
        """
        try:
            logger.info(f"[TOPIC] Starting initial model fit for user {self.user_id}")

            message_ids, embeddings, message_texts = await self.get_recent_messages_and_generate_embeddings(
                hours_lookback=None
            )

            if len(message_ids) < min_documents:
                logger.warning(
                    f"[TOPIC] Not enough documents for initial fit "
                    f"({len(message_ids)} < {min_documents})"
                )
                return None

            logger.info(f"[TOPIC] Fitting initial model on {len(message_texts)} documents...")

            topic_model = BERTopic(
                embedding_model=None,
                representation_model=self.representation_model,
                min_topic_size=5,
                nr_topics="auto",
                calculate_probabilities=False,
                verbose=True
            )

            topics, probs = topic_model.fit_transform(message_texts, embeddings)

            version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

            topic_labels = {}
            topic_info = topic_model.get_topic_info()
            for _, row in topic_info.iterrows():
                topic_id = int(row['Topic'])
                if topic_id == -1:
                    continue
                topic_labels[topic_id] = str(row['Name'])

            storage_path = await self.upload_model_to_storage(topic_model, version)

            date_range_end = datetime.now(timezone.utc)

            if message_texts:
                first_msg_result = self.db.table("conversation_messages").select("created_at").eq("id", message_ids[0]).execute()
                if first_msg_result.data:
                    date_range_start = datetime.fromisoformat(first_msg_result.data[0]["created_at"].replace('Z', '+00:00'))
                else:
                    date_range_start = date_range_end - timedelta(hours=24)
            else:
                date_range_start = date_range_end - timedelta(hours=24)

            self.db.table("bertopic_models").insert({
                "user_id": self.user_id,
                "model_version": version,
                "storage_path": storage_path,
                "total_topics": len(set(topics)) - (1 if -1 in topics else 0),
                "total_documents": len(message_texts),
                "date_range_start": date_range_start.isoformat(),
                "date_range_end": date_range_end.isoformat(),
                "is_active": True,
                "metadata": {
                    "min_topic_size": 5,
                    "outliers": list(topics).count(-1),
                    "topic_labels": topic_labels,
                    "is_initial_fit": True
                }
            }).execute()

            await self._save_topics_to_db(
                topic_model, message_texts, topics, topic_labels
            )

            logger.info(f"[TOPIC] Initial model fit complete: {version}")
            return version

        except Exception as e:
            logger.error(f"[TOPIC] Error fitting initial model: {e}")
            raise

    async def merge_and_update_model(
        self,
        min_documents: int = 10
    ) -> Optional[str]:
        """
        Daily fit + merge workflow

        1. Download yesterday's model (if exists)
        2. Fetch last 24h messages + generate embeddings on-the-fly
        3. Fit new model on these messages
        4. Merge with yesterday's model
        5. Transform only new messages
        6. Save top 10 topics (overwrite old ones)

        Args:
            min_documents: Minimum number of new messages required (default: 10)

        Returns:
            New model version if successful, None otherwise
        """
        try:
            logger.info(f"[TOPIC] Starting daily fit+merge for user {self.user_id}")

            active_model_result = self.db.table("bertopic_models").select(
                "model_version, storage_path"
            ).eq(
                "user_id", self.user_id
            ).eq(
                "is_active", True
            ).order("created_at", desc=True).limit(1).execute()

            _, new_embeddings, new_texts = await self.get_recent_messages_and_generate_embeddings(
                hours_lookback=24
            )

            if len(new_texts) < min_documents:
                logger.info(
                    f"[TOPIC] Not enough new messages for fit+merge "
                    f"({len(new_texts)} < {min_documents})"
                )
                return None

            logger.info(f"[TOPIC] Fitting new model on {len(new_texts)} messages from last 24h...")
            new_model = BERTopic(
                embedding_model=None,
                representation_model=self.representation_model,
                min_topic_size=5,
                nr_topics="auto",
                calculate_probabilities=False,
                verbose=True
            )
            new_model.fit(new_texts, new_embeddings)

            if not active_model_result.data:
                logger.info(f"[TOPIC] No active model found, using new model as initial")
                final_model = new_model
                old_version = None
            else:
                old_version = active_model_result.data[0]["model_version"]
                logger.info(f"[TOPIC] Downloading yesterday's model: {old_version}")

                existing_model = await self.download_model_from_storage(old_version)

                logger.info(f"[TOPIC] Merging models...")
                final_model = BERTopic.merge_models([existing_model, new_model])

            new_version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

            topics, _ = final_model.transform(new_texts, new_embeddings)

            topic_labels = {}
            topic_info = final_model.get_topic_info()
            for _, row in topic_info.iterrows():
                topic_id = int(row['Topic'])
                if topic_id == -1:
                    continue
                topic_labels[topic_id] = str(row['Name'])

            storage_path = await self.upload_model_to_storage(final_model, new_version)

            date_range_end = datetime.now(timezone.utc)
            date_range_start = date_range_end - timedelta(hours=24)

            metadata = {
                "min_topic_size": 5,
                "new_documents": len(new_texts),
                "outliers": list(topics).count(-1),
                "topic_labels": topic_labels
            }

            if old_version:
                metadata["merged_from"] = old_version

            self.db.table("bertopic_models").insert({
                "user_id": self.user_id,
                "model_version": new_version,
                "storage_path": storage_path,
                "total_topics": len(set(topics)) - (1 if -1 in topics else 0),
                "total_documents": len(new_texts),
                "date_range_start": date_range_start.isoformat(),
                "date_range_end": date_range_end.isoformat(),
                "is_active": True,
                "metadata": metadata
            }).execute()

            await self._save_topics_to_db(
                final_model, new_texts, topics, topic_labels
            )

            logger.info(f"[TOPIC] Daily fit+merge complete: {new_version}")
            return new_version

        except Exception as e:
            logger.error(f"[TOPIC] Error in daily fit+merge: {e}")
            raise


    # =====================================================
    # HELPER METHODS
    # =====================================================

    async def _save_topics_to_db(
        self,
        model: BERTopic,
        texts: List[str],
        topics: List[int],
        topic_labels: Optional[Dict[int, str]] = None
    ) -> None:
        """
        Save top 10 topics to topic_analysis table (overwrites old entries)

        Args:
            model: BERTopic model
            texts: Message texts
            topics: Topic assignments
            topic_labels: Generated topic labels
        """
        try:
            topic_info = model.get_topic_info()

            logger.info(f"[TOPIC] Deleting old topic_analysis entries for user {self.user_id}")
            self.db.table("topic_analysis").delete().eq("user_id", self.user_id).execute()

            topics_to_insert = []
            date_range_end = datetime.now(timezone.utc)
            date_range_start = date_range_end - timedelta(hours=24)

            count = 0
            for _, row in topic_info.iterrows():
                topic_id = int(row['Topic'])

                if topic_id == -1:
                    continue

                if count >= 10:
                    break

                topic_texts = [
                    texts[i] for i, t in enumerate(topics) if t == topic_id
                ]
                sample_messages = topic_texts[:5]

                topic_keywords = [word for word, _ in model.get_topic(topic_id)[:10]]

                if topic_labels and topic_id in topic_labels:
                    topic_label = topic_labels[topic_id]
                elif 'Name' in row:
                    topic_label = str(row['Name'])
                else:
                    topic_label = f"Topic {topic_id}: {', '.join(topic_keywords[:3])}"

                topics_to_insert.append({
                    "user_id": self.user_id,
                    "topic_id": topic_id,
                    "topic_label": topic_label,
                    "topic_keywords": topic_keywords,
                    "message_count": int(row['Count']),
                    "sample_messages": sample_messages,
                    "date_range_start": date_range_start.isoformat(),
                    "date_range_end": date_range_end.isoformat()
                })

                count += 1

            if topics_to_insert:
                self.db.table("topic_analysis").insert(topics_to_insert).execute()
                logger.info(f"[TOPIC] Saved top {len(topics_to_insert)} topics to database")
            else:
                logger.warning(f"[TOPIC] No topics to save (all were outliers)")

        except Exception as e:
            logger.error(f"[TOPIC] Error saving topics to DB: {e}")
            raise
