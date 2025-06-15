import streamlit as st
import pandas as pd
import re
from datetime import datetime, date, time, timedelta
from io import BytesIO
import os
import hashlib

# --- Accountbeheer ---
USERS_DIR = "users"
os.makedirs(USERS_DIR, exist_ok=True)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def user_exists(email):
    return os.path.exists(os.path.join(USERS_DIR, email))

def save_user(email, password):
    os.makedirs(os.path.join(USERS_DIR, email), exist_ok=True)
    with open(os.path.join(USERS_DIR, email, "account.txt"), "w") as f:
        f.write(hash_password(password))

def check_login(email, password):
    path = os.path.join(USERS_DIR, email, "account.txt")
    if not os.path.exists(path):
        return False
    with open(path) as f:
        return f.read().strip() == hash_password(password)

# --- Login/Registratie ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_email"] = ""

if not st.session_state["logged_in"]:
    st.title("Login of registreer")
    tab1, tab2 = st.tabs(["Inloggen", "Account aanmaken"])

    with tab1:
        email = st.text_input("E-mail", key="login_email")
        password = st.text_input("Wachtwoord", type="password", key="login_pw")
        if st.button("Inloggen"):
            if user_exists(email) and check_login(email, password):
                st.session_state["logged_in"] = True
                st.session_state["user_email"] = email
                st.rerun()
            else:
                st.error("Onjuiste inloggegevens.")

    with tab2:
        email = st.text_input("E-mail", key="reg_email")
        password = st.text_input("Wachtwoord", type="password", key="reg_pw")
        if st.button("Account aanmaken"):
            if user_exists(email):
                st.error("Account bestaat al.")
            else:
                save_user(email, password)
                st.success("Account aangemaakt! Je kunt nu inloggen.")
    st.stop()

# --- Data per gebruiker ---
def user_file(filename):
    return os.path.join(USERS_DIR, st.session_state["user_email"], filename)

UREN_CSV = user_file("uren_data.csv")
BEDRIJVEN_CSV = user_file("bedrijven.csv")
PERSOON_CSV = user_file("persoon.csv")
EERSTE_PERIODE_CSV = user_file("eerste_periode.csv")

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

if st.sidebar.button("Uitloggen"):
    st.session_state["logged_in"] = False
    st.session_state["user_email"] = ""
    st.rerun()

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

# ------------------ Bedrijven beheren ------------------
elif pagina == "Bedrijven beheren":
    st.title("Bedrijven beheren")
    st.markdown("Voeg bedrijven toe met uurtarief, begindatum, actief-status en loonstrookgegevens.")

    with st.form("bedrijf_form", clear_on_submit=True):
        naam = st.text_input("Bedrijfsnaam")
        uurtarief = st.number_input("Uurtarief (€)", min_value=0.0, value=12.0, step=0.5)
        startdatum = st.date_input("Begindatum", value=date.today())
        actief = st.checkbox("Actief bij dit bedrijf?", value=True)
        st.markdown("**Vul je loonstrook in voor het juiste percentage**")
        bruto = st.number_input("Bruto loon volgens loonstrook (€)", min_value=0.0, step=0.01, format="%.2f", key="bruto_nieuw")
        netto = st.number_input("Netto loon volgens loonstrook (€)", min_value=0.0, step=0.01, format="%.2f", key="netto_nieuw")
        reiskosten = st.number_input("Totale reiskostenvergoeding volgens loonstrook (€)", min_value=0.0, step=0.01, format="%.2f", key="reiskosten_nieuw")
        dagen = st.number_input("Aantal dagen op loonstrook", min_value=1, step=1, value=1, key="dagen_nieuw")
        loonheffingspercentage = None
        if bruto > 0 and netto > 0 and netto <= bruto and dagen > 0:
            bruto_per_dag = bruto / dagen
            netto_per_dag = (netto - reiskosten) / dagen
            loonheffingspercentage = 1 - (netto_per_dag / bruto_per_dag)
            st.info(f"Automatisch berekend percentage: {loonheffingspercentage*100:.2f}%")
        toevoegen = st.form_submit_button("Toevoegen")

        if toevoegen and naam and loonheffingspercentage is not None:
            st.session_state["bedrijven"].append({
                "naam": naam,
                "uurtarief": uurtarief,
                "startdatum": startdatum,
                "actief": actief,
                "loonheffingspercentage": loonheffingspercentage,
                "reiskosten": reiskosten,
                "loonstrook_dagen": dagen,
                "loonstrook_bruto": bruto,
                "loonstrook_netto": netto
            })
            save_bedrijven()
            st.success(f"Bedrijf '{naam}' toegevoegd.")

    if st.session_state["bedrijven"]:
        st.subheader("Bestaande bedrijven")
        bedrijven_df = pd.DataFrame(st.session_state["bedrijven"])
        st.table(bedrijven_df[["naam", "uurtarief", "startdatum", "actief", "loonheffingspercentage", "reiskosten", "loonstrook_dagen", "loonstrook_bruto", "loonstrook_netto"]])

        # Bewerken van een bedrijf
        if "edit_bedrijf" in st.session_state:
            idx = st.session_state["edit_bedrijf"]
            bedrijf = st.session_state["bedrijven"][idx]
            st.info("Pas het bedrijf aan en klik op 'Opslaan'")
            with st.form("edit_bedrijf_form"):
                naam = st.text_input("Bedrijfsnaam", value=bedrijf["naam"])
                uurtarief = st.number_input("Uurtarief (€)", min_value=0.0, value=float(bedrijf["uurtarief"]), step=0.5)
                startdatum = st.date_input("Begindatum", value=pd.to_datetime(bedrijf.get("startdatum", date.today())))
                actief = st.checkbox("Actief bij dit bedrijf?", value=bedrijf.get("actief", True))
                st.markdown("**Vul je loonstrook in voor het juiste percentage**")
                bruto = st.number_input("Bruto loon volgens loonstrook (€)", min_value=0.0, step=0.01, format="%.2f", key=f"bruto_{idx}")
                netto = st.number_input("Netto loon volgens loonstrook (€)", min_value=0.0, step=0.01, format="%.2f", key=f"netto_{idx}")
                reiskosten = st.number_input("Totale reiskostenvergoeding volgens loonstrook (€)", min_value=0.0, step=0.01, format="%.2f", key=f"reiskosten_{idx}")
                dagen = st.number_input("Aantal dagen op loonstrook", min_value=1, step=1, value=int(bedrijf.get("loonstrook_dagen", 1)), key=f"dagen_{idx}")
                loonheffingspercentage = None
                if bruto > 0 and netto > 0 and netto <= bruto and dagen > 0:
                    bruto_per_dag = bruto / dagen
                    netto_per_dag = (netto - reiskosten) / dagen
                    loonheffingspercentage = 1 - (netto_per_dag / bruto_per_dag)
                    st.info(f"Automatisch berekend percentage: {loonheffingspercentage*100:.2f}%")
                opslaan = st.form_submit_button("Opslaan")
                annuleren = st.form_submit_button("Annuleren")
            if opslaan and loonheffingspercentage is not None:
                st.session_state["bedrijven"][idx] = {
                    "naam": naam,
                    "uurtarief": uurtarief,
                    "startdatum": startdatum,
                    "actief": actief,
                    "loonheffingspercentage": loonheffingspercentage,
                    "reiskosten": reiskosten,
                    "loonstrook_dagen": dagen,
                    "loonstrook_bruto": bruto,
                    "loonstrook_netto": netto
                }
                save_bedrijven()
                del st.session_state["edit_bedrijf"]
                st.rerun()
            if annuleren:
                del st.session_state["edit_bedrijf"]
                st.rerun()
    else:
        st.info("Nog geen bedrijven toegevoegd.")

# ------------------ Uren invoeren ------------------
elif pagina == "Uren invoeren":
    st.title("Uren invoeren")

    if not st.session_state["bedrijven"]:
        st.warning("Voeg eerst een bedrijf toe onder 'Bedrijven beheren'.")
    else:
        bedrijven_namen = [b["naam"] for b in st.session_state["bedrijven"] if b.get("actief", True)]
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

    def get_loonheffingspercentage(bedrijfsnaam):
        for b in bedrijven:
            if b["naam"] == bedrijfsnaam:
                return b.get("loonheffingspercentage", 0.10)
        return 0.10

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
                st.rerun()

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
                st.rerun()
            if annuleren:
                del st.session_state["edit_row"]
                st.rerun()

        # Periodebeheer: 4-weken periodes met opslag en datums in selectbox
        st.subheader("Periode selectie (4 weken per periode)")
        if st.session_state["eerste_periode_start"] is None:
            eerste_start = st.date_input("Kies de begindatum van de allereerste periode")
            if st.button("Zet eerste periode"):
                st.session_state["eerste_periode_start"] = eerste_start
                save_eerste_periode(eerste_start)
                st.success("Eerste periode ingesteld!")
                st.rerun()
            st.stop()
        else:
            eerste_start = st.session_state["eerste_periode_start"]
            st.info(f"Eerste periode start op: {eerste_start.strftime('%d-%m-%Y')}")
            if st.button("Wijzig eerste periode"):
                nieuwe_start = st.date_input("Nieuwe begindatum eerste periode", value=eerste_start, key="nieuwe_periode_start")
                if st.button("Opslaan nieuwe eerste periode"):
                    st.session_state["eerste_periode_start"] = nieuwe_start
                    save_eerste_periode(nieuwe_start)
                    st.success("Eerste periode aangepast!")
                    st.rerun()
                st.stop()
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

        # Loonheffingspercentage per bedrijf
        df_periode["Loonheffingspercentage"] = df_periode["Bedrijf"].apply(get_loonheffingspercentage)

        def schatting_per_bedrijf(row):
            return row["Bedrag"] * (1 - row["Loonheffingspercentage"])

        df_periode["NettoBedrag"] = df_periode.apply(schatting_per_bedrijf, axis=1)

        totaal_uren = df_periode['Uren'].sum()
        totaal_bedrag = df_periode['Bedrag'].sum()
        totaal_nettobedrag = df_periode['NettoBedrag'].sum()

        st.metric("Totaal gewerkte uren", f"{totaal_uren:.2f} uur")
        st.metric("Totaal bruto bedrag", f"€{totaal_bedrag:.2f}")
        st.metric("Totaal netto bedrag (geschat)", f"€{totaal_nettobedrag:.2f}")

        # Weekoverzicht met datums achter weeknummer
        st.subheader("Weekoverzicht")
        def week_datum_range(weeknr):
            week_df = df_periode[df_periode['Week'] == weeknr]
            if week_df.empty:
                return ""
            start = week_df['Datum_obj'].min().strftime('%d-%m-%Y')
            eind = week_df['Datum_obj'].max().strftime('%d-%m-%Y')
            return f"{start} t/m {eind}"

        weekoverzicht = df_periode.groupby("Week")[["Uren", "Bedrag", "NettoBedrag"]].sum().reset_index()
        weekoverzicht["Datums"] = weekoverzicht["Week"].apply(week_datum_range)
        weekoverzicht["Weeknummer"] = weekoverzicht.apply(lambda r: f"Week {r['Week']} ({r['Datums']})", axis=1)
        st.dataframe(weekoverzicht[["Weeknummer", "Uren", "Bedrag", "NettoBedrag"]])

        # Selecteer week en kopieer uren
        st.subheader("Kopieer je weekoverzicht")
        weeknummers = weekoverzicht['Week'].tolist()
        weeklabels = weekoverzicht['Weeknummer'].tolist()
        if weeknummers:
            gekozen_idx = st.selectbox("Kies weeknummer", list(range(len(weeknummers))), format_func=lambda i: weeklabels[i])
            gekozen_week = weeknummers[gekozen_idx]
            week_df = df_periode[df_periode['Week'] == gekozen_week]

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