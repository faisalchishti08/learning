---
card: spring-framework
gi: 190
slug: publishing-events-applicationeventpublisher
title: "Publishing events (ApplicationEventPublisher)"
---

## 1. What it is

`ApplicationEventPublisher` is the single interface used to fire any event from a Spring bean. Inject it wherever you want to publish; call `publishEvent(Object)` with either an `ApplicationEvent` subclass or a plain object (Spring wraps it in `PayloadApplicationEvent`).

```java
@Service
class OrderService {
    private final ApplicationEventPublisher publisher;

    OrderService(ApplicationEventPublisher publisher) {
        this.publisher = publisher;
    }

    public void placeOrder(Order order) {
        // … business logic …
        publisher.publishEvent(new OrderPlacedEvent(this, order));
    }
}
```

`ApplicationContext` itself implements `ApplicationEventPublisher`, so you can also inject `ApplicationContext` and call its `publishEvent` — but injecting the narrower interface keeps coupling minimal and makes testing easier.

## 2. Why & when

- **Decouple side effects** — a service publishes an event; one or many listeners react (email, audit, cache invalidation) without the service knowing any of them.
- **Same-JVM, synchronous dispatch** — default multicaster calls listeners in the same thread; no external broker needed for simple flows.
- **Testing** — replace `ApplicationEventPublisher` with a mock or a test listener to verify that the correct events are published.
- **Don't use** for cross-service communication in a microservices setup — use a message broker (Kafka, RabbitMQ) there.

## 3. Core concept

`ApplicationEventPublisher` is a single-method interface:

```java
public interface ApplicationEventPublisher {
    void publishEvent(ApplicationEvent event);
    void publishEvent(Object event);   // wraps in PayloadApplicationEvent<T>
}
```

`ApplicationContext` implements it by delegating to the registered `ApplicationEventMulticaster` bean (default: `SimpleApplicationEventMulticaster`). The multicaster iterates all matching `ApplicationListener<E>` beans plus `@EventListener` methods and invokes them synchronously.

**Injection options (in order of preference):**

| How | When to use |
|---|---|
| Constructor parameter `ApplicationEventPublisher` | Services, components — recommended |
| `@Autowired ApplicationEventPublisher` field/setter | Same effect, less testable |
| `implements ApplicationEventPublisherAware` | Rare: when you must set the publisher before dependency injection completes |
| Inject `ApplicationContext` | Only if you also need other ApplicationContext features |

**Payload events:** `publishEvent(anyPojo)` wraps the pojo in `PayloadApplicationEvent<T>`. Listeners declare `@EventListener` with the POJO type directly — Spring unwraps automatically.

```java
publisher.publishEvent(new UserDto("Alice"));   // published as PayloadApplicationEvent<UserDto>

@EventListener
public void handle(UserDto dto) { ... }           // Spring unwraps PayloadApplicationEvent
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="pea" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Publisher -->
  <rect x="5" y="30" width="150" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="80" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">OrderService</text>
  <text x="80" y="68" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">publishEvent(event)</text>
  <text x="80" y="80" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">via ApplicationEventPublisher</text>

  <!-- Multicaster -->
  <rect x="200" y="15" width="180" height="120" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="290" y="35" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">ApplicationEventMulticaster</text>
  <text x="290" y="50" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">SimpleApplicationEventMulticaster</text>
  <text x="290" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">finds matching listeners</text>
  <text x="290" y="82" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">invokes synchronously (default)</text>
  <text x="290" y="94" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">or async if TaskExecutor set</text>
  <line x1="157" y1="60" x2="198" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#pea)"/>

  <!-- Listener 1 -->
  <rect x="425" y="15" width="130" height="35" rx="4" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="30" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">EmailListener</text>
  <text x="490" y="43" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">@EventListener</text>

  <!-- Listener 2 -->
  <rect x="425" y="60" width="130" height="35" rx="4" fill="#79c0ff" opacity="0.2" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="75" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">AuditListener</text>
  <text x="490" y="88" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">ApplicationListener&lt;E&gt;</text>

  <!-- Listener 3 -->
  <rect x="425" y="105" width="130" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="490" y="120" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">CacheListener</text>
  <text x="490" y="133" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">@EventListener + @Order</text>

  <!-- Arrows multicaster → listeners -->
  <line x1="382" y1="55" x2="423" y2="32"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#pea)"/>
  <line x1="382" y1="70" x2="423" y2="77"  stroke="#79c0ff" stroke-width="1.5" marker-end="url(#pea)"/>
  <line x1="382" y1="85" x2="423" y2="120" stroke="#8b949e" stroke-width="1.5" marker-end="url(#pea)"/>

  <!-- PayloadApplicationEvent note -->
  <rect x="5" y="120" width="185" height="45" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="97" y="135" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">publishEvent(anyPojo) wraps in</text>
  <text x="97" y="147" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">PayloadApplicationEvent&lt;T&gt;</text>
  <text x="97" y="159" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">listeners use POJO type directly</text>
</svg>

`publishEvent()` delegates to the multicaster, which routes synchronously to all matching listeners. Injecting `ApplicationEventPublisher` (not `ApplicationContext`) keeps coupling narrow.

## 5. Runnable example

Scenario: **product inventory system** — price change triggers email, audit, and cache invalidation.

### Level 1 — Basic

Constructor injection; publish an `ApplicationEvent` subclass.

```java
// PublishEventsBasic.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.stereotype.*;

record PriceChangedEvent(String sku, double oldPrice, double newPrice)
    extends ApplicationEvent {
    PriceChangedEvent(Object src, String sku, double o, double n) {
        super(src); this.sku=sku; this.oldPrice=o; this.newPrice=n;
    }
    // Explicit getters for record fields (ApplicationEvent stores source, not fields)
    public String getSku() { return sku; }
    public double getOldPrice() { return oldPrice; }
    public double getNewPrice() { return newPrice; }
}

@Component
class PriceAlertListener {
    @EventListener
    public void onPrice(PriceChangedEvent e) {
        double pct = (e.getNewPrice() - e.getOldPrice()) / e.getOldPrice() * 100;
        System.out.printf("[Alert] %s price changed %.0f%% → %.2f%n",
            e.getSku(), pct, e.getNewPrice());
    }
}

@Service
class PricingService {
    private final ApplicationEventPublisher pub;
    PricingService(ApplicationEventPublisher pub) { this.pub = pub; }

    public void updatePrice(String sku, double newPrice) {
        double oldPrice = 100.0; // pretend fetched from DB
        System.out.println("[Pricing] Updating " + sku + " to " + newPrice);
        pub.publishEvent(new PriceChangedEvent(this, sku, oldPrice, newPrice));
    }
}

@Configuration @ComponentScan class PubConfig { }

public class PublishEventsBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PubConfig.class);
        ctx.getBean(PricingService.class).updatePrice("SKU-XYZ", 89.99);
        ctx.close();
    }
}
```

How to run: `java PublishEventsBasic.java`

`ApplicationEventPublisher` is injected by Spring automatically — no explicit `@Bean` needed. `publishEvent` is synchronous; the listener executes before `updatePrice` returns.

### Level 2 — Intermediate

Publish plain POJO (no `ApplicationEvent` subclass); multiple listeners; `ApplicationEventPublisherAware`.

```java
// PublishEventsIntermediate.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.stereotype.*;

// Plain POJO — no need to extend ApplicationEvent
record StockLevelAlert(String warehouse, String sku, int quantity) {}

// Listener uses the POJO type directly — Spring unwraps PayloadApplicationEvent
@Component
class RestockListener {
    @EventListener
    public void onLowStock(StockLevelAlert alert) {
        System.out.println("[Restock] Low stock at " + alert.warehouse()
            + ": " + alert.sku() + " → " + alert.quantity() + " units");
    }
}

@Component
class AuditListener {
    @EventListener
    public void audit(StockLevelAlert alert) {
        System.out.println("[Audit]   Logged: " + alert);
    }
}

// ApplicationEventPublisherAware — alternative to constructor injection
@Service
class WarehouseMonitor implements ApplicationEventPublisherAware {
    private ApplicationEventPublisher pub;
    @Override
    public void setApplicationEventPublisher(ApplicationEventPublisher pub) {
        this.pub = pub;
    }
    public void checkStock(String warehouse, String sku, int qty) {
        System.out.println("[Monitor] Checking " + sku + " at " + warehouse);
        if (qty < 10) pub.publishEvent(new StockLevelAlert(warehouse, sku, qty));
    }
}

@Configuration @ComponentScan class PubIntermConfig { }

public class PublishEventsIntermediate {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PubIntermConfig.class);
        var monitor = ctx.getBean(WarehouseMonitor.class);
        monitor.checkStock("WH-01", "WIDGET-A", 3);   // below threshold → both listeners fire
        monitor.checkStock("WH-01", "WIDGET-B", 50);  // above threshold → nothing
        ctx.close();
    }
}
```

How to run: `java PublishEventsIntermediate.java`

`publishEvent(new StockLevelAlert(...))` wraps the POJO in `PayloadApplicationEvent<StockLevelAlert>`. Both `@EventListener` methods declare `StockLevelAlert` as parameter — Spring unwraps and dispatches. `ApplicationEventPublisherAware` is an alternative wiring mechanism; constructor injection is preferred.

### Level 3 — Advanced

Multiple event types; chained publishing (listener publishes a follow-up event); testing with a captured event list.

```java
// PublishEventsAdvanced.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.stereotype.*;
import java.util.*;
import java.util.concurrent.*;

// Event hierarchy
sealed interface InventoryEvent permits StockAdded, StockDepleted {}
record StockAdded(String sku, int qty) implements InventoryEvent {}
record StockDepleted(String sku) implements InventoryEvent {}

// Chain: StockAdded → may trigger StockDepleted
@Component
class InventoryChainListener {
    private final ApplicationEventPublisher pub;
    InventoryChainListener(ApplicationEventPublisher pub) { this.pub = pub; }

    @EventListener
    public void onAdded(StockAdded e) {
        System.out.println("[Chain] Stock added: " + e.sku() + " +" + e.qty());
        // Simulate: if new qty after add is still 0 (backorder), fire depletion
        if (e.qty() == 0) pub.publishEvent(new StockDepleted(e.sku()));
    }
}

@Component
class DepletionAlertListener {
    @EventListener
    public void onDepleted(StockDepleted e) {
        System.out.println("[Alert] *** STOCK DEPLETED: " + e.sku() + " — trigger reorder ***");
    }
}

// Testable: captures published events
@Component
class EventCapture {
    final List<Object> captured = new CopyOnWriteArrayList<>();
    @EventListener
    public void capture(StockAdded e) { captured.add(e); }
    @EventListener
    public void capture(StockDepleted e) { captured.add(e); }
}

@Service
class InventoryManager {
    private final ApplicationEventPublisher pub;
    InventoryManager(ApplicationEventPublisher pub) { this.pub = pub; }
    public void receive(String sku, int qty) {
        pub.publishEvent(new StockAdded(sku, qty));
    }
}

@Configuration @ComponentScan class PubAdvConfig { }

public class PublishEventsAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PubAdvConfig.class);
        var mgr  = ctx.getBean(InventoryManager.class);
        var cap  = ctx.getBean(EventCapture.class);

        mgr.receive("SKU-A", 100);  // normal receipt
        mgr.receive("SKU-B", 0);    // zero qty → chained StockDepleted event

        System.out.println("=== Captured events: ===");
        cap.captured.forEach(e -> System.out.println("  " + e));
        ctx.close();
    }
}
```

How to run: `java PublishEventsAdvanced.java`

`InventoryChainListener` receives `StockAdded`, then conditionally publishes `StockDepleted`. The multicaster dispatches the chained event synchronously before returning from the first listener. `EventCapture` shows how to test event publishing: swap `ApplicationEventPublisher` for a test-scoped bean that captures events instead of dispatching them, then assert on `captured`.

## 6. Walkthrough

Tracing `mgr.receive("SKU-B", 0)`:

**Step 1 — `publisher.publishEvent(new StockAdded("SKU-B", 0))` called.**

**Step 2 — `SimpleApplicationEventMulticaster` finds listeners for `StockAdded`:**
- `InventoryChainListener.onAdded`
- `DepletionAlertListener.onDepleted` — **no match** (wrong type)
- `EventCapture.capture(StockAdded)` — **matches**

**Step 3 — `InventoryChainListener.onAdded` called:**
- Prints `[Chain] Stock added: SKU-B +0`
- qty == 0 → calls `pub.publishEvent(new StockDepleted("SKU-B"))`
  - **Nested dispatch** of `StockDepleted` happens synchronously here.
  - `DepletionAlertListener.onDepleted` runs: `[Alert] *** STOCK DEPLETED: SKU-B ***`
  - `EventCapture.capture(StockDepleted)` runs: captured=[..., StockDepleted("SKU-B")]

**Step 4 — Control returns to multicaster; `EventCapture.capture(StockAdded)` runs:** captured=[..., StockAdded("SKU-B", 0)]

**Final captured list:** `[StockAdded("SKU-B", 0), StockDepleted("SKU-B")]` (StockDepleted was captured during the nested dispatch inside `onAdded`).

## 7. Gotchas & takeaways

> **`publishEvent` is synchronous by default.** The calling thread blocks until ALL listeners complete. For long-running listeners, add `@Async` + `@EnableAsync`, or configure a `TaskExecutor` on `SimpleApplicationEventMulticaster`.

> **`publishEvent(Object)` wraps in `PayloadApplicationEvent<T>`.** Listener parameter must be the exact POJO type (not `PayloadApplicationEvent<MyDto>`) — Spring unwraps automatically. If you use `PayloadApplicationEvent<MyDto>` in the listener, you can still access it, but you also get the source. Prefer the plain-POJO style.

- **Testing:** inject a `ApplicationEventPublisher` mock and verify `publishEvent` is called with the right arguments. Or use `@SpringBootTest` with `@RecordApplicationEvents` and `ApplicationEvents` to capture all events published during a test.
- **Self-injection loop:** if you inject `ApplicationEventPublisher` into a bean and that bean also has `@EventListener`, Spring resolves this correctly — no circular dependency.
- **`ApplicationContext.publishEvent` vs `ApplicationEventPublisher.publishEvent`:** identical. `ApplicationContext` implements `ApplicationEventPublisher`. The interface is the narrower dependency.
- **Event ordering across types:** if Listener A's `@EventListener` publishes a new event, that new event is dispatched fully (synchronously) before the original listener chain continues.
