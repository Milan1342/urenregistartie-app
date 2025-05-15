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
except Exception:
    st.error("❌ Kan spreadsheet niet openen. Controleer of de naam klopt en of het service-account toegang heeft tot het document.")
    st.stop()

# Titel
st.title("Urenregistratie & Inkomsten Tracker")

# Toon bestaande data
try:
    data = SHEET.get_all_records(expected_headers=["Datum", "Uren", "Uurloon", "Salaris", "Netto Salaris"])
    df = pd.DataFrame(data)
except Exception:
    st.warning("⚠️ Fout bij het ophalen van de gegevens. Controleer of de headers kloppen in de sheet.")
    st.stop()

# Zorg dat kolommen numeriek zijn
df["Uren"] = pd.to_numeric(df["Uren"], errors="coerce")
df["Salaris"] = pd.to_numeric(df["Salaris"], errors="coerce")
df["Netto Salaris"] = pd.to_numeric(df["Netto Salaris"], errors="coerce")

# Bereken totaal jaarinkomen tot nu toe
jaar_inkomen = df["Salaris"].sum(skipna=True)

# Formulier voor invoer
with st.form("uren_formulier"):
    datum = st.date_input("Datum", value=datetime.today())
    uren = st.number_input("Uren", min_value=0.0, step=0.25)
    uurloon = st.number_input("Uurloon (€)", min_value=0.0, step=1.0, format="%.2f")
    submitted = st.form_submit_button("Toevoegen")

    if submitted:
        salaris = uren * uurloon

        # Update jaarinkomen inclusief deze invoer
        nieuw_totaal = jaar_inkomen + salaris

        # Bepaal netto percentage op basis van drempel
        if nieuw_totaal <= 20000:
            netto_salaris = salaris * 0.93
        else:
            netto_salaris = salaris * 0.70

        nieuwe_rij = [str(datum), uren, uurloon, salaris, netto_salaris]
        SHEET.append_row(nieuwe_rij)
        st.success("✅ Uren succesvol toegevoegd!")

        # Herbereken voor weergave
        df.loc[len(df)] = [str(datum), uren, uurloon, salaris, netto_salaris]
        jaar_inkomen = nieuw_totaal

# Toon overzicht
if not df.empty:
    st.subheader("📊 Overzicht")
    st.dataframe(df)

    totaal_uren = df["Uren"].sum(skipna=True)
    totaal_bruto = df["Salaris"].sum(skipna=True)
    totaal_netto = df["Netto Salaris"].sum(skipna=True)

    st.metric("Totale uren", f"{totaal_uren:.2f} uur")
    st.metric("Totaal bruto salaris", f"€ {totaal_bruto:.2f}")
    st.metric("Totaal netto salaris", f"€ {totaal_netto:.2f}")
else:
    st.info("📂 Geen gegevens beschikbaar in de spreadsheet.")
