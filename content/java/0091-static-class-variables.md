---
card: java
gi: 91
slug: static-class-variables
title: Static (class) variables
---

## 1. What it is

A static variable (also called a class variable) is declared with the `static` keyword inside a class body. Unlike instance fields, there is exactly one copy shared across all instances of the class and accessible directly via the class name. Static fields are initialised once when the class is first loaded by the JVM, before any instance is created.

```java
class Counter {
    static int count = 0;        // one copy, shared by all Counter objects
    int        id;               // each object has its own id

    Counter() {
        id = ++count;            // id is per-instance; count is class-wide
    }
}
// Counter.count == 3 after creating three Counter objects
```

## 2. Why & when

Use `static` fields when:
- **Constants** — `static final double PI = 3.14159;` — a value the same for every instance.
- **Shared state / counters** — tracking how many objects have been created, a shared cache, a registry.
- **Singleton resources** — a single connection pool, a shared logger instance.
- **Factory methods** — static fields that hold cached singletons returned by `getInstance()`.

Avoid mutable static state in multi-threaded code without explicit synchronisation — it is a global variable and all threads share it.

## 3. Core concept

```java
public class StaticFields {

    // ---- static final: constants ----
    static final double  TAX_RATE   = 0.08;
    static final String  APP_NAME   = "MyApp";
    static final int     MAX_USERS  = 1_000;

    // ---- Mutable static field ----
    static int instanceCount = 0;
    static long totalCreated  = 0L;

    // ---- Static initializer block ----
    static {
        System.out.println("Class loaded: " + APP_NAME);
        // Complex setup that can't be done in a field initializer
    }

    // ---- Instance fields ----
    final int id;
    String    name;

    StaticFields(String name) {
        instanceCount++;
        totalCreated++;
        this.id   = (int) totalCreated;
        this.name = name;
    }

    void destroy() {
        instanceCount--;   // simulate removal from active set
    }

    public static void main(String[] args) {
        System.out.println("TAX_RATE  : " + TAX_RATE);
        System.out.println("MAX_USERS : " + MAX_USERS);
        System.out.println("count before: " + StaticFields.instanceCount);

        var a = new StaticFields("Alice");
        var b = new StaticFields("Bob");
        var c = new StaticFields("Carol");

        System.out.println("count after 3 creates: " + StaticFields.instanceCount);
        System.out.println("total ever created   : " + StaticFields.totalCreated);

        b.destroy();
        System.out.println("count after 1 destroy: " + StaticFields.instanceCount);

        // Access via instance reference (works but discouraged — use class name)
        System.out.println("via instance ref     : " + a.instanceCount);  // same value

        // Static fields per-class — not per-instance
        System.out.printf("a.id=%d  b.id=%d  c.id=%d%n", a.id, b.id, c.id);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Static field: one shared copy in class metadata vs per-instance copies in heap objects; arrows from three objects to the single static field">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>

  <!-- Class/static area -->
  <rect x="16" y="18" width="240" height="133" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="136" y="36" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">Counter (class area)</text>
  <text x="136" y="50" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">loaded once by JVM</text>
  <line x1="26" y1="56" x2="246" y2="56" stroke="#8b949e" stroke-width="0.5"/>
  <rect x="30" y="64" width="200" height="24" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="130" y="80" fill="#6db33f" font-family="monospace" font-size="9" text-anchor="middle">static int count = 3</text>
  <text x="136" y="108" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">shared — one copy</text>
  <text x="136" y="121" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Counter.count</text>
  <text x="136" y="134" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">accessible without an instance</text>

  <!-- Three heap objects pointing to static -->
  <rect x="280" y="18" width="130" height="50" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="345" y="35" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">obj1 (heap)</text>
  <text x="290" y="50" fill="#e6edf3" font-size="7.5" font-family="monospace">int id = 1</text>
  <text x="290" y="63" fill="#8b949e" font-size="7.5" font-family="monospace">count → shared</text>

  <rect x="280" y="80" width="130" height="50" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="345" y="97" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">obj2 (heap)</text>
  <text x="290" y="112" fill="#e6edf3" font-size="7.5" font-family="monospace">int id = 2</text>
  <text x="290" y="125" fill="#8b949e" font-size="7.5" font-family="monospace">count → shared</text>

  <rect x="280" y="128" width="130" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="345" y="145" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">obj3: id=3</text>

  <!-- Arrows to static -->
  <line x1="280" y1="75"  x2="246" y2="76"  stroke="#6db33f" stroke-width="1" stroke-dasharray="3"/>
  <line x1="280" y1="105" x2="246" y2="76"  stroke="#6db33f" stroke-width="1" stroke-dasharray="3"/>
  <line x1="280" y1="143" x2="246" y2="76"  stroke="#6db33f" stroke-width="1" stroke-dasharray="3"/>

  <!-- Constants box -->
  <rect x="432" y="18" width="242" height="133" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="553" y="36" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">static final — constants</text>
  <line x1="442" y1="42" x2="664" y2="42" stroke="#8b949e" stroke-width="0.5"/>
  <text x="442" y="57" fill="#e6edf3" font-size="8" font-family="monospace">static final double PI = 3.14;</text>
  <text x="442" y="71" fill="#e6edf3" font-size="8" font-family="monospace">static final String NAME = "X";</text>
  <text x="442" y="87" fill="#8b949e" font-size="7.5" font-family="sans-serif">Naming: UPPER_SNAKE_CASE</text>
  <text x="442" y="100" fill="#8b949e" font-size="7.5" font-family="sans-serif">Access: ClassName.CONSTANT</text>
  <line x1="442" y1="107" x2="664" y2="107" stroke="#8b949e" stroke-width="0.5"/>
  <text x="442" y="121" fill="#6db33f" font-size="7.5" font-family="monospace">static initializer block:</text>
  <text x="442" y="134" fill="#8b949e" font-size="7.5" font-family="monospace">static { /* complex init */ }</text>
</svg>

One static field copy lives in the class area; all instances see and share the same value — changing it from any instance (or the class name) affects every reference to it.

## 5. Runnable example

Scenario: an object registry that counts active instances and tracks the total ever created — static fields drive the registry, while instance fields hold per-object identity. The example grows from a simple counter, to a thread-safe atomic counter, to a full registry with static initializer.

### Level 1 — Basic

```java
public class StaticFieldsBasic {

    // static fields — shared across all instances
    static int    activeCount  = 0;
    static long   totalCreated = 0L;
    static final  String SYSTEM_NAME = "ObjectRegistry";

    // instance field — per-object
    final int id;
    final String label;

    StaticFieldsBasic(String label) {
        totalCreated++;
        activeCount++;
        this.id    = (int) totalCreated;
        this.label = label;
    }

    void deregister() {
        activeCount--;
        System.out.println("Deregistered: " + this);
    }

    @Override public String toString() {
        return "[" + id + "] " + label;
    }

    public static void main(String[] args) {
        System.out.println("System: " + SYSTEM_NAME);
        System.out.printf("active=%d  total=%d%n", activeCount, totalCreated);

        var a = new StaticFieldsBasic("Alpha");
        var b = new StaticFieldsBasic("Beta");
        var c = new StaticFieldsBasic("Gamma");

        System.out.printf("After creating 3: active=%d  total=%d%n",
            activeCount, totalCreated);

        b.deregister();
        System.out.printf("After deregister: active=%d  total=%d%n",
            activeCount, totalCreated);

        // Access via class name (preferred) vs instance reference (legal but misleading)
        System.out.println("StaticFieldsBasic.activeCount = " + StaticFieldsBasic.activeCount);
        System.out.println("a.activeCount (same value)    = " + a.activeCount);
    }
}
```

**How to run:** `java StaticFieldsBasic.java`

`totalCreated` and `activeCount` are static — every `new StaticFieldsBasic(...)` call increments the same variables regardless of which instance's constructor runs. `a.activeCount` and `StaticFieldsBasic.activeCount` refer to the same field; using the class name is preferred because it makes the static nature explicit. `SYSTEM_NAME` is `static final` — a constant in UPPER_SNAKE_CASE that is the same for every instance.

### Level 2 — Intermediate

Same registry: use a static `Map` to store live instances by ID, a static initializer block to set up the registry metadata, and show that modifying the map through any reference updates the single shared map.

```java
import java.util.*;

public class StaticFieldsIntermediate {

    // Static final map — one map object shared by all instances
    static final Map<Integer, StaticFieldsIntermediate> REGISTRY = new LinkedHashMap<>();
    static int nextId = 1;

    // Static initializer block — runs once when class is loaded
    static {
        System.out.println("[class loaded] REGISTRY initialised");
    }

    final int    id;
    final String name;
    boolean      active;

    StaticFieldsIntermediate(String name) {
        this.id     = nextId++;
        this.name   = name;
        this.active = true;
        REGISTRY.put(this.id, this);   // register self in the shared map
    }

    void disable() {
        active = false;
        // Note: still in REGISTRY — caller must decide to remove
    }

    static void printRegistry() {
        System.out.printf("%-4s  %-8s  %s%n", "ID", "Name", "Active");
        System.out.println("-".repeat(24));
        REGISTRY.forEach((id, obj) ->
            System.out.printf("%-4d  %-8s  %b%n", id, obj.name, obj.active));
        System.out.println("Total: " + REGISTRY.size());
    }

    public static void main(String[] args) {
        new StaticFieldsIntermediate("Alpha");
        new StaticFieldsIntermediate("Beta");
        new StaticFieldsIntermediate("Gamma");

        System.out.println("=== After creation ===");
        printRegistry();

        REGISTRY.get(2).disable();
        REGISTRY.remove(3);

        System.out.println("\n=== After update ===");
        printRegistry();
    }
}
```

**How to run:** `java StaticFieldsIntermediate.java`

The `static { }` initializer block runs exactly once when the JVM first loads `StaticFieldsIntermediate`. `REGISTRY` is `static final` — the reference itself cannot be reassigned, but the `LinkedHashMap` it points to is mutable. `REGISTRY.put(this.id, this)` inside the constructor registers each new instance in the single shared map. `REGISTRY.get(2).disable()` modifies the instance in the registry, and `REGISTRY.remove(3)` removes the third entry — all acting on the same shared map.

### Level 3 — Advanced

Same registry: demonstrate thread-safe static state using `AtomicInteger`, a static factory pattern, and the risk of static mutable state in multi-threaded code without synchronisation.

```java
import java.util.concurrent.atomic.AtomicInteger;
import java.util.*;

public class StaticFieldsAdvanced {

    // Thread-safe counter (AtomicInteger replaces plain static int for multi-thread)
    private static final AtomicInteger ID_GEN  = new AtomicInteger(0);
    private static final AtomicInteger ACTIVE   = new AtomicInteger(0);
    private static final List<String>  EVENT_LOG = Collections.synchronizedList(new ArrayList<>());

    // Immutable constants
    static final String VERSION = "2.0";
    static final int    MAX     = 10;

    private final int    id;
    private final String name;
    private       boolean alive;

    // Private constructor — factory-only creation
    private StaticFieldsAdvanced(String name) {
        this.id    = ID_GEN.incrementAndGet();
        this.name  = name;
        this.alive = true;
        ACTIVE.incrementAndGet();
        EVENT_LOG.add("CREATED id=" + id + " name=" + name);
    }

    // Static factory method
    static StaticFieldsAdvanced create(String name) {
        if (ACTIVE.get() >= MAX) throw new IllegalStateException("Registry full");
        return new StaticFieldsAdvanced(name);
    }

    void destroy() {
        if (!alive) return;
        alive = false;
        ACTIVE.decrementAndGet();
        EVENT_LOG.add("DESTROYED id=" + id);
    }

    public static void main(String[] args) {
        System.out.println("Version: " + VERSION);

        var a = StaticFieldsAdvanced.create("Alpha");
        var b = StaticFieldsAdvanced.create("Beta");
        var c = StaticFieldsAdvanced.create("Gamma");

        System.out.printf("Active: %d  Total IDs generated: %d%n",
            ACTIVE.get(), ID_GEN.get());

        b.destroy();
        System.out.printf("After destroy: active=%d%n", ACTIVE.get());

        System.out.println("\nEvent log:");
        EVENT_LOG.forEach(e -> System.out.println("  " + e));

        // Static field risk in multi-threaded code (demonstration — single thread here)
        System.out.println("\nThread: " + Thread.currentThread().getName()
            + "  active=" + ACTIVE.get());
    }
}
```

**How to run:** `java StaticFieldsAdvanced.java`

`AtomicInteger.incrementAndGet()` and `decrementAndGet()` are atomic operations — safe when multiple threads increment the counter simultaneously (unlike `++` on a plain `int`, which is read-modify-write and can lose increments under concurrency). `Collections.synchronizedList` wraps the `ArrayList` so that individual `add` calls are thread-safe. The private constructor and static `create` factory enforce the maximum-active constraint — no external code can bypass the check by calling `new` directly.

## 6. Walkthrough

Execution trace through `StaticFieldsAdvanced.main`:

**Class loading.** When `StaticFieldsAdvanced` is first referenced, the JVM runs static field initializers: `ID_GEN = new AtomicInteger(0)`, `ACTIVE = new AtomicInteger(0)`, `EVENT_LOG = synchronizedList(new ArrayList<>())`.

**`create("Alpha")`.** `ACTIVE.get() = 0 < MAX=10` — check passes. `new StaticFieldsAdvanced("Alpha")`: `ID_GEN.incrementAndGet()` → `1` (atomic). `ACTIVE.incrementAndGet()` → `1`. Event `"CREATED id=1 name=Alpha"` appended. Returns `a` with `id=1`.

**`b.destroy()`.** `alive = true` → set to `false`. `ACTIVE.decrementAndGet()` → `2`. Event `"DESTROYED id=2"` appended. `ID_GEN` is not decremented — IDs are monotonically increasing and never reused.

**Event log order.** CREATED Alpha, CREATED Beta, CREATED Gamma, DESTROYED Beta — the `synchronizedList` preserves insertion order while preventing concurrent list corruption.

```
Static field lifecycle:
  JVM loads class → static fields initialised once
  create("Alpha") → ID_GEN: 0→1, ACTIVE: 0→1, log: +CREATED
  create("Beta")  → ID_GEN: 1→2, ACTIVE: 1→2, log: +CREATED
  create("Gamma") → ID_GEN: 2→3, ACTIVE: 2→3, log: +CREATED
  b.destroy()     → ACTIVE: 3→2, log: +DESTROYED
```

## 7. Gotchas & takeaways

> **Mutable static fields are global state and are not thread-safe without synchronisation.** A plain `static int counter` incremented from multiple threads can lose increments. Use `AtomicInteger` for counters, `ConcurrentHashMap` for shared maps, or `synchronized` methods to protect complex invariants.

> **Accessing a static field via an instance reference (`obj.CONSTANT`) is legal but misleading.** It looks like the value is per-object when it is actually class-wide. Always access static members via the class name (`ClassName.FIELD`) so the static nature is immediately visible to readers.

- Static fields have exactly one copy in the JVM, shared by all instances and accessible before any instance exists.
- `static final` fields are constants; name them in UPPER_SNAKE_CASE.
- Static initializer blocks `static { }` run once when the class is loaded — useful for complex setup that cannot be done in a field initializer.
- Mutable static state introduces global shared mutable state, making code harder to test and safe only with proper synchronisation.
- Use `AtomicInteger`, `AtomicLong`, `ConcurrentHashMap`, etc. when static fields are shared across threads.
- Access static members via `ClassName.field`, not `instance.field`.
