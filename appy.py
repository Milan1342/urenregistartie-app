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
    uren_input = st.text_input("Uren gewerkt", placeholder="Bijv. 5,5 of 5.5")
    uurloon_input = st.text_input("Uurloon (€)", placeholder="Bijv. 12,50 of 12.50")
    submitted = st.form_submit_button("Toevoegen")

    if submitted:
        try:
            # Vervang komma's door punten voor correcte conversie
            uren = float(uren_input.replace(",", "."))
            uurloon = float(uurloon_input.replace(",", "."))

            salaris = uren * uurloon
            # Voor studenten < €20.000/jaar is belastingdruk ~7% incl. arbeidskorting
            belastingdruk = 0.07
            netto_salaris = round(salaris * (1 - belastingdruk), 2)

            nieuwe_rij = [str(datum), uren, uurloon, round(salaris, 2), netto_salaris]
            SHEET.append_row(nieuwe_rij)
            st.success("✅ Uren succesvol toegevoegd!")
        except ValueError:
            st.error("❌ Ongeldige invoer. Gebruik alleen cijfers (bijv. 12,5 of 12.5).")

# Toon bestaande data
try:
    data = SHEET.get_all_records(expected_headers=["Datum", "Uren", "Uurloon", "Salaris", "Netto Salaris"])
    df = pd.DataFrame(data)
except Exception as e:
    st.warning("⚠️ Fout bij het ophalen van de gegevens. Controleer of de headers kloppen in de sheet.")
    st.stop()

# Controleer of alle vereiste kolommen aanwezig zijn
verwachte_kolommen = ["Datum", "Uren", "Uurloon", "Salaris", "Netto Salaris"]
ontbrekend = [kol for kol in verwachte_kolommen if kol not in df.columns]
if ontbrekend:
    st.error(f"❌ De volgende kolommen ontbreken in de sheet: {', '.join(ontbrekend)}")
    st.stop()

if not df.empty:
    st.subheader("📊 Overzicht")
    st.dataframe(df)

    # Zorg dat de kolommen numeriek zijn
    df["Uren"] = pd.to_numeric(df["Uren"], errors="coerce")
    df["Salaris"] = pd.to_numeric(df["Salaris"], errors="coerce")
    df["Netto Salaris"] = pd.to_numeric(df["Netto Salaris"], errors="coerce")

    # Bereken totalen
    totaal_uren = df["Uren"].sum(skipna=True)
    totaal_salaris = df["Salaris"].sum(skipna=True)
    totaal_netto = df["Netto Salaris"].sum(skipna=True)

    # Toon totalen
    st.metric("Totale uren", f"{totaal_uren:.2f} uur")
    st.metric("Bruto totaal", f"€ {totaal_salaris:.2f}")
    st.metric("Netto totaal", f"€ {totaal_netto:.2f}")
else:
    st.info("📂 Geen gegevens beschikbaar in de spreadsheet.")

