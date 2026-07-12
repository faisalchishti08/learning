---
card: spring-security
gi: 116
slug: reactivesecuritycontextholder
title: "ReactiveSecurityContextHolder"
---

## 1. What it is

`ReactiveSecurityContextHolder` is the reactive-stack replacement for the `SecurityContextHolder` every earlier card in this course relied on — and it has to work completely differently, because `SecurityContextHolder`'s default strategy stores the current `SecurityContext` in a `ThreadLocal`, an assumption that silently breaks the moment a single logical request's processing hops across multiple threads, which is routine in WebFlux's reactive execution model. `ReactiveSecurityContextHolder.getContext()` returns a `Mono<SecurityContext>` sourced from **Reactor Context** — metadata that travels *with* the logical chain of reactive operators as data flows through them, regardless of which physical thread ends up executing any given step.

```java
@GetMapping("/whoami")
public Mono<String> whoami() {
    return ReactiveSecurityContextHolder.getContext()
            .map(SecurityContext::getAuthentication)
            .map(Authentication::getName);
}
```

## 2. Why & when

A `ThreadLocal` associates a value with *one specific thread* — reading it later only works if you're still executing on that same thread. Reactive pipelines routinely violate this: an operator might run on the event-loop thread that first received the request, hop onto a worker thread for a blocking-adjacent operation wrapped in `subscribeOn`, then resume on yet another thread when an upstream `Mono` completes — a `ThreadLocal`-based `SecurityContextHolder.getContext()` called partway through that chain would find nothing, or worse, find whatever unrelated context happens to be set on *that* particular thread at that moment, since reactive schedulers reuse threads across many concurrent, unrelated requests. Reactor Context solves this by attaching the security context as data carried alongside the reactive subscription itself, propagated automatically as operators compose, regardless of thread hops.

Reach for `ReactiveSecurityContextHolder` when:

- Reading the current authenticated principal inside a WebFlux controller or reactive service method — this is the direct reactive-stack replacement for `SecurityContextHolder.getContext().getAuthentication()`.
- Writing a custom `ReactiveAuthenticationManager` or authorization check that needs to read (or, less commonly, contribute to) the current security context as part of a `Mono`/`Flux` chain.
- Debugging why an authenticated principal appears to be "missing" partway through a reactive chain — this almost always traces to the context read happening outside the reactive chain entirely (e.g., inside a plain, non-reactive helper method that isn't composed via `Mono`/`Flux` operators), rather than a genuine authentication failure.
- Understanding why `SecurityContextHolder`-based code, copied directly from a Servlet-stack application, silently returns nothing meaningful when ported naively into a WebFlux application — the two context-propagation mechanisms are not interchangeable.

## 3. Core concept

```
Servlet stack:
    SecurityContextHolder.getContext()        -- reads from a ThreadLocal, valid on THIS thread only
    set once per request, thread never changes mid-request -- ThreadLocal works fine

Reactive stack:
    ReactiveSecurityContextHolder.getContext() -- returns Mono<SecurityContext>
    the context is stored in the REACTOR CONTEXT, which:
        - is IMMUTABLE (writing produces a NEW context, doesn't mutate the existing one)
        - PROPAGATES DOWNSTREAM automatically through subscribe/operator chains
        - survives thread hops, because it's carried as metadata on the SUBSCRIPTION, not the thread

Correct usage -- READ the context AS PART OF the reactive chain:
    ReactiveSecurityContextHolder.getContext()
        .map(SecurityContext::getAuthentication)
        .flatMap(auth -> doSomethingWith(auth))   <-- composed, never blocks, survives thread hops

INCORRECT usage -- trying to read it OUTSIDE the chain (e.g. calling .block() to "just get the value")
    defeats the entire non-blocking model AND may simply find no context at all,
    since blocking pulls execution out of the reactive scheduling context that carries it
```

The context is written once, automatically, by the reactive security filter chain at the start of request processing — application code almost always only ever *reads* it, via exactly this `Mono`-returning method.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a reactive chain hopping across three different threads while the security context stored in reactor context travels alongside the subscription itself remaining readable at every step regardless of which thread executes it">
  <rect x="20" y="30" width="600" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="50" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Thread A -&gt; Thread B -&gt; Thread C  (the SAME logical request, different physical threads)</text>
  <text x="320" y="70" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">a ThreadLocal set on Thread A is INVISIBLE on Thread B and C</text>

  <rect x="20" y="110" width="600" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="130" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Reactor Context (carried WITH the subscription, not any one thread)</text>

  <rect x="40" y="140" width="160" height="40" rx="6" fill="#161b22" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="120" y="164" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Thread A: read context OK</text>

  <rect x="250" y="140" width="160" height="40" rx="6" fill="#161b22" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="330" y="164" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Thread B: read context OK</text>

  <rect x="460" y="140" width="160" height="40" rx="6" fill="#161b22" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="540" y="164" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Thread C: read context OK</text>

  <line x1="200" y1="160" x2="245" y2="160" stroke="#3fb950" stroke-width="1.6" marker-end="url(#rc116)"/>
  <line x1="410" y1="160" x2="455" y2="160" stroke="#3fb950" stroke-width="1.6" marker-end="url(#rc116)"/>

  <defs><marker id="rc116" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Reactor Context travels with the logical subscription across thread hops; a `ThreadLocal` does not.

## 5. Runnable example

The scenario: model both context-propagation strategies side by side — a naive `ThreadLocal` losing its value across a simulated thread hop, and a `Context`-style carrier (an explicit map passed through the chain) preserving it — growing into a small "read the current user" composed operation, then into showing why calling `.get()`/blocking prematurely can defeat the whole mechanism.

### Level 1 — Basic

A `ThreadLocal` set on one thread is invisible from another; a value carried explicitly through the call survives.

```java
import java.util.concurrent.*;

public class ReactiveContextLevel1 {
    static final ThreadLocal<String> threadLocalContext = new ThreadLocal<>();

    public static void main(String[] args) throws Exception {
        threadLocalContext.set("alice"); // set on the MAIN thread
        System.out.println("read on main thread: " + threadLocalContext.get());

        ExecutorService otherThread = Executors.newSingleThreadExecutor();
        String readOnOtherThread = otherThread.submit(() -> threadLocalContext.get()).get();
        System.out.println("read on a DIFFERENT thread: " + readOnOtherThread);

        // in contrast, an EXPLICIT value passed as a parameter survives the thread hop just fine
        String explicitlyCarried = otherThread.submit(() -> "value explicitly passed: alice").get();
        System.out.println(explicitlyCarried);

        otherThread.shutdown();
    }
}
```

**How to run:** save as `ReactiveContextLevel1.java`, run `java ReactiveContextLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
read on main thread: alice
read on a DIFFERENT thread: null
value explicitly passed: alice
```

The `ThreadLocal` value set on `main` is genuinely invisible from the other thread's point of view — this is precisely the failure mode a `SecurityContextHolder`-based read would hit inside a reactive chain that hops threads; Reactor Context avoids it by never relying on thread identity at all, carrying the value explicitly (conceptually, as shown in the third line) alongside the logical chain instead.

### Level 2 — Intermediate

Model a minimal `Context`-carrying chain (a simplified stand-in for Reactor Context) that survives a simulated thread hop, and read the "current user" as part of a composed operation.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;

public class ReactiveContextLevel2 {
    // a MINIMAL stand-in for reactor.util.context.Context -- immutable, explicitly carried
    record SimpleContext(Map<String, Object> values) {
        static SimpleContext of(String key, Object value) { return new SimpleContext(Map.of(key, value)); }
        Object get(String key) { return values.get(key); }
    }

    static class SecurityContext {
        final String principalName;
        SecurityContext(String principalName) { this.principalName = principalName; }
    }

    // mirrors ReactiveSecurityContextHolder.getContext() -- reads from the EXPLICITLY carried context
    static CompletableFuture<SecurityContext> getSecurityContext(SimpleContext ctx) {
        return CompletableFuture.completedFuture((SecurityContext) ctx.get("securityContext"));
    }

    static CompletableFuture<String> whoAmI(SimpleContext ctx, ExecutorService differentThreadPool) {
        // the ACTUAL work happens on a DIFFERENT thread, but the context was carried in as a parameter,
        // not looked up via ThreadLocal -- so it survives the hop
        return CompletableFuture.supplyAsync(() -> {
            SecurityContext secCtx = (SecurityContext) ctx.get("securityContext");
            return secCtx.principalName;
        }, differentThreadPool);
    }

    public static void main(String[] args) throws Exception {
        SimpleContext ctx = SimpleContext.of("securityContext", new SecurityContext("alice"));

        ExecutorService otherThreadPool = Executors.newSingleThreadExecutor();
        String principalName = whoAmI(ctx, otherThreadPool).get();
        System.out.println("principal read on a DIFFERENT thread, via explicitly-carried context: " + principalName);

        otherThreadPool.shutdown();
    }
}
```

**How to run:** save as `ReactiveContextLevel2.java`, run `java ReactiveContextLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
principal read on a DIFFERENT thread, via explicitly-carried context: alice
```

What changed: `SimpleContext` is passed explicitly as a parameter into `whoAmI`, which runs its actual work on a genuinely different thread pool — the security context still resolves correctly because it was never dependent on thread identity in the first place, exactly how `ReactiveSecurityContextHolder.getContext()` composed into a `Mono` chain resolves correctly regardless of which thread Reactor's scheduler happens to run each step on.

### Level 3 — Advanced

Show the anti-pattern directly: attempting to "just get the value" by blocking/escaping the reactive chain, versus correctly composing the read as part of the chain — and a composed authorization check that depends on the context.

```java
import java.util.*;
import java.util.concurrent.*;

public class ReactiveContextLevel3 {
    record SimpleContext(Map<String, Object> values) {
        static SimpleContext of(String key, Object value) { return new SimpleContext(Map.of(key, value)); }
    }
    static class SecurityContext {
        final String principalName;
        final Set<String> authorities;
        SecurityContext(String principalName, Set<String> authorities) {
            this.principalName = principalName;
            this.authorities = authorities;
        }
    }
    static class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String message) { super(message); }
    }

    // CORRECT: composed as part of the chain, the context is passed through explicitly at every step
    static CompletableFuture<String> correctlyComposedCheck(SimpleContext ctx, String requiredAuthority,
                                                             ExecutorService pool) {
        return CompletableFuture.supplyAsync(() -> {
            SecurityContext secCtx = (SecurityContext) ctx.values().get("securityContext");
            if (!secCtx.authorities.contains(requiredAuthority)) {
                throw new AccessDeniedException(secCtx.principalName + " lacks " + requiredAuthority);
            }
            return secCtx.principalName;
        }, pool).thenCompose(principalName ->
                CompletableFuture.supplyAsync(() -> "authorized: " + principalName, pool) // ANOTHER thread hop, still fine
        );
    }

    public static void main(String[] args) throws Exception {
        SimpleContext ctx = SimpleContext.of("securityContext", new SecurityContext("alice", Set.of("ROLE_ADMIN")));
        ExecutorService pool = Executors.newFixedThreadPool(3); // multiple threads -- hops are LIKELY

        String result = correctlyComposedCheck(ctx, "ROLE_ADMIN", pool).get();
        System.out.println(result);

        SimpleContext bobCtx = SimpleContext.of("securityContext", new SecurityContext("bob", Set.of("ROLE_USER")));
        try {
            correctlyComposedCheck(bobCtx, "ROLE_ADMIN", pool).get();
        } catch (ExecutionException e) {
            System.out.println("denied: " + e.getCause().getMessage());
        }

        pool.shutdown();
    }
}
```

**How to run:** save as `ReactiveContextLevel3.java`, run `java ReactiveContextLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
authorized: alice
denied: bob lacks ROLE_ADMIN
```

What changed: `correctlyComposedCheck` chains a `thenCompose` after the initial check, meaning the computation almost certainly continues on a *different* thread from the pool for its second step — yet the result is still correct, because the security context was captured and used within each step's own closure rather than depending on any thread-local state persisting between them. This is precisely the discipline `ReactiveSecurityContextHolder.getContext().flatMap(...)` chains follow: read the context once, as part of the reactive pipeline, and thread its value through subsequent steps via the chain's own composition rather than any ambient, thread-bound storage.

## 6. Walkthrough

Trace alice's authorized check from Level 3 end to end, mapping each step back to the real `ReactiveSecurityContextHolder` API.

**Step 1 — a request arrives at a WebFlux endpoint**, already authenticated by the reactive security filter chain (the reactive counterpart to card 0100's `BearerTokenAuthenticationFilter`, for a JWT-secured reactive resource server, for instance). The filter chain writes the resulting `SecurityContext` into Reactor Context — this corresponds to `ctx` already containing `new SecurityContext("alice", {"ROLE_ADMIN"})` by the time `correctlyComposedCheck` is called.

**Step 2 — the controller method's reactive chain begins.** In a real application:
```java
@GetMapping("/admin/dashboard")
public Mono<String> adminDashboard() {
    return ReactiveSecurityContextHolder.getContext()
            .map(SecurityContext::getAuthentication)
            .flatMap(auth -> checkAuthority(auth, "ROLE_ADMIN"));
}
```
`ReactiveSecurityContextHolder.getContext()` resolves the `Mono<SecurityContext>` from Reactor Context — corresponding to `ctx.values().get("securityContext")` in the simulated code.

**Step 3 — the authority check runs**, corresponding to `CompletableFuture.supplyAsync(...)`'s body: `secCtx.authorities.contains("ROLE_ADMIN")` is `true` for alice, so no exception is thrown, and `"alice"` is returned as this step's result — this computation might run on any thread from the pool; it doesn't matter which, since the context was read fresh from `ctx`, not from any thread-local state.

**Step 4 — a second, dependent step composes onto the first.** `.thenCompose(principalName -> CompletableFuture.supplyAsync(() -> "authorized: " + principalName, pool))` — this models a further reactive operator (perhaps fetching dashboard data specific to this admin user) that runs *after* the authority check, quite possibly on yet another thread from the pool.

**Step 5 — the final result.** `"authorized: alice"` — resolved correctly, having potentially hopped across two or three different physical threads throughout the chain, with no step ever needing to rely on thread-local storage to know who the current principal was.

```
Reactor Context: {securityContext: SecurityContext(alice, {ROLE_ADMIN})}
      |
      v  (carried explicitly, NOT via ThreadLocal)
step 1 (thread X): read context -> authority check passes -> "alice"
      |
      v  (thenCompose -- may hop to thread Y)
step 2 (thread Y): "authorized: alice"
```

## 7. Gotchas & takeaways

> **Gotcha:** calling `.block()` on a `Mono` obtained from `ReactiveSecurityContextHolder.getContext()` (to "just get the value synchronously") is both an anti-pattern (it defeats the entire non-blocking model this stack is built around) and can genuinely fail — blocking inside certain reactive execution contexts (particularly within the request-handling chain itself, on an event-loop thread) throws an exception specifically because it would risk stalling that thread. Always compose the read as part of the reactive chain via `map`/`flatMap`, never as a synchronous escape hatch.

- `ReactiveSecurityContextHolder` replaces `SecurityContextHolder` for WebFlux applications because `ThreadLocal`-based storage does not survive the thread hops routine in reactive execution.
- The security context is carried via Reactor Context — immutable, propagated automatically alongside the logical reactive chain, and readable correctly regardless of which physical thread executes any given step.
- Application code should read the context by composing `ReactiveSecurityContextHolder.getContext()` into a `map`/`flatMap` chain, never by blocking to extract the value synchronously.
- The security filter chain writes the context once, automatically, at the start of reactive request processing — application code almost always only reads it, mirroring the read-only relationship most controller code has with `SecurityContextHolder` in the Servlet stack.
- Code ported naively from the Servlet stack (calling `SecurityContextHolder.getContext()` directly inside WebFlux code) compiles and may even appear to work under light, single-threaded testing, but silently returns stale, wrong, or empty context under real reactive scheduling — this class of bug is exactly why understanding the underlying mechanism, not just the API surface, matters here.
