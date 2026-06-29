---
card: spring-framework
gi: 2
slug: history-evolution-spring-1-6
title: History & evolution (Spring 1 → 6)
---

## 1. What it is

The Spring Framework has evolved continuously since 2003. Each major version brought a paradigm shift that reflected changes in the Java ecosystem:

| Version | Year | Signature addition |
|---|---|---|
| 1.0 | 2003 | IoC container, XML configuration, AOP, JDBC template |
| 2.0 | 2006 | Namespace XML (`<context:component-scan>`), AspectJ AOP |
| 2.5 | 2007 | Annotation-driven config (`@Component`, `@Autowired`, `@MVC`) |
| 3.0 | 2009 | Java-based config (`@Configuration`), REST support, EL |
| 3.1 | 2011 | Environment profiles (`@Profile`), cache abstraction |
| 4.0 | 2013 | Java 8, generics-based injection, WebSocket, `@Conditional` |
| 5.0 | 2017 | Kotlin, reactive (WebFlux, Project Reactor), JDK 8 baseline |
| 5.3 | 2020 | Last 5.x; long-term support branch |
| 6.0 | 2022 | JDK 17 baseline, Jakarta EE 9+, AOT/GraalVM native images |
| 6.1 | 2023 | Virtual threads (JDK 21), RestClient, JVM Checkpoint Restore |

## 2. Why & when

Knowing the history helps you:

- **Read older codebases.** Legacy apps often use XML configuration (Spring 1–2.x style) or a mix of XML and annotations (Spring 2.5–3.x). Understanding the era tells you what style to expect.
- **Understand why things exist.** `@Component`-scan was an answer to XML verbosity. `@Configuration` replaced XML application context files. WebFlux replaced blocking Servlet APIs. Each feature has a reason.
- **Navigate migration guides.** Upgrading a Spring 4.x app to 6.x requires knowing what changed across three major versions (package renames, dropped APIs, new baselines).

## 3. Core concept

Three eras best summarise Spring's evolution:

**Era 1 — XML-centric (1.0–2.5):** Configuration lived in `applicationContext.xml`. Every bean was `<bean id="..." class="...">` with explicit `<property>` wiring. Spring 2.0 added custom XML namespaces (`<tx:annotation-driven/>`, `<aop:config/>`) to reduce boilerplate. The container was mature but configuration was verbose.

**Era 2 — Annotation-driven (2.5–4.x):** Spring 2.5 let you scan classes annotated `@Component`, `@Service`, `@Repository`, `@Controller` instead of declaring each bean in XML. `@Autowired` replaced `<property ref="...">`. Spring 3.0 introduced `@Configuration` classes as a pure-Java replacement for XML. Spring 4.x added `@Conditional` (the foundation of Spring Boot's auto-configuration).

**Era 3 — Modern / reactive / native (5.x–6.x):** Spring 5 embraced reactive programming with WebFlux and Project Reactor, enabling non-blocking I/O with a functional programming model. Kotlin became a first-class citizen. Spring 6 raised the baseline to JDK 17 and Jakarta EE 9 (`javax.*` → `jakarta.*`), added Ahead-of-Time (AOT) compilation support for GraalVM native images, and Spring 6.1 added virtual thread support for Project Loom.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Framework version timeline from 1.0 in 2003 to 6.1 in 2023">
  <defs>
    <marker id="timarr" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Timeline axis -->
  <line x1="30" y1="110" x2="680" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#timarr)"/>

  <!-- Eras background -->
  <rect x="30" y="80" width="190" height="60" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1" opacity="0.7"/>
  <text x="125" y="102" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">XML-centric</text>
  <text x="125" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1.0 → 2.5</text>

  <rect x="230" y="80" width="200" height="60" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1" opacity="0.7"/>
  <text x="330" y="102" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Annotation-driven</text>
  <text x="330" y="118" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">2.5 → 4.x</text>

  <rect x="440" y="80" width="230" height="60" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1" opacity="0.7"/>
  <text x="555" y="102" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Modern / Reactive / Native</text>
  <text x="555" y="118" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">5.0 → 6.1</text>

  <!-- Version markers -->
  <circle cx="60"  cy="110" r="4" fill="#8b949e"/>
  <text x="60"  y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1.0</text>
  <text x="60"  y="147" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2003</text>

  <circle cx="145" cy="110" r="4" fill="#8b949e"/>
  <text x="145" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2.5</text>
  <text x="145" y="147" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2007</text>

  <circle cx="270" cy="110" r="4" fill="#79c0ff"/>
  <text x="270" y="135" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">3.0</text>
  <text x="270" y="147" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">2009</text>

  <circle cx="390" cy="110" r="4" fill="#79c0ff"/>
  <text x="390" y="135" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">4.0</text>
  <text x="390" y="147" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">2013</text>

  <circle cx="480" cy="110" r="4" fill="#6db33f"/>
  <text x="480" y="135" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">5.0</text>
  <text x="480" y="147" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">2017</text>

  <circle cx="590" cy="110" r="4" fill="#6db33f"/>
  <text x="590" y="135" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">6.0</text>
  <text x="590" y="147" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">2022</text>

  <circle cx="650" cy="110" r="4" fill="#6db33f"/>
  <text x="650" y="135" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">6.1</text>
  <text x="650" y="147" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">2023</text>

  <!-- Top labels -->
  <text x="60"  y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">XML beans</text>
  <text x="145" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@Component</text>
  <text x="270" y="68" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">@Config</text>
  <text x="390" y="68" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">JDK 8</text>
  <text x="480" y="68" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">WebFlux</text>
  <text x="590" y="68" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">jakarta.*</text>
  <text x="650" y="68" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Loom</text>

  <text x="350" y="200" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Each major version answered a problem: verbosity → testability → scalability → performance → cloud-native</text>
</svg>

Three eras, each with a defining question answered: "how do we reduce XML?", "how do we go reactive?", "how do we go native?"

## 5. Runnable example

We'll write the same `GreetingService` three ways — one per era — so you can see how configuration style evolved while the actual business logic stayed unchanged.

### Level 1 — Basic

Era 1 style: pure Java, no annotations, manual wiring (mirrors Spring 1.x XML-driven approach).

```java
// EraOneDemo.java — run with: java EraOneDemo.java
// Mirrors Spring 1.x / 2.x: all wiring done explicitly (like XML does it)

public class EraOneDemo {

    // POJO — no Spring annotations. In Spring 1.x this would be in applicationContext.xml:
    // <bean id="greetingService" class="GreetingService">
    //   <property name="prefix" value="Hello"/>
    // </bean>
    static class GreetingService {
        private String prefix;
        void setPrefix(String prefix) { this.prefix = prefix; }  // setter injection
        String greet(String name) { return prefix + ", " + name + "!"; }
    }

    static class WelcomeController {
        private GreetingService greetingService;
        void setGreetingService(GreetingService gs) { this.greetingService = gs; }
        void handleRequest(String name) {
            System.out.println("Response: " + greetingService.greet(name));
        }
    }

    // Wiring — in Spring 1.x this XML does the job:
    // <bean id="welcomeController" class="WelcomeController">
    //   <property name="greetingService" ref="greetingService"/>
    // </bean>
    static Object[] loadApplicationContext() {
        GreetingService gs = new GreetingService();
        gs.setPrefix("Hello");  // <property name="prefix" value="Hello"/>
        WelcomeController ctrl = new WelcomeController();
        ctrl.setGreetingService(gs);
        return new Object[]{ctrl};
    }

    public static void main(String[] args) {
        WelcomeController ctrl = (WelcomeController) loadApplicationContext()[0];
        ctrl.handleRequest("Alice");
        ctrl.handleRequest("Bob");
    }
}
```

How to run: `java EraOneDemo.java`

Setter injection and explicit wiring. Spring 1.x replaced the `loadApplicationContext()` method with an XML file; everything else was identical.

### Level 2 — Intermediate

Era 2 style: annotations drive the container. `@Service`, `@Autowired`, constructor injection — the style most Spring 3.x–4.x apps use.

```java
// EraTwoDemo.java — run with: java EraTwoDemo.java
// Mirrors Spring 2.5–4.x: annotation-driven, no XML

// In a real Spring app these would be separate files with @Service / @Controller.
// Here we simulate what the container sees and does.

import java.util.*;

public class EraTwoDemo {

    // Marker interfaces to simulate Spring annotations
    @interface Service {}
    @interface Autowired {}

    @Service
    static class GreetingService {
        private final String prefix = "Hello";   // value from @Value("${greeting.prefix:Hello}")
        String greet(String name) { return prefix + ", " + name + "!"; }
    }

    @Service
    static class AuditService {
        void log(String action) { System.out.println("[AUDIT] " + action); }
    }

    @Service
    static class WelcomeController {
        // Constructor injection — @Autowired implied on single constructor in Spring 4.3+
        private final GreetingService greetingService;
        private final AuditService auditService;

        WelcomeController(GreetingService gs, AuditService audit) {
            this.greetingService = gs;
            this.auditService = audit;
        }

        void handleRequest(String name) {
            auditService.log("handleRequest(" + name + ")");
            System.out.println("Response: " + greetingService.greet(name));
        }
    }

    // Simulated @ComponentScan container
    @SuppressWarnings("unchecked")
    static <T> T buildContext(Class<T> rootBean, Object... extras) throws Exception {
        Map<Class<?>, Object> ctx = new LinkedHashMap<>();
        // Register all "beans" in dependency order
        ctx.put(GreetingService.class, new GreetingService());
        ctx.put(AuditService.class, new AuditService());
        ctx.put(WelcomeController.class,
            new WelcomeController(
                (GreetingService) ctx.get(GreetingService.class),
                (AuditService) ctx.get(AuditService.class)));
        System.out.println("Context initialised: " + ctx.size() + " beans");
        return (T) ctx.get(rootBean);
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Era 2: Annotation-driven Spring ===");
        WelcomeController ctrl = buildContext(WelcomeController.class);
        ctrl.handleRequest("Alice");
        ctrl.handleRequest("Bob");
    }
}
```

How to run: `java EraTwoDemo.java`

Constructor injection replaces setters. The "container" (our `buildContext`) mirrors what Spring's component-scan does: discover annotated classes and wire them together.

### Level 3 — Advanced

Era 3 style: functional, immutable, interface-oriented. Simulates Spring 6.x patterns — records, sealed interfaces, profile-aware wiring, and a virtual-thread-ready design.

```java
// EraThreeDemo.java — run with: java EraThreeDemo.java (JDK 17+)
// Mirrors Spring 6.x: records, sealed types, profile-aware config, Loom-ready

import java.util.*;
import java.util.concurrent.*;
import java.util.function.Function;

public class EraThreeDemo {

    // Sealed interface for greeting strategies (Spring 6.x loves records + sealed types)
    sealed interface GreetingStrategy permits FormalGreeting, CasualGreeting {}
    record FormalGreeting(String prefix) implements GreetingStrategy {}
    record CasualGreeting(String prefix) implements GreetingStrategy {}

    record GreetingService(GreetingStrategy strategy) {
        String greet(String name) {
            return switch (strategy) {
                case FormalGreeting(var p) -> p + ", " + name + ". How do you do?";
                case CasualGreeting(var p) -> p + " " + name + "!";
            };
        }
    }

    record AuditService(List<String> log) {
        void record(String action) {
            log.add(Thread.currentThread().getName() + " | " + action);
        }
        void printLog() { log.forEach(e -> System.out.println("  [AUDIT] " + e)); }
    }

    record WelcomeController(GreetingService greeting, AuditService audit) {
        String handleRequest(String name) {
            audit.record("handleRequest(" + name + ")");
            return greeting.greet(name);
        }
    }

    // Profile-aware "configuration class" — mirrors @Profile("formal") / @Profile("casual")
    static WelcomeController buildContext(String profile) {
        GreetingStrategy strategy = "formal".equals(profile)
            ? new FormalGreeting("Good day")
            : new CasualGreeting("Hey");
        AuditService audit = new AuditService(Collections.synchronizedList(new ArrayList<>()));
        return new WelcomeController(new GreetingService(strategy), audit);
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Era 3: Spring 6.x style (JDK 17+) ===");

        // Profile = "formal"
        System.out.println("\n[Profile: formal]");
        WelcomeController formal = buildContext("formal");
        System.out.println(formal.handleRequest("Alice"));

        // Profile = "casual"
        System.out.println("\n[Profile: casual]");
        WelcomeController casual = buildContext("casual");
        System.out.println(casual.handleRequest("Bob"));

        // Virtual-thread pool (Project Loom, JDK 21; Spring 6.1 supports this natively)
        System.out.println("\n[Virtual threads — Spring 6.1 Loom support]");
        AuditService sharedAudit = new AuditService(Collections.synchronizedList(new ArrayList<>()));
        WelcomeController shared = new WelcomeController(
            new GreetingService(new CasualGreeting("Hi")), sharedAudit);

        try (ExecutorService vThreadPool = Executors.newVirtualThreadPerTaskExecutor()) {
            List<Future<String>> results = new ArrayList<>();
            for (String name : List.of("Carol", "Dan", "Eve")) {
                results.add(vThreadPool.submit(() -> shared.handleRequest(name)));
            }
            for (Future<String> f : results) System.out.println("  " + f.get());
        }

        System.out.println("\nAudit log:");
        sharedAudit.printLog();

        System.out.println("\n=== Evolution summary ===");
        System.out.println("  Era 1 (XML):         setter injection, explicit bean declarations");
        System.out.println("  Era 2 (annotations): @Service + constructor injection + @Transactional");
        System.out.println("  Era 3 (modern):      records, sealed types, virtual threads, native images");
    }
}
```

How to run: `java EraThreeDemo.java` (JDK 17+; virtual thread block requires JDK 21+)

Records are immutable — no `setPrefix()` needed. Pattern-matching `switch` on the sealed `GreetingStrategy` is idiomatic Spring 6.x / JDK 17+ code. Virtual threads run the same `handleRequest` without blocking platform threads — exactly what Spring 6.1's Loom integration enables.

## 6. Walkthrough

**Era 1 walkthrough (Level 1):**

1. `loadApplicationContext()` plays the role of `ClassPathXmlApplicationContext("applicationContext.xml")` — creates beans and injects values.
2. `gs.setPrefix("Hello")` mirrors `<property name="prefix" value="Hello"/>` in XML.
3. `ctrl.setGreetingService(gs)` mirrors `<property name="greetingService" ref="greetingService"/>`.
4. `ctrl.handleRequest("Alice")` delegates through `greetingService.greet("Alice")` → `"Hello, Alice!"`.

**Era 2 walkthrough (Level 2):**

1. `buildContext` scans all `@Service`-annotated classes (simulated by explicit `ctx.put` calls).
2. `WelcomeController`'s constructor parameter types (`GreetingService`, `AuditService`) are matched against already-registered beans.
3. `ctrl.handleRequest("Alice")` now also audits the call via `AuditService.log`, showing cross-cutting concern wiring.

**Era 3 walkthrough (Level 3):**

1. `buildContext("formal")` acts as a `@Bean @Profile("formal")` method — returns a different `GreetingStrategy` based on active profile.
2. Pattern-matching `switch` on the sealed `GreetingStrategy` dispatches to the correct greeting format without `instanceof` chains.
3. `Executors.newVirtualThreadPerTaskExecutor()` creates a Loom virtual-thread pool. Three `handleRequest` calls execute concurrently on virtual threads, sharing the same `WelcomeController` instance safely because records are immutable.
4. The audit log shows which thread name handled each request — platform threads show `Thread-N`, virtual threads show `VirtualThread-N`.

**Data transformation at each era:**

| Era | Input | Processing | Output |
|---|---|---|---|
| 1 | XML declaration + method call | Setter injection + method dispatch | Greeting string printed |
| 2 | `@Service` + component-scan | Constructor injection + audit side effect | Greeting + audit log |
| 3 | Profile + virtual thread | Sealed type dispatch + concurrent processing | Greeting × 3, sorted audit log |

## 7. Gotchas & takeaways

> **Spring 6.x requires `jakarta.*` imports, not `javax.*`.** If you copy an old Spring 4/5 snippet and it imports `javax.servlet.*`, `javax.persistence.*`, or `javax.validation.*`, it will not compile against Spring 6 dependencies. The migration is mechanical but affects every file that touches the web layer, JPA, or Bean Validation.

> **Spring 5.3 is the last version supporting JDK 8 and Java EE (`javax.*`).** Projects that cannot upgrade to JDK 17 are stuck at Spring 5.3. That branch received maintenance until 2024; any project still on it should plan its JDK upgrade.

- Spring versions track closely with Java LTS releases: Spring 4 targeted JDK 8, Spring 6 targets JDK 17 (minimum), Spring 6.1 benefits from JDK 21 virtual threads.
- Spring Boot wraps Spring Framework; Boot 3.x is built on Framework 6.x. Upgrading Boot 2→3 implies all of the Framework 5→6 changes.
- Annotation-driven config (Era 2) is still the most common style in active codebases; know XML (Era 1) only to read legacy code.
- Records and sealed types (Era 3) are idiomatic Spring 6.x patterns because they're naturally immutable — perfect for beans.
- Spring's backwards-compatibility is strong within major versions but deliberately breaks between them; check the migration guide for each major upgrade.
