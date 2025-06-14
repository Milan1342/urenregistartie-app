import streamlit as st
import pandas as pd
import re
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Urenregistratie", layout="wide")
st.title("Urenregistratie Periode")

st.markdown("""
Voer je uren in onder elkaar, bijvoorbeeld:

```
Ma- 14 apr 12.30/20.30(30) 7.5uur
Di- 29 apr 12.00/20.30(60) 7.5 uur
```
""")

input_text = st.text_area("Plak hier je uren:", height=300)

# Verbeterd regex patroon, optioneel jaartal, flexibeler met spaties
pattern = re.compile(
    r"(?P<dag>\w{2})-\s*(?P<datum>\d{1,2}\s\w{3}(?:\s\d{4})?)\s+"
    r"(?P<start>\d{1,2}[.:]\d{2})\s*/\s*(?P<eind>\d{1,2}[.:]\d{2})"
    r"\((?P<pauze>\d+)\)\s+(?P<uren>[\d.,]+)\s*uur",
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

if input_text:
    rows = input_text.strip().split('\n')
    default_year = datetime.now().year
    data = []
    fouten = []
    for i, row in enumerate(rows, 1):
        parsed = parse_row(row, default_year)
        if parsed:
            data.append(parsed)
        else:
            fouten.append(f"Regel {i} niet herkend: {row}")

    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        totaal_uren = df['Uren'].sum()
        st.metric("Totaal gewerkte uren", f"{totaal_uren:.2f} uur")
        # Download knop
        excel_bytes = to_excel(df)
        st.download_button(
            label="Download als Excel",
            data=excel_bytes,
            file_name="urenregistratie.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    if fouten:
        st.warning("Sommige regels konden niet worden verwerkt:\n" + "\n".join(fouten))