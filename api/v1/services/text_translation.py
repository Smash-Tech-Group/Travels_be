from deep_translator import GoogleTranslator


class TextTranslationService:
    
    def translate_text(self, source_text: str, target_language: str):
        ''''This function uses GoogleTranslator to translate provided text'''

        translator = GoogleTranslator(target=target_language)
        return translator.translate(source_text)
    

translation_service = TextTranslationService()
