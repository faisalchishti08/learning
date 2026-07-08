---
card: java
gi: 403
slug: copyonwritearraylist-copyonwritearrayset
title: CopyOnWriteArrayList / CopyOnWriteArraySet
---

## 1. What it is

`CopyOnWriteArrayList<E>` and `CopyOnWriteArraySet<E>` are thread-safe collections that take a distinctive approach: **every mutating operation** (`add`, `remove`, `set`) copies the entire underlying array, applies the change to the copy, and then atomically swaps the internal reference to point at the new array. Reads (including iteration) always work against a fixed, unchanging snapshot — they never see a partial modification and never throw `ConcurrentModificationException`, even while another thread is actively mutating the collection.

## 2. Why & when

Iterating a plain `ArrayList` (or `HashSet`) while another thread modifies it — or even while the *same* thread modifies it mid-iteration — throws `ConcurrentModificationException`. That's a real problem for a very common pattern: a list of event listeners, observers, or subscribers, where iteration ("notify everyone") happens constantly and modification ("someone subscribes or unsubscribes") happens rarely.

`CopyOnWriteArrayList` is built exactly for that **read-heavy, write-rare** shape. Because every iterator works against a private, immutable snapshot taken when the iteration began, you can safely add or remove listeners *while* another thread is in the middle of notifying all of them — no exception, no external locking needed. The tradeoff is cost: every single write copies the *entire* backing array, which is fine occasionally but would be disastrous for a list that's mutated frequently or is very large — that's precisely why it's a poor fit for write-heavy workloads, where `Collections.synchronizedList` or a `ConcurrentHashMap`-backed structure would be more appropriate.

## 3. Core concept

```java
CopyOnWriteArrayList<String> listeners = new CopyOnWriteArrayList<>();
listeners.add("emailListener");
listeners.add("smsListener");

// Thread A: iterating (notifying) --------------------
for (String listener : listeners) {         // iterates over a SNAPSHOT taken right here
    System.out.println("Notifying " + listener);
    // Thread B could add/remove listeners concurrently right now -- no exception, no visible change to THIS loop
}

// Thread B: mutating, possibly during Thread A's loop above ----
listeners.add("pushListener"); // creates a brand-new internal array; doesn't affect A's in-progress iteration
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A write to a CopyOnWriteArrayList copies the whole backing array and swaps the reference; an in-progress iterator keeps using the old array snapshot">
  <rect x="8" y="8" width="624" height="184" rx="8" fill="#0d1117"/>
  <text x="20" y="28" fill="#e6edf3" font-size="11" font-family="sans-serif">Before write: iterator holds a reference to array v1</text>
  <rect x="30" y="40" width="200" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="60" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">array v1: [email, sms]</text>
  <line x1="130" y1="70" x2="130" y2="90" stroke="#79c0ff" stroke-dasharray="3,2"/>
  <text x="130" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">iterator still reading v1</text>

  <text x="20" y="140" fill="#e6edf3" font-size="11" font-family="sans-serif">add("push") copies to a NEW array v2, then swaps the field reference</text>
  <rect x="350" y="40" width="240" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="60" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">array v2: [email, sms, push] (new copy)</text>

  <line x1="230" y1="55" x2="345" y2="55" stroke="#f85149" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#a6)"/>
  <text x="290" y="45" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">copy</text>
  <defs><marker id="a6" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker></defs>
</svg>

An in-progress iteration keeps seeing the old snapshot; the write never touches it, so no `ConcurrentModificationException` is possible.

## 5. Runnable example

Scenario: an event bus that notifies a list of subscribers — the same subscriber list, evolved from a plain `ArrayList` that crashes when a listener unsubscribes itself mid-notification, through a `CopyOnWriteArrayList` fix, to a version demonstrating that in-flight iterations don't see concurrent changes.

### Level 1 — Basic

```java
import java.util.*;

public class EventBusCrash {
    public static void main(String[] args) {
        List<String> listeners = new ArrayList<>(List.of("email", "sms", "push"));

        for (String listener : listeners) {
            System.out.println("Notifying " + listener);
            if (listener.equals("sms")) {
                listeners.remove("sms"); // modifying the list WHILE iterating it
            }
        }
    }
}
```

**How to run:** `java EventBusCrash.java`

A plain `ArrayList` throws `ConcurrentModificationException` the moment you modify it during a `for-each` loop over itself (even from the very same thread) — the enhanced `for` loop's internal iterator detects the list changed underneath it and fails fast rather than risk silently corrupt behaviour.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class EventBusFixed {
    public static void main(String[] args) {
        CopyOnWriteArrayList<String> listeners = new CopyOnWriteArrayList<>(List.of("email", "sms", "push"));

        for (String listener : listeners) {
            System.out.println("Notifying " + listener);
            if (listener.equals("sms")) {
                listeners.remove("sms"); // safe: this creates a NEW backing array; the current iteration is unaffected
            }
        }

        System.out.println("Listeners after: " + listeners);
    }
}
```

**How to run:** `java EventBusFixed.java`

`CopyOnWriteArrayList` never throws `ConcurrentModificationException` — `listeners.remove("sms")` swaps in a fresh internal array, but the loop's iterator is still working off the *snapshot* taken when iteration started, so it continues to visit `"push"` normally. The list itself, checked afterward, correctly reflects the removal.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.List;

public class EventBusConcurrentThreads {
    public static void main(String[] args) throws InterruptedException {
        CopyOnWriteArrayList<String> listeners = new CopyOnWriteArrayList<>(List.of("email", "sms", "push"));

        Thread notifier = new Thread(() -> {
            for (String listener : listeners) { // this iteration's snapshot is fixed at the moment it began
                System.out.println("Notifying " + listener);
                try { Thread.sleep(30); } catch (InterruptedException ignored) { }
            }
            System.out.println("Notification round complete.");
        });

        Thread subscriber = new Thread(() -> {
            try { Thread.sleep(15); } catch (InterruptedException ignored) { }
            listeners.add("webhook"); // added WHILE notifier's loop above is mid-iteration
            System.out.println("New subscriber added: webhook");
        });

        notifier.start();
        subscriber.start();
        notifier.join();
        subscriber.join();

        System.out.println("Final listeners (next round would include webhook): " + listeners);
    }
}
```

**How to run:** `java EventBusConcurrentThreads.java`

The `notifier` thread's current notification round does **not** see `"webhook"` even though it's added mid-iteration by another thread — the round was already iterating a fixed snapshot of `[email, sms, push]`. The list itself, however, is correctly updated, so the *next* time anything iterates `listeners`, `"webhook"` will be included.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example, creating a `CopyOnWriteArrayList` with three initial listeners and starting two threads: `notifier` and `subscriber`.

The `notifier` thread begins its `for-each` loop over `listeners`. Internally, `CopyOnWriteArrayList`'s iterator captures a reference to the *current* backing array (`[email, sms, push]`) the moment iteration starts — this reference will not change for the rest of this particular loop, no matter what happens to `listeners` afterward. The loop prints `"Notifying email"`, sleeps 30ms, then continues.

Concurrently, the `subscriber` thread sleeps 15ms (so it wakes up while `notifier` is still mid-loop, likely partway through processing `"email"` or about to move to `"sms"`), then calls `listeners.add("webhook")`. Internally, this copies the current backing array (`[email, sms, push]`), appends `"webhook"` to the copy (`[email, sms, push, webhook]`), and atomically swaps `listeners`' internal array reference to point at this new, longer array. It then prints `"New subscriber added: webhook"`.

Back in the `notifier` thread, the loop continues to `"sms"` and then `"push"` — but because its iterator is still holding the *original* array reference from before the swap, it never sees `"webhook"`; it only ever visits the three listeners that existed when the loop began. After processing `"push"`, the loop ends naturally (three elements visited, as expected), and `"Notification round complete."` prints.

Both threads then finish (`join()` returns for each), and `main` prints the final state of `listeners` — which, because it reflects the *current* array (post-swap), correctly includes `"webhook"`, proving the addition did take effect on the collection itself, just not on the notification round that was already in progress.

Expected output (interleaving of the two threads' prints may vary slightly, but the key facts — 3 notifications, no crash, final list has 4 entries — are stable):
```
Notifying email
New subscriber added: webhook
Notifying sms
Notifying push
Notification round complete.
Final listeners (next round would include webhook): [email, sms, push, webhook]
```

## 7. Gotchas & takeaways

> Every single mutation on a `CopyOnWriteArrayList` copies the **entire** backing array. For a list with thousands of elements mutated frequently, this is disastrous for performance — it's built specifically for **read-heavy, write-rare** use cases like listener/observer lists, not as a general-purpose thread-safe list replacement.

- Modifying a plain `ArrayList` (or `HashSet`) during iteration — even from the same thread — throws `ConcurrentModificationException`; `CopyOnWriteArrayList`/`Set` never does.
- Iterators over a `CopyOnWriteArrayList` always reflect a fixed snapshot taken when the iteration began — concurrent additions or removals during that iteration are invisible to it, but are correctly visible to any *later* iteration.
- The write cost (a full array copy per mutation) is the tradeoff for that iteration safety — use these classes only where reads vastly outnumber writes.
- `CopyOnWriteArraySet` is built on top of `CopyOnWriteArrayList` internally and offers the same snapshot-iteration guarantee for set semantics (no duplicates).
- Typical use cases: listener/subscriber lists, configuration that's read constantly but updated rarely, or any small collection where correctness during concurrent iteration matters more than raw write throughput.
