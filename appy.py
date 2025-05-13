import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Set up Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Open sheet
sheet_url = st.secrets["gsheet"]["sheet_url"]
sheet = client.open_by_url(sheet_url).sheet1

# Inlezen data
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Titel
st.title("Urenregistratie & Inkomsten Tracker")

# Formulier voor invoer
with st.form("uren_form"):
    datum = st.date_input("Datum", value=datetime.today())
    uren = st.number_input("Aantal uren gewerkt", min_value=0.0, step=0.25)
    tarief = st.number_input("Uurtarief (€)", min_value=0.0, step=1.0)
    activiteit = st.text_input("Activiteit")
    submit = st.form_submit_button("Toevoegen")

    if submit:
        new_row = {
            "Datum": datum.strftime("%Y-%m-%d"),
            "Uren": uren,
            "Tarief": tarief,
            "Activiteit": activiteit,
            "Inkomsten": round(uren * tarief, 2)
        }
        sheet.append_row(list(new_row.values()))
        st.success("Gegevens toegevoegd!")

        # Refresh dataframe
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

# Overzicht
if not df.empty:
    df["Datum"] = pd.to_datetime(df["Datum"])
    df = df.sort_values("Datum", ascending=False)
    st.subheader("Overzicht")
    st.dataframe(df)

    totaal_inkomen = df["Inkomsten"].sum()
    totaal_uren = df["Uren"].sum()
    st.metric("Totaal verdiend", f"€ {totaal_inkomen:,.2f}")
    st.metric("Totaal uren", f"{totaal_uren:.2f} uur")
else:
    st.info("Nog geen gegevens ingevoerd.")

