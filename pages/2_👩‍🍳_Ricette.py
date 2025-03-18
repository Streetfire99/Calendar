import streamlit as st
import pandas as pd
from backend import chat_with_openai

st.set_page_config(
    page_title="Ricette - Calendar Mentor",
    page_icon="👩‍🍳",
    layout="wide"
)

st.title("👩‍🍳 Ricette")

# Interfaccia per le ricette
st.header("Chiedi una Ricetta")
with st.form("recipe_form"):
    recipe_prompt = st.text_area("Cosa vorresti cucinare?", 
                               placeholder="Es: Vorrei una ricetta vegetariana veloce con le zucchine")
    
    if st.form_submit_button("Chiedi Ricetta"):
        if recipe_prompt:
            with st.spinner("Sto cercando la ricetta perfetta per te..."):
                try:
                    response = chat_with_openai(recipe_prompt)
                    st.success("Ecco la tua ricetta!")
                    st.write(response)
                except Exception as e:
                    st.error(f"Si è verificato un errore: {str(e)}")
        else:
            st.error("Per favore inserisci una richiesta per la ricetta")

# Carica le ricette salvate
try:
    recipes = pd.read_csv('recipes.csv')
    
    if not recipes.empty:
        st.header("Le Tue Ricette Salvate")
        st.dataframe(recipes)
    else:
        st.info("Non hai ancora ricette salvate")

except FileNotFoundError:
    st.info("Non hai ancora un database di ricette. Le ricette che salverai appariranno qui.") 