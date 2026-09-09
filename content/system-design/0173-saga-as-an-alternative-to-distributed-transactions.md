---
card: system-design
gi: 173
slug: saga-as-an-alternative-to-distributed-transactions
title: Saga as an alternative to distributed transactions
---

## 1. What it is

A **saga** breaks a multi-step business operation that spans several services into a sequence of small, independent local transactions, each committed immediately in its own service. If a later step fails, the saga runs **compensating transactions** — explicit undo steps — for every earlier step that already committed, to unwind the work already done. This avoids [2PC's blocking problem](0172-distributed-transactions-2pc-3pc-their-cost.md) entirely, at the cost of giving up strict atomicity: for a window of time, the system genuinely is in a partially-completed state.

## 2. Why & when

2PC guarantees atomicity but requires every participant to hold locks until a coordinator's final decision, which can block indefinitely if the coordinator fails. A saga instead commits each step's own local transaction immediately and independently — no cross-service locks are ever held — and instead prepares an explicit compensating action for every step, to be run only if a later step fails. Use a saga for any multi-step business process spanning multiple services (an order that debits payment, reserves inventory, and schedules shipping) where you would rather accept a temporary, self-correcting inconsistency than pay 2PC's blocking cost.

## 3. Core concept

- **Local transactions, not a global one:** each step commits to its own service's database immediately, using that service's own normal transaction — no cross-service lock is ever held.
- **Compensating transaction per step:** for every forward step (e.g. "reserve inventory"), a corresponding undo step is defined (e.g. "release the inventory reservation") to run if the saga needs to roll back.
- **Forward recovery vs. backward recovery:** on failure, a saga can either retry the failed step until it succeeds (forward recovery) or run compensations for every already-completed step, in reverse order (backward recovery) — most designs use backward recovery for a failure that cannot simply be retried.
- **Orchestration vs. choreography:** an *orchestrated* saga has one central coordinator explicitly calling each step and deciding when to compensate; a *choreographed* saga instead has each service react to events from the previous step and publish its own event when done, with no central coordinator.
- **Idempotent steps are essential:** because a step (or its compensation) might be retried after a timeout, every step and compensation must be safe to run more than once — the same principle as [idempotency keys](0168-idempotency-keys-for-safe-retries.md).

## 4. Diagram

```
   orchestrated saga: "place order"

   step 1: reserve inventory     -> OK (committed locally)
   step 2: charge payment        -> OK (committed locally)
   step 3: schedule shipping     -> FAILS

   saga now runs COMPENSATIONS, in reverse order:
   compensate step 2: refund payment       -> OK
   compensate step 1: release inventory    -> OK

   final state: order marked FAILED, all prior steps' effects undone
```
*Caption: each forward step commits immediately in its own service; a later failure triggers compensations for every already-completed step, undoing them one by one.*

## 5. Runnable example

**Level 1 — Basic.** Run a sequence of local steps, each committing independently.

**Level 2 — Compensation on failure.** When a step fails, run compensating actions for every already-completed step, in reverse order.

**Level 3 — An orchestrator tracking saga state.** Show the saga's overall status (in progress, compensating, failed) as it executes.

```java
// SagaDemo.java
import java.util.*;
import java.util.function.*;

public class SagaDemo {

    static class SagaStep {
        final String name;
        final Supplier<Boolean> action;       // Level 1: the forward step - returns false on failure
        final Runnable compensation;          // Level 2: the undo action for this step
        SagaStep(String name, Supplier<Boolean> action, Runnable compensation) {
            this.name = name; this.action = action; this.compensation = compensation;
        }
    }

    enum SagaStatus { IN_PROGRESS, COMPLETED, COMPENSATING, FAILED }

    // Level 3: the orchestrator runs each step in order, tracking overall status, compensating on failure.
    static SagaStatus runSaga(List<SagaStep> steps) {
        SagaStatus status = SagaStatus.IN_PROGRESS;
        List<SagaStep> completedSteps = new ArrayList<>();

        for (SagaStep step : steps) {
            System.out.println("running step: " + step.name);
            boolean ok = step.action.get();
            if (!ok) {
                System.out.println("step FAILED: " + step.name + " - starting compensation");
                status = SagaStatus.COMPENSATING;
                // Level 2: compensate every already-completed step, in REVERSE order.
                Collections.reverse(completedSteps);
                for (SagaStep completed : completedSteps) {
                    System.out.println("  compensating: " + completed.name);
                    completed.compensation.run();
                }
                return SagaStatus.FAILED;
            }
            completedSteps.add(step);
        }
        return SagaStatus.COMPLETED;
    }

    public static void main(String[] args) {
        // Level 1 & 2: define the forward steps AND their compensations up front.
        SagaStep reserveInventory = new SagaStep(
            "reserve inventory",
            () -> { System.out.println("  inventory reserved"); return true; },
            () -> System.out.println("  inventory reservation RELEASED"));

        SagaStep chargePayment = new SagaStep(
            "charge payment",
            () -> { System.out.println("  payment charged"); return true; },
            () -> System.out.println("  payment REFUNDED"));

        SagaStep scheduleShipping = new SagaStep(
            "schedule shipping",
            () -> { System.out.println("  shipping service UNAVAILABLE - step failed"); return false; }, // simulate failure
            () -> System.out.println("  (no compensation needed - this step never succeeded)"));

        SagaStatus result = runSaga(List.of(reserveInventory, chargePayment, scheduleShipping));
        System.out.println("final saga status: " + result);
    }
}
```

**How to run:** save as `SagaDemo.java`, then run `java SagaDemo.java`.

## 6. Walkthrough

1. `runSaga` iterates the steps in order; `reserveInventory.action.get()` runs, prints "inventory reserved", and returns `true`, so the step is added to `completedSteps` and the loop moves on — this local transaction has already committed, independently, with no cross-service lock held.
2. `chargePayment.action.get()` similarly succeeds, printing "payment charged" and returning `true`; it too is added to `completedSteps`, which now holds `[reserveInventory, chargePayment]` in that order.
3. `scheduleShipping.action.get()` runs and returns `false` (simulating the shipping service being unavailable); the `if (!ok)` branch triggers, setting `status = COMPENSATING` and printing the failure message.
4. `Collections.reverse(completedSteps)` flips the list to `[chargePayment, reserveInventory]`, and the loop calls each one's `compensation.run()` in that reversed order — `chargePayment`'s compensation runs first, printing "payment REFUNDED", followed by `reserveInventory`'s compensation, printing "inventory reservation RELEASED".
5. The method returns `SagaStatus.FAILED`, and critically, `scheduleShipping`'s own compensation is never run at all — since that step's forward action never actually succeeded, there is nothing for it to undo, which is exactly why the compensation loop only ever processes `completedSteps`, not the step that failed itself.

## 7. Gotchas & takeaways

> Gotcha: a compensation is not always a perfect mirror of its forward action — "refund payment" does not un-happen the original charge in the way a database rollback would; the customer may have already seen the charge, and the refund is itself a new, separate operation with its own delay and failure modes. Designing compensations that are genuinely safe and semantically correct for your specific business process is real design work, not a mechanical inversion of the forward steps.

- A saga trades strict cross-service atomicity for independently-committing local transactions plus explicit compensation on failure, avoiding the blocking cost of [2PC](0172-distributed-transactions-2pc-3pc-their-cost.md) entirely.
- Compensations must be defined for every step that can actually succeed, and are only run for steps that already completed — never for the step that failed itself.
- Every step and compensation must be idempotent, since retries (of the step, or of a compensation) are a normal part of running a saga reliably.
- Related concepts: [Distributed transactions (2PC / 3PC) & their cost](0172-distributed-transactions-2pc-3pc-their-cost.md) (the stricter alternative a saga avoids), [Idempotency keys for safe retries](0168-idempotency-keys-for-safe-retries.md) (the mechanism that makes retrying a saga step safe), [Publish-Subscribe](0111-publish-subscribe.md) (the common foundation for a choreographed saga's step-to-step communication).
