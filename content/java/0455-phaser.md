---
card: java
gi: 455
slug: phaser
title: Phaser
---

## 1. What it is

`Phaser`, added in Java 7, is a flexible synchronization barrier — like `CyclicBarrier`, it lets a group of threads ("parties") wait for each other at a shared point before any proceed, and it supports repeated rounds ("phases"). Unlike `CyclicBarrier`, whose party count is fixed for its entire lifetime, `Phaser`'s set of participants can **change dynamically**: `register()` adds a new party at any time, and `arriveAndDeregister()` lets a party leave permanently, with the phaser automatically adjusting how many parties it waits for on subsequent phases.

## 2. Why & when

`CyclicBarrier` requires knowing the exact number of participating threads up front, fixed for the barrier's entire lifetime — fine for a static pool of worker threads, but a poor fit whenever the number of participants can genuinely change over time: a thread that finishes its work early and shouldn't be waited for anymore, or a new worker that joins partway through a multi-phase computation. `Phaser` was built specifically to handle this dynamism: `register()` and `arriveAndDeregister()` let the barrier's effective party count grow and shrink as needed, without ever needing to construct a new barrier object or coordinate that transition manually.

You reach for `Phaser` whenever a multi-phase, barrier-style synchronization needs a genuinely dynamic set of participants — a pipeline where workers can join or leave between phases, a computation where some threads finish early and shouldn't block the rest, or any scenario where `CyclicBarrier`'s fixed party count is too rigid.

## 3. Core concept

```java
import java.util.concurrent.Phaser;

Phaser phaser = new Phaser(3); // 3 parties initially

// Each party, once per phase:
phaser.arriveAndAwaitAdvance(); // arrive at this phase, block until ALL current parties have arrived

// A NEW party can join dynamically, at any point:
phaser.register(); // party count increases -- future phases wait for this new party too

// A party can leave permanently, at any point:
phaser.arriveAndDeregister(); // this party's final arrival -- party count decreases from now on
```

`arriveAndAwaitAdvance()` is the everyday "arrive and wait for everyone else" call, used repeatedly across phases; `arriveAndDeregister()` is specifically for a party's *final* arrival, telling the phaser not to expect anything further from it.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Phaser's set of participating parties can grow via register or shrink via arriveAndDeregister between phases, unlike CyclicBarrier's fixed party count set once at construction">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">Phase 0: parties A, B (2 registered)</text>
  <rect x="30" y="38" width="100" height="26" fill="#1c2430" stroke="#6db33f"/><text x="80" y="56" fill="#6db33f" font-size="9" text-anchor="middle">A</text>
  <rect x="140" y="38" width="100" height="26" fill="#1c2430" stroke="#6db33f"/><text x="190" y="56" fill="#6db33f" font-size="9" text-anchor="middle">B</text>

  <text x="20" y="90" fill="#e6edf3" font-size="11" font-family="sans-serif">Phase 1: C registers -- parties A, B, C (3 registered)</text>
  <rect x="30" y="102" width="100" height="26" fill="#1c2430" stroke="#6db33f"/><text x="80" y="120" fill="#6db33f" font-size="9" text-anchor="middle">A</text>
  <rect x="140" y="102" width="100" height="26" fill="#1c2430" stroke="#6db33f"/><text x="190" y="120" fill="#6db33f" font-size="9" text-anchor="middle">B</text>
  <rect x="250" y="102" width="100" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="300" y="120" fill="#79c0ff" font-size="9" text-anchor="middle">C (new)</text>

  <text x="440" y="60" fill="#8b949e" font-size="10" font-family="sans-serif">register() adds a party</text>
  <text x="440" y="130" fill="#8b949e" font-size="10" font-family="sans-serif">arriveAndDeregister() removes one</text>
</svg>

The set of parties a `Phaser` waits for can change between phases — something `CyclicBarrier` cannot do.

## 5. Runnable example

Scenario: a multi-phase task where the exact set of participating workers changes over time — the same phaser, evolved from a fixed set of parties advancing together through phases, through a new worker joining mid-way, to a worker leaving early so the remaining workers proceed without waiting for it.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class PhaserBasic {
    public static void main(String[] args) {
        Phaser phaser = new Phaser(3); // 3 fixed parties

        Runnable worker = () -> {
            String name = Thread.currentThread().getName();
            for (int phase = 0; phase < 3; phase++) {
                System.out.println(name + " working on phase " + phaser.getPhase());
                phaser.arriveAndAwaitAdvance(); // wait here until ALL 3 parties reach this point
            }
        };

        Thread t1 = new Thread(worker, "worker-1");
        Thread t2 = new Thread(worker, "worker-2");
        Thread t3 = new Thread(worker, "worker-3");
        t1.start(); t2.start(); t3.start();

        try { t1.join(); t2.join(); t3.join(); } catch (InterruptedException ignored) { }
        System.out.println("All phases complete. Final phase number: " + phaser.getPhase());
    }
}
```

**How to run:** `java PhaserBasic.java`

With 3 fixed parties, all three threads always finish each phase's print statement before any of them advances to the next phase's — `arriveAndAwaitAdvance()` blocks each thread until every currently-registered party has arrived for that phase. (Which specific thread prints first within a given phase isn't guaranteed, but no thread ever gets ahead to a later phase while another is still on an earlier one.)

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class PhaserDynamicRegister {
    public static void main(String[] args) throws InterruptedException {
        Phaser phaser = new Phaser(1); // main thread itself is party #1, so it can control timing

        Runnable worker = () -> {
            String name = Thread.currentThread().getName();
            for (int i = 0; i < 3; i++) {
                System.out.println(name + " arriving at phase " + phaser.getPhase());
                if (i == 2) {
                    phaser.arriveAndDeregister(); // last arrival: leave the phaser entirely, don't block future phases
                } else {
                    phaser.arriveAndAwaitAdvance();
                }
            }
        };

        phaser.register(); // worker-1
        Thread t1 = new Thread(worker, "worker-1");
        t1.start();

        phaser.register(); // worker-2
        Thread t2 = new Thread(worker, "worker-2");
        t2.start();

        phaser.arriveAndAwaitAdvance(); // main advances phase 0 -> 1, alongside worker-1 and worker-2

        // NOW register a third party, mid-way, BEFORE the next phase begins
        phaser.register();
        Thread t3 = new Thread(worker, "worker-3");
        t3.start();

        phaser.arriveAndAwaitAdvance(); // main advances phase 1 -> 2, now with worker-3 also participating
        phaser.arriveAndDeregister();   // main is done; deregister so remaining workers can finish their last phase alone

        t1.join(); t2.join(); t3.join();
        System.out.println("Final registered parties: " + phaser.getRegisteredParties());
    }
}
```

**How to run:** `java PhaserDynamicRegister.java`

The main thread itself acts as a party, controlling exactly when phases advance and precisely when `worker-3` joins — `phaser.register()` is called *after* phase 0 has already completed, and `worker-3` only participates starting from phase 1 onward. This is something `CyclicBarrier`, whose party count is fixed forever at construction, simply cannot express.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class PhaserEarlyDeregister {
    public static void main(String[] args) throws InterruptedException {
        Phaser phaser = new Phaser(3); // worker-1, worker-2, worker-3, all fixed from the start

        Runnable shortWorker = () -> { // leaves EARLY, after only 1 phase
            System.out.println("worker-1 arriving at phase " + phaser.getPhase());
            phaser.arriveAndDeregister(); // done for good -- reduces the party count from 3 to 2
            System.out.println("worker-1 done, deregistered");
        };

        Runnable longWorker = () -> {
            String name = Thread.currentThread().getName();
            for (int i = 0; i < 3; i++) {
                System.out.println(name + " arriving at phase " + phaser.getPhase());
                if (i == 2) phaser.arriveAndDeregister();
                else phaser.arriveAndAwaitAdvance();
            }
        };

        Thread t1 = new Thread(shortWorker, "worker-1");
        Thread t2 = new Thread(longWorker, "worker-2");
        Thread t3 = new Thread(longWorker, "worker-3");
        t1.start(); t2.start(); t3.start();

        t1.join(); t2.join(); t3.join();

        System.out.println("All done. Registered parties remaining: " + phaser.getRegisteredParties());
    }
}
```

**How to run:** `java PhaserEarlyDeregister.java`

`worker-1` participates in only the first phase, then calls `arriveAndDeregister()` and exits entirely — from that point on, the phaser only waits for `worker-2` and `worker-3`, who go on to complete two more phases together **without ever waiting for `worker-1` again**. This adaptive party count is exactly what makes `Phaser` suitable for workloads where participants naturally finish at different times.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `phaser` is constructed with `3` parties (`worker-1`, `worker-2`, `worker-3`, all registered from the start — no dynamic registration is needed here, unlike Level 2). All three threads start.

`worker-1` runs `shortWorker`: it prints `"worker-1 arriving at phase 0"`, then immediately calls `phaser.arriveAndDeregister()` — this both records `worker-1`'s arrival for phase 0 *and* permanently removes it from the phaser's party count, dropping it from 3 to 2. `worker-1` then prints `"worker-1 done, deregistered"` and its thread ends.

Meanwhile, `worker-2` and `worker-3` are both running `longWorker`. Each prints `"arriving at phase 0"` and calls `phaser.arriveAndAwaitAdvance()`. Since the phaser now only needs `worker-2`'s and `worker-3`'s arrivals to complete phase 0 (having already counted `worker-1`'s single arrival, and having had `worker-1` deregister), phase 0 completes once both of them have arrived — critically, `worker-1`'s absence from *future* phases is not a problem, since it already deregistered rather than simply vanishing.

`worker-2` and `worker-3` then proceed through phase 1 together (`i = 1`, calling `arriveAndAwaitAdvance()` again), and finally phase 2 (`i = 2`), where each calls `arriveAndDeregister()` instead, since it's their final iteration — this drops the phaser's party count further, from 2 down to 0 once both have deregistered.

After all three threads finish (`join()` returns for each), `phaser.getRegisteredParties()` correctly reports `0` — every party that started has, by this point, explicitly deregistered.

Expected output shape (the exact interleaving of "arriving" print lines within a shared phase can vary, but the phase progression itself — worker-1 alone at phase 0, then worker-2/worker-3 continuing through phases 1 and 2 without it — is stable):
```
worker-1 arriving at phase 0
worker-1 done, deregistered
worker-2 arriving at phase 0
worker-3 arriving at phase 0
worker-3 arriving at phase 1
worker-2 arriving at phase 1
worker-3 arriving at phase 2
worker-2 arriving at phase 2
All done. Registered parties remaining: 0
```

## 7. Gotchas & takeaways

> A party that simply lets its thread end **without** calling `arriveAndDeregister()` first remains counted as a registered party forever, as far as the `Phaser` is concerned — every future phase will wait indefinitely for an arrival that will never come, since that thread no longer exists to provide it. Always ensure every participating thread calls `arriveAndDeregister()` on its *final* arrival (rather than `arriveAndAwaitAdvance()`), or the phaser can deadlock the remaining, still-active parties.

- `Phaser` generalizes `CyclicBarrier`'s repeated-phase synchronization to support a dynamically changing set of participants.
- `register()` adds a new party at any time; `arriveAndDeregister()` is a party's *final* arrival, permanently reducing the phaser's active party count.
- `arriveAndAwaitAdvance()` is the everyday "arrive at this phase and wait for everyone else" call, used for every phase except a party's last.
- Forgetting to deregister a party whose thread is about to end is the classic `Phaser` bug — it leaves the phaser waiting forever for an arrival that can never happen, deadlocking every other still-active party.
- `getRegisteredParties()` and `getPhase()` provide useful introspection into a phaser's current state — how many parties are still active, and which phase number is currently in progress.
