import os
from langgraph.checkpoint.redis import RedisSaver
from dotenv import load_dotenv
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

ttl_config = {
   "default_ttl": 60,
   "refresh_on_read": True
}

CHECKPOINTER_REDIS = RedisSaver(REDIS_URL, ttl=ttl_config)
CHECKPOINTER_REDIS.setup()

