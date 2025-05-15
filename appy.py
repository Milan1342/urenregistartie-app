import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Scopes voor Google Sheets toegang
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Authenticatie via Streamlit secrets
CREDS = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], SCOPE
)
client = gspread.authorize(CREDS)

# Open de spreadsheet
try:
    SHEET = client.open("urenregistratie").sheet1
except Exception:
    st.error("❌ Kan spreadsheet niet openen. Controleer of de naam klopt en of het service-account toegang heeft tot het document.")
    st.stop()

st.title("Urenregistratie & Inkomsten Tracker")

with st.form("uren_formulier"):
    datum = st.date_input("Datum", value=datetime.today())
    starttijd = st.time_input("Starttijd")
    eindtijd = st.time_input("Eindtijd")
    pauze_min = st.number_input("Pauze (in minuten)", min_value=0, step=5)

    uurloon_input = st.text_input("Uurloon (€)", placeholder="Bijv. 12,50")

    submitted = st.form_submit_button("Toevoegen")

    if submitted:
        # Verwerk uurloon met ondersteuning voor komma
        try:
            uurloon = float(uurloon_input.replace(",", "."))
        except ValueError:
            st.error("❌ Ongeldige invoer voor uurloon. Gebruik alleen cijfers, bijv. 12,50.")
            st.stop()

        start_dt = datetime.combine(datum, starttijd)
        eind_dt = datetime.combine(datum, eindtijd)

        if eind_dt <= start_dt:
            st.error("❌ Eindtijd moet later zijn dan starttijd.")
        else:
            totale_tijd = (eind_dt - start_dt).total_seconds() / 3600  # in uren
            pauze_uren = pauze_min / 60
            gewerkte_uren = max(totale_tijd - pauze_uren, 0)

            salaris = gewerkte_uren * uurloon

            # Netto salaris voor studenten met inkomen < 20.000 → ~96% belastingvrij
            netto_salaris = salaris * 0.96

            nieuwe_rij = [str(datum), round(gewerkte_uren, 2), uurloon, round(salaris, 2), round(netto_salaris, 2)]
            SHEET.append_row(nieuwe_rij)

            st.success("✅ Uren succesvol toegevoegd!")

# Data ophalen
verwachte_kolommen = ["Datum", "Uren", "Uurloon", "Salaris", "Netto Salaris"]
try:
    data = SHEET.get_all_records(expected_headers=verwachte_kolommen)
    df = pd.DataFrame(data)
except Exception:
    st.error(f"❌ De volgende kolommen ontbreken in het blad: {', '.join(verwachte_kolommen)}")
    st.stop()

if not df.empty:
    st.subheader("📊 Overzicht")
    st.dataframe(df)

    try:
        df["Uren"] = pd.to_numeric(df["Uren"], errors="coerce")
        df["Salaris"] = pd.to_numeric(df["Salaris"], errors="coerce")
        df["Netto Salaris"] = pd.to_numeric(df["Netto Salaris"], errors="coerce")

        totaal_uren = df["Uren"].sum()
        totaal_bruto = df["Salaris"].sum()
        totaal_netto = df["Netto Salaris"].sum()

        st.metric("Totale uren", f"{totaal_uren:.2f} uur")
        st.metric("Totaal salaris", f"€ {totaal_bruto:.2f}")
        st.metric("Netto salaris", f"€ {totaal_netto:.2f}")
    except Exception:
        st.warning("⚠️ Kon totalen niet berekenen — controleer de datatypes.")
else:
    st.info("📂 Geen gegevens beschikbaar in de spreadsheet.")
