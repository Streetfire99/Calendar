import os
from dotenv import load_dotenv
from ibm_watson import SpeechToTextV1, TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from openai import OpenAI
import json
import pygame
import tempfile
import logging

# Configura il logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carica le variabili d'ambiente dal file .env
load_dotenv()

class VoiceAssistant:
    def __init__(self):
        try:
            # Inizializza Speech to Text
            stt_api_key = os.getenv('SPEECH_TO_TEXT_IAM_APIKEY')
            stt_url = os.getenv('SPEECH_TO_TEXT_URL')
            if not stt_api_key or not stt_url:
                raise ValueError("Credenziali Speech to Text mancanti nel file .env")
            
            stt_authenticator = IAMAuthenticator(stt_api_key)
            self.speech_to_text = SpeechToTextV1(authenticator=stt_authenticator)
            self.speech_to_text.set_service_url(stt_url)
            
            # Verifica che il servizio sia accessibile
            models = self.speech_to_text.list_models().get_result()
            logger.info(f"Modelli STT disponibili: {[m['name'] for m in models['models']]}")
            
            # Inizializza Text to Speech
            tts_api_key = os.getenv('TEXT_TO_SPEECH_IAM_APIKEY')
            tts_url = os.getenv('TEXT_TO_SPEECH_URL')
            if not tts_api_key or not tts_url:
                raise ValueError("Credenziali Text to Speech mancanti nel file .env")
            
            tts_authenticator = IAMAuthenticator(tts_api_key)
            self.text_to_speech = TextToSpeechV1(authenticator=tts_authenticator)
            self.text_to_speech.set_service_url(tts_url)
            
            # Verifica che il servizio sia accessibile
            voices = self.text_to_speech.list_voices().get_result()
            logger.info(f"Voci TTS disponibili: {[v['name'] for v in voices['voices']]}")

            # Inizializza OpenAI
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                raise ValueError("Chiave API OpenAI mancante nel file .env")
            self.openai_client = OpenAI(api_key=openai_api_key)
            
            # Inizializza pygame per la riproduzione audio
            pygame.mixer.init()
            logger.info("Inizializzazione VoiceAssistant completata con successo")
            
        except Exception as e:
            logger.error(f"Errore durante l'inizializzazione: {str(e)}")
            raise

    def transcribe_audio(self, audio_file):
        """Converte l'audio in testo usando Watson Speech to Text"""
        try:
            logger.info(f"Inizio trascrizione audio da {audio_file}")
            
            # Verifica che il file esista e non sia vuoto
            if not os.path.exists(audio_file):
                logger.error(f"File audio non trovato: {audio_file}")
                return ""
            
            if os.path.getsize(audio_file) == 0:
                logger.error("File audio vuoto")
                return ""
            
            with open(audio_file, 'rb') as audio:
                result = self.speech_to_text.recognize(
                    audio=audio,
                    content_type='audio/wav',
                    model='en-US_BroadbandModel',  # Usa il modello inglese che sappiamo essere disponibile
                    smart_formatting=True,
                    interim_results=False,
                    word_confidence=True,
                    timestamps=True
                ).get_result()
            
            logger.info(f"Risultato trascrizione: {result}")
            if result.get('results'):
                transcript = result['results'][0]['alternatives'][0]['transcript']
                confidence = result['results'][0]['alternatives'][0].get('confidence', 0)
                logger.info(f"Testo trascritto: {transcript} (confidenza: {confidence})")
                
                if confidence < 0.5:  # Se la confidenza è bassa
                    logger.warning(f"Bassa confidenza nella trascrizione: {confidence}")
                    return ""
                    
                return transcript
            
            logger.warning("Nessun risultato dalla trascrizione")
            return ""
            
        except Exception as e:
            logger.error(f"Errore durante la trascrizione: {str(e)}")
            return ""  # Invece di sollevare l'errore, ritorniamo stringa vuota

    def interpret_command(self, text):
        """Interpreta il comando usando OpenAI"""
        system_prompt = """Sei un assistente che interpreta comandi vocali per un'app calendario. 
        I possibili comandi sono:
        1. Aggiungere un evento (es. "aggiungi un evento per domani alle 15")
        2. Cercare una ricetta (es. "cerca una ricetta per la pasta al pesto")
        3. Gestire i task (es. "aggiungi un nuovo task per comprare il latte")
        4. Consultare la dispensa (es. "cosa c'è in dispensa")
        
        Restituisci un JSON con:
        - command_type: il tipo di comando (add_event, search_recipe, manage_task, check_pantry)
        - parameters: i parametri necessari per il comando
        - response: una risposta naturale da dare all'utente"""

        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
        )

        return json.loads(response.choices[0].message.content)

    def speak(self, text):
        """Converte il testo in audio usando Watson Text to Speech e lo riproduce"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            audio_result = self.text_to_speech.synthesize(
                text,
                voice='it-IT_FrancescaV3Voice',
                accept='audio/mp3'
            ).get_result()
            
            temp_file.write(audio_result.content)
            temp_file_path = temp_file.name

        # Riproduci l'audio
        pygame.mixer.music.load(temp_file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        # Pulisci il file temporaneo
        os.unlink(temp_file_path)

    def process_voice_command(self, audio_file):
        """Processa un comando vocale completo"""
        # Trascrivi l'audio in testo
        text = self.transcribe_audio(audio_file)
        if not text:
            return {"error": "Non ho capito il comando"}

        # Interpreta il comando
        interpretation = self.interpret_command(text)
        
        # Pronuncia la risposta
        self.speak(interpretation['response'])
        
        return interpretation 