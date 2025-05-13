import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# Scopes voor Google Sheets toegang
SCOPE = ["https://spreadsheets.google.com/feeds"]


# Authenticatie via Streamlit secrets
CREDS = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], SCOPE
)
client = gspread.authorize(CREDS)

# Open de spreadsheet en de juiste sheet
SHEET = client.open("urenregistratie").sheet1

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
        SHEET.append_row(nieuwe_rij)
        st.success("Uren succesvol toegevoegd!")

# Toon bestaande data
data = SHEET.get_all_records()
df = pd.DataFrame(data)

if not df.empty:
    st.subheader("Overzicht")
    st.dataframe(df)

    # Totale uren en inkomsten
    totaal_uren = df["Aantal uren"].sum()
    totaal_inkomsten = df["Totaal"].sum()

    st.metric("Totale uren", f"{totaal_uren:.2f} uur")
    st.metric("Totale inkomsten", f"€ {totaal_inkomsten:.2f}")

