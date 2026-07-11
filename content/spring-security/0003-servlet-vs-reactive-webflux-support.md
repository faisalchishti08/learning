---
card: spring-security
gi: 3
slug: servlet-vs-reactive-webflux-support
title: "Servlet vs reactive (WebFlux) support"
---

## 1. What it is

Spring Security ships two parallel, largely mirror-image sets of abstractions — a servlet-based stack (`SecurityFilterChain`, `HttpSecurity`, backed by the Servlet API's blocking `Filter` chain) for Spring MVC applications, and a reactive stack (`SecurityWebFilterChain`, `ServerHttpSecurity`, backed by Project Reactor's non-blocking `WebFilter` chain) for Spring WebFlux applications — with each stack's configuration DSL deliberately similar in shape to the other, but backed by fundamentally different underlying execution models (blocking thread-per-request versus non-blocking event-loop-based).

```java
// SERVLET (Spring MVC) -- blocking, one thread per request
@Bean
SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http.authorizeHttpRequests(a -> a.requestMatchers("/admin/**").hasRole("ADMIN"));
    return http.build();
}
```

```java
// REACTIVE (Spring WebFlux) -- non-blocking, event-loop based
@Bean
SecurityWebFilterChain springSecurityFilterChain(ServerHttpSecurity http) {
    http.authorizeExchange(a -> a.pathMatchers("/admin/**").hasRole("ADMIN"));
    return http.build();
}
```

## 2. Why & when

Spring MVC and Spring WebFlux represent two fundamentally different concurrency models for handling HTTP requests — MVC's Servlet-based, blocking, one-thread-per-request model, and WebFlux's non-blocking, event-loop-based reactive model — and security enforcement needs to integrate correctly with whichever model an application actually uses, since the two have genuinely different threading and context-propagation characteristics that affect how something like "the currently authenticated user" is even tracked during request processing. Spring Security provides a dedicated stack for each rather than forcing one model onto both, because naively adapting servlet-based security's assumptions (a security context tied to the current thread, which stays fixed for a blocking request's duration) onto WebFlux's model (where a single logical request's processing may hop across multiple threads as it moves through a reactive pipeline) would be actively incorrect, not merely awkward.

Reach for the servlet-based `SecurityFilterChain`/`HttpSecurity` stack when:

- Building a traditional Spring MVC application — this remains the default, more common Spring Security configuration style, and the one most existing documentation, tutorials, and Stack Overflow answers assume unless stated otherwise.

Reach for the reactive `SecurityWebFilterChain`/`ServerHttpSecurity` stack when:

- Building a Spring WebFlux application — using the servlet-based configuration classes in a WebFlux application simply won't work correctly, since WebFlux doesn't run on the Servlet API at all; the reactive-specific configuration classes are required.
- The application needs to scale to a high number of concurrent connections with comparatively few threads (WebFlux's core value proposition) and security enforcement needs to participate correctly in that non-blocking execution model, including how the authenticated user's identity propagates through a reactive processing chain (a later card in this series covers `ReactiveSecurityContextHolder` specifically).

## 3. Core concept

```
 SERVLET stack:                              REACTIVE stack:
   HttpSecurity                                 ServerHttpSecurity
   SecurityFilterChain                          SecurityWebFilterChain
   Filter (javax.servlet / jakarta.servlet)      WebFilter (org.springframework.web.server)
   SecurityContextHolder (ThreadLocal-based)     ReactiveSecurityContextHolder (Reactor Context-based)
   blocking, one thread PER REQUEST for its      non-blocking, ONE request's processing may run across
   ENTIRE duration                                MULTIPLE threads as it moves through the reactive pipeline

 SAME conceptual model (authenticate, then authorize) -- DIFFERENT underlying mechanics,
 because a ThreadLocal-based SecurityContext CANNOT correctly track identity across
 a request that hops threads, which is NORMAL in a reactive pipeline
```

The reactive stack exists specifically because the servlet stack's `ThreadLocal`-based security context tracking mechanism is fundamentally incompatible with how a WebFlux request's processing actually executes.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A servlet request stays on one thread for its whole duration letting a thread local security context work correctly while a reactive request may hop across several different threads as it moves through the pipeline requiring a different context propagation mechanism entirely">
  <text x="20" y="30" fill="#6db33f" font-size="8.5" font-family="sans-serif">SERVLET: one request, ONE thread, whole duration</text>
  <rect x="20" y="40" width="580" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="310" y="59" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">thread-42 handles the ENTIRE request -- ThreadLocal SecurityContext works fine</text>

  <text x="20" y="100" fill="#79c0ff" font-size="8.5" font-family="sans-serif">REACTIVE: one request, MULTIPLE threads across its lifecycle</text>
  <rect x="20" y="110" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="110" y="129" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">thread-A (stage 1)</text>
  <rect x="230" y="110" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="320" y="129" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">thread-B (stage 2)</text>
  <rect x="440" y="110" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="530" y="129" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">thread-C (stage 3)</text>
  <text x="320" y="160" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">a ThreadLocal would LOSE the security context between stages -- Reactor Context propagates it correctly instead</text>
</svg>

The servlet model's single-thread assumption simply doesn't hold for a reactive pipeline — a fundamentally different context-propagation mechanism is required, not merely a different API surface.

## 5. Runnable example

The scenario: model both context-tracking mechanisms directly — a `ThreadLocal`-style context that works correctly for a single-threaded request but breaks across a thread hop, versus an explicitly-passed context that survives a hop correctly. Start with the servlet-style `ThreadLocal` approach working fine within one thread, then show it failing across a simulated thread hop, then add the reactive-style explicit-context-passing approach that correctly survives the hop.

### Level 1 — Basic

A `ThreadLocal`-based security context, working correctly within a single thread — the servlet model's approach.

```java
public class ServletVsReactiveLevel1 {
    static ThreadLocal<String> securityContext = new ThreadLocal<>();

    static void authenticate(String username) {
        securityContext.set(username);
    }

    static void businessLogic() {
        String currentUser = securityContext.get(); // reads from the SAME thread's ThreadLocal
        System.out.println("business logic sees current user: " + currentUser);
    }

    public static void main(String[] args) {
        authenticate("alice");
        businessLogic(); // runs on the SAME thread as authenticate() -- works correctly
    }
}
```

How to run: `java ServletVsReactiveLevel1.java`

`businessLogic` correctly reads `"alice"` from `securityContext`, because both `authenticate` and `businessLogic` ran on the same thread — this is exactly how servlet-based Spring Security's `SecurityContextHolder` works for a typical blocking request that never hops threads.

### Level 2 — Intermediate

Show the `ThreadLocal` approach breaking when the same logical "request" is processed across a thread hop, mirroring what happens if servlet-style context tracking were naively applied to a reactive pipeline.

```java
public class ServletVsReactiveLevel2 {
    static ThreadLocal<String> securityContext = new ThreadLocal<>();

    static void authenticate(String username) {
        securityContext.set(username);
    }

    static void businessLogic() {
        String currentUser = securityContext.get();
        System.out.println("business logic sees current user: " + currentUser); // will print null!
    }

    public static void main(String[] args) throws InterruptedException {
        authenticate("alice"); // runs on the MAIN thread

        // simulates a reactive pipeline hopping to a DIFFERENT thread for the next processing stage
        Thread differentThread = new Thread(ServletVsReactiveLevel2::businessLogic);
        differentThread.start();
        differentThread.join();
    }
}
```

How to run: `java ServletVsReactiveLevel2.java`

`businessLogic`, now running on `differentThread` rather than the main thread, sees `securityContext.get()` return `null` — the `ThreadLocal` value set on the main thread is completely invisible to any other thread, which is precisely the failure mode that would occur if servlet-based security's `ThreadLocal`-backed `SecurityContextHolder` were naively used in a reactive pipeline that genuinely hops threads between processing stages.

### Level 3 — Advanced

Add the reactive-style solution: an explicitly-passed context object (modeling Reactor's `Context`) that correctly survives the thread hop, because it's carried along with the data rather than relying on thread-local storage.

```java
public class ServletVsReactiveLevel3 {
    // models Reactor's Context -- an IMMUTABLE, explicitly-passed value, NOT thread-bound
    record ReactiveContext(String currentUser) {}

    static ReactiveContext authenticate(String username) {
        return new ReactiveContext(username); // returns the context EXPLICITLY, rather than storing it thread-locally
    }

    static void businessLogic(ReactiveContext context) {
        System.out.println("business logic sees current user: " + context.currentUser()); // correctly populated
    }

    public static void main(String[] args) throws InterruptedException {
        ReactiveContext context = authenticate("alice"); // runs on the MAIN thread

        // the SAME thread hop as Level 2 -- but this time the context is passed EXPLICITLY, not thread-locally
        Thread differentThread = new Thread(() -> businessLogic(context));
        differentThread.start();
        differentThread.join();
    }
}
```

How to run: `java ServletVsReactiveLevel3.java`

Even though `businessLogic` again runs on a completely different thread than `authenticate`, it correctly prints `"alice"`, because `context` was passed explicitly as a method parameter (captured by the lambda) rather than relying on any thread-local storage mechanism — this is the core structural difference `ReactiveSecurityContextHolder` (built on Reactor's `Context`) exploits: carrying the security context along with the reactive pipeline's own data flow, rather than depending on the executing thread's identity, which the reactive model makes no promises about staying constant across a single logical request.

## 6. Walkthrough

Trace the thread hop and context propagation in Level 3.

1. `authenticate("alice")` runs on the main thread, constructing and returning `new ReactiveContext("alice")` — this object is assigned to the local variable `context` on the main thread.
2. `new Thread(() -> businessLogic(context))` constructs a new `Thread` whose body is a lambda — critically, this lambda *captures* the `context` variable by value (a reference to the same `ReactiveContext` object), which Java allows for effectively-final local variables.
3. `differentThread.start()` begins executing the lambda on a genuinely different thread than the main thread — but because `context` was captured directly into the lambda's closure, the new thread has direct access to the exact same `ReactiveContext` object the main thread constructed, with no dependency on any thread-local storage mechanism at all.
4. Inside `businessLogic(context)`, running on `differentThread`, `context.currentUser()` returns `"alice"` — correctly, because `context` is simply a plain object reference passed as a normal method argument, and plain object references work identically regardless of which thread happens to be holding them.
5. `differentThread.join()` on the main thread waits for `differentThread` to finish before `main` itself exits, ensuring the `println` inside `businessLogic` actually executes and is visible before the program terminates — this mirrors how Reactor's own `Context` is carried along the entire length of a reactive pipeline's execution, correctly surviving any number of thread hops the underlying scheduler introduces.

```
Level 2 (ThreadLocal): authenticate sets ThreadLocal on main thread
                        businessLogic on differentThread -> ThreadLocal.get() -> null (LOST across the hop)

Level 3 (explicit Context): authenticate RETURNS a context object
                             context object passed EXPLICITLY (captured by lambda) to businessLogic
                             businessLogic on differentThread -> context.currentUser() -> "alice" (SURVIVES the hop)
```

## 7. Gotchas & takeaways

> **Gotcha:** mixing servlet-based (`SecurityContextHolder`, `ThreadLocal`-based) and reactive (`ReactiveSecurityContextHolder`, Reactor `Context`-based) security context APIs within the same reactive application is a common and confusing mistake — calling `SecurityContextHolder.getContext()` from within a WebFlux reactive pipeline may return stale, incorrect, or empty data, since that API's `ThreadLocal` assumption simply doesn't hold in a reactive execution model; the reactive-specific `ReactiveSecurityContextHolder` (typically accessed via a reactive operator chain, not a direct blocking call) must be used consistently throughout a WebFlux application instead.

- Spring Security's servlet and reactive stacks are parallel but genuinely distinct implementations, reflecting the fundamentally different threading models of Spring MVC (blocking, one thread per request) and Spring WebFlux (non-blocking, potentially multiple threads per logical request).
- The servlet stack's `SecurityContextHolder` relies on `ThreadLocal` storage, which works correctly precisely because a servlet request's processing stays on one thread for its entire duration — an assumption the reactive model doesn't share.
- The reactive stack instead propagates security context as part of Reactor's own `Context` mechanism, which travels explicitly along with a reactive pipeline's data flow rather than depending on thread identity, correctly surviving the thread hops that are a normal and expected part of reactive execution.
- Choosing the correct configuration classes (`HttpSecurity`/`SecurityFilterChain` for MVC, `ServerHttpSecurity`/`SecurityWebFilterChain` for WebFlux) and the correspondingly correct context-access API is not optional or interchangeable — using the wrong stack's classes and APIs for a given application type will not work correctly, not merely suboptimally.
