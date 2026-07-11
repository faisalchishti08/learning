---
card: spring-cloud
gi: 128
slug: spring-cloud-data-flow-overview-orchestration
title: "Spring Cloud Data Flow overview (orchestration)"
---

## 1. What it is

Spring Cloud Data Flow is an orchestration platform sitting above Spring Cloud Stream and Spring Cloud Task — it provides a server, a shell/UI, and a DSL for composing pre-built or custom stream applications into data pipelines and task applications into scheduled or on-demand jobs, then deploying and managing the lifecycle of those pipelines and jobs across a target runtime (Kubernetes, Cloud Foundry, or a local environment), without requiring an operator to manually wire together and deploy each individual stream/task application by hand.

```
dataflow:> stream create --name order-pipeline --definition "http | filter --expression=payload.amount>100 | jdbc" --deploy
dataflow:> task create --name import-orders --definition "import-orders-task"
dataflow:> task launch import-orders
```

```yaml
# Data Flow deploys and manages the ACTUAL underlying Spring Cloud Stream/Task applications
# -- "http", "filter", "jdbc" are pre-built or custom Spring Cloud Stream applications, composed via the DSL
```

## 2. Why & when

Building individual Spring Cloud Stream applications (a source, a processor, a sink) and Spring Cloud Task applications, as earlier cards covered, gives the building blocks — but assembling several of them into an actual working pipeline (deploying each one, wiring their bindings together, monitoring the whole pipeline's health, redeploying when one stage needs updating) is significant operational work if done manually, application by application. Spring Cloud Data Flow provides exactly this orchestration layer: a simple DSL (`source | processor | sink`) describes an entire pipeline's topology in one line, and the Data Flow server handles translating that into actual deployed instances of each named application, wiring their message broker bindings together automatically, and providing a unified view of the whole pipeline's health and throughput.

Reach for Spring Cloud Data Flow when:

- Composing multiple Spring Cloud Stream applications into an actual data pipeline (ingest, transform, sink) and wanting a single tool to define, deploy, monitor, and manage that pipeline's full lifecycle, rather than manually deploying and wiring each stage independently.
- Orchestrating Spring Cloud Task applications — scheduling recurring batch jobs, launching on-demand data processing tasks, and tracking their execution history — with a centralized view across many task definitions, rather than each task application managing its own scheduling independently.
- A library of common, reusable pre-built stream applications (an `http` source, a `jdbc` sink, a `filter` processor, and many others in the Data Flow ecosystem) covers a meaningful part of a needed pipeline, letting a team assemble a working pipeline from existing components plus a small amount of custom application code, rather than writing every stage from scratch.

## 3. Core concept

```
 Data Flow DSL describes the TOPOLOGY, not the deployment mechanics:

   stream create --definition "http | filter --expression=... | jdbc"
     http:   pre-built SOURCE application (receives HTTP POSTs, publishes to the stream)
     filter: pre-built PROCESSOR application (drops messages not matching an expression)
     jdbc:   pre-built SINK application (writes accepted messages to a database)

 Data Flow SERVER translates this ONE line into:
   1. deploying an instance of the "http" application
   2. deploying an instance of the "filter" application
   3. deploying an instance of the "jdbc" application
   4. wiring each one's Spring Cloud Stream bindings so messages flow http -> filter -> jdbc, IN ORDER
   5. monitoring the deployed pipeline's health going forward
```

The DSL is deliberately declarative — an operator describes *what* pipeline they want, and the Data Flow server figures out *how* to actually deploy and connect the underlying applications to realize it.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single Data Flow DSL line describing a source filter sink pipeline is translated by the Data Flow server into three separately deployed and automatically wired Spring Cloud Stream applications">
  <rect x="20" y="20" width="600" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="30" y="42" fill="#6db33f" font-size="8" font-family="sans-serif">stream create --definition "http | filter --expression=payload.amount&gt;100 | jdbc"</text>

  <rect x="20" y="100" width="170" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="105" y="128" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">http (source)</text>

  <rect x="235" y="100" width="170" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="128" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">filter (processor)</text>

  <rect x="450" y="100" width="170" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="535" y="128" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">jdbc (sink)</text>

  <defs><marker id="a128" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="190" y1="123" x2="235" y2="123" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a128)"/>
  <line x1="405" y1="123" x2="450" y2="123" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a128)"/>
  <line x1="320" y1="54" x2="320" y2="100" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>
</svg>

One declarative line at the top, three independently deployed, automatically-wired applications underneath.

## 5. Runnable example

The scenario: model Data Flow's DSL parsing and pipeline deployment orchestration — parsing a `source | processor | sink` definition into individual application deployments, then wiring simulated bindings between them so a message actually flows end to end through the deployed pipeline. Start with parsing the DSL into stages, then add deploying each stage and wiring bindings, then add a full message flowing through the assembled pipeline, mirroring what actually happens after a `stream create --deploy` command.

### Level 1 — Basic

Parsing a Data Flow stream definition string into its individual application stages.

```java
import java.util.*;

public class DataFlowOverviewLevel1 {
    static List<String> parseStreamDefinition(String definition) {
        String[] stages = definition.split("\\|");
        List<String> parsed = new ArrayList<>();
        for (String stage : stages) parsed.add(stage.trim());
        return parsed;
    }

    public static void main(String[] args) {
        String definition = "http | filter | jdbc";
        List<String> stages = parseStreamDefinition(definition);

        System.out.println("parsed stages: " + stages);
    }
}
```

How to run: `java DataFlowOverviewLevel1.java`

`parseStreamDefinition` splits the pipe-separated DSL string into three individual application names — this is the first step Data Flow's server performs when a `stream create` command is issued, before any actual deployment happens.

### Level 2 — Intermediate

Add deploying each parsed stage and wiring simulated stream bindings between adjacent stages, mirroring how the Data Flow server connects a pipeline's applications.

```java
import java.util.*;
import java.util.function.Function;

public class DataFlowOverviewLevel2 {
    static List<String> parseStreamDefinition(String definition) {
        List<String> parsed = new ArrayList<>();
        for (String stage : definition.split("\\|")) parsed.add(stage.trim());
        return parsed;
    }

    // stands in for the ACTUAL deployed Spring Cloud Stream applications
    static Map<String, Function<String, String>> applicationRegistry = Map.of(
            "http", input -> input, // source: just emits whatever it received
            "filter", input -> input.contains("REJECT") ? null : input, // processor: drops rejected messages
            "jdbc", input -> "PERSISTED: " + input // sink: "writes" to a database
    );

    static void deployAndWirePipeline(List<String> stages) {
        System.out.println("deploying pipeline stages: " + stages);
        for (String stage : stages) {
            System.out.println("  deployed application: " + stage + " (bindings auto-wired to adjacent stages)");
        }
    }

    public static void main(String[] args) {
        List<String> stages = parseStreamDefinition("http | filter | jdbc");
        deployAndWirePipeline(stages);
    }
}
```

How to run: `java DataFlowOverviewLevel2.java`

Each stage is reported as independently deployed — `applicationRegistry` models the actual, separately-running Spring Cloud Stream application each stage name refers to, exactly as Data Flow deploys real, independent application instances for `http`, `filter`, and `jdbc`, wiring their stream bindings together rather than combining them into one process.

### Level 3 — Advanced

Add a full message actually flowing through the assembled, wired pipeline — from the source, through the processor (which may drop it), to the sink — mirroring the real end-to-end data flow a deployed Data Flow pipeline produces.

```java
import java.util.*;
import java.util.function.Function;

public class DataFlowOverviewLevel3 {
    static List<String> parseStreamDefinition(String definition) {
        List<String> parsed = new ArrayList<>();
        for (String stage : definition.split("\\|")) parsed.add(stage.trim());
        return parsed;
    }

    static Map<String, Function<String, String>> applicationRegistry = Map.of(
            "http", input -> input,
            "filter", input -> input.contains("amount=50") ? null : input, // drops orders with amount=50 specifically
            "jdbc", input -> "PERSISTED: " + input
    );

    // models the WIRED pipeline: a message flows stage by stage, stopping if any stage returns null (dropped)
    static String runThroughPipeline(List<String> stages, String message) {
        String current = message;
        for (String stage : stages) {
            if (current == null) {
                System.out.println("  message DROPPED before reaching stage: " + stage);
                return null;
            }
            Function<String, String> application = applicationRegistry.get(stage);
            current = application.apply(current);
            System.out.println("  after stage '" + stage + "': " + current);
        }
        return current;
    }

    public static void main(String[] args) {
        List<String> stages = parseStreamDefinition("http | filter | jdbc");

        System.out.println("-- message 1: amount=150 (should pass through fully) --");
        String result1 = runThroughPipeline(stages, "order amount=150");
        System.out.println("final result: " + result1);

        System.out.println("-- message 2: amount=50 (should be FILTERED OUT) --");
        String result2 = runThroughPipeline(stages, "order amount=50");
        System.out.println("final result: " + result2);
    }
}
```

How to run: `java DataFlowOverviewLevel3.java`

The first message (`"order amount=150"`) passes through all three stages unmodified by `http`, unfiltered by `filter` (since it doesn't contain `"amount=50"`), and reaches `jdbc`, which prepends `"PERSISTED: "`; the second message (`"order amount=50"`) is dropped by the `filter` stage (returning `null`), so `runThroughPipeline`'s loop detects `current == null` before reaching the `jdbc` stage and reports the message as dropped rather than incorrectly attempting to persist it — this mirrors exactly how a real deployed Data Flow pipeline's `filter` application would drop non-matching messages before they ever reach the downstream `jdbc` sink application.

## 6. Walkthrough

Trace `runThroughPipeline(stages, "order amount=50")` in Level 3.

1. `current = "order amount=50"` initially; the `for` loop's first iteration processes `stage = "http"`.
2. `current == null` is `false`, so processing proceeds — `applicationRegistry.get("http")` returns the identity function, `application.apply(current)` returns `"order amount=50"` unchanged, and this is printed as the state after the `http` stage.
3. The loop's second iteration processes `stage = "filter"` — `current` is still non-null, so `applicationRegistry.get("filter")` is invoked: `input.contains("amount=50")` checks `"order amount=50".contains("amount=50")`, which is `true`, so the filter function returns `null`.
4. `current` is now reassigned to `null`, and this is printed as the state after the `filter` stage (`"after stage 'filter': null"`).
5. The loop's third iteration processes `stage = "jdbc"` — this time, `current == null` is checked *first*, before attempting to apply the `jdbc` stage's function, and it's `true`, so the method prints `"message DROPPED before reaching stage: jdbc"` and immediately returns `null` from `runThroughPipeline`, without ever calling `jdbc`'s function on a null value.
6. `main`'s final `println` for this message correctly reports `final result: null` — the message never reached the persistence stage at all, exactly matching what a real Data Flow pipeline's `filter` application dropping a message would produce: that message simply never arrives at the downstream `jdbc` sink, with no attempt made to persist a `null`/nonexistent payload.

```
runThroughPipeline(["http","filter","jdbc"], "order amount=50"):
  http:   "order amount=50" -> "order amount=50" (unchanged)
  filter: contains "amount=50"? YES -> returns null (DROPPED)
  jdbc:   current is null BEFORE this stage runs -> loop returns null immediately, jdbc's function NEVER called

final result: null   (message never reached the sink)
```

## 7. Gotchas & takeaways

> **Gotcha:** Data Flow's DSL describes a *logical* pipeline topology, but each named stage (`http`, `filter`, `jdbc`) is deployed as a genuinely separate, independently-scaled application instance communicating over a real message broker — a common misconception coming from this card's simplified in-process model is assuming a Data Flow pipeline behaves like one program's straight-line function calls; in reality, each stage has its own deployment lifecycle, its own potential failure modes, and messages between stages travel over network/broker infrastructure with all the latency and delivery-guarantee considerations that implies, exactly as covered in the earlier Spring Cloud Stream cards this orchestration layer builds on.

- Spring Cloud Data Flow's core value is orchestration: turning a simple, declarative pipeline description into actual deployed, wired, monitored Spring Cloud Stream and Spring Cloud Task applications, without requiring manual per-application deployment and wiring.
- The pipe-separated DSL (`source | processor | sink`) directly mirrors the conceptual data flow of a pipeline, with each named stage referring to either a pre-built, reusable application from Data Flow's ecosystem or a custom application a team has registered.
- Because each stage is a genuinely independent, separately-deployed application, the underlying behavior (message delivery guarantees, scaling each stage independently, individual stage failure handling) follows directly from the Spring Cloud Stream concepts covered in earlier Messaging cards — Data Flow orchestrates deployment and wiring, it doesn't change the fundamental messaging semantics underneath.
- The following cards in this section cover streams and tasks within Data Flow specifically, Spring Cloud Skipper (Data Flow's underlying deployment/versioning mechanism), and the Spring Cloud Deployer abstraction Data Flow and Skipper both build on to remain portable across different target runtimes (Kubernetes, Cloud Foundry, local).
