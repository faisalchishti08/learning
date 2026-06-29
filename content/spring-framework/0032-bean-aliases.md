---
card: spring-framework
gi: 32
slug: bean-aliases
title: Bean aliases
---

## 1. What it is

A **bean alias** is an alternative name for a bean. The container stores one primary name and zero or more aliases; `getBean()` accepts any of them and returns the same singleton.

```java
// In @Configuration:
@Bean({"orderService", "orders", "order-svc"})
public OrderService orderService() { return new OrderService(); }
// Three names, one bean: "orderService" (primary), "orders", "order-svc"

// In XML:
// <alias name="orderService" alias="orders"/>
// <alias name="orderService" alias="order-svc"/>
```

Spring allows multiple aliases so that different components, modules, or legacy integrations can refer to the same bean by different names — without duplicating the bean definition.

In one sentence: **A bean alias is an additional name that resolves to the same bean definition and singleton instance, enabling multiple reference names for one bean without duplication.**

## 2. Why & when

Aliases solve the "known by many names" problem:

- **Cross-module naming.** `billing-module` calls the payment bean `"payments"`, `reporting-module` calls the same bean `"payment-gateway"`. One alias satisfies both without changing existing code.
- **Legacy migration.** Old code uses `"dataSource"`, new code uses `"primaryDataSource"`. Register one and alias the other during the transition period.
- **Readability.** A short alias `"pricing"` is more readable in tests than the full `"productPricingStrategyImpl"`.
- **Interface segregation.** Expose the same bean under multiple interface-typed names so callers inject the narrowest interface they need.

Create aliases explicitly when:
- Different teams/modules reference the same bean by different names.
- You are renaming a bean and need to support both old and new names temporarily.
- A framework requires a specific bean name that differs from your naming convention.

## 3. Core concept

The container stores aliases in a separate `SimpleAliasRegistry.aliasMap`:

```
aliasMap: {
  "orders"    → "orderService",
  "order-svc" → "orderService"
}

beanDefinitionMap: {
  "orderService" → BeanDefinition(class=OrderService)
}
singletonObjects: {
  "orderService" → <the singleton instance>
}
```

When you call `ctx.getBean("orders")`:
1. Container looks up `aliasMap["orders"]` → `"orderService"` (the canonical name).
2. Container looks up `singletonObjects["orderService"]` → the instance.

`ctx.getAliases("orderService")` returns `["orders", "order-svc"]`.

Aliases are transitive: if `"B"` aliases `"A"` and `"C"` aliases `"B"`, then `"C"` resolves to `"A"`.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Alias map resolves alias names to canonical bean name, then to singleton in singletonObjects">
  <defs>
    <marker id="a32" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Aliases -->
  <rect x="10" y="30" width="140" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="80" y="53" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">"orders"</text>

  <rect x="10" y="82" width="140" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="80" y="105" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">"order-svc"</text>

  <rect x="10" y="134" width="140" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="80" y="157" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">"orderService"</text>

  <!-- AliasMap -->
  <rect x="220" y="45" width="160" height="80" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="300" y="67" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">aliasMap</text>
  <text x="300" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"orders" → "orderService"</text>
  <text x="300" y="101" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"order-svc" → "orderService"</text>

  <line x1="150" y1="48"  x2="218" y2="75"  stroke="#8b949e" stroke-width="1.5" marker-end="url(#a32)"/>
  <line x1="150" y1="100" x2="218" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a32)"/>
  <line x1="150" y1="152" x2="218" y2="110" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4,2"/>
  <text x="175" y="143" fill="#79c0ff" font-size="8" font-family="sans-serif">canonical</text>

  <!-- Singleton -->
  <rect x="460" y="65" width="180" height="56" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="550" y="87" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="550" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">singleton instance</text>

  <line x1="380" y1="85" x2="458" y2="92" stroke="#6db33f" stroke-width="2" marker-end="url(#a32)"/>
  <text x="420" y="80" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">canonical lookup</text>

  <text x="340" y="175" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getBean("orders") → aliasMap → "orderService" → singletonObjects → same instance</text>
</svg>

Any alias lookup resolves through `aliasMap` to the canonical name, then to the singleton. All aliases return the same object.

## 5. Runnable example

Scenario: a payment service used by a billing module (calls it `"payments"`) and a reporting module (calls it `"payment-gateway"`). Both must get the same bean without duplicating the definition.

### Level 1 — Basic

Simple alias: one bean, two names.

```java
// AliasDemo.java — run with: java AliasDemo.java
import java.util.*;

public class AliasDemo {

    record Payment(String id, String customer, double amount) {}

    static class PaymentService {
        private int seq = 1000;
        Payment process(String customer, double amount) {
            Payment p = new Payment("PAY-" + seq++, customer, amount);
            System.out.println("  [PAYMENT] " + p);
            return p;
        }
        List<Payment> history() { return List.of(); }
    }

    static class AliasContainer {
        private final Map<String, Object>  beans   = new LinkedHashMap<>();
        private final Map<String, String>  aliases = new LinkedHashMap<>();

        void register(String name, Object bean) {
            beans.put(name, bean);
            System.out.println("  [CTX] Primary name: '" + name + "'");
        }

        void alias(String alias, String canonical) {
            if (!beans.containsKey(canonical))
                throw new RuntimeException("Cannot alias '" + alias + "': '" + canonical + "' not found");
            aliases.put(alias, canonical);
            System.out.println("  [CTX] Alias: '" + alias + "' → '" + canonical + "'");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) {
            String canonical = aliases.getOrDefault(name, name);
            Object bean = beans.get(canonical);
            if (bean == null)
                throw new RuntimeException("NoSuchBeanDefinitionException: '" + name + "'");
            return (T) bean;
        }

        String[] getAliases(String name) {
            return aliases.entrySet().stream()
                .filter(e -> e.getValue().equals(name))
                .map(Map.Entry::getKey).toArray(String[]::new);
        }
    }

    public static void main(String[] args) {
        AliasContainer ctx = new AliasContainer();

        System.out.println("=== Registration + aliasing ===");
        ctx.register("paymentService", new PaymentService());
        ctx.alias("payments",        "paymentService");
        ctx.alias("payment-gateway", "paymentService");

        System.out.println("\n=== Billing module uses 'payments' ===");
        PaymentService billing = ctx.getBean("payments");
        billing.process("alice", 99.99);

        System.out.println("\n=== Reporting module uses 'payment-gateway' ===");
        PaymentService reporting = ctx.getBean("payment-gateway");
        reporting.process("bob", 149.00);

        System.out.println("\n=== Same instance? " + (billing == reporting));
        System.out.println("Aliases for 'paymentService': " + Arrays.toString(ctx.getAliases("paymentService")));
    }
}
```

How to run: `java AliasDemo.java`

`billing == reporting` is `true` — both aliases resolve to the same singleton. Any payment made via the billing module's reference is visible via the reporting module's reference, because they hold the same object.

### Level 2 — Intermediate

Cross-module naming: define aliases in a central registry so each module's code uses its own preferred name without knowing the canonical name.

```java
// AliasDemo2.java — run with: java AliasDemo2.java
import java.util.*;
import java.util.function.*;

public class AliasDemo2 {

    record Payment(String id, double amount) {}
    record Report(String title, List<Payment> payments) {}

    // Shared service — canonical name "paymentGateway"
    static class PaymentGateway {
        private final List<Payment> ledger = new ArrayList<>();
        private int seq = 1;
        Payment charge(double amount) {
            Payment p = new Payment("PAY-" + seq++, amount);
            ledger.add(p);
            System.out.println("  [GATEWAY] Charged: " + p);
            return p;
        }
        List<Payment> getLedger() { return Collections.unmodifiableList(ledger); }
    }

    // Billing module — knows this service as "paymentsApi"
    static class BillingModule {
        private final PaymentGateway paymentsApi;
        BillingModule(PaymentGateway paymentsApi) { this.paymentsApi = paymentsApi; }
        void bill(double amount) { paymentsApi.charge(amount); }
    }

    // Reporting module — knows this service as "transactionLedger"
    static class ReportingModule {
        private final PaymentGateway transactionLedger;
        ReportingModule(PaymentGateway transactionLedger) { this.transactionLedger = transactionLedger; }
        Report monthlyReport() {
            return new Report("Monthly Payments", new ArrayList<>(transactionLedger.getLedger()));
        }
    }

    static class CrossModuleCtx {
        private final Map<String, Object>  beans   = new LinkedHashMap<>();
        private final Map<String, String>  aliases = new LinkedHashMap<>();

        void register(String name, Object bean) { beans.put(name, bean); }
        void alias(String alias, String target)  { aliases.put(alias, target); }
        @SuppressWarnings("unchecked")
        <T> T getBean(String name) {
            String canonical = aliases.getOrDefault(name, name);
            return (T) beans.getOrDefault(canonical, beans.get(name));
        }
    }

    public static void main(String[] args) {
        CrossModuleCtx ctx = new CrossModuleCtx();

        PaymentGateway gateway = new PaymentGateway();

        // Central registry wires up aliases for each module
        ctx.register("paymentGateway", gateway);
        ctx.alias("paymentsApi",       "paymentGateway");  // billing's name
        ctx.alias("transactionLedger", "paymentGateway");  // reporting's name

        System.out.println("=== Billing module uses 'paymentsApi' ===");
        BillingModule billing = new BillingModule(ctx.getBean("paymentsApi"));
        billing.bill(49.99);
        billing.bill(99.00);

        System.out.println("\n=== Reporting module uses 'transactionLedger' ===");
        ReportingModule reporting = new ReportingModule(ctx.getBean("transactionLedger"));
        Report r = reporting.monthlyReport();
        System.out.println("  " + r.title() + ": " + r.payments().size() + " transactions");
        r.payments().forEach(p -> System.out.printf("  %s $%.2f%n", p.id(), p.amount()));

        System.out.println("\n  Canonical 'paymentGateway' == 'paymentsApi': "
            + (gateway == ctx.getBean("paymentsApi")));
    }
}
```

How to run: `java AliasDemo2.java`

The billing module and reporting module use completely different names for the same bean. Neither module knows the canonical name `"paymentGateway"`. The central context configuration maintains the alias mapping. This is the standard pattern for multi-module Spring applications.

### Level 3 — Advanced

Alias chains and override: aliasing an alias, and replacing an alias binding at migration time.

```java
// AliasDemo3.java — run with: java AliasDemo3.java
import java.util.*;
import java.util.function.*;

public class AliasDemo3 {

    record Payment(String id, double amount, String processor) {}

    interface PaymentProcessor {
        Payment process(double amount);
        String name();
    }

    static class StripeProcessor implements PaymentProcessor {
        private int seq = 1;
        public Payment process(double a) { return new Payment("stripe-" + seq++, a, "stripe"); }
        public String name() { return "Stripe"; }
    }

    static class BraintreeProcessor implements PaymentProcessor {
        private int seq = 1;
        public Payment process(double a) { return new Payment("bt-" + seq++, a, "braintree"); }
        public String name() { return "Braintree"; }
    }

    static class CheckoutService {
        private final PaymentProcessor processor;
        CheckoutService(PaymentProcessor p) { this.processor = p; }
        void checkout(double total) {
            Payment p = processor.process(total);
            System.out.printf("  [CHECKOUT] $%.2f via %s → %s%n", total, processor.name(), p.id());
        }
    }

    static class AliasChainCtx {
        private final Map<String, Object>  beans    = new LinkedHashMap<>();
        private final Map<String, String>  aliasMap = new LinkedHashMap<>();

        void register(String name, Object b) { beans.put(name, b); }

        void alias(String alias, String target) {
            aliasMap.put(alias, target);
            System.out.println("  [ALIAS] '" + alias + "' → '" + target + "'");
        }

        void reAlias(String alias, String newTarget) {
            String old = aliasMap.get(alias);
            aliasMap.put(alias, newTarget);
            System.out.println("  [RE-ALIAS] '" + alias + "': '" + old + "' → '" + newTarget + "'");
        }

        // Resolve alias chain
        @SuppressWarnings("unchecked")
        <T> T getBean(String name) {
            Set<String> visited = new HashSet<>();
            String current = name;
            while (aliasMap.containsKey(current)) {
                if (!visited.add(current)) throw new RuntimeException("Circular alias: " + current);
                current = aliasMap.get(current);
            }
            Object b = beans.get(current);
            if (b == null) throw new RuntimeException("No bean: '" + name + "' (resolved: '" + current + "')");
            return (T) b;
        }
    }

    public static void main(String[] args) {
        AliasChainCtx ctx = new AliasChainCtx();

        ctx.register("stripeProcessor",     new StripeProcessor());
        ctx.register("braintreeProcessor",  new BraintreeProcessor());

        System.out.println("=== Phase 1: payment processor is Stripe ===");
        ctx.alias("activeProcessor",  "stripeProcessor");   // "activeProcessor" → "stripe..."
        ctx.alias("primaryPayment",   "activeProcessor");   // chain: "primaryPayment" → "activeProcessor" → "stripe..."

        CheckoutService svc = new CheckoutService(ctx.getBean("primaryPayment"));
        System.out.println("  Processor: " + ctx.getBean("primaryPayment").name());
        svc.checkout(49.99);
        svc.checkout(99.00);

        System.out.println("\n=== Migration: switch activeProcessor to Braintree ===");
        ctx.reAlias("activeProcessor", "braintreeProcessor");

        // New checkout uses Braintree via the same "primaryPayment" alias chain
        CheckoutService svc2 = new CheckoutService(ctx.getBean("primaryPayment"));
        System.out.println("  Processor: " + ctx.getBean("primaryPayment").name());
        svc2.checkout(149.00);

        System.out.println("\n=== Alias resolution chain ===");
        System.out.println("  'primaryPayment' → 'activeProcessor' → 'braintreeProcessor' → BraintreeProcessor");
    }
}
```

How to run: `java AliasDemo3.java`

`"primaryPayment"` chains through `"activeProcessor"` to the concrete processor. Switching `"activeProcessor"` from Stripe to Braintree instantly changes what `"primaryPayment"` resolves to — without touching `CheckoutService` or any other caller. This is a migration pattern: gradually flip the alias, verify, then clean up.

## 6. Walkthrough

**Level 3 — alias chain resolution:**

```
getBean("primaryPayment")
  → aliasMap["primaryPayment"] = "activeProcessor"  (phase 2: braintree)
  → aliasMap["activeProcessor"] = "braintreeProcessor"
  → "braintreeProcessor" not in aliasMap → canonical
  → beans["braintreeProcessor"] = BraintreeProcessor
  → return BraintreeProcessor singleton
```

**`svc2.checkout(149.00)` execution:**
```
checkout(149.00)
  → processor.process(149.00)
      → BraintreeProcessor.process(149.00)
          → Payment("bt-1", 149.00, "braintree")
  → "[CHECKOUT] $149.00 via Braintree → bt-1"
```

**Alias state across migration phases:**

| Phase | `aliasMap["activeProcessor"]` | `getBean("primaryPayment")` returns |
|---|---|---|
| Phase 1 | `"stripeProcessor"` | `StripeProcessor` |
| After reAlias | `"braintreeProcessor"` | `BraintreeProcessor` |

## 7. Gotchas & takeaways

> **Aliases are not bean names.** `ctx.containsBean("orders")` returns `true` if `"orders"` is an alias for a known bean. But `ctx.getBeanDefinitionNames()` returns only **primary** names — not aliases. Use `ctx.getAliases("orderService")` to see the aliases for a primary name.

> **Circular aliases throw immediately.** If `"A"` aliases `"B"` and `"B"` aliases `"A"`, Spring throws `AliasException` during context startup — not at runtime.

- In `@Bean({"name1", "name2", "name3"})`, the first value is the primary name; subsequent values become aliases.
- In XML, `<alias name="canonical" alias="altName"/>` adds an alias at any point in the config — can appear before or after the `<bean>` definition.
- Spring Boot auto-configuration uses aliases extensively to provide short names (`"dataSource"`) for beans whose canonical names are longer implementation names.
- `ctx.isAlias("orders")` returns `true` if `"orders"` is an alias (not a primary name).
- Avoid long alias chains — they make dependency tracing harder. Keep chains to at most one level deep.
