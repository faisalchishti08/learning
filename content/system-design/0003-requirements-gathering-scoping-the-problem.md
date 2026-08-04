---
card: system-design
gi: 3
slug: requirements-gathering-scoping-the-problem
title: Requirements gathering & scoping the problem
---

## 1. What it is

**Requirements gathering** is the process of asking targeted questions to turn a vague prompt, such as "design Twitter", into a concrete, bounded problem you can actually design a solution for. **Scoping** is the act of deliberately deciding what is in the design and what is out, so a 45-minute conversation stays finishable.

Think of a doctor's intake questions before a diagnosis: "where does it hurt, since when, how bad" turns a vague complaint into a specific, answerable problem. System design prompts are deliberately vague for the same reason a patient's first sentence is vague — the interviewer wants to see you ask the right questions, not guess.

## 2. Why & when

A prompt like "design Twitter" could mean the posting flow, the timeline-generation algorithm, the search feature, the notification system, or all of them combined. Without scoping, you either run out of time trying to design everything, or you design the wrong part of the system entirely. Gathering requirements first prevents both failures.

You do this at the very start of every design problem, before drawing a single box. It typically takes 3 to 5 minutes out of a 45-minute interview, and it is time well spent: every later decision becomes easier to justify once you know exactly what you are building.

## 3. Core concept

**The gathering process has three moves, done in order:**

1. **Ask what the core use cases are.** For "design Twitter", ask: "Should I focus on posting and viewing a timeline, or also search, direct messages, and notifications?" The interviewer will usually narrow it for you — take that narrowing as the scope.
2. **Ask about scale.** "How many users, how many requests per day, read-heavy or write-heavy?" This feeds directly into the estimation step covered in later tutorials in this section.
3. **State what is explicitly out of scope, out loud.** "I will focus on posting a tweet and reading a timeline. I will not design search, ads, or direct messages, unless we have time later." This protects you: if you never mention search, the interviewer may wonder if you forgot it exists. Saying it is out of scope shows it was a deliberate choice.

**A scoping rule of thumb:** pick 2 to 4 core functional requirements to design in depth. Anything beyond that becomes a shallow mention ("I'd add a notification service later, using the same queue pattern") rather than a full design. Depth on a few features beats a shallow pass over many.

## 4. Diagram

```
 VAGUE PROMPT              CLARIFYING QUESTIONS           SCOPED PROBLEM
 "Design Twitter"    -->   "Post + read timeline,    -->  IN SCOPE:
                            or also search & DMs?"          - post a tweet
                           "How many users, read-           - view a timeline
                            heavy or write-heavy?"         OUT OF SCOPE (say so!):
                                                             - search
                                                             - direct messages
```
*Caption: three questions turn an open-ended prompt into a bounded, statable problem.*

## 5. Runnable example

### Artifact: a Java program modeling the scope decision as an explicit in/out list

```java
import java.util.*;

public class ScopeBuilder {

    public static void main(String[] args) {
        List<String> allPossibleFeatures = Arrays.asList(
            "post a tweet",
            "view a timeline",
            "follow a user",
            "search tweets",
            "direct messages",
            "notifications",
            "trending topics"
        );

        // Decision made after asking the interviewer's clarifying answers.
        Set<String> inScope = new LinkedHashSet<>(Arrays.asList(
            "post a tweet",
            "view a timeline",
            "follow a user"
        ));

        List<String> outOfScope = new ArrayList<>();
        for (String feature : allPossibleFeatures) {
            if (!inScope.contains(feature)) {
                outOfScope.add(feature);
            }
        }

        System.out.println("IN SCOPE (design in depth):");
        for (String f : inScope) System.out.println("  - " + f);

        System.out.println("OUT OF SCOPE (state this out loud, do not silently drop it):");
        for (String f : outOfScope) System.out.println("  - " + f);
    }
}
```

**How to run:** save as `ScopeBuilder.java`, run `java ScopeBuilder.java` (JDK 17+).

## 6. Walkthrough

1. `allPossibleFeatures` lists every feature someone might associate with "Twitter" — far too many to design in 45 minutes.
2. `inScope` is a `LinkedHashSet` holding only the features chosen after clarifying questions; a `LinkedHashSet` is used so the print order matches the order the features were decided on.
3. The loop builds `outOfScope` by checking, for each possible feature, whether it is missing from `inScope`.
4. The program prints both lists clearly labeled. Output:
```
IN SCOPE (design in depth):
  - post a tweet
  - view a timeline
  - follow a user
OUT OF SCOPE (state this out loud, do not silently drop it):
  - search tweets
  - direct messages
  - notifications
  - trending topics
```
5. This mirrors exactly what you should say out loud in an interview: name what you will design, then explicitly name what you are leaving out and why, so the interviewer knows it was a choice.

## 7. Gotchas & takeaways

> **Gotcha:** silently ignoring a feature (like search) without mentioning it reads as an oversight. Stating "I'm leaving search out of scope for now" reads as a deliberate, senior decision.

- Ask about use cases and scale before designing anything — these two questions shape everything downstream.
- Cap your in-scope list at 2 to 4 core features so you have time to go deep.
- Always say your out-of-scope list out loud; an unstated omission looks like a gap in your thinking.
