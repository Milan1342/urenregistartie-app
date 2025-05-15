import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Scopes voor Google Sheets toegang
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Authenticatie via Streamlit secrets
CREDS = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], SCOPE
)
client = gspread.authorize(CREDS)

# Probeer de sheet te openen met foutafhandeling
try:
    SHEET = client.open("urenregistratie").sheet1
except Exception as e:
    st.error("❌ Kan spreadsheet niet openen. Controleer of de naam klopt en of het service-account toegang heeft tot het document.")
    st.stop()

# Titel
st.title("Urenregistratie & Inkomsten Tracker")

# Formulier voor invoer
with st.form("uren_formulier"):
    datum = st.date_input("Datum", value=datetime.today())
    klant = st.text_input("Klant")
    project = st.text_input("Project")
    uren_input = st.text_input("Aantal uren (bijv. 7,5)")
    tarief_input = st.text_input("Tarief per uur (€) (bijv. 45,00)")
    submitted = st.form_submit_button("Toevoegen")

    if submitted:
        try:
            # Komma naar punt en omzetten naar float
            uren = float(uren_input.replace(",", "."))
            tarief = float(tarief_input.replace(",", "."))
            totaal = uren * tarief
            nieuwe_rij = [str(datum), klant, project, uren, tarief, totaal]
            SHEET.append_row(nieuwe_rij)
            st.success("✅ Uren succesvol toegevoegd!")
        except ValueError:
            st.error("❌ Ongeldige invoer. Gebruik alleen cijfers en een punt of komma voor decimalen.")

# Toon bestaande data
try:
    data = SHEET.get_all_records(expected_headers=["Datum", "Klant", "Project", "Aantal uren", "Tarief per uur (€)", "Totaal"])
    df = pd.DataFrame(data)
except Exception as e:
    st.error("❌ Kan gegevens niet ophalen uit de sheet. Controleer de headerrij.")
    st.stop()

if not df.empty:
    st.subheader("Overzicht")
    st.dataframe(df)

    # Som van uren en inkomsten (controleer kolomnamen)
    if "Aantal uren" in df.columns and "Totaal" in df.columns:
        totaal_uren = df["Aantal uren"].sum()
        totaal_inkomsten = df["Totaal"].sum()

        st.metric("Totale uren", f"{totaal_uren:.2f} uur")
        st.metric("Totale inkomsten", f"€ {totaal_inkomsten:.2f}")
    else:
        st.warning("Controleer of de kolommen 'Aantal uren' en 'Totaal' correct gespeld zijn in je Google Sheet.")
