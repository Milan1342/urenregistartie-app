export interface WorkEntry {
    date: string;
    day: string;
    startTime: string;
    endTime: string;
    totalHours: number;
    totalMinutes: number;
}

export interface EarningsSummary {
    totalHours: number;
    totalEarnings: number;
    earningsAfterTax: number;
}