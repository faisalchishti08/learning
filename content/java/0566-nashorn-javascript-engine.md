---
card: java
gi: 566
slug: nashorn-javascript-engine
title: Nashorn JavaScript engine
---

## 1. What it is

Nashorn was the JavaScript engine bundled with the JDK starting in Java 8, accessible through the standard `javax.script` API (`ScriptEngineManager`, `ScriptEngine`). It replaced the older, slower Rhino engine, compiling JavaScript to JVM bytecode for much better performance, and let Java code evaluate JavaScript, call JavaScript functions, and pass objects back and forth between the two languages in the same process.

## 2. Why & when

Embedding a scripting language inside a Java application is useful when you want end users or configuration files to supply *logic*, not just data — a pricing rule, a validation expression, a small transformation — without recompiling and redeploying the Java application itself. Before Nashorn, doing this with JavaScript meant either the slow Rhino engine or a third-party dependency. Nashorn shipped in the JDK itself (Java 8 through Java 14, after which it was removed from the JDK and later deprecated), so any Java 8+ application could embed a reasonably fast JavaScript engine with zero extra dependencies via `javax.script`. It's worth understanding both for legacy codebases still using it, and because it's a good example of the JVM's general "scripting engine" abstraction (`javax.script` also supports other JSR-223-compliant languages).

## 3. Core concept

```java
import javax.script.*;

ScriptEngineManager manager = new ScriptEngineManager();
ScriptEngine engine = manager.getEngineByName("nashorn");

Object result = engine.eval("1 + 2 * 3");
System.out.println(result); // 7 (as a Java Double/Integer, depending on the expression)

engine.eval("function greet(name) { return 'Hello, ' + name + '!'; }");
Invocable invocable = (Invocable) engine;
Object greeting = invocable.invokeFunction("greet", "World");
System.out.println(greeting); // Hello, World!
```

`ScriptEngineManager.getEngineByName("nashorn")` looks up the engine by its JSR-223 name. `eval(...)` runs a script and returns its last expression's value as a Java `Object`. Casting the engine to `Invocable` unlocks calling a specific JavaScript function by name from Java code, passing Java arguments and receiving a Java-usable return value.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java code hands a script to Nashorn, which runs it on the JVM and returns a Java-usable result">
  <rect x="10" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="100" y="50" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java code</text>

  <line x1="190" y1="35" x2="250" y2="35" stroke="#8b949e" stroke-width="2" marker-end="url(#n1)"/>
  <text x="220" y="25" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">eval(script)</text>

  <rect x="250" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="340" y="45" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Nashorn engine</text>
  <text x="340" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">compiles JS -&gt; JVM bytecode</text>

  <line x1="250" y1="65" x2="190" y2="65" stroke="#8b949e" stroke-width="2" marker-end="url(#n2)"/>
  <text x="220" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Java-usable result</text>

  <text x="10" y="120" fill="#8b949e" font-size="10" font-family="sans-serif">Java objects passed into the script are directly usable as JS objects, and vice versa.</text>

  <defs>
    <marker id="n1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="n2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The engine runs inside the same JVM process as the calling Java code — no separate process, no serialization boundary.

## 5. Runnable example

Scenario: letting a pricing rule be supplied as a small JavaScript expression instead of hard-coded Java — starting with evaluating a single expression, then calling a named JavaScript function with arguments, then binding a Java object into the script's scope so the script can read and use real application data.

**Note:** Nashorn shipped in the JDK for Java 8–14 and was removed as a built-in engine afterward (its standalone successor is the separate `org.openjdk.nashorn:nashorn-core` artifact). These examples require running on a JDK version (8–14) that still bundles Nashorn, e.g. via `java` from a JDK 11 or JDK 14 installation.

### Level 1 — Basic

```java
import javax.script.*;

public class NashornBasic {
    public static void main(String[] args) throws ScriptException {
        ScriptEngineManager manager = new ScriptEngineManager();
        ScriptEngine engine = manager.getEngineByName("nashorn");

        Object result = engine.eval("2 + 3 * 4");
        System.out.println("Result: " + result);
        System.out.println("Java type: " + result.getClass().getSimpleName());
    }
}
```

**How to run:** `java NashornBasic.java` (on a JDK 8–14 that bundles Nashorn)

Expected output:
```
Result: 14
Java type: Integer
```

`manager.getEngineByName("nashorn")` retrieves the Nashorn `ScriptEngine`. `engine.eval("2 + 3 * 4")` runs that JavaScript expression using standard JavaScript operator precedence (multiplication before addition), and returns the final expression's value as a Java `Object` — here, a boxed `Integer`, since Nashorn maps small whole-number JavaScript values to Java's `Integer` where possible.

### Level 2 — Intermediate

```java
import javax.script.*;

public class NashornPricingRule {
    public static void main(String[] args) throws ScriptException, NoSuchMethodException {
        ScriptEngineManager manager = new ScriptEngineManager();
        ScriptEngine engine = manager.getEngineByName("nashorn");

        // A pricing rule supplied as JavaScript — could come from a config file at runtime.
        String pricingRuleScript =
            "function calculatePrice(basePrice, quantity) {" +
            "    var discount = quantity >= 10 ? 0.15 : (quantity >= 5 ? 0.05 : 0.0);" +
            "    return basePrice * quantity * (1 - discount);" +
            "}";

        engine.eval(pricingRuleScript);
        Invocable invocable = (Invocable) engine;

        Object price1 = invocable.invokeFunction("calculatePrice", 10.0, 3);
        Object price2 = invocable.invokeFunction("calculatePrice", 10.0, 7);
        Object price3 = invocable.invokeFunction("calculatePrice", 10.0, 12);

        System.out.println("3 units:  $" + price1);
        System.out.println("7 units:  $" + price2);
        System.out.println("12 units: $" + price3);
    }
}
```

**How to run:** `java NashornPricingRule.java`

Expected output:
```
3 units:  $30.0
7 units:  $66.5
12 units: $102.0
```

The real-world concern this adds: calling a **named function by argument** rather than only evaluating a bare expression, letting the same script define multiple reusable pieces of logic. `invocable.invokeFunction("calculatePrice", 10.0, 3)` passes Java `double` and `int` arguments into the JavaScript function — Nashorn converts them to JavaScript numbers automatically — and the discount tiers defined entirely in JavaScript (no discount under 5 units, 5% for 5–9, 15% for 10+) determine the final price, without any of that pricing logic living in compiled Java code.

### Level 3 — Advanced

```java
import javax.script.*;
import java.util.*;

public class NashornDataBinding {
    public static class Order {
        public double basePrice;
        public int quantity;
        public String customerTier;

        public Order(double basePrice, int quantity, String customerTier) {
            this.basePrice = basePrice;
            this.quantity = quantity;
            this.customerTier = customerTier;
        }
    }

    public static void main(String[] args) throws ScriptException {
        ScriptEngineManager manager = new ScriptEngineManager();
        ScriptEngine engine = manager.getEngineByName("nashorn");

        String pricingRuleScript =
            "var discount = 0.0;" +
            "if (order.customerTier === 'GOLD') { discount = 0.20; }" +
            "else if (order.customerTier === 'SILVER') { discount = 0.10; }" +
            "else if (order.quantity >= 10) { discount = 0.05; }" +
            "var finalPrice = order.basePrice * order.quantity * (1 - discount);" +
            "finalPrice;"; // last expression is the eval() result

        List<Order> orders = List.of(
            new Order(20.0, 3, "GOLD"),
            new Order(20.0, 3, "SILVER"),
            new Order(20.0, 12, "BRONZE")
        );

        for (Order order : orders) {
            engine.put("order", order); // bind this Java object into the script's scope
            Object finalPrice = engine.eval(pricingRuleScript);
            System.out.println(order.customerTier + ", qty=" + order.quantity + " -> $" + finalPrice);
        }
    }
}
```

**How to run:** `java NashornDataBinding.java`

Expected output:
```
GOLD, qty=3 -> $48.0
SILVER, qty=3 -> $54.0
BRONZE, qty=12 -> $228.0
```

This handles the production-flavoured case of **binding a real Java object into the script's variable scope** via `engine.put("order", order)`, so the JavaScript pricing rule can read `order.basePrice`, `order.quantity`, and `order.customerTier` directly as if they were native JavaScript object properties — Nashorn exposes public Java fields and getters transparently to script code, letting the same script logic run once per order without regenerating the script text for each order's data.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Three `Order` instances are built with different customer tiers and quantities: GOLD/3, SILVER/3, BRONZE/12.

`pricingRuleScript` is a single JavaScript string defining tiered discount logic based on a variable named `order`, which does not yet exist when the string is written — it's expected to be supplied from the Java side before each `eval` call.

The `for` loop processes each `Order` in sequence. For the first order (GOLD, qty=3): `engine.put("order", order)` binds this specific `Order` instance into the engine's scope under the name `order`, making its public fields readable from JavaScript as `order.basePrice`, `order.quantity`, `order.customerTier`.

`engine.eval(pricingRuleScript)` then runs the script against that binding:

```
order.customerTier === 'GOLD'  -> true  -> discount = 0.20
finalPrice = order.basePrice * order.quantity * (1 - discount)
           = 20.0 * 3 * (1 - 0.20)
           = 60.0 * 0.80
           = 48.0
```

The script's last statement, the bare expression `finalPrice;`, becomes `eval`'s return value — `48.0`, returned as a Java `Object` (a boxed `Double`). `main` prints `"GOLD, qty=3 -> $48.0"`.

The loop's second iteration rebinds `order` to the SILVER order via another `engine.put("order", order)` call — this **overwrites** the previous binding in the same shared engine scope, so the script sees the new order's data on this `eval` call: `customerTier === 'SILVER'` is `true`, so `discount = 0.10`, giving `finalPrice = 20.0 * 3 * 0.90 = 54.0`.

The third iteration binds the BRONZE order (qty=12): neither the GOLD nor SILVER branch matches, but `order.quantity >= 10` is `true` (12 >= 10), so `discount = 0.05`, giving `finalPrice = 20.0 * 12 * 0.95 = 228.0`. Each iteration's `eval` call re-runs the *entire* script from scratch against the newly bound `order`, which is why the same `pricingRuleScript` string can be reused unchanged across all three, different-shaped inputs.

## 7. Gotchas & takeaways

> Nashorn was **deprecated in Java 11** (JEP 335) and **removed from the JDK entirely starting with Java 15** (JEP 372) — `manager.getEngineByName("nashorn")` returns `null` on Java 15+, causing a `NullPointerException` on the next line unless checked. New code targeting Java 15+ needing embedded JavaScript should use the standalone `org.openjdk.nashorn:nashorn-core` Maven artifact (same engine, now maintained outside the JDK) or a different embedded engine like GraalVM's JavaScript support.

- `engine.eval(...)` returns the value of the script's **last expression or statement**, similar to how a JavaScript REPL echoes the last evaluated value — end scripts with a bare expression (as in the Level 3 example) when you need a return value from `eval` itself.
- `engine.put(key, value)` and `engine.get(key)` bind Java values into (and read them back from) the engine's default scope — bindings persist across multiple `eval` calls on the same engine unless overwritten or the scope is reset.
- Casting the engine to `Invocable` (as in Level 2) is required to call a specific named function directly with `invokeFunction(...)`, rather than only being able to `eval` an entire script and read its trailing expression.
- Numeric type conversions between Java and JavaScript aren't always exact one-to-one — small whole numbers often surface in Java as `Integer`, while others become `Double`; always check `result.getClass()` if precise Java typing matters downstream.
- Because Nashorn compiles to real JVM bytecode, scripts run inside the same JVM process, sandboxing, and permission model as the host Java application — untrusted script content can still perform actions the host process is authorized for (reading files, opening sockets), so never `eval` untrusted script content without a proper security sandbox.
