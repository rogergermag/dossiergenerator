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
import base64
import re
import extract_msg
import tempfile

def force_schweizer_deutsch(text: str) -> str:
    if not text:
        return text
    return text.replace("ß", "ss")


st.set_page_config(page_title="Dossier Generator", page_icon="📄", layout="wide")

st.markdown("# 📄 **Roger Germ AG - Kandidatendossier Generator**")
#st.caption("*Roger Germ AG - Automatische Dossiererstellung*")

# ============================================
# SIDEBAR
# ============================================
st.sidebar.image("rg_logo_web.png", width=180)
#st.sidebar.markdown("### 📸 Titelblatt-Bild")
bilder = {
    "01 - BSA": "Bild 01 BSA-min.png",
    "02 - Elektroinstallation": "Bild 02 Elektroinstallation-min.png",
    "03 - Elektroplanung": "Bild 03 Elektroplanung Engineering-min.png",
    "04 - Erneuerbare Energien": "Bild 04 erneuerbare energien-min.png",
    "05 - Gebäudeautomation Home": "Bild 05 Gebäudeautomation-min.png",
    "06 - ICT": "Bild 06 ICT-min.png",
    "07 - Innendienst": "Bild 07 Innendienst-min.png",
    "08 - Sicherheitstechnik": "Bild 08 Sicherheitstechnik-min.png",
    "09 - verschiedene Berufe": "Bild 09 verschiedene Berufe-min.png",
    "10 - Vertrieb": "Bild 10 Vertrieb-min.png",
    "11 - Gebäudeautomation MSRL": "Bild 11 GA MSRL.jpg",
    "12 - Industrie Lebensmittel": "Bild 12 Industrie Lebensmittel.jpg",
    "13 - Industrie Maschinenbau": "Bild 13 Industrie Maschinenbau.jpg",
    "14 - Industrie Allgemein": "Bild 14 Industrie Allgemein.jpg",
    "15 - SGK": "Bild 15 SGK.jpg",
    "16 - SPS": "Bild 16 SPS Programmierung.png",
}

selected_label = st.sidebar.radio("", list(bilder.keys()))
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
#st.info("ℹ️ **Vorlage.docx ist bereits im System hinterlegt**")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Fragebogen**")
    fragebogen = st.file_uploader("📋 Fragebogen (PDF)", type=["pdf"])

with col2:
    st.markdown("**CV + Zeugnisse**")
    cv_files = st.file_uploader(
        "📄 CV + Zeugnisse (PDF)",
        type=["pdf"],
        accept_multiple_files=True
    )

with col3:
    st.markdown("**Handnotizen**")
    notizen_files = st.file_uploader(
        "✍️ Handnotizen (PDF/TXT/JPG/PNG)",
        type=["pdf", "txt", "jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

st.markdown("### 🔴 Hinweise von Andreas")

col_h1, col_h2 = st.columns(2)

with col_h1:
    wechsel_input = st.text_area(
        "Grund des Stellenwechsels",
        height=120
    )

    eindruck_input = st.text_area(
        "Persönlicher Eindruck",
        height=120
    )

with col_h2:
    ziele_input = st.text_area(
        "Ziele des Kandidaten",
        height=120
    )

    position_input = st.text_input(
        "Position"
    )

    sonstiges_input = st.text_input(
        "Sonstiges",
    )


#st.markdown("### 🧪 Template-Test (nur Vorlage prüfen)")

#if st.button("Template nur testen"):
#    try:
#        doc_test = DocxTemplate("Vorlage.docx")
#        test_context = {"Kandidat": "Test Kandidat"}  # Minimal reicht
#        doc_test.render(test_context)
#        st.success("✅ Vorlage.docx ist Jinja-seitig OK.")
#    except Exception as e:
#        st.error("❌ Fehler im Template (Jinja2):")
#        st.write(str(e))



# ============================================
# GENERIEREN
# ============================================
if st.button("▶️ **DOSSIER GENERIEREN**", type="primary", use_container_width=True):
    
    # Validierungen
    
    if not (fragebogen or cv_files):
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

        name = file.name.lower()

        if name.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file)
            return "\n".join([page.extract_text() or "" for page in reader.pages])

        if name.endswith(".txt"):
            return file.read().decode("utf-8")

        if name.endswith(".msg"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".msg") as tmp:
                tmp.write(file.read())
                tmp_path = tmp.name

            msg = extract_msg.Message(tmp_path)

            text = f"""Betreff: {msg.subject or ""}

    Absender: {msg.sender or ""}
    
    Inhalt:
    {msg.body or ""}
    """
            return text
    
        if name.endswith((".jpg", ".jpeg", ".png")):
            image_bytes = file.read()
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            mime_type = "image/jpeg" if name.endswith((".jpg", ".jpeg")) else "image/png"
    
            vision_resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Lies diese handschriftlichen oder fotografierten Handnotizen aus dem Bild aus. Gib nur den erkannten Text zurück, ohne Erklärungen."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0
            )
            return vision_resp.choices[0].message.content
    
        return ""
    
    frage_text = extract_text(fragebogen)
    cv_text = ""
    for file in cv_files:
        cv_text += extract_text(file) + "\n\n"

    notizen_text = ""
    for file in notizen_files:
        notizen_text += extract_text(file) + "\n\n"

    notizen_gesamt = f"""Sonstiges:
    {sonstiges_input}
    
    Handnotizen:
    {notizen_text}
    """
    
    progress.progress(20)
    
    # ============================================
    # 2. KI: DATEN EXTRAHIEREN
    # ============================================
    status.text("🤖 Extrahiere strukturierte Daten mit KI...")
    
    extract_prompt = f"""Du bist Schweizer Recruiting-Experte in der Elektrobranche.

QUELLEN (Priorität):

1. Sonstiges und Handnotizen
2. Fragebogen
3. CV und Arbeitszeugnisse

WICHTIG:
- Verwende nur Informationen aus den oben genannten Quellen.
- Wenn eine Information nicht eindeutig vorhanden ist, lasse das Feld leer.
- Erfinde keine Daten.
- Verwende Schweizer Rechtschreibung (ss statt ß).

FRAGEBOGEN:
{frage_text[:10000]}

CV + ZEUGNISSE:
{cv_text[:20000]}

NOTIZEN UND HINWEISE:
{notizen_gesamt}

WICHTIG ZUM SALAER:
- Das Salär soll grundsätzlich aus dem Fragebogen übernommen werden (Wert in Feld: realistische Salärvorstellung bei 100%).
- Wenn in den Notizen oder Hinweisen von Andreas ein anderes oder präziseres Salär steht, haben die Notizen immer Vorrang.
- Wenn mehrere Salärangaben vorkommen, verwende die Angabe aus den Notizen.
- Übernimm das Salär möglichst exakt.

WICHTIG ZU AUSBILDUNGEN:
- Erfasse den höchsten ERFOLGREICH abgeschlossenen Titel für das Feld "hoechste_Ausbildung".
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
- Lasse die Monate immer weg, d.h. Schreibe nur die Jahreszahlen, z.B 2007 - 2008 Lehre Elektromonteur EFZ

WICHTIG ZU SPRACHEN:
- Entnimm die Sprachkenntnisse IMMER zuerst aus dem Fragebogen.
- Nur wenn dort nichts steht, verwende den CV.

WICHTIG ZUR VERFUEGBARKEIT:
- Wenn im Fragebogen eine Kündigungsfrist steht (z.B. "Kündigungsfrist 3 Monate"), dann schreibe bei "verfuegbarkeit" z.B. "3 Monate Kündigungsfrist".
- Wenn im Fragebogen ein mögliches Startdatum (z.B. "Eintrittstermin 01.09.2026") steht, dann schreibe bei "verfuegbarkeit" z.B. "Ab 01.09.2026 verfügbar".
- Wenn beides vorhanden ist, verwende das mögliche Startdatum.
- Wenn weder Kündigungsfrist noch Startdatum ersichtlich sind, lasse "verfuegbarkeit" leer.

WICHTIG ZU ICT-KENNTNISSEN:
- Wenn bei ICT-Kenntnissen Excel als regelmässig angegeben wird, schreibe dann statt Excel und Word immer MS Office!

**EXTRAHIERE als JSON (Schweizer Format: ss statt ß, keine Bindestriche):**
{{
  "kandidat_name": "Vorname Nachname",
  "nachname": "Nachname",
  "geburtsdatum": "TT.MM.JJJJ",
  "nationalitaet": "Schweiz",
  "mobilitaet": "Führerschein B",
  "verfuegbarkeit": "per sofort",
  "salaer": "150'000 CHF",
  "kuendigungsfrist": "3 Monate",
  "hoechste_Ausbildung": Elektro-Projektleiter mit eidg. FA",
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
    - 4-5 Schlagworte sollen wichtigste persönliche Eigenschaften oder Stärken sein
    - Verwende KEINE Berufstitel (z.B. Elektroinstallateur, Projektleiter, Monteur, etc.)
    - Verwende KEINE Ausbildungen oder Abschlüsse
    - Schlagworte dürfen KEINE Jobbezeichnungen enthalten
    - keine ganzen Sätze
    - keine Nummerierung
    - keine Duplikate
    - nur Informationen aus Fragebogen, CV und Arbeitszeugnissen verwenden

    Quellen:
    FRAGEBOGEN:
    {frage_text[:5000]}

    CV:
    {cv_text[:10000]}

    ARBEITSZEUGNISSE / NOTIZEN:
    {notizen_text[:10000]}

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
    wechsel_prompt = f"""Formuliere den Wechselgrund für {daten['kandidat_name']}.

QUELLE:

1. Verwende zuerst die Stichworte aus dem Interviewfeld "Wechselgrund".
2. Falls dieses Feld leer ist, verwende stattdessen Informationen aus den Handnotizen.
3. Verwende niemals Ziele oder Karrierewünsche als Wechselgrund.

Wechselgrund Stichworte:
{wechsel_input}

Handnotizen:
{notizen_text[:4000]}

Vorgaben:

- 1 bis maximal 2 Sätze
- Der Name "{daten['kandidat_name']}" soll je nach Textlänge 1–2 Mal erwähnt werden
- Sachlich und professionell formuliert
- Keine negativen Aussagen über den aktuellen Arbeitgeber
- Nichts dazuerfinden
- Verwende Schweizer Rechtschreibung. Das Zeichen ß darf nicht verwendet werden, stattdessen immer ss schreiben. Verwende ä,ö,ü.

Der letzte Satz muss immer exakt so lauten: Über die genauen Hintergründe spricht Herr {daten['nachname']} im persönlichen Gespräch gerne ausführlicher.
"""
    
    wechsel = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": wechsel_prompt}],
        temperature=0.1
    ).choices[0].message.content
    
    # Ziele
    ziele_prompt = f"""Formuliere den Abschnitt "Ziele" für {daten['kandidat_name']}.

QUELLEN:

- Interviewfeld "Ziele"
- Fragebogen
- Handnotizen

Alle Quellen dürfen verwendet werden.  
Wenn mehrere Informationen vorhanden sind, haben die Stichworte aus dem Interviewfeld die höchste Priorität.

Ziel-Stichworte aus Interview:
{ziele_input}

Fragebogen:
{frage_text[:4000]}

Handnotizen:
{notizen_text[:4000]}

Vorgaben:

- Beginne mit:
Herr {daten['nachname']} sucht eine neue Herausforderung, in die er seine Kenntnisse und Erfahrungen einbringen kann.

- Danach 2–3 weitere Sätze.
- Der Name "{daten['kandidat_name']}" soll insgesamt etwa 2 Mal vorkommen.
- Sachlich und professionell formuliert.
- Keine negativen Aussagen.
- Nichts dazuerfinden.
- Verwende Schweizer Rechtschreibung. Das Zeichen ß darf nicht verwendet werden, stattdessen immer ss schreiben. Verwende ä,ö,ü.

- Der letzte Satz soll immer in etwa so lauten: Wichtig sind ihm ein gut aufgestellter Arbeitgeber, interessante Projekte und Tätigkeiten sowie ein wertschätzendes Arbeitsumfeld.
"""

    ziele = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": ziele_prompt}],
        temperature=0.2
    ).choices[0].message.content
    
    # Arbeitszeugnisse
    zeug_prompt = f"""Fasse die wichtigsten Aussagen aus den Arbeitszeugnissen von {daten['kandidat_name']} zusammen.

WICHTIG:
- Du darfst KEIN EINZIGES WORT verändern.
- Du darfst KEINE Sätze zusammenfassen.
- Kopiere die Sätze 1:1 so, wie sie in der Quelle stehen.
- Wenn du einen Satz auswählst, übernimm ihn vollständig
- Verwende ausschliesslich Aussagen aus den Arbeitszeugnissen.
- Setze jeden Satz in «Gänsefüsschen».
- Keine eigenen Formulierungen erfinden.

REIHENFOLGE:
1. Fachliche Fähigkeiten und Erfahrungen
2. Persönlichkeit
3. Verhalten gegenüber Vorgesetzten, Kunden und Mitarbeitern

STRUKTUR:
- Beginne mit:
Seine Vorgesetzten schreiben folgendes über Herrn {daten['nachname']}:

- Danach folgen auf der gleichen Zeile die ca. 10 kurze Aussagen.
- Alle Aussagen hintereinander als Fliesstext.
- Keine Aufzählungen.
- Keine Kategorienüberschriften.

QUELLE (Arbeitszeugnisse aus CV-PDF):

{cv_text[:20000]}
"""
    
    zeugnisse = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": zeug_prompt}],
    temperature=0.1
).choices[0].message.content
    
    # Persönlicher Eindruck
    eindruck_prompt = f"""Formuliere den persönlichen Eindruck aus dem Interview für {daten['kandidat_name']}.

QUELLEN:

- Interviewfeld "Persönlicher Eindruck"
- Handnotizen

Alle Quellen dürfen verwendet werden.  
Wenn mehrere Informationen vorhanden sind, haben die Stichworte aus dem Interviewfeld die höchste Priorität.

Persönlicher Eindruck Stichworte aus Interview:
{eindruck_input}

Handnotizen:
{notizen_text[:2000]}

Vorgaben:

- Beginne exakt mit:
Herr {daten['nachname']} ist ein aufgestellter, freundlicher und sympathischer Mann der einen sehr guten Eindruck hinterlassen hat. Er kommuniziert offen, überlegt und schlüssig.

- Danach 3–4 zusätzliche Sätze zum persönlichen Eindruck.
- Dinge, die nicht eindeutig aus den Quellen hervorgehen, müssen in der "Es scheint..." Form formuliert werden.
- Der Name "{daten['kandidat_name']}" soll insgesamt etwa 2–3 Mal im Text vorkommen.
- Sachlich und professionell formuliert.
- Verwende nur Informationen aus den Quellen.
- Verwende Schweizer Rechtschreibung. Das Zeichen ß darf nicht verwendet werden, stattdessen immer ss schreiben. Verwende ä,ö,ü.
"""

    eindruck = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": eindruck_prompt}],
    temperature=0.2
).choices[0].message.content
    
    # Kompetenzen
    komp_prompt = f"""Erstelle den Abschnitt "Kompetenzen" für {daten['kandidat_name']}.

QUELLEN UND PRIORITÄT:
1. Fragebogen
2. CV
3. Arbeitszeugnisse

STRUKTUR:

Erste Zeile:
- Nur exakte Berufstitel / Stellenbezeichnungen aus dem CV
- Keine Ausbildungen
- Keine Firmen
- Höchste Funktion zuerst
- Kommagetrennt in einer Zeile
- Keine Überschrift
- Danach eine Leerzeile

WICHTIG ZU BERUFSERFAHRUNGEN IM FRAGEBOGEN:
- Wenn im Fragebogen unter "Berufserfahrungen" Kompetenzen aufgeführt sind, sollen diese zuerst erscheinen
- Kompetenzen mit Einstufung "Anfänger" weglassen
- Kompetenzen mit Einstufung "regelmässig" oder "Experte" aufführen
- Wenn "Kalkulation" und "Angebote" oder "Offerten" vorkommen, fasse sie zusammen als:
Erstellen von Kalkulationen und Offerten

ZUSÄTZLICHE REGELN:
- Wenn die Person mindestens bauleitender Monteur ist, führe diese Kompetenz auf:
Ressourcenmanagement
- Wenn die Person "Elektroinstallateur" oder "Elektromonteur" ist, führe diese Kompetenz auf:
Elektroinstallation im Stark- und Schwachstrombereich

#- Wenn die Person im CV Führungserfahrung im Militär oder Zivilschutz aufweist (z.B. Korporal, Leutnant, Oberleutnant, Hauptmann, etc.), schreibe direkt nach der Zeile mit den Berufstiteln in einer neuen Zeile etwas wie:
#Führungsfunktion im Militär. Falls du nicht sicher bist ob es eine Führungsfunktion ist, dann lass es weg.

DANACH DIREKT KOMPETENZZEILEN:
- Kurz und prägnant formuliert
- Fachlich
- Keine Einleitung
- Keine Überschrift
- Keine Leerzeilen
- Keine Bullet-Zeichen
- Maximal eine Zeile pro Kompetenz
- Maximal 11 Kompetenzen
- Möglichst konkrete Tätigkeiten statt allgemeiner Formulierungen
- Verwende Schweizer Rechtschreibung. Das Zeichen ß darf nicht verwendet werden, stattdessen immer ss schreiben. Verwende ä, ö, ü.

QUELLEN:

FRAGEBOGEN:
{frage_text[:10000]}

CV:
{cv_text[:10000]}

ARBEITSZEUGNISSE:
{cv_text[:20000]}
"""

    kompetenzen = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": komp_prompt}]
    ).choices[0].message.content
    
    progress.progress(80)

    # Schweizer Rechtschreibung erzwingen (kein ß)
    wechsel     = force_schweizer_deutsch(wechsel)
    ziele       = force_schweizer_deutsch(ziele)
    zeugnisse   = force_schweizer_deutsch(zeugnisse)
    eindruck    = force_schweizer_deutsch(eindruck)
    kompetenzen = force_schweizer_deutsch(kompetenzen)

    
    # ============================================
    # 5. FORMATIERUNGEN
    # ============================================
    status.text("📝 Formatiere Daten...")
    
    # Sprachen (max. 3 pro Zeile)
    sprach_liste = [
        f"{s['sprache']}: {re.sub(r'\s*\(.*?\)', '', s['niveau']).strip()}"
        for s in daten.get('sprachen', [])
    ]
    
    zeilen = []
    for i in range(0, len(sprach_liste), 3):
        zeile = "     ".join(sprach_liste[i:i+3])
        zeilen.append(zeile)
    
    sprachen = "\n".join(zeilen)

    
    # ICT (2 Zeilen)
    ict_reg = ", ".join(daten.get('ict_regelmaessig', []))
    ict_grund = daten.get('ict_grundkenntnisse', [])
    ict = ict_reg + (f"\nGrundkenntnisse: {', '.join(ict_grund)}" if ict_grund else "")
    
    # Ausbildungen
    ausbildungen = "\n".join(daten.get('ausbildungen', []))
    
    # Salär mit Zusatz
    salaer = daten.get('salaer', '')

    salaer = daten.get('salaer', '')

    # Zahl aus dem Salär extrahieren
    match = re.search(r"\d[\d' ]*", salaer)

    if match:
        zahl = match.group(0).replace("'", "").replace(" ", "")
        try:
            wert = int(zahl)
            if wert < 20000 and "x13" not in salaer.lower():
                salaer = salaer + " x13"
        except:
            pass
    
    progress.progress(90)

    # ============================================
    # ANMERKUNGEN (Teilzeit erkennen)
    # ============================================
    
    anmerkungen = ""
    
    pensum_match = re.search(r"\b(100|[1-9]?\d)%\b", frage_text + " " + notizen_text)
    
    if pensum_match:
        pensum = pensum_match.group(1)
    
        if pensum != "100":
            grund = ""
    
            grund_match = re.search(
                r"(Familie|Kinder|Weiterbildung|Studium|Selbständigkeit|Nebenjob)",
                frage_text + " " + notizen_text,
                re.IGNORECASE
            )
    
            if grund_match:
                grund = grund_match.group(1)
    
            if grund:
                anmerkungen = f"Herr {daten['nachname']} möchte gerne {pensum}% arbeiten aufgrund von {grund}."
            else:
                anmerkungen = f"Herr {daten['nachname']} möchte gerne {pensum}% arbeiten."

    
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
        "Position": position_input,
        "hoechste_Ausbildung": daten.get('hoechste_Ausbildung', ''),
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
        "Anmerkungen": anmerkungen,
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
    
    #col1, col2 = st.columns(2)
    #with col1:
    #    st.json({
    #        "Name": daten['kandidat_name'],
    #        "Salär": daten['salaer'],
    #        "Kündigungsfrist": daten['kuendigungsfrist']
    #    })
    #
   # with col2:
   #     st.write("**Schlagworte:**")
   #     for i, sw in enumerate(schlagworte[:6], 1):
   #         if sw:
   #             st.write(f"{i}. {sw}")
    
    with st.expander("👁️ Generierte Texte Vorschau"):
        st.markdown("**Wechselgrund:**")
        st.write(wechsel)
        st.markdown("**Ziele:**")
        st.write(ziele)
        st.markdown("**Eindruck:**")
        st.write(eindruck)



