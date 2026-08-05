---
card: system-design
gi: 83
slug: when-to-choose-sql-vs-nosql
title: When to choose SQL vs NoSQL
---

## 1. What it is

Choosing between a SQL (relational) and a NoSQL database is a decision made per data type, based on a small set of concrete questions: how structured and interrelated is the data, how does it need to scale, how strong must consistency be, and are the access patterns known in advance. There is no single universally "better" choice — each family of databases makes different trade-offs, and the right answer depends on the specific data and workload.

## 2. Why & when

Picking the wrong tool for a given piece of data shows up later as pain: forcing highly relational, transactional data (payments, inventory) into a NoSQL store without proper joins or ACID guarantees risks real correctness bugs; forcing a massive, simple, ever-growing key-value workload (session data, IoT telemetry) into a relational database can mean fighting its scaling limits unnecessarily. Make this decision explicitly and per data type — a real system, as the next tutorial covers, often uses more than one kind of database at once.

## 3. Core concept

**Question 1 — how relational is the data?** Data with many meaningful relationships that are queried flexibly and change over time (an e-commerce catalog with categories, orders, customers, and reviews all cross-referenced) fits a relational model's joins well. Data that is naturally self-contained per entity, rarely needs to be queried by fields you did not anticipate, fits NoSQL's document or key-value model better.

**Question 2 — how strong must consistency be?** Data where an inconsistency has a real cost (a bank balance, an inventory count that could be oversold) favors ACID guarantees. Data where a brief, eventual-consistency window is truly harmless (a follower count, a "recently viewed" list) can safely use a BASE-style NoSQL store, trading some consistency for availability and scale.

**Question 3 — what is the write and scale profile?** Very high, horizontally distributed write volume (metrics, logs, event streams, IoT data) favors a wide-column or time-series store built for that shape. Moderate, less extreme volume with complex query needs favors a relational database, which can also scale a long way vertically and with read replicas before horizontal partitioning becomes necessary.

**Question 4 — are the access patterns known and stable?** If you can enumerate the queries in advance and they rarely change, access-pattern-first NoSQL modeling pays off. If queries are unpredictable, exploratory, or change frequently as the business evolves, a relational database's flexible, general-purpose query language is a better match.

## 4. Diagram

```
Decision checklist, applied per data type (not once for the whole system):

  Q1: many cross-referenced relationships, flexible ad-hoc queries?  --YES--> lean SQL
                                                                       --NO---> lean NoSQL

  Q2: does inconsistency have a REAL cost (money, inventory)?        --YES--> lean SQL (ACID)
                                                                       --NO---> BASE is acceptable

  Q3: extremely high, horizontally distributed write volume?         --YES--> lean NoSQL
                                                                       --NO---> SQL can likely handle it

  Q4: are the exact access patterns known and stable in advance?     --YES--> NoSQL modeling pays off
                                                                       --NO---> SQL's flexibility wins
```
*Caption: each question is answered per data type, not once for an entire system — different parts of the same application often land on different sides.*

## 5. Runnable example

**Level 1 — Basic.** A small scoring function that answers each decision question for a described dataset.

**Level 2 — Applying it to concrete examples.** Score several real data types (payments, session cache, product catalog, IoT telemetry) using the same function.

**Level 3 — A borderline case.** Show a dataset where the answer is close, illustrating that this is a judgment call, not a formula with one correct output.

```java
// SqlVsNoSql.java
import java.util.*;

public class SqlVsNoSql {

    record DataProfile(String name, boolean manyRelationships, boolean consistencyCritical,
                        boolean extremeWriteVolume, boolean accessPatternsKnownInAdvance) {}

    // Level 1: a simple scoring function mirroring the four-question checklist.
    static String recommend(DataProfile p) {
        int sqlPoints = 0, noSqlPoints = 0;

        if (p.manyRelationships()) sqlPoints++; else noSqlPoints++;
        if (p.consistencyCritical()) sqlPoints++; else noSqlPoints++;
        if (p.extremeWriteVolume()) noSqlPoints++; else sqlPoints++;
        if (p.accessPatternsKnownInAdvance()) noSqlPoints++; else sqlPoints++;

        String verdict = sqlPoints > noSqlPoints ? "SQL" : (noSqlPoints > sqlPoints ? "NoSQL" : "BORDERLINE - either could work");
        return p.name() + ": SQL=" + sqlPoints + " NoSQL=" + noSqlPoints + " -> " + verdict;
    }

    public static void main(String[] args) {
        // Level 2: concrete, realistic examples.
        List<DataProfile> profiles = List.of(
            new DataProfile("Payments ledger", true, true, false, false),
            new DataProfile("Session cache", false, false, true, true),
            new DataProfile("Product catalog (flexible browsing/search)", true, false, false, false),
            new DataProfile("IoT sensor telemetry", false, false, true, true)
        );
        for (DataProfile p : profiles) System.out.println(recommend(p));

        // Level 3: a genuinely borderline case - two questions favor each side.
        DataProfile borderline = new DataProfile(
            "User activity feed (some relationships, high write volume)",
            true,  // has relationships (user -> posts -> comments)
            false, // brief inconsistency is fine
            true,  // very high write volume
            false  // queries evolve as product features change
        );
        System.out.println(recommend(borderline));
        System.out.println("  -> a real system often resolves this by SPLITTING the data:");
        System.out.println("     relational store for posts/comments structure, NoSQL for the high-volume activity stream itself");
    }
}
```

**How to run:** save as `SqlVsNoSql.java`, then run `java SqlVsNoSql.java`.

## 6. Walkthrough

1. `recommend` awards one point to SQL or NoSQL for each of the four questions, based directly on the criteria in Part 3 — `manyRelationships` and `consistencyCritical` favor SQL when true; `extremeWriteVolume` and `accessPatternsKnownInAdvance` favor NoSQL when true.
2. "Payments ledger" scores `SQL=3, NoSQL=1` — highly relational, consistency-critical, moderate write volume, unpredictable future queries — a clear SQL recommendation matching real-world practice.
3. "Session cache" and "IoT sensor telemetry" both score `NoSQL=3, SQL=1` — simple, non-relational, extreme write volume or extremely simple lookup pattern — matching the common real-world choice of a key-value or time-series store for both.
4. "Product catalog" scores `SQL=3, NoSQL=1` — many relationships (categories, variants) and unpredictable ad-hoc search/filter queries, both favoring SQL.
5. The borderline case scores evenly (`SQL=2, NoSQL=2`), and the printout explicitly acknowledges what a real team would do: split the data itself, using a relational store for the structured, relationship-heavy part and a NoSQL store for the high-volume stream — exactly the polyglot persistence pattern covered next.

## 7. Gotchas & takeaways

> Gotcha: treating this as a one-time, whole-system decision ("we are a SQL shop" or "we are a NoSQL shop") is itself a common mistake; the right granularity is per data type, and a single application very often uses both, each for the part of its data that fits.

- Answer the four questions per dataset, not once for an entire application — different pieces of the same system frequently land on opposite sides.
- A borderline or mixed answer is common and legitimate; it is often the signal to split the data across two purpose-built stores rather than forcing one store to handle both shapes.
- Related concepts: [Polyglot persistence in one system](0084-polyglot-persistence-in-one-system.md) (the direct next step once you have data types that land on different sides), [BASE vs ACID](0080-base-vs-acid.md) (the consistency question, in depth).
