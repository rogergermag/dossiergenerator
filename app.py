"""
KANDIDATENDOSSIER GENERATOR
Roger Germ AG - Automatisch!
"""

import streamlit as st
from openai import OpenAI
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Inches
from PIL import Image
import io
import json
import PyPDF2

st.set_page_config(page_title="Dossier Generator", page_icon="📄", layout="wide")

st.markdown("# 📄 **Kandidatendossier Generator**")
st.caption("*Roger Germ AG - Automatische Dossiererstellung*")

# ============================================
# SIDEBAR
# ============================================
st.sidebar.markdown("### 📸 Titelblatt-Bild")
bilder = {
    "1 - BSA": "Bild 01 BSA-min.png",
    "2 - Elektroinstallation": "Bild 02 Elektroinstallation-min.png",
    "3 - Elektroplanung": "Bild 03 Elektroplanung Engineering-min.png",
    "4 - Erneuerbare Energien": "Bild 04 erneuerbare energien-min.png",
 
}

selected_label = st.sidebar.radio("Wähle:", list(bilder.keys()))
selected_image = bilder[selected_label]

# Vorschau (Placeholder - ersetze mit echtem Bild)
try:
    img_preview = Image.open(selected_image)
    st.sidebar.image(img_preview, width=200)
except:
    st.sidebar.image(f"https://via.placeholder.com/200x150?text={selected_label}", width=200)

api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# ============================================
# FILE UPLOADS (OHNE VORLAGE!)
# ============================================
st.markdown("### 📁 Input-Dateien")
st.info("ℹ️ **Vorlage.docx ist bereits im System hinterlegt**")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Pflicht-Dateien**")
    fragebogen = st.file_uploader("📋 Fragebogen (PDF/TXT)", type=["pdf", "txt"])
    cv = st.file_uploader("📄 CV + Zeugnisse (PDF)", type=["pdf"])

with col2:
    st.markdown("**Optional**")
    notizen = st.file_uploader("✍️ Handnotizen (PDF/TXT)", type=["pdf", "txt"])

hinweise = st.text_area("🔴 Hinweise von Andreas", height=80, placeholder="Spezielle Anmerkungen...")


st.markdown("### 🧪 Template-Test (nur Vorlage prüfen)")

if st.button("Template nur testen"):
    try:
        doc_test = DocxTemplate("Vorlage.docx")
        test_context = {"Kandidat": "Test Kandidat"}  # Minimal reicht
        doc_test.render(test_context)
        st.success("✅ Vorlage.docx ist Jinja-seitig OK.")
    except Exception as e:
        st.error("❌ Fehler im Template (Jinja2):")
        st.write(str(e))



# ============================================
# GENERIEREN
# ============================================
if st.button("🚀 **DOSSIER GENERIEREN**", type="primary", use_container_width=True):
    
    # Validierungen
    
    if not (fragebogen or cv):
        st.error("❌ Mindestens Fragebogen ODER CV erforderlich!")
        st.stop()
    
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    
    progress = st.progress(0)
    status = st.empty()
    
    # ============================================
    # 1. TEXT EXTRAHIEREN
    # ============================================
    status.text("📖 Extrahiere Texte aus PDFs...")
    progress.progress(10)
    
    def extract_text(file):
        if not file:
            return ""
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            return "\n".join([page.extract_text() for page in reader.pages])
        return file.read().decode("utf-8")
    
    frage_text = extract_text(fragebogen)
    cv_text = extract_text(cv)
    notizen_text = extract_text(notizen)
    
    progress.progress(20)
    
    # ============================================
    # 2. KI: DATEN EXTRAHIEREN
    # ============================================
    status.text("🤖 Extrahiere strukturierte Daten mit KI...")
    
    extract_prompt = f"""Du bist Schweizer Recruiting-Experte.

**QUELLEN (Priorität):**
1. Notizen (überschreibt alles!)
2. Fragebogen
3. CV

FRAGEBOGEN:
{frage_text[:5000]}

CV + ZEUGNISSE:
{cv_text[:10000]}

NOTIZEN:
{notizen_text}

HINWEISE:
{hinweise}

WICHTIG ZU AUSBILDUNGEN:
- Erfasse ALLE relevanten Ausbildungen aus CV
- Dazu gehören auch Lehrabschlüsse (z.B. Elektromonteur, Elektroinstallateur EFZ)
- Wenn im CV eine Lehre vorkommt (z.B. "Lehre Automatiker EFZ"), muss sie in der Liste "ausbildungen" erscheinen
- Lasse Sprachzertifikate weg
- Lasse unwichtige oder ganz kurze Ausbildungen weg
- Es sollen maximal 6-8 Ausbildungen erscheinen
- Falls mehr vorhanden sind, nimm nur die wichtigsten
- Die Liste "ausbildungen" muss umgekehrt chronologisch sortiert sein.
- Die neueste Ausbildung steht immer zuerst.
- Die älteste Ausbildung steht am Schluss.

**EXTRAHIERE als JSON (Schweizer Format: ss statt ß, keine Bindestriche):**
{{
  "kandidat_name": "Vorname Nachname",
  "nachname": "Nachname",
  "geburtsdatum": "TT.MM.JJJJ",
  "nationalitaet": "Schweiz",
  "mobilitaet": "Führerschein B",
  "verfuegbarkeit": "per sofort",
  "salaer": "150'000 CHF x 13",
  "kuendigungsfrist": "3 Monate",
  "hoechste_ausbildung": "Dipl. Ing. FH",
  "ausbildungen": [
    "2007 - 2008 Praxisprüfung PX14 gemäss NIV",
    "1999 - 2002 Studium Elektrotechnik FH",
    "1989 - 1993 Lehre Elektromonteur EFZ"
    ],
  "sprachen": [{{"sprache": "Deutsch", "niveau": "Muttersprache"}}],
  "ict_regelmaessig": ["MS Office", "AutoCAD"],
  "ict_grundkenntnisse": ["Excel", "Teams"],
  "jobtitel": ["Projektleiter", "Ingenieur"],
  "wechselgrund_stichworte": "mehr Verantwortung",
  "ziele_stichworte": "Projektleitung, Teamführung",
  "eindruck_stichworte": "offen, kompetent"
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
    # 3. KI: SCHLAGWORTE
    # ============================================
    status.text("💡 Generiere Schlagworte...")

    schlag_prompt = f"""
    Erstelle genau 6 prägnante Schlagworte für ein Kandidatendossier.

    Regeln:
    - maximal 1 Wort pro Schlagwort
    - 1-2 Schlagworte sollen wichtigste Fachkompetenzen sein
    - 4-5 Schlagworte sollen wichtigste persönliche Eigenschaften sein
    - keine ganzen Sätze
    - keine Nummerierung
    - keine Duplikate
    - nur Informationen aus Fragebogen, CV und Arbeitszeugnissen verwenden

    Quellen:
    FRAGEBOGEN:
    {frage_text[:2000]}

    CV:
    {cv_text[:2000]}

    ARBEITSZEUGNISSE / NOTIZEN:
    {notizen_text[:2000]}

    Gib genau 6 Schlagworte zurück, jedes Schlagwort in einer eigenen Zeile und sonst nichts.
    """

    schlag_resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": schlag_prompt}],
        temperature=0.1
    )

    antwort = schlag_resp.choices[0].message.content.strip()

    schlagworte = [
        s.strip()
        for s in antwort.replace(",", "\n").replace(";", "\n").split("\n")
        if s.strip()
    ]

    schlagworte = schlagworte[:6]

    while len(schlagworte) < 6:
        schlagworte.append("")

    progress.progress(50)
    
    # ============================================
    # 4. KI: TEXTE GENERIEREN
    # ============================================
    status.text("✍️ Generiere Fliesstexte...")
    
    # Wechselgrund
    wechsel = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""Wechselgrund für {daten['kandidat_name']}.
2-3 Sätze, Name 2x, endet "persönliches Gespräch"."""}]
    ).choices[0].message.content
    
    # Ziele
    ziele = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""Ziele für {daten['kandidat_name']}.
Beginnt "Herr {daten['nachname']} sucht neue Herausforderung..."."""}]
    ).choices[0].message.content
    
    # Arbeitszeugnisse
    zeug_prompt = f"""Fasse die wichtigsten Aussagen aus den Arbeitszeugnissen von {daten['kandidat_name']} zusammen.

WICHTIG:

- Verwende ausschliesslich Aussagen aus den Arbeitszeugnissen.
- Übernimm die Aussagen wortwörtlich.
- Setze jeden Satz in «Gänsefüsschen».
- Keine eigenen Formulierungen erfinden.

REIHENFOLGE:
1. Fachliche Fähigkeiten und Erfahrungen
2. Persönlichkeit
3. Verhalten gegenüber Vorgesetzten, Kunden und Mitarbeitern

STRUKTUR:
- Beginne mit:
«Seine Vorgesetzten beschreiben ihn wie folgt:»

- Danach folgen auf der gleichen Zeile die ca. 10 kurze Aussagen.
- Alle Aussagen hintereinander als Fliesstext.
- Keine Aufzählungen.
- Keine Kategorienüberschriften.

QUELLE (Arbeitszeugnisse aus CV-PDF):

{cv_text[:20000]}
"""
    
    zeugnisse = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": zeug_prompt}],
    temperature=0.1
).choices[0].message.content
    
    # Persönlicher Eindruck
    eindruck = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""Persönlicher Eindruck {daten['kandidat_name']}.
Beginnt "Herr {daten['nachname']} ist ein aufgestellter, freundlicher Mann..."."""}]
    ).choices[0].message.content
    
    # Kompetenzen
    komp_prompt = f"""Erstelle den Abschnitt "Kompetenzen" für {daten['kandidat_name']}.

    STRUKTUR:

Erste Zeile:
- Nur Jobtitel aus dem CV
- Nur Stellenbezeichnungen
- Keine Ausbildungen
- Keine Firmen
- Höchste Funktion zuerst
- Kommagetrennt in einer Zeile
- Keine Überschrift

Danach direkt Kompetenzzeilen:
- Kurz und prägnant formuliert
- Fachlich
- Keine Einleitung
- Keine Überschrift
- Keine Leerzeilen
- Keine Bullet-Zeichen
- Maximal eine Zeile pro Kompetenz
- Maximal 10–12 Kompetenzen
- Möglichst konkrete Tätigkeiten statt allgemeiner Formulierungen

Beispiel Stil:

Projektleitung von Grossprojekten bis 8 MCHF
Leitung standortübergreifender Projekte und Teams
Budgetverantwortung
Krisenmanagement auf Baustellen
Optimierung von Prozessen und Abläufen
Hardware- und Softwareintegration
Ressourcenmanagement
Akquise und Verkauf
Technische Gesamtkoordination
Abklärungen mit Auftraggebern, Planern und Lieferanten
Mitarbeiterführung und -entwicklung
Kundenberatung und Betreuung

    Quellen:
    CV:
    {cv_text[:10000]}

    FRAGEBOGEN:
    {frage_text[:10000]}

    ARBEITSZEUGNISSE / NOTIZEN:
    {notizen_text[:10000]}
    """

    kompetenzen = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": komp_prompt}]
    ).choices[0].message.content
    
    progress.progress(80)
    
    # ============================================
    # 5. FORMATIERUNGEN
    # ============================================
    status.text("📝 Formatiere Daten...")
    
    # Sprachen (eine Zeile, grosse Abstände)
    sprachen = "     ".join([f"{s['sprache']}: {s['niveau']}" for s in daten.get('sprachen', [])])
    
    # ICT (2 Zeilen)
    ict_reg = ", ".join(daten.get('ict_regelmaessig', []))
    ict_grund = daten.get('ict_grundkenntnisse', [])
    ict = ict_reg + (f"\nGrundkenntnisse: {', '.join(ict_grund)}" if ict_grund else "")
    
    # Ausbildungen
    ausbildungen = "\n".join(daten.get('ausbildungen', []))
    
    # Salär mit Zusatz
    salaer = daten.get('salaer', '')
    
    progress.progress(90)
    
    # ============================================
    # 6. WORD-DOKUMENT ERSTELLEN
    # ============================================
    status.text("📄 Erstelle Word-Dokument...")
    
    # VORLAGE AUS REPOSITORY LADEN!
    doc = DocxTemplate("Vorlage.docx")
    
    # BILD einfügen
    import os

    image_path = os.path.join(os.getcwd(), selected_image)

    try:
        doc.replace_pic("titelbild", image_path)
        titelbild = ""
    except:
        st.warning(f"⚠️ Bild {selected_image} nicht gefunden - verwende Platzhalter")
        titelbild = None
    
    # Context befüllen
    context = {
        "bild": titelbild,
        "Kandidat": daten.get('kandidat_name', ''),
        "hoechste_Ausbildung": daten.get('hoechste_ausbildung', ''),
        "Salaer": salaer,
        "Schlagwort1": schlagworte[0] if len(schlagworte) > 0 else '',
        "Schlagwort2": schlagworte[1] if len(schlagworte) > 1 else '',
        "Schlagwort3": schlagworte[2] if len(schlagworte) > 2 else '',
        "Schlagwort4": schlagworte[3] if len(schlagworte) > 3 else '',
        "Schlagwort5": schlagworte[4] if len(schlagworte) > 4 else '',
        "Schlagwort6": schlagworte[5] if len(schlagworte) > 5 else '',
        "Geburtsdatum": daten.get('geburtsdatum', ''),
        "Nationalitaet": daten.get('nationalitaet', ''),
        "Mobilitaet": daten.get('mobilitaet', ''),
        "Verfuegbarkeit": daten.get('verfuegbarkeit', ''),
        "Salaer": salaer,
        "Ausbildung": ausbildungen,
        "Sprachen": sprachen,
        "ICT_Kenntnisse": ict,
        "Kompetenzen": kompetenzen,
        "Stellenwechsel": wechsel,
        "Ziele": ziele,
        "Arbeitszeugnisse": zeugnisse,
        "Eindruck": eindruck,
        "Anmerkungen": ""
    }
    
    doc.render(context)
    
    # Als BytesIO speichern
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    
    progress.progress(100)
    status.success("✅ DOSSIER ERFOLGREICH GENERIERT!")
    
    # ============================================
    # 7. DOWNLOAD + VORSCHAU
    # ============================================
    nachname = daten.get('nachname', 'Kandidat')
    
    st.download_button(
        label="📥 **DOSSIER HERUNTERLADEN**",
        data=bio.getvalue(),
        file_name=f"Dossier_{nachname}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
    
    # Vorschau
    st.markdown("---")
    st.subheader("📋 Zusammenfassung")
    
    col1, col2 = st.columns(2)
    with col1:
        st.json({
            "Name": daten['kandidat_name'],
            "Salär": daten['salaer'],
            "Kündigungsfrist": daten['kuendigungsfrist']
        })
    
    with col2:
        st.write("**Schlagworte:**")
        for i, sw in enumerate(schlagworte[:6], 1):
            if sw:
                st.write(f"{i}. {sw}")
    
    with st.expander("👁️ Generierte Texte Vorschau"):
        st.markdown("**Wechselgrund:**")
        st.write(wechsel)
        st.markdown("**Ziele:**")
        st.write(ziele)




