import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# Scopes voor Google Sheets toegang
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Authenticatie via Streamlit secrets met google-auth
CREDS = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)
client = gspread.authorize(CREDS)

# Open de spreadsheet en de juiste sheet
try:
    SHEET = client.open("urenregistratie").sheet1
except Exception as e:
    st.error("Kan de spreadsheet niet openen. Controleer of de naam klopt en of de service account toegang heeft gedeeld.")
    st.stop()

# Titel
st.title("Urenregistratie & Inkomsten Tracker")

# Formulier voor invoer
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
        try:
            SHEET.append_row(nieuwe_rij)
            st.success("Uren succesvol toegevoegd!")
        except Exception as e:
            st.error("Fout bij toevoegen van de gegevens aan Google Sheet.")
            st.exception(e)

# Toon bestaande data
try:
    data = SHEET.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error("Fout bij ophalen van gegevens uit Google Sheet.")
    st.stop()

if not df.empty:
    st.subheader("Overzicht")
    st.dataframe(df)

    # Zorg dat de kolomnamen correct zijn
    if "Aantal uren" in df.columns and "Totaal" in df.columns:
        totaal_uren = df["Aantal uren"].sum()
        totaal_inkomsten = df["Totaal"].sum()

        st.metric("Totale uren", f"{totaal_uren:.2f} uur")
        st.metric("Totale inkomsten", f"€ {totaal_inkomsten:.2f}")
    else:
        st.warning("Controleer of de kolommen 'Aantal uren' en 'Totaal' correct gespeld zijn in je Google Sheet.")
