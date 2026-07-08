---
card: java
gi: 457
slug: java-lang-invoke-methodhandle-methodtype
title: java.lang.invoke (MethodHandle, MethodType)
---

## 1. What it is

`java.lang.invoke`, added in Java 7 alongside `invokedynamic`, is the package that gives ordinary Java code a typed, efficient way to look up and call a method, constructor, or field access as a first-class value. Its two central types are `MethodType` — an immutable description of a method's signature (return type plus parameter types, with no method attached) — and `MethodHandle` — a direct, typed reference to one specific method, constructor, or field accessor that you can invoke almost like calling a method pointer. Together they are the API layer that sits underneath `invokedynamic`, but you can also use them directly from plain Java code without ever touching bytecode generation.

## 2. Why & when

Before Java 7, the only way to call a method whose name you only know at runtime was **reflection** (`Method.invoke`). Reflection works, but every call goes through access checks, argument boxing into an `Object[]`, and a fair amount of internal dispatch overhead — a `Method` object does not know its exact signature at the JVM bytecode level, so the JVM cannot optimize the call site as aggressively as a normal method call. `MethodHandle` was designed to close that gap: once you have looked up a handle and it has "warmed up," the JVM can inline and optimize a `MethodHandle.invoke` call much like a direct method call, because the handle carries an exact, static `MethodType`.

You reach for `java.lang.invoke` when you are building infrastructure that needs fast, repeated, dynamically-selected method calls: language runtimes hosted on the JVM, serialization/reflection frameworks, dependency-injection containers, or any library doing the kind of "call this method by name, many times, as fast as possible" work that plain reflection makes slow. For everyday application code where you already know the method at compile time, you simply call the method directly — `MethodHandle` is a specialist tool for framework and library authors, not a replacement for normal method calls.

## 3. Core concept

```java
import java.lang.invoke.*;

MethodHandles.Lookup lookup = MethodHandles.lookup();

// MethodType: describes a signature -- "returns int, takes (String)"
MethodType methodType = MethodType.methodType(int.class, String.class);

// MethodHandle: a direct, typed handle to String.length()
MethodHandle lengthHandle = lookup.findVirtual(String.class, "length",
        MethodType.methodType(int.class));

int len = (int) lengthHandle.invoke("hello"); // 5 -- call it like a method pointer
```

`MethodType` is just data — a signature with no target. `MethodHandle` is the callable thing: you obtain one from a `Lookup` object (which also enforces normal Java access control — you cannot use a public `Lookup` to reach a `private` method you would not otherwise be allowed to call), and then invoke it with `invoke` or `invokeExact`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Lookup finds a method matching a MethodType and returns a MethodHandle that can be invoked directly">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="150" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="60" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">MethodType</text>
  <text x="105" y="74" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(int, String)</text>

  <rect x="245" y="30" width="150" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="60" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Lookup.findVirtual</text>
  <text x="320" y="74" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(access-checked)</text>

  <rect x="460" y="30" width="150" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="535" y="60" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">MethodHandle</text>
  <text x="535" y="74" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">callable target</text>

  <line x1="180" y1="55" x2="240" y2="55" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="395" y1="55" x2="455" y2="55" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>

  <rect x="245" y="120" width="150" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="144" fill="#f0883e" font-size="12" text-anchor="middle" font-family="sans-serif">handle.invoke(args)</text>
  <line x1="535" y1="80" x2="535" y2="140" stroke="#8b949e" stroke-width="2"/>
  <line x1="535" y1="140" x2="400" y2="140" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A `MethodType` describes the shape of a call; `Lookup` turns that shape plus a name into an executable `MethodHandle`.

## 5. Runnable example

Scenario: building a tiny "call any method by name" dispatcher — the same idea evolved from a single hard-coded handle, through a name-keyed registry of handles built once and reused, to a handle bound to different receiver instances at invocation time.

### Level 1 — Basic

```java
import java.lang.invoke.*;

public class MHBasic {
    public static void main(String[] args) throws Throwable {
        MethodHandles.Lookup lookup = MethodHandles.lookup();

        MethodHandle upperCase = lookup.findVirtual(String.class, "toUpperCase",
                MethodType.methodType(String.class));

        String result = (String) upperCase.invoke("hello");
        System.out.println(result);
    }
}
```

**How to run:** `java MHBasic.java`

Expected output:
```
HELLO
```

`findVirtual` looks up an instance method by declaring class, name, and `MethodType` (here: takes no arguments, returns `String`). `invoke` then calls it on the receiver `"hello"`, exactly as `"hello".toUpperCase()` would.

### Level 2 — Intermediate

```java
import java.lang.invoke.*;
import java.util.*;

public class MHRegistry {
    static final Map<String, MethodHandle> REGISTRY = new HashMap<>();

    static void register(String name, Class<?> owner, String methodName, MethodType type) throws Exception {
        MethodHandles.Lookup lookup = MethodHandles.lookup();
        REGISTRY.put(name, lookup.findVirtual(owner, methodName, type));
    }

    public static void main(String[] args) throws Throwable {
        // Build the registry once -- looking up a handle has real cost, so we do it a single time.
        register("upper", String.class, "toUpperCase", MethodType.methodType(String.class));
        register("trim", String.class, "trim", MethodType.methodType(String.class));
        register("length", String.class, "length", MethodType.methodType(int.class));

        String input = "  hello world  ";
        String trimmed = (String) REGISTRY.get("trim").invoke(input);
        String upper = (String) REGISTRY.get("upper").invoke(trimmed);
        int length = (int) REGISTRY.get("length").invoke(upper);

        System.out.println("Result: \"" + upper + "\" length=" + length);
    }
}
```

**How to run:** `java MHRegistry.java`

Expected output:
```
Result: "HELLO WORLD" length=11
```

This is the real-world concern reflection-heavy frameworks face: looking up a handle is comparatively expensive, so you do it **once** at startup, cache it (here, in a `Map<String, MethodHandle>` keyed by a logical operation name), and reuse the same handle for every future call — exactly the pattern a dependency-injection container or an ORM uses to avoid repeated reflective lookups per request.

### Level 3 — Advanced

```java
import java.lang.invoke.*;
import java.util.*;

public class MHDispatcher {
    record Account(String owner, double balance) {
        double withdraw(double amount) {
            if (amount > balance) throw new IllegalStateException("insufficient funds for " + owner);
            return balance - amount;
        }
    }

    public static void main(String[] args) throws Throwable {
        MethodHandles.Lookup lookup = MethodHandles.lookup();

        // One handle, bound to the Account type -- reused across MANY different receiver instances.
        MethodHandle withdraw = lookup.findVirtual(Account.class, "withdraw",
                MethodType.methodType(double.class, double.class));

        List<Account> accounts = List.of(
                new Account("alice", 100.0),
                new Account("bob", 40.0)
        );

        for (Account account : accounts) {
            try {
                double newBalance = (double) withdraw.invoke(account, 50.0);
                System.out.println(account.owner() + " new balance: " + newBalance);
            } catch (IllegalStateException e) {
                System.out.println(account.owner() + " withdraw failed: " + e.getMessage());
            } catch (Throwable t) {
                // MethodHandle.invoke declares "throws Throwable" -- it can propagate
                // checked exceptions, unchecked exceptions, and even Errors undeclared.
                throw new RuntimeException("unexpected failure", t);
            }
        }
    }
}
```

**How to run:** `java MHDispatcher.java`

Expected output:
```
alice new balance: 50.0
bob withdraw failed: insufficient funds for bob
```

One `MethodHandle` for `Account.withdraw(double)` is looked up a single time, then invoked once per `Account` instance with a different receiver each time — the handle is not tied to one object, only to the method's shape, so it is reused exactly like `REGISTRY.get("trim")` was reused across different string arguments in Level 2. `withdraw.invoke(account, 50.0)` passes `account` as the receiver (the `this`) and `50.0` as the method's own argument.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. First, `MethodHandles.lookup()` captures a `Lookup` object scoped to `MHDispatcher` — this is the access-control context: it can find anything `MHDispatcher` itself would legally be allowed to call.

`lookup.findVirtual(Account.class, "withdraw", MethodType.methodType(double.class, double.class))` searches `Account` for an instance method named `withdraw` that returns `double` and takes one `double` parameter. It finds `Account.withdraw(double)` and returns a `MethodHandle` bound to that exact signature — this lookup happens **once**, before the loop.

The `for` loop then iterates over two `Account` records. On each iteration, `withdraw.invoke(account, 50.0)` calls the handle: the first argument (`account`) is treated as the receiver — the object `withdraw` is called *on* — and the remaining argument (`50.0`) is the method's actual parameter. This is equivalent to writing `account.withdraw(50.0)` directly, but the method to call was chosen once, generically, ahead of time.

For `alice` (balance 100.0), `withdraw(50.0)` runs: `amount > balance` is `50.0 > 100.0`, false, so it returns `balance - amount = 50.0`. That value comes back through `invoke` as an `Object`, gets cast to `double`, and is printed.

For `bob` (balance 40.0), `withdraw(50.0)` runs: `50.0 > 40.0` is true, so `Account.withdraw` throws `IllegalStateException("insufficient funds for bob")`. Because `invoke` propagates whatever the underlying method throws, unwrapped, that same `IllegalStateException` surfaces directly at the call site and is caught by the `catch (IllegalStateException e)` block, printing the failure message.

```
account (receiver) --+
                      |
50.0 (argument)   ----+--> withdraw.invoke(account, 50.0) --> Account.withdraw(double) --> double or throw
```

## 7. Gotchas & takeaways

> `MethodHandle.invoke` is polymorphic-signature and declares `throws Throwable` — the compiler does not check argument types or count against the handle's actual signature at compile time the way it would for a normal method call. Passing the wrong number or type of arguments compiles fine and fails with a `WrongMethodTypeException` at runtime. Prefer `invokeExact` when you want the compiler-checked, zero-adaptation form, and only use the looser `invoke` when you deliberately want argument-type adaptation.

- `MethodType` is pure signature data (return type + parameter types) with no target method — build one with `MethodType.methodType(returnType, paramTypes...)`.
- `MethodHandle` is a direct, typed, callable reference to one specific method, constructor, or field accessor — obtained through a `Lookup`, which also enforces the same access control (`public`/`private`/package) that ordinary Java code is subject to.
- Looking up a handle has real, one-time cost — do it once (at startup, in a cache, in a registry) and reuse the resulting handle many times, exactly as frameworks do.
- A `MethodHandle` for an instance method is not bound to one receiver — the same handle can be invoked against many different objects of the matching type, passing the receiver as the first argument to `invoke`.
- This package is the foundation `invokedynamic` is built on, but you can and do use `MethodHandle`/`MethodType` directly from plain Java code, without generating any bytecode yourself.
