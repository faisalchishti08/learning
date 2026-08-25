# Java Design Patterns

## Overview

Design patterns are reusable solutions to recurring design problems. Three categories: **Creational** (how objects are created), **Structural** (how objects are composed), **Behavioral** (how objects communicate). Modern Java idioms (lambdas, records, sealed classes) often simplify classic patterns.

---

## 1. Creational Patterns

### 1.1 Singleton

**Problem:** Ensure a class has exactly one instance, provide global access.

```java
// Thread-safe Singleton: Initialization-on-demand holder (best practice)
public class Singleton {
    private Singleton() {}

    private static class Holder {
        // Initialized lazily when Holder is first accessed
        // Class loading is thread-safe — no synchronized needed
        static final Singleton INSTANCE = new Singleton();
    }

    public static Singleton getInstance() {
        return Holder.INSTANCE;
    }

    public void doWork() { System.out.println("working"); }
}
```

```java
// Enum Singleton [Java 5+] — serialization-safe, reflection-safe
public enum DatabaseConnection {
    INSTANCE;
    private final java.sql.Connection conn = null; // init in constructor

    public void query(String sql) { /* use conn */ }
}
// Usage: DatabaseConnection.INSTANCE.query("SELECT 1");
```

**When to use:** Logger, config, connection pool. Avoid overuse — singletons are hard to test (global state). Prefer dependency injection instead.

> ⚠️ **Pitfall:** `synchronized getInstance()` is correct but slow. Double-checked locking needs `volatile`. Holder idiom is simplest and correct.

---

### 1.2 Factory Method

**Problem:** Let subclasses decide which class to instantiate.

```java
public class FactoryMethodDemo {
    interface Notification {
        void send(String message);
    }

    static class EmailNotification implements Notification {
        private String address;
        EmailNotification(String address) { this.address = address; }
        @Override public void send(String msg) { System.out.println("Email to " + address + ": " + msg); }
    }

    static class SMSNotification implements Notification {
        private String phone;
        SMSNotification(String phone) { this.phone = phone; }
        @Override public void send(String msg) { System.out.println("SMS to " + phone + ": " + msg); }
    }

    // Factory method — caller specifies type as string or enum
    static Notification create(String type, String target) {
        return switch (type) {
            case "email" -> new EmailNotification(target);
            case "sms"   -> new SMSNotification(target);
            default      -> throw new IllegalArgumentException("Unknown type: " + type);
        };
    }

    public static void main(String[] args) {
        Notification n = create("email", "alice@example.com");
        n.send("Hello!"); // Email to alice@example.com: Hello!
    }
}
```

---

### 1.3 Builder

**Problem:** Construct complex objects step-by-step, avoid telescoping constructors.

```java
public class BuilderDemo {
    static final class HttpRequest {
        private final String method;
        private final String url;
        private final java.util.Map<String, String> headers;
        private final String body;
        private final int timeoutMs;

        private HttpRequest(Builder b) {
            this.method = b.method;
            this.url = b.url;
            this.headers = java.util.Collections.unmodifiableMap(b.headers);
            this.body = b.body;
            this.timeoutMs = b.timeoutMs;
        }

        @Override public String toString() {
            return method + " " + url + " timeout=" + timeoutMs + "ms headers=" + headers;
        }

        static class Builder {
            private final String method;
            private final String url;
            private java.util.Map<String, String> headers = new java.util.HashMap<>();
            private String body = "";
            private int timeoutMs = 5000;

            Builder(String method, String url) {
                this.method = method; this.url = url;
            }

            Builder header(String key, String value) { headers.put(key, value); return this; }
            Builder body(String body) { this.body = body; return this; }
            Builder timeout(int ms) { this.timeoutMs = ms; return this; }
            HttpRequest build() { return new HttpRequest(this); }
        }
    }

    public static void main(String[] args) {
        HttpRequest req = new HttpRequest.Builder("POST", "https://api.example.com/users")
            .header("Content-Type", "application/json")
            .header("Authorization", "Bearer token123")
            .body("{\"name\":\"Alice\"}")
            .timeout(3000)
            .build();

        System.out.println(req);
    }
}
```

**When to use:** Many optional parameters, immutable objects, complex construction. Records [Java 16+] often replace builders for simple data classes.

---

### 1.4 Prototype

**Problem:** Clone an existing object instead of creating from scratch.

```java
public class PrototypeDemo {
    static class Template implements Cloneable {
        private String name;
        private java.util.List<String> tags;

        Template(String name, java.util.List<String> tags) {
            this.name = name;
            this.tags = new java.util.ArrayList<>(tags);
        }

        // Deep clone
        @Override public Template clone() {
            return new Template(name, new java.util.ArrayList<>(tags)); // deep copy of list
        }

        void setName(String name) { this.name = name; }
        void addTag(String tag) { tags.add(tag); }
        @Override public String toString() { return name + " " + tags; }
    }

    public static void main(String[] args) {
        Template original = new Template("Base", java.util.List.of("tag1", "tag2"));
        Template copy1 = original.clone();
        copy1.setName("Variant A");
        copy1.addTag("extra");

        System.out.println(original); // Base [tag1, tag2] — unchanged
        System.out.println(copy1);    // Variant A [tag1, tag2, extra]
    }
}
```

---

## 2. Structural Patterns

### 2.1 Decorator

**Problem:** Add behavior to objects dynamically without subclassing.

```java
public class DecoratorDemo {
    interface TextProcessor {
        String process(String text);
    }

    static class TrimProcessor implements TextProcessor {
        @Override public String process(String text) { return text.trim(); }
    }

    // Decorator: wraps another TextProcessor
    static class UpperCaseDecorator implements TextProcessor {
        private final TextProcessor wrapped;
        UpperCaseDecorator(TextProcessor wrapped) { this.wrapped = wrapped; }
        @Override public String process(String text) {
            return wrapped.process(text).toUpperCase();
        }
    }

    static class PrefixDecorator implements TextProcessor {
        private final TextProcessor wrapped;
        private final String prefix;
        PrefixDecorator(TextProcessor wrapped, String prefix) {
            this.wrapped = wrapped; this.prefix = prefix;
        }
        @Override public String process(String text) {
            return prefix + wrapped.process(text);
        }
    }

    // Lambda-based decorator [Java 8+] — no class needed
    static TextProcessor decorate(TextProcessor p, java.util.function.UnaryOperator<String> fn) {
        return text -> fn.apply(p.process(text));
    }

    public static void main(String[] args) {
        TextProcessor pipeline = new PrefixDecorator(
            new UpperCaseDecorator(
                new TrimProcessor()
            ),
            ">> "
        );
        System.out.println(pipeline.process("  hello world  ")); // >> HELLO WORLD

        // Lambda version
        TextProcessor p2 = decorate(
            decorate(String::trim, String::toUpperCase),
            s -> ">> " + s
        );
        System.out.println(p2.process("  hello  ")); // >> HELLO
    }
}
```

**When to use:** Java I/O is built on Decorator — `new BufferedReader(new FileReader(...))`.

---

### 2.2 Adapter

**Problem:** Convert the interface of a class into another interface clients expect.

```java
public class AdapterDemo {
    // Legacy API — can't modify
    static class LegacyLogger {
        void writeLog(int severity, String msg) {
            System.out.printf("[%s] %s%n", severity == 0 ? "INFO" : "ERROR", msg);
        }
    }

    // New interface
    interface Logger {
        void info(String msg);
        void error(String msg);
    }

    // Adapter: wraps legacy, exposes new interface
    static class LegacyLoggerAdapter implements Logger {
        private final LegacyLogger legacy;
        LegacyLoggerAdapter(LegacyLogger legacy) { this.legacy = legacy; }
        @Override public void info(String msg) { legacy.writeLog(0, msg); }
        @Override public void error(String msg) { legacy.writeLog(1, msg); }
    }

    static void process(Logger log) {
        log.info("Processing started");
        log.error("Something failed");
    }

    public static void main(String[] args) {
        process(new LegacyLoggerAdapter(new LegacyLogger()));
        // [INFO] Processing started
        // [ERROR] Something failed
    }
}
```

---

### 2.3 Composite

**Problem:** Treat individual objects and groups of objects uniformly (tree structures).

```java
public class CompositeDemo {
    interface FileSystemNode {
        String name();
        long size();
        void print(String indent);
    }

    record File(String name, long size) implements FileSystemNode {
        @Override public void print(String indent) {
            System.out.println(indent + name + " (" + size + " bytes)");
        }
    }

    static class Directory implements FileSystemNode {
        private final String name;
        private final java.util.List<FileSystemNode> children = new java.util.ArrayList<>();

        Directory(String name) { this.name = name; }
        void add(FileSystemNode node) { children.add(node); }

        @Override public String name() { return name; }
        @Override public long size() { return children.stream().mapToLong(FileSystemNode::size).sum(); }
        @Override public void print(String indent) {
            System.out.println(indent + name + "/  (" + size() + " bytes total)");
            children.forEach(c -> c.print(indent + "  "));
        }
    }

    public static void main(String[] args) {
        Directory root = new Directory("root");
        Directory src = new Directory("src");
        src.add(new File("Main.java", 1024));
        src.add(new File("Utils.java", 512));
        root.add(src);
        root.add(new File("README.md", 256));

        root.print("");
        // root/  (1792 bytes total)
        //   src/  (1536 bytes total)
        //     Main.java (1024 bytes)
        //     Utils.java (512 bytes)
        //   README.md (256 bytes)
    }
}
```

---

### 2.4 Proxy

**Problem:** Provide a surrogate to control access to another object (lazy init, caching, logging, security).

```java
import java.lang.reflect.*;

public class ProxyDemo {
    interface DataService {
        String fetch(String key);
    }

    static class RealDataService implements DataService {
        @Override public String fetch(String key) {
            System.out.println("Fetching from DB: " + key);
            return "data:" + key;
        }
    }

    // Caching proxy
    static DataService cachingProxy(DataService real) {
        java.util.Map<String, String> cache = new java.util.HashMap<>();
        return (DataService) Proxy.newProxyInstance(
            DataService.class.getClassLoader(),
            new Class<?>[]{DataService.class},
            (proxy, method, args) -> {
                String key = (String) args[0];
                return cache.computeIfAbsent(key, k -> {
                    try { return (String) method.invoke(real, k); }
                    catch (Exception e) { throw new RuntimeException(e); }
                });
            }
        );
    }

    public static void main(String[] args) {
        DataService service = cachingProxy(new RealDataService());
        System.out.println(service.fetch("user:1")); // Fetching from DB: user:1 → data:user:1
        System.out.println(service.fetch("user:1")); // (from cache, no DB call) → data:user:1
        System.out.println(service.fetch("user:2")); // Fetching from DB: user:2 → data:user:2
    }
}
```

---

## 3. Behavioral Patterns

### 3.1 Strategy

**Problem:** Define a family of algorithms, make them interchangeable.

```java
public class StrategyDemo {
    // Strategy interface — Java 8+: can be a functional interface
    @FunctionalInterface
    interface SortStrategy {
        void sort(int[] arr);
    }

    static class Sorter {
        private SortStrategy strategy;
        Sorter(SortStrategy strategy) { this.strategy = strategy; }
        void setStrategy(SortStrategy strategy) { this.strategy = strategy; }
        void sort(int[] arr) { strategy.sort(arr); }
    }

    public static void main(String[] args) {
        int[] data = {5, 2, 8, 1, 9, 3};

        // Lambda as strategy [Java 8+]
        Sorter sorter = new Sorter(java.util.Arrays::sort);
        sorter.sort(data);
        System.out.println(java.util.Arrays.toString(data)); // [1, 2, 3, 5, 8, 9]

        // Swap strategy at runtime
        data = new int[]{5, 2, 8, 1, 9, 3};
        sorter.setStrategy(arr -> {
            // bubble sort
            for (int i = 0; i < arr.length - 1; i++)
                for (int j = 0; j < arr.length - 1 - i; j++)
                    if (arr[j] > arr[j+1]) { int t = arr[j]; arr[j] = arr[j+1]; arr[j+1] = t; }
        });
        sorter.sort(data);
        System.out.println(java.util.Arrays.toString(data)); // [1, 2, 3, 5, 8, 9]
    }
}
```

**Modern note:** With lambdas, Strategy is just passing a function. `Comparator`, `Runnable`, `Supplier` are all Strategy.

---

### 3.2 Observer

**Problem:** Define a one-to-many dependency — when one changes, dependents are notified.

```java
public class ObserverDemo {
    @FunctionalInterface
    interface EventListener<T> { void onEvent(T event); }

    static class EventBus<T> {
        private final java.util.List<EventListener<T>> listeners = new java.util.ArrayList<>();
        void subscribe(EventListener<T> listener) { listeners.add(listener); }
        void publish(T event) { listeners.forEach(l -> l.onEvent(event)); }
    }

    record OrderEvent(String orderId, String status) {}

    public static void main(String[] args) {
        EventBus<OrderEvent> bus = new EventBus<>();

        // Lambda listeners
        bus.subscribe(e -> System.out.println("Email: Order " + e.orderId() + " → " + e.status()));
        bus.subscribe(e -> System.out.println("SMS: Order " + e.orderId() + " " + e.status()));
        bus.subscribe(e -> {
            if ("SHIPPED".equals(e.status()))
                System.out.println("Warehouse: update inventory for " + e.orderId());
        });

        bus.publish(new OrderEvent("ORD-001", "SHIPPED"));
        // Email: Order ORD-001 → SHIPPED
        // SMS: Order ORD-001 SHIPPED
        // Warehouse: update inventory for ORD-001
    }
}
```

---

### 3.3 Command

**Problem:** Encapsulate a request as an object — supports undo, queuing, logging.

```java
public class CommandDemo {
    @FunctionalInterface
    interface Command { void execute(); }

    static class TextEditor {
        private final StringBuilder text = new StringBuilder();
        private final java.util.Deque<Command> history = new java.util.ArrayDeque<>();
        private final java.util.Deque<Command> undoHistory = new java.util.ArrayDeque<>();

        void execute(Command cmd, Command undo) {
            cmd.execute();
            history.push(cmd);
            undoHistory.push(undo);
        }

        void undo() {
            if (!undoHistory.isEmpty()) undoHistory.pop().execute();
        }

        void type(String s) {
            execute(
                () -> text.append(s),
                () -> text.delete(text.length() - s.length(), text.length())
            );
        }

        @Override public String toString() { return text.toString(); }
    }

    public static void main(String[] args) {
        TextEditor editor = new TextEditor();
        editor.type("Hello");
        editor.type(" World");
        System.out.println(editor); // Hello World
        editor.undo();
        System.out.println(editor); // Hello
        editor.undo();
        System.out.println(editor); // (empty)
    }
}
```

---

### 3.4 Template Method

**Problem:** Define algorithm skeleton in base class; subclasses fill in specific steps.

```java
public class TemplateMethodDemo {
    abstract static class DataMigration {
        // Template method — defines the algorithm
        final void migrate() {
            readData();
            transformData();
            writeData();
            cleanup();
        }

        abstract void readData();
        abstract void transformData();
        abstract void writeData();

        // Hook — optional override
        void cleanup() { System.out.println("Default cleanup"); }
    }

    static class CSVMigration extends DataMigration {
        @Override void readData() { System.out.println("Read CSV file"); }
        @Override void transformData() { System.out.println("Parse CSV rows"); }
        @Override void writeData() { System.out.println("Write to database"); }
        @Override void cleanup() { System.out.println("Close CSV file"); }
    }

    static class APIMigration extends DataMigration {
        @Override void readData() { System.out.println("Call REST API"); }
        @Override void transformData() { System.out.println("Map JSON fields"); }
        @Override void writeData() { System.out.println("Batch insert"); }
        // cleanup() uses default
    }

    public static void main(String[] args) {
        new CSVMigration().migrate();
        System.out.println("---");
        new APIMigration().migrate();
    }
}
```

---

### 3.5 Chain of Responsibility

**Problem:** Pass request along a chain of handlers until one handles it.

```java
public class ChainDemo {
    @FunctionalInterface
    interface Handler { boolean handle(int request);  }

    static Handler chain(Handler... handlers) {
        return request -> {
            for (Handler h : handlers) {
                if (h.handle(request)) return true;
            }
            return false;
        };
    }

    public static void main(String[] args) {
        // Auth → rate-limit → business logic → fallback
        Handler auth       = req -> { if (req < 0) { System.out.println("Auth fail"); return true; } return false; };
        Handler rateLimit  = req -> { if (req > 1000) { System.out.println("Rate limited"); return true; } return false; };
        Handler business   = req -> { System.out.println("Processed: " + req); return true; };

        Handler pipeline = chain(auth, rateLimit, business);
        pipeline.handle(42);    // Processed: 42
        pipeline.handle(-1);    // Auth fail
        pipeline.handle(9999);  // Rate limited
    }
}
```

---

## Quick Reference

```
Creational:
  Singleton      one instance (Holder idiom or enum)
  Factory Method factory method delegates creation to subclasses
  Abstract Factory family of related factories
  Builder        step-by-step construction (fluent API)
  Prototype      clone existing object

Structural:
  Adapter        convert interface to expected interface
  Decorator      add behavior by wrapping (Java I/O pattern)
  Facade         simple interface over complex subsystem
  Composite      tree structure — treat leaf and branch uniformly
  Proxy          control access (caching, logging, lazy init)
  Flyweight      share common state between many objects

Behavioral:
  Strategy       algorithm family, swappable (→ lambdas in Java 8+)
  Observer       event pub/sub (→ EventListener pattern)
  Command        encapsulate request as object (supports undo)
  Template Method skeleton in base, details in subclass
  Chain of Resp. pass request along handler chain
  State          behavior changes with internal state
  Iterator       sequential access (→ Iterable/Iterator)
  Visitor        add operations to object hierarchy without changing it

Java 8+ modernizations:
  Strategy    → @FunctionalInterface + lambda
  Command     → Runnable / lambda
  Observer    → Consumer<T> listeners
  Factory     → switch expression
  Builder     → record (for simple immutable data)
```
