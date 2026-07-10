---
card: spring-framework
gi: 398
slug: jmx-mbean-export-managedresource
title: "JMX (MBean export, @ManagedResource)"
---

## 1. What it is

Java Management Extensions (JMX) is the standard Java mechanism for exposing an application's internals — configuration, metrics, operations — to external monitoring and management tools (like `jconsole`, `VisualVM`, or a monitoring agent) as **MBeans** (Managed Beans). Spring's JMX support lets you turn an ordinary Spring bean into an MBean just by annotating it with `@ManagedResource`, `@ManagedAttribute`, and `@ManagedOperation`, instead of hand-writing a JMX `*MBean` interface.

```java
@ManagedResource(objectName = "app:name=CacheManager", description = "Runtime cache controls")
class CacheManager {
    private int hitCount;

    @ManagedAttribute(description = "Number of cache hits since startup")
    public int getHitCount() { return hitCount; }

    @ManagedOperation(description = "Clear all cached entries")
    public void clearCache() { /* ... */ }
}
```

## 2. Why & when

Before Spring's JMX support, exposing an object over JMX meant writing a separate `FooMBean` interface mirroring every method you wanted exposed, implementing `FooMBean` on your class, and manually registering it with the platform `MBeanServer` — a lot of boilerplate for what's conceptually just "let ops see and tweak this bean at runtime." Spring's `@ManagedResource` collapses that into annotations plus an `MBeanExporter` (or the `@EnableMBeanExport`/Spring Boot auto-configuration equivalent) that scans for annotated beans and registers them automatically.

Reach for Spring's JMX support when:

- You need runtime visibility into internal state (queue depth, cache hit rate, thread pool size) that a metrics system alone doesn't capture, or you need it available to `jconsole`-style tooling without deploying a full metrics stack.
- You want operators to be able to trigger an operational action at runtime (clear a cache, reload configuration, pause a scheduled job) without redeploying or restarting the application.
- Your organization already has JMX-based monitoring/alerting infrastructure and expects new applications to expose the same kind of MBeans as existing ones.

In greenfield Spring Boot applications, Micrometer plus a metrics backend (Prometheus, CloudWatch) usually replaces JMX for *observability*, but JMX is still commonly used for *management operations* (triggering an action) since Micrometer is metrics-focused, not action-focused — and Spring Boot Actuator itself exposes many of its endpoints as MBeans automatically alongside HTTP.

## 3. Core concept

```
 @ManagedResource class                MBeanServer (JVM-wide registry)
        |                                       ^
        | scanned by                            |
        v                                       |
 MBeanExporter  ------------------ registers --- |
        |
        | wraps annotated methods as:
        v
 @ManagedAttribute -> JMX attribute (get/set)
 @ManagedOperation -> JMX operation (invokable method)
```

`MBeanExporter` is the bridge: it finds beans annotated `@ManagedResource`, builds a `ModelMBean` reflecting their `@ManagedAttribute`/`@ManagedOperation` members, and registers that `ModelMBean` under the given `objectName` with the JVM's `MBeanServer`, where any JMX client can find and use it.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring bean annotated ManagedResource exported to the platform MBeanServer for JMX clients">
  <rect x="10" y="60" width="170" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">CacheManager</text>
  <text x="95" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@ManagedResource</text>

  <rect x="235" y="60" width="170" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MBeanExporter</text>
  <text x="320" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">scans + registers</text>

  <rect x="460" y="60" width="170" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MBeanServer</text>
  <text x="545" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">jconsole / VisualVM</text>

  <line x1="180" y1="95" x2="230" y2="95" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <line x1="405" y1="95" x2="455" y2="95" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Once registered, any JMX client can read attributes and invoke operations on the bean — a live remote control panel for the running JVM.

## 5. Runnable example

### Level 1 — Basic

A single `@ManagedResource` bean exported and inspected programmatically through the platform `MBeanServer` (standing in for an external `jconsole` connection, so the example is fully self-contained).

```java
import org.springframework.context.annotation.*;
import org.springframework.jmx.export.annotation.*;
import org.springframework.jmx.support.MBeanServerFactoryBean;

import javax.management.MBeanServer;
import javax.management.ObjectName;

public class JmxBasic {

    @ManagedResource(objectName = "app:name=CacheManager", description = "Runtime cache controls")
    static class CacheManager {
        private int hitCount = 42;

        @ManagedAttribute(description = "Number of cache hits since startup")
        public int getHitCount() { return hitCount; }
    }

    @Configuration
    @EnableMBeanExport
    static class Config {
        @Bean
        CacheManager cacheManager() { return new CacheManager(); }
    }

    public static void main(String[] args) throws Exception {
        var context = new AnnotationConfigApplicationContext(Config.class);
        MBeanServer mBeanServer = context.getBean(MBeanServer.class);

        ObjectName name = new ObjectName("app:name=CacheManager");
        Object hitCount = mBeanServer.getAttribute(name, "HitCount");
        System.out.println("HitCount via JMX: " + hitCount);

        context.close();
    }
}
```

How to run: add `spring-context` on the classpath, then `java JmxBasic.java`.

`@EnableMBeanExport` activates an `MBeanExporter` bean that scans the whole context at startup for `@ManagedResource`-annotated beans; finding `CacheManager`, it registers it under `app:name=CacheManager` with the JVM's platform `MBeanServer`. Reading the `HitCount` attribute through `mBeanServer.getAttribute(...)` — rather than calling `cacheManager.getHitCount()` directly — demonstrates that any JMX client (not just this code) can now read that value the same way.

### Level 2 — Intermediate

Add a `@ManagedOperation` so an external tool can trigger behavior, not just read state, and show the mutation taking effect through the MBean interface.

```java
import org.springframework.context.annotation.*;
import org.springframework.jmx.export.annotation.*;
import javax.management.MBeanServer;
import javax.management.ObjectName;

public class JmxIntermediate {

    @ManagedResource(objectName = "app:name=CacheManager", description = "Runtime cache controls")
    static class CacheManager {
        private int hitCount = 42;
        private boolean cleared = false;

        @ManagedAttribute(description = "Number of cache hits since startup")
        public int getHitCount() { return hitCount; }

        @ManagedOperation(description = "Clear the cache and reset the hit counter")
        public String clearCache() {
            hitCount = 0;
            cleared = true;
            return "Cache cleared at " + java.time.Instant.now();
        }
    }

    @Configuration
    @EnableMBeanExport
    static class Config {
        @Bean
        CacheManager cacheManager() { return new CacheManager(); }
    }

    public static void main(String[] args) throws Exception {
        var context = new AnnotationConfigApplicationContext(Config.class);
        MBeanServer mBeanServer = context.getBean(MBeanServer.class);
        ObjectName name = new ObjectName("app:name=CacheManager");

        System.out.println("Before: " + mBeanServer.getAttribute(name, "HitCount"));

        Object result = mBeanServer.invoke(name, "clearCache", new Object[0], new String[0]);
        System.out.println("Operation result: " + result);

        System.out.println("After: " + mBeanServer.getAttribute(name, "HitCount"));

        context.close();
    }
}
```

How to run: `java JmxIntermediate.java` (same classpath as Level 1).

`@ManagedOperation` exposes `clearCache()` as an invokable JMX operation. Calling it via `mBeanServer.invoke(name, "clearCache", ...)` runs on the *same* `CacheManager` instance managed by the Spring context — the `hitCount` drop from `42` to `0` is visible through a subsequent `getAttribute` call, proving the MBean is a live view onto real application state, not a snapshot.

### Level 3 — Advanced

Production JMX exports typically need multiple related beans registered under a consistent naming scheme, a writable attribute for runtime configuration tuning, and JMX notifications so external tools can react to state changes rather than polling.

```java
import org.springframework.context.annotation.*;
import org.springframework.jmx.export.annotation.*;
import org.springframework.jmx.export.notification.NotificationPublisher;
import org.springframework.jmx.export.notification.NotificationPublisherAware;

import javax.management.Notification;
import javax.management.MBeanServer;
import javax.management.ObjectName;

public class JmxAdvanced {

    @ManagedResource(objectName = "app:name=RateLimiter", description = "Runtime-tunable rate limiter")
    static class RateLimiter implements NotificationPublisherAware {
        private int permitsPerSecond = 100;
        private NotificationPublisher publisher;

        @Override
        public void setNotificationPublisher(NotificationPublisher publisher) {
            this.publisher = publisher;
        }

        @ManagedAttribute(description = "Current permits allowed per second")
        public int getPermitsPerSecond() { return permitsPerSecond; }

        @ManagedAttribute(description = "Tune permits allowed per second at runtime")
        public void setPermitsPerSecond(int value) {
            int old = this.permitsPerSecond;
            this.permitsPerSecond = value;
            if (publisher != null) {
                publisher.sendNotification(new Notification(
                        "ratelimiter.changed", this, 1,
                        "permitsPerSecond changed from " + old + " to " + value));
            }
        }
    }

    @Configuration
    @EnableMBeanExport
    static class Config {
        @Bean
        RateLimiter rateLimiter() { return new RateLimiter(); }
    }

    public static void main(String[] args) throws Exception {
        var context = new AnnotationConfigApplicationContext(Config.class);
        MBeanServer mBeanServer = context.getBean(MBeanServer.class);
        ObjectName name = new ObjectName("app:name=RateLimiter");

        mBeanServer.addNotificationListener(name,
                (notification, handback) -> System.out.println("Notification: " + notification.getMessage()),
                null, null);

        System.out.println("Initial: " + mBeanServer.getAttribute(name, "PermitsPerSecond"));
        mBeanServer.setAttribute(name, new javax.management.Attribute("PermitsPerSecond", 250));
        System.out.println("Updated: " + mBeanServer.getAttribute(name, "PermitsPerSecond"));

        context.close();
    }
}
```

How to run: `java JmxAdvanced.java` (same classpath as Level 1).

Because both the getter and setter are annotated `@ManagedAttribute`, the JMX attribute becomes writable — `mBeanServer.setAttribute(...)` lets an operator (or an automated tuning system) change `permitsPerSecond` on a live application without a restart. `NotificationPublisherAware` lets the bean push a JMX `Notification` whenever the value changes, so monitoring tools can react in real time instead of polling the attribute repeatedly.

## 6. Walkthrough

Trace `JmxAdvanced.main` end to end:

1. **Export at startup.** `@EnableMBeanExport` builds an `MBeanExporter`, which scans the context, finds `RateLimiter` (annotated `@ManagedResource`), and registers a `ModelMBean` for it under `app:name=RateLimiter` with the platform `MBeanServer`. Because `RateLimiter` implements `NotificationPublisherAware`, Spring injects a `NotificationPublisher` into it during this export step, wiring it to that same registered MBean.
2. **Listener attached.** `mBeanServer.addNotificationListener(name, ...)` registers a callback that will fire whenever this specific MBean sends a notification — simulating what a monitoring tool subscribing to the MBean would do.
3. **Read initial value.** `getAttribute(name, "PermitsPerSecond")` calls through to `RateLimiter.getPermitsPerSecond()`, printing `100`.
4. **Write a new value.** `setAttribute(name, new Attribute("PermitsPerSecond", 250))` calls `RateLimiter.setPermitsPerSecond(250)` on the live bean.
5. **Inside the setter.** The old value (`100`) is captured, the field is updated to `250`, and because `publisher` was wired in step 1, `publisher.sendNotification(...)` fires a JMX `Notification` describing the change.
6. **Notification delivered.** The `MBeanServer`'s notification dispatch mechanism delivers that `Notification` to the listener registered in step 2, which prints `"Notification: permitsPerSecond changed from 100 to 250"` — this happens synchronously within the `setAttribute` call in this simple example.
7. **Read updated value.** `getAttribute(name, "PermitsPerSecond")` now returns `250`, confirming the write took effect on the same live bean instance managed by the Spring context.

```
mBeanServer.setAttribute("PermitsPerSecond", 250)
      -> RateLimiter.setPermitsPerSecond(250)
            old=100, new=250
            publisher.sendNotification(...)
                  -> registered listener prints notification
      -> field updated
mBeanServer.getAttribute("PermitsPerSecond") -> 250
```

## 7. Gotchas & takeaways

> Gotcha: exposing a writable `@ManagedAttribute` setter (like `setPermitsPerSecond`) means anyone with JMX access to the JVM can change that value at runtime — JMX has its own separate access-control and remote-connector security configuration (`com.sun.management.jmxremote.*` system properties), which is easy to leave wide open or entirely unauthenticated on a remotely-accessible port. Never expose remote JMX on a production host without authentication and, ideally, SSL.

- `@ManagedResource`/`@ManagedAttribute`/`@ManagedOperation` turn a plain Spring bean into a live, inspectable-and-actionable JMX MBean with a handful of annotations, no separate MBean interface required.
- Read-only attributes (getter only) are safe for exposing metrics; read-write attributes (getter + setter both annotated) let operators change runtime behavior — reserve those for values that are genuinely safe to tune live.
- `NotificationPublisherAware` lets an MBean push events instead of forcing monitoring tools to poll attributes repeatedly.
- Spring Boot Actuator already exposes many of its own endpoints as MBeans automatically; use `@ManagedResource` primarily for custom, application-specific management hooks that Actuator doesn't cover.
