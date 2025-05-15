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

# Open de spreadsheet en de juiste sheet
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
    uren = st.number_input("Aantal uren", min_value=0.0, step=0.25)
    tarief = st.number_input("Uurloon (€)", min_value=0.0, step=1.0)
    submitted = st.form_submit_button("Toevoegen")

    if submitted:
        salaris = uren * tarief
        nieuwe_rij = [str(datum), uren, tarief, salaris]
        SHEET.append_row(nieuwe_rij)
        st.success("Uren succesvol toegevoegd!")

# Data ophalen met opgegeven headers
headers = ["Datum", "Uren", "Uurloon", "Salaris"]
data = SHEET.get_all_records(expected_headers=headers)
df = pd.DataFrame(data)

if not df.empty:
    st.subheader("Overzicht")
    st.dataframe(df)

    totaal_uren = df["Uren"].sum()
    totaal_salaris = df["Salaris"].sum()

    st.metric("Totale uren", f"{totaal_uren:.2f} uur")
    st.metric("Totaal salaris", f"€ {totaal_salaris:.2f}")
