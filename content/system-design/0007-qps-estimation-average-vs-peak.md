---
card: system-design
gi: 7
slug: qps-estimation-average-vs-peak
title: QPS estimation (average vs peak)
---

## 1. What it is

**Queries Per Second (QPS)** is the number of requests a system receives every second. **Average QPS** is the total requests in a day divided evenly across all 86,400 seconds in that day. **Peak QPS** is the actual, higher rate during the busiest moments — most traffic is not spread evenly; it clusters around certain hours or events. Estimating both numbers tells you how many servers you need, sized for the busy moments, not the calm ones.

Think of a restaurant: average customers per hour across a whole day looks manageable, but if everyone arrives at once for lunch, the kitchen needs enough staff for that lunch rush specifically, not for the daily average.

## 2. Why & when

If you size a system only for average load, it falls over exactly when it matters most — during a traffic spike. QPS estimation is one of the first numbers you compute after gathering requirements, because it directly answers "how many servers do I need?" and "do I need a load balancer, a queue, or auto-scaling?"

You compute this any time you know (or can estimate) daily active users and roughly how many requests each user generates.

## 3. Core concept

**The estimation method, step by step:**

1. **Start from daily active users (DAU).** Either given by the interviewer or a reasonable assumption, e.g. "100 million DAU".
2. **Estimate requests per user per day.** For a read-heavy feed app, maybe each user makes 10 read requests a day. Multiply: `100,000,000 users × 10 requests = 1,000,000,000 requests/day`.
3. **Convert to average QPS** by dividing by the number of seconds in a day (86,400): `1,000,000,000 / 86,400 ≈ 11,574 average QPS`.
4. **Estimate peak QPS.** Traffic is rarely flat across 24 hours. A common, defensible rule of thumb is that peak traffic is **2 to 3 times the average**, because usage clusters around waking hours or specific events. `Peak QPS ≈ average QPS × peak factor (commonly 2-3x)`.

Using the 3x factor: `11,574 × 3 ≈ 34,722 peak QPS`. **You size your system for the peak number, not the average**, because the system must survive the busiest second, not just perform well on a typical one.

## 4. Diagram

```
 Daily requests = DAU x requests/user/day
        |
        v
 Average QPS = Daily requests / 86,400 seconds
        |
        v (x 2-3, traffic is not flat)
        |
 Peak QPS  <-- design your servers for THIS number
```
*Caption: average QPS comes from dividing by a day's seconds; peak QPS multiplies that by a clustering factor, and peak is what you design for.*

## 5. Runnable example

### Artifact: a Java QPS calculator from DAU and requests-per-user

```java
public class QpsEstimator {

    static final long SECONDS_PER_DAY = 86_400L;

    static long dailyRequests(long dau, long requestsPerUserPerDay) {
        return dau * requestsPerUserPerDay;
    }

    static double averageQps(long dailyRequests) {
        return dailyRequests / (double) SECONDS_PER_DAY;
    }

    static double peakQps(double averageQps, double peakFactor) {
        return averageQps * peakFactor;
    }

    public static void main(String[] args) {
        long dau = 100_000_000L;              // 100 million daily active users
        long requestsPerUserPerDay = 10L;      // e.g. 10 feed reads per user per day
        double peakFactor = 3.0;               // common assumption: peak is 3x average

        long daily = dailyRequests(dau, requestsPerUserPerDay);
        double avg = averageQps(daily);
        double peak = peakQps(avg, peakFactor);

        System.out.println("Daily requests: " + daily);
        System.out.printf("Average QPS: %.0f%n", avg);
        System.out.printf("Peak QPS (x%.0f): %.0f%n", peakFactor, peak);
    }
}
```

**How to run:** save as `QpsEstimator.java`, run `java QpsEstimator.java` (JDK 17+).

## 6. Walkthrough

1. `dailyRequests` multiplies daily active users by requests per user per day, giving the total requests the system serves in 24 hours.
2. `averageQps` divides that daily total by 86,400 (the number of seconds in a day), spreading the load evenly to get a baseline rate.
3. `peakQps` multiplies the average by a peak factor (here, 3.0) to model real, uneven traffic.
4. `main` runs the three steps in order with the 100-million-DAU scenario and prints each intermediate number.
5. Output:
```
Daily requests: 1000000000
Average QPS: 11574
Peak QPS (x3): 34722
```
6. In an interview, you say this out loud in the same order: "100 million DAU, 10 requests each, so 1 billion requests a day. Divide by 86,400 seconds, that's about 11,600 average QPS. Traffic isn't flat, so I'll assume peak is 3x average — about 35,000 QPS. I'll design for that peak number."

## 7. Gotchas & takeaways

> **Gotcha:** designing only for average QPS. A system that comfortably handles 11,600 QPS can still fail completely at a genuine peak of 35,000 QPS, because it was never tested or provisioned for that rate.

- Always compute both average and peak QPS; state the peak factor you assumed (2-3x is a safe, common default) and why.
- A single machine typically handles somewhere from a few hundred to a few thousand QPS for a simple service; compare your peak QPS against that to decide if you need multiple servers behind a load balancer.
- Round numbers aggressively — the goal is the right order of magnitude, not decimal precision.
