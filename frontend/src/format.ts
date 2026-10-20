// Indian number grouping (₹1,00,000 not ₹100,000) for monetary figures --
// survey respondents and report readers are in India, and Western grouping
// on rupee amounts reads as a translation error to that audience.
const inrFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export function formatINR(value: number): string {
  return inrFormatter.format(value);
}
