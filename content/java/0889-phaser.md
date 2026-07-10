---
card: java
gi: 889
slug: phaser
title: Phaser
---

## 1. What it is

`Phaser` is a more flexible generalization of [`CyclicBarrier`](0887-cyclicbarrier.md): it also synchronizes a group of threads through repeated phases, but unlike a `CyclicBarrier`'s fixed party count, a `Phaser`'s set of participants can grow and shrink dynamically between (or even during) phases via `register()`/`bulkRegister()` (join) and `arriveAndDeregister()` (finish and leave). Threads signal arrival at the current phase with `arrive()` (don't wait) or `arriveAndAwaitAdvance()` (arrive and block until every registered party has also arrived), and the phaser tracks a phase number that increments each time all registered parties have arrived.

## 2. Why & when

Use `Phaser` instead of `CyclicBarrier` specifically when the number of participating threads isn't fixed for the whole computation — a pipeline where worker threads are spawned or retired between phases, a simulation where entities can "die" (deregister) or "spawn" (register) between iterations, or a recursive fork/join-style computation where subtasks dynamically join the same phased coordination. `CyclicBarrier`'s constructor requires a fixed party count up front and cannot adapt if the number of participants changes; `Phaser` handles this natively. It is a more complex API in exchange for that flexibility, so if your thread count truly is fixed and known ahead of time, `CyclicBarrier`'s simpler API is usually the better fit.

## 3. Core concept

```java
Phaser phaser = new Phaser(1); // register the "main" thread itself as 1 initial party

for (int i = 0; i < workerCount; i++) {
    phaser.register(); // dynamically add each worker as a new party BEFORE it starts
    new Thread(() -> {
        doPhaseOneWork();
        phaser.arriveAndAwaitAdvance(); // wait for ALL currently-registered parties
        doPhaseTwoWork();
        phaser.arriveAndDeregister(); // finish and LEAVE -- reduces the party count for future phases
    }).start();
}
phaser.arriveAndAwaitAdvance(); // main thread also participates in phase 1's synchronization
phaser.arriveAndDeregister();   // main thread leaves once its own participation is done
```

Parties can register and deregister across phases, meaning the exact set (and count) of threads being synchronized can differ from one phase to the next.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Phaser tracking phase 0 with 3 registered parties, one party deregisters after phase 0, a new party registers before phase 1, so phase 1 has a different set of participants">
  <text x="160" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Phase 0: parties A, B, C</text>
  <rect x="20" y="35" width="80" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="60" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">A</text>
  <rect x="120" y="35" width="80" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">B</text>
  <rect x="220" y="35" width="80" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="260" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">C (leaves after phase 0)</text>

  <text x="480" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Phase 1: parties A, B, D</text>
  <rect x="380" y="35" width="80" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="420" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">A</text>
  <rect x="480" y="35" width="80" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="520" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">B</text>
  <rect x="580" y="35" width="50" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="605" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">D (new)</text>

  <line x1="320" y1="50" x2="376" y2="50" stroke="#8b949e" stroke-width="2" marker-end="url(#a23)"/>
  <text x="330" y="130" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">The set of parties being synchronized can change from one phase to the next -- CyclicBarrier cannot do this.</text>
  <defs><marker id="a23" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Party C deregisters after phase 0; party D registers before phase 1 — the phaser tracks whatever the current set of parties is at each phase.*

## 5. Runnable example

Scenario: a simulation where worker "agents" complete a fixed number of phases but new agents can join mid-simulation, growing from a fixed-count `CyclicBarrier` version (which can't handle dynamic joining), to a `Phaser` version supporting dynamic registration, to a version where agents also deregister early once their own work is done.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class FixedCyclicBarrierLimitation {
    public static void main(String[] args) throws InterruptedException {
        int initialAgents = 3;
        // CyclicBarrier requires a FIXED party count up front -- cannot add a 4th agent mid-simulation
        CyclicBarrier barrier = new CyclicBarrier(initialAgents,
            () -> System.out.println("--- phase complete for all " + initialAgents + " initial agents ---"));

        Thread[] threads = new Thread[initialAgents];
        for (int i = 0; i < initialAgents; i++) {
            final int id = i;
            threads[i] = new Thread(() -> {
                for (int phase = 1; phase <= 2; phase++) {
                    try { Thread.sleep(20L * (id + 1)); } catch (InterruptedException ignored) {}
                    System.out.println("agent " + id + " finished phase " + phase);
                    try { barrier.await(); } catch (Exception e) { Thread.currentThread().interrupt(); }
                }
            });
            threads[i].start();
        }
        for (Thread t : threads) t.join();
        System.out.println("done -- but a 4th agent joining mid-run would require constructing a NEW barrier entirely");
    }
}
```

**How to run:** `java FixedCyclicBarrierLimitation.java` (JDK 17+).

Expected output shape:
```
agent 0 finished phase 1
agent 1 finished phase 1
agent 2 finished phase 1
--- phase complete for all 3 initial agents ---
agent 0 finished phase 2
agent 1 finished phase 2
agent 2 finished phase 2
--- phase complete for all 3 initial agents ---
done -- but a 4th agent joining mid-run would require constructing a NEW barrier entirely
```

Works fine for a fixed set of 3 agents, but `CyclicBarrier`'s party count is baked in at construction — there's no way to add a 4th agent partway through without rebuilding the whole synchronization structure.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class PhaserDynamicRegistration {
    public static void main(String[] args) throws InterruptedException {
        Phaser phaser = new Phaser(1); // main thread registers as the first party

        Thread[] initial = new Thread[2];
        for (int i = 0; i < 2; i++) {
            final int id = i;
            phaser.register(); // register EACH worker as a new party before starting it
            initial[i] = new Thread(() -> runAgent(id, phaser));
            initial[i].start();
        }

        // main participates in phase 1, THEN dynamically adds a 3rd agent before phase 2
        phaser.arriveAndAwaitAdvance();
        System.out.println("--- phase 1 complete, now adding a new agent dynamically ---");

        phaser.register(); // dynamically add a 3rd party AFTER phase 1 has already happened
        Thread lateJoiner = new Thread(() -> runAgent(2, phaser));
        lateJoiner.start();

        phaser.arriveAndDeregister(); // main thread is done participating -- leaves the phaser
        for (Thread t : initial) t.join();
        lateJoiner.join();
        System.out.println("done");
    }

    static void runAgent(int id, Phaser phaser) {
        try { Thread.sleep(20L * (id + 1)); } catch (InterruptedException ignored) {}
        System.out.println("agent " + id + " finished phase " + phaser.getPhase());
        phaser.arriveAndAwaitAdvance();
    }
}
```

**How to run:** `java PhaserDynamicRegistration.java`.

Expected output shape (the late-joining agent 2 only participates from phase 2 onward, something `CyclicBarrier` cannot express):
```
agent 0 finished phase 0
agent 1 finished phase 0
--- phase 1 complete, now adding a new agent dynamically ---
agent 2 finished phase 1
done
```

The real-world concern added: a new party (agent 2) is registered *after* phase 1 has already completed, and correctly participates starting from phase 2 — something a `CyclicBarrier`, whose party count is fixed at construction, has no way to express without discarding and recreating the whole barrier.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class PhaserWithDeregistration {
    public static void main(String[] args) throws InterruptedException {
        Phaser phaser = new Phaser(1); // main is party 1
        AtomicInteger activeAgents = new AtomicInteger(3);

        for (int i = 0; i < 3; i++) {
            final int id = i;
            phaser.register();
            new Thread(() -> {
                int totalPhasesForThisAgent = 3 - id; // agent 0 does 3 phases, agent 1 does 2, agent 2 does 1
                for (int phase = 0; phase < totalPhasesForThisAgent; phase++) {
                    try { Thread.sleep(10); } catch (InterruptedException ignored) {}
                    System.out.println("agent " + id + " completed a phase (phaser phase=" + phaser.getPhase() + ")");
                    if (phase == totalPhasesForThisAgent - 1) {
                        // last phase for this agent -- arrive AND leave, reducing future party counts
                        phaser.arriveAndDeregister();
                        activeAgents.decrementAndGet();
                    } else {
                        phaser.arriveAndAwaitAdvance(); // more phases to go -- arrive and wait for the group
                    }
                }
            }).start();
        }

        // main waits through phases, deregistering once no agents remain registered
        while (phaser.getUnarrivedParties() > 0 || phaser.getRegisteredParties() > 1) {
            phaser.arriveAndAwaitAdvance();
        }
        phaser.arriveAndDeregister();

        System.out.println("simulation complete, active agents remaining: " + activeAgents.get());
    }
}
```

**How to run:** `java PhaserWithDeregistration.java`.

Expected output shape (agent 2 leaves after phase 0, agent 1 after phase 1, agent 0 after phase 2 — each phase has progressively fewer parties):
```
agent 0 completed a phase (phaser phase=0)
agent 1 completed a phase (phaser phase=0)
agent 2 completed a phase (phaser phase=0)
agent 0 completed a phase (phaser phase=1)
agent 1 completed a phase (phaser phase=1)
agent 0 completed a phase (phaser phase=2)
simulation complete, active agents remaining: 0
```

This adds the production-flavored hard case: agents with **different numbers of phases** to complete, each deregistering (via `arriveAndDeregister()`) once its own work is done — the phaser's effective party count shrinks after each agent finishes, so later phases only wait for the agents still actively participating, exactly the kind of dynamic, uneven-lifetime coordination `CyclicBarrier`'s fixed party model cannot represent.

## 6. Walkthrough

Tracing `PhaserWithDeregistration.main`:

1. `Phaser phaser = new Phaser(1)` registers `main` itself as the first party; then three agent threads are each registered (`phaser.register()`) before being started, bringing the total registered party count to 4.
2. In phase 0 (the phaser's initial phase number), all three agents sleep briefly and print their completion message, then each calls either `arriveAndAwaitAdvance()` (agents 0 and 1, which have more phases left) or, for agent 2 (whose `totalPhasesForThisAgent` is 1), `arriveAndDeregister()` on its very first and only phase.
3. `arriveAndDeregister()` both signals this thread's arrival for the current phase *and* removes it from the phaser's party count going forward — once agents 0, 1, and 2 (deregistering) have all arrived, along with `main` (still registered), the phase advances to phase 1, and agent 2 does not participate in any future phase.
4. `main`'s loop condition (`phaser.getUnarrivedParties() > 0 || phaser.getRegisteredParties() > 1`) keeps it looping through `arriveAndAwaitAdvance()` calls as long as there's more than just itself registered — each call advances the phase once every currently-registered party (now down to agent 0, agent 1, and `main`) has arrived.
5. In phase 1, agent 1 completes its second (and final) phase and calls `arriveAndDeregister()`, dropping the party count further; agent 0 (needing three total phases) calls `arriveAndAwaitAdvance()` instead, since it has one more phase remaining.
6. In phase 2, only agent 0 and `main` remain registered; agent 0 completes its third and final phase and deregisters.
7. `main`'s loop condition now finds `getRegisteredParties() == 1` (just itself), so the loop exits, and `main` calls its own final `arriveAndDeregister()`, cleanly finishing the simulation with no parties left registered.

## 7. Gotchas & takeaways

> **Gotcha:** every `register()` must eventually be matched by an `arriveAndDeregister()` (or the party must keep arriving forever) — a registered party that simply stops calling `arrive()`/`arriveAndAwaitAdvance()` without deregistering leaves the phaser permanently waiting for an arrival that will never come, stalling every other party's `arriveAndAwaitAdvance()` calls indefinitely.

- `Phaser` generalizes `CyclicBarrier` to support a dynamically changing set of participants across phases via `register()`/`arriveAndDeregister()`, at the cost of a more involved API.
- Use `arrive()` when a party wants to signal completion without waiting for others to catch up; use `arriveAndAwaitAdvance()` when it should block until the whole current group has arrived.
- Always deregister a party once it's done participating — a party that neither arrives nor deregisters will stall the phase advance for everyone else forever.
- For a fixed, known number of threads synchronizing across repeated phases, prefer [`CyclicBarrier`](0887-cyclicbarrier.md)'s simpler API — reach for `Phaser` specifically when the participant count genuinely varies between or during phases.
- `phaser.getPhase()` reports the current phase number, useful for logging or diagnostics; `getRegisteredParties()`/`getUnarrivedParties()` let coordinating code (like the `main` thread above) make decisions based on how many parties remain active.
