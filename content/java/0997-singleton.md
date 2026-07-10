---
card: java
gi: 997
slug: singleton
title: Singleton
---

## 1. What it is

The **Singleton** pattern ensures a class has **exactly one instance** for the entire application, and provides one well-known way to access it. Instead of `new`-ing the class wherever it's needed (which would create multiple, independent instances), code asks the class itself for "the" instance, and always gets the same object back. It's commonly used for things that genuinely should be unique and shared: a configuration object, a connection pool, a logging registry.

## 2. Why & when

Some resources are expensive to create, need centrally-managed shared state, or must genuinely be unique to avoid conflicting with themselves (two independent connection pools competing for the same database limits, for instance). Singleton exists to guarantee — at the language level, not just by convention — that only one instance is ever created, no matter how many places in the codebase ask for it.

Reach for Singleton sparingly: it's genuinely useful for things that are unique by nature (one JVM-wide configuration, one connection pool per database). It's overused when applied to things that merely *feel* global but aren't actually unique in every context (a "current user" singleton breaks the moment the application needs to handle two users, such as in a multi-tenant server) — those are usually better modeled as a value passed around or managed by a dependency-injection framework instead of a hard-coded static singleton.

## 3. Core concept

```
// Thread-safe lazy singleton using double-checked locking
class ConfigurationManager {
    private static volatile ConfigurationManager instance;
    private final String environment;

    private ConfigurationManager() { // private: nobody else can call `new`
        this.environment = "production";
    }

    static ConfigurationManager getInstance() {
        if (instance == null) {                       // first check, no lock (fast path)
            synchronized (ConfigurationManager.class) {
                if (instance == null) {                // second check, inside the lock
                    instance = new ConfigurationManager();
                }
            }
        }
        return instance;
    }

    String getEnvironment() { return environment; }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three different callers all calling ConfigurationManager.getInstance and all receiving a reference to the same single object">
  <rect x="30" y="20" width="130" height="34" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="95" y="41" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller A</text>
  <rect x="30" y="80" width="130" height="34" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="95" y="101" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller B</text>
  <rect x="30" y="140" width="130" height="34" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="95" y="161" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller C</text>

  <rect x="360" y="80" width="220" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="102" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">the ONE</text>
  <text x="470" y="120" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ConfigurationManager instance</text>

  <line x1="160" y1="37" x2="360" y2="95" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="160" y1="97" x2="360" y2="105" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="160" y1="157" x2="360" y2="115" stroke="#79c0ff" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

All callers call `getInstance()` and all get a reference to the exact same object, never a fresh copy.

## 5. Runnable example

Scenario: a configuration manager shared across an application, evolving from a naive (broken under concurrency) singleton into a robust, thread-safe implementation using the idiomatic Java enum form.

### Level 1 — Basic

```java
// File: SingletonBasic.java
class ConfigurationManager {
    private static ConfigurationManager instance;
    private final String environment = "production";

    private ConfigurationManager() {
        System.out.println("ConfigurationManager constructed");
    }

    static ConfigurationManager getInstance() {
        if (instance == null) {
            instance = new ConfigurationManager();
        }
        return instance;
    }

    String getEnvironment() { return environment; }
}

public class SingletonBasic {
    public static void main(String[] args) {
        ConfigurationManager a = ConfigurationManager.getInstance();
        ConfigurationManager b = ConfigurationManager.getInstance();
        System.out.println("same instance: " + (a == b));
        System.out.println("environment: " + a.getEnvironment());
    }
}
```

**How to run:** save as `SingletonBasic.java`, then `javac SingletonBasic.java && java SingletonBasic` (JDK 17+).

Expected output:
```
ConfigurationManager constructed
same instance: true
environment: production
```

Note "constructed" printed only once, even though `getInstance()` was called twice — but this version isn't safe if two threads call `getInstance()` at the exact same moment for the first time; both could see `instance == null` and construct two separate objects.

### Level 2 — Intermediate

```java
// File: SingletonIntermediate.java
class ConfigurationManager {
    private static volatile ConfigurationManager instance;
    private final String environment = "production";

    private ConfigurationManager() {
        System.out.println("ConfigurationManager constructed");
    }

    // Double-checked locking: synchronize only on first creation, not on every call.
    static ConfigurationManager getInstance() {
        if (instance == null) {
            synchronized (ConfigurationManager.class) {
                if (instance == null) {
                    instance = new ConfigurationManager();
                }
            }
        }
        return instance;
    }

    String getEnvironment() { return environment; }
}

public class SingletonIntermediate {
    public static void main(String[] args) throws InterruptedException {
        Runnable task = () -> System.out.println(ConfigurationManager.getInstance().getEnvironment());
        Thread t1 = new Thread(task);
        Thread t2 = new Thread(task);
        t1.start(); t2.start();
        t1.join(); t2.join();
    }
}
```

**How to run:** save as `SingletonIntermediate.java`, then `javac SingletonIntermediate.java && java SingletonIntermediate` (JDK 17+).

Expected output (order of the two "production" lines may vary, but "constructed" appears exactly once):
```
ConfigurationManager constructed
production
production
```

The real-world concern added: two threads race to call `getInstance()` for the first time. The `volatile` field plus double-checked locking guarantees only one thread ever constructs the instance, and every thread — including the one that lost the race — ends up with the same reference.

### Level 3 — Advanced

```java
// File: SingletonAdvanced.java
import java.util.concurrent.atomic.AtomicInteger;

// The idiomatic, JVM-enforced Java singleton: an enum with one constant.
// The JVM guarantees exactly one instance per enum constant, even across
// serialization and reflection-based attacks that can break other approaches.
enum ConfigurationManager {
    INSTANCE;

    private final String environment = "production";
    private final AtomicInteger accessCount = new AtomicInteger(0);

    String getEnvironment() {
        accessCount.incrementAndGet();
        return environment;
    }

    int getAccessCount() { return accessCount.get(); }
}

public class SingletonAdvanced {
    public static void main(String[] args) throws InterruptedException {
        Runnable task = () -> System.out.println(ConfigurationManager.INSTANCE.getEnvironment());

        Thread[] threads = new Thread[5];
        for (int i = 0; i < threads.length; i++) {
            threads[i] = new Thread(task);
            threads[i].start();
        }
        for (Thread t : threads) t.join();

        System.out.println("total accesses: " + ConfigurationManager.INSTANCE.getAccessCount());
    }
}
```

**How to run:** save as `SingletonAdvanced.java`, then `javac SingletonAdvanced.java && java SingletonAdvanced` (JDK 17+).

Expected output (the five "production" lines may print in any order):
```
production
production
production
production
production
total accesses: 5
```

The production-flavored hard case: five threads hit `ConfigurationManager.INSTANCE` concurrently. Because an `enum` constant is instantiated exactly once by the JVM itself — before any thread can even reference it — there's no race condition to manage at all, and `AtomicInteger` safely tracks concurrent increments to the shared access count.

## 6. Walkthrough

Tracing `SingletonAdvanced.main` end to end:

1. `ConfigurationManager` is declared as an `enum` with a single constant, `INSTANCE`. The JVM guarantees this constant is created exactly once, during class initialization, before any code can reference `ConfigurationManager.INSTANCE`.
2. Five `Thread` objects are created, each wrapping the same `task` lambda, and all five are started in a tight loop — they may run concurrently, all reaching `ConfigurationManager.INSTANCE.getEnvironment()` at nearly the same time.
3. Because `INSTANCE` already exists (constructed once, before any thread started), every thread's `ConfigurationManager.INSTANCE` reference resolves to the exact same object — no locking is needed to guard first-time construction, unlike the double-checked-locking version.
4. Inside `getEnvironment()`, `accessCount.incrementAndGet()` runs — `AtomicInteger`'s increment is atomic, so even with five threads calling it concurrently, no increment is lost; the final count reflects all five calls.
5. Each thread prints `"production"` (the return value of `getEnvironment()`) — the five lines can interleave in any order depending on the OS thread scheduler, but there are always exactly five of them.
6. `t.join()` in the loop waits for all five threads to finish before `main` continues. `ConfigurationManager.INSTANCE.getAccessCount()` is then called from the main thread, reading the final, fully-updated count: `5`.

## 7. Gotchas & takeaways

> **Gotcha:** the naive `if (instance == null) instance = new ...` singleton (Level 1) is not thread-safe — two threads can both pass the `null` check before either finishes constructing, resulting in two separate instances and silently breaking the "exactly one" guarantee the whole pattern exists for.

- Singleton guarantees exactly one instance, accessed through one well-known method or reference, for the lifetime of the application.
- The naive lazy version breaks under concurrency; double-checked locking (with a `volatile` field) fixes it but adds ceremony.
- The `enum`-with-one-constant form is the idiomatic, safest Java singleton: the JVM enforces single instantiation and it's automatically thread-safe and serialization-safe.
- Singleton is overused when applied to state that only *seems* global — a "current user" or "current request" singleton breaks the moment the application needs to serve more than one at a time.
- Modern practice often prefers a dependency-injection framework's "singleton scope" (one instance managed by the framework, injected everywhere it's needed) over a hand-rolled static singleton, since it keeps the class itself testable and swappable — see [SOLID — Dependency Inversion](0993-solid-dependency-inversion.md).
- See [Factory Method](0998-factory-method.md) for a pattern often used alongside Singleton to control how instances of *other* classes get created.
