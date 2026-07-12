---
card: microservices
gi: 30
slug: team-size-organizational-readiness-two-pizza-teams
title: "Team size & organizational readiness (two-pizza teams)"
---

## 1. What it is

The **two-pizza team** rule, popularized by Amazon, says a team should be small enough to be fed by two pizzas — roughly 6 to 10 people. The idea, applied to microservices, is that each service should ideally be owned by a team small enough to communicate efficiently without heavy process, and large enough to genuinely own its service's full lifecycle (build, test, deploy, operate) without depending on people outside the team for routine work. This is [Conway's Law](0022-conway-s-law-and-its-inverse-maneuver.md) applied directly to sizing: team size and structure should be a deliberate input to your service architecture, not an afterthought.

## 2. Why & when

A team that's too small to own a service's full lifecycle either needs constant help from other teams (recreating cross-team coordination the split was meant to avoid) or accumulates operational debt because there simply aren't enough people to build features *and* maintain reliable deployment, monitoring, and on-call coverage. A team that's too large loses the fast, low-overhead internal communication that makes a single team effective — large teams tend to fracture into sub-groups anyway, at which point the "team" boundary no longer matches the communication structure Conway's Law actually predicts.

Use two-pizza-team sizing as a design input, not just an organizational nicety, when deciding how many services your organization can genuinely support: count the number of full-lifecycle-capable teams you actually have, and treat that as a rough ceiling on how many independently-owned services you can operate well. An organization with three small teams attempting to run twenty separately owned services is setting itself up for services that are technically split but operationally under-resourced.

## 3. Core concept

The sizing question isn't abstract — it's a direct capacity calculation: given a team's size and the operational work one service genuinely requires (feature development, on-call, monitoring, deployment maintenance), how many services can that team responsibly own before quality degrades?

- Too few people per service → overloaded team, services with weak operational health.
- Too many people per team → communication overhead creeps back in, defeating the purpose of a small, focused team.
- Right-sized → each team owns a number of services proportional to its actual capacity to do build-and-run work well.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A right-sized two-pizza team owning two well-run services, versus an undersized team stretched across five services with degraded operational health">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Right-sized</text>
  <rect x="30" y="35" width="100" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Team (8 people)</text>
  <rect x="160" y="35" width="80" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="200" y="55" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Service A</text>
  <rect x="250" y="35" width="80" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="290" y="55" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Service B</text>
  <text x="200" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2 services, well-run</text>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Overstretched</text>
  <rect x="390" y="35" width="90" height="45" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="435" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Team (4 people)</text>
  <g fill="#1c2430" stroke="#f0883e">
    <rect x="490" y="20" width="50" height="22" rx="3"/><rect x="545" y="20" width="50" height="22" rx="3"/>
    <rect x="490" y="47" width="50" height="22" rx="3"/><rect x="545" y="47" width="50" height="22" rx="3"/>
    <rect x="490" y="74" width="50" height="22" rx="3"/>
  </g>
  <text x="540" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">5 services, degraded operations</text>
</svg>

Team capacity should bound the number of services a team genuinely owns well, not just the number an architecture diagram allows.

## 5. Runnable example

Scenario: modeling teams' operational capacity for owning services, first as a naive count, then as a weighted capacity calculation, then applied to flag genuinely overstretched teams.

### Level 1 — Basic

```java
// File: NaiveServiceCount.java -- just counting services per team, no capacity check
import java.util.*;

public class NaiveServiceCount {
    record Team(String name, int memberCount, List<String> ownedServices) { }

    public static void main(String[] args) {
        Team platformTeam = new Team("PlatformTeam", 4, List.of("Auth", "Billing", "Notifications", "Reporting", "Search"));
        System.out.println(platformTeam.name() + " owns " + platformTeam.ownedServices().size() + " services with " + platformTeam.memberCount() + " people");
    }
}
```

**How to run:** `javac NaiveServiceCount.java && java NaiveServiceCount` (JDK 17+).

Expected output:
```
PlatformTeam owns 5 services with 4 people
```

This tells you the raw numbers but not whether they're actually sustainable — five services for four people sounds concerning, but there's no explicit capacity model here to confirm it.

### Level 2 — Intermediate

```java
// File: CapacityModel.java -- a rough capacity model: how many services
// CAN a team of a given size responsibly own?
import java.util.*;

public class CapacityModel {
    record Team(String name, int memberCount, List<String> ownedServices) { }

    static final double SERVICES_PER_PERSON_CAPACITY = 0.5; // a rough rule of thumb: ~1 service per 2 people

    static int capacityFor(int memberCount) {
        return (int) Math.floor(memberCount * SERVICES_PER_PERSON_CAPACITY);
    }

    static boolean isOverstretched(Team team) {
        return team.ownedServices().size() > capacityFor(team.memberCount());
    }

    public static void main(String[] args) {
        Team platformTeam = new Team("PlatformTeam", 4, List.of("Auth", "Billing", "Notifications", "Reporting", "Search"));
        int capacity = capacityFor(platformTeam.memberCount());
        System.out.println(platformTeam.name() + ": capacity=" + capacity + ", actual=" + platformTeam.ownedServices().size() + ", overstretched=" + isOverstretched(platformTeam));
    }
}
```

**How to run:** `javac CapacityModel.java && java CapacityModel` (JDK 17+).

Expected output:
```
PlatformTeam: capacity=2, actual=5, overstretched=true
```

With a rough capacity model (half a service per person, a deliberately conservative rule of thumb), `PlatformTeam`'s 4 people have capacity for about `2` services — but they actually own `5`, flagging them as concretely overstretched, not just "sounds like a lot."

### Level 3 — Advanced

```java
// File: OrganizationWideCheck.java -- run the capacity check across the
// WHOLE organization, and recommend concrete action per team.
import java.util.*;

public class OrganizationWideCheck {
    record Team(String name, int memberCount, List<String> ownedServices) { }

    static final double SERVICES_PER_PERSON_CAPACITY = 0.5;

    static int capacityFor(int memberCount) { return (int) Math.floor(memberCount * SERVICES_PER_PERSON_CAPACITY); }

    static String recommend(Team team) {
        int capacity = capacityFor(team.memberCount());
        int actual = team.ownedServices().size();
        if (actual <= capacity) return "healthy -- capacity for " + capacity + ", owns " + actual;
        int excess = actual - capacity;
        return "OVERSTRETCHED by " + excess + " service(s) -- grow the team, merge some services, or transfer " + excess + " service(s) to another team";
    }

    public static void main(String[] args) {
        List<Team> teams = List.of(
            new Team("PlatformTeam", 4, List.of("Auth", "Billing", "Notifications", "Reporting", "Search")),
            new Team("OrdersTeam", 8, List.of("Orders", "Inventory")),
            new Team("PaymentsTeam", 2, List.of("Payments", "Refunds", "Invoicing"))
        );

        for (Team team : teams) {
            System.out.println(team.name() + ": " + recommend(team));
        }
    }
}
```

**How to run:** `javac OrganizationWideCheck.java && java OrganizationWideCheck` (JDK 17+).

Expected output:
```
PlatformTeam: OVERSTRETCHED by 3 service(s) -- grow the team, merge some services, or transfer 3 service(s) to another team
OrdersTeam: healthy -- capacity for 4, owns 2
PaymentsTeam: OVERSTRETCHED by 2 service(s) -- grow the team, merge some services, or transfer 2 service(s) to another team
```

The production-flavored case: three teams, three genuinely different verdicts, each with a specific, actionable number attached. `OrdersTeam`, right-sized at 8 people for 2 services, is healthy with capacity to spare. `PlatformTeam` and `PaymentsTeam` are both overstretched, each with a concrete count of how many services exceed their capacity — a specific number a manager or architect can act on (grow the team, consolidate services, or redistribute ownership), rather than a vague sense that "things feel stretched."

## 6. Walkthrough

1. `capacityFor(2)` for `PaymentsTeam` computes `Math.floor(2 * 0.5) = 1` — a team of just 2 people has capacity for roughly 1 service under this conservative model.
2. `recommend(paymentsTeam)` computes `capacity = 1` and `actual = 3` (Payments, Refunds, Invoicing). Since `actual > capacity`, it computes `excess = 3 - 1 = 2` and returns the overstretched message naming that exact excess.
3. `capacityFor(8)` for `OrdersTeam` computes `Math.floor(8 * 0.5) = 4`. `recommend(ordersTeam)` finds `actual = 2`, which is `<= capacity (4)`, so it returns the healthy message, explicitly showing the spare capacity (`4` capacity, `2` owned).
4. `capacityFor(4)` for `PlatformTeam` computes `Math.floor(4 * 0.5) = 2`. `recommend(platformTeam)` finds `actual = 5`, computes `excess = 5 - 2 = 3`, and returns the overstretched message.
5. The final loop prints all three teams' verdicts together, making the organization-wide picture visible at once: one healthy team with room to take on more, two overstretched teams with specific, differing amounts of excess load — exactly the kind of concrete input a reorganization or service-consolidation decision needs.

```
PaymentsTeam (2 people):  capacity 1, owns 3 -> overstretched by 2
OrdersTeam   (8 people):  capacity 4, owns 2 -> healthy, room for 2 more
PlatformTeam (4 people):  capacity 2, owns 5 -> overstretched by 3
```

## 7. Gotchas & takeaways

> **Gotcha:** a fixed ratio like "0.5 services per person" is a deliberately rough rule of thumb, not a universal constant — the right capacity depends heavily on each service's actual complexity, traffic, and operational demands. A team of 8 running two extremely high-traffic, complex services can be more stretched than a team of 4 running five simple, low-traffic ones. Use a ratio like this as a starting conversation, not a rigid formula.

- Two-pizza team sizing (roughly 6–10 people) is meant to keep a team small enough to communicate efficiently while large enough to own a service's full lifecycle without constant outside help.
- Team capacity should be a deliberate input to how many services an organization takes on — not an afterthought discovered only once teams are already visibly overstretched.
- A concrete capacity model (services owned versus services a team can responsibly support) turns "this team feels stretched" into an actionable number: grow the team, consolidate services, or redistribute ownership.
- This is [Conway's Law](0022-conway-s-law-and-its-inverse-maneuver.md) applied to sizing: if team structure predicts architecture, then team *capacity* should predict how many independently-owned services that architecture can actually sustain well.
