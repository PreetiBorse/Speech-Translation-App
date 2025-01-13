import streamlit as st
from dotenv import load_dotenv
import os
import azure.cognitiveservices.speech as speech_sdk
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

def main():
    try:
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


        # Configure speech
        speech_config = speech_sdk.SpeechConfig(ai_key, ai_region)

        # Streamlit UI elements with custom decorations
        st.set_page_config(page_title="SpeechVerse", page_icon="🎤")

        # Add a background color using linear gradient
        # Header and subheading with custom font
        st.markdown("<h1 style='text-align: center; color: #2C3E50;'>SpeechVerse</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #16A085;'>Real-time Speech Translation</h2>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #2C3E50;'>Speak in English, and this app will translate your speech to another language instantly.</h3>", unsafe_allow_html=True)

        # Language selection and button
        targetLanguage = st.selectbox("Select target language", ["fr", "es", "hi"])
        
        if st.button("Start Translation"):
            Translate(targetLanguage, translation_config, speech_config)

    except Exception as ex:
        st.error(f"Error: {ex}")

def Translate(targetLanguage, translation_config, speech_config):
    # Translate speech (from microphone)
    audio_config = speech_sdk.AudioConfig(use_default_microphone=True)
    translator = speech_sdk.translation.TranslationRecognizer(translation_config, audio_config=audio_config)
    st.write("Listening... Please speak now.")
    
    try:
        result = translator.recognize_once_async().get()
        st.write(f"Recognized: {result.text}")
        
        translation = result.translations[targetLanguage]
        st.write(f"Translated to {targetLanguage.upper()}: {translation}")

        # Transliterating for Hindi
        if targetLanguage == 'hi':
            transliterated_text = transliterate(translation, sanscript.DEVANAGARI, sanscript.ITRANS)
            st.write(f"Transliterated text: {transliterated_text}")
            speak_text = transliterated_text
            speech_config.speech_synthesis_voice_name = "hi-IN-AaravNeural"  # Hindi voice
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
        speak = speech_synthesizer.speak_text_async(speak_text).get()
        if speak.reason == speech_sdk.ResultReason.SynthesizingAudioCompleted:
            st.write("Translation spoken successfully!")
        elif speak.reason == speech_sdk.ResultReason.Canceled:
            cancellation_details = speak.cancellation_details
            st.write(f"Speech synthesis was canceled. Reason: {cancellation_details.reason}")
            if cancellation_details.reason == speech_sdk.CancellationReason.Error:
                st.write(f"Error details: {cancellation_details.error_details}")
        else:
            st.write(f"Speech synthesis failed: {speak.reason}")

    except Exception as ex:
        st.error(f"Exception during speech synthesis: {ex}")

if __name__ == "__main__":
    main()
