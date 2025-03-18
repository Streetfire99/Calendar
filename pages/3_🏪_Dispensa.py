import streamlit as st
import pandas as pd
from backend import load_pantry
from datetime import datetime

st.set_page_config(
    page_title="Dispensa - Calendar Mentor",
    page_icon="🏪",
    layout="wide"
)

st.title("🏪 Dispensa")

# Carica gli elementi della dispensa
try:
    pantry = load_pantry()
    
    # Converti le date di scadenza
    pantry['expiration_date'] = pd.to_datetime(pantry['expiration_date'], format='mixed')

    # Ordina per data di scadenza
    pantry = pantry.sort_values('expiration_date')
    
    # Visualizza gli elementi esistenti
    if not pantry.empty:
        st.header("Elementi in Dispensa")
        
        # Aggiungi filtri
        col1, col2 = st.columns(2)
        with col1:
            category_filter = st.multiselect(
                "Filtra per Categoria",
                options=sorted(pantry['category'].unique())
            )
        
        with col2:
            expiration_filter = st.date_input(
                "Filtra per Data di Scadenza",
                value=None
            )
        
        # Applica i filtri
        filtered_pantry = pantry.copy()
        if category_filter:
            filtered_pantry = filtered_pantry[filtered_pantry['category'].isin(category_filter)]
        
        if expiration_filter:
            # Converti le date in formato datetime
            filtered_pantry['expiration_date'] = pd.to_datetime(filtered_pantry['expiration_date'], format='%Y-%m-%d')
            expiration_filter = pd.to_datetime(expiration_filter)
            filtered_pantry = filtered_pantry[filtered_pantry['expiration_date'].dt.date <= expiration_filter.date()]
        
        # Visualizza la tabella filtrata
        st.dataframe(filtered_pantry)
        
        # Statistiche
        st.header("Statistiche Dispensa")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Totale Prodotti", len(pantry))
        
        with col2:
            products_by_category = pantry['category'].value_counts()
            st.write("Prodotti per Categoria")
            st.bar_chart(products_by_category)
        
        with col3:
            # Calcola i prodotti in scadenza nei prossimi 7 giorni
            pantry['expiration_date'] = pd.to_datetime(pantry['expiration_date'])  # Rimuovo il format specifico per permettere il parsing automatico
            today = pd.Timestamp.now().date()
            expiring_7_days = pantry[pantry['expiration_date'].dt.date <= (today + pd.Timedelta(days=7))]
            st.metric("Prodotti in Scadenza (7 giorni)", len(expiring_7_days))
            
    else:
        st.info("La dispensa è vuota")

    # Form per aggiungere un nuovo elemento
    st.header("Aggiungi Elemento")
    with st.form("new_item_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nome Prodotto")
            quantity = st.number_input("Quantità", min_value=0)
            unit = st.selectbox("Unità di Misura", ["pz", "g", "kg", "ml", "l"])
            
        with col2:
            category = st.selectbox("Categoria", ["Dispensa", "Frigo", "Freezer"])
            expiration_date = st.date_input("Data di Scadenza")
            min_quantity = st.number_input("Quantità Minima", min_value=0)
        
        if st.form_submit_button("Aggiungi alla Dispensa"):
            if name and quantity > 0:
                # Genera un nuovo ID
                new_id = 1 if pantry.empty else pantry['id'].max() + 1
                
                new_item = {
                    "id": new_id,
                    "name": name,
                    "quantity": quantity,
                    "unit": unit,
                    "category": category,
                    "expiration_date": expiration_date.strftime('%Y-%m-%d'),  # Formato consistente per le nuove date
                    "min_quantity": min_quantity
                }
                
                # Aggiungi il nuovo elemento al DataFrame e salva
                new_item_df = pd.DataFrame([new_item])
                updated_pantry = pd.concat([pantry, new_item_df], ignore_index=True)
                updated_pantry.to_csv('pantry.csv', index=False)
                
                st.success("Elemento aggiunto con successo!")
                st.rerun()
            else:
                st.error("Per favore compila tutti i campi obbligatori")

except FileNotFoundError:
    st.error("File pantry.csv non trovato. Assicurati che il file esista nella directory corretta.") 