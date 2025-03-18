import pandas as pd
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
org_id = os.getenv("OPENAI_ORG_ID")

# Initialize OpenAI client with organization ID
client = None
if api_key and org_id:
    try:
        client = OpenAI(
            api_key=api_key,
            organization=org_id
        )
    except Exception as e:
        print(f"Error initializing OpenAI client: {str(e)}")
        client = None

def load_events():
    try:
        return pd.read_csv('events.csv')
    except FileNotFoundError:
        return pd.DataFrame(columns=['id', 'title', 'start_datetime', 'end_datetime', 'description', 'event_type', 'color', 'is_all_day', 'recipe_id', 'location', 'attendees', 'recurring', 'created_at', 'updated_at', 'name'])

def load_pantry():
    try:
        return pd.read_csv('pantry.csv')
    except FileNotFoundError:
        return pd.DataFrame()

def load_projects():
    try:
        return pd.read_csv('progetti.csv')
    except FileNotFoundError:
        return pd.DataFrame()

def load_recipes():
    try:
        return pd.read_csv('recipes.csv')
    except FileNotFoundError:
        return pd.DataFrame()

def _save_recipes(df):
    df.to_csv('recipes.csv', index=False)

def add_event(event):
    events = load_events()
    # Converti l'evento in un DataFrame
    event_df = pd.DataFrame([event])
    
    # Usa pd.concat per unire i DataFrame
    events = pd.concat([events, event_df], ignore_index=True)
    
    # Controlla il numero di colonne nel DataFrame
    expected_columns = ['id', 'title', 'start_datetime', 'end_datetime', 'description', 'event_type', 'color', 'is_all_day', 'recipe_id', 'location', 'attendees', 'recurring', 'created_at', 'updated_at', 'name']
    
    # Se il numero di colonne non corrisponde, non impostare i nomi delle colonne
    if len(events.columns) == len(expected_columns):
        events.columns = expected_columns
    
    # Gestisci i formati misti per 'start_datetime' e 'end_datetime'
    def parse_datetime(dt):
        if pd.isna(dt):
            return pd.NaT
        try:
            return pd.to_datetime(dt)
        except ValueError:
            # Se non riesce a convertire, prova ad aggiungere un'ora di default
            return pd.to_datetime(dt + ' 00:00:00', errors='coerce')

    events['start_datetime'] = events['start_datetime'].apply(parse_datetime)
    events['end_datetime'] = events['end_datetime'].apply(parse_datetime)

    # Ordina gli eventi per data e ora di inizio
    events = events.sort_values(by='start_datetime')
    
    events.to_csv('events.csv', index=False)

def delete_task(task_id):
    projects = load_projects()
    projects = projects[projects['id'] != task_id]
    projects.to_csv('progetti.csv', index=False)

def chat_with_openai(prompt):
    """Funzione per interagire con ChatGPT"""
    if client is None:
        return "Mi dispiace, il servizio OpenAI non è configurato correttamente. Controlla le variabili d'ambiente."
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in chat_with_openai: {str(e)}")
        return "Mi dispiace, c'è stato un errore nella comunicazione con ChatGPT."

def search_recipes(query):
    """Cerca ricette usando OpenAI per interpretare la query"""
    if client is None:
        return []
        
    try:
        # Usa OpenAI per interpretare la query
        response = chat_with_openai(query)
        
        # Pulisci la risposta JSON
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        # Prova a parsare la risposta JSON
        search_params = json.loads(response)
        
        return search_params  # Restituisce i parametri di ricerca
    except Exception as e:
        print(f"Errore nella ricerca ricette: {e}")
        return []

def manage_tasks_with_chat(user_message):
    """Gestisce le task tramite chat con GPT"""
    if client is None:
        return "Mi dispiace, il servizio OpenAI non è configurato correttamente. Controlla le variabili d'ambiente."
        
    system_prompt = """Sei un assistente che aiuta a gestire le task. Puoi eseguire le seguenti azioni:
    - AGGIUNGI: Aggiunge una nuova task
    - MODIFICA: Modifica una task esistente
    - ELIMINA: Elimina una task
    - LISTA: Mostra la lista delle task
    - STATO: Cambia lo stato di una task
    
    Analizza il messaggio dell'utente e restituisci un JSON con:
    {
        "action": "AGGIUNGI|MODIFICA|ELIMINA|LISTA|STATO",
        "data": {
            "nome": "nome task",
            "descrizione": "descrizione task",
            "stato": "da iniziare|in corso|completato|conclusa",
            "data_inizio": "YYYY-MM-DD",
            "data_fine": "YYYY-MM-DD"
        }
    }
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        
        result = response.choices[0].message.content
        # Pulisci la risposta JSON
        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.endswith("```"):
            result = result[:-3]
        result = result.strip()
        
        action_data = json.loads(result)
        
        # Esegui l'azione richiesta
        if action_data["action"] == "AGGIUNGI":
            df = pd.read_csv('progetti.csv')
            new_task = pd.DataFrame([action_data["data"]])
            df = pd.concat([df, new_task], ignore_index=True)
            df.to_csv('progetti.csv', index=False)
            return "Task aggiunta con successo!"
            
        elif action_data["action"] == "MODIFICA":
            df = pd.read_csv('progetti.csv')
            task_name = action_data["data"]["nome"]
            df.loc[df['Nome'] == task_name] = action_data["data"]
            df.to_csv('progetti.csv', index=False)
            return "Task modificata con successo!"
            
        elif action_data["action"] == "ELIMINA":
            df = pd.read_csv('progetti.csv')
            task_name = action_data["data"]["nome"]
            df = df[df['Nome'] != task_name]
            df.to_csv('progetti.csv', index=False)
            return "Task eliminata con successo!"
            
        elif action_data["action"] == "LISTA":
            df = pd.read_csv('progetti.csv')
            return df.to_string()
            
        elif action_data["action"] == "STATO":
            df = pd.read_csv('progetti.csv')
            task_name = action_data["data"]["nome"]
            new_status = action_data["data"]["stato"]
            df.loc[df['Nome'] == task_name, 'Stato'] = new_status
            df.to_csv('progetti.csv', index=False)
            return f"Stato della task '{task_name}' aggiornato a '{new_status}'"
            
        return "Azione non riconosciuta"
        
    except Exception as e:
        print(f"Errore nella gestione delle task: {str(e)}")
        return "Mi dispiace, c'è stato un errore nella gestione delle task." 