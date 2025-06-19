import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
from io import BytesIO
import os
import hashlib
import shutil

# --- Accountbeheer ---
USERS_DIR = "users"
os.makedirs(USERS_DIR, exist_ok=True)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def user_exists(email):
    return os.path.exists(os.path.join(USERS_DIR, email))

def save_user(email, password):
    try:
        user_dir = os.path.join(USERS_DIR, email)
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, "account.txt")
        with open(file_path, "w") as f:
            f.write(hash_password(password))
    except Exception as e:
        print(f"Fout bij aanmaken account.txt: {e}")

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

# --- Hulpfuncties voor uurtarief en loonheffing ---
def get_uurtarief(bedrijfsnaam):
    bedrijven = st.session_state.get("bedrijven", [])
    for b in bedrijven:
        if b["naam"] == bedrijfsnaam:
            return b.get("uurtarief", 0.0)
    return 0.0

def get_loonheffingspercentage(bedrijfsnaam):
    bedrijven = st.session_state.get("bedrijven", [])
    for b in bedrijven:
        if b["naam"] == bedrijfsnaam:
            return b.get("loonheffingspercentage", 0.10)
    return 0.10

def to_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# --- Navigatie met jaaropgave als extra pagina ---
sidebar_opties = ["Uren invoeren", "Overzicht", "Bedrijven beheren", "Persoonsgegevens"]

if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Overzicht"

# Navigatie: radio alleen als je op een hoofd-pagina zit
if st.session_state.get("pagina") not in sidebar_opties:
    pagina = st.session_state["pagina"]
else:
    gekozen = st.sidebar.radio("Ga naar pagina:", sidebar_opties, index=sidebar_opties.index(st.session_state.get("pagina", "Overzicht")))
    if gekozen != st.session_state.get("pagina"):
        st.session_state["pagina"] = gekozen
        st.rerun()
    pagina = st.session_state["pagina"]

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

st.sidebar.markdown("---")
if st.sidebar.button("Account verwijderen"):
    if st.sidebar.checkbox("Weet je het zeker? Dit kan niet ongedaan worden gemaakt!"):
        user_dir = os.path.join(USERS_DIR, st.session_state["user_email"])
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
        st.session_state["logged_in"] = False
        st.session_state["user_email"] = ""
        st.success("Je account is verwijderd.")
        st.rerun()

# ------------------ Bedrijven beheren ------------------
elif pagina == "Bedrijven beheren":
    st.title("Bedrijven beheren")
    st.markdown("Bekijk, bewerk of verwijder bestaande bedrijven en voeg nieuwe bedrijven toe.")

     # --- Bestaande bedrijven tonen, bewerken en verwijderen ---
    if st.session_state["bedrijven"]:
        st.subheader("Bestaande bedrijven")
        bedrijven_df = pd.DataFrame(st.session_state["bedrijven"])
        kolommen = ["naam", "uurtarief", "startdatum", "actief", "loonheffingspercentage", "reiskosten", "loonstrook_dagen", "loonstrook_bruto", "loonstrook_netto"]
        bestaande_kolommen = [k for k in kolommen if k in bedrijven_df.columns]

        # Tabel met bewerk/verwijder knoppen
        for idx, row in bedrijven_df.iterrows():
            cols = st.columns([2,2,2,2,2,2,2,2,2,1,1])
            for j, k in enumerate(bestaande_kolommen):
                cols[j].write(str(row[k]))
            if cols[-2].button("✏️", key=f"edit_bedrijf_{idx}"):
                st.session_state["edit_bedrijf"] = idx
            if cols[-1].button("🗑️", key=f"del_bedrijf_{idx}"):
                st.session_state["bedrijven"].pop(idx)
                save_bedrijven()
                st.rerun()

        # Bewerken van een bedrijf (met index-check en robuuste validatie)
        if "edit_bedrijf" in st.session_state:
            idx = st.session_state["edit_bedrijf"]
            if idx >= len(st.session_state["bedrijven"]):
                del st.session_state["edit_bedrijf"]
                st.rerun()
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

                # Toon percentage als alles is ingevuld
                if bruto > 0 and netto > 0 and dagen > 0 and netto <= bruto + reiskosten:
                    bruto_per_dag = (bruto + reiskosten) / dagen
                    netto_per_dag = netto / dagen
                    loonheffingspercentage = 1 - (netto_per_dag / bruto_per_dag)
                    st.info(f"Automatisch berekend percentage: {loonheffingspercentage*100:.2f}%")
                else:
                    loonheffingspercentage = None

                opslaan = st.form_submit_button("Opslaan")
                annuleren = st.form_submit_button("Annuleren")

            if opslaan:
                foutmelding = ""
                if not naam:
                    foutmelding = "Vul een bedrijfsnaam in."
                elif not (bruto > 0 and netto > 0 and dagen > 0 and netto <= bruto + reiskosten):
                    foutmelding = "Vul alle loonstrookvelden correct in (bruto, netto, reiskosten, dagen)."
                else:
                    bruto_per_dag = (bruto + reiskosten) / dagen
                    netto_per_dag = netto / dagen
                    loonheffingspercentage = 1 - (netto_per_dag / bruto_per_dag)
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
                    st.success("Bedrijf aangepast.")
                    st.rerun()
                if foutmelding:
                    st.warning(foutmelding)
            if annuleren:
                del st.session_state["edit_bedrijf"]
                st.rerun()
    else:
        st.info("Nog geen bedrijven toegevoegd.")

    # --- Toevoegen bedrijf ---
        st.title("Bedrijven Aanmaken")
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
        toevoegen = st.form_submit_button("Toevoegen")

        # Toon alvast het percentage als alles is ingevuld
        if bruto > 0 and netto > 0 and dagen > 0 and netto <= bruto + reiskosten:
            bruto_per_dag = (bruto + reiskosten) / dagen
            netto_per_dag = netto / dagen
            loonheffingspercentage = 1 - (netto_per_dag / bruto_per_dag)
            st.info(f"Automatisch berekend percentage: {loonheffingspercentage * 100:.2f} %")

        if toevoegen:
            foutmelding = ""
            if not naam:
                foutmelding = "Vul een bedrijfsnaam in."
            elif not (bruto > 0 and netto > 0 and dagen > 0 and netto <= bruto + reiskosten):
                foutmelding = "Vul alle loonstrookvelden correct in (bruto, netto, reiskosten, dagen)."
            else:
                bruto_per_dag = (bruto + reiskosten) / dagen
                netto_per_dag = netto / dagen
                loonheffingspercentage = 1 - (netto_per_dag / bruto_per_dag)
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
            if foutmelding:
                st.warning(foutmelding)

   
# ------------------ Uren invoeren ------------------
elif pagina == "Uren invoeren":
    st.title("Uren invoeren")

    if not st.session_state["bedrijven"]:
        st.warning("Voeg eerst een bedrijf toe onder 'Bedrijven beheren'.")
    else:
        bedrijven_namen = [b["naam"] for b in st.session_state["bedrijven"] if b.get("actief", True)]
        with st.form("uren_formulier", clear_on_submit=True):
            bedrijf = st.selectbox("Bedrijf", bedrijven_namen)
            datum = st.date_input("Datum", date.today())
            dag = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"][datum.weekday()]
            starttijd = st.time_input("Starttijd", time(9, 0))
            eindtijd = st.time_input("Eindtijd", time(17, 0))
            pauze = st.number_input("Pauze (minuten)", min_value=0, max_value=180, value=30)
            toevoegen = st.form_submit_button("Toevoegen")

            # Automatische berekening gewerkte uren
            start_dt = datetime.combine(date.today(), starttijd)
            eind_dt = datetime.combine(date.today(), eindtijd)
            diff = (eind_dt - start_dt).total_seconds() / 3600  # verschil in uren
            uren = max(0, diff - pauze / 60)

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
                st.success("Uren toegevoegd!")

# ------------------ Overzicht ------------------
elif pagina == "Overzicht":
    st.title("Overzicht")

    data = st.session_state.get("uren_data", [])
    bedrijven = st.session_state.get("bedrijven", [])

    if not bedrijven:
        st.warning("Er zijn nog geen bedrijven toegevoegd. Voeg eerst bedrijven toe onder 'Bedrijven beheren'.")
        st.stop()
    if not data:
        st.warning("Er zijn nog geen uren ingevoerd. Voeg eerst uren toe onder 'Uren invoeren'.")
        st.stop()

    df = pd.DataFrame(data)
    if df.empty:
        st.warning("Er zijn geen uren gevonden in de database.")
        st.stop()

    # Controleer of alle benodigde kolommen aanwezig zijn
    benodigde_kolommen = ["Bedrijf", "Dag", "Datum", "Starttijd", "Eindtijd", "Pauze (min)", "Uren"]
    for kol in benodigde_kolommen:
        if kol not in df.columns:
            st.error(f"Kolom '{kol}' ontbreekt in de data. Controleer je CSV-bestanden.")
            st.stop()

    # Datum parsing en extra kolommen
    df['Datum_obj'] = pd.to_datetime(df['Datum'], errors='coerce')
    df = df.dropna(subset=['Datum_obj'])
    if df.empty:
        st.warning("Geen geldige datums gevonden in je uren. Controleer je invoer.")
        st.stop()
    df['Week'] = df['Datum_obj'].dt.isocalendar().week
    df['Jaar'] = df['Datum_obj'].dt.year

    # --- Filter op bedrijf ---
    bedrijven_namen = ["Allemaal"] + [b["naam"] for b in bedrijven]
    gekozen_bedrijf = st.selectbox("Filter op bedrijf", bedrijven_namen)
    if gekozen_bedrijf != "Allemaal":
        df = df[df["Bedrijf"] == gekozen_bedrijf]

    # --- Jaarinkomsten ---
    df["Uurtarief"] = df["Bedrijf"].apply(get_uurtarief)
    df["Bedrag"] = df["Uren"] * df["Uurtarief"]
    df["Loonheffingspercentage"] = df["Bedrijf"].apply(get_loonheffingspercentage)
    df["NettoBedrag"] = df.apply(lambda row: row["Bedrag"] * (1 - row["Loonheffingspercentage"]), axis=1)

    jaar_bruto = df["Bedrag"].sum()
    jaar_netto = df["NettoBedrag"].sum()
    jaar_uren = df["Uren"].sum()

    # --- Jaaropgave knop ---
    if st.button("Bekijk jaaropgave"):
        st.session_state["pagina"] = "Jaaropgave"
        st.rerun()

    # --- Knop naar uren aanpassen pagina ---
    if st.button("Bekijk en bewerk alle uren"):
        st.session_state["pagina"] = "Uren aanpassen"
        st.rerun()

    # Periodebeheer: 4-weken periodes met opslag en datums in selectbox
    st.subheader("Periode selectie (4 weken per periode)")

    eerste_start = st.session_state.get("eerste_periode_start", None)
    if eerste_start is not None:
        st.info(f"Eerste periode start op: {eerste_start.strftime('%d-%m-%Y')}")
    else:
        st.info("Er is nog geen eerste periode ingesteld. Stel deze in om periodes te kunnen bekijken.")

    if st.session_state["eerste_periode_start"] is None:
        eerste_start = st.date_input("Kies de begindatum van de allereerste periode")
        if st.button("Zet eerste periode"):
            save_eerste_periode(eerste_start)
            st.success("Eerste periode ingesteld!")
            st.rerun()
        st.stop()
    else:
        eerste_start = st.session_state["eerste_periode_start"]
        if st.button("Wijzig eerste periode"):
            nieuwe_start = st.date_input("Nieuwe begindatum eerste periode", value=eerste_start, key="nieuwe_periode_start")
            if st.button("Opslaan nieuwe eerste periode"):
                st.session_state["eerste_periode_start"] = nieuwe_start
                save_eerste_periode(nieuwe_start)
                st.success("Eerste periode aangepast!")
            st.stop()

        # Bepaal het aantal periodes tot nu toe
        dagen_geleden = (date.today() - eerste_start).days
        huidige_periode = 1 + dagen_geleden // 28
        totaal_periodes = max(1, huidige_periode)

        # Maak periode-opties met datums
        periode_opties = []
        for p in range(1, totaal_periodes + 1):
            p_start = eerste_start + timedelta(days=(p - 1) * 28)
            p_eind = p_start + timedelta(days=27)
            periode_opties.append(f"Periode {p} ({p_start.strftime('%d-%m-%Y')} t/m {p_eind.strftime('%d-%m-%Y')})")
        periode_idx = st.selectbox("Kies periode", list(range(totaal_periodes)), format_func=lambda i: periode_opties[i])
        periode_start = eerste_start + timedelta(days=(periode_idx) * 28)
        periode_eind = periode_start + timedelta(days=27)
        # Filter df_periode op deze periode:
        mask = (df['Datum_obj'] >= pd.to_datetime(periode_start)) & (df['Datum_obj'] <= pd.to_datetime(periode_eind))
        df_periode = df.loc[mask].copy()


        # Weekoverzicht met datums achter weeknummer
        st.subheader("Weekoverzicht")

        weekoverzicht = df_periode.groupby("Week")[["Uren", "Bedrag", "NettoBedrag"]].sum().reset_index()

        # Plak hier de functie:
        def week_datum_range(weeknr):
            week_df = df_periode[df_periode['Week'] == weeknr]
            if week_df.empty:
                return ""
            start = week_df['Datum_obj'].min()
            end = week_df['Datum_obj'].max()
            if not isinstance(start, pd.Timestamp) or not isinstance(end, pd.Timestamp):
                return ""
            if pd.isna(start) or pd.isna(end):
                return ""
            return f"{start.strftime('%d-%m-%Y')} t/m {end.strftime('%d-%m-%Y')}"

        weekoverzicht["Datums"] = weekoverzicht["Week"].apply(week_datum_range)


        weekoverzicht["Datums"] = weekoverzicht["Week"].apply(week_datum_range)
        weekoverzicht["Weeknummer"] = weekoverzicht.apply(lambda r: f"Week {r['Week']} ({r['Datums']})", axis=1)

        weekoverzicht["NettoBedrag"] = weekoverzicht["NettoBedrag"].round(2)
        weekoverzicht["Bedrag"] = weekoverzicht["Bedrag"].round(2)

        st.dataframe(weekoverzicht[["Weeknummer", "Uren", "Bedrag", "NettoBedrag"]])

        # Selecteer week en kopieer uren
        st.subheader("Kopieer je weekoverzicht")
        weeknummers = weekoverzicht['Week'].tolist()
        weeklabels = weekoverzicht['Weeknummer'].tolist()
        if weeknummers:
            gekozen_idx = st.selectbox("Kies weeknummer", list(range(len(weeknummers))), format_func=lambda i: weeklabels[i])
            gekozen_week = weeknummers[gekozen_idx]
            week_df = df_periode[df_periode['Week'] == gekozen_week]

            if not week_df.empty:
                kopieer_tekst = "\n".join(
                    f"{row['Dag']}- {row['Datum']} {row['Starttijd']}/{row['Eindtijd']}({row['Pauze (min)']}) {row['Uren']:.2f} uur"
                    for _, row in week_df.iterrows()
                )
                key_kopieer = f"kopieer_tekst_{gekozen_week}"
                st.text_area("Kopieer deze tekst en stuur door:", kopieer_tekst, height=200, key=key_kopieer)
            else:
                st.info("Geen uren gevonden voor deze week.")
        else:
            st.info("Geen weekoverzicht beschikbaar.")

# ------------------ Uren aanpassen ------------------
if pagina == "Uren aanpassen":
    st.title("Uren aanpassen en verwijderen")
    data = st.session_state.get("uren_data", [])
    if not data:
        st.info("Er zijn nog geen uren ingevoerd.")
    else:
        df = pd.DataFrame(data)
        st.dataframe(df)
        st.write("Klik op het potloodje om een regel te bewerken of op de prullenbak om te verwijderen.")
        benodigde_kolommen = ["Bedrijf", "Dag", "Datum", "Starttijd", "Eindtijd", "Pauze (min)", "Uren"]
        for i, row in df.iterrows():
            cols = st.columns([2,2,2,2,2,2,2,1,1])
            for j, col in enumerate(benodigde_kolommen):
                cols[j].write(str(row[col]))
            if cols[-2].button("✏️", key=f"edit_{i}_aanpassen"):
                st.session_state["edit_row"] = i
            if cols[-1].button("🗑️", key=f"del_{i}_aanpassen"):
                st.session_state["uren_data"].pop(i)
                save_uren()
                st.rerun()

        # Bewerken van een regel
        if "edit_row" in st.session_state:
            idx = st.session_state["edit_row"]
            if idx >= len(st.session_state["uren_data"]):
                del st.session_state["edit_row"]
                st.rerun()
            edit_row = st.session_state["uren_data"][idx]
            st.info("Pas de gegevens aan en klik op 'Opslaan'")
            with st.form("edit_form_aanpassen"):
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

    if st.button("Terug naar overzicht"):
        st.session_state["pagina"] = "Overzicht"
        st.rerun()

# ------------------ Jaaropgave ------------------
elif pagina == "Jaaropgave":
    st.title("Jaaropgave")
    data = st.session_state.get("uren_data", [])
    bedrijven = st.session_state.get("bedrijven", [])
    if not bedrijven or not data:
        st.warning("Er zijn nog geen bedrijven of uren ingevoerd.")
        st.stop()
    df = pd.DataFrame(data)
    df['Datum_obj'] = pd.to_datetime(df['Datum'], errors='coerce')
    df = df.dropna(subset=['Datum_obj'])
    df['Jaar'] = df['Datum_obj'].dt.year

    bedrijven_namen = ["Allemaal"] + [b["naam"] for b in bedrijven]
    gekozen_bedrijf = st.selectbox("Bedrijf", bedrijven_namen)
    jaren = sorted(df['Jaar'].unique())
    gekozen_jaar = st.selectbox("Jaar", jaren, index=len(jaren)-1)

    df = df[df['Jaar'] == gekozen_jaar]
    if gekozen_bedrijf != "Allemaal":
        df = df[df["Bedrijf"] == gekozen_bedrijf]

    df["Uurtarief"] = df["Bedrijf"].apply(get_uurtarief)
    df["Bedrag"] = df["Uren"] * df["Uurtarief"]
    df["Loonheffingspercentage"] = df["Bedrijf"].apply(get_loonheffingspercentage)
    df["NettoBedrag"] = df.apply(lambda row: row["Bedrag"] * (1 - row["Loonheffingspercentage"]), axis=1)

    jaar_bruto = df["Bedrag"].sum()
    jaar_netto = df["NettoBedrag"].sum()
    jaar_uren = df["Uren"].sum()

    st.metric("Jaarinkomsten bruto", f"€{jaar_bruto:.2f}")
    st.metric("Jaarinkomsten netto (geschat)", f"€{jaar_netto:.2f}")
    st.metric("Jaaruren", f"{jaar_uren:.2f} uur")

    st.dataframe(df[["Datum", "Bedrijf", "Uren", "Uurtarief", "Bedrag", "NettoBedrag"]])

    if st.button("Terug naar overzicht"):
        st.session_state["pagina"] = "Overzicht"
        st.rerun()