---
card: spring-integration
gi: 67
slug: jmx-support
title: "JMX support"
---

## 1. What it is

JMX support (`Jmx.attributePollingAdapter(...)`, `Jmx.operationInvokingAdapter(...)`, `Jmx.notificationListeningChannelAdapter(...)`, `Jmx.mbeanExportingAdapter(...)`) connects a flow to Java Management Extensions — the standard mechanism the JVM exposes for managing and monitoring running applications through MBeans (Managed Beans). Inbound, an adapter polls an MBean attribute or listens for JMX notifications and turns them into messages; outbound, a message can invoke an MBean operation or set an attribute, and a flow's own channels can even be exported as MBeans for external tools to inspect.

## 2. Why & when

You reach for JMX support when the integration point is the JVM's own management layer rather than an external network protocol:

- **Monitoring tools already speak JMX** — many operations dashboards, application servers, and profilers connect over JMX by default; exposing flow metrics or triggering flow behavior through JMX means those existing tools work without custom glue code.
- **A flow needs to react to JVM-level events** — garbage collection notifications, memory threshold crossings, or a custom MBean's state-change notification can all trigger a Spring Integration flow via `Jmx.notificationListeningChannelAdapter`.
- **An operational action should be triggerable without redeploying** — exposing a `.handle(...)` step's behavior as an invokable MBean operation lets an operator trigger it via `jconsole`, `jmxterm`, or a monitoring dashboard, without adding a REST endpoint just for that one operational task.

## 3. Core concept

Think of JMX as a building's control panel bolted to the wall next to the elevator — dials showing current readings (attributes), buttons to press for specific actions (operations), and a light that flashes when something needs attention (notifications). Spring Integration's JMX adapters let a flow either watch those dials and act on what it sees (polling attributes, listening for notifications) or reach out and press those buttons itself (invoking operations), all without needing a custom network protocol — JMX is the shared building-wide interface every management tool already knows how to read.

```java
@Bean
public IntegrationFlow jmxAttributePollingFlow() {
    return IntegrationFlow.from(
            Jmx.attributePollingAdapter("java.lang:type=Memory", "HeapMemoryUsage"),
            e -> e.poller(Pollers.fixedDelay(10_000)))
        .handle((javax.management.openmbean.CompositeData usage, headers) -> {
            long used = (Long) usage.get("used");
            if (used > 500_000_000L) alertService.notifyHighMemory(used);
        })
        .get();
}
```

Every ten seconds, the flow reads the JVM's own heap-usage MBean attribute and reacts if it crosses a threshold — no separate metrics-scraping agent required.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Attribute polling adapter reads an MBean attribute on an interval; notification listening adapter reacts to pushed JMX notifications; operation invoking adapter calls an MBean operation from a message" >
  <rect x="10" y="20" width="195" height="120" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="107" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Attribute polling</text>
  <text x="25" y="50" fill="#e6edf3" font-size="7" font-family="monospace">poll every N sec</text>
  <text x="25" y="70" fill="#79c0ff" font-size="7" font-family="monospace">MBean.getAttribute()</text>
  <text x="25" y="100" fill="#8b949e" font-size="7" font-family="sans-serif">-&gt; Message with value</text>

  <rect x="222" y="20" width="195" height="120" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="319" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Notification listening</text>
  <text x="237" y="50" fill="#e6edf3" font-size="7" font-family="monospace">MBean pushes event</text>
  <text x="237" y="70" fill="#79c0ff" font-size="7" font-family="monospace">no polling delay</text>
  <text x="237" y="100" fill="#8b949e" font-size="7" font-family="sans-serif">-&gt; Message on notification</text>

  <rect x="434" y="20" width="195" height="120" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="531" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Operation invoking</text>
  <text x="449" y="50" fill="#e6edf3" font-size="7" font-family="monospace">Message arrives</text>
  <text x="449" y="70" fill="#6db33f" font-size="7" font-family="monospace">MBean.invoke(op, args)</text>
  <text x="449" y="100" fill="#8b949e" font-size="7" font-family="sans-serif">-&gt; operational action taken</text>
</svg>

Three directions through the same management layer: read a dial, react to a flashing light, or press a button.

## 5. Runnable example

The scenario: monitoring a JVM-style resource attribute and alerting on a threshold, simulated with a plain in-memory "MBean" (no real JVM MBeanServer or JMX connection needed to demonstrate the polling and reaction logic), starting with a single poll-and-check, then adding notification-style push alerts, then adding an operation-invoking cooldown so alerts don't spam.

### Level 1 — Basic

```java
// JmxMonitorDemo.java
public class JmxMonitorDemo {
    // Stand-in for an MBean attribute: a value the flow polls, like heap usage.
    static class FakeMemoryMBean {
        long usedBytes;
        FakeMemoryMBean(long usedBytes) { this.usedBytes = usedBytes; }
        long getHeapMemoryUsed() { return usedBytes; } // stand-in for MBean.getAttribute("HeapMemoryUsage")
    }

    public static void main(String[] args) {
        FakeMemoryMBean mbean = new FakeMemoryMBean(600_000_000L);
        long used = mbean.getHeapMemoryUsed();
        if (used > 500_000_000L) {
            System.out.println("ALERT: heap usage " + used + " exceeds threshold");
        }
    }
}
```

How to run: `java JmxMonitorDemo.java`. Expected output: `ALERT: heap usage 600000000 exceeds threshold` — a single poll-and-threshold check, the core of an attribute-polling adapter.

### Level 2 — Intermediate

```java
// JmxMonitorDemo.java
import java.util.*;

public class JmxMonitorDemo {
    static class FakeMemoryMBean {
        long usedBytes;
        FakeMemoryMBean(long usedBytes) { this.usedBytes = usedBytes; }
        long getHeapMemoryUsed() { return usedBytes; }
    }

    // Real-world concern: polling once isn't enough -- the flow must run repeatedly on an
    // interval (as Pollers.fixedDelay does), and only alert on state transitions, not every poll.
    static class ThresholdMonitor {
        private boolean currentlyAlerting = false;
        void poll(FakeMemoryMBean mbean, long thresholdBytes) {
            long used = mbean.getHeapMemoryUsed();
            boolean overThreshold = used > thresholdBytes;
            if (overThreshold && !currentlyAlerting) {
                System.out.println("ALERT: heap usage " + used + " crossed threshold");
                currentlyAlerting = true;
            } else if (!overThreshold && currentlyAlerting) {
                System.out.println("RECOVERED: heap usage back to " + used);
                currentlyAlerting = false;
            }
        }
    }

    public static void main(String[] args) {
        FakeMemoryMBean mbean = new FakeMemoryMBean(400_000_000L);
        ThresholdMonitor monitor = new ThresholdMonitor();
        long threshold = 500_000_000L;

        long[] readings = { 400_000_000L, 600_000_000L, 620_000_000L, 450_000_000L };
        for (long reading : readings) {
            mbean.usedBytes = reading;
            monitor.poll(mbean, threshold);
        }
    }
}
```

How to run: `java JmxMonitorDemo.java`. Expected output: the second reading triggers `ALERT: ...`, the third reading (still over threshold) triggers nothing further, and the fourth reading (back under threshold) triggers `RECOVERED: ...` — mirroring how a well-behaved polling adapter alerts once on a transition rather than on every single poll while the condition holds.

### Level 3 — Advanced

```java
// JmxMonitorDemo.java
import java.util.*;

public class JmxMonitorDemo {
    static class FakeMemoryMBean {
        long usedBytes;
        FakeMemoryMBean(long usedBytes) { this.usedBytes = usedBytes; }
        long getHeapMemoryUsed() { return usedBytes; }
        // Stand-in for an operation-invoking adapter calling an MBean operation to remediate.
        void triggerGc() { System.out.println("  (invoked MBean operation: gc())"); usedBytes -= 200_000_000L; }
    }

    static class ThresholdMonitor {
        private boolean currentlyAlerting = false;
        private long lastActionMillis = 0;
        private static final long COOLDOWN_MILLIS = 1000;

        void poll(FakeMemoryMBean mbean, long thresholdBytes, long nowMillis) {
            long used = mbean.getHeapMemoryUsed();
            boolean overThreshold = used > thresholdBytes;

            if (overThreshold) {
                if (!currentlyAlerting) {
                    System.out.println("ALERT: heap usage " + used + " crossed threshold");
                    currentlyAlerting = true;
                }
                // Production concern: don't invoke a remediating operation on every poll while
                // still over threshold -- a cooldown prevents hammering the MBean operation.
                if (nowMillis - lastActionMillis > COOLDOWN_MILLIS) {
                    mbean.triggerGc();
                    lastActionMillis = nowMillis;
                } else {
                    System.out.println("  (skipping remediation, cooldown active)");
                }
            } else if (currentlyAlerting) {
                System.out.println("RECOVERED: heap usage back to " + used);
                currentlyAlerting = false;
            }
        }
    }

    public static void main(String[] args) {
        FakeMemoryMBean mbean = new FakeMemoryMBean(600_000_000L);
        ThresholdMonitor monitor = new ThresholdMonitor();
        long threshold = 500_000_000L;

        long now = 0;
        for (int i = 0; i < 3; i++) {
            System.out.println("-- poll at t=" + now + " --");
            monitor.poll(mbean, threshold, now);
            now += 200; // polls arrive faster than the cooldown in this simulation
        }
    }
}
```

How to run: `java JmxMonitorDemo.java`. Expected output: the first poll alerts and invokes `gc()`, dropping usage by 200MB; the second and third polls (within the 1000ms cooldown) skip remediation even if still over threshold — demonstrating the cooldown guard a real operation-invoking adapter needs so a flapping metric doesn't trigger a remediation operation on every single poll cycle.

## 6. Walkthrough

Trace a heap-alert-and-remediate cycle end to end.

1. **Poller fires**: `Jmx.attributePollingAdapter`'s poller calls `MBeanServerConnection.getAttribute("java.lang:type=Memory", "HeapMemoryUsage")` on the configured interval.
2. **Attribute retrieved**: the JVM's built-in Memory MBean returns a `CompositeData` describing current heap usage; the adapter wraps the relevant value as a message payload.
3. **Threshold check**: a `.handle(...)` step inspects the value and decides whether it crosses a configured threshold, tracking whether this is a new alert condition or a continuation of one already raised — the state-transition logic in Level 2.
4. **Remediation (optional)**: if configured, a `Jmx.operationInvokingAdapter` further down the flow calls an MBean operation — perhaps `System.gc()` exposed via an MBean, or an application-specific cache-eviction operation — subject to a cooldown so repeated over-threshold polls don't invoke it every cycle.
5. **Notification path (alternative entry point)**: instead of polling, a `Jmx.notificationListeningChannelAdapter` can register directly with an MBean's notification broadcaster, so the flow reacts the instant the MBean emits a notification, with no polling delay at all — useful when the MBean already proactively announces state changes.
6. **External visibility**: separately, `Jmx.mbeanExportingAdapter` can expose the flow's own channels and interceptors as MBeans, so external tools like `jconsole` can inspect message counts or invoke flow-defined operations directly through the same JMX interface the flow itself is consuming from other MBeans.

```
poller tick (every N sec)
  -> MBeanServerConnection.getAttribute("HeapMemoryUsage")
    -> threshold check (new alert? still alerting? recovered?)
       new alert    -> notify + (if cooldown elapsed) invoke remediation MBean operation
       still over   -> skip remediation if within cooldown
       recovered    -> notify recovery
```

## 7. Gotchas & takeaways

> **Gotcha:** polling an MBean attribute on a short interval under load can itself add measurable overhead (attribute retrieval isn't free, especially for composite or aggregate attributes) — pick a polling interval that matches how quickly the underlying value actually needs to be noticed, not the shortest interval available.

- Prefer `Jmx.notificationListeningChannelAdapter` over attribute polling when the MBean already emits notifications for the events of interest — it reacts instantly and avoids the trade-off between polling frequency and overhead entirely.
- An operation-invoking adapter that fires on every poll while a condition persists can turn a monitoring flow into an accidental denial-of-service against the very MBean it's meant to help — always gate repeated invocations with a cooldown or a state-transition check.
- JMX access itself typically requires authentication and, for remote connections, SSL configuration; treat an exposed MBeanServer as a privileged surface, not an open metrics endpoint.
- Exporting a flow's channels as MBeans (`Jmx.mbeanExportingAdapter`) is a convenient way to get visibility into message counts and rates in tools operators already use, without adding a bespoke metrics endpoint just for this flow.
