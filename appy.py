import streamlit as st
import pandas as pd
import re
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Urenregistratie", layout="wide")
st.title("Urenregistratie Automatisering")

st.markdown("""
Plak hieronder je notities, bijvoorbeeld:

```
Ma- 14 apr 12.30/20.30(30) 7.5uur
Di- 15 apr 12.00/20.30(60) 7.5 uur
...
Totaal: 15 uur, €180 netto
```
""")

input_text = st.text_area("Plak hier je uren:", height=300)
uurtarief = st.number_input("Uurtarief netto (€)", min_value=0.0, value=12.0, step=0.5)

pattern = re.compile(
    r"(?P<dag>\w{2})-\s*(?P<datum>\d{1,2}\s\w{3}(?:\s\d{4})?)\s+"
    r"(?P<start>\d{1,2}[.:]\d{2})\s*/\s*(?P<eind>\d{1,2}[.:]\d{2})\s*"
    r"\(\s*(?P<pauze>\d+)\s*\)\s+(?P<uren>[\d.,]+)\s*uur",
    re.IGNORECASE
)

def parse_row(row: str, default_year: int) -> dict | None:
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
            "Dag": items['dag'].capitalize(),
            "Datum": datum_obj.strftime("%Y-%m-%d"),
            "Starttijd": start_time,
            "Eindtijd": end_time,
            "Pauze (min)": int(items['pauze']),
            "Uren": float(items['uren'].replace(',', '.'))
        }
    return None

def to_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def weeknummer(datum: str) -> int:
    return datetime.strptime(datum, "%Y-%m-%d").isocalendar()[1]

if input_text:
    rows = input_text.strip().split('\n')
    default_year = datetime.now().year
    data = []
    fouten = []
    for i, row in enumerate(rows, 1):
        parsed = parse_row(row, default_year)
        if parsed:
            parsed["Week"] = weeknummer(parsed["Datum"])
            data.append(parsed)
        elif row.strip() and not row.lower().startswith("totaal"):
            fouten.append(f"Regel {i} niet herkend: {row}")

    if data:
        df = pd.DataFrame(data)
        df['Datum_obj'] = pd.to_datetime(df['Datum'])

        # Periode filter
        st.subheader("Kies een periode")
        min_datum = df['Datum_obj'].min().date()
        max_datum = df['Datum_obj'].max().date()
        start_datum = st.date_input("Startdatum", min_datum, min_value=min_datum, max_value=max_datum)
        eind_datum = st.date_input("Einddatum", max_datum, min_value=min_datum, max_value=max_datum)

        mask = (df['Datum_obj'] >= pd.to_datetime(start_datum)) & (df['Datum_obj'] <= pd.to_datetime(eind_datum))
        df_periode = df.loc[mask].copy()
        st.dataframe(df_periode.drop(columns=['Datum_obj']), use_container_width=True)

        totaal_uren = df_periode['Uren'].sum()
        geschat_bedrag = totaal_uren * uurtarief

        st.metric("Totaal gewerkte uren", f"{totaal_uren:.2f} uur")
        st.metric("Geschat netto bedrag", f"€{geschat_bedrag:.2f}")

        # Weekoverzicht
        st.subheader("Weekoverzicht")
        weekoverzicht = df_periode.groupby("Week")["Uren"].sum().reset_index()
        st.dataframe(weekoverzicht)

        # Selecteer week en kopieer uren
        st.subheader("Kopieer je weekoverzicht")
        weeknummers = weekoverzicht['Week'].tolist()
        if weeknummers:
            gekozen_week = st.selectbox("Kies weeknummer", weeknummers)
            week_df = df_periode[df_periode['Week'] == gekozen_week]

            # Maak tekst voor kopiëren
            kopieer_tekst = "\n".join(
                f"{row['Dag']} {row['Datum']} {row['Starttijd']}-{row['Eindtijd']} ({row['Uren']} uur)"
                for _, row in week_df.iterrows()
            )
            kopieer_tekst += f"\nTotaal: {week_df['Uren'].sum():.2f} uur"

            st.text_area("Kopieer deze tekst en stuur door:", kopieer_tekst, height=200)

        # Download knop
        excel_bytes = to_excel(df_periode.drop(columns=['Datum_obj']))
        st.download_button(
            label="Download als Excel",
            data=excel_bytes,
            file_name="urenregistratie.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    if fouten:
        st.warning("Sommige regels konden niet worden verwerkt:\n" + "\n".join(fouten))