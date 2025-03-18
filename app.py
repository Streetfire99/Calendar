import streamlit as st
import pandas as pd
from backend import add_event, delete_task, chat_with_openai, load_events
from datetime import datetime, timedelta
import calendar
import time

# Importa il nuovo assistente vocale
from voice_assistant_v2 import VoiceAssistant

st.set_page_config(
    page_title="Calendar Mentor",
    page_icon="📅",
    layout="wide"
)

# Inizializza le variabili di stato per la registrazione
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False

# Inizializza l'assistente vocale
if 'voice_assistant' not in st.session_state:
    st.session_state.voice_assistant = VoiceAssistant()

# Inizializza la lista dei messaggi nella sessione se non esiste
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

# Funzione per aggiungere un messaggio alla chat
def add_chat_message(message, type="info"):
    st.session_state.chat_messages.append({
        "message": message,
        "type": type,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })

# Funzione per ottenere il colore del tag in base al tipo di evento
def get_event_color(event_type):
    color_map = {
        "general": "#039BE5",    # Blu chiaro
        "meeting": "#7986CB",    # Indaco
        "deadline": "#EF5350",   # Rosso
        "reminder": "#33B679",   # Verde
        "recipe": "#8E24AA",     # Viola
        "task": "#F4511E",       # Arancione
        "wellness": "#0B8043",   # Verde scuro
        "shopping": "#E67C73"    # Rosa
    }
    return color_map.get(event_type, "#616161")  # Grigio come default

# Stili CSS personalizzati
st.markdown("""
<style>
    /* Stile generale della pagina */
    .main {
        padding: 1rem;
        max-width: 100%;
    }
    
    /* Header del calendario */
    .calendar-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Stile del calendario */
    .calendar {
        width: 100%;
        table-layout: fixed;
        border-collapse: separate;
        border-spacing: 1px;
        background-color: #e0e0e0;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .calendar thead {
        background-color: #f8f9fa;
        position: sticky;
        top: 0;
        z-index: 1;
    }
    
    .calendar th {
        background-color: #f8f9fa;
        padding: 0.75rem;
        text-align: center;
        font-weight: 500;
        color: #5f6368;
        font-size: 0.9em;
        border: none;
    }
    
    .calendar td {
        background-color: white;
        padding: 0.25rem;
        vertical-align: top;
        position: relative;
        min-width: 100px;
        height: 120px;  /* Altezza fissa per le celle */
        border: 1px solid #e0e0e0;
        transition: background-color 0.2s ease;
        color: #333333;  /* Aggiungo colore del testo scuro */
    }
    
    .calendar tbody tr {
        border-bottom: 1px solid #e0e0e0;
    }
    
    .calendar td:hover {
        background-color: #f8f9fa;
    }
    
    /* Stile degli eventi */
    .event-container {
        margin-top: 20px;
        height: calc(100% - 25px);
        overflow-y: auto;
        scrollbar-width: thin;
        padding: 0 2px;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    
    .event-tag {
        margin: 1px 0;
        padding: 3px 6px;
        border-radius: 4px;
        font-size: 0.8em;
        color: white;
        display: block;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    .event-tag:hover {
        transform: scale(1.02);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        z-index: 1;
    }
    
    /* Stili specifici per la vista settimanale e giornaliera */
    .hour-cell {
        background-color: #f8f9fa;
        text-align: center;
        font-size: 0.85em;
        color: #5f6368;
        border-right: 1px solid #e0e0e0;
        white-space: nowrap;
    }
    
    /* Stili per le celle del calendario */
    .today {
        background-color: #e8f5e9 !important;
        border: 2px solid #1a73e8 !important;
    }
    
    .other-month {
        background-color: #fafafa;
    }
    
    .day-number {
        font-size: 0.9em;
        color: #5f6368;
        position: absolute;
        top: 5px;
        right: 5px;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
    }
    
    .today .day-number {
        background-color: #1a73e8;
        color: white;
    }
    
    /* Stili per la vista settimanale */
    .week-view td {
        height: 60px !important;
        padding: 0.25rem !important;
    }
    
    .week-view .event-tag {
        margin: 1px 0;
        padding: 2px 4px;
        font-size: 0.8em;
    }
    
    /* Stili per la vista giornaliera */
    .day-view td {
        height: 60px !important;
    }
    
    .day-view .event-tag {
        margin: 2px 0;
        padding: 4px 8px;
    }
    
    /* Stile della barra laterale */
    .sidebar {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-left: 1rem;
    }
    
    /* Stile dei form */
    .stForm {
        background-color: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Stile degli input */
    .stTextInput > div > div {
        padding: 0.5rem;
    }
    
    /* Stile dei bottoni */
    .stButton > button {
        width: 100%;
        background-color: #1a73e8;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        border: none;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #1557b0;
    }
    
    /* Stile degli expander */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 4px;
        padding: 0.5rem;
        font-size: 0.9em;
    }
    
    /* Scrollbar personalizzata */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    
    /* Chat container */
    .chat-container {
        position: fixed;
        bottom: 20px;
        left: 20px;
        width: 300px;
        max-height: 400px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 1000;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }
    
    /* Chat header */
    .chat-header {
        padding: 10px;
        background-color: #1a73e8;
        color: white;
        font-weight: 500;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Chat messages container */
    .chat-messages {
        padding: 10px;
        overflow-y: auto;
        max-height: 300px;
        background-color: #f8f9fa;
    }
    
    /* Individual message */
    .chat-message {
        margin-bottom: 8px;
        padding: 8px;
        border-radius: 8px;
        font-size: 0.9em;
        line-height: 1.4;
    }
    
    .message-info {
        background-color: #e3f2fd;
        border-left: 4px solid #1a73e8;
    }
    
    .message-success {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
    }
    
    .message-warning {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
    }
    
    .message-error {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
    
    /* Message timestamp */
    .message-timestamp {
        font-size: 0.8em;
        color: #666;
        float: right;
    }
</style>
""", unsafe_allow_html=True)

# Layout principale
st.markdown("<h1 style='text-align: center; color: #1a73e8; margin-bottom: 2rem;'>📅 Calendar Mentor</h1>", unsafe_allow_html=True)

# Chat a comparsa sulla destra
chat_html = """
<div style='position: fixed; right: 20px; top: 80px; width: 300px; max-height: 80vh; 
    background-color: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
    z-index: 1000; overflow: hidden; display: flex; flex-direction: column;'>
    <div style='padding: 10px; background-color: #1a73e8; color: white; font-weight: 500;
        display: flex; justify-content: space-between; align-items: center;'>
        🤖 Assistente AI
    </div>
    <div style='padding: 10px; overflow-y: auto; max-height: calc(80vh - 50px); background-color: #f8f9fa;'>
"""

# Aggiungi i messaggi alla chat
for msg in st.session_state.chat_messages[-10:]:  # Mostra solo gli ultimi 10 messaggi
    msg_style = {
        "info": "background-color: #e3f2fd; border-left: 4px solid #1a73e8;",
        "success": "background-color: #e8f5e9; border-left: 4px solid #4caf50;",
        "warning": "background-color: #fff3e0; border-left: 4px solid #ff9800;",
        "error": "background-color: #ffebee; border-left: 4px solid #f44336;"
    }
    chat_html += f"""
        <div style='margin-bottom: 8px; padding: 8px; border-radius: 8px; 
            font-size: 0.9em; line-height: 1.4; {msg_style[msg["type"]]}'>
            {msg['message']}
            <span style='font-size: 0.8em; color: #666; float: right;'>{msg['timestamp']}</span>
        </div>
    """

chat_html += """
    </div>
</div>
"""

st.markdown(chat_html, unsafe_allow_html=True)

# Aggiungi il pulsante del microfono nella barra superiore
mic_col1, mic_col2, mic_col3 = st.columns([2, 2, 2])

with mic_col2:
    # Verifica se PyAudio è disponibile
    try:
        import pyaudio
        pyaudio_available = True
    except ImportError:
        pyaudio_available = False
        st.warning("⚠️ La registrazione vocale non è disponibile in questo ambiente. PyAudio non è installato.")
    
    if pyaudio_available:
        # Informazioni sui permessi del microfono
        st.markdown("""
            <div style='margin-bottom: 10px; padding: 8px; border-radius: 4px; background-color: #e3f2fd; border-left: 4px solid #1a73e8;'>
                ℹ️ Per utilizzare il microfono:
                <ol style='margin: 5px 0; padding-left: 20px;'>
                    <li>Clicca su "Consenti" quando il browser chiede i permessi</li>
                    <li>Se non vedi la richiesta, clicca sull'icona 🔒 nella barra degli indirizzi</li>
                    <li>Seleziona "Consenti" per l'accesso al microfono</li>
                </ol>
            </div>
        """, unsafe_allow_html=True)

        # Pulsante del microfono
        mic_button = st.button(
            "🎤 Stop Registrazione" if st.session_state.is_recording else "🎤 Inizia Registrazione",
            type="primary" if st.session_state.is_recording else "secondary"
        )
        
        if mic_button:
            if not st.session_state.is_recording:
                st.session_state.is_recording = True
                add_chat_message("🎤 Iniziata la registrazione. Parla ora e premi Stop quando hai finito.", "info")
                st.rerun()
            else:
                st.session_state.is_recording = False
                try:
                    # Gestisci il comando vocale
                    response = st.session_state.voice_assistant.handle_voice_command()
                    if response:
                        add_chat_message("✅ Comando elaborato con successo!", "success")
                    else:
                        add_chat_message("⚠️ Nessun comando riconosciuto", "warning")
                except Exception as e:
                    add_chat_message(f"❌ Errore: {str(e)}", "error")
                st.rerun()

        # Mostra lo stato della registrazione
        if st.session_state.is_recording:
            st.markdown("🔴 **Registrazione in corso...**")

# Controlli del calendario
col_controls = st.columns([2, 6, 2])
with col_controls[0]:
    st.date_input("Seleziona data", key="date_selector", value=datetime.today(), label_visibility="collapsed")
with col_controls[1]:
    selected_date = st.session_state.date_selector
    st.markdown(f"<h2 style='text-align: center; color: #5f6368;'>{selected_date.strftime('%B %Y').title()}</h2>", unsafe_allow_html=True)
with col_controls[2]:
    view_type = st.selectbox("Tipo di vista", ["Mese", "Settimana", "Giorno"], index=0, label_visibility="collapsed")

# Layout principale del calendario
col_calendar, col_events = st.columns([4, 1])

with col_calendar:
    # Carica gli eventi
    events = load_events()
    if 'start_datetime' in events.columns:
        events['start_datetime'] = pd.to_datetime(events['start_datetime'], errors='coerce')
        
        # Funzioni helper per le diverse viste
        def get_week_dates(date):
            # Converte la data in datetime se è un oggetto date
            if isinstance(date, type(datetime.now().date())):
                date = datetime.combine(date, datetime.min.time())
            start = date - timedelta(days=date.weekday())
            return [(start + timedelta(days=i)).date() for i in range(7)]
        
        def get_day_hours():
            return [f"{i:02d}:00" for i in range(24)]
        
        if view_type == "Mese":
            # Vista mensile
            month_calendar = calendar.monthcalendar(selected_date.year, selected_date.month)
            days_of_week = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
            
            # Stili CSS per il calendario
            st.markdown("""
                <style>
                    .calendar {
                        width: 100%;
                        border-collapse: collapse;
                        background: white;
                    }
                    .calendar th {
                        padding: 8px;
                        text-align: center;
                        font-weight: 500;
                        color: #5f6368;
                        border-bottom: 1px solid #e0e0e0;
                    }
                    .calendar td {
                        padding: 8px;
                        border: 1px solid #e0e0e0;
                        vertical-align: top;
                        height: 100px;
                        width: 14.28%;
                        background-color: white;
                        color: #333333;  /* Aggiungo colore del testo scuro */
                    }
                    .calendar td:first-child {
                        border-left: none;
                    }
                    .calendar td:last-child {
                        border-right: none;
                    }
                    .calendar tr:first-child td {
                        border-top: none;
                    }
                    .calendar tr:last-child td {
                        border-bottom: none;
                    }
                    .calendar .today {
                        background-color: #e8f5e9;
                    }
                    .calendar .day-number {
                        font-size: 14px;
                        color: #333333;  /* Cambio colore del numero del giorno */
                        margin-bottom: 4px;
                        text-align: right;
                    }
                    .calendar .today .day-number {
                        color: #1a73e8;
                        font-weight: 500;
                    }
                    .calendar .events {
                        font-size: 12px;
                        line-height: 1.2;
                    }
                    .calendar .event {
                        background-color: var(--event-color);
                        color: #ffffff !important;  /* Forza il colore bianco */
                        padding: 2px 4px;
                        border-radius: 2px;
                        margin: 1px 0;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                        cursor: pointer;
                        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                        font-weight: 500;  /* Rendi il testo più spesso */
                        text-shadow: 0 1px 2px rgba(0,0,0,0.2);  /* Aggiungi ombra al testo */
                    }
                    .calendar .event:hover {
                        opacity: 0.9;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    }
                </style>
            """, unsafe_allow_html=True)
            
            # Genera il calendario in formato tabella
            calendar_html = '<table class="calendar">'
            
            # Header con i giorni della settimana
            calendar_html += '<tr>'
            for day in days_of_week:
                calendar_html += f'<th>{day}</th>'
            calendar_html += '</tr>'
            
            # Griglia del calendario
            for week in month_calendar:
                calendar_html += '<tr>'
                for day in week:
                    if day == 0:
                        calendar_html += '<td></td>'
                    else:
                        current_date = datetime(selected_date.year, selected_date.month, day).date()
                        is_today = current_date == datetime.today().date()
                        
                        calendar_html += f'<td class="{"today" if is_today else ""}">'
                        calendar_html += f'<div class="day-number">{day}</div>'
                        calendar_html += '<div class="events">'
                        
                        # Trova gli eventi per questo giorno
                        day_events = events[events['start_datetime'].dt.date == current_date]
                        if not day_events.empty:
                            day_events = day_events.sort_values('start_datetime')
                            for _, event in day_events.iterrows():
                                event_color = get_event_color(event['event_type'])
                                event_time = event['start_datetime'].strftime('%H:%M')
                                event_display = f"{event_time} {event['title']}" if event_time != "00:00" else event['title']
                                
                                calendar_html += f'<div class="event" style="--event-color: {event_color}">{event_display}</div>'
                        
                        calendar_html += '</div></td>'
                calendar_html += '</tr>'
            
            calendar_html += '</table>'
            st.markdown(calendar_html, unsafe_allow_html=True)

        elif view_type == "Settimana":
            # Vista settimanale
            week_dates = get_week_dates(selected_date)
            days_of_week = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
            
            st.markdown("""
                <style>
                    .week-calendar {
                        width: 100%;
                        border-collapse: collapse;
                        background: white;
                    }
                    .week-calendar th {
                        padding: 4px;
                        text-align: center;
                        font-weight: 500;
                        color: #5f6368;
                        border-bottom: 1px solid #e0e0e0;
                        font-size: 12px;
                    }
                    .week-calendar td {
                        padding: 2px;
                        border: 1px solid #e0e0e0;
                        vertical-align: top;
                        height: 40px;
                        width: 14.28%;
                    }
                    .week-calendar .time-column {
                        width: 40px;
                        background-color: #f8f9fa;
                        text-align: right;
                        padding-right: 4px;
                        color: #5f6368;
                        font-size: 11px;
                    }
                    .week-calendar .today {
                        background-color: #e8f5e9;
                    }
                    .week-calendar .event {
                        background-color: var(--event-color);
                        color: #ffffff !important;  /* Forza il colore bianco */
                        padding: 1px 3px;
                        border-radius: 2px;
                        margin: 1px 0;
                        font-size: 11px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                        cursor: pointer;
                        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                        font-weight: 500;  /* Rendi il testo più spesso */
                        text-shadow: 0 1px 2px rgba(0,0,0,0.2);  /* Aggiungi ombra al testo */
                    }
                    .week-calendar .event:hover {
                        opacity: 0.9;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    }
                </style>
            """, unsafe_allow_html=True)
            
            # Genera il calendario settimanale
            calendar_html = '<table class="week-calendar">'
            
            # Header con le date
            calendar_html += '<tr><th></th>'
            for i, date in enumerate(week_dates):
                is_today = date == datetime.today().date()
                day_name = days_of_week[i]
                day_number = date.day
                calendar_html += f'<th class="{"today" if is_today else ""}">{day_name}<br>{day_number}</th>'
            calendar_html += '</tr>'
            
            # Griglia delle ore (solo dalle 8 alle 20)
            hours = [f"{i:02d}:00" for i in range(8, 21)]
            for hour in hours:
                calendar_html += '<tr>'
                calendar_html += f'<td class="time-column">{hour}</td>'
                
                for date in week_dates:
                    is_today = date == datetime.today().date()
                    calendar_html += f'<td class="{"today" if is_today else ""}">'
                    
                    # Trova gli eventi per questa ora e data
                    hour_events = events[
                        (events['start_datetime'].dt.date == date) & 
                        (events['start_datetime'].dt.hour == int(hour.split(':')[0]))
                    ]
                    
                    if not hour_events.empty:
                        for _, event in hour_events.iterrows():
                            event_color = get_event_color(event['event_type'])
                            event_display = event['title']
                            calendar_html += f'<div class="event" style="--event-color: {event_color}">{event_display}</div>'
                    
                    calendar_html += '</td>'
                calendar_html += '</tr>'
            
            calendar_html += '</table>'
            st.markdown(calendar_html, unsafe_allow_html=True)

        elif view_type == "Giorno":
            # Vista giornaliera
            st.markdown("""
                <style>
                    .day-calendar {
                        width: 100%;
                        border-collapse: collapse;
                        background: white;
                    }
                    .day-calendar th {
                        padding: 8px;
                        text-align: center;
                        font-weight: 500;
                        color: #5f6368;
                        border-bottom: 1px solid #e0e0e0;
                    }
                    .day-calendar td {
                        padding: 8px;
                        border: 1px solid #e0e0e0;
                        vertical-align: top;
                        height: 60px;
                    }
                    .day-calendar .time-column {
                        width: 60px;
                        background-color: #f8f9fa;
                        text-align: right;
                        padding-right: 8px;
                        color: #5f6368;
                    }
                    .day-calendar .event {
                        background-color: var(--event-color);
                        color: #ffffff !important;  /* Forza il colore bianco */
                        padding: 4px 8px;
                        border-radius: 2px;
                        margin: 2px 0;
                        font-size: 12px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                        cursor: pointer;
                        font-weight: 500;  /* Rendi il testo più spesso */
                        text-shadow: 0 1px 2px rgba(0,0,0,0.2);  /* Aggiungi ombra al testo */
                    }
                    .day-calendar .event:hover {
                        opacity: 0.9;
                    }
                </style>
            """, unsafe_allow_html=True)
            
            # Genera il calendario giornaliero
            calendar_html = '<table class="day-calendar">'
            
            # Header con la data
            calendar_html += f'<tr><th colspan="2">{selected_date.strftime("%A, %d %B %Y")}</th></tr>'
            
            # Griglia delle ore
            hours = get_day_hours()
            for hour in hours:
                calendar_html += '<tr>'
                calendar_html += f'<td class="time-column">{hour}</td>'
                calendar_html += '<td>'
                
                # Trova gli eventi per questa ora
                hour_events = events[
                    (events['start_datetime'].dt.date == selected_date) & 
                    (events['start_datetime'].dt.hour == int(hour.split(':')[0]))
                ]
                
                if not hour_events.empty:
                    for _, event in hour_events.iterrows():
                        event_color = get_event_color(event['event_type'])
                        event_time = event['start_datetime'].strftime('%H:%M')
                        event_display = f"{event_time} - {event['title']}"
                        calendar_html += f'<div class="event" style="--event-color: {event_color}">{event_display}</div>'
                
                calendar_html += '</td></tr>'
            
            calendar_html += '</table>'
            st.markdown(calendar_html, unsafe_allow_html=True)

    with col_events:
        st.markdown("<div class='sidebar'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #5f6368; margin-bottom: 1rem;'>Eventi del Giorno</h3>", unsafe_allow_html=True)
        
        # Mostra gli eventi del giorno selezionato
        if 'start_datetime' in events.columns:
            day_events = events[events['start_datetime'].dt.date == selected_date]
            if not day_events.empty:
                for _, event in day_events.iterrows():
                    with st.expander(f"{event['start_datetime'].strftime('%H:%M')} - {event['title']}", expanded=True):
                        st.markdown(f"**Tipo:** {event['event_type'].capitalize()}")
                        st.markdown(f"**Descrizione:** {event['description']}")
                        if event['location']:
                            st.markdown(f"**Luogo:** {event['location']}")
            else:
                st.info("Nessun evento per questa data")

        # Form per aggiungere un nuovo evento
        st.markdown("<h3 style='color: #5f6368; margin: 1.5rem 0 1rem;'>Nuovo Evento</h3>", unsafe_allow_html=True)
        with st.form("new_event_form", clear_on_submit=True):
            event_name = st.text_input("Titolo", key="event_name")
            event_type = st.selectbox("Tipo", 
                                    ["general", "meeting", "deadline", "reminder", "recipe", 
                                     "task", "wellness", "shopping"])
            event_description = st.text_area("Descrizione", key="event_description")
            event_start = st.date_input("Data", value=selected_date)
            event_start_time = st.time_input("Ora")
            event_location = st.text_input("Luogo (opzionale)")
            
            if st.form_submit_button("Aggiungi Evento"):
                if event_name and event_description:
                    new_event = {
                        "id": len(events) + 1,
                        "title": event_name,
                        "start_datetime": f"{event_start} {event_start_time}",
                        "end_datetime": f"{event_start} {event_start_time}",
                        "description": event_description,
                        "event_type": event_type,
                        "color": get_event_color(event_type),
                        "is_all_day": False,
                        "recipe_id": None,
                        "location": event_location,
                        "attendees": None,
                        "recurring": None,
                        "created_at": pd.Timestamp.now(),
                        "updated_at": pd.Timestamp.now(),
                        "name": None
                    }
                    add_event(new_event)
                    st.success("✅ Evento aggiunto!")
                    st.rerun()
                else:
                    st.error("Compila i campi obbligatori")
        st.markdown("</div>", unsafe_allow_html=True) 