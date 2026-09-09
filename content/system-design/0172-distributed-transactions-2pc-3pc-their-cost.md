---
card: system-design
gi: 172
slug: distributed-transactions-2pc-3pc-their-cost
title: Distributed transactions (2PC / 3PC) & their cost
---

## 1. What it is

A **distributed transaction** commits or rolls back a change across multiple independent systems (e.g. two different databases, or two microservices) as a single atomic unit — either all of them apply the change, or none of them do. **Two-Phase Commit (2PC)** is the classic protocol for this: a coordinator first asks every participant to *prepare* the change (phase 1), and only if every participant confirms readiness does it tell them all to actually *commit* (phase 2). **Three-Phase Commit (3PC)** adds an extra phase to reduce (but not eliminate) 2PC's biggest weakness: participants getting stuck, blocked, if the coordinator fails at the wrong moment.

## 2. Why & when

A single-database transaction is atomic for free, using the database's own commit log. But updating two *separate* systems atomically — say, debiting an account in one database and crediting a different system in another — cannot rely on either system's own transaction alone, since each only knows about its own state. 2PC provides an all-or-nothing guarantee across multiple systems by having every participant explicitly agree it *can* commit before any of them actually does. Use it only when you truly need strict atomicity across systems and can accept its cost — real production systems increasingly avoid 2PC in favor of a [saga](0173-saga-as-an-alternative-to-distributed-transactions.md), specifically because of the blocking problem covered below.

## 3. Core concept

- **Phase 1 — Prepare:** the coordinator asks every participant "can you commit this change?"; each participant does whatever work is needed to guarantee it *can* commit later (e.g. writing to its own durable log) and replies yes or no, without yet making the change visible.
- **Phase 2 — Commit (or abort):** if every participant said yes, the coordinator tells them all to commit for real; if even one said no (or timed out), the coordinator tells them all to abort instead.
- **The blocking problem:** if the coordinator crashes *after* participants have all said "yes" but *before* it sends the final commit/abort decision, every participant is stuck holding its prepared-but-undecided change, unable to safely commit or abort on its own, until the coordinator recovers.
- **3PC's added phase:** 3PC inserts a "pre-commit" acknowledgment step between prepare and commit, so participants can independently decide to commit if the coordinator disappears after this point — reducing, though not fully eliminating, the blocking window.
- **Cost:** every participant must hold locks (or reserved resources) from the prepare phase until the final decision arrives, which can be a long time under failure — this is real, ongoing resource contention across every involved system, for the whole duration of the transaction.

## 4. Diagram

```
   coordinator                 participant-A (DB1)      participant-B (DB2)
        |-- PREPARE ------------------->|                        |
        |-- PREPARE ---------------------------------------------->|
        |<---------- YES (can commit) --|                        |
        |<---------- YES (can commit) ----------------------------|
        |
        |   (BOTH said yes - safe to commit)
        |
        |-- COMMIT --------------------->|                        |
        |-- COMMIT --------------------------------------------->|
        |<---------- ACK ---------------|                        |
        |<---------- ACK -----------------------------------------|

   FAILURE CASE: coordinator crashes HERE, after both said "yes", before sending COMMIT
        -> participant-A and participant-B are BOTH stuck, holding locks, awaiting a decision
```
*Caption: every participant must agree before any commit happens, but if the coordinator fails right after that agreement, participants are left blocked, unable to decide on their own.*

## 5. Runnable example

**Level 1 — Basic.** A coordinator runs the prepare phase across participants and collects their votes.

**Level 2 — Commit only if every participant voted yes.** Model the all-or-nothing decision.

**Level 3 — Simulate the coordinator crashing between phases.** Show participants left in a blocked, undecided state.

```java
// TwoPhaseCommitDemo.java
import java.util.*;

public class TwoPhaseCommitDemo {

    enum ParticipantState { IDLE, PREPARED, COMMITTED, ABORTED, BLOCKED }

    static class Participant {
        final String name;
        ParticipantState state = ParticipantState.IDLE;
        boolean willVoteYes;
        Participant(String name, boolean willVoteYes) { this.name = name; this.willVoteYes = willVoteYes; }

        // Level 1: phase 1 - can this participant commit? It locks resources in preparation.
        boolean prepare() {
            if (willVoteYes) {
                state = ParticipantState.PREPARED;
                System.out.println("  " + name + ": PREPARED (voted yes, resources locked)");
                return true;
            }
            state = ParticipantState.ABORTED;
            System.out.println("  " + name + ": voted NO");
            return false;
        }

        void commit() { state = ParticipantState.COMMITTED; System.out.println("  " + name + ": COMMITTED"); }
        void abort() { state = ParticipantState.ABORTED; System.out.println("  " + name + ": ABORTED"); }
    }

    // Level 2: run the full 2PC protocol - prepare everyone, then commit or abort based on the votes.
    static void runTwoPhaseCommit(List<Participant> participants, boolean coordinatorCrashesBeforeDecision) {
        System.out.println("PHASE 1: prepare");
        boolean allVotedYes = true;
        for (Participant p : participants) {
            if (!p.prepare()) allVotedYes = false;
        }

        if (!allVotedYes) {
            System.out.println("PHASE 2: at least one NO vote - aborting everyone");
            for (Participant p : participants) if (p.state == ParticipantState.PREPARED) p.abort();
            return;
        }

        // Level 3: simulate the coordinator crashing right after collecting all "yes" votes.
        if (coordinatorCrashesBeforeDecision) {
            System.out.println("COORDINATOR CRASHES before sending the commit decision!");
            for (Participant p : participants) p.state = ParticipantState.BLOCKED;
            return;
        }

        System.out.println("PHASE 2: everyone voted yes - committing everyone");
        for (Participant p : participants) p.commit();
    }

    public static void main(String[] args) {
        System.out.println("=== scenario 1: normal successful commit ===");
        List<Participant> normalRun = List.of(new Participant("DB1", true), new Participant("DB2", true));
        runTwoPhaseCommit(normalRun, false);
        for (Participant p : normalRun) System.out.println(p.name + " final state: " + p.state);

        System.out.println("=== scenario 2: coordinator crashes between phases ===");
        List<Participant> crashRun = List.of(new Participant("DB1", true), new Participant("DB2", true));
        runTwoPhaseCommit(crashRun, true);
        for (Participant p : crashRun) System.out.println(p.name + " final state: " + p.state + " (stuck holding locked resources, awaiting the coordinator's decision)");
    }
}
```

**How to run:** save as `TwoPhaseCommitDemo.java`, then run `java TwoPhaseCommitDemo.java`.

## 6. Walkthrough

1. In scenario 1, `runTwoPhaseCommit` calls `p.prepare()` on both `DB1` and `DB2`; since both were constructed with `willVoteYes = true`, both transition to `PREPARED` and the loop's `allVotedYes` flag stays `true`.
2. With `allVotedYes` true and `coordinatorCrashesBeforeDecision` false, execution reaches the final "PHASE 2: everyone voted yes" branch, calling `commit()` on both participants, transitioning them to `COMMITTED` — the final printed states confirm a clean, successful distributed commit.
3. In scenario 2, both participants again vote yes during phase 1, reaching `PREPARED` exactly as before — from the participants' point of view, nothing about this scenario looks any different yet.
4. This time `coordinatorCrashesBeforeDecision` is `true`, so instead of reaching the commit branch, the method hits the crash-simulation branch, setting both participants' state to `BLOCKED` and returning immediately — no `commit()` or `abort()` is ever called on either participant.
5. The final printed states show both `DB1` and `DB2` stuck at `BLOCKED`, still holding whatever resources they locked during their own `prepare()` call, with no way to know on their own whether they should actually commit or abort — this is exactly the blocking problem: each participant did its part correctly, but the *coordinator's* failure at the critical moment leaves the whole transaction, and every lock it holds, in limbo until the coordinator recovers and tells them what happened.

## 7. Gotchas & takeaways

> Gotcha: the "blocked" participants in scenario 2 are not merely delayed — they typically must hold their locked resources (rows locked, connections reserved) for as long as the coordinator remains unavailable, which can stall unrelated work in the same database that needs those same resources; this real, cascading cost across multiple systems is the central reason many modern architectures avoid 2PC in favor of [sagas](0173-saga-as-an-alternative-to-distributed-transactions.md), even though a saga gives up strict atomicity in exchange.

- 2PC gives strict all-or-nothing atomicity across multiple independent systems, at the cost of every participant locking resources for the full duration of the protocol.
- The blocking problem — participants stuck holding locks if the coordinator crashes between phases — is 2PC's fundamental weakness, and 3PC only partially mitigates it.
- This cost is why 2PC has fallen out of favor for many real distributed systems, despite the theoretical appeal of true atomicity.
- Related concepts: [Saga as an alternative to distributed transactions](0173-saga-as-an-alternative-to-distributed-transactions.md) (the more commonly used alternative), [Consensus (Paxos / Raft) overview](0170-consensus-paxos-raft-overview.md) (a related but distinct coordination problem: agreeing on one ordered log, not atomically committing a single cross-system transaction), [Distributed locks (Redis Redlock / ZooKeeper)](0167-distributed-locks-redis-redlock-zookeeper.md) (the kind of resource a blocked participant is often still holding).
