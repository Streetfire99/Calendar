import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

st.set_page_config(
    page_title="Wellness - Calendar Mentor",
    page_icon="🧘‍♀️",
    layout="wide"
)

st.title("🧘‍♀️ Wellness")

# Inizializza lo stato della sessione se non esiste
if 'wellness_data' not in st.session_state:
    try:
        st.session_state.wellness_data = pd.read_csv('wellness.csv')
    except FileNotFoundError:
        st.session_state.wellness_data = pd.DataFrame(columns=[
            'data', 'umore', 'energia', 'stress', 'sonno_ore', 'attivita_fisica_minuti',
            'meditazione_minuti', 'note'
        ])

# Form per aggiungere dati giornalieri
st.header("Registro Giornaliero")
with st.form("wellness_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        data = st.date_input("Data", value=datetime.now())
        umore = st.slider("Umore", 1, 10, 5)
        energia = st.slider("Livello di Energia", 1, 10, 5)
        stress = st.slider("Livello di Stress", 1, 10, 5)
    
    with col2:
        sonno_ore = st.number_input("Ore di Sonno", min_value=0.0, max_value=24.0, value=7.0, step=0.5)
        attivita_fisica = st.number_input("Minuti di Attività Fisica", min_value=0, value=30)
        meditazione = st.number_input("Minuti di Meditazione", min_value=0, value=10)
    
    note = st.text_area("Note sulla Giornata")
    
    if st.form_submit_button("Salva"):
        new_data = {
            'data': data,
            'umore': umore,
            'energia': energia,
            'stress': stress,
            'sonno_ore': sonno_ore,
            'attivita_fisica_minuti': attivita_fisica,
            'meditazione_minuti': meditazione,
            'note': note
        }
        
        # Aggiungi i nuovi dati
        new_data_df = pd.DataFrame([new_data])
        st.session_state.wellness_data = pd.concat([st.session_state.wellness_data, new_data_df], ignore_index=True)
        
        # Salva i dati nel file
        st.session_state.wellness_data.to_csv('wellness.csv', index=False)
        st.success("Dati salvati con successo!")
        st.rerun()

# Visualizza statistiche e grafici
if not st.session_state.wellness_data.empty:
    st.header("Le Tue Statistiche")
    
    # Converti la colonna data in datetime
    st.session_state.wellness_data['data'] = pd.to_datetime(st.session_state.wellness_data['data'])
    
    # Filtra per periodo
    periodo = st.selectbox("Seleziona Periodo", ["Ultima Settimana", "Ultimo Mese", "Ultimi 3 Mesi", "Tutto"])
    
    if periodo == "Ultima Settimana":
        data_filtrata = st.session_state.wellness_data[st.session_state.wellness_data['data'] >= datetime.now() - timedelta(days=7)]
    elif periodo == "Ultimo Mese":
        data_filtrata = st.session_state.wellness_data[st.session_state.wellness_data['data'] >= datetime.now() - timedelta(days=30)]
    elif periodo == "Ultimi 3 Mesi":
        data_filtrata = st.session_state.wellness_data[st.session_state.wellness_data['data'] >= datetime.now() - timedelta(days=90)]
    else:
        data_filtrata = st.session_state.wellness_data
    
    # Crea i grafici
    col1, col2 = st.columns(2)
    
    with col1:
        # Grafico dell'umore e energia
        fig_mood = px.line(data_filtrata, x='data', y=['umore', 'energia', 'stress'],
                          title='Andamento Umore, Energia e Stress')
        st.plotly_chart(fig_mood)
        
        # Statistiche del sonno
        st.subheader("Statistiche del Sonno")
        media_sonno = data_filtrata['sonno_ore'].mean()
        st.metric("Media Ore di Sonno", f"{media_sonno:.1f}")
    
    with col2:
        # Grafico attività fisica e meditazione
        fig_activity = px.bar(data_filtrata, x='data', y=['attivita_fisica_minuti', 'meditazione_minuti'],
                            title='Attività Fisica e Meditazione')
        st.plotly_chart(fig_activity)
        
        # Statistiche attività
        st.subheader("Statistiche Attività")
        col3, col4 = st.columns(2)
        with col3:
            media_attivita = data_filtrata['attivita_fisica_minuti'].mean()
            st.metric("Media Minuti Attività Fisica", f"{media_attivita:.0f}")
        with col4:
            media_meditazione = data_filtrata['meditazione_minuti'].mean()
            st.metric("Media Minuti Meditazione", f"{media_meditazione:.0f}")
    
    # Mostra le note più recenti
    st.header("Note Recenti")
    note_recenti = data_filtrata.sort_values('data', ascending=False).head(5)
    for _, row in note_recenti.iterrows():
        if row['note']:
            st.text(f"{row['data'].strftime('%d/%m/%Y')}: {row['note']}")
else:
    st.info("Inizia a registrare i tuoi dati di benessere per vedere le statistiche qui!") 