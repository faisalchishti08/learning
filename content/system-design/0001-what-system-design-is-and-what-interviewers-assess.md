---
card: system-design
gi: 1
slug: what-system-design-is-and-what-interviewers-assess
title: What system design is (and what interviewers assess)
---

## 1. What it is

**System design** is the practice of planning how a large software system's parts fit together — clients, servers, databases, caches, and queues — so the whole system meets its goals for scale, speed, and reliability. Think of it like an architect's blueprint for a building: the blueprint does not lay every brick, but it decides where the load-bearing walls go, so the building does not collapse under real weight.

A **system design interview** asks you to produce that blueprint out loud, for a system like "design Twitter" or "design a URL shortener", in about 45 minutes. There is no single correct answer. The interviewer wants to see how you think, not whether you memorized one diagram.

## 2. Why & when

Companies use system design interviews because writing correct code is not the same skill as designing a system that survives real traffic, hardware failure, and growth. A senior engineer must be able to estimate scale, spot bottlenecks before they happen, and explain tradeoffs to a team. This card exists to build that skill, one concept at a time, before you combine them into full designs later in the card.

You use system design thinking whenever you build something bigger than a single script: choosing a database, deciding whether to cache, deciding whether one server is enough. The alternative — guessing, then fixing production at 3 a.m. — is expensive. Planning first is cheaper.

## 3. Core concept

Interviewers assess four things, in roughly this order of importance:

1. **Structured communication.** Do you clarify the problem before designing? Do you narrate your plan instead of jumping straight to a diagram?
2. **Requirements-driven decisions.** Do your choices trace back to a stated requirement ("I picked a cache because reads outnumber writes 100:1"), or are they arbitrary ("I'll just add Redis because everyone does")?
3. **Estimation and scale awareness.** Can you turn "500 million users" into "roughly 5,800 requests per second" and use that number to justify a decision, such as needing more than one server?
4. **Tradeoff reasoning.** Every real choice trades one quality for another (consistency for availability, cost for latency). Interviewers want to hear you name the tradeoff, not pretend a choice is free.

A useful mental loop for any design question is: **Requirements → Estimate the scale → Sketch the high-level design → Go deep on the hardest part → State the tradeoffs.** The rest of this section teaches the first two steps in detail, since they anchor everything that follows.

## 4. Diagram

```
 REQUIREMENTS  --->  ESTIMATION  --->  HIGH-LEVEL DESIGN  --->  DEEP DIVE  --->  TRADEOFFS
 (what must it     (how big is the    (boxes and arrows:      (the one hard    (what did we
  do, how well)      problem, in       client, server,          sub-problem,     give up to
                     numbers)          cache, DB, queue)        solved in detail) get this?)
```
*Caption: the five-step loop this whole card teaches, applied to every design question.*

## 5. Runnable example

### Artifact: a small Java program that models the assessment loop as data

```java
import java.util.*;

public class DesignInterviewLoop {

    // Each step of the loop, with a short description of what you produce.
    static class Step {
        String name;
        String output;
        Step(String name, String output) {
            this.name = name;
            this.output = output;
        }
    }

    public static void main(String[] args) {
        List<Step> loop = new ArrayList<>();
        loop.add(new Step("Requirements", "list of functional + non-functional requirements"));
        loop.add(new Step("Estimation", "QPS, storage, bandwidth numbers"));
        loop.add(new Step("High-level design", "boxes: client, load balancer, service, cache, DB"));
        loop.add(new Step("Deep dive", "detailed design of the single hardest sub-problem"));
        loop.add(new Step("Tradeoffs", "what was sacrificed for what was gained"));

        System.out.println("System design interview loop:");
        int i = 1;
        for (Step s : loop) {
            System.out.println(i + ". " + s.name + " -> " + s.output);
            i++;
        }
    }
}
```

**How to run:** save as `DesignInterviewLoop.java`, then run `java DesignInterviewLoop.java` (JDK 17+ can run a single file directly, no separate compile step needed).

## 6. Walkthrough

1. The program builds a list of `Step` objects, one per stage of the loop.
2. Each `Step` stores a `name` (the stage) and an `output` (what you should have produced by the end of that stage).
3. The `main` method loops over the list in order and prints each stage with a number, so the printed order matches the order you should follow in a real interview.
4. Running it prints:
```
System design interview loop:
1. Requirements -> list of functional + non-functional requirements
2. Estimation -> QPS, storage, bandwidth numbers
3. High-level design -> boxes: client, load balancer, service, cache, DB
4. Deep dive -> detailed design of the single hardest sub-problem
5. Tradeoffs -> what was sacrificed for what was gained
```
5. The point of modeling this as data, not prose, is that you can reuse the same five-step object in your head for any design prompt — "design Twitter", "design a rate limiter", or "design a chat app" all fit the same loop.

## 7. Gotchas & takeaways

> **Gotcha:** the most common failure is skipping straight to a high-level design (boxes and arrows) before clarifying requirements. This produces a design for the wrong problem, and you cannot recover the lost time.

- Always spend the first few minutes on requirements and estimation, even if the interviewer seems eager to see a diagram.
- There is no single "correct" design. Interviewers grade the reasoning, not the exact boxes drawn.
- Keep narrating out loud. A silent, correct diagram scores worse than a narrated, imperfect one, because the interviewer cannot assess thinking they cannot hear.
