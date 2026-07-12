---
card: spring-security
gi: 100
slug: jwt-based-bearer-token-authentication
title: "JWT-based (bearer token) authentication"
---

## 1. What it is

`oauth2ResourceServer(oauth2 -> oauth2.jwt(...))` is the specific configuration that wires the JWT half of card 0099's resource server support: it registers a `BearerTokenAuthenticationFilter` that extracts the token from the `Authorization: Bearer <token>` header, hands it to a `JwtDecoder` for decoding and validation, and — on success — wraps the result in a `JwtAuthenticationToken`, Spring Security's `Authentication` implementation whose principal is the decoded `Jwt` object itself (its header, its claims, its raw token value all remain accessible). This card is the entry point for the rest of the section: the next three cards go deep on the three moving parts this one only names — `JwtDecoder`/JWK sets (card 0101), the specific validators that check claims like `iss`/`aud`/`exp` (card 0103), and mapping claims to authorities (card 0104).

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/public/**").permitAll()
            .anyRequest().authenticated())
        .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
        .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS));
    return http.build();
}
```

## 2. Why & when

Card 0099 introduced the resource server role in the abstract and contrasted it with opaque tokens at a high level; this card exists because "just call `.jwt()`" glosses over several real decisions an application must make: where the decoder gets its keys from, what happens when a token is malformed rather than merely invalid, and how the resulting principal differs from the `UserDetails`-based principal every earlier card in this course assumed. Every one of those decisions shows up the moment a real request with a real (or malformed, or expired) bearer token hits the filter chain.

Reach for understanding this filter's behavior specifically when:

- Debugging a `401` response on an endpoint — the JWT path's failure modes (missing header, malformed token, failed decode, failed validation) each produce a distinct `WWW-Authenticate` error, and knowing which one fired narrows the cause immediately.
- Deciding what the authenticated principal actually is in controller code — `@AuthenticationPrincipal Jwt jwt` (not a `UserDetails`) is the idiomatic way to access claims directly in a JWT-secured endpoint.
- Configuring `sessionCreationPolicy(STATELESS)` alongside this filter — since the bearer token is presented fresh on every request, there is no reason to create or consult an `HttpSession`, and doing so anyway wastes memory without buying anything.
- Composing JWT resource server support with `oauth2Login()` in the same application (e.g., a backend that both logs browser users in via OIDC *and* exposes an API other services call with bearer tokens) — the two filters coexist in the same chain, keyed to different endpoints via `securityMatcher`.

## 3. Core concept

```
Incoming request:
    GET /api/orders
    Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6...

BearerTokenAuthenticationFilter (registered by .jwt(...)):
  1. no header at all, or wrong scheme  -> pass through UNAUTHENTICATED (later blocked by authorizeHttpRequests)
  2. header present, malformed (not even valid JWT structure)
       -> decode() throws BadJwtException -> 401, error="invalid_token"
  3. header present, well-formed JWT, but signature/claims invalid
       -> decode() throws JwtValidationException -> 401, error="invalid_token"
  4. header present, valid JWT
       -> JwtAuthenticationConverter builds a JwtAuthenticationToken
       -> SecurityContextHolder populated FOR THIS REQUEST ONLY (no session)
       -> authorizeHttpRequests evaluates normally against this Authentication

Principal type: org.springframework.security.oauth2.jwt.Jwt
    jwt.getSubject()      -- the "sub" claim
    jwt.getClaims()       -- full claim map
    jwt.getTokenValue()   -- the raw, original JWT string
    jwt.getHeaders()      -- alg, kid, typ
```

Unlike `formLogin()`'s principal (typically a `UserDetails`), a JWT resource server's principal is the token itself — there is no separate "load the user" step unless a custom `JwtAuthenticationConverter` (card 0104) is added to bridge to one.

## 4. Diagram

<svg viewBox="0 0 660 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a request with a bearer token being processed by the bearer token authentication filter which decodes the jwt and on success builds a JwtAuthenticationToken with the decoded Jwt as its principal or on failure returns a 401 with a WWW Authenticate header describing the error">
  <rect x="20" y="20" width="200" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="120" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">GET /api/orders</text>
  <text x="120" y="55" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Authorization: Bearer ...</text>

  <line x1="220" y1="43" x2="260" y2="43" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#jw100)"/>

  <rect x="265" y="10" width="240" height="66" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="385" y="32" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">BearerTokenAuthenticationFilter</text>
  <text x="385" y="48" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">extract -&gt; JwtDecoder.decode(token)</text>
  <text x="385" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(card 0101)</text>

  <line x1="385" y1="76" x2="230" y2="130" stroke="#f85149" stroke-width="1.5" marker-end="url(#jw100b)"/>
  <line x1="385" y1="76" x2="470" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jw100c)"/>

  <rect x="70" y="132" width="220" height="60" rx="7" fill="#1c2430" stroke="#f85149" stroke-width="1.3"/>
  <text x="180" y="152" fill="#f85149" font-size="9.5" text-anchor="middle" font-family="sans-serif">decode FAILS</text>
  <text x="180" y="168" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">401 Unauthorized</text>
  <text x="180" y="182" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">WWW-Authenticate: Bearer error="invalid_token"</text>

  <rect x="360" y="132" width="240" height="76" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="480" y="152" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">decode SUCCEEDS</text>
  <text x="480" y="168" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">JwtAuthenticationToken</text>
  <text x="480" y="182" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">principal = Jwt (sub, claims, raw value)</text>
  <text x="480" y="196" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">-&gt; SecurityContext for THIS request only</text>

  <defs>
    <marker id="jw100" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="jw100b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="jw100c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Every request stands alone: decode failure or success is decided fresh, with no session to fall back on.

## 5. Runnable example

The scenario: a minimal `BearerTokenAuthenticationFilter` simulation that extracts a header, decodes a token, and builds a principal — grown from a bare pass/fail case into distinguishing missing-header from malformed-token from failed-validation, then into a full request-handling loop producing the right HTTP status and error code for each case.

### Level 1 — Basic

Extract the header, decode, build a principal on success.

```java
import java.util.*;

public class JwtAuthLevel1 {
    record Jwt(String subject, Map<String, Object> claims, String rawValue) {}
    record JwtAuthenticationToken(Jwt principal) {}

    static class JwtDecoder {
        private final Set<String> validTokens;
        JwtDecoder(Set<String> validTokens) { this.validTokens = validTokens; }

        Jwt decode(String token) {
            if (!validTokens.contains(token)) throw new IllegalArgumentException("invalid_token");
            return new Jwt("alice", Map.of("sub", "alice", "scope", "read:orders"), token);
        }
    }

    static JwtAuthenticationToken authenticate(String authorizationHeader, JwtDecoder decoder) {
        String token = authorizationHeader.substring("Bearer ".length());
        Jwt jwt = decoder.decode(token);
        return new JwtAuthenticationToken(jwt);
    }

    public static void main(String[] args) {
        JwtDecoder decoder = new JwtDecoder(Set.of("valid-jwt-abc"));

        JwtAuthenticationToken authentication = authenticate("Bearer valid-jwt-abc", decoder);
        System.out.println("authenticated subject: " + authentication.principal().subject());
        System.out.println("raw token preserved: " + authentication.principal().rawValue());
    }
}
```

**How to run:** save as `JwtAuthLevel1.java`, run `java JwtAuthLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
authenticated subject: alice
raw token preserved: valid-jwt-abc
```

`authenticate` mirrors `BearerTokenAuthenticationFilter`'s happy path: extract the token, decode it, wrap the result — the principal (`Jwt`) retains the raw token value alongside its parsed claims, exactly like the real `Jwt` class does.

### Level 2 — Intermediate

Distinguish the three ways a request can fail to authenticate: no header, malformed token, and a token that decodes structurally but fails validation.

```java
import java.util.*;

public class JwtAuthLevel2 {
    record Jwt(String subject, Map<String, Object> claims, String rawValue) {}
    record JwtAuthenticationToken(Jwt principal) {}

    static class BadJwtException extends RuntimeException {
        BadJwtException(String message) { super(message); }
    }
    static class JwtValidationException extends RuntimeException {
        JwtValidationException(String message) { super(message); }
    }

    static class JwtDecoder {
        private final Map<String, Long> wellFormedTokens = new HashMap<>(); // token -> expiresAt epoch seconds

        void registerWellFormed(String token, long expiresAtEpochSeconds) {
            wellFormedTokens.put(token, expiresAtEpochSeconds);
        }

        Jwt decode(String token) {
            if (!token.startsWith("eyJ")) { // stands in for "not even valid JWT structure"
                throw new BadJwtException("malformed JWT");
            }
            Long expiresAt = wellFormedTokens.get(token);
            if (expiresAt == null) {
                throw new BadJwtException("unknown token");
            }
            if (System.currentTimeMillis() / 1000 >= expiresAt) {
                throw new JwtValidationException("token expired");
            }
            return new Jwt("alice", Map.of("sub", "alice"), token);
        }
    }

    enum Outcome { NO_HEADER, MALFORMED, VALIDATION_FAILED, SUCCESS }
    record AuthResult(Outcome outcome, String detail, JwtAuthenticationToken authentication) {}

    static AuthResult authenticate(String authorizationHeader, JwtDecoder decoder) {
        if (authorizationHeader == null || !authorizationHeader.startsWith("Bearer ")) {
            return new AuthResult(Outcome.NO_HEADER, "no bearer token presented", null);
        }
        String token = authorizationHeader.substring("Bearer ".length());
        try {
            Jwt jwt = decoder.decode(token);
            return new AuthResult(Outcome.SUCCESS, "ok", new JwtAuthenticationToken(jwt));
        } catch (BadJwtException e) {
            return new AuthResult(Outcome.MALFORMED, e.getMessage(), null);
        } catch (JwtValidationException e) {
            return new AuthResult(Outcome.VALIDATION_FAILED, e.getMessage(), null);
        }
    }

    public static void main(String[] args) {
        JwtDecoder decoder = new JwtDecoder();
        decoder.registerWellFormed("eyJ.valid.token", System.currentTimeMillis() / 1000 + 3600);
        decoder.registerWellFormed("eyJ.expired.token", System.currentTimeMillis() / 1000 - 60);

        System.out.println(authenticate(null, decoder));
        System.out.println(authenticate("Bearer not-a-jwt-at-all", decoder));
        System.out.println(authenticate("Bearer eyJ.expired.token", decoder));
        System.out.println(authenticate("Bearer eyJ.valid.token", decoder));
    }
}
```

**How to run:** save as `JwtAuthLevel2.java`, run `java JwtAuthLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
AuthResult[outcome=NO_HEADER, detail=no bearer token presented, authentication=null]
AuthResult[outcome=MALFORMED, detail=malformed JWT, authentication=null]
AuthResult[outcome=VALIDATION_FAILED, detail=token expired, authentication=null]
AuthResult[outcome=SUCCESS, detail=ok, authentication=JwtAuthenticationToken[principal=Jwt[subject=alice, claims={sub=alice}, rawValue=eyJ.valid.token]]]
```

What changed: `authenticate` now distinguishes four distinct outcomes rather than one binary pass/fail — no header at all is not an error (it's simply unauthenticated, left for `authorizeHttpRequests` to reject), a structurally invalid token is a different failure (`BadJwtException`) from one that parses but fails a check like expiry (`JwtValidationException`) — this mirrors the real distinction between `BadJwtException` and `JwtValidationException` that Spring Security's own `JwtDecoder` implementations throw.

### Level 3 — Advanced

Map each outcome to the actual HTTP response a client would receive, including the `WWW-Authenticate` header's `error` parameter, and show how a downstream controller accesses claims via the principal once authentication succeeds.

```java
import java.util.*;

public class JwtAuthLevel3 {
    record Jwt(String subject, Map<String, Object> claims, String rawValue) {
        Object claim(String name) { return claims.get(name); }
    }
    record JwtAuthenticationToken(Jwt principal) {}

    static class BadJwtException extends RuntimeException { BadJwtException(String m) { super(m); } }
    static class JwtValidationException extends RuntimeException { JwtValidationException(String m) { super(m); } }

    static class JwtDecoder {
        private final Map<String, Map<String, Object>> wellFormedTokens = new HashMap<>();
        private final Map<String, Long> expiries = new HashMap<>();

        void register(String token, Map<String, Object> claims, long expiresAtEpochSeconds) {
            wellFormedTokens.put(token, claims);
            expiries.put(token, expiresAtEpochSeconds);
        }

        Jwt decode(String token) {
            if (!token.startsWith("eyJ")) throw new BadJwtException("malformed JWT");
            Map<String, Object> claims = wellFormedTokens.get(token);
            if (claims == null) throw new BadJwtException("unknown token");
            if (System.currentTimeMillis() / 1000 >= expiries.get(token)) throw new JwtValidationException("token expired");
            return new Jwt(String.valueOf(claims.get("sub")), claims, token);
        }
    }

    record HttpResponse(int status, String wwwAuthenticate, String body) {}

    // mirrors BearerTokenAuthenticationEntryPoint's response shaping on failure
    static HttpResponse handleRequest(String authorizationHeader, JwtDecoder decoder) {
        if (authorizationHeader == null || !authorizationHeader.startsWith("Bearer ")) {
            return new HttpResponse(401, "Bearer realm=\"api\"", "");
        }
        String token = authorizationHeader.substring("Bearer ".length());
        try {
            Jwt jwt = decoder.decode(token);
            // "controller" logic: use the authenticated principal's claims directly
            String scope = String.valueOf(jwt.claim("scope"));
            String body = "{\"orders\":[],\"authenticatedAs\":\"" + jwt.subject() + "\",\"grantedScope\":\"" + scope + "\"}";
            return new HttpResponse(200, null, body);
        } catch (BadJwtException e) {
            return new HttpResponse(401, "Bearer error=\"invalid_token\", error_description=\"" + e.getMessage() + "\"", "");
        } catch (JwtValidationException e) {
            return new HttpResponse(401, "Bearer error=\"invalid_token\", error_description=\"" + e.getMessage() + "\"", "");
        }
    }

    public static void main(String[] args) {
        JwtDecoder decoder = new JwtDecoder();
        decoder.register("eyJ.valid.token", Map.of("sub", "alice", "scope", "read:orders"),
                System.currentTimeMillis() / 1000 + 3600);

        HttpResponse noHeader = handleRequest(null, decoder);
        System.out.println("no header -> " + noHeader.status() + " WWW-Authenticate: " + noHeader.wwwAuthenticate());

        HttpResponse malformed = handleRequest("Bearer not-a-jwt", decoder);
        System.out.println("malformed -> " + malformed.status() + " WWW-Authenticate: " + malformed.wwwAuthenticate());

        HttpResponse success = handleRequest("Bearer eyJ.valid.token", decoder);
        System.out.println("valid -> " + success.status() + " body: " + success.body());
    }
}
```

**How to run:** save as `JwtAuthLevel3.java`, run `java JwtAuthLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
no header -> 401 WWW-Authenticate: Bearer realm="api"
malformed -> 401 WWW-Authenticate: Bearer error="invalid_token", error_description="malformed JWT"
valid -> 200 body: {"orders":[],"authenticatedAs":"alice","grantedScope":"read:orders"}
```

What changed: `handleRequest` now produces the actual HTTP-visible response for each case, including the distinct `WWW-Authenticate` header shape (a bare realm challenge when no credential was presented at all, versus an `error="invalid_token"` challenge when one was presented but rejected) — this is precisely the signal a well-behaved API client uses to distinguish "you need to log in" from "your token is bad, get a new one" without any human reading server logs.

## 6. Walkthrough

Trace the successful request from Level 3 end to end, then contrast it with the malformed-token case.

**Step 1 — the inbound request:**
```
GET /api/orders HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJ.valid.token
```

**Step 2 — the filter extracts the token.** `handleRequest` checks the header starts with `"Bearer "` (it does) and slices off `"eyJ.valid.token"` — corresponding to `BearerTokenAuthenticationFilter` pulling the raw token value out of the header before anything else happens.

**Step 3 — decoding.** `decoder.decode("eyJ.valid.token")` runs: the structural check (`startsWith("eyJ")`) passes, the token is found in `wellFormedTokens`, and the expiry check (`System.currentTimeMillis() / 1000 >= expiries.get(token)`) is `false` since the registered expiry is an hour in the future — no exception is thrown, and a `Jwt` is constructed with `subject="alice"` and the full claims map.

**Step 4 — the principal reaches "controller" logic.** `jwt.claim("scope")` reads `"read:orders"` straight out of the decoded claims — this corresponds to a real controller parameter typed `@AuthenticationPrincipal Jwt jwt` giving direct, typed access to exactly this data, with no separate database lookup required.

**Step 5 — the response:**
```
HTTP/1.1 200 OK
Content-Type: application/json

{"orders":[],"authenticatedAs":"alice","grantedScope":"read:orders"}
```

**Contrast — the malformed case, step by step:** `handleRequest("Bearer not-a-jwt", decoder)` extracts `"not-a-jwt"`, calls `decoder.decode`, and immediately fails the `startsWith("eyJ")` structural check — `BadJwtException("malformed JWT")` is thrown before any claim, signature, or expiry logic ever runs. The `catch (BadJwtException e)` block builds a `401` with `error="invalid_token"` and the specific description, never reaching the "controller" body-building line at all.

```
GET /api/orders, Authorization: Bearer eyJ.valid.token
  -> extract token
  -> decode(): structural check OK -> lookup OK -> expiry check OK -> Jwt built
  -> Authentication populated for THIS request
  -> "controller": jwt.claim("scope") -> "read:orders"
  -> 200 OK, body reflects authenticated principal's own claims

GET /api/orders, Authorization: Bearer not-a-jwt
  -> extract token
  -> decode(): structural check FAILS -> BadJwtException, thrown immediately
  -> 401, WWW-Authenticate: Bearer error="invalid_token"
  -> "controller" NEVER reached
```

## 7. Gotchas & takeaways

> **Gotcha:** a missing `Authorization` header is *not* itself a `401` from the JWT filter — it simply leaves the request unauthenticated, and whether that's acceptable depends entirely on `authorizeHttpRequests` (a `permitAll()` matcher lets it through, `anyRequest().authenticated()` rejects it). Conflating "no credential presented" with "credential rejected" in custom error-handling code produces confusing responses; keep them distinct, as `BearerTokenAuthenticationEntryPoint` does.

- The JWT resource server path decodes and validates the token entirely within the request, producing a `JwtAuthenticationToken` whose principal is the `Jwt` object itself — not a `UserDetails`.
- Failures fall into distinct categories with distinct meanings: no credential presented, a structurally malformed token, and a well-formed-but-invalid token (expired, bad signature, wrong issuer) — each should surface a different, useful signal to the caller.
- No `HttpSession` is created or consulted for this authentication path — each request is authenticated fresh from its own bearer token, which is precisely what makes `SessionCreationPolicy.STATELESS` the natural pairing.
- `@AuthenticationPrincipal Jwt jwt` in controller code gives direct access to claims without any additional lookup — the token itself carries everything the request needs to know about who is calling and what they're allowed to do.
- The next three cards unpack what this card treats as a black box: where `JwtDecoder` gets its verification keys (card 0101), which specific claims it checks (card 0103), and how claims become `GrantedAuthority` objects (card 0104).
