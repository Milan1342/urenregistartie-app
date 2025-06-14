class Overview {
    private workEntries: WorkEntry[];

    constructor(workEntries: WorkEntry[]) {
        this.workEntries = workEntries;
    }

    displayOverview(): void {
        console.log("Overview of Work Hours and Earnings:");
        this.workEntries.forEach(entry => {
            console.log(`Date: ${entry.date}, Start: ${entry.startTime}, End: ${entry.endTime}, Hours: ${entry.hours}, Earnings: ${this.calculateTotalEarnings(entry)}`);
        });
        console.log(`Total Earnings: ${this.calculateTotalEarnings()}`);
    }

    calculateTotalEarnings(entry?: WorkEntry): number {
        const hourlyRate = 20; // Example hourly rate
        if (entry) {
            return entry.hours * hourlyRate * (1 - 0.2); // Assuming 20% tax
        }
        return this.workEntries.reduce((total, entry) => total + (entry.hours * hourlyRate * (1 - 0.2)), 0);
    }
}