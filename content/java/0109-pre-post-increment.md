---
card: java
gi: 109
slug: pre-post-increment
title: Pre/post increment ++
---

## 1. What it is

`++` increases a variable's value by exactly `1`. It comes in two forms that differ in what the *expression itself* evaluates to, not in the final stored value: **pre-increment** (`++x`) increments the variable first and the expression evaluates to the *new* value; **post-increment** (`x++`) evaluates to the *old* value first, and the increment happens as a side effect that becomes visible immediately after. When `++x` or `x++` is used as its own statement, the distinction is invisible — both leave `x` one greater than before. The difference only matters when the expression's *value* is used somewhere else, such as being assigned, printed, or passed as an argument in the same statement.

```java
int a = 5;
int b = ++a;   // a becomes 6 first, then b is assigned that new value: b == 6, a == 6
int c = 5;
int d = c++;   // d is assigned the OLD value 5 first, then c becomes 6: d == 5, c == 6
```

## 2. Why & when

`++` is the standard idiom for loop counters (`for (int i = 0; i < n; i++)`), running totals, and any "advance by one" operation. Pre- versus post-increment matters whenever the increment is embedded inside a larger expression:

- Array/string traversal: `array[i++]` accesses the current index, *then* advances `i` — a very common pattern for consuming elements in sequence.
- Building an ID or sequence generator: `return nextId++;` returns the current ID before advancing the counter for the next caller.
- Classic bugs arise from using the same variable more than once in one statement with `++`, e.g., `array[i] = i++;` — the order of operand evaluation versus side-effect timing becomes ambiguous to a reader (though Java's evaluation order is actually well-defined) and should be avoided for clarity even where it is legal.

## 3. Core concept

```java
public class IncrementDemo {
    public static void main(String[] args) {
        int a = 5;
        int preResult = ++a;     // a becomes 6, THEN preResult is assigned 6
        System.out.println("a=" + a + ", preResult=" + preResult);   // a=6, preResult=6

        int c = 5;
        int postResult = c++;    // postResult is assigned 5 (OLD value), THEN c becomes 6
        System.out.println("c=" + c + ", postResult=" + postResult); // c=6, postResult=5

        // Common idiom: consume-then-advance
        int[] data = { 10, 20, 30 };
        int i = 0;
        System.out.println("data[i++] = " + data[i++]);  // prints 10 (data[0]), i is now 1
        System.out.println("i is now: " + i);             // 1

        // Embedding in a condition
        int count = 0;
        while (count++ < 3) {
            System.out.println("count during loop: " + count);   // 1, 2, 3 (count already incremented by the time body runs)
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Pre-increment versus post-increment: plus plus a increments a first then evaluates to the new value 6, while c plus plus evaluates to the old value 5 first then increments c to 6.">
  <rect x="8" y="8" width="684" height="149" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Same final value, different expression result</text>

  <rect x="16" y="34" width="320" height="110" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="176" y="50" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">int b = ++a;  (a starts at 5)</text>
  <text x="30" y="72" fill="#e6edf3" font-size="8" font-family="monospace">1. a = a + 1  →  a = 6</text>
  <text x="30" y="90" fill="#79c0ff" font-size="8.5" font-family="monospace">2. expression evaluates to 6</text>
  <text x="30" y="108" fill="#6db33f" font-size="8" font-family="monospace">3. b = 6</text>
  <text x="30" y="128" fill="#8b949e" font-size="7.5" font-family="sans-serif">Increment happens BEFORE the value is used.</text>

  <rect x="352" y="34" width="332" height="110" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="518" y="50" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">int d = c++;  (c starts at 5)</text>
  <text x="366" y="72" fill="#e6edf3" font-size="8" font-family="monospace">1. expression evaluates to 5 (old c)</text>
  <text x="366" y="90" fill="#79c0ff" font-size="8.5" font-family="monospace">2. d = 5</text>
  <text x="366" y="108" fill="#6db33f" font-size="8" font-family="monospace">3. c = c + 1  →  c = 6</text>
  <text x="366" y="128" fill="#8b949e" font-size="7.5" font-family="sans-serif">Increment happens AFTER the value is used.</text>
</svg>

Both `++a` and `c++` leave the variable one greater — the difference is only which value the surrounding expression sees.

## 5. Runnable example

Scenario: a simple ticket-dispenser that hands out sequential ticket numbers to customers — a textbook use of post-increment for "return current, then advance" semantics — extended to a thread-safety concern.

### Level 1 — Basic

```java
public class TicketBasic {
    static int nextTicket = 1;

    static int takeTicket() {
        return nextTicket++;   // returns the CURRENT ticket number, then advances the counter
    }

    public static void main(String[] args) {
        System.out.println("Customer A gets ticket: " + takeTicket());  // 1
        System.out.println("Customer B gets ticket: " + takeTicket());  // 2
        System.out.println("Customer C gets ticket: " + takeTicket());  // 3
        System.out.println("Next ticket will be: " + nextTicket);        // 4
    }
}
```

**How to run:** `java TicketBasic.java`

`return nextTicket++;` evaluates to the *current* value of `nextTicket` (the value the `return` statement actually sends back), and only after that value has been captured does `nextTicket` get incremented. This is exactly the desired behavior for a ticket dispenser: each customer receives the number that was "current" at the moment they asked, and the next customer gets one more.

### Level 2 — Intermediate

Same dispenser, now demonstrating why swapping to pre-increment (`++nextTicket`) would change the numbering, and adding a a "peek" feature that must not have any side effect (contrasted with the incrementing `takeTicket`).

```java
public class TicketIntermediate {
    static int nextTicket = 1;

    static int takeTicket() {
        return nextTicket++;    // post-increment: caller gets the OLD value
    }

    static int peekNextTicket() {
        return nextTicket;       // no ++ at all — just reads, no side effect
    }

    // Demonstration only: shows what would happen with pre-increment instead
    static int takeTicketWithPreIncrementBug() {
        return ++nextTicket;    // pre-increment: caller gets the NEW value, skipping one number
    }

    public static void main(String[] args) {
        System.out.println("Peek before anyone takes a ticket: " + peekNextTicket()); // 1

        int a = takeTicket();
        int b = takeTicket();
        System.out.println("Customer A: " + a + ", Customer B: " + b);  // 1, 2
        System.out.println("Peek now: " + peekNextTicket());              // 3

        // Reset and show the pre-increment version would have skipped ticket #3
        nextTicket = 3;
        int buggy = takeTicketWithPreIncrementBug();
        System.out.println("Buggy pre-increment result: " + buggy + " (skipped 3, gave 4 instead)");
    }
}
```

**How to run:** `java TicketIntermediate.java`

`peekNextTicket` reads `nextTicket` with no `++` at all, so it is a pure, side-effect-free query — calling it repeatedly never changes the counter. `takeTicketWithPreIncrementBug` uses `++nextTicket` instead of `nextTicket++`: this increments the counter *first*, so the first customer to call it when `nextTicket == 3` would receive `4`, silently skipping ticket `3` entirely — a subtle numbering bug that would be easy to miss in review since `++nextTicket` and `nextTicket++` look almost identical.

### Level 3 — Advanced

Same dispenser, now made safe for concurrent access from multiple threads (multiple customers requesting tickets simultaneously), showing why a plain `nextTicket++` is *not* atomic despite looking like a single operation, and fixing it with `AtomicInteger`.

```java
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.*;

public class TicketAdvanced {

    // UNSAFE: plain int with ++ is not atomic — read, increment, write are three separate steps
    static int unsafeNextTicket = 1;
    static int unsafeTakeTicket() {
        return unsafeNextTicket++;  // can race: two threads may read the same value before either writes back
    }

    // SAFE: AtomicInteger.getAndIncrement performs the read-increment-write as one atomic step
    static AtomicInteger safeNextTicket = new AtomicInteger(1);
    static int safeTakeTicket() {
        return safeNextTicket.getAndIncrement();  // equivalent semantics to nextTicket++, but atomic
    }

    public static void main(String[] args) throws InterruptedException {
        int threads = 8, ticketsPerThread = 500;
        ExecutorService pool = Executors.newFixedThreadPool(threads);

        ConcurrentHashMap<Integer, Integer> unsafeSeen = new ConcurrentHashMap<>();
        for (int t = 0; t < threads; t++) {
            pool.submit(() -> {
                for (int i = 0; i < ticketsPerThread; i++) {
                    int ticket = unsafeTakeTicket();
                    unsafeSeen.merge(ticket, 1, Integer::sum);  // counts how many times each ticket number was issued
                }
            });
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);

        long duplicates = unsafeSeen.values().stream().filter(count -> count > 1).count();
        System.out.println("Unsafe dispenser: " + duplicates + " ticket numbers were issued more than once (race condition)");

        ConcurrentHashMap<Integer, Integer> safeSeen = new ConcurrentHashMap<>();
        ExecutorService pool2 = Executors.newFixedThreadPool(threads);
        for (int t = 0; t < threads; t++) {
            pool2.submit(() -> {
                for (int i = 0; i < ticketsPerThread; i++) {
                    int ticket = safeTakeTicket();
                    safeSeen.merge(ticket, 1, Integer::sum);
                }
            });
        }
        pool2.shutdown();
        pool2.awaitTermination(5, TimeUnit.SECONDS);

        long safeDuplicates = safeSeen.values().stream().filter(count -> count > 1).count();
        System.out.println("Safe dispenser: " + safeDuplicates + " ticket numbers were issued more than once");
    }
}
```

**How to run:** `java TicketAdvanced.java`

`unsafeNextTicket++` looks like one operation but the JVM actually performs it as three steps: read the current value, add one, write the new value back. If two threads both read the value `7` before either writes back `8`, both compute "current value 7, next 8" and both `unsafeTakeTicket()` calls return `7` — a duplicate ticket, and the counter only advances by one instead of two for that pair of calls. `AtomicInteger.getAndIncrement()` performs the equivalent of `nextTicket++` (return old value, then increment) as a single indivisible hardware-level operation (via compare-and-swap), so no two threads can ever observe or produce the same "old value," eliminating the race entirely. Running the unsafe version under real concurrent load will typically show a nonzero count of duplicate ticket numbers, while the safe version shows zero.

## 6. Walkthrough

Trace a potential race in `unsafeTakeTicket()` when two threads call it "simultaneously" while `unsafeNextTicket == 7`:

**Thread A reads.** Thread A executes the "read" step of `unsafeNextTicket++`, loading the current value `7` into a CPU register or local slot.

**Thread B reads (before A writes back).** Before Thread A has written its incremented value back to memory, Thread B also executes its own "read" step, and — because Thread A hasn't written yet — Thread B also loads `7`.

**Both increment and write.** Thread A computes `7 + 1 = 8` and writes `8` back to `unsafeNextTicket`. Thread B, working from its own stale read of `7`, also computes `7 + 1 = 8` and writes `8` back — overwriting (or racing with) Thread A's write.

**Both threads return `7`.** Since post-increment returns the *value that was read*, both `unsafeTakeTicket()` calls return `7` to their respective callers — two different customers receive the same ticket number, and the counter has only advanced from `7` to `8`, even though two tickets were "issued."

```
Time →
Thread A: read unsafeNextTicket (7) -----------------> write 8 -----> returns 7
Thread B:        read unsafeNextTicket (7) --> write 8 (overlaps!) -> returns 7

Both got 7. Counter only reached 8, not 9. One ticket number lost, one duplicated.
```

**The atomic fix.** `AtomicInteger.getAndIncrement()` wraps the read-modify-write sequence in a hardware-supported atomic primitive (compare-and-swap), so the entire "read old value, compute new value, write new value, but only if nothing else changed it in between" happens as one indivisible step from every other thread's perspective — if the compare-and-swap detects that another thread updated the value in between, it retries automatically, guaranteeing every thread sees a distinct old value.

## 7. Gotchas & takeaways

> **`x++` and `++x` produce the same final stored value — they only differ in what the surrounding expression evaluates to.** Used as a standalone statement (`x++;` on its own line), there is no observable difference at all.

> **`x++` on a plain variable is not thread-safe, even though it looks like a single operation.** It is actually read-modify-write in three separate steps, which can interleave across threads. Use `AtomicInteger`/`AtomicLong` (or synchronization) for counters shared across threads.

- Pre-increment (`++x`): increment happens first, expression evaluates to the new value.
- Post-increment (`x++`): expression evaluates to the old value first, increment happens as a side effect immediately after.
- `array[i++]` is the idiomatic "use current index, then advance" pattern for sequential array/collection consumption.
- Avoid using the same variable with `++` more than once in a single statement — even though Java's evaluation order is well-defined, it reads ambiguously and invites bugs during maintenance.
