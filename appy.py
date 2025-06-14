import streamlit as st
import pandas as pd
import re
from datetime import datetime, date, time, timedelta
from io import BytesIO
import os

UREN_CSV = "uren_data.csv"
BEDRIJVEN_CSV = "bedrijven.csv"
PERSOON_CSV = "persoon.csv"
EERSTE_PERIODE_CSV = "eerste_periode.csv"

def load_data():
    if os.path.exists(UREN_CSV):
        st.session_state["uren_data"] = pd.read_csv(UREN_CSV).to_dict("records")
    if os.path.exists(BEDRIJVEN_CSV):
        st.session_state["bedrijven"] = pd.read_csv(BEDRIJVEN_CSV).to_dict("records")

def save_uren():
    pd.DataFrame(st.session_state["uren_data"]).to_csv(UREN_CSV, index=False)

def save_bedrijven():
    pd.DataFrame(st.session_state["bedrijven"]).to_csv(BEDRIJVEN_CSV, index=False)

def save_persoon():
    pd.DataFrame([{
        "naam": st.session_state["persoon"].get("naam", ""),
        "geboortedatum": st.session_state["persoon"].get("geboortedatum", date(2000,1,1))
    }]).to_csv(PERSOON_CSV, index=False)

def load_persoon():
    if os.path.exists(PERSOON_CSV):
        df = pd.read_csv(PERSOON_CSV)
        if not df.empty:
            st.session_state["persoon"]["naam"] = df.iloc[0]["naam"]
            st.session_state["persoon"]["geboortedatum"] = pd.to_datetime(df.iloc[0]["geboortedatum"]).date()

def save_eerste_periode(dt):
    pd.DataFrame([{"eerste_periode_start": dt}]).to_csv(EERSTE_PERIODE_CSV, index=False)

def load_eerste_periode():
    if os.path.exists(EERSTE_PERIODE_CSV):
        df = pd.read_csv(EERSTE_PERIODE_CSV)
        if not df.empty:
            return pd.to_datetime(df.iloc[0]["eerste_periode_start"]).date()
    return None

# Laad data bij start
if "data_loaded" not in st.session_state:
    load_data()
    if "persoon" not in st.session_state:
        st.session_state["persoon"] = {
            "naam": "",
            "geboortedatum": date(2000,1,1)
        }
    load_persoon()
    st.session_state["eerste_periode_start"] = load_eerste_periode()
    st.session_state["data_loaded"] = True

st.set_page_config(page_title="Urenregistratie", layout="wide")

pagina = st.sidebar.radio(
    "Ga naar pagina:",
    ("Uren invoeren", "Overzicht", "Bedrijven beheren", "Persoonsgegevens")
)

# Welkom rechtsboven (behalve op Persoonsgegevens)
if pagina != "Persoonsgegevens":
    naam = st.session_state["persoon"].get("naam", "Gebruiker")
    st.markdown(
        f"<div style='text-align:right; font-size:1.2em; font-weight:bold;'>Welkom {naam}!</div>",
        unsafe_allow_html=True
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

# ------------------ Persoonsgegevens ------------------
if pagina == "Persoonsgegevens":
    st.title("Persoonsgegevens")
    with st.form("persoon_form"):
        naam = st.text_input("Naam", value=st.session_state["persoon"].get("naam", ""))
        geboortedatum = st.date_input("Geboortedatum", value=st.session_state["persoon"].get("geboortedatum", date(2000,1,1)))
        opslaan = st.form_submit_button("Opslaan")

        if opslaan:
            st.session_state["persoon"]["naam"] = naam
            st.session_state["persoon"]["geboortedatum"] = geboortedatum
            save_persoon()
            st.success("Persoonsgegevens opgeslagen.")

    vandaag = date.today()
    geboortedatum = st.session_state["persoon"].get("geboortedatum", date(2000,1,1))
    leeftijd = vandaag.year - geboortedatum.year - (
        (vandaag.month, vandaag.day) < (geboortedatum.month, geboortedatum.day)
    )
    st.info(f"Leeftijd: {leeftijd} jaar")

    # Eenvoudige schatting loonheffing (alleen leeftijd)
    if leeftijd < 21:
        schatting = 0.10
    else:
        schatting = 0.36
    st.session_state["persoon"]["loonheffingspercentage"] = schatting
    st.info(f"Geschat loonheffingspercentage: {schatting*100:.1f}%")

# ------------------ Bedrijven beheren ------------------
elif pagina == "Bedrijven beheren":
    st.title("Bedrijven beheren")
    st.markdown("Voeg bedrijven toe met uurtarief, loonheffing en loonheffingskorting.")

    with st.form("bedrijf_form", clear_on_submit=True):
        naam = st.text_input("Bedrijfsnaam")
        uurtarief = st.number_input("Uurtarief (€)", min_value=0.0, value=12.0, step=0.5)
        loonheffing = st.checkbox("Loonheffing aanwezig?", value=True)
        loonheffingskorting = st.checkbox("Loonheffingskorting toepassen?", value=True)
        toevoegen = st.form_submit_button("Toevoegen")

        if toevoegen and naam:
            st.session_state["bedrijven"].append({
                "naam": naam,
                "uurtarief": uurtarief,
                "loonheffing": loonheffing,
                "loonheffingskorting": loonheffingskorting
            })
            save_bedrijven()
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
                datum = st.date_input("Datum", date.today())
                dag = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"][datum.weekday()]
                st.info(f"Dag: {dag}")
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
                    save_uren()

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
                save_uren()

# ------------------ Overzicht ------------------
elif pagina == "Overzicht":
    st.title("Overzicht")

    data = st.session_state["uren_data"]
    bedrijven = st.session_state["bedrijven"]

    def heeft_loonheffing(bedrijfsnaam):
        for b in bedrijven:
            if b["naam"] == bedrijfsnaam:
                return b.get("loonheffing", False)
        return False

    def heeft_loonheffingskorting(bedrijfsnaam):
        for b in bedrijven:
            if b["naam"] == bedrijfsnaam:
                return b.get("loonheffingskorting", False)
        return False

    if data and bedrijven:
        df = pd.DataFrame(data)
        df['Datum_obj'] = pd.to_datetime(df['Datum'])
        df['Week'] = df['Datum_obj'].dt.isocalendar().week

        # Toevoegen: Uren aanpassen/verwijderen
        st.subheader("Uren aanpassen of verwijderen")
        for i, row in df.iterrows():
            cols = st.columns([2,2,2,2,2,2,2,1,1])
            for j, col in enumerate(["Bedrijf","Dag","Datum","Starttijd","Eindtijd","Pauze (min)","Uren"]):
                cols[j].write(str(row[col]))
            if cols[-2].button("✏️", key=f"edit_{i}"):
                st.session_state["edit_row"] = i
            if cols[-1].button("🗑️", key=f"del_{i}"):
                st.session_state["uren_data"].pop(i)
                save_uren()
                st.experimental_rerun()

        # Bewerken van een regel
        if "edit_row" in st.session_state:
            idx = st.session_state["edit_row"]
            edit_row = st.session_state["uren_data"][idx]
            st.info("Pas de gegevens aan en klik op 'Opslaan'")
            with st.form("edit_form"):
                bedrijf = st.text_input("Bedrijf", value=edit_row["Bedrijf"])
                dag = st.text_input("Dag", value=edit_row["Dag"])
                datum = st.date_input("Datum", value=pd.to_datetime(edit_row["Datum"]).date())
                starttijd = st.text_input("Starttijd", value=edit_row["Starttijd"])
                eindtijd = st.text_input("Eindtijd", value=edit_row["Eindtijd"])
                pauze = st.number_input("Pauze (min)", value=int(edit_row["Pauze (min)"]))
                uren = st.number_input("Uren", value=float(edit_row["Uren"]))
                opslaan = st.form_submit_button("Opslaan")
                annuleren = st.form_submit_button("Annuleren")
            if opslaan:
                st.session_state["uren_data"][idx] = {
                    "Bedrijf": bedrijf,
                    "Dag": dag,
                    "Datum": datum.strftime("%Y-%m-%d"),
                    "Starttijd": starttijd,
                    "Eindtijd": eindtijd,
                    "Pauze (min)": pauze,
                    "Uren": uren
                }
                save_uren()
                del st.session_state["edit_row"]
                st.experimental_rerun()
            if annuleren:
                del st.session_state["edit_row"]
                st.experimental_rerun()

        # Periodebeheer: 4-weken periodes met opslag en datums in selectbox
        st.subheader("Periode selectie (4 weken per periode)")
        if st.session_state["eerste_periode_start"] is None:
            eerste_start = st.date_input("Kies de begindatum van de allereerste periode")
            if st.button("Zet eerste periode"):
                st.session_state["eerste_periode_start"] = eerste_start
                save_eerste_periode(eerste_start)
                st.success("Eerste periode ingesteld!")
            st.stop()
        else:
            eerste_start = st.session_state["eerste_periode_start"]
            st.info(f"Eerste periode start op: {eerste_start.strftime('%d-%m-%Y')}")
            # Bepaal het aantal periodes tot nu toe
            dagen_geleden = (date.today() - eerste_start).days
            huidige_periode = 1 + dagen_geleden // 28
            totaal_periodes = max(1, huidige_periode)
            # Maak periode-opties met datums
            periode_opties = []
            for p in range(1, totaal_periodes+1):
                p_start = eerste_start + timedelta(days=(p-1)*28)
                p_eind = p_start + timedelta(days=27)
                periode_opties.append(f"Periode {p} ({p_start.strftime('%d-%m-%Y')} t/m {p_eind.strftime('%d-%m-%Y')})")
            periode_idx = st.selectbox("Kies periode", list(range(totaal_periodes)), format_func=lambda i: periode_opties[i])
            periode_start = eerste_start + timedelta(days=(periode_idx)*28)
            periode_eind = periode_start + timedelta(days=27)
            st.info(f"Periode {periode_idx+1}: {periode_start.strftime('%d-%m-%Y')} t/m {periode_eind.strftime('%d-%m-%Y')}")
            # Filter df_periode op deze periode:
            mask = (df['Datum_obj'] >= pd.to_datetime(periode_start)) & (df['Datum_obj'] <= pd.to_datetime(periode_eind))
            df_periode = df.loc[mask].copy()

        # Uurtarief ophalen per bedrijf
        def get_uurtarief(bedrijfsnaam):
            for b in bedrijven:
                if b["naam"] == bedrijfsnaam:
                    return b["uurtarief"]
            return 0.0

        df_periode["Uurtarief"] = df_periode["Bedrijf"].apply(get_uurtarief)
        df_periode["Bedrag"] = df_periode["Uren"] * df_periode["Uurtarief"]

        # Loonheffingspercentage uit persoonsgegevens
        schatting_basis = st.session_state["persoon"].get("loonheffingspercentage", 0.36)
        df_periode["LoonheffingAanwezig"] = df_periode["Bedrijf"].apply(heeft_loonheffing)
        df_periode["Loonheffingskorting"] = df_periode["Bedrijf"].apply(heeft_loonheffingskorting)

        def schatting_per_bedrijf(row):
            if row["LoonheffingAanwezig"]:
                if row["Loonheffingskorting"]:
                    return row["Bedrag"] * (1 - schatting_basis)
                else:
                    return row["Bedrag"] * (1 - 0.40)
            else:
                return row["Bedrag"]

        df_periode["NettoBedrag"] = df_periode.apply(schatting_per_bedrijf, axis=1)

        totaal_uren = df_periode['Uren'].sum()
        totaal_bedrag = df_periode['Bedrag'].sum()
        totaal_nettobedrag = df_periode['NettoBedrag'].sum()

        st.metric("Totaal gewerkte uren", f"{totaal_uren:.2f} uur")
        st.metric("Totaal bruto bedrag", f"€{totaal_bedrag:.2f}")
        st.metric("Totaal netto bedrag (geschat)", f"€{totaal_nettobedrag:.2f}")

        # Weekoverzicht
        st.subheader("Weekoverzicht")
        weekoverzicht = df_periode.groupby("Week")[["Uren", "Bedrag", "NettoBedrag"]].sum().reset_index()
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