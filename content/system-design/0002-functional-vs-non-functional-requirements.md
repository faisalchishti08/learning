---
card: system-design
gi: 2
slug: functional-vs-non-functional-requirements
title: Functional vs non-functional requirements
---

## 1. What it is

A **functional requirement** describes what the system must *do* — the features and behaviors a user can observe, such as "users can post a tweet" or "users can shorten a URL". A **non-functional requirement (NFR)** describes how well the system must do it — qualities like speed, reliability, and scale, such as "the system must respond in under 200 milliseconds" or "the system must stay available 99.9% of the time".

A simple analogy: functional requirements are the rooms a house must have (kitchen, bedroom, bathroom). Non-functional requirements are the standards those rooms must meet (the roof must not leak, the house must survive an earthquake of a given magnitude).

## 2. Why & when

You split requirements into these two buckets because they are gathered differently and they drive different design decisions. Functional requirements come from asking "what can the user do?" and they shape your API endpoints and data model. Non-functional requirements come from asking "at what scale, and with what guarantees?" and they shape your architecture: whether you need a cache, multiple database replicas, or a message queue.

Skipping non-functional requirements is the most common beginner mistake in a design interview. A design that supports every feature but falls over at real traffic, or loses data on a crash, has failed the actual goal even if every feature button works.

## 3. Core concept

**Functional requirements** answer "what actions can a user take, and what happens?" Good functional requirements are specific and testable. For a URL shortener: "a user submits a long URL and receives a short URL", "visiting the short URL redirects to the original long URL". Vague requirements like "the system should work well" are not functional requirements; they belong in the non-functional bucket, restated with numbers.

**Non-functional requirements** answer "how well, how fast, how reliably, at what scale?" The five you will use most often in this card are:

| NFR | Question it answers | Example target |
|---|---|---|
| Scalability | How much load must it handle, and can it grow? | 10 million daily active users |
| Latency | How fast must a response come back? | p99 read latency under 100 ms |
| Availability | What fraction of time must it be reachable? | 99.99% uptime |
| Consistency | Must every reader see the same, latest data? | eventual consistency is acceptable |
| Durability | Can data ever be lost after being accepted? | zero data loss on writes |

**The key design link:** every non-functional requirement pushes you toward specific building blocks. High read latency at scale pushes you toward a cache. High availability pushes you toward replication across multiple servers. High durability pushes you toward writing to disk, and to more than one machine, before acknowledging a write.

## 4. Diagram

```
FUNCTIONAL                         NON-FUNCTIONAL
"what can it do?"                  "how well must it do it?"

 [ Post a tweet ]                   Scalability: 500M users
 [ Follow a user ]        ---->     Latency:      p99 < 200ms
 [ View a timeline ]                Availability: 99.99%
 [ Delete a tweet ]                 Consistency:  eventual OK
                                    Durability:   no data loss
        |                                  |
        v                                  v
  shapes the API                shapes the ARCHITECTURE
  and data model                (cache? replicas? queue?)
```
*Caption: functional requirements shape the API; non-functional requirements shape the architecture around it.*

## 5. Runnable example

### Artifact: a Java program that separates a mixed requirement list into the two buckets

```java
import java.util.*;

public class RequirementSorter {

    enum Kind { FUNCTIONAL, NON_FUNCTIONAL }

    static class Requirement {
        String text;
        Kind kind;
        Requirement(String text, Kind kind) {
            this.text = text;
            this.kind = kind;
        }
    }

    public static void main(String[] args) {
        List<Requirement> raw = new ArrayList<>();
        raw.add(new Requirement("Users can shorten a long URL into a short one", Kind.FUNCTIONAL));
        raw.add(new Requirement("Visiting a short URL redirects to the original URL", Kind.FUNCTIONAL));
        raw.add(new Requirement("The system must handle 100 million redirects per day", Kind.NON_FUNCTIONAL));
        raw.add(new Requirement("p99 redirect latency must stay under 100 ms", Kind.NON_FUNCTIONAL));
        raw.add(new Requirement("Users can see a click-count for their short URL", Kind.FUNCTIONAL));
        raw.add(new Requirement("The system must stay available 99.9% of the time", Kind.NON_FUNCTIONAL));

        Map<Kind, List<String>> buckets = new EnumMap<>(Kind.class);
        buckets.put(Kind.FUNCTIONAL, new ArrayList<>());
        buckets.put(Kind.NON_FUNCTIONAL, new ArrayList<>());

        for (Requirement r : raw) {
            buckets.get(r.kind).add(r.text);
        }

        for (Kind k : Kind.values()) {
            System.out.println(k + ":");
            for (String text : buckets.get(k)) {
                System.out.println("  - " + text);
            }
        }
    }
}
```

**How to run:** save as `RequirementSorter.java`, run `java RequirementSorter.java` (JDK 17+).

## 6. Walkthrough

1. The program builds a flat list of six requirements for a URL shortener, each already tagged as `FUNCTIONAL` or `NON_FUNCTIONAL` by a human during requirements gathering.
2. It creates a `Map` with one list per `Kind`, using an `EnumMap` so both buckets exist even before any items are added.
3. It loops over the raw list once and appends each requirement's text into its matching bucket.
4. It prints both buckets. Output:
```
FUNCTIONAL:
  - Users can shorten a long URL into a short one
  - Visiting a short URL redirects to the original URL
  - Users can see a click-count for their short URL
NON_FUNCTIONAL:
  - The system must handle 100 million redirects per day
  - p99 redirect latency must stay under 100 ms
  - The system must stay available 99.9% of the time
```
5. In a real interview, you do this sorting by hand on a whiteboard: two labeled columns, filled in as you gather requirements from the interviewer's answers to your clarifying questions.

## 7. Gotchas & takeaways

> **Gotcha:** treating "the system should be fast and reliable" as a completed non-functional requirement. It has no number, so it cannot drive a decision. Always push for a measurable target, and if the interviewer will not give one, state a reasonable assumption out loud.

- Gather functional requirements first — they define the scope of the problem you are solving.
- Then gather non-functional requirements — they define how hard that problem is, in numbers.
- Every architecture decision later in a design should trace back to one of these two lists.
