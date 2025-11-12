# import eventlet
# eventlet.monkey_patch()

import os
import sys
import base64
import logging
import asyncio
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask import send_from_directory
from dotenv import load_dotenv
from speech_module import Speech
from translate_module import Translate
from detect_gender import detect_gender_from_audio
from collections import defaultdict
from translation_config import translation_config
from prompts_rti import get_contextual_interpretation, RTI_PROMPT
import concurrent.futures
import threading
from spitch import Spitch
import os
import logging
from redis_client import clear_conversation_history


load_dotenv()

executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config.from_object(Config)
app.config['MAIL_DEBUG'] = True
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Use Semaphore for Eventlet-safe locking
session_locks = defaultdict(lambda: threading.Lock())
buffers = defaultdict(list)

user_sessions = {}

speech = Speech()
translator = Translate()
client = Spitch()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@socketio.on('connect')
def handle_connect():
    socket_id = request.sid
    with session_locks[socket_id]:
        user_sessions[request.sid] = {
            'transcript': '',
            'translated_text': ''
        }
    logger.info(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    socket_id = request.sid
    if socket_id in user_sessions:
        with session_locks[socket_id]:
            user_sessions.pop(socket_id, None)
        session_locks.pop(socket_id, None)
    
    clear_conversation_history(socket_id)
    logger.info(f'Client disconnected: {request.sid}')

@socketio.on('message')
def handle_message(data):
    socket_id = request.sid
    executor.submit(process_audio_message, data, socket_id)

def process_audio_message(data, socket_id):
    try:
        # Extract base64 audio data
        audio_data_url = data['audio']['dataURL']
        header, encoded = audio_data_url.split(',', 1)
        audio_bytes = base64.b64decode(encoded)

         # Fetch requested languages from the frontend if sent
        requested_source = data['source_lang']
        requested_target = data['target_lang']

        #Set the source and target languages to the selected languages (if none, or error default)
        source_lang = translation_config.get_source_language(requested_source)
        target_lang = translation_config.get_target_language(requested_target)
        logging.info(f"Source lang: {source_lang}, Target lang: {target_lang}")

        # Speech-to-Text
        logger.info(f"[{socket_id}] Received audio length: {len(audio_bytes)}")
        transcript = speech.speech_to_text(audio_bytes, language_code=source_lang).strip()  

        if not transcript:
            return

        # Add this chunk to buffer
        buffers[socket_id].append(transcript)
        
        logging.info(f"----------Transcript: {transcript}")
        # call the contextual interpretation function
        MAX_CHUNKS = 3  # flush every 3 pieces

        if len(buffers[socket_id]) >= MAX_CHUNKS:
            # Combine buffered chunks
            batch_text = " ".join(buffers[socket_id])
            buffers[socket_id] = []  # reset buffer

            # Call Claude only once
            nw_transcript = get_contextual_interpretation(
                socket_id, RTI_PROMPT, batch_text, source_lang, target_lang
            )
            # nw_transcript = get_contextual_interpretation(socket_id, RTI_PROMPT, transcript, source_lang, target_lang)
            context_transcript = nw_transcript["refined_text"]
            # transcript = client.speech.transcribe(language='en', content=audio_bytes).text
            logger.info("\n=================================================================")
            logger.info(f"[{socket_id}] Raw: {nw_transcript["current_chunk"]}")
            logger.info(f"[{socket_id}] Transcript: {context_transcript}")
            logger.info("=================================================================")
        
        if not transcript.strip():
            socketio.emit('results', {
                'transcript': '',
                'translated_text': '',
                'audio_data_url': ''
            }, to=socket_id)
            return

        # Translate
        # translation = translator.translate_text(context_transcript, target_language_code=target_lang)
        # translation = client.text.translate(text=nw_transcript["current_chunk"], source=source_lang, target=target_lang).text
        # translated_text = translation['translated_text']
        translated_text= nw_transcript["tts_translation"]
        # detected_language = translation['detected_language_code']
        # logger.info(f"[{socket_id}] Detected Language: {detected_language}")
        
        logger.info(f"[{socket_id}] Translated Text: {translated_text}")
        

        # detect gender
        gender = detect_gender_from_audio(audio_bytes)
        # Text-to-Speech
        tts_audio = speech.text_to_speech(translated_text, gender, language_code=target_lang)

        # Generate silence
        num_samples = int(24000 * 1)
        silence = b'\x00' * num_samples * 2 * 1 # 1 second of silence at 24000 Hz, stereo, 16-bit

        # Combine silence and TTS audio
        tts_audio_with_pause = silence + tts_audio + silence

        tts_audio_base64 = base64.b64encode(tts_audio_with_pause).decode('utf-8')
        audio_data_url = f"data:audio/mp3;base64,{tts_audio_base64}"

        # Safely update user session
        with session_locks[socket_id]:
            if socket_id not in user_sessions:
                return  # User disconnected

            user_sessions[socket_id]['transcript'] += ' ' + context_transcript
            user_sessions[socket_id]['translated_text'] += ' ' + translated_text

        # Send results back to client
        socketio.emit('results', {
            'transcript': context_transcript,
            'translated_text': translated_text,
            'audio_data_url': audio_data_url
        }, to=socket_id)

    except Exception as e:
        logging.info(f"Error in background task: {e}")
        socketio.emit('error', {'message': str(e)}, to=socket_id)

if __name__ == '__main__':
    # Use eventlet's WSGI server
    socketio.run(app, host='0.0.0.0', port=5000)
