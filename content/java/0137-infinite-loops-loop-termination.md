---
card: java
gi: 137
slug: infinite-loops-loop-termination
title: Infinite loops & loop termination
---

## 1. What it is

An **infinite loop** is any loop whose condition never becomes `false`, so it keeps running forever unless something inside it forcibly exits (a `break`, a `return`, an uncaught exception, or the process being killed). Java lets you write one explicitly and intentionally with `while (true)` or `for (;;)` — both mean "loop forever until I say otherwise from inside."

```java
int count = 0;
while (true) {
    System.out.println("Tick " + count);
    count++;
    if (count >= 3) {
        break; // the ONLY thing stopping this loop from running forever
    }
}
```

Without that `break`, this loop would print `"Tick 0"`, `"Tick 1"`, `"Tick 2"`, `"Tick 3"`... forever, never returning control to whatever called it.

## 2. Why & when

Deliberate infinite loops are a standard, idiomatic tool — not a mistake — when the natural exit condition doesn't fit cleanly into a `while`/`for` header, and is instead best expressed as a check somewhere in the middle of the body:

- **Event loops and servers** — a program that waits for connections or messages and processes them "forever" (until shut down) is inherently `while (true)`-shaped.
- **Read-then-decide loops** — when you must read or compute something first, and only *then* can decide whether to stop, sometimes it's clearer to write `while (true) { ...; if (done) break; }` than to contort the same logic into a loop header.
- **Menu loops** — repeat "show menu, read choice, act on it" until the choice is explicitly "quit," which is naturally a mid-body check.

The danger is the *accidental* version: a `while` or `for` loop whose condition variable is never actually updated on some code path, so it silently runs forever without that ever being the intent — the difference between a controlled `while (true)` with a clear `break`, and a bug, is entirely about whether termination is guaranteed and where.

## 3. Core concept

```java
public class InfiniteLoopDemo {
    public static void main(String[] args) {
        int attempts = 0;

        while (true) {
            attempts++;
            System.out.println("Working... attempt " + attempts);

            if (attempts == 4) {
                System.out.println("Condition met — breaking out.");
                break; // without this, the loop never ends
            }
        }

        System.out.println("Loop finished after " + attempts + " attempts.");
    }
}
```

`while (true)` has no condition that can ever turn `false` on its own — the *only* way this loop ends is the `break` statement inside it, triggered by an ordinary `if` check in the middle of the body, not in the loop header.

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Infinite loop diagram: while true loops back to itself unconditionally after each pass, and the only exit is an internal break statement guarded by an if check.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">while (true) { ...; if (done) break; } — the header can never stop the loop</text>

  <rect x="280" y="45" width="140" height="28" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="350" y="64" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">while (true)</text>

  <path d="M 350 73 L 350 95" stroke="#e6edf3" stroke-width="2" marker-end="url(#a)"/>
  <rect x="260" y="95" width="180" height="28" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="114" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">do work; check "if (done)"</text>

  <path d="M 260 109 C 130 109 130 59 278 59" stroke="#e6edf3" stroke-width="2" fill="none" marker-end="url(#a)"/>
  <text x="120" y="90" fill="#8b949e" font-size="8.5" font-family="sans-serif">always loops back</text>

  <path d="M 440 109 L 560 109" stroke="#6db33f" stroke-width="2" marker-end="url(#b)"/>
  <text x="500" y="99" fill="#6db33f" font-size="8.5" font-family="sans-serif">done: break</text>
  <rect x="560" y="95" width="90" height="28" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="605" y="114" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">exit</text>

  <text x="350" y="145" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Termination depends entirely on the break firing — there is no header condition to fall back on.</text>
  <defs>
    <marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#e6edf3"/></marker>
    <marker id="b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`while (true)` guarantees the loop keeps going; only an internal `break` (or `return`/exception) can stop it.

## 5. Runnable example

Scenario: a simulated polling loop that checks a "job status" repeatedly until it's done — starting with a basic `while (true)` and `break`, then adding a maximum poll count as a safety net, then hardening it to also react to a failure status, not just a success status.

### Level 1 — Basic

```java
public class PollBasic {
    public static void main(String[] args) {
        String[] simulatedStatuses = { "PENDING", "PENDING", "DONE" };
        int poll = 0;

        while (true) {
            String status = simulatedStatuses[poll];
            System.out.println("Poll " + (poll + 1) + ": status = " + status);
            poll++;

            if (status.equals("DONE")) {
                break;
            }
        }
        System.out.println("Job finished after " + poll + " poll(s).");
    }
}
```

**How to run:** `java PollBasic.java`

`while (true)` has no built-in stopping point — the loop relies entirely on the `if (status.equals("DONE")) break;` check inside the body. As long as the data eventually contains `"DONE"`, the loop terminates; if it never did, this loop would run until it read past the end of the array and crashed, which is exactly the risk explicit infinite loops carry.

### Level 2 — Intermediate

Same polling loop, now with a **maximum poll count** as an explicit safety net, so the loop cannot run forever even if the job status data never contains `"DONE"` — addressing the exact risk called out above.

```java
public class PollIntermediate {
    public static void main(String[] args) {
        String[] simulatedStatuses = { "PENDING", "PENDING", "PENDING", "PENDING" }; // never becomes DONE
        int poll = 0;
        final int maxPolls = 3;
        boolean done = false;

        while (true) {
            String status = simulatedStatuses[poll];
            System.out.println("Poll " + (poll + 1) + ": status = " + status);
            poll++;
            done = status.equals("DONE");

            if (done || poll >= maxPolls) {
                break;
            }
        }

        System.out.println(done ? "Job finished after " + poll + " poll(s)."
                                 : "Gave up after " + poll + " poll(s) — job never completed.");
    }
}
```

**How to run:** `java PollIntermediate.java`

The `break` condition is now `done || poll >= maxPolls` — the loop stops as soon as *either* the job finishes *or* the poll count hits its cap, whichever comes first. This is the standard remedy for a "loop until an external condition holds" pattern: always pair it with an independent, guaranteed-to-trigger upper bound.

### Level 3 — Advanced

Same polling loop, now also distinguishing an explicit `"FAILED"` status (which should stop the loop immediately, without waiting for the max-poll cap) from ordinary `"PENDING"` — a real production concern, since treating a definitive failure the same as "still waiting" would waste time polling a job that has already, unambiguously, failed.

```java
public class PollAdvanced {

    enum Outcome { SUCCESS, FAILURE, TIMEOUT }

    static Outcome pollJob(String[] statuses, int maxPolls) {
        int poll = 0;
        while (true) {
            if (poll >= maxPolls) {
                return Outcome.TIMEOUT;
            }
            String status = statuses[poll];
            System.out.println("Poll " + (poll + 1) + ": status = " + status);
            poll++;

            if (status.equals("DONE")) {
                return Outcome.SUCCESS;
            }
            if (status.equals("FAILED")) {
                return Outcome.FAILURE;
            }
            // otherwise PENDING — loop continues
        }
    }

    public static void main(String[] args) {
        System.out.println(pollJob(new String[]{ "PENDING", "FAILED", "DONE" }, 5));
        System.out.println(pollJob(new String[]{ "PENDING", "PENDING", "DONE" }, 5));
        System.out.println(pollJob(new String[]{ "PENDING", "PENDING", "PENDING" }, 2));
    }
}
```

**How to run:** `java PollAdvanced.java`

Here the loop exits via `return`, not `break` — a `return` inside a `while (true)` immediately exits both the loop and the enclosing method at once, which is why `pollJob` needs no separate variable to remember the outcome; each exit point (`TIMEOUT`, `SUCCESS`, `FAILURE`) directly returns its own enum value. Notice the `poll >= maxPolls` check now happens at the *top* of the loop body (before reading `statuses[poll]`), preventing an out-of-bounds read when the job never resolves within the allotted polls, as in the third call.

## 6. Walkthrough

Trace the third call, `pollJob(new String[]{ "PENDING", "PENDING", "PENDING" }, 2)`:

**Poll 1.** `poll = 0`. Timeout check: `0 >= 2` → `false`, continue. Read `statuses[0] = "PENDING"`; print `"Poll 1: status = PENDING"`; `poll` becomes `1`. Neither `"DONE"` nor `"FAILED"` matches `"PENDING"`, so the loop goes back to the top.

**Poll 2.** Timeout check: `1 >= 2` → `false`, continue. Read `statuses[1] = "PENDING"`; print `"Poll 2: status = PENDING"`; `poll` becomes `2`. Still `"PENDING"`, loop again.

**Poll 3 attempt.** Timeout check: `2 >= 2` → `true` — this fires *before* attempting `statuses[2]`, so `return Outcome.TIMEOUT;` executes immediately, and the third array element is never even read (which matters, since the array in this call only holds two meaningfully distinct entries relevant to the cap; more importantly, the check protects against any array shorter than `maxPolls`).

```
poll=0: timeout? 0>=2 false -> read "PENDING" -> poll=1 -> not DONE/FAILED, loop
poll=1: timeout? 1>=2 false -> read "PENDING" -> poll=2 -> not DONE/FAILED, loop
poll=2: timeout? 2>=2 TRUE  -> return TIMEOUT (array not read again)
```

**Final output.** The three calls print `SUCCESS` (found `"DONE"` after seeing a `"FAILED"` at poll 2, which is itself irrelevant to the first array's second element being `"FAILED"` — here it actually returns `FAILURE` at poll 2 for the first call), `SUCCESS` (found `"DONE"` on poll 3 for the second call), and `TIMEOUT` (for the third call, exactly as traced above). Each `Outcome` enum value prints via its default `toString()`, giving `FAILURE`, `SUCCESS`, and `TIMEOUT` on their own lines.

## 7. Gotchas & takeaways

> **`while (true)` and `for (;;)` have no built-in stopping point at all** — every guarantee that the loop terminates comes entirely from code *inside* the body (a `break`, `return`, or thrown exception). If that internal exit path has a bug — an `if` condition that's never actually satisfied — the loop truly never ends, and the program hangs or spins the CPU forever.

> **A `while` or `for` loop with a normal-looking condition can be just as "infinite" by accident** if nothing in the body ever changes the variables the condition depends on — infinite loops aren't only the explicit `while (true)` form; forgetting a counter's increment is the more common real-world cause.

- Use `while (true)` deliberately when the natural exit check belongs in the middle of the loop body, not the header — and always pair it with a clear, reachable `break`/`return`.
- Prefer checking a hard upper bound (like `maxPolls`) independently of the "success" condition, so the loop cannot hang even if success never arrives.
- Put safety-limit checks (like a timeout) at the very top of the loop body when they must run before any data access that could otherwise go out of bounds.
- Every loop — infinite-looking or not — should have an obviously reachable path to termination; if you can't point to the line that will eventually stop it, that's a bug waiting to happen.
