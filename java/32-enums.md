# Java Enums

## Overview

An enum (enumeration) is a special class type that represents a fixed set of constants. Before enums (pre-Java 5), constants were defined as `public static final int` — called the "int enum pattern" — which had no type safety, no namespace, and no useful string form. Enums solve all of that. Every enum constant is implicitly `public static final` and is a full-blown instance of the enum class.

---

## 1. Basic Enum

### What it is

A named set of constants. The compiler generates a class extending `java.lang.Enum`. Each constant is a singleton instance of that class, created in declaration order.

### Visual Diagram

```
enum Day { MON, TUE, WED, THU, FRI, SAT, SUN }

          ordinal:  0    1    2    3    4    5    6
          name:   MON  TUE  WED  THU  FRI  SAT  SUN
                   ^                             ^
               values()[0]                 values()[6]
```

### Built-in methods

| Method | Returns | Description |
|---|---|---|
| `Day.values()` | `Day[]` | All constants in declaration order |
| `Day.valueOf("MON")` | `Day` | Constant by name; throws `IllegalArgumentException` if not found |
| `day.name()` | `String` | The constant's declared name |
| `day.ordinal()` | `int` | 0-based declaration index |
| `day.compareTo(other)` | `int` | Negative/zero/positive by ordinal difference |
| `day.toString()` | `String` | Same as `name()` by default |

### Code Example 1 — Declaration and basic methods

```java
enum Day { MON, TUE, WED, THU, FRI, SAT, SUN }

Day d = Day.WED;
System.out.println(d.name());       // WED
System.out.println(d.ordinal());    // 2
System.out.println(d.toString());   // WED

Day parsed = Day.valueOf("FRI");
System.out.println(parsed);         // FRI
```

**What this does:** Creates a `Day` constant, reads its name, ordinal, and reconstructs a constant from a string. `valueOf` is case-sensitive — `"fri"` would throw.

### Code Example 2 — Iterating with `values()`

```java
for (Day d : Day.values()) {
    System.out.printf("%s -> ordinal %d%n", d.name(), d.ordinal());
}
```

**What this does:** Prints every constant in declaration order with its ordinal. `values()` returns a new array each call — don't call in tight loops.

### Code Example 3 — Classic switch

```java
Day today = Day.SAT;
switch (today) {
    case SAT:
    case SUN:
        System.out.println("Weekend");
        break;
    default:
        System.out.println("Weekday");
}
```

**What this does:** Switches on enum constant. Note: no `Day.SAT` — inside a switch the type is already known.

### Code Example 4 — Enhanced switch (Java 14+)

```java
Day today = Day.MON;
String type = switch (today) {
    case MON, TUE, WED, THU, FRI -> "Weekday";
    case SAT, SUN                 -> "Weekend";
};
System.out.println(type); // Weekday
```

**What this does:** Arrow-case switch as expression. Exhaustive — no default needed when all constants covered.

### Dry Run — `values()` + `compareTo`

```
Day.values() → [MON, TUE, WED, THU, FRI, SAT, SUN]

MON.compareTo(WED)  → 0 - 2 = -2  (MON comes before WED)
SUN.compareTo(MON)  → 6 - 0 =  6  (SUN comes after MON)
FRI.compareTo(FRI)  → 4 - 4 =  0  (same)
```

> ⚠️ **Pitfall:** `ordinal()` is fragile — it changes if you reorder constants. Never persist ordinal values to a database. Use `name()` or a dedicated field instead.

> ⚠️ **Pitfall:** `valueOf(String)` is case-sensitive and throws `IllegalArgumentException` (not null) on no match. Wrap in try-catch or use a safe lookup.

---

## 2. Enum with Fields, Constructors, and Methods

### What it is

Each enum constant can carry data. You add a constructor (always implicitly private — you cannot call it externally) and fields. Each constant passes arguments to the constructor in its declaration.

### Visual Diagram

```
enum Planet {
    MERCURY (3.303e+23, 2.4397e6),   ← calls Planet(mass, radius)
    VENUS   (4.869e+24, 6.0518e6),
    EARTH   (5.976e+24, 6.37814e6);

    private final double mass;        ← per-constant data
    private final double radius;

    Planet(double mass, double radius) { ... }  ← private implicitly
}

MERCURY.mass   = 3.303e+23
EARTH.mass     = 5.976e+24   ← different data, same type
```

### Code Example 1 — Planet enum

```java
enum Planet {
    MERCURY(3.303e+23, 2.4397e6),
    VENUS  (4.869e+24, 6.0518e6),
    EARTH  (5.976e+24, 6.37814e6),
    MARS   (6.421e+23, 3.3972e6);

    private static final double G = 6.67300E-11;
    private final double mass;    // in kilograms
    private final double radius;  // in meters

    Planet(double mass, double radius) {
        this.mass   = mass;
        this.radius = radius;
    }

    double surfaceGravity() {
        return G * mass / (radius * radius);
    }

    double surfaceWeight(double otherMass) {
        return otherMass * surfaceGravity();
    }
}

double earthWeight = 75.0;
double mass = earthWeight / Planet.EARTH.surfaceGravity();
for (Planet p : Planet.values()) {
    System.out.printf("Weight on %s = %.2f%n", p, p.surfaceWeight(mass));
}
```

**What this does:** Each planet carries its own mass and radius. `surfaceWeight` uses the planet's own gravity. The static field `G` is shared across all constants (not per-constant).

### Code Example 2 — HTTP Status enum

```java
enum HttpStatus {
    OK(200, "OK"),
    NOT_FOUND(404, "Not Found"),
    INTERNAL_ERROR(500, "Internal Server Error");

    private final int code;
    private final String phrase;

    HttpStatus(int code, String phrase) {
        this.code   = code;
        this.phrase = phrase;
    }

    public int code()     { return code; }
    public String phrase(){ return phrase; }

    public boolean isError() { return code >= 400; }
}

System.out.println(HttpStatus.NOT_FOUND.code());     // 404
System.out.println(HttpStatus.OK.isError());         // false
System.out.println(HttpStatus.INTERNAL_ERROR.phrase()); // Internal Server Error
```

**What this does:** Bundles code + phrase together. `isError()` encodes domain logic directly on the enum — the enum knows about itself.

### Dry Run — surfaceGravity() for MERCURY

```
G      = 6.673e-11
mass   = 3.303e+23
radius = 2.4397e6

surfaceGravity = G * mass / (radius * radius)
               = 6.673e-11 * 3.303e+23 / (2.4397e6)^2
               = 2.202e+13 / 5.952e+12
               ≈ 3.70 m/s²

surfaceWeight(mass=75/9.8≈7.65) = 7.65 * 3.70 ≈ 28.3 N
```

> ⚠️ **Pitfall:** Enum constructors cannot be `public` or `protected`. Declaring `public Planet(...)` is a compile error. The JVM ensures constants are created exactly once at class-load time.

---

## 3. Abstract Methods Per Constant (Constant-Specific Class Bodies)

### What it is

Each enum constant can override an abstract method with its own implementation. The compiler generates an anonymous subclass for each constant that provides the body. This replaces large switch/if-else dispatch chains.

### Visual Diagram

```
enum Operation {
    PLUS   { double apply(x, y) { return x + y; } }   ← anonymous subclass
    MINUS  { double apply(x, y) { return x - y; } }   ← anonymous subclass
    TIMES  { double apply(x, y) { return x * y; } }   ← anonymous subclass
    DIVIDE { double apply(x, y) { return x / y; } }   ← anonymous subclass

    abstract double apply(double x, double y);          ← declared on enum
}

vs. the bad pattern:
switch (op) {
    case PLUS:  return x + y;   // adding a new op means editing this switch
    ...
}
```

### Code Example 1 — Operation enum

```java
enum Operation {
    PLUS   { @Override public double apply(double x, double y) { return x + y; } },
    MINUS  { @Override public double apply(double x, double y) { return x - y; } },
    TIMES  { @Override public double apply(double x, double y) { return x * y; } },
    DIVIDE { @Override public double apply(double x, double y) { return x / y; } };

    public abstract double apply(double x, double y);
}

double x = 4, y = 2;
for (Operation op : Operation.values()) {
    System.out.printf("%.1f %s %.1f = %.1f%n", x, op, y, op.apply(x, y));
}
// 4.0 PLUS 2.0 = 6.0
// 4.0 MINUS 2.0 = 2.0
// 4.0 TIMES 2.0 = 8.0
// 4.0 DIVIDE 2.0 = 2.0
```

**What this does:** Each constant carries its own `apply` logic. Adding a new operation means adding one constant — no existing code changes (Open/Closed Principle).

### Code Example 2 — Strategy-per-constant with a default

```java
enum PaymentMethod {
    CREDIT_CARD {
        @Override
        public double fee(double amount) { return amount * 0.03; }
    },
    DEBIT_CARD {
        @Override
        public double fee(double amount) { return 0.50; }
    },
    CASH {
        @Override
        public double fee(double amount) { return 0.0; }
    };

    public abstract double fee(double amount);
}

for (PaymentMethod m : PaymentMethod.values()) {
    System.out.printf("%s fee on $100: $%.2f%n", m, m.fee(100));
}
```

**What this does:** Each payment method encapsulates its own fee calculation. No switch statements needed anywhere in the codebase.

### Code Example 3 — Non-abstract with selective override

```java
enum DiscountStrategy {
    NONE {
        // uses default
    },
    SEASONAL {
        @Override
        public double discount(double price) { return price * 0.10; }
    },
    VIP {
        @Override
        public double discount(double price) { return price * 0.20; }
    };

    public double discount(double price) { return 0.0; } // default: no discount
}

System.out.println(DiscountStrategy.VIP.discount(100));      // 20.0
System.out.println(DiscountStrategy.NONE.discount(100));     // 0.0
```

**What this does:** Non-abstract base method provides a default. Only constants that differ need to override.

### Dry Run — Operation.DIVIDE.apply(10, 4)

```
constant = DIVIDE
apply(10, 4) dispatches to DIVIDE's anonymous subclass body:
  return x / y  →  return 10 / 4  →  2.5
```

> ⚠️ **Pitfall:** If you add a new abstract method to the enum, every existing constant body must implement it or you get a compile error. This is actually a feature — exhaustiveness enforcement.

---

## 4. Enum Implementing Interface

### What it is

Enums can implement interfaces (they cannot extend classes — they already implicitly extend `java.lang.Enum`). This is useful for polymorphic use of enums in APIs that take the interface type.

### Visual Diagram

```
interface Printable { void print(); }

enum Color implements Printable {
    RED, GREEN, BLUE;
    @Override public void print() { System.out.println("Color: " + this); }
}

Printable p = Color.RED;    ← enum constant used as interface type
p.print();                  → "Color: RED"
```

### Code Example 1 — Implementing a custom interface

```java
interface Describable {
    String describe();
}

enum Season implements Describable {
    SPRING {
        @Override public String describe() { return "Warm and blooming"; }
    },
    SUMMER {
        @Override public String describe() { return "Hot and sunny"; }
    },
    FALL {
        @Override public String describe() { return "Cool and colorful"; }
    },
    WINTER {
        @Override public String describe() { return "Cold and snowy"; }
    };
}

for (Season s : Season.values()) {
    System.out.println(s + ": " + s.describe());
}
```

**What this does:** Each season has its own description. The enum implements `Describable`, so it can be passed anywhere that interface is expected.

### Code Example 2 — Implementing Runnable

```java
enum Task implements Runnable {
    CLEANUP {
        @Override public void run() { System.out.println("Cleaning up..."); }
    },
    BACKUP {
        @Override public void run() { System.out.println("Running backup..."); }
    };
}

Thread t = new Thread(Task.CLEANUP);
t.start(); // Cleaning up...
```

**What this does:** Enum constants passed directly as `Runnable` to a Thread. No lambda or anonymous class needed.

### Code Example 3 — Interface with default method + enum

```java
interface Logger {
    void log(String message);
    default void warn(String message) {
        log("[WARN] " + message);
    }
}

enum LogLevel implements Logger {
    INFO  { @Override public void log(String m) { System.out.println("[INFO] "  + m); } },
    ERROR { @Override public void log(String m) { System.err.println("[ERROR] " + m); } };
}

LogLevel.INFO.warn("disk almost full");  // [INFO] [WARN] disk almost full
```

**What this does:** Default method from interface is inherited by all constants. Only `log` is abstract; `warn` is free.

> ⚠️ **Pitfall:** Enums cannot extend any class (they already extend `Enum`). If you need shared behavior, use an interface with default methods, or put the logic in a non-abstract enum method.

---

## 5. EnumSet

### What it is

`EnumSet` is a specialized `Set<E extends Enum<E>>` backed by a **bit vector** (a single `long` for enums with ≤64 constants). Each bit position corresponds to an ordinal. All operations — add, remove, contains, iteration — are O(1) bit manipulations. Much faster and more memory-efficient than `HashSet<MyEnum>`.

### Visual Diagram

```
enum Day { MON, TUE, WED, THU, FRI, SAT, SUN }
ordinal:    0    1    2    3    4    5    6

EnumSet.of(MON, WED, FRI):

bit vector:  1  0  1  0  1  0  0
             ^        ^     ^
            MON      WED   FRI

EnumSet.complementOf(above):

bit vector:  0  1  0  1  0  1  1
                ^     ^     ^  ^
               TUE  THU  SAT SUN
```

### Code Example 1 — Factory methods

```java
import java.util.EnumSet;

enum Day { MON, TUE, WED, THU, FRI, SAT, SUN }

EnumSet<Day> workdays  = EnumSet.range(Day.MON, Day.FRI);
EnumSet<Day> weekend   = EnumSet.of(Day.SAT, Day.SUN);
EnumSet<Day> all       = EnumSet.allOf(Day.class);
EnumSet<Day> none      = EnumSet.noneOf(Day.class);
EnumSet<Day> notMonday = EnumSet.complementOf(EnumSet.of(Day.MON));

System.out.println(workdays);   // [MON, TUE, WED, THU, FRI]
System.out.println(weekend);    // [SAT, SUN]
System.out.println(notMonday);  // [TUE, WED, THU, FRI, SAT, SUN]
```

**What this does:** Shows all major factory methods. `range` is inclusive on both ends. `complementOf` flips all bits.

### Code Example 2 — Set operations

```java
EnumSet<Day> workdays = EnumSet.range(Day.MON, Day.FRI);
EnumSet<Day> meeting  = EnumSet.of(Day.TUE, Day.THU);

// Intersection (days with meetings)
EnumSet<Day> temp = EnumSet.copyOf(workdays);
temp.retainAll(meeting);
System.out.println("Meeting days: " + temp); // [TUE, THU]

// Union
EnumSet<Day> union = EnumSet.copyOf(workdays);
union.addAll(EnumSet.of(Day.SAT));
System.out.println("Extended week: " + union); // [MON, TUE, WED, THU, FRI, SAT]
```

**What this does:** `copyOf` prevents mutation of the original. All set operations work on bit vectors — single CPU instruction per operation.

### Code Example 3 — copyOf from Collection

```java
List<Day> list = List.of(Day.MON, Day.WED, Day.FRI);
EnumSet<Day> fromList = EnumSet.copyOf(list);
System.out.println(fromList); // [MON, WED, FRI]
```

**What this does:** Converts any non-empty `Collection<Day>` to `EnumSet`. Note: the collection must not be empty — `copyOf` from an empty collection throws `IllegalArgumentException`. Use `noneOf` then `addAll` for that case.

### Dry Run — EnumSet bit vector operations

```
Day ordinals: MON=0, TUE=1, WED=2, THU=3, FRI=4, SAT=5, SUN=6

EnumSet.of(MON, WED, FRI):
  bit mask = 0b0010101  (bits 0, 2, 4 set)

EnumSet.of(TUE, THU):
  bit mask = 0b0001010  (bits 1, 3 set)

intersection (retainAll):
  0b0010101
& 0b0001010
= 0b0000000  → empty set

EnumSet.allOf(Day.class):
  bit mask = 0b1111111  (all 7 bits set)

complementOf(allOf - SUN):
  ~0b0111111 & 0b1111111 = 0b1000000  → {SUN}
```

> ⚠️ **Pitfall:** `EnumSet.copyOf(emptyCollection)` throws `IllegalArgumentException`. Use `EnumSet.noneOf(Day.class)` for an empty set.

> ⚠️ **Pitfall:** `EnumSet` is not thread-safe. Wrap with `Collections.synchronizedSet(enumSet)` if shared across threads.

---

## 6. EnumMap

### What it is

`EnumMap<K extends Enum<K>, V>` is a specialized `Map` backed by an **array indexed by ordinal**. Key lookups are `array[key.ordinal()]` — O(1) with zero hashing overhead. More compact and faster than `HashMap<MyEnum, V>`.

### Visual Diagram

```
enum Day { MON=0, TUE=1, WED=2, THU=3, FRI=4, SAT=5, SUN=6 }

EnumMap<Day, String> schedule = new EnumMap<>(Day.class);
schedule.put(Day.MON, "Standup");
schedule.put(Day.FRI, "Retro");

Internal array:
index: [ 0       | 1    | 2    | 3    | 4      | 5    | 6    ]
key:   [ MON     | TUE  | WED  | THU  | FRI    | SAT  | SUN  ]
value: ["Standup"| null | null | null | "Retro"| null | null ]

get(Day.FRI) → array[4] → "Retro"   ← O(1), no hashing
```

### Code Example 1 — Counting with EnumMap

```java
import java.util.EnumMap;

enum Priority { LOW, MEDIUM, HIGH, CRITICAL }

List<Priority> tickets = List.of(
    Priority.HIGH, Priority.LOW, Priority.MEDIUM,
    Priority.HIGH, Priority.CRITICAL, Priority.HIGH
);

EnumMap<Priority, Integer> counts = new EnumMap<>(Priority.class);
for (Priority p : tickets) {
    counts.merge(p, 1, Integer::sum);
}

System.out.println(counts);
// {LOW=1, MEDIUM=1, HIGH=3, CRITICAL=1}  ← always in declaration order
```

**What this does:** Counts occurrences per priority. Result is always in enum declaration order — a bonus over HashMap.

### Code Example 2 — Schedule builder

```java
EnumMap<Day, List<String>> schedule = new EnumMap<>(Day.class);
schedule.put(Day.MON, List.of("Standup", "Planning"));
schedule.put(Day.WED, List.of("Design Review"));
schedule.put(Day.FRI, List.of("Retro", "Demo"));

schedule.forEach((day, events) ->
    System.out.println(day + ": " + events)
);
```

**What this does:** Maps each day to a list of events. `forEach` iterates in declaration order (MON to SUN), not insertion order — unlike HashMap.

### Code Example 3 — getOrDefault and computeIfAbsent

```java
EnumMap<Day, List<String>> tasks = new EnumMap<>(Day.class);

// Safe add without pre-checking
tasks.computeIfAbsent(Day.TUE, k -> new ArrayList<>()).add("Code Review");
tasks.computeIfAbsent(Day.TUE, k -> new ArrayList<>()).add("PR Merge");

System.out.println(tasks.getOrDefault(Day.MON, List.of("No tasks")));
System.out.println(tasks.get(Day.TUE)); // [Code Review, PR Merge]
```

**What this does:** `computeIfAbsent` initializes the list on first access. `getOrDefault` avoids null checks.

> ⚠️ **Pitfall:** `EnumMap` does not allow null keys. Null values are permitted. Using a null key throws `NullPointerException`.

> ⚠️ **Pitfall:** EnumMap iterates in **declaration order** — this is guaranteed, unlike HashMap. Don't rely on this in APIs that might switch to HashMap later.

---

## 7. Singleton Enum Pattern

### What it is

An enum with a single constant is the simplest, most robust singleton in Java (Effective Java, Item 3). The JVM guarantees each constant is instantiated exactly once. Immune to reflection attacks (unlike class-based singletons) and handles serialization correctly without any extra code.

### Visual Diagram

```
Classic singleton problems:
  ┌─────────────────────────────────────────────────────────┐
  │ Reflection: Constructor.setAccessible(true) → new copy  │  ← broken
  │ Serialization: readObject() → new instance              │  ← broken
  │ Double-checked locking: subtle memory model bugs         │  ← tricky
  └─────────────────────────────────────────────────────────┘

Enum singleton:
  ┌─────────────────────────────────────────────────────────┐
  │ enum DatabaseConnection { INSTANCE; ... }               │
  │                                                         │
  │ JVM: creates INSTANCE once, at class-load time          │
  │ Reflection: Enum constructor cannot be called (JVM rule)│  ← safe
  │ Serialization: enum constants are singletons by spec    │  ← safe
  └─────────────────────────────────────────────────────────┘
```

### Code Example 1 — Minimal enum singleton

```java
public enum AppConfig {
    INSTANCE;

    private final String dbUrl    = "jdbc:postgresql://localhost/mydb";
    private final int    poolSize = 10;

    public String getDbUrl()    { return dbUrl; }
    public int    getPoolSize() { return poolSize; }
}

// Usage:
AppConfig config = AppConfig.INSTANCE;
System.out.println(config.getDbUrl()); // jdbc:postgresql://localhost/mydb

// Same instance everywhere:
System.out.println(AppConfig.INSTANCE == AppConfig.INSTANCE); // true
```

**What this does:** `INSTANCE` is created once when the class loads. Any code calling `AppConfig.INSTANCE` gets the identical object reference.

### Code Example 2 — Registry singleton with state

```java
public enum ServiceRegistry {
    INSTANCE;

    private final Map<String, Object> services = new HashMap<>();

    public void register(String name, Object service) {
        services.put(name, service);
    }

    @SuppressWarnings("unchecked")
    public <T> T lookup(String name) {
        return (T) services.get(name);
    }
}

// In bootstrap:
ServiceRegistry.INSTANCE.register("emailService", new EmailService());

// Anywhere in the app:
EmailService es = ServiceRegistry.INSTANCE.lookup("emailService");
```

**What this does:** A global service locator backed by the enum singleton guarantee. No synchronization needed for the `INSTANCE` reference itself (though the map's mutations may need it in concurrent code).

### Code Example 3 — Compare singleton approaches

```java
// 1. Eager class singleton — reflection breaks it
public class BadSingleton {
    private static final BadSingleton INSTANCE = new BadSingleton();
    private BadSingleton() {}
    public static BadSingleton getInstance() { return INSTANCE; }
    // Attack: BadSingleton.class.getDeclaredConstructors()[0].setAccessible(true) → new instance
}

// 2. Enum singleton — reflection-proof
public enum GoodSingleton {
    INSTANCE;
    // Attack attempt: GoodSingleton.class.getDeclaredConstructors()[0].newInstance(...)
    // → throws IllegalArgumentException: "Cannot reflectively create enum objects"
}

// 3. Serialization test
// Class singleton: must implement readResolve() or readObject() creates a new instance
// Enum singleton: JVM spec §8.9 guarantees enum constants are serialized by name only
//                 and deserialized by looking up the existing constant — always same instance
```

**What this does:** Shows why enum wins. The JVM itself blocks reflective enum instantiation. Serialization round-trips return the same constant.

### Code Example 4 — Enum singleton implementing interface

```java
public interface DatabaseConnection {
    void connect();
    void disconnect();
    boolean isConnected();
}

public enum ProdDatabase implements DatabaseConnection {
    INSTANCE;

    private boolean connected = false;

    @Override public void connect()    { connected = true;  System.out.println("Connected"); }
    @Override public void disconnect() { connected = false; System.out.println("Disconnected"); }
    @Override public boolean isConnected() { return connected; }
}

// Test code can use the DatabaseConnection interface with a mock
DatabaseConnection db = ProdDatabase.INSTANCE;
db.connect();
System.out.println(db.isConnected()); // true
```

**What this does:** Combines singleton and interface. Test code can inject a mock `DatabaseConnection` without changing production code.

> ⚠️ **Pitfall:** Enum singletons are initialized at class-load time. If initialization throws (e.g., config file missing), you get `ExceptionInInitializerError` — not a clean startup failure. Put risky init in a method, not in field initializers.

> ⚠️ **Pitfall:** Enum singletons cannot be subclassed. If you later need different implementations per environment (prod/test), use the interface approach (Code Example 4) from day one.

---

## Summary Cheat-Sheet

```
Basic enum:
  Day.values()           → Day[]        (all constants)
  Day.valueOf("MON")     → Day.MON      (by name, throws if missing)
  d.name()               → "MON"
  d.ordinal()            → 0
  d.compareTo(other)     → ordinal diff

Enum with fields:
  constructor always private/package
  fields final, set in constructor per-constant
  static fields shared across all constants

Abstract methods:
  each constant has its own anonymous subclass
  no switch/if-else dispatch needed

Interface:
  enum implements Interface — allowed
  enum extends Class       — NOT allowed (already extends Enum)

EnumSet:
  backed by bit vector — O(1) everything
  EnumSet.of, range, allOf, noneOf, complementOf, copyOf
  NOT thread-safe

EnumMap:
  backed by array[ordinal] — O(1) everything
  always iterates in declaration order
  null keys NOT allowed

Singleton:
  enum INSTANCE — reflection-safe, serialization-safe, simple
```
