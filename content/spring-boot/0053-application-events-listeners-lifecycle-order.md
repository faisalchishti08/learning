---
card: spring-boot
gi: 53
slug: application-events-listeners-lifecycle-order
title: Application events & listeners (lifecycle order)
---

## 1. What it is

**Spring Boot application events** are lifecycle signals published by `SpringApplication` during startup and shutdown. Each event marks a specific stage. **`ApplicationListener`** beans (or `@EventListener` methods) react to these events to execute code at the right moment in the lifecycle.

The six key events in order:

| # | Event | When |
|---|---|---|
| 1 | `ApplicationStartingEvent` | Before any processing; no `ApplicationContext` yet |
| 2 | `ApplicationEnvironmentPreparedEvent` | `Environment` ready; `ApplicationContext` not yet created |
| 3 | `ApplicationContextInitializedEvent` | `ApplicationContext` created; beans not yet loaded |
| 4 | `ApplicationPreparedEvent` | Bean definitions loaded; context not yet refreshed |
| 5 | `ApplicationStartedEvent` | Context refreshed; `CommandLineRunner`s not yet called |
| 6 | `ApplicationReadyEvent` | App fully ready; `CommandLineRunner`s have run |

For errors: `ApplicationFailedEvent` fires if the context fails to start.

## 2. Why & when

Most application code uses `@PostConstruct` or `CommandLineRunner` for startup logic. Application events are needed when:

- You need to execute code **before** beans exist (events 1–4) — e.g. configure logging, set system properties, load cloud configuration.
- You need to differentiate between "context refreshed" (`ApplicationStartedEvent`) and "truly ready" (`ApplicationReadyEvent`).
- You are writing a library or framework component that must not depend on the application's beans being available.
- You need to react to failures (`ApplicationFailedEvent`) for cleanup or alerting.

For post-startup business logic, prefer `CommandLineRunner` or `ApplicationRunner` (tutorial 56), which are simpler.

## 3. Core concept

Spring Boot's startup is a linear pipeline. Think of events as **flag stations** on a racecourse: each station signals a stage completion. Listeners are spectators stationed at specific flags who act when the flag drops.

Registration matters:
- Listeners for events 1–4 (before `ApplicationContext` exists) **cannot** be `@Component` beans — the context doesn't exist yet to discover them. Register them via `SpringApplication.addListeners()` or `META-INF/spring.factories`.
- Listeners for events 5–6 (after context refresh) **can** be `@Component` beans with `@EventListener`.

A listener for `ApplicationReadyEvent` using the bean approach:
```java
@Component
public class StartupTask {
    @EventListener(ApplicationReadyEvent.class)
    public void onReady() {
        // safe: all beans exist, app is serving traffic
    }
}
```

A listener registered before the context (for early events):
```java
SpringApplication app = new SpringApplication(MyApp.class);
app.addListeners(new EarlySetupListener());  // runs before beans are created
app.run(args);
```

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot application event lifecycle order from ApplicationStartingEvent to ApplicationReadyEvent">
  <!-- Vertical timeline -->
  <line x1="100" y1="20" x2="100" y2="240" stroke="#8b949e" stroke-width="2" marker-end="url(#ev)"/>

  <!-- Events -->
  <circle cx="100" cy="40" r="7" fill="#3d2020" stroke="#f85149" stroke-width="2"/>
  <text x="118" y="45" fill="#f85149" font-size="11" font-family="monospace">1. ApplicationStartingEvent</text>
  <text x="118" y="58" fill="#8b949e" font-size="9" font-family="monospace">   no context, no environment</text>

  <circle cx="100" cy="80" r="7" fill="#1c2430" stroke="#8b949e" stroke-width="2"/>
  <text x="118" y="85" fill="#8b949e" font-size="11" font-family="monospace">2. ApplicationEnvironmentPreparedEvent</text>
  <text x="118" y="98" fill="#8b949e" font-size="9" font-family="monospace">   environment ready, no context yet</text>

  <circle cx="100" cy="120" r="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="118" y="125" fill="#79c0ff" font-size="11" font-family="monospace">3. ApplicationContextInitializedEvent</text>
  <text x="118" y="138" fill="#8b949e" font-size="9" font-family="monospace">   context created, beans not loaded</text>

  <circle cx="100" cy="160" r="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="118" y="165" fill="#79c0ff" font-size="11" font-family="monospace">4. ApplicationPreparedEvent</text>
  <text x="118" y="178" fill="#8b949e" font-size="9" font-family="monospace">   bean defs loaded, not refreshed</text>

  <circle cx="100" cy="200" r="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="118" y="205" fill="#6db33f" font-size="11" font-family="monospace">5. ApplicationStartedEvent</text>
  <text x="118" y="218" fill="#8b949e" font-size="9" font-family="monospace">   context refreshed, runners pending</text>

  <circle cx="100" cy="240" r="9" fill="#16202e" stroke="#6db33f" stroke-width="2.5"/>
  <text x="118" y="245" fill="#6db33f" font-size="12" font-family="monospace" font-weight="bold">6. ApplicationReadyEvent ← app live!</text>

  <defs>
    <marker id="ev" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Events fire in strict order; listeners must be registered before the event fires to receive it.

## 5. Runnable example

```java
// AppEventsDemo.java
// How to run: java AppEventsDemo.java  (JDK 17+)
// Simulates the Spring Boot application event lifecycle and listener registration.

import java.util.*;
import java.util.function.Consumer;

public class AppEventsDemo {

    // ── Simulated event types ─────────────────────────────────────
    enum Event {
        STARTING, ENVIRONMENT_PREPARED, CONTEXT_INITIALIZED,
        PREPARED, STARTED, READY, FAILED
    }

    // ── Listener registry ─────────────────────────────────────────
    static Map<Event, List<Consumer<String>>> listeners = new EnumMap<>(Event.class);

    static void addListener(Event e, Consumer<String> listener) {
        listeners.computeIfAbsent(e, k -> new ArrayList<>()).add(listener);
    }

    static void publish(Event event, String context) {
        System.out.println("\n[EVENT] " + event + " — " + context);
        listeners.getOrDefault(event, List.of()).forEach(l -> l.accept(context));
    }

    public static void main(String[] args) {
        // ── Register listeners BEFORE run() ─────────────────────────
        // Early listeners (must be registered programmatically — no context yet)
        addListener(Event.STARTING, ctx ->
            System.out.println("  EarlyListener: configuring JUL → SLF4J bridge"));

        addListener(Event.ENVIRONMENT_PREPARED, ctx ->
            System.out.println("  CloudConfigListener: loading remote config from Config Server"));

        addListener(Event.CONTEXT_INITIALIZED, ctx ->
            System.out.println("  LibraryInitializer: setting up low-level framework state"));

        // Late listeners (@EventListener beans — registered via context)
        addListener(Event.STARTED, ctx ->
            System.out.println("  MetricsBean: registering JVM metrics with Micrometer"));

        addListener(Event.READY, ctx ->
            System.out.println("  WarmupRunner: pre-populating caches"));

        addListener(Event.READY, ctx ->
            System.out.println("  StartupNotifier: sending Slack alert 'service is up'"));

        // ── Simulate the startup lifecycle ───────────────────────────
        System.out.println("=== Spring Boot Application Lifecycle ===");

        publish(Event.STARTING,              "before any processing");
        publish(Event.ENVIRONMENT_PREPARED,  "Environment ready; no ApplicationContext");
        publish(Event.CONTEXT_INITIALIZED,   "ApplicationContext instance created");
        publish(Event.PREPARED,              "bean definitions loaded; context not yet refreshed");
        publish(Event.STARTED,               "context refreshed; CommandLineRunners pending");
        System.out.println("\n  [executing CommandLineRunner and ApplicationRunner beans]");
        publish(Event.READY,                 "app fully ready; serving traffic");
    }
}
```

**How to run:** `java AppEventsDemo.java`

Expected output:
```
=== Spring Boot Application Lifecycle ===

[EVENT] STARTING — before any processing
  EarlyListener: configuring JUL → SLF4J bridge

[EVENT] ENVIRONMENT_PREPARED — Environment ready; no ApplicationContext
  CloudConfigListener: loading remote config from Config Server

[EVENT] CONTEXT_INITIALIZED — ApplicationContext instance created
  LibraryInitializer: setting up low-level framework state

[EVENT] PREPARED — bean definitions loaded; context not yet refreshed

[EVENT] STARTED — context refreshed; CommandLineRunners pending
  MetricsBean: registering JVM metrics with Micrometer

  [executing CommandLineRunner and ApplicationRunner beans]

[EVENT] READY — app fully ready; serving traffic
  WarmupRunner: pre-populating caches
  StartupNotifier: sending Slack alert 'service is up'
```

## 6. Walkthrough

- `addListener(Event.STARTING, ...)` registers before `run()`, simulating `SpringApplication.addListeners(...)` or `spring.factories`. These listeners receive early events before beans exist.
- `CloudConfigListener` on `ENVIRONMENT_PREPARED` mimics Spring Cloud Bootstrap's mechanism: remote config is loaded into the `Environment` before the `ApplicationContext` sees any `@Value` annotations.
- `MetricsBean` on `STARTED` is a `@EventListener` bean; it runs after context refresh when all beans are available.
- The `[executing CommandLineRunner...]` line shows that runners execute between `STARTED` and `READY`.
- Two listeners on `READY`: both run in registration order. Multiple `@EventListener` methods on `READY` are all called.

## 7. Gotchas & takeaways

> Registering a listener for `ApplicationStartingEvent` via `@Component` and `@EventListener` does not work — the context that would discover the bean doesn't exist yet. The listener silently misses the event. Use `SpringApplication.addListeners()` or `spring.factories` for events 1–4.

> `ApplicationReadyEvent` fires after `CommandLineRunner` and `ApplicationRunner` beans have executed. If a `CommandLineRunner` throws, the `ApplicationReadyEvent` is never published — `ApplicationFailedEvent` fires instead. Do not rely on `READY` as a heartbeat.

- For most "do something on startup" use cases, prefer `CommandLineRunner` / `ApplicationRunner` (simpler, tested via `@SpringBootTest`).
- Use `@Order(N)` on multiple listeners for the same event to control their relative execution order.
- Async listeners: annotate with `@Async` to run the listener in a separate thread (requires `@EnableAsync`).
- `ApplicationFailedEvent` carries the exception — use it for alerting or cleanup when startup fails.
- Test event listeners with `ApplicationContextRunner` or `@SpringBootTest` with a custom `ApplicationListener` registered in test setup.
