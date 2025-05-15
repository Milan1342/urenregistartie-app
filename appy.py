import streamlit as st
import pandas as pd
import re
from datetime import datetime

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

data = []

# Regex patroon voor invoer als: Ma- 14 apr 12.30/20.30(30) 7.5uur
pattern = r"(?P<dag>\w{2})-\s*(?P<datum>\d{1,2}\s\w{3})\s+(?P<start>\d{1,2}[.:]\d{2})/(?P<eind>\d{1,2}[.:]\d{2})\((?P<pauze>\d+)\)\s+(?P<uren>[\d.,]+)\s*uur"

def parse_row(row):
    match = re.match(pattern, row.strip(), re.IGNORECASE)
    if match:
        items = match.groupdict()
        # Converteer tijden
        start_time = items['start'].replace('.', ':')
        end_time = items['eind'].replace('.', ':')
        datum_str = f"{items['datum']} 2025"
        try:
            datum_obj = datetime.strptime(datum_str, "%d %b %Y")
        except ValueError:
            return None

        return {
            "Dag": items['dag'],
            "Datum": datum_obj.strftime("%Y-%m-%d"),
            "Starttijd": start_time,
            "Eindtijd": end_time,
            "Pauze (min)": int(items['pauze']),
            "Uren": float(items['uren'].replace(',', '.'))
        }
    return None

if input_text:
    rows = input_text.strip().split('\n')
    for row in rows:
        parsed = parse_row(row)
        if parsed:
            data.append(parsed)

    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        totaal_uren = df['Uren'].sum()
        st.metric("Totaal gewerkte uren", f"{totaal_uren:.2f} uur")
    else:
        st.warning("Geen geldige regels gevonden. Zorg dat het formaat klopt zoals aangegeven.")
