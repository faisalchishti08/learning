---
card: system-design
gi: 15
slug: the-design-interview-framework-steps-timeboxing
title: The design interview framework (steps & timeboxing)
---

## 1. What it is

The **design interview framework** is a fixed sequence of steps you follow in every system design interview, each with a rough time budget, so a 45-minute conversation reliably covers requirements, scale, architecture, depth, and tradeoffs, instead of running out of time on one part. It is the concrete, timed version of the five-step loop introduced earlier in this section, now with minutes attached to each stage.

Think of it as a runner's race pacing plan: knowing roughly how many minutes to spend on each mile keeps you from sprinting the first mile and having nothing left for the last one.

## 2. Why & when

Without timeboxing, it is very easy to spend 25 minutes perfecting requirements and estimation, and then rush the actual architecture and deep dive in the remaining 20 minutes — or the opposite, drawing boxes immediately and never justifying them. This framework is the last tutorial in the Fundamentals & Estimation section because it ties together every concept covered so far (requirements, non-functional requirements, scoping, assumptions, estimation) into one timed run-through you use at the start of every design problem from here on.

## 3. Core concept

**The framework, with a rough 45-minute budget:**

1. **Requirements gathering & scoping (3-5 min).** Clarify functional and non-functional requirements; explicitly state what is in scope and out of scope.
2. **Capacity estimation (3-5 min).** Compute average and peak QPS, storage over your time horizon, and bandwidth, using round numbers.
3. **High-level design (10-15 min).** Draw the main boxes — client, load balancer, service, cache, database, queue — and the request path between them. Keep this at a system-wide level; do not go deep on any one part yet.
4. **Deep dive on the hardest part (10-15 min).** Pick the one or two sub-problems that make this system genuinely hard (e.g. "how do we generate a unique short code with no collisions?" for a URL shortener) and design that part in real detail.
5. **Tradeoffs, bottlenecks & wrap-up (5-8 min).** Name what you would do differently at 10x the scale, what single points of failure remain, and what you deliberately left out.

**Adjusting on the fly:** if the interviewer interrupts to redirect you (a very common and expected occurrence), follow their lead — it usually means they want more depth in a specific area. Keep a mental checkpoint of elapsed time so you notice if any single step is running long, and consciously move on.

## 4. Diagram

```
 0     5           10                 25                 40      45  (minutes)
 |-----|-----------|------------------|------------------|-------|
  Reqs & Scope   Estimation      High-level design      Deep dive   Tradeoffs
   (3-5m)          (3-5m)            (10-15m)            (10-15m)    (5-8m)

  keep a mental checkpoint: if any step runs long, consciously move on
```
*Caption: the five framework steps mapped onto a 45-minute interview, each with its own rough time budget.*

## 5. Runnable example

### Artifact: a Java program that tracks elapsed time against the framework's budget and warns when a step overruns

```java
import java.util.*;

public class InterviewTimeboxer {

    static class Step {
        String name;
        int budgetMinutes;
        Step(String name, int budgetMinutes) {
            this.name = name;
            this.budgetMinutes = budgetMinutes;
        }
    }

    public static void main(String[] args) {
        List<Step> framework = new ArrayList<>();
        framework.add(new Step("Requirements & scoping", 5));
        framework.add(new Step("Capacity estimation", 5));
        framework.add(new Step("High-level design", 15));
        framework.add(new Step("Deep dive", 15));
        framework.add(new Step("Tradeoffs & wrap-up", 5));

        // Simulated actual time spent on each step, from a mock interview run.
        int[] actualMinutesSpent = { 4, 7, 14, 12, 5 };

        int elapsed = 0;
        for (int i = 0; i < framework.size(); i++) {
            Step s = framework.get(i);
            int actual = actualMinutesSpent[i];
            elapsed += actual;
            String status = actual > s.budgetMinutes ? "OVER budget, move on now" : "on track";
            System.out.printf(
                "%-25s budget=%2dm  actual=%2dm  [%s]  elapsed total=%2dm%n",
                s.name, s.budgetMinutes, actual, status, elapsed
            );
        }
    }
}
```

**How to run:** save as `InterviewTimeboxer.java`, run `java InterviewTimeboxer.java` (JDK 17+).

## 6. Walkthrough

1. `framework` lists the five steps in order, each paired with its recommended minute budget from the table above.
2. `actualMinutesSpent` simulates a real run of the interview, with one entry per step, including a step that runs over its budget (capacity estimation, budgeted 5 minutes but taking 7).
3. The loop walks both lists together, adding each step's actual time to a running `elapsed` total, and flags any step whose actual time exceeds its budget.
4. Output:
```
Requirements & scoping    budget= 5m  actual= 4m  [on track]  elapsed total= 4m
Capacity estimation       budget= 5m  actual= 7m  [OVER budget, move on now]  elapsed total=11m
High-level design         budget=15m  actual=14m  [on track]  elapsed total=25m
Deep dive                 budget=15m  actual=12m  [on track]  elapsed total=37m
Tradeoffs & wrap-up       budget= 5m  actual= 5m  [on track]  elapsed total=42m
```
5. Notice that going over budget on estimation (by 2 minutes) still left enough time to land the interview at 42 minutes, because later steps recovered the time. This mirrors real interview pacing: a small overrun early is recoverable if you consciously tighten a later step, but the total must stay tracked, out loud in your head, throughout.

## 7. Gotchas & takeaways

> **Gotcha:** spending too long perfecting the high-level design's box diagram, leaving no time for the deep dive. The deep dive is usually where interviewers assess the most technical depth — a design with beautiful boxes but no deep dive reads as shallow.

- Follow the five-step order every time: requirements → estimation → high-level design → deep dive → tradeoffs.
- Keep a rough mental clock; if a step is clearly overrunning its budget, say so and move on ("I'll keep estimation brief and revisit if needed").
- The deep dive and tradeoffs steps carry the most signal about your technical depth — protect their time budget above the earlier steps.
