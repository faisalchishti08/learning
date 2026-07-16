---
card: spring-integration
gi: 81
slug: scripting-support-groovy-jsr-223
title: "Scripting support (Groovy, JSR-223)"
---

## 1. What it is

Scripting support (`ScriptExecutingMessageProcessor`, `Scripts.script(...)`, working through the JSR-223 `ScriptEngine` API) lets a flow's transformer, filter, router, or service activator logic be written as an external script — Groovy, JavaScript (Nashorn/GraalVM), Python (Jython), or any other JSR-223-compliant language — instead of compiled Java. The script is evaluated at runtime against the message, and its result becomes the step's output, letting behavior be changed by editing a script file rather than recompiling and redeploying the application.

## 2. Why & when

You reach for scripting support when a piece of flow logic genuinely needs to change more often, or more flexibly, than a compiled deployment cycle allows:

- **Business rules change frequently and are owned by someone who shouldn't need a full deployment pipeline** — a discount-eligibility rule expressed as a small Groovy script can be edited and reloaded without rebuilding and redeploying the whole application, provided the script location is refreshable at runtime.
- **A small piece of custom logic doesn't warrant a full Java class** — a one-line filter condition or a simple field transformation, expressed inline as a script string in configuration, avoids the ceremony of a dedicated Java class solely for that purpose.
- **The exact language matters less than the flexibility** — because scripting support works through the generic JSR-223 API, the same mechanism supports Groovy, JavaScript, or other supported languages depending on team familiarity, without changing how the flow wires the script in.

## 3. Core concept

Think of compiled Java logic as a fixed machine part, custom-milled and bolted into place — reliable, but changing it means shutting down the whole machine, removing the part, and installing a newly machined replacement. A script-based step is more like a small chalkboard bolted next to the machine with instructions written on it: an operator can erase and rewrite those instructions on the fly (assuming the script source can be reloaded), and the machine reads them fresh each time it needs to make that particular decision — much more flexible, at the cost of losing some of the compiler's up-front checking that a bolted-on Java part gets for free.

```java
@Bean
public IntegrationFlow discountEligibilityFlow() {
    return IntegrationFlow.from("orderChannel")
        .filter(Scripts.script("classpath:scripts/isDiscountEligible.groovy")
            .lang("groovy")
            .refreshCheckDelay(30_000)) // reload the script from disk if it changed
        .handle((Order order, headers) -> discountService.applyDiscount(order))
        .get();
}
```

Editing `isDiscountEligible.groovy` on disk and waiting for the next refresh check changes the filter's behavior without recompiling or restarting the application.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Compiled Java logic requires a rebuild and redeploy to change; a scripted step reads its logic from an external script file that can be edited and reloaded at runtime without redeploying" >
  <rect x="20" y="20" width="280" height="110" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Compiled Java logic</text>
  <text x="35" y="45" fill="#e6edf3" font-size="7" font-family="monospace">edit .java -&gt; recompile</text>
  <text x="35" y="65" fill="#e6edf3" font-size="7" font-family="monospace">-&gt; rebuild artifact</text>
  <text x="35" y="85" fill="#e6edf3" font-size="7" font-family="monospace">-&gt; redeploy application</text>
  <text x="35" y="110" fill="#8b949e" font-size="7" font-family="sans-serif">full deployment cycle per change</text>

  <rect x="340" y="20" width="280" height="110" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Scripted step</text>
  <text x="355" y="45" fill="#e6edf3" font-size="7" font-family="monospace">edit .groovy file on disk</text>
  <text x="355" y="65" fill="#79c0ff" font-size="7" font-family="monospace">-&gt; next refresh check re-reads it</text>
  <text x="355" y="90" fill="#6db33f" font-size="7" font-family="monospace">-&gt; new logic active, no redeploy</text>
</svg>

Scripted logic trades compile-time safety for the ability to change behavior without a full deployment cycle.

## 5. Runnable example

The scenario: evaluating a discount-eligibility rule that changes over time, simulated with a `Function<Order, Boolean>` standing in for a re-evaluated script (no real JSR-223 `ScriptEngine` needed to demonstrate the reload-without-redeploy concept, since the point is the runtime-swappable-logic pattern itself), starting with a fixed rule, then adding a rule that can be swapped at runtime, then adding periodic reload-checking so a changed rule takes effect without restarting the process.

### Level 1 — Basic

```java
// ScriptedRuleDemo.java
import java.util.function.*;

public class ScriptedRuleDemo {
    record Order(String id, double amount, String customerTier) {}

    // Stand-in for a fixed Groovy script's logic, evaluated once and never changing.
    static boolean isDiscountEligible(Order order) {
        return order.amount() > 100.0 && order.customerTier().equals("GOLD");
    }

    public static void main(String[] args) {
        Order order = new Order("ORD-1", 150.0, "GOLD");
        System.out.println("Eligible: " + isDiscountEligible(order));
    }
}
```

How to run: `java ScriptedRuleDemo.java`. Expected output: `Eligible: true` — a fixed rule, equivalent to what a compiled Java condition or an unchanging script would produce.

### Level 2 — Intermediate

```java
// ScriptedRuleDemo.java
import java.util.function.*;

public class ScriptedRuleDemo {
    record Order(String id, double amount, String customerTier) {}

    // Real-world concern: the rule itself needs to be swappable, the way editing a script file
    // and having the engine re-evaluate it swaps behavior without recompiling anything.
    static class EligibilityRule {
        private volatile Function<Order, Boolean> currentRule;
        EligibilityRule(Function<Order, Boolean> initialRule) { this.currentRule = initialRule; }
        void updateRule(Function<Order, Boolean> newRule) { this.currentRule = newRule; }
        boolean evaluate(Order order) { return currentRule.apply(order); }
    }

    public static void main(String[] args) {
        EligibilityRule rule = new EligibilityRule(
            order -> order.amount() > 100.0 && order.customerTier().equals("GOLD"));

        Order order = new Order("ORD-1", 80.0, "SILVER");
        System.out.println("Before rule change, eligible: " + rule.evaluate(order));

        // Simulates the script file being edited and reloaded with new business logic.
        rule.updateRule(order2 -> order2.amount() > 50.0); // tier requirement dropped

        System.out.println("After rule change, eligible: " + rule.evaluate(order));
    }
}
```

How to run: `java ScriptedRuleDemo.java`. Expected output: `Before rule change, eligible: false` (an $80 silver-tier order fails the original rule), then `After rule change, eligible: true` once the rule is swapped to the looser condition — mirroring how editing and reloading a script changes the flow's decision without any recompilation of the surrounding application.

### Level 3 — Advanced

```java
// ScriptedRuleDemo.java
import java.util.function.*;
import java.util.concurrent.atomic.*;

public class ScriptedRuleDemo {
    record Order(String id, double amount, String customerTier) {}

    // Production concern: a real scripted step polls its source file periodically (refreshCheckDelay)
    // rather than recompiling on every single message -- and a script that fails to load (syntax
    // error) must not take down the whole flow; fall back to the last-known-good rule instead.
    static class RefreshableEligibilityRule {
        private volatile Function<Order, Boolean> currentRule;
        private final AtomicInteger scriptVersion = new AtomicInteger(0);

        RefreshableEligibilityRule(Function<Order, Boolean> initialRule) { this.currentRule = initialRule; }

        void checkForRefresh(Function<Order, Boolean> candidateRule, boolean candidateIsValid) {
            if (!candidateIsValid) {
                System.out.println("Script reload failed (syntax error); keeping version " + scriptVersion.get());
                return;
            }
            currentRule = candidateRule;
            System.out.println("Script reloaded successfully, now version " + scriptVersion.incrementAndGet());
        }

        boolean evaluate(Order order) { return currentRule.apply(order); }
    }

    public static void main(String[] args) {
        RefreshableEligibilityRule rule = new RefreshableEligibilityRule(
            order -> order.amount() > 100.0 && order.customerTier().equals("GOLD"));

        Order order = new Order("ORD-1", 80.0, "SILVER");
        System.out.println("v0 eligible: " + rule.evaluate(order));

        // Simulated refresh check #1: a broken script (syntax error detected during reload).
        rule.checkForRefresh(null, false);
        System.out.println("still v0 eligible: " + rule.evaluate(order));

        // Simulated refresh check #2: a valid, updated script.
        rule.checkForRefresh(o -> o.amount() > 50.0, true);
        System.out.println("v1 eligible: " + rule.evaluate(order));
    }
}
```

How to run: `java ScriptedRuleDemo.java`. Expected output: `v0 eligible: false`; the broken-script refresh prints a failure message and evaluation is unaffected (`still v0 eligible: false`); the valid refresh prints a success message and the rule updates (`v1 eligible: true`) — the resilience pattern a production scripting integration needs so a typo in a hot-reloaded script degrades gracefully to the last-known-good behavior instead of crashing the flow.

## 6. Walkthrough

Trace a scripted filter step through a rule change, including a bad reload.

1. **Initial load**: at startup, the scripting component reads and compiles the configured script (`isDiscountEligible.groovy`), producing an executable form the JSR-223 engine can invoke against each message.
2. **Normal evaluation**: for each order flowing through the `.filter(...)` step, the script executes with the message (or its payload) bound as a variable, returning a boolean that determines whether the message continues down the flow.
3. **Periodic refresh check**: on the configured interval (`refreshCheckDelay`), the scripting component checks whether the underlying script file has changed since it was last loaded — comparing a modification timestamp, typically.
4. **Successful reload**: if the file changed and the new script compiles successfully, the component swaps in the newly compiled logic; subsequent messages are evaluated against the updated rule with no application restart.
5. **Failed reload**: if the changed file fails to compile (a syntax error introduced by whoever edited it), the component logs the failure and continues using the last successfully-loaded version of the script, rather than letting a bad edit take down message processing entirely.
6. **Ongoing operation**: this cycle — evaluate, periodically check for changes, reload or fall back — repeats indefinitely, letting whoever owns the business rule iterate on it independently of the application's own deployment cadence.

```
startup: load + compile script -> active rule v0
  each message -> evaluate against active rule
  periodic refresh check:
    file unchanged -> no-op
    file changed, compiles -> swap to new version, becomes active rule
    file changed, fails to compile -> log failure, keep previous active rule
```

## 7. Gotchas & takeaways

> **Gotcha:** a scripted condition has none of the compiler's static type-checking that an equivalent Java class would get — a typo in a field name inside the script (referencing `order.amout` instead of `order.amount`) surfaces only at runtime, and only when a message actually triggers that code path, potentially long after the script was deployed; thorough testing of scripts matters more, not less, than for compiled code.

- Scripting support trades compile-time safety for runtime flexibility — reach for it specifically where that trade genuinely pays off (frequently-changing business rules owned outside the usual deploy pipeline), not as a default way of writing flow logic.
- Always plan for a script failing to reload (a syntax error, a missing dependency) — falling back to the last-known-good version, as in Level 3, keeps a bad edit from taking down live message processing.
- JSR-223 makes the specific scripting language somewhat interchangeable (Groovy, JavaScript, others), but each engine has its own performance characteristics and level of Java interop; Groovy's tight integration with Java types is often the most ergonomic choice within a Spring Integration flow specifically.
- Treat scripts as code that deserves the same testing discipline as compiled logic — the fact that they can be changed without a deployment doesn't mean they can be changed without verification.
