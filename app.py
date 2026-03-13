import streamlit as st
from docxtpl import DocxTemplate
import PyPDF2
import pandas as pd
from openai import OpenAI
import io
import json
from datetime import datetime

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Kandidatendossier Generator", page_icon="📄")

st.title("📄 Kandidatendossier Automatisierung")
st.caption("Roger Germ AG - Andreas Gloger")

# ============================================
# SIDEBAR: EINSTELLUNGEN
# ============================================
st.sidebar.header("⚙️ Einstellungen")

bildauswahl = st.sidebar.selectbox(
    "Titelblatt-Bild",
    [f"bild_{i}.jpg" for i in range(1, 11)],
    index=0
)

# ============================================
# FILE UPLOADS
# ============================================
st.header("📁 Input-Dateien")

col1, col2 = st.columns(2)

with col1:
    fragebogen_file = st.file_uploader(
        "📋 Fragebogen (PDF/TXT/MSG)",
        type=["pdf", "txt", "msg"],
        help="Quelle 1 - Höchste Priorität"
    )
    
    cv_file = st.file_uploader(
        "📄 CV + Zeugnisse + Diplome (PDF)",
        type=["pdf"],
        help="Quelle 2 & 3"
    )

with col2:
    notizen_file = st.file_uploader(
        "✍️ Handnotizen (PDF/TXT/Bild)",
        type=["pdf", "txt", "png", "jpg"],
        help="Quelle 4 - Überschreibt Fragebogen bei Widerspruch!"
    )
    
    hinweise_andreas = st.text_area(
        "🔴 Hinweise von Andreas",
        height=100,
        help="Rote Markierungen aus Unterlagen"
    )

# ============================================
# GENERIEREN
# ============================================
if st.button("🚀 Dossier generieren", type="primary", use_container_width=True):
    
    if not fragebogen_file and not cv_file:
        st.error("❌ Mindestens Fragebogen ODER CV erforderlich!")
        st.stop()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # ============================================
    # 1. DATEIEN EXTRAHIEREN
    # ============================================
    status_text.text("📖 Extrahiere Texte aus PDFs...")
    progress_bar.progress(10)
    
    fragebogen_text = ""
    cv_zeugnisse_text = ""
    notizen_text = ""
    
    # Fragebogen
    if fragebogen_file:
        if fragebogen_file.name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(fragebogen_file)
            for page in pdf_reader.pages:
                fragebogen_text += page.extract_text() + "\n"
        elif fragebogen_file.name.endswith('.txt'):
            fragebogen_text = fragebogen_file.read().decode("utf-8")
        # TODO: .msg mit extract-msg library
    
    # CV + Zeugnisse
    if cv_file:
        pdf_reader = PyPDF2.PdfReader(cv_file)
        total_pages = len(pdf_reader.pages)
        
        # Erste Hälfte = CV, zweite Hälfte = Zeugnisse
        cv_pages = total_pages // 2
        
        cv_text = ""
        zeugnisse_text = ""
        
        for i, page in enumerate(pdf_reader.pages):
            text = page.extract_text() + "\n"
            if i < cv_pages:
                cv_text += text
            else:
                zeugnisse_text += text
        
        cv_zeugnisse_text = cv_text + "\n\n=== ZEUGNISSE ===\n\n" + zeugnisse_text
    
    # Notizen
    if notizen_file:
        if notizen_file.name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(notizen_file)
            for page in pdf_reader.pages:
                notizen_text += page.extract_text() + "\n"
        elif notizen_file.name.endswith('.txt'):
            notizen_text = notizen_file.read().decode("utf-8")
        # TODO: OCR für Bilder mit pytesseract
    
    progress_bar.progress(20)
    
    # ============================================
    # 2. KI: STRUKTURIERTE DATEN EXTRAHIEREN
    # ============================================
    status_text.text("🤖 Extrahiere strukturierte Daten mit KI...")
    
    extraktions_prompt = f"""Du bist Experte für Schweizer Recruiting-Dossiers.

QUELLEN-PRIORITÄT (bei Widerspruch):
1. Notizen (überschreibt alles!)
2. Fragebogen
3. CV
4. Zeugnisse

FRAGEBOGEN:
{fragebogen_text}

CV + ZEUGNISSE:
{cv_zeugnisse_text}

NOTIZEN (HÖCHSTE PRIORITÄT!):
{notizen_text}

HINWEISE VON ANDREAS:
{hinweise_andreas}

EXTRAHIERE EXAKT (Schweizer Format: ss statt ß, keine Bindestriche):

{{
  "kandidat_name": "Vorname Nachname",
  "nachname": "nur Nachname",
  "geburtsdatum": "TT.MM.JJJJ",
  "nationalitaet": "Schweiz / Deutschland / etc",
  "mobilitaet": "Führerschein B / ÖV / etc",
  "verfuegbarkeit": "per sofort / nach Vereinbarung / 3 Monate",
  "salaer_realistisch": "150'000 CHF x 13",
  "kuendigungsfrist_wortlaut": "EXAKTER Wortlaut aus Fragebogen!",
  
  "hoechste_ausbildung": "z.B. Dipl. Elektroingenieur FH",
  
  "ausbildungen": [
    "2020 - 2023 Bachelor of Science FH in Elektrotechnik, FH Zürich",
    "2018 - 2020 Berufsmaturität Technik, BBZ Zürich"
  ],
  
  "sprachen": [
    {{"sprache": "Deutsch", "niveau": "Muttersprache"}},
    {{"sprache": "Englisch", "niveau": "sehr gute Kenntnisse"}},
    {{"sprache": "Französisch", "niveau": "Grundkenntnisse"}}
  ],
  
  "ict_regelmaessig": ["MS Office", "AutoCAD", "SAP"],
  "ict_grundkenntnisse": ["Excel", "PowerPoint", "Teams"],
  
  "jobtitel": ["Projektleiter Elektroplanung", "Elektroingenieur", "Technischer Sachbearbeiter"],
  
  "wechselgrund_stichworte": "sucht mehr Verantwortung, flachere Hierarchien, ...",
  "ziele_stichworte": "Projektleitung, Teamführung, technische Weiterentwicklung, ...",
  "eindruck_stichworte": "offen, kompetent, strukturiert, motiviert, ..."
}}

REGELN:
- Bei Unsicherheit: Feld leer "" oder []
- Ausbildungen: Neueste ZUERST, nur Jahre, Format "JJJJ - JJJJ"
- Sprachen: Nur mit Kenntnissen, ohne A1/B2/C1
- ICT: MS Office wenn einzelne Office-Programme vorkommen
- Salär: NUR realistische Vorstellung, NICHT aktuelles Salär!
- Kündigungsfrist: EXAKTER Wortlaut, keine Interpretation!
- Schweizer Deutsch: ss (nicht ß), keine Bindestriche
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du bist Schweizer Recruiting-Experte. Antworte nur mit JSON."},
            {"role": "user", "content": extraktions_prompt}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    daten = json.loads(response.choices[0].message.content)
    
    progress_bar.progress(40)
    
    # ============================================
    # 3. KI: SCHLAGWORTE FÜR TITELBLATT
    # ============================================
    status_text.text("💡 Generiere Schlagworte...")
    
    schlagworte_prompt = f"""Erstelle 4-6 aussagekräftige Schlagworte für das Titelblatt eines Recruiting-Dossiers.

KANDIDAT: {daten.get('kandidat_name')}

INFOS:
{cv_zeugnisse_text[:3000]}
{notizen_text}

ANFORDERUNGEN:
- 4-6 einzelne Schlagworte ODER max. 3 Zweier-Pärchen
- Zeigen Qualifikation des Kandidaten
- Beispiele: "selbständig", "unternehmerisch denkend und handelnd", "engagiert", "lösungsorientiert", "erfahren"
- Muss zu Infos im Dossier passen
- Schweizer Deutsch (ss, keine Bindestriche)

Gib als JSON-Array zurück: ["Schlagwort1", "Schlagwort2", ...]
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": schlagworte_prompt}],
        temperature=0.4,
        response_format={"type": "json_object"}
    )
    
    schlagworte_result = json.loads(response.choices[0].message.content)
    schlagworte = schlagworte_result.get('schlagworte', [])
    
    # Padding auf 6 (falls weniger)
    while len(schlagworte) < 6:
        schlagworte.append("")
    
    progress_bar.progress(50)
    
    # ============================================
    # 4. KI: WECHSELGRUND
    # ============================================
    status_text.text("✍️ Generiere Wechselgrund...")
    
    wechselgrund_prompt = f"""Erstelle den Abschnitt "Grund des Stellenwechsels" für ein Kandidatendossier.

KANDIDAT: {daten.get('kandidat_name')}
NACHNAME: {daten.get('nachname')}

STICHWORTE:
{daten.get('wechselgrund_stichworte', '')}
{hinweise_andreas}

REGELN:
- 2-3 Sätze
- Name {daten.get('nachname')} 2-3x erwähnen
- Endet mit: "Im persönlichen Gespräch gibt Herr {daten.get('nachname')} gerne mehr Auskunft."
- Sachlich, professionell
- Schweizer Deutsch (ss, keine Bindestriche, kein Dialekt)

Nur der Text, keine Überschrift.
"""

    wechselgrund = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": wechselgrund_prompt}],
        temperature=0.4
    ).choices[0].message.content.strip()
    
    progress_bar.progress(60)
    
    # ============================================
    # 5. KI: ZIELE
    # ============================================
    status_text.text("🎯 Generiere Ziele...")
    
    ziele_prompt = f"""Erstelle den Abschnitt "Ziele" für ein Kandidatendossier.

KANDIDAT: {daten.get('kandidat_name')}
NACHNAME: {daten.get('nachname')}

STICHWORTE:
{daten.get('ziele_stichworte', '')}
{hinweise_andreas}

REGELN:
- Beginne mit: "Herr {daten.get('nachname')} sucht eine neue Herausforderung, in die er seine Kenntnisse und Erfahrungen einbringen kann."
- Name {daten.get('nachname')} 2-3x erwähnen
- Endet mit (leicht variiert): "Wichtig ist ihm ein gut aufgestellter Arbeitgeber, interessante Projekte und Tätigkeiten sowie ein wertschätzendes Arbeitsumfeld."
- Schweizer Deutsch (ss, keine Bindestriche)

Nur der Text, keine Überschrift.
"""

    ziele = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": ziele_prompt}],
        temperature=0.4
    ).choices[0].message.content.strip()
    
    progress_bar.progress(70)
    
    # ============================================
    # 6. KI: ARBEITSZEUGNISSE ZUSAMMENFASSUNG
    # ============================================
    status_text.text("📜 Fasse Arbeitszeugnisse zusammen...")
    
    zeugnisse_prompt = f"""Fasse die Arbeitszeugnisse zusammen für ein Kandidatendossier.

KANDIDAT: {daten.get('kandidat_name')}
NACHNAME: {daten.get('nachname')}

ZEUGNISSE:
{zeugnisse_text if 'zeugnisse_text' in locals() else cv_zeugnisse_text[len(cv_zeugnisse_text)//2:]}

REGELN:
- BEGINNE MIT: "Seine Vorgesetzten schreiben folgendes über Herrn {daten.get('nachname')}:"
- Dann WORTWÖRTLICHE Zitate in «Gänsefüsschen»
- Reihenfolge: 1) Fachlich & Erfahrungen, 2) Persönlichkeit, 3) Umgang mit Vorgesetzten/Kunden/Mitarbeitern
- Alles hintereinander (nicht einzeln pro Kategorie)
- Ca. 10 Sätze, aussagekräftig
- WICHTIG: Muss auf 1/3 Seite passen! Falls Material zu lang, kürzen.
- Schweizer Deutsch (ss)

Nur der Text mit Einleitung.
"""

    arbeitszeugnisse = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": zeugnisse_prompt}],
        temperature=0.2
    ).choices[0].message.content.strip()
    
    # Sicherstellen dass nicht zu lang (max ca. 1500 Zeichen)
    if len(arbeitszeugnisse) > 1500:
        kuerzen_prompt = f"""Kürze folgenden Text auf max. 10 Sätze, behalte wichtigste Aussagen und Format:

{arbeitszeugnisse}

WICHTIG: Beginne weiterhin mit "Seine Vorgesetzten..." und behalte Gänsefüsschen.
"""
        arbeitszeugnisse = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": kuerzen_prompt}],
            temperature=0.2
        ).choices[0].message.content.strip()
    
    progress_bar.progress(80)
    
    # ============================================
    # 7. KI: PERSÖNLICHER EINDRUCK
    # ============================================
    status_text.text("👤 Generiere persönlichen Eindruck...")
    
    eindruck_prompt = f"""Erstelle "Mein persönlicher Eindruck" für ein Kandidatendossier.

KANDIDAT: {daten.get('kandidat_name')}
NACHNAME: {daten.get('nachname')}

STICHWORTE:
{daten.get('eindruck_stichworte', '')}
{notizen_text}
{hinweise_andreas}

REGELN:
- BEGINNE MIT: "Herr {daten.get('nachname')} ist ein aufgestellter, freundlicher und sympathischer Mann, der einen sehr guten Eindruck hinterlassen hat. Er kommuniziert offen, überlegt und schlüssig."
- Name {daten.get('nachname')} ca. 3x erwähnen
- Unsicherheiten in "es scheint"-Form ("Er scheint selbständig zu arbeiten...")
- Schweizer Deutsch (ss, keine Bindestriche)
- Ca. 5-8 Sätze

Nur der Text, keine Überschrift.
"""

    eindruck = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": eindruck_prompt}],
        temperature=0.4
    ).choices[0].message.content.strip()
    
    progress_bar.progress(85)
    
    # ============================================
    # 8. KI: KOMPETENZEN
    # ============================================
    status_text.text("⚡ Generiere Kompetenzen...")
    
    kompetenzen_prompt = f"""Erstelle Kompetenzpunkte für ein Kandidatendossier.

KANDIDAT: {daten.get('kandidat_name')}

JOBTITEL: {', '.join(daten.get('jobtitel', []))}

CV:
{cv_text if 'cv_text' in locals() else cv_zeugnisse_text[:3000]}

REGELN:
- ERSTE ZEILE: Alle Jobtitel kommagetrennt, höchste Funktion zuerst
- Dann: Kurze, prägnante, fachliche Bullet Points (ohne Bullet-Zeichen)
- KEINE Leerzeilen zwischen Punkten
- Muss auf Seite 2 passen - bei zu viel Text Unwichtiges streichen
- NIE auf Seite 3 fortführen!
- Max. 8-10 Kompetenzpunkte
- Schweizer Deutsch (ss, keine Bindestriche)

Format:
Projektleiter, Ingenieur, Sachbearbeiter
Mehrjährige Erfahrung in Elektroplanung
Kenntnisse in AutoCAD und SAP
...

Nur die Kompetenzen, keine Überschrift.
"""

    kompetenzen = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": kompetenzen_prompt}],
        temperature=0.3
    ).choices[0].message.content.strip()
    
    progress_bar.progress(90)
    
    # ============================================
    # 9. FORMATIERUNGEN VORBEREITEN
    # ============================================
    status_text.text("📝 Bereite Formatierungen vor...")
    
    # Sprachen: Eine Zeile, grosse Abstände, keine Kommas
    sprachen_formatiert = "     ".join([
        f"{s['sprache']}: {s['niveau']}"
        for s in daten.get('sprachen', [])
        if s.get('sprache')
    ])
    
    # ICT: 2 Zeilen
    ict_regelmaessig = ", ".join(daten.get('ict_regelmaessig', []))
    ict_grundkenntnisse_liste = daten.get('ict_grundkenntnisse', [])
    if ict_grundkenntnisse_liste:
        ict_gesamt = ict_regelmaessig + "\nGrundkenntnisse: " + ", ".join(ict_grundkenntnisse_liste)
    else:
        ict_gesamt = ict_regelmaessig
    
    # Ausbildungen: Zeilenumbrüche
    ausbildungen_formatiert = "\n".join(daten.get('ausbildungen', []))
    
    # Salär mit Zusatz
    salaer_formatiert = daten.get('salaer_realistisch', '') + "\nGesprächsbereit je nach Gesamtpaket"
    
    # ============================================
    # 10. WORD-VORLAGE BEFÜLLEN
    # ============================================
    status_text.text("📄 Befülle Word-Vorlage...")
    
    # Vorlage laden (aus Repository oder Upload)
    doc = DocxTemplate("Vorlage.docx")  # Oder: DocxTemplate(vorlage_upload)
    
    context = {
        # Seite 1
        "Kandidat": daten.get('kandidat_name', ''),
        "höchste Ausbildung": daten.get('hoechste_ausbildung', ''),
        "Wertepaar": schlagworte[0] if len(schlagworte) > 0 else '',
        # Für flexible Anzahl würde man Loop brauchen - hier feste Struktur
        "Schlagwort1": schlagworte[0] if len(schlagworte) > 0 else '',
        "Schlagwort2": schlagworte[1] if len(schlagworte) > 1 else '',
        "Schlagwort3": schlagworte[2] if len(schlagworte) > 2 else '',
        "Schlagwort4": schlagworte[3] if len(schlagworte) > 3 else '',
        "Schlagwort5": schlagworte[4] if len(schlagworte) > 4 else '',
        "Schlagwort6": schlagworte[5] if len(schlagworte) > 5 else '',
        
        # Seite 2 - Stammdaten
        "Geburtsdatum": daten.get('geburtsdatum', ''),
        "Nationalität": daten.get('nationalitaet', ''),
        "Mobilität": daten.get('mobilitaet', ''),
        "Verfügbarkeit": daten.get('verfuegbarkeit', ''),
        "Salär": salaer_formatiert,
        
        "Ausbildung": ausbildungen_formatiert,
        "Sprachen": sprachen_formatiert,
        "ICT-Kenntnisse": ict_gesamt,
        "Kompetenzen": kompetenzen,
        
        # Seite 3 - Texte
        "Stellenwechsel": wechselgrund,
        "Ziele": ziele,
        "Arbeitszeugnisse": arbeitszeugnisse,  # WICHTIG: In Vorlage ergänzen!
        "Eindruck": eindruck,
        
        "Anmerkungen": "",  # Leer lassen laut Prompt
    }
    
    doc.render(context)
    
    progress_bar.progress(95)
    
    # ============================================
    # 11. QUALITÄTSKONTROLLE
    # ============================================
    status_text.text("✅ Führe Qualitätskontrolle durch...")
    
    warnungen = []
    
    # Prüfung 1: Salär ist realistisch (nicht aktuell)
    if "aktuell" in salaer_formatiert.lower():
        warnungen.append("⚠️ Salär: Enthält 'aktuell' - prüfe ob realistische Vorstellung!")
    
    # Prüfung 2: Sprachen ohne A1/B2
    if any(level in sprachen_formatiert for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']):
        warnungen.append("⚠️ Sprachen: Enthält Niveau-Codes (A1/B2) - sollten entfernt werden!")
    
    # Prüfung 3: Kommas in Sprachen
    if ',' in sprachen_formatiert:
        warnungen.append("⚠️ Sprachen: Enthält Kommas - sollten grosse Abstände sein!")
    
    # Prüfung 4: ICT Grundkenntnisse
    if ict_grundkenntnisse_liste and "Grundkenntnisse:" not in ict_gesamt:
        warnungen.append("⚠️ ICT: Grundkenntnisse fehlt als Präfix!")
    
    # Prüfung 5: Kompetenzen Länge
    if len(kompetenzen) > 1200:
        warnungen.append("⚠️ Kompetenzen: Sehr lang - könnte auf Seite 3 rutschen!")
    
    # Prüfung 6: Kündigungsfrist
    if not daten.get('kuendigungsfrist_wortlaut'):
        warnungen.append("⚠️ Kündigungsfrist: Nicht gefunden - bitte manuell prüfen!")
    
    progress_bar.progress(100)
    status_text.text("✅ Fertig!")
    
    # ============================================
    # 12. DOWNLOAD
    # ============================================
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    
    nachname = daten.get('nachname', 'Kandidat')
    dossier_name = f"Dossier_{nachname}.docx"
    
    st.success("🎉 Dossier erfolgreich generiert!")
    
    st.download_button(
        label="📥 Dossier herunterladen",
        data=bio.getvalue(),
        file_name=dossier_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
    
    # ============================================
    # 13. QUALITÄTSREPORT
    # ============================================
    st.divider()
    st.subheader("📋 Qualitätskontrolle")
    
    if warnungen:
        st.warning("**Folgende Punkte prüfen:**")
        for warnung in warnungen:
            st.write(warnung)
    else:
        st.success("✅ Alle automatischen Prüfungen bestanden!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Extrahierte Daten:**")
        st.json({
            "Name": daten.get('kandidat_name'),
            "Geburtsdatum": daten.get('geburtsdatum'),
            "Salär": daten.get('salaer_realistisch'),
            "Kündigungsfrist": daten.get('kuendigungsfrist_wortlaut'),
            "Höchste Ausbildung": daten.get('hoechste_ausbildung'),
        })
    
    with col2:
        st.write("**Schlagworte:**")
        for i, sw in enumerate(schlagworte[:6], 1):
            if sw:
                st.write(f"{i}. {sw}")
    
    # Expander für Vorschau der generierten Texte
    with st.expander("👁️ Vorschau generierte Texte"):
        st.write("**Wechselgrund:**")
        st.write(wechselgrund)
        st.write("")
        st.write("**Ziele:**")
        st.write(ziele)
        st.write("")
        st.write("**Arbeitszeugnisse:**")
        st.write(arbeitszeugnisse)
        st.write("")
        st.write("**Persönlicher Eindruck:**")
        st.write(eindruck)
