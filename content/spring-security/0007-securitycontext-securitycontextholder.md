---
card: spring-security
gi: 7
slug: securitycontext-securitycontextholder
title: "SecurityContext & SecurityContextHolder"
---

## 1. What it is

`SecurityContext` is the small container object holding the current request's `Authentication` (the established identity), and `SecurityContextHolder` is the static access point application code uses to read it — `SecurityContextHolder.getContext().getAuthentication()` retrieves the currently authenticated user from anywhere in the call stack, without that identity needing to be explicitly threaded through every method signature as a parameter, because `SecurityContextHolder` stores it (by default) in a `ThreadLocal`, making it implicitly available to any code running on the same thread that's handling the current request.

```java
Authentication auth = SecurityContextHolder.getContext().getAuthentication();
String currentUsername = auth.getName();

// far more commonly, injected directly where needed:
@GetMapping("/me")
String whoAmI(Authentication authentication) {
    return authentication.getName(); // Spring resolves this parameter FROM the SecurityContext automatically
}
```

## 2. Why & when

Once the authentication filter (from the previous card) establishes a caller's identity, that identity needs to be accessible from application code — a service method deep in the call stack, a `@PreAuthorize` expression, an audit-logging component — without every single method along the way needing an explicit `Authentication` parameter threaded through it manually. `SecurityContextHolder` solves this the same way many "ambient context" problems are solved: a well-known, globally-accessible holder (backed by `ThreadLocal` in the servlet stack, as the earlier servlet-vs-reactive card established) that any code running within the current request's processing can query, at any depth in the call stack, without the calling code needing to have been handed the identity explicitly.

Reach for `SecurityContextHolder` (or, more commonly, its more idiomatic alternatives) when:

- Needing the currently authenticated user's identity somewhere in application code that isn't a controller method directly — a service class, a custom `AuditListener`, a scheduled task triggered within a request's processing.
- In a controller method specifically, prefer injecting `Authentication` (or a custom `@AuthenticationPrincipal`-annotated parameter) directly as a method argument over calling `SecurityContextHolder` manually — Spring resolves this injection automatically from the same underlying context, and it's more testable (a test can simply pass a mock `Authentication` as an argument) than code that reaches into a static holder.
- Understanding how `@PreAuthorize`/`@PostAuthorize` method security annotations (a later card) actually determine "the current user" — they read from exactly this same `SecurityContextHolder`-backed context underneath their more declarative syntax.

## 3. Core concept

```
 authentication filter succeeds:
   SecurityContextHolder.getContext().setAuthentication(authenticatedUserObject)
        |
        v (stored, typically, in a ThreadLocal -- available to ANY code on the SAME thread)
        |
   ANY code running on this thread, at ANY depth in the call stack, can call:
     SecurityContextHolder.getContext().getAuthentication()
   and get back the SAME Authentication object, with NO explicit parameter passing required

   controller method  -->  service method  -->  repository method  -->  audit logger
        (all can independently query SecurityContextHolder and get the SAME identity)
```

The "ambient availability" is the whole point — no method signature in the call chain needs to explicitly carry the identity as a parameter for deeply-nested code to still access it correctly.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An authenticated identity is stored once in the SecurityContextHolder and multiple unrelated pieces of code at different depths of the call stack can each independently query it and retrieve the same identity without it being passed as an explicit parameter">
  <rect x="240" y="20" width="160" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">SecurityContextHolder</text>

  <rect x="20" y="110" width="150" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="95" y="134" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">controller method</text>

  <rect x="245" y="110" width="150" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="320" y="134" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">service method</text>

  <rect x="470" y="110" width="150" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="545" y="134" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">audit logger</text>

  <defs><marker id="a7" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="95" y1="110" x2="280" y2="60" stroke="#8b949e" stroke-width="1.1" stroke-dasharray="3,3" marker-end="url(#a7)"/>
  <line x1="320" y1="110" x2="320" y2="60" stroke="#8b949e" stroke-width="1.1" stroke-dasharray="3,3" marker-end="url(#a7)"/>
  <line x1="545" y1="110" x2="360" y2="60" stroke="#8b949e" stroke-width="1.1" stroke-dasharray="3,3" marker-end="url(#a7)"/>
</svg>

Three unrelated pieces of code, each independently querying the same central holder, none of them requiring the identity to have been passed to them explicitly.

## 5. Runnable example

The scenario: model `ThreadLocal`-backed context storage and multiple independent "components" (a controller, a service, an audit logger) each reading the same identity without any explicit parameter passing between them. Start with basic set/get, then add multiple independent readers accessing the same stored identity, then add proper context clearing after a request completes, demonstrating why cleanup matters to avoid identity leaking across unrelated requests.

### Level 1 — Basic

Basic set/get through a `ThreadLocal`-backed holder.

```java
public class SecurityContextHolderLevel1 {
    static ThreadLocal<String> securityContext = new ThreadLocal<>();

    static class SecurityContextHolder {
        static void setAuthentication(String username) { securityContext.set(username); }
        static String getAuthentication() { return securityContext.get(); }
    }

    public static void main(String[] args) {
        SecurityContextHolder.setAuthentication("alice"); // set ONCE, by the authentication filter

        String currentUser = SecurityContextHolder.getAuthentication(); // read from ANYWHERE, no parameter needed
        System.out.println("current user: " + currentUser);
    }
}
```

How to run: `java SecurityContextHolderLevel1.java`

`setAuthentication` and `getAuthentication` operate on the same static `ThreadLocal` — this is the minimal mechanism `SecurityContextHolder` provides, letting identity be set once and read back from anywhere without explicit passing.

### Level 2 — Intermediate

Add multiple independent "components" — a controller, a service, and an audit logger — each reading the same identity without it being passed between them as a parameter.

```java
public class SecurityContextHolderLevel2 {
    static ThreadLocal<String> securityContext = new ThreadLocal<>();

    static class SecurityContextHolder {
        static void setAuthentication(String username) { securityContext.set(username); }
        static String getAuthentication() { return securityContext.get(); }
    }

    // NONE of these three methods receive the username as a parameter -- each queries the holder independently
    static void controllerMethod() {
        System.out.println("controller: current user is " + SecurityContextHolder.getAuthentication());
        serviceMethod(); // called with NO identity parameter
    }

    static void serviceMethod() {
        System.out.println("service: current user is " + SecurityContextHolder.getAuthentication());
        auditLog();
    }

    static void auditLog() {
        System.out.println("audit logger: recording action performed by " + SecurityContextHolder.getAuthentication());
    }

    public static void main(String[] args) {
        SecurityContextHolder.setAuthentication("alice"); // set ONCE, at the "authentication filter" stage
        controllerMethod(); // triggers the WHOLE call chain, none of which needed alice passed explicitly
    }
}
```

How to run: `java SecurityContextHolderLevel2.java`

All three methods print `"alice"`, despite none of them receiving a username parameter and none of them calling each other with any identity information — each independently queries `SecurityContextHolder`, and because all three run on the same thread within the same call chain, they all see the same, single value that was set once at the top.

### Level 3 — Advanced

Add proper context clearing after a request completes, demonstrating why cleanup matters — without it, a stale identity from one request could incorrectly leak into a subsequent, unrelated request handled by the same (reused) thread.

```java
public class SecurityContextHolderLevel3 {
    static ThreadLocal<String> securityContext = new ThreadLocal<>();

    static class SecurityContextHolder {
        static void setAuthentication(String username) { securityContext.set(username); }
        static String getAuthentication() { return securityContext.get(); }
        static void clearContext() { securityContext.remove(); } // ESSENTIAL cleanup after each request
    }

    static void handleRequest(String username, boolean clearAfterward) {
        SecurityContextHolder.setAuthentication(username);
        System.out.println("processing request for: " + SecurityContextHolder.getAuthentication());

        if (clearAfterward) {
            SecurityContextHolder.clearContext(); // models Spring Security's own cleanup filter running at request end
        }
        // WITHOUT clearing, this thread's ThreadLocal STILL holds the previous request's identity
    }

    public static void main(String[] args) {
        System.out.println("-- request 1: alice, WITHOUT proper cleanup --");
        handleRequest("alice", false);

        System.out.println("-- request 2: bob, on the SAME (reused) thread, expecting a FRESH context --");
        // if the pool/framework reuses this thread WITHOUT clearing, bob's request could see STALE data
        // before setAuthentication("bob") even runs:
        System.out.println("  stale leftover BEFORE bob authenticates: " + SecurityContextHolder.getAuthentication());
        handleRequest("bob", true); // THIS time, properly cleared afterward

        System.out.println("-- request 3: on the SAME thread again, AFTER proper cleanup --");
        System.out.println("  context correctly EMPTY before any new authentication: " + SecurityContextHolder.getAuthentication());
    }
}
```

How to run: `java SecurityContextHolderLevel3.java`

Before request 2's `handleRequest("bob", true)` call even runs, `SecurityContextHolder.getAuthentication()` still returns `"alice"` — the stale leftover from request 1, which was never cleared; after request 2 properly clears its context, request 3's check correctly shows `null` (empty) — this demonstrates precisely why Spring Security's own filter chain always includes a cleanup step (typically as part of `SecurityContextHolderFilter`'s own request-completion logic) ensuring the `ThreadLocal` is cleared at the end of every request, preventing one request's identity from ever leaking into a subsequent, unrelated request that happens to reuse the same underlying thread (which is common and expected in a thread-pooled servlet container).

## 6. Walkthrough

Trace the stale-context leak in Level 3.

1. `handleRequest("alice", false)` runs — `SecurityContextHolder.setAuthentication("alice")` sets the `ThreadLocal` to `"alice"`, and because `clearAfterward` is `false`, `clearContext()` is never called before this method returns — the `ThreadLocal` still holds `"alice"` after this call completes.
2. `main` then prints `SecurityContextHolder.getAuthentication()` directly, *before* `handleRequest("bob", true)` has even been called — because nothing cleared the context after request 1, this read still returns `"alice"`, the leftover value from the *previous*, entirely unrelated request.
3. `handleRequest("bob", true)` then runs — `setAuthentication("bob")` overwrites the `ThreadLocal` with `"bob"`, the request is processed correctly with the right identity this time, and because `clearAfterward` is `true`, `clearContext()` (which calls `securityContext.remove()`) runs at the end, properly resetting the `ThreadLocal` to empty.
4. `main`'s final check, after this properly-cleaned-up request, reads `SecurityContextHolder.getAuthentication()` again — this time it correctly returns `null`, confirming the context was properly reset and no stale identity remains for whatever request (if any) runs next on this same thread.
5. In a real servlet container, threads are pooled and reused across many different requests over time — if Spring Security's own filter chain didn't reliably clear the `SecurityContextHolder`'s `ThreadLocal` at the end of every single request, a later request on a reused thread could incorrectly, silently see a *previous, unrelated* caller's identity, which would be a serious security defect; this is precisely why that cleanup step is a non-negotiable, built-in part of the filter chain's own design.

```
request 1 (alice, NOT cleared):
  setAuthentication("alice") -> ThreadLocal = "alice"
  (no clearContext() call)
  ThreadLocal STILL = "alice" after handleRequest returns

BEFORE request 2 processes anything: getAuthentication() -> "alice"  <- STALE LEAK from request 1!

request 2 (bob, PROPERLY cleared):
  setAuthentication("bob") -> ThreadLocal = "bob"
  clearContext() -> ThreadLocal = null

request 3 check: getAuthentication() -> null   <- correctly EMPTY, no leak
```

## 7. Gotchas & takeaways

> **Gotcha:** manually spawning a new thread (or submitting work to a thread pool/`ExecutorService`) from within request-handling code does *not* automatically carry the current `SecurityContextHolder` value to that new thread — since it's `ThreadLocal`-backed, a new thread starts with an empty context, exactly as demonstrated in the earlier servlet-vs-reactive card's Level 2 example; explicitly capturing and propagating the `SecurityContext` to any manually-spawned thread (via `DelegatingSecurityContextRunnable`/`DelegatingSecurityContextExecutor`, Spring Security utilities built exactly for this purpose) is necessary whenever asynchronous work needs to see the same authenticated identity as the request that spawned it.

- `SecurityContextHolder` provides ambient, globally-accessible storage for the current request's established `Authentication`, letting any code running on the same thread query it without the identity needing to be explicitly passed as a parameter through every method in the call chain.
- This mechanism is `ThreadLocal`-backed by default in the servlet stack, which works correctly precisely because a servlet request's processing stays on one thread — exactly the assumption the earlier servlet-vs-reactive card established as the reason the reactive stack needs a fundamentally different context-propagation mechanism instead.
- Proper context cleanup at the end of every request (clearing the `ThreadLocal`) is essential and non-negotiable in a thread-pooled environment — without it, one request's identity can leak into a subsequent, unrelated request that happens to reuse the same thread, a serious security concern Spring Security's own filter chain reliably handles.
- In controller methods specifically, injecting `Authentication` (or `@AuthenticationPrincipal`) as a method parameter is generally preferred over calling `SecurityContextHolder` directly — it's more explicit, more testable, and Spring resolves it from exactly the same underlying context automatically.
