"""
KANDIDATENDOSSIER GENERATOR
Roger Germ AG - Vollautomatisch!
"""

import streamlit as st
from openai import OpenAI
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Inches
from PIL import Image
import io
import json
from datetime import datetime
import PyPDF2

# Konfiguration
st.set_page_config(
    page_title="Dossier Generator", 
    page_icon="📄",
    layout="wide"
)

st.markdown("""
# 📄 **Kandidatendossier Generator**
*Automatische Dossiererstellung aus Fragebogen, CV, Notizen*
""")

# ============================================
# SIDEBAR: BILD-AUSWAHL + API KEY
# ============================================
st.sidebar.markdown("### 📸 Titelblatt-Bild")
bilder = {
    "1 - BSA": "Bild 01 BSA-min.png",
    "2 - Elektroinstallation": "Bild 02 Elektroinstallation-min.png", 
    "3 - Elektroplanung": "Bild 03 Elektroplanung Engineering-min.png",
    "4 - Natur": "bild_4.jpg",
    "5 - Architektur": "bild_5.jpg",
    "6 - Innovation": "bild_6.jpg",
    "7 - Produktion": "bild_7.jpg",
    "8 - Labor": "bild_8.jpg",
    "9 - Werkstatt": "bild_9.jpg",
    "10 - Digital": "bild_10.jpg"
}

selected_label = st.sidebar.radio("Wähle:", list(bilder.keys()))
selected_image = bilder[selected_label]

# Vorschau
st.sidebar.image(f"https://via.placeholder.com/200x150/cccccc?text={selected_label}", width=200)

api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# ============================================
# FILE UPLOADS
# ============================================
st.markdown("### 📁 Input-Dateien")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Priorität 1-2**")
    fragebogen = st.file_uploader("📋 Fragebogen", type=["pdf", "txt"])
    cv = st.file_uploader("📄 CV + Zeugnisse", type=["pdf"])

with col2:
    st.markdown("**Priorität 3-4**")
    notizen = st.file_uploader("✍️ Notizen", type=["pdf", "txt"])
    

# Hinweise
hinweise = st.text_area("🔴 Hinweise Andreas", height=80)

# ============================================
# GENERIEREN BUTTON
# ============================================
if st.button("🚀 **DOSSIER GENERIEREN**", type="primary", use_container_width=True):

    # Mindest-Validierung
    if not (fragebogen or cv):
        st.error("❌ Mindestens Fragebogen ODER CV!")
        st.stop()

    progress = st.progress(0)
    status = st.empty()
    
    # ============================================
    # 1. TEXT EXTRAHIEREN
    # ============================================
    status.text("📖 Extrahiere Texte...")
    progress.progress(10)
    
    def extract_text(file):
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            return "\n".join([page.extract_text() for page in reader.pages])
        return file.read().decode("utf-8")
    
    frage_text = extract_text(fragebogen) if fragebogen else ""
    cv_text = extract_text(cv) if cv else ""
    notizen_text = extract_text(notizen) if notizen else ""
    
    progress.progress(20)
    
    # ============================================
    # 2. STRUKTURIERTE DATEN (KI)
    # ============================================
    status.text("🤖 Extrahiere Daten...")
    
    extract_prompt = f"""
**QUELLEN-PRIORITÄT:**
1. Notizen (überschreibt alles!)
2. Fragebogen  
3. CV

FRAGEBOGEN: {frage_text[:4000]}
CV: {cv_text[:4000]}
NOTIZEN: {notizen_text}
HINWEISE: {hinweise}

**EXTRAHIERE JSON (Schweizer Format: ss statt ß):**
{{
  "kandidat_name": "",
  "nachname": "",
  "geburtsdatum": "",
  "nationalitaet": "",
  "salaer": "",
  "kuendigungsfrist": "",
  "hoechste_ausbildung": "",
  "ausbildungen": [],
  "sprachen": [{{"sprache":"", "niveau":""}}],
  "ict_regelmaessig": [],
  "ict_grundkenntnisse": [],
  "jobtitel": [],
  "wechselgrund": "",
  "ziele": "",
  "eindruck": ""
}}
"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": extract_prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    daten = json.loads(response.choices[0].message.content)
    progress.progress(40)
    
    # ============================================
    # 3. SCHLAGWORTE
    # ============================================
    status.text("💡 Schlagworte...")
    schlag_prompt = f"""
Erstelle 6 Schlagworte für {daten['kandidat_name']}.
CV: {cv_text[:2000]}
JSON: {json.dumps(daten)}
"""
    schlag_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": schlag_prompt}]
    )
    schlagworte = schlag_response.choices[0].message.content.split('\n')[:6]
    progress.progress(50)
    
    # ============================================
    # 4. TEXTE GENERIEREN
    # ============================================
    status.text("✍️ Generiere Texte...")
    
    # Wechselgrund
    wechsel_prompt = f"""Wechselgrund für {daten['kandidat_name']}.
2-3 Sätze, Name 2x erwähnen, endet mit "persönliches Gespräch".
"""
    wechsel = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": wechsel_prompt}]).choices[0].message.content
    
    # Ziele  
    ziele_prompt = f"""Ziele für {daten['kandidat_name']}.
Beginnt mit "Herr {daten['nachname']} sucht neue Herausforderung".
"""
    ziele = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": ziele_prompt}]).choices[0].message.content
    
    # Arbeitszeugnisse
    zeug_prompt = f"""Arbeitszeugnisse für {daten['kandidat_name']}.
Beginnt "Seine Vorgesetzten schreiben:", wortwörtliche Zitate in «»."""
    zeugnisse = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": zeug_prompt}]).choices[0].message.content
    
    # Eindruck
    eindruck_prompt = f"""Persönlicher Eindruck {daten['kandidat_name']}.
Beginnt "Herr {daten['nachname']} ist aufgestellter sympathischer Mann...". """
    eindruck = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": eindruck_prompt}]).choices[0].message.content
    
    # Kompetenzen
    komp_prompt = f"""Kompetenzen {daten['kandidat_name']}.
1. Zeile: {', '.join(daten['jobtitel'])}
2+. Bullet-Points (ohne Bullets)."""
    kompetenzen = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": komp_prompt}]).choices[0].message.content
    
    progress.progress(80)
    
    # ============================================
    # 5. FORMATIERUNGEN
    # ============================================
    status.text("📝 Formatiere...")
    
    # Sprachen
    sprachen = "     ".join([f"{s['sprache']}: {s['niveau']}" for s in daten['sprachen']])
    
    # ICT
    ict = ", ".join(daten['ict_regelmaessig'])
    if daten['ict_grundkenntnisse']:
        ict += f"\nGrundkenntnisse: {', '.join(daten['ict_grundkenntnisse'])}"
    
    # Ausbildungen
    ausbildungen = "\n".join(daten['ausbildungen'])
    
    # Salär
    salaer = daten['salaer'] + "\nGesprächsbereit je nach Paket"
    
    progress.progress(90)
    
    # ============================================
    # 6. WORD DOKUMENT
    # ============================================
    status.text("📄 Erstelle Word...")
    
    doc = DocxTemplate(vorlage_file)
    
    # BILD!
    titelbild = InlineImage(doc, selected_image, Inches(6.5), Inches(4.0))
    
    context = {
        "bild": titelbild,
        "Kandidat": daten['kandidat_name'],
        "Geburtsdatum": daten['geburtsdatum'],
        "Nationalität": daten['nationalitaet'],
        "Mobilität": "Führerschein B",  # aus Daten
        "Verfügbarkeit": daten['verfuegbarkeit'],
        "Salär": salaer,
        "Ausbildung": ausbildungen,
        "Sprachen": sprachen,
        "ICT-Kenntnisse": ict,
        "Kompetenzen": kompetenzen,
        "Stellenwechsel": wechsel,
        "Ziele": ziele,
        "Arbeitszeugnisse": zeugnisse,
        "Eindruck": eindruck,
        "Anmerkungen": ""
    }
    
    doc.render(context)
    
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    
    progress.progress(100)
    status.success("✅ DOSSIER FERTIG!")
    
    # DOWNLOAD
    st.download_button(
        "📥 **DOSSIER HERUNTERLADEN**",
        bio.getvalue(),
        f"Dossier_{daten['nachname']}.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    
    # VORSCHAU
    st.subheader("📋 Zusammenfassung")
    st.json({
        "Name": daten['kandidat_name'],
        "Salär": daten['salaer'],
        "Schlagworte": schlagworte[:3],
        "Länge Wechselgrund": len(wechsel),
        "Bild": selected_label
    })



