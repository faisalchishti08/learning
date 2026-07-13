---
card: microservices
gi: 394
slug: secrets-management-rotation
title: "Secrets management & rotation"
---

## 1. What it is

A **secret** is any credential a service needs to function but must never be exposed: database passwords, [API keys](0393-api-keys.md), TLS private keys, JWT signing keys, third-party service tokens. **Secrets management** is the discipline of storing, distributing, and auditing access to those values without hard-coding them into source code or configuration files. **Rotation** is the practice of periodically replacing a secret with a new value — on a schedule, or immediately after a suspected leak — so that any given secret has a limited window in which it's dangerous if it does leak.

## 2. Why & when

Every service in a microservices system needs *some* secrets — a database password, a signing key, credentials for [service-to-service authentication](0391-service-to-service-authentication.md) — and the [larger attack surface](0378-microservices-security-challenges-larger-attack-surface.md) of a distributed system means there are now many more places those secrets could leak from:

- **Secrets in source code or config files get committed to version control** — often permanently, since git history retains old commits even after the secret is removed from the latest version.
- **Secrets in plain environment variables** are visible to anything that can read the process's environment (a debugging endpoint, a crash dump, a compromised sidecar container) and commonly end up duplicated across CI logs, deployment manifests, and developer laptops.
- **A secret with no expiry stays dangerous forever** once leaked, until someone notices and manually rotates it — which, in practice, is often "never," because rotating a widely-used secret means touching every service that uses it without causing an outage.
- **Compliance regimes** (SOC 2, PCI-DSS, and similar) frequently mandate both centralized secrets storage and periodic rotation as explicit controls, not just best practice.

You need a real secrets-management strategy the moment more than a couple of services need shared credentials, and rotation becomes essential the moment any secret could plausibly need to survive a leak without becoming a lasting compromise — which, in a production system, is effectively all of them.

## 3. Core concept

Think of the difference between writing your house key's shape on a sticky note taped to your front door (anyone who looks finds it, and it never changes) versus using a smart lock that issues a new access code to your dog-walker every week and can revoke any single code instantly if one leaks, without changing anyone else's. Secrets management done well works like the smart lock: secrets are held in one dedicated, access-controlled place — not scattered across code and config — and rotation makes them cheap to invalidate the moment something looks wrong.

Concretely, mature secrets management rests on a few pillars:

1. **A dedicated secrets store**, not source code or plain environment variables — tools like HashiCorp Vault, AWS Secrets Manager, Google Secret Manager, or Kubernetes Secrets (with encryption at rest enabled) hold the actual values, access-controlled and audit-logged.
2. **Services fetch secrets at runtime**, either by querying the store directly on startup or via an injected sidecar/init-container, rather than baking secrets into a container image or deployment manifest.
3. **Short-lived, dynamically-generated credentials** where possible — instead of a single static database password every instance shares forever, a system like Vault can issue a unique, time-limited database credential *per service instance*, automatically revoked when its lease expires.
4. **Rotation on a schedule, plus emergency rotation on suspected compromise.** Scheduled rotation limits how long any given secret stays valid even if nothing goes wrong; emergency rotation is the fast-path response when something *does*.
5. **Zero-downtime rotation** typically means a brief overlap window where both the old and new secret are valid, so in-flight services can pick up the new value without a hard cutover causing failed requests.

Rotation and [token exchange](0390-token-exchange.md) share a philosophy even though they solve different problems: both limit how much damage a single leaked credential can do, by keeping credentials narrowly-scoped and short-lived rather than broad and permanent.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A service fetches its database credential from a secrets store at startup instead of reading it from a config file; the store issues a short-lived credential and automatically rotates it before expiry" font-family="sans-serif">
  <rect x="30" y="30" width="170" height="50" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="115" y="50" fill="#f85149" font-size="10" text-anchor="middle">BAD: password in</text>
  <text x="115" y="65" fill="#f85149" font-size="10" text-anchor="middle">application.yml / git repo</text>

  <rect x="30" y="120" width="170" height="50" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="115" y="150" fill="#e6edf3" font-size="10" text-anchor="middle">order-service</text>

  <rect x="280" y="120" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="355" y="142" fill="#e6edf3" font-size="10" text-anchor="middle">Secrets store</text>
  <text x="355" y="158" fill="#8b949e" font-size="9" text-anchor="middle">(Vault / Secrets Manager)</text>
  <text x="355" y="173" fill="#8b949e" font-size="8" text-anchor="middle">issues short-lived creds</text>

  <rect x="500" y="120" width="120" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="560" y="140" fill="#e6edf3" font-size="10" text-anchor="middle">Database</text>
  <text x="560" y="155" fill="#8b949e" font-size="8" text-anchor="middle">per-instance creds</text>

  <line x1="200" y1="145" x2="280" y2="145" stroke="#6db33f" marker-end="url(#sm)"/>
  <text x="240" y="135" fill="#6db33f" font-size="8" text-anchor="middle">fetch at startup</text>
  <line x1="430" y1="145" x2="500" y2="145" stroke="#79c0ff" marker-end="url(#sm)"/>
  <text x="465" y="135" fill="#79c0ff" font-size="7" text-anchor="middle">TTL cred</text>
  <text x="355" y="205" fill="#8b949e" font-size="8" text-anchor="middle">rotates / revokes automatically before TTL expires</text>
  <defs>
    <marker id="sm" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Instead of a password baked into config or committed to a repository, the service fetches a short-lived credential from a dedicated secrets store at runtime, which issues and rotates database credentials automatically.

## 5. Runnable example

Scenario: a database credential used by order-service. We start with a hard-coded password, move to fetching it from a simulated secrets store, then add expiry-aware rotation with an overlap window so a rotating credential doesn't break in-flight service instances.

### Level 1 — Basic

```java
// File: HardcodedSecret.java -- the database password is baked directly into
// the source. It never changes, and anyone who reads this file (or the repo
// history, even after "removing" it in a later commit) has it forever.
public class HardcodedSecret {
    static final String DB_PASSWORD = "Sup3rSecretPassw0rd!"; // <-- committed to source control

    static String connectToDatabase() {
        return "Connecting with password '" + DB_PASSWORD + "' -- same value, forever, visible to anyone with repo access";
    }

    public static void main(String[] args) {
        System.out.println(connectToDatabase());
    }
}
```

How to run: `java HardcodedSecret.java`

`DB_PASSWORD` is a constant baked into the compiled class file and, more importantly, into whatever source-control history this file lives in. Even if a later commit "removes" it, the value remains recoverable from git history indefinitely — the defining problem with any secret that's ever touched source code.

### Level 2 — Intermediate

```java
// File: FetchFromSecretsStore.java -- the password is no longer in source code.
// It's fetched at RUNTIME from a simulated secrets store, keyed by service
// identity -- closer to how Vault or a cloud secrets manager actually works.
import java.util.*;

public class FetchFromSecretsStore {
    // Simulated secrets store: never checked into source control in a real system.
    static final Map<String, String> SECRETS_STORE = Map.of(
            "order-service/db-password", "runtime-fetched-Xk9#mP2vQ"
    );

    static String fetchSecret(String path) {
        String value = SECRETS_STORE.get(path);
        if (value == null) throw new IllegalStateException("no secret at path: " + path);
        return value;
    }

    static String connectToDatabase(String serviceName) {
        String password = fetchSecret(serviceName + "/db-password");
        return "Connecting as '" + serviceName + "' with a password fetched at runtime (never stored in source)";
    }

    public static void main(String[] args) {
        System.out.println(connectToDatabase("order-service"));
        System.out.println("Rotating the secret means updating ONE place: the store -- not every service's config file.");
    }
}
```

How to run: `java FetchFromSecretsStore.java`

`SECRETS_STORE` stands in for a real secrets manager: the password lives in exactly one place, addressed by a path tied to the requesting service's identity. `connectToDatabase` fetches it at runtime rather than reading a compiled-in constant. This is already a major improvement — the source code (and its history) never contains the actual password — but this version still has no concept of the secret ever *changing*; the same value is fetched forever until someone manually updates the store.

### Level 3 — Advanced

```java
// File: RotatingSecretWithOverlap.java -- the secrets store now issues
// short-lived, VERSIONED credentials with a TTL, and supports an OVERLAP
// window where both the current and previous version remain valid --
// so in-flight service instances don't break the instant rotation happens.
import java.time.*;
import java.util.*;

public class RotatingSecretWithOverlap {
    record SecretVersion(String value, Instant issuedAt, Instant expiresAt) {
        boolean isValid(Instant now) { return !now.isBefore(issuedAt) && now.isBefore(expiresAt); }
    }

    static class RotatingStore {
        // Keeps the CURRENT and the PREVIOUS version during an overlap window.
        SecretVersion current;
        SecretVersion previous;

        RotatingStore(SecretVersion initial) { this.current = initial; }

        void rotate(String newValue, Instant now, Duration ttl) {
            previous = current; // old version stays valid until IT expires, giving instances time to catch up
            current = new SecretVersion(newValue, now, now.plus(ttl));
        }

        // A consumer presents whatever credential it currently holds; either the
        // current or a still-unexpired previous version is accepted.
        boolean isAcceptable(String presentedValue, Instant now) {
            if (current.value().equals(presentedValue) && current.isValid(now)) return true;
            if (previous != null && previous.value().equals(presentedValue) && previous.isValid(now)) return true;
            return false;
        }
    }

    public static void main(String[] args) {
        Instant t0 = Instant.parse("2026-07-13T00:00:00Z");
        Duration ttl = Duration.ofHours(24);
        RotatingStore store = new RotatingStore(new SecretVersion("cred-v1-Xk9mP2", t0, t0.plus(ttl)));

        // An older service instance fetched cred-v1 at startup and holds onto it.
        String instanceAHeldCredential = "cred-v1-Xk9mP2";

        // Scheduled rotation happens a few hours later -- overlap window begins.
        Instant tRotate = t0.plus(Duration.ofHours(6));
        store.rotate("cred-v2-Ln4qR8", tRotate, ttl);
        System.out.println("Rotated at " + tRotate + "; new instances now fetch cred-v2");

        // instanceA hasn't restarted yet -- does its OLD credential still work during the overlap?
        Instant tCheck = tRotate.plus(Duration.ofMinutes(30));
        System.out.println("instanceA's old credential still accepted during overlap: "
                + store.isAcceptable(instanceAHeldCredential, tCheck));

        // A NEW instance fetches the current credential and uses it.
        System.out.println("New instance's fresh credential accepted: " + store.isAcceptable("cred-v2-Ln4qR8", tCheck));

        // Well after the old version's TTL expires, the OLD credential is finally rejected.
        Instant tLate = t0.plus(Duration.ofHours(25));
        System.out.println("instanceA's old credential accepted long after original TTL: "
                + store.isAcceptable(instanceAHeldCredential, tLate));
    }
}
```

How to run: `java RotatingSecretWithOverlap.java`

`RotatingStore` keeps both `current` and `previous` secret versions, each with its own `issuedAt`/`expiresAt` window. `rotate` demotes the current version to `previous` (which keeps ticking down toward *its own* original expiry) and installs a fresh `current`. `isAcceptable` checks a presented credential against *either* version, as long as that specific version hasn't expired yet — this is what makes rotation safe for already-running service instances: they don't need to restart the instant rotation happens, because their held-onto old credential remains valid until its own TTL runs out, not the instant a new one is issued.

## 6. Walkthrough

Trace `RotatingSecretWithOverlap.main` in order. **First**, `store` is created with `current = SecretVersion("cred-v1-Xk9mP2", t0, t0+24h)` — the only version that exists yet. `instanceAHeldCredential` is set to this same value, simulating a running service instance that fetched it once at startup and is holding it in memory.

**Next**, `store.rotate("cred-v2-Ln4qR8", tRotate, ttl)` runs at `t0+6h`. Inside `rotate`, `previous` is set to the *current* `SecretVersion` object (still `cred-v1`, still expiring at `t0+24h` — its own original expiry, untouched by the rotation event), and `current` is reassigned to a brand-new `SecretVersion` for `cred-v2`, valid from `tRotate` to `tRotate+24h`.

**Then**, `store.isAcceptable(instanceAHeldCredential, tCheck)` runs at `tRotate+30min` (`t0+6.5h`). The first check, against `current` (`cred-v2`), fails because the *value* doesn't match. The second check, against `previous` (`cred-v1`), succeeds: the value matches, and `previous.isValid(tCheck)` is `true` because `tCheck` (`t0+6.5h`) is still before `previous.expiresAt()` (`t0+24h`). instanceA's old credential is accepted — it never had to notice rotation happened at all.

**Also then**, `store.isAcceptable("cred-v2-Ln4qR8", tCheck)` checks the *new* instance's fresh credential against `current` directly — value matches, and it's within its own validity window, so it's accepted too. Both old and new credentials work simultaneously during the overlap.

**Finally**, `store.isAcceptable(instanceAHeldCredential, tLate)` runs at `t0+25h` — one hour past `cred-v1`'s *original* expiry of `t0+24h`. `previous.isValid(tLate)` is now `false`, because `tLate` is after `previous.expiresAt()`. instanceA's old credential is finally rejected — by this point it has had 24 hours (its original TTL) to notice rotation and fetch the new value; if it hasn't, that's now a genuine problem the system should alert on.

```
Rotated at 2026-07-13T06:00:00Z; new instances now fetch cred-v2
instanceA's old credential still accepted during overlap: true
New instance's fresh credential accepted: true
instanceA's old credential accepted long after original TTL: false
```

## 7. Gotchas & takeaways

> Rotating a secret with a hard cutover — instantly invalidating the old value the moment the new one is issued — is a common cause of self-inflicted outages: every service instance that hasn't yet picked up the new credential starts failing simultaneously. Overlap windows (as in Level 3) trade a short period of "two valid credentials at once" for zero-downtime rotation; without that trade-off, teams often end up disabling rotation altogether just to avoid the operational pain, which defeats the whole point.

- Never store secrets in source code, container images, or plain environment variables checked into a repo — a dedicated secrets store with access control and audit logging is the baseline, not a luxury.
- Prefer short-lived, dynamically-issued credentials over long-lived static ones — the shorter a credential's useful lifetime, the smaller the damage window if it leaks.
- Rotation needs an overlap window (old and new both valid briefly) to be operationally safe; a hard cutover risks outages exactly when a security-motivated action is happening.
- Rotate on a fixed schedule *and* immediately on any suspected compromise — scheduled rotation limits ambient risk, emergency rotation limits the fallout from a known incident.
- The same instinct that motivates rotation — never let a single, long-lived, unscoped credential exist longer than it has to — also motivates [token exchange](0390-token-exchange.md)'s down-scoping and [API keys](0393-api-keys.md)'s per-key revocation; they're different mechanisms solving the same underlying problem.
