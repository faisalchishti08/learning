---
card: spring-security
gi: 54
slug: custom-authenticationsuccesshandler-failurehandler
title: "Custom AuthenticationSuccessHandler/FailureHandler"
---

## 1. What it is

`AuthenticationSuccessHandler` (`onAuthenticationSuccess(request, response, authentication)`) and `AuthenticationFailureHandler` (`onAuthenticationFailure(request, response, exception)`) are the two interfaces `AbstractAuthenticationProcessingFilter` (from earlier in this section) delegates to once an authentication attempt concludes, deciding exactly what response the client actually receives — the default implementations handle form login's redirect behavior, but a custom implementation can produce anything: a JSON response for an API client, a different redirect target based on the user's role, or custom logging tied to the specific outcome.

```java
@Component
public class RoleBasedSuccessHandler implements AuthenticationSuccessHandler {
    public void onAuthenticationSuccess(HttpServletRequest request, HttpServletResponse response,
                                         Authentication authentication) throws IOException {
        boolean isAdmin = authentication.getAuthorities().stream()
                .anyMatch(a -> a.getAuthority().equals("ROLE_ADMIN"));
        response.sendRedirect(isAdmin ? "/admin/dashboard" : "/dashboard");
    }
}
```

## 2. Why & when

The default success/failure handlers (redirect on success to the saved request or a default URL, redirect on failure to a login-page-plus-error-parameter) fit a traditional server-rendered application well, but many real requirements don't: an API client expects a JSON body, not a redirect it can't follow; different user roles might need different landing pages; a failure might need to trigger additional logic (incrementing a failed-attempt counter, as covered two cards back, though that's more commonly handled via event listeners) beyond simply redirecting back to the login form. Custom handlers exist precisely because `AbstractAuthenticationProcessingFilter`'s design already separates "was authentication successful" (the filter's own concern) from "what should the response actually be" (the handler's concern) — swapping in a custom handler changes only the latter, leaving the entire rest of the authentication mechanism untouched.

Reach for a custom `AuthenticationSuccessHandler`/`AuthenticationFailureHandler` when:

- Building an API where a redirect-based response makes no sense — a JSON success handler returning a token or user profile, and a JSON failure handler returning a structured error body with an appropriate status code.
- Different users need different post-login destinations based on their role or account state — an admin landing on a dashboard, a regular user landing elsewhere, a user who hasn't completed onboarding redirected to a setup flow instead.
- `SimpleUrlAuthenticationSuccessHandler` and `SimpleUrlAuthenticationFailureHandler` (the built-in base classes `SavedRequestAwareAuthenticationSuccessHandler` extends) are worth understanding as a starting point — many custom handlers extend one of these rather than implementing the raw interface from scratch, inheriting useful behavior like redirect-strategy configuration.

## 3. Core concept

```
 AbstractAuthenticationProcessingFilter.doFilter(...), after attemptAuthentication():

   IF authentication SUCCEEDED:
       successHandler.onAuthenticationSuccess(request, response, authenticationResult)
         -- THIS METHOD decides the ENTIRE response: redirect? JSON body? custom header?
   IF an AuthenticationException was thrown:
       failureHandler.onAuthenticationFailure(request, response, exception)
         -- THIS METHOD decides the ENTIRE response for the failure case

 the FILTER itself never hard-codes what the response looks like --
   it delegates BOTH outcomes ENTIRELY to whichever handler is configured
```

Swapping the handler changes the client-facing behavior completely, without touching a single line of the authentication logic itself.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="After an authentication attempt concludes the filter delegates entirely to either an AuthenticationSuccessHandler or an AuthenticationFailureHandler each of which independently decides the full shape of the response whether that is a redirect a JSON body or custom logic">
  <rect x="15" y="65" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">authentication</text>
  <text x="90" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">attempt concludes</text>

  <rect x="230" y="15" width="200" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="330" y="36" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">AuthenticationSuccessHandler</text>
  <text x="330" y="49" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">decides the ENTIRE response</text>

  <rect x="230" y="105" width="200" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="330" y="126" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">AuthenticationFailureHandler</text>
  <text x="330" y="139" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">decides the ENTIRE response</text>

  <defs><marker id="a54" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="80" x2="230" y2="38" stroke="#8b949e" stroke-width="1" marker-end="url(#a54)"/>
  <text x="185" y="55" fill="#8b949e" font-size="6.5" font-family="sans-serif">success</text>
  <line x1="165" y1="95" x2="230" y2="128" stroke="#8b949e" stroke-width="1" marker-end="url(#a54)"/>
  <text x="185" y="115" fill="#8b949e" font-size="6.5" font-family="sans-serif">failure</text>
</svg>

Each handler owns the entire response — nothing about the response shape is decided anywhere else.

## 5. Runnable example

The scenario: implement a JSON-based success/failure handler pair (for an API client), then add role-based redirect logic, then combine both into a single handler that detects the client type (API vs. browser) and responds appropriately — a realistic dual-purpose application.

### Level 1 — Basic

A JSON success handler and a JSON failure handler, replacing redirect-based defaults entirely.

```java
import java.util.*;

public class CustomHandlerLevel1 {
    record Authentication(String principal, Set<String> authorities) {}
    record HttpResponse(int status, String body) {}

    interface AuthenticationSuccessHandler { HttpResponse onSuccess(Authentication auth); }
    interface AuthenticationFailureHandler { HttpResponse onFailure(String exceptionMessage); }

    static AuthenticationSuccessHandler jsonSuccessHandler = auth ->
            new HttpResponse(200, "{\"status\":\"ok\",\"username\":\"" + auth.principal() + "\",\"authorities\":" + auth.authorities() + "}");

    static AuthenticationFailureHandler jsonFailureHandler = message ->
            new HttpResponse(401, "{\"status\":\"error\",\"message\":\"" + message + "\"}");

    public static void main(String[] args) {
        HttpResponse success = jsonSuccessHandler.onSuccess(new Authentication("alice", Set.of("ROLE_USER")));
        System.out.println(success);

        HttpResponse failure = jsonFailureHandler.onFailure("Bad credentials");
        System.out.println(failure);
    }
}
```

How to run: `java CustomHandlerLevel1.java`

Both handlers produce a structured JSON body with an appropriate status code instead of any redirect — a JavaScript client (or any API consumer) can parse either response directly, something a `302` redirect response would not offer at all.

### Level 2 — Intermediate

Add role-based redirect logic for a browser-facing success handler, landing different users on different pages.

```java
import java.util.*;

public class CustomHandlerLevel2 {
    record Authentication(String principal, Set<String> authorities) {}
    record HttpResponse(int status, String location) {}

    interface AuthenticationSuccessHandler { HttpResponse onSuccess(Authentication auth); }

    static AuthenticationSuccessHandler roleBasedSuccessHandler = auth -> {
        if (auth.authorities().contains("ROLE_ADMIN")) return new HttpResponse(302, "/admin/dashboard");
        if (auth.authorities().contains("ROLE_ONBOARDING_INCOMPLETE")) return new HttpResponse(302, "/onboarding/setup");
        return new HttpResponse(302, "/dashboard"); // the DEFAULT destination for a regular, fully-onboarded user
    };

    public static void main(String[] args) {
        System.out.println("admin login: " + roleBasedSuccessHandler.onSuccess(new Authentication("alice", Set.of("ROLE_ADMIN"))));
        System.out.println("new user login: " + roleBasedSuccessHandler.onSuccess(
                new Authentication("bob", Set.of("ROLE_USER", "ROLE_ONBOARDING_INCOMPLETE"))));
        System.out.println("regular user login: " + roleBasedSuccessHandler.onSuccess(new Authentication("carol", Set.of("ROLE_USER"))));
    }
}
```

How to run: `java CustomHandlerLevel2.java`

The identical handler, given three different authority sets, produces three different redirect destinations — alice (admin) lands on `/admin/dashboard`, bob (mid-onboarding) lands on `/onboarding/setup`, and carol (a regular, fully set-up user) lands on the plain `/dashboard`, all decided purely by inspecting the authenticated user's authorities.

### Level 3 — Advanced

Combine both approaches into one handler that detects the client type from the request and responds with either JSON or a role-based redirect accordingly — a single application correctly serving both an API and a browser-facing UI.

```java
import java.util.*;

public class CustomHandlerLevel3 {
    record Authentication(String principal, Set<String> authorities) {}
    record Request(Map<String, String> headers) {}
    record HttpResponse(int status, String contentTypeOrLocation, String body) {}

    interface AuthenticationSuccessHandler { HttpResponse onSuccess(Request request, Authentication auth); }
    interface AuthenticationFailureHandler { HttpResponse onFailure(Request request, String exceptionMessage); }

    static boolean isApiClient(Request request) {
        String accept = request.headers().getOrDefault("Accept", "");
        return accept.contains("application/json");
    }

    static AuthenticationSuccessHandler adaptiveSuccessHandler = (request, auth) -> {
        if (isApiClient(request)) {
            return new HttpResponse(200, "application/json",
                    "{\"status\":\"ok\",\"username\":\"" + auth.principal() + "\"}");
        }
        String destination = auth.authorities().contains("ROLE_ADMIN") ? "/admin/dashboard" : "/dashboard";
        return new HttpResponse(302, destination, null);
    };

    static AuthenticationFailureHandler adaptiveFailureHandler = (request, message) -> {
        if (isApiClient(request)) {
            return new HttpResponse(401, "application/json", "{\"status\":\"error\",\"message\":\"" + message + "\"}");
        }
        return new HttpResponse(302, "/login?error", null);
    };

    public static void main(String[] args) {
        Request apiRequest = new Request(Map.of("Accept", "application/json"));
        Request browserRequest = new Request(Map.of("Accept", "text/html"));
        Authentication admin = new Authentication("alice", Set.of("ROLE_ADMIN"));

        System.out.println("API client, success: " + adaptiveSuccessHandler.onSuccess(apiRequest, admin));
        System.out.println("browser client, success: " + adaptiveSuccessHandler.onSuccess(browserRequest, admin));
        System.out.println("API client, failure: " + adaptiveFailureHandler.onFailure(apiRequest, "Bad credentials"));
        System.out.println("browser client, failure: " + adaptiveFailureHandler.onFailure(browserRequest, "Bad credentials"));
    }
}
```

How to run: `java CustomHandlerLevel3.java`

The identical `admin` authentication produces a JSON body for the API request and a role-based redirect for the browser request; the identical failure message produces a JSON error body for the API request and a plain redirect for the browser request — one pair of handlers correctly serving two entirely different client types based purely on inspecting the request's `Accept` header.

## 6. Walkthrough

Trace `adaptiveSuccessHandler.onSuccess(apiRequest, admin)` from Level 3.

1. `isApiClient(apiRequest)` runs first: `request.headers().getOrDefault("Accept", "")` retrieves `"application/json"` from `apiRequest`'s headers; `.contains("application/json")` checks this string, which is `true` — so `isApiClient` returns `true`.
2. Because `isApiClient` returned `true`, the `if` branch inside `adaptiveSuccessHandler` executes: it constructs `new HttpResponse(200, "application/json", "{\"status\":\"ok\",\"username\":\"alice\"}")`, embedding `auth.principal()` (which is `"alice"`) directly into the JSON body string.
3. This response object is returned immediately — the role-based redirect logic further down in the method (checking `ROLE_ADMIN`) is never reached at all for this call, since the method returns from within the `if` block.
4. Compare this with `adaptiveSuccessHandler.onSuccess(browserRequest, admin)`, called next in `main`: `isApiClient(browserRequest)` checks `"text/html".contains("application/json")`, which is `false`, so the method falls through past the `if` block entirely, reaching `auth.authorities().contains("ROLE_ADMIN")` — since `admin`'s authorities do contain `"ROLE_ADMIN"`, `destination` is set to `"/admin/dashboard"`, and the method returns a `302` redirect response instead.
5. Both calls received the *identical* `admin` `Authentication` object, but produced entirely different `HttpResponse` shapes — the sole deciding factor in each case was the incoming request's own `Accept` header, inspected fresh at the start of each call.

```
adaptiveSuccessHandler.onSuccess(apiRequest, admin):
  isApiClient -> Accept contains "application/json" -> TRUE
  -> return JSON response {"status":"ok","username":"alice"}  (ROLE_ADMIN check NEVER reached)

adaptiveSuccessHandler.onSuccess(browserRequest, admin):
  isApiClient -> Accept is "text/html" -> FALSE
  -> falls through to role check -> ROLE_ADMIN present -> redirect to /admin/dashboard
```

## 7. Gotchas & takeaways

> **Gotcha:** a custom `AuthenticationSuccessHandler` completely replacing the default `SavedRequestAwareAuthenticationSuccessHandler` silently loses the saved-request redirect behavior (from an earlier card in this section) unless the custom handler explicitly reimplements it — a browser-facing custom handler that unconditionally redirects to one fixed URL, rather than checking for a saved request first, regresses the "land back where you were headed" experience users may already expect.

- `AuthenticationSuccessHandler` and `AuthenticationFailureHandler` fully own the response for their respective outcomes — swapping either one changes client-facing behavior completely, without touching the underlying authentication mechanism at all.
- Custom handlers are the natural place to serve genuinely different response shapes to different client types (JSON for an API, a redirect for a browser), typically by inspecting a request header like `Accept`.
- Role- or state-based redirect logic (different landing pages for different user types) belongs naturally in a custom success handler, since it has full access to the authenticated user's authorities at exactly the right moment.
- When replacing a built-in handler like `SavedRequestAwareAuthenticationSuccessHandler`, deliberately consider whether any of its existing behavior (saved-request redirects, in that specific case) needs to be preserved in the custom replacement, rather than being silently lost.
