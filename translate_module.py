import os
from google.cloud import translate_v3 as translate

class Translate:
    def __init__(self):
        self.client = translate.TranslationServiceClient()
        self.project_id = os.getenv("PROJECT_ID")
        self.location = "us-central1"
        self.parent = f"projects/{self.project_id}/locations/{self.location}"

    def translate_text(self, text, target_language_code='en'):
        response = self.client.translate_text(
            parent=self.parent,
            contents=[text],
            mime_type='text/plain',
            target_language_code=target_language_code
        )
        print("Translation API response:", response)
        if response.translations:
            translation = response.translations[0]
            print(response.translations[0].translated_text)
            print("Detected language:", response.translations[0].detected_language_code)
            return {
                'translated_text': translation.translated_text,
                'detected_language_code': translation.detected_language_code
            }
        return {'translated_text': '', 'detected_language_code': ''}
