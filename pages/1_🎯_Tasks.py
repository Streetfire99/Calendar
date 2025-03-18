import streamlit as st
import pandas as pd
from backend import delete_task, manage_tasks_with_chat

st.set_page_config(
    page_title="Tasks - Calendar Mentor",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Task Manager")

# Carica i progetti
try:
    projects = pd.read_csv('progetti.csv')
    
    # Visualizza i progetti esistenti
    if not projects.empty:
        st.header("Progetti Attivi")
        st.dataframe(projects)
    else:
        st.info("Nessun progetto attivo al momento")

    # Chat per gestire le task
    st.header("Gestisci Task via Chat")
    st.write("""
    Puoi gestire le tue task scrivendo in linguaggio naturale. Esempi:
    - "Aggiungi una nuova task per chiamare Marco domani"
    - "Modifica la task 'Progetto Website' e imposta lo stato come completato"
    - "Elimina la task 'Report Mensile'"
    - "Mostrami la lista delle task"
    - "Cambia lo stato della task 'Ringraziare Terlizzi' a conclusa"
    """)
    
    user_message = st.text_area("Scrivi il tuo messaggio:")
    if st.button("Invia"):
        if user_message:
            with st.spinner("Elaboro la tua richiesta..."):
                response = manage_tasks_with_chat(user_message)
                st.write(response)
                st.rerun()
        else:
            st.error("Per favore inserisci un messaggio")

    # Form per eliminare un task (metodo tradizionale)
    st.header("Elimina Task")
    with st.form("delete_task_form"):
        task_id = st.text_input("ID Task da eliminare")
        
        if st.form_submit_button("Elimina Task"):
            if task_id:
                delete_task(task_id)
                st.success("Task eliminato con successo!")
                st.rerun()
            else:
                st.error("Per favore inserisci l'ID del task da eliminare")

except FileNotFoundError:
    st.error("File progetti.csv non trovato. Assicurati che il file esista nella directory corretta.") 