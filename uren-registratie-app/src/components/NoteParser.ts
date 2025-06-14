class NoteParser {
    notes: string[];

    constructor(notes: string[]) {
        this.notes = notes;
    }

    parseNotes(): WorkEntry[] {
        const workEntries: WorkEntry[] = [];
        this.notes.forEach(note => {
            const regex = /(\d{4}-\d{2}-\d{2})\s+(\w+)\s+(\d{2}:\d{2})\s+to\s+(\d{2}:\d{2})/;
            const match = note.match(regex);
            if (match) {
                const date = match[1];
                const day = match[2];
                const startTime = match[3];
                const endTime = match[4];
                const hoursWorked = this.extractWorkHours(startTime, endTime);
                workEntries.push({ date, day, startTime, endTime, hoursWorked });
            }
        });
        return workEntries;
    }

    extractWorkHours(startTime: string, endTime: string): number {
        const start = new Date(`1970-01-01T${startTime}:00`);
        const end = new Date(`1970-01-01T${endTime}:00`);
        const hours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
        return hours >= 0 ? hours : 0;
    }
}