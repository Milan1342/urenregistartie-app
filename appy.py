import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Urenregistratie", layout="centered")

st.title("Urenregistratie & Inkomsten Tracker")

# CSV-bestand beheren
CSV_FILE = "uren.csv"

# Probeer eerder ingevoerde data te laden
try:
    df = pd.read_csv(CSV_FILE, parse_dates=["Datum"])
except FileNotFoundError:
    df = pd.DataFrame(columns=["Datum", "Activiteit", "Uren", "Inkomsten"])

# Uurtarief invoeren
tarief = st.number_input("Uurtarief (€ per uur)", value=25.0, step=1.0)

# Nieuwe invoer
st.subheader("Nieuwe invoer")
col1, col2 = st.columns(2)
with col1:
    datum = st.date_input("Datum", value=datetime.today())
with col2:
    uren = st.number_input("Aantal uren", min_value=0.0, value=1.0)

activiteit = st.text_input("Activiteit", placeholder="Bijv. Website bouwen")

if st.button("Toevoegen"):
    if activiteit:
        nieuw = {
            "Datum": pd.to_datetime(datum),
            "Activiteit": activiteit,
            "Uren": uren,
            "Inkomsten": round(uren * tarief, 2)
        }
        df = pd.concat([df, pd.DataFrame([nieuw])], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)
        st.success("Invoer toegevoegd!")
        st.rerun()
    else:
        st.warning("Vul een activiteit in.")

# Overzicht
st.subheader("Overzicht")
if not df.empty:
    df_sorted = df.sort_values("Datum", ascending=False)
    st.dataframe(df_sorted, use_container_width=True)

    # Totale inkomsten
    totaal = df["Inkomsten"].sum()
    st.metric("Totaal verdiend", f"€ {totaal:.2f}")

    # Download knop
    st.download_button("Download als CSV", data=df.to_csv(index=False), file_name="uren.csv", mime="text/csv")
else:
    st.info("Nog geen gegevens ingevoerd.")
