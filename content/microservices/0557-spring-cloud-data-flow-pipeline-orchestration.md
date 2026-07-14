---
card: microservices
gi: 557
slug: spring-cloud-data-flow-pipeline-orchestration
title: "Spring Cloud Data Flow (pipeline orchestration)"
---

## 1. What it is

**Spring Cloud Data Flow** is an orchestration layer that composes individually deployable [Spring Cloud Stream](0547-spring-cloud-stream-event-driven.md) applications and [Spring Cloud Task](0556-spring-cloud-task-short-lived-microservices.md) applications into larger data pipelines — streaming pipelines (a chain of stream applications connected via message brokers) and batch/task pipelines (a sequence or DAG of task executions with defined dependencies) — providing a dashboard, a DSL for defining pipeline topology, and deployment orchestration across target platforms (Kubernetes, Cloud Foundry, or local). Rather than manually wiring together and deploying each Stream/Task application's configuration by hand, Data Flow provides a declarative way to say "connect *this* source, *this* processor, and *this* sink into one streaming pipeline" and handles the deployment mechanics.

## 2. Why & when

You reach for Spring Cloud Data Flow once you have multiple Stream or Task applications that need to be composed into larger pipelines and consistently deployed and monitored as a unit:

- **A single Stream application (a `Function` bean bound to input/output channels) is useful in isolation, but real data pipelines often chain several stages together** — a source that ingests raw data, one or more processors that transform it, and a sink that stores or forwards the final result. Manually configuring the binder destinations to connect each stage's output to the next stage's input, consistently across every application, is tedious and error-prone to do by hand at scale.
- **Data Flow's DSL lets you express this composition declaratively**: `http | transform | jdbc` (as a simplified example) describes a pipeline where an HTTP source's output feeds a transform processor's input, whose output feeds a JDBC sink's input — Data Flow handles configuring the actual binder destination names consistently across all three applications to wire them together correctly.
- **For Task applications, Data Flow supports defining a sequence or DAG of tasks with dependencies** — "run task B only after task A succeeds," or more complex branching based on a task's exit status — giving orchestrated, multi-step batch workflows without hand-rolling that orchestration logic yourself.
- **You reach for Data Flow specifically once you're composing multiple Stream/Task applications into pipelines that need consistent deployment, monitoring, and lifecycle management** — for a single, standalone Stream or Task application with no broader pipeline composition need, Data Flow's orchestration layer is more infrastructure than the situation calls for.

## 3. Core concept

Think of a factory assembly line made up of individually-designed, individually-testable stations (a Stream application per station), where a plant manager (Data Flow) decides the actual line layout — which station's output conveyor belt feeds into which next station's input, in what order, and manages starting up or shutting down the whole line as one coordinated unit — rather than each station operator individually deciding and wiring up their own conveyor belt connections to arbitrary other stations. The stations themselves (the Stream/Task applications) don't need to know the full line's layout; the plant manager's layout plan (the Data Flow DSL definition) is what actually determines and enacts the connections between them.

Concretely:

1. **Individual Spring Cloud Stream applications (or pre-built ones from Data Flow's own starter app library) are registered with Data Flow** as reusable building blocks — a source, one or more processors, a sink.
2. **A stream definition, written in Data Flow's pipe-and-filter DSL** (`source | processor | sink`), describes how these building blocks should be connected — Data Flow translates this into the actual binder destination configuration each individual application needs, deploying them wired together correctly.
3. **A task definition (or a composed task graph, using a similar DSL with conditional operators)** describes a sequence or DAG of Task application executions — Data Flow triggers each task in the defined order, tracking each execution via the same [Spring Cloud Task](0556-spring-cloud-task-short-lived-microservices.md) execution history mechanism underneath.
4. **Data Flow's dashboard provides visibility into both stream pipelines' running state and task executions' history**, giving one operational view over compositions that would otherwise require manually cross-referencing several individually-deployed applications' own separate states.

## 4. Diagram

<svg viewBox="0 0 660 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Data Flow's DSL composes individually deployable stream applications into a connected pipeline, and orchestrates deployment across a target platform">
  <rect x="20" y="60" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">http (source)</text>
  <rect x="200" y="60" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="270" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">transform</text>
  <rect x="380" y="60" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="450" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">jdbc (sink)</text>

  <line x1="160" y1="80" x2="200" y2="80" stroke="#8b949e" marker-end="url(#a17)"/>
  <line x1="340" y1="80" x2="380" y2="80" stroke="#8b949e" marker-end="url(#a17)"/>

  <text x="270" y="145" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DSL: http | transform | jdbc</text>
  <text x="270" y="165" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Data Flow wires binder destinations to connect these three, deploys as one pipeline</text>
  <defs><marker id="a17" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

A pipe-and-filter DSL definition describes how independently-deployable applications should be wired together; Data Flow handles the actual binder configuration and deployment.

## 5. Runnable example

Scenario: composing a simple ingest-transform-store pipeline. We start with a plain Java model of manually wiring three stages together, extend it to a DSL-driven composition model, then show the real Data Flow shell/DSL shape.

### Level 1 — Basic

```java
// File: ManualPipelineWiring.java -- models MANUALLY wiring three
// processing stages together, by hand, with hardcoded connections.
import java.util.function.Function;

public class ManualPipelineWiring {
    static Function<String, String> transformStage = raw -> raw.toUpperCase();
    static void sinkStage(String data) { System.out.println("[sink] storing: " + data); }

    static void manuallyWiredPipeline(String rawInput) {
        String transformed = transformStage.apply(rawInput); // hardcoded: transform's output feeds sink DIRECTLY
        sinkStage(transformed);
    }

    public static void main(String[] args) {
        manuallyWiredPipeline("order placed: widget x3");
        System.out.println("Wiring is hardcoded IN CODE -- changing the pipeline shape means editing this method directly.");
    }
}
```

How to run: `java ManualPipelineWiring.java`

`manuallyWiredPipeline` hardcodes the connection between `transformStage` and `sinkStage` directly in Java code — reconfiguring the pipeline (adding a stage, reordering stages, swapping the sink) requires editing this method, rather than being expressible as an external, declarative configuration.

### Level 2 — Intermediate

```java
// File: DslDrivenComposition.java -- models composing stages via a
// DECLARATIVE DSL string, parsed and wired at runtime -- closer to
// Data Flow's actual pipe-and-filter approach.
import java.util.*;
import java.util.function.Function;

public class DslDrivenComposition {
    static Map<String, Function<String, String>> registeredStages = Map.of(
        "transform", (Function<String, String>) String::toUpperCase,
        "reverse", (Function<String, String>) s -> new StringBuilder(s).reverse().toString()
    );

    // parses a DSL string like "transform | reverse" and wires the stages together dynamically
    static String runPipeline(String dslDefinition, String input) {
        String[] stageNames = dslDefinition.split("\\|");
        String current = input;
        for (String stageName : stageNames) {
            Function<String, String> stage = registeredStages.get(stageName.trim());
            current = stage.apply(current);
            System.out.println("After stage '" + stageName.trim() + "': " + current);
        }
        return current;
    }

    public static void main(String[] args) {
        System.out.println("Final result: " + runPipeline("transform | reverse", "order placed"));
        System.out.println("Changing the pipeline shape is now just changing the DSL STRING, not the Java code.");
    }
}
```

How to run: `java DslDrivenComposition.java`

`runPipeline` parses the DSL string `"transform | reverse"` at runtime and dynamically wires the named stages together in that order — reconfiguring the pipeline (say, to `"reverse | transform"` or adding a third stage) is purely a change to the DSL string, with zero change to the underlying stage implementations or the wiring logic itself, mirroring exactly how Data Flow's DSL decouples pipeline topology from the individual applications being composed.

### Level 3 — Advanced

```java
// File: SpringCloudDataFlowRealShape.java -- illustrative Data Flow
// SHELL commands (NOT executable Java) showing REAL stream and task
// pipeline definitions, as they'd actually be entered via the Data Flow shell/dashboard.
public class SpringCloudDataFlowRealShape {

    static final String REGISTER_APPS = """
        app register --name http --type source --uri maven://org.springframework.cloud.stream.app:http-source-rabbit:3.2.1
        app register --name transform --type processor --uri maven://org.springframework.cloud.stream.app:transform-processor-rabbit:3.2.1
        app register --name jdbc --type sink --uri maven://org.springframework.cloud.stream.app:jdbc-sink-rabbit:3.2.1
        """;

    static final String DEFINE_AND_DEPLOY_STREAM = """
        stream create --name order-ingest-pipeline --definition "http | transform --expression=payload.toUpperCase() | jdbc --tableName=orders"
        stream deploy --name order-ingest-pipeline
        """;

    static final String COMPOSED_TASK_DEFINITION = """
        task create --name nightly-reconciliation --definition "extract-data && validate-data && reconcile-inventory"
        task launch --name nightly-reconciliation
        """;

    public static void main(String[] args) {
        System.out.println(REGISTER_APPS);
        System.out.println(DEFINE_AND_DEPLOY_STREAM);
        System.out.println(COMPOSED_TASK_DEFINITION);
        System.out.println("These are REAL Data Flow shell commands -- run against a real Data Flow server, deployed to Kubernetes/Cloud Foundry/local.");
    }
}
```

How to run: `java SpringCloudDataFlowRealShape.java` prints the illustrative shell commands; against a real, running Spring Cloud Data Flow server (deployed via its own Docker image or Kubernetes manifest), these exact commands, entered via the Data Flow shell or dashboard, register applications, define a stream pipeline connecting them, deploy it to the configured target platform, and separately define and launch a composed task graph with sequential dependencies (`&&` meaning "run the next task only if the previous one succeeded").

`stream create --definition "http | transform --expression=... | jdbc --tableName=..."` is the actual pipe-and-filter DSL Data Flow uses — each `|`-separated segment names a registered application, with `--` options configuring that specific application instance's behavior. `task create --definition "extract-data && validate-data && reconcile-inventory"` similarly composes three separately-registered Task applications into one orchestrated sequence, where `&&` expresses "proceed to the next task only on success," giving conditional, multi-step orchestration without writing any custom orchestration code.

## 6. Walkthrough

Trace what happens when `stream deploy --name order-ingest-pipeline` is executed against the stream defined in Level 3, end to end:

1. **Data Flow's server parses the stored stream definition** (`http | transform --expression=payload.toUpperCase() | jdbc --tableName=orders`), identifying three registered applications to deploy: `http` (source), `transform` (processor), `jdbc` (sink).
2. **Data Flow generates unique message-broker destination names to connect consecutive applications** — say, a destination named `order-ingest-pipeline.http` connecting `http`'s output to `transform`'s input, and `order-ingest-pipeline.transform` connecting `transform`'s output to `jdbc`'s input — configuring each application's Spring Cloud Stream bindings accordingly before deployment.
3. **Data Flow deploys each of the three applications to the configured target platform** (say, Kubernetes) as separate Pods/Deployments, each one an ordinary Spring Cloud Stream application under the hood, each configured (via the destination names from step 2) to connect to the correct neighboring stage.
4. **An HTTP request arrives at the deployed `http` source application** — it publishes the request body as a message onto the `order-ingest-pipeline.http` destination.
5. **The `transform` processor, subscribed to `order-ingest-pipeline.http`, receives this message**, applies its configured `payload.toUpperCase()` expression, and publishes the transformed result onto `order-ingest-pipeline.transform`.
6. **The `jdbc` sink, subscribed to `order-ingest-pipeline.transform`, receives the transformed message** and inserts it into the configured `orders` table — completing the pipeline's end-to-end flow, from an incoming HTTP request through a transformation stage to durable storage, entirely coordinated by Data Flow's deployment and destination-naming logic, without any of the three individual applications needing to know about the other two directly.

## 7. Gotchas & takeaways

> **Gotcha:** Data Flow orchestrates *deployment and wiring*, but each individual Stream/Task application in the pipeline still runs as its own independent process with its own resource allocation, scaling behavior, and failure mode — a slow or failing `transform` processor stage doesn't automatically get "fixed" or scaled by Data Flow just because it's part of a defined pipeline; each stage still needs its own appropriately-configured scaling and resiliency settings, exactly as it would if deployed standalone.

- Spring Cloud Data Flow composes individually deployable Stream and Task applications into larger pipelines via a declarative pipe-and-filter DSL, handling the binder destination wiring and deployment mechanics rather than requiring manual, hand-coded configuration per pipeline.
- Stream pipelines connect a chain of message-driven applications (source, processors, sink); composed task definitions orchestrate sequences or DAGs of short-lived Task application executions with defined dependencies.
- Data Flow's dashboard gives unified visibility into running pipelines and task execution history, consolidating what would otherwise require checking several individually-deployed applications' separate states.
- Reach for Data Flow once you're composing multiple Stream/Task applications into genuine pipelines needing consistent deployment and monitoring — a single standalone Stream or Task application doesn't need this orchestration layer.
