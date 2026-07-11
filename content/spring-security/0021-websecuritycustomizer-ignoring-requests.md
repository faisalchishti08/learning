---
card: spring-security
gi: 21
slug: websecuritycustomizer-ignoring-requests
title: "WebSecurityCustomizer (ignoring requests)"
---

## 1. What it is

`WebSecurityCustomizer` is a functional interface (`customize(WebSecurity)`) used to make certain request paths bypass the Spring Security filter chain *entirely* — not "permit all" (which still runs the full chain, just without requiring authentication), but a genuine skip, via `WebSecurity.ignoring()`, most commonly applied to static resources (CSS, JavaScript, images) that carry no security-relevant state at all.

```java
@Bean
public WebSecurityCustomizer webSecurityCustomizer() {
    return web -> web.ignoring().requestMatchers("/css/**", "/js/**", "/images/**");
}
```

## 2. Why & when

`permitAll()` inside `authorizeHttpRequests` still routes a matching request through every filter in the chain — `SecurityContextHolderFilter` still runs, `CsrfFilter` still runs, `ExceptionTranslationFilter` still wraps the call — it merely skips the final authorization check. For truly static, non-sensitive assets (a stylesheet, a logo image) that overhead is pure waste: there is no session to load, no CSRF token relevant to a `GET` for a `.css` file, and no security decision to make at all. `WebSecurityCustomizer`'s `ignoring()` removes these paths from the filter chain's consideration entirely, which is both a minor performance win and a correctness simplification — nothing security-related can go wrong for a path the security filters never even see.

Reach for `WebSecurityCustomizer`/`ignoring()` when:

- Serving static assets (CSS, JavaScript, images, fonts) that carry no user-specific or sensitive data and need no security processing whatsoever.
- A health-check or metrics endpoint that must remain reachable even if the security configuration itself is broken or misconfigured (though this must be weighed carefully — an ignored path is also unprotected from anything the chain would have caught, such as CSRF, so exposing writable operations this way is a mistake).
- Never use `ignoring()` for any path that serves user-specific content, accepts writes, or needs any authentication/authorization decision — for those, `permitAll()` (or a similarly explicit rule) inside `authorizeHttpRequests` is correct instead, since it keeps the path inside the chain's protective machinery even while allowing anonymous access.

## 3. Core concept

```
 request path checked against ignored patterns FIRST, before the filter chain is even entered:

   matches an ignored pattern (e.g. /css/**)?
     YES -> request BYPASSES the entire SecurityFilterChain -- no filters run at all
     NO  -> request enters the normal SecurityFilterChain
              (SecurityContextHolderFilter -> CsrfFilter -> auth filter -> ... -> AuthorizationFilter)

 CONTRAST with permitAll():
   permitAll() path STILL enters the chain -- every filter still runs -- only the FINAL
   authorization check is skipped for that path
```

`ignoring()` removes a path from the chain's consideration entirely; `permitAll()` keeps it in the chain but grants access unconditionally.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request for a static css file matching an ignored pattern bypasses the entire security filter chain and reaches the resource directly while a request for a permitAll path still passes through every filter in the chain before being granted access at the final authorization step">
  <rect x="15" y="25" width="180" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="45" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">GET /css/site.css</text>
  <text x="105" y="58" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(ignored pattern)</text>

  <rect x="15" y="115" width="180" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="135" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">GET /public/info</text>
  <text x="105" y="148" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(permitAll path)</text>

  <rect x="260" y="90" width="230" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="375" y="110" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">full SecurityFilterChain</text>
  <text x="375" y="123" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(context, csrf, auth, authz)</text>

  <rect x="540" y="30" width="80" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="580" y="55" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">resource</text>

  <defs><marker id="a21" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="195" y1="48" x2="540" y2="48" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a21)"/>
  <text x="330" y="42" fill="#8b949e" font-size="6.5" font-family="sans-serif">BYPASSES chain entirely</text>
  <line x1="195" y1="135" x2="260" y2="113" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a21)"/>
  <line x1="490" y1="113" x2="540" y2="55" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a21)"/>
</svg>

Two very different-looking outcomes from two configuration styles that both end up "accessible without authentication."

## 5. Runnable example

The scenario: model both `ignoring()` and `permitAll()` for the same kind of request, instrumenting each filter so the difference in actual work performed is directly observable. Start with a bare-bones filter chain and an `ignoring()` bypass, then add `permitAll()` alongside it for comparison, then add a realistic mixed configuration with static assets, a public API endpoint, and a protected endpoint all handled correctly by the right mechanism.

### Level 1 — Basic

A minimal filter chain (modeled as an ordered list of named steps) and an `ignoring()` check that skips it entirely.

```java
import java.util.*;

public class WebSecurityCustomizerLevel1 {
    static List<String> ignoredPatterns = List.of("/css/", "/js/", "/images/");

    static boolean isIgnored(String path) {
        return ignoredPatterns.stream().anyMatch(path::startsWith);
    }

    static String runFilterChain(String path) {
        List<String> stepsRun = new ArrayList<>();
        stepsRun.add("SecurityContextHolderFilter");
        stepsRun.add("CsrfFilter");
        stepsRun.add("AuthorizationFilter");
        return "ran: " + stepsRun;
    }

    public static void main(String[] args) {
        for (String path : List.of("/css/site.css", "/account")) {
            if (isIgnored(path)) {
                System.out.println(path + " -> BYPASSED entirely, resource served directly");
            } else {
                System.out.println(path + " -> " + runFilterChain(path));
            }
        }
    }
}
```

How to run: `java WebSecurityCustomizerLevel1.java`

`/css/site.css` matches an ignored prefix and never calls `runFilterChain` at all; `/account` doesn't match any ignored pattern and runs every step of the (simplified) chain — the difference is not "which filter denies or allows it," but whether any filter runs at all.

### Level 2 — Intermediate

Add `permitAll()` as a genuinely different mechanism, still running the full chain but granting access at the final step.

```java
import java.util.*;

public class WebSecurityCustomizerLevel2 {
    static List<String> ignoredPatterns = List.of("/css/", "/js/");
    static List<String> permitAllPatterns = List.of("/public/");

    static boolean isIgnored(String path) { return ignoredPatterns.stream().anyMatch(path::startsWith); }
    static boolean isPermitAll(String path) { return permitAllPatterns.stream().anyMatch(path::startsWith); }

    static String runFilterChain(String path, String principal) {
        List<String> stepsRun = new ArrayList<>();
        stepsRun.add("SecurityContextHolderFilter (ran)");
        stepsRun.add("CsrfFilter (ran)");
        String authzResult = isPermitAll(path)
                ? "AuthorizationFilter: permitAll -> granted regardless of principal"
                : (principal != null ? "AuthorizationFilter: granted, principal=" + principal : "AuthorizationFilter: DENIED, 401");
        stepsRun.add(authzResult);
        return String.join(" | ", stepsRun);
    }

    public static void main(String[] args) {
        for (String path : List.of("/css/site.css", "/public/info", "/account")) {
            if (isIgnored(path)) {
                System.out.println(path + " -> BYPASSED entirely (ignoring())");
            } else {
                System.out.println(path + " -> " + runFilterChain(path, null));
            }
        }
    }
}
```

How to run: `java WebSecurityCustomizerLevel2.java`

`/public/info` is *not* in `ignoredPatterns`, so it still runs `SecurityContextHolderFilter` and `CsrfFilter` (both print "(ran)"), and only the final `AuthorizationFilter` step grants access unconditionally via the `permitAll` branch — genuinely more work performed than `/css/site.css`'s complete bypass, even though both end up accessible without a principal.

### Level 3 — Advanced

A realistic three-category configuration — ignored static assets, a permit-all public API endpoint, and a protected endpoint — with request counters proving exactly how much filter work each category actually triggers.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class WebSecurityCustomizerLevel3 {
    static List<String> ignoredPatterns = List.of("/css/", "/js/", "/images/");
    static List<String> permitAllPatterns = List.of("/api/public/");

    static AtomicInteger contextFilterInvocations = new AtomicInteger();
    static AtomicInteger csrfFilterInvocations = new AtomicInteger();
    static AtomicInteger authorizationFilterInvocations = new AtomicInteger();

    static boolean isIgnored(String path) { return ignoredPatterns.stream().anyMatch(path::startsWith); }
    static boolean isPermitAll(String path) { return permitAllPatterns.stream().anyMatch(path::startsWith); }

    static String handle(String path, String principal) {
        if (isIgnored(path)) {
            return "BYPASSED (ignoring()) -- no filter counters incremented";
        }
        contextFilterInvocations.incrementAndGet();
        csrfFilterInvocations.incrementAndGet();
        authorizationFilterInvocations.incrementAndGet();

        if (isPermitAll(path)) return "200 OK (permitAll, filters still ran)";
        if (principal == null) return "401 Unauthorized (filters ran, then denied)";
        return "200 OK, principal=" + principal + " (filters ran, then granted)";
    }

    public static void main(String[] args) {
        record Req(String path, String principal) {}
        List<Req> requests = List.of(
                new Req("/css/site.css", null),
                new Req("/api/public/status", null),
                new Req("/account", "alice"),
                new Req("/js/app.js", null)
        );

        for (Req req : requests) System.out.println(req.path() + " -> " + handle(req.path(), req.principal()));

        System.out.println("total SecurityContextHolderFilter invocations: " + contextFilterInvocations.get());
        System.out.println("total CsrfFilter invocations: " + csrfFilterInvocations.get());
    }
}
```

How to run: `java WebSecurityCustomizerLevel3.java`

Both static-asset requests (`/css/site.css`, `/js/app.js`) return immediately without incrementing any counter; `/api/public/status` and `/account` both increment all three counters (proving the full chain ran for both), even though `/api/public/status` needs no authentication at all — the final counter tally (`2`, not `4`) makes concrete exactly how many requests actually touched the security machinery, versus how many were served directly.

## 6. Walkthrough

Trace the four requests from Level 3 in the order `main` issues them.

1. `handle("/css/site.css", null)` runs first — `isIgnored` checks `"/css/site.css".startsWith("/css/")`, which is `true`, so the method returns immediately with the bypass message, without touching any of the three `AtomicInteger` counters.
2. `handle("/api/public/status", null)` runs next — `isIgnored` returns `false` (no ignored prefix matches `/api/public/`), so all three counters are incremented to `1`; then `isPermitAll("/api/public/status")` checks against `permitAllPatterns = ["/api/public/"]` and returns `true`, so the method returns `"200 OK (permitAll, filters still ran)"` regardless of `principal` being `null`.
3. `handle("/account", "alice")` runs next — again `isIgnored` is `false`, so all three counters increment to `2`; `isPermitAll("/account")` is `false`, and since `principal` is `"alice"` (not `null`), the final branch returns `"200 OK, principal=alice (filters ran, then granted)"`.
4. `handle("/js/app.js", null)` runs last — `isIgnored` returns `true` again, bypassing everything exactly as step 1 did, leaving the counters unchanged at `2`.
5. The final two `println` calls report `contextFilterInvocations.get()` and `csrfFilterInvocations.get()`, both equal to `2` — confirming that of the four total requests, only the two *non-ignored* ones (`/api/public/status` and `/account`) ever actually entered the simulated filter chain, regardless of whether they ultimately required authentication.

```
/css/site.css        -> ignored -> bypass, counters untouched
/api/public/status    -> NOT ignored -> filters run, counters=1 -> permitAll -> 200
/account (alice)      -> NOT ignored -> filters run, counters=2 -> principal present -> 200
/js/app.js            -> ignored -> bypass, counters untouched (still 2)
```

## 7. Gotchas & takeaways

> **Gotcha:** `ignoring()` removes CSRF protection, session handling, and every other filter's safeguards for the matched path — using it for anything beyond genuinely static, read-only, non-sensitive assets (accidentally including a writable endpoint under too-broad a pattern like `/api/**` instead of a narrow `/css/**`) silently strips away protections a developer might assume are still in effect.

- `ignoring()` (via `WebSecurityCustomizer`) makes a path bypass the `SecurityFilterChain` entirely — no filter runs, not even context-loading or CSRF checks; `permitAll()` keeps the path inside the chain and only skips the final authorization decision.
- Reserve `ignoring()` for genuinely static, non-sensitive resources; use `permitAll()` for any endpoint — even a public one — that should still benefit from the chain's other protections.
- Because ignored paths skip the chain entirely, they also skip `SecurityContextHolderFilter` — no `Authentication` will ever be available for an ignored path, even if a valid session or token is present in the request.
- When performance-profiling a high-traffic static-asset path, confirming it is actually configured via `ignoring()` (not merely `permitAll()`) is a legitimate optimization, since it avoids the full chain's per-request overhead.
