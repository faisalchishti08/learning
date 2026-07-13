---
card: microservices
gi: 386
slug: oauth2-roles-resource-owner-client-auth-server-resource-serv
title: "OAuth2 roles (resource owner, client, auth server, resource server)"
---

## 1. What it is

**OAuth2** is a standard protocol for **delegated authorization** — letting one application access a user's resources on another service *without* that application ever seeing the user's password. It defines four distinct roles that participate in every OAuth2 interaction: the **resource owner** (typically the end user), the **client** (the application requesting access), the **authorization server** (which authenticates the resource owner and issues tokens), and the **resource server** (which hosts the protected data and accepts those tokens). Understanding these four roles precisely is the foundation for everything else in OAuth2 — the [grant types](0387-oauth2-grant-types-flows-auth-code-client-credentials-etc.md), [OpenID Connect](0388-openid-connect-oidc.md), and [token relay](0389-token-relay-propagation-between-services.md) all build directly on this vocabulary.

## 2. Why & when

OAuth2 exists to solve a specific, painful problem: before it, if you wanted a third-party app to access your data on another service (say, a photo-printing app that needs to read your photos from a cloud storage service), the only option was to hand the third-party app your actual cloud storage password. That app could then do *anything* your account could do, forever, until you changed your password — a wildly excessive amount of trust for "please read my photos."

You need OAuth2's role model whenever:

- **An application needs limited access to a user's data on another service**, without ever holding that user's actual credentials for the other service.
- **You want revocable, scoped access.** The user can grant an app access to *only* `photos:read`, not full account control, and can revoke that access later without changing their password.
- **You're building microservices that need to call each other, or call third-party APIs, on behalf of a user or as themselves** — the same role model (adapted slightly) underlies both user-delegated access and machine-to-machine service calls (see the client-credentials grant in [OAuth2 grant types](0387-oauth2-grant-types-flows-auth-code-client-credentials-etc.md)).
- **You need a standard your framework already supports.** Spring Security's OAuth2 client and resource-server modules are built directly around these four roles, so understanding them is a prerequisite to configuring either correctly.

## 3. Core concept

Think of a hotel valet system. You (the **resource owner**) own the car. The valet company's front desk (the **authorization server**) is who you trust to hand out valet keys — a special key that only starts the car and opens the trunk, not the glove compartment lock or your house key that happens to be on the same ring. The valet attendant (the **client**) never sees your actual house key or full keyring; they're handed a limited valet key by the front desk, only after you've authorized it. The parking garage (the **resource server**) is where your car actually lives, and it accepts the valet key as sufficient proof to release your car — while still trusting that the front desk did the real vetting.

Concretely, the four roles are:

1. **Resource owner** — the entity capable of granting access to a protected resource. Usually a human user, but can be a system in machine-to-machine flows.
2. **Client** — the application requesting access to the resource on the resource owner's behalf. This could be a web app, a mobile app, or another service. Critically, **the client is never handed the resource owner's actual password** — that's the entire point of the protocol.
3. **Authorization server** — the system that authenticates the resource owner (or verifies the client's own credentials in machine-to-machine flows) and, on success, issues **access tokens** (and often refresh tokens) to the client. This is the system that runs the actual login screen and consent prompt.
4. **Resource server** — the API that hosts the protected resources and accepts access tokens as proof of authorization, without needing to know how the user originally authenticated — it just needs to trust and validate the token, using the mechanisms covered in [token-based security](0383-token-based-security.md), [JWT validation](0384-json-web-token-jwt-structure-validation.md), or [introspection](0385-opaque-tokens-token-introspection.md).

In many real deployments the authorization server and resource server are operated by the same organization (or even the same process for a simple system), but the roles remain conceptually distinct — and in microservices architectures, it's common for *one* central authorization server to issue tokens that *many* independent resource servers (your various microservices) all validate.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four OAuth2 roles: the resource owner grants consent, the authorization server issues a token to the client after authenticating the resource owner, and the client presents that token to the resource server to access protected data" font-family="sans-serif">
  <rect x="20" y="20" width="120" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="80" y="42" fill="#79c0ff" font-size="10" text-anchor="middle">Resource owner</text>
  <text x="80" y="58" fill="#8b949e" font-size="8" text-anchor="middle">(the user)</text>

  <rect x="20" y="190" width="120" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="80" y="212" fill="#f0883e" font-size="10" text-anchor="middle">Client</text>
  <text x="80" y="228" fill="#8b949e" font-size="8" text-anchor="middle">(the app)</text>

  <rect x="260" y="20" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="335" y="45" fill="#6db33f" font-size="10" text-anchor="middle">Authorization server</text>
  <text x="335" y="62" fill="#8b949e" font-size="8" text-anchor="middle">authenticates owner,</text>
  <text x="335" y="74" fill="#8b949e" font-size="8" text-anchor="middle">issues token</text>

  <rect x="480" y="190" width="140" height="50" rx="8" fill="#1c2430" stroke="#e6edf3" stroke-width="2"/>
  <text x="550" y="212" fill="#e6edf3" font-size="10" text-anchor="middle">Resource server</text>
  <text x="550" y="228" fill="#8b949e" font-size="8" text-anchor="middle">validates token,</text>

  <line x1="140" y1="45" x2="260" y2="45" stroke="#79c0ff" marker-end="url(#a5)"/>
  <text x="200" y="35" fill="#79c0ff" font-size="8" text-anchor="middle">1. consent</text>
  <line x1="260" y1="60" x2="140" y2="210" stroke="#6db33f" marker-end="url(#a5)"/>
  <text x="170" y="140" fill="#6db33f" font-size="8" text-anchor="middle">2. token issued</text>
  <line x1="140" y1="215" x2="480" y2="215" stroke="#f0883e" marker-end="url(#a5)"/>
  <text x="300" y="205" fill="#f0883e" font-size="8" text-anchor="middle">3. request + token</text>
  <defs>
    <marker id="a5" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

The resource owner consents once at the authorization server, which issues a token to the client; the client then presents that token — not the owner's password — to the resource server.

## 5. Runnable example

Scenario: a photo-printing client app wants read access to a user's photos, hosted by a separate photo-storage resource server. We simulate the four roles interacting, starting with the broken "hand over the password" anti-pattern, then proper delegated authorization, then a realistic machine-to-machine variant where the client is itself a backend service.

### Level 1 — Basic

```java
// File: PasswordSharingAntiPattern.java -- the problem OAuth2 exists to fix: the
// client is handed the resource owner's ACTUAL password, giving it full, unlimited,
// unrevocable-without-a-password-change access.
import java.util.*;

public class PasswordSharingAntiPattern {
    static final Map<String, String> USER_PASSWORDS = Map.of("alice", "hunter2");

    // The client is handed the RAW password directly -- can do ANYTHING alice's account can do.
    static String printingAppFetchesPhotos(String username, String password) {
        if (!password.equals(USER_PASSWORDS.get(username))) {
            return "DENIED: wrong password";
        }
        return "Full account access granted to the printing app -- it could also delete photos, change settings, etc.";
    }

    public static void main(String[] args) {
        System.out.println(printingAppFetchesPhotos("alice", "hunter2"));
        System.out.println("The printing app only needed to READ photos, but now holds a password good for EVERYTHING.");
    }
}
```

How to run: `java PasswordSharingAntiPattern.java`

The printing app only ever needed read access to photos, but handing it the raw password gives it unlimited access to everything the account can do, indefinitely, until the password is changed. There's no way to grant "just photos, just read, just for a while" — this all-or-nothing trust is exactly the problem OAuth2's role separation exists to eliminate.

### Level 2 — Intermediate

```java
// File: FourRoleDelegation.java -- models the four OAuth2 roles interacting properly:
// resource owner consents at the auth server, the auth server issues a SCOPED token
// to the client, and the client presents that token (never the password) to the resource server.
import java.util.*;

public class FourRoleDelegation {
    static final Map<String, String> USER_PASSWORDS = Map.of("alice", "hunter2");

    // AUTHORIZATION SERVER: authenticates the resource owner, issues a scoped token.
    static class AuthorizationServer {
        static String authenticateAndIssueToken(String username, String password, String requestedScope) {
            if (!password.equals(USER_PASSWORDS.get(username))) return null;
            return "token-for-" + username + "-scope-" + requestedScope; // deliberately simplified token
        }
    }

    // RESOURCE SERVER: hosts photos, trusts tokens from the authorization server, never sees the password.
    static class ResourceServer {
        static String getPhotos(String token) {
            if (token == null || !token.contains("scope-photos:read")) {
                return "403: token missing or insufficient scope";
            }
            String username = token.split("-")[2]; // extract for display only
            return "Photos returned for '" + username + "' -- resource server NEVER saw a password";
        }
    }

    public static void main(String[] args) {
        // The CLIENT (printing app) never receives the password -- only the resulting token.
        String token = AuthorizationServer.authenticateAndIssueToken("alice", "hunter2", "photos:read");
        System.out.println("Client (printing app) received scoped token: " + token);
        System.out.println(ResourceServer.getPhotos(token));
    }
}
```

How to run: `java FourRoleDelegation.java`

The four roles are now distinct classes/participants: `USER_PASSWORDS` (owned conceptually by the resource owner and only ever checked by the authorization server), `AuthorizationServer` (which is the *only* place a password is checked), and `ResourceServer` (which never sees a password at all — only a token). The "client" in this simplified example is just the flow of control in `main`, receiving a token, not a password, and presenting that token onward.

### Level 3 — Advanced

```java
// File: MachineToMachineRoles.java -- a REALISTIC variant: the "client" is itself a
// backend service (an inventory-sync job) acting as ITS OWN identity, not on behalf
// of a human user -- the resource owner and client roles COLLAPSE into one machine
// identity, which is common for service-to-service OAuth2 (client_credentials grant).
import java.util.*;

public class MachineToMachineRoles {
    // In machine-to-machine flows, "clients" are registered with their OWN credentials -- no human involved.
    static final Map<String, String> CLIENT_SECRETS = Map.of("inventory-sync-job", "client-secret-xyz");
    static final Map<String, String> CLIENT_ALLOWED_SCOPES = Map.of("inventory-sync-job", "inventory:write");

    static class AuthorizationServer {
        // Authenticates the CLIENT ITSELF (not a human resource owner) and issues a token scoped to what THAT client is allowed.
        static String issueClientToken(String clientId, String clientSecret, String requestedScope) {
            if (!clientSecret.equals(CLIENT_SECRETS.get(clientId))) {
                return null; // client authentication failed
            }
            String allowedScope = CLIENT_ALLOWED_SCOPES.get(clientId);
            if (!requestedScope.equals(allowedScope)) {
                return null; // requesting a scope this client was never registered for
            }
            return "token-for-client-" + clientId + "-scope-" + requestedScope;
        }
    }

    static class ResourceServer {
        static String updateInventory(String token, String sku, int quantity) {
            if (token == null || !token.contains("scope-inventory:write")) {
                return "403: token missing or insufficient scope for inventory writes";
            }
            return "Inventory updated: sku=" + sku + " qty=" + quantity + " (via token: " + token + ")";
        }
    }

    public static void main(String[] args) {
        // Legitimate: correct client secret, requesting the scope it's actually registered for.
        String validToken = AuthorizationServer.issueClientToken("inventory-sync-job", "client-secret-xyz", "inventory:write");
        System.out.println("Issued: " + validToken);
        System.out.println(ResourceServer.updateInventory(validToken, "sku-42", 100));

        // Same client, WRONG secret (e.g. leaked/rotated credential mismatch).
        String badSecretToken = AuthorizationServer.issueClientToken("inventory-sync-job", "wrong-secret", "inventory:write");
        System.out.println(ResourceServer.updateInventory(badSecretToken, "sku-42", 100));

        // Same client, correct secret, but requesting a scope it was NEVER registered for.
        String overreachToken = AuthorizationServer.issueClientToken("inventory-sync-job", "client-secret-xyz", "inventory:delete-all");
        System.out.println(ResourceServer.updateInventory(overreachToken, "sku-42", 100));
    }
}
```

How to run: `java MachineToMachineRoles.java`

This models the `client_credentials` grant (detailed further in [OAuth2 grant types](0387-oauth2-grant-types-flows-auth-code-client-credentials-etc.md)): there's no human resource owner in the loop at all, because the "client" (a backend inventory-sync job) is authenticating *as itself*. `issueClientToken` checks two things: does the client know its own registered secret, and is the requested scope one it's actually allowed to request? A wrong secret fails outright. A correct secret but an over-reaching scope request (`inventory:delete-all`, which was never granted to this client) is also refused — the authorization server enforces that clients can't simply ask for more than they were registered for.

## 6. Walkthrough

Trace `MachineToMachineRoles.main` in order. **First**, `issueClientToken("inventory-sync-job", "client-secret-xyz", "inventory:write")` runs. `clientSecret.equals(CLIENT_SECRETS.get("inventory-sync-job"))` compares `"client-secret-xyz"` to the registered secret, which matches. `CLIENT_ALLOWED_SCOPES.get("inventory-sync-job")` returns `"inventory:write"`, and the requested scope equals that exactly — both checks pass, and a token string is returned. `ResourceServer.updateInventory` then checks the token contains `"scope-inventory:write"`, which it does, and the inventory update succeeds.

**Next**, `issueClientToken("inventory-sync-job", "wrong-secret", "inventory:write")` runs. The secret comparison fails immediately (`"wrong-secret"` does not equal the registered `"client-secret-xyz"`), so the method returns `null` before scope is even considered. `updateInventory(null, ...)` then checks `token == null`, which is true, and returns `"403: token missing or insufficient scope"`.

**Then**, `issueClientToken("inventory-sync-job", "client-secret-xyz", "inventory:delete-all")` runs. This time the secret is correct, so the first check passes — but `CLIENT_ALLOWED_SCOPES.get("inventory-sync-job")` is `"inventory:write"`, which does not equal the requested `"inventory:delete-all"`. The method returns `null` here too, and the resulting call to `updateInventory(null, ...)` is again denied — demonstrating that having valid credentials doesn't mean a client can request any scope it wants; the authorization server enforces what each registered client is actually entitled to.

```
valid secret + registered scope       -> token issued -> inventory updated
wrong secret                           -> token = null -> 403 (token missing)
valid secret + UNREGISTERED scope      -> token = null -> 403 (over-reach blocked at issuance)
```

## 7. Gotchas & takeaways

> A subtle but important point: the resource server in Level 2 and Level 3 never authenticates the resource owner or the client itself — it only ever validates a *token*. This is precisely why the resource server can remain simple and stateless with respect to credentials, but it also means the resource server's security is entirely dependent on the authorization server issuing tokens correctly and the resource server validating them correctly (signature/expiry/scope, as covered in [JWT validation](0384-json-web-token-jwt-structure-validation.md) or [introspection](0385-opaque-tokens-token-introspection.md)) — a bug in either place compromises the whole chain.

- The four roles — resource owner, client, authorization server, resource server — are distinct even when the same organization operates more than one of them.
- The client never sees the resource owner's password; it only ever receives a scoped, revocable token from the authorization server.
- In machine-to-machine scenarios, the resource owner and client roles effectively collapse into one machine identity, authenticating with its own registered credentials rather than a human's.
- A resource server's trust boundary is the token, not the caller's network location — reinforcing [zero-trust networking](0380-zero-trust-networking.md): the resource server independently validates every token, every time.
- This role model is the foundation for the specific [grant types](0387-oauth2-grant-types-flows-auth-code-client-credentials-etc.md) (authorization code, client credentials, etc.) and for [OpenID Connect](0388-openid-connect-oidc.md), which layers user identity information on top of pure authorization.
