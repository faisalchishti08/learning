# Java Nested Classes

A **nested class** is a class defined inside another class or method. Java has four varieties, each with different scoping rules, access capabilities, and use cases.

```
Nested Class Types
──────────────────────────────────────────────────────────────────
class Outer {
    static class StaticNested { }     // 1. Static nested class
    class Inner { }                   // 2. Inner class (non-static)

    void method() {
        class Local { }              // 3. Local class (inside method)
        Runnable r = new Runnable()  // 4. Anonymous class
            { public void run(){} };
    }
}
```

---

## 1. Static Nested Class

### What and Why

A **static nested class** is declared with the `static` keyword inside an outer class. It has no implicit reference to any outer class instance — it behaves like a regular top-level class that happens to live inside another class's namespace.

**Why it exists:** Grouping. When a helper class is logically tied to the outer class but doesn't need access to outer instance state, declaring it static nested keeps the code organized without the overhead of an outer-instance reference.

**Key access rule:** static nested class can access the outer class's `static` members (including private ones), but **not** instance members.

```
┌───────────────────────────────────────────────────────┐
│                  Outer                                 │
│   static int outerStatic = 10;                        │
│   int outerInstance = 20;                             │
│                                                       │
│   ┌──────────────────────────────────────────┐       │
│   │         static class Nested              │       │
│   │   // CAN access: outerStatic             │       │
│   │   // CANNOT access: outerInstance        │       │
│   │   // No hidden reference to Outer        │       │
│   └──────────────────────────────────────────┘       │
└───────────────────────────────────────────────────────┘

Instantiation: new Outer.Nested()    ← no Outer instance needed
```

### Example 1 — Basic static nested class

```java
class University {
    private static String name = "MIT";
    private int studentCount = 50000;    // instance field

    static class Department {
        private String deptName;

        Department(String name) { this.deptName = name; }

        void display() {
            System.out.println(University.name + " — " + deptName);
            // System.out.println(studentCount);  // COMPILE ERROR — instance member
        }
    }
}

// Usage — no University instance needed
University.Department cs = new University.Department("Computer Science");
cs.display();   // MIT — Computer Science
```

**What this does:** `Department` is created directly with `new University.Department(...)`. It accesses the `static` field `name` (including `private`) but cannot touch `studentCount` because that requires an outer instance.

> ⚠️ **Pitfall:** People confuse static nested class with inner class. The `static` keyword is the key difference. Remove `static` and suddenly `Department` gets an implicit reference to `University` instance, has access to `studentCount`, and must be instantiated via `universityInstance.new Department(...)`.

---

### Example 2 — Builder pattern (canonical static nested use case)

```java
class HttpRequest {
    private final String url;
    private final String method;
    private final int timeoutMs;
    private final boolean followRedirects;

    private HttpRequest(Builder b) {      // private — only Builder can create
        this.url = b.url;
        this.method = b.method;
        this.timeoutMs = b.timeoutMs;
        this.followRedirects = b.followRedirects;
    }

    @Override
    public String toString() {
        return method + " " + url + " (timeout=" + timeoutMs + "ms, redirects=" + followRedirects + ")";
    }

    static class Builder {               // static nested — no HttpRequest instance needed to build
        private String url;
        private String method   = "GET";
        private int timeoutMs   = 5000;
        private boolean followRedirects = true;

        Builder(String url) { this.url = url; }

        Builder method(String m)          { this.method = m; return this; }
        Builder timeoutMs(int t)          { this.timeoutMs = t; return this; }
        Builder followRedirects(boolean f){ this.followRedirects = f; return this; }

        HttpRequest build() { return new HttpRequest(this); }
    }
}

// Usage
HttpRequest req = new HttpRequest.Builder("https://api.example.com/data")
    .method("POST")
    .timeoutMs(3000)
    .followRedirects(false)
    .build();
System.out.println(req);
// POST https://api.example.com/data (timeout=3000ms, redirects=false)
```

**What this does:** `Builder` is static nested — you call `new HttpRequest.Builder(url)` without any `HttpRequest` instance existing yet. That's essential: the builder's job is *to create* the outer object, so it can't depend on one already existing.

#### Dry Run — Builder chain

| Step | Call | Builder State |
|------|------|---------------|
| 1 | `new Builder("https://...")` | `url=https://...`, `method=GET`, `timeout=5000`, `redirects=true` |
| 2 | `.method("POST")` | `method=POST` — returns `this` |
| 3 | `.timeoutMs(3000)` | `timeoutMs=3000` — returns `this` |
| 4 | `.followRedirects(false)` | `followRedirects=false` — returns `this` |
| 5 | `.build()` | `new HttpRequest(this)` — copies all fields |

---

### Example 3 — `Map.Entry` style: static nested as data container

```java
class Graph {
    private static int nodeCount = 0;

    static class Edge {
        final int from;
        final int to;
        final double weight;

        Edge(int from, int to, double weight) {
            this.from = from;
            this.to = to;
            this.weight = weight;
        }

        @Override
        public String toString() {
            return from + " -[" + weight + "]-> " + to;
        }

        static Edge unweighted(int from, int to) {  // static method on static nested: fine
            return new Edge(from, to, 1.0);
        }
    }
}

Graph.Edge e1 = new Graph.Edge(1, 2, 3.5);
Graph.Edge e2 = Graph.Edge.unweighted(2, 3);
System.out.println(e1);  // 1 -[3.5]-> 2
System.out.println(e2);  // 2 -[1.0]-> 3
```

**What this does:** `Graph.Edge` is a simple value-carrying structure. It lives logically inside `Graph` but needs no `Graph` instance to exist. This mirrors `java.util.Map.Entry`.

---

## 2. Inner Class (Non-Static)

### What and Why

An **inner class** (non-static nested class) holds an implicit reference to the instance of its enclosing outer class. Every inner class instance is bound to exactly one outer instance. This gives the inner class full access to all of the outer's members — even `private` fields and methods.

**Why it exists:** Situations where a helper class is so tightly coupled to a specific outer *instance* that it needs to read and modify that instance's state directly. The classic example: an `Iterator` for a custom collection.

```
┌────────────────────────────────────────────────────────────────┐
│                    Outer instance  (heap object)               │
│  int data = 42;                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          Inner instance (separate heap object)            │  │
│  │  [hidden field: Outer.this ──────────────────────────────┼──┤
│  │  can read/write Outer.data directly                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘

Instantiation: outer.new Inner()    ← requires an Outer instance
Access outer: Outer.this.fieldName  ← disambiguation syntax
```

### Example 1 — Inner class accessing outer's private fields

```java
class BankAccount {
    private double balance;
    private String owner;

    BankAccount(String owner, double balance) {
        this.owner = owner;
        this.balance = balance;
    }

    class TransactionLog {                    // inner — has Outer.this reference
        private java.util.List<String> logs = new java.util.ArrayList<>();

        void record(String action, double amount) {
            logs.add(action + " " + amount + " | balance=" + balance);
            // ↑ directly reads BankAccount's private 'balance' field
        }

        void printAll() {
            System.out.println("Log for " + owner + ":");   // reads private 'owner'
            logs.forEach(System.out::println);
        }
    }

    void deposit(double amount) {
        balance += amount;
        TransactionLog log = new TransactionLog();  // inside outer: can use directly
        log.record("DEPOSIT", amount);
        log.printAll();
    }
}

BankAccount acc = new BankAccount("Alice", 1000);
BankAccount.TransactionLog log = acc.new TransactionLog();  // outside: needs instance
log.record("VIEW", 0);
```

**What this does:** `TransactionLog` reads `balance` and `owner` directly because it holds `Outer.this` — a reference to the specific `BankAccount` instance it was created from.

> ⚠️ **Pitfall:** Every inner class instance holds a **strong reference** to its outer instance. If you keep the inner instance alive (e.g., in a static collection or a long-lived listener), the outer instance **cannot be garbage collected** even if nothing else references it. This is a classic memory leak in Android and Swing.

---

### Example 2 — Iterator pattern (canonical inner class use)

```java
class NumberRange implements Iterable<Integer> {
    private final int start;
    private final int end;

    NumberRange(int start, int end) {
        this.start = start;
        this.end = end;
    }

    @Override
    public java.util.Iterator<Integer> iterator() {
        return new RangeIterator();    // inner class created tied to this NumberRange
    }

    class RangeIterator implements java.util.Iterator<Integer> {
        private int current = start;   // reads outer's 'start' field

        @Override
        public boolean hasNext() { return current <= end; }  // reads outer's 'end'

        @Override
        public Integer next() {
            if (!hasNext()) throw new java.util.NoSuchElementException();
            return current++;
        }
    }
}

NumberRange range = new NumberRange(1, 5);
for (int n : range) {
    System.out.print(n + " ");  // 1 2 3 4 5
}
```

**What this does:** `RangeIterator` reads `start` and `end` directly from the enclosing `NumberRange` instance. No need to pass them as constructor args — the inner class inherits access.

#### Dry Run — Iterating `NumberRange(1, 5)`

| Step | `hasNext()` | `current` | `next()` returns |
|------|------------|-----------|-----------------|
| init | `1 <= 5` = true | 1 | — |
| call 1 | `1 <= 5` = true | 1 → 2 | 1 |
| call 2 | `2 <= 5` = true | 2 → 3 | 2 |
| call 3 | `3 <= 5` = true | 3 → 4 | 3 |
| call 4 | `4 <= 5` = true | 4 → 5 | 4 |
| call 5 | `5 <= 5` = true | 5 → 6 | 5 |
| call 6 | `6 <= 5` = false | 6 | throws `NoSuchElementException` |

---

### Example 3 — `Outer.this` disambiguation

```java
class Window {
    private String title;

    Window(String title) { this.title = title; }

    class Button {
        private String label;

        Button(String label) { this.label = label; }

        void click() {
            // 'title' here would be ambiguous if Button also had a 'title' field
            System.out.println("Button '" + label + "' clicked in window: " + Window.this.title);
            //                                                                  ^^^^^^^^^^^^
            //                                              explicit reference to outer instance
        }

        String windowTitle() { return Window.this.title; }
    }

    Button createButton(String label) { return new Button(label); }
}

Window w = new Window("Settings");
Window.Button b = w.createButton("Save");
b.click();   // Button 'Save' clicked in window: Settings
```

**What this does:** `Window.this.title` explicitly names which enclosing instance's `title` is meant. Without the qualifier, if `Button` also had a `title` field, it would shadow the outer one.

---

## 3. Local Class

### What and Why

A **local class** is declared inside a method body. It's fully scoped to that method — it doesn't exist outside it. It can access:
- The enclosing method's **effectively-final** local variables
- All members of the enclosing class instance (`Outer.this`)

**Why it exists:** When you need a class with multiple methods (so a lambda won't do) but it's entirely specific to one method's logic. Rarely used in modern Java — usually replaced by a private static nested class or a lambda.

```
void someMethod() {
    int x = 10;                 // effectively final
    ┌────────────────────────┐
    │     class LocalHelper  │  ← only visible inside someMethod()
    │       void doWork() {  │
    │         use(x);        │  ← can access x (eff-final)
    │       }                │
    └────────────────────────┘
    LocalHelper h = new LocalHelper();  // instantiated within same scope
}
```

### Example 1 — Local class with effectively-final variable capture

```java
class TextProcessor {
    void process(String[] texts, String separator) {
        // 'separator' is effectively final (never reassigned)

        class LineFormatter {         // local class — exists only in this method
            String format(String text) {
                return separator + text + separator;
            }

            String formatAll(String[] items) {
                StringBuilder sb = new StringBuilder();
                for (String item : items) sb.append(format(item)).append("\n");
                return sb.toString();
            }
        }

        LineFormatter formatter = new LineFormatter();
        System.out.println(formatter.formatAll(texts));
    }
}

new TextProcessor().process(new String[]{"hello", "world"}, "***");
// ***hello***
// ***world***
```

**What this does:** `LineFormatter` is a class with two methods — more than a lambda can handle. It captures `separator` from the enclosing method. After `process()` returns, `LineFormatter` ceases to exist as a usable type.

> ⚠️ **Pitfall:** The captured variable must be **effectively final** — never reassigned after initial assignment. If you write `separator = separator.trim()`, the compiler will refuse to let `LineFormatter` capture it because reassignment breaks the "final" guarantee.

---

### Example 2 — Local class implementing an interface

```java
interface Validator {
    boolean isValid(String input);
    String errorMessage();
}

class RegistrationService {
    void register(String username, int minLength, int maxLength) {
        class UsernameValidator implements Validator {
            @Override
            public boolean isValid(String input) {
                return input != null
                    && input.length() >= minLength   // captures minLength (eff-final)
                    && input.length() <= maxLength;  // captures maxLength (eff-final)
            }

            @Override
            public String errorMessage() {
                return "Username must be " + minLength + "–" + maxLength + " characters";
            }
        }

        Validator v = new UsernameValidator();
        if (!v.isValid(username)) {
            System.out.println("Invalid: " + v.errorMessage());
        } else {
            System.out.println("Registered: " + username);
        }
    }
}

RegistrationService svc = new RegistrationService();
svc.register("al", 3, 20);     // Invalid: Username must be 3–20 characters
svc.register("alice", 3, 20);  // Registered: alice
```

**What this does:** `UsernameValidator` implements a two-method interface, which rules out a simple lambda. The local class captures `minLength` and `maxLength` from the method parameters.

---

### Example 3 — Local class accessing outer instance

```java
class EventBus {
    private java.util.List<String> eventLog = new java.util.ArrayList<>();

    void dispatchBatch(String[] events) {
        class BatchDispatcher {
            void dispatch(String event) {
                eventLog.add(event);         // accesses outer instance field directly
                System.out.println("Dispatched: " + event);
            }
        }
        BatchDispatcher d = new BatchDispatcher();
        for (String e : events) d.dispatch(e);
    }

    java.util.List<String> getLog() { return eventLog; }
}
```

**What this does:** `BatchDispatcher` can read and write `eventLog` — an instance field of the enclosing `EventBus`. Local classes have full access to the enclosing instance's members, just like inner classes.

---

## 4. Anonymous Class

### What and Why

An **anonymous class** is a class declared and instantiated in one expression. It has no name. It either extends a class or implements an interface, and defines its body inline. You can only use it once — there's no type name to reuse.

**Why it exists:** Before Java 8 lambdas, anonymous classes were the standard way to pass behavior as data — event handlers, callbacks, `Comparator`, `Runnable`. Today lambdas replace most anonymous class uses, but anonymous classes are still needed when you must implement a multi-method interface or extend a class inline.

```
new InterfaceName() { ... }     // implements an interface
new AbstractClass() { ... }     // extends a class (abstract or concrete)

No name → can't reference type elsewhere
Can capture effectively-final variables from enclosing scope
```

### Example 1 — Pre-Java 8 style Comparator

```java
import java.util.*;

List<String> names = Arrays.asList("Charlie", "Alice", "Bob");

// Anonymous class (pre-Java 8 pattern)
Comparator<String> byLength = new Comparator<String>() {
    @Override
    public int compare(String a, String b) {
        return Integer.compare(a.length(), b.length());
    }
};

Collections.sort(names, byLength);
System.out.println(names);   // [Bob, Alice, Charlie]

// Equivalent lambda (Java 8+)
names.sort((a, b) -> Integer.compare(a.length(), b.length()));

// Even more concise with method reference
names.sort(Comparator.comparingInt(String::length));
```

**What this does:** The anonymous class creates a one-time `Comparator` implementation. The lambda and method reference are strictly shorter and cleaner for single-method interfaces.

---

### Example 2 — Multi-method interface (lambda can't replace)

```java
interface Lifecycle {
    void start();
    void stop();
    boolean isRunning();
}

class Server {
    void manage(Lifecycle component) {
        component.start();
        System.out.println("Running: " + component.isRunning());
        component.stop();
        System.out.println("Running: " + component.isRunning());
    }
}

boolean[] running = {false};   // effectively-final array trick for capture mutation

Lifecycle mockComponent = new Lifecycle() {
    @Override public void start()         { running[0] = true;  System.out.println("Started"); }
    @Override public void stop()          { running[0] = false; System.out.println("Stopped"); }
    @Override public boolean isRunning()  { return running[0]; }
};

new Server().manage(mockComponent);
// Started
// Running: true
// Stopped
// Running: false
```

**What this does:** `Lifecycle` has three methods — a lambda cannot implement it. Anonymous class is the right tool here (or a full private static nested class). The `boolean[]` trick lets the anonymous class "mutate" a captured value while keeping the array reference effectively final.

> ⚠️ **Pitfall:** The `boolean[] running = {false}` trick works but is a code smell. It sidesteps the effectively-final rule by mutating the array contents (not the reference). For production code, extract a proper named class instead.

---

### Example 3 — Anonymous class extending a concrete class

```java
class Counter {
    protected int count = 0;
    void increment() { count++; }
    int value()      { return count; }
}

// Extend Counter inline with custom logging
Counter loggingCounter = new Counter() {
    @Override
    void increment() {
        super.increment();
        System.out.println("Incremented to " + count);
    }
};

loggingCounter.increment();   // Incremented to 1
loggingCounter.increment();   // Incremented to 2
System.out.println(loggingCounter.value());  // 2
```

**What this does:** The anonymous class extends `Counter` and overrides `increment()` to add logging. `super.increment()` calls the parent's logic first.

---

### Example 4 — Capturing effectively-final variables

```java
class EventSystem {
    interface EventHandler { void handle(String eventData); }

    void addListener(String prefix, EventHandler handler) {
        handler.handle("test");   // simplified — in real code, stored and called later
    }
}

String logPrefix = "APP";          // effectively final — never reassigned

EventSystem.EventHandler handler = new EventSystem.EventHandler() {
    @Override
    public void handle(String data) {
        System.out.println("[" + logPrefix + "] Event: " + data);
        // logPrefix = "OTHER";    // COMPILE ERROR — would make it non-effectively-final
    }
};

new EventSystem().addListener(logPrefix, handler);
// [APP] Event: test
```

**What this does:** `logPrefix` is captured. Java copies its value into the anonymous class at the time of creation. The variable must remain effectively final for the lifetime of the anonymous class.

#### Dry Run — Variable capture

| Variable | Capture mechanism | What happens at capture |
|----------|------------------|------------------------|
| `logPrefix = "APP"` | Copied into hidden field of anon class | anon class gets its own `logPrefix = "APP"` |
| `logPrefix = "OTHER"` — if reassigned | Compile error | Compiler refuses: variable not effectively final |
| Array `boolean[] flag` | Reference copied | Array object shared; contents can be mutated |

---

### Anonymous Class vs Lambda Comparison

```java
// Anonymous class — works for any interface, has its own 'this'
Runnable r1 = new Runnable() {
    @Override
    public void run() {
        System.out.println("this = " + this.getClass().getSimpleName());
        // 'this' refers to the anonymous class instance
    }
};

// Lambda — only for functional interfaces, 'this' from enclosing scope
Runnable r2 = () -> {
    System.out.println("this = " + this.getClass().getSimpleName());
    // 'this' refers to the enclosing class instance (if inside a class)
};
```

**What this does:** The critical behavioral difference — inside an anonymous class, `this` refers to the anonymous class instance. Inside a lambda, `this` refers to the enclosing scope's `this`. This matters for self-referencing in event deregistration.

> ⚠️ **Pitfall:** Anonymous classes cannot define constructors (they have no name). Use instance initializers `{ ... }` for setup logic. Also: an anonymous class creates a new `.class` file at compile time (e.g., `Outer$1.class`), which adds to JAR size when overused.

---

## 5. When to Use Each — Decision Guide

### Comparison Table

| Type | Outer Access | Instantiation | Reusable | Modern Java Role |
|------|-------------|---------------|----------|-----------------|
| Static nested | `static` members only | `new Outer.Inner()` | Yes (named type) | Preferred for helpers, Builder |
| Inner (non-static) | All members (private included) | `outer.new Inner()` | Yes (named type) | Iterator, tight coupling to outer state |
| Local | Eff-final locals + outer instance | Within method only | No | Rare; use lambda or static nested instead |
| Anonymous | Eff-final locals + outer instance | Inline once | No | Replaced by lambda (single-method) |

---

### Decision Flowchart

```
Need a class defined inside another class?
│
├─ Does it need access to outer INSTANCE state?
│   ├─ YES → Inner class (or anonymous if one-time)
│   └─ NO  → Static nested class (preferred — lighter)
│
├─ Is it only needed in one method?
│   ├─ YES + single method → Lambda (Java 8+)
│   ├─ YES + multiple methods → Local class or anonymous class
│   └─ NO → Named nested class (static or inner)
│
├─ Is it one-time use?
│   ├─ YES + single method interface → Lambda
│   ├─ YES + multi-method interface  → Anonymous class
│   └─ NO → Named class (reuse is impossible with anonymous)
│
└─ Is it a Builder / helper / data container?
    └─ Static nested class (canonical use)
```

---

### Example — Choosing the right type for a custom List

```java
class SimpleList<T> {
    private Object[] data = new Object[10];
    private int size = 0;

    void add(T item) { data[size++] = item; }

    // INNER CLASS: iterator needs outer instance's data and size
    class ListIterator implements java.util.Iterator<T> {
        private int index = 0;

        @Override
        public boolean hasNext() { return index < size; }   // reads outer 'size'

        @SuppressWarnings("unchecked")
        @Override
        public T next() { return (T) data[index++]; }       // reads outer 'data'
    }

    // STATIC NESTED: stats helper needs no specific list instance for its logic
    static class Stats {
        static String summarize(int size) {
            return "List with " + size + " elements";
        }
    }

    java.util.Iterator<T> iterator() { return new ListIterator(); }
    String stats()                   { return Stats.summarize(size); }
}

SimpleList<String> list = new SimpleList<>();
list.add("x"); list.add("y"); list.add("z");

java.util.Iterator<String> it = list.iterator();   // inner class
while (it.hasNext()) System.out.print(it.next() + " ");  // x y z

System.out.println(list.stats());   // List with 3 elements
```

**What this does:** `ListIterator` (inner) needs the list's `data` and `size` — inner class is correct. `Stats` (static nested) is a utility that takes a count and formats a string — it doesn't need any list instance.

---

### Example — Memory leak via inner class (and how to fix)

```java
// PROBLEMATIC: inner class holds strong reference to Activity/outer
class Activity {
    private byte[] largeData = new byte[1024 * 1024];  // 1MB

    // AsyncTask as inner class captures 'this' implicitly
    class DataLoader implements Runnable {
        @Override
        public void run() {
            // ... uses Activity.this.largeData
        }
    }

    Runnable createLoader() { return new DataLoader(); }
}

// If the Runnable is kept alive after Activity is "done",
// Activity and its 1MB cannot be garbage collected.

// FIX: use static nested + weak reference
class ActivityFixed {
    private byte[] largeData = new byte[1024 * 1024];

    static class DataLoader implements Runnable {
        private java.lang.ref.WeakReference<ActivityFixed> ref;

        DataLoader(ActivityFixed activity) {
            this.ref = new java.lang.ref.WeakReference<>(activity);
        }

        @Override
        public void run() {
            ActivityFixed activity = ref.get();
            if (activity != null) {
                // use activity.largeData
            }
            // if null, Activity was GC'd — gracefully do nothing
        }
    }
}
```

**What this does:** Converting `DataLoader` to a `static` nested class removes the implicit `Outer.this` reference. The explicit `WeakReference` lets the GC collect `ActivityFixed` when nothing else holds it, even if `DataLoader` is still alive.

> ⚠️ **Pitfall:** This pattern is critical in long-lived contexts (Android Activities, Swing frames, server request handlers). An inner class registered as a listener or submitted to a thread pool will silently pin the outer object in memory. Always prefer static nested + explicit reference passing.

---

## Quick Reference

```
Type             | static | Access Outer | Syntax
─────────────────┼────────┼──────────────┼──────────────────────────────
Static nested    | yes    | static only  | new Outer.Nested()
Inner            | no     | all members  | outerRef.new Inner()
Local            | no     | eff-final    | new LocalClass() inside method
Anonymous        | no     | eff-final    | new Interface() { ... } inline

Key rules:
  - Only static nested can be instantiated without an outer instance
  - Only static nested avoids the memory-leak risk
  - Local + anonymous capture: variable must be effectively final [Java 8+] (was 'final' before)
  - Lambda replaces most anonymous class uses for single-method interfaces [Java 8+]
  - Anonymous class 'this' = anon instance; lambda 'this' = enclosing scope
```
