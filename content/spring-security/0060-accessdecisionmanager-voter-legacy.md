---
card: spring-security
gi: 60
slug: accessdecisionmanager-voter-legacy
title: "AccessDecisionManager / Voter (legacy)"
---

## 1. What it is

`AccessDecisionManager` was the pre-`AuthorizationManager` mechanism for authorization decisions, built around a list of `AccessDecisionVoter`s (`RoleVoter`, `AuthenticatedVoter`, `WebExpressionVoter`, and any custom voters) each independently returning `ACCESS_GRANTED`, `ACCESS_DENIED`, or `ACCESS_ABSTAIN` for a given check, combined by a configurable strategy (`AffirmativeBased` — one grant is enough; `UnanimousBased` — no voter may deny; `ConsensusBased` — majority rules) into a single final decision. It is now superseded by the simpler `AuthorizationManager` design (covered two cards back), but remains relevant for understanding legacy code and the underlying concepts `AuthorizationManager` streamlined.

```java
public interface AccessDecisionVoter<S> {
    int ACCESS_GRANTED = 1;
    int ACCESS_ABSTAIN = 0;
    int ACCESS_DENIED = -1;
    int vote(Authentication authentication, S object, Collection<ConfigAttribute> attributes);
}

// AffirmativeBased strategy: the FIRST voter to return ACCESS_GRANTED wins; ACCESS_DENIED from EVEN ONE voter... 
// actually denies IMMEDIATELY; ABSTAIN votes are simply skipped
```

## 2. Why & when

Combining several independent access checks (a role check, an IP check, a custom business rule) into one final yes/no decision requires some strategy for what happens when they disagree — one voter grants, another abstains, a third denies — and `AccessDecisionManager`'s three built-in strategies (affirmative, unanimous, consensus) each answer that disagreement question differently. This flexibility, however, came at the cost of real complexity: understanding a given access decision required tracing through however many voters were registered, in whatever order, combined by whichever strategy was configured — complexity `AuthorizationManager`'s single-method, single-decision design (from two cards back) deliberately eliminated, since the overwhelming majority of real applications never actually needed the full generality of multiple independently-voting components.

Reach for understanding `AccessDecisionManager`/`AccessDecisionVoter` when:

- Maintaining or migrating legacy code still using this API directly — recognizing that a custom `AccessDecisionVoter`'s logic maps onto a single custom `AuthorizationManager` implementation (from the earlier card) is the key insight for a clean migration.
- Understanding older Spring Security documentation, tutorials, or Stack Overflow answers that predate the `AuthorizationManager` design — much existing material still references voters and decision managers directly.
- Never reach for this API in new code — `AuthorizationManager` and its composition helpers (`AuthorizationManagers.allOf`/`anyOf`, from the earlier card) are the current, recommended replacement for every use case this older API addressed.

## 3. Core concept

```
 AffirmativeBased (Spring Security's HISTORICAL DEFAULT strategy):
   for each voter, in order:
     ACCESS_GRANTED -> IMMEDIATELY GRANT overall access, stop checking further voters
     ACCESS_DENIED  -> remember this denial, but KEEP CHECKING remaining voters (a LATER grant can still win!)
     ACCESS_ABSTAIN -> ignore, move to the next voter
   if NO voter granted: DENY overall (using whatever denial was recorded, or a generic one if none)

 UnanimousBased:
   ANY voter returning ACCESS_DENIED -> IMMEDIATELY DENY overall, no further voters checked
   otherwise (all GRANTED or ABSTAIN): GRANT

 ConsensusBased:
   count GRANTED votes vs DENIED votes (ABSTAIN votes don't count toward either)
   MORE granted than denied -> GRANT; more denied than granted -> DENY; TIE -> configurable default
```

Three genuinely different ways the exact same set of voter votes could be combined into a completely different final outcome.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three voters cast independent votes granted denied and abstain for the same access check AffirmativeBased UnanimousBased and ConsensusBased strategies each combine the identical three votes into a potentially different final decision">
  <rect x="15" y="20" width="130" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="80" y="41" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">voter 1: GRANTED</text>

  <rect x="15" y="65" width="130" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="80" y="86" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">voter 2: DENIED</text>

  <rect x="15" y="110" width="130" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="80" y="131" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">voter 3: ABSTAIN</text>

  <rect x="230" y="10" width="150" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="305" y="31" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">AffirmativeBased: GRANT</text>

  <rect x="230" y="75" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="305" y="96" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">UnanimousBased: DENY</text>

  <rect x="230" y="140" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="305" y="161" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">ConsensusBased: TIE (1-1)</text>

  <defs><marker id="a60" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="145" y1="37" x2="230" y2="27" stroke="#8b949e" stroke-width="1" marker-end="url(#a60)"/>
  <line x1="145" y1="82" x2="230" y2="92" stroke="#8b949e" stroke-width="1" marker-end="url(#a60)"/>
  <line x1="145" y1="127" x2="230" y2="157" stroke="#8b949e" stroke-width="1" marker-end="url(#a60)"/>
</svg>

Identical three votes; three different final outcomes, purely depending on the combination strategy chosen.

## 5. Runnable example

The scenario: implement all three combination strategies against the identical set of voter votes, proving they genuinely disagree on the outcome, then map a legacy custom voter's logic onto its modern `AuthorizationManager` equivalent, demonstrating the migration path.

### Level 1 — Basic

The `AffirmativeBased` strategy implemented faithfully, including its "keep checking after a denial" behavior.

```java
import java.util.*;

public class AccessDecisionLegacyLevel1 {
    enum Vote { GRANTED, DENIED, ABSTAIN }
    interface Voter { Vote vote(); }

    static boolean affirmativeBased(List<Voter> voters) {
        boolean anyDenied = false;
        for (Voter voter : voters) {
            Vote v = voter.vote();
            if (v == Vote.GRANTED) return true; // IMMEDIATE grant -- stops checking further voters
            if (v == Vote.DENIED) anyDenied = true; // remembered, but does NOT stop the loop
            // ABSTAIN: simply ignored, loop continues
        }
        return false; // no GRANTED vote was ever found -- overall DENIED
    }

    public static void main(String[] args) {
        List<Voter> votersDenyThenGrant = List.of(
                () -> Vote.DENIED,   // voter 1 denies
                () -> Vote.GRANTED   // voter 2 grants -- and STILL wins overall!
        );
        System.out.println("deny-then-grant, AffirmativeBased: " + affirmativeBased(votersDenyThenGrant));

        List<Voter> allAbstain = List.of(() -> Vote.ABSTAIN, () -> Vote.ABSTAIN);
        System.out.println("all abstain, AffirmativeBased: " + affirmativeBased(allAbstain));
    }
}
```

How to run: `java AccessDecisionLegacyLevel1.java`

Even though the first voter in `votersDenyThenGrant` explicitly denies, the second voter's grant still wins overall under `AffirmativeBased` — a single `DENIED` vote is never immediately fatal under this strategy, which surprises many people encountering it for the first time; with all voters abstaining, no grant is ever found, so the overall result defaults to `false`.

### Level 2 — Intermediate

Implement `UnanimousBased` and `ConsensusBased` against the identical voter set, proving all three strategies genuinely disagree.

```java
import java.util.*;

public class AccessDecisionLegacyLevel2 {
    enum Vote { GRANTED, DENIED, ABSTAIN }
    interface Voter { Vote vote(); }

    static boolean affirmativeBased(List<Voter> voters) {
        for (Voter voter : voters) {
            Vote v = voter.vote();
            if (v == Vote.GRANTED) return true;
        }
        return false;
    }

    static boolean unanimousBased(List<Voter> voters) {
        for (Voter voter : voters) {
            if (voter.vote() == Vote.DENIED) return false; // ANY denial -> IMMEDIATE overall denial
        }
        return true;
    }

    static boolean consensusBased(List<Voter> voters) {
        long granted = voters.stream().filter(v -> v.vote() == Vote.GRANTED).count();
        long denied = voters.stream().filter(v -> v.vote() == Vote.DENIED).count();
        return granted > denied; // TIES default to false here, for concreteness
    }

    public static void main(String[] args) {
        List<Voter> voters = List.of(
                () -> Vote.GRANTED,  // one voter grants
                () -> Vote.DENIED,   // one voter denies
                () -> Vote.ABSTAIN   // one voter abstains
        );

        System.out.println("AffirmativeBased: " + affirmativeBased(voters) + "  (first GRANTED wins)");
        System.out.println("UnanimousBased:   " + unanimousBased(voters) + "  (the single DENIED sinks it)");
        System.out.println("ConsensusBased:   " + consensusBased(voters) + "  (1 granted vs 1 denied -- TIE, defaults false)");
    }
}
```

How to run: `java AccessDecisionLegacyLevel2.java`

The *exact same* three votes (one grant, one deny, one abstain) produce three *different* final outcomes: `AffirmativeBased` grants (the grant vote is enough), `UnanimousBased` denies (the single deny vote is fatal), and `ConsensusBased` ties and defaults to deny — concretely demonstrating why understanding which strategy is configured is essential to correctly predicting the outcome of any given voter combination.

### Level 3 — Advanced

Map a legacy custom voter directly onto its modern `AuthorizationManager` equivalent, demonstrating the migration path this section's earlier `AuthorizationManager` card sets up.

```java
import java.util.*;
import java.util.function.Supplier;

public class AccessDecisionLegacyLevel3 {
    record Authentication(Set<String> authorities) {}

    // LEGACY STYLE: a custom AccessDecisionVoter
    enum Vote { GRANTED, DENIED, ABSTAIN }
    static class BusinessHoursVoter {
        int vote(Authentication auth, String requiredRole, boolean withinBusinessHours) {
            if (!withinBusinessHours) return -1; // ACCESS_DENIED, using the interface's own int constants
            if (auth.authorities().contains("ROLE_" + requiredRole)) return 1; // ACCESS_GRANTED
            return 0; // ACCESS_ABSTAIN -- this voter has no opinion on missing roles, only on business hours
        }
    }

    // MODERN EQUIVALENT: the SAME logic, expressed as a single AuthorizationManager
    record AuthorizationDecision(boolean granted) {}
    interface AuthorizationManager { AuthorizationDecision check(Supplier<Authentication> auth, boolean withinBusinessHours, String requiredRole); }

    static AuthorizationManager businessHoursAuthorizationManager = (authSupplier, withinBusinessHours, requiredRole) -> {
        if (!withinBusinessHours) return new AuthorizationDecision(false);
        return new AuthorizationDecision(authSupplier.get().authorities().contains("ROLE_" + requiredRole));
    };

    public static void main(String[] args) {
        Authentication admin = new Authentication(Set.of("ROLE_ADMIN"));

        BusinessHoursVoter legacyVoter = new BusinessHoursVoter();
        System.out.println("legacy voter, within hours: " + legacyVoter.vote(admin, "ADMIN", true) + " (1 = GRANTED)");
        System.out.println("legacy voter, outside hours: " + legacyVoter.vote(admin, "ADMIN", false) + " (-1 = DENIED)");

        System.out.println("modern manager, within hours: "
                + businessHoursAuthorizationManager.check(() -> admin, true, "ADMIN"));
        System.out.println("modern manager, outside hours: "
                + businessHoursAuthorizationManager.check(() -> admin, false, "ADMIN"));
    }
}
```

How to run: `java AccessDecisionLegacyLevel3.java`

Both the legacy voter and the modern manager produce equivalent decisions for the identical inputs — within business hours, admin's role check passes and access is granted; outside business hours, both immediately deny regardless of role — the migration is a direct, one-to-one translation of the same underlying logic from the old three-way-vote-returning method into the new boolean-decision-returning method.

## 6. Walkthrough

Trace `affirmativeBased(votersDenyThenGrant)` from Level 1.

1. The `for` loop begins with the first voter: `voter.vote()` calls the lambda `() -> Vote.DENIED`, returning `Vote.DENIED`.
2. `if (v == Vote.GRANTED) return true;` checks whether this vote is `GRANTED` — it is not (it's `DENIED`), so this line does not return; the loop simply continues to the next iteration, without recording the denial anywhere in this particular simplified implementation (Level 1 doesn't track `anyDenied` at all in its final printed logic path, since the method returns as soon as a grant is found regardless).
3. The loop proceeds to the second voter: `voter.vote()` calls `() -> Vote.GRANTED`, returning `Vote.GRANTED`.
4. `if (v == Vote.GRANTED) return true;` now matches, so the method returns `true` immediately — the loop never needed to consider anything beyond this second voter, and the earlier `DENIED` vote from the first voter had no lasting effect on the final outcome at all.
5. This is precisely the behavior that often surprises developers encountering `AffirmativeBased` for the first time: a `DENIED` vote is not itself sufficient to deny access — it only contributes to a denial if *no* voter anywhere in the list ever grants; a single `GRANTED` vote, appearing anywhere in the list, overrides any number of preceding denials.

```
voter 1: DENIED  -> not GRANTED, loop continues (denial itself has NO immediate effect)
voter 2: GRANTED -> return true IMMEDIATELY

final result: GRANTED overall, DESPITE voter 1's denial
```

## 7. Gotchas & takeaways

> **Gotcha:** `AffirmativeBased`'s "any grant wins, even after a denial" behavior is a common source of confusion and misconfigured security policies for anyone assuming voters behave like a simple majority vote or a unanimous requirement — always confirm which strategy is actually configured before reasoning about what a set of voters will collectively decide, since the three strategies can produce genuinely opposite results for the identical set of votes.

- `AccessDecisionManager`/`AccessDecisionVoter` is the legacy, more complex predecessor to `AuthorizationManager`, combining multiple independent three-way votes (grant/deny/abstain) via a configurable strategy rather than a single, simpler yes/no decision.
- The three built-in strategies (`AffirmativeBased`, `UnanimousBased`, `ConsensusBased`) can produce genuinely different final outcomes from the identical set of underlying votes — understanding which is configured is essential to correctly predicting a decision's outcome.
- A custom `AccessDecisionVoter`'s logic maps directly onto a single custom `AuthorizationManager` implementation, making migration from the legacy API to the modern one a straightforward, mechanical translation in most cases.
- New applications should use `AuthorizationManager` exclusively — this legacy API is documented here purely to support understanding and migrating existing code, not as a recommendation for new development.
