---
card: spring-security
gi: 104
slug: mapping-authorities-from-claims-jwtauthenticationconverter
title: "Mapping authorities from claims (JwtAuthenticationConverter)"
---

## 1. What it is

`JwtAuthenticationConverter` is the component that turns a validated `Jwt` (card 0100's principal) into the final `AbstractAuthenticationToken` Spring Security actually authorizes against — and its default behavior is deliberately narrow: it reads the `scope` (or `scp`) claim, splits it on whitespace, and prefixes each value with `SCOPE_` to produce `GrantedAuthority` objects (exactly what card 0100's Level 2 example modeled). Real applications frequently need more than that — a custom `roles` claim, a nested claim structure some providers use for group membership, or authorities that must be looked up from a local database keyed by the token's subject — and `JwtAuthenticationConverter.setJwtGrantedAuthoritiesConverter(...)` (or a fully custom `Converter<Jwt, AbstractAuthenticationToken>`) is the extension point for exactly that.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    JwtAuthenticationConverter converter = new JwtAuthenticationConverter();
    converter.setJwtGrantedAuthoritiesConverter(jwt -> {
        List<String> roles = jwt.getClaimAsStringList("roles"); // a CUSTOM claim, not the standard "scope"
        return roles == null ? List.of() : roles.stream()
                .map(role -> new SimpleGrantedAuthority("ROLE_" + role))
                .collect(Collectors.toList());
    });

    http.oauth2ResourceServer(oauth2 -> oauth2.jwt(jwt -> jwt.jwtAuthenticationConverter(converter)));
    return http.build();
}
```

## 2. Why & when

`scope` (or `scp`) is a standard OAuth2 claim describing what an access token is authorized to do on the resource owner's behalf — it's a reasonable default authority source, but it conflates two genuinely different concepts: *what this particular token was granted permission to do* (scope) versus *who this user actually is within your application's own role model* (roles, groups, permissions). An identity provider's token might carry `scope=read write` while your application's authorization logic actually needs to know the user is a `MANAGER` in your own domain — information that has to come from either a custom claim the provider was configured to include, or a lookup against your own data, neither of which the default `SCOPE_`-prefixing behavior can provide.

Reach for a custom authorities converter when:

- The identity provider issues a custom claim (`roles`, `groups`, `permissions`) that better represents your authorization model than the generic `scope` claim.
- `@PreAuthorize` expressions throughout the application are written against role-style authorities (`hasRole('ADMIN')`) rather than scope-style ones (`hasAuthority('SCOPE_admin')") — the claim mapping is the one place to bridge that gap, rather than rewriting every authorization check.
- Authorities depend on data the token doesn't (and shouldn't) carry at all — for instance, a subscription tier stored in your own database that determines feature access, requiring the converter to perform a lookup keyed by the token's subject.
- Combining multiple claim sources into one authority set — some providers report top-level `scope` for OAuth2-granted permissions *and* a nested `resource_access` structure for role assignments (a pattern common with Keycloak, for instance), both of which need merging into one flat set of `GrantedAuthority` objects.

## 3. Core concept

```
DEFAULT JwtAuthenticationConverter behavior:
    reads "scope" (falls back to "scp") claim
    splits on whitespace
    prefixes each value with "SCOPE_"
    e.g. scope="read:orders write:orders" -> [SCOPE_read:orders, SCOPE_write:orders]

CUSTOMIZING via setJwtGrantedAuthoritiesConverter (Converter<Jwt, Collection<GrantedAuthority>>):
    completely REPLACES the default scope-mapping logic
    can read ANY claim, apply ANY prefix, or perform ANY lookup
    e.g.:
        jwt -> jwt.getClaimAsStringList("roles").stream()
                  .map(r -> new SimpleGrantedAuthority("ROLE_" + r))
                  .toList()

FULL replacement via a custom Converter<Jwt, AbstractAuthenticationToken>:
    bypasses JwtAuthenticationConverter entirely
    lets you build an ENTIRELY custom Authentication type (not just custom authorities)
    registered the same way: .jwt(jwt -> jwt.jwtAuthenticationConverter(myFullConverter))

Registration point (either style):
    http.oauth2ResourceServer(oauth2 -> oauth2.jwt(jwt -> jwt.jwtAuthenticationConverter(converter)))
```

The converter runs once per request, immediately after `JwtDecoder` succeeds and before `authorizeHttpRequests` evaluates anything — it is the single seam between "this token is valid" and "here is what this token's bearer is allowed to do."

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a validated jwt with a scope claim and a roles claim the default converter only maps scope into SCOPE prefixed authorities while a custom converter can map roles into ROLE prefixed authorities or merge both sources together">
  <rect x="20" y="80" width="160" height="60" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="100" y="100" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">validated Jwt</text>
  <text x="100" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">scope="read write"</text>
  <text x="100" y="129" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">roles=["manager"]</text>

  <line x1="180" y1="95" x2="220" y2="60" stroke="#8b949e" stroke-width="1.4" marker-end="url(#mc104)"/>
  <line x1="180" y1="125" x2="220" y2="160" stroke="#6db33f" stroke-width="1.4" marker-end="url(#mc104b)"/>

  <rect x="225" y="20" width="220" height="60" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="335" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">DEFAULT converter</text>
  <text x="335" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reads "scope" ONLY</text>
  <text x="335" y="71" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; [SCOPE_read, SCOPE_write]</text>

  <rect x="225" y="130" width="220" height="70" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="335" y="150" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">CUSTOM converter</text>
  <text x="335" y="166" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reads "roles" (or BOTH claims)</text>
  <text x="335" y="179" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; [ROLE_manager]</text>
  <text x="335" y="192" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">or merged: [ROLE_manager, SCOPE_read, ...]</text>

  <line x1="445" y1="50" x2="490" y2="50" stroke="#8b949e" stroke-width="1.4" marker-end="url(#mc104)"/>
  <line x1="445" y1="165" x2="490" y2="165" stroke="#6db33f" stroke-width="1.4" marker-end="url(#mc104b)"/>

  <rect x="495" y="20" width="140" height="60" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="565" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JwtAuthenticationToken</text>

  <rect x="495" y="130" width="140" height="70" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="565" y="170" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">JwtAuthenticationToken</text>

  <defs>
    <marker id="mc104" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="mc104b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The same token yields entirely different authority sets depending on which claim (or claims) the converter is configured to read.

## 5. Runnable example

The scenario: implement the default scope-mapping behavior first, then replace it with a custom `roles`-claim mapping, then merge multiple claim sources together while also handling absent claims and a local-database authority lookup — the three most common real-world variations.

### Level 1 — Basic

The default behavior: split `scope`, prefix with `SCOPE_`.

```java
import java.util.*;
import java.util.stream.*;

public class AuthConverterLevel1 {
    record Jwt(Map<String, Object> claims) {
        String getClaimAsString(String name) { return (String) claims.get(name); }
    }

    // mirrors the DEFAULT JwtGrantedAuthoritiesConverter
    static List<String> defaultConvert(Jwt jwt) {
        String scope = jwt.getClaimAsString("scope");
        if (scope == null || scope.isBlank()) return List.of();
        return Arrays.stream(scope.split(" ")).map(s -> "SCOPE_" + s).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        Jwt jwt = new Jwt(Map.of("sub", "alice", "scope", "read:orders write:orders"));

        List<String> authorities = defaultConvert(jwt);
        System.out.println("default authorities: " + authorities);
    }
}
```

**How to run:** save as `AuthConverterLevel1.java`, run `java AuthConverterLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
default authorities: [SCOPE_read:orders, SCOPE_write:orders]
```

`defaultConvert` is exactly `JwtAuthenticationConverter`'s built-in behavior — split on whitespace, prefix every token with `SCOPE_` — nothing else about the JWT's claims is consulted.

### Level 2 — Intermediate

Replace the default with a custom converter reading a `roles` claim instead, and handle the case where that claim is entirely absent.

```java
import java.util.*;
import java.util.stream.*;

public class AuthConverterLevel2 {
    record Jwt(Map<String, Object> claims) {
        @SuppressWarnings("unchecked")
        List<String> getClaimAsStringList(String name) {
            Object value = claims.get(name);
            return value == null ? null : (List<String>) value;
        }
    }

    // a CUSTOM converter -- COMPLETELY replaces the default scope-mapping logic
    static List<String> rolesConverter(Jwt jwt) {
        List<String> roles = jwt.getClaimAsStringList("roles");
        if (roles == null) return List.of(); // claim absent -- no authorities, NOT an error
        return roles.stream().map(r -> "ROLE_" + r.toUpperCase()).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        Jwt withRoles = new Jwt(Map.of("sub", "alice", "roles", List.of("manager", "auditor")));
        Jwt withoutRoles = new Jwt(Map.of("sub", "bob")); // this token's provider never included a "roles" claim

        System.out.println("alice authorities: " + rolesConverter(withRoles));
        System.out.println("bob authorities: " + rolesConverter(withoutRoles));
    }
}
```

**How to run:** save as `AuthConverterLevel2.java`, run `java AuthConverterLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
alice authorities: [ROLE_MANAGER, ROLE_AUDITOR]
bob authorities: []
```

What changed: `rolesConverter` reads an entirely different claim (`roles`, not `scope`) and applies a different prefix (`ROLE_`, not `SCOPE_`) — this is the essence of customizing `JwtAuthenticationConverter`: the provider's claim shape and your application's authority naming convention are decoupled, bridged by exactly this one function. Bob's token, lacking a `roles` claim entirely, correctly yields an empty authority set rather than throwing.

### Level 3 — Advanced

Merge multiple claim sources (scope *and* roles) into one authority set, and add a local-database lookup for a case the token's claims alone can't answer — a feature flag stored only in your own system.

```java
import java.util.*;
import java.util.stream.*;

public class AuthConverterLevel3 {
    record Jwt(Map<String, Object> claims) {
        String getClaimAsString(String name) { return (String) claims.get(name); }
        @SuppressWarnings("unchecked")
        List<String> getClaimAsStringList(String name) {
            Object value = claims.get(name);
            return value == null ? List.of() : (List<String>) value;
        }
        String getSubject() { return getClaimAsString("sub"); }
    }

    static class LocalFeatureFlagStore {
        private final Map<String, Set<String>> flagsBySubject = new HashMap<>();
        void grant(String subject, String flag) { flagsBySubject.computeIfAbsent(subject, s -> new HashSet<>()).add(flag); }
        Set<String> flagsFor(String subject) { return flagsBySubject.getOrDefault(subject, Set.of()); }
    }

    // merges THREE sources: standard scope claim, custom roles claim, and a LOCAL lookup the token can't carry
    static List<String> mergedConvert(Jwt jwt, LocalFeatureFlagStore flagStore) {
        List<String> authorities = new ArrayList<>();

        String scope = jwt.getClaimAsString("scope");
        if (scope != null && !scope.isBlank()) {
            for (String s : scope.split(" ")) authorities.add("SCOPE_" + s);
        }

        for (String role : jwt.getClaimAsStringList("roles")) {
            authorities.add("ROLE_" + role.toUpperCase());
        }

        for (String flag : flagStore.flagsFor(jwt.getSubject())) {
            authorities.add("FEATURE_" + flag.toUpperCase()); // NOT in the token at all -- looked up locally
        }

        return authorities;
    }

    public static void main(String[] args) {
        LocalFeatureFlagStore flagStore = new LocalFeatureFlagStore();
        flagStore.grant("alice", "beta-dashboard"); // an internal feature flag, unrelated to the identity provider

        Jwt aliceToken = new Jwt(Map.of(
                "sub", "alice",
                "scope", "read:orders",
                "roles", List.of("manager")));

        List<String> authorities = mergedConvert(aliceToken, flagStore);
        System.out.println("alice's merged authorities: " + authorities);

        // bob has NO roles claim, NO feature flags, only a scope -- must not throw, just yield less
        Jwt bobToken = new Jwt(Map.of("sub", "bob", "scope", "read:orders"));
        System.out.println("bob's merged authorities: " + mergedConvert(bobToken, flagStore));
    }
}
```

**How to run:** save as `AuthConverterLevel3.java`, run `java AuthConverterLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
alice's merged authorities: [SCOPE_read:orders, ROLE_MANAGER, FEATURE_BETA-DASHBOARD]
bob's merged authorities: [SCOPE_read:orders]
```

What changed: `mergedConvert` now combines three genuinely different authority sources in one pass — the standard `scope` claim (what the token itself grants), a custom `roles` claim (who the identity provider says this user is), and a local database lookup keyed by subject (data the token was never meant to carry at all, like an internal feature flag) — all flattened into one `GrantedAuthority` set that `@PreAuthorize` expressions can check uniformly, regardless of which of the three sources a given authority actually came from.

## 6. Walkthrough

Trace alice's authentication from Level 3 end to end, picking up immediately after card 0101's `JwtDecoder.decode()` succeeds.

**Step 1 — the validated `Jwt` is available.** This corresponds to `aliceToken` — already signature-verified and claim-validated (cards 0101, 0103) by the time `mergedConvert` is ever called; the converter's job starts only after the token is already trusted.

**Step 2 — the scope claim is read and mapped.** `jwt.getClaimAsString("scope")` returns `"read:orders"`; splitting on whitespace yields one token, prefixed to `"SCOPE_read:orders"` and added to `authorities`.

**Step 3 — the roles claim is read and mapped.** `jwt.getClaimAsStringList("roles")` returns `["manager"]`; each entry is upper-cased and prefixed, yielding `"ROLE_MANAGER"`, added to `authorities`.

**Step 4 — the local lookup runs.** `flagStore.flagsFor("alice")` — using `jwt.getSubject()`, `"alice"`, as the lookup key — returns `{"beta-dashboard"}`, since `flagStore.grant("alice", "beta-dashboard")` was called earlier in `main`. This becomes `"FEATURE_BETA-DASHBOARD"`, added to `authorities`. Note this step touches **no** claim on the token at all — it is pure application-side data, correlated only by the trusted `sub` claim.

**Step 5 — the final authority set is returned:** `[SCOPE_read:orders, ROLE_MANAGER, FEATURE_BETA-DASHBOARD]`. In a real Spring Security application, this list becomes the `Collection<GrantedAuthority>` on the resulting `JwtAuthenticationToken`.

**Step 6 — an example downstream authorization check.** A controller endpoint annotated `@PreAuthorize("hasAuthority('FEATURE_BETA-DASHBOARD')")` would now permit alice's request:
```
GET /api/dashboard/beta HTTP/1.1
Authorization: Bearer <alice's JWT>
```
```
HTTP/1.1 200 OK
```
while the identical endpoint, hit with bob's token (whose merged authorities are only `[SCOPE_read:orders]`), would be denied:
```
GET /api/dashboard/beta HTTP/1.1
Authorization: Bearer <bob's JWT>
```
```
HTTP/1.1 403 Forbidden
```

```
aliceToken.claims: {sub: alice, scope: "read:orders", roles: [manager]}
        |
        +-- scope  -> SCOPE_read:orders
        +-- roles  -> ROLE_MANAGER
        +-- sub -> flagStore.flagsFor("alice") -> FEATURE_BETA-DASHBOARD  (NOT from the token itself)
        |
        v
  [SCOPE_read:orders, ROLE_MANAGER, FEATURE_BETA-DASHBOARD]  -- the merged, final authority set
```

## 7. Gotchas & takeaways

> **Gotcha:** performing a database lookup inside a `JwtAuthenticationConverter` (as `mergedConvert`'s `flagStore.flagsFor(...)` call does) runs on *every single authenticated request*, since there's no session to cache the result in for a stateless resource server — an expensive or slow lookup here becomes a per-request cost across the entire API. If this matters at your traffic volume, consider caching the lookup result (keyed by subject, with a short TTL) rather than hitting the database on every call.

- `JwtAuthenticationConverter`'s default behavior maps only the `scope`/`scp` claim to `SCOPE_`-prefixed authorities — any other claim, or any authority that depends on local data, requires an explicit custom converter.
- Customizing `setJwtGrantedAuthoritiesConverter` replaces the authority-mapping logic entirely; it does not layer on top of the default unless you explicitly call the default converter yourself and merge its output.
- Merging multiple claim sources (standard scope, custom roles, locally-looked-up data) into one flat `GrantedAuthority` set is a common and reasonable pattern — `@PreAuthorize` expressions don't need to know or care which source a given authority came from.
- Absent claims should degrade to an empty authority contribution, not an exception — a token missing an optional `roles` claim is a normal case, not an error condition.
- Any lookup performed inside the converter runs on every request in a stateless resource server, since there is no session to cache it in — factor that cost into the design, and cache aggressively if the lookup is expensive.
