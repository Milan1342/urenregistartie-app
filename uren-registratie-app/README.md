# Uren Registratie App

Deze applicatie is ontworpen om de urenregistratie te automatiseren en overzichtelijk te maken. Het stelt gebruikers in staat om hun werkuren eenvoudig te registreren, te berekenen en te exporteren.

## Functionaliteiten

- **Notities Parser**: Verwerkt gebruikersnotities om relevante werkinformatie te extraheren.
- **Uren Overzicht**: Biedt een samenvatting van gewerkte uren en berekent de totale verdiensten na belasting.
- **CSV Export**: Maakt het mogelijk om werkdata in CSV-formaat te exporteren voor eenvoudige verzending naar de werkgever.

## Bestandenstructuur

- `src/main.ts`: Het instappunt van de applicatie.
- `src/components/NoteParser.ts`: Bevat de `NoteParser` klasse voor het verwerken van notities.
- `src/components/Overview.ts`: Bevat de `Overview` klasse voor het weergeven van samenvattingen.
- `src/components/Exporter.ts`: Bevat de `Exporter` klasse voor het exporteren van gegevens.
- `src/utils/calculations.ts`: Bevat hulpfuncties voor het berekenen van uren en verdiensten.
- `src/types/index.ts`: Bevat interfaces voor werkregistraties en verdienoverzichten.

## Installatie

1. Clone de repository naar je lokale machine.
2. Navigeer naar de projectmap.
3. Voer `npm install` uit om de benodigde afhankelijkheden te installeren.

## Gebruik

1. Start de applicatie met `npm start`.
2. Voer je werknotities in volgens het vereiste formaat.
3. Bekijk het overzicht van je gewerkte uren en verdiensten.
4. Exporteer je gegevens naar CSV voor verzending naar je werkgever.

## Licentie

Dit project is gelicentieerd onder de MIT-licentie.