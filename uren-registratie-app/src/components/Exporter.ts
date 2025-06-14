export class Exporter {
    private workData: any[];

    constructor(workData: any[]) {
        this.workData = workData;
    }

    public exportToCSV(): string {
        const header = 'Datum,Dag,Begin Tijd,Eind Tijd,Totaal Uren,Totaal Minuten,Verdiend Bedrag\n';
        const rows = this.workData.map(entry => {
            return `${entry.date},${entry.day},${entry.startTime},${entry.endTime},${entry.totalHours},${entry.totalMinutes},${entry.earnedAmount}`;
        }).join('\n');

        return header + rows;
    }
}