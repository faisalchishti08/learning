---
card: spring-security
gi: 96
slug: oidc-user-info-id-token
title: "OIDC user info & ID token"
---

## 1. What it is

An authenticated `OidcUser` actually carries **two** distinct sources of profile data, and understanding the difference matters: the **ID token** (`OidcIdToken`, obtained directly in the token exchange of card 0095, signed and cryptographically verifiable) and the **UserInfo response** (`OidcUserInfo`, an additional, optional HTTP call to the provider's standardized `/userinfo` endpoint using the access token as a bearer credential, *not* independently signed). Spring Security fetches both when a `userInfoUri` is configured, then merges their claims into one combined view exposed via `OidcUser.getClaims()` — but `getIdToken()` and `getUserInfo()` remain separately accessible because they carry different trust guarantees and different claim sets.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http.oauth2Login(oauth2 -> oauth2
        .userInfoEndpoint(userInfo -> userInfo
            .oidcUserService(this::loadUser))); // customize how OidcUser is assembled
    return http.build();
}

private OidcUser loadUser(OidcUserRequest request) {
    OidcUser user = new OidcUserService().loadUser(request);
    System.out.println("id_token claims: " + user.getIdToken().getClaims());
    System.out.println("userinfo claims: " + user.getUserInfo() != null ? user.getUserInfo().getClaims() : "none");
    return user;
}
```

## 2. Why & when

The two sources exist because they serve different purposes in the OIDC spec: the ID token is meant to be a compact, self-contained proof of *authentication* — who signed in and when — validated once at login time and then typically discarded from active use (it isn't meant to be sent to other APIs). The UserInfo endpoint exists because cramming every possible profile field (`picture`, `locale`, `phone_number`, custom claims) into a JWT that gets passed around defeats the "compact" part of the design, and some profile data can change between logins (a user updates their profile picture) without needing to invalidate the entire ID token. Fetching UserInfo separately, using the access token, lets an application pull fresh, possibly larger profile data on demand, at the cost of one extra HTTP round trip and slightly weaker guarantees (the response isn't signed the way the ID token is, so it's only as trustworthy as the TLS connection and the provider serving it correctly).

Reach for distinguishing them explicitly when:

- Deciding which claim to trust for something security-sensitive — always prefer the ID token's claims (`sub`, `iss`, `aud`) for identity decisions, since they're signed and validated; use UserInfo claims for display purposes (name, picture) where authenticity is less critical.
- A provider's UserInfo endpoint is slow, rate-limited, or unavailable — since it's a genuinely separate optional HTTP call, `oidcUserService` can be customized to skip it and rely on ID token claims alone when they're sufficient.
- Debugging why an expected profile field (like `email_verified`) is missing — it might be present in one source but not the other, or require an additional scope (`email`, `profile`) to be requested for either endpoint to return it.
- Building a custom `OidcUser` (card 0098) that merges these two sources differently — for instance, always preferring the UserInfo response's `picture` over a stale one baked into the ID token at login time.

## 3. Core concept

```
OidcIdToken (from the TOKEN exchange, card 0095's exchange step):
    SIGNED by the provider -- verifiable, tamper-evident
    Standard claims: iss, sub, aud, exp, iat, (nonce)
    Meant for: proving WHO authenticated and WHEN -- not for re-sending to other APIs
    Available via: oidcUser.getIdToken().getClaims()

OidcUserInfo (from a SEPARATE HTTP call to the provider's /userinfo endpoint):
    Authenticated by: presenting the access_token as a Bearer credential
    NOT independently signed -- trust depends on the TLS channel + the provider being honest
    Richer, provider-defined claims: name, picture, locale, phone_number, custom fields
    OPTIONAL -- only fetched if userInfoUri is configured AND access_token has sufficient scope
    Available via: oidcUser.getUserInfo().getClaims() -- may be null if this call wasn't made

oidcUser.getClaims() -- a MERGED view: id_token claims + userinfo claims, userinfo often taking
                        precedence for overlapping keys since it's the fresher of the two calls
```

`getName()` on an `OidcUser` resolves via the `userNameAttributeName` configured on the `ClientRegistration` (card 0089) against this merged claim set — usually `"sub"`.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing the token endpoint returning a signed id token which is validated and separately the access token being used to call the userinfo endpoint returning unsigned but richer profile claims both feeding into a merged OidcUser claims view">
  <rect x="20" y="30" width="270" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="52" fill="#6db33f" font-size="10.5" text-anchor="middle" font-family="sans-serif">OidcIdToken</text>
  <text x="155" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">from token endpoint, SIGNED</text>
  <text x="155" y="86" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">iss, sub, aud, exp, iat</text>
  <text x="155" y="102" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">verifiable / tamper-evident</text>

  <rect x="350" y="30" width="270" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="485" y="52" fill="#79c0ff" font-size="10.5" text-anchor="middle" font-family="sans-serif">OidcUserInfo</text>
  <text x="485" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">from /userinfo, using access_token</text>
  <text x="485" y="86" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">name, picture, locale, ...</text>
  <text x="485" y="102" fill="#f0883e" font-size="8.5" text-anchor="middle" font-family="sans-serif">NOT independently signed</text>

  <line x1="155" y1="120" x2="300" y2="165" stroke="#6db33f" stroke-width="1.5" marker-end="url(#u96)"/>
  <line x1="485" y1="120" x2="340" y2="165" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#u96)"/>

  <rect x="220" y="170" width="200" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.4"/>
  <text x="320" y="192" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OidcUser.getClaims()</text>
  <text x="320" y="207" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">merged view of both sources</text>

  <defs><marker id="u96" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The ID token is signed proof of authentication; UserInfo is a richer, separately-fetched, unsigned profile — both feed the merged claim view.

## 5. Runnable example

The scenario: model an ID token and a separately-fetched UserInfo response, merge them into a combined claims view, then handle the case where UserInfo disagrees with the ID token (a changed profile picture) and where the UserInfo call fails or is skipped entirely.

### Level 1 — Basic

Two claim maps, merged into one.

```java
import java.util.*;

public class OidcUserInfoLevel1 {
    record IdToken(Map<String, Object> claims) {}
    record UserInfo(Map<String, Object> claims) {}

    static Map<String, Object> mergeClaims(IdToken idToken, UserInfo userInfo) {
        Map<String, Object> merged = new LinkedHashMap<>(idToken.claims());
        if (userInfo != null) merged.putAll(userInfo.claims()); // userinfo's claims win on overlapping keys
        return merged;
    }

    public static void main(String[] args) {
        IdToken idToken = new IdToken(Map.of(
                "iss", "https://accounts.google.com",
                "sub", "109283746",
                "aud", "abc123"));

        UserInfo userInfo = new UserInfo(Map.of(
                "sub", "109283746",
                "name", "Alice Example",
                "picture", "https://example.com/alice.jpg"));

        Map<String, Object> merged = mergeClaims(idToken, userInfo);
        System.out.println("merged claims: " + new TreeMap<>(merged));
    }
}
```

**How to run:** save as `OidcUserInfoLevel1.java`, run `java OidcUserInfoLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
merged claims: {aud=abc123, iss=https://accounts.google.com, name=Alice Example, picture=https://example.com/alice.jpg, sub=109283746}
```

`mergeClaims` starts from the ID token's claims and layers UserInfo's on top — since `sub` appears in both and agrees, the merged value is unaffected; `name` and `picture` only exist in UserInfo and are simply added.

### Level 2 — Intermediate

Model the actual HTTP call to `/userinfo` (using the access token as a Bearer credential) as a separate, potentially skippable step, and show that UserInfo's `sub` must match the ID token's `sub` — a mismatch here is a serious problem, not just noise.

```java
import java.util.*;

public class OidcUserInfoLevel2 {
    record IdToken(Map<String, Object> claims) {}
    record UserInfo(Map<String, Object> claims) {}

    static class UserInfoEndpoint {
        private final Map<String, UserInfo> bySubject = new HashMap<>();
        void register(String subject, UserInfo info) { bySubject.put(subject, info); }

        // simulates: GET /userinfo, Authorization: Bearer <accessToken>
        UserInfo fetch(String accessToken, String expectedSubjectForToken) {
            System.out.println("GET /userinfo with Authorization: Bearer " + accessToken);
            return bySubject.get(expectedSubjectForToken);
        }
    }

    static class SubjectMismatchException extends RuntimeException {
        SubjectMismatchException(String message) { super(message); }
    }

    static Map<String, Object> loadMergedClaims(IdToken idToken, UserInfoEndpoint endpoint, String accessToken) {
        String idTokenSubject = String.valueOf(idToken.claims().get("sub"));
        UserInfo userInfo = endpoint.fetch(accessToken, idTokenSubject);

        Map<String, Object> merged = new LinkedHashMap<>(idToken.claims());
        if (userInfo != null) {
            String userInfoSubject = String.valueOf(userInfo.claims().get("sub"));
            if (!idTokenSubject.equals(userInfoSubject)) {
                // the SAME access token must describe the SAME subject as the id_token -- otherwise something is very wrong
                throw new SubjectMismatchException("id_token sub=" + idTokenSubject + " but userinfo sub=" + userInfoSubject);
            }
            merged.putAll(userInfo.claims());
        }
        return merged;
    }

    public static void main(String[] args) {
        UserInfoEndpoint endpoint = new UserInfoEndpoint();
        endpoint.register("109283746", new UserInfo(Map.of(
                "sub", "109283746", "name", "Alice Example", "picture", "https://example.com/alice-new.jpg")));

        IdToken idToken = new IdToken(Map.of("iss", "https://accounts.google.com", "sub", "109283746", "aud", "abc123"));

        Map<String, Object> merged = loadMergedClaims(idToken, endpoint, "access-tok-abc");
        System.out.println("merged: " + new TreeMap<>(merged));
    }
}
```

**How to run:** save as `OidcUserInfoLevel2.java`, run `java OidcUserInfoLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
GET /userinfo with Authorization: Bearer access-tok-abc
merged: {aud=abc123, iss=https://accounts.google.com, name=Alice Example, picture=https://example.com/alice-new.jpg, sub=109283746}
```

What changed: the UserInfo call is now a real request modeled with an `Authorization: Bearer` header, and — critically — `loadMergedClaims` verifies that UserInfo's `sub` agrees with the ID token's `sub` before merging anything; this check mirrors `OidcUserService`'s real behavior, which throws exactly this kind of error if a provider's UserInfo response ever disagreed with its own ID token on identity.

### Level 3 — Advanced

The UserInfo call can fail (network error, provider outage, insufficient scope) or simply not be configured at all — a robust `OidcUser` assembly must fall back gracefully to ID-token-only claims rather than failing the entire login over an optional enhancement.

```java
import java.util.*;
import java.util.function.*;

public class OidcUserInfoLevel3 {
    record IdToken(Map<String, Object> claims) {}
    record UserInfo(Map<String, Object> claims) {}
    record OidcUser(IdToken idToken, UserInfo userInfo, Map<String, Object> mergedClaims) {
        boolean hasUserInfo() { return userInfo != null; }
    }

    static class UserInfoEndpoint {
        private final Map<String, UserInfo> bySubject = new HashMap<>();
        private final Set<String> unreachableFor = new HashSet<>();

        void register(String subject, UserInfo info) { bySubject.put(subject, info); }
        void simulateOutageFor(String subject) { unreachableFor.add(subject); }

        UserInfo fetch(String subject) {
            if (unreachableFor.contains(subject)) throw new RuntimeException("connection timed out");
            return bySubject.get(subject);
        }
    }

    // mirrors OidcUserService.loadUser: userinfo is OPTIONAL -- its absence or failure must not break login
    static OidcUser assembleOidcUser(IdToken idToken, UserInfoEndpoint endpoint, boolean userInfoConfigured) {
        String subject = String.valueOf(idToken.claims().get("sub"));
        UserInfo userInfo = null;

        if (userInfoConfigured) {
            try {
                userInfo = endpoint.fetch(subject);
            } catch (RuntimeException e) {
                System.out.println("WARNING: userinfo fetch failed (" + e.getMessage() + "), falling back to id_token claims only");
            }
        }

        Map<String, Object> merged = new LinkedHashMap<>(idToken.claims());
        if (userInfo != null) merged.putAll(userInfo.claims());

        return new OidcUser(idToken, userInfo, merged);
    }

    public static void main(String[] args) {
        UserInfoEndpoint endpoint = new UserInfoEndpoint();
        endpoint.register("109283746", new UserInfo(Map.of("sub", "109283746", "name", "Alice Example")));
        endpoint.simulateOutageFor("555000111"); // this subject's provider call will fail

        IdToken aliceIdToken = new IdToken(Map.of("sub", "109283746", "iss", "https://accounts.google.com"));
        IdToken bobIdToken = new IdToken(Map.of("sub", "555000111", "iss", "https://accounts.google.com"));

        OidcUser alice = assembleOidcUser(aliceIdToken, endpoint, true);
        System.out.println("alice: hasUserInfo=" + alice.hasUserInfo() + " claims=" + new TreeMap<>(alice.mergedClaims()));

        OidcUser bob = assembleOidcUser(bobIdToken, endpoint, true);
        System.out.println("bob: hasUserInfo=" + bob.hasUserInfo() + " claims=" + new TreeMap<>(bob.mergedClaims()));

        OidcUser noUserInfoConfigured = assembleOidcUser(aliceIdToken, endpoint, false);
        System.out.println("no-userinfo-configured: hasUserInfo=" + noUserInfoConfigured.hasUserInfo()
                + " claims=" + new TreeMap<>(noUserInfoConfigured.mergedClaims()));
    }
}
```

**How to run:** save as `OidcUserInfoLevel3.java`, run `java OidcUserInfoLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
alice: hasUserInfo=true claims={iss=https://accounts.google.com, name=Alice Example, sub=109283746}
WARNING: userinfo fetch failed (connection timed out), falling back to id_token claims only
bob: hasUserInfo=false claims={iss=https://accounts.google.com, sub=555000111}
no-userinfo-configured: hasUserInfo=false claims={iss=https://accounts.google.com, sub=109283746}
```

What changed: `assembleOidcUser` now treats the UserInfo call as genuinely optional at two levels — it can be skipped entirely (`userInfoConfigured=false`, bob's peer case at the end) or attempted and fail (bob's simulated outage) — and in either case login still succeeds with an `OidcUser` built from ID token claims alone, exactly mirroring how a UserInfo outage degrades the richness of the principal without ever blocking authentication itself.

## 6. Walkthrough

Trace bob's case from Level 3 — a successful login whose UserInfo call fails — end to end.

**Step 1 — the code-for-token exchange completes** (as in cards 0090 and 0095), returning both an access token and a signed ID token for bob, whose `sub` claim is `"555000111"`.

**Step 2 — ID token validation passes** (card 0095's `iss`/`aud`/`exp` checks) — this happens regardless of what follows with UserInfo, since the ID token alone is sufficient to establish that authentication succeeded.

**Step 3 — Spring Security attempts the UserInfo call**, since a `userInfoUri` is configured for this registration:
```
GET /oauth2/v2/userinfo HTTP/1.1
Host: openidconnect.googleapis.com
Authorization: Bearer access-tok-for-bob
```
This corresponds to `endpoint.fetch("555000111")` inside `assembleOidcUser` — but `simulateOutageFor("555000111")` was configured, so this raises a `RuntimeException("connection timed out")` instead of returning a response.

**Step 4 — the failure is caught, not propagated.** `assembleOidcUser`'s `catch` block logs the warning and leaves `userInfo` as `null`, rather than letting the exception escape and fail the entire authentication — this mirrors `OidcUserService`'s real behavior of treating the UserInfo endpoint as best-effort.

**Step 5 — the merged claims fall back to ID-token-only.** `merged` is built from `idToken.claims()` alone (`sub`, `iss`), since there's no `userInfo` to layer on top; `new OidcUser(idToken, null, merged)` is constructed with `userInfo` explicitly `null`.

**Step 6 — login completes successfully anyway.** `bob.hasUserInfo()` is `false`, but bob is fully authenticated — a controller with `@AuthenticationPrincipal OidcUser principal` still receives a valid principal; only `principal.getUserInfo()` returns `null` and any UserInfo-only claim (like `name`, in this example) is simply absent from `getClaims()`.

```
token exchange -> id_token (sub=555000111) validated -> OK, authentication CAN succeed regardless
        |
        v
GET /userinfo  --------X (connection timed out)
        |
        v
catch -> log warning -> userInfo = null -> merge with id_token claims ONLY
        |
        v
OidcUser(hasUserInfo=false) -- authentication still SUCCEEDS
```

**Contrast — the response an application relying on `name` would see:** a template rendering `principal.getClaims().get("name")` for bob would render `null` (or omit the greeting entirely) in this request, purely because of the transient UserInfo outage, while alice's equivalent request would render `"Alice Example"` — this is exactly the kind of intermittent, provider-dependent gap that makes the UserInfo endpoint unsuitable for anything security-critical.

## 7. Gotchas & takeaways

> **Gotcha:** never make authorization decisions based solely on a claim that only exists in the UserInfo response (e.g., a custom `role` or `department` claim some providers include there) — that response isn't signed the way the ID token is, so its integrity depends entirely on the TLS channel and the provider's own correctness, not on a verifiable signature your application checked itself. Prefer ID-token claims, or better, your own application's authorization data, for anything access-control-relevant.

- The ID token is signed and obtained directly from the token endpoint; UserInfo is a separate, optional, unsigned HTTP call authenticated by the access token as a bearer credential.
- `OidcUser.getClaims()` is a merged view of both sources, with UserInfo generally taking precedence on overlapping keys since it reflects the more recent state.
- A UserInfo response whose `sub` disagrees with the ID token's `sub` is a serious integrity problem, not a minor inconsistency, and Spring Security's `OidcUserService` rejects it rather than silently merging mismatched identities.
- The UserInfo call is best-effort: its absence (not configured) or failure (network error, outage) must not — and in Spring Security's default implementation does not — block authentication; it only reduces how much profile data ends up in the final `OidcUser`.
- Reserve UserInfo-sourced claims for display purposes; use ID-token claims (or your own application's authorization model) for anything that gates access.
