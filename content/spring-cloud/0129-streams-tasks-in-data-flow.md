---
card: spring-cloud
gi: 129
slug: streams-tasks-in-data-flow
title: "Streams & tasks in Data Flow"
---

## 1. What it is

Data Flow manages two structurally different kinds of workload through largely parallel DSL and lifecycle commands — streams (`stream create`/`deploy`, long-running pipelines of Spring Cloud Stream applications that keep processing messages continuously until explicitly stopped) and tasks (`task create`/`launch`, Spring Cloud Task applications that run once to completion and exit, launched either on demand or on a schedule) — reflecting the same long-running-service-versus-short-lived-process distinction earlier cards established between Spring Cloud Stream and Spring Cloud Task individually, now unified under one orchestration platform's consistent tooling.

```
dataflow:> stream create --name order-pipeline --definition "http | jdbc" --deploy
dataflow:> stream destroy --name order-pipeline

dataflow:> task create --name import-orders --definition "import-orders-app"
dataflow:> task launch --name import-orders
dataflow:> task execution list --name import-orders
```

```
STREAM: create, deploy, undeploy, destroy   -- lifecycle of a CONTINUOUSLY RUNNING pipeline
TASK:   create, launch, execution list       -- lifecycle of a REPEATEDLY LAUNCHED, run-to-completion job
```

## 2. Why & when

Streams and tasks solve genuinely different problems — a stream continuously processes an unbounded flow of messages (order events arriving indefinitely), while a task performs one bounded unit of work and finishes (importing today's batch file, running a nightly cleanup) — and their operational lifecycles reflect this: a stream is deployed once and stays running, requiring explicit action (`stream undeploy`/`destroy`) to stop; a task is launched, runs to completion, and exits on its own, with `task launch` naturally invoked repeatedly (manually, or via Data Flow's own scheduling integration) for each new run. Understanding which lifecycle model applies to a given workload is foundational to using Data Flow correctly — treating a task like a stream (deploying it once and expecting it to keep running) or a stream like a task (expecting it to naturally terminate) reflects a fundamental misunderstanding of the underlying workload type.

Reach for the stream lifecycle when:

- The workload is continuous and unbounded — an ingestion pipeline consuming an ever-arriving flow of events, a real-time transformation/enrichment pipeline — deployed once and expected to keep running indefinitely, monitored for ongoing health rather than for a single completion.

Reach for the task lifecycle when:

- The workload is bounded and finite — a batch import, a report generation, a one-off migration — launched (possibly repeatedly, on a schedule or on demand) with each launch producing its own distinct, trackable execution and expected to terminate.
- Correlating individual runs matters — task execution history (via `TaskExplorer`, an earlier card) naturally tracks discrete task launches, which has no direct stream equivalent, since a stream doesn't have discrete "runs" in the same sense — it simply runs continuously until stopped.

## 3. Core concept

```
 STREAM lifecycle:
   create (register the definition) -> deploy (start it running) -> [runs INDEFINITELY] -> undeploy/destroy (stop it)
   ONE deployment, continuously processing messages, until explicitly torn down

 TASK lifecycle:
   create (register the definition) -> launch (run it ONCE) -> [runs to COMPLETION, exits]
                                     -> launch AGAIN (a SEPARATE, independently-tracked execution)
                                     -> launch AGAIN (yet another SEPARATE execution)
   MANY independent, discrete executions, each with its OWN TaskExecution record
```

A stream has one lifecycle per deployment; a task has one lifecycle per *launch*, with the same task definition potentially launched many times, each producing its own independently-trackable execution.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A stream is deployed once and keeps running continuously represented by an unbroken bar while a task definition is launched multiple separate times each producing its own discrete bounded execution represented by separate short segments">
  <text x="30" y="30" fill="#6db33f" font-size="8" font-family="sans-serif">STREAM (one deployment, runs continuously):</text>
  <rect x="30" y="40" width="580" height="24" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="57" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">deployed -&gt; running indefinitely -&gt; (until explicitly undeployed)</text>

  <text x="30" y="105" fill="#79c0ff" font-size="8" font-family="sans-serif">TASK (same definition, launched multiple SEPARATE times):</text>
  <rect x="30" y="115" width="120" height="24" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="90" y="132" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">launch 1</text>
  <rect x="260" y="115" width="120" height="24" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="132" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">launch 2</text>
  <rect x="490" y="115" width="120" height="24" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="550" y="132" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">launch 3</text>
</svg>

One unbroken bar for a stream's single continuous run; three separate, discrete bars for a task's independently-tracked launches.

## 5. Runnable example

The scenario: model both lifecycle types against the same underlying "system," a stream that starts and keeps running until explicitly stopped, and a task definition launched multiple separate times, each producing its own tracked execution. Start with stream deployment and undeployment, then add task launching producing multiple independent executions, then combine both in one Data Flow-style session, mirroring realistic mixed usage.

### Level 1 — Basic

A stream's lifecycle: deploy once, runs continuously, explicitly undeployed later.

```java
public class DataFlowStreamsTasksLevel1 {
    static class Stream {
        String name;
        boolean running = false;
        Stream(String name) { this.name = name; }
        void deploy() { running = true; System.out.println("stream '" + name + "' DEPLOYED, now running continuously"); }
        void undeploy() { running = false; System.out.println("stream '" + name + "' UNDEPLOYED, stopped"); }
    }

    public static void main(String[] args) {
        Stream orderPipeline = new Stream("order-pipeline");

        orderPipeline.deploy();
        System.out.println("... time passes, messages keep flowing continuously ...");
        System.out.println("still running? " + orderPipeline.running);

        orderPipeline.undeploy(); // explicit action REQUIRED to stop it
        System.out.println("still running? " + orderPipeline.running);
    }
}
```

How to run: `java DataFlowStreamsTasksLevel1.java`

`orderPipeline.running` stays `true` for as long as no explicit `undeploy()` call happens — this is the core stream behavior: one deployment, indefinite continuous operation, requiring deliberate action to stop.

### Level 2 — Intermediate

A task's lifecycle: the same definition launched multiple separate times, each producing its own independent, tracked execution.

```java
import java.util.*;

public class DataFlowStreamsTasksLevel2 {
    record TaskExecution(int executionId, String taskName, long startTime, Integer exitCode) {}

    static class TaskDefinition {
        String name;
        List<TaskExecution> executions = new ArrayList<>();
        int nextExecutionId = 1;
        TaskDefinition(String name) { this.name = name; }

        TaskExecution launch() {
            TaskExecution execution = new TaskExecution(nextExecutionId++, name, System.currentTimeMillis(), 0);
            executions.add(execution); // a NEW, independent execution record EVERY launch
            System.out.println("task '" + name + "' LAUNCHED, executionId=" + execution.executionId() + " -- runs to completion, then exits");
            return execution;
        }
    }

    public static void main(String[] args) {
        TaskDefinition importOrders = new TaskDefinition("import-orders");

        importOrders.launch(); // launch 1 -- runs, completes, exits
        importOrders.launch(); // launch 2 -- a SEPARATE, independent run
        importOrders.launch(); // launch 3 -- yet another SEPARATE run

        System.out.println("total independent executions for 'import-orders': " + importOrders.executions.size());
    }
}
```

How to run: `java DataFlowStreamsTasksLevel2.java`

Three calls to `launch()` produce three separate `TaskExecution` records, each with its own incrementing `executionId` — unlike the stream's single, ongoing `running` state, `import-orders` has no persistent "running" concept between launches at all; each launch is entirely independent, runs to completion, and exits, exactly mirroring how a real Data Flow task definition can be launched any number of times, with each launch tracked as its own distinct execution.

### Level 3 — Advanced

Combine both lifecycle types in one Data Flow-style session, including a stream that stays running while several separate task launches happen alongside it, and querying execution history filtered to just the tasks.

```java
import java.util.*;

public class DataFlowStreamsTasksLevel3 {
    static class Stream {
        String name;
        boolean running = false;
        Stream(String name) { this.name = name; }
        void deploy() { running = true; }
        void undeploy() { running = false; }
    }

    record TaskExecution(int executionId, String taskName, long startTime, Integer exitCode) {}

    static class TaskDefinition {
        String name;
        List<TaskExecution> executions = new ArrayList<>();
        int nextExecutionId = 1;
        TaskDefinition(String name) { this.name = name; }
        TaskExecution launch() {
            TaskExecution execution = new TaskExecution(nextExecutionId++, name, System.currentTimeMillis(), 0);
            executions.add(execution);
            return execution;
        }
    }

    public static void main(String[] args) {
        // ONE stream, deployed once, stays running for the ENTIRE session
        Stream orderPipeline = new Stream("order-pipeline");
        orderPipeline.deploy();
        System.out.println("order-pipeline deployed, running=" + orderPipeline.running);

        // a task, launched THREE separate times WHILE the stream keeps running, unaffected
        TaskDefinition importOrders = new TaskDefinition("import-orders");
        importOrders.launch();
        System.out.println("  (order-pipeline still running=" + orderPipeline.running + " -- unaffected by task launches)");
        importOrders.launch();
        importOrders.launch();

        System.out.println("import-orders total executions: " + importOrders.executions.size());
        System.out.println("order-pipeline STILL running=" + orderPipeline.running + " (never stopped, no lifecycle overlap with the task)");

        orderPipeline.undeploy(); // the stream's OWN lifecycle, entirely independent of how many times the task ran
        System.out.println("order-pipeline finally undeployed, running=" + orderPipeline.running);
    }
}
```

How to run: `java DataFlowStreamsTasksLevel3.java`

`orderPipeline.running` stays `true` throughout all three `importOrders.launch()` calls — the stream's lifecycle and the task's lifecycle are completely independent of each other, coexisting within the same Data Flow deployment/session without any interaction, exactly mirroring how a real Data Flow instance commonly runs both long-lived stream pipelines and repeatedly-launched task jobs side by side, each following its own separate operational model.

## 6. Walkthrough

Trace the full sequence in Level 3.

1. `orderPipeline.deploy()` sets `orderPipeline.running = true` — this stream is now, conceptually, running continuously; nothing in the rest of the program will change this state until `undeploy()` is explicitly called at the very end.
2. `importOrders.launch()` is called three times in total across the program — each call creates a new `TaskExecution` object with an incrementing `executionId` (`1`, then `2`, then `3`) and appends it to `importOrders.executions`, which ends up holding three entries.
3. Between and around these three launches, every check of `orderPipeline.running` returns `true` — the task launches have no code path that touches `orderPipeline` at all, so there's no mechanism by which they could have affected it, mirroring how in a real Data Flow deployment, launching a task has no bearing on any separately-deployed stream's own running state.
4. After the third launch, `importOrders.executions.size()` is `3`, correctly reflecting three independent, completed executions of the same task definition.
5. `orderPipeline.undeploy()` finally sets `running = false` — this happens as the very last step, entirely independently timed from the task launches that happened earlier; a real operator could equally have chosen to undeploy the stream before, during, or long after any number of task launches, since the two lifecycles genuinely don't interact.

```
orderPipeline.deploy()          -> running = true
importOrders.launch() x3        -> 3 independent TaskExecution records, orderPipeline.running UNCHANGED (still true)
orderPipeline.undeploy()        -> running = false  (happens on its OWN schedule, unrelated to the task launches)
```

## 7. Gotchas & takeaways

> **Gotcha:** a task application that's accidentally written to run indefinitely (never actually terminating, perhaps due to a bug in its own completion logic) breaks Data Flow's task model in a specific, confusing way — its `TaskExecution` record will show a start time but never receive an end time or exit code (exactly the "stuck running" state covered in the earlier `TaskExplorer` card), and repeated launches of the same definition may pile up as seemingly-still-running executions. A task application must genuinely terminate on its own for the task lifecycle model to function correctly; this is a fundamentally different expectation from a stream application, which is *supposed* to run indefinitely.

- Streams and tasks in Data Flow directly reflect the underlying Spring Cloud Stream (continuous, message-driven) versus Spring Cloud Task (bounded, run-to-completion) distinction established in earlier cards, now managed through Data Flow's unified but lifecycle-appropriate tooling for each.
- A stream has one deployment lifecycle per definition (deploy once, runs until undeployed); a task has one lifecycle per *launch*, with a single task definition potentially producing many independent, separately-tracked executions over time.
- The two lifecycles coexist independently within the same Data Flow instance — launching a task has no effect on any deployed stream's running state, and vice versa, since they represent fundamentally different kinds of workload with fundamentally different operational models.
- Choosing correctly between modeling a piece of work as a stream versus a task is foundational to using Data Flow well — a continuous, unbounded flow of data belongs in a stream; a bounded, completable unit of work belongs in a task, and conflating the two leads to a mismatch between the workload's actual nature and the lifecycle tooling being applied to manage it.
