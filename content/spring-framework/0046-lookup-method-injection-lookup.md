---
card: spring-framework
gi: 46
slug: lookup-method-injection-lookup
title: Lookup method injection @Lookup
---

## 1. What it is

**`@Lookup` method injection** is the annotation form of Spring's lookup method feature. A method annotated with `@Lookup` is overridden by a CGLIB-generated subclass so that it returns a fresh instance from the container each time it is called.

```java
@Component
public abstract class CommandManager {

    public Object process(Object commandState) {
        Command cmd = createCommand();      // Spring overrides this
        cmd.setState(commandState);
        return cmd.execute();
    }

    @Lookup                                 // override: return ctx.getBean(Command.class)
    protected abstract Command createCommand();

    // With explicit bean name:
    @Lookup("specialCommand")
    protected abstract Command createSpecialCommand();
}
```

`@Lookup` can also be placed on a concrete method with an empty or stub body — Spring's CGLIB override ignores the body and always calls `ctx.getBean(returnType)`.

In one sentence: **`@Lookup` tells Spring to override the annotated method so it always calls `getBean()` and returns a fresh bean from the container — the clean solution when a singleton needs a new prototype instance per call.**

## 2. Why & when

`@Lookup` is the preferred solution when:

- A singleton bean needs a **new prototype instance** on each method call, not once at startup.
- You want to avoid coupling the bean to `ApplicationContext` by calling `ctx.getBean()` directly.
- `ObjectFactory<T>` or `Provider<T>` injection would work but you prefer a more declarative style.
- You have a natural "create command" / "create job" method in your design — `@Lookup` names it explicitly.

`@Lookup` does NOT help when you need a new bean for each HTTP request (`@RequestScope`) — use Spring's scoped proxies for that.

## 3. Core concept

```
Without @Lookup (problem):
  singleton CommandManager → autowired Command at startup
  → cmd.execute() always runs same Command instance

With @Lookup:
  Spring creates at startup:
    class CommandManager$$CGLIB extends CommandManager {
      @Override Command createCommand() {
          return applicationContext.getBean(Command.class); // fresh each call
      }
    }
  The registered "commandManager" bean is CommandManager$$CGLIB (singleton)
  Each process() call → createCommand() → new Command from context

Bean name resolution:
  @Lookup               → ctx.getBean(methodReturnType)
  @Lookup("beanName")  → ctx.getBean("beanName", returnType)
```

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@Lookup: Spring CGLIB subclass overrides the annotated method to call getBean each time">
  <defs>
    <marker id="a46" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b46" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Abstract class -->
  <rect x="10" y="20" width="220" height="100" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="42" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">CommandManager (abstract)</text>
  <text x="120" y="62" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">process(state) { ... }</text>
  <text x="120" y="80" fill="#e06c75" font-size="9" text-anchor="middle" font-family="sans-serif">@Lookup</text>
  <text x="120" y="96" fill="#e06c75" font-size="9" text-anchor="middle" font-family="sans-serif">abstract Command createCommand()</text>

  <!-- CGLIB arrow and box -->
  <line x1="120" y1="120" x2="120" y2="152" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a46)"/>
  <text x="135" y="138" fill="#6db33f" font-size="8" font-family="sans-serif">CGLIB</text>

  <rect x="10" y="155" width="220" height="38" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="174" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">CommandManager$$CGLIB</text>
  <text x="120" y="188" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">createCommand() → ctx.getBean(Command)</text>

  <!-- Container -->
  <rect x="300" y="55" width="170" height="60" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="385" y="79" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ApplicationContext</text>
  <text x="385" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">getBean(Command.class)</text>

  <line x1="230" y1="178" x2="297" y2="85"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#a46)"/>

  <!-- Prototype beans -->
  <rect x="530" y="20"  width="140" height="32" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="600" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Command (new #1)</text>
  <rect x="530" y="62"  width="140" height="32" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="600" y="82" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Command (new #2)</text>
  <rect x="530" y="104" width="140" height="32" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="600" y="124" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Command (new #3)</text>

  <line x1="470" y1="78" x2="527" y2="36"  stroke="#79c0ff" stroke-width="1" marker-end="url(#b46)"/>
  <line x1="470" y1="85" x2="527" y2="78"  stroke="#79c0ff" stroke-width="1" marker-end="url(#b46)"/>
  <line x1="470" y1="92" x2="527" y2="120" stroke="#79c0ff" stroke-width="1" marker-end="url(#b46)"/>
</svg>

Spring replaces the abstract `createCommand()` with a CGLIB override that calls `ctx.getBean(Command.class)`. Three calls to `process()` → three distinct `Command` instances.

## 5. Runnable example

Scenario: a `WorkerPool` singleton that spawns a fresh `WorkUnit` prototype on each `submitWork()` call. Demonstrate `@Lookup` with and without explicit bean name.

### Level 1 — Basic

`@Lookup` resolving by return type.

```java
// LookupDemo.java — run with: java LookupDemo.java
import java.lang.annotation.*;
import java.util.*;
import java.util.function.Supplier;

public class LookupDemo {

    @Retention(RetentionPolicy.RUNTIME) @interface Lookup { String value() default ""; }

    static int unitSeq = 0;

    // Prototype bean
    static class WorkUnit {
        final int id;
        String payload;

        WorkUnit() { this.id = ++unitSeq; }

        void configure(String payload) {
            System.out.println("  [PROTOTYPE] WorkUnit#" + id + " configured: " + payload);
            this.payload = payload;
        }

        String process() {
            return "WorkUnit#" + id + " processed: " + payload.toUpperCase();
        }
    }

    // Abstract singleton
    static abstract class WorkerPool {
        private int submittedCount = 0;

        // @Lookup: overridden by CGLIB to call ctx.getBean(WorkUnit.class)
        @Lookup
        protected abstract WorkUnit createUnit();

        String submitWork(String payload) {
            WorkUnit unit = createUnit();
            unit.configure(payload);
            submittedCount++;
            return unit.process() + " (total submitted: " + submittedCount + ")";
        }
    }

    // Simulate Spring CGLIB: create a subclass that overrides the @Lookup method
    static WorkerPool createWorkerPool(Supplier<WorkUnit> prototypeFactory) {
        return new WorkerPool() {
            @Override
            protected WorkUnit createUnit() {
                System.out.println("  [@Lookup] createUnit() → ctx.getBean(WorkUnit.class)");
                return prototypeFactory.get();
            }
        };
    }

    public static void main(String[] args) {
        System.out.println("=== Container creates singleton WorkerPool with @Lookup override ===");
        WorkerPool pool = createWorkerPool(WorkUnit::new);

        System.out.println("\n=== Three work submissions ===");
        System.out.println("  " + pool.submitWork("build-report-2026-Q1"));
        System.out.println("  " + pool.submitWork("export-csv-customers"));
        System.out.println("  " + pool.submitWork("sync-inventory-EU"));

        System.out.println("\n=== pool is the same singleton; WorkUnit instances are distinct ===");
        System.out.println("  Total WorkUnits created: " + unitSeq);
    }
}
```

How to run: `java LookupDemo.java`

`createWorkerPool()` simulates Spring's CGLIB: it returns a subclass whose `createUnit()` calls the prototype factory. Each `submitWork()` gets a fresh `WorkUnit`. `unitSeq` proves three distinct instances were created. `pool` is the same object on all three calls.

### Level 2 — Intermediate

`@Lookup("beanName")` resolving by explicit name — used when multiple beans share the same type.

```java
// LookupDemo2.java — run with: java LookupDemo2.java
import java.lang.annotation.*;
import java.util.*;
import java.util.function.Supplier;

public class LookupDemo2 {

    @Retention(RetentionPolicy.RUNTIME) @interface Lookup { String value() default ""; }

    static int jobSeq = 0;

    interface ExportJob {
        void configure(String target);
        String run();
        int getId();
    }

    static class CsvExportJob implements ExportJob {
        final int id = ++jobSeq;
        String target;
        CsvExportJob() { System.out.println("  [PROTO] CsvExportJob#" + id + " created"); }
        @Override public void configure(String t) { this.target = t; }
        @Override public String run() { return "CSV[#" + id + "] exported " + target; }
        @Override public int getId() { return id; }
    }

    static class XmlExportJob implements ExportJob {
        final int id = ++jobSeq;
        String target;
        XmlExportJob() { System.out.println("  [PROTO] XmlExportJob#" + id + " created"); }
        @Override public void configure(String t) { this.target = t; }
        @Override public String run() { return "XML[#" + id + "] exported " + target; }
        @Override public int getId() { return id; }
    }

    // Singleton — two @Lookup methods, each resolving a different bean name
    static abstract class ExportService {
        private final List<String> completed = new ArrayList<>();

        @Lookup("csvExportJob")           // explicit name
        protected abstract ExportJob createCsvJob();

        @Lookup("xmlExportJob")
        protected abstract ExportJob createXmlJob();

        String exportCsv(String target) {
            ExportJob job = createCsvJob();
            job.configure(target);
            String result = job.run();
            completed.add(result);
            return result;
        }

        String exportXml(String target) {
            ExportJob job = createXmlJob();
            job.configure(target);
            String result = job.run();
            completed.add(result);
            return result;
        }

        List<String> getCompleted() { return Collections.unmodifiableList(completed); }
    }

    static ExportService createExportService(
            Supplier<ExportJob> csvFactory, Supplier<ExportJob> xmlFactory) {
        return new ExportService() {
            @Override protected ExportJob createCsvJob() {
                System.out.println("  [@Lookup(\"csvExportJob\")] → ctx.getBean(\"csvExportJob\")");
                return csvFactory.get();
            }
            @Override protected ExportJob createXmlJob() {
                System.out.println("  [@Lookup(\"xmlExportJob\")] → ctx.getBean(\"xmlExportJob\")");
                return xmlFactory.get();
            }
        };
    }

    public static void main(String[] args) {
        System.out.println("=== Container startup ===");
        ExportService svc = createExportService(CsvExportJob::new, XmlExportJob::new);

        System.out.println("\n=== Export operations ===");
        System.out.println("  " + svc.exportCsv("customers-table"));
        System.out.println("  " + svc.exportCsv("orders-table"));
        System.out.println("  " + svc.exportXml("product-catalog"));
        System.out.println("  " + svc.exportXml("inventory-data"));

        System.out.println("\n=== Completed jobs ===");
        svc.getCompleted().forEach(r -> System.out.println("  " + r));
        System.out.println("  Total job instances: " + jobSeq);
    }
}
```

How to run: `java LookupDemo2.java`

Two `@Lookup` methods with different bean names: `createCsvJob()` always returns a new `CsvExportJob`, `createXmlJob()` always returns a new `XmlExportJob`. Four calls → four distinct prototype instances. The singleton `svc` holds only the completed results list.

### Level 3 — Advanced

`@Lookup` in a pipeline: singleton `PipelineEngine` creates fresh `Stage` prototypes per pipeline run. Each `Stage` carries its own state and results.

```java
// LookupDemo3.java — run with: java LookupDemo3.java
import java.util.*;
import java.util.function.Supplier;

public class LookupDemo3 {

    static int stageSeq = 0;

    // Prototype: one per pipeline run step
    static class PipelineStage {
        final int id;
        String name;
        final List<String> log = new ArrayList<>();
        boolean failed = false;

        PipelineStage() { this.id = ++stageSeq; }

        void configure(String name) {
            this.name = name;
            System.out.println("  [PROTO] PipelineStage#" + id + " configured as '" + name + "'");
        }

        boolean execute(Map<String, Object> context) {
            log.add("Stage#" + id + ":" + name + " START context=" + context.keySet());
            // Simulate: 'validate' stage fails if no 'data' key
            if (name.equals("validate") && !context.containsKey("data")) {
                log.add("FAIL: 'data' key missing");
                failed = true;
                return false;
            }
            context.put(name + ".result", "OK#" + id);
            log.add("Stage#" + id + ":" + name + " DONE");
            return true;
        }

        List<String> getLog() { return Collections.unmodifiableList(log); }
    }

    // Singleton pipeline engine — creates fresh PipelineStage per run
    static abstract class PipelineEngine {
        private int runCount = 0;

        // @Lookup — Spring overrides to return ctx.getBean(PipelineStage.class)
        protected abstract PipelineStage createStage();

        Map<String, Object> run(String pipelineName, List<String> stageNames,
                                Map<String, Object> input) {
            runCount++;
            System.out.printf("%n  === Pipeline run #%d: %s ===%n", runCount, pipelineName);
            Map<String, Object> ctx = new HashMap<>(input);

            for (String stageName : stageNames) {
                PipelineStage stage = createStage();   // fresh prototype per stage
                stage.configure(stageName);
                boolean ok = stage.execute(ctx);
                stage.getLog().forEach(l -> System.out.println("    " + l));
                if (!ok) {
                    ctx.put("pipeline.failed", true);
                    ctx.put("pipeline.failedStage", stageName);
                    break;
                }
            }

            ctx.put("pipeline.name", pipelineName);
            ctx.put("pipeline.runId", runCount);
            return ctx;
        }

        int getRunCount() { return runCount; }
    }

    static PipelineEngine createEngine(Supplier<PipelineStage> stageFactory) {
        return new PipelineEngine() {
            @Override protected PipelineStage createStage() {
                return stageFactory.get();
            }
        };
    }

    public static void main(String[] args) {
        System.out.println("=== Container: PipelineEngine singleton + PipelineStage prototype ===");
        PipelineEngine engine = createEngine(PipelineStage::new);

        System.out.println("\n=== Run 1: successful pipeline ===");
        Map<String, Object> result1 = engine.run(
            "order-processing",
            List.of("enrich", "validate", "transform", "publish"),
            Map.of("orderId", "ORD-001", "data", "order payload")
        );
        System.out.println("  Result: " + result1.get("pipeline.name")
            + " runId=" + result1.get("pipeline.runId")
            + " failed=" + result1.get("pipeline.failed"));

        System.out.println("\n=== Run 2: failing pipeline (no 'data' key) ===");
        Map<String, Object> result2 = engine.run(
            "incomplete-pipeline",
            List.of("enrich", "validate", "transform"),
            Map.of("orderId", "ORD-002")   // missing 'data'
        );
        System.out.println("  Result: failed=" + result2.get("pipeline.failed")
            + " failedStage=" + result2.get("pipeline.failedStage"));

        System.out.println("\n=== Summary ===");
        System.out.println("  Engine run count: " + engine.getRunCount());
        System.out.println("  Total PipelineStage instances created: " + stageSeq);
    }
}
```

How to run: `java LookupDemo3.java`

`PipelineEngine` is a singleton with `runCount` accumulated across runs. Each `run()` call creates one `PipelineStage` per stage name via `createStage()` — every stage is a fresh prototype. Run 1 creates 4 stages (IDs 1–4). Run 2 creates 2 stages (IDs 5–6, stops at `validate` failure). `stageSeq` equals 6 total.

## 6. Walkthrough

**Level 3 — Run 1 stage sequence:**

```
engine.run("order-processing", ["enrich","validate","transform","publish"], {orderId,data}):

  stage = createStage() → new PipelineStage() → id=1
  stage.configure("enrich")
  stage.execute({orderId,data})
    → context.containsKey("data") = true → proceed
    → ctx["enrich.result"] = "OK#1"
    → return true ✓

  stage = createStage() → new PipelineStage() → id=2
  stage.configure("validate")
  stage.execute({orderId,data,enrich.result})
    → data key present → proceed
    → ctx["validate.result"] = "OK#2"
    → return true ✓

  ... (id=3 transform, id=4 publish — both succeed)

  ctx = {orderId=ORD-001, data=..., enrich.result=OK#1, validate.result=OK#2,
         transform.result=OK#3, publish.result=OK#4,
         pipeline.name=order-processing, pipeline.runId=1}
```

## 7. Gotchas & takeaways

> **`@Lookup` requires CGLIB bytecode generation.** The class must not be `final`, and the annotated method must not be `final`, `static`, or `private`. Mark the class and method as `abstract` or `protected` for clarity.

> **`@Lookup` does not work on beans instantiated with `new`.** Spring must create the bean instance itself to apply the CGLIB override. If you write `new CommandManager()`, the `createCommand()` method is abstract and will throw `AbstractMethodError`.

- `@Lookup` is annotation-equivalent to XML `<lookup-method name="createCommand" bean="command"/>` — same capability, cleaner syntax.
- `ObjectFactory<Command>` or `javax.inject.Provider<Command>` as a constructor-injected field achieves the same result — call `factory.getObject()` / `provider.get()` instead of the lookup method.
- `@Lookup` is the cleanest approach when the "create a command" behavior is a natural part of the class's contract and you want it named in the method signature.
- If the prototype bean has constructor parameters, use `@Lookup` with an explicit bean name that maps to a `@Bean` factory method.
