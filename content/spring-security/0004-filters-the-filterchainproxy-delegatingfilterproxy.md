---
card: spring-security
gi: 4
slug: filters-the-filterchainproxy-delegatingfilterproxy
title: "Filters & the FilterChainProxy / DelegatingFilterProxy"
---

## 1. What it is

Spring Security intercepts requests using the Servlet API's own `Filter` mechanism, but wires them into the application through two bridging components — `DelegatingFilterProxy`, a single, thin Servlet `Filter` registered directly with the servlet container that delegates every request to a named Spring bean (decoupling Spring Security's filters from needing to be manually registered with the container), and `FilterChainProxy`, the actual Spring bean `DelegatingFilterProxy` delegates to, which internally holds and invokes Spring Security's own full, ordered chain of specific-purpose filters (authentication, CSRF protection, session management, and others).

```java
// registered ONCE with the servlet container, regardless of how many Spring Security filters actually exist
// (Spring Boot auto-configures this automatically -- rarely hand-written)
public class DelegatingFilterProxy implements Filter {
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain) {
        // delegates to the Spring-managed "springSecurityFilterChain" bean -- which IS a FilterChainProxy
        springSecurityFilterChain.doFilter(req, res, chain);
    }
}
```

```
FilterChainProxy internally holds the ORDERED list:
  [ SecurityContextPersistenceFilter, CsrfFilter, UsernamePasswordAuthenticationFilter, ..., AuthorizationFilter ]
```

## 2. Why & when

The Servlet API's own `Filter` mechanism is the natural place to intercept every request before it reaches application code, but registering many individual, fine-grained security filters directly with the servlet container is awkward — servlet container filter registration typically happens outside of Spring's own dependency injection and configuration lifecycle, making it hard to configure Spring Security's filters using ordinary Spring beans and properties. `DelegatingFilterProxy` solves this by being the *only* filter the servlet container itself needs to know about — a thin adapter that simply hands off to whatever Spring-managed bean is configured to actually handle security — while `FilterChainProxy` (the bean it delegates to) is where Spring Security's real, rich, Spring-configured filter chain actually lives, fully able to use dependency injection, `@Bean` configuration, and all of Spring's usual machinery.

Reach for understanding this two-layer bridging when:

- Debugging why a security filter isn't being invoked, or is being invoked in an unexpected order — knowing that `DelegatingFilterProxy` is a thin, single entry point and `FilterChainProxy` is where the actual ordered chain lives clarifies where to look (almost always within `FilterChainProxy`'s configuration, not the servlet-level registration).
- Understanding how Spring Security integrates with a servlet container without requiring manual, container-specific filter registration for every individual security concern — this bridging is what lets `SecurityFilterChain` beans (the next card) be configured entirely through ordinary Spring `@Bean` methods.
- Adding a custom filter into Spring Security's own chain — custom filters are added to the `FilterChainProxy`'s internal ordered list (via `HttpSecurity`'s configuration API), not registered separately with the servlet container, which is what keeps custom security logic consistently ordered relative to Spring Security's own built-in filters.

## 3. Core concept

```
 servlet container's OWN filter registration:
   [ ONE entry: DelegatingFilterProxy ]   <- the container knows about exactly this one thin filter

 DelegatingFilterProxy.doFilter(request, response, chain):
   delegates to the Spring bean named "springSecurityFilterChain"
        |
        v
 that bean IS a FilterChainProxy, which internally holds the REAL, ordered list:
   [ SecurityContextPersistenceFilter -> CsrfFilter -> UsernamePasswordAuthenticationFilter -> ... -> AuthorizationFilter ]

 EACH filter in this internal list runs in order, each deciding whether to
 pass the request along to the NEXT filter, or short-circuit (reject) it
```

The servlet container's own filter registration stays maximally simple (one entry), while all of Spring Security's actual complexity and configurability lives inside the Spring-managed `FilterChainProxy`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The servlet container registers only DelegatingFilterProxy which delegates to a Spring managed FilterChainProxy bean containing the actual ordered list of Spring Security filters that a request passes through in sequence">
  <rect x="20" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="110" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">servlet container</text>
  <text x="110" y="56" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">registers ONE filter</text>

  <rect x="250" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="340" y="48" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">DelegatingFilterProxy</text>

  <rect x="480" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="48" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">FilterChainProxy</text>

  <rect x="70" y="110" width="500" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="320" y="132" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">SecurityContext -&gt; CSRF -&gt; Authentication -&gt; ... -&gt; Authorization filters</text>
  <text x="320" y="146" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">the REAL, ordered, Spring-managed chain -- lives INSIDE FilterChainProxy</text>

  <defs><marker id="a4" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="200" y1="43" x2="250" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a4)"/>
  <line x1="430" y1="43" x2="480" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a4)"/>
  <line x1="550" y1="66" x2="550" y2="110" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3" marker-end="url(#a4)"/>
</svg>

One thin servlet-registered adapter, delegating to a rich, Spring-managed chain that's where all the actual security logic lives.

## 5. Runnable example

The scenario: model the two-layer bridging directly — a single "container-registered" delegating filter forwarding to a Spring-managed chain of ordered inner filters, each able to short-circuit the request. Start with a single delegating filter forwarding to an empty chain, then add multiple ordered inner filters, then add a filter that short-circuits the chain, demonstrating exactly how a rejection at one filter stops the remaining filters (and the eventual controller) from ever running.

### Level 1 — Basic

A single delegating filter forwarding to an (initially empty) inner chain — modeling `DelegatingFilterProxy`'s bridging role alone.

```java
import java.util.*;
import java.util.function.Function;

public class FilterChainLevel1 {
    record Request(String path, boolean hasValidSession) {}

    // stands in for FilterChainProxy -- holds the REAL, ordered list of security filters
    static class FilterChainProxy {
        List<Function<Request, Boolean>> filters = new ArrayList<>(); // each filter: request -> "should continue?"
        boolean process(Request request) {
            for (Function<Request, Boolean> filter : filters) {
                if (!filter.apply(request)) return false; // this filter REJECTED -- stop here
            }
            return true; // every filter passed
        }
    }

    // stands in for DelegatingFilterProxy -- the ONLY thing the "servlet container" itself knows about
    static class DelegatingFilterProxy {
        FilterChainProxy delegate;
        DelegatingFilterProxy(FilterChainProxy delegate) { this.delegate = delegate; }
        boolean doFilter(Request request) {
            System.out.println("DelegatingFilterProxy: delegating to FilterChainProxy");
            return delegate.process(request);
        }
    }

    public static void main(String[] args) {
        FilterChainProxy chain = new FilterChainProxy(); // empty for now -- no filters configured yet
        DelegatingFilterProxy container = new DelegatingFilterProxy(chain);

        boolean result = container.doFilter(new Request("/orders", true));
        System.out.println("request allowed through? " + result);
    }
}
```

How to run: `java FilterChainLevel1.java`

With `chain.filters` empty, `process` trivially returns `true` for any request — this models the bridging structure alone, before any actual security filters are added to the internal chain.

### Level 2 — Intermediate

Add multiple ordered inner filters, each contributing its own check, running in sequence.

```java
import java.util.*;
import java.util.function.Function;

public class FilterChainLevel2 {
    record Request(String path, boolean hasValidSession, boolean hasCsrfToken) {}

    static class FilterChainProxy {
        List<Function<Request, Boolean>> filters = new ArrayList<>();
        boolean process(Request request) {
            for (Function<Request, Boolean> filter : filters) {
                if (!filter.apply(request)) return false;
            }
            return true;
        }
    }

    static class DelegatingFilterProxy {
        FilterChainProxy delegate;
        DelegatingFilterProxy(FilterChainProxy delegate) { this.delegate = delegate; }
        boolean doFilter(Request request) { return delegate.process(request); }
    }

    public static void main(String[] args) {
        FilterChainProxy chain = new FilterChainProxy();

        // ordered EXACTLY as Spring Security would order them: session/context first, then CSRF, etc.
        chain.filters.add(request -> {
            System.out.println("filter 1 (SecurityContext): checking session validity");
            return request.hasValidSession();
        });
        chain.filters.add(request -> {
            System.out.println("filter 2 (CSRF): checking CSRF token");
            return request.hasCsrfToken();
        });

        DelegatingFilterProxy container = new DelegatingFilterProxy(chain);

        boolean result = container.doFilter(new Request("/orders", true, true));
        System.out.println("request allowed through? " + result);
    }
}
```

How to run: `java FilterChainLevel2.java`

Both filters run in the order they were added, each printing its own check before returning — with both checks passing (`hasValidSession=true`, `hasCsrfToken=true`), the request is ultimately allowed through, having passed through two distinct, independently-added filters exactly as `FilterChainProxy` would invoke its own internally-ordered list of real Spring Security filters.

### Level 3 — Advanced

Add a filter that short-circuits the chain (a missing CSRF token, for instance), demonstrating that a rejection at one filter stops every remaining filter — and the eventual controller — from ever running.

```java
import java.util.*;
import java.util.function.Function;

public class FilterChainLevel3 {
    record Request(String path, boolean hasValidSession, boolean hasCsrfToken) {}

    static class FilterChainProxy {
        List<Function<Request, Boolean>> filters = new ArrayList<>();
        boolean process(Request request) {
            for (int i = 0; i < filters.size(); i++) {
                boolean passed = filters.get(i).apply(request);
                if (!passed) {
                    System.out.println("  -> REJECTED at filter index " + i + " -- chain STOPS here, remaining filters SKIPPED");
                    return false;
                }
            }
            System.out.println("  -> ALL filters passed");
            return true;
        }
    }

    static class DelegatingFilterProxy {
        FilterChainProxy delegate;
        DelegatingFilterProxy(FilterChainProxy delegate) { this.delegate = delegate; }
        boolean doFilter(Request request) { return delegate.process(request); }
    }

    static void simulateControllerIfAllowed(boolean chainResult) {
        if (chainResult) System.out.println("  controller method: RUNS");
        else System.out.println("  controller method: NEVER RUNS");
    }

    public static void main(String[] args) {
        FilterChainProxy chain = new FilterChainProxy();
        chain.filters.add(request -> { System.out.println("filter 0 (SecurityContext)"); return request.hasValidSession(); });
        chain.filters.add(request -> { System.out.println("filter 1 (CSRF)"); return request.hasCsrfToken(); });
        chain.filters.add(request -> { System.out.println("filter 2 (Authorization) -- should NEVER print if filter 1 rejects"); return true; });

        DelegatingFilterProxy container = new DelegatingFilterProxy(chain);

        System.out.println("-- request WITH a valid session but MISSING CSRF token --");
        boolean result = container.doFilter(new Request("/orders", true, false)); // hasCsrfToken=false
        simulateControllerIfAllowed(result);
    }
}
```

How to run: `java FilterChainLevel3.java`

`filter 2`'s print statement never appears in the output — the chain stops at `filter 1` (index `1`), because `hasCsrfToken` is `false`, and `process`'s loop returns `false` immediately without ever calling `filters.get(2)` — `simulateControllerIfAllowed(false)` correctly reports the controller method never ran, exactly mirroring how a real CSRF rejection in Spring Security's `FilterChainProxy` prevents every subsequent filter (including the eventual authorization checks and the target controller method) from ever executing.

## 6. Walkthrough

Trace `chain.process(request)` in Level 3 with `hasCsrfToken = false`.

1. The `for` loop begins with `i = 0` — `filters.get(0).apply(request)` runs `filter 0`'s lambda, printing its label and returning `request.hasValidSession()`, which is `true` — `passed` is `true`, so the `if (!passed)` check is `false`, and the loop continues.
2. `i = 1` — `filters.get(1).apply(request)` runs `filter 1`'s lambda, printing its label and returning `request.hasCsrfToken()`, which is `false` this time — `passed` is `false`.
3. `if (!passed)` is now `true`, so the method prints the rejection message specifically identifying `"filter index 1"` as where the chain stopped, and immediately `return false` — this exits the loop and the method entirely, without the loop's `i` ever reaching `2`.
4. Because `filters.get(2)` (the "Authorization" filter, deliberately labeled to note it should never print) is never called, its `println` never executes — the printed output correctly shows only `filter 0` and `filter 1`'s labels, with no trace of `filter 2` at all.
5. `container.doFilter(request)` returns `false`, matching what `process` returned, and `simulateControllerIfAllowed(false)` correctly reports the controller method never ran — this precisely mirrors a real Spring Security `CsrfFilter` rejection: the request never proceeds past that specific filter, and every filter (and the eventual controller) positioned after it in the chain simply never executes for this particular request.

```
process(request with hasCsrfToken=false):
  i=0: filter 0 (SecurityContext) -> hasValidSession=true -> PASS, continue
  i=1: filter 1 (CSRF) -> hasCsrfToken=false -> FAIL
       -> REJECTED at filter index 1, chain STOPS
       -> filter 2 (Authorization) NEVER CALLED, never even printed
  process() returns false
  controller method: NEVER RUNS
```

## 7. Gotchas & takeaways

> **Gotcha:** the specific *order* filters run in matters enormously and is not arbitrary — a CSRF check running before session/authentication establishment, for instance, would be checking a token against a security context that hasn't even been populated yet. Spring Security carefully defines a specific, documented default ordering for its built-in filters, and custom filters added via `HttpSecurity`'s configuration API must be inserted at a deliberate position relative to that existing order (using methods like `addFilterBefore`/`addFilterAfter`), not appended arbitrarily — the next card on `SecurityFilterChain` and the one after on filter ordering cover this in more depth.

- `DelegatingFilterProxy` is the single, thin bridge between the servlet container's own filter registration mechanism and Spring's dependency-injection-managed bean configuration — it exists purely to avoid needing to register Spring Security's many individual filters directly and separately with the container.
- `FilterChainProxy` is the actual Spring-managed bean holding Spring Security's real, ordered list of filters — this is where the meaningful security logic and configuration genuinely live, and it's fully configurable through ordinary Spring `@Bean` methods and the `HttpSecurity` DSL.
- Any single filter in the chain rejecting a request immediately stops that request from proceeding any further — neither the remaining filters in the chain nor the eventual target controller method ever execute for a rejected request, which is what makes the filter chain an effective, fail-closed security enforcement mechanism.
- Spring Boot's auto-configuration handles wiring up `DelegatingFilterProxy` and `FilterChainProxy` automatically for a typical application — most day-to-day Spring Security configuration work happens entirely through `HttpSecurity`/`SecurityFilterChain` beans (the next card), without ever needing to interact with `DelegatingFilterProxy` directly.
