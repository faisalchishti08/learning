---
card: system-design
gi: 180
slug: secrets-management-rotation
title: Secrets management & rotation
---

## 1. What it is

**Secrets management** is the practice of storing sensitive credentials — database passwords, API keys, TLS private keys, encryption keys — in a dedicated, access-controlled system (like HashiCorp Vault, AWS Secrets Manager, or Kubernetes Secrets) instead of hardcoding them in source code or configuration files. **Rotation** is periodically replacing a secret with a new value and retiring the old one, so that any single leaked credential has a limited useful lifetime, and so a compromised secret can be actively invalidated rather than remaining valid forever.

## 2. Why & when

A secret hardcoded into source code ends up in version control history forever, even if later removed, and is visible to anyone with repository access. A secrets manager centralizes storage, applies fine-grained access control (which service or person can read which secret), and often audits every access. Rotation matters because a secret that never changes becomes a permanent liability the moment it leaks — an old, unrevoked credential found in a years-old log file or a former employee's laptop is just as valid as it was the day it was created, unless it has since been rotated. Use dedicated secrets management for any credential your application needs, and build in rotation from the start, since retrofitting rotation into a system that assumes a secret never changes is much harder later.

## 3. Core concept

- **Centralized, access-controlled storage:** secrets live in one place with an audit log of who accessed what, instead of scattered across configuration files, environment variables set by hand, and chat messages.
- **Dynamic secrets:** some secrets managers can generate short-lived, unique credentials per request (e.g. a temporary database username/password pair that expires in an hour) instead of handing out one long-lived shared credential.
- **Rotation without downtime — the overlap window:** rotating a secret safely usually requires a period where *both* the old and new values are valid, so in-flight requests using the old value, and services that have not yet picked up the new value, keep working during the transition.
- **Automated rotation vs. manual rotation:** automated rotation (the secrets manager itself periodically generates and pushes a new value) is far more reliable than a manual, calendar-reminder-driven process, which tends to slip or get skipped under time pressure.
- **Revocation on suspected compromise:** rotation is also the mechanism for immediately invalidating a secret believed to be leaked — the old value is retired at once, rather than waiting for its next scheduled rotation.

## 4. Diagram

```
   time -->
   secret v1: [========== valid ==========]
   secret v2:                    [========== valid ==========]
                                  ^                            ^
                          rotation begins:            old secret (v1)
                          v2 issued, BOTH             finally revoked,
                          v1 and v2 valid              only v2 remains
                          during the overlap

   during the overlap window: services still using v1 keep working;
   services updated to v2 also work; nothing breaks mid-rotation
```
*Caption: a safe rotation keeps both the old and new secret valid for an overlap period, so nothing breaks while every consumer transitions to the new value.*

## 5. Runnable example

**Level 1 — Basic.** A secrets store: retrieve a secret by name, instead of it being hardcoded.

**Level 2 — Rotate a secret with an overlap window.** Both the old and new values remain valid until the old one is explicitly revoked.

**Level 3 — Immediate revocation on suspected compromise.** Skip the overlap window entirely when a secret is known to be leaked.

```java
// SecretsManagementDemo.java
import java.util.*;

public class SecretsManagementDemo {

    static class SecretVersion {
        final String value;
        boolean valid = true;
        SecretVersion(String value) { this.value = value; }
    }

    // Level 1: the secrets store - secrets are looked up by name, never hardcoded in application code.
    static Map<String, List<SecretVersion>> secretsStore = new HashMap<>();

    static void storeSecret(String name, String value) {
        secretsStore.computeIfAbsent(name, k -> new ArrayList<>()).add(new SecretVersion(value));
    }

    // A consumer "authenticates" using any CURRENTLY VALID version of the secret.
    static boolean authenticateWithSecret(String name, String providedValue) {
        List<SecretVersion> versions = secretsStore.getOrDefault(name, List.of());
        for (SecretVersion v : versions) {
            if (v.valid && v.value.equals(providedValue)) return true;
        }
        return false;
    }

    // Level 2: rotate - issue a new version, keeping the old one valid during the overlap.
    static void rotateSecret(String name, String newValue) {
        storeSecret(name, newValue);
        System.out.println("rotated \"" + name + "\": new version issued, old version still valid during overlap");
    }

    // Level 2 (continued): after the overlap window, explicitly revoke the old version.
    static void revokeOldVersions(String name, String currentValue) {
        for (SecretVersion v : secretsStore.get(name)) {
            if (!v.value.equals(currentValue)) v.valid = false;
        }
        System.out.println("revoked all versions of \"" + name + "\" except the current one");
    }

    // Level 3: immediate revocation - skip the overlap window entirely for a known-compromised secret.
    static void emergencyRevoke(String name, String compromisedValue) {
        for (SecretVersion v : secretsStore.get(name)) {
            if (v.value.equals(compromisedValue)) v.valid = false;
        }
        System.out.println("EMERGENCY revoked the compromised version of \"" + name + "\" immediately, no overlap");
    }

    public static void main(String[] args) {
        storeSecret("db-password", "v1-p@ssw0rd");

        System.out.println("service authenticating with v1: " + authenticateWithSecret("db-password", "v1-p@ssw0rd"));

        // Level 2: rotate to v2 - v1 stays valid during the overlap window.
        rotateSecret("db-password", "v2-p@ssw0rd");
        System.out.println("service still using OLD v1 during overlap: " + authenticateWithSecret("db-password", "v1-p@ssw0rd"));
        System.out.println("service updated to NEW v2 during overlap: " + authenticateWithSecret("db-password", "v2-p@ssw0rd"));

        // Overlap window ends - revoke everything except v2.
        revokeOldVersions("db-password", "v2-p@ssw0rd");
        System.out.println("service still trying OLD v1 after revocation: " + authenticateWithSecret("db-password", "v1-p@ssw0rd"));
        System.out.println("service using v2 after revocation: " + authenticateWithSecret("db-password", "v2-p@ssw0rd"));

        // Level 3: v2 is discovered leaked - emergency revoke it immediately, with NO overlap.
        rotateSecret("db-password", "v3-p@ssw0rd");
        emergencyRevoke("db-password", "v2-p@ssw0rd");
        System.out.println("attempting to use LEAKED v2 immediately after emergency revocation: " + authenticateWithSecret("db-password", "v2-p@ssw0rd"));
    }
}
```

**How to run:** save as `SecretsManagementDemo.java`, then run `java SecretsManagementDemo.java`.

## 6. Walkthrough

1. `authenticateWithSecret("db-password", "v1-p@ssw0rd")` finds the single stored version marked `valid = true` and matching, so it returns `true` — this models a service authenticating using the only secret version that exists so far.
2. `rotateSecret("db-password", "v2-p@ssw0rd")` calls `storeSecret` again for the same name, appending a *second* `SecretVersion` to the list rather than replacing the first — both v1 and v2 now coexist, each still marked `valid = true`.
3. Both subsequent `authenticateWithSecret` calls, one with `"v1-p@ssw0rd"` and one with `"v2-p@ssw0rd"`, succeed, because the method's loop checks every version marked valid — this is the overlap window in action: a service still using the old value and a service already updated to the new value both keep working simultaneously.
4. `revokeOldVersions("db-password", "v2-p@ssw0rd")` iterates every stored version and sets `valid = false` for any version whose value does not equal the current one (`"v2-p@ssw0rd"`), so v1's `valid` flag flips to `false`; the next call to `authenticateWithSecret` with the old v1 value now finds no matching *valid* version and returns `false`, while the v2 call still succeeds.
5. After rotating again to v3, `emergencyRevoke("db-password", "v2-p@ssw0rd")` immediately sets v2's `valid` flag to `false` — no overlap window is honored for this specific version, since it is known to be compromised — and the final `authenticateWithSecret` call with the leaked v2 value correctly fails right away, rather than remaining usable for some grace period.

## 7. Gotchas & takeaways

> Gotcha: rotating a secret without an overlap window (immediately invalidating the old value the instant the new one is issued) works fine for a planned rotation only if every single consumer picks up the new value atomically at the same moment — in any real distributed system with multiple instances and propagation delay, this causes a brief but real outage as some instances are still using the now-invalid old value; the overlap window exists specifically to avoid this, and should only be skipped for a genuine emergency revocation.

- Centralizing secrets in a dedicated, access-controlled store avoids scattering credentials across code, config files, and informal channels.
- An overlap window during planned rotation is what lets a fleet of services transition to a new secret without any downtime.
- Emergency revocation deliberately skips the overlap window, accepting a brief disruption in exchange for immediately closing a known leak.
- Related concepts: [Spring Cloud Vault for secrets](0185-spring-cloud-vault-for-secrets.md) (a concrete implementation of this pattern for Spring applications), [API keys & mutual TLS (mTLS)](0178-api-keys-mutual-tls-mtls.md) (the kind of credential this management and rotation discipline applies to), [Encryption in transit (TLS) & at rest](0179-encryption-in-transit-tls-at-rest.md) (the encryption keys themselves are also secrets needing this same management).
