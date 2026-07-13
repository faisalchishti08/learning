---
card: microservices
gi: 322
slug: orchestration-based-saga
title: "Orchestration-based saga"
---

## 1. What it is

An **orchestration-based saga** coordinates a multi-step [saga](0320-saga-pattern.md) using one central component — the **orchestrator** — that explicitly tells each participating service what to do next and decides what compensation to run if a step fails. Unlike a [choreography-based saga](0321-choreography-based-saga.md), where coordination logic is scattered across every participant's event subscriptions, an orchestration-based saga keeps the entire flow — every step and every compensation — in one place: the orchestrator.

## 2. Why & when

As a saga grows past a few steps, [choreography](0321-choreography-based-saga.md) becomes hard to reason about: no single file shows the whole flow, and adding conditional logic ("skip payment if the customer has store credit") means threading that logic through multiple services' event handlers. Orchestration solves this by moving all the flow logic — the sequence of steps, the conditions, and the compensations for each possible failure point — into one orchestrator, which the participating services don't need to know exists; each participant just exposes commands ("reserve stock," "charge payment") and the orchestrator calls them in order.

Use orchestration once a saga has enough steps or enough conditional branching that a reader can no longer hold the whole flow in their head from choreography alone, or once you need centralized visibility into where a given saga instance currently stands (which step it's on, whether it's compensating). The cost is a new component — the orchestrator itself — which becomes a piece of infrastructure that must be built, deployed, and made reliable (its own state needs to survive crashes, since it is now the keeper of "where every in-flight saga currently is").

## 3. Core concept

The orchestrator holds an explicit state machine per saga instance: it knows the ordered list of steps, calls each participant directly (a command, not a broadcast event), waits for that step's result, and on failure walks backward through the compensations for every step that already succeeded — all driven from one piece of code, rather than emergent from independent subscriptions.

```java
class OrderSagaOrchestrator {
    enum Step { PLACE_ORDER, RESERVE_STOCK, CHARGE_PAYMENT, DONE, COMPENSATING, FAILED }
    Step currentStep = Step.PLACE_ORDER;

    void run() { /* explicitly calls each participant in order, tracks currentStep */ }
}
```

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A central orchestrator calls order service, then inventory service, then payment service directly, one at a time, and receives a result back from each before moving to the next">
  <rect x="250" y="10" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="32" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Orchestrator</text>

  <rect x="20" y="90" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order Service</text>
  <rect x="250" y="90" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Inventory Service</text>
  <rect x="480" y="90" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="550" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Payment Service</text>

  <line x1="280" y1="44" x2="110" y2="90" stroke="#8b949e" marker-end="url(#a322)"/>
  <line x1="110" y1="90" x2="280" y2="44" stroke="#8b949e" marker-end="url(#a322)" stroke-dasharray="3,3"/>
  <line x1="320" y1="44" x2="320" y2="90" stroke="#8b949e" marker-end="url(#a322)"/>
  <line x1="360" y1="44" x2="530" y2="90" stroke="#8b949e" marker-end="url(#a322)"/>

  <text x="320" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Orchestrator calls each service directly, ONE AT A TIME, and waits for the result</text>
  <text x="320" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">before deciding the next step -- the WHOLE flow lives in this one component</text>

  <defs><marker id="a322" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The orchestrator directly commands each participant in sequence and centrally decides what happens next, including any compensation.

## 5. Runnable example

Scenario: the same three-step order saga (order, inventory, payment), now driven by an explicit orchestrator that calls each participant directly and tracks saga state — first the happy path, then a failure with centralized compensation, and finally an orchestrator that persists its state so it can resume correctly after a crash mid-saga.

### Level 1 — Basic

```java
// File: OrchestratorHappyPath.java -- one orchestrator calls each
// participant directly, in order, and tracks the saga's current step.
public class OrchestratorHappyPath {
    enum Step { PLACE_ORDER, RESERVE_STOCK, CHARGE_PAYMENT, DONE }

    static boolean placeOrder(String orderId) { System.out.println("order: PLACED " + orderId); return true; }
    static boolean reserveStock(String orderId) { System.out.println("inventory: RESERVED for " + orderId); return true; }
    static boolean chargePayment(String orderId) { System.out.println("payment: CHARGED for " + orderId); return true; }

    public static void main(String[] args) {
        Step currentStep = Step.PLACE_ORDER;
        String orderId = "order-1";

        if (placeOrder(orderId)) currentStep = Step.RESERVE_STOCK;
        if (currentStep == Step.RESERVE_STOCK && reserveStock(orderId)) currentStep = Step.CHARGE_PAYMENT;
        if (currentStep == Step.CHARGE_PAYMENT && chargePayment(orderId)) currentStep = Step.DONE;

        System.out.println("Saga finished at step: " + currentStep);
    }
}
```

How to run: `java OrchestratorHappyPath.java`

The orchestrator (here, just `main`) calls `placeOrder`, `reserveStock`, and `chargePayment` directly, one after another, updating `currentStep` as each succeeds — every participant is called by name, in an explicit sequence the orchestrator controls, rather than each service reacting independently to events it subscribed to.

### Level 2 — Intermediate

```java
// File: OrchestratorWithCompensation.java -- payment step FAILS; the
// orchestrator (not the participants) decides which compensations to run,
// in reverse order, from ONE central place.
import java.util.*;

public class OrchestratorWithCompensation {
    enum Step { PLACE_ORDER, RESERVE_STOCK, CHARGE_PAYMENT, DONE, COMPENSATING, FAILED }

    static boolean placeOrder(String id) { System.out.println("order: PLACED " + id); return true; }
    static boolean reserveStock(String id) { System.out.println("inventory: RESERVED for " + id); return true; }
    static boolean chargePayment(String id) { System.out.println("payment: DECLINED for " + id); return false; }
    static void cancelOrder(String id) { System.out.println("order: CANCELLED " + id + " (compensation)"); }
    static void releaseStock(String id) { System.out.println("inventory: RELEASED for " + id + " (compensation)"); }

    public static void main(String[] args) {
        String orderId = "order-1";
        List<Runnable> compensations = new ArrayList<>();
        Step step = Step.PLACE_ORDER;

        if (placeOrder(orderId)) { compensations.add(() -> cancelOrder(orderId)); step = Step.RESERVE_STOCK; }
        if (step == Step.RESERVE_STOCK && reserveStock(orderId)) { compensations.add(() -> releaseStock(orderId)); step = Step.CHARGE_PAYMENT; }
        if (step == Step.CHARGE_PAYMENT && !chargePayment(orderId)) step = Step.COMPENSATING;

        if (step == Step.COMPENSATING) {
            System.out.println("orchestrator: payment failed -- running compensations in reverse order");
            Collections.reverse(compensations);
            compensations.forEach(Runnable::run);
            step = Step.FAILED;
        }
        System.out.println("Saga finished at step: " + step);
    }
}
```

How to run: `java OrchestratorWithCompensation.java`

The orchestrator, and only the orchestrator, decides that a `false` result from `chargePayment` means moving to `COMPENSATING` and running every registered compensation in reverse — `releaseStock` before `cancelOrder`. Neither `inventory` nor `order` had to know about payment's failure directly; they simply exposed compensation actions, and the orchestrator's central logic decided when to invoke them.

### Level 3 — Advanced

```java
// File: OrchestratorWithPersistedState.java -- the orchestrator persists
// its current step (simulated with a simple map "database") BEFORE each
// call, so if the process crashes mid-saga, it can RESUME from the last
// known step instead of losing track or restarting from scratch.
import java.util.*;

public class OrchestratorWithPersistedState {
    enum Step { PLACE_ORDER, RESERVE_STOCK, CHARGE_PAYMENT, DONE }
    static Map<String, Step> persistedState = new HashMap<>(); // stands in for a real saga-state table

    static boolean placeOrder(String id) { System.out.println("order: PLACED " + id); return true; }
    static boolean reserveStock(String id) { System.out.println("inventory: RESERVED for " + id); return true; }
    static boolean chargePayment(String id) { System.out.println("payment: CHARGED for " + id); return true; }

    static void runStep(String orderId, Step step, Runnable action) {
        persistedState.put(orderId, step); // PERSIST before running, so a crash mid-step can be detected on restart
        action.run();
    }

    static void driveSaga(String orderId, Step resumeFrom) {
        Step current = resumeFrom;
        if (current == Step.PLACE_ORDER) { runStep(orderId, Step.PLACE_ORDER, () -> placeOrder(orderId)); current = Step.RESERVE_STOCK; }
        if (current == Step.RESERVE_STOCK) { runStep(orderId, Step.RESERVE_STOCK, () -> reserveStock(orderId)); current = Step.CHARGE_PAYMENT; }
        if (current == Step.CHARGE_PAYMENT) { runStep(orderId, Step.CHARGE_PAYMENT, () -> chargePayment(orderId)); current = Step.DONE; }
        persistedState.put(orderId, current);
    }

    public static void main(String[] args) {
        String orderId = "order-1";

        System.out.println("--- First process run: starts, then CRASHES after RESERVE_STOCK ---");
        runStep(orderId, Step.PLACE_ORDER, () -> placeOrder(orderId));
        runStep(orderId, Step.RESERVE_STOCK, () -> reserveStock(orderId));
        System.out.println("(process crashes here -- persistedState says: " + persistedState.get(orderId) + ")");

        System.out.println("--- New process starts, reads persisted state, RESUMES from there ---");
        Step resumeFrom = persistedState.get(orderId) == Step.RESERVE_STOCK ? Step.CHARGE_PAYMENT : Step.PLACE_ORDER;
        driveSaga(orderId, resumeFrom); // does NOT re-run placeOrder or reserveStock

        System.out.println("Final persisted state: " + persistedState.get(orderId));
    }
}
```

How to run: `java OrchestratorWithPersistedState.java`

The first simulated process run calls `runStep` for `PLACE_ORDER` and `RESERVE_STOCK`, each of which writes the *current* step into `persistedState` before running its action — this durable write is what lets recovery work. The process is then simulated as crashing (nothing special happens in the code; the point is that no further steps run). A second simulated process reads `persistedState.get(orderId)`, sees `RESERVE_STOCK` was the last completed step, and computes `resumeFrom = CHARGE_PAYMENT` — deliberately skipping `placeOrder` and `reserveStock`, which already succeeded, and continuing only with the step that never ran.

## 6. Walkthrough

Trace `OrchestratorWithPersistedState.main` in order. **First**, `runStep(orderId, Step.PLACE_ORDER, ...)` runs: it writes `persistedState.put(orderId, Step.PLACE_ORDER)` and then executes `placeOrder`, printing that the order was placed.

**Next**, `runStep(orderId, Step.RESERVE_STOCK, ...)` runs the same way: it persists `Step.RESERVE_STOCK` and then executes `reserveStock`. At this point the "crash" is simulated — the program simply prints the persisted state and moves on, standing in for the orchestrator process dying here in a real deployment.

**Then**, a fresh call to `driveSaga` begins, representing a new orchestrator process (or a retry) picking up where the last one left off. It reads `persistedState.get(orderId)`, which is `Step.RESERVE_STOCK`, and computes `resumeFrom = Step.CHARGE_PAYMENT` — the step that comes *after* the last one known to have completed.

**Inside `driveSaga`**, because `resumeFrom` is `Step.CHARGE_PAYMENT`, the `if (current == Step.PLACE_ORDER)` and `if (current == Step.RESERVE_STOCK)` branches are both skipped entirely — `placeOrder` and `reserveStock` are never re-invoked. Only the `if (current == Step.CHARGE_PAYMENT)` branch runs, persisting that step and calling `chargePayment`, after which `current` becomes `Step.DONE` and that final state is persisted.

**Finally**, `main` prints the persisted state, which is `Step.DONE` — the saga completed correctly across two separate "process lifetimes" without re-running any already-completed step.

```
Run 1: PLACE_ORDER (persist+run) -> RESERVE_STOCK (persist+run) -> [CRASH]
Run 2: read persisted=RESERVE_STOCK -> resume at CHARGE_PAYMENT (skip earlier steps) -> DONE
```

## 7. Gotchas & takeaways

> An orchestrator that keeps saga state only in memory is a single point of failure for every in-flight saga: a crash loses track of exactly which step each order was on, and steps can be run twice (or never) on restart. Real orchestrators persist their state (often in their own database) before or after every step, exactly as shown in Level 3.

- The orchestrator centralizes flow logic and compensation decisions in one place, unlike [choreography](0321-choreography-based-saga.md), where this logic is scattered across every participant.
- Participating services expose commands the orchestrator calls directly; they don't need to know a saga or an orchestrator exists.
- The orchestrator itself becomes critical infrastructure — its state must be durably persisted so a crash mid-saga can be recovered from correctly, not just retried from scratch or silently forgotten.
- Choose orchestration over choreography once a saga's step count or conditional complexity makes the flow hard to follow from independent event subscriptions alone.
