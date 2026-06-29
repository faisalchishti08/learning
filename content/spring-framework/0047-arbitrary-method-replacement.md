---
card: spring-framework
gi: 47
slug: arbitrary-method-replacement
title: Arbitrary method replacement
---

## 1. What it is

**Arbitrary method replacement** lets Spring replace the implementation of any bean method at runtime using a `MethodReplacer` object. Unlike `@Lookup` which specifically fetches a bean from the context, arbitrary method replacement can intercept any method and provide a completely different body.

In XML:

```xml
<bean id="myBean" class="com.example.MyBean">
    <replaced-method name="computeValue" replacer="myReplacer"/>
</bean>

<bean id="myReplacer" class="com.example.MyReplacerImpl"/>
```

The `MethodReplacer` interface:

```java
public interface MethodReplacer {
    Object reimplement(Object obj, Method method, Object[] args) throws Throwable;
}
```

In annotation-driven code there is no direct `@Replaced` annotation — AOP (`@Around`) or method overrides are the idiomatic alternatives. Arbitrary method replacement is an XML-era feature that predates Spring AOP as it is used today.

In one sentence: **Arbitrary method replacement lets Spring swap out the body of any method in a bean with a `MethodReplacer` implementation — a low-level hook that predates AOP and is rarely needed in modern Spring, but demonstrates the extent of Spring's bean customization.**

## 2. Why & when

Arbitrary method replacement was designed for cases where:

- A method must behave differently in one deployment without subclassing.
- A third-party class method needs to be overridden without modifying the source.
- Hot-patching a method during testing.

In practice, Spring AOP (`@Around`, `@Before`, `@After`) covers all these use cases more cleanly. Arbitrary method replacement is encountered mainly when:

- Working with legacy XML-configured Spring applications.
- Understanding the historical depth of Spring's customization model.
- Teaching the full scope of Spring's bean lifecycle extension points.

Prefer Spring AOP for all new cross-cutting concerns.

## 3. Core concept

```
Normal execution:
  myBean.computeValue(42) → original implementation

With replaced-method:
  myBean.computeValue(42)
    → Spring CGLIB subclass intercepts the call
    → delegates to myReplacer.reimplement(obj, method, [42])
    → return value of reimplement() returned to caller
    → original method body never executes

MethodReplacer signature:
  Object reimplement(Object obj, Method method, Object[] args) throws Throwable;
  // obj    = the bean instance
  // method = the Method that was called
  // args   = the arguments passed to that method
```

## 4. Diagram

<svg viewBox="0 0 680 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Arbitrary method replacement: CGLIB subclass intercepts the call and delegates to MethodReplacer; original method body skipped">
  <defs>
    <marker id="a47" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b47" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#e06c75"/></marker>
    <marker id="c47" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Caller -->
  <rect x="10" y="70" width="100" height="48" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="60" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Caller</text>

  <!-- CGLIB proxy -->
  <rect x="165" y="30" width="175" height="130" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="253" y="52" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">MyBean$$CGLIB</text>
  <text x="253" y="70" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@Override computeValue(int):</text>
  <text x="253" y="86" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">return replacer.reimplement(</text>
  <text x="253" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">  this, method, args);</text>
  <line x1="165" y1="120" x2="340" y2="120" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="253" y="138" fill="#e06c75" font-size="8" text-anchor="middle" font-family="sans-serif">original body</text>
  <text x="253" y="152" fill="#e06c75" font-size="8" text-anchor="middle" font-family="sans-serif">NEVER executed</text>

  <line x1="110" y1="94" x2="162" y2="94" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a47)"/>

  <!-- MethodReplacer -->
  <rect x="400" y="55" width="195" height="68" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="498" y="77" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">MyReplacerImpl</text>
  <text x="498" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reimplement(obj, method, args)</text>
  <text x="498" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">→ custom implementation</text>

  <line x1="340" y1="85" x2="397" y2="85" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#c47)"/>

  <!-- Return value -->
  <line x1="397" y1="105" x2="112" y2="105" stroke="#6db33f" stroke-width="1.2" stroke-dasharray="3,2" marker-end="url(#a47)"/>
  <text x="250" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Original method body is bypassed. MethodReplacer.reimplement() provides the new behaviour.</text>
</svg>

CGLIB intercepts every call to `computeValue()` and delegates to `MyReplacerImpl.reimplement()`. The original method body is never reached.

## 5. Runnable example

Scenario: a `TaxCalculator` with a standard tax method. In a test/staging environment, the method is replaced with a zero-tax stub. Then demonstrate a logging replacer that wraps the original.

### Level 1 — Basic

Replace a method with a fixed stub.

```java
// ArbitraryMethodReplDemo.java — run with: java ArbitraryMethodReplDemo.java
import java.lang.reflect.*;
import java.util.*;

public class ArbitraryMethodReplDemo {

    // MethodReplacer interface (mirrors Spring's)
    interface MethodReplacer {
        Object reimplement(Object obj, Method method, Object[] args) throws Throwable;
    }

    // Bean whose method will be replaced
    static class TaxCalculator {
        // This implementation will be replaced
        double calculateTax(double grossAmount, String jurisdiction) {
            double rate = switch (jurisdiction) {
                case "US-CA" -> 0.095;
                case "US-NY" -> 0.08875;
                case "EU-DE" -> 0.19;
                default      -> 0.10;
            };
            double tax = grossAmount * rate;
            System.out.printf("  [ORIGINAL] calculateTax(%.2f, %s) = %.4f (rate=%.3f)%n",
                grossAmount, jurisdiction, tax, rate);
            return tax;
        }
    }

    // Stub replacer: always returns 0 (test/staging environment)
    static class ZeroTaxReplacer implements MethodReplacer {
        @Override
        public Object reimplement(Object obj, Method method, Object[] args) {
            System.out.printf("  [REPLACER] ZeroTaxReplacer: %s(%s) → 0.0 (stub)%n",
                method.getName(), Arrays.toString(args));
            return 0.0;
        }
    }

    // Container: register method replacement and create CGLIB-like proxy
    static class Ctx {
        private final Map<String, Object> beans       = new HashMap<>();
        private final Map<String, Map<String, MethodReplacer>> replacements = new HashMap<>();

        void register(String name, Object bean) { beans.put(name, bean); }

        void replaceMethod(String beanName, String methodName, MethodReplacer replacer) {
            replacements.computeIfAbsent(beanName, k -> new HashMap<>()).put(methodName, replacer);
            System.out.println("  [CTX] replaced method '" + methodName + "' on '" + beanName + "'");
        }

        Object invoke(String beanName, String methodName, Object... args) throws Exception {
            Object bean   = beans.get(beanName);
            var replacer  = replacements.getOrDefault(beanName, Map.of()).get(methodName);
            Method method = Arrays.stream(bean.getClass().getDeclaredMethods())
                .filter(m -> m.getName().equals(methodName)).findFirst()
                .orElseThrow(() -> new NoSuchMethodException(methodName));

            if (replacer != null) {
                return replacer.reimplement(bean, method, args);
            }
            return method.invoke(bean, args);
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Production configuration ===");
        Ctx prod = new Ctx();
        prod.register("taxCalc", new TaxCalculator());
        System.out.println("  US-CA: " + prod.invoke("taxCalc", "calculateTax", 1000.0, "US-CA"));
        System.out.println("  EU-DE: " + prod.invoke("taxCalc", "calculateTax", 500.0, "EU-DE"));

        System.out.println("\n=== Test configuration (method replaced with stub) ===");
        Ctx test = new Ctx();
        test.register("taxCalc", new TaxCalculator());
        test.replaceMethod("taxCalc", "calculateTax", new ZeroTaxReplacer());
        System.out.println("  US-CA: " + test.invoke("taxCalc", "calculateTax", 1000.0, "US-CA"));
        System.out.println("  EU-DE: " + test.invoke("taxCalc", "calculateTax", 500.0,  "EU-DE"));
    }
}
```

How to run: `java ArbitraryMethodReplDemo.java`

`ZeroTaxReplacer.reimplement()` intercepts calls to `calculateTax()` and returns `0.0` without calling the original. The `prod` context uses the original; the `test` context replaces it. The bean class itself is unchanged.

### Level 2 — Intermediate

A logging `MethodReplacer` that wraps the original method — call the original and add before/after logging.

```java
// ArbitraryMethodReplDemo2.java — run with: java ArbitraryMethodReplDemo2.java
import java.lang.reflect.*;
import java.util.*;

public class ArbitraryMethodReplDemo2 {

    interface MethodReplacer {
        Object reimplement(Object obj, Method method, Object[] args) throws Throwable;
    }

    static class PricingService {
        double getPrice(String productId, String tier) {
            double base = switch (productId) {
                case "P1" -> 99.0;
                case "P2" -> 249.0;
                default   -> 49.0;
            };
            double price = tier.equals("vip") ? base * 0.85 : base;
            return price;
        }

        double applyBulkDiscount(double unitPrice, int quantity) {
            if (quantity >= 100) return unitPrice * 0.70;
            if (quantity >= 50)  return unitPrice * 0.80;
            if (quantity >= 10)  return unitPrice * 0.90;
            return unitPrice;
        }
    }

    // Logging replacer: wraps original method, logs before + after + timing
    static class LoggingReplacer implements MethodReplacer {
        @Override
        public Object reimplement(Object obj, Method method, Object[] args) throws Throwable {
            System.out.printf("  [LOG] BEFORE %s(%s)%n", method.getName(), Arrays.toString(args));
            long start  = System.nanoTime();
            Object result = method.invoke(obj, args);
            long elapsedUs = (System.nanoTime() - start) / 1_000;
            System.out.printf("  [LOG] AFTER  %s → %s (%dµs)%n",
                method.getName(), result, elapsedUs);
            return result;
        }
    }

    static class Ctx {
        private final Map<String, Object> beans       = new HashMap<>();
        private final Map<String, Map<String, MethodReplacer>> replacers = new HashMap<>();

        void register(String name, Object b) { beans.put(name, b); }
        void replaceMethod(String bean, String method, MethodReplacer r) {
            replacers.computeIfAbsent(bean, k -> new HashMap<>()).put(method, r);
        }

        Object invoke(String bean, String method, Object... args) throws Exception {
            Object b  = beans.get(bean);
            var replacer = replacers.getOrDefault(bean, Map.of()).get(method);
            Method m  = Arrays.stream(b.getClass().getDeclaredMethods())
                .filter(x -> x.getName().equals(method) && x.getParameterCount() == args.length)
                .findFirst().orElseThrow();
            return replacer != null ? replacer.reimplement(b, m, args) : m.invoke(b, args);
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== PricingService with logging replacer on both methods ===");
        Ctx ctx = new Ctx();
        ctx.register("pricing", new PricingService());

        LoggingReplacer logger = new LoggingReplacer();
        ctx.replaceMethod("pricing", "getPrice",          logger);
        ctx.replaceMethod("pricing", "applyBulkDiscount", logger);

        System.out.println("\n=== Method calls (both logged via replacer) ===");
        double price = (double) ctx.invoke("pricing", "getPrice", "P2", "vip");
        System.out.println("  price = " + price);

        double bulkPrice = (double) ctx.invoke("pricing", "applyBulkDiscount", price, 75);
        System.out.println("  bulkPrice = " + bulkPrice);

        System.out.println("\n=== Without replacement — original called directly ===");
        PricingService direct = new PricingService();
        System.out.println("  direct price = " + direct.getPrice("P2", "vip"));
    }
}
```

How to run: `java ArbitraryMethodReplDemo2.java`

`LoggingReplacer` calls `method.invoke(obj, args)` internally — it wraps the original rather than replacing it. This is the `@Around` advice pattern implemented via `MethodReplacer`. Both `getPrice` and `applyBulkDiscount` log before/after. The direct call skips all logging.

### Level 3 — Advanced

Context-sensitive replacement: a `FeatureFlagReplacer` that routes to different implementations based on a feature flag checked at call time.

```java
// ArbitraryMethodReplDemo3.java — run with: java ArbitraryMethodReplDemo3.java
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

public class ArbitraryMethodReplDemo3 {

    interface MethodReplacer {
        Object reimplement(Object obj, Method method, Object[] args) throws Throwable;
    }

    // Feature flags (simulates a feature toggle service)
    static class FeatureFlags {
        private final Map<String, Boolean> flags = new ConcurrentHashMap<>();
        void enable(String flag)  { flags.put(flag, true);  System.out.println("  [FLAGS] enabled:  " + flag); }
        void disable(String flag) { flags.put(flag, false); System.out.println("  [FLAGS] disabled: " + flag); }
        boolean isEnabled(String flag) { return flags.getOrDefault(flag, false); }
    }

    static class RecommendationEngine {
        // V1: simple keyword match
        List<String> recommend(String userId, String category) {
            System.out.println("  [V1] recommend(" + userId + ", " + category + ")");
            return List.of(category + "-basic-1", category + "-basic-2");
        }
    }

    // V2 implementation (new algorithm — behind a feature flag)
    static List<String> recommendV2(String userId, String category) {
        System.out.println("  [V2] recommend(" + userId + ", " + category + ") — ML algorithm");
        return List.of(
            category + "-personalized-" + userId.hashCode() % 100,
            category + "-trending-1",
            category + "-trending-2"
        );
    }

    // FeatureFlag replacer: routes to V2 when flag is enabled, V1 otherwise
    static class FeatureFlagReplacer implements MethodReplacer {
        private final FeatureFlags flags;
        private final String       featureName;
        private final Method       v2Method;

        FeatureFlagReplacer(FeatureFlags flags, String featureName, Method v2Method) {
            this.flags = flags; this.featureName = featureName; this.v2Method = v2Method;
        }

        @Override
        public Object reimplement(Object obj, Method method, Object[] args) throws Throwable {
            if (flags.isEnabled(featureName)) {
                System.out.println("  [REPLACER] flag '" + featureName + "' ON → V2");
                return v2Method.invoke(null, args);   // static V2 method
            } else {
                System.out.println("  [REPLACER] flag '" + featureName + "' OFF → V1 (original)");
                return method.invoke(obj, args);
            }
        }
    }

    static class Ctx {
        private final Map<String, Object> beans     = new HashMap<>();
        private final Map<String, Map<String, MethodReplacer>> replacers = new HashMap<>();

        void register(String name, Object b) { beans.put(name, b); }
        void replaceMethod(String bean, String method, MethodReplacer r) {
            replacers.computeIfAbsent(bean, k -> new HashMap<>()).put(method, r);
        }

        @SuppressWarnings("unchecked")
        <T> T invoke(String bean, String method, Object... args) throws Exception {
            Object b = beans.get(bean);
            var r    = replacers.getOrDefault(bean, Map.of()).get(method);
            Method m = Arrays.stream(b.getClass().getDeclaredMethods())
                .filter(x -> x.getName().equals(method)).findFirst().orElseThrow();
            return (T) (r != null ? r.reimplement(b, m, args) : m.invoke(b, args));
        }
    }

    public static void main(String[] args) throws Exception {
        FeatureFlags flags = new FeatureFlags();

        System.out.println("=== Container startup ===");
        Ctx ctx = new Ctx();
        ctx.register("recommendationEngine", new RecommendationEngine());

        Method v2 = ArbitraryMethodReplDemo3.class
            .getDeclaredMethod("recommendV2", String.class, String.class);

        ctx.replaceMethod("recommendationEngine", "recommend",
            new FeatureFlagReplacer(flags, "recommendations.v2", v2));

        System.out.println("\n=== With V2 flag disabled (V1) ===");
        List<String> r1 = ctx.invoke("recommendationEngine", "recommend", "user-alice", "electronics");
        System.out.println("  " + r1);

        System.out.println("\n=== Enable V2 flag at runtime ===");
        flags.enable("recommendations.v2");
        List<String> r2 = ctx.invoke("recommendationEngine", "recommend", "user-alice", "electronics");
        System.out.println("  " + r2);

        System.out.println("\n=== Toggle back to V1 ===");
        flags.disable("recommendations.v2");
        List<String> r3 = ctx.invoke("recommendationEngine", "recommend", "user-bob", "books");
        System.out.println("  " + r3);

        System.out.println("\n=== Comparison with modern AOP (@Around) ===");
        System.out.println("  MethodReplacer: XML-era, lower-level, full method replacement");
        System.out.println("  @Around advice: annotation-driven, composable, standard approach");
        System.out.println("  Both achieve the same result; @Around is preferred in new code");
    }
}
```

How to run: `java ArbitraryMethodReplDemo3.java`

`FeatureFlagReplacer.reimplement()` checks the flag at call time — not at startup. Toggling `flags.enable("recommendations.v2")` makes subsequent calls route to `recommendV2()`. Toggling it off reverts to V1. The bean and the flag system are decoupled; no code change is needed to switch algorithms.

## 6. Walkthrough

**Level 3 — flag toggle at runtime:**

```
ctx.invoke("recommendationEngine", "recommend", "user-alice", "electronics"):
  b = RecommendationEngine instance
  replacer = FeatureFlagReplacer (registered)
  method = RecommendationEngine.recommend(String,String)
  replacer.reimplement(b, method, ["user-alice","electronics"]):
    flags.isEnabled("recommendations.v2") = false → V1 path
    → method.invoke(b, "user-alice","electronics")
    → [electronics-basic-1, electronics-basic-2]

flags.enable("recommendations.v2")

ctx.invoke(...):
  replacer.reimplement(...):
    flags.isEnabled("recommendations.v2") = true → V2 path
    → v2Method.invoke(null, "user-alice","electronics")
    → [electronics-personalized-NNN, electronics-trending-1, electronics-trending-2]
```

## 7. Gotchas & takeaways

> **Arbitrary method replacement is rarely needed in modern Spring.** Before reaching for `<replaced-method>`, check whether `@Around` AOP, `@Conditional` beans, or `@Profile` achieve the same result more cleanly and readably.

> **`MethodReplacer.reimplement()` can call `method.invoke(obj, args)` to execute the original body.** If you don't call the original, the original body is never executed — which is the point for full replacement. If you do call it, you get wrapping semantics (like `@Around`).

- `replaced-method` only works in XML configuration. There is no annotation equivalent — use AOP annotations instead.
- Spring CGLIB creates a subclass that overrides the replaced method. The class must not be `final`, and the method must not be `final` or `static`.
- `MethodReplacer` receives the actual `java.lang.reflect.Method` object and argument array, giving access to method name, parameter types, and return type for conditional routing.
- Feature flags, A/B testing, and environment-specific behavior are better served by `@Conditional`, `@Profile`, or a feature-toggle library (Unleash, LaunchDarkly) than by `MethodReplacer`.
