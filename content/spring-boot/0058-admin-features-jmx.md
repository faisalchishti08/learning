---
card: spring-boot
gi: 58
slug: admin-features-jmx
title: Admin features (JMX)
---

## 1. What it is

**JMX (Java Management Extensions)** is the standard Java mechanism for exposing application internals — beans, metrics, configuration — to external management tools. Spring Boot integrates with JMX in two ways:

1. **Spring JMX** (`spring-jmx`): any `@Component` bean annotated with `@ManagedResource` exposes its `@ManagedOperation` and `@ManagedAttribute` methods to JMX clients (JConsole, VisualVM, Java Mission Control).
2. **Spring Boot Admin Features** (`spring.application.admin.enabled=true`): exposes a `SpringApplicationAdminMXBean` that allows remote management operations like graceful shutdown via JMX.

```properties
# Enable the Spring Boot admin MBean
spring.application.admin.enabled=true
spring.application.admin.jmx-name=org.springframework.boot:type=Admin,name=SpringApplication
```

The MBean exposes: `isReady()`, `isEmbeddedWebApplication()`, `getProperty(key)`, and `shutdown()`.

JMX itself is also controlled:
```properties
spring.jmx.enabled=true                  # default in Spring Boot 2.x, default false in 3.x
spring.jmx.default-domain=com.example
```

## 2. Why & when

JMX predates REST APIs as the standard way to monitor and manage Java applications. It is still used in:

- **Legacy enterprise environments** with JMX-based monitoring (Nagios JMX plugins, JConsole dashboards).
- **Operational tooling** that needs remote inspection of bean state or property values without adding an HTTP endpoint.
- **Graceful shutdown** via JMX: useful when you cannot call an HTTP endpoint but can connect a JMX client.
- **Development diagnostics**: `jconsole` or VisualVM can show all Spring beans and their managed attributes live.

In modern Kubernetes / cloud environments, HTTP Actuator endpoints are preferred over JMX. Use JMX when your operations team has existing JMX tooling or when HTTP access is unavailable.

## 3. Core concept

JMX works through a **MBean Server** — a registry inside the JVM where objects (MBeans) are registered under a name (ObjectName). External clients connect to the MBean Server via RMI or `jmx://` and can call operations or read attributes on registered MBeans.

Spring Boot's integration:
- `MBeanExporter` automatically registers beans annotated with `@ManagedResource` into the MBean Server.
- The ObjectName is derived from the class name and domain, or from the annotation.
- `@ManagedAttribute` on a getter/setter pair exposes it as a readable/writable JMX attribute.
- `@ManagedOperation` on a method exposes it as a callable JMX operation.
- The `SpringApplicationAdminMXBean` (when admin.enabled=true) is always registered regardless of `@ManagedResource`.

```java
@Component
@ManagedResource(objectName = "com.example:type=App,name=ConfigManager")
public class ConfigManager {
    @ManagedAttribute
    public String getEnvironment() { return "production"; }

    @ManagedOperation
    public void reloadConfig() { /* ... */ }
}
```

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JMX architecture: Spring beans expose MBeans to JMX clients via MBean Server">
  <!-- Spring app -->
  <rect x="20" y="20" width="240" height="180" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="140" y="46" fill="#6db33f" font-size="12" font-family="monospace" font-weight="bold" text-anchor="middle">Spring Boot App</text>

  <rect x="36" y="58" width="208" height="44" rx="5" fill="#2d3748" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="78" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">@ManagedResource</text>
  <text x="140" y="94" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">ConfigManager @ManagedOperation</text>

  <rect x="36" y="112" width="208" height="44" rx="5" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="140" y="132" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">SpringApplicationAdminMXBean</text>
  <text x="140" y="148" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">isReady() shutdown() getProperty()</text>

  <rect x="36" y="166" width="208" height="26" rx="5" fill="#16202e" stroke="#6db33f" stroke-width="1"/>
  <text x="140" y="184" fill="#6db33f" font-size="9" font-family="monospace" text-anchor="middle">MBean Server (registry)</text>

  <!-- Arrow: beans → MBean Server -->
  <line x1="140" y1="156" x2="140" y2="164" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jm)"/>

  <!-- Client tools -->
  <rect x="440" y="60" width="200" height="100" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="540" y="84" fill="#8b949e" font-size="12" font-family="monospace" text-anchor="middle">JMX Clients</text>
  <text x="540" y="108" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">JConsole</text>
  <text x="540" y="126" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">VisualVM</text>
  <text x="540" y="144" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">Java Mission Control</text>

  <!-- RMI connection -->
  <line x1="264" y1="175" x2="438" y2="110" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#jm)"/>
  <text x="360" y="148" fill="#8b949e" font-size="10" font-family="sans-serif" text-anchor="middle">RMI / jmx://</text>

  <defs>
    <marker id="jm" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

`MBeanExporter` registers `@ManagedResource` beans and the Spring Boot admin MBean into the MBean Server; JMX clients connect remotely to call operations and read attributes.

## 5. Runnable example

```java
// JmxAdminDemo.java
// How to run: java JmxAdminDemo.java  (JDK 17+)
// Simulates @ManagedResource, @ManagedAttribute, @ManagedOperation,
// and SpringApplicationAdminMXBean without a real JMX server.

import java.util.*;

public class JmxAdminDemo {

    // ── Simulated JMX annotations ─────────────────────────────────
    @interface ManagedResource   { String objectName() default ""; }
    @interface ManagedAttribute  {}
    @interface ManagedOperation  {}

    // ── A managed bean ────────────────────────────────────────────
    @ManagedResource(objectName = "com.example:type=App,name=ConfigManager")
    static class ConfigManager {
        private String environment = "production";
        private boolean maintenanceMode = false;

        @ManagedAttribute public String getEnvironment()          { return environment; }
        @ManagedAttribute public boolean isMaintenanceMode()      { return maintenanceMode; }
        @ManagedAttribute public void setMaintenanceMode(boolean v){ maintenanceMode = v; }

        @ManagedOperation public String reloadConfig()  { return "Config reloaded OK"; }
        @ManagedOperation public String healthCheck()   { return "All systems nominal"; }
    }

    // ── SpringApplicationAdminMXBean simulation ───────────────────
    static class SpringApplicationAdminMXBean {
        private boolean ready = true;
        boolean isReady()                    { return ready; }
        boolean isEmbeddedWebApplication()   { return true; }
        String getProperty(String key)       { return "property[" + key + "]=demoValue"; }
        void shutdown()                      { System.out.println("[Admin] Shutdown requested via JMX"); ready = false; }
    }

    // ── Minimal MBean server simulation ───────────────────────────
    static Map<String, Object> mBeanServer = new LinkedHashMap<>();

    static void register(String objectName, Object mBean) {
        mBeanServer.put(objectName, mBean);
        System.out.println("MBean registered: " + objectName);
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== JMX MBean Server ===\n");

        ConfigManager configMgr = new ConfigManager();
        SpringApplicationAdminMXBean adminBean = new SpringApplicationAdminMXBean();

        register("com.example:type=App,name=ConfigManager", configMgr);
        register("org.springframework.boot:type=Admin,name=SpringApplication", adminBean);

        System.out.println("\n--- JConsole connects: reading attributes ---");
        System.out.println("ConfigManager.environment     = " + configMgr.getEnvironment());
        System.out.println("ConfigManager.maintenanceMode = " + configMgr.isMaintenanceMode());
        System.out.println("AdminMBean.isReady()          = " + adminBean.isReady());
        System.out.println("AdminMBean.getProperty(db.url)= " + adminBean.getProperty("db.url"));

        System.out.println("\n--- Operator invokes operations ---");
        System.out.println("ConfigManager.reloadConfig()  → " + configMgr.reloadConfig());
        System.out.println("ConfigManager.healthCheck()   → " + configMgr.healthCheck());

        System.out.println("\n--- Operator enables maintenance mode ---");
        configMgr.setMaintenanceMode(true);
        System.out.println("ConfigManager.maintenanceMode = " + configMgr.isMaintenanceMode());

        System.out.println("\n--- Remote graceful shutdown ---");
        adminBean.shutdown();
        System.out.println("AdminMBean.isReady()          = " + adminBean.isReady());
    }
}
```

**How to run:** `java JmxAdminDemo.java`

Expected output:
```
=== JMX MBean Server ===

MBean registered: com.example:type=App,name=ConfigManager
MBean registered: org.springframework.boot:type=Admin,name=SpringApplication

--- JConsole connects: reading attributes ---
ConfigManager.environment     = production
ConfigManager.maintenanceMode = false
AdminMBean.isReady()          = true
AdminMBean.getProperty(db.url)= property[db.url]=demoValue

--- Operator invokes operations ---
ConfigManager.reloadConfig()  → Config reloaded OK
ConfigManager.healthCheck()   → All systems nominal

--- Operator enables maintenance mode ---
ConfigManager.maintenanceMode = true

--- Remote graceful shutdown ---
[Admin] Shutdown requested via JMX
AdminMBean.isReady()          = false
```

## 6. Walkthrough

- `register()` simulates `MBeanExporter` registering beans under their ObjectNames into the MBean Server map.
- Reading `getEnvironment()` and `isMaintenanceMode()` shows `@ManagedAttribute` — these appear as JMX attributes that monitoring tools can poll or display in dashboards.
- Calling `reloadConfig()` and `healthCheck()` shows `@ManagedOperation` — these appear as buttons in JConsole that operators can click to trigger actions.
- Setting `maintenanceMode = true` via the JMX attribute setter (`setMaintenanceMode`) shows how JMX can change runtime application state without a code deployment.
- `adminBean.shutdown()` demonstrates the Spring Boot admin MBean's shutdown operation — the app marks itself not ready and Spring proceeds to close the context.

## 7. Gotchas & takeaways

> In Spring Boot 3.x, JMX is **disabled by default** (`spring.jmx.enabled=false`). This avoids opening a JMX port in production containers where JMX exposure is a security risk. Explicitly enable it when needed: `spring.jmx.enabled=true`.

> The `SpringApplicationAdminMXBean.shutdown()` operation calls `SpringApplication.exit()` — it closes the `ApplicationContext` gracefully. In Kubernetes this is usually handled by SIGTERM → graceful shutdown hooks, making the JMX shutdown less commonly used in cloud environments.

- Enable remote JMX with system properties: `-Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=9999 -Dcom.sun.management.jmxremote.authenticate=false` (authentication disabled only for dev).
- `spring.jmx.default-domain` sets the domain prefix for all auto-exported beans (default: `org.springframework.boot`).
- Actuator MBeans: Spring Boot Actuator also registers MBeans under `org.springframework.boot` for its endpoints — they are accessible via JMX without any extra configuration.
- For modern greenfield projects, prefer Actuator HTTP endpoints over JMX for monitoring and management.
