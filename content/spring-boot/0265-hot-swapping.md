---
card: spring-boot
gi: 265
slug: hot-swapping
title: Hot swapping
---

## 1. What it is

**Hot swapping** is the ability to replace running code in a JVM without restarting the process. Unlike DevTools' automatic restart (which restarts the application classloader), true hot swapping patches bytecode *in-place* in the running JVM. The application keeps all its state — open connections, loaded caches, in-memory data — and the changed method body takes effect immediately.

Spring Boot supports hot swapping through several mechanisms, each with different capabilities:

1. **JVM Hot Swap (built-in, limited)** — the JVM supports swapping method bodies during debug sessions (JDWP), but only if the method signature doesn't change. Adding fields, constructors, or changing method signatures fails.
2. **Spring DevTools automatic restart** — not true hot swap, but fast (1–2 s) classloader-based restart. Available without any special JVM agent.
3. **JRebel** — a commercial JVM agent that enables full hot swap including added fields, changed hierarchies, and new classes/methods.
4. **HotSwapAgent + DCEVM (Dynamic Code Evolution VM)** — open-source alternative to JRebel; patches the JVM to allow broader hot swap.

## 2. Why & when

Hot swapping eliminates the restart cycle entirely. Its value compared to DevTools restart:

| Feature | DevTools Restart | JVM Hot Swap | JRebel / DCEVM |
|---|---|---|---|
| Speed | ~1–2s | < 100ms | < 100ms |
| Preserves state | No (new context) | Yes | Yes |
| Added methods | Yes (full restart) | No | Yes |
| Added fields | Yes (full restart) | No | Yes |
| Changed DB connections | No (reinitialised) | Yes | Yes |
| Cost | Free | Free (limited) | Paid / Open-source |

Use hot swapping when state preservation matters — e.g., you're debugging a multi-step workflow that's tedious to reproduce, or you're working with a slow-to-initialise Spring context.

## 3. Core concept

The JVM's JDWP (Java Debug Wire Protocol) includes a `RedefineClasses` command that replaces class bytecode. The JVM patches the method bodies for the affected class in-place. Restrictions (standard HotSpot JVM):

- ✅ Change method body.
- ✅ Add/change local variables.
- ❌ Add or remove methods.
- ❌ Add or remove fields.
- ❌ Change class hierarchy (super class or interfaces).

**DCEVM** patches the JVM to remove these restrictions. **JRebel** works differently — it doesn't use `RedefineClasses` at all; instead its agent instruments every class at load time to delegate to a "version registry" that swaps implementations atomically.

In an IDE:
- **IntelliJ IDEA** — in debug mode, saving a file + `Build → Recompile` triggers automatic `RedefineClasses`. IDEA shows "HotSwap successful" or "HotSwap failed" in the console.
- **VS Code** — with the Java Debug extension, the same trigger applies automatically on file save during a debug session.

## 4. Diagram

<svg viewBox="0 0 700 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Hot swap mechanisms: JVM standard (method body only) vs DCEVM/JRebel (full class changes)">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Standard JVM -->
  <rect x="10" y="30" width="310" height="190" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="165" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Standard HotSpot JVM</text>
  <text x="165" y="73" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">via JDWP RedefineClasses</text>

  <rect x="25" y="85" width="280" height="30" rx="5" fill="#1c2430" stroke="#238636" stroke-width="1.5"/>
  <text x="165" y="105" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Method body change  ✓</text>

  <rect x="25" y="125" width="280" height="30" rx="5" fill="#1c2430" stroke="#8b1a1a" stroke-width="1.5"/>
  <text x="165" y="145" fill="#ff7b72" font-size="10" text-anchor="middle" font-family="sans-serif">Add / remove method  ✗</text>

  <rect x="25" y="165" width="280" height="30" rx="5" fill="#1c2430" stroke="#8b1a1a" stroke-width="1.5"/>
  <text x="165" y="185" fill="#ff7b72" font-size="10" text-anchor="middle" font-family="sans-serif">Add field / change hierarchy  ✗</text>

  <!-- DCEVM / JRebel -->
  <rect x="380" y="30" width="310" height="190" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">DCEVM / JRebel</text>
  <text x="535" y="73" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Enhanced JVM or agent</text>

  <rect x="395" y="85" width="280" height="30" rx="5" fill="#1c2430" stroke="#238636" stroke-width="1.5"/>
  <text x="535" y="105" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Method body change  ✓</text>

  <rect x="395" y="125" width="280" height="30" rx="5" fill="#1c2430" stroke="#238636" stroke-width="1.5"/>
  <text x="535" y="145" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Add / remove method  ✓</text>

  <rect x="395" y="165" width="280" height="30" rx="5" fill="#1c2430" stroke="#238636" stroke-width="1.5"/>
  <text x="535" y="185" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Add field / change hierarchy  ✓</text>

  <text x="350" y="240" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Both preserve JVM state — no restart, no lost connections or caches</text>
</svg>

Standard JVM hot swap replaces method bodies only; DCEVM and JRebel lift all restrictions on class structure changes.

## 5. Runnable example

```java
// HotSwappingDemo.java — run with: java HotSwappingDemo.java
// Demonstrates the JVM RedefineClasses hot swap mechanism by
// simulating what happens when an IDE triggers hot swap,
// and shows the setup for DCEVM and DevTools alternatives.

import java.lang.instrument.ClassDefinition;

public class HotSwappingDemo {

    // A class whose method body we want to change without restarting
    static class DiscountCalculator {
        double calculate(double price) {
            return price * 0.10; // v1: 10% discount
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Hot Swapping Demo ===\n");

        DiscountCalculator calc = new DiscountCalculator();
        System.out.printf("Before hot swap: 10%% of 100 = %.2f%n", calc.calculate(100));

        // Simulate hot swap: in a real JVM this happens via JDWP RedefineClasses.
        // The IDE sends updated bytecode; the JVM patches the method body in-place.
        System.out.println("\n[IDE] Saved DiscountCalculator.java (changed 10% → 20%)");
        System.out.println("[JVM] HotSwap triggered via JDWP RedefineClasses");
        System.out.println("[JVM] Method body replaced for DiscountCalculator.calculate()");
        System.out.println("[JVM] HotSwap successful — no restart");

        // In the real world, after hot swap the SAME instance uses the new bytecode:
        System.out.printf("%nAfter hot swap:  20%% of 100 = %.2f%n",
            simulateAfterSwap(calc, 100));

        System.out.println();
        printSetupGuide();
    }

    // Simulates the effect of hot swap (in real JVM the method body is replaced)
    static double simulateAfterSwap(DiscountCalculator calc, double price) {
        // After RedefineClasses, calc.calculate() would now return price * 0.20
        // We simulate the result here without actual bytecode manipulation:
        return price * 0.20;
    }

    static void printSetupGuide() {
        System.out.println("--- Setup: how to enable hot swap ---\n");

        System.out.println("Option 1: Standard JVM hot swap (built-in, limited)");
        System.out.println("""
            1. Start Spring Boot app in DEBUG mode:
               mvn spring-boot:run -Dagentlib="-agentlib:jdwp=..."
               OR click 'Debug' in IntelliJ (not 'Run')
            2. Edit a method body in your IDE
            3. IntelliJ: Build → Recompile File (Ctrl+Shift+F9)
            4. Console shows: "HotSwap successful for 1 class"
            5. Limitation: method signature changes → "HotSwap failed"
            """);

        System.out.println("Option 2: DCEVM (HotSwapAgent) — full hot swap, free");
        System.out.println("""
            1. Download JDK with DCEVM support (Trava DCEVM builds for JDK 11/17)
               OR JBR (JetBrains Runtime) which includes DCEVM for JDK 21+
            2. Add JVM arg: -XX:+AllowEnhancedClassRedefinition
            3. Download HotSwapAgent: github.com/HotswapProjects/HotswapAgent
            4. Add JVM arg: -javaagent:hotswap-agent.jar
            5. Start in debug mode — now all class changes hot-swap including new methods
            """);

        System.out.println("Option 3: JRebel — full hot swap, commercial");
        System.out.println("""
            1. License at jrebel.com (free trial available)
            2. Add JVM arg: -agentpath:/path/to/libjrebel.so (Linux) or .dylib (Mac)
            3. Works with any JVM — no special JDK required
            4. Supports Spring beans, JPA entities, Hibernate mappings, CDI
            """);

        System.out.println("Option 4: DevTools restart — not hot swap, but good enough");
        System.out.println("""
            1. Add spring-boot-devtools to pom.xml (optional scope)
            2. IDE auto-compiles on save → DevTools triggers restart in ~1s
            3. State is lost, but 1s is fast enough for most workflows
            """);
    }
}
```

**How to run:** `java HotSwappingDemo.java`

## 6. Walkthrough

- **`RedefineClasses` simulation** — the demo prints what JDWP's `RedefineClasses` command does: patches the bytecode for a method body in-place. The existing `calc` object reference keeps pointing to the same heap object — its fields are unchanged, only the method code is new.
- **Standard JVM limit** — "HotSwap failed" appears in the IDE when you add a field or method. The standard HotSpot JVM's class format doesn't support these structural changes at runtime; only DCEVM and JRebel remove this constraint.
- **DCEVM / JBR** — JetBrains Runtime (JBR), the JDK bundled with IntelliJ IDEA, includes DCEVM patches. If you use IntelliJ's bundled JDK for running your app (not just for the IDE itself), you get enhanced hot swap for free.
- **`HotswapAgent`** — a Java agent that plugs into DCEVM and teaches it about framework-specific hot swap hooks. For Spring Boot: after a class is redefined, HotswapAgent notifies Spring's `BeanDefinitionRegistry` to re-register changed beans — so `@Autowired` references pick up the new version without a full restart.
- **DevTools trade-off** — DevTools restart loses JVM state (caches, sessions, connections) but is free, simple, and works with any JDK. For most developers the 1–2 s restart is fast enough; hot swap matters when state preservation is needed (e.g., debugging a multi-step form).

## 7. Gotchas & takeaways

> **Hot swap and DevTools restart are not compatible simultaneously.** If you run with DevTools and also enable JDWP hot swap, both fire on a class change. DevTools restarts the classloader, which invalidates the JVM hot swap. Choose one: DevTools for simplicity, DCEVM/JRebel for state-preserving hot swap.

> **Spring beans don't automatically re-inject after hot swap without HotswapAgent.** If you change a `@Service` class and the JVM hot-swaps the bytecode, existing `@Autowired` references still hold the old proxy. HotswapAgent adds Spring-aware hooks that re-register changed beans. Without it, you may see stale behaviour even after a successful hot swap.

- In IntelliJ IDEA: `Settings → Build → Compiler → Build project automatically` + Registry: `compiler.automake.allow.when.app.running` enables auto hot swap without manual recompile triggers.
- JDWP must be enabled: `java -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005 -jar app.jar`.
- JBR (JetBrains Runtime) for JDK 17+ includes DCEVM — download from JetBrains, use it as project SDK for the best free hot swap experience.
- Use hot swap for **method body** edits; use DevTools restart for **new classes** and **field changes**.
