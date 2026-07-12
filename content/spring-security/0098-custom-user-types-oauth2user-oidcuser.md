---
card: spring-security
gi: 98
slug: custom-user-types-oauth2user-oidcuser
title: "Custom user types (OAuth2User/OidcUser)"
---

## 1. What it is

The default `OAuth2User`/`OidcUser` implementations Spring Security builds after a successful login are generic, provider-agnostic wrappers over a raw claims map — perfectly functional, but they carry no notion of *your* application's own concepts: a local user id, an internal role set derived from business rules, or a `Set<GrantedAuthority>` computed by looking the provider's identity up in your own database. Customizing this means implementing your own `OAuth2UserService<OAuth2UserRequest, OAuth2User>` (for plain OAuth2 logins) or `OAuth2UserService<OidcUserRequest, OidcUser>` (for OIDC logins) — typically by delegating to the default implementation to do the actual provider communication, then wrapping or replacing its result with a custom type before returning it.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http.oauth2Login(oauth2 -> oauth2
        .userInfoEndpoint(userInfo -> userInfo
            .oidcUserService(this::loadOidcUser)      // for OIDC providers
            .userService(this::loadOAuth2User)));     // for plain OAuth2 providers
    return http.build();
}

private OidcUser loadOidcUser(OidcUserRequest request) {
    OidcUser delegate = new OidcUserService().loadUser(request); // let the default do the real work first
    return new AppOidcUser(delegate, lookUpLocalAuthorities(delegate.getSubject()));
}
```

## 2. Why & when

Every card in this OAuth2/OIDC section so far has treated the resulting `OAuth2User`/`OidcUser` as an opaque bag of provider claims — sufficient for authentication, but insufficient the moment authorization needs to key off something the provider doesn't know about, like an internal role assigned by your own admin panel. `oauth2Login()`'s default behavior grants every successful login a single flat authority (`ROLE_USER`, or `OAUTH2_USER`/`OIDC_USER`) — reasonable as a default, but rarely what a real application's `@PreAuthorize` expressions actually need to check against.

Reach for a custom `OAuth2UserService` when:

- Authorization decisions depend on data that lives in your own database, not the provider's profile — for example, mapping the authenticated email to an internal `User` record and its associated roles.
- Different authorities should be granted based on provider-side data — for instance, granting `ROLE_ADMIN` only if the provider's profile reports the user belongs to a specific organization or group.
- The application needs to persist a local `User` record the first time a given provider identity logs in (a "just-in-time provisioning" pattern), rather than only ever reading — never writing — local state during login.
- Downstream code wants a strongly-typed principal (`getLocalUserId()`, `getDisplayName()`) instead of manually pulling values out of a raw `Map<String, Object>` via `getAttributes()`/`getClaims()` at every call site.

## 3. Core concept

```
Default behavior:
    OidcUserService.loadUser(request) -> DefaultOidcUser
        - wraps id_token + userinfo claims
        - authorities: just ONE, e.g. "OIDC_USER"

Custom behavior (delegating pattern -- almost always the right approach):
    1. call the DEFAULT service first -- let it do signature validation, claim merging, etc.
    2. use the delegate's claims (subject, email) to look up / provision a LOCAL user record
    3. compute authorities from LOCAL data (roles table), not just the provider's flat default
    4. wrap everything in a CUSTOM OidcUser implementation that:
         - implements getAuthorities() -> the computed, real authority set
         - implements getAttributes(), getIdToken(), getUserInfo() -> delegate to the wrapped DefaultOidcUser
         - ADDS new accessors specific to your domain, e.g. getLocalUserId()

register the custom service via:
    http.oauth2Login(oauth2 -> oauth2.userInfoEndpoint(u -> u.oidcUserService(this::loadOidcUser)))
```

Delegating to the default implementation rather than reimplementing it from scratch means you never have to duplicate ID token validation, signature verification, or claim-merging logic — you only add what's specific to your application.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a custom OidcUserService delegating to the default OidcUserService to get provider claims validated then looking up a local user record by subject to compute real authorities and wrapping both into a custom OidcUser implementation">
  <rect x="20" y="30" width="180" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">OidcUserRequest</text>
  <text x="110" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(from login flow)</text>

  <line x1="200" y1="55" x2="240" y2="55" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#cu98)"/>

  <rect x="245" y="30" width="180" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="335" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">default OidcUserService</text>
  <text x="335" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">validates + merges claims</text>

  <line x1="335" y1="80" x2="335" y2="110" stroke="#8b949e" stroke-width="1.5" marker-end="url(#cu98)"/>
  <text x="335" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">DefaultOidcUser (delegate)</text>

  <line x1="335" y1="115" x2="200" y2="150" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cu98b)"/>
  <text x="240" y="140" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">subject -&gt; lookup</text>

  <rect x="20" y="155" width="180" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="175" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">local user database</text>
  <text x="110" y="190" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">roles, local user id</text>

  <line x1="200" y1="180" x2="400" y2="150" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cu98b)"/>

  <rect x="400" y="120" width="220" height="90" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="510" y="145" fill="#6db33f" font-size="10.5" text-anchor="middle" font-family="sans-serif">AppOidcUser</text>
  <text x="510" y="163" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">getAuthorities() -&gt; computed</text>
  <text x="510" y="177" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">getClaims() -&gt; delegate.getClaims()</text>
  <text x="510" y="191" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">getLocalUserId() -&gt; new accessor</text>

  <defs>
    <marker id="cu98" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="cu98b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The custom service wraps, rather than replaces, the default's validated result — adding local data without redoing provider-facing work.

## 5. Runnable example

The scenario: build a minimal delegating `CustomOidcUserService` that looks up local authorities by subject, grow it to just-in-time provision a brand-new local user on first login, then add a strongly-typed `AppOidcUser` that exposes a local user id alongside the standard claims.

### Level 1 — Basic

Delegate to a "default" provider result, then compute authorities from a local lookup table.

```java
import java.util.*;

public class CustomOidcUserLevel1 {
    record DefaultOidcUser(String subject, Map<String, Object> claims) {}
    record AppOidcUser(DefaultOidcUser delegate, Set<String> authorities) {
        String getSubject() { return delegate.subject(); }
        Map<String, Object> getClaims() { return delegate.claims(); }
    }

    static class LocalUserDirectory {
        private final Map<String, Set<String>> rolesBySubject = new HashMap<>();
        void registerRoles(String subject, Set<String> roles) { rolesBySubject.put(subject, roles); }
        Set<String> rolesFor(String subject) { return rolesBySubject.getOrDefault(subject, Set.of("ROLE_USER")); }
    }

    static AppOidcUser loadOidcUser(DefaultOidcUser delegate, LocalUserDirectory directory) {
        Set<String> authorities = directory.rolesFor(delegate.subject());
        return new AppOidcUser(delegate, authorities);
    }

    public static void main(String[] args) {
        LocalUserDirectory directory = new LocalUserDirectory();
        directory.registerRoles("109283746", Set.of("ROLE_USER", "ROLE_ADMIN"));

        DefaultOidcUser aliceDelegate = new DefaultOidcUser("109283746", Map.of("email", "alice@example.com"));
        DefaultOidcUser strangerDelegate = new DefaultOidcUser("999999999", Map.of("email", "stranger@example.com"));

        AppOidcUser alice = loadOidcUser(aliceDelegate, directory);
        AppOidcUser stranger = loadOidcUser(strangerDelegate, directory);

        System.out.println("alice authorities: " + new TreeSet<>(alice.authorities()));
        System.out.println("stranger authorities: " + new TreeSet<>(stranger.authorities()));
    }
}
```

**How to run:** save as `CustomOidcUserLevel1.java`, run `java CustomOidcUserLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
alice authorities: [ROLE_ADMIN, ROLE_USER]
stranger authorities: [ROLE_USER]
```

`loadOidcUser` mirrors the delegating pattern: it never re-derives the subject or claims itself (those came from `delegate`, standing in for the real, already-validated `DefaultOidcUser`) — it only adds the one thing the default implementation can't know, the locally-assigned role set, falling back to a bare `ROLE_USER` for anyone not explicitly registered.

### Level 2 — Intermediate

Add just-in-time provisioning: the very first login from a given subject creates a local user record rather than merely reading one.

```java
import java.util.*;

public class CustomOidcUserLevel2 {
    record DefaultOidcUser(String subject, Map<String, Object> claims) {}
    record LocalUser(String subject, String email, Set<String> roles) {}
    record AppOidcUser(DefaultOidcUser delegate, LocalUser localUser) {
        String getSubject() { return delegate.subject(); }
        Set<String> getAuthorities() { return localUser.roles(); }
    }

    static class LocalUserDirectory {
        private final Map<String, LocalUser> usersBySubject = new HashMap<>();

        LocalUser findOrProvision(String subject, String email) {
            LocalUser existing = usersBySubject.get(subject);
            if (existing != null) return existing;

            // FIRST login for this subject -- provision a brand-new local record with a safe default role
            LocalUser provisioned = new LocalUser(subject, email, Set.of("ROLE_USER"));
            usersBySubject.put(subject, provisioned);
            System.out.println("provisioned NEW local user for subject=" + subject + " email=" + email);
            return provisioned;
        }
    }

    static AppOidcUser loadOidcUser(DefaultOidcUser delegate, LocalUserDirectory directory) {
        String email = String.valueOf(delegate.claims().get("email"));
        LocalUser localUser = directory.findOrProvision(delegate.subject(), email);
        return new AppOidcUser(delegate, localUser);
    }

    public static void main(String[] args) {
        LocalUserDirectory directory = new LocalUserDirectory();

        DefaultOidcUser aliceFirstLogin = new DefaultOidcUser("109283746", Map.of("email", "alice@example.com"));
        AppOidcUser first = loadOidcUser(aliceFirstLogin, directory);
        System.out.println("first login authorities: " + first.getAuthorities());

        // SECOND login, same subject -- must reuse the SAME local record, not provision again
        DefaultOidcUser aliceSecondLogin = new DefaultOidcUser("109283746", Map.of("email", "alice@example.com"));
        AppOidcUser second = loadOidcUser(aliceSecondLogin, directory);
        System.out.println("second login authorities: " + second.getAuthorities());
        System.out.println("same local user instance reused: " + (first.localUser() == second.localUser()));
    }
}
```

**How to run:** save as `CustomOidcUserLevel2.java`, run `java CustomOidcUserLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
provisioned NEW local user for subject=109283746 email=alice@example.com
first login authorities: [ROLE_USER]
second login authorities: [ROLE_USER]
same local user instance reused: true
```

What changed: `findOrProvision` only prints its provisioning message once — on alice's first login it creates and stores a new `LocalUser`, and on her second login (a distinct `DefaultOidcUser` object, but with the same `subject`) it finds and reuses the *same* stored record rather than creating a duplicate, exactly mirroring how just-in-time provisioning must be idempotent per subject.

### Level 3 — Advanced

Real authority computation should also react to provider-side signals — for example, revoking admin access if the provider's own profile no longer reports the user in a trusted group — and must handle a claim (like `email`) being unexpectedly absent without crashing the whole login.

```java
import java.util.*;

public class CustomOidcUserLevel3 {
    record DefaultOidcUser(String subject, Map<String, Object> claims) {}
    record LocalUser(String subject, String email, Set<String> roles) {}
    record AppOidcUser(DefaultOidcUser delegate, LocalUser localUser) {
        String getSubject() { return delegate.subject(); }
        Set<String> getAuthorities() { return localUser.roles(); }
    }

    static class LocalUserDirectory {
        private final Map<String, LocalUser> usersBySubject = new HashMap<>();

        LocalUser findOrProvision(String subject, String email) {
            return usersBySubject.computeIfAbsent(subject, s -> {
                System.out.println("provisioned NEW local user for subject=" + s + " email=" + email);
                return new LocalUser(s, email, Set.of("ROLE_USER"));
            });
        }

        void updateRoles(String subject, Set<String> roles) {
            LocalUser existing = usersBySubject.get(subject);
            usersBySubject.put(subject, new LocalUser(existing.subject(), existing.email(), roles));
        }
    }

    @SuppressWarnings("unchecked")
    static AppOidcUser loadOidcUser(DefaultOidcUser delegate, LocalUserDirectory directory) {
        // email can legitimately be absent if the "email" scope wasn't granted -- never assume it's present
        Object emailClaim = delegate.claims().get("email");
        String email = emailClaim != null ? String.valueOf(emailClaim) : "unknown@unset.local";

        LocalUser localUser = directory.findOrProvision(delegate.subject(), email);

        // re-derive authorities from a provider-reported group claim EVERY login, not just at provisioning time --
        // this means access is revoked automatically if the provider stops reporting the trusted group
        List<String> groups = (List<String>) delegate.claims().getOrDefault("groups", List.of());
        Set<String> authorities = new LinkedHashSet<>(Set.of("ROLE_USER"));
        if (groups.contains("admins")) authorities.add("ROLE_ADMIN");
        directory.updateRoles(delegate.subject(), authorities);

        return new AppOidcUser(delegate, directory.findOrProvision(delegate.subject(), email));
    }

    public static void main(String[] args) {
        LocalUserDirectory directory = new LocalUserDirectory();

        // login #1: alice is reported as being in the "admins" group by the provider
        DefaultOidcUser aliceAsAdmin = new DefaultOidcUser("109283746",
                Map.of("email", "alice@example.com", "groups", List.of("admins", "engineering")));
        AppOidcUser adminLogin = loadOidcUser(aliceAsAdmin, directory);
        System.out.println("login #1 authorities: " + new TreeSet<>(adminLogin.getAuthorities()));

        // login #2, same subject: provider no longer reports "admins" -- access must be REVOKED, not sticky
        DefaultOidcUser aliceDemoted = new DefaultOidcUser("109283746",
                Map.of("email", "alice@example.com", "groups", List.of("engineering")));
        AppOidcUser demotedLogin = loadOidcUser(aliceDemoted, directory);
        System.out.println("login #2 authorities: " + new TreeSet<>(demotedLogin.getAuthorities()));

        // a user whose provider profile has no "email" claim at all (email scope not granted)
        DefaultOidcUser noEmailClaim = new DefaultOidcUser("555000111", Map.of());
        AppOidcUser noEmailLogin = loadOidcUser(noEmailClaim, directory);
        System.out.println("no-email-claim user authorities: " + noEmailLogin.getAuthorities());
    }
}
```

**How to run:** save as `CustomOidcUserLevel3.java`, run `java CustomOidcUserLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
provisioned NEW local user for subject=109283746 email=alice@example.com
login #1 authorities: [ROLE_ADMIN, ROLE_USER]
login #2 authorities: [ROLE_USER]
provisioned NEW local user for subject=555000111 email=unknown@unset.local
no-email-claim user authorities: [ROLE_USER]
```

What changed: `loadOidcUser` now recomputes authorities from the provider's `groups` claim on *every* login and persists that via `updateRoles`, rather than only ever setting a role once at provisioning — alice's second login, where the provider no longer lists her in `"admins"`, correctly loses `ROLE_ADMIN`, demonstrating that provider-side group membership should be treated as the current source of truth, checked fresh each time, not a one-time grant. The absent-`email`-claim case falls back to a stand-in default value rather than throwing a `NullPointerException` that would otherwise fail the entire login over a missing optional field.

## 6. Walkthrough

Trace alice's demotion (login #2 in Level 3) end to end, since it's the case that reveals why re-deriving authorities every login (rather than only at provisioning) matters.

**Step 1 — the OIDC login flow completes** (cards 0090/0095), and Spring Security's default `OidcUserService` builds a validated `DefaultOidcUser`. Here, `aliceDemoted` stands in for that object, with `claims()` containing `groups=[engineering]` — critically, `admins` is no longer present, unlike her first login.

**Step 2 — the custom service is invoked** because `oidcUserService(this::loadOidcUser)` was registered — this corresponds to `loadOidcUser(aliceDemoted, directory)` being called.

**Step 3 — the email claim is read defensively.** `emailClaim` is `"alice@example.com"` here (present), so `email` becomes that value directly — this branch exists for the *other* case in this level (the no-email user), but every call passes through the same defensive check.

**Step 4 — the local user is found, not re-provisioned.** `directory.findOrProvision("109283746", email)` — since alice's subject already has an entry from login #1 — returns the existing record via `computeIfAbsent`'s early exit; no "provisioned NEW local user" message prints for this call, exactly as the earlier `Level 2` idempotency check confirmed.

**Step 5 — authorities are recomputed from scratch, not merely read.** `groups` is `["engineering"]`; `groups.contains("admins")` evaluates to `false`, so `authorities` remains just `{ROLE_USER}` — `ROLE_ADMIN` is never added this time, in contrast to login #1 where it was.

**Step 6 — the recomputed authorities are persisted.** `directory.updateRoles("109283746", {ROLE_USER})` overwrites alice's stored `LocalUser`, replacing the version that still had `ROLE_ADMIN` from login #1.

**Step 7 — the final `AppOidcUser` is built and returned**, wrapping the now-updated local user. A controller's `@AuthenticationPrincipal AppOidcUser principal` for this request sees `getAuthorities()` return `{ROLE_USER}` only — any `@PreAuthorize("hasRole('ADMIN')")` endpoint that alice could reach during login #1 is now correctly denied to her in this session.

```
login #1: groups=[admins, engineering]  -> authorities={ROLE_USER, ROLE_ADMIN} -> persisted
login #2: groups=[engineering]          -> authorities={ROLE_USER}            -> persisted, OVERWRITING #1's grant
                                                                                    (recomputed EVERY login, not cached)
```

**Contrast with a naive "only provision once" implementation:** had `loadOidcUser` only set authorities inside the `computeIfAbsent` block (at provisioning time) rather than on every call, alice's second login would have skipped straight to step 4's cache hit and kept her stale `ROLE_ADMIN` forever, regardless of what the provider reports going forward — a stale-privilege bug that recomputing on every login specifically avoids.

## 7. Gotchas & takeaways

> **Gotcha:** the custom `OAuth2UserService`/`OidcUserService` you register replaces the *default* one entirely for the registrations it's wired to — if your implementation doesn't delegate to a real default (or equivalent logic) for provider communication and claim validation, you silently lose that validation. Always build your custom result on top of a genuinely validated delegate, never bypass it.

- Custom `OAuth2User`/`OidcUser` types exist to bridge provider-supplied identity with your application's own authorization data (local roles, local user ids) — the provider's default claims alone are rarely sufficient for real `@PreAuthorize` decisions.
- The delegating pattern — call the default service first, then wrap its result — is almost always correct: it preserves ID token validation and claim merging while adding exactly the local logic your application needs.
- Just-in-time provisioning (creating a local user record on first login) must be idempotent per subject — a second login for the same identity should find, not recreate, the local record.
- Prefer recomputing authorities from provider-reported signals (like group membership) on every login rather than only at provisioning time — a one-time grant that's never rechecked becomes a stale-privilege bug the moment the provider-side membership changes.
- Guard against optional claims (like `email`, gated behind a scope that might not have been granted) being absent — a missing claim should degrade gracefully, not throw and fail the entire login.
