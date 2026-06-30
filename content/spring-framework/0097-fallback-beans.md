---
card: spring-framework
gi: 97
slug: fallback-beans
title: "@Fallback beans"
---

## 1. What it is

`@Fallback` (introduced in Spring 6.2) is the **inverse of `@Primary`**: a bean marked `@Fallback` is only used when no other non-fallback candidate of the same type is available. It is the "last resort" default — present to prevent `NoSuchBeanDefinitionException` when no real implementation has been registered.

Where `@Primary` says "prefer me," `@Fallback` says "use me only if nothing better exists."

## 2. Why & when

`@Fallback` solves the **default-implementation problem** cleanly:

- You want a no-op or stub implementation to be active unless a real one is configured.
- A library/framework provides a default bean that should yield to any user-defined bean of the same type.
- You want tests to use a real bean when available but silently fall back to a stub when the dep isn't wired.

Before Spring 6.2, the same pattern required `@ConditionalOnMissingBean` (Spring Boot) or careful `@Primary`-on-user-bean plus `@Order` tricks. `@Fallback` is the clean semantic alternative.

> **Note**: `@Fallback` requires Spring Framework 6.2+ (Spring Boot 3.4+). In older projects use `@ConditionalOnMissingBean` or `@Primary` workarounds instead.

## 3. Core concept

Resolution algorithm when multiple candidates exist:

1. Spring collects all beans assignable to the required type.
2. Remove `@Fallback` beans from the candidate list.
3. If exactly one non-fallback candidate remains, inject it.
4. If zero non-fallback candidates remain, re-admit the `@Fallback` beans and resolve from them (using normal `@Primary` / name rules).
5. If multiple non-fallback candidates remain and none is `@Primary`, throw `NoUniqueBeanDefinitionException`.

Contrast with `@Primary`: `@Primary` biases the selection toward one bean; `@Fallback` biases it away from one bean.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <!-- Scenario A: real impl present -->
  <rect x="10" y="30" width="160" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="90" y="53" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">RealPayment</text>
  <text x="90" y="68" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">implements Gateway</text>

  <rect x="10" y="110" width="160" height="54" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="90" y="133" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">@Fallback NoOpGateway</text>
  <text x="90" y="148" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">implements Gateway</text>

  <!-- Autowired -->
  <rect x="285" y="80" width="140" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="355" y="102" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@Autowired</text>
  <text x="355" y="116" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Gateway gw</text>

  <!-- Result A -->
  <rect x="520" y="40" width="165" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="602" y="63" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">→ RealPayment</text>
  <text x="602" y="77" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(non-fallback wins)</text>

  <!-- Result B -->
  <rect x="520" y="130" width="165" height="44" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="602" y="150" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">→ NoOpGateway</text>
  <text x="602" y="165" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(only when no real impl)</text>

  <line x1="172" y1="57" x2="282" y2="97" stroke="#6db33f" stroke-width="2" marker-end="url(#a97)"/>
  <line x1="172" y1="137" x2="282" y2="112" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#c97)"/>
  <line x1="427" y1="97" x2="517" y2="62" stroke="#6db33f" stroke-width="2" marker-end="url(#a97)"/>
  <line x1="355" y1="126" x2="355" y2="155" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="355" y1="155" x2="517" y2="152" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#c97)"/>
  <text x="430" y="50" fill="#6db33f" font-size="10" font-family="sans-serif">real present</text>
  <text x="360" y="170" fill="#8b949e" font-size="10" font-family="sans-serif">no real bean</text>
  <defs>
    <marker id="a97" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="c97" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <text x="350" y="210" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">@Fallback yields to any non-fallback candidate; becomes active only when nothing else matches</text>
</svg>

`@Fallback` sits on the sideline and only steps in when no real implementation exists.

## 5. Runnable example

### Level 1 — Basic

A no-op `@Fallback` notification service that's silently replaced when a real implementation is registered.

```java
// FallbackBasic.java  (requires Spring 6.2+)
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.context.annotation.Fallback;
import org.springframework.stereotype.*;

interface NotificationService {
    void notify(String message);
}

@Component
@Fallback   // only used when no other NotificationService bean exists
class NoOpNotification implements NotificationService {
    public void notify(String message) {
        System.out.println("[NOOP] Notification suppressed: " + message);
    }
}

@Service
class AlertEngine {
    private final NotificationService notifier;

    @Autowired
    public AlertEngine(NotificationService notifier) { this.notifier = notifier; }

    public void alert(String msg) {
        System.out.println("Firing alert: " + msg);
        notifier.notify(msg);
    }
}

@Configuration
@ComponentScan
class FbCfg {}

public class FallbackBasic {
    public static void main(String[] args) {
        // No real NotificationService — @Fallback NoOpNotification is used
        var ctx = new AnnotationConfigApplicationContext(FbCfg.class);
        ctx.getBean(AlertEngine.class).alert("Disk 95% full");
        ctx.close();
    }
}
```

How to run: `java FallbackBasic.java`

Only the `@Fallback` bean exists, so it becomes the candidate. The `[NOOP]` output confirms it was selected. If a real `NotificationService` were registered, `NoOpNotification` would step aside automatically.

### Level 2 — Intermediate

Demonstrate the switch: context A has no real implementation (fallback active); context B adds a real implementation (fallback yields).

```java
// FallbackSwitch.java  (requires Spring 6.2+)
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.context.annotation.Fallback;
import org.springframework.stereotype.*;

interface CacheService {
    void put(String key, String val);
    String get(String key);
}

@Component
@Fallback   // in-memory no-op cache — active only if no other CacheService exists
class NoOpCache implements CacheService {
    public void put(String k, String v) { System.out.println("[NOOP-CACHE] put " + k + "=" + v); }
    public String get(String k)         { System.out.println("[NOOP-CACHE] get " + k + " → null"); return null; }
}

@Component
@Profile("redis")  // real cache only when 'redis' profile is active
class RedisCache implements CacheService {
    private final java.util.Map<String,String> store = new java.util.HashMap<>();
    public void put(String k, String v) { store.put(k, v); System.out.println("[REDIS] put " + k + "=" + v); }
    public String get(String k)         { var v = store.get(k); System.out.println("[REDIS] get " + k + "=" + v); return v; }
}

@Service
class ProductService {
    @Autowired CacheService cache;
    public void demo() {
        cache.put("p1", "Widget");
        cache.get("p1");
    }
}

@Configuration
@ComponentScan
class SwitchCfg {}

public class FallbackSwitch {
    public static void main(String[] args) {
        System.out.println("=== No redis profile — @Fallback NoOpCache active ===");
        var ctx1 = new AnnotationConfigApplicationContext(SwitchCfg.class);
        ctx1.getBean(ProductService.class).demo();
        ctx1.close();

        System.out.println("\n=== redis profile — RedisCache active, @Fallback yields ===");
        var ctx2 = new AnnotationConfigApplicationContext();
        ctx2.getEnvironment().setActiveProfiles("redis");
        ctx2.register(SwitchCfg.class);
        ctx2.refresh();
        ctx2.getBean(ProductService.class).demo();
        ctx2.close();
    }
}
```

How to run: `java FallbackSwitch.java`

No profile: only `NoOpCache` qualifies — it's `@Fallback` but there are no competitors, so it wins. Redis profile: `RedisCache` is also active — as a non-fallback candidate it displaces `NoOpCache` automatically.

### Level 3 — Advanced

A framework-style scenario: a library provides `@Fallback` default implementations for serialization and metrics; user code can override either independently.

```java
// FallbackFramework.java  (requires Spring 6.2+)
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.context.annotation.Fallback;
import org.springframework.stereotype.*;

// ---- Library-provided fallbacks ----
interface Serializer   { String serialize(Object o); }
interface MetricsTracker { void track(String event); }

@Component @Fallback
class DefaultSerializer implements Serializer {
    public String serialize(Object o) { return o.toString(); }
}

@Component @Fallback
class NoOpMetrics implements MetricsTracker {
    public void track(String e) { /* intentionally silent */ }
}

// ---- User-provided override for Serializer (not Metrics) ----
@Component
class JsonSerializer implements Serializer {
    public String serialize(Object o) { return "{\"v\":\"" + o + "\"}"; }
}

// ---- App code ----
@Service
class EventBus {
    @Autowired private Serializer   serializer;  // gets JsonSerializer (user-defined)
    @Autowired private MetricsTracker metrics;   // gets NoOpMetrics (@Fallback — no override)

    public void publish(String topic, Object payload) {
        String json = serializer.serialize(payload);
        metrics.track("publish:" + topic);
        System.out.printf("[EventBus] topic=%s payload=%s ser=%s%n",
            topic, json, serializer.getClass().getSimpleName());
    }
}

@Configuration
@ComponentScan
class FrameworkCfg {}

public class FallbackFramework {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(FrameworkCfg.class);
        ctx.getBean(EventBus.class).publish("orders", "OrderId=42");
        System.out.println("Metrics: " + ctx.getBean(MetricsTracker.class).getClass().getSimpleName());
        ctx.close();
    }
}
```

How to run: `java FallbackFramework.java`

`JsonSerializer` (non-fallback) displaces `DefaultSerializer` (@Fallback) for the `Serializer` injection. `NoOpMetrics` remains active because no non-fallback `MetricsTracker` was registered. The library's defaults activate exactly where no custom bean has been provided.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Component scan** — finds `DefaultSerializer` (`@Fallback`), `NoOpMetrics` (`@Fallback`), `JsonSerializer` (plain), and `EventBus`.
2. **`EventBus` wiring — `Serializer` field**:
   - Candidates: `DefaultSerializer` (fallback=true), `JsonSerializer` (fallback=false).
   - Non-fallback candidate set = `{JsonSerializer}` — exactly one. Injected.
3. **`EventBus` wiring — `MetricsTracker` field**:
   - Candidates: `NoOpMetrics` (fallback=true).
   - Non-fallback candidate set = `{}` — empty. Re-admit fallback beans: `{NoOpMetrics}`. Exactly one. Injected.
4. **`publish()` called** — `serializer.serialize("OrderId=42")` returns `{"v":"OrderId=42"}` (JSON). `metrics.track(…)` is a no-op. Output printed.
5. **Final `getBean(MetricsTracker.class)`** — returns `NoOpMetrics`, confirming the fallback is still active.

Expected output:
```
[EventBus] topic=orders payload={"v":"OrderId=42"} ser=JsonSerializer
Metrics: NoOpMetrics
```

## 7. Gotchas & takeaways

> `@Fallback` requires **Spring Framework 6.2+**. In earlier versions, achieve the same effect with `@ConditionalOnMissingBean` (Spring Boot) or by annotating the non-fallback user beans with `@Primary`.

> A `@Fallback` bean can itself be `@Primary`. That makes it the highest-priority fallback — useful when you have multiple fallback implementations and want to control which one wins when no real bean exists.

- `@Fallback` is the inverse of `@Primary`: primary says "prefer me"; fallback says "only use me as last resort."
- Both annotations live on `org.springframework.context.annotation`.
- Combining `@Fallback` with `@Profile` gives you environment-sensitive defaults with zero application code change.
- When no non-fallback candidate exists, the normal `@Primary`/qualifier/name resolution applies among the fallback candidates.
- Library authors should annotate default beans with `@Fallback` so users can override them by simply registering their own bean — zero special configuration needed.
