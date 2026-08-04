---
card: system-design
gi: 4
slug: constraints-assumptions-clarifying-questions
title: Constraints, assumptions & clarifying questions
---

## 1. What it is

A **constraint** is a hard limit the interviewer gives you, such as "assume a single data center" or "the client is a mobile app on unreliable networks". An **assumption** is a number or fact you fill in yourself, out loud, when the interviewer does not give you one, such as "I'll assume the average tweet is 280 characters, plus 100 bytes of metadata". A **clarifying question** is how you find out which constraints exist before you start assuming things you should have just asked about.

Think of it like following a recipe with missing steps: constraints are the ingredients you were told you must use; assumptions are the sensible substitutions you make, and say out loud, for the steps the recipe left blank.

## 2. Why & when

Interviewers deliberately leave gaps in the prompt to see how you handle ambiguity. Asking a good clarifying question shows you gather information before deciding. Stating a reasonable assumption when a question would not be worth asking (like the exact byte size of a timestamp) shows you can keep moving without stalling on every small detail. Getting this balance wrong in either direction is a real failure mode: asking too many trivial questions wastes interview time, and assuming too much on things that actually matter produces a design for the wrong problem.

You apply this right after scoping the problem, and you keep applying it throughout the interview whenever you hit a number or a rule you do not actually know.

## 3. Core concept

**When to ask vs. when to assume** comes down to impact: if the answer would change your architecture, ask. If the answer is a minor detail that does not change your design either way, state an assumption and move on.

Worth asking (high impact on the design):
- "Is this read-heavy or write-heavy?" (changes whether you cache reads or optimize writes)
- "Do we need strong consistency, or is eventual consistency acceptable?" (changes your database choice)
- "Single data center, or must this work globally?" (changes whether you need multi-region replication)

Fine to assume (low impact, state it and move on):
- "I'll assume the average object is about 1 KB, including metadata."
- "I'll assume a typical 80/20 split, 80% reads and 20% writes, unless told otherwise."
- "I'll assume standard HTTP/JSON between client and server."

**The pattern for stating an assumption:** name the assumption, give the number, and say why it is reasonable ("I'll assume 500 million monthly active users, since that's roughly Twitter's public figure, and about 20% of them are active daily"). This shows your reasoning, not just a guessed number.

## 4. Diagram

```
                 Does this answer change
                 my architecture choice?
                        |
             +----------+----------+
             |                     |
            YES                    NO
             |                     |
      ASK THE INTERVIEWER    STATE AN ASSUMPTION
      "Read-heavy or          "I'll assume ~1 KB
       write-heavy?"           per record, that's
                                typical for this."
```
*Caption: the decision rule that sorts every unknown into "ask" or "assume".*

## 5. Runnable example

### Artifact: a Java program that classifies unknowns into "ask" vs "assume" by impact score

```java
import java.util.*;

public class ClarifyOrAssume {

    static class Unknown {
        String question;
        int impact; // 1 (low) to 5 (high) — does it change the architecture?
        Unknown(String question, int impact) {
            this.question = question;
            this.impact = impact;
        }
    }

    static final int ASK_THRESHOLD = 3;

    public static void main(String[] args) {
        List<Unknown> unknowns = new ArrayList<>();
        unknowns.add(new Unknown("Read-heavy or write-heavy workload?", 5));
        unknowns.add(new Unknown("Strong consistency required?", 5));
        unknowns.add(new Unknown("Single data center or global?", 4));
        unknowns.add(new Unknown("Average record size in bytes?", 2));
        unknowns.add(new Unknown("Exact HTTP header format?", 1));

        for (Unknown u : unknowns) {
            String action = u.impact >= ASK_THRESHOLD ? "ASK" : "ASSUME";
            System.out.printf("[%s] (impact %d/5) %s%n", action, u.impact, u.question);
        }
    }
}
```

**How to run:** save as `ClarifyOrAssume.java`, run `java ClarifyOrAssume.java` (JDK 17+).

## 6. Walkthrough

1. Each `Unknown` pairs a question with an `impact` score from 1 to 5, representing how much the answer would change the design.
2. `ASK_THRESHOLD` is set to 3: anything scoring 3 or above is worth interrupting the interviewer for; below that, you assume.
3. The loop checks each unknown's impact against the threshold and labels it `ASK` or `ASSUME`.
4. Output:
```
[ASK] (impact 5/5) Read-heavy or write-heavy workload?
[ASK] (impact 5/5) Strong consistency required?
[ASK] (impact 4/5) Single data center or global?
[ASSUME] (impact 2/5) Average record size in bytes?
[ASSUME] (impact 1/5) Exact HTTP header format?
```
5. In the interview itself you run this classification mentally, in real time: the first two or three high-impact questions get asked out loud early; the low-impact ones get a stated assumption so the conversation keeps moving.

## 7. Gotchas & takeaways

> **Gotcha:** asking a low-impact question ("what programming language does the client use?" when it does not change the design) burns interview time and signals you cannot tell what matters. Save your questions for things that actually change the architecture.

- Ask only about things that would change your design; assume the rest, and say so out loud.
- Always state assumptions as numbers with a brief justification, not silently in your head.
- If an assumption turns out to matter more than you thought, you can revisit it later — say that too ("I'll revisit this if it turns out to be the bottleneck").
