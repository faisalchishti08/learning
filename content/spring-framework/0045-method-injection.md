---
card: spring-framework
gi: 45
slug: method-injection
title: Method injection
---

## 1. What it is

**Method injection** is a Spring feature that lets a singleton bean **call a method that returns a new prototype-scoped bean on each invocation**, even though the singleton bean itself cannot hold a reference to the prototype factory directly.

The classic problem: a singleton `CommandManager` needs a new `Command` instance every time `process()` is called. If `Command` is injected once via constructor, the singleton always reuses the same `Command` instance — prototype scope is lost.

Spring offers two solutions under "method injection":

1. **Lookup method injection** — Spring overrides an abstract method via CGLIB to return a new prototype bean each time it is called.
2. **Arbitrary method replacement** — Spring replaces any method body with a custom `MethodReplacer` implementation.

```java
@Component
public abstract class CommandManager {

    public Object process(Object commandState) {
        Command command = createCommand();   // abstract — Spring overrides this
        command.setState(commandState);
        return command.execute();
    }

    @Lookup                             // Spring provides the implementation
    protected abstract Command createCommand();
}
```

In one sentence: **Method injection solves the singleton-consumes-prototype problem by letting Spring override a method in a singleton bean so it returns a fresh prototype bean on every call, without the singleton holding a reference to the `ApplicationContext`.**

## 2. Why & when

The scope mismatch problem arises when:

- A **singleton bean** (`CommandManager`) needs to use a **prototype bean** (`Command`) that carries per-request state.
- Simply `@Autowired`-injecting the prototype into the singleton gives the singleton a fixed reference — the prototype is created once at startup and reused, breaking its prototype nature.

Alternatives:
- Implement `ApplicationContextAware` and call `ctx.getBean(Command.class)` — works but couples the bean to the container API.
- Use `ObjectFactory<Command>` or `Provider<Command>` — cleaner, but requires an extra field.
- **`@Lookup` (lookup method injection)** — cleanest; the method declaration is the contract, and Spring provides the implementation via CGLIB.

## 3. Core concept

```
Singleton + prototype injection — the problem:

  @Singleton CommandManager:
    @Autowired Command command;  ← created ONCE at startup
    process(state) → command.setState(state) → execute()
    // same Command instance on every process() call — breaks prototype

Lookup method injection — the solution:

  CommandManager is abstract; createCommand() is abstract
  Spring creates a CGLIB subclass of CommandManager at startup:
    class CommandManager$$SpringCGLIB extends CommandManager {
        @Override
        Command createCommand() {
            return ctx.getBean(Command.class);  // new instance each call
        }
    }
  The singleton CommandManager now creates a fresh Command per call
  without knowing about the ApplicationContext
```

## 4. Diagram

<svg viewBox="0 0 680 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Method injection: CGLIB subclass overrides createCommand() to get a fresh prototype bean from the context on each call">
  <defs>
    <marker id="a45" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b45" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Singleton box -->
  <rect x="10" y="25" width="210" height="120" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="115" y="45" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">CommandManager (singleton)</text>
  <text x="115" y="62" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">process(state) { ... }</text>
  <text x="115" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">abstract createCommand()</text>

  <!-- CGLIB subclass -->
  <rect x="10" y="170" width="210" height="28" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="115" y="188" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">CommandManager$$CGLIB extends above</text>

  <line x1="115" y1="145" x2="115" y2="167" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a45)"/>

  <!-- createCommand override box -->
  <rect x="270" y="140" width="225" height="58" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="383" y="162" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@Override createCommand()</text>
  <text x="383" y="180" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">return ctx.getBean(Command.class)</text>

  <line x1="220" y1="183" x2="267" y2="168" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a45)"/>

  <!-- Prototype beans -->
  <rect x="540" y="30"  width="130" height="36" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="605" y="53" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Command (new #1)</text>

  <rect x="540" y="82"  width="130" height="36" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="605" y="105" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Command (new #2)</text>

  <rect x="540" y="134" width="130" height="36" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="605" y="157" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Command (new #3)</text>

  <line x1="495" y1="158" x2="537" y2="48"  stroke="#79c0ff" stroke-width="1.2" marker-end="url(#b45)"/>
  <line x1="495" y1="162" x2="537" y2="100" stroke="#79c0ff" stroke-width="1.2" marker-end="url(#b45)"/>
  <line x1="495" y1="168" x2="537" y2="152" stroke="#79c0ff" stroke-width="1.2" marker-end="url(#b45)"/>

  <text x="340" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Each process() call creates a fresh Command via CGLIB override</text>
</svg>

Spring creates a CGLIB subclass of `CommandManager` that overrides `createCommand()`. Each call to `process()` gets a fresh `Command` prototype — the singleton itself never holds a stale reference.

## 5. Runnable example

Scenario: a `TaskDispatcher` singleton that needs a fresh `Task` prototype per dispatch. Demonstrate the problem first, then solve it with method injection.

### Level 1 — Basic

Show the scope mismatch problem, then the manual `@Lookup`-style fix.

```java
// MethodInjectionDemo.java — run with: java MethodInjectionDemo.java

public class MethodInjectionDemo {

    static int taskCounter = 0;

    static class Task {
        final int id;
        String state;

        Task() {
            this.id = ++taskCounter;
            System.out.println("  [TASK] new Task#" + id + " created");
        }

        void setState(String state) { this.state = state; }
        String execute() {
            return "Task#" + id + " executing state=" + state;
        }
    }

    // --- Problem: singleton holds one Task ---
    static class BrokenTaskDispatcher {
        private final Task task;   // injected once — stale after first use

        BrokenTaskDispatcher(Task task) { this.task = task; }

        String dispatch(String state) {
            task.setState(state);
            return task.execute();
        }
    }

    // --- Solution: lookup method returns fresh Task every time ---
    // In real Spring: abstract class + @Lookup; here: interface + lambda
    interface TaskSupplier { Task get(); }

    static class FixedTaskDispatcher {
        private final TaskSupplier taskSupplier;   // factory, not a fixed Task

        FixedTaskDispatcher(TaskSupplier taskSupplier) { this.taskSupplier = taskSupplier; }

        String dispatch(String state) {
            Task task = taskSupplier.get();   // new Task each call (prototype scope)
            task.setState(state);
            return task.execute();
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Problem: singleton holds fixed Task ===");
        BrokenTaskDispatcher broken = new BrokenTaskDispatcher(new Task());
        System.out.println("  " + broken.dispatch("order-1"));
        System.out.println("  " + broken.dispatch("order-2"));
        System.out.println("  " + broken.dispatch("order-3"));
        System.out.println("  All used Task#" + 1 + " — prototype lost!");

        taskCounter = 0;  // reset for demo clarity

        System.out.println("\n=== Solution: lookup method (factory) ===");
        // taskSupplier = the CGLIB-overridden createTask() equivalent
        FixedTaskDispatcher fixed = new FixedTaskDispatcher(Task::new);
        System.out.println("  " + fixed.dispatch("order-1"));
        System.out.println("  " + fixed.dispatch("order-2"));
        System.out.println("  " + fixed.dispatch("order-3"));
        System.out.println("  Each dispatch got a fresh Task — prototype scope preserved!");
    }
}
```

How to run: `java MethodInjectionDemo.java`

`BrokenTaskDispatcher` holds a single `Task` — all three dispatches share `Task#1`. `FixedTaskDispatcher` holds a `TaskSupplier` factory (equivalent to a CGLIB-overridden `@Lookup` method) — each dispatch creates a new `Task`. The `Task::new` constructor reference simulates what Spring's CGLIB override does.

### Level 2 — Intermediate

Abstract class with lookup method, CGLIB-style override implemented with reflection.

```java
// MethodInjectionDemo2.java — run with: java MethodInjectionDemo2.java
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;
import java.util.function.Supplier;

public class MethodInjectionDemo2 {

    @Retention(RetentionPolicy.RUNTIME) @interface Lookup { Class<?> value(); }

    static int notifCounter = 0;

    // Prototype bean
    static class Notification {
        final int id;
        String    recipient;
        String    message;

        Notification() {
            this.id = ++notifCounter;
            System.out.println("  [PROTOTYPE] Notification#" + id + " created");
        }

        void configure(String recipient, String message) {
            this.recipient = recipient; this.message = message;
        }

        String send() { return "SENT Notification#" + id + " → " + recipient + ": " + message; }
    }

    // Abstract singleton — createNotification() will be overridden
    static abstract class NotificationDispatcher {
        private int dispatchCount = 0;

        // The abstract method — Spring (or our container) provides the body
        @Lookup(Notification.class)
        protected abstract Notification createNotification();

        String dispatch(String recipient, String message) {
            Notification notif = createNotification();   // each call → new Notification
            notif.configure(recipient, message);
            dispatchCount++;
            return notif.send() + " [dispatch#" + dispatchCount + "]";
        }
    }

    // Simulated CGLIB: create a subclass at runtime using a Proxy / anonymous class
    static NotificationDispatcher createWithLookupMethod(Supplier<Notification> factory) {
        return new NotificationDispatcher() {
            @Override
            protected Notification createNotification() {
                System.out.println("  [CGLIB] createNotification() → fetching prototype");
                return factory.get();
            }
        };
    }

    public static void main(String[] args) {
        System.out.println("=== Container startup: create singleton with CGLIB-like override ===");
        // Supplier simulates "ctx.getBean(Notification.class)" — new instance each call
        NotificationDispatcher dispatcher = createWithLookupMethod(Notification::new);

        System.out.println("\n=== Three dispatches → three distinct Notification instances ===");
        System.out.println("  " + dispatcher.dispatch("alice@example.com", "Your order is shipped"));
        System.out.println("  " + dispatcher.dispatch("bob@example.com",   "Payment received"));
        System.out.println("  " + dispatcher.dispatch("carol@example.com", "Account created"));

        System.out.println("\n=== The singleton itself ===");
        System.out.println("  Same dispatcher instance: " + dispatcher.getClass().getSimpleName());
    }
}
```

How to run: `java MethodInjectionDemo2.java`

`createWithLookupMethod()` returns an anonymous subclass of `NotificationDispatcher` that overrides `createNotification()` — mirroring what Spring CGLIB does for `@Lookup` methods. Each `dispatch()` call creates a new `Notification` prototype, while `dispatcher` itself is a singleton.

### Level 3 — Advanced

Full pipeline: singleton `ReportRunner` dispatches to fresh prototype `ReportJob` instances, each with their own config and state.

```java
// MethodInjectionDemo3.java — run with: java MethodInjectionDemo3.java
import java.util.*;
import java.util.function.Supplier;

public class MethodInjectionDemo3 {

    static int jobIdSeq = 0;

    // Prototype bean — one per report run
    static class ReportJob {
        final int id;
        private String  reportType;
        private String  target;
        private boolean completed = false;
        private final List<String> results = new ArrayList<>();

        ReportJob() {
            this.id = ++jobIdSeq;
            System.out.println("    [PROTOTYPE] ReportJob#" + id + " created");
        }

        void configure(String type, String target) {
            this.reportType = type; this.target = target;
        }

        void run() {
            System.out.println("    [JOB#" + id + "] running " + reportType + " on " + target);
            results.add("ReportJob#" + id + ":" + reportType + " → " + target.toUpperCase());
            results.add("rows: " + (int)(Math.random() * 900 + 100));
            completed = true;
        }

        List<String> getResults() { return Collections.unmodifiableList(results); }
        boolean isCompleted() { return completed; }
        int getId() { return id; }
    }

    // Abstract singleton — @Lookup method
    static abstract class ReportRunner {
        private final Map<Integer, List<String>> archive = new LinkedHashMap<>();

        // @Lookup method — overridden by container
        protected abstract ReportJob newJob();

        String run(String reportType, String target) {
            ReportJob job = newJob();
            job.configure(reportType, target);
            job.run();
            archive.put(job.getId(), job.getResults());
            return "ReportJob#" + job.getId() + " completed: " + job.getResults();
        }

        int runBatch(List<String[]> batch) {
            // Each item in batch gets its own fresh ReportJob
            batch.forEach(spec -> run(spec[0], spec[1]));
            return batch.size();
        }

        void printArchive() {
            System.out.println("  Archive (" + archive.size() + " jobs):");
            archive.forEach((id, res) -> System.out.println("    Job#" + id + ": " + res));
        }
    }

    // Container helper: create CGLIB-like subclass with overridden newJob()
    static ReportRunner createRunner(Supplier<ReportJob> jobFactory) {
        return new ReportRunner() {
            @Override
            protected ReportJob newJob() {
                System.out.println("  [CGLIB] newJob() → creating prototype ReportJob");
                return jobFactory.get();
            }
        };
    }

    public static void main(String[] args) {
        System.out.println("=== Container startup ===");
        // Supplier<ReportJob> = ctx.getBean(ReportJob.class) — new instance each call
        ReportRunner runner = createRunner(ReportJob::new);

        System.out.println("\n=== Single runs ===");
        System.out.println("  " + runner.run("SalesReport",    "region:APAC"));
        System.out.println("  " + runner.run("InventoryAudit", "warehouse:EU-1"));

        System.out.println("\n=== Batch run (3 jobs, each fresh ReportJob) ===");
        int ran = runner.runBatch(List.of(
            new String[]{"ComplianceReport", "entity:FIN-001"},
            new String[]{"RevenueReport",    "quarter:2026-Q1"},
            new String[]{"UsageReport",      "service:api-v2"}
        ));
        System.out.println("  Batch completed: " + ran + " jobs");

        System.out.println("\n=== Job archive ===");
        runner.printArchive();

        System.out.println("\n=== runner is a singleton — jobIdSeq reflects unique jobs ===");
        System.out.println("  Total distinct ReportJob instances created: " + jobIdSeq);
    }
}
```

How to run: `java MethodInjectionDemo3.java`

`ReportRunner` is a singleton. `ReportJob` is a prototype. Every `run()` and every iteration of `runBatch()` calls `newJob()`, which returns a fresh `ReportJob`. The archive accumulates results from 5 distinct jobs (IDs 1–5). `runner` itself is created once. `jobIdSeq` equals the number of `ReportJob` instances created — each increments it.

## 6. Walkthrough

**Level 3 — batch run internals:**

```
runner.runBatch([["ComplianceReport","entity:FIN-001"], ...]):
  batch.forEach(spec -> run(spec[0], spec[1])):

    run("ComplianceReport", "entity:FIN-001"):
      job = newJob()    ← CGLIB override → new ReportJob() → id=3
      job.configure("ComplianceReport", "entity:FIN-001")
      job.run()         → results: ["ReportJob#3:ComplianceReport → ENTITY:FIN-001", "rows: NNN"]
      archive[3] = [...]

    run("RevenueReport", "quarter:2026-Q1"):
      job = newJob()    ← new ReportJob() → id=4
      ...

    run("UsageReport", "service:api-v2"):
      job = newJob()    ← new ReportJob() → id=5
      ...
```

**Key invariant:** `runner` singleton is created once. `newJob()` creates a new `ReportJob` on every call. The singleton never holds a reference to a specific `ReportJob` after `run()` returns — only the archive map holds results.

## 7. Gotchas & takeaways

> **`@Lookup` requires CGLIB, which requires the class to be non-final and the method to be non-final, non-static, non-private.** Spring creates a subclass at runtime to override the method. If the class or method is `final`, Spring throws an exception at startup.

> **The class annotated with `@Lookup` must be a Spring-managed bean.** You cannot use `@Lookup` on a class you instantiate yourself with `new`. Spring must be the one creating the proxy subclass.

- `@Lookup` is equivalent to `ObjectFactory<T>` injection — both solve the singleton-prototype scope mismatch.
- `ApplicationContext.getBean(T.class)` inside a Spring bean works too, but couples the bean to the container API — `@Lookup` avoids this coupling.
- Arbitrary method replacement (using `MethodReplacer`) is even more flexible — it can replace any method, not just prototype lookups — but it is rarely needed in modern Spring and predates lambda/functional solutions.
- Spring Boot auto-detects `@Lookup` on abstract methods when component scanning is enabled — no extra XML configuration needed.
