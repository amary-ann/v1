import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models import Session, Convo, Request

logging.basicConfig(level=logging.INFO,  format='%(asctime)s - %(levelname)s - %(message)s',  handlers=[logging.FileHandler('app.log', mode='w'), logging.StreamHandler()])

async def interpret(request:Request):
    collection_name = os.getenv("MONGO_DB_COLLECTION")
    mongo_string = os.getenv("MONGO_CONNECTION_STRING")
    client = AsyncIOMotorClient(mongo_string)

    await init_beanie(database=client[collection_name], document_models=[Session])

    session = await Session.find_one({"user_id": request.user_id})
    conversation = Convo(conversation=request.conversation, is_user=True)

    if session:
        session.conversation.append(conversation)
        await session.save()
        logging.info("User conversation saved to session")
    else:

        session = Session(user_id=request.user_id)
        session.conversations=[conversation]
        await session.insert()
        logging.info("New session created and user conversation saved.")

    
