import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from openai import OpenAI
import re
import os
from geopy.distance import geodesic

# --- Workaround für ChromaDB auf Streamlit Cloud ---
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# --- KONFIGURATION & LOGIN ---
st.set_page_config(page_title="Swiss Electro Matcher", layout="wide")

# Passwort-Abfrage für den Zugriff
def check_password():
    if "auth" not in st.session_state:
        st.session_state.auth = False
    if not st.session_state.auth:
        pwd = st.text_input("Passwort eingeben", type="password")
        if pwd == "Elektro2024": # Hier dein Wunschpasswort setzen
            st.session_state.auth = True
            st.rerun()
        return False
    return True

if check_password():
    # OpenAI Client Setup
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    except:
        st.error("Bitte OPENAI_API_KEY in den Streamlit Secrets hinterlegen!")
        st.stop()

    # PLZ Daten laden
    @st.cache_data
    def load_plz():
        df = pd.read_csv('ch_plz.csv', sep=';')
        return df[['PLZ4', 'Ortschaftsname', 'E', 'N']].drop_duplicates('PLZ4')

    plz_data = load_plz()

    # --- DATENBANK SETUP ---
    if 'kandidaten' not in st.session_state:
        # Start-Datenrahmen
        st.session_state.kandidaten = pd.DataFrame(columns=[
            "Vorname", "Nachname", "PLZ", "Ort", "E-Mail", "Mobil", "Skills", "Dossier_Text"
        ])

    # --- SIDEBAR NAVIGATION ---
    menu = st.sidebar.radio("Menü", ["Suche & Matching", "Dossier Upload (Ingestor)", "Datenbank pflegen"])

    # --- SEITE: UPLOAD ---
    if menu == "Dossier Upload (Ingestor)":
        st.header("📥 Ingestor: Dossiers einlesen")
        files = st.file_uploader("PDFs hochladen", accept_multiple_files=True, type="pdf")
        
        if st.button("Verarbeitung starten") and files:
            for f in files:
                doc = fitz.open(stream=f.read(), filetype="pdf")
                text = chr(12).join([page.get_text() for page in doc])
                
                # Einfache KI-Extraktion der Stammdaten
                prompt = f"Extrahiere Vorname, Nachname, PLZ, E-Mail aus diesem Text. Antworte NUR im Format: Vorname;Nachname;PLZ;Email\nText: {text[:2000]}"
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                raw = response.choices[0].message.content.split(";")
                
                # Dubletten-Check
                if not st.session_state.kandidaten[st.session_state.kandidaten['E-Mail'] == raw[3]].empty:
                    st.info(f"Kandidat {raw[0]} {raw[1]} bereits vorhanden. Update wird durchgeführt.")
                    st.session_state.kandidaten = st.session_state.kandidaten[st.session_state.kandidaten['E-Mail'] != raw[3]]

                # Hinzufügen
                new_row = {
                    "Vorname": raw[0], "Nachname": raw[1], "PLZ": raw[2], 
                    "E-Mail": raw[3], "Dossier_Text": text
                }
                st.session_state.kandidaten = pd.concat([st.session_state.kandidaten, pd.DataFrame([new_row])], ignore_index=True)
            st.success("Dossiers verarbeitet!")

    # --- SEITE: SUCHE ---
    elif menu == "Suche & Matching":
        st.header("🔍 KI-Matching")
        job_desc = st.text_area("Stellenbeschreibung / Anforderungen")
        ziel_plz = st.number_input("Arbeitsort PLZ", value=8000)
        radius = st.slider("Umkreis (km)", 5, 100, 30)

        if st.button("Passende Kandidaten finden"):
            # Hier käme die Vektor-Suche Logik (vereinfacht für Start)
            st.write("Suche im Umkreis und prüfe Qualifikationen (HFP, NIV)...")
            # Filterung & Anzeige
            st.dataframe(st.session_state.kandidaten[["Vorname", "Nachname", "PLZ", "E-Mail"]])

    # --- SEITE: DATENBANK ---
    elif menu == "Datenbank pflegen":
        st.header("🛠️ Datenbank-Verwaltung")
        st.write("Hier kannst du fehlende Infos (PLZ, Tel) direkt in der Tabelle ergänzen:")
        edited_df = st.data_editor(st.session_state.kandidaten, num_rows="dynamic")
        if st.button("Speichern"):
            st.session_state.kandidaten = edited_df
            st.success("Datenbank aktualisiert!")