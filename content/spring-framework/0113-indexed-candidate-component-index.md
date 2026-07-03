---
card: spring-framework
gi: 113
slug: indexed-candidate-component-index
title: "@Indexed & candidate component index"
---

## 1. What it is

`@Indexed` (Spring 5+) is an annotation that triggers compile-time generation of a **candidate component index** file (`META-INF/spring.components`). At startup, Spring reads this index instead of scanning the classpath, making application startup significantly faster in large codebases.

Without the index, Spring's component scanner walks every `.class` file in the scan path at runtime using ASM. With the index, it reads a pre-built list of candidates — O(n) classpath walk becomes O(1) file read.

## 2. Why & when

Use `@Indexed` and the component index when:

- Your application has **hundreds or thousands of classes** in the scan path — startup time noticeably improves.
- You're building a **library** that ships `@Component`-annotated classes — add the index so consuming applications don't have to scan your JAR.
- You need **predictable startup time** (containerised environments, lambda cold starts, test suite spin-up).

The feature is opt-in: existing code without `@Indexed` continues to work exactly as before — the index is simply never consulted. Adding `@Indexed` requires `spring-context-indexer` on the **annotation processor** classpath (Maven `provided` / Gradle `compileOnly`).

## 3. Core concept

At compile time, `spring-context-indexer` (an annotation processor) scans source files, finds all classes annotated with `@Indexed` or stereotypes that are themselves `@Indexed` (e.g., `@Component` is meta-annotated with `@Indexed`), and writes entries to `META-INF/spring.components` inside the JAR.

Each entry is:
```
com.example.UserService=org.springframework.stereotype.Component
```
Key = fully qualified class name, value = the stereotype annotation.

At runtime, `ClassPathScanningCandidateComponentProvider` checks whether `META-INF/spring.components` exists. If it does, it uses the index directly — no classpath walking. If the index is absent or incomplete, it falls back to the standard bytecode scan.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Compile time -->
  <rect x="10" y="30" width="180" height="54" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="100" y="53" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Compile time</text>
  <text x="100" y="69" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">spring-context-indexer</text>

  <!-- Index file -->
  <rect x="10" y="105" width="180" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="100" y="128" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">spring.components</text>
  <text x="100" y="142" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">META-INF/</text>

  <!-- Runtime -->
  <rect x="300" y="30" width="170" height="54" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="385" y="53" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Runtime scan</text>
  <text x="385" y="69" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">reads index → skips walk</text>

  <!-- Context -->
  <rect x="560" y="30" width="130" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="625" y="53" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Context ready</text>
  <text x="625" y="69" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">faster startup</text>

  <line x1="100" y1="84" x2="100" y2="103" stroke="#6db33f" stroke-width="2" marker-end="url(#a113)"/>
  <line x1="192" y1="127" x2="297" y2="57" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a113)"/>
  <line x1="472" y1="57" x2="557" y2="57" stroke="#79c0ff" stroke-width="2" marker-end="url(#b113)"/>
  <defs>
    <marker id="a113" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b113" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="175" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Index generated at compile time; consumed at runtime — no classpath walk needed</text>
</svg>

The annotation processor pre-builds the bean list at compile time so Spring doesn't scan at runtime.

## 5. Runnable example

### Level 1 — Basic

Show the `@Indexed` annotation and what goes into the index file, simulating what the annotation processor generates.

```java
// IndexedBasic.java
import org.springframework.context.annotation.*;
import org.springframework.context.index.CandidateComponentsIndexLoader;
import org.springframework.stereotype.*;

// In real projects these would be in a Maven/Gradle project
// with spring-context-indexer on the annotation processor classpath.
// The annotation processor writes META-INF/spring.components at compile time.
// Here we demonstrate the annotation and how to query the index programmatically.

@Service   // @Service is meta-annotated with @Indexed in spring-context
class OrderService {
    public String process(int id) { return "Order#" + id + " processed"; }
}

@Repository
class OrderRepository {
    public String find(int id) { return "Order#" + id; }
}

@Configuration
@ComponentScan(basePackageClasses = IndexedBasic.class)
class IdxCfg {}

public class IndexedBasic {
    public static void main(String[] args) {
        // Check if a spring.components index is available
        var index = CandidateComponentsIndexLoader.loadIndex(IndexedBasic.class.getClassLoader());
        if (index != null) {
            System.out.println("Index available — candidates for @Component:");
            index.getCandidateTypes(IndexedBasic.class.getPackageName(),
                                    "org.springframework.stereotype.Component")
                 .forEach(c -> System.out.println("  " + c));
        } else {
            System.out.println("No spring.components index found — falling back to classpath scan.");
            System.out.println("(Normal without spring-context-indexer annotation processor)");
        }

        // Context still works regardless — fallback scan happens automatically
        var ctx = new AnnotationConfigApplicationContext(IdxCfg.class);
        System.out.println(ctx.getBean(OrderService.class).process(42));
        ctx.close();
    }
}
```

How to run: `java IndexedBasic.java`

Without `spring-context-indexer` on the annotation processor classpath, no index file exists and the message confirms the scanner falls back. In a real Maven/Gradle build with the processor configured, `META-INF/spring.components` is generated at compile time and the index path is taken at startup.

### Level 2 — Intermediate

Simulate what the index file contains and how Spring uses it, by writing `META-INF/spring.components` manually and verifying Spring picks it up.

```java
// IndexedSimulated.java
import org.springframework.context.annotation.*;
import org.springframework.context.index.CandidateComponentsIndex;
import org.springframework.context.index.CandidateComponentsIndexLoader;
import org.springframework.stereotype.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;

@Service class PaymentService  { public String pay()  { return "PaymentService.pay()";  } }
@Service class ShippingService { public String ship() { return "ShippingService.ship()"; } }

@Configuration
@ComponentScan(basePackageClasses = IndexedSimulated.class)
class SimIdxCfg {}

public class IndexedSimulated {
    public static void main(String[] args) throws Exception {
        // Manually write a spring.components file to a temp directory
        var dir = Files.createTempDirectory("spring-idx");
        var metaInf = dir.resolve("META-INF");
        Files.createDirectories(metaInf);
        var indexFile = metaInf.resolve("spring.components");

        Files.writeString(indexFile,
            "PaymentService=org.springframework.stereotype.Component\n" +
            "ShippingService=org.springframework.stereotype.Component\n");
        System.out.println("Written index to: " + indexFile);

        // Load it with a custom classloader that includes the temp dir
        var loader = new URLClassLoader(new URL[]{dir.toUri().toURL()},
                                         IndexedSimulated.class.getClassLoader());
        var index = CandidateComponentsIndexLoader.loadIndex(loader);

        if (index != null) {
            System.out.println("Index loaded. Package candidates:");
            // In a real app the package would be the actual package name
            index.getCandidateTypes("", "org.springframework.stereotype.Component")
                 .forEach(c -> System.out.println("  " + c));
        }

        // The actual Spring context still uses the scan (the written index uses bare class names)
        var ctx = new AnnotationConfigApplicationContext(SimIdxCfg.class);
        System.out.println(ctx.getBean(PaymentService.class).pay());
        System.out.println(ctx.getBean(ShippingService.class).ship());
        ctx.close();

        loader.close();
    }
}
```

How to run: `java IndexedSimulated.java`

Writing `META-INF/spring.components` manually shows the exact file format the annotation processor generates. `CandidateComponentsIndexLoader` reads it; the `getCandidateTypes` call shows the indexed class names.

### Level 3 — Advanced

Show the startup-time benefit with a timing comparison — scanning 50 classes with and without an index, using `ClassPathScanningCandidateComponentProvider` directly.

```java
// IndexedPerf.java
import org.springframework.context.annotation.*;
import org.springframework.beans.factory.support.*;
import org.springframework.stereotype.*;

// 10 representative "application classes" — in a real app there'd be hundreds
@Service class S1{} @Service class S2{} @Service class S3{} @Service class S4{} @Service class S5{}
@Repository class R1{} @Repository class R2{} @Repository class R3{}
@Component class C1{} @Component class C2{}

@Configuration
@ComponentScan(basePackageClasses = IndexedPerf.class)
class PerfCfg {}

public class IndexedPerf {
    public static void main(String[] args) {
        System.out.println("=== Without index (classpath scan) ===");
        long t0 = System.nanoTime();
        var factory = new DefaultListableBeanFactory();
        var scanner = new ClassPathBeanDefinitionScanner(factory);
        int count = scanner.scan(IndexedPerf.class.getPackageName());
        long t1 = System.nanoTime();
        System.out.printf("Scanned %d beans in %.1f ms%n", count, (t1-t0)/1_000_000.0);

        System.out.println("\n=== Full ApplicationContext startup ===");
        long t2 = System.nanoTime();
        var ctx = new AnnotationConfigApplicationContext(PerfCfg.class);
        long t3 = System.nanoTime();
        System.out.printf("Context ready (%d beans) in %.1f ms%n",
            ctx.getBeanDefinitionCount(), (t3-t2)/1_000_000.0);

        // In a real project with spring-context-indexer, the scan phase
        // is replaced by a file read — typically 5–20x faster at scale.
        System.out.println("\nWith spring-context-indexer configured in Maven/Gradle,");
        System.out.println("the scan phase is replaced by reading META-INF/spring.components");
        System.out.println("— typically 5–20x faster for projects with 500+ classes.");
        ctx.close();
    }
}
```

How to run: `java IndexedPerf.java`

The output shows current scan timing. In a real project with the annotation processor configured, the scan phase is eliminated and startup time drops proportionally to classpath size.

## 6. Walkthrough

How the index is used at runtime when available:

1. **`AnnotationConfigApplicationContext` created** → triggers `ClassPathScanningCandidateComponentProvider`.
2. **Provider calls `CandidateComponentsIndexLoader.loadIndex(classLoader)`** — looks for `META-INF/spring.components` on the classpath.
3. **Index found** → instead of walking `scan/basePackage/**/*.class`, reads the index file entries for the relevant package prefix.
4. **For each indexed entry** — loads only the candidate class names listed in the index. No ASM scan of unrelated classes.
5. **Filters still applied** — include/exclude filters run on the indexed candidates, same as without index.
6. **`BeanDefinition`s registered** — result is identical to a full scan; only the discovery phase is faster.

Expected output for Level 3 (representative timing):
```
=== Without index (classpath scan) ===
Scanned 10 beans in 8.3 ms

=== Full ApplicationContext startup ===
Context ready (17 beans) in 14.2 ms

With spring-context-indexer configured in Maven/Gradle,
the scan phase is replaced by reading META-INF/spring.components
— typically 5–20x faster for projects with 500+ classes.
```

## 7. Gotchas & takeaways

> If you add `spring-context-indexer` to the annotation processor but some classes in the scan path do **not** have `@Indexed` (or a stereotype that carries it), those classes are absent from the index and **will not be discovered** at runtime. This causes silent missing-bean failures. Either index all candidates or set `spring.index.ignore=true` to disable the index and fall back to scanning.

> The index is **not dynamic** — if you add a class after the JAR is built without rebuilding, the new class won't be in the index. Always rebuild when adding annotated classes in index-enabled projects.

- `@Component`, `@Service`, `@Repository`, `@Controller` are all meta-annotated with `@Indexed` in Spring 5+ — you don't need to add `@Indexed` separately to classes using standard stereotypes.
- Add `@Indexed` explicitly on custom annotations that you want indexed when they're used as stereotypes.
- Add the indexer to Maven: `<annotationProcessorPaths>` or Gradle `annotationProcessor 'org.springframework:spring-context-indexer'`.
- To disable index lookup: `spring.index.ignore=true` in `spring.properties` on the classpath.
- Spring Boot 2.7+ uses the index automatically when the indexer is on the annotation processor path.
