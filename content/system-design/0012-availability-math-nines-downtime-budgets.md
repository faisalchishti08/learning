---
card: system-design
gi: 12
slug: availability-math-nines-downtime-budgets
title: Availability math (nines & downtime budgets)
---

## 1. What it is

**Availability** is the fraction of time a system is up and successfully serving requests, usually written as a percentage made of repeated "9" digits, like "99.9%" (informally called "three nines"). Each extra nine represents a huge cut in allowed downtime. **Availability math** is converting that percentage into an actual downtime budget, in minutes or hours per year, so the number becomes concrete instead of abstract.

Think of a grade of 99% on a year-long, 365-day open-book exam: it sounds excellent, but it still means you were "wrong" (down) for about 3.65 days across the year — a number worth actually knowing before you promise it to someone.

## 2. Why & when

Saying "99.9% available" without knowing it means "about 8.76 hours of downtime a year" makes it easy to promise a number you cannot actually engineer for, or to panic over a number that is actually generous. You do this math right after setting an availability SLO, so you know exactly what engineering effort (redundancy, failover, monitoring) that target demands.

## 3. Core concept

**The formula:** `downtime allowed = (1 - availability) × total time in period`. Applied to a year (525,600 minutes):

| Availability | Nickname | Downtime per year | Downtime per month |
|---|---|---|---|
| 99% | "two nines" | ~3.65 days | ~7.3 hours |
| 99.9% | "three nines" | ~8.76 hours | ~43.8 minutes |
| 99.99% | "four nines" | ~52.6 minutes | ~4.4 minutes |
| 99.999% | "five nines" | ~5.26 minutes | ~26 seconds |

**Why each nine is a big jump, not a small one:** going from 99% to 99.9% is not "0.9% better" in a linear sense — it is a **10x reduction** in allowed downtime, from about 3.65 days a year down to under 9 hours. Each additional nine cuts the downtime budget by another factor of 10. This is why "five nines" is extremely hard and expensive to achieve: it allows only about 5 minutes of downtime across an entire year.

**How this feeds into design:** a single server, on unremarkable hardware, might realistically give you something like 99% to 99.9% availability on its own. To reach 99.99% or higher, you generally need redundancy — multiple servers, automatic failover, and multiple availability zones or regions — because no single machine is reliable enough alone to hit that target.

## 4. Diagram

```
 99%      |################----| ~3.65 days down/year
 99.9%    |####################| ~8.76 hours down/year     (10x less than 99%)
 99.99%   |####################| ~52.6 minutes down/year   (10x less than 99.9%)
 99.999%  |####################| ~5.26 minutes down/year   (10x less than 99.99%)

 each additional "9" = 10x less allowed downtime
```
*Caption: each extra nine of availability is a tenfold cut in the downtime budget, not a small incremental gain.*

## 5. Runnable example

### Artifact: a Java calculator converting availability percentages into downtime budgets

```java
public class AvailabilityCalculator {

    static final double MINUTES_PER_YEAR = 365 * 24 * 60; // 525,600

    static double downtimeMinutesPerYear(double availabilityPercent) {
        double availabilityFraction = availabilityPercent / 100.0;
        return (1 - availabilityFraction) * MINUTES_PER_YEAR;
    }

    static String humanReadable(double minutes) {
        if (minutes >= 60 * 24) {
            return String.format("%.2f days", minutes / (60 * 24));
        } else if (minutes >= 60) {
            return String.format("%.2f hours", minutes / 60);
        } else {
            return String.format("%.2f minutes", minutes);
        }
    }

    public static void main(String[] args) {
        double[] targets = { 99.0, 99.9, 99.99, 99.999 };

        for (double target : targets) {
            double downtime = downtimeMinutesPerYear(target);
            System.out.printf("%.3f%% availability -> %s downtime/year%n", target, humanReadable(downtime));
        }
    }
}
```

**How to run:** save as `AvailabilityCalculator.java`, run `java AvailabilityCalculator.java` (JDK 17+).

## 6. Walkthrough

1. `MINUTES_PER_YEAR` fixes the total number of minutes in a year (365 × 24 × 60 = 525,600), the denominator for every calculation.
2. `downtimeMinutesPerYear` converts a percentage like 99.9 into a fraction (0.999), subtracts it from 1 to get the *unavailable* fraction, and multiplies by the total minutes in a year.
3. `humanReadable` picks a sensible unit (days, hours, or minutes) so the result is easy to say out loud, instead of a raw, hard-to-parse minute count.
4. `main` loops over four common availability targets and prints each one's downtime budget.
5. Output:
```
99.000% availability -> 5.26 days downtime/year
99.900% availability -> 8.76 hours downtime/year
99.990% availability -> 52.56 minutes downtime/year
99.999% availability -> 5.26 minutes downtime/year
```
6. Spoken in an interview: "If we promise 99.9%, that's about 8.76 hours of downtime a year we're allowed — roughly 44 minutes a month. If the interviewer wants four nines instead, that budget shrinks tenfold, to under an hour a year, which means I need redundancy, not just a single well-run server."

## 7. Gotchas & takeaways

> **Gotcha:** treating "99% vs 99.9%" as a small difference because the percentages look close. The actual downtime gap is a full order of magnitude — days versus hours — and that gap is exactly what determines whether a single server is enough or true redundancy is required.

- Always convert an availability percentage into a concrete downtime budget (minutes/hours per year) before committing to it.
- Each additional nine is a 10x cut in allowed downtime, and typically requires a real architecture change (redundancy, failover) to achieve.
- Use this math to sanity-check availability SLOs: a target above 99.99% for a design with a single point of failure is not realistic without adding redundancy first.
