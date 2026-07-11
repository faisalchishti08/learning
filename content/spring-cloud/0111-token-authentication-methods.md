---
card: spring-cloud
gi: 111
slug: token-authentication-methods
title: "Token & authentication methods"
---

## 1. What it is

Before an application can read any secret from Vault, it must authenticate to Vault itself, and Spring Cloud Vault supports several distinct authentication methods for this — a static token (the simplest, but least operationally ideal), AppRole (a role-id/secret-id pair designed specifically for machine-to-machine authentication), Kubernetes auth (using the pod's own service account token, requiring no separately-managed credential at all), and several others — each producing a Vault client token that's then used to authorize every subsequent secret read.

```properties
# static token -- simplest, but the token itself must be distributed and rotated manually
spring.cloud.vault.authentication=TOKEN
spring.cloud.vault.token=${VAULT_TOKEN}
```

```properties
# AppRole -- designed for machine authentication, no long-lived static credential needed
spring.cloud.vault.authentication=APPROLE
spring.cloud.vault.app-role.role-id=${VAULT_ROLE_ID}
spring.cloud.vault.app-role.secret-id=${VAULT_SECRET_ID}
```

## 2. Why & when

Reading secrets from Vault requires solving a bootstrapping problem: the application needs *some* credential to authenticate to Vault before it can fetch the actual secrets it needs, and that bootstrapping credential itself needs to be provisioned and secured somehow. A static token is the simplest possible answer but the weakest operationally — it's a long-lived, powerful credential that, once distributed (environment variable, mounted file), behaves exactly like any other static secret this whole system exists to avoid: if leaked, it remains valid until manually revoked. Kubernetes auth solves the bootstrapping problem more elegantly for applications actually running in Kubernetes: Vault trusts the Kubernetes API server itself to vouch for a pod's identity via its service account token, so the application authenticates using a credential the platform already provisions and rotates automatically, with nothing extra for the application team to manage.

Reach for a specific authentication method when:

- Running in Kubernetes — Kubernetes auth is almost always the better choice over a static token, since it relies on infrastructure the platform already manages (service account tokens), eliminating a separately-distributed Vault credential entirely.
- Running outside Kubernetes, in an environment with its own strong machine identity mechanism (a cloud provider's instance metadata service, for instance) — the corresponding cloud-specific Vault auth method (AWS IAM auth, Azure auth) similarly avoids a separately-managed static credential.
- No stronger platform-provided identity mechanism is available, and a human operator must provision the initial credential — AppRole is the standard middle ground: a role-id (less sensitive, can be embedded in configuration) paired with a secret-id (sensitive, distributed more carefully, and often itself short-lived or single-use) balances security against operational simplicity better than a single, fully static token.

## 3. Core concept

```
 static TOKEN auth:
   application already HAS a Vault token (distributed some other way) -> uses it directly

 APPROLE auth:
   application has role-id + secret-id -> exchanges them WITH Vault -> Vault issues a SHORT-LIVED client token
   -> application uses THAT token for subsequent secret reads (not the role-id/secret-id directly)

 KUBERNETES auth:
   application (running as a pod) has its Kubernetes service-account token (auto-mounted by the platform)
   -> presents it to Vault -> Vault verifies it WITH the Kubernetes API server -> issues a Vault client token
   -> NO separately-provisioned Vault credential needed at all
```

Every method's end goal is the same: obtain a Vault client token — the methods differ entirely in *how* the application proves its identity to get that token in the first place.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three different authentication methods each ultimately produce a Vault client token that is then used identically for all subsequent secret reads regardless of which method obtained it">
  <rect x="20" y="20" width="150" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="95" y="44" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">static token</text>
  <rect x="20" y="80" width="150" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="95" y="104" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">AppRole (role-id/secret-id)</text>
  <rect x="20" y="140" width="150" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="95" y="164" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Kubernetes service-account</text>

  <rect x="260" y="80" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="335" y="108" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Vault client token</text>

  <rect x="480" y="80" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="550" y="108" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">secret reads</text>

  <defs><marker id="a111" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="170" y1="40" x2="260" y2="95" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a111)"/>
  <line x1="170" y1="100" x2="260" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a111)"/>
  <line x1="170" y1="160" x2="260" y2="110" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a111)"/>
  <line x1="410" y1="103" x2="480" y2="103" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a111)"/>
</svg>

Three different paths in, one uniform token out — everything downstream of authentication behaves identically regardless of which method produced the token.

## 5. Runnable example

The scenario: model two authentication methods (static token and AppRole) that both ultimately produce a client token used identically for subsequent secret reads, proving the downstream secret-reading code is authentication-method-agnostic. Start with static token auth as the baseline, then add AppRole's exchange step, then add Kubernetes-style auth with a short-lived, platform-provided credential, showing all three converge to the same downstream shape.

### Level 1 — Basic

Static token authentication — the application already possesses a Vault token directly.

```java
public class VaultAuthLevel1 {
    static class VaultClient {
        String clientToken;
        VaultClient(String clientToken) { this.clientToken = clientToken; }
        String readSecret(String path) {
            System.out.println("reading " + path + " using token " + clientToken);
            return "secret-value-for-" + path;
        }
    }

    public static void main(String[] args) {
        String staticToken = "s.abc123xyz"; // provisioned some OTHER way -- env var, mounted file, etc.
        VaultClient client = new VaultClient(staticToken);

        System.out.println(client.readSecret("secret/order-service/api-key"));
    }
}
```

How to run: `java VaultAuthLevel1.java`

The `staticToken` is used directly, with no exchange step — simple, but this token is a long-lived credential that itself needs separate secure provisioning and eventual rotation, which is precisely the operational weakness the other methods address.

### Level 2 — Intermediate

Add AppRole authentication: an exchange step converts a role-id/secret-id pair into a Vault client token, which is then used identically to Level 1's static token for subsequent reads.

```java
public class VaultAuthLevel2 {
    static class VaultClient {
        String clientToken;
        VaultClient(String clientToken) { this.clientToken = clientToken; }
        String readSecret(String path) {
            System.out.println("reading " + path + " using token " + clientToken);
            return "secret-value-for-" + path;
        }
    }

    // models Vault's auth/approle/login endpoint
    static VaultClient authenticateWithAppRole(String roleId, String secretId) {
        System.out.println("exchanging role-id/secret-id for a client token...");
        String issuedToken = "s.approle-issued-" + roleId.substring(0, 4); // Vault issues a FRESH token per login
        return new VaultClient(issuedToken);
    }

    public static void main(String[] args) {
        String roleId = "role-order-service";   // less sensitive -- can live in configuration
        String secretId = "secret-id-9f8e7d";    // sensitive -- distributed more carefully

        VaultClient client = authenticateWithAppRole(roleId, secretId);
        System.out.println(client.readSecret("secret/order-service/api-key")); // SAME readSecret as Level 1
    }
}
```

How to run: `java VaultAuthLevel2.java`

`authenticateWithAppRole` performs the exchange step Level 1 skipped, producing a `VaultClient` with a freshly-issued token — but once constructed, `client.readSecret` is called exactly the same way it was in Level 1, because downstream secret-reading code never needs to know which authentication method originally produced the client's token.

### Level 3 — Advanced

Add Kubernetes-style authentication (a platform-provided, auto-rotated service account token exchanged for a Vault token), and demonstrate all three methods converging to the same downstream `readSecret` call, proving authentication method is fully decoupled from secret consumption.

```java
public class VaultAuthLevel3 {
    static class VaultClient {
        String clientToken;
        String authMethod;
        VaultClient(String clientToken, String authMethod) { this.clientToken = clientToken; this.authMethod = authMethod; }
        String readSecret(String path) {
            System.out.println("[" + authMethod + "] reading " + path + " using token " + clientToken);
            return "secret-value-for-" + path;
        }
    }

    static VaultClient authenticateWithStaticToken(String token) {
        return new VaultClient(token, "TOKEN");
    }

    static VaultClient authenticateWithAppRole(String roleId, String secretId) {
        return new VaultClient("s.approle-issued-" + roleId.substring(0, 4), "APPROLE");
    }

    // models Vault verifying a pod's service-account token WITH the Kubernetes API server
    static VaultClient authenticateWithKubernetes(String serviceAccountToken) {
        System.out.println("Vault verifying service-account token with the Kubernetes API server...");
        return new VaultClient("s.k8s-issued-" + serviceAccountToken.substring(0, 4), "KUBERNETES");
    }

    // ONE function reads a secret from ANY authenticated client, regardless of auth method used to obtain it
    static void demonstrateRead(VaultClient client, String path) {
        System.out.println(client.readSecret(path));
    }

    public static void main(String[] args) {
        VaultClient tokenClient = authenticateWithStaticToken("s.abc123xyz");
        VaultClient appRoleClient = authenticateWithAppRole("role-order-service", "secret-id-9f8e7d");
        VaultClient k8sClient = authenticateWithKubernetes("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...");

        demonstrateRead(tokenClient, "secret/order-service/api-key");
        demonstrateRead(appRoleClient, "secret/order-service/api-key");
        demonstrateRead(k8sClient, "secret/order-service/api-key");
    }
}
```

How to run: `java VaultAuthLevel3.java`

`demonstrateRead` is called three times with three `VaultClient` instances produced by three completely different authentication flows, yet `demonstrateRead`'s own code is a single, unchanged one-line function — this is the practical proof that once authentication produces a client token, absolutely nothing downstream (secret reading, in this example) needs to branch on or even know which method was used to obtain it.

## 6. Walkthrough

Trace `authenticateWithKubernetes` in Level 3.

1. `authenticateWithKubernetes("eyJhbGci...")` is called with a value modeling a Kubernetes service-account token — in a real cluster, this token is automatically mounted into every pod's filesystem by the platform, requiring no manual provisioning by the application team at all.
2. `println` reports that Vault is verifying this token with the Kubernetes API server — this models the real Kubernetes auth flow: Vault doesn't trust the token blindly, it calls back to the Kubernetes API server to confirm the token is genuinely valid and belongs to the service account it claims to.
3. Assuming that verification succeeds (modeled here unconditionally, for simplicity), a new `VaultClient` is constructed with a freshly-issued token (`"s.k8s-issued-eyJh"`, derived from a substring of the input for illustration) and `authMethod = "KUBERNETES"`.
4. `demonstrateRead(k8sClient, "secret/order-service/api-key")` is called — inside, `client.readSecret(path)` executes, printing `"[KUBERNETES] reading secret/order-service/api-key using token s.k8s-issued-eyJh"`.
5. Comparing this to the equivalent calls for `tokenClient` and `appRoleClient`: all three produce a structurally identical log line, differing only in the `authMethod` tag and the specific token value — `readSecret`'s own implementation is completely unaware of, and unaffected by, which authentication method was used upstream.

```
authenticateWithKubernetes(serviceAccountToken)
  Vault verifies token WITH the Kubernetes API server (external trust check)
  -> issues a fresh Vault client token: "s.k8s-issued-eyJh"
  -> VaultClient(token, "KUBERNETES") constructed

demonstrateRead(k8sClient, path) -> client.readSecret(path) -> IDENTICAL call shape to the TOKEN and APPROLE clients
```

## 7. Gotchas & takeaways

> **Gotcha:** a static Vault token, once distributed to an application (as an environment variable, a mounted file), is itself a long-lived secret that needs the same operational care as any other static credential — accidentally logging it, committing it to a repository, or leaving it in a container image layer defeats much of the security benefit Vault was introduced to provide in the first place. This is precisely why AppRole and Kubernetes auth (and other platform-integrated methods) are generally preferred over static token auth wherever the target platform supports them.

- Every Vault authentication method converges on the same end result — a client token — and every operation downstream of authentication (secret reads, lease renewal) behaves identically regardless of which method produced that token.
- Static token authentication is the simplest to configure but reintroduces the exact static-credential-distribution problem Vault otherwise solves for application secrets — reserve it for situations with no better platform-integrated alternative, such as local development.
- AppRole's role-id/secret-id split allows the less-sensitive role-id to live in ordinary configuration while the more-sensitive secret-id is distributed through a more carefully controlled channel (and can itself be made single-use or short-lived), striking a reasonable balance for environments without a stronger platform identity mechanism.
- Kubernetes auth (and equivalent cloud-provider-native auth methods) is generally the strongest practical option when available, since it relies entirely on identity infrastructure the platform already manages and rotates, eliminating a separately-provisioned Vault credential from the application's concerns altogether.
