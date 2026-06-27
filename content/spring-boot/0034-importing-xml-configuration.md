---
card: spring-boot
gi: 34
slug: importing-xml-configuration
title: Importing XML configuration
---

## 1. What it is

**Importing XML configuration** means bringing a legacy Spring XML bean definition file (e.g. `applicationContext.xml`) into a modern Spring Boot application that otherwise uses Java-based configuration. The bridge is the `@ImportResource` annotation, placed on a `@Configuration` class.

```java
@SpringBootApplication
@ImportResource("classpath:legacy-beans.xml")
public class MyApp {
    public static void main(String[] args) {
        SpringApplication.run(MyApp.class, args);
    }
}
```

Spring Boot reads the XML file and registers every `<bean>` defined in it alongside the beans discovered by component scanning and `@Configuration` classes.

## 2. Why & when

Spring started as an XML-first framework (2003). Many production codebases still have thousands of lines of XML configuration accumulated over years. When upgrading such a project to Spring Boot, rewriting all XML at once is risky — `@ImportResource` lets you migrate **incrementally**: keep existing XML working, and add new code in Java.

Use `@ImportResource` when:
- Migrating a legacy Spring app to Spring Boot without a big-bang rewrite.
- A third-party library ships bean definitions in XML that you cannot change.
- You have specialised XML-only features like Spring Integration or Spring Batch XML DSL flows.

Avoid it for new development — Java configuration is type-safe, IDE-navigable, and easier to test.

## 3. Core concept

Think of the Spring application context as a bucket of beans. Normally Spring Boot fills it from two sources: **component scanning** (finds `@Component`-annotated classes) and **`@Configuration` classes** (finds `@Bean` methods). `@ImportResource` opens a third pipe that reads an XML file and pours its bean definitions into the same bucket.

The XML file follows the classic Spring schema:

```xml
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="...">
    <bean id="legacyService" class="com.example.LegacyService"/>
</beans>
```

Important rules:
1. The path prefix matters: `classpath:` looks in `src/main/resources`; `file:` uses the filesystem.
2. Multiple files can be imported: `@ImportResource({"classpath:a.xml", "classpath:b.xml"})`.
3. All beans from the XML are treated identically to beans from Java config — they participate in autowiring, `@Autowired` injection, and `@Bean` method injection.

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@ImportResource merging XML beans into the Spring application context alongside Java beans">
  <!-- Application context -->
  <rect x="20" y="20" width="620" height="220" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="48" fill="#6db33f" font-size="13" font-family="sans-serif" font-weight="bold" text-anchor="middle">Spring Application Context</text>

  <!-- Java config source -->
  <rect x="40" y="64" width="200" height="64" rx="7" fill="#2d3748" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="90" fill="#79c0ff" font-size="12" font-family="monospace" text-anchor="middle">@SpringBootApplication</text>
  <text x="140" y="110" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">@ImportResource(…)</text>

  <!-- XML source -->
  <rect x="420" y="64" width="200" height="64" rx="7" fill="#2d3748" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="520" y="90" fill="#79c0ff" font-size="12" font-family="monospace" text-anchor="middle">legacy-beans.xml</text>
  <text x="520" y="110" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">&lt;bean id="legacySvc"…&gt;</text>

  <!-- Bean pool -->
  <rect x="140" y="158" width="380" height="60" rx="7" fill="#16202e" stroke="#6db33f" stroke-width="1"/>
  <text x="330" y="182" fill="#e6edf3" font-size="12" font-family="monospace" text-anchor="middle">Bean pool</text>
  <text x="330" y="202" fill="#8b949e" font-size="11" font-family="sans-serif" text-anchor="middle">javaBean  +  legacySvc  →  autowired together</text>

  <!-- Arrows -->
  <line x1="180" y1="128" x2="260" y2="158" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="480" y1="128" x2="400" y2="158" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

Both Java-config beans and XML beans end up in the same context and can be injected into each other.

## 5. Runnable example

```java
// XmlImportDemo.java
// How to run: java XmlImportDemo.java  (JDK 17+)
// Shows how @ImportResource merges XML-defined beans with Java-defined beans.
// (No Spring on classpath needed — this is a pure-Java simulation.)

import java.util.*;

// Simulate bean registry
public class XmlImportDemo {

    record BeanDef(String id, String className, String source) {}

    public static void main(String[] args) {
        List<BeanDef> context = new ArrayList<>();

        // ── Step 1: Java @Configuration beans (discovered by component scan) ──
        List<BeanDef> javaBeans = List.of(
            new BeanDef("appService",  "com.example.AppService",  "Java @Bean"),
            new BeanDef("webClient",   "com.example.WebClient",   "Java @Bean")
        );
        System.out.println("=== Loading Java @Configuration beans ===");
        for (BeanDef b : javaBeans) {
            context.add(b);
            System.out.println("  + " + b.id() + " (" + b.source() + ")");
        }

        // ── Step 2: @ImportResource reads legacy-beans.xml ─────────────────
        // In a real app Spring parses the XML; here we simulate the parsed output.
        List<BeanDef> xmlBeans = List.of(
            new BeanDef("legacyService", "com.example.LegacyService", "XML <bean>"),
            new BeanDef("legacyDao",     "com.example.LegacyDao",     "XML <bean>")
        );
        System.out.println("\n=== Loading XML beans via @ImportResource(\"classpath:legacy-beans.xml\") ===");
        for (BeanDef b : xmlBeans) {
            context.add(b);
            System.out.println("  + " + b.id() + " (" + b.source() + ")");
        }

        // ── Step 3: All beans available in the same context ─────────────────
        System.out.println("\n=== Final application context (" + context.size() + " beans) ===");
        for (BeanDef b : context) {
            System.out.printf("  %-18s → %-40s [%s]%n", b.id(), b.className(), b.source());
        }

        System.out.println("\n✅ Java beans can @Autowired XML beans and vice versa.");
    }
}
```

**How to run:** `java XmlImportDemo.java`

Expected output:
```
=== Loading Java @Configuration beans ===
  + appService (Java @Bean)
  + webClient (Java @Bean)

=== Loading XML beans via @ImportResource("classpath:legacy-beans.xml") ===
  + legacyService (XML <bean>)
  + legacyDao (XML <bean>)

=== Final application context (4 beans) ===
  appService         → com.example.AppService                  [Java @Bean]
  webClient          → com.example.WebClient                   [Java @Bean]
  legacyService      → com.example.LegacyService               [XML <bean>]
  legacyDao          → com.example.LegacyDao                   [XML <bean>]

✅ Java beans can @Autowired XML beans and vice versa.
```

## 6. Walkthrough

- `javaBeans` represents what Spring Boot discovers via component scanning and `@Configuration` classes — these are the modern beans.
- `xmlBeans` represents what Spring parses from the XML file named in `@ImportResource`. Each `<bean id="..." class="...">` element becomes one entry.
- Both lists are added to the same `context` list, mirroring the real Spring application context where all beans share one registry regardless of origin.
- The final printout shows four beans, each labelled by source — in a real Spring Boot app you can `@Autowired legacyService` into a Java-config bean or `<property ref="appService"/>` in XML; Spring resolves cross-source references transparently.
- The note at the end is the key point: the context is unified. There is no "XML context" vs "Java context" — it is one bucket.

## 7. Gotchas & takeaways

> XML bean IDs must not clash with Java bean names. If a `<bean id="dataSource">` in XML and a `@Bean` named `dataSource` in Java both exist, the **later-processed one wins** and silently overrides the first. This is a subtle bug during migration.

> The classpath prefix `classpath:` is relative to the root of the classpath (your `src/main/resources` directory in a Maven/Gradle project). A common mistake is specifying a path like `classpath:config/beans.xml` when the file is actually at `src/main/resources/beans.xml` — move the file or fix the path.

- `@ImportResource` is an incremental migration tool, not a permanent design goal. Remove it once all XML beans are migrated to Java.
- Multiple XML files: `@ImportResource({"classpath:a.xml", "classpath:b.xml"})` — all are merged.
- XML supports property placeholders (`${db.url}`) and Spring EL — both work alongside `@Value` in Java config.
- If your XML uses `<context:component-scan>`, it may double-register beans already found by Spring Boot's auto-scan. Add `default-lazy-init="true"` to XML or remove the redundant scan.
- In tests, `@SpringBootTest` picks up `@ImportResource` from the main class automatically — no extra annotation needed.
