from dotenv import load_dotenv
import os
import azure.cognitiveservices.speech as speech_sdk
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

def main():
    try:
        global speech_config
        global translation_config

        # Load Configuration Settings
        load_dotenv()
        ai_key = os.getenv('SPEECH_KEY')
        ai_region = os.getenv('SPEECH_REGION')

        # Configure translation
        translation_config = speech_sdk.translation.SpeechTranslationConfig(ai_key, ai_region)
        translation_config.speech_recognition_language = 'en-US'
        translation_config.add_target_language('fr')
        translation_config.add_target_language('es')
        translation_config.add_target_language('hi')  # Add Hindi as a target language
        print('Ready to translate from', translation_config.speech_recognition_language)

        # Configure speech
        speech_config = speech_sdk.SpeechConfig(ai_key, ai_region)

        # Get user input for target language
        targetLanguage = ''
        while targetLanguage != 'quit':
            targetLanguage = input('\nEnter a target language\n fr = French\n es = Spanish\n hi = Hindi\n Enter Quit to stop\n').lower()
            if targetLanguage in translation_config.target_languages:
                Translate(targetLanguage)
            else:
                targetLanguage = 'quit'

    except Exception as ex:
        print("Error:", ex)

def Translate(targetLanguage):
    translation = ''

    # Translate speech (from microphone)
    audio_config = speech_sdk.AudioConfig(use_default_microphone=True)
    translator = speech_sdk.translation.TranslationRecognizer(translation_config, audio_config=audio_config)
    print("Speak now...")

    result = translator.recognize_once_async().get()
    print('Translating "{}"'.format(result.text))
    translation = result.translations[targetLanguage]
    print(f"Translated to {targetLanguage}: {translation}")

    # Transliterating for Hindi
    if targetLanguage == 'hi':
        transliterated_text = transliterate(translation, sanscript.DEVANAGARI, sanscript.ITRANS)
        transliterated_text = transliterated_text.replace('.', '')  # Remove full stop for Hindi
        speak_text = transliterated_text
        print(f"Transliterated text for speech synthesis: {transliterated_text}")
        # Use a supported Hindi neural voice
        speech_config.speech_synthesis_voice_name = "hi-IN-AaravNeural"  # Change this to any other Hindi voice if preferred
    else:
        speak_text = translation

        # Configure voice settings for other languages
        if targetLanguage == 'fr':
            speech_config.speech_synthesis_voice_name = "fr-FR-HenriNeural"
        elif targetLanguage == 'es':
            speech_config.speech_synthesis_voice_name = "es-ES-AlvaroNeural"
        else:
            speech_config.speech_synthesis_voice_name = "en-GB-RyanNeural"  # Default English voice

    # Configure audio output
    audio_output_config = speech_sdk.audio.AudioOutputConfig(use_default_speaker=True)
    speech_synthesizer = speech_sdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output_config)

    # Attempt speech synthesis
    try:
        print(f"Attempting to synthesize speech for: '{speak_text}'")
        speak = speech_synthesizer.speak_text_async(speak_text).get()
        if speak.reason == speech_sdk.ResultReason.SynthesizingAudioCompleted:
            print("Translated text spoken successfully!")
        elif speak.reason == speech_sdk.ResultReason.Canceled:
            cancellation_details = speak.cancellation_details
            print(f"Speech synthesis was canceled. Reason: {cancellation_details.reason}")
            if cancellation_details.reason == speech_sdk.CancellationReason.Error:
                print(f"Error details: {cancellation_details.error_details}")
        else:
            print(f"Speech synthesis failed: {speak.reason}")
    except Exception as ex:
        print("Exception during speech synthesis:", ex)


if __name__ == "__main__":
    main()
