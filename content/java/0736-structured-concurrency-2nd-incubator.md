---
card: java
gi: 736
slug: structured-concurrency-2nd-incubator
title: Structured concurrency (2nd incubator)
---

## 1. What it is

**Java 20** (JEP 437) is the **second incubator** round of [structured concurrency](0726-structured-concurrency-incubator.md), continuing to refine `StructuredTaskScope` after its first incubator round in Java 19. The core model — forking related subtasks within a scope, the scope unable to exit until every subtask has terminated, `ShutdownOnFailure` and `ShutdownOnSuccess` policies — carries forward unchanged. This round's changes are primarily API polish based on incubator feedback: minor method signature adjustments and clearer interaction rules with the also-incubating [scoped values](0732-scoped-values-incubator.md), which shipped for the first time in this same Java 20 release and was specifically designed to propagate correctly into `StructuredTaskScope` subtasks.

## 2. Why & when

Structured concurrency's first incubator round proved the core model — bounded subtask lifetimes tied to an enclosing scope — but scoped values didn't exist yet in Java 19, so the interaction between "share context implicitly down a call tree" and "manage a group of concurrent subtasks safely" hadn't been exercised in practice. With scoped values arriving in this same Java 20 release, this second incubator round is where the two features' design gets validated together: a `ScopedValue` bound in the thread that opens a `StructuredTaskScope` needs to be reliably visible to every subtask that scope forks, without the eager, unconditional propagation cost `InheritableThreadLocal` would impose. This matters for exactly the realistic backend pattern both features exist to support together: a request handler binds a request ID (or auth context, or trace ID) via a scoped value, then fans out to multiple concurrent subtasks via `StructuredTaskScope` to call several downstream services — every one of those subtasks needs to see the same bound context for logging, authorization, and tracing to work correctly, and needs that context's lifetime to be exactly as bounded as the subtasks' own lifetimes.

## 3. Core concept

```java
static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

ScopedValue.where(REQUEST_ID, "req-42").run(() -> {
    try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
        // Subtasks forked here correctly see REQUEST_ID.get() == "req-42",
        // even though each runs on a different (virtual) thread.
        var userTask = scope.fork(() -> fetchUser());
        var orderTask = scope.fork(() -> fetchOrders());
        scope.join();
        scope.throwIfFailed();
    }
});
```

The scoped value's binding and the structured task scope's subtask lifetimes are both tied to the same enclosing block, so they naturally stay in sync.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A scoped value bound in the outer block is visible to every subtask forked by a StructuredTaskScope nested inside it, and both the binding and the subtasks share the same bounded lifetime" >
  <rect x="20" y="20" width="600" height="180" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="42" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">ScopedValue.where(REQUEST_ID, "req-42").run(() -&gt; {</text>

  <rect x="60" y="60" width="520" height="120" rx="8" fill="#0f1620" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="82" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">try (var scope = new StructuredTaskScope.ShutdownOnFailure())</text>

  <rect x="90" y="100" width="200" height="50" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="190" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">fork(fetchUser) sees "req-42"</text>

  <rect x="350" y="100" width="200" height="50" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="450" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">fork(fetchOrders) sees "req-42"</text>

  <text x="330" y="200" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">binding lifetime and subtask lifetimes are both scoped to the same block</text>
</svg>

Nesting `StructuredTaskScope` inside a `ScopedValue` binding is the idiomatic combination this round validates.

## 5. Runnable example

Scenario: a backend request handler binding a request ID and an authenticated user ID via scoped values, then fanning out to concurrent downstream calls via structured concurrency — each subtask logs using both bound values without either being passed as an explicit parameter. It grows from a basic two-value binding with one subtask, to multiple concurrent subtasks all correctly observing the same bindings, to a version handling subtask failure while confirming the scoped values remain correctly visible even during the cancellation path.

### Level 1 — Basic

```java
// File: ScopedStructuredBasic.java
// Run with --enable-preview --add-modules jdk.incubator.concurrent — Java 20 incubators.
import jdk.incubator.concurrent.ScopedValue;
import jdk.incubator.concurrent.StructuredTaskScope;
import java.util.concurrent.Future;

public class ScopedStructuredBasic {
    static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

    static String fetchUser() throws InterruptedException {
        Thread.sleep(20);
        return "user-data for " + REQUEST_ID.get();
    }

    public static void main(String[] args) throws Exception {
        ScopedValue.where(REQUEST_ID, "req-1").run(() -> {
            try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
                Future<String> userTask = scope.fork(ScopedStructuredBasic::fetchUser);
                scope.join();
                scope.throwIfFailed();
                System.out.println(userTask.resultNow());
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview --add-modules jdk.incubator.concurrent ScopedStructuredBasic.java
java --enable-preview --add-modules jdk.incubator.concurrent ScopedStructuredBasic
```

Expected output:
```
user-data for req-1
```

### Level 2 — Intermediate

```java
// File: ScopedStructuredMultiIntermediate.java
// Binds TWO scoped values (request ID and user ID) and forks THREE
// concurrent subtasks, all correctly observing both bindings — the
// real-world shape of request-scoped context fanning out to several calls.
import jdk.incubator.concurrent.ScopedValue;
import jdk.incubator.concurrent.StructuredTaskScope;
import java.util.concurrent.Future;

public class ScopedStructuredMultiIntermediate {
    static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();
    static final ScopedValue<String> USER_ID = ScopedValue.newInstance();

    static String call(String serviceName, long delayMs) throws InterruptedException {
        Thread.sleep(delayMs);
        return "[" + REQUEST_ID.get() + "/" + USER_ID.get() + "] " + serviceName + " responded";
    }

    public static void main(String[] args) throws Exception {
        ScopedValue.where(REQUEST_ID, "req-77").where(USER_ID, "alice").run(() -> {
            try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
                Future<String> userTask = scope.fork(() -> call("user-service", 20));
                Future<String> orderTask = scope.fork(() -> call("order-service", 30));
                Future<String> cartTask = scope.fork(() -> call("cart-service", 10));

                scope.join();
                scope.throwIfFailed();

                System.out.println(userTask.resultNow());
                System.out.println(orderTask.resultNow());
                System.out.println(cartTask.resultNow());
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview --add-modules jdk.incubator.concurrent ScopedStructuredMultiIntermediate.java
java --enable-preview --add-modules jdk.incubator.concurrent ScopedStructuredMultiIntermediate
```

Expected output:
```
[req-77/alice] user-service responded
[req-77/alice] order-service responded
[req-77/alice] cart-service responded
```

### Level 3 — Advanced

```java
// File: ScopedStructuredFailureAdvanced.java
// One subtask fails; confirms the scoped values remain correctly bound and
// readable even in the OTHER subtasks up until they're cancelled, and in the
// exception-handling code after the scope closes — the production-flavored
// shape of a fan-out call where one downstream service errors.
import jdk.incubator.concurrent.ScopedValue;
import jdk.incubator.concurrent.StructuredTaskScope;
import java.util.concurrent.Future;

public class ScopedStructuredFailureAdvanced {
    static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

    static String reliableCall() throws InterruptedException {
        Thread.sleep(100); // slow enough that cancellation should interrupt it
        return "should not complete: " + REQUEST_ID.get();
    }

    static String failingCall() {
        throw new RuntimeException("downstream service failed for " + REQUEST_ID.get());
    }

    public static void main(String[] args) {
        ScopedValue.where(REQUEST_ID, "req-500").run(() -> {
            try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
                Future<String> slow = scope.fork(ScopedStructuredFailureAdvanced::reliableCall);
                Future<String> failing = scope.fork(ScopedStructuredFailureAdvanced::failingCall);

                scope.join();
                scope.throwIfFailed();

                System.out.println("unreachable: " + slow.resultNow());
            } catch (Exception e) {
                // REQUEST_ID is still bound here — we're still inside the
                // ScopedValue.where(...).run() block's lambda.
                System.out.println("[" + REQUEST_ID.get() + "] request failed: " + e.getCause().getMessage());
            }
        });
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview --add-modules jdk.incubator.concurrent ScopedStructuredFailureAdvanced.java
java --enable-preview --add-modules jdk.incubator.concurrent ScopedStructuredFailureAdvanced
```

Expected output:
```
[req-500] request failed: downstream service failed for req-500
```

## 6. Walkthrough

1. `ScopedStructuredFailureAdvanced.main` binds `REQUEST_ID` to `"req-500"` and runs a lambda inside `ScopedValue.where(...).run(...)`. Inside that lambda, a `StructuredTaskScope.ShutdownOnFailure` is opened and two subtasks are forked: `reliableCall` (slow, 100ms sleep) and `failingCall` (throws immediately).
2. `failingCall` runs on its own (virtual) thread and, before throwing, calls `REQUEST_ID.get()` to build its exception message — successfully reading `"req-500"` even though it's executing on a different thread than the one that established the binding. This confirms the binding correctly propagated to this forked subtask.
3. Because the scope uses the `ShutdownOnFailure` policy, the moment `failingCall` throws, the scope's failure-handling logic kicks in: it records the exception and immediately requests cancellation of the *other* running subtask, `reliableCall`, by interrupting its thread — this is the exact same automatic-cancellation behavior demonstrated in the original [structured concurrency](0726-structured-concurrency-incubator.md) tutorial, now happening inside a scoped-value binding.
4. `reliableCall`, mid-`Thread.sleep(100)`, receives the interrupt and exits early via `InterruptedException` rather than completing its full 100ms sleep and returning its `"should not complete"` string — which is why that string never appears in the output.
5. `scope.join()` returns once both subtasks have terminated (one by exception, one by cancellation), and `scope.throwIfFailed()` throws, wrapping `failingCall`'s original `RuntimeException`, since `ShutdownOnFailure` recorded that as the scope's failure.
6. Control jumps to the `catch (Exception e)` block — still inside the outer `ScopedValue.where(REQUEST_ID, "req-500").run(...)` lambda, since the `try`/`catch` is nested within it, not around it. This means `REQUEST_ID.get()` is still validly bound here too, and the catch block successfully reads `"req-500"` again to build its final error message.
7. This demonstrates the key integration point this second incubator round specifically validated: a scoped value's binding lifetime is tied to its enclosing `where(...).run()` block, not to any individual subtask's lifetime — so it remains correctly readable throughout the entire structured-concurrency operation, including during failure handling and cancellation, exactly matching how a plain method call's local variables would behave, just extended safely across concurrent subtasks.

```
ScopedValue.where(REQUEST_ID, "req-500").run(() -> {
    |  [binding "req-500" active for this whole block]
    try (scope) {
        fork reliableCall()  ---- sleeping 100ms ---- gets INTERRUPTED when failingCall throws
        fork failingCall()   ---- reads REQUEST_ID.get()="req-500" ---- throws immediately
        |
        scope.join() + throwIfFailed()  -> throws (wrapping failingCall's exception)
    } catch (Exception e) {
        REQUEST_ID.get() still == "req-500"  <- still inside the binding's block
        print "[req-500] request failed: ..."
    }
})
```

## 7. Gotchas & takeaways

> Both `StructuredTaskScope` (second incubator round) and `ScopedValue` (first appearance) are **incubator APIs in Java 20**, requiring `--enable-preview --add-modules jdk.incubator.concurrent`; their combined behavior is exactly what this round's refinements targeted, and both continued evolving — including eventual relocation out of the incubator namespace entirely — before final standardization in later JDKs.
- A scoped value's binding correctly propagates into subtasks forked by a `StructuredTaskScope` **opened within** the binding's block — but a scope (or any thread) started entirely outside that block, even one running concurrently, does not see the binding; propagation follows the structural nesting of the code, not general thread relationships.
- Exception handling code that runs after `scope.throwIfFailed()` throws is still "inside" the `ScopedValue.where(...).run()` block as long as the `try`/`catch` is nested within that block's lambda (as in Level 3) — moving the `catch` outside the `run()` call entirely would mean the scoped value is no longer bound there, so structure this kind of code carefully if the catch block also needs the bound context.
- `ShutdownOnFailure`'s automatic cancellation of sibling subtasks (demonstrated again here) composes cleanly with scoped values specifically because both mechanisms share the same block-based lifetime model — neither one needs special-casing to work correctly with the other, which is precisely the validation this second incubator round performed.
- The broader takeaway: scoped values and structured concurrency are designed as a matched pair for exactly this style of code — bind context once at the top of a request-handling method, fan out to concurrent subtasks underneath, and trust that both the context and the subtasks' lifetimes stay correctly bounded together without manual parameter threading or thread-pool bookkeeping.
