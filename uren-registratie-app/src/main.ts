import { NoteParser } from './components/NoteParser';
import { Overview } from './components/Overview';
import { Exporter } from './components/Exporter';

const noteParser = new NoteParser();
const overview = new Overview();
const exporter = new Exporter();

// Example user notes
const userNotes = [
    "2023-10-01, Monday, 09:00 - 17:00",
    "2023-10-02, Tuesday, 10:00 - 18:00",
    // Add more notes as needed
];

// Parse notes to extract work hours
const workEntries = noteParser.parseNotes(userNotes);

// Display the overview of work hours and earnings
overview.displayOverview(workEntries);

// Export the work data to CSV format
const csvData = exporter.exportToCSV(workEntries);
console.log(csvData); // This can be replaced with actual file saving logic