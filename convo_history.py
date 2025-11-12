from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from models import Session

def get_convo_history(session):
    convo_string = ""
    messages = []
    user_query = ""
    for message in session.chats:
        if message.is_user:
            convo_string += f"Customer: {message.message}\n"
            messages.append(HumanMessage(content=message.message))
            
            # Set user_query to the last message from the user
            user_query = message.message
        else:
            convo_string += f"AI: {message.message}\n"
            messages.append(AIMessage(content=message.message))
    
    return convo_string, messages, user_query