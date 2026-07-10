---
card: java
gi: 985
slug: dynamic-proxies-java-lang-reflect-proxy
title: "Dynamic proxies (java.lang.reflect.Proxy)"
---

## 1. What it is

`java.lang.reflect.Proxy` lets you generate, entirely at runtime, a new class implementing one or more specified interfaces, with every single method call on any instance of that generated class routed to a single, generic `InvocationHandler` object you provide — no `.class` file for this proxy class exists anywhere in your source code or compiled output; the JVM synthesizes it on the fly, the first time you call `Proxy.newProxyInstance(classLoader, interfaces, handler)`. Inside the `InvocationHandler`'s single required method, `invoke(Object proxy, Method method, Object[] args)`, you receive complete reflective information about exactly which interface method was called and with what arguments, letting one handler implementation generically intercept, log, validate, delegate, or otherwise customize behavior for an entire interface's worth of methods, without writing a single hand-coded implementing class.

## 2. Why & when

Dynamic proxies matter for exactly the kind of cross-cutting, interface-uniform behavior that would otherwise require either a hand-written wrapper class implementing every method of a potentially large interface (tedious, and needing to be kept manually in sync if the interface changes) or code generation at build time (adding a build-step dependency). Spring's own AOP (aspect-oriented programming) proxies, many mocking frameworks (Mockito's interface mocks), and lazy-loading or transactional-wrapper patterns in various frameworks all rely on exactly this mechanism: given only an interface, generate an implementing class on the fly whose every method delegates to a single, shared piece of logic — logging every call, checking a transaction is active before delegating to the real implementation, recording calls for later verification in a test, or lazily creating the real underlying object only when its first method is actually invoked. The key limitation to know: `Proxy.newProxyInstance` can only generate a proxy implementing *interfaces*, never a concrete class — for proxying an arbitrary concrete class (one without a suitable interface already in place), a different mechanism (typically bytecode-generation libraries like CGLIB or ByteBuddy, which Spring itself falls back to for exactly this case) is required instead.

## 3. Core concept

```java
interface Greeter {
    String greet(String name);
}

InvocationHandler handler = (proxy, method, args) -> {
    System.out.println("calling: " + method.getName() + " with args: " + Arrays.toString(args));
    return "Hello, " + args[0] + "! (via proxy)";
};

Greeter greeter = (Greeter) Proxy.newProxyInstance(
    Greeter.class.getClassLoader(),
    new Class<?>[]{ Greeter.class },   // the interface(s) the proxy will implement
    handler                             // EVERY method call routes through this ONE handler
);

greeter.greet("Ada");   // routes through 'handler', which decides what to actually do and return
```

Every method call on `greeter` — regardless of which interface method was actually called — is routed uniformly through the single `handler.invoke(...)` call, which receives full reflective information (the `Method` object, the actual arguments) about exactly which call is happening, letting one implementation handle an entire interface generically.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A generated proxy class implementing an interface, routing every method call through a single shared InvocationHandler, which decides what to actually do for each call" >
  <rect x="20" y="30" width="180" height="60" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Proxy (generated class)</text>
  <text x="110" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">implements Greeter</text>

  <rect x="260" y="30" width="180" height="60" fill="#1c2430" stroke="#6db33f"/>
  <text x="350" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">InvocationHandler</text>
  <text x="350" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ONE handler for EVERY method</text>

  <rect x="480" y="30" width="140" height="60" fill="#1c2430" stroke="#f0883e"/>
  <text x="550" y="55" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">decides: log, delegate,</text>
  <text x="550" y="70" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">validate, mock, etc.</text>

  <line x1="200" y1="60" x2="260" y2="60" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="440" y1="60" x2="480" y2="60" stroke="#8b949e" marker-end="url(#a)"/>

  <text x="320" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Every one of Greeter's methods, whatever they are, routes through this SAME handler</text>
</svg>

*Every method call on a generated proxy routes through one shared handler, which decides how to respond based on which method was actually called.*

## 5. Runnable example

Scenario: build a small logging and delegating proxy around a real service interface, evolving from a basic logging-only proxy, to a realistic proxy that both logs and delegates to a real implementation, to a more advanced case building a simple, generic retry-on-failure wrapper usable for any interface at all.

### Level 1 — Basic

```java
import java.lang.reflect.*;
import java.util.*;

public class DynamicProxyBasic {
    interface Greeter {
        String greet(String name);
    }

    public static void main(String[] args) {
        InvocationHandler handler = (proxy, method, methodArgs) -> {
            System.out.println("intercepted call to: " + method.getName());
            return "Hello, " + methodArgs[0] + "!";
        };

        Greeter greeter = (Greeter) Proxy.newProxyInstance(
            DynamicProxyBasic.class.getClassLoader(),
            new Class<?>[]{ Greeter.class },
            handler
        );

        System.out.println(greeter.greet("Ada"));
    }
}
```

**How to run:** `java DynamicProxyBasic.java` (JDK 17+).

Expected output:
```
intercepted call to: greet
Hello, Ada!
```

There is no actual `Greeter`-implementing class anywhere in this source file — `Proxy.newProxyInstance` generates one at runtime, and every call to any of `Greeter`'s methods (here, just `greet`) is routed through the single `handler` lambda, which decides what to do and return, entirely generically, based on the `Method` object it receives.

### Level 2 — Intermediate

```java
import java.lang.reflect.*;

public class DynamicProxyLoggingDelegate {
    interface Calculator {
        int add(int a, int b);
        int multiply(int a, int b);
    }

    static class RealCalculator implements Calculator {
        public int add(int a, int b) { return a + b; }
        public int multiply(int a, int b) { return a * b; }
    }

    public static void main(String[] args) {
        Calculator real = new RealCalculator();

        InvocationHandler loggingHandler = (proxy, method, methodArgs) -> {
            System.out.println("calling " + method.getName() + Arrays.toString(methodArgs));
            Object result = method.invoke(real, methodArgs); // DELEGATE to the real implementation
            System.out.println("result: " + result);
            return result;
        };

        Calculator proxied = (Calculator) Proxy.newProxyInstance(
            DynamicProxyLoggingDelegate.class.getClassLoader(),
            new Class<?>[]{ Calculator.class },
            loggingHandler
        );

        proxied.add(3, 4);
        proxied.multiply(5, 6);
    }
}
```

**How to run:** `java DynamicProxyLoggingDelegate.java` (JDK 17+; requires `import java.util.Arrays;`).

Expected output:
```
calling add[3, 4]
result: 7
calling multiply[5, 6]
result: 30
```

The real-world concern added: `loggingHandler` genuinely delegates to a *real* implementation (`method.invoke(real, methodArgs)`), logging before and after — this is exactly the cross-cutting logging/instrumentation pattern proxies are commonly used for: the actual calculation logic lives entirely in `RealCalculator`, completely unaware it's being proxied, while the proxy transparently adds logging behavior around every single method call, for both `add` and `multiply`, without either method needing its own separate logging code.

### Level 3 — Advanced

```java
import java.lang.reflect.*;

public class DynamicProxyRetryWrapper {
    interface FlakyService {
        String fetchData();
    }

    static class UnreliableService implements FlakyService {
        int attemptCount = 0;
        public String fetchData() {
            attemptCount++;
            if (attemptCount < 3) {
                throw new RuntimeException("simulated transient failure (attempt " + attemptCount + ")");
            }
            return "real data (succeeded on attempt " + attemptCount + ")";
        }
    }

    // A GENERIC retry-wrapping factory -- works for ANY interface, not just FlakyService,
    // since it operates purely reflectively over whatever interface/target it's given.
    @SuppressWarnings("unchecked")
    static <T> T withRetry(T target, Class<T> iface, int maxAttempts) {
        InvocationHandler retryHandler = (proxy, method, args) -> {
            RuntimeException lastFailure = null;
            for (int attempt = 1; attempt <= maxAttempts; attempt++) {
                try {
                    return method.invoke(target, args);
                } catch (InvocationTargetException e) {
                    lastFailure = (RuntimeException) e.getCause();
                    System.out.println("attempt " + attempt + " failed: " + lastFailure.getMessage());
                }
            }
            throw lastFailure;
        };
        return (T) Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{ iface }, retryHandler);
    }

    public static void main(String[] args) {
        FlakyService retrying = withRetry(new UnreliableService(), FlakyService.class, 5);
        System.out.println("final result: " + retrying.fetchData());
    }
}
```

**How to run:** `java DynamicProxyRetryWrapper.java` (JDK 17+).

Expected output:
```
attempt 1 failed: simulated transient failure (attempt 1)
attempt 2 failed: simulated transient failure (attempt 2)
final result: real data (succeeded on attempt 3)
```

The production-flavored hard case: `withRetry` is a fully generic factory — it works for `FlakyService` here, but the identical code would work unchanged for any other interface at all, since it operates purely on the reflective `Method`/`Class` information it's given, never hard-coding any specific interface's method names; this is exactly the kind of reusable, cross-cutting resilience wrapper (retry logic, in this case) real production frameworks build using dynamic proxies, letting arbitrary interfaces gain retry behavior without their own implementing classes needing any retry-specific code at all.

## 6. Walkthrough

Tracing `retrying.fetchData()` end to end from `DynamicProxyRetryWrapper.main`:

1. `retrying` is a dynamically-generated proxy implementing `FlakyService`, backed by `retryHandler` — calling `retrying.fetchData()` routes this call, via the JVM's proxy machinery, into `retryHandler.invoke(proxy, method, args)`, with `method` representing `FlakyService.fetchData` and `args` being an empty array (since `fetchData` takes no parameters).
2. Inside the handler, the `for` loop begins its first attempt: `method.invoke(target, args)` reflectively calls `fetchData()` on the actual underlying `UnreliableService` instance (`target`) — this increments `attemptCount` to `1`, and since `1 < 3`, the real method throws a `RuntimeException`.
3. Because reflective invocation wraps any exception thrown by the invoked method in `InvocationTargetException`, the `catch` block catches this wrapper, extracts the original exception via `e.getCause()`, stores it as `lastFailure`, and prints the failure message for attempt 1 — the loop then continues to its next iteration rather than propagating the failure immediately.
4. The second attempt repeats the identical process: `method.invoke` is called again, `attemptCount` becomes `2`, and since `2 < 3` is still true, another exception is thrown, caught, and logged as attempt 2's failure.
5. The third attempt calls `method.invoke` once more: `attemptCount` becomes `3`, and since `3 < 3` is now false, `UnreliableService.fetchData` returns normally this time, with the string `"real data (succeeded on attempt 3)"` — because this call succeeded without throwing, the handler's `return method.invoke(target, args)` line (inside the `try` block) returns this value directly, immediately exiting both the `for` loop and the `invoke` method altogether, without needing any further retry attempts.
6. This returned value propagates back out through the proxy machinery as the result of the original `retrying.fetchData()` call in `main`, which prints `"final result: real data (succeeded on attempt 3)"` — demonstrating that the entire retry logic (catching failures, logging each attempt, eventually succeeding or exhausting attempts) was applied transparently around `UnreliableService`'s own method, which itself contains no retry-related code whatsoever — all of that behavior was added purely through the generic, reflective proxy wrapper.

## 7. Gotchas & takeaways

> **Gotcha:** `Proxy.newProxyInstance` can only generate proxies implementing interfaces — it has no way to proxy a concrete class that doesn't already implement a suitable interface, since there is no interface method signature list for the generated proxy class to conform to; proxying an arbitrary concrete class instead requires a bytecode-generation library (CGLIB, ByteBuddy), which works differently (generating an actual subclass of the target class rather than an interface-implementing proxy) and is what frameworks like Spring fall back to automatically when no suitable interface is available.

- `Proxy.newProxyInstance` generates, entirely at runtime, a class implementing one or more specified interfaces, routing every method call through a single, shared `InvocationHandler`.
- This mechanism underlies cross-cutting behaviors applied uniformly across an entire interface — logging, transactional wrapping, lazy initialization, mocking, and retry logic — without needing a hand-written implementing class per interface.
- The `InvocationHandler`'s `invoke(proxy, method, args)` receives full reflective information about exactly which method was called and with what arguments, letting one handler implementation generically process an entire interface's worth of methods.
- Delegating to a real underlying implementation from within the handler (`method.invoke(target, args)`) lets a proxy add behavior *around* real logic (logging, retrying, validating) without modifying that real implementation at all.
- Dynamic proxies can only implement interfaces, never concrete classes directly — proxying a concrete class without a suitable interface requires a different mechanism, typically a bytecode-generation library.
- See [Reflection API deep dive](0983-reflection-api-deep-dive.md) for the underlying `Method`/reflective machinery dynamic proxies are built directly on top of, and [ServiceLoader & SPI](0988-serviceloader-spi.md) for a different, complementary mechanism for discovering and loading interface implementations dynamically.
