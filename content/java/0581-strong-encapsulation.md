---
card: java
gi: 581
slug: strong-encapsulation
title: Strong encapsulation
---

## 1. What it is

**Strong encapsulation** is the module system's enforcement, applied by the JDK to its own internal implementation packages, that classes outside a module can no longer reflectively bypass access checks (`setAccessible(true)`) into that module's non-exported, non-opened packages — even packages that used to be casually reachable via reflection on the classpath. It's the same `exports`/`opens` mechanism covered in earlier topics, applied by the JDK team to `java.base` and the other platform modules, closing off internals that were never meant to be depended on but had been reachable for two decades.

## 2. Why & when

Before Java 9, plenty of code — frameworks, serialization libraries, debugging tools, sometimes application code directly — used reflection to reach into JDK classes' private fields (`java.lang.String`'s internal character storage, `java.util.ArrayList`'s backing array) because reflection had no concept of module boundaries: `field.setAccessible(true)` simply worked, everywhere, unconditionally. This let tooling do useful things, but it also meant the JDK team couldn't freely change these internal representations without risking silent breakage in code that reflectively depended on implementation details never meant to be public. Strong encapsulation closes that gap: `java.base` and the other JDK platform modules now declare real, restrictive `opens` boundaries (in most cases, none at all for their genuinely internal packages), so `setAccessible(true)` against JDK-internal fields now throws `InaccessibleObjectException` by default, unless the JVM is explicitly launched with an override flag granting that access. This matters directly whenever you upgrade an older codebase (or a library/framework it depends on) to a modern JDK and something that used to reflectively poke into JDK internals suddenly fails — understanding *why*, and what the sanctioned fix or escape hatch is, is a common real-world JDK-upgrade task.

## 3. Core concept

```java
import java.lang.reflect.Field;

String s = "hello";
Field valueField = String.class.getDeclaredField("value"); // java.lang.String's internal byte[]
valueField.setAccessible(true); // throws InaccessibleObjectException by default on modern JDKs
```

`java.lang.String` lives in the `java.lang` package, part of the `java.base` module — a module that `exports java.lang` (so ordinary use of `String`'s public API works everywhere, as always) but does **not** `opens java.lang` to arbitrary code. `getDeclaredField("value")` succeeds (merely obtaining a reflective handle requires no special permission), but `setAccessible(true)` — the call that would actually let code read or write that normally-inaccessible private field — is exactly what strong encapsulation blocks by default.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="java.base exports java.lang for normal use but does not open it, so reflective access to private JDK fields is blocked by default">
  <rect x="20" y="20" width="280" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="47" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">new String(...), s.length(), etc. -&gt; OK (exports)</text>

  <rect x="320" y="20" width="300" height="45" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="470" y="47" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">field.setAccessible(true) on "value" -&gt; blocked (no opens)</text>

  <text x="20" y="100" fill="#8b949e" font-size="10" font-family="sans-serif">Same module (java.base), same package (java.lang) — two different permissions,</text>
  <text x="20" y="115" fill="#8b949e" font-size="10" font-family="sans-serif">granted independently: normal compiled use vs. reflective access-check bypass.</text>
</svg>

`exports` and `opens` are independent switches — a package can have one without the other, exactly as covered in the `opens` directive topic, now applied to the JDK's own code.

## 5. Runnable example

Scenario: a small "field inspector" debugging utility that reflects into an object's fields to print their values — starting with it failing when pointed at a JDK class's internals, then unlocking that specific case with an explicit JVM flag, then rewriting the utility to only ever reflect into the caller's *own* application classes, which need no special flags at all because same-module reflection is never restricted this way.

### Level 1 — Basic

```java
// File: FieldInspector.java
import java.lang.reflect.Field;

public class FieldInspector {
    public static void inspect(Object target, String fieldName) throws Exception {
        Field field = target.getClass().getDeclaredField(fieldName);
        field.setAccessible(true); // reflective bypass — this is what strong encapsulation blocks
        System.out.println(fieldName + " = " + field.get(target));
    }

    public static void main(String[] args) throws Exception {
        inspect("hello", "value"); // java.lang.String's internal byte[] storage
    }
}
```

**How to run:** `java FieldInspector.java`

Expected output (throws at runtime — this is the intended demonstration):
```
Exception in thread "main" java.lang.reflect.InaccessibleObjectException: Unable to make field private final byte[] java.lang.String.value accessible: module java.base does not "opens java.lang" to unnamed module @...
```

`target.getClass().getDeclaredField("value")` succeeds — merely obtaining the `Field` reflection object requires no special module permission. `field.setAccessible(true)` is where the failure occurs: `FieldInspector` runs as classpath code, in the unnamed module, and `java.base` does not `opens java.lang` to it — the exception message names the exact module (`java.base`) and package (`java.lang`) responsible, pointing precisely at what's being blocked and why.

### Level 2 — Intermediate

```java
// File: FieldInspector.java — UNCHANGED from Level 1
import java.lang.reflect.Field;

public class FieldInspector {
    public static void inspect(Object target, String fieldName) throws Exception {
        Field field = target.getClass().getDeclaredField(fieldName);
        field.setAccessible(true);
        System.out.println(fieldName + " = " + field.get(target));
    }

    public static void main(String[] args) throws Exception {
        inspect("hello", "value");
    }
}
```

**How to run:** the exact same source file, launched with an explicit JVM override flag:
```
java --add-opens java.base/java.lang=ALL-UNNAMED FieldInspector.java
```

Expected output:
```
value = [B@<some hash>
```

The real-world concern this adds: `--add-opens java.base/java.lang=ALL-UNNAMED` is a **JVM launch flag**, not a code change, that explicitly grants the reflective `opens` permission `java.base` normally withholds for `java.lang` — `ALL-UNNAMED` means "grant this to any classpath (unnamed-module) code." This is the standard, sanctioned escape hatch for legacy tooling that genuinely needs this kind of reflective access and can't be rewritten immediately: it makes the exact call that failed in Level 1 succeed, but requires an explicit, visible, deliberate opt-in at launch time — unlike pre-Java-9, where this "just worked" silently, with no visibility into which code depended on it.

### Level 3 — Advanced

```java
// File: SafeFieldInspector.java — reflects only into the CALLER'S OWN application classes
import java.lang.reflect.Field;

public class SafeFieldInspector {
    static class Order {
        private final String customerId = "cust-42";
        private final double total = 199.99;
    }

    public static void inspect(Object target, String fieldName) throws Exception {
        Field field = target.getClass().getDeclaredField(fieldName);
        field.setAccessible(true); // still called, but now WITHIN the same module — no flag needed
        System.out.println(fieldName + " = " + field.get(target));
    }

    public static void main(String[] args) throws Exception {
        Order order = new Order();
        inspect(order, "customerId"); // Order is defined right here — same class, same module
        inspect(order, "total");
    }
}
```

**How to run:** `java SafeFieldInspector.java` — no special flags needed at all.

Expected output:
```
customerId = cust-42
total = 199.99
```

This handles the production-flavoured, and genuinely robust, fix: rather than fighting strong encapsulation with `--add-opens` for every JDK class a debugging utility might ever be pointed at, `SafeFieldInspector` only reflects into `Order` — a class defined in the *same* compilation unit and therefore the *same* module (the unnamed module, in this classpath example, but the identical reasoning applies to real named modules). Reflective access within the same module has never been restricted by strong encapsulation at all — only *cross-module* reflective access is gated, exactly as the earlier `opens` directive topic covered — so this version needs no JVM flags, works identically on any JDK version, and never depends on JDK-internal representations that could change.

## 6. Walkthrough

Execution starts with the plain `java SafeFieldInspector.java` command in Level 3 — no `--add-opens`, no special flags, because this code doesn't need any.

`main` creates an `Order` instance with `customerId = "cust-42"` and `total = 199.99`, then calls `inspect(order, "customerId")`. Inside `inspect`, `target.getClass().getDeclaredField("customerId")` retrieves the `Field` object for `Order.customerId`. `field.setAccessible(true)` is called — the exact same method call that threw `InaccessibleObjectException` in Level 1 — but this time it succeeds immediately, without any special flag.

```
Level 1 (FieldInspector inspecting java.lang.String):        Level 3 (SafeFieldInspector inspecting its own Order):
FieldInspector's module: unnamed                              SafeFieldInspector's module: unnamed
String.class's module: java.base                              Order.class's module: unnamed (SAME module as the caller)
CROSS-module reflective access -> java.base doesn't            SAME-module reflective access -> never restricted
  opens java.lang to unnamed -> BLOCKED                          by strong encapsulation at all -> ALLOWED
```

The reason `setAccessible(true)` succeeds here is that the module-boundary check strong encapsulation performs only applies to **cross-module** reflective access — since `Order` is declared inside `SafeFieldInspector.java` itself, both classes belong to the exact same module (the unnamed module, since this is classpath code; the identical reasoning would apply if this were compiled as part of a real named module instead). There is no module boundary being crossed at all, so there's nothing for strong encapsulation to block.

`field.get(target)` reads `order.customerId`'s value, `"cust-42"`, and `inspect` prints `"customerId = cust-42"`. The second call, `inspect(order, "total")`, follows the identical path for the `total` field, printing `"total = 199.99"`.

This demonstrates the core lesson: strong encapsulation is not "reflection is now broken" — it's specifically "reflection *across module boundaries* into non-opened packages is now blocked." Code that only ever reflects into its own, same-module classes (a common pattern for internal debugging or testing utilities) is entirely unaffected, while code that reaches into another module's (especially the JDK's own) internals is exactly what gets stopped, by design.

## 7. Gotchas & takeaways

> `--add-opens` (and its siblings `--add-exports`, `--add-reads`) are meant as **temporary migration aids**, not permanent architecture — every JDK-internal API a codebase depends on via these flags remains a real risk of behavioral change or removal in a future JDK release, since the JDK team's compatibility commitment only ever covered the genuinely public, exported/opened surface. Treat any `--add-opens` flag in a production launch command as a tracked technical-debt item with a plan to remove the underlying dependency, not a permanent fixture.

- Not every JDK-internal package behaves the same way: `jdk.unsupported` (home to `sun.misc.Unsafe` and a handful of other historically-abused internals) is deliberately both exported *and* opened unconditionally by the JDK team specifically to ease migration — so code using `sun.misc.Unsafe` reflectively still works without any flag, even on modern JDKs, unlike `java.lang`'s private fields demonstrated above. Strong encapsulation's exact strictness varies package by package, based on the JDK team's own migration-friendliness decisions for that specific package.
- `jdeps --jdk-internals <jarfile>` is a JDK-bundled tool that scans a compiled JAR and reports exactly which internal, module-boundary-restricted JDK APIs it depends on, along with suggested public replacements where known — an essential first step when migrating an older codebase to a modern JDK and needing to find every strong-encapsulation-affected usage before it fails at runtime.
- `--add-opens module/package=target-module` (or `=ALL-UNNAMED` for classpath code) is the runtime flag for reflective access; the separate, compile-time equivalent for code that needs to `import` an internal type directly rather than reach it only via reflection is `--add-exports module/package=target-module` — both exist because `exports` (compile-time visibility) and `opens` (runtime reflective access) are independently gated, exactly as covered in the `opens` directive topic.
- Strong encapsulation was phased in gradually: earlier JDK 9+ releases allowed illegal reflective access by default with only a runtime *warning* printed to standard error (not yet an error), before later JDK versions made it a hard `InaccessibleObjectException` by default — always test against the specific target JDK version a codebase will actually run on, since the exact enforcement behavior has shifted across versions.
- Many popular frameworks (Spring, Hibernate, Jackson, and others) needed their own updates to add appropriate `--add-opens`-equivalent module directives or avoid JDK-internal reflection entirely as part of supporting modern JDKs — if a third-party framework throws `InaccessibleObjectException` referencing a `java.base` (or other JDK) package, check whether a newer version of that framework already fixed it before reaching for `--add-opens` as a workaround.
