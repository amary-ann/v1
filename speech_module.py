import os
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech

class Speech:
    def __init__(self):
        self.sample_rate_hertz = 16000
        self.encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
        self.tts_client = texttospeech.TextToSpeechClient()
        self.stt_client = speech.SpeechClient()

    def speech_to_text(self, audio_content, language_code='en-US'):
        config = {
            "encoding": self.encoding,
            "sample_rate_hertz": self.sample_rate_hertz,
            "language_code": language_code,
            "model":"latest_long",
            # "enable_automatic_punctuation": True,
        }
        audio = {"content": audio_content}
        response = self.stt_client.recognize(config=config, audio=audio)
        if response.results:
            transcript = response.results[0].alternatives[0].transcript
            return transcript
        return ""

    def text_to_speech(self, text,gender, language_code='en-US'):
        if gender == "MALE":
            voice_gender = texttospeech.SsmlVoiceGender.MALE 
        else:
            voice_gender = texttospeech.SsmlVoiceGender.FEMALE  

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=voice_gender
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        response = self.tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return response.audio_content
