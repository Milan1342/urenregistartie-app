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

# Formulier voor invoer
with st.form("uren_formulier"):
    datum = st.date_input("Datum", value=datetime.today())
    uren_input = st.text_input("Uren (bijv. 7,5 of 7.5)")
    uurloon_input = st.text_input("Uurloon (€) (bijv. 45,00 of 45.00)")
    submitted = st.form_submit_button("Toevoegen")

    if submitted:
        try:
            uren = float(uren_input.replace(",", "."))
            uurloon = float(uurloon_input.replace(",", "."))
            bruto_salaris = uren * uurloon
            netto_salaris = bruto_salaris * 0.70  # Aangenomen 30% belasting
            nieuwe_rij = [str(datum), uren, uurloon, bruto_salaris, netto_salaris]
            SHEET.append_row(nieuwe_rij)
            st.success("✅ Uren succesvol toegevoegd!")
        except ValueError:
            st.error("❌ Ongeldige invoer. Gebruik alleen getallen (en komma of punt voor decimalen).")

# Toon bestaande data
try:
    data = SHEET.get_all_records(expected_headers=["Datum", "Uren", "Uurloon", "Salaris", "Netto"])
    df = pd.DataFrame(data)
except Exception:
    st.warning("⚠️ Fout bij het ophalen van de gegevens. Controleer of de headers kloppen in de sheet.")
    st.stop()

if not df.empty:
    st.subheader("📊 Overzicht")
    st.dataframe(df)

    # Zorg dat de kolommen numeriek zijn
    df["Uren"] = pd.to_numeric(df["Uren"], errors="coerce")
    df["Salaris"] = pd.to_numeric(df["Salaris"], errors="coerce")
    df["Netto"] = pd.to_numeric(df["Netto"], errors="coerce")

    # Bereken totalen
    totaal_uren = df["Uren"].sum(skipna=True)
    totaal_bruto = df["Salaris"].sum(skipna=True)
    totaal_netto = df["Netto"].sum(skipna=True)

    # Toon totalen
    try:
        st.metric("Totale uren", f"{totaal_uren:.2f} uur")
        st.metric("Totaal bruto salaris", f"€ {totaal_bruto:.2f}")
        st.metric("Totaal netto salaris", f"€ {totaal_netto:.2f}")
    except Exception:
        st.warning("⚠️ Kan geen totalen tonen — controleer of alle data correct is ingevuld.")
else:
    st.info("📂 Geen gegevens beschikbaar in de spreadsheet.")
