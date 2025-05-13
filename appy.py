import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="Urenregistratie", layout="centered")
st.title("Urenregistratie & Inkomsten Tracker")

# Google Sheets configuratie
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
client = gspread.authorize(CREDS)

# Sheet openen
SHEET_NAME = "urenregistratie"
sheet = client.open(SHEET_NAME).sheet1

# Data inlezen uit sheet
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Uurtarief invoer
tarief = st.number_input("Uurtarief (€ per uur)", value=25.0, step=1.0)

# Invoer nieuwe uren
st.subheader("Nieuwe invoer")
col1, col2 = st.columns(2)
with col1:
    datum = st.date_input("Datum", value=datetime.today())
with col2:
    uren = st.number_input("Aantal uren", min_value=0.0, value=1.0)

activiteit = st.text_input("Activiteit", placeholder="Bijv. Website bouwen")

if st.button("Toevoegen"):
    if activiteit:
        inkomsten = round(uren * tarief, 2)
        nieuwe_gegevens = [datum.strftime("%Y-%m-%d"), activiteit, uren, inkomsten]
        sheet.append_row(nieuwe_gegevens)
        st.success("Invoer toegevoegd!")
        st.experimental_rerun()
    else:
        st.warning("Vul een activiteit in.")

# Overzicht tonen
st.subheader("Overzicht")
if not df.empty:
    df["Datum"] = pd.to_datetime(df["Datum"])
    df_sorted = df.sort_values("Datum", ascending=False)
    st.dataframe(df_sorted, use_container_width=True)

    totaal = df["Inkomsten"].sum()
    st.metric("Totaal verdiend", f"€ {totaal:.2f}")

    st.download_button("Download als CSV", data=df.to_csv(index=False), file_name="uren.csv", mime="text/csv")
else:
    st.info("Nog geen gegevens ingevoerd.")


