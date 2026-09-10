---
card: system-design
gi: 222
slug: disaster-recovery-rpo-rto
title: Disaster recovery (RPO / RTO)
---

## 1. What it is

**Disaster recovery (DR)** is the plan and infrastructure for restoring a system after a major failure — a whole region outage, a corrupted database, a catastrophic bug. Two numbers define how good a DR plan must be: **Recovery Point Objective (RPO)** is how much data loss is acceptable, measured as time ("we can afford to lose up to 5 minutes of writes"). **Recovery Time Objective (RTO)** is how long the system can be down before recovery must complete, also measured as time ("the system must be back up within 30 minutes").

## 2. Why & when

Without explicit RPO and RTO targets, "disaster recovery" is an untested assumption — nobody actually knows how much data would be lost or how long recovery would take until a real disaster forces them to find out, usually at the worst possible time. Setting RPO and RTO numbers up front, based on real business requirements, turns DR from a vague hope into a concrete engineering target you can design for, test, and verify.

Every production system needs explicit RPO/RTO targets, even if the honest answer for a small internal tool is "we can lose a day of data and be down for a day" — the point is that it is a deliberate, known decision, not an accident. Systems with strict targets (an RPO of seconds, an RTO of minutes) require real investment — [multi-region deployment](0221-multi-az-multi-region-deployment.md), frequent backups, and automated, tested failover — proportional to how tight the targets are.

## 3. Core concept

- **RPO (Recovery Point Objective) — how much data can you lose.** If your last backup was 6 hours ago and disaster strikes now, you lose 6 hours of writes — that is your actual RPO given that backup frequency. A tighter RPO requires more frequent backups or continuous replication (see [multi-AZ & multi-region](0221-multi-az-multi-region-deployment.md)'s synchronous vs. asynchronous replication tradeoff).
- **RTO (Recovery Time Objective) — how long can you be down.** This includes every step: detecting the failure, deciding to fail over, actually standing up the replacement (or restoring from backup), and confirming it is healthy before serving traffic. A tighter RTO requires automation — a manual, runbook-driven recovery process cannot reliably hit an RTO measured in minutes.
- **Backup vs. replication as RPO strategies.** Periodic backups (e.g. nightly) give an RPO equal to the backup interval — simple, cheap, but coarse. Continuous replication (as in multi-AZ/multi-region) gives an RPO close to the replication lag — much tighter, at higher infrastructure cost.
- **Warm standby vs. cold standby as RTO strategies.** A **cold standby** (backups exist, but no infrastructure is running) has a long RTO — you must provision everything from scratch. A **warm standby** (a smaller, already-running replica environment) can take over faster. A **hot standby** (a full-scale, already-running replica, as in active-passive [multi-region](0221-multi-az-multi-region-deployment.md)) gives the shortest RTO, at the highest ongoing cost.
- **DR plans must be tested, not just written.** An untested DR plan (a document describing steps nobody has actually executed) routinely fails in a real disaster — steps are missing, assumptions are wrong, or the person who knew the manual step has left the team. Regular DR drills (actually failing over, on a schedule, even when nothing is wrong) are what make a DR plan trustworthy.

## 4. Diagram

```
   Normal operation:  writes flowing continuously
        |
        v
   [DISASTER STRIKES at time T]
        |
        |<------------- RPO ------------->|
        |  (data written in this window     |
        |   is the data you LOSE, based      |
        |   on your backup/replication        |
        |   frequency)                          |
        |                                        |
   last backup/replicated               T (disaster)
   point BEFORE T
                                                    |
                                                    |<--------- RTO --------->|
                                                    |  (time from disaster to  |
                                                    |   system fully recovered  |
                                                    |   and serving traffic     |
                                                    |   again)                    |
                                                    |                              |
                                              detection -> decision -> failover -> verified healthy
```
*Caption: RPO looks backward from the disaster (how much was lost), RTO looks forward from it (how long until recovery). Both are targets you design infrastructure and process to hit — not numbers that emerge automatically.*

## 5. Runnable example

**Level 1 — Basic.** Compute actual RPO from a given backup interval, and compare it against a target.

**Level 2 — Intermediate.** Simulate a disaster and a recovery process with timed steps, computing the actual RTO achieved and comparing it against a target.

**Level 3 — Advanced.** Compare cold, warm, and hot standby strategies for the same disaster scenario, showing the RTO each one actually achieves.

```java
// DisasterRecoveryDemo.java
import java.util.*;

public class DisasterRecoveryDemo {

    // ---------- Level 1: RPO from backup interval ----------
    static void evaluateRpo(String strategyName, int backupIntervalMinutes, int rpoTargetMinutes) {
        // Worst case: disaster strikes right before the next backup - you lose a full interval.
        int actualWorstCaseRpo = backupIntervalMinutes;
        boolean meetsTarget = actualWorstCaseRpo <= rpoTargetMinutes;
        System.out.println("  " + strategyName + ": backup every " + backupIntervalMinutes +
            " min -> worst-case RPO = " + actualWorstCaseRpo + " min (target: " + rpoTargetMinutes +
            " min) -> " + (meetsTarget ? "MEETS target" : "MISSES target"));
    }

    // ---------- Level 2: RTO from a timed recovery process ----------
    record RecoveryStep(String name, int minutes) {}

    static int simulateRecovery(List<RecoveryStep> steps, int rtoTargetMinutes) {
        int totalMinutes = 0;
        System.out.println("  disaster detected at t=0");
        for (RecoveryStep step : steps) {
            totalMinutes += step.minutes();
            System.out.println("    t=" + totalMinutes + " min: " + step.name() + " complete");
        }
        boolean meetsTarget = totalMinutes <= rtoTargetMinutes;
        System.out.println("  total recovery time: " + totalMinutes + " min (target: " + rtoTargetMinutes +
            " min) -> " + (meetsTarget ? "MEETS target" : "MISSES target"));
        return totalMinutes;
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - RPO for different backup strategies, target = 15 min:");
        evaluateRpo("nightly backup", 24 * 60, 15);
        evaluateRpo("hourly backup", 60, 15);
        evaluateRpo("continuous replication (5 min lag)", 5, 15);

        System.out.println("\nLevel 2 - RTO for a cold-standby recovery process, target = 30 min:");
        simulateRecovery(List.of(
            new RecoveryStep("detect the failure (monitoring alert)", 3),
            new RecoveryStep("human decides to declare a disaster", 5),
            new RecoveryStep("provision new infrastructure from scratch", 25),
            new RecoveryStep("restore database from last backup", 15),
            new RecoveryStep("verify system health before routing traffic", 5)
        ), 30);

        System.out.println("\nLevel 3 - compare cold, warm, and hot standby for the SAME disaster:");
        System.out.println("  cold standby (nothing pre-provisioned):");
        int coldRto = simulateRecovery(List.of(
            new RecoveryStep("detect failure", 3),
            new RecoveryStep("provision infrastructure from scratch", 40),
            new RecoveryStep("restore from backup", 20),
            new RecoveryStep("verify health", 5)
        ), 20);

        System.out.println("\n  warm standby (smaller replica already running, needs scale-up):");
        int warmRto = simulateRecovery(List.of(
            new RecoveryStep("detect failure", 3),
            new RecoveryStep("scale up already-running standby", 8),
            new RecoveryStep("switch traffic over", 2),
            new RecoveryStep("verify health", 2)
        ), 20);

        System.out.println("\n  hot standby (full-scale replica already running and serving read traffic):");
        int hotRto = simulateRecovery(List.of(
            new RecoveryStep("detect failure", 2),
            new RecoveryStep("promote standby, switch traffic", 1),
            new RecoveryStep("verify health", 1)
        ), 20);

        System.out.println("\n  summary: cold=" + coldRto + "min, warm=" + warmRto + "min, hot=" + hotRto +
            "min  (against a 20 min target, only warm and hot succeed)");
    }
}
```

**How to run:** `java DisasterRecoveryDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `evaluateRpo("nightly backup", 24*60, 15)` computes the worst-case RPO as simply the backup interval — 1440 minutes — since a disaster right before the next backup loses everything since the last one. Against a 15-minute target, this clearly `"MISSES target"`. `"hourly backup"` (60 minutes) also misses. Only `"continuous replication (5 min lag)"` — the only strategy tighter than the 15-minute target — prints `"MEETS target"`.
2. This shows RPO is not a property you configure directly — it falls directly out of how often you back up or replicate, and hitting a tight RPO target requires choosing a strategy whose interval is actually smaller than the target.
3. **Level 2:** `simulateRecovery` accumulates `totalMinutes` across five sequential steps, printing the running total after each one — this is what a real recovery timeline looks like: detection, decision, infrastructure provisioning, data restore, and health verification, each adding to the total time before the system is back.
4. The cold-standby example totals `3+5+25+15+5 = 53` minutes, which misses the 30-minute target — the printed message says so directly, showing this specific recovery process is not fast enough for that RTO.
5. **Level 3** runs the same kind of simulation three times with progressively less work needed at disaster time. Cold standby (`3+40+20+5 = 68` min) misses a 20-minute target badly, because everything is provisioned from scratch. Warm standby (`3+8+2+2 = 15` min) meets the target, because a smaller replica was already running and only needed scaling up. Hot standby (`2+1+1 = 4` min) easily meets it, because the replica was already running at full scale — recovery is just a traffic switch. The final summary line makes the tradeoff explicit: only the strategies with pre-provisioned standing infrastructure hit the tighter target, at correspondingly higher ongoing cost.

## 7. Gotchas & takeaways

> **Gotcha:** an RPO or RTO target set without considering actual infrastructure cost is just a wish. A business stakeholder asking for "zero data loss, instant recovery" must understand that means synchronous multi-region replication and a hot standby running at full scale, continuously — a real, ongoing cost that needs to be weighed against the actual cost of downtime or data loss.

- Set RPO and RTO from real business impact analysis (what does an hour of downtime, or an hour of lost data, actually cost the business), not from an arbitrary "as fast as possible" instinct.
- Match your backup/replication strategy to your RPO target, and your standby strategy (cold/warm/hot) to your RTO target — Level 1 and Level 3 both show these are direct, computable relationships, not vague aspirations.
- Run DR drills on a schedule — an untested recovery plan is discovered to be wrong, usually with missing steps or wrong assumptions, exactly when you can least afford it: during a real disaster.
- This whole discipline builds directly on [multi-AZ & multi-region deployment](0221-multi-az-multi-region-deployment.md) — the replication mode and standby topology chosen there determine what RPO and RTO are even achievable.
