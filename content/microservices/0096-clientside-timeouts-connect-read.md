---
card: microservices
gi: 96
slug: client-side-timeouts-connect-read
title: "Client-side timeouts (connect / read)"
---

## 1. What it is

A client-side timeout is a maximum time a caller will wait before giving up on an outbound call, and there are two distinct kinds that need separate values: a **connect timeout** bounds how long to wait while establishing the connection itself (the [TCP/TLS handshake](0095-connection-pooling-keep-alive.md)), and a **read timeout** bounds how long to wait for the response *after* the connection is established and the request has been sent. Without both configured explicitly, most HTTP client libraries default to waiting indefinitely — a silent, dangerous default in a distributed system.

## 2. Why & when

Without a timeout, a caller waiting on a downstream service that has stopped responding (crashed mid-request, network partition, severe overload) will simply wait forever — that calling thread is now permanently occupied doing nothing useful, precisely the resource-exhaustion problem [backpressure](0086-backpressure-in-synchronous-calls.md) exists to prevent, except here the trigger is a hung downstream call rather than incoming request volume. Timeouts turn an indefinite hang into a bounded failure: the caller gives up after a defined period, frees its resources, and can then decide how to handle the failure (retry, fall back, or propagate the error) instead of being stuck.

Configure both connect and read timeouts on *every* outbound call a service makes — there is essentially never a good reason to accept a client library's default of unlimited waiting. Set them based on the downstream call's realistic behavior: a connect timeout can usually be short (a few seconds — either the network path works or it doesn't, quickly), while a read timeout needs to account for the downstream operation's actual expected processing time, with some margin, but still bounded well below "forever."

## 3. Core concept

The two timeouts guard two different phases of the call, and a hang in either phase is caught by its own dedicated limit.

```
[connect timeout guards this phase]  [read timeout guards this phase]
TCP+TLS handshake  --------------->  request sent -------> waiting for response
     |                                                            |
  if this hangs past connectTimeout: fail                if this hangs past readTimeout: fail
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A timeline showing the connect phase guarded by a connect timeout and the response-waiting phase guarded by a separate read timeout, each independently bounding how long the caller will wait">
  <rect x="20" y="40" width="260" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="62" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Connecting (handshake)</text>
  <text x="150" y="80" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">guarded by connectTimeout</text>

  <rect x="320" y="40" width="300" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="62" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Waiting for response</text>
  <text x="470" y="80" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">guarded by readTimeout</text>

  <line x1="280" y1="65" x2="320" y2="65" stroke="#8b949e" stroke-width="1.5"/>
</svg>

Each phase of the call is bounded by its own independent timeout.

## 5. Runnable example

Scenario: a client calling a downstream service, first with no timeouts at all (a hung call blocks forever, simulated with a bound to keep the example runnable), then fixed with a read timeout that fails fast on a slow response, then extended to distinguish connect timeout failures from read timeout failures, each producing a different, actionable error.

### Level 1 — Basic

```java
// File: NoTimeout.java -- NO timeout configured -- the call waits for
// however long the downstream service takes, with NO upper bound.
public class NoTimeout {
    static String call(int downstreamDelayMs) throws InterruptedException {
        Thread.sleep(downstreamDelayMs); // the caller waits EXACTLY this long, whatever it is
        return "response received";
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("Calling a downstream service that takes 300ms to respond...");
        String result = call(300); // if this were 300 SECONDS instead, the caller would wait 300 seconds
        System.out.println(result);
    }
}
```

**How to run:** `javac NoTimeout.java && java NoTimeout` (JDK 17+).

Expected output:
```
Calling a downstream service that takes 300ms to respond...
response received
```

There is no upper bound here at all — this example happens to complete quickly, but the exact same code would happily wait minutes or hours if the downstream service hung, with no way for the caller to give up on its own.

### Level 2 — Intermediate

```java
// File: WithReadTimeout.java -- configure a READ TIMEOUT: give up if
// the response doesn't arrive within a bounded window, regardless of how
// long the downstream service actually takes.
import java.util.concurrent.*;

public class WithReadTimeout {
    static class ReadTimeoutException extends RuntimeException {
        ReadTimeoutException(long timeoutMs) { super("read timed out after " + timeoutMs + "ms"); }
    }

    static String call(int downstreamDelayMs, long readTimeoutMs) throws Exception {
        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<String> future = executor.submit(() -> {
            Thread.sleep(downstreamDelayMs);
            return "response received";
        });
        try {
            return future.get(readTimeoutMs, TimeUnit.MILLISECONDS); // BOUNDED wait
        } catch (TimeoutException e) {
            future.cancel(true);
            throw new ReadTimeoutException(readTimeoutMs);
        } finally {
            executor.shutdownNow();
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("Calling a downstream service that hangs for 5000ms, with a 200ms read timeout...");
        try {
            call(5000, 200); // downstream would take 5 seconds -- FAR beyond our patience
        } catch (ReadTimeoutException e) {
            System.out.println("Caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac WithReadTimeout.java && java WithReadTimeout` (JDK 17+).

Expected output:
```
Calling a downstream service that hangs for 5000ms, with a 200ms read timeout...
Caught: read timed out after 200ms
```

The caller gave up after 200ms — a small, bounded, predictable delay — instead of waiting the full 5000ms the downstream service would have actually taken.

### Level 3 — Advanced

```java
// File: DistinguishingConnectVsReadTimeout.java -- model BOTH timeout
// types separately, producing a DIFFERENT, more actionable error for
// each -- a connect failure means "couldn't even reach it"; a read
// failure means "reached it, but it never answered."
import java.util.concurrent.*;

public class DistinguishingConnectVsReadTimeout {
    static class ConnectTimeoutException extends RuntimeException {
        ConnectTimeoutException(String host) { super("could not connect to " + host + " within the connect timeout"); }
    }
    static class ReadTimeoutException extends RuntimeException {
        ReadTimeoutException(String host) { super("connected to " + host + " but response timed out"); }
    }

    static String call(String host, int connectDelayMs, int readDelayMs, long connectTimeoutMs, long readTimeoutMs) throws Exception {
        ExecutorService executor = Executors.newSingleThreadExecutor();
        try {
            Future<Void> connectFuture = executor.submit(() -> { Thread.sleep(connectDelayMs); return null; });
            try {
                connectFuture.get(connectTimeoutMs, TimeUnit.MILLISECONDS); // PHASE 1: connect
            } catch (TimeoutException e) {
                throw new ConnectTimeoutException(host);
            }

            Future<String> readFuture = executor.submit(() -> { Thread.sleep(readDelayMs); return "response from " + host; });
            try {
                return readFuture.get(readTimeoutMs, TimeUnit.MILLISECONDS); // PHASE 2: read
            } catch (TimeoutException e) {
                throw new ReadTimeoutException(host);
            }
        } finally {
            executor.shutdownNow();
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("Scenario A: unreachable host (connect hangs)");
        try {
            call("unreachable-service", 2000, 0, 100, 500); // connect itself hangs past 100ms
        } catch (ConnectTimeoutException e) {
            System.out.println("  Caught: " + e.getMessage());
        }

        System.out.println("Scenario B: reachable but slow to respond (read hangs)");
        try {
            call("slow-service", 20, 2000, 100, 500); // connects fine (20ms), but response hangs past 500ms
        } catch (ReadTimeoutException e) {
            System.out.println("  Caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac DistinguishingConnectVsReadTimeout.java && java DistinguishingConnectVsReadTimeout` (JDK 17+).

Expected output:
```
Scenario A: unreachable host (connect hangs)
  Caught: could not connect to unreachable-service within the connect timeout
Scenario B: reachable but slow to respond (read hangs)
  Caught: connected to slow-service but response timed out
```

## 6. Walkthrough

1. **Level 1** — `call` simply sleeps for whatever `downstreamDelayMs` is passed and returns. `main` calls it with `300`, and it completes in roughly 300ms — but nothing about `call`'s structure bounds that delay in any way; a `downstreamDelayMs` of 300000 (5 minutes) or an indefinitely hung real network call would leave the caller waiting exactly that long, with no mechanism to give up.
2. **Level 2 — bounding the wait with a read timeout** — `call` now submits the downstream work to an `ExecutorService` and waits for it via `future.get(readTimeoutMs, TimeUnit.MILLISECONDS)` — a version of `.get()` that itself throws `TimeoutException` if the result isn't ready within the specified window, rather than waiting indefinitely. `main` calls it with a downstream delay of `5000`ms but a `readTimeoutMs` of only `200` — `future.get` throws `TimeoutException` after 200ms (long before the simulated 5-second downstream delay would have completed), which is caught, converted into the more descriptive `ReadTimeoutException`, and re-thrown; `main`'s own `catch` block catches that and prints the message.
3. **Level 3 — separating the two timeout phases** — `call` now explicitly models two sequential phases: a `connectFuture` (simulating the TCP/TLS handshake, taking `connectDelayMs`) bounded by `connectTimeoutMs`, and only if that succeeds, a `readFuture` (simulating waiting for the response, taking `readDelayMs`) bounded by `readTimeoutMs`. Each phase throws its own distinct exception type on timeout.
4. **Tracing Scenario A** — `call("unreachable-service", 2000, 0, 100, 500)` sets `connectDelayMs=2000` but `connectTimeoutMs=100` — the connect phase's `Future.get` times out after 100ms, well before the simulated 2000ms handshake would complete, throwing `TimeoutException`, caught and converted into `ConnectTimeoutException`. Critically, the *read* phase (`readFuture`) is never even reached — the method throws before getting there, correctly reflecting that a connection that never succeeded has nothing to "read" from yet.
5. **Tracing Scenario B** — `call("slow-service", 20, 2000, 100, 500)` sets `connectDelayMs=20` (well under the 100ms connect timeout, so the connect phase succeeds quickly) but `readDelayMs=2000` against a `readTimeoutMs` of only `500` — the connect phase completes normally, then the read phase's `Future.get` times out after 500ms, throwing `TimeoutException`, converted into `ReadTimeoutException`. The distinct exception types printed in `main`'s output — "could not connect" versus "connected... but response timed out" — give an operator debugging a real production incident immediately actionable information: Scenario A suggests a network/DNS/firewall problem reaching the host at all, while Scenario B suggests the host is reachable but its own processing (or a downstream dependency *of that* service) is the bottleneck — two very different debugging paths.

## 7. Gotchas & takeaways

> **Gotcha:** a read timeout set too aggressively relative to a downstream operation's genuine, expected processing time causes the caller to give up on requests that would have succeeded, generating unnecessary failures and (if combined with a retry policy) unnecessary retry load on an already-working downstream service. Set read timeouts based on the downstream operation's real p99 latency plus reasonable margin, not an arbitrary short value chosen for "safety."

- Connect timeout and read timeout guard two different phases of a call and should be configured (and reasoned about) separately — a hang in either phase has a different likely root cause.
- Never accept a client library's default of unlimited waiting — configure both timeouts explicitly on every outbound call.
- Distinguishing connect-timeout failures from read-timeout failures in error messages/logs gives operators a real head start on diagnosing whether the problem is network reachability or downstream processing.
- Timeouts turn an indefinite hang into a bounded, actionable failure — the caller can then decide to retry (see [idempotency of operations](0082-idempotency-of-operations.md) for when that's safe), fall back, or propagate the error, rather than being stuck.
- This is a direct application of [backpressure](0086-backpressure-in-synchronous-calls.md) principles to the outbound side of a call: bounding how long you'll wait protects your own service's resources from being consumed by a hung downstream dependency.
