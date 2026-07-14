---
card: microservices
gi: 495
slug: backward-forward-compatibility
title: "Backward & forward compatibility"
---

## 1. What it is

**Backward compatibility** means a new version of a service can correctly handle requests built against an older contract — old clients keep working against the new server. **Forward compatibility** means an older version of a service (or a consumer) can tolerate messages built against a newer contract without breaking — new fields or values don't crash an old client that's never seen them before. Together, they're what let independently-deployed services evolve their contracts without requiring every consumer to upgrade in lockstep.

## 2. Why & when

You design explicitly for both directions of compatibility because independently deployable microservices, by definition, are never all on the same version at the same moment:

- **A [rolling deployment](0450-rolling-deployment.md) always has old and new versions running side by side, briefly.** During the rollout window, some instances run the old contract and some run the new one — both must be able to serve real traffic correctly, which requires exactly the compatibility guarantees these two properties describe.
- **Different consumer teams upgrade their own clients on their own schedule.** A provider that breaks backward compatibility forces every consumer to upgrade in lockstep with the provider's own release — exactly the kind of tight coupling [independent deployability](0013-independent-deployability.md) is meant to avoid.
- **Forward compatibility matters just as much as backward compatibility, and is easier to overlook.** A consumer built to expect exactly three fields that crashes when a fourth, genuinely new field appears is a forward-compatibility failure — the consumer wasn't tolerant of contract evolution it hadn't seen yet.
- **You design for both from the very first version of any contract with independent consumers** — retrofitting compatibility discipline onto a contract that's already been carelessly evolved is far harder than building it in from the start.

## 3. Core concept

Think of a spoken language evolving over generations: a grandparent (an old client) should still be understood by their grandchildren (a new server) using mostly-familiar vocabulary — that's backward compatibility. And a grandchild using a brand-new slang word should still be broadly understandable to a grandparent, who simply ignores the unfamiliar word rather than being unable to parse the whole sentence — that's forward compatibility. A language (a contract) that requires every speaker to instantly adopt every change simultaneously would be unusable across generations.

Concretely, the practices that produce both properties:

1. **New fields are added as optional, never required.** An old client that doesn't send a new optional field should still be accepted; a new server should supply a sensible default when an old request omits it.
2. **New fields are additive, not replacing existing ones.** Renaming or removing an existing field breaks every client still expecting it — add a new field alongside the old one and deprecate the old one gradually instead.
3. **Unknown fields are ignored, not rejected.** A client (or server) receiving a message with fields it doesn't recognize should skip them, not fail — this is what makes forward compatibility possible: the [tolerant reader pattern](0496-tolerant-reader-pattern.md) captures this discipline explicitly.
4. **Enum-like fields should tolerate new values gracefully.** A new status value an old client has never seen shouldn't crash it — designing for an "unknown/other" fallback, rather than assuming the enum is closed, keeps evolution smooth.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An old client works against a new server (backward compatibility) and an old client tolerates new fields from a new server (forward compatibility), during a rolling deployment where both versions run simultaneously">
  <rect x="20" y="30" width="280" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">backward compat:</text>
  <text x="160" y="72" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">old client works against NEW server</text>

  <rect x="360" y="30" width="280" height="55" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="500" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">forward compat:</text>
  <text x="500" y="72" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">old client tolerates NEW fields</text>

  <text x="330" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">both matter during a rolling deployment, where old and new versions run side by side</text>
</svg>

Both compatibility directions are needed simultaneously whenever old and new versions coexist, which is essentially always during a deployment.

## 5. Runnable example

Scenario: an old client parsing responses from both an old and a new server version. We start with a basic backward-compatible request handled by a new server, extend it to a forward-compatible response with a new field the old client must tolerate, then handle the hard case: a new, unrecognized enum value in a status field, which the old client must handle gracefully rather than crashing.

### Level 1 — Basic

```java
// File: BackwardCompatBasic.java -- models an OLD client sending a
// request built against the OLD contract, handled correctly by a NEW
// server that still understands it -- BACKWARD compatibility.
import java.util.*;

public class BackwardCompatBasic {
    // The OLD client's request shape -- only knows about these two fields.
    static Map<String, String> oldClientBuildsRequest() {
        return Map.of("orderId", "42", "customerEmail", "old-client@example.com");
    }

    // The NEW server: still accepts the OLD request shape, even though it's evolved since.
    static String newServerHandleRequest(Map<String, String> request) {
        String orderId = request.get("orderId");
        String email = request.get("customerEmail");
        System.out.println("[new server] handled OLD-shaped request: orderId=" + orderId + ", email=" + email);
        return "order " + orderId + " created";
    }

    public static void main(String[] args) {
        Map<String, String> oldRequest = oldClientBuildsRequest();
        String result = newServerHandleRequest(oldRequest);
        System.out.println("[old client] received: " + result);
    }
}
```

How to run: `java BackwardCompatBasic.java`

`newServerHandleRequest` only reads the two fields it needs (`orderId`, `customerEmail`) from the request map — it makes no assumption that any *other* field must also be present, which is exactly what allows it to correctly accept a request built by an old client that's never heard of any newer, additional fields.

### Level 2 — Intermediate

```java
// File: ForwardCompatBasic.java -- the SAME pair, now demonstrating
// FORWARD compatibility: the NEW server's response includes a NEW field
// the OLD client has never seen, and the OLD client must tolerate it
// gracefully -- ignoring what it doesn't recognize, rather than failing.
import java.util.*;

public class ForwardCompatBasic {
    // The NEW server's response includes a NEW field: "loyaltyPointsEarned".
    static Map<String, Object> newServerBuildsResponse(String orderId) {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("orderId", orderId);
        response.put("status", "CONFIRMED");
        response.put("loyaltyPointsEarned", 15); // NEW field, added after the old client was built
        return response;
    }

    // The OLD client: only reads the fields IT knows about, ignoring anything unfamiliar.
    static void oldClientParseResponse(Map<String, Object> response) {
        String orderId = (String) response.get("orderId");
        String status = (String) response.get("status");
        // The old client never reads "loyaltyPointsEarned" -- it doesn't know it exists,
        // and critically, its presence causes NO error.
        System.out.println("[old client] parsed known fields: orderId=" + orderId + ", status=" + status);
        System.out.println("[old client] unrecognized fields in response were safely ignored");
    }

    public static void main(String[] args) {
        Map<String, Object> response = newServerBuildsResponse("42");
        System.out.println("[new server] full response: " + response);
        oldClientParseResponse(response);
    }
}
```

How to run: `java ForwardCompatBasic.java`

`oldClientParseResponse` only ever calls `response.get("orderId")` and `response.get("status")` — it never enumerates every key in the map or asserts the map's exact size, so `loyaltyPointsEarned` being present is completely invisible to it. This is the concrete mechanism of forward compatibility: the old client's parsing logic simply doesn't look for fields it doesn't know about, so their presence causes no failure.

### Level 3 — Advanced

```java
// File: ForwardCompatUnknownEnumValue.java -- the SAME forward-compatible
// response handling, now handling the PRODUCTION-FLAVORED hard case: the
// NEW server introduces a genuinely NEW status enum value the OLD client
// has NEVER seen. A naive switch/if-chain would either crash or silently
// mishandle it -- the OLD client must have an explicit "unknown/other"
// fallback branch to handle this gracefully.
import java.util.*;

public class ForwardCompatUnknownEnumValue {
    static Map<String, Object> newServerBuildsResponse(String orderId, String status) {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("orderId", orderId);
        response.put("status", status);
        return response;
    }

    // The OLD client's known statuses at the time it was built.
    static Set<String> oldClientKnownStatuses = Set.of("PENDING", "SHIPPED", "DELIVERED", "CANCELLED");

    static void oldClientHandleStatus(Map<String, Object> response) {
        String orderId = (String) response.get("orderId");
        String status = (String) response.get("status");

        if (!oldClientKnownStatuses.contains(status)) {
            // The GRACEFUL fallback: don't crash, don't guess -- treat unknown as a safe generic case.
            System.out.println("[old client] order " + orderId + ": UNKNOWN status '" + status
                    + "' (introduced after this client was built) -- displaying generic 'processing' fallback UI");
            return;
        }

        switch (status) {
            case "PENDING" -> System.out.println("[old client] order " + orderId + ": showing 'awaiting confirmation'");
            case "SHIPPED" -> System.out.println("[old client] order " + orderId + ": showing 'on its way'");
            case "DELIVERED" -> System.out.println("[old client] order " + orderId + ": showing 'delivered'");
            case "CANCELLED" -> System.out.println("[old client] order " + orderId + ": showing 'cancelled'");
        }
    }

    public static void main(String[] args) {
        System.out.println("--- known status, old client handles it normally ---");
        oldClientHandleStatus(newServerBuildsResponse("42", "SHIPPED"));

        System.out.println();
        System.out.println("--- NEW status introduced by the server AFTER the old client was built ---");
        oldClientHandleStatus(newServerBuildsResponse("99", "AWAITING_CUSTOMS_CLEARANCE"));
    }
}
```

How to run: `java ForwardCompatUnknownEnumValue.java`

`oldClientHandleStatus` checks `status` against `oldClientKnownStatuses` *before* the `switch` statement — for `"AWAITING_CUSTOMS_CLEARANCE"`, a status value invented after this client shipped, the membership check fails, so the explicit fallback branch runs, printing a generic but safe message and returning immediately, never even reaching the `switch`. Without this guard, the `switch` (having no `default` case) would simply do nothing silently for an unknown value — the explicit fallback is what gives the old client a deliberate, visible, safe behavior instead of silent, confusing non-response.

## 6. Walkthrough

Trace `ForwardCompatUnknownEnumValue.main` in order. **First**, the known-status case calls `oldClientHandleStatus(newServerBuildsResponse("42", "SHIPPED"))`. Inside `oldClientHandleStatus`, the `if (!oldClientKnownStatuses.contains("SHIPPED"))` check is `false`, since `"SHIPPED"` is in the known set — the fallback branch is skipped, and execution reaches the `switch`, matching the `"SHIPPED"` case and printing the appropriate message.

**Next**, the new-status case calls `oldClientHandleStatus(newServerBuildsResponse("99", "AWAITING_CUSTOMS_CLEARANCE"))`. This time, `oldClientKnownStatuses.contains("AWAITING_CUSTOMS_CLEARANCE")` is `false`, since this value didn't exist when the old client's `oldClientKnownStatuses` set was defined — the `if` condition is `true`.

**Then**, the fallback branch runs: it prints a message explicitly naming the unrecognized status and explaining it was introduced after this client was built, then displays a generic fallback rather than attempting to guess at meaning — and critically, `return` exits the method right there, so the `switch` statement below is never reached for this case at all.

**After that**, no exception is thrown anywhere, no crash occurs, and the old client has produced a reasonable, if generic, response to a status value it genuinely has no specific knowledge of — exactly the graceful degradation forward compatibility requires.

**Finally**, comparing the two outcomes side by side shows the design working as intended: a known status gets its full, specific handling, while an unknown one gets a safe, honest fallback — neither crashes, and neither silently does nothing without explanation.

```
--- known status, old client handles it normally ---
[old client] order 42: showing 'on its way'

--- NEW status introduced by the server AFTER the old client was built ---
[old client] order 99: UNKNOWN status 'AWAITING_CUSTOMS_CLEARANCE' (introduced after this client was built) -- displaying generic 'processing' fallback UI
```

## 7. Gotchas & takeaways

> A `switch` statement (or equivalent) with no explicit default/fallback case doesn't "fail safely" on an unrecognized value — it fails *silently*, doing nothing and giving no indication anything unexpected happened, which is often worse than a visible error because it goes unnoticed until a user reports confusing, blank behavior. Always add an explicit fallback branch for values a client doesn't recognize.
- Backward and forward compatibility are properties of the *contract's evolution discipline*, not something you can add after the fact to a contract that's already been carelessly broken — additive, optional, ignorable-when-unknown changes from the very first version are what make both properties achievable.
- This discipline is exactly what the [tolerant reader pattern](0496-tolerant-reader-pattern.md) formalizes on the consumer side — read only what you need, tolerate everything else, and have an explicit fallback for values you don't recognize.
- [API versioning strategies](0494-api-versioning-strategies-uri-header-media-type.md) are the tool for handling genuinely *breaking* changes that additive evolution can't accommodate — compatibility discipline reduces how often you actually need to reach for a breaking version bump.
- Test both directions explicitly: run old client code against a new server, and feed a new server's actual responses (including any new fields or values) through old client parsing logic, to catch compatibility regressions before they reach real users during a real rollout.
