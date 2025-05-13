import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Urenregistratie", layout="centered")

st.title("Urenregistratie & Inkomsten Tracker")

CSV_FILE = "uren.csv"

# Probeer CSV te laden of maak lege DataFrame aan
if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
    try:
        df = pd.read_csv(CSV_FILE, parse_dates=["Datum"])
    except Exception:
        df = pd.DataFrame(columns=["Datum", "Activiteit", "Uren", "Inkomsten"])
else:
    df = pd.DataFrame(columns=["Datum", "Activiteit", "Uren", "Inkomsten"])

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
        nieuwe_gegevens = {
            "Datum": pd.to_datetime(datum),
            "Activiteit": activiteit,
            "Uren": uren,
            "Inkomsten": round(uren * tarief, 2)
        }
        df = pd.concat([df, pd.DataFrame([nieuwe_gegevens])], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)

        # Sla tijdelijk op in session_state en herlaad
        st.session_state["invoer_toegevoegd"] = True
        st.experimental_rerun()
    else:
        st.warning("Vul een activiteit in.")

# Herlaad gegevens na invoer
if st.session_state.get("invoer_toegevoegd", False):
    if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
        df = pd.read_csv(CSV_FILE, parse_dates=["Datum"])
    st.session_state["invoer_toegevoegd"] = False



# Overzicht tonen
st.subheader("Overzicht")
if not df.empty:
    df_sorted = df.sort_values("Datum", ascending=False)
    st.dataframe(df_sorted, use_container_width=True)

    totaal = df["Inkomsten"].sum()
    st.metric("Totaal verdiend", f"€ {totaal:.2f}")

    st.download_button("Download als CSV", data=df.to_csv(index=False), file_name="uren.csv", mime="text/csv")
else:
    st.info("Nog geen gegevens ingevoerd.")

