---
card: system-design
gi: 174
slug: authentication-vs-authorization
title: Authentication vs authorization
---

## 1. What it is

**Authentication** answers "who are you?" — verifying a user's identity, usually via a password, a token, or a certificate. **Authorization** answers "what are you allowed to do?" — deciding whether an already-identified user may perform a specific action, such as reading a file or deleting an account. A system always authenticates first, then authorizes: you must know who someone is before you can decide what they can do.

## 2. Why & when

Confusing these two leads to real security bugs: a system that only checks "is this a valid, logged-in user" (authentication) but never checks "is this specific user allowed to view this specific resource" (authorization) lets any logged-in user access any other user's data. Every request that touches protected data or performs a sensitive action needs both checks, done in the right order and never skipped. Use this distinction to structure any access-control logic: verify identity first, then check permissions for the specific action being requested.

## 3. Core concept

- **Authentication mechanisms:** passwords, one-time codes, biometrics, client certificates, or a previously-issued token (a session ID or a [JWT](0177-jwt-structure-validation.md)) that proves the identity was already verified earlier.
- **Authorization mechanisms:** role-based access control (a user's role, like "admin" or "viewer", determines what they can do), or fine-grained per-resource permission checks (does *this* user own *this* specific record?).
- **Authentication happens once per session (or per request, for stateless tokens); authorization happens per action:** you log in once, but every single sensitive action still needs its own authorization check.
- **401 vs 403:** an HTTP `401 Unauthorized` response actually means "you are not authenticated" (who are you?); a `403 Forbidden` response means "you are authenticated, but not allowed to do this" (authorization failed) — the naming is a common source of confusion.
- **Never trust the client's claim of identity or permission:** both checks must happen on the server, using data the server itself controls (a validated token, a database lookup) — never based on a value the client simply sends and claims is true.

## 4. Diagram

```
   request: GET /documents/42, with an auth token

   step 1: AUTHENTICATION
      validate the token -> who is this? -> "user-17" (or reject: 401 Unauthorized)

   step 2: AUTHORIZATION
      does user-17 have permission to read document 42?
        - check: is user-17 the owner, or does their role allow it?
        - yes -> proceed, return the document
        - no  -> reject: 403 Forbidden (we know who you are, but not allowed)
```
*Caption: authentication establishes identity first; authorization then checks that specific identity's permission for the specific action requested.*

## 5. Runnable example

**Level 1 — Basic.** Authenticate a token to an identity.

**Level 2 — Authorize an action for that identity.** Check role-based permission separately from authentication.

**Level 3 — Fine-grained, per-resource authorization.** Check ownership of a specific resource, not just a general role.

```java
// AuthNvsAuthZDemo.java
import java.util.*;

public class AuthNvsAuthZDemo {

    static Map<String, String> validTokensToUserId = Map.of("token-abc", "user-17", "token-xyz", "user-42");
    static Map<String, String> userRoles = Map.of("user-17", "member", "user-42", "admin");
    static Map<Integer, String> documentOwners = Map.of(42, "user-17", 99, "user-42");

    // Level 1: authentication - who is this, based on their token?
    static String authenticate(String token) {
        String userId = validTokensToUserId.get(token);
        if (userId == null) throw new SecurityException("401 Unauthorized: invalid token");
        return userId;
    }

    // Level 2: authorization by role - can this role perform admin-only actions?
    static boolean isAdmin(String userId) {
        return "admin".equals(userRoles.get(userId));
    }

    // Level 3: fine-grained authorization - does this specific user own this specific document?
    static boolean canReadDocument(String userId, int documentId) {
        if (isAdmin(userId)) return true; // admins can read anything
        return userId.equals(documentOwners.get(documentId));
    }

    static void handleReadRequest(String token, int documentId) {
        String userId = authenticate(token); // step 1: who are you?
        System.out.println("authenticated as " + userId);
        if (!canReadDocument(userId, documentId)) { // step 2: are you allowed to do THIS?
            System.out.println("403 Forbidden: " + userId + " cannot read document " + documentId);
            return;
        }
        System.out.println("200 OK: " + userId + " reading document " + documentId);
    }

    public static void main(String[] args) {
        handleReadRequest("token-abc", 42); // user-17 reading their own document
        handleReadRequest("token-abc", 99); // user-17 trying to read user-42's document
        handleReadRequest("token-xyz", 99); // user-42 (admin) reading their own document
        handleReadRequest("token-xyz", 42); // user-42 (admin) reading user-17's document - allowed via admin role
        try {
            handleReadRequest("token-invalid", 42);
        } catch (SecurityException e) {
            System.out.println("caught: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `AuthNvsAuthZDemo.java`, then run `java AuthNvsAuthZDemo.java`.

## 6. Walkthrough

1. `handleReadRequest("token-abc", 42)` calls `authenticate`, which finds `"token-abc"` maps to `"user-17"` in `validTokensToUserId` — authentication succeeds, establishing identity before anything else is checked.
2. `canReadDocument("user-17", 42)` checks `isAdmin` first (false, since `user-17`'s role is `"member"`), then falls to `userId.equals(documentOwners.get(42))`; `documentOwners.get(42)` is `"user-17"`, which matches, so it returns `true`, and the request succeeds with `"200 OK"`.
3. `handleReadRequest("token-abc", 99)` authenticates the same `user-17` successfully again, but `canReadDocument("user-17", 99)` finds `documentOwners.get(99)` is `"user-42"`, not `"user-17"`, and `isAdmin("user-17")` is false — so it returns `false`, and the request is correctly rejected with `"403 Forbidden"`, despite the user being perfectly validly authenticated.
4. `handleReadRequest("token-xyz", 42)` authenticates as `"user-42"`; `canReadDocument("user-42", 42)` checks `isAdmin("user-42")` first, which is `true` (their role is `"admin"`), so the method returns `true` immediately without even checking ownership — the admin role grants access regardless of who actually owns document 42.
5. The final call, `handleReadRequest("token-invalid", 42)`, fails at the very first step: `authenticate` finds no entry for `"token-invalid"` in `validTokensToUserId` and throws a `SecurityException`, which is caught in `main` and printed — this request never even reaches the authorization check, since authentication itself failed first.

## 7. Gotchas & takeaways

> Gotcha: performing the authorization check using data supplied by the client (e.g. trusting a `userId` field sent in the request body, instead of the identity established during authentication) lets any authenticated user simply claim to be someone else for the purposes of the authorization check — always derive the identity used in authorization from the server-validated authentication step, never from client-supplied input.

- Authentication establishes identity; authorization decides what that identity may do — always in that order, and both are required for every sensitive action.
- `401` means "we don't know who you are"; `403` means "we know who you are, but you can't do this" — mixing these up confuses API consumers about what actually went wrong.
- Fine-grained (per-resource) authorization checks are often necessary beyond a simple role check, especially for ownership-based access.
- Related concepts: [Sessions vs tokens](0175-sessions-vs-tokens.md) (the mechanisms that carry an authenticated identity between requests), [OAuth2 & OpenID Connect](0176-oauth2-openid-connect.md) (standard protocols implementing authentication and delegated authorization), [JWT structure & validation](0177-jwt-structure-validation.md) (a common token format carrying the authenticated identity).
