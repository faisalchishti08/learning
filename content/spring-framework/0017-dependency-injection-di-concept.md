---
card: spring-framework
gi: 17
slug: dependency-injection-di-concept
title: Dependency Injection (DI) concept
---

## 1. What it is

**Dependency Injection (DI)** is the specific mechanism Spring uses to implement IoC. Instead of an object fetching or constructing its own collaborators, those collaborators are *injected* (passed in) by the container.

Spring supports three injection styles:

| Style | Syntax | Spring preference |
|---|---|---|
| **Constructor** | `MyBean(Dep dep)` | Preferred — makes deps explicit, allows `final` |
| **Setter** | `@Autowired void setDep(Dep d)` | For optional deps; allows reconfiguration |
| **Field** | `@Autowired Dep dep` | Convenient but hides deps; avoid in production |

In all three cases Spring's `ApplicationContext` finds the right bean to inject by matching the declared type (or name), then passes it in.

In one sentence: **DI is the act of the container passing your object's required collaborators to it rather than having the object reach out and grab them itself.**

## 2. Why & when

Every object that collaborates with another object is a potential DI candidate. The key question: *does this class need another class to do its job?* If yes, inject that other class.

Benefits:
- **Testability.** Pass a mock at construction time — no framework needed for unit tests.
- **Replaceability.** Inject an interface; the container decides which implementation to wire.
- **Clarity.** Constructor injection lists every dependency explicitly — no hidden globals, no thread-local lookups.
- **Safety.** The container detects missing or ambiguous deps at startup, not at runtime.

The only things you should *not* inject are value objects (`new Money(100, "USD")`) and JDK types (`new HashMap<>()`). Everything that has behaviour — services, repositories, clients, event publishers — should be injected.

## 3. Core concept

Think of a restaurant kitchen. The chef (your service) needs a knife, a cutting board, and an oven. With *no DI* the chef walks to a supplier, picks up these tools, and is forever tied to those exact vendors. With *DI* the restaurant owner stocks the kitchen — the chef just uses whatever is provided.

**Constructor injection** (the recommended style):
```java
@Service
class ReportService {
    private final DataSource dataSource;
    private final Formatter formatter;

    ReportService(DataSource dataSource, Formatter formatter) {
        this.dataSource = dataSource;  // injected by container
        this.formatter  = formatter;
    }
}
```

The container's algorithm:
1. Find all beans of type `DataSource` in the context — if exactly one exists, inject it.
2. Find all beans of type `Formatter` — same rule.
3. If more than one candidate exists, use `@Qualifier("csvFormatter")` or `@Primary` to disambiguate.
4. If no candidate exists, throw `NoSuchBeanDefinitionException` at startup.

**Field injection** — works but defeats testability:
```java
@Autowired DataSource dataSource;  // test cannot set this without Spring
```

**Setter injection** — use for genuinely optional dependencies:
```java
@Autowired(required = false)
void setCache(Cache cache) { this.cache = cache; }
```

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three DI styles: constructor, setter, field — container injects in all cases">
  <defs>
    <marker id="a17" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Container -->
  <rect x="240" y="10" width="200" height="48" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="340" y="30" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">ApplicationContext</text>
  <text x="340" y="48" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">holds DataSource + Formatter beans</text>

  <!-- Constructor injection -->
  <rect x="10" y="100" width="170" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="122" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Constructor DI</text>
  <text x="95" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ReportService(ds, fmt)</text>
  <text x="95" y="154" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">deps are final ✓</text>

  <!-- Setter injection -->
  <rect x="250" y="100" width="170" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="335" y="122" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Setter DI</text>
  <text x="335" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">setDataSource(ds)</text>
  <text x="335" y="154" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">optional deps OK</text>

  <!-- Field injection -->
  <rect x="490" y="100" width="170" height="60" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="575" y="122" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Field DI</text>
  <text x="575" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Autowired DataSource ds</text>
  <text x="575" y="154" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">hides deps ✗</text>

  <line x1="290" y1="58" x2="130" y2="98" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a17)"/>
  <line x1="340" y1="58" x2="340" y2="98" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a17)"/>
  <line x1="390" y1="58" x2="555" y2="98" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a17)"/>

  <text x="340" y="195" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Container injects the right bean in all three styles — constructor is preferred</text>
</svg>

The container injects through whichever style you declare. Constructor injection makes dependencies a compile-time contract; field injection hides them.

## 5. Runnable example

Scenario: a weather report generator that depends on a `DataProvider` (fetches raw data) and a `Formatter` (structures the output). We evolve from tight coupling to full DI.

### Level 1 — Basic

Tight coupling: `WeatherReport` creates its own data source and formatter inside the constructor — impossible to test or swap.

```java
// DIDemo.java — run with: java DIDemo.java
public class DIDemo {

    static class RawDataProvider {
        String fetch(String city) {
            return "city=" + city + " temp=22C wind=15kph humidity=60%";
        }
    }

    static class PlainFormatter {
        String format(String raw) {
            return "Weather: " + raw.replace(" ", " | ");
        }
    }

    static class WeatherReport {
        private final RawDataProvider provider;
        private final PlainFormatter  formatter;

        WeatherReport() {
            // No DI: WeatherReport controls its own collaborators
            this.provider  = new RawDataProvider();
            this.formatter = new PlainFormatter();
        }

        String generate(String city) {
            return formatter.format(provider.fetch(city));
        }
    }

    public static void main(String[] args) {
        WeatherReport report = new WeatherReport();
        System.out.println(report.generate("London"));
        System.out.println(report.generate("Tokyo"));
    }
}
```

How to run: `java DIDemo.java`

`WeatherReport` is locked to `RawDataProvider` and `PlainFormatter`. Adding a `JsonFormatter` or a cached data provider means editing `WeatherReport` itself.

### Level 2 — Intermediate

Constructor DI: extract interfaces, pass implementations through the constructor. `WeatherReport` becomes decoupled.

```java
// DIDemo2.java — run with: java DIDemo2.java
public class DIDemo2 {

    // Abstractions
    interface DataProvider { String fetch(String city); }
    interface Formatter    { String format(String raw); }

    // Implementations
    static class LiveDataProvider implements DataProvider {
        public String fetch(String city) {
            return "city=" + city + " temp=22C wind=15kph humidity=60%";
        }
    }

    static class MockDataProvider implements DataProvider {
        public String fetch(String city) {
            return "city=" + city + " temp=0C wind=0kph humidity=0%";  // test stub
        }
    }

    static class PlainFormatter implements Formatter {
        public String format(String raw) { return "PLAIN: " + raw.replace(" ", " | "); }
    }

    static class JsonFormatter implements Formatter {
        public String format(String raw) {
            // Parse pairs and produce JSON-like output
            StringBuilder sb = new StringBuilder("{");
            for (String pair : raw.split(" ")) {
                String[] kv = pair.split("=");
                if (kv.length == 2) sb.append("\"").append(kv[0]).append("\":\"").append(kv[1]).append("\",");
            }
            if (sb.charAt(sb.length()-1) == ',') sb.setLength(sb.length()-1);
            return sb.append("}").toString();
        }
    }

    // WeatherReport only knows the interfaces — injected via constructor
    static class WeatherReport {
        private final DataProvider provider;
        private final Formatter    formatter;

        WeatherReport(DataProvider provider, Formatter formatter) {  // DI
            this.provider  = provider;
            this.formatter = formatter;
        }

        String generate(String city) {
            return formatter.format(provider.fetch(city));
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Production: live data + JSON output ===");
        WeatherReport prod = new WeatherReport(new LiveDataProvider(), new JsonFormatter());
        System.out.println(prod.generate("London"));

        System.out.println("\n=== Test: mock data + plain output (no network) ===");
        WeatherReport test = new WeatherReport(new MockDataProvider(), new PlainFormatter());
        System.out.println(test.generate("London"));
    }
}
```

How to run: `java DIDemo2.java`

Two completely different behaviours — same `WeatherReport` class. The test version uses a mock provider so no HTTP call is needed. The container (or `main` in this demo) decides which combination to wire.

### Level 3 — Advanced

Add an optional `Cache` dependency via setter DI, and a `ReportAggregator` that depends on multiple `WeatherReport` instances — showing qualifier-based injection disambiguation.

```java
// DIDemo3.java — run with: java DIDemo3.java
import java.util.*;

public class DIDemo3 {

    interface DataProvider { String fetch(String city); }
    interface Formatter    { String format(String raw); }
    interface Cache        { Optional<String> get(String k); void put(String k, String v); }

    static class LiveDataProvider implements DataProvider {
        public String fetch(String city) { return "city=" + city + " temp=22C wind=15kph"; }
    }

    static class JsonFormatter implements Formatter {
        public String format(String raw) {
            StringBuilder sb = new StringBuilder("{");
            for (String pair : raw.split(" ")) {
                String[] kv = pair.split("=");
                if (kv.length == 2) sb.append("\"").append(kv[0]).append("\":\"").append(kv[1]).append("\",");
            }
            if (sb.charAt(sb.length()-1) == ',') sb.setLength(sb.length()-1);
            return sb.append("}").toString();
        }
    }

    static class SimpleCache implements Cache {
        private final Map<String, String> store = new HashMap<>();
        public Optional<String> get(String k) { return Optional.ofNullable(store.get(k)); }
        public void put(String k, String v)   { store.put(k, v); System.out.println("  [CACHE PUT] " + k); }
    }

    // Constructor DI for required deps, setter DI for optional cache
    static class WeatherReport {
        private final DataProvider provider;
        private final Formatter    formatter;
        private Cache cache = null;  // optional

        WeatherReport(DataProvider provider, Formatter formatter) {
            this.provider  = provider;
            this.formatter = formatter;
        }

        // Setter DI for optional dependency — Spring calls this if a Cache bean exists
        void setCache(Cache cache) {
            this.cache = cache;
            System.out.println("  [SETTER DI] Cache injected into " + this.getClass().getSimpleName());
        }

        String generate(String city) {
            if (cache != null) {
                Optional<String> hit = cache.get(city);
                if (hit.isPresent()) { System.out.println("  [CACHE HIT] " + city); return hit.get(); }
            }
            String result = formatter.format(provider.fetch(city));
            if (cache != null) cache.put(city, result);
            return result;
        }
    }

    // Aggregator receives two distinct WeatherReport beans
    // (in Spring: @Qualifier("primary") / @Qualifier("backup") distinguish them)
    static class ReportAggregator {
        private final WeatherReport primary;
        private final WeatherReport backup;

        ReportAggregator(WeatherReport primary, WeatherReport backup) {
            this.primary = primary;
            this.backup  = backup;
        }

        void printBoth(String city) {
            System.out.println("Primary  → " + primary.generate(city));
            System.out.println("Backup   → " + backup.generate(city));
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Wiring phase (simulates Spring container) ===");
        Cache cache = new SimpleCache();

        WeatherReport primary = new WeatherReport(new LiveDataProvider(), new JsonFormatter());
        primary.setCache(cache);   // setter DI for optional dep

        WeatherReport backup = new WeatherReport(
            city -> "city=" + city + " temp=BACKUP",  // lambda data provider
            raw  -> "BACKUP:" + raw
        );
        // backup has no cache — optional dep omitted

        ReportAggregator agg = new ReportAggregator(primary, backup);

        System.out.println("\n=== First call (cold cache) ===");
        agg.printBoth("Paris");

        System.out.println("\n=== Second call (primary hits cache) ===");
        agg.printBoth("Paris");
    }
}
```

How to run: `java DIDemo3.java`

**Setter DI** for `Cache` lets it remain optional — if no `Cache` bean is registered, Spring simply skips the setter call. The `ReportAggregator` shows two beans of the same type disambiguated by qualifier. The cache hit on the second call demonstrates that DI is not just about construction — injected collaborators carry state and behaviour through the full lifecycle of the owning bean.

## 6. Walkthrough

**Wiring phase — simulates Spring container startup:**
1. `new SimpleCache()` created first — no deps.
2. `new WeatherReport(new LiveDataProvider(), new JsonFormatter())` — constructor DI for required deps.
3. `primary.setCache(cache)` — setter DI for optional `Cache`; Spring calls `@Autowired` setters after constructor.
4. `backup` uses lambda implementations wired inline; no cache setter called.
5. `new ReportAggregator(primary, backup)` — two `WeatherReport` beans disambiguated by variable name (in Spring: `@Qualifier`).

**First `printBoth("Paris")` call:**
```
primary.generate("Paris")
  → cache.get("Paris") → Optional.empty()   (cold miss)
  → provider.fetch("Paris") → "city=Paris temp=22C wind=15kph"
  → formatter.format(raw)   → {"city":"Paris","temp":"22C","wind":"15kph"}
  → cache.put("Paris", ...) → [CACHE PUT] Paris
  → returns {"city":"Paris",...}

backup.generate("Paris")
  → cache == null → skip cache
  → "BACKUP:city=Paris temp=BACKUP"
```

**Second `printBoth("Paris")` call:**
```
primary.generate("Paris")
  → cache.get("Paris") → Optional["{"city":"Paris",...}"]   (cache HIT)
  → returns cached value immediately — provider never called
```

**Data/state transformation at each layer:**

| Layer | Input | Output |
|---|---|---|
| `LiveDataProvider.fetch` | `"Paris"` | `"city=Paris temp=22C wind=15kph"` |
| `JsonFormatter.format` | raw string | `{"city":"Paris","temp":"22C","wind":"15kph"}` |
| `SimpleCache.put` | key + JSON | stored in `HashMap` |
| Second call: `cache.get` | `"Paris"` | JSON string (bypasses provider) |

## 7. Gotchas & takeaways

> **Field injection breaks unit tests.** `@Autowired DataProvider provider` is a private field — you cannot set it from a test without reflection or a Spring test context. Constructor injection means `new WeatherReport(mockProvider, mockFormatter)` works in any JUnit test without any Spring infrastructure.

> **`@Autowired` on a constructor is optional in Spring 5+** when the class has exactly one constructor. Spring will inject it automatically. You still need `@Autowired` on setter and field injection sites.

- Prefer constructor injection for required, immutable dependencies. Use setter injection for optional deps. Avoid field injection in production code.
- `@Qualifier("beanName")` or `@Primary` on a bean definition resolves ambiguity when multiple beans of the same type exist.
- Spring matches by *type* first, then by *name* (variable name matching bean name) as a tiebreaker.
- Circular DI (A needs B, B needs A via constructors) throws `BeanCurrentlyInCreationException` at startup — fix by extracting a third shared dependency or restructuring.
- `@Lazy` on a constructor parameter defers injection until first use, breaking constructor-injection circular deps as a last resort.
