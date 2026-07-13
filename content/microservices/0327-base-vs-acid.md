---
card: microservices
gi: 327
slug: base-vs-acid
title: "BASE vs ACID"
---

## 1. What it is

**ACID** (Atomicity, Consistency, Isolation, Durability) is the traditional guarantee a single database transaction makes: it fully happens or fully doesn't, the data is always valid, concurrent transactions don't see each other's half-finished work, and once committed it survives crashes. **BASE** (Basically Available, Soft state, Eventually consistent) is the looser guarantee that distributed microservices systems typically operate under instead: the system stays available even under partial failure, the data can be in a temporary, evolving ("soft") state, and it converges to correctness eventually rather than instantly. BASE is not a step-by-step protocol like [2PC](0319-two-phase-commit-2pc-overview-drawbacks.md) or a specific technique like [sagas](0320-saga-pattern.md) — it is the *name for the tradeoff* that patterns like sagas and [eventual consistency](0326-eventual-consistency.md) are built around.

## 2. Why & when

A single database can offer ACID because it fully controls all the data in one place. The moment data is split across independently deployed services, guaranteeing full ACID across all of them requires coordinating locks across the network (2PC) — which, as covered in [why 2PC/XA is avoided in microservices](0318-why-2pc-xa-is-avoided-in-microservices.md), sacrifices availability whenever any one participant is slow or down. BASE is the deliberate acknowledgment that, in a distributed system, you generally cannot have both full ACID guarantees *and* every service staying independently available — you must choose which one to relax, and microservices architectures overwhelmingly choose to relax consistency (accepting BASE) in order to keep availability.

Keep ACID guarantees inside each individual service's own database — a single service's local writes should still be atomic, consistent, isolated, and durable. Adopt BASE for anything that spans services: sagas, event-driven replication, CQRS read models. The choice isn't "ACID is old and BASE is modern" — it's a genuine tradeoff, and some operations (anything involving real money movement across systems, for instance) may still justify the cost of stronger cross-service coordination in specific, narrow cases.

## 3. Core concept

Think of it as a spectrum of one core tradeoff — consistency versus availability under network partition (this is exactly the C and A of the CAP theorem). ACID leans toward consistency: correctness is guaranteed at every instant, at the cost of blocking (or refusing) operations when full coordination isn't possible. BASE leans toward availability: the system keeps serving requests even when parts of it can't currently agree on the latest state, at the cost of temporarily allowing observably inconsistent or stale data.

```java
// ACID-style: one transaction, one database, atomic and immediately consistent.
// BASE-style: independent local commits + eventual convergence via events/sagas.
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two columns comparing ACID (single database, locks held, strongly consistent, can block) against BASE (multiple services, no cross-service locks, eventually consistent, stays available)">
  <rect x="30" y="20" width="270" height="150" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="165" y="45" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">ACID</text>
  <text x="165" y="68" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Single database</text>
  <text x="165" y="86" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Locks held until commit</text>
  <text x="165" y="104" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Immediately consistent</text>
  <text x="165" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Can block / refuse under partition</text>
  <text x="165" y="150" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">favors CONSISTENCY</text>

  <rect x="340" y="20" width="270" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="475" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">BASE</text>
  <text x="475" y="68" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Multiple independent services</text>
  <text x="475" y="86" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">No cross-service locks</text>
  <text x="475" y="104" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Eventually consistent</text>
  <text x="475" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Stays available under partition</text>
  <text x="475" y="150" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">favors AVAILABILITY</text>
</svg>

ACID and BASE sit on opposite ends of the same consistency-versus-availability tradeoff; microservices generally choose the BASE side across service boundaries.

## 5. Runnable example

Scenario: a "transfer credit between two customer wallets" operation, first implemented ACID-style inside one database, then split across two services and shown blocking under partition when forced to stay ACID, and finally rebuilt BASE-style as a saga that stays available at the cost of a temporary inconsistent window.

### Level 1 — Basic

```java
// File: AcidSingleDatabaseTransfer.java -- one database, one atomic
// transaction: both balances change together or neither does.
import java.util.*;

public class AcidSingleDatabaseTransfer {
    static Map<String, Double> balances = new HashMap<>(); // ONE database -- both wallets live here

    static boolean transfer(String from, String to, double amount) { // simulates ONE atomic transaction
        if (balances.get(from) < amount) { System.out.println("ACID: insufficient funds, transaction ABORTED, nothing changed"); return false; }
        balances.put(from, balances.get(from) - amount); // both changes happen "at once", inside one commit
        balances.put(to, balances.get(to) + amount);
        System.out.println("ACID: transfer committed atomically -- both balances updated together");
        return true;
    }

    public static void main(String[] args) {
        balances.put("alice", 100.0);
        balances.put("bob", 20.0);

        transfer("alice", "bob", 30.0);
        System.out.println("Balances: " + balances + " -- consistent at EVERY instant, no observer could ever see a half-done transfer.");
    }
}
```

How to run: `java AcidSingleDatabaseTransfer.java`

Both balance changes happen inside the same in-memory operation, standing in for a single database transaction — no other code, in this simplified model, could ever observe a state where Alice's balance decreased but Bob's hadn't yet increased. This is the ACID ideal: instantaneous, all-or-nothing, always consistent.

### Level 2 — Intermediate

```java
// File: AcidAcrossServicesBlocks.java -- the SAME transfer, but the two
// wallets are now in TWO SEPARATE services; forcing ACID-style atomicity
// across them means BLOCKING (refusing) the whole operation the moment
// one participant can't be reached -- the availability cost of ACID
// across a network.
public class AcidAcrossServicesBlocks {
    static double aliceBalance = 100.0;
    static double bobBalance = 20.0;
    static boolean bobServiceReachable = false; // simulating a network partition / outage

    static boolean tryAcidTransfer(double amount) {
        System.out.println("coordinator: checking BOTH services are reachable before committing anything (2PC-style)...");
        if (!bobServiceReachable) {
            System.out.println("coordinator: bob-service UNREACHABLE -- to preserve ACID, the ENTIRE transfer is REFUSED, even though alice-service is fine.");
            return false; // ACID discipline forces refusing the WHOLE operation
        }
        aliceBalance -= amount; bobBalance += amount;
        return true;
    }

    public static void main(String[] args) {
        boolean success = tryAcidTransfer(30.0);
        System.out.println("Transfer succeeded? " + success + " -- alice's balance UNCHANGED at " + aliceBalance
                + " even though alice-service itself was perfectly healthy, purely because bob-service was down.");
    }
}
```

How to run: `java AcidAcrossServicesBlocks.java`

`tryAcidTransfer` insists on confirming both services before touching either balance, matching the 2PC "prepare" discipline that real cross-service ACID would require. Because `bobServiceReachable` is `false`, the entire operation is refused — Alice's perfectly healthy service is denied service purely because a *different* service, involved in the same strict transaction, is unreachable. This is the availability cost that comes from insisting on ACID across a service boundary.

### Level 3 — Advanced

```java
// File: BaseSagaStaysAvailable.java -- the SAME scenario, rebuilt BASE-style
// as a saga: alice-service commits its own step IMMEDIATELY regardless of
// bob-service's reachability; the system stays AVAILABLE, accepting a
// temporary inconsistent window, and reconciles once bob-service recovers.
import java.util.*;

public class BaseSagaStaysAvailable {
    static double aliceBalance = 100.0;
    static double bobBalance = 20.0;
    static boolean bobServiceReachable = false;
    static Queue<Double> pendingCredits = new LinkedList<>(); // BASE: "soft state" -- work not yet applied, but tracked

    static void debitAlice(double amount) {
        aliceBalance -= amount; // commits its OWN local step immediately -- does NOT wait for bob-service
        pendingCredits.add(amount);
        System.out.println("alice-service: debited " + amount + " immediately and independently. New balance: " + aliceBalance);
        System.out.println("system remains AVAILABLE -- alice's request succeeds even though bob-service is currently down.");
    }

    static void tryApplyPendingCredits() { // runs later, e.g. on a retry loop, once bob-service recovers
        if (!bobServiceReachable) {
            System.out.println("bob-service still unreachable -- " + pendingCredits.size() + " credit(s) remain PENDING (soft state).");
            return;
        }
        while (!pendingCredits.isEmpty()) {
            double amount = pendingCredits.poll();
            bobBalance += amount;
            System.out.println("bob-service: applied pending credit of " + amount + ". New balance: " + bobBalance);
        }
    }

    public static void main(String[] args) {
        debitAlice(30.0);
        System.out.println("--- money is temporarily 'in flight': debited from alice, not yet credited to bob ---");

        tryApplyPendingCredits(); // still down -- credit stays pending

        System.out.println("--- bob-service recovers ---");
        bobServiceReachable = true;
        tryApplyPendingCredits(); // now succeeds, system converges

        System.out.println("Final: alice=" + aliceBalance + ", bob=" + bobBalance + " -- EVENTUALLY consistent, and the system never refused alice's request.");
    }
}
```

How to run: `java BaseSagaStaysAvailable.java`

`debitAlice` commits its own local change instantly and queues the corresponding credit, without ever checking whether bob-service is reachable — this is "basically available": alice's request succeeds regardless of the other service's health. `tryApplyPendingCredits` is called once while bob-service is still down (it correctly reports the credit as pending, unresolved "soft state") and again after `bobServiceReachable` is flipped to `true`, at which point it drains the queue and applies the credit — the system converges to the correct final balances, but only after a real, observable window during which the money was debited from Alice and not yet credited to Bob.

## 6. Walkthrough

Trace `BaseSagaStaysAvailable.main` in order. **First**, `debitAlice(30.0)` runs: it immediately subtracts `30.0` from `aliceBalance` (now `70.0`) and adds `30.0` to `pendingCredits` — this commit is entirely local to alice-service and does not check `bobServiceReachable` at all, which is why the request succeeds instantly regardless of bob-service's state.

**Next**, `tryApplyPendingCredits()` is called while `bobServiceReachable` is still `false`. Inside, the `if (!bobServiceReachable)` branch fires, printing that the one queued credit remains pending — `bobBalance` is untouched and `pendingCredits` still holds the `30.0` entry.

**Then**, `main` sets `bobServiceReachable = true`, simulating the previously-down service recovering, and calls `tryApplyPendingCredits()` again. This time the `if` guard is false, so the `while` loop runs: it polls the one pending credit, adds `30.0` to `bobBalance` (now `50.0`), and prints the update; the loop then finds `pendingCredits` empty and exits.

**Finally**, `main` prints the final balances: `alice=70.0, bob=50.0` — correctly summing to the same total as the original `100.0 + 20.0 = 120.0`, but only reached after passing through an intermediate state (`alice=70.0, bob=20.0`, totaling `90.0`, with `30.0` "in flight") that any observer querying bob-service during that window would have seen as genuinely, if temporarily, inconsistent.

```
debitAlice(30)              -> alice=70 (immediate, LOCAL commit) | pendingCredits=[30]
tryApplyPendingCredits()    -> bob DOWN -> still pending, bob=20 (STALE relative to the full transfer)
[bob-service recovers]
tryApplyPendingCredits()    -> bob UP -> credit applied -> bob=50, pendingCredits=[]
Final: alice=70, bob=50  (sums correctly; got there via BASE, not ACID)
```

## 7. Gotchas & takeaways

> BASE is not "no guarantees" — it is a different, weaker but still well-defined guarantee (eventual convergence, given no further writes) traded deliberately for availability. A system with no plan for how or when convergence happens (no retry loop, no reconciliation job) isn't practicing BASE; it's just broken.

- ACID guarantees instantaneous, all-or-nothing correctness but requires cross-participant coordination (locks) that hurts availability when spread across services.
- BASE keeps every service available even under partial failure, accepting a real, observable window of temporary inconsistency that resolves once all steps eventually complete.
- Keep ACID inside each service's own database; adopt BASE for anything that spans service boundaries, via patterns like [sagas](0320-saga-pattern.md) and [eventual consistency](0326-eventual-consistency.md).
- This is the same underlying tradeoff described by the CAP theorem: under a network partition, you can favor consistency or availability, but generally not both at once.
