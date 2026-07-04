---
card: spring-framework
gi: 204
slug: spring-jcl-logging-bridge
title: Spring JCL logging bridge
---

## 1. What it is

**Spring JCL** (`spring-jcl`) is a tiny logging bridge module bundled with Spring Framework that replaces Apache Commons Logging (JCL). Spring Framework's own source code calls `LogFactory.getLog(MyClass.class)` — a Commons Logging API call — and Spring JCL routes those calls transparently to whatever logging implementation is on the classpath: **SLF4J**, **Log4j 2**, or the JDK's `java.util.logging` (JUL).

The result is that Spring Framework has zero hard dependency on any logging implementation. You add SLF4J + Logback (or Log4j 2) to your project and Spring's internal log output flows through your chosen framework automatically.

## 2. Why & when

Java has too many logging frameworks: JUL (built in), Log4j 1/2, Logback, SLF4J (a facade), Commons Logging (another facade). Libraries that hard-code one framework force you to use it or add conflict-resolution exclusions.

Spring's solution since 5.0: ship a zero-dependency `spring-jcl` that detects what's on the classpath at runtime and bridges to it. You never configure Spring JCL itself — you configure Logback or Log4j 2 as you normally would, and Spring's logs appear in your existing log output.

You care about this when:
- Debugging Spring internals (`org.springframework.*` log categories).
- Diagnosing why Spring's log output is missing or duplicated.
- Migrating from Spring 4 (which depended on actual Apache Commons Logging) to Spring 5+.

## 3. Core concept

Think of Spring JCL as a hotel concierge: a guest (Spring Framework code) asks "can you log this?" The concierge looks around and says "I see Logback at the front desk — I'll hand this to them." The guest never knows which clerk handled it.

Detection order (first found wins):
1. **SLF4J** — if SLF4J is on the classpath, route all calls to it. Logback or Log4j 2 can then be the SLF4J backend.
2. **Log4j 2** — if `log4j-core` is present and SLF4J is not, route directly to Log4j 2 API.
3. **JUL** — fall through to `java.util.logging.Logger`.

Under the hood, `spring-jcl`'s `LogFactory.getLog(Class)` returns one of three `Log` implementations — `Slf4jLog`, `Log4jLog`, or `JavaUtilLog` — each delegating to the corresponding framework.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg">
  <!-- Spring code -->
  <rect x="15" y="80" width="130" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="101" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Framework</text>
  <text x="80" y="117" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">LogFactory.getLog()</text>

  <!-- Arrow -->
  <line x1="145" y1="105" x2="205" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>

  <!-- Spring JCL bridge -->
  <rect x="205" y="75" width="120" height="60" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="265" y="98" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">spring-jcl</text>
  <text x="265" y="115" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">detects classpath</text>
  <text x="265" y="128" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">routes calls</text>

  <!-- Three backends -->
  <line x1="325" y1="95" x2="395" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="325" y1="105" x2="395" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="325" y1="115" x2="395" y2="150" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 2" marker-end="url(#a)"/>

  <rect x="395" y="40" width="100" height="38" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="445" y="63" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">SLF4J + Logback</text>

  <rect x="395" y="86" width="100" height="38" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="445" y="109" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Log4j 2</text>

  <rect x="395" y="132" width="100" height="38" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 2"/>
  <text x="445" y="155" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">JUL (fallback)</text>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>
</svg>

Spring Framework uses the Commons Logging API. Spring JCL intercepts those calls and routes them to the actual backend you configured.

## 5. Runnable example

Scenario: a **minimal Spring context** — first showing default JUL output, then routing through SLF4J + Logback, then configuring log levels for specific Spring packages.

### Level 1 — Basic

Boot a minimal Spring context with no SLF4J on the classpath — Spring JCL falls back to JUL.

```java
// JclDemo.java
import org.springframework.context.annotation.*;

@Configuration
public class JclDemo {
    public static void main(String[] args) {
        // Spring JCL will detect no SLF4J / Log4j2 → falls back to JUL
        // JUL default level is INFO, so you'll see Spring INFO logs
        java.util.logging.Logger root = java.util.logging.Logger.getLogger("");
        root.setLevel(java.util.logging.Level.WARNING); // quiet JUL down for demo

        var ctx = new AnnotationConfigApplicationContext(JclDemo.class);
        // Spring internally calls log.debug("Refreshing...") etc.
        // With level=WARNING those are suppressed
        System.out.println("Context started: " + ctx.getDisplayName());
        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-jcl.jar:. JclDemo.java`

Without SLF4J or Log4j 2 on the classpath, `LogFactory.getLog(…)` returns a `JavaUtilLog` wrapper. Spring's startup messages flow through JUL. Setting the root JUL level to WARNING suppresses Spring's verbose INFO/DEBUG output.

---

### Level 2 — Intermediate

Add SLF4J + Logback. Spring JCL automatically detects SLF4J and routes all `org.springframework.*` log calls to Logback.

```java
// JclDemo.java
// Classpath: spring-context.jar spring-jcl.jar slf4j-api.jar logback-classic.jar
import org.springframework.context.annotation.*;
import org.slf4j.*;

@Configuration
public class JclDemo {
    // Your own code uses SLF4J directly
    private static final Logger log = LoggerFactory.getLogger(JclDemo.class);

    public static void main(String[] args) {
        // Logback auto-configures from logback.xml or logback-test.xml on classpath
        // Spring JCL detects SLF4J → all org.springframework.* calls go to Logback
        log.info("Starting application");
        var ctx = new AnnotationConfigApplicationContext(JclDemo.class);
        log.info("Context ready: {}", ctx.getDisplayName());
        ctx.close();
        log.info("Context closed");
    }
}
```

`logback-test.xml` (place on classpath):
```xml
<configuration>
  <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder><pattern>%d{HH:mm:ss} %-5level %logger{36} - %msg%n</pattern></encoder>
  </appender>
  <logger name="org.springframework" level="WARN"/>
  <root level="INFO"><appender-ref ref="STDOUT"/></root>
</configuration>
```

How to run: `java -cp spring-context.jar:spring-jcl.jar:slf4j-api.jar:logback-classic.jar:. JclDemo.java`

Spring JCL's `LogFactory.getLog(Class)` returns `Slf4jLog` because SLF4J is detected first. All Spring internal `log.debug(…)` / `log.info(…)` calls delegate to SLF4J, which Logback handles. Your `logback.xml` controls levels for `org.springframework.*` the same way it controls any other logger.

---

### Level 3 — Advanced

Demonstrate programmatic log-level control: turn on `DEBUG` for Spring's bean factory during startup to trace bean creation, then restore to INFO. Show the bridging explicitly.

```java
// JclDemo.java
import org.springframework.context.annotation.*;
import org.apache.commons.logging.*;
import ch.qos.logback.classic.*;
import org.slf4j.LoggerFactory;

@Configuration
@ComponentScan
public class JclDemo {

    public static void main(String[] args) throws Exception {
        // 1. Temporarily enable DEBUG for Spring's bean factory
        setLogLevel("org.springframework.beans.factory", Level.DEBUG);

        System.out.println("=== Spring bean factory DEBUG enabled ===");
        var ctx = new AnnotationConfigApplicationContext(JclDemo.class);

        // 2. Restore to WARN after startup
        setLogLevel("org.springframework.beans.factory", Level.WARN);
        System.out.println("=== Log level restored to WARN ===");

        // 3. Show that spring-jcl LogFactory is being used
        Log springLog = LogFactory.getLog(JclDemo.class);
        System.out.println("Log impl: " + springLog.getClass().getName());
        springLog.info("Hello from spring-jcl Log");

        ctx.close();
    }

    static void setLogLevel(String loggerName, Level level) {
        ((Logger) LoggerFactory.getLogger(loggerName)).setLevel(level);
    }
}

@org.springframework.stereotype.Component
class SampleBean {
    SampleBean() { System.out.println("SampleBean created"); }
}
```

How to run: same classpath + logback-classic.jar

During startup, Logback's `org.springframework.beans.factory` logger is set to DEBUG, so you see verbose bean registration messages. After startup it's set back to WARN. The `springLog.getClass().getName()` prints `org.springframework.jcl.Slf4jLog`, confirming the bridge is active.

## 6. Walkthrough

**Detection at class load time:**
When `spring-jcl`'s `LogFactory` is first used, its static initialiser calls `ClassUtils.isPresent("org.slf4j.LoggerFactory", classLoader)`. If true, it stores `"slf4j"` as the active strategy. Detection runs once per `ClassLoader`.

**`LogFactory.getLog(Class)` path (SLF4J detected):**
1. `LogFactory.getLog(MyClass.class)` is called by Spring Framework code.
2. Spring JCL checks the stored strategy: `"slf4j"`.
3. Returns `new Slf4jLog("org.springframework.beans.factory.support.DefaultListableBeanFactory")`.
4. `Slf4jLog.info(msg)` delegates to `slf4jLogger.info(msg)`.
5. SLF4J routes to Logback's logger for that name.
6. Logback checks its configured level — if INFO or lower, appends to the console via the pattern encoder.

**`logback.xml` level hierarchy:**
`org.springframework` set to WARN means all loggers whose name starts with `org.springframework` inherit WARN unless explicitly overridden. `org.springframework.beans.factory` set to DEBUG overrides its subtree. The most specific matching logger wins.

**No `spring-jcl` config needed:**
Spring JCL has no properties file, no `spring-jcl.properties`. It is entirely classpath-driven. You configure Logback (or Log4j 2) as you always have.

**Output excerpt (Level 3, DEBUG on):**
```
=== Spring bean factory DEBUG enabled ===
13:45:01 DEBUG o.s.b.f.s.DefaultListableBeanFactory - Creating shared instance of singleton bean 'sampleBean'
SampleBean created
13:45:01 DEBUG o.s.b.f.s.DefaultListableBeanFactory - Finished creating instance of bean 'sampleBean'
=== Log level restored to WARN ===
Log impl: org.springframework.jcl.Slf4jLog
13:45:01 INFO  com.example.JclDemo - Hello from spring-jcl Log
```

## 7. Gotchas & takeaways

> **Including `commons-logging` JAR alongside `spring-jcl` causes duplicate output.** Spring 5+ ships its own `spring-jcl` which replaces `commons-logging`. If you have `commons-logging` as a transitive dependency (from old libraries), exclude it: `<exclusion><groupId>commons-logging</groupId><artifactId>commons-logging</artifactId></exclusion>`.

> **SLF4J 2.x changed its detection API.** `spring-jcl` targets SLF4J 1.7.x detection. If you use SLF4J 2.x (with Logback 1.4+), Spring 6+ handles it correctly — but Spring 5.x and SLF4J 2.x can produce `NoSuchMethodError`. Match versions.

- You never call `spring-jcl` APIs in your own code — that's for Spring Framework internals. Your application code uses SLF4J's `LoggerFactory` directly.
- `Log` (Commons Logging) and `Logger` (SLF4J) look similar but are different interfaces. `spring-jcl` bridges the former to the latter.
- Spring Boot configures Logback by default via `spring-boot-starter-logging`. You get optimal bridge setup out of the box.
- To see every Spring bean registration, set `org.springframework.beans.factory` to DEBUG — extremely verbose but invaluable for diagnosing wiring issues.
- Log4j 2 direct (without SLF4J) works too: add `log4j-core` and `log4j-api` without SLF4J and Spring JCL routes to Log4j 2 API directly.
