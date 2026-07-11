---
card: spring-security
gi: 27
slug: http-basic-authentication
title: "HTTP Basic authentication"
---

## 1. What it is

HTTP Basic is the authentication scheme defined by RFC 7617, where the client sends credentials on every single request as an `Authorization: Basic <base64(username:password)>` header — no session, no cookie, no login page; `BasicAuthenticationFilter` extracts and decodes this header on each request and, if present, hands the credentials to the `AuthenticationManager` exactly like form login does, producing the same kind of `UsernamePasswordAuthenticationToken`. `http.httpBasic(Customizer.withDefaults())` enables it.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .httpBasic(Customizer.withDefaults())
        .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS));
    return http.build();
}
```

```
Authorization: Basic YWxpY2U6aHVudGVyMg==
                     ^ base64("alice:hunter2")
```

## 2. Why & when

HTTP Basic is deliberately the simplest possible authentication scheme — no redirects, no HTML, no multi-step handshake — which makes it well suited to machine-to-machine calls, internal service traffic, and quick API testing, where a client can trivially construct the header itself without needing to follow a browser-oriented login flow. Its major weakness is exactly its simplicity: the base64-encoded credentials are *not encrypted*, merely encoded (trivially reversible), and are resent on every single request, so it must always run over TLS, and it is a poor fit for browser-facing applications since browsers render a jarring native credential prompt with no way to "log out" short of closing the browser.

Reach for HTTP Basic when:

- Building or testing internal service-to-service calls, or a simple API where a full OAuth2/token-based flow would be unnecessary overhead relative to the security requirements.
- Quick manual testing of a protected endpoint via a tool like `curl -u username:password` — Basic's simplicity makes it convenient for this, even if it isn't the production authentication mechanism.
- Contrast with form login: Basic never redirects and never renders any page of its own — a failed Basic attempt gets a bare `401` with a `WWW-Authenticate: Basic realm="..."` header, prompting the client (or a browser's native dialog) to retry, rather than a redirect to any login page.

## 3. Core concept

```
 EVERY request must carry:
   Authorization: Basic <base64(username:password)>

 BasicAuthenticationFilter.doFilterInternal(request):
   1. read "Authorization" header
   2. IF missing or not "Basic " prefixed -> pass through (let a LATER stage decide, e.g. reject as unauthenticated)
   3. base64-DECODE the header value -> "username:password"
   4. split on first ":" -> username, password
   5. build UsernamePasswordAuthenticationToken(username, password) -- UNVERIFIED
   6. authenticationManager.authenticate(unverified)  -- same path as form login, same AuthenticationProvider
   7. IF success: SecurityContextHolder populated (but typically NOT persisted -- re-sent every request anyway)
   8. IF failure: 401 + WWW-Authenticate: Basic realm="..."
```

Every request is independently authenticated from scratch — there is no session-based "remembering" of a prior successful Basic login.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request carrying a base64 encoded Authorization Basic header is decoded by BasicAuthenticationFilter into a username and password wrapped in the same UsernamePasswordAuthenticationToken used by form login and verified through the identical AuthenticationManager path">
  <rect x="10" y="60" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="100" y="80" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Authorization: Basic</text>
  <text x="100" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">YWxpY2U6aHVudGVyMg==</text>

  <rect x="240" y="60" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="325" y="80" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">BasicAuthenticationFilter</text>
  <text x="325" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">base64-decode -&gt; alice:hunter2</text>

  <rect x="460" y="60" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="80" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">UsernamePassword</text>
  <text x="540" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">AuthenticationToken</text>

  <defs><marker id="a27" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="190" y1="85" x2="240" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a27)"/>
  <line x1="410" y1="85" x2="460" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a27)"/>
</svg>

The same token type form login produces — Basic differs only in *how* the credentials arrive, not in how they're subsequently verified.

## 5. Runnable example

The scenario: build a Basic-header decoder and verifier, then add the `WWW-Authenticate` challenge response for missing/invalid credentials, then add per-request re-authentication proving no session state is relied upon at all.

### Level 1 — Basic

Decode a Basic header and verify the resulting credentials.

```java
import java.util.*;

public class HttpBasicLevel1 {
    static Map<String, String> validCredentials = Map.of("alice", "hunter2");

    record DecodedCredentials(String username, String password) {}

    static DecodedCredentials decodeBasicHeader(String headerValue) {
        String base64Part = headerValue.substring("Basic ".length());
        String decoded = new String(Base64.getDecoder().decode(base64Part));
        int colonIndex = decoded.indexOf(':');
        return new DecodedCredentials(decoded.substring(0, colonIndex), decoded.substring(colonIndex + 1));
    }

    public static void main(String[] args) {
        String header = "Basic " + Base64.getEncoder().encodeToString("alice:hunter2".getBytes());
        System.out.println("raw header: " + header);

        DecodedCredentials creds = decodeBasicHeader(header);
        System.out.println("decoded username: " + creds.username() + ", password: " + creds.password());

        boolean matches = validCredentials.get(creds.username()) != null && validCredentials.get(creds.username()).equals(creds.password());
        System.out.println("authenticated? " + matches);
    }
}
```

How to run: `java HttpBasicLevel1.java`

`decodeBasicHeader` strips the `"Basic "` prefix, base64-decodes the remainder to recover `"alice:hunter2"`, and splits on the first colon — exactly the parsing `BasicAuthenticationFilter` performs on every request carrying this header.

### Level 2 — Intermediate

Add the `401` + `WWW-Authenticate` challenge response for missing or invalid credentials, matching Basic's actual failure behavior.

```java
import java.util.*;

public class HttpBasicLevel2 {
    static Map<String, String> validCredentials = Map.of("alice", "hunter2");
    static final String REALM = "MyApp";

    record DecodedCredentials(String username, String password) {}

    static DecodedCredentials decodeBasicHeader(String headerValue) {
        String base64Part = headerValue.substring("Basic ".length());
        String decoded = new String(Base64.getDecoder().decode(base64Part));
        int colonIndex = decoded.indexOf(':');
        return new DecodedCredentials(decoded.substring(0, colonIndex), decoded.substring(colonIndex + 1));
    }

    static String handleRequest(String authorizationHeader) {
        if (authorizationHeader == null || !authorizationHeader.startsWith("Basic ")) {
            return "401 Unauthorized, WWW-Authenticate: Basic realm=\"" + REALM + "\" (no Basic header present)";
        }
        DecodedCredentials creds = decodeBasicHeader(authorizationHeader);
        String storedPassword = validCredentials.get(creds.username());
        if (storedPassword == null || !storedPassword.equals(creds.password())) {
            return "401 Unauthorized, WWW-Authenticate: Basic realm=\"" + REALM + "\" (bad credentials)";
        }
        return "200 OK, authenticated as " + creds.username();
    }

    public static void main(String[] args) {
        System.out.println(handleRequest(null));
        String validHeader = "Basic " + Base64.getEncoder().encodeToString("alice:hunter2".getBytes());
        System.out.println(handleRequest(validHeader));
        String invalidHeader = "Basic " + Base64.getEncoder().encodeToString("alice:wrongpass".getBytes());
        System.out.println(handleRequest(invalidHeader));
    }
}
```

How to run: `java HttpBasicLevel2.java`

A missing header and a header with wrong credentials both produce a `401` carrying the `WWW-Authenticate: Basic realm="MyApp"` header — this is the signal that prompts a browser to pop up its native credential dialog, or tells a programmatic client (like `curl`) exactly what authentication scheme and realm are expected.

### Level 3 — Advanced

Prove Basic's fully stateless nature: run several requests with no session object involved at all, each independently re-verifying credentials from scratch, including one where the credentials happen to change between requests.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class HttpBasicLevel3 {
    static Map<String, String> validCredentials = new HashMap<>(Map.of("alice", "hunter2"));
    static final String REALM = "MyApp";
    static AtomicInteger totalVerificationsPerformed = new AtomicInteger();

    record DecodedCredentials(String username, String password) {}

    static DecodedCredentials decodeBasicHeader(String headerValue) {
        String base64Part = headerValue.substring("Basic ".length());
        String decoded = new String(Base64.getDecoder().decode(base64Part));
        int colonIndex = decoded.indexOf(':');
        return new DecodedCredentials(decoded.substring(0, colonIndex), decoded.substring(colonIndex + 1));
    }

    // NOTE: no session parameter anywhere -- every call is independently, fully re-verified
    static String handleRequest(String authorizationHeader) {
        totalVerificationsPerformed.incrementAndGet(); // increments on EVERY call, unlike a session-backed mechanism
        if (authorizationHeader == null || !authorizationHeader.startsWith("Basic ")) {
            return "401 Unauthorized, WWW-Authenticate: Basic realm=\"" + REALM + "\"";
        }
        DecodedCredentials creds = decodeBasicHeader(authorizationHeader);
        String storedPassword = validCredentials.get(creds.username());
        if (storedPassword == null || !storedPassword.equals(creds.password())) {
            return "401 Unauthorized, WWW-Authenticate: Basic realm=\"" + REALM + "\"";
        }
        return "200 OK, authenticated as " + creds.username();
    }

    static String basicHeaderFor(String username, String password) {
        return "Basic " + Base64.getEncoder().encodeToString((username + ":" + password).getBytes());
    }

    public static void main(String[] args) {
        String header = basicHeaderFor("alice", "hunter2");

        for (int i = 1; i <= 3; i++) {
            System.out.println("request " + i + ": " + handleRequest(header));
        }

        // password changed server-side; the SAME old header now fails, immediately, on the very next request
        validCredentials.put("alice", "newpassword");
        System.out.println("request 4 (password changed server-side, stale header): " + handleRequest(header));

        System.out.println("total independent verifications performed: " + totalVerificationsPerformed.get());
    }
}
```

How to run: `java HttpBasicLevel3.java`

Requests 1 through 3 all succeed using the identical header, each one independently re-decoding and re-verifying the credentials (`totalVerificationsPerformed` increments every time, proving no caching or session shortcut is taken); the moment `validCredentials` changes server-side, the *very next* request — still carrying the old, now-stale header — is rejected immediately, with no separate "logout" or session-invalidation step required, since there was never any session-backed state to invalidate in the first place.

## 6. Walkthrough

Trace all four calls to `handleRequest` in Level 3's `main`.

1. Request 1: `handleRequest(header)` increments `totalVerificationsPerformed` to `1`, then decodes `header` to recover `("alice", "hunter2")`, checks `validCredentials.get("alice")` (currently `"hunter2"`), finds it matches, and returns the `200 OK` success message.
2. Requests 2 and 3 repeat the *exact same* decode-and-verify work independently — `totalVerificationsPerformed` reaches `2`, then `3` — nothing from request 1 is reused or cached; each request is authenticated completely from scratch, purely from the header it itself carries.
3. Between requests 3 and 4, `validCredentials.put("alice", "newpassword")` changes the stored password server-side — this models an administrator resetting alice's password, or alice changing it through some other channel.
4. Request 4 calls `handleRequest(header)` with the *same* `header` variable used in requests 1 through 3 (still encoding `"alice:hunter2"`) — decoding it again produces the same `("alice", "hunter2")` pair, but now `validCredentials.get("alice")` returns `"newpassword"`, which does not equal `"hunter2"`, so the method returns the `401` message.
5. The final `println` reports `totalVerificationsPerformed.get()` as `4` — one increment per call, confirming that all four requests, including the three identical successful ones, were each fully and independently re-verified, with no memoized "already authenticated" shortcut taken anywhere.

```
request 1 (header: alice:hunter2)  -> stored password="hunter2" -> MATCH -> 200
request 2 (same header)            -> stored password="hunter2" -> MATCH -> 200
request 3 (same header)            -> stored password="hunter2" -> MATCH -> 200
--- server changes alice's password to "newpassword" ---
request 4 (SAME old header)        -> stored password="newpassword" -> NO MATCH -> 401 (instantly, no logout needed)
```

## 7. Gotchas & takeaways

> **Gotcha:** base64 encoding is *not* encryption — anyone who can observe the raw `Authorization` header (an unencrypted connection, a misconfigured proxy log, browser developer tools shared in a bug report) can trivially decode the username and password with any standard base64 tool. HTTP Basic must always be used over TLS; using it over plain HTTP exposes credentials in the clear on every single request.

- Every request under HTTP Basic is independently, fully re-authenticated from its own header — there is no session, no "remember me," and no persisted `SecurityContext` to rely on, which also means a password change takes effect immediately on the very next request, with no separate logout step needed.
- The `WWW-Authenticate: Basic realm="..."` response header is what tells a client (or prompts a browser's native dialog) to retry with credentials — its absence is a common sign that Basic isn't actually configured, even if a `401` is otherwise being returned correctly.
- Pairing `httpBasic()` with `sessionManagement(STATELESS)` is a natural and common combination, since Basic's per-request credential model doesn't benefit from session persistence at all.
- Prefer HTTP Basic for machine-to-machine or internal traffic and quick manual testing; prefer form login (or OAuth2/token-based schemes, covered in later cards) for any browser-facing, human-driven login experience.
