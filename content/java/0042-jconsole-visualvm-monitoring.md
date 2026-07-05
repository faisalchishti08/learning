---
card: java
gi: 42
slug: jconsole-visualvm-monitoring
title: jconsole / VisualVM — monitoring
---

## 1. What it is

**`jconsole`** and **VisualVM** are graphical JVM monitoring tools that connect to a running JVM and display real-time charts for heap, threads, classes, and MBean attributes.

- **`jconsole`** ships with every JDK (`$JAVA_HOME/bin/jconsole`). Lightweight, built-in, covers heap/threads/classes/MBeans.
- **VisualVM** (`jvisualvm`) was bundled with JDK 8 but is now a standalone download at `visualvm.github.io`. It adds CPU/memory profiling, heap dump analysis, thread dump analysis, and plugin support.

Both connect via JMX (Java Management Extensions) — the same API that `ManagementFactory` exposes programmatically.

## 2. Why & when

Use `jconsole` when:
- You need a **quick look at heap trends** on a server you can SSH into.
- Checking **thread counts** and **class-loading** during startup.
- Browsing **MBeans** to tweak application configuration at runtime.
- No internet access (it ships with the JDK).

Use **VisualVM** when:
- You need **CPU profiling** — which methods are hot.
- Analysing **heap dumps** (`.hprof`) visually.
- You want **plugin support** (Eclipse MAT integration, JFR viewer, etc.).
- You want a better thread timeline and sampler.

Both require either: same-machine access (local process), or a JMX port open (`-Dcom.sun.management.jmxremote.port=9999`).

## 3. Core concept

```bash
# Launch jconsole (connects to local JVMs automatically)
jconsole

# Or connect to a remote JVM (remote JMX must be enabled)
jconsole <host>:<port>

# Enable remote JMX on the target JVM:
java -Dcom.sun.management.jmxremote \
     -Dcom.sun.management.jmxremote.port=9999 \
     -Dcom.sun.management.jmxremote.ssl=false \
     -Dcom.sun.management.jmxremote.authenticate=false \
     -jar app.jar

# VisualVM (download from visualvm.github.io)
./visualvm --jdkhome /path/to/jdk

# Programmatic JMX — same data jconsole reads:
ManagementFactory.getMemoryMXBean().getHeapMemoryUsage()
ManagementFactory.getThreadMXBean().getThreadCount()
ManagementFactory.getGarbageCollectorMXBeans()
ManagementFactory.getPlatformMBeanServer()  // register custom MBeans

# Register a custom MBean so jconsole can see it:
ObjectName name = new ObjectName("com.example:type=OrderService");
ManagementFactory.getPlatformMBeanServer().registerMBean(orderServiceMBean, name);
```

JMX architecture:
- The **MBean Server** runs inside every JVM by default.
- **MBeans** are Java objects that expose attributes and operations.
- **jconsole/VisualVM** are JMX clients that browse and display MBean data.
- Standard MBeans: `java.lang:type=Memory`, `java.lang:type=Threading`, `java.lang:type=GarbageCollector,name=G1 Young Generation`.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jconsole and VisualVM connect to the JMX server inside a running JVM to read MBeans">
  <rect x="8" y="8" width="684" height="204" rx="8" fill="#0d1117"/>

  <!-- JVM box -->
  <rect x="20" y="25" width="255" height="170" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="147" y="44" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Running JVM</text>

  <!-- MBeans inside JVM -->
  <rect x="35" y="54"  width="225" height="24" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="147" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">java.lang:type=Memory</text>

  <rect x="35" y="84"  width="225" height="24" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="147" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">java.lang:type=Threading</text>

  <rect x="35" y="114" width="225" height="24" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="147" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">java.lang:type=GarbageCollector,name=G1</text>

  <rect x="35" y="144" width="225" height="35" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="147" y="157" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">com.example:type=OrderService</text>
  <text x="147" y="171" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(custom MBean)</text>

  <!-- JMX connector -->
  <rect x="330" y="88" width="90" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="375" y="106" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">JMX / RMI</text>
  <text x="375" y="119" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">port 9999</text>

  <line x1="275" y1="110" x2="326" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jx1)"/>

  <!-- Clients -->
  <rect x="478" y="30"  width="200" height="55" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="578" y="50"  fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">jconsole</text>
  <text x="578" y="67"  fill="#6db33f" font-size="8"  text-anchor="middle" font-family="sans-serif">Heap / Threads / Classes / MBeans</text>
  <text x="578" y="79"  fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">ships with JDK</text>

  <rect x="478" y="98"  width="200" height="55" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="578" y="118" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">VisualVM</text>
  <text x="578" y="134" fill="#6db33f" font-size="8"  text-anchor="middle" font-family="sans-serif">CPU profiler / Heap analyser</text>
  <text x="578" y="146" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">separate download</text>

  <rect x="478" y="166" width="200" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="578" y="183" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Custom code (ManagementFactory)</text>
  <text x="578" y="196" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">programmatic JMX client</text>

  <line x1="420" y1="100" x2="474" y2="57"  stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jx2)"/>
  <line x1="420" y1="110" x2="474" y2="125" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jx2)"/>
  <line x1="420" y1="120" x2="474" y2="184" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jx2)"/>

  <defs>
    <marker id="jx1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
    <marker id="jx2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
  </defs>
</svg>

`jconsole` and VisualVM are JMX clients that read standard and custom MBeans from the JVM's built-in MBean Server, optionally via a remote JMX/RMI port.

## 5. Runnable example

Scenario: expose a custom `OrderService` MBean that tracks order count and average latency, inspect it programmatically (same as `jconsole` would show), and simulate what `jconsole` displays.

### Level 1 — Basic

```java
// JconsoleBasic.java — read standard MBeans programmatically (what jconsole shows)
import java.lang.management.*;
import java.nio.file.*;

public class JconsoleBasic {
    public static void main(String[] args) throws Exception {
        System.out.println("=== JMX / jconsole data demo ===\n");

        // Heap (Memory tab in jconsole)
        MemoryMXBean mem = ManagementFactory.getMemoryMXBean();
        MemoryUsage heap = mem.getHeapMemoryUsage();
        System.out.printf("Heap: used=%d MB, committed=%d MB, max=%d MB%n",
            heap.getUsed() / 1_048_576,
            heap.getCommitted() / 1_048_576,
            heap.getMax() / 1_048_576);

        // Threads (Threads tab)
        ThreadMXBean tmx = ManagementFactory.getThreadMXBean();
        System.out.printf("Threads: live=%d, daemon=%d, peak=%d%n",
            tmx.getThreadCount(), tmx.getDaemonThreadCount(), tmx.getPeakThreadCount());

        // Classes (Classes tab)
        ClassLoadingMXBean cls = ManagementFactory.getClassLoadingMXBean();
        System.out.printf("Classes: loaded=%d, total=%d, unloaded=%d%n",
            cls.getLoadedClassCount(), cls.getTotalLoadedClassCount(), cls.getUnloadedClassCount());

        // GC (VM Summary → Garbage Collectors)
        for (GarbageCollectorMXBean gc : ManagementFactory.getGarbageCollectorMXBeans())
            System.out.printf("GC [%s]: count=%d, time=%d ms%n",
                gc.getName(), gc.getCollectionCount(), gc.getCollectionTime());

        // JVM info (VM Summary tab)
        RuntimeMXBean rt = ManagementFactory.getRuntimeMXBean();
        System.out.println("\nJVM: " + rt.getVmName() + " " + rt.getVmVersion());
        System.out.println("Uptime: " + rt.getUptime() + " ms");
        System.out.println("PID: " + ProcessHandle.current().pid());
        System.out.println("\nOpen jconsole and connect to PID above to see these live.");
    }
}
```

**How to run:** `java JconsoleBasic.java`

Every value printed here is what `jconsole` shows on its tabs — same MBeans, same data. `jconsole` just graphs them over time and auto-refreshes.

### Level 2 — Intermediate

Same order-service scenario: register a **custom MBean** that `jconsole` can browse in its MBeans tab. The MBean exposes `OrderCount` and `AverageLatencyMs` as readable attributes, and `resetCounters()` as an operation.

```java
// JconsoleCustomMBean.java — register a custom MBean visible in jconsole
import java.lang.management.*;
import javax.management.*;

public class JconsoleCustomMBean {

    // MBean interface — jconsole shows all methods matching get/set/is
    public interface OrderServiceMBean {
        long getOrderCount();
        double getAverageLatencyMs();
        void resetCounters();
    }

    // MBean implementation
    static class OrderService implements OrderServiceMBean {
        private long count = 0;
        private long totalLatencyMs = 0;

        public synchronized long getOrderCount() { return count; }
        public synchronized double getAverageLatencyMs() {
            return count == 0 ? 0.0 : (double) totalLatencyMs / count;
        }
        public synchronized void resetCounters() { count = 0; totalLatencyMs = 0; }

        synchronized void recordOrder(long latencyMs) {
            count++;
            totalLatencyMs += latencyMs;
        }
    }

    public static void main(String[] args) throws Exception {
        OrderService svc = new OrderService();

        // Register in the platform MBean server (same server jconsole reads)
        MBeanServer mbs = ManagementFactory.getPlatformMBeanServer();
        ObjectName name = new ObjectName("com.example:type=OrderService");
        mbs.registerMBean(svc, name);

        System.out.println("=== Custom MBean registered ===");
        System.out.println("MBean: " + name);
        System.out.println("PID:   " + ProcessHandle.current().pid());
        System.out.println("Open jconsole → MBeans tab → com.example → OrderService");
        System.out.println();

        // Simulate orders arriving
        java.util.Random rng = new java.util.Random();
        for (int i = 0; i < 30; i++) {
            long latency = 50 + rng.nextInt(200);
            svc.recordOrder(latency);

            if (i % 5 == 4) {
                // Read the MBean through the MBeanServer (same as jconsole does)
                long count = (Long) mbs.getAttribute(name, "OrderCount");
                double avg  = (Double) mbs.getAttribute(name, "AverageLatencyMs");
                System.out.printf("Orders: %d | Avg latency: %.1f ms%n", count, avg);
            }
            Thread.sleep(200);
        }

        // Invoke operation (same as clicking 'resetCounters' in jconsole)
        mbs.invoke(name, "resetCounters", null, null);
        System.out.println("Counters reset via MBeanServer (like jconsole Invoke button).");
        System.out.printf("After reset: count=%d%n", svc.getOrderCount());
    }
}
```

**How to run:** `java JconsoleCustomMBean.java`

While the program runs, open `jconsole`, connect to the PID, open the **MBeans** tab, expand `com.example → OrderService → Attributes`. You'll see `OrderCount` and `AverageLatencyMs` updating live. Under `Operations` you can click `resetCounters`.

### Level 3 — Advanced

Same order-service MBean grown to use `NotificationBroadcasterSupport` so `jconsole` receives **JMX notifications** (alerts) when latency exceeds a threshold — the JMX equivalent of application-level alerting.

```java
// JconsoleNotifications.java — custom MBean with JMX notifications (alerts)
import java.lang.management.*;
import javax.management.*;
import java.util.*;
import java.util.concurrent.atomic.*;

public class JconsoleNotifications {

    public interface OrderServiceMBean extends NotificationEmitter {
        long getOrderCount();
        double getAverageLatencyMs();
        long getSlowOrderCount();
        void setSlowThresholdMs(long thresholdMs);
        long getSlowThresholdMs();
        void resetCounters();
    }

    static class OrderService extends NotificationBroadcasterSupport implements OrderServiceMBean {
        private final AtomicLong orderCount      = new AtomicLong();
        private final AtomicLong totalLatencyMs  = new AtomicLong();
        private final AtomicLong slowOrderCount  = new AtomicLong();
        private final AtomicLong seqNo           = new AtomicLong();
        private volatile long slowThresholdMs = 200;

        public long   getOrderCount()        { return orderCount.get(); }
        public long   getSlowOrderCount()    { return slowOrderCount.get(); }
        public long   getSlowThresholdMs()   { return slowThresholdMs; }
        public void   setSlowThresholdMs(long t) { slowThresholdMs = t; }
        public double getAverageLatencyMs()  {
            long c = orderCount.get();
            return c == 0 ? 0.0 : (double) totalLatencyMs.get() / c;
        }
        public void resetCounters() {
            orderCount.set(0); totalLatencyMs.set(0); slowOrderCount.set(0);
        }

        void recordOrder(long latencyMs) {
            orderCount.incrementAndGet();
            totalLatencyMs.addAndGet(latencyMs);
            if (latencyMs > slowThresholdMs) {
                slowOrderCount.incrementAndGet();
                // Emit JMX notification — jconsole shows these as events
                Notification n = new Notification(
                    "com.example.order.slow",
                    this,
                    seqNo.incrementAndGet(),
                    System.currentTimeMillis(),
                    String.format("Slow order: %d ms (threshold=%d ms)", latencyMs, slowThresholdMs)
                );
                sendNotification(n);
            }
        }

        @Override
        public MBeanNotificationInfo[] getNotificationInfo() {
            return new MBeanNotificationInfo[] {
                new MBeanNotificationInfo(
                    new String[] { "com.example.order.slow" },
                    Notification.class.getName(),
                    "Emitted when an order exceeds the slow-threshold"
                )
            };
        }
    }

    public static void main(String[] args) throws Exception {
        OrderService svc = new OrderService();
        MBeanServer mbs  = ManagementFactory.getPlatformMBeanServer();
        ObjectName name  = new ObjectName("com.example:type=OrderService");
        mbs.registerMBean(svc, name);

        // Local notification listener (what jconsole subscribes for)
        List<String> receivedAlerts = new ArrayList<>();
        mbs.addNotificationListener(name, (notif, handback) ->
            receivedAlerts.add(notif.getMessage()), null, null);

        System.out.println("=== JMX notifications demo ===");
        System.out.println("PID: " + ProcessHandle.current().pid());
        System.out.println("jconsole: MBeans → com.example → OrderService → Notifications");
        System.out.println("(subscribe in jconsole to receive slow-order alerts)");
        System.out.println();

        // Simulate mixed-latency orders
        Random rng = new Random();
        for (int i = 0; i < 40; i++) {
            // 20% of orders are intentionally slow
            long latency = rng.nextInt(100) < 20 ? 250 + rng.nextInt(300) : 30 + rng.nextInt(150);
            svc.recordOrder(latency);
            Thread.sleep(150);
        }

        System.out.printf("Orders: %d | Avg: %.1f ms | Slow: %d%n",
            svc.getOrderCount(), svc.getAverageLatencyMs(), svc.getSlowOrderCount());
        System.out.println("\nNotifications received locally:");
        receivedAlerts.forEach(a -> System.out.println("  ALERT: " + a));
    }
}
```

**How to run:** `java JconsoleNotifications.java`

While running, connect `jconsole`, open the **MBeans** tab, navigate to `com.example → OrderService → Notifications`, and click **Subscribe** — you'll receive `com.example.order.slow` notifications each time a slow order is processed. This is the JMX equivalent of an application-level alert.

## 6. Walkthrough

Execution trace in `JconsoleNotifications.main`:

**MBean registration.** `mbs.registerMBean(svc, name)` registers the `OrderService` object into the platform MBean Server under the name `com.example:type=OrderService`. The MBean Server is the in-JVM registry that `jconsole` connects to.

**`jconsole` connection.** When you launch `jconsole` and connect to the PID, it establishes a JMX connection to the MBean Server (local attach via `/tmp/hsperfdata_*`). It calls `mbs.queryMBeans(null, null)` to discover all registered MBeans. Standard beans (`java.lang:type=Memory`, etc.) appear automatically; our `com.example:type=OrderService` appears because we registered it.

**Attribute reads.** Every time `jconsole` refreshes (default: 1 second), it calls `mbs.getAttribute(name, "OrderCount")`. This invokes `svc.getOrderCount()` on the server side and returns the value over the JMX channel. The "Heap" and "Threads" charts in `jconsole` work the same way — periodic `getAttribute` calls.

**Notification flow.** When a slow order arrives (`latencyMs > slowThresholdMs`), `sendNotification(n)` is called. This invokes all registered `NotificationListener` callbacks — both our local listener and any `jconsole` subscriber. The notification carries a type string, sequence number, timestamp, and message. jconsole shows it in the Notifications panel.

**Request/response for attribute read (conceptual):**
```
jconsole → getAttribute("com.example:type=OrderService", "AverageLatencyMs")
JVM MBean Server → dispatches to svc.getAverageLatencyMs()
svc.getAverageLatencyMs() → returns 87.3
JVM MBean Server → returns Double(87.3) to jconsole
jconsole → displays "87.3" in Attributes panel
```

**State changes per attribute call:** the method is invoked synchronously in the MBean Server's thread pool. No locking on our side (we use `AtomicLong` for thread safety). The returned value is a snapshot at the moment of the call.

## 7. Gotchas & takeaways

> **Remote JMX without SSL is a security risk.** `-Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false` should only be used in a trusted internal network (localhost or VPN). An open JMX port lets any client execute arbitrary MBean operations, including `java.lang:type=Runtime.gc()` and custom MBeans with write attributes. Always use SSL + authentication for production remote monitoring.

> **`jconsole` and VisualVM block startup** if you specify `-Dcom.sun.management.jmxremote.port=9999` and that port is occupied. Use a health-check or startup probe to verify the port before launching your app.

- `jconsole` ships with the JDK — `$JAVA_HOME/bin/jconsole` — zero extra install.
- VisualVM is a separate download but has CPU profiling and heap dump analysis that `jconsole` lacks.
- MBean naming convention: `<domain>:type=<ClassName>[,name=<instance>]` — follow this for standard tooling compatibility.
- `NotificationBroadcasterSupport` + `sendNotification()` = JMX alerts — same mechanism Spring Boot Actuator uses for health events.
- For headless servers, use `jmxterm` (CLI JMX client) or expose MBeans via HTTP through Spring Boot Actuator (`/actuator/metrics`).
