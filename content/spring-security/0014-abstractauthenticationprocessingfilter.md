---
card: spring-security
gi: 14
slug: abstractauthenticationprocessingfilter
title: "AbstractAuthenticationProcessingFilter"
---

## 1. What it is

`AbstractAuthenticationProcessingFilter` is the base servlet `Filter` class that every request-based login mechanism in Spring Security extends — `UsernamePasswordAuthenticationFilter` (form login) and `BasicAuthenticationFilter`'s sibling classes all build on the same template: check whether this request matches a configured login URL, if so extract credentials and build an unverified `Authentication`, hand it to the `AuthenticationManager` (which dispatches to `ProviderManager`, covered two cards back), and then either populate the `SecurityContext` and call `onAuthenticationSuccess`, or call `onAuthenticationFailure`. Applications rarely instantiate it directly, but writing a custom login mechanism (an API-key filter, a magic-link filter) almost always means extending it.

```java
public abstract class AbstractAuthenticationProcessingFilter extends GenericFilterBean {
    protected abstract Authentication attemptAuthentication(HttpServletRequest request, HttpServletResponse response)
            throws AuthenticationException;
    // doFilter() calls attemptAuthentication(), then routes to success/failure handlers automatically
}
```

## 2. Why & when

Writing a brand-new authentication mechanism from scratch — parsing a servlet `Filter`, deciding when it applies, calling the `AuthenticationManager`, populating the `SecurityContext`, invoking success/failure handlers, and correctly short-circuiting the rest of the chain on failure — is a lot of repetitive plumbing that every login mechanism needs identically. `AbstractAuthenticationProcessingFilter` factors all of that plumbing into the base class and reduces a custom mechanism's actual work to exactly one method: `attemptAuthentication`, which only needs to extract this specific mechanism's credentials from the request and return an unverified `Authentication` for the `AuthenticationManager` to validate.

Reach for extending `AbstractAuthenticationProcessingFilter` when:

- Building a custom login mechanism that is triggered by a specific request pattern (a specific URL, a specific header) rather than being present on every request — an API-key login endpoint, a one-time magic-link login, a custom SSO callback handler.
- The mechanism needs the same success/failure handling infrastructure (`AuthenticationSuccessHandler`, `AuthenticationFailureHandler`, session fixation protection, remember-me integration) that form login already gets for free, without reimplementing it.
- Contrast this with writing a plain `OncePerRequestFilter` for mechanisms that apply to *every* request and don't represent a discrete "login attempt" (like a filter that merely reads an already-established token on every call) — those don't need this base class's login-specific lifecycle at all.

## 3. Core concept

```
 AbstractAuthenticationProcessingFilter.doFilter(request, response, chain):
   1. requiresAuthentication(request, response)?  -- does the request match THIS filter's configured URL?
        NO  -> chain.doFilter(request, response); return   -- pass through untouched
        YES -> continue
   2. Authentication unverified = attemptAuthentication(request, response)  -- SUBCLASS supplies this
   3. Authentication result = authenticationManager.authenticate(unverified)  -- delegates to ProviderManager
   4. IF successful:
        SecurityContextHolder...setAuthentication(result)
        successHandler.onAuthenticationSuccess(request, response, result)
   5. IF AuthenticationException thrown:
        failureHandler.onAuthenticationFailure(request, response, exception)
```

A subclass only ever implements step 2 — everything else is inherited, shared behavior.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request matching the configured login URL flows into attemptAuthentication supplied by a subclass which produces an unverified Authentication passed to the AuthenticationManager the result is routed to either an AuthenticationSuccessHandler or an AuthenticationFailureHandler both inherited from the base class">
  <rect x="10" y="75" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="80" y="95" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">request matches</text>
  <text x="80" y="108" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">login URL</text>

  <rect x="185" y="75" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="260" y="95" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">attemptAuthentication</text>
  <text x="260" y="108" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(subclass-supplied)</text>

  <rect x="370" y="75" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="445" y="95" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">AuthenticationManager</text>
  <text x="445" y="108" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">.authenticate(...)</text>

  <rect x="555" y="20" width="70" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="590" y="45" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">success</text>

  <rect x="555" y="135" width="70" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="590" y="160" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">failure</text>

  <defs><marker id="a14" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="150" y1="98" x2="185" y2="98" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a14)"/>
  <line x1="335" y1="98" x2="370" y2="98" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a14)"/>
  <line x1="520" y1="88" x2="555" y2="45" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a14)"/>
  <line x1="520" y1="108" x2="555" y2="155" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a14)"/>
</svg>

The subclass owns exactly one box (`attemptAuthentication`); the base class owns URL matching and both outcome paths.

## 5. Runnable example

The scenario: build a minimal `AbstractAuthenticationProcessingFilter`-style base class, then extend it with a custom API-key login mechanism. Start with the base class's shared `doFilter`-style lifecycle and a trivial subclass, then add a real success/failure handler split, then add URL matching so the filter only activates for one specific login endpoint.

### Level 1 — Basic

A minimal base class implementing the shared lifecycle, and one subclass supplying `attemptAuthentication`.

```java
import java.util.*;

public class AbstractAuthFilterLevel1 {
    record Authentication(String principal, boolean verified) {}
    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String msg) { super(msg); }
    }

    static abstract class AbstractAuthenticationProcessingFilter {
        abstract Authentication attemptAuthentication(Map<String, String> requestHeaders);

        // shared lifecycle, identical for every subclass
        String doFilter(Map<String, String> requestHeaders) {
            try {
                Authentication unverified = attemptAuthentication(requestHeaders);
                return "authenticated as " + unverified.principal();
            } catch (AuthenticationException ex) {
                return "authentication failed: " + ex.getMessage();
            }
        }
    }

    static class ApiKeyAuthenticationFilter extends AbstractAuthenticationProcessingFilter {
        Authentication attemptAuthentication(Map<String, String> requestHeaders) {
            String key = requestHeaders.get("X-API-Key");
            if (key == null) throw new AuthenticationException("missing X-API-Key header");
            if (!key.equals("secret-key-123")) throw new AuthenticationException("invalid API key");
            return new Authentication("service-account", true);
        }
    }

    public static void main(String[] args) {
        ApiKeyAuthenticationFilter filter = new ApiKeyAuthenticationFilter();
        System.out.println(filter.doFilter(Map.of("X-API-Key", "secret-key-123")));
        System.out.println(filter.doFilter(Map.of()));
    }
}
```

How to run: `java AbstractAuthFilterLevel1.java`

`ApiKeyAuthenticationFilter` implements only `attemptAuthentication`; the inherited `doFilter` handles the try/catch and result-formatting identically for any future subclass.

### Level 2 — Intermediate

Split success and failure into pluggable handlers, matching the real success/failure-handler pattern.

```java
import java.util.*;
import java.util.function.BiConsumer;

public class AbstractAuthFilterLevel2 {
    record Authentication(String principal, boolean verified) {}
    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String msg) { super(msg); }
    }

    interface SuccessHandler { void onSuccess(Authentication auth); }
    interface FailureHandler { void onFailure(AuthenticationException ex); }

    static abstract class AbstractAuthenticationProcessingFilter {
        SuccessHandler successHandler = auth -> System.out.println("default success: " + auth.principal());
        FailureHandler failureHandler = ex -> System.out.println("default failure: " + ex.getMessage());

        abstract Authentication attemptAuthentication(Map<String, String> requestHeaders);

        void doFilter(Map<String, String> requestHeaders) {
            try {
                Authentication unverified = attemptAuthentication(requestHeaders);
                successHandler.onSuccess(unverified);
            } catch (AuthenticationException ex) {
                failureHandler.onFailure(ex);
            }
        }
    }

    static class ApiKeyAuthenticationFilter extends AbstractAuthenticationProcessingFilter {
        Authentication attemptAuthentication(Map<String, String> requestHeaders) {
            String key = requestHeaders.get("X-API-Key");
            if (key == null || !key.equals("secret-key-123")) throw new AuthenticationException("invalid or missing API key");
            return new Authentication("service-account", true);
        }
    }

    public static void main(String[] args) {
        ApiKeyAuthenticationFilter filter = new ApiKeyAuthenticationFilter();
        // customize the handlers, exactly as a real app would via setAuthenticationSuccessHandler(...)
        filter.successHandler = auth -> System.out.println("issuing session token for " + auth.principal());
        filter.failureHandler = ex -> System.out.println("returning 401: " + ex.getMessage());

        filter.doFilter(Map.of("X-API-Key", "secret-key-123"));
        filter.doFilter(Map.of("X-API-Key", "wrong-key"));
    }
}
```

How to run: `java AbstractAuthFilterLevel2.java`

The base class now holds `successHandler`/`failureHandler` fields with sane defaults, but `main` overrides both with custom behavior before invoking `doFilter` — mirroring `filter.setAuthenticationSuccessHandler(...)` on a real `AbstractAuthenticationProcessingFilter` subclass in a `SecurityFilterChain` bean.

### Level 3 — Advanced

Add URL matching, so the filter only activates for its configured login endpoint and passes through untouched otherwise — the actual first check `AbstractAuthenticationProcessingFilter.doFilter` performs in production.

```java
import java.util.*;

public class AbstractAuthFilterLevel3 {
    record Authentication(String principal, boolean verified) {}
    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String msg) { super(msg); }
    }
    record Request(String path, Map<String, String> headers) {}

    interface SuccessHandler { void onSuccess(Authentication auth); }
    interface FailureHandler { void onFailure(AuthenticationException ex); }

    static abstract class AbstractAuthenticationProcessingFilter {
        private final String loginUrl;
        SuccessHandler successHandler = auth -> System.out.println("success: " + auth.principal());
        FailureHandler failureHandler = ex -> System.out.println("failure: " + ex.getMessage());

        AbstractAuthenticationProcessingFilter(String loginUrl) { this.loginUrl = loginUrl; }

        boolean requiresAuthentication(Request request) { return request.path().equals(loginUrl); }

        abstract Authentication attemptAuthentication(Request request);

        void doFilter(Request request, Runnable restOfChain) {
            if (!requiresAuthentication(request)) {
                System.out.println(request.path() + " -> not the login URL, passing through");
                restOfChain.run();
                return;
            }
            try {
                Authentication unverified = attemptAuthentication(request);
                successHandler.onSuccess(unverified);
            } catch (AuthenticationException ex) {
                failureHandler.onFailure(ex);
            }
        }
    }

    static class ApiKeyAuthenticationFilter extends AbstractAuthenticationProcessingFilter {
        ApiKeyAuthenticationFilter(String loginUrl) { super(loginUrl); }

        Authentication attemptAuthentication(Request request) {
            String key = request.headers().get("X-API-Key");
            if (key == null || !key.equals("secret-key-123")) throw new AuthenticationException("invalid or missing API key");
            return new Authentication("service-account", true);
        }
    }

    public static void main(String[] args) {
        ApiKeyAuthenticationFilter filter = new ApiKeyAuthenticationFilter("/login/api-key");
        filter.successHandler = auth -> System.out.println("issuing session for " + auth.principal());
        filter.failureHandler = ex -> System.out.println("401: " + ex.getMessage());

        Runnable restOfChain = () -> System.out.println("  -> reached controller");

        filter.doFilter(new Request("/login/api-key", Map.of("X-API-Key", "secret-key-123")), restOfChain);
        filter.doFilter(new Request("/orders", Map.of()), restOfChain);
    }
}
```

How to run: `java AbstractAuthFilterLevel3.java`

`requiresAuthentication` now gates everything: only a request to `/login/api-key` triggers `attemptAuthentication`, while any other path (`/orders`) is passed straight through to `restOfChain`, exactly like `UsernamePasswordAuthenticationFilter` only intercepting its configured `loginProcessingUrl` and letting every other request continue down the rest of the `SecurityFilterChain`.

## 6. Walkthrough

Trace Level 3 for two requests: `POST /login/api-key` with a valid key, then `GET /orders`.

1. `filter.doFilter(request, restOfChain)` runs for `/login/api-key` first — `requiresAuthentication` compares `request.path()` against the configured `loginUrl` (`"/login/api-key"`) and returns `true`, since they match exactly.
2. Because `requiresAuthentication` returned `true`, `restOfChain.run()` is *not* called yet; instead `attemptAuthentication(request)` runs, reads `X-API-Key` from the request's headers, finds it equal to `"secret-key-123"`, and returns `new Authentication("service-account", true)` without throwing.
3. Back in `doFilter`, the try block completes normally, so `successHandler.onSuccess(unverified)` runs, printing `"issuing session for service-account"` — in a real filter this is also where `SecurityContextHolder.getContext().setAuthentication(result)` would run, and the response would be committed (a redirect, or a token written to the body).
4. For the second call, `/orders` is checked against `requiresAuthentication`: `"/orders".equals("/login/api-key")` is `false`, so the method immediately prints the pass-through message and calls `restOfChain.run()`, printing `"  -> reached controller"` — this request never touches `attemptAuthentication` at all, since it isn't a login attempt.
5. If a third request hit `/login/api-key` with a missing or wrong key, `attemptAuthentication` would throw `AuthenticationException`, which the surrounding try/catch would route to `failureHandler.onFailure`, printing the configured `"401: ..."` message instead of ever calling `successHandler`.

```
POST /login/api-key  -->  requiresAuthentication=true  -->  attemptAuthentication  -->  successHandler (or failureHandler)
GET  /orders          -->  requiresAuthentication=false -->  restOfChain.run() (skips authentication entirely)
```

## 7. Gotchas & takeaways

> **Gotcha:** forgetting to configure `requiresAuthentication`'s matching URL correctly (or leaving it at a default meant for a different mechanism) is a common source of a custom filter either never firing at all, or firing on every request and rejecting traffic that was never meant to be a login attempt. Always confirm the exact URL/method pattern the filter is registered against matches what the client actually sends.

- `AbstractAuthenticationProcessingFilter` factors the shared login lifecycle (URL matching, delegating to `AuthenticationManager`, success/failure handler dispatch) into the base class, leaving a subclass responsible only for `attemptAuthentication`.
- It is the correct base class specifically for *discrete login attempts* triggered by a specific URL — a filter meant to run on every request checking an already-established credential (like a bearer token already attached to every call) is usually better written as a plain `OncePerRequestFilter` instead.
- Success and failure handling are pluggable (`AuthenticationSuccessHandler`, `AuthenticationFailureHandler`) independently of the credential-extraction logic in `attemptAuthentication`, letting the same custom login mechanism plug into different post-login behaviors (redirect vs. JSON token response) without touching its core authentication logic.
- `UsernamePasswordAuthenticationFilter` is simply the built-in, most common subclass of this base class — understanding the base class explains why every form-login-style mechanism in Spring Security shares the same overall request lifecycle.
