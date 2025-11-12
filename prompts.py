import os
import openai
import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from redis_client import store_message_to_redis,get_conversation_history

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',  handlers=[logging.FileHandler('app.log', mode='w'), logging.StreamHandler()])


CONTEXT_PROMPT = """
You are a professional context deriver skilled in deriving and rephrasing text to convey the actual meaning not just words.\
   Your task is to rephrase the input text only in the original source language specified with the language code, not in English only if the source language is not English or any other language.\
You are to use the following universal guidelines:

GUIDELINES:
1.Resolve references (e.g., pronouns, ellipses) using conversation history.
2.Identify the domain and topic based on prior context.
3.Preserve tone, cultural nuance, and intent already established.
4.Ensure your output flows naturally and reads like a continuation of the conversation.
5.If the text contains idioms, figures of speech, or metaphors, rephrase them to convey the intended meaning in a way that is natural in the source language.
6.If the text in it's raw form conveys the meaning, do not change it. Only rephrase if the raw text does not convey the meaning.
7.Understand the topic and context of the conversation to ensure your interpretation is relevant and accurate.
8.Let your rephrasing reflect the original meaning, strictly preserving the source language.
7.Apply the following rules for interpreting proper names and cultural terms:
   UNIVERSAL NAMING & CULTURAL RULES:
      - Geographic Names:
         - Countries & Major Geographical Features: Translate using traditional, commonly accepted names in the target language.
         - Cities & Towns: Translate only when a widely accepted equivalent exists in the target language; otherwise, retain the original.
         - Street Names: Never translate street names. Preserve original spelling and diacritics.
      - Books, Media, and Songs:
         - Translate titles only if an official translation exists in the target language.
         - If no official version exists, retain the original title.
         - Band names and song names should not be translated
      - Cultural & Historical Sites:
         - Translate only if an official or widely accepted equivalent exists. Otherwise, keep the original and optionally clarify in parentheses.
      - Personal and Institutional Names:
         - Individual Names: Never translate people’s names. Preserve diacritics and original spelling when possible.
         - Royalty and Religious Figures: Use recognized localized forms when they exist (e.g., “Pope Francis”, “King Charles III”).
         - Papal Names: Use established translations (e.g., “Pape François” → “Pope Francis”).
      - Organizations and Acronyms:
         - International Organizations: Use official equivalents in the target language if they exist (e.g., “ONU” → “UN”).
         - Acronyms: Translate only when an accepted localized version exists. Otherwise, leave as-is.

When in Doubt:
If a name, place, or title does not have an official or widely accepted translation, preserve the original.\
   You may add the translated or clarified form in parentheses if needed to avoid confusion.\
   You are not supposed to hint that you are doing contextual interpretation.\
   You are to provide the rephrased text in the source language only.\
   Don't put anything else that is not relating to the rephrased text.\

You will return a JSON response containing:
- The original current chunk.
- The contextually clarified version of that chunk (in the source language).

Sample (Idiom use case):
User: "He gives me butterflies in my stomach."
You: "He makes me feel excited and nervous."


OUTPUT FORMAT:
current_chunk: <exact input text>,
current_contextual_text: <redefined meaning, rephrased ONLY in the source language>,

NOTE: Output JSON object containing values based on the above format.



Previous Conversation Context:
{conversation_text}

Current chunk to interpret:
{current_chunk}

Source Language:
{source_language}

"""

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm_model_name = 'gpt-4o'

llm = ChatOpenAI(model = llm_model_name, temperature=0.2)

def get_contextual_interpretation(session,context_prompt, current_chunk, source_lang):
   convo_history = get_conversation_history(session) # redis cache
   context_interpret= ChatPromptTemplate.from_template(context_prompt)
   context_chain = context_interpret | llm | JsonOutputParser() #chain
   response = context_chain.invoke( #invoke the chain
      {"conversation_text" : convo_history,
         "current_chunk": current_chunk,
         "source_language": source_lang})
   logging.info("Contextual Interpretation done")
   context_interpretation = response["current_contextual_text"]
   store_message_to_redis(session, context_interpretation)
   return response