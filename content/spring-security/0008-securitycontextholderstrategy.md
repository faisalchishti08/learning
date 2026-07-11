---
card: spring-security
gi: 8
slug: securitycontextholderstrategy
title: "SecurityContextHolderStrategy"
---

## 1. What it is

`SecurityContextHolderStrategy` is the pluggable interface `SecurityContextHolder` delegates all its actual storage behavior to — the default `ThreadLocalSecurityContextHolderStrategy` backs storage with `ThreadLocal`, as the previous card covered, but `InheritableThreadLocalSecurityContextHolderStrategy` instead uses `InheritableThreadLocal` (so a security context automatically propagates from a parent thread to any child threads it spawns), and a fully custom strategy can be registered to change storage behavior application-wide, all without any calling code (`SecurityContextHolder.getContext()`) needing to change at all.

```java
// switching strategy globally, at application startup -- no calling code anywhere else needs to change
SecurityContextHolder.setStrategyName(SecurityContextHolder.MODE_INHERITABLETHREADLOCAL);
```

```java
public interface SecurityContextHolderStrategy {
    void clearContext();
    SecurityContext getContext();
    void setContext(SecurityContext context);
    SecurityContext createEmptyContext();
}
```

## 2. Why & when

The previous card established that `SecurityContextHolder`'s default `ThreadLocal`-based storage works correctly for a typical servlet request that stays on one thread — but some applications genuinely spawn child threads from within request-handling code and want that child thread to automatically inherit the parent's security context, without manually propagating it. Rather than hardcoding one single storage mechanism into `SecurityContextHolder` itself, Spring Security factors the actual storage behavior out into the swappable `SecurityContextHolderStrategy` interface, letting an application choose (or even implement its own custom strategy) without changing any of the calling code that reads and writes through `SecurityContextHolder`'s own static methods — exactly the same "depend on an interface, swap the implementation" pattern seen throughout Spring Security and Spring Cloud more broadly.

Reach for a non-default `SecurityContextHolderStrategy` when:

- An application spawns genuine child threads (not through Spring's own async/reactive machinery, which has its own dedicated context-propagation solutions) from within request-handling code, and wants those child threads to automatically see the same authenticated identity as the parent — `MODE_INHERITABLETHREADLOCAL` handles this automatically via `InheritableThreadLocal`.
- A genuinely custom storage mechanism is needed for the security context — perhaps storing it somewhere other than thread-local memory entirely for a specialized deployment scenario — a fully custom `SecurityContextHolderStrategy` implementation can be registered to replace the built-in ones.
- Understanding why `SecurityContextHolder.setStrategyName(...)` exists as a global, application-wide switch at all — recognizing this as a deliberate extensibility point, distinct from ordinary per-request configuration, clarifies that it's a startup-time, application-wide decision rather than something toggled per-request.

## 3. Core concept

```
 SecurityContextHolder (static access point, calling code NEVER changes)
        |
        v  delegates ALL actual storage behavior to
 SecurityContextHolderStrategy (the SWAPPABLE interface)
        |
        +-- ThreadLocalSecurityContextHolderStrategy (DEFAULT)
        |     -- plain ThreadLocal -- child threads get NOTHING automatically
        |
        +-- InheritableThreadLocalSecurityContextHolderStrategy
        |     -- InheritableThreadLocal -- child threads AUTOMATICALLY inherit the parent's context
        |
        +-- (a fully CUSTOM implementation, if needed)

 SecurityContextHolder.setStrategyName(...) switches WHICH implementation is active,
 GLOBALLY, for the WHOLE application -- calling code (SecurityContextHolder.getContext()) is UNCHANGED
```

The same interface-swap pattern seen throughout this series (`DiscoveryClient`, `AppDeployer`) applied here specifically to security context storage strategy.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SecurityContextHolder delegates to one of two swappable strategy implementations plain ThreadLocal where child threads get nothing automatically or InheritableThreadLocal where child threads automatically inherit the parents context with calling code unchanged either way">
  <rect x="230" y="20" width="180" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">SecurityContextHolder</text>

  <rect x="30" y="100" width="250" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="155" y="120" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">ThreadLocalStrategy (default)</text>
  <text x="155" y="134" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">child threads: NOTHING inherited</text>

  <rect x="350" y="100" width="260" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="480" y="120" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">InheritableThreadLocalStrategy</text>
  <text x="480" y="134" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">child threads: AUTOMATICALLY inherit</text>

  <defs><marker id="a8" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="280" y1="60" x2="155" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a8)"/>
  <line x1="360" y1="60" x2="480" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a8)"/>
</svg>

One static entry point at the top, two (or more) swappable storage strategies underneath — a global, application-wide choice.

## 5. Runnable example

The scenario: model both storage strategies directly — a plain `ThreadLocal`-based one where a child thread sees nothing, and an `InheritableThreadLocal`-based one where a child thread automatically inherits the parent's value — behind one shared holder interface. Start with the default strategy showing a child thread seeing nothing, then swap to the inheritable strategy showing automatic propagation, then add a custom strategy demonstrating the full extensibility the interface provides.

### Level 1 — Basic

The default strategy: a plain `ThreadLocal`, where a spawned child thread sees nothing inherited.

```java
public class SecurityContextStrategyLevel1 {
    interface Strategy {
        void setContext(String value);
        String getContext();
    }

    static class ThreadLocalStrategy implements Strategy {
        ThreadLocal<String> storage = new ThreadLocal<>();
        public void setContext(String value) { storage.set(value); }
        public String getContext() { return storage.get(); }
    }

    static class SecurityContextHolder {
        static Strategy strategy = new ThreadLocalStrategy(); // the DEFAULT
        static void setContext(String value) { strategy.setContext(value); }
        static String getContext() { return strategy.getContext(); }
    }

    public static void main(String[] args) throws InterruptedException {
        SecurityContextHolder.setContext("alice"); // set on the MAIN thread

        Thread child = new Thread(() -> System.out.println("child thread sees: " + SecurityContextHolder.getContext()));
        child.start();
        child.join();
    }
}
```

How to run: `java SecurityContextStrategyLevel1.java`

The child thread prints `null` — the default `ThreadLocalStrategy` provides no automatic propagation to spawned child threads, exactly matching the earlier card's demonstration of plain `ThreadLocal`'s single-thread-only visibility.

### Level 2 — Intermediate

Swap in an inheritable strategy, changing only the strategy assignment — the calling code (`setContext`/`getContext`) remains identical, but now the child thread automatically inherits the value.

```java
public class SecurityContextStrategyLevel2 {
    interface Strategy {
        void setContext(String value);
        String getContext();
    }

    static class ThreadLocalStrategy implements Strategy {
        ThreadLocal<String> storage = new ThreadLocal<>();
        public void setContext(String value) { storage.set(value); }
        public String getContext() { return storage.get(); }
    }

    static class InheritableThreadLocalStrategy implements Strategy {
        InheritableThreadLocal<String> storage = new InheritableThreadLocal<>();
        public void setContext(String value) { storage.set(value); }
        public String getContext() { return storage.get(); }
    }

    static class SecurityContextHolder {
        static Strategy strategy = new ThreadLocalStrategy(); // will be SWAPPED below
        static void setStrategy(Strategy newStrategy) { strategy = newStrategy; }
        static void setContext(String value) { strategy.setContext(value); }
        static String getContext() { return strategy.getContext(); }
    }

    public static void main(String[] args) throws InterruptedException {
        SecurityContextHolder.setStrategy(new InheritableThreadLocalStrategy()); // THE ONLY CHANGE from Level 1

        SecurityContextHolder.setContext("alice"); // SAME call as Level 1

        Thread child = new Thread(() -> System.out.println("child thread sees: " + SecurityContextHolder.getContext()));
        child.start();
        child.join();
    }
}
```

How to run: `java SecurityContextStrategyLevel2.java`

The child thread now correctly prints `"alice"` — the only change from Level 1 was swapping the active `Strategy` implementation; `setContext`/`getContext`'s calling code is byte-for-byte identical, exactly demonstrating how `SecurityContextHolder.setStrategyName(SecurityContextHolder.MODE_INHERITABLETHREADLOCAL)` changes global propagation behavior without requiring any change to the application code that reads and writes through `SecurityContextHolder`'s own static methods.

### Level 3 — Advanced

Add a fully custom strategy — one that logs every access, demonstrating the interface's extensibility for purposes beyond just choosing between the two built-in options.

```java
import java.util.*;

public class SecurityContextStrategyLevel3 {
    interface Strategy {
        void setContext(String value);
        String getContext();
    }

    static class ThreadLocalStrategy implements Strategy {
        ThreadLocal<String> storage = new ThreadLocal<>();
        public void setContext(String value) { storage.set(value); }
        public String getContext() { return storage.get(); }
    }

    // a FULLY CUSTOM strategy -- wraps another strategy, adding audit logging on every access
    static class AuditingStrategy implements Strategy {
        Strategy delegate;
        List<String> auditLog = new ArrayList<>();
        AuditingStrategy(Strategy delegate) { this.delegate = delegate; }
        public void setContext(String value) {
            auditLog.add("SET context to '" + value + "'");
            delegate.setContext(value);
        }
        public String getContext() {
            String value = delegate.getContext();
            auditLog.add("READ context, got '" + value + "'");
            return value;
        }
    }

    static class SecurityContextHolder {
        static Strategy strategy = new AuditingStrategy(new ThreadLocalStrategy()); // CUSTOM strategy, wrapping the default
        static void setContext(String value) { strategy.setContext(value); }
        static String getContext() { return strategy.getContext(); }
    }

    public static void main(String[] args) {
        SecurityContextHolder.setContext("alice");
        SecurityContextHolder.getContext();
        SecurityContextHolder.getContext();

        AuditingStrategy auditing = (AuditingStrategy) SecurityContextHolder.strategy;
        System.out.println("audit log entries:");
        for (String entry : auditing.auditLog) System.out.println("  " + entry);
    }
}
```

How to run: `java SecurityContextStrategyLevel3.java`

`AuditingStrategy` wraps another `Strategy` (here, `ThreadLocalStrategy`) and adds logging around every `setContext`/`getContext` call, without needing to reimplement the actual storage mechanism itself — `SecurityContextHolder`'s own calling code (`setContext`/`getContext`) is completely unaffected by this addition, exactly demonstrating how a genuinely custom `SecurityContextHolderStrategy` implementation could add cross-cutting behavior (auditing, metrics, validation) around security context access application-wide, purely by registering a different strategy at startup.

## 6. Walkthrough

Trace the three `SecurityContextHolder` calls in Level 3.

1. `SecurityContextHolder.setContext("alice")` calls `strategy.setContext("alice")`, which dispatches to `AuditingStrategy.setContext` — this appends `"SET context to 'alice'"` to `auditLog`, then calls `delegate.setContext("alice")`, which is `ThreadLocalStrategy.setContext`, actually storing `"alice"` in its `ThreadLocal`.
2. The first `SecurityContextHolder.getContext()` call dispatches to `AuditingStrategy.getContext` — this first calls `delegate.getContext()`, retrieving `"alice"` from the underlying `ThreadLocalStrategy`, then appends `"READ context, got 'alice'"` to `auditLog`, then returns `"alice"`.
3. The second `getContext()` call repeats the identical process, appending a second `"READ context, got 'alice'"` entry.
4. The final `for` loop over `auditing.auditLog` prints three lines in order: the one `SET` entry, followed by the two `READ` entries — this audit trail was produced entirely by the custom `AuditingStrategy` wrapper, with `SecurityContextHolder`'s own `setContext`/`getContext` methods (and any other application code calling them) completely unaware that any auditing was happening underneath.
5. This demonstrates the practical extensibility payoff of the strategy pattern: adding cross-cutting behavior around every security context access, application-wide, required writing exactly one new class (`AuditingStrategy`) and changing exactly one line (which strategy is assigned at startup) — no change anywhere else in the application's existing code that already calls `SecurityContextHolder.getContext()`/`setContext(...)`.

```
setContext("alice"):
  AuditingStrategy.setContext -> log "SET context to 'alice'" -> delegate.setContext("alice") (actual storage)

getContext() [called twice]:
  AuditingStrategy.getContext -> delegate.getContext() -> "alice" -> log "READ context, got 'alice'" -> return "alice"
  (repeated for the second call)

auditLog: ["SET context to 'alice'", "READ context, got 'alice'", "READ context, got 'alice'"]
```

## 7. Gotchas & takeaways

> **Gotcha:** `InheritableThreadLocal`-based propagation only helps with threads spawned *directly* as children of the current thread (via `new Thread(...)`) — it does not automatically propagate correctly through a thread *pool* (an `ExecutorService`), since pooled threads are typically created once, upfront, long before any specific task submission, meaning the "parent" at inheritance time isn't the thread that later submits work to that pool. For thread-pool-based asynchronous work, Spring Security's dedicated `DelegatingSecurityContextExecutor`/`DelegatingSecurityContextExecutorService` utilities (which explicitly capture and re-apply the context per task) are the correct tool, not simply switching to the inheritable strategy.

- `SecurityContextHolderStrategy` factors `SecurityContextHolder`'s actual storage behavior out into a swappable interface, letting an application change global context-propagation behavior (or add custom cross-cutting logic around every access) without touching any of the calling code that already reads and writes through `SecurityContextHolder`'s static methods.
- The default `ThreadLocalSecurityContextHolderStrategy` and the alternative `InheritableThreadLocalSecurityContextHolderStrategy` differ specifically in whether directly-spawned child threads automatically inherit the parent thread's security context.
- Choosing a strategy is a global, application-wide, typically startup-time decision (`SecurityContextHolder.setStrategyName(...)`), not something toggled per-request — this reflects that it's an infrastructural choice about how context storage behaves throughout the entire application's lifetime.
- Thread-pool-based asynchronous work needs Spring Security's dedicated context-propagation utilities rather than relying on `InheritableThreadLocal`'s parent-to-child inheritance model, which doesn't correctly apply to the way thread pools actually create and reuse their worker threads.
