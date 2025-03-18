import speech_recognition as sr
from gtts import gTTS
import os
import openai
import tempfile
from datetime import datetime, timedelta
import logging
from backend import add_event, delete_task, chat_with_openai, load_events

class VoiceAssistant:
    def __init__(self):
        # Configurazione logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Configurazione riconoscimento vocale
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 1000  # Ridotto da 4000 per maggiore sensibilità
        self.recognizer.dynamic_energy_threshold = True  # Abilita la regolazione automatica della soglia
        self.recognizer.pause_threshold = 1.0  # Aumentato per dare più tempo tra le parole
        self.recognizer.phrase_threshold = 0.3  # Ridotto per rilevare frasi più brevi
        self.recognizer.non_speaking_duration = 0.5  # Ridotto il tempo di silenzio richiesto
        
        # Configurazione sintesi vocale
        self.language = "it"
        
        # Configurazione OpenAI
        self.openai_client = openai.OpenAI()
        
        # Verifica disponibilità PyAudio
        try:
            import pyaudio
            self.pyaudio_available = True
        except ImportError:
            self.pyaudio_available = False
            self.logger.warning("PyAudio non disponibile. La registrazione vocale non sarà disponibile.")
        
        self.logger.info("Inizializzazione VoiceAssistant completata")

    def listen(self):
        """Ascolta l'input vocale e lo converte in testo."""
        if not self.pyaudio_available:
            self.logger.error("PyAudio non disponibile. La registrazione vocale non è supportata.")
            return None
            
        try:
            with sr.Microphone() as source:
                self.logger.info("In ascolto...")
                # Regola per il rumore ambientale
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                try:
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=None)
                    self.logger.info("Audio catturato, elaborazione in corso...")
                    text = self.recognizer.recognize_google(audio, language="it-IT")
                    self.logger.info(f"Testo riconosciuto: {text}")
                    return text
                except sr.WaitTimeoutError:
                    self.logger.warning("Timeout: nessun audio rilevato")
                    return None
                except sr.UnknownValueError:
                    self.logger.warning("Audio non riconosciuto")
                    return None
                except sr.RequestError as e:
                    self.logger.error(f"Errore nel servizio di riconoscimento: {e}")
                    return None
                except Exception as e:
                    self.logger.error(f"Errore durante l'ascolto: {e}")
                    return None
        except Exception as e:
            self.logger.error(f"Errore nell'inizializzazione del microfono: {e}")
            return None

    def speak(self, text):
        """Converte il testo in audio e lo riproduce."""
        try:
            # Crea un file temporaneo per l'audio
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                tts = gTTS(text=text, lang=self.language)
                tts.save(temp_file.name)
                # Riproduci l'audio
                os.system(f"afplay {temp_file.name}")
                # Pulisci il file temporaneo
                os.unlink(temp_file.name)
        except Exception as e:
            self.logger.error(f"Errore durante la sintesi vocale: {e}")

    def process_command(self, text):
        """Processa il comando vocale usando OpenAI e esegue le azioni necessarie."""
        try:
            # Crea il prompt per l'assistente
            system_prompt = """Sei un assistente del calendario che aiuta a gestire eventi e attività. 
            Analizza il comando dell'utente e restituisci una risposta JSON strutturata con le azioni da eseguire.
            Se l'utente menziona "domani", usa la data di domani. Se menziona "oggi", usa la data odierna.
            
            Esempio di comando: "aggiungi task per domani di comprare il latte"
            Esempio di risposta:
            {
                "action": "add_task",
                "data": {
                    "title": "Comprare il latte",
                    "description": "Lista della spesa: latte",
                    "date": "2025-03-16",
                    "time": "09:00",
                    "event_type": "task"
                },
                "response": "Ho aggiunto il task 'Comprare il latte' per domani alle 09:00."
            }
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
            
            # Ottieni la risposta da OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=250,
                temperature=0.7,
                response_format={ "type": "json_object" }
            )
            
            # Estrai la risposta JSON
            import json
            result = json.loads(response.choices[0].message.content.strip())
            self.logger.info(f"Risposta OpenAI strutturata: {result}")
            
            # Esegui l'azione appropriata
            if result["action"] == "add_task" or result["action"] == "add_event":
                # Gestisci le date relative
                from datetime import datetime, timedelta
                if "domani" in text.lower():
                    target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                elif "oggi" in text.lower():
                    target_date = datetime.now().strftime("%Y-%m-%d")
                else:
                    target_date = result["data"]["date"]
                
                # Prepara i dati dell'evento
                event_data = {
                    "id": len(load_events()) + 1,
                    "title": result["data"]["title"],
                    "description": result["data"]["description"],
                    "start_datetime": f"{target_date} {result['data'].get('time', '09:00')}",
                    "end_datetime": f"{target_date} {result['data'].get('time', '10:00')}",
                    "event_type": result["data"]["event_type"],
                    "is_all_day": False,
                    "location": "",
                    "attendees": None,
                    "recurring": None,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                
                # Aggiungi l'evento
                add_event(event_data)
                self.logger.info(f"Evento aggiunto: {event_data}")
            
            elif result["action"] == "delete_task":
                delete_task(result["data"]["title"])
                self.logger.info(f"Task eliminata: {result['data']['title']}")
            
            return result["response"]
            
        except Exception as e:
            self.logger.error(f"Errore durante l'elaborazione del comando: {e}")
            return "Mi dispiace, si è verificato un errore durante l'elaborazione del comando."

    def handle_voice_command(self):
        """Gestisce l'intero processo di comando vocale."""
        if not self.pyaudio_available:
            return "Mi dispiace, la registrazione vocale non è disponibile in questo ambiente. PyAudio non è installato."
            
        # Ascolta il comando
        text = self.listen()
        
        if text:
            # Processa il comando
            response = self.process_command(text)
            # Pronuncia la risposta
            self.speak(response)
            return response
        return None 