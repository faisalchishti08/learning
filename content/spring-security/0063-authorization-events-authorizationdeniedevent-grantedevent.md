---
card: spring-security
gi: 63
slug: authorization-events-authorizationdeniedevent-grantedevent
title: "Authorization events (AuthorizationDeniedEvent/GrantedEvent)"
---

## 1. What it is

Spring Security publishes `AuthorizationDeniedEvent` and (opt-in, since it's noisy by default) `AuthorizationGrantedEvent` for every URL- and method-level authorization decision, mirroring the authentication-events pattern from earlier in this section — `@EventListener`-annotated methods can subscribe to either event type to react to authorization outcomes (audit logging denied access attempts, monitoring for repeated denials indicating probing or a misconfigured client) entirely independently of the authorization decision logic itself.

```java
@Component
public class AuthorizationAuditListener {
    @EventListener
    public void onDenied(AuthorizationDeniedEvent<?> event) {
        auditLog.record("ACCESS_DENIED", event.getAuthentication().get().getName(), event.getObject().toString());
    }
}

// AuthorizationGrantedEvent is NOT published by default (would be extremely high-volume);
// enable it explicitly only if genuinely needed:
@Bean
static AuthorizationEventPublisher authorizationEventPublisher(ApplicationEventPublisher publisher) {
    var eventPublisher = new SpringAuthorizationEventPublisher(publisher);
    return eventPublisher; // publishes BOTH denied and granted events once configured this way
}
```

## 2. Why & when

Authorization decisions happen constantly — every request, every protected method call — and most granted decisions are simply the expected, routine case, uninteresting to log individually at high volume; denied decisions, by contrast, are comparatively rare and often genuinely worth knowing about: a user probing for access they shouldn't have, a misconfigured client repeatedly hitting an endpoint it lacks permission for, or simply useful signal for debugging an unexpected `403`. This asymmetry is exactly why `AuthorizationDeniedEvent` is published by default while `AuthorizationGrantedEvent` requires opting in — the framework's default behavior matches what's actually useful to observe in the overwhelming majority of applications without any configuration at all.

Reach for authorization event listeners when:

- Building a security audit trail specifically for denied access attempts — the default-enabled `AuthorizationDeniedEvent` is exactly the signal for this, requiring no extra configuration.
- Detecting patterns across repeated denials — many denied attempts targeting the same resource from one source, or one account probing many different resources it lacks access to, both suggesting deliberate probing rather than an incidental permission mismatch.
- Opting into `AuthorizationGrantedEvent` only when genuinely needed (a compliance requirement demanding a complete access log, not just denials) — understanding the volume trade-off this introduces before enabling it broadly.

## 3. Core concept

```
 EVERY authorization check (URL-based via AuthorizationFilter, OR method-based via @PreAuthorize's interceptor):

   check.granted() == false:
     AuthorizationDeniedEvent PUBLISHED  (DEFAULT behavior -- no configuration needed)

   check.granted() == true:
     AuthorizationGrantedEvent published ONLY IF explicitly enabled
       (via a custom AuthorizationEventPublisher bean, since granting is the COMMON case
        and publishing an event for EVERY SINGLE ONE would be needlessly high-volume by default)
```

Denials are noteworthy by default; grants are the routine background noise, opted into only when specifically needed.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Every authorization decision that denies access publishes an AuthorizationDeniedEvent by default while granted decisions only publish an AuthorizationGrantedEvent if that behavior has been explicitly opted into reflecting that denials are comparatively rare and noteworthy while grants are the routine common case">
  <rect x="15" y="65" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="88" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">authorization check</text>

  <rect x="230" y="20" width="180" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="38" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">DENIED -&gt; event published</text>
  <text x="320" y="51" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(DEFAULT, always on)</text>

  <rect x="230" y="105" width="180" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="123" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">GRANTED -&gt; event NOT published</text>
  <text x="320" y="136" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(unless explicitly opted in)</text>

  <defs><marker id="a63" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="80" x2="230" y2="41" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a63)"/>
  <line x1="165" y1="95" x2="230" y2="126" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a63)"/>
</svg>

Two outcomes, deliberately asymmetric default visibility — denials are noteworthy, grants are routine.

## 5. Runnable example

The scenario: implement the asymmetric default publishing behavior directly, then a listener detecting repeated denials from one source (a probing-detection use case), then show enabling granted-event publishing and the volume difference this introduces.

### Level 1 — Basic

The core asymmetric publishing behavior: denied events always publish, granted events only publish when opted in.

```java
import java.util.*;
import java.util.function.Consumer;

public class AuthorizationEventsLevel1 {
    record AuthorizationDecision(boolean granted, String resource, String username) {}

    interface DeniedListener { void onDenied(AuthorizationDecision decision); }

    static List<DeniedListener> deniedListeners = new ArrayList<>();
    static boolean grantedEventsEnabled = false; // matches the REAL default: OFF unless explicitly configured

    static void publishDecision(AuthorizationDecision decision) {
        if (!decision.granted()) {
            deniedListeners.forEach(l -> l.onDenied(decision)); // ALWAYS published, regardless of configuration
        } else if (grantedEventsEnabled) {
            System.out.println("[GRANTED EVENT] " + decision.username() + " -> " + decision.resource());
        }
        // if granted AND grantedEventsEnabled is false: NOTHING is published at all for this decision
    }

    public static void main(String[] args) {
        deniedListeners.add(decision -> System.out.println("[DENIED EVENT] " + decision.username() + " -> " + decision.resource()));

        publishDecision(new AuthorizationDecision(true, "/dashboard", "alice"));  // granted, events OFF -> silent
        publishDecision(new AuthorizationDecision(false, "/admin/reports", "bob")); // denied -> ALWAYS logged
    }
}
```

How to run: `java AuthorizationEventsLevel1.java`

alice's granted access to `/dashboard` produces no output at all, since `grantedEventsEnabled` is `false`; bob's denied access to `/admin/reports` is logged unconditionally, since denied events always publish regardless of any configuration flag — exactly matching the real framework's default, asymmetric behavior.

### Level 2 — Intermediate

Add a probing-detection listener accumulating denial counts per username across multiple resources.

```java
import java.util.*;

public class AuthorizationEventsLevel2 {
    record AuthorizationDecision(boolean granted, String resource, String username) {}
    interface DeniedListener { void onDenied(AuthorizationDecision decision); }

    static List<DeniedListener> deniedListeners = new ArrayList<>();
    static Map<String, Set<String>> deniedResourcesPerUser = new HashMap<>();
    static final int PROBING_THRESHOLD = 3;

    static void publishDecision(AuthorizationDecision decision) {
        if (!decision.granted()) deniedListeners.forEach(l -> l.onDenied(decision));
    }

    public static void main(String[] args) {
        deniedListeners.add(decision -> {
            Set<String> resources = deniedResourcesPerUser.computeIfAbsent(decision.username(), k -> new HashSet<>());
            resources.add(decision.resource());
            if (resources.size() >= PROBING_THRESHOLD) {
                System.out.println("[SECURITY ALERT] " + decision.username() + " denied access to " + resources.size()
                        + " distinct resources: " + resources + " -- possible access probing");
            }
        });

        publishDecision(new AuthorizationDecision(false, "/admin/reports", "mallory"));
        publishDecision(new AuthorizationDecision(false, "/admin/users", "mallory"));
        publishDecision(new AuthorizationDecision(false, "/admin/settings", "mallory")); // THIRD distinct resource
    }
}
```

How to run: `java AuthorizationEventsLevel2.java`

Each of the three denials targets a different resource but the same username, `mallory` — the listener accumulates a growing set of distinct denied resources per user, and once that set reaches `PROBING_THRESHOLD` (3), it prints a security alert, flagging a pattern of denials across multiple resources that a single-denial-at-a-time view would never reveal on its own.

### Level 3 — Advanced

Enable granted-event publishing explicitly, and demonstrate the resulting volume difference by counting how many total events fire for a realistic mixed workload of mostly-granted, occasionally-denied requests.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class AuthorizationEventsLevel3 {
    record AuthorizationDecision(boolean granted, String resource, String username) {}

    static AtomicInteger deniedEventCount = new AtomicInteger();
    static AtomicInteger grantedEventCount = new AtomicInteger();

    static void publishDecision(AuthorizationDecision decision, boolean grantedEventsEnabled) {
        if (!decision.granted()) {
            deniedEventCount.incrementAndGet();
        } else if (grantedEventsEnabled) {
            grantedEventCount.incrementAndGet();
        }
        // if granted and grantedEventsEnabled is false: no counter incremented at all
    }

    public static void main(String[] args) {
        // a realistic workload: 100 requests, 95 granted (the routine case), 5 denied (the noteworthy case)
        List<AuthorizationDecision> workload = new ArrayList<>();
        for (int i = 0; i < 95; i++) workload.add(new AuthorizationDecision(true, "/dashboard", "user" + i));
        for (int i = 0; i < 5; i++) workload.add(new AuthorizationDecision(false, "/admin/reports", "user" + i));

        System.out.println("-- with grantedEventsEnabled = false (the DEFAULT) --");
        for (AuthorizationDecision d : workload) publishDecision(d, false);
        System.out.println("denied events published: " + deniedEventCount.get() + ", granted events published: " + grantedEventCount.get());

        deniedEventCount.set(0);
        grantedEventCount.set(0);

        System.out.println();
        System.out.println("-- with grantedEventsEnabled = true (EXPLICITLY opted in) --");
        for (AuthorizationDecision d : workload) publishDecision(d, true);
        System.out.println("denied events published: " + deniedEventCount.get() + ", granted events published: " + grantedEventCount.get());
    }
}
```

How to run: `java AuthorizationEventsLevel3.java`

With the default configuration, only the 5 denied decisions produce any published event at all, while the 95 granted decisions produce none; opting into granted-event publishing makes *all 95* additional events fire too — a nearly 20x increase in event volume for this workload, concretely illustrating why granted events are opt-in by default rather than automatically enabled alongside denied events.

## 6. Walkthrough

Trace the second loop (`grantedEventsEnabled = true`) from Level 3's `main`.

1. Before the loop starts, `deniedEventCount.set(0)` and `grantedEventCount.set(0)` reset both counters to zero, so this second pass starts from a clean slate independent of the first pass's results.
2. The loop iterates all 100 entries in `workload`, calling `publishDecision(d, true)` for each — this time passing `true` for `grantedEventsEnabled`.
3. For each of the first 95 entries (all `granted = true`), `publishDecision`'s `if (!decision.granted())` check is `false` (since `decision.granted()` is `true`), so the method moves to the `else if (grantedEventsEnabled)` branch — this time `grantedEventsEnabled` is `true`, so `grantedEventCount.incrementAndGet()` runs for each of these 95 entries, bringing the final count to `95`.
4. For each of the remaining 5 entries (all `granted = false`), `publishDecision`'s first `if` condition is `true`, so `deniedEventCount.incrementAndGet()` runs — exactly as it did in the first pass, since this branch's behavior never depended on `grantedEventsEnabled` at all.
5. The final `println` reports `deniedEventCount.get()` as `5` (unchanged from what denial-only publishing would always produce) and `grantedEventCount.get()` as `95` — confirming that opting into granted-event publishing adds a genuinely large volume of additional events precisely because grants are the overwhelmingly common case in any typical, mostly-successful workload.

```
workload: 95 granted + 5 denied = 100 total decisions

grantedEventsEnabled=false (DEFAULT): denied=5, granted=0   (only the noteworthy 5% produces ANY event)
grantedEventsEnabled=true (opt-in):    denied=5, granted=95  (the routine 95% now ALSO produces events)
```

## 7. Gotchas & takeaways

> **Gotcha:** enabling `AuthorizationGrantedEvent` publishing without a corresponding plan for the resulting event volume (a high-throughput sink, sampling, or filtering logic in the listener itself) can meaningfully impact application performance or overwhelm downstream logging/monitoring systems, precisely because granted decisions vastly outnumber denied ones in any healthy, mostly-successful application — always evaluate expected volume before opting in broadly.

- `AuthorizationDeniedEvent` is published by default for every denied authorization decision, requiring no configuration — appropriate given how comparatively rare and noteworthy denials typically are.
- `AuthorizationGrantedEvent` requires explicit opt-in, since granted decisions are the overwhelming majority in any healthy application, and publishing an event for every single one by default would introduce needless volume for most use cases.
- Accumulating denial events across multiple resources or repeated attempts (rather than reacting to each denial in isolation) is a natural and valuable pattern for detecting deliberate probing or misconfigured clients.
- Before opting into granted-event publishing, consider the resulting event volume relative to the application's typical grant/deny ratio, and plan the listener's downstream handling (sampling, filtering, a high-throughput sink) accordingly.
