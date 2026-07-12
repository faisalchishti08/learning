---
card: microservices
gi: 21
slug: microservices-vs-service-mesh-vs-serverless
title: Microservices vs Service Mesh vs Serverless
---

## 1. What it is

These three terms answer different questions and are frequently confused because they're often used together. **Microservices** is an architectural style — how you split a system's functionality into independently deployable services. A **service mesh** is infrastructure — a layer (typically a "sidecar" proxy deployed alongside each service instance) that handles cross-cutting network concerns like retries, timeouts, encryption, and observability, without that logic living in each service's own code. **Serverless** (specifically Functions-as-a-Service) is a deployment and execution model — code that runs only in response to a triggering event, with no long-running process to manage, and can scale down to zero when idle.

A microservice can be deployed with or without a service mesh, and can be deployed as a traditional long-running process or, for parts of it, as serverless functions. They compose rather than compete.

## 2. Why & when

Microservices decide *what* your services are and *how they're bounded*. A service mesh decides *how network calls between services are handled* — without a mesh, each service's own code must implement its own retry logic, its own timeout handling, its own TLS setup; with a mesh, a sidecar proxy standing next to each service instance handles that uniformly, letting the service's own code stay focused purely on business logic. Serverless decides *how the code actually runs* — a serverless function has no persistent process sitting around waiting for requests; it starts up in response to a trigger and can shut down entirely between invocations, which is excellent for spiky, unpredictable, or low-volume workloads but introduces "cold start" latency and doesn't suit workloads that need to hold long-running in-memory state.

Choose a service mesh when you have enough services that reimplementing retry/timeout/observability logic in each one's code becomes real duplicated effort worth centralizing into infrastructure. Choose serverless for a specific piece of functionality with a genuinely event-driven, spiky, or infrequent invocation pattern — not as a blanket replacement for every service, since a busy, steadily-loaded service usually runs more predictably and cheaply as a traditional long-running process.

## 3. Core concept

Three independent axes, not three competing choices:

- **Microservices vs monolith:** architectural granularity — how functionality is split into deployable units.
- **Service mesh vs in-code networking logic:** where cross-cutting network concerns (retry, timeout, mTLS, tracing) live — a shared infrastructure layer, or duplicated in each service's own code.
- **Long-running process vs serverless function:** execution model — a process that's always running and holds its own state, or code that starts fresh on each triggering event and can scale to zero.

A real system can mix these freely: microservices with no mesh, microservices with a mesh, some services as long-running processes and others as serverless functions for spiky workloads.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A microservice can run as a long-running process with or without a sidecar mesh proxy, or as a serverless function triggered by events with no persistent process">
  <text x="120" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Microservice + mesh</text>
  <rect x="30" y="35" width="90" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service code</text>
  <rect x="130" y="35" width="60" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="55" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">sidecar</text>
  <text x="160" y="66" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">proxy</text>

  <text x="350" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Microservice, no mesh</text>
  <rect x="290" y="35" width="130" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="355" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service code +</text>
  <text x="355" y="68" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">its own retry/timeout logic</text>

  <text x="550" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Serverless function</text>
  <rect x="490" y="35" width="120" height="45" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="550" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">runs on trigger,</text>
  <text x="550" y="68" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">scales to zero when idle</text>
</svg>

Three independent choices about deployment: architectural split, network-concern placement, and execution lifecycle.

## 5. Runnable example

Scenario: calling a downstream service with retry logic, first duplicated in the service's own code, then modeled as a mesh-style sidecar handling it uniformly, then contrasted with a serverless function's on-demand, no-persistent-process execution model.

### Level 1 — Basic

```java
// File: RetryInServiceCode.java -- retry logic lives INSIDE the service's own code
public class RetryInServiceCode {
    static int attempts = 0;

    static String callDownstream() {
        attempts++;
        if (attempts < 3) throw new RuntimeException("transient failure");
        return "success";
    }

    // EVERY service that calls a downstream dependency has to write this SAME retry loop itself
    static String businessLogicWithRetry() {
        for (int i = 0; i < 5; i++) {
            try { return callDownstream(); }
            catch (RuntimeException e) { System.out.println("  retrying after: " + e.getMessage()); }
        }
        throw new RuntimeException("exhausted retries");
    }

    public static void main(String[] args) {
        System.out.println(businessLogicWithRetry());
    }
}
```

**How to run:** `javac RetryInServiceCode.java && java RetryInServiceCode` (JDK 17+).

Expected output:
```
  retrying after: transient failure
  retrying after: transient failure
success
```

The retry loop is written directly inside this service's business logic. If ten services in the system each call downstream dependencies, this same retry loop (or a subtly different, inconsistent version of it) gets duplicated ten times.

### Level 2 — Intermediate

```java
// File: MeshStyleSidecar.java -- retry logic moves OUT of business logic,
// into a SEPARATE sidecar-style class the business logic doesn't need to know about.
public class MeshStyleSidecar {
    // stands in for the ACTUAL downstream dependency -- business logic never calls this directly
    static int attempts = 0;
    static String realDownstreamCall() {
        attempts++;
        if (attempts < 3) throw new RuntimeException("transient failure");
        return "success";
    }

    // stands in for a MESH SIDECAR -- intercepts every outbound call, applies retry uniformly
    static class Sidecar {
        String callWithMeshRetry(java.util.function.Supplier<String> call) {
            for (int i = 0; i < 5; i++) {
                try { return call.get(); }
                catch (RuntimeException e) { System.out.println("  [sidecar] retrying after: " + e.getMessage()); }
            }
            throw new RuntimeException("exhausted retries");
        }
    }

    // business logic is now CLEAN -- it doesn't write retry logic itself at all
    static String businessLogic(Sidecar sidecar) {
        return sidecar.callWithMeshRetry(MeshStyleSidecar::realDownstreamCall);
    }

    public static void main(String[] args) {
        System.out.println(businessLogic(new Sidecar()));
    }
}
```

**How to run:** `javac MeshStyleSidecar.java && java MeshStyleSidecar` (JDK 17+).

Expected output:
```
  [sidecar] retrying after: transient failure
  [sidecar] retrying after: transient failure
success
```

`businessLogic` no longer contains any retry loop at all — it delegates the call through `Sidecar`, which owns retry behavior uniformly. In a real service mesh, this "sidecar" is a separate process running alongside the service, intercepting its network traffic transparently — every service gets the same retry behavior without duplicating the logic in its own code.

### Level 3 — Advanced

```java
// File: ServerlessVsLongRunning.java -- contrast a LONG-RUNNING service
// (persistent state across calls) with a SERVERLESS function (fresh state
// every invocation, models scale-to-zero behavior).
public class ServerlessVsLongRunning {
    // LONG-RUNNING microservice: state persists across every call, because the process never restarts
    static class LongRunningService {
        int requestCount = 0; // lives for the LIFETIME of the process
        String handleRequest() {
            requestCount++;
            return "request #" + requestCount + " (process has been running the whole time)";
        }
    }

    // SERVERLESS function: models a FRESH invocation each time -- no state survives between calls,
    // because in a real serverless platform, the underlying process may not even exist between invocations.
    static class ServerlessFunction {
        static String handleInvocation() {
            int requestCount = 0; // ALWAYS starts fresh -- cannot remember the previous invocation
            requestCount++;
            boolean isColdStart = true; // in a real platform, this models spinning up a new execution environment
            String coldStartNote = isColdStart ? " (COLD START -- environment just spun up)" : "";
            return "request #" + requestCount + coldStartNote;
        }
    }

    public static void main(String[] args) {
        LongRunningService service = new LongRunningService();
        System.out.println("Long-running: " + service.handleRequest());
        System.out.println("Long-running: " + service.handleRequest());
        System.out.println("Long-running: " + service.handleRequest()); // requestCount correctly reaches 3

        System.out.println("Serverless:   " + ServerlessFunction.handleInvocation());
        System.out.println("Serverless:   " + ServerlessFunction.handleInvocation());
        System.out.println("Serverless:   " + ServerlessFunction.handleInvocation()); // ALWAYS "request #1" -- no memory between calls
    }
}
```

**How to run:** `javac ServerlessVsLongRunning.java && java ServerlessVsLongRunning` (JDK 17+).

Expected output:
```
Long-running: request #1 (process has been running the whole time)
Long-running: request #2 (process has been running the whole time)
Long-running: request #3 (process has been running the whole time)
Serverless:   request #1 (COLD START -- environment just spun up)
Serverless:   request #1 (COLD START -- environment just spun up)
Serverless:   request #1 (COLD START -- environment just spun up)
```

The production-flavored contrast: `LongRunningService.requestCount` genuinely accumulates across calls, because `service` is one object whose state persists for as long as the process runs — exactly how a traditional microservice instance behaves. `ServerlessFunction.handleInvocation` resets `requestCount` to zero on every single call, modeling how a real serverless platform can tear down and recreate the execution environment between invocations — any state a function needs to persist must be stored externally (a database, a cache), never assumed to survive in local memory between calls.

## 6. Walkthrough

1. `LongRunningService service = new LongRunningService()` constructs one object whose `requestCount` field will live for as long as `service` itself exists — in a real deployment, this models one running instance of a microservice, alive continuously.
2. The three `service.handleRequest()` calls each increment the *same* `requestCount` field, correctly producing `1`, `2`, then `3` — proof that state genuinely persists across calls, because it's the same long-running object handling all three.
3. `ServerlessFunction.handleInvocation()` is a `static` method with a `requestCount` local variable declared *inside* the method body — it is re-initialized to `0` at the start of every single call, with absolutely no connection to any previous call's state.
4. Each of the three `ServerlessFunction.handleInvocation()` calls therefore independently prints `"request #1"` — modeling a real serverless platform, where the function's execution environment may be created fresh (a "cold start") for each invocation, and nothing in local memory is guaranteed to survive between them.
5. The practical consequence, visible directly in this output: a long-running service can safely keep an in-memory counter, cache, or session; a serverless function cannot — anything that needs to persist across invocations must be written to and read from external storage instead.

```
LongRunningService (one persistent object):
  call 1 -> requestCount: 0 -> 1
  call 2 -> requestCount: 1 -> 2   (SAME field, remembers)
  call 3 -> requestCount: 2 -> 3

ServerlessFunction (fresh invocation each time):
  call 1 -> requestCount: 0 -> 1   (local var, discarded after return)
  call 2 -> requestCount: 0 -> 1   (starts over, no memory)
  call 3 -> requestCount: 0 -> 1   (starts over, no memory)
```

## 7. Gotchas & takeaways

> **Gotcha:** treating "serverless" as simply "microservices, but smaller" is a common and costly misunderstanding — a serverless function that assumes it can hold meaningful state in memory between invocations (a cache, a counter, a database connection pool warmed up once) will behave unpredictably in production, because the platform offers no guarantee that state, or even the same execution environment, survives from one invocation to the next.

- Microservices, service mesh, and serverless answer three different questions: how functionality is split, where cross-cutting network logic lives, and how code actually executes — they compose rather than compete.
- A service mesh moves retry, timeout, and observability logic out of each service's own code into a shared infrastructure layer (conceptually, a sidecar proxy), avoiding duplicated implementations across many services.
- A serverless function has no guaranteed persistent state between invocations — anything that must survive across calls needs to live in external storage, not local memory.
- Mixing these freely within one system is normal and often correct: traditional long-running microservices for steady workloads, serverless functions for spiky or infrequent ones, with or without a mesh handling cross-cutting network concerns uniformly.
