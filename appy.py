import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ===============================
# Google Sheets authenticatie
# ===============================

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Haal de service-account credentials op uit Streamlit secrets
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)

# Autoriseer de client met de credentials
client = gspread.authorize(creds)

# Probeer de spreadsheet te openen
try:
    SHEET = client.open("urenregistratie").sheet1
except Exception as e:
    st.error("❌ Kan spreadsheet niet openen. Controleer of de naam klopt en of het service-account toegang heeft tot het document.")
    st.exception(e)
    st.stop()

# ===============================
# Streamlit UI
# ===============================

st.title("Urenregistratie & Inkomsten Tracker")

# Formulier voor ureninvoer
with st.form("uren_formulier"):
    datum = st.date_input("Datum", value=datetime.today())
    klant = st.text_input("Klant")
    project = st.text_input("Project")
    uren = st.number_input("Aantal uren", min_value=0.0, step=0.25)
    tarief = st.number_input("Tarief per uur (€)", min_value=0.0, step=1.0)
    submitted = st.form_submit_button("Toevoegen")

    if submitted:
        totaal = uren * tarief
        nieuwe_rij = [str(datum), klant, project, uren, tarief, totaal]
        SHEET.append_row(nieuwe_rij)
        st.success("✅ Uren succesvol toegevoegd!")

# ===============================
# Toon data uit de sheet
# ===============================

data = SHEET.get_all_records()
df = pd.DataFrame(data)

if not df.empty:
    st.subheader("📊 Overzicht")
    st.dataframe(df)

    # Controleer of juiste kolommen aanwezig zijn
    if "Aantal uren" in df.columns and "Totaal" in df.columns:
        totaal_uren = df["Aantal uren"].sum()
        totaal_inkomsten = df["Totaal"].sum()

        st.metric("Totale uren", f"{totaal_uren:.2f} uur")
        st.metric("Totale inkomsten", f"€ {totaal_inkomsten:.2f}")
    else:
        st.warning("⚠️ Kolommen 'Aantal uren' en/of 'Totaal' ontbreken. Controleer je Google Sheet.")
else:
    st.info("Nog geen gegevens beschikbaar in de sheet.")
