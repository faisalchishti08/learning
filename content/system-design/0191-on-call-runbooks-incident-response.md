---
card: system-design
gi: 191
slug: on-call-runbooks-incident-response
title: On-call, runbooks & incident response
---

## 1. What it is

**On-call** is a rotation of engineers who are responsible for responding to production alerts outside normal working hours, one person (or small group) at a time. A **runbook** is a written, step-by-step guide for diagnosing and resolving a specific, known type of incident (e.g. "database connection pool exhausted"), so the on-call responder does not have to reconstruct the right response from scratch under pressure at 3 AM. **Incident response** is the overall structured process a team follows once an alert fires: acknowledging it, diagnosing the problem, mitigating it, and later reviewing what happened.

## 2. Why & when

An [SLO-based alert](0190-dashboards-slo-based-alerting.md) firing at 3 AM is only useful if someone actually sees it and knows what to do — on-call rotations ensure a specific person is always responsible for responding, rather than an alert going unnoticed until the next business day. A runbook turns "someone eventually figures out the fix" into "the documented, previously-proven fix is followed immediately," which matters enormously when the responder is unfamiliar with a specific subsystem, or simply tired and stressed. Use a structured incident response process for any production system where downtime has a real cost, and write a runbook for any incident type that has happened more than once, or is likely enough to be worth preparing for in advance.

## 3. Core concept

- **Acknowledge, then triage:** the first response to an alert is acknowledging it (so others know someone is on it) and triaging its severity — not necessarily fixing it immediately, since triage might determine it can wait or needs to be escalated.
- **Runbook lookup:** a well-organized on-call setup links each alert directly to the relevant runbook, so the responder does not have to search for it while already under time pressure.
- **Mitigate first, root-cause later:** the immediate goal during an active incident is restoring service (a mitigation — a rollback, a restart, a failover), not necessarily finding and fixing the true underlying root cause, which can be investigated more carefully afterward without time pressure.
- **Escalation path:** a runbook (and the on-call process generally) should define when and to whom to escalate if the primary responder cannot resolve the issue alone — a defined path, not an ad-hoc decision made mid-incident.
- **Post-incident review (postmortem):** after mitigation, a blameless review documents what happened, why, and what should change (a new runbook, a fix, better alerting) to reduce the chance or impact of recurrence — this is where the actual root cause is typically addressed.

## 4. Diagram

```
   alert fires
        |
        v
   on-call engineer ACKNOWLEDGES (others know someone is responding)
        |
        v
   TRIAGE: how severe? does a runbook exist for this alert?
        |
        v
   runbook found?  --- yes --> follow documented steps -> MITIGATE (restore service first)
        |
        no
        |
        v
   improvise + ESCALATE if needed (defined escalation path, not ad-hoc)
        |
        v
   service restored -> incident marked resolved
        |
        v
   POST-INCIDENT REVIEW (blameless): what happened, why, what changes
        |
        v
   NEW or UPDATED runbook written for next time
```
*Caption: mitigation comes first to restore service quickly; root-cause analysis and process improvement happen afterward, in the calmer post-incident review.*

## 5. Runnable example

**Level 1 — Basic.** An alert triggers on-call acknowledgment and severity triage.

**Level 2 — Runbook lookup and execution.** Follow documented steps for a known alert type; escalate if none exists.

**Level 3 — Track incident state through to resolution and a post-incident review.** Show the full lifecycle from alert to a documented follow-up action.

```java
// IncidentResponseDemo.java
import java.util.*;

public class IncidentResponseDemo {

    enum IncidentState { FIRED, ACKNOWLEDGED, MITIGATING, RESOLVED, REVIEWED }

    static class Runbook {
        final String alertType;
        final List<String> steps;
        Runbook(String alertType, List<String> steps) { this.alertType = alertType; this.steps = steps; }
    }

    static Map<String, Runbook> runbooks = Map.of(
        "db-connection-pool-exhausted", new Runbook("db-connection-pool-exhausted",
            List.of("check current pool utilization", "identify slow/stuck queries holding connections", "restart the affected service instance", "monitor pool utilization for 10 minutes")),
        "high-error-rate-checkout", new Runbook("high-error-rate-checkout",
            List.of("check payments-service dashboard", "roll back the most recent deployment if within the last hour", "verify error rate returns to normal"))
    );

    static class Incident {
        final String alertType;
        IncidentState state = IncidentState.FIRED;
        List<String> log = new ArrayList<>();
        Incident(String alertType) { this.alertType = alertType; }
    }

    // Level 1: acknowledge and triage.
    static void acknowledge(Incident incident) {
        incident.state = IncidentState.ACKNOWLEDGED;
        incident.log.add("acknowledged by on-call engineer");
        System.out.println("  ACKNOWLEDGED: " + incident.alertType);
    }

    // Level 2: look up and follow the runbook, or escalate if none exists.
    static void mitigate(Incident incident) {
        incident.state = IncidentState.MITIGATING;
        Runbook runbook = runbooks.get(incident.alertType);
        if (runbook == null) {
            incident.log.add("NO RUNBOOK FOUND - escalating to secondary on-call");
            System.out.println("  no runbook for \"" + incident.alertType + "\" - ESCALATING");
            return;
        }
        System.out.println("  following runbook for \"" + incident.alertType + "\":");
        for (String step : runbook.steps) {
            incident.log.add("executed step: " + step);
            System.out.println("    - " + step);
        }
    }

    // Level 3: resolve, then hold a post-incident review producing a concrete follow-up action.
    static String resolveAndReview(Incident incident) {
        incident.state = IncidentState.RESOLVED;
        System.out.println("  RESOLVED: " + incident.alertType);
        incident.state = IncidentState.REVIEWED;
        String followUp = runbooks.containsKey(incident.alertType)
            ? "runbook followed successfully - no new runbook needed, minor timing improvement noted"
            : "NEW runbook written for \"" + incident.alertType + "\" based on this incident's ad-hoc resolution";
        incident.log.add("post-incident review complete: " + followUp);
        System.out.println("  POST-INCIDENT REVIEW: " + followUp);
        return followUp;
    }

    public static void main(String[] args) {
        System.out.println("-- incident 1: a KNOWN alert type, with an existing runbook --");
        Incident incident1 = new Incident("db-connection-pool-exhausted");
        acknowledge(incident1);
        mitigate(incident1);
        resolveAndReview(incident1);

        System.out.println("-- incident 2: a NEW, previously unseen alert type, no runbook exists --");
        Incident incident2 = new Incident("unexpected-cache-invalidation-storm");
        acknowledge(incident2);
        mitigate(incident2);
        resolveAndReview(incident2);

        System.out.println("full log for incident 2: " + incident2.log);
    }
}
```

**How to run:** save as `IncidentResponseDemo.java`, then run `java IncidentResponseDemo.java`.

## 6. Walkthrough

1. `acknowledge(incident1)` transitions `incident1.state` from `FIRED` to `ACKNOWLEDGED` and records this in its log — this models the first action any on-call responder takes, before any diagnosis or fix begins.
2. `mitigate(incident1)` looks up `runbooks.get("db-connection-pool-exhausted")`, finds the matching `Runbook`, and iterates its `steps`, printing and logging each one in order — this is the documented, previously-proven response being followed directly, rather than improvised under pressure.
3. `resolveAndReview(incident1)` transitions through `RESOLVED` to `REVIEWED`, and since `runbooks.containsKey(incident1.alertType)` is true, the follow-up message notes the existing runbook worked, with no new one needed — a case where the prior preparation paid off directly.
4. For `incident2`, `mitigate` looks up `runbooks.get("unexpected-cache-invalidation-storm")`, finds no entry (`null`), and takes the escalation branch instead — logging "NO RUNBOOK FOUND - escalating," modeling exactly what should happen when a genuinely new kind of incident occurs.
5. `resolveAndReview(incident2)` finds `runbooks.containsKey(...)` is `false` this time, so the follow-up message specifically calls for writing a *new* runbook based on this incident — closing the loop by turning a previously-undocumented failure mode into future-proofed, prepared knowledge, exactly the mechanism by which an on-call team's runbook library grows over time.

## 7. Gotchas & takeaways

> Gotcha: skipping the post-incident review once an incident is resolved (a common temptation once the pressure is off) means the exact same "new, unseen" incident type in `incident2`'s scenario will likely recur with no runbook still written for it — the review step is what actually converts a stressful, ad-hoc resolution into prepared knowledge for the next time; treat it as a required step, not an optional nice-to-have.

- On-call rotations ensure alerts are actually seen and acted on; runbooks turn a stressful, improvised response into a documented, proven procedure.
- Restoring service (mitigation) takes priority during an active incident; deeper root-cause analysis happens afterward, without time pressure.
- A blameless post-incident review is what actually converts a resolved incident into a new or improved runbook, closing the loop for next time.
- Related concepts: [Dashboards & SLO-based alerting](0190-dashboards-slo-based-alerting.md) (what actually triggers the alert an on-call engineer responds to), [Chaos engineering](0139-chaos-engineering.md) (a proactive way to test runbooks and incident response before a real incident forces it), [Health checks & heartbeats](0132-health-checks-heartbeats.md) (a common signal that first surfaces the problem an incident responds to).
