import redis
import os
import json
import logging
from datetime import datetime
import uuid
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

redis_server = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    decode_responses=True
)

def test_redis_connection():
    try:
        redis_server.ping()
        logger.info("Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False

def store_message_to_redis(session_id, llm_response):
    key = f"session:{session_id}:history"
    message = {
        'timestamp': datetime.utcnow().isoformat(),
        'context': llm_response
    }
    redis_server.lpush(key, json.dumps(message))
    
    
def get_conversation_history(session_id, limit=10):
    key = f"session:{session_id}:history"
    messages = redis_server.lrange(key, 0, limit-1)
    return [json.loads(msg) for msg in messages]
    

def clear_conversation_history(session_id):
    try:
        key = f"session:{session_id}:history"
        redis_server.delete(key)
        logger.info(f"Cleared conversation history for session {session_id}")
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")