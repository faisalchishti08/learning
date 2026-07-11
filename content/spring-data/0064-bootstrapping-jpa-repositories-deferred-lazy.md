---
card: spring-data
gi: 64
slug: bootstrapping-jpa-repositories-deferred-lazy
title: "Bootstrapping JPA repositories (deferred/lazy)"
---

## 1. What it is

`@EnableJpaRepositories(bootstrapMode = ...)` controls *when* Spring Data JPA repository proxies are actually wired up during application startup: `DEFAULT` builds them eagerly as beans are created, `DEFERRED` builds them but waits until the `EntityManagerFactory` (Hibernate/JPA's expensive-to-build bootstrap object) has fully finished initializing, and `LAZY` goes further and only builds each individual repository proxy the first time it's actually injected and used.

```java
@EnableJpaRepositories(bootstrapMode = BootstrapMode.DEFERRED)
@SpringBootApplication
class Application { }
```

## 2. Why & when

Building the JPA `EntityManagerFactory` is one of the slowest parts of application startup, since it scans all entities, validates mappings, and (depending on configuration) builds a second-level cache. `BootstrapMode` decides whether repository beans have to wait for that expensive step to fully complete before they themselves become usable, which directly affects how fast the application context finishes starting.

Reach for a non-default bootstrap mode specifically when:

- Startup time matters (e.g., serverless/cold-start environments, or large applications with hundreds of repositories) and you want repository bean creation to overlap with the `EntityManagerFactory`'s own background initialization — `DEFERRED` mode.
- Only a fraction of your repositories are actually used in any given process run (e.g., a modular monolith where each request path only touches a handful of the total repositories) and you want unused ones to never pay their initialization cost — `LAZY` mode.
- You're debugging a startup-order problem where a repository is injected and used before the persistence layer is ready — understanding `DEFAULT` (synchronous, in bean-creation order) explains why that failure happens.

## 3. Core concept

```
 DEFAULT:  repository proxies built AS SOON AS their bean is created
           -- may block on EntityManagerFactory if it isn't ready yet

 DEFERRED: repository proxies built when requested, but the actual work
           waits until EntityManagerFactory bootstrap has FULLY finished
           -- lets EMF init run in the background while other beans start

 LAZY:     like DEFERRED, but ALSO delays building each individual
           repository proxy until it is first actually injected/used
           -- unused repositories never pay their init cost at all
```

Each mode pushes repository initialization later — `DEFAULT` is immediate, `DEFERRED` waits for the shared persistence unit, `LAZY` waits per-repository until first use.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Three bootstrap modes build repository proxies at different points relative to EntityManagerFactory init and first use">
  <text x="20" y="20" fill="#8b949e" font-size="9.5" font-family="sans-serif">timeline -&gt;</text>

  <rect x="20" y="30" width="150" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="95" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">DEFAULT: build now</text>

  <rect x="20" y="80" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="95" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">DEFERRED: wait...</text>
  <rect x="330" y="80" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="405" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">EMF ready -&gt; build</text>

  <rect x="20" y="130" width="150" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="95" y="152" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">LAZY: wait...</text>
  <rect x="500" y="130" width="120" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="560" y="152" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">first use -&gt; build</text>

  <line x1="170" y1="97" x2="325" y2="97" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="4,3"/>
  <line x1="170" y1="147" x2="495" y2="147" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="4,3"/>
</svg>

`DEFERRED` builds all repositories once the persistence unit is ready; `LAZY` further delays each one until it is actually used.

## 5. Runnable example

The scenario: an application wiring several repositories at startup, evolving from eager (`DEFAULT`-style) construction, to deferred construction that waits for a shared "persistence unit" to finish, to lazy per-repository construction triggered only on first use.

### Level 1 — Basic

Model `DEFAULT` bootstrap mode: every repository proxy is built immediately as its bean is created.

```java
import java.util.*;

class EntityManagerFactory {
    EntityManagerFactory() {
        System.out.println("EntityManagerFactory: scanning entities, building mappings...");
    }
}

class Repository {
    private final String name;
    Repository(String name, EntityManagerFactory emf) {
        this.name = name;
        System.out.println("  Repository[" + name + "]: proxy built (using EMF)");
    }
}

public class BootstrapLevel1 {
    public static void main(String[] args) {
        System.out.println("Application starting (bootstrapMode = DEFAULT)");
        EntityManagerFactory emf = new EntityManagerFactory(); // must finish first
        // Every repository bean built immediately, in bean-creation order.
        Repository orders = new Repository("OrderRepository", emf);
        Repository customers = new Repository("CustomerRepository", emf);
        Repository products = new Repository("ProductRepository", emf);
        System.out.println("Application ready");
    }
}
```

How to run: `java BootstrapLevel1.java`

Each `Repository` is constructed the moment its line runs, and each constructor call happens strictly after `emf` finished — mirroring `DEFAULT` mode, where every repository proxy is built synchronously, in bean-creation order, and none of them can start until the `EntityManagerFactory` they depend on is fully ready.

### Level 2 — Intermediate

Model `DEFERRED` mode: repository beans are created right away as lightweight placeholders, but their actual proxy-building work is queued until the `EntityManagerFactory` signals it has finished — letting the two initialize concurrently instead of strictly sequentially.

```java
import java.util.*;
import java.util.function.*;

class EntityManagerFactory {
    private final List<Runnable> onReady = new ArrayList<>();
    private boolean ready = false;

    void whenReady(Runnable callback) {
        if (ready) callback.run(); else onReady.add(callback);
    }

    void finishInitializing() {
        System.out.println("EntityManagerFactory: finished scanning entities and building mappings");
        ready = true;
        onReady.forEach(Runnable::run); // fire all deferred repository builds now
    }
}

class DeferredRepository {
    private final String name;
    DeferredRepository(String name, EntityManagerFactory emf) {
        this.name = name;
        System.out.println("  Repository[" + name + "]: bean created, deferring proxy build...");
        emf.whenReady(() -> System.out.println("    Repository[" + name + "]: proxy built (EMF was ready)"));
    }
}

public class BootstrapLevel2 {
    public static void main(String[] args) {
        System.out.println("Application starting (bootstrapMode = DEFERRED)");
        EntityManagerFactory emf = new EntityManagerFactory();

        // These beans are created immediately, but their proxy work is DEFERRED.
        DeferredRepository orders = new DeferredRepository("OrderRepository", emf);
        DeferredRepository customers = new DeferredRepository("CustomerRepository", emf);

        System.out.println("(other unrelated beans could initialize here, in parallel with EMF)");
        emf.finishInitializing(); // only now do the deferred repository builds actually run
        System.out.println("Application ready");
    }
}
```

How to run: `java BootstrapLevel2.java`

Both `DeferredRepository` beans print "bean created, deferring..." immediately, but their "proxy built" message only appears after `emf.finishInitializing()` runs — standing in for how `DEFERRED` mode lets unrelated application beans keep initializing while the `EntityManagerFactory` finishes its own expensive work in the background, instead of blocking on it up front like `DEFAULT` does.

### Level 3 — Advanced

Model `LAZY` mode: repository proxies are not built even when the `EntityManagerFactory` becomes ready — only on first actual use, via a lazy-initializing wrapper (standing in for a JDK dynamic proxy).

```java
import java.util.*;
import java.util.function.*;

class EntityManagerFactory {
    private boolean ready = false;
    void finishInitializing() {
        System.out.println("EntityManagerFactory: ready");
        ready = true;
    }
    boolean isReady() { return ready; }
}

class RealRepository {
    private final String name;
    RealRepository(String name, EntityManagerFactory emf) {
        this.name = name;
        if (!emf.isReady()) throw new IllegalStateException("EMF not ready");
        System.out.println("    Repository[" + name + "]: actual proxy built NOW (first use)");
    }
    void findAll() { System.out.println("    Repository[" + name + "]: findAll() executed"); }
}

// Stands in for the lazy JDK dynamic proxy Spring Data creates under bootstrapMode = LAZY.
class LazyRepository {
    private final String name;
    private final EntityManagerFactory emf;
    private RealRepository real; // null until first real use

    LazyRepository(String name, EntityManagerFactory emf) {
        this.name = name; this.emf = emf;
        System.out.println("  Repository[" + name + "]: lazy proxy created, NOT built yet");
    }

    private RealRepository resolve() {
        if (real == null) real = new RealRepository(name, emf); // built only here, on first call
        return real;
    }

    void findAll() { resolve().findAll(); }
}

public class BootstrapLevel3 {
    public static void main(String[] args) {
        System.out.println("Application starting (bootstrapMode = LAZY)");
        EntityManagerFactory emf = new EntityManagerFactory();

        LazyRepository orders = new LazyRepository("OrderRepository", emf);
        LazyRepository customers = new LazyRepository("CustomerRepository", emf); // never used below!

        emf.finishInitializing();
        System.out.println("Application ready (no repository proxies actually built yet)");

        System.out.println("First request arrives, needs OrderRepository:");
        orders.findAll(); // THIS triggers the real proxy build, only now
        // customers.findAll() is never called -> CustomerRepository's real proxy is never built
    }
}
```

How to run: `java BootstrapLevel3.java`

`customers` is created but never queried, so `RealRepository` for `CustomerRepository` is never constructed at all — only `orders.findAll()` triggers `resolve()`, which lazily builds the real proxy at that moment. This is the full benefit of `LAZY` mode: repositories that are never exercised in a given process run never pay their initialization cost.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `emf` is created (not yet ready). Then two `LazyRepository` wrappers are constructed — each immediately prints "lazy proxy created, NOT built yet" and stores `real = null`; no `RealRepository` exists for either at this point.

Next, `emf.finishInitializing()` runs, printing "EntityManagerFactory: ready" and flipping `ready` to `true` — but critically, this does **not** trigger either `LazyRepository` to build its real proxy; `LAZY` mode has no hook that fires on EMF readiness the way `DEFERRED` did in Level 2.

"Application ready" prints next, with zero real repository proxies built so far. Then `orders.findAll()` is called: this invokes `resolve()`, which sees `real == null`, so it constructs a `new RealRepository("OrderRepository", emf)` right there — printing "actual proxy built NOW (first use)" — and only then calls `findAll()` on it, printing "findAll() executed". `customers.findAll()` is never called in this program, so `CustomerRepository`'s `RealRepository` is never constructed — its cost is never paid.

```
DEFAULT:  emf ready --------> [orders built][customers built][products built] -> app ready
DEFERRED: emf init (bg) --+-> [orders queued][customers queued]                -> emf ready -> both built -> app ready
                           |
LAZY:     emf init -> emf ready -> app ready -> (nothing built) -> first orders.findAll() -> orders built now
                                                                     (customers never built)
```

In a real Spring Boot application with `bootstrapMode = BootstrapMode.LAZY`, the application context can report "started" well before any repository has actually been fully initialized — the first HTTP request that reaches a controller depending on `OrderRepository` is what triggers that specific repository's real Hibernate-backed implementation to be built, on that request's thread, adding a one-time delay to that first request rather than to application startup.

## 7. Gotchas & takeaways

> Gotcha: `LAZY` mode moves initialization cost from application startup to the *first request* that touches each repository — this can make an individual early request unexpectedly slow (or even fail, if `EntityManagerFactory` somehow isn't fully ready) in exchange for faster startup; it is a genuine tradeoff, not a free win.

- `DEFAULT`: every repository proxy is built synchronously and immediately, in bean-creation order.
- `DEFERRED`: repository beans exist immediately, but proxy construction waits until the shared `EntityManagerFactory` finishes, letting the two initialize concurrently.
- `LAZY`: goes further — each individual repository's proxy is only built the first time it is actually injected and used; unused repositories never pay the cost.
- Use `DEFERRED`/`LAZY` to reduce startup time in large applications or many-repository codebases; understand the tradeoff of pushing cost onto first use before adopting `LAZY` in latency-sensitive request paths.
