class TranslationConfig:
    def __init__(self):
        self.supported_languages = {
            "en-US": "English (US)",
            "fr-FR": "French (FR)",
            "en": "English",
            "fr": "French",
            "es": "Spanish",
            "de": "German",
            "zh": "Chinese",
            "ar": "Arabic",
            "hi": "Hindi",
            "yo": "Yoruba",
            "ig": "Igbo",
            "ha": "Hausa"
        }
        self.default_source = "en-US"
        self.default_target = "fr"

    def get_source_language(self, requested=None):
        return requested if requested in self.supported_languages else self.default_source

    def get_target_language(self, requested=None):
        return requested if requested in self.supported_languages else self.default_target

    def get_all_languages(self):
        return self.supported_languages


translation_config = TranslationConfig()