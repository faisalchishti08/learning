---
card: microservices
gi: 222
slug: secrets-management-encryption
title: "Secrets management & encryption"
---

## 1. What it is

Secrets management is the practice of storing sensitive configuration values — database passwords, API keys, encryption keys, tokens — separately from ordinary configuration, using dedicated storage that encrypts them at rest, controls who and what can read them, and avoids ever placing them in plaintext in source control, logs, or unencrypted config files.

## 2. Why & when

[Configuration as code](0221-configuration-as-code.md) is a strong default for ordinary settings, but applying it uncritically to secrets is actively dangerous: a password committed to Git remains recoverable from that repository's history forever, even after being "removed" in a later commit, and anyone with read access to the repository (or a leaked clone of it) gains the secret. Secrets need storage with different properties entirely — encryption at rest, fine-grained access control, and often automatic rotation — which is why dedicated secret stores (like [Spring Cloud Vault](0236-spring-cloud-vault-for-secrets.md), covered later) exist as a separate concern from general configuration management.

Route any credential, key, or token through dedicated secrets management rather than plain configuration files, from the very first line of code that needs one — retrofitting secret handling after a plaintext secret has already been committed requires rotating the compromised credential, not just deleting the line that referenced it. Ordinary, non-sensitive settings (timeouts, feature flags, URLs that aren't credentials themselves) don't need this treatment.

## 3. Core concept

A secret store holds sensitive values encrypted at rest and releases the decrypted value only to an authenticated, authorized caller at the moment it's actually needed, rather than the value existing in plaintext anywhere in configuration files, environment dumps, or version control history.

```java
// BAD -- a plaintext secret sitting in ordinary configuration, or worse, committed to Git
String dbPassword = "hunter2"; // visible to anyone who can read this file OR the repo's history

// GOOD -- fetched from a dedicated secret store, decrypted only at the point of use
interface SecretStore { String getSecret(String path); } // e.g. backed by Vault
String dbPassword = secretStore.getSecret("secret/order-service/db-password"); // NEVER stored in plaintext config
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An application authenticates to a secret store, which holds credentials encrypted at rest, and releases a decrypted secret only to that authenticated caller -- distinct from ordinary configuration flowing directly from a config file" >
  <rect x="20" y="65" width="140" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Application</text>

  <rect x="250" y="55" width="160" height="65" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="78" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Secret store</text>
  <text x="330" y="94" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">encrypted at rest</text>
  <text x="330" y="107" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">access-controlled</text>

  <rect x="480" y="65" width="140" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="87" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Decrypted secret</text>
  <text x="550" y="100" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">in memory ONLY</text>

  <line x1="160" y1="82" x2="248" y2="82" stroke="#8b949e" marker-end="url(#arr222)"/>
  <text x="204" y="76" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">authenticate</text>
  <line x1="410" y1="82" x2="478" y2="87" stroke="#8b949e" marker-end="url(#arr222)"/>

  <defs>
    <marker id="arr222" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The secret exists in plaintext only briefly, in memory, after an authenticated fetch — never at rest in a file or repository.

## 5. Runnable example

Scenario: a service that starts with a plaintext-in-code secret (visible to anyone reading the source), refactors to fetch that secret from a simulated encrypted secret store requiring authentication, and finally demonstrates access control rejecting an unauthorized caller — the same store, the same secret, but only an authenticated, authorized caller can retrieve the decrypted value.

### Level 1 — Basic

```java
// File: PlaintextSecretInCode.java -- the DB password sits in PLAIN TEXT,
// visible to anyone reading this source file (or its Git history).
public class PlaintextSecretInCode {
    static final String DB_PASSWORD = "hunter2"; // PLAINTEXT -- visible in source AND in Git history forever

    public static void main(String[] args) {
        System.out.println("Connecting with password: " + DB_PASSWORD);
        System.out.println("Anyone with read access to this file (or repo history) now has this password.");
    }
}
```

**How to run:** `javac PlaintextSecretInCode.java && java PlaintextSecretInCode` (JDK 17+).

### Level 2 — Intermediate

```java
// File: FetchFromSecretStore.java -- the password is now held ENCRYPTED
// inside a simulated secret store, and only released to a caller that
// AUTHENTICATES first -- never sitting in plaintext in this source file.
import java.util.*;

public class FetchFromSecretStore {
    static class SecretStore {
        // simulates "encryption at rest": stored value is XOR-obscured, not plaintext
        Map<String, String> encryptedSecrets = new HashMap<>(Map.of("db-password", xorEncrypt("hunter2")));

        static String xorEncrypt(String value) {
            StringBuilder sb = new StringBuilder();
            for (char c : value.toCharArray()) sb.append((char) (c ^ 42));
            return sb.toString();
        }

        String getSecret(String token, String path) { // requires a TOKEN -- no anonymous reads
            if (!token.equals("valid-app-token")) throw new SecurityException("unauthenticated secret access denied");
            return xorEncrypt(encryptedSecrets.get(path)); // XOR twice = decrypt
        }
    }

    public static void main(String[] args) {
        SecretStore secretStore = new SecretStore();
        String dbPassword = secretStore.getSecret("valid-app-token", "db-password"); // AUTHENTICATED fetch
        System.out.println("Connecting with password fetched from secret store: " + dbPassword);
        System.out.println("The password was never written in plaintext in THIS source file.");
    }
}
```

**How to run:** `javac FetchFromSecretStore.java && java FetchFromSecretStore` (JDK 17+).

Expected output:
```
Connecting with password fetched from secret store: hunter2
The password was never written in plaintext in THIS source file.
```

### Level 3 — Advanced

```java
// File: AccessControlRejectsUnauthorized.java -- adds per-secret access
// control: an authenticated caller can still be DENIED a specific secret
// it isn't authorized for, mirroring real least-privilege secret policies.
import java.util.*;

public class AccessControlRejectsUnauthorized {
    static class SecretStore {
        Map<String, String> encryptedSecrets = new HashMap<>(Map.of(
            "order-service/db-password", xorEncrypt("hunter2"),
            "payment-service/api-key", xorEncrypt("sk_live_abc123")
        ));
        // an ACCESS POLICY: which caller identities may read which secret paths
        Map<String, Set<String>> accessPolicy = Map.of(
            "order-service-token", Set.of("order-service/db-password"),       // order-service can ONLY read its own secret
            "payment-service-token", Set.of("payment-service/api-key")
        );

        static String xorEncrypt(String value) {
            StringBuilder sb = new StringBuilder();
            for (char c : value.toCharArray()) sb.append((char) (c ^ 42));
            return sb.toString();
        }

        String getSecret(String callerToken, String path) {
            Set<String> allowedPaths = accessPolicy.get(callerToken);
            if (allowedPaths == null || !allowedPaths.contains(path)) {
                throw new SecurityException("caller not authorized for secret path: " + path); // DENIED
            }
            return xorEncrypt(encryptedSecrets.get(path));
        }
    }

    public static void main(String[] args) {
        SecretStore secretStore = new SecretStore();

        String ownSecret = secretStore.getSecret("order-service-token", "order-service/db-password"); // ALLOWED
        System.out.println("order-service fetched its OWN secret: " + ownSecret);

        try {
            secretStore.getSecret("order-service-token", "payment-service/api-key"); // order-service trying ANOTHER service's secret
        } catch (SecurityException e) {
            System.out.println("Caught expected denial: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac AccessControlRejectsUnauthorized.java && java AccessControlRejectsUnauthorized` (JDK 17+).

Expected output:
```
order-service fetched its OWN secret: hunter2
Caught expected denial: caller not authorized for secret path: payment-service/api-key
```

## 6. Walkthrough

1. **Level 1, the exposed baseline** — `DB_PASSWORD` is a plain string literal compiled directly into the class; anyone with access to this source file, the compiled class file (via decompilation), or the Git repository's commit history has the password permanently, with no way to revoke that visibility short of rotating the actual credential.
2. **Level 2, storing encrypted, requiring authentication** — `SecretStore.encryptedSecrets` holds the password only in its XOR-obscured (simulating "encrypted at rest") form, and `getSecret` requires a valid `token` argument before performing the decryption and returning the plaintext value — a caller with no token, or the wrong token, is rejected via `SecurityException` before ever reaching the decrypted value.
3. **Level 2, where plaintext now exists** — the decrypted `dbPassword` string exists only transiently, in the calling method's local memory, after a successful authenticated fetch — never written to this source file or to any persisted config.
4. **Level 3, adding per-path access control** — `accessPolicy` maps each caller token to the specific set of secret paths that caller is allowed to read, meaning authentication alone (having *a* valid token) is no longer sufficient — the token must also be authorized for the *specific* secret path being requested.
5. **Level 3, the allowed case** — `secretStore.getSecret("order-service-token", "order-service/db-password")` succeeds because `accessPolicy.get("order-service-token")` contains exactly that path, so the decrypted value is returned normally.
6. **Level 3, the denied case** — the second call uses the same, validly-authenticated `"order-service-token"`, but requests `"payment-service/api-key"`, a path *not* in that token's allowed set; `getSecret` throws `SecurityException` even though the token itself is valid, demonstrating least-privilege access control: being authenticated is necessary but not sufficient — authorization for the specific secret is checked separately, exactly mirroring how a real secret store like Vault scopes access per-secret-path rather than granting all-or-nothing access to every stored secret.

## 7. Gotchas & takeaways

> **Gotcha:** removing a secret from a file and committing that removal does *not* remove it from Git history — the plaintext value remains fully recoverable from any earlier commit unless the repository's history is rewritten (a disruptive, coordination-heavy operation) or, more practically, the compromised credential is simply rotated; treat any secret that was ever committed in plaintext as compromised and rotate it, rather than relying on deleting the line.

- Secrets need dedicated storage with encryption at rest and access control — treating them like ordinary [configuration as code](0221-configuration-as-code.md) risks permanent, unrevokable exposure via version control history.
- A secret should be fetched from a secret store at the point of use and never persisted in plaintext in configuration files, logs, or source control.
- Authentication (proving who the caller is) and authorization (checking what that caller is allowed to access) are separate checks — a valid caller identity doesn't automatically grant access to every stored secret.
- Any secret that was ever committed to version control in plaintext should be treated as compromised and rotated, not just removed from the latest commit.
- Dedicated secret-management tooling in the Spring ecosystem, like [Spring Cloud Vault](0236-spring-cloud-vault-for-secrets.md), implements these guarantees so applications don't need to build secret storage themselves.
