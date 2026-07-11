---
card: spring-security
gi: 51
slug: authentication-events-success-failure-listeners
title: "Authentication events (success/failure listeners)"
---

## 1. What it is

Spring Security publishes a Spring `ApplicationEvent` for every authentication outcome — `AuthenticationSuccessEvent` on success, and a distinct subtype per failure reason (`AuthenticationFailureBadCredentialsEvent`, `AuthenticationFailureLockedEvent`, `AuthenticationFailureDisabledEvent`, and others matching the account-status exceptions from two cards back) — letting any number of independent `@EventListener`-annotated methods react to authentication activity without being coupled to (or interfering with) the authentication flow itself.

```java
@Component
public class AuthenticationAuditListener {
    @EventListener
    public void onSuccess(AuthenticationSuccessEvent event) {
        auditLog.record("LOGIN_SUCCESS", event.getAuthentication().getName());
    }

    @EventListener
    public void onFailure(AbstractAuthenticationFailureEvent event) {
        auditLog.record("LOGIN_FAILURE", event.getAuthentication().getName(), event.getException().getMessage());
        failedLoginTracker.recordFailure(event.getAuthentication().getName());
    }
}
```

## 2. Why & when

Reacting to authentication activity — logging every login for an audit trail, incrementing a failed-attempt counter that eventually locks an account, alerting on suspicious patterns (many failures across many different accounts from one IP) — is a cross-cutting concern that has nothing to do with *how* authentication itself is verified, and coupling this reactive logic directly into a custom `AuthenticationProvider` would tangle two genuinely separate responsibilities together. Spring Security's event-publishing design keeps them cleanly separate: `ProviderManager` publishes the appropriate event after every authentication attempt completes (success or failure), and any number of independent listeners can react — for logging, security monitoring, account lockout enforcement, or anything else — without the authentication logic itself needing any awareness that these listeners exist.

Reach for authentication event listeners when:

- Building an audit trail of authentication activity — logging every success and failure, including the specific failure reason, without embedding that logging logic inside a custom `AuthenticationProvider`.
- Implementing the automatic account-lockout mechanism (from the earlier "account status" card) — an `AuthenticationFailureBadCredentialsEvent` listener is the natural place to increment a failed-attempt counter, keeping that logic entirely separate from the credential-verification logic itself.
- Detecting suspicious patterns across multiple failures — a listener accumulating failure events by source IP or by targeted username can flag potential credential-stuffing or brute-force activity, again without touching the authentication providers themselves.

## 3. Core concept

```
 ProviderManager.authenticate(unverified):
   ... delegates to the appropriate AuthenticationProvider ...

   ON SUCCESS:  publish AuthenticationSuccessEvent(resultingAuthentication)
   ON FAILURE:  publish the SPECIFIC failure event matching the exception type:
        BadCredentialsException      -> AuthenticationFailureBadCredentialsEvent
        LockedException              -> AuthenticationFailureLockedEvent
        DisabledException            -> AuthenticationFailureDisabledEvent
        AccountExpiredException      -> AuthenticationFailureExpiredEvent
        ... (one distinct event type per distinct failure reason)

 ANY number of @EventListener-annotated methods, in ANY component, can subscribe to ANY of these event types --
   they run AFTER the authentication outcome is already determined, and CANNOT influence that outcome
```

Listeners observe and react to an already-decided outcome — they never participate in deciding it.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="After an authentication attempt completes ProviderManager publishes either a success event or a specific failure event matching the exception type multiple independent listeners an audit logger a failed attempt tracker and a suspicious activity detector all react to the same event without knowing about each other">
  <rect x="15" y="65" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">authentication</text>
  <text x="90" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">attempt completes</text>

  <rect x="215" y="65" width="170" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="300" y="85" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">event published</text>
  <text x="300" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(success or specific failure)</text>

  <rect x="440" y="15" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="530" y="36" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">audit logger listener</text>

  <rect x="440" y="60" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="530" y="81" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">failed-attempt tracker</text>

  <rect x="440" y="105" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="530" y="126" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">suspicious-activity detector</text>

  <defs><marker id="a51" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="88" x2="215" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a51)"/>
  <line x1="385" y1="80" x2="440" y2="32" stroke="#8b949e" stroke-width="1" marker-end="url(#a51)"/>
  <line x1="385" y1="88" x2="440" y2="77" stroke="#8b949e" stroke-width="1" marker-end="url(#a51)"/>
  <line x1="385" y1="95" x2="440" y2="122" stroke="#8b949e" stroke-width="1" marker-end="url(#a51)"/>
</svg>

One published event, three independent listeners reacting — none aware the others exist.

## 5. Runnable example

The scenario: model a simple event-publishing mechanism for authentication outcomes and multiple independent listeners, then wire up the account-lockout tracker as a genuine listener (rather than logic embedded in the authentication flow itself), then add a suspicious-activity detector reacting to patterns across multiple different accounts.

### Level 1 — Basic

A minimal event bus publishing authentication outcomes to any number of registered listeners.

```java
import java.util.*;
import java.util.function.Consumer;

public class AuthEventsLevel1 {
    interface AuthEvent {}
    record SuccessEvent(String username) implements AuthEvent {}
    record FailureEvent(String username, String reason) implements AuthEvent {}

    static class EventBus {
        List<Consumer<AuthEvent>> listeners = new ArrayList<>();
        void subscribe(Consumer<AuthEvent> listener) { listeners.add(listener); }
        void publish(AuthEvent event) { listeners.forEach(l -> l.accept(event)); }
    }

    public static void main(String[] args) {
        EventBus bus = new EventBus();

        bus.subscribe(event -> {
            if (event instanceof SuccessEvent e) System.out.println("[AUDIT] login success: " + e.username());
            if (event instanceof FailureEvent e) System.out.println("[AUDIT] login failure: " + e.username() + " (" + e.reason() + ")");
        });

        bus.publish(new SuccessEvent("alice"));
        bus.publish(new FailureEvent("bob", "bad credentials"));
    }
}
```

How to run: `java AuthEventsLevel1.java`

`EventBus.publish` calls every registered listener for each event, regardless of the event's specific type — the single subscribed listener here uses pattern matching to distinguish success from failure and logs each accordingly, exactly modeling how `@EventListener` methods react to whichever event types they declare interest in.

### Level 2 — Intermediate

Add a second, independent listener — a failed-attempt tracker driving account lockout — completely decoupled from the audit logger.

```java
import java.util.*;
import java.util.function.Consumer;

public class AuthEventsLevel2 {
    interface AuthEvent {}
    record SuccessEvent(String username) implements AuthEvent {}
    record FailureEvent(String username, String reason) implements AuthEvent {}

    static class EventBus {
        List<Consumer<AuthEvent>> listeners = new ArrayList<>();
        void subscribe(Consumer<AuthEvent> listener) { listeners.add(listener); }
        void publish(AuthEvent event) { listeners.forEach(l -> l.accept(event)); }
    }

    static Map<String, Integer> failedAttempts = new HashMap<>();
    static final int LOCKOUT_THRESHOLD = 3;

    public static void main(String[] args) {
        EventBus bus = new EventBus();

        // Listener 1: audit logging -- knows NOTHING about lockout logic
        bus.subscribe(event -> {
            if (event instanceof SuccessEvent e) System.out.println("[AUDIT] success: " + e.username());
            if (event instanceof FailureEvent e) System.out.println("[AUDIT] failure: " + e.username());
        });

        // Listener 2: failed-attempt tracker -- knows NOTHING about audit logging
        bus.subscribe(event -> {
            if (event instanceof FailureEvent e) {
                int count = failedAttempts.merge(e.username(), 1, Integer::sum);
                if (count >= LOCKOUT_THRESHOLD) System.out.println("[LOCKOUT] " + e.username() + " locked after " + count + " failures");
            }
            if (event instanceof SuccessEvent e) failedAttempts.remove(e.username()); // reset on ANY successful login
        });

        bus.publish(new FailureEvent("bob", "bad credentials"));
        bus.publish(new FailureEvent("bob", "bad credentials"));
        bus.publish(new FailureEvent("bob", "bad credentials")); // THIRD failure -- crosses the threshold
    }
}
```

How to run: `java AuthEventsLevel2.java`

Both listeners react to the same three `FailureEvent` publications independently — the audit listener simply logs each one, while the lockout tracker accumulates a per-username count and prints a lockout message once bob's count reaches `LOCKOUT_THRESHOLD` on the third failure — neither listener has any reference to or knowledge of the other's existence.

### Level 3 — Advanced

Add a suspicious-activity detector that reacts to patterns *across multiple different usernames* sharing a source IP — a listener whose logic genuinely couldn't live inside any single authentication provider, since it needs a cross-attempt, cross-account view.

```java
import java.util.*;
import java.util.function.Consumer;

public class AuthEventsLevel3 {
    interface AuthEvent {}
    record SuccessEvent(String username, String sourceIp) implements AuthEvent {}
    record FailureEvent(String username, String sourceIp) implements AuthEvent {}

    static class EventBus {
        List<Consumer<AuthEvent>> listeners = new ArrayList<>();
        void subscribe(Consumer<AuthEvent> listener) { listeners.add(listener); }
        void publish(AuthEvent event) { listeners.forEach(l -> l.accept(event)); }
    }

    static Map<String, Set<String>> distinctUsernamesTriedPerIp = new HashMap<>(); // sourceIp -> usernames attempted
    static final int SUSPICIOUS_USERNAME_COUNT = 3;

    public static void main(String[] args) {
        EventBus bus = new EventBus();

        // suspicious-activity detector: flags an IP attempting MANY DIFFERENT usernames -- classic credential-stuffing pattern
        bus.subscribe(event -> {
            String sourceIp = null;
            String username = null;
            if (event instanceof FailureEvent e) { sourceIp = e.sourceIp(); username = e.username(); }
            if (event instanceof SuccessEvent e) { sourceIp = e.sourceIp(); username = e.username(); }

            Set<String> usernamesFromThisIp = distinctUsernamesTriedPerIp.computeIfAbsent(sourceIp, k -> new HashSet<>());
            usernamesFromThisIp.add(username);
            if (usernamesFromThisIp.size() >= SUSPICIOUS_USERNAME_COUNT) {
                System.out.println("[SECURITY ALERT] IP " + sourceIp + " has tried " + usernamesFromThisIp.size()
                        + " distinct usernames: " + usernamesFromThisIp + " -- possible credential stuffing");
            }
        });

        String attackerIp = "203.0.113.99";
        bus.publish(new FailureEvent("alice", attackerIp));
        bus.publish(new FailureEvent("bob", attackerIp));
        bus.publish(new FailureEvent("carol", attackerIp)); // THIRD distinct username from the SAME IP
    }
}
```

How to run: `java AuthEventsLevel3.java`

Each of the three `FailureEvent`s targets a *different* username, but all originate from the identical `attackerIp` — the detector accumulates a growing `Set<String>` of distinct usernames attempted per IP, and once that set reaches `SUSPICIOUS_USERNAME_COUNT` (3), it prints a security alert — a pattern (many usernames, one source) that no single per-account lockout tracker (like Level 2's) would ever notice, since each individual account only saw exactly one failure.

## 6. Walkthrough

Trace all three `bus.publish` calls in Level 3's `main`.

1. `bus.publish(new FailureEvent("alice", "203.0.113.99"))` invokes the single subscribed listener; inside, `sourceIp = "203.0.113.99"` and `username = "alice"` are extracted; `distinctUsernamesTriedPerIp.computeIfAbsent("203.0.113.99", k -> new HashSet<>())` creates a fresh empty set for this IP (since it's the first time this IP has appeared), and `usernamesFromThisIp.add("alice")` adds `"alice"` to it, bringing its size to `1` — since `1 >= 3` is `false`, no alert fires.
2. `bus.publish(new FailureEvent("bob", "203.0.113.99"))` runs next; `computeIfAbsent` this time finds the *existing* set for `"203.0.113.99"` (already containing `{"alice"}`) rather than creating a new one, and `usernamesFromThisIp.add("bob")` grows it to `{"alice", "bob"}`, size `2` — still `2 >= 3` is `false`, no alert.
3. `bus.publish(new FailureEvent("carol", "203.0.113.99"))` runs last; the same set is retrieved and grown to `{"alice", "bob", "carol"}`, size `3` — now `3 >= 3` is `true`, so the security alert prints, listing all three distinct usernames attempted from this single IP.
4. This demonstrates the detector's state accumulates *across* separate event publications, tied together purely by the shared `sourceIp` key in `distinctUsernamesTriedPerIp` — no single event alone carries enough information to trigger the alert; it's the pattern across all three that does.

```
FailureEvent(alice, 203.0.113.99) -> usernamesFromThisIp = {alice}              size=1, no alert
FailureEvent(bob,   203.0.113.99) -> usernamesFromThisIp = {alice, bob}         size=2, no alert
FailureEvent(carol, 203.0.113.99) -> usernamesFromThisIp = {alice, bob, carol}  size=3 >= threshold -> ALERT
```

## 7. Gotchas & takeaways

> **Gotcha:** authentication event listeners run *after* the authentication outcome has already been determined and cannot influence, veto, or delay it — a listener attempting to throw an exception to "block" a login after the fact has no effect on the already-completed authentication decision; any logic that needs to actually *affect* whether authentication succeeds (like the account-lockout check itself, as opposed to merely tracking the count) belongs inside an `AuthenticationProvider`, checked before the decision is made, not in an event listener reacting afterward.

- Authentication events (`AuthenticationSuccessEvent`, and a distinct failure event per exception type) decouple reacting to authentication activity from the authentication logic itself, letting any number of independent listeners observe outcomes without being coupled to how those outcomes were determined.
- Listeners are purely reactive — they run after the outcome is decided and cannot change it; enforcement logic (denying a locked account) must live in an `AuthenticationProvider`'s account-status checks instead.
- Multiple listeners can maintain entirely independent state and react to the same events for entirely different purposes (audit logging, per-account lockout tracking, cross-account suspicious-pattern detection) without any coordination or awareness of each other.
- Cross-attempt, cross-account patterns (many different usernames failing from one source) are a natural fit for an event listener specifically because they require accumulating state across multiple separate authentication attempts, something no single authentication decision could see in isolation.
