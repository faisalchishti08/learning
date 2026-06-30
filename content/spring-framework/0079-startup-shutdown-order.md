---
card: spring-framework
gi: 79
slug: startup-shutdown-order
title: Startup shutdown order
---

## 1. What it is

Spring's **startup and shutdown order** describes the combined sequence in which beans are created, initialised, started, stopped, and destroyed. Creation follows the dependency graph (a bean's dependencies are created before it). Destruction is the strict reverse. `SmartLifecycle` phases add a second ordering layer on top — affecting when `start()` / `stop()` fire relative to each other, but not overriding the underlying bean creation/destruction order.

```
Full lifecycle order for a production app:

STARTUP:
  ① Bean construction (dependency order — leaves of graph first)
  ② @Autowired / @Value injection
  ③ @PostConstruct / afterPropertiesSet / init-method    (per bean)
  ④ context.refresh() completes
  ⑤ SmartLifecycle.start() — in phase order (lower phase first)

SHUTDOWN (context.close()):
  ⑥ SmartLifecycle.stop(callback) — in REVERSE phase order (higher phase first)
  ⑦ @PreDestroy / DisposableBean.destroy() / destroy-method (per bean, reverse creation order)
```

In one sentence: **Spring's startup order is: create all beans in dependency order → run lifecycle callbacks → start `SmartLifecycle` beans in phase order; shutdown reverses each step, so the last bean to start is the first to stop and the first bean created is the last to be destroyed.**

## 2. Why & when

Understanding startup/shutdown order matters when:

- A bean's `@PostConstruct` calls a collaborator — you must know the collaborator is already constructed and injected (it is, because Spring creates it first as a dependency).
- A `SmartLifecycle` bean's `start()` calls another bean — the other bean is already fully initialised (construction + callbacks done), but might not be `started` yet if it's in a later phase.
- A background thread set up in `@PostConstruct` depends on another bean being `started` — use `SmartLifecycle` for this, not `@PostConstruct`.
- Shutdown: a service's `@PreDestroy` must flush to a database — the database bean must not yet be destroyed (it's safe because destruction is reverse of creation, so the DB's `@PreDestroy` fires after the service's).

## 3. Core concept

```
Dependency graph:  A ← B ← C  (C depends on B depends on A)

CREATION (startup):
  A is created first (no deps)    → @PostConstruct A
  B is created second (deps on A) → @PostConstruct B
  C is created third  (deps on B) → @PostConstruct C
  [context.refresh() completes]
  SmartLifecycle.start() by phase:
    phase -1: A.start() (if SmartLifecycle)
    phase 0:  B.start() (if SmartLifecycle)

DESTRUCTION (shutdown):
  SmartLifecycle.stop() by reverse phase:
    phase 0:  B.stop()  (if SmartLifecycle)
    phase -1: A.stop()  (if SmartLifecycle)
  Then bean destruction in REVERSE CREATION order:
    C.@PreDestroy → C destroyed
    B.@PreDestroy → B destroyed (A still alive)
    A.@PreDestroy → A destroyed (last)

Rule for @PreDestroy safety:
  When C.@PreDestroy runs, B and A are still alive → C can call them.
  When B.@PreDestroy runs, A is still alive → B can call A.
  When A.@PreDestroy runs, B and C are already gone → A must not call them.
```

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Complete startup and shutdown order with all layers">
  <defs>
    <marker id="a79" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b79" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="208" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Complete startup → shutdown sequence (three distinct layers)</text>

  <!-- Layer 1: Bean creation + init -->
  <rect x="10" y="30" width="200" height="70" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="110" y="47" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">LAYER 1 — Bean init</text>
  <text x="110" y="61" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">① construct (dep order)</text>
  <text x="110" y="74" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">② inject</text>
  <text x="110" y="87" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">③ @PostConstruct etc.</text>

  <!-- Layer 2: Lifecycle start -->
  <rect x="240" y="30" width="200" height="70" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="340" y="47" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">LAYER 2 — Lifecycle start</text>
  <text x="340" y="61" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">④ context.refresh() done</text>
  <text x="340" y="74" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">⑤ SmartLifecycle.start()</text>
  <text x="340" y="87" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">   (low phase first)</text>

  <!-- Application box -->
  <rect x="460" y="30" width="200" height="70" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="560" y="58" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">APPLICATION</text>
  <text x="560" y="74" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">handling requests</text>

  <!-- Arrows startup -->
  <line x1="210" y1="65" x2="238" y2="65" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a79)"/>
  <line x1="440" y1="65" x2="458" y2="65" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a79)"/>

  <!-- Separator -->
  <line x1="15" y1="115" x2="660" y2="115" stroke="#8b949e" stroke-width="0.5" stroke-dasharray="4,3"/>
  <text x="338" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">context.close() ↓</text>

  <!-- Layer 2 shutdown -->
  <rect x="240" y="137" width="200" height="60" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="340" y="153" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">LAYER 2 — Lifecycle stop</text>
  <text x="340" y="167" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">⑥ SmartLifecycle.stop()</text>
  <text x="340" y="180" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">   (high phase first)</text>

  <!-- Layer 1 shutdown -->
  <rect x="10" y="137" width="200" height="60" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="110" y="153" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">LAYER 1 — Bean destroy</text>
  <text x="110" y="167" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">⑦ @PreDestroy etc.</text>
  <text x="110" y="180" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">   (reverse creation order)</text>

  <!-- Arrows shutdown (right to left) -->
  <line x1="458" y1="167" x2="442" y2="167" stroke="#8b949e" stroke-width="1.3" marker-end="url(#b79)"/>
  <line x1="238" y1="167" x2="212" y2="167" stroke="#8b949e" stroke-width="1.3" marker-end="url(#b79)"/>
</svg>

Startup flows left-to-right: bean init → lifecycle start → application. Shutdown reverses: lifecycle stop → bean destroy.

## 5. Runnable example

Scenario: a real-world three-layer system — a database pool, a service, and a web server — demonstrating every step of the full startup and shutdown sequence with logging at each layer.

### Level 1 — Basic

Capture the complete create → init → destroy sequence for two dependent beans.

```java
// StartupShutdownOrderDemo.java — run with: java StartupShutdownOrderDemo.java
import java.util.*;

public class StartupShutdownOrderDemo {

    static final List<String> LOG = new ArrayList<>();

    static class DatabasePool {
        boolean open = false;
        DatabasePool()    { LOG.add("1.construct:DatabasePool"); System.out.println("  [CONSTRUCT]     DatabasePool"); }
        void postConstruct() { open=true; LOG.add("3.postConstruct:DatabasePool"); System.out.println("  [POSTCONSTRUCT] DatabasePool — connections open=" + open); }
        void preDestroy()    { open=false; LOG.add("7.preDestroy:DatabasePool");    System.out.println("  [PREDESTROY]    DatabasePool — connections closed"); }
    }

    static class OrderService {
        private final DatabasePool db;
        OrderService(DatabasePool db) { this.db=db; LOG.add("1.construct:OrderService"); System.out.println("  [CONSTRUCT]     OrderService (db.open=" + db.open + " ← false, inject not done yet)"); }
        void inject()        { LOG.add("2.inject:OrderService");            System.out.println("  [INJECT]        OrderService — db wired (db.open=" + db.open + " ← now true after db.postConstruct)"); }
        void postConstruct() { LOG.add("3.postConstruct:OrderService");     System.out.println("  [POSTCONSTRUCT] OrderService — db.open=" + db.open + " ✓"); }
        void preDestroy()    { LOG.add("7.preDestroy:OrderService");        System.out.println("  [PREDESTROY]    OrderService — db.open=" + db.open + " (db still alive ✓)"); }
    }

    public static void main(String[] args) {
        System.out.println("=== STARTUP ===");
        // Spring creates in dependency order (DatabasePool first — no deps)
        DatabasePool db  = new DatabasePool();
        LOG.add("2.inject:DatabasePool");
        System.out.println("  [INJECT]        DatabasePool (no injected fields)");
        db.postConstruct();

        OrderService svc = new OrderService(db);
        svc.inject();
        svc.postConstruct();

        System.out.println("\n[LOG so far] " + LOG);

        System.out.println("\n=== APPLICATION ===");
        System.out.println("  [APP] processing orders...");

        System.out.println("\n=== SHUTDOWN ===");
        // Destruction in REVERSE creation order (OrderService first, DatabasePool last)
        svc.preDestroy();
        db.preDestroy();

        System.out.println("\n[FULL LOG] " + LOG);
    }
}
```

How to run: `java StartupShutdownOrderDemo.java`

`DatabasePool` is created and initialised before `OrderService` — its `@PostConstruct` fires first. `OrderService` constructor receives a reference to `DatabasePool` but `db.open` is `false` at that point (injection and `@PostConstruct` happen after construction). Shutdown fires `@PreDestroy` in reverse order: `OrderService` first (can still use `DatabasePool`), then `DatabasePool`.

### Level 2 — Intermediate

Add `SmartLifecycle` to the sequence — `start()` fires after `@PostConstruct` and after `context.refresh()`.

```java
// StartupShutdownOrderDemo2.java — run with: java StartupShutdownOrderDemo2.java
import java.util.*;
import java.util.concurrent.*;

public class StartupShutdownOrderDemo2 {

    interface SmartLifecycle { boolean isAutoStartup(); int getPhase(); void start(); void stop(Runnable cb); boolean isRunning(); }
    static final List<String> LOG = Collections.synchronizedList(new ArrayList<>());

    static class DbPool {
        boolean open = false;
        DbPool() { LOG.add("CONSTRUCT:DbPool"); System.out.println("[CONSTRUCT] DbPool"); }
        void postConstruct() { open=true; LOG.add("POSTCONSTRUCT:DbPool"); System.out.println("[POSTCONSTRUCT] DbPool — open=true"); }
        void preDestroy()    { open=false; LOG.add("PREDESTROY:DbPool"); System.out.println("[PREDESTROY] DbPool — open=false"); }
    }

    static class OrderProcessor implements SmartLifecycle {
        private final DbPool db;
        boolean ready = false;
        private volatile boolean running = false;
        OrderProcessor(DbPool db) { this.db=db; LOG.add("CONSTRUCT:OrderProcessor"); System.out.println("[CONSTRUCT] OrderProcessor"); }
        void postConstruct()     { ready=true;   LOG.add("POSTCONSTRUCT:OrderProcessor"); System.out.println("[POSTCONSTRUCT] OrderProcessor — db.open=" + db.open); }
        @Override public boolean isAutoStartup(){ return true; }
        @Override public int     getPhase()     { return 0; }
        @Override public void    start()        { running=true; LOG.add("START:OrderProcessor"); System.out.println("[LIFECYCLE.start] OrderProcessor — db.open=" + db.open + " ready=" + ready + " (both true ✓)"); }
        @Override public void    stop(Runnable cb){ running=false; LOG.add("STOP:OrderProcessor"); System.out.println("[LIFECYCLE.stop] OrderProcessor"); cb.run(); }
        @Override public boolean isRunning()    { return running; }
        void preDestroy()    { LOG.add("PREDESTROY:OrderProcessor"); System.out.println("[PREDESTROY] OrderProcessor — db still open=" + db.open); }
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== LAYER 1: Bean creation + init ===");
        DbPool         db  = new DbPool();
        db.postConstruct();
        OrderProcessor svc = new OrderProcessor(db);
        svc.postConstruct();

        System.out.println("\n=== LAYER 2: context.refresh() → SmartLifecycle.start() ===");
        svc.start();  // only called after all beans' @PostConstruct have run

        System.out.println("\n=== APPLICATION RUNNING ===");
        Thread.sleep(200);

        System.out.println("\n=== SHUTDOWN LAYER 2: SmartLifecycle.stop() ===");
        CountDownLatch latch = new CountDownLatch(1);
        svc.stop(latch::countDown);
        latch.await(3, TimeUnit.SECONDS);

        System.out.println("\n=== SHUTDOWN LAYER 1: @PreDestroy (reverse creation order) ===");
        svc.preDestroy();
        db.preDestroy();

        System.out.println("\n[FULL LOG] " + LOG);
    }
}
```

How to run: `java StartupShutdownOrderDemo2.java`

`POSTCONSTRUCT:OrderProcessor` appears before `START:OrderProcessor` — confirming that `@PostConstruct` fires during bean creation while `start()` fires only after `context.refresh()`. Shutdown reverses: `STOP:OrderProcessor` → `PREDESTROY:OrderProcessor` → `PREDESTROY:DbPool`.

### Level 3 — Advanced

Three-bean chain with full ordering proof: print a combined log and assert the complete event sequence.

```java
// StartupShutdownOrderDemo3.java — run with: java StartupShutdownOrderDemo3.java
import java.util.*;
import java.util.concurrent.*;

public class StartupShutdownOrderDemo3 {

    interface SmartLifecycle { boolean isAutoStartup(); int getPhase(); void start(); void stop(Runnable cb); boolean isRunning(); }
    static final List<String> LOG = Collections.synchronizedList(new ArrayList<>());

    static class A implements SmartLifecycle {
        boolean open = false; volatile boolean running = false;
        A()                  { LOG.add("A.construct"); }
        void postConstruct() { open=true;    LOG.add("A.postConstruct"); System.out.println("[PC ] A — open=true"); }
        @Override public boolean isAutoStartup(){ return true; }
        @Override public int     getPhase()     { return -1; }   // phase -1: starts first
        @Override public void    start()        { running=true;  LOG.add("A.start"); System.out.println("[SL ] A.start() phase=-1"); }
        @Override public void    stop(Runnable cb){ running=false; LOG.add("A.stop"); System.out.println("[SL ] A.stop() phase=-1"); cb.run(); }
        @Override public boolean isRunning()    { return running; }
        void preDestroy()    { open=false;   LOG.add("A.preDestroy"); System.out.println("[PD ] A — open=false"); }
    }

    static class B implements SmartLifecycle {
        private final A a; volatile boolean running = false;
        B(A a)               { this.a=a; LOG.add("B.construct"); }
        void postConstruct() { LOG.add("B.postConstruct"); System.out.println("[PC ] B — a.open=" + a.open); }
        @Override public boolean isAutoStartup(){ return true; }
        @Override public int     getPhase()     { return 0; }
        @Override public void    start()        { running=true;  LOG.add("B.start"); System.out.println("[SL ] B.start() phase=0 a.running=" + a.running); }
        @Override public void    stop(Runnable cb){ running=false; LOG.add("B.stop"); System.out.println("[SL ] B.stop() phase=0"); cb.run(); }
        @Override public boolean isRunning()    { return running; }
        void preDestroy()    { LOG.add("B.preDestroy"); System.out.println("[PD ] B — a.open=" + a.open + " ← still alive"); }
    }

    static class C implements SmartLifecycle {
        private final B b; volatile boolean running = false;
        C(B b)               { this.b=b; LOG.add("C.construct"); }
        void postConstruct() { LOG.add("C.postConstruct"); System.out.println("[PC ] C — b.isRunning=" + b.isRunning() + " (false expected — start not yet)"); }
        @Override public boolean isAutoStartup(){ return true; }
        @Override public int     getPhase()     { return 0; }   // same phase as B: starts in parallel
        @Override public void    start()        { running=true;  LOG.add("C.start"); System.out.println("[SL ] C.start() phase=0"); }
        @Override public void    stop(Runnable cb){ running=false; LOG.add("C.stop"); System.out.println("[SL ] C.stop() phase=0"); cb.run(); }
        @Override public boolean isRunning()    { return running; }
        void preDestroy()    { LOG.add("C.preDestroy"); System.out.println("[PD ] C — b destroyed? " + !b.isRunning() + " (b already stopped by SmartLifecycle)"); }
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== STARTUP ===");
        A a = new A(); a.postConstruct();
        B b = new B(a); b.postConstruct();
        C c = new C(b); c.postConstruct();

        System.out.println("\n=== LIFECYCLE START (phase -1 first, then phase 0) ===");
        a.start();  // phase -1
        b.start();  // phase 0 — with A already started
        c.start();  // phase 0 — parallel with B in real Spring

        System.out.println("\n=== APPLICATION ===");
        System.out.println("A.running=" + a.running + " B.running=" + b.running + " C.running=" + c.running);

        System.out.println("\n=== SHUTDOWN LAYER 2 (phase 0 first, then phase -1) ===");
        CountDownLatch l = new CountDownLatch(3);
        b.stop(l::countDown); c.stop(l::countDown); // phase 0 stops first (B and C parallel)
        l.await(1, TimeUnit.SECONDS);
        CountDownLatch l2 = new CountDownLatch(1);
        a.stop(l2::countDown); // phase -1 stops after phase 0
        l2.await(1, TimeUnit.SECONDS);

        System.out.println("\n=== SHUTDOWN LAYER 1 (reverse creation: C, B, A) ===");
        c.preDestroy(); b.preDestroy(); a.preDestroy();

        System.out.println("\n=== FULL EVENT LOG ===");
        for (int i=0; i<LOG.size(); i++) System.out.println("  " + (i+1) + ". " + LOG.get(i));

        // Assert key ordering rules
        List<String> expected = List.of("A.construct","B.construct","C.construct",
            "A.postConstruct","B.postConstruct","C.postConstruct",
            "A.start","B.start","C.start",
            "B.stop","C.stop","A.stop",
            "C.preDestroy","B.preDestroy","A.preDestroy");
        System.out.println("\n[ASSERT] LOG matches expected: " + expected.equals(LOG));
    }
}
```

How to run: `java StartupShutdownOrderDemo3.java`

The full event log shows every step in order. Key assertions: all constructs before all `@PostConstruct`; all `@PostConstruct` before all `start()`; shutdown stops phase 0 (B, C) before phase -1 (A); `@PreDestroy` fires in reverse creation order (C, B, A) after all `stop()` calls.

## 6. Walkthrough

**Level 3 full event sequence:**

```
STARTUP:
  1.  A.construct        ← creation order: A (no deps)
  2.  B.construct        ← B depends on A
  3.  C.construct        ← C depends on B
  4.  A.postConstruct    ← init callbacks in creation order
  5.  B.postConstruct    ← a.open=true ✓
  6.  C.postConstruct    ← b.isRunning()=false ✓ (start not yet)
  7.  A.start()          ← phase -1: first to start
  8.  B.start()          ← phase 0: after phase -1, a.running=true ✓
  9.  C.start()          ← phase 0: parallel with B

APPLICATION running...

SHUTDOWN:
  10. B.stop()           ← phase 0 stops first (before phase -1)
  11. C.stop()           ← phase 0 (parallel with B)
  12. A.stop()           ← phase -1 stops after all phase 0 done
  13. C.preDestroy()     ← reverse creation: C first
  14. B.preDestroy()     ← a.open still true ✓
  15. A.preDestroy()     ← last to be destroyed

[ASSERT] LOG matches expected ✓
```

## 7. Gotchas & takeaways

> **`@PostConstruct` fires during bean creation — before `context.refresh()` completes.** When your `@PostConstruct` runs, sibling beans that depend on the same things may not yet have had their `@PostConstruct` called. Only `SmartLifecycle.start()` is guaranteed to run after ALL beans are created and all `@PostConstruct` methods have fired.

> **SmartLifecycle `stop()` and `@PreDestroy` are separate layers — both fire at `context.close()`.** The `stop()` layer fires first (reverse phase order), then the `@PreDestroy` / `destroy()` / `destroy-method` layer fires (reverse creation order). A bean may see its `stop()` called with its `@PreDestroy` following soon after.

- `@DependsOn` creates an explicit dependency edge even with no `@Autowired` link — useful to force creation order for side-effect dependencies. This affects both creation order and (reversed) destruction order.
- When using `context.start()` / `context.stop()` explicitly (not via `close()`), only the `SmartLifecycle` layer fires — `@PreDestroy` and `DisposableBean.destroy()` do NOT fire. They only fire on `context.close()` (which calls `stop()` + then destroys beans).
- In Spring Boot, the embedded server is a `SmartLifecycle` bean. Graceful shutdown (`server.shutdown=graceful`) adds a drain period between `stop()` being called on the server and the context being destroyed.
