import os
import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_anthropic import ChatAnthropic  # Claude integration
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from redis_client import store_message_to_redis, get_conversation_history

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('app.log', mode='w'), logging.StreamHandler()]
)

RTI_PROMPT = """
You are an intelligent bot tasked with interpreting real-time conversational input. 
Your goal is to process short text chunks (phrases or sentences), ensure coherence with the prior conversation, and output TWO VERSIONS of the clarified content.

Your task relies on BOTH:
1. The current input chunk.
2. The ongoing conversation history for continuity, context, and reference resolution.

Processing Instructions
For each input, you must create:

1. **REFINED SOURCE LANGUAGE VERSION**  
   - Rephrase or clarify the raw input so it becomes a coherent, natural continuation of the conversation.  
   - Use the source language only.  
   - Make minimal edits if the input is already clear.  
   - Resolve pronouns, references, and vague expressions using the conversation history.  
   - Preserve tone, domain accuracy, and style established so far.  

2. **TRANSLATION SCRIPT IN TARGET LANGUAGE (TTS-Ready)**  
   - Translate the clarified source version into target language for natural spoken delivery.  
   - Criteria:  
     - Natural conversational rhythm (not literal word-for-word).  
     - Retain precise terminology relevant to the topic.  
     - Add natural pauses using ellipses (...) where appropriate.  
     - Preserve the tone and voice of the speaker.  
     - Maintain coherence with prior context in conversation history.  
     - Avoid stage directions or annotations.  

Common Challenges to Address
- Speech-to-text errors: misheard words, missing punctuation, fragmented phrases.  
- Contextual gaps: incomplete thoughts, vague references (fill them using history).  
- Cultural adaptation: ensure output in target language reads like natural speech, not a rigid translation.  

Output Format (strict JSON):
{{
  "current_chunk": "<exact input text>",
  "refined_text": "<clarified version in source language>",
  "tts_translation": "<TTS-ready script in target language>"
}}


Conversation History:
{conversation_text}

Current Input:
{current_chunk}

Source Language:
{source_language}

Target Language:
{target_language}

"""

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Claude 3 Haiku is best for real-time, but you can switch to Sonnet/Opus
llm_model_name = "claude-3-haiku-20240307"
llm = ChatAnthropic(model=llm_model_name, temperature=0.2)

def get_contextual_interpretation(session, context_prompt, chunk, source_lang, target_lang):
   """
   Process a real-time input chunk using Claude, 
   leveraging conversation history for context.
   Produces:
   - refined_text (source language, clarified)
   - tts_translation (target language, TTS-ready)
   """

   # Get prior conversation history from Redis
   convo_history = get_conversation_history(session)

   # Build chain: prompt → Claude → JSON parser
   context_interpret = ChatPromptTemplate.from_template(context_prompt)
   context_chain = context_interpret | llm | JsonOutputParser()

   # Run the chain with inputs
   response = context_chain.invoke({
      "conversation_text": convo_history,
      "current_chunk": chunk,
      "source_language": source_lang,
      "target_language": target_lang
   })

   logging.info("Contextual Interpretation done")

   # Store refined text in Redis (so history builds on clarified version)
   refined_text = response["refined_text"]
   store_message_to_redis(session, refined_text)
   print(f"{refined_text}")
   return response
