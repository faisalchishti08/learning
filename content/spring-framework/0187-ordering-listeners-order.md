---
card: spring-framework
gi: 187
slug: ordering-listeners-order
title: "Ordering listeners (@Order)"
---

## 1. What it is

When multiple listeners handle the same event type, Spring dispatches them in the order determined by `@Order`. Lower values run first; `Ordered.HIGHEST_PRECEDENCE` = `Integer.MIN_VALUE`; `Ordered.LOWEST_PRECEDENCE` = `Integer.MAX_VALUE`. Unordered listeners (no `@Order`) run last at `LOWEST_PRECEDENCE`.

```java
@EventListener
@Order(1)
public void validate(OrderPlacedEvent e) { /* runs first */ }

@EventListener
@Order(2)
public void notify(OrderPlacedEvent e) { /* runs second */ }

@EventListener
@Order(Ordered.LOWEST_PRECEDENCE)
public void archive(OrderPlacedEvent e) { /* runs last */ }
```

For `ApplicationListener<E>` beans, implement `SmartApplicationListener` to control ordering with more precision.

## 2. Why & when

- **Dependency between listeners** — listener B requires the side-effects of listener A (e.g., A writes a DB record, B sends an email referencing it). `@Order` ensures A runs first.
- **Fail-fast validation before side effects** — put validation listeners at `@Order(1)` so they can throw and abort the sequence before expensive external calls at `@Order(2)`.
- **Graceful degradation** — put critical listeners at lowest order values and optional/logging listeners at high values; an exception in a critical listener aborts lower-priority ones, not vice versa.
- **Beware** that order is meaningless for async listeners — `@Async` + `@Order` is contradictory. Order only applies to synchronous dispatch.

## 3. Core concept

Spring's `SimpleApplicationEventMulticaster` collects all applicable `ApplicationListener<E>` instances and sorts them by their `getOrder()` value before dispatching. `@EventListener` methods are wrapped in `ApplicationListenerMethodAdapter`, which picks up `@Order` from the method.

**Three ordering mechanisms:**

| Mechanism | How | When to use |
|---|---|---|
| `@Order(n)` on `@EventListener` method | declares priority | most common case |
| `@Order(n)` on `ApplicationListener<E>` bean class | declares priority | when using the interface |
| Implement `SmartApplicationListener` | override `getOrder()` + type-filter logic | when ordering must be combined with conditional type matching |

**`SmartApplicationListener`** also lets you declare `supportsEventType` and `supportsSourceType` for fine-grained matching — useful in frameworks.

**`@Order` on the bean vs on the method:** for `@EventListener` methods, `@Order` must be on the *method*, not the class. For `ApplicationListener<E>` beans, `@Order` on the *class* (or `implements Ordered`) controls order.

## 4. Diagram

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="oda" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Publisher -->
  <rect x="5" y="70" width="120" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="65" y="88" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Publisher</text>
  <text x="65" y="102" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">publishEvent()</text>
  <line x1="127" y1="90" x2="147" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#oda)"/>

  <!-- Multicaster sorts and dispatches in order -->
  <rect x="150" y="5" width="530" height="170" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="415" y="22" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">SimpleApplicationEventMulticaster (sorted by getOrder())</text>

  <!-- Listener boxes in order -->
  <rect x="165" y="32" width="500" height="25" rx="3" fill="#6db33f" opacity="0.3"/>
  <text x="220" y="49" fill="#6db33f" font-size="8" font-family="sans-serif">@Order(-100)  ValidateListener</text>
  <text x="500" y="49" fill="#8b949e" font-size="8" font-family="sans-serif">Highest priority — runs 1st</text>

  <rect x="165" y="62" width="500" height="25" rx="3" fill="#6db33f" opacity="0.2"/>
  <text x="220" y="79" fill="#e6edf3" font-size="8" font-family="sans-serif">@Order(1)      AuditListener</text>
  <text x="500" y="79" fill="#8b949e" font-size="8" font-family="sans-serif">Runs 2nd</text>

  <rect x="165" y="92" width="500" height="25" rx="3" fill="#6db33f" opacity="0.15"/>
  <text x="220" y="109" fill="#e6edf3" font-size="8" font-family="sans-serif">@Order(10)     NotifyListener</text>
  <text x="500" y="109" fill="#8b949e" font-size="8" font-family="sans-serif">Runs 3rd</text>

  <rect x="165" y="122" width="500" height="25" rx="3" fill="#8b949e" opacity="0.1"/>
  <text x="220" y="139" fill="#8b949e" font-size="8" font-family="sans-serif">(no @Order)    ArchiveListener</text>
  <text x="500" y="139" fill="#8b949e" font-size="8" font-family="sans-serif">LOWEST_PRECEDENCE — runs last</text>

  <text x="415" y="158" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">exception in any listener stops subsequent ones (synchronous dispatch)</text>
</svg>

Listeners are sorted by order value before dispatch; lower value = higher priority = runs earlier. No `@Order` means `LOWEST_PRECEDENCE`.

## 5. Runnable example

The scenario is an **order validation and processing pipeline** where ordering guarantees that validation always runs before notification, and archival runs last.

### Level 1 — Basic

`@Order` on `@EventListener` methods; observe execution sequence.

```java
// OrderingListenersBasic.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.core.annotation.*;
import org.springframework.stereotype.*;

class OrderSubmittedEvent extends ApplicationEvent {
    private final String orderId;
    OrderSubmittedEvent(Object src, String id) { super(src); orderId=id; }
    public String getOrderId() { return orderId; }
}

@Component
class OrderPipeline {

    @Order(1)
    @EventListener
    public void validate(OrderSubmittedEvent e) {
        System.out.println("[1-Validate]  " + e.getOrderId());
        // throw new IllegalArgumentException("invalid") to abort pipeline
    }

    @Order(2)
    @EventListener
    public void charge(OrderSubmittedEvent e) {
        System.out.println("[2-Charge]    " + e.getOrderId());
    }

    @Order(3)
    @EventListener
    public void fulfil(OrderSubmittedEvent e) {
        System.out.println("[3-Fulfil]    " + e.getOrderId());
    }

    @Order(Ordered.LOWEST_PRECEDENCE)
    @EventListener
    public void archive(OrderSubmittedEvent e) {
        System.out.println("[LAST-Archive]" + e.getOrderId());
    }
}

@Service
class OrderSubmitService {
    private final ApplicationEventPublisher pub;
    OrderSubmitService(ApplicationEventPublisher pub) { this.pub = pub; }
    public void submit(String id) { pub.publishEvent(new OrderSubmittedEvent(this, id)); }
}

@Configuration @ComponentScan class OrdConfig { }

public class OrderingListenersBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(OrdConfig.class);
        ctx.getBean(OrderSubmitService.class).submit("ORD-001");
        ctx.close();
    }
}
```

How to run: `java OrderingListenersBasic.java`

Output is always in declaration order: `[1-Validate]` → `[2-Charge]` → `[3-Fulfil]` → `[LAST-Archive]`. Uncomment the `throw` in `validate` and the run terminates after step 1 — subsequent listeners never execute. This is a simple sequential pipeline enforced purely by `@Order`.

### Level 2 — Intermediate

Separate listener classes with `@Order`; fail-fast validation aborts the pipeline; show listener order is stable regardless of bean registration order.

```java
// OrderingListenersIntermediate.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.core.annotation.*;
import org.springframework.stereotype.*;

class PaymentRequestedEvent extends ApplicationEvent {
    private final String paymentId; private final double amount;
    PaymentRequestedEvent(Object src, String id, double a) { super(src); paymentId=id; amount=a; }
    public String getPaymentId() { return paymentId; }
    public double getAmount()    { return amount; }
}

// Registered in alphabetical bean order — but dispatch follows @Order
@Order(3) @Component
class ZettaChargeListener {
    @EventListener
    public void onPayment(PaymentRequestedEvent e) {
        System.out.println("[Order 3 - Charge] " + e.getPaymentId());
    }
}

@Order(1) @Component
class AalphaValidateListener {
    @EventListener
    public void onPayment(PaymentRequestedEvent e) {
        System.out.println("[Order 1 - Validate] " + e.getPaymentId()
            + " amount=" + e.getAmount());
        if (e.getAmount() <= 0)
            throw new IllegalArgumentException("Invalid amount: " + e.getAmount());
    }
}

@Order(2) @Component
class MediumFraudListener {
    @EventListener
    public void onPayment(PaymentRequestedEvent e) {
        System.out.println("[Order 2 - Fraud check] " + e.getPaymentId());
    }
}

@Service
class PaymentService {
    private final ApplicationEventPublisher pub;
    PaymentService(ApplicationEventPublisher pub) { this.pub = pub; }
    public void request(String id, double amount) {
        System.out.println("--- Requesting payment " + id + " $" + amount);
        try {
            pub.publishEvent(new PaymentRequestedEvent(this, id, amount));
        } catch (IllegalArgumentException ex) {
            System.out.println("Aborted: " + ex.getMessage());
        }
    }
}

@Configuration @ComponentScan class IntermOrdConfig { }

public class OrderingListenersIntermediate {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(IntermOrdConfig.class);
        var svc = ctx.getBean(PaymentService.class);
        svc.request("PAY-001", 150.0);   // all 3 listeners run
        svc.request("PAY-002", -5.0);    // validate throws → charge never runs
        ctx.close();
    }
}
```

How to run: `java OrderingListenersIntermediate.java`

`ZettaChargeListener` has `@Order(3)` and is registered first alphabetically, but Spring dispatches it LAST among the three. `@Order` on the class works for `ApplicationListener<E>` beans; for `@EventListener` methods it must be on the method. The exception from `AalphaValidateListener` propagates up through `publishEvent` — `MediumFraudListener` and `ZettaChargeListener` are skipped for the invalid payment.

### Level 3 — Advanced

`SmartApplicationListener` for combined ordering + type filtering; contrasting with `@Order` approach.

```java
// OrderingListenersAdvanced.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.core.annotation.*;
import org.springframework.stereotype.*;
import java.util.*;

class TradeEvent extends ApplicationEvent {
    private final String symbol; private final double price; private final String type;
    TradeEvent(Object src, String sym, double p, String t) { super(src); symbol=sym; price=p; type=t; }
    public String getSymbol() { return symbol; }
    public double getPrice()  { return price; }
    public String getType()   { return type; }
}

// SmartApplicationListener: controls order + type matching in one place
@Component
class RiskCheckListener implements SmartApplicationListener {

    @Override
    public boolean supportsEventType(Class<? extends ApplicationEvent> eventType) {
        return TradeEvent.class.isAssignableFrom(eventType);
    }

    @Override
    public boolean supportsSourceType(Class<?> sourceType) {
        return true;  // accept from any source
    }

    @Override
    public int getOrder() { return 1; }  // runs first

    @Override
    public void onApplicationEvent(ApplicationEvent event) {
        TradeEvent te = (TradeEvent) event;
        System.out.println("[Risk #1] Checking " + te.getSymbol() + " @" + te.getPrice());
        if (te.getPrice() > 10_000)
            throw new IllegalStateException("Trade price exceeds limit: " + te.getPrice());
    }
}

@Component
class ExecuteTradeListener implements SmartApplicationListener {

    @Override
    public boolean supportsEventType(Class<? extends ApplicationEvent> eventType) {
        return TradeEvent.class.isAssignableFrom(eventType);
    }

    @Override
    public boolean supportsSourceType(Class<?> sourceType) { return true; }

    @Override
    public int getOrder() { return 2; }  // runs after RiskCheck

    @Override
    public void onApplicationEvent(ApplicationEvent event) {
        TradeEvent te = (TradeEvent) event;
        System.out.println("[Execute #2] Executing " + te.getType()
            + " " + te.getSymbol() + " @" + te.getPrice());
    }
}

// Regular @EventListener + @Order for non-critical listeners
@Component
class TradeAuditListener {
    @Order(Ordered.LOWEST_PRECEDENCE)
    @EventListener
    public void audit(TradeEvent e) {
        System.out.println("[Audit LAST] Logged: " + e.getSymbol() + " " + e.getType());
    }
}

@Service
class TradingService {
    private final ApplicationEventPublisher pub;
    TradingService(ApplicationEventPublisher pub) { this.pub = pub; }
    public void trade(String sym, double price, String type) {
        try {
            pub.publishEvent(new TradeEvent(this, sym, price, type));
        } catch (IllegalStateException ex) {
            System.out.println("Trade rejected: " + ex.getMessage());
        }
    }
}

@Configuration @ComponentScan class AdvOrdConfig { }

public class OrderingListenersAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AdvOrdConfig.class);
        var svc = ctx.getBean(TradingService.class);
        svc.trade("AAPL", 175.0, "BUY");
        System.out.println("---");
        svc.trade("TSLA", 15000.0, "SELL");  // rejected by risk check
        ctx.close();
    }
}
```

How to run: `java OrderingListenersAdvanced.java`

`SmartApplicationListener` combines `getOrder()` with `supportsEventType` — useful when the type filtering logic is non-trivial. `RiskCheckListener` at order 1 runs before `ExecuteTradeListener` at order 2. The regular `@EventListener` + `@Order(LOWEST_PRECEDENCE)` in `TradeAuditListener` runs last. For the second trade, risk check throws at order 1 — execute and audit listeners never run.

## 6. Walkthrough

Tracing `svc.trade("AAPL", 175.0, "BUY")`:

**Step 1 — `pub.publishEvent(new TradeEvent(...))` called.**

**Step 2 — Multicaster sorts listeners for `TradeEvent`:**

| Listener | Source | Order value |
|---|---|---|
| `RiskCheckListener` | `SmartApplicationListener.getOrder()` | 1 |
| `ExecuteTradeListener` | `SmartApplicationListener.getOrder()` | 2 |
| `TradeAuditListener.audit` | `@Order(LOWEST_PRECEDENCE)` | 2147483647 |

**Step 3 — Dispatch in order:**

1. `RiskCheckListener.onApplicationEvent(event)`:
   - `175.0 > 10_000` → `false`.
   - Prints `[Risk #1] Checking AAPL @175.0`. No exception.
2. `ExecuteTradeListener.onApplicationEvent(event)`:
   - Prints `[Execute #2] Executing BUY AAPL @175.0`.
3. `TradeAuditListener.audit(event)`:
   - Prints `[Audit LAST] Logged: AAPL BUY`.

**Step 4 — `publishEvent` returns**; `trade` method completes.

**For `svc.trade("TSLA", 15000.0, "SELL")`:**

At step 3.1: `15000.0 > 10_000` → `true`. `IllegalStateException` thrown. Steps 3.2 and 3.3 never execute. Exception propagates to `trade()`, caught, prints `Trade rejected: Trade price exceeds limit: 15000.0`.

## 7. Gotchas & takeaways

> **`@Order` on the class has no effect for `@EventListener` methods.** Class-level `@Order` controls the bean's order as a candidate for dependency injection, not event dispatch. For `@EventListener` methods, `@Order` must be on the **method** itself. Only for `ApplicationListener<E>` beans does class-level `@Order` affect event dispatch.

> **Ordering is only meaningful for synchronous listeners.** Once a listener is annotated with `@Async`, it runs on a thread pool thread. The submission to the pool happens in order, but pool threads are scheduled by the OS — actual execution order is non-deterministic. Never combine `@Order` with `@Async` expecting sequence guarantees.

- `Ordered.HIGHEST_PRECEDENCE` = `Integer.MIN_VALUE`; lowest number = first to run.
- `Ordered.LOWEST_PRECEDENCE` = `Integer.MAX_VALUE`; highest number = last to run.
- Use negative order values (`@Order(-100)`) for pre-processing listeners (validation, security checks) that must run before positive-order business listeners.
- `SmartApplicationListener` is for framework/library code; application code is better served by `@EventListener` + `@Order`.
- The sort is stable: two listeners with the same order value run in an unspecified but consistent order within a session.
