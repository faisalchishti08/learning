---
card: spring-cloud
gi: 112
slug: lease-renewal-rotation
title: "Lease renewal & rotation"
---

## 1. What it is

Every dynamic secret Vault issues (a database credential, the client token from authentication itself) comes with a lease — a time-to-live after which Vault automatically revokes it — and Spring Cloud Vault runs a background lease renewal process that periodically extends these leases before they expire, for as long as the application is running and the secret is still needed, so a long-running application keeps using the same credential without interruption, right up until the point it deliberately lets the lease lapse (on shutdown) or Vault itself refuses further renewal (hitting the lease's maximum TTL).

```properties
spring.cloud.vault.config.lifecycle.enabled=true
spring.cloud.vault.config.lifecycle.min-renewal=10s
spring.cloud.vault.config.lifecycle.expiry-threshold=60s
```

```java
// application code never manually renews -- Spring Cloud Vault's background task does it automatically
@Value("${database.password}")
String databasePassword; // remains valid for as long as the application keeps running, transparently
```

## 2. Why & when

A dynamic secret's whole security benefit — automatic expiration limiting the blast radius of a leaked credential — becomes an operational liability if nothing renews it before that expiration actually happens: a database credential that silently expires mid-run would cause every subsequent database connection attempt to fail authentication, taking down a running application with no warning. Lease renewal solves this by proactively extending the lease *before* it expires, on a schedule tuned by `min-renewal`/`expiry-threshold`, keeping the credential continuously valid without the application needing to notice or react — the tradeoff dynamic secrets require in exchange for their security benefit is exactly this ongoing renewal responsibility, and Spring Cloud Vault fully automates it rather than leaving it to hand-rolled application code.

Reach for understanding lease renewal explicitly when:

- Running any application that consumes dynamic Vault secrets (database credentials, generated certificates) for longer than that secret's lease duration — renewal is what makes long-running consumption of short-lived secrets actually work in practice.
- Diagnosing an application failure that manifests as sudden authentication failures against a downstream system (a database, an API) after running successfully for some time — an expired, un-renewed lease is a common root cause worth checking specifically.
- Configuring lease renewal timing (`min-renewal`, `expiry-threshold`) to match a specific secret's lease duration and an application's tolerance for renewal-related background overhead — too-infrequent renewal risks expiry slipping through; too-frequent renewal adds unnecessary load against Vault.

## 3. Core concept

```
 secret issued with lease duration = 300s (5 minutes)

 WITHOUT renewal:
   t=0s: credential valid
   t=300s: credential EXPIRES, Vault revokes it -> application's next use of it FAILS

 WITH renewal (expiry-threshold=60s -- renew when within 60s of expiry):
   t=0s:   credential valid, lease expires at t=300s
   t=240s: background task notices lease is within 60s of expiring -> RENEWS -> new expiry = t=540s
   t=480s: background task notices lease is within 60s of expiring -> RENEWS -> new expiry = t=780s
   ... continues indefinitely, credential NEVER actually reaches expiry while the app is running
```

Renewal doesn't issue a brand-new credential — it extends the *existing* credential's validity window, so the application-facing value (the actual username/password) never changes mid-run purely due to renewal.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A credentials lease is proactively renewed before its expiry threshold is reached extending validity repeatedly so the credential never actually lapses while the application keeps running">
  <line x1="30" y1="80" x2="610" y2="80" stroke="#8b949e" stroke-width="1.5"/>
  <circle cx="30" cy="80" r="4" fill="#6db33f"/>
  <text x="30" y="105" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">issued</text>

  <circle cx="230" cy="80" r="4" fill="#79c0ff"/>
  <text x="230" y="60" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">renew (within threshold)</text>
  <text x="230" y="105" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">t=240s</text>

  <circle cx="430" cy="80" r="4" fill="#79c0ff"/>
  <text x="430" y="60" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">renew (within threshold)</text>
  <text x="430" y="105" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">t=480s</text>

  <circle cx="600" cy="80" r="4" fill="#8b949e"/>
  <text x="600" y="105" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">... continues</text>
</svg>

Each renewal pushes the expiry point further out, well before it's ever reached — the credential's validity window slides forward continuously rather than being allowed to run out.

## 5. Runnable example

The scenario: model a background renewal loop that proactively extends a credential's lease before expiry, contrasted against an unrenewed credential that eventually fails. Start with an unrenewed lease reaching expiry and failing, then add proactive renewal preventing that failure, then simulate Vault refusing renewal past a maximum TTL, requiring the application to obtain an entirely fresh credential instead.

### Level 1 — Basic

An unrenewed lease: time passes, the lease expires, and any subsequent use fails.

```java
public class LeaseRenewalLevel1 {
    static class Lease {
        long issuedAtMs;
        long durationMs;
        Lease(long durationMs) { this.issuedAtMs = System.currentTimeMillis(); this.durationMs = durationMs; }
        boolean isExpired(long nowMs) { return (nowMs - issuedAtMs) > durationMs; }
    }

    static void useCredential(Lease lease) {
        if (lease.isExpired(System.currentTimeMillis())) {
            throw new IllegalStateException("credential lease has EXPIRED -- authentication will fail downstream");
        }
        System.out.println("using credential successfully");
    }

    public static void main(String[] args) throws InterruptedException {
        Lease lease = new Lease(50); // 50ms lease, deliberately short for this demo

        useCredential(lease); // succeeds -- still fresh

        Thread.sleep(100); // simulate time passing well past the lease duration, with NO renewal

        try {
            useCredential(lease); // NOW fails -- nothing renewed it
        } catch (IllegalStateException e) {
            System.out.println("failure: " + e.getMessage());
        }
    }
}
```

How to run: `java LeaseRenewalLevel1.java`

The first `useCredential` call succeeds, but after `Thread.sleep(100)` pushes past the `50ms` lease with no renewal in between, the second call throws — this is exactly the failure mode lease renewal exists to prevent for any application running longer than a dynamic secret's lease duration.

### Level 2 — Intermediate

Add a background renewal loop that proactively extends the lease before it expires, preventing the Level 1 failure entirely.

```java
public class LeaseRenewalLevel2 {
    static class Lease {
        long issuedAtMs;
        long durationMs;
        Lease(long durationMs) { this.issuedAtMs = System.currentTimeMillis(); this.durationMs = durationMs; }
        boolean isExpired(long nowMs) { return (nowMs - issuedAtMs) > durationMs; }
        boolean isWithinRenewalThreshold(long nowMs, long thresholdMs) { return (issuedAtMs + durationMs - nowMs) < thresholdMs; }
        void renew() { issuedAtMs = System.currentTimeMillis(); System.out.println("lease RENEWED, new expiry pushed out"); } // extends the SAME lease
    }

    static void useCredential(Lease lease) {
        if (lease.isExpired(System.currentTimeMillis())) throw new IllegalStateException("credential lease has EXPIRED");
        System.out.println("using credential successfully");
    }

    // models Spring Cloud Vault's background lease-renewal task, checking periodically
    static void backgroundRenewalCheck(Lease lease, long thresholdMs) {
        if (lease.isWithinRenewalThreshold(System.currentTimeMillis(), thresholdMs)) {
            lease.renew();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Lease lease = new Lease(100); // 100ms lease

        useCredential(lease);

        Thread.sleep(70); // approaching expiry (70ms of the 100ms lease elapsed)
        backgroundRenewalCheck(lease, 40); // renewal threshold: renew if within 40ms of expiry -- 30ms remain, so THIS renews

        Thread.sleep(70); // WITHOUT renewal, total elapsed (140ms) would have exceeded the original 100ms lease
        useCredential(lease); // succeeds -- renewal reset the clock, so this is well within the NEW window
    }
}
```

How to run: `java LeaseRenewalLevel2.java`

Without renewal, waiting `70ms` then another `70ms` (`140ms` total) would exceed the original `100ms` lease and cause `useCredential` to fail exactly as in Level 1; because `backgroundRenewalCheck` correctly detects the lease is within its `40ms` renewal threshold (only `30ms` remained) and calls `lease.renew()`, resetting `issuedAtMs`, the second `useCredential` call succeeds — the credential was never allowed to actually reach expiry.

### Level 3 — Advanced

Add a maximum TTL that renewal eventually can't extend past (mirroring Vault's own `max_ttl` setting), requiring the application to request an entirely fresh credential once renewal is no longer possible.

```java
public class LeaseRenewalLevel3 {
    static class Lease {
        long issuedAtMs;
        long firstIssuedAtMs; // tracks the ORIGINAL issuance, for max-TTL calculation across renewals
        long durationMs;
        long maxTtlMs;
        Lease(long durationMs, long maxTtlMs) {
            this.issuedAtMs = System.currentTimeMillis();
            this.firstIssuedAtMs = this.issuedAtMs;
            this.durationMs = durationMs;
            this.maxTtlMs = maxTtlMs;
        }
        boolean isExpired(long nowMs) { return (nowMs - issuedAtMs) > durationMs; }
        boolean isWithinRenewalThreshold(long nowMs, long thresholdMs) { return (issuedAtMs + durationMs - nowMs) < thresholdMs; }
        boolean canStillRenew(long nowMs) { return (nowMs - firstIssuedAtMs) < maxTtlMs; } // Vault enforces this server-side too
        void renew() { issuedAtMs = System.currentTimeMillis(); }
    }

    static Lease requestFreshCredential(long durationMs, long maxTtlMs) {
        System.out.println("requesting a BRAND NEW credential from Vault (old one hit its max TTL)");
        return new Lease(durationMs, maxTtlMs);
    }

    public static void main(String[] args) throws InterruptedException {
        Lease lease = new Lease(30, 80); // 30ms lease, 80ms absolute max TTL across ALL renewals

        for (int i = 0; i < 5; i++) {
            Thread.sleep(25);
            long now = System.currentTimeMillis();
            if (lease.isWithinRenewalThreshold(now, 15)) {
                if (lease.canStillRenew(now)) {
                    lease.renew();
                    System.out.println("iteration " + i + ": renewed (still under max TTL)");
                } else {
                    // Vault refuses further renewal past max_ttl -- the application must get a FRESH credential instead
                    lease = requestFreshCredential(30, 80);
                }
            } else {
                System.out.println("iteration " + i + ": no renewal needed yet");
            }
        }
    }
}
```

How to run: `java LeaseRenewalLevel3.java`

After enough renewals push the *original* credential's age past its `80ms` `maxTtlMs`, `canStillRenew` starts returning `false` even though the lease is still within its renewal threshold — at that point the code calls `requestFreshCredential` instead of `renew`, obtaining an entirely new `Lease` with its own new `firstIssuedAtMs`, mirroring how a real Vault-backed dynamic secret that hits its configured `max_ttl` can no longer be renewed and the application must re-authenticate/re-request a completely new credential rather than continuing to extend the old one indefinitely.

## 6. Walkthrough

Trace the iteration where renewal transitions to fresh-credential-request in Level 3.

1. Each loop iteration sleeps `25ms`, then checks `lease.isWithinRenewalThreshold(now, 15)` — since the lease duration is `30ms` and `15ms` is the threshold, this becomes `true` on most iterations given how close `25ms` sleeps push the lease toward its `30ms` boundary.
2. When the threshold check is `true`, `lease.canStillRenew(now)` checks `(now - firstIssuedAtMs) < 80` — early iterations, where the *original* issuance is still recent, satisfy this, so `lease.renew()` runs, updating `issuedAtMs` (but *not* `firstIssuedAtMs`, which stays fixed at the original issuance time).
3. As iterations continue, `now - firstIssuedAtMs` keeps growing (since `firstIssuedAtMs` never resets on renewal), and eventually exceeds `80ms` — at that point `canStillRenew` returns `false` even though the *current* lease window (`issuedAtMs` to `issuedAtMs + 30`) hasn't been reached yet, because the *absolute* age since original issuance is what `max_ttl` actually bounds.
4. When `canStillRenew` returns `false`, the `else` branch runs `requestFreshCredential(30, 80)`, which constructs and returns a brand-new `Lease` object — critically, this new lease's `firstIssuedAtMs` is reset to the current time, giving it its own fresh `80ms` max-TTL budget, completely independent of the old, now-abandoned lease.
5. `lease = requestFreshCredential(...)` reassigns the local variable, so all subsequent loop iterations operate against this new lease — exactly mirroring how a real application, upon hitting Vault's refusal to renew past `max_ttl`, must fetch and start using an entirely new dynamic secret rather than continuing to try to extend the old one.

```
renewals keep pushing issuedAtMs forward, but firstIssuedAtMs stays FIXED at original issuance
  now - firstIssuedAtMs  keeps growing across renewals
  once it exceeds maxTtlMs (80ms) -> canStillRenew() returns false
  -> requestFreshCredential() called -> NEW Lease with its OWN fresh firstIssuedAtMs and full 80ms budget
```

## 7. Gotchas & takeaways

> **Gotcha:** `max_ttl` bounds the *total* lifetime of a credential across all its renewals combined, not the duration of any single renewal — a common misunderstanding is assuming renewal can extend a lease indefinitely as long as each individual renewal happens before that renewal's own expiry; in reality, Vault (and the correct application logic mirroring it, as `firstIssuedAtMs` tracks in Level 3) enforces an absolute ceiling on how long any one credential, however many times renewed, remains valid before a genuinely fresh one is required.

- Lease renewal is what makes long-running consumption of short-lived dynamic secrets practical — without it, every dynamic secret would need a lease duration longer than the application's entire runtime, largely defeating the security benefit of short leases in the first place.
- Spring Cloud Vault automates renewal entirely as a background process — application code consuming `@Value`-bound secrets needs no awareness of renewal happening at all, exactly as application code needs no awareness of which authentication method (an earlier card) was used.
- A credential's `max_ttl` is an absolute ceiling on total lifetime, tracked from original issuance, independent of how many times it's been renewed along the way — once reached, only a genuinely new credential (not a renewal) can continue providing access.
- Renewal timing configuration (`min-renewal`, `expiry-threshold`) should be tuned relative to the actual lease durations Vault issues for a given secret — too narrow a renewal window risks a race against actual expiry under load or network delay; too wide a window wastes unnecessary renewal calls against Vault.
