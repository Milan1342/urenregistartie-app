import streamlit as st
import pandas as pd
import re
from datetime import datetime, date, time
from io import BytesIO

st.set_page_config(page_title="Urenregistratie", layout="wide")

# Centrale periode-instelling in de sidebar
if "periode_start" not in st.session_state:
    st.session_state["periode_start"] = date.today()
if "periode_eind" not in st.session_state:
    st.session_state["periode_eind"] = date.today()

with st.sidebar.expander("Periode instellen", expanded=True):
    st.write("Stel hier de standaard periode in voor overzichten en filters.")
    periode_start = st.date_input("Periode start", st.session_state["periode_start"], key="periode_start_input")
    periode_eind = st.date_input("Periode eind", st.session_state["periode_eind"], key="periode_eind_input")
    if st.button("Periode opslaan"):
        st.session_state["periode_start"] = periode_start
        st.session_state["periode_eind"] = periode_eind
        st.success("Periode opgeslagen!")

pagina = st.sidebar.radio(
    "Ga naar pagina:",
    ("Uren invoeren", "Overzicht", "Bedrijven beheren")
)

if "uren_data" not in st.session_state:
    st.session_state["uren_data"] = []
if "bedrijven" not in st.session_state:
    st.session_state["bedrijven"] = []

def to_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def weeknummer(datum: str) -> int:
    return datetime.strptime(datum, "%Y-%m-%d").isocalendar()[1]

pattern = re.compile(
    r"(?P<dag>\w{2})-\s*(?P<datum>\d{1,2}\s\w{3}(?:\s\d{4})?)\s+"
    r"(?P<start>\d{1,2}[.:]\d{2})\s*/\s*(?P<eind>\d{1,2}[.:]\d{2})\s*"
    r"\(\s*(?P<pauze>\d+)\s*\)\s+(?P<uren>[\d.,]+)\s*uur",
    re.IGNORECASE
)

def parse_row(row: str, default_year: int, bedrijf: str) -> dict | None:
    match = pattern.match(row.strip())
    if match:
        items = match.groupdict()
        start_time = items['start'].replace('.', ':')
        end_time = items['eind'].replace('.', ':')
        # Voeg jaar toe als niet aanwezig
        if len(items['datum'].split()) == 2:
            datum_str = f"{items['datum']} {default_year}"
        else:
            datum_str = items['datum']
        try:
            datum_obj = datetime.strptime(datum_str, "%d %b %Y")
        except ValueError:
            return None
        return {
            "Bedrijf": bedrijf,
            "Dag": items['dag'].capitalize(),
            "Datum": datum_obj.strftime("%Y-%m-%d"),
            "Starttijd": start_time,
            "Eindtijd": end_time,
            "Pauze (min)": int(items['pauze']),
            "Uren": float(items['uren'].replace(',', '.'))
        }
    return None

# ------------------ Bedrijven beheren ------------------
if pagina == "Bedrijven beheren":
    st.title("Bedrijven beheren")
    st.markdown("Voeg bedrijven toe met uurtarief en loonheffing.")

    with st.form("bedrijf_form", clear_on_submit=True):
        naam = st.text_input("Bedrijfsnaam")
        uurtarief = st.number_input("Uurtarief (€)", min_value=0.0, value=12.0, step=0.5)
        loonheffing = st.checkbox("Loonheffing aanwezig?", value=True)
        toevoegen = st.form_submit_button("Toevoegen")

        if toevoegen and naam:
            st.session_state["bedrijven"].append({
                "naam": naam,
                "uurtarief": uurtarief,
                "loonheffing": loonheffing
            })
            st.success(f"Bedrijf '{naam}' toegevoegd.")

    if st.session_state["bedrijven"]:
        st.subheader("Bestaande bedrijven")
        st.table(pd.DataFrame(st.session_state["bedrijven"]))
    else:
        st.info("Nog geen bedrijven toegevoegd.")

# ------------------ Uren invoeren ------------------
elif pagina == "Uren invoeren":
    st.title("Uren invoeren")

    if not st.session_state["bedrijven"]:
        st.warning("Voeg eerst een bedrijf toe onder 'Bedrijven beheren'.")
    else:
        bedrijven_namen = [b["naam"] for b in st.session_state["bedrijven"]]
        invoermethode = st.radio(
            "Kies je invoermethode:",
            ("Handmatig invullen", "Plakken uit notities")
        )

        if invoermethode == "Handmatig invullen":
            with st.form("uren_formulier", clear_on_submit=True):
                bedrijf = st.selectbox("Bedrijf", bedrijven_namen)
                dag = st.selectbox("Dag", ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"])
                datum = st.date_input("Datum", date.today())
                starttijd = st.time_input("Starttijd", time(9, 0))
                eindtijd = st.time_input("Eindtijd", time(17, 0))
                pauze = st.number_input("Pauze (minuten)", min_value=0, max_value=180, value=30)
                toevoegen = st.form_submit_button("Toevoegen")

                # Automatische berekening gewerkte uren
                start_dt = datetime.combine(date.today(), starttijd)
                eind_dt = datetime.combine(date.today(), eindtijd)
                diff = (eind_dt - start_dt).total_seconds() / 3600  # verschil in uren
                uren = max(0, diff - pauze / 60)

                st.info(f"Gewerkte uren (excl. pauze): {uren:.2f}")

                if toevoegen:
                    st.session_state["uren_data"].append({
                        "Bedrijf": bedrijf,
                        "Dag": dag,
                        "Datum": datum.strftime("%Y-%m-%d"),
                        "Starttijd": starttijd.strftime("%H:%M"),
                        "Eindtijd": eindtijd.strftime("%H:%M"),
                        "Pauze (min)": pauze,
                        "Uren": uren
                    })

        elif invoermethode == "Plakken uit notities":
            bedrijf = st.selectbox("Bedrijf", bedrijven_namen, key="bedrijf_plak")
            st.markdown("""
            Plak hieronder je notities, bijvoorbeeld:

            ```
            Ma- 14 apr 12.30/20.30(30) 7.5uur
            Di- 15 apr 12.00/20.30(60) 7.5 uur
            ...
            Totaal: 15 uur, €180 netto
            ```
            """)
            input_text = st.text_area("Plak hier je uren:", height=200)
            fouten = []
            if st.button("Toevoegen uit tekst"):
                rows = input_text.strip().split('\n')
                default_year = datetime.now().year
                for i, row in enumerate(rows, 1):
                    parsed = parse_row(row, default_year, bedrijf)
                    if parsed:
                        st.session_state["uren_data"].append(parsed)
                    elif row.strip() and not row.lower().startswith("totaal"):
                        fouten.append(f"Regel {i} niet herkend: {row}")
                if fouten:
                    st.warning("Sommige regels konden niet worden verwerkt:\n" + "\n".join(fouten))

# ------------------ Overzicht ------------------
elif pagina == "Overzicht":
    st.title("Overzicht")

    data = st.session_state["uren_data"]
    bedrijven = st.session_state["bedrijven"]

    if data and bedrijven:
        df = pd.DataFrame(data)
        df['Datum_obj'] = pd.to_datetime(df['Datum'])
        df['Week'] = df['Datum_obj'].dt.isocalendar().week

        # Filter op bedrijf
        bedrijven_namen = [b["naam"] for b in bedrijven]
        bedrijf_filter = st.selectbox("Filter op bedrijf", ["Alle bedrijven"] + bedrijven_namen)
        if bedrijf_filter != "Alle bedrijven":
            df = df[df["Bedrijf"] == bedrijf_filter]

        # Gebruik centrale periode
        st.subheader("Periode")
        start_datum = st.session_state["periode_start"]
        eind_datum = st.session_state["periode_eind"]
        st.info(f"Periode: {start_datum} t/m {eind_datum}")

        mask = (df['Datum_obj'] >= pd.to_datetime(start_datum)) & (df['Datum_obj'] <= pd.to_datetime(eind_datum))
        df_periode = df.loc[mask].copy()
        st.dataframe(df_periode.drop(columns=['Datum_obj']), use_container_width=True)

        # Uurtarief ophalen per bedrijf
        def get_uurtarief(bedrijfsnaam):
            for b in bedrijven:
                if b["naam"] == bedrijfsnaam:
                    return b["uurtarief"]
            return 0.0

        df_periode["Uurtarief"] = df_periode["Bedrijf"].apply(get_uurtarief)
        df_periode["Bedrag"] = df_periode["Uren"] * df_periode["Uurtarief"]

        totaal_uren = df_periode['Uren'].sum()
        totaal_bedrag = df_periode['Bedrag'].sum()

        st.metric("Totaal gewerkte uren", f"{totaal_uren:.2f} uur")
        st.metric("Totaal bedrag", f"€{totaal_bedrag:.2f}")

        # Weekoverzicht
        st.subheader("Weekoverzicht")
        weekoverzicht = df_periode.groupby("Week")[["Uren", "Bedrag"]].sum().reset_index()
        st.dataframe(weekoverzicht)

        # Selecteer week en kopieer uren
        st.subheader("Kopieer je weekoverzicht")
        weeknummers = weekoverzicht['Week'].tolist()
        if weeknummers:
            gekozen_week = st.selectbox("Kies weeknummer", weeknummers)
            week_df = df_periode[df_periode['Week'] == gekozen_week]

            # Maak tekst voor kopiëren (zonder bedrijf, bedrag of totaal)
            kopieer_tekst = "\n".join(
                f"{row['Dag']}- {row['Datum']} {row['Starttijd']}/{row['Eindtijd']}({row['Pauze (min)']}) {row['Uren']:.2f} uur"
                for _, row in week_df.iterrows()
            )
            
            st.text_area("Kopieer deze tekst en stuur door:", kopieer_tekst, height=200)
            
        # Download knop
        excel_bytes = to_excel(df_periode.drop(columns=['Datum_obj']))
        st.download_button(
            label="Download als Excel",
            data=excel_bytes,
            file_name="urenregistratie.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Nog geen uren of bedrijven ingevoerd.")