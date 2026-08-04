---
card: system-design
gi: 11
slug: sla-slo-sli-defined
title: SLA, SLO, SLI defined
---

## 1. What it is

An **SLI (Service Level Indicator)** is a measured number describing how your system is actually behaving, such as "99.95% of requests last hour returned successfully". An **SLO (Service Level Objective)** is the internal target you set for that indicator, such as "we aim for 99.9% success rate over 30 days". An **SLA (Service Level Agreement)** is an external, often contractual promise to a customer, usually a looser version of the SLO, with a stated consequence if it is broken, such as "99.5% uptime, or you get a service credit".

Think of it as a runner's own training log (SLI: the actual times they ran), their personal goal (SLO: "average under 25 minutes for a 5K"), and a promise to a coach or sponsor (SLA: "I will finish every race under 30 minutes, or forfeit the sponsorship").

## 2. Why & when

These three terms let you talk precisely about reliability, instead of vaguely saying a system should be "reliable" or "fast". You define them once non-functional requirements are gathered, and they become the numbers every later reliability decision (replication, redundancy, monitoring) is measured against. Interviewers use SLA/SLO/SLI language to check that you can turn a vague reliability goal into a measurable, monitorable target.

## 3. Core concept

**The relationship between the three, and why they nest:**

- **SLI** is the raw measurement: a percentage, a latency number, an error rate, gathered continuously from real traffic.
- **SLO** is a target *for* an SLI, set by your own team, usually tighter than the SLA, because you want a safety margin before you actually break your promise to customers. Example: SLO = 99.95% success rate.
- **SLA** is a promise *to someone external*, usually a looser number than the SLO, with a defined penalty for missing it. Example: SLA = 99.9% success rate, or the customer receives a service credit.

**Why the SLO is stricter than the SLA:** this gap is your safety margin, sometimes called an **error budget**. If your SLO is 99.95% and your SLA is 99.9%, you have room to notice and fix a problem internally before you ever breach the external, contractual promise. Setting the SLO equal to the SLA leaves no room to react — the first sign of trouble is already a broken contract.

**Common SLI metrics used in system design:** availability (% of successful requests), latency (e.g. p99 response time), error rate, and durability (probability data is never lost).

## 4. Diagram

```
  SLI (measured reality)      "99.94% of requests succeeded this month"
        |
        | compared against
        v
  SLO (internal target)       "we aim for 99.95% success"   <-- tighter
        |
        | looser version becomes
        v
  SLA (external promise)      "we promise 99.9%, or you get credit"  <-- looser

  gap between SLO and SLA = your error budget / safety margin
```
*Caption: SLI is what you measure; SLO is your internal target; SLA is the looser external promise, with the gap between them as your safety margin.*

## 5. Runnable example

### Artifact: a Java program that checks a measured SLI against SLO and SLA thresholds

```java
public class SlaSloSliChecker {

    static final double SLO_TARGET = 99.95; // internal target, %
    static final double SLA_PROMISE = 99.9; // external promise, %

    static String evaluate(double measuredSli) {
        if (measuredSli >= SLO_TARGET) {
            return "Healthy: meeting internal SLO.";
        } else if (measuredSli >= SLA_PROMISE) {
            return "Warning: missed SLO, but SLA is still safe. Investigate now.";
        } else {
            return "BREACH: SLA violated. Customer-facing consequence triggered.";
        }
    }

    public static void main(String[] args) {
        double[] measuredOverTime = { 99.97, 99.92, 99.85 };

        for (double sli : measuredOverTime) {
            System.out.printf("Measured SLI: %.2f%% -> %s%n", sli, evaluate(sli));
        }
    }
}
```

**How to run:** save as `SlaSloSliChecker.java`, run `java SlaSloSliChecker.java` (JDK 17+).

## 6. Walkthrough

1. `SLO_TARGET` and `SLA_PROMISE` encode the two thresholds, with the SLO set tighter (99.95%) than the SLA (99.9%), exactly as they would be in a real reliability policy.
2. `evaluate` compares one measured SLI value against both thresholds, returning a healthy, warning, or breach message.
3. `main` runs three example SLI readings that gradually decline, simulating a system degrading over time.
4. Output:
```
Measured SLI: 99.97% -> Healthy: meeting internal SLO.
Measured SLI: 99.92% -> Warning: missed SLO, but SLA is still safe. Investigate now.
Measured SLI: 99.85% -> BREACH: SLA violated. Customer-facing consequence triggered.
```
5. The middle result is the entire point of setting an SLO stricter than the SLA: it gives an early warning ("Warning") while there is still time to fix the problem, before it becomes a contractual breach.

## 7. Gotchas & takeaways

> **Gotcha:** setting the SLO equal to the SLA. This removes your error budget entirely — the moment your SLI dips, you have already broken your external promise, with no warning window to react.

- SLI = what you measure. SLO = your internal target. SLA = your external, often contractual, promise.
- Always set the SLO tighter than the SLA, so you have a safety margin — an error budget — before a real breach.
- In a design interview, translate a vague "the system should be reliable" requirement into a concrete SLO, such as "99.95% availability, measured monthly".
