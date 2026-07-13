---
card: microservices
gi: 319
slug: two-phase-commit-2pc-overview-drawbacks
title: "Two-phase commit (2PC) overview & drawbacks"
---

## 1. What it is

**Two-phase commit (2PC)** is a protocol that lets a **coordinator** get multiple independent databases to agree on committing or rolling back the same logical transaction, as one atomic unit. It runs in exactly two phases: a **prepare (voting) phase**, where every participant locks its affected rows and votes yes or no, and a **commit (decision) phase**, where the coordinator tells everyone the final outcome based on those votes.

## 2. Why & when

2PC exists because a transaction that spans multiple databases has no built-in way to be atomic — each database can only guarantee atomicity for its own local writes. 2PC bolts atomicity on top by adding a coordination layer: nobody actually commits until every participant has confirmed it is *able* to commit, which prevents the classic failure of "database A committed but database B failed," which would leave the overall business operation half-done.

Use 2PC only when every participant supports the XA protocol (or an equivalent two-phase interface), when the number of participants and their round-trip latency are both small, and when temporarily blocking each participant's affected rows for the duration of the protocol is genuinely acceptable. In practice this describes tightly-controlled, low-latency, same-datacenter systems — not independently deployed microservices talking over an internet-scale network, which is why [2PC/XA is generally avoided in microservices](0318-why-2pc-xa-is-avoided-in-microservices.md) in favor of the [saga pattern](0320-saga-pattern.md).

## 3. Core concept

**Phase 1 (prepare):** the coordinator sends a `prepare` message to every participant. Each participant does everything needed to guarantee it *can* commit — validates the operation, writes to a durable log, and locks the affected rows — then replies `yes` (ready) or `no` (cannot proceed). **Phase 2 (commit/rollback):** if every participant voted `yes`, the coordinator sends `commit` to all of them, and each one finalizes its change and releases its locks; if any participant voted `no`, the coordinator sends `rollback` to all of them instead, and every participant undoes its prepared change and releases its locks. Crucially, no participant's locks are released until phase 2 completes — that lock-holding window is the protocol's central cost.

```java
enum Vote { YES, NO }
interface Participant {
    Vote prepare();  // locks resources, returns a vote
    void commit();    // called on EVERY participant only if ALL voted YES
    void rollback();  // called on EVERY participant if ANY voted NO
}
```

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Coordinator sends prepare to two participants who vote; if both vote yes the coordinator sends commit to both, else it sends rollback to both">
  <rect x="250" y="10" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="32" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Coordinator</text>

  <rect x="40" y="90" width="150" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="115" y="112" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Participant A</text>
  <rect x="450" y="90" width="150" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="525" y="112" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Participant B</text>

  <line x1="280" y1="44" x2="150" y2="90" stroke="#8b949e" marker-end="url(#a319)"/>
  <line x1="360" y1="44" x2="500" y2="90" stroke="#8b949e" marker-end="url(#a319)"/>
  <text x="320" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1. PREPARE (lock, vote)</text>

  <line x1="150" y1="124" x2="280" y2="160" stroke="#3fb950" marker-end="url(#a319b)"/>
  <line x1="500" y1="124" x2="360" y2="160" stroke="#3fb950" marker-end="url(#a319b)"/>
  <text x="320" y="185" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">votes: YES, YES -&gt; coordinator sends COMMIT to both</text>

  <defs>
    <marker id="a319" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a319b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Phase 1 collects votes while holding locks; phase 2 broadcasts one shared decision — commit if all voted yes, rollback if any voted no.

## 5. Runnable example

Scenario: a minimal 2PC coordinator over two in-memory participants, first shown succeeding, then extended to correctly roll back both participants when one votes no, and finally hardened to detect the protocol's classic failure — a participant left "in doubt" because the coordinator never delivered its final decision.

### Level 1 — Basic

```java
// File: TwoPhaseCommitBasic.java -- both participants vote yes; coordinator commits both.
import java.util.*;

public class TwoPhaseCommitBasic {
    enum Vote { YES, NO }
    static class Participant {
        String name; boolean locked, committed;
        Participant(String name) { this.name = name; }
        Vote prepare() { locked = true; System.out.println(name + ": prepared, voting YES"); return Vote.YES; }
        void commit() { committed = true; locked = false; System.out.println(name + ": COMMITTED"); }
    }

    public static void main(String[] args) {
        List<Participant> participants = List.of(new Participant("order-service"), new Participant("payment-service"));

        boolean allYes = true;
        for (Participant p : participants) if (p.prepare() != Vote.YES) allYes = false;

        System.out.println("Coordinator decision: " + (allYes ? "COMMIT" : "ROLLBACK"));
        if (allYes) for (Participant p : participants) p.commit();
    }
}
```

How to run: `java TwoPhaseCommitBasic.java`

Both participants vote `YES` during `prepare`, so `allYes` stays `true`, and the coordinator calls `commit()` on each — a clean, uneventful happy path where the protocol behaves exactly as designed.

### Level 2 — Intermediate

```java
// File: TwoPhaseCommitRollback.java -- one participant votes NO; the
// coordinator must roll back EVERY participant, including the ones that
// already voted YES and are holding locks.
import java.util.*;

public class TwoPhaseCommitRollback {
    enum Vote { YES, NO }
    static class Participant {
        String name; boolean locked, committed; boolean voteNo;
        Participant(String name, boolean voteNo) { this.name = name; this.voteNo = voteNo; }
        Vote prepare() {
            locked = true;
            Vote v = voteNo ? Vote.NO : Vote.YES;
            System.out.println(name + ": prepared, voting " + v);
            return v;
        }
        void commit() { committed = true; locked = false; System.out.println(name + ": COMMITTED"); }
        void rollback() { locked = false; System.out.println(name + ": ROLLED BACK, lock released"); }
    }

    public static void main(String[] args) {
        List<Participant> participants = List.of(
                new Participant("order-service", false),
                new Participant("payment-service", true)); // this one will vote NO (e.g. card declined)

        boolean allYes = true;
        for (Participant p : participants) if (p.prepare() != Vote.YES) allYes = false;

        System.out.println("Coordinator decision: " + (allYes ? "COMMIT" : "ROLLBACK"));
        for (Participant p : participants) {
            if (allYes) p.commit(); else p.rollback(); // EVERY participant gets the SAME decision
        }
    }
}
```

How to run: `java TwoPhaseCommitRollback.java`

`order-service` votes `YES` and locks its rows; `payment-service` votes `NO`. Because even one `NO` vote flips `allYes` to `false`, the coordinator's decision is `ROLLBACK` for *everyone* — including `order-service`, which voted `YES` and had done nothing wrong. Its `rollback()` runs, undoing its prepared change and releasing its lock, purely because a different participant refused. This is the essence of atomicity: no partial commits are ever allowed.

### Level 3 — Advanced

```java
// File: TwoPhaseCommitInDoubt.java -- simulates the CLASSIC 2PC failure:
// the coordinator crashes AFTER collecting votes but BEFORE delivering the
// final decision, leaving a participant "in doubt" -- still holding its
// lock, unable to know whether to commit or roll back on its own.
import java.util.*;

public class TwoPhaseCommitInDoubt {
    enum Vote { YES, NO }
    enum Status { LOCKED_WAITING, COMMITTED, ROLLED_BACK }

    static class Participant {
        String name; Status status = Status.LOCKED_WAITING;
        Participant(String name) { this.name = name; }
        Vote prepare() { System.out.println(name + ": prepared, LOCKED, voting YES, awaiting decision"); return Vote.YES; }
        void receiveDecision(boolean commit) {
            status = commit ? Status.COMMITTED : Status.ROLLED_BACK;
            System.out.println(name + ": received decision -- now " + status);
        }
    }

    public static void main(String[] args) {
        Participant orderService = new Participant("order-service");
        Participant paymentService = new Participant("payment-service");

        orderService.prepare();
        paymentService.prepare(); // both voted YES and are now LOCKED, awaiting the coordinator's decision

        System.out.println("--- COORDINATOR CRASHES HERE, before sending the decision to anyone ---");
        // orderService.receiveDecision(...) is simply never called -- simulating the crash

        System.out.println("payment-service DID receive its decision (network got there before the crash):");
        paymentService.receiveDecision(true);

        System.out.println("order-service status: " + orderService.status
                + " -- IN DOUBT: locked indefinitely, no way to know locally whether to commit or roll back.");
    }
}
```

How to run: `java TwoPhaseCommitInDoubt.java`

Both participants prepare and vote `YES`, entering `LOCKED_WAITING`. The coordinator then "crashes" — simulated simply by never calling `orderService.receiveDecision(...)`. `payment-service` happens to have already received its decision (`true`, meaning commit) before the crash, so it correctly transitions to `COMMITTED`. But `order-service` is left permanently in `LOCKED_WAITING`: it has no way to determine, on its own, whether the overall transaction was ultimately committed or rolled back, and its lock stays held until an operator manually intervenes or the coordinator recovers and re-delivers the decision — the exact scenario that makes 2PC risky in systems where coordinators and networks are not perfectly reliable.

## 6. Walkthrough

Trace `TwoPhaseCommitInDoubt.main` in order. **First**, `orderService.prepare()` and `paymentService.prepare()` both run, printing that each has locked its resources and voted `YES`; both participants' `status` fields are `LOCKED_WAITING` at this point.

**Next**, the program prints a line marking the simulated coordinator crash. Critically, `orderService.receiveDecision(...)` is never invoked anywhere in the program — this omission *is* the simulated crash.

**Then**, `paymentService.receiveDecision(true)` is called, representing the lucky case where the network delivered the decision to this one participant before the coordinator died. Inside, `status` is set to `COMMITTED` and this is printed.

**Finally**, `main` prints `orderService.status`, which is still `LOCKED_WAITING` — this participant received a `YES`-vote acknowledgment from itself but never learned the coordinator's final decision, so from its own local perspective it cannot safely release its lock or decide whether to commit or roll back; it is stuck "in doubt" until external intervention.

```
prepare(order) -> YES, LOCKED       prepare(payment) -> YES, LOCKED
              |
              v   COORDINATOR CRASHES (decision never sent to order-service)
payment-service: decision delivered -> COMMITTED
order-service:   decision NEVER delivered -> stuck at LOCKED_WAITING (in doubt)
```

## 7. Gotchas & takeaways

> The "in-doubt" state is 2PC's best-known failure mode: a coordinator crash between collecting votes and broadcasting the decision leaves participants holding locks with no safe way to resolve themselves. Some XA implementations add a recovery protocol for this, but it requires the coordinator to eventually come back and remember what it had decided — an availability risk many teams are unwilling to accept.

- 2PC has exactly two phases: prepare (vote, while locking) and commit/rollback (the coordinator's single shared decision, applied to everyone).
- A single `NO` vote forces every participant to roll back, even ones that voted `YES` and did nothing wrong.
- If the coordinator crashes after collecting votes but before delivering the decision, participants are left "in doubt," holding locks indefinitely.
- These drawbacks are exactly why microservices architectures prefer the [saga pattern](0320-saga-pattern.md), trading strict cross-service atomicity for availability — see [why 2PC/XA is avoided in microservices](0318-why-2pc-xa-is-avoided-in-microservices.md).
