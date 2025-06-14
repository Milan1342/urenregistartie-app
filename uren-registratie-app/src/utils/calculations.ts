export function calculateHours(startTime: string, endTime: string): number {
    const start = new Date(`1970-01-01T${startTime}:00`);
    const end = new Date(`1970-01-01T${endTime}:00`);
    const difference = end.getTime() - start.getTime();
    return difference > 0 ? difference / 3600000 : 0; // Return hours
}

export function calculateEarnings(hoursWorked: number, hourlyRate: number, taxRate: number): number {
    const grossEarnings = hoursWorked * hourlyRate;
    const netEarnings = grossEarnings * (1 - taxRate);
    return netEarnings;
}