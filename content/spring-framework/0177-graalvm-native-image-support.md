---
card: spring-framework
gi: 177
slug: graalvm-native-image-support
title: GraalVM native image support
---

## 1. What it is

**GraalVM native image** is a technology that compiles a Java application ahead-of-time into a standalone native binary. The binary contains the application code, its dependencies, and a minimal runtime (Substrate VM) — but no full JVM.

Spring Boot 3+ provides first-class native image support:

```xml
<!-- pom.xml — native Maven plugin -->
<plugin>
  <groupId>org.graalvm.buildtools</groupId>
  <artifactId>native-maven-plugin</artifactId>
</plugin>
```

Build command:
```bash
./mvnw -Pnative native:compile
# produces: target/<app-name>  (native binary)
./target/<app-name>             # starts in < 100 ms
```

The resulting binary is a single executable with no JVM dependency; it can be copied into a `FROM scratch` Docker image.

## 2. Why & when

- **Serverless / FaaS** (AWS Lambda, Google Cloud Functions, Knative) — cold start latency directly affects cost and latency. Native images start in under 100ms vs 3–10s for JVM.
- **Kubernetes density** — native binaries use 30–70% less RSS memory than equivalent JVM processes; more pods fit on the same node.
- **Distroless / minimal containers** — native binary + `FROM scratch` = tiny, attack-surface-free images (no `bash`, no JRE).
- **CLI tools** — Spring Shell or Picocli apps distributed as binaries (`graal-native` as replacement for Go binaries).
- **Avoid** when: the app uses heavy runtime reflection/dynamic class loading (common with some JPA providers, CGLIB patterns, or legacy libraries without native support), or when build-time overhead in CI is unacceptable.

## 3. Core concept

The `native-image` tool performs **closed-world static analysis** from `main()`:

1. Follows every reachable method call, field access, and resource reference transitively.
2. Includes every reachable class in the native binary.
3. Anything NOT reachable at build time is absent from the binary — including classes discovered only at runtime via `Class.forName()` or `getDeclaredMethod()`.

This is why **hints** are required for dynamic features: you must tell `native-image` what classes/methods/resources will be needed at runtime even if static analysis can't see them.

Spring Boot 3's AOT engine generates these hints automatically for standard Spring patterns. Libraries must also provide their own hints (via `RuntimeHintsRegistrar`).

**Build-time steps:**
```
Source code + dependencies
      │
      ▼ ./mvnw spring-boot:process-aot
Generated __BeanDefinitions.java + reflect-config.json + resource-config.json
      │
      ▼ ./mvnw -Pnative native:compile  (invokes native-image internally)
Native binary  (self-contained executable)
```

**Runtime behaviour:**
- No JVM boot.
- Spring uses the AOT-generated `ApplicationContextInitializer`.
- No classpath scanning or reflection for wired beans.
- Resources listed in `resource-config.json` are embedded in the binary.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="na177" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="nb177" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Build pipeline -->
  <rect x="5" y="5" width="690" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="23" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Build Pipeline</text>

  <rect x="15"  y="32" width="100" height="30" rx="4" fill="#6db33f" opacity="0.2"/>
  <text x="65"  y="51" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Your source</text>
  <line x1="116" y1="47" x2="136" y2="47" stroke="#6db33f" stroke-width="1.5" marker-end="url(#na177)"/>

  <rect x="138" y="32" width="100" height="30" rx="4" fill="#6db33f" opacity="0.2"/>
  <text x="188" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">javac</text>
  <text x="188" y="57" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">.class files</text>
  <line x1="239" y1="47" x2="259" y2="47" stroke="#6db33f" stroke-width="1.5" marker-end="url(#na177)"/>

  <rect x="261" y="32" width="125" height="30" rx="4" fill="#6db33f" opacity="0.3"/>
  <text x="323" y="47" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">spring-boot:process-aot</text>
  <text x="323" y="57" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">__BeanDefs + hints</text>
  <line x1="387" y1="47" x2="407" y2="47" stroke="#6db33f" stroke-width="1.5" marker-end="url(#na177)"/>

  <rect x="409" y="32" width="130" height="30" rx="4" fill="#6db33f" opacity="0.3"/>
  <text x="474" y="47" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">native-image tool</text>
  <text x="474" y="57" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">static analysis + compile</text>
  <line x1="540" y1="47" x2="560" y2="47" stroke="#6db33f" stroke-width="1.5" marker-end="url(#na177)"/>

  <rect x="562" y="32" width="120" height="30" rx="4" fill="#6db33f" opacity="0.4"/>
  <text x="622" y="47" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Native binary</text>
  <text x="622" y="57" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">standalone executable</text>

  <text x="350" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Total build time: minutes (CI). Output: single binary, no JRE needed.</text>

  <!-- Runtime comparison -->
  <rect x="5" y="120" width="340" height="105" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="175" y="138" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">JVM Docker image</text>
  <text x="175" y="155" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">FROM eclipse-temurin:21  (~200MB base)</text>
  <text x="175" y="170" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">COPY target/app.jar /app.jar</text>
  <text x="175" y="185" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ENTRYPOINT ["java","-jar","/app.jar"]</text>
  <text x="175" y="200" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Image: ~250MB | Start: 1–3s | RSS: 200MB+</text>

  <rect x="360" y="120" width="335" height="105" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="527" y="138" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Native Docker image</text>
  <text x="527" y="155" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">FROM scratch</text>
  <text x="527" y="170" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">COPY target/app /app</text>
  <text x="527" y="185" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ENTRYPOINT ["/app"]</text>
  <text x="527" y="200" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Image: ~60MB | Start: &lt;100ms | RSS: 50–80MB</text>
</svg>

The same Spring Boot source produces two deployment artefacts: a fat JAR for JVM and a native binary for GraalVM — both built from the same codebase.

## 5. Runnable example

The scenario is a **product catalogue service** — growing from a standard Spring app, to configuring the native build profile, to adding native-image–specific customisation.

### Level 1 — Basic

A runnable Spring Boot REST service — the starting point before adding native support.

```java
// NativeImageBasic.java — Spring Boot web service (JVM run)
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.stereotype.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;

record Product(String id, String name, double price) {}

@Service
class ProductCatalog {
    private final List<Product> products = List.of(
        new Product("p1", "Laptop",  1200.0),
        new Product("p2", "Phone",    800.0),
        new Product("p3", "Tablet",   400.0)
    );
    public List<Product> findAll()             { return products; }
    public Optional<Product> findById(String id) {
        return products.stream().filter(p -> p.id().equals(id)).findFirst();
    }
}

@RestController
@RequestMapping("/products")
class ProductController {
    private final ProductCatalog catalog;
    ProductController(ProductCatalog catalog) { this.catalog = catalog; }

    @GetMapping
    public List<Product> list() { return catalog.findAll(); }

    @GetMapping("/{id}")
    public Product get(@PathVariable String id) {
        return catalog.findById(id)
            .orElseThrow(() -> new RuntimeException("Product not found: " + id));
    }
}

@SpringBootApplication
public class NativeImageBasic {
    public static void main(String[] args) {
        SpringApplication.run(NativeImageBasic.class, args);
    }
}
```

How to run: `./mvnw spring-boot:run` (JVM) or test with `curl localhost:8080/products`

This is a standard Spring Boot 3 app. No special native configuration is needed beyond adding `native-maven-plugin` to `pom.xml` — Spring Boot's autoconfiguration is fully native-ready out of the box for standard patterns.

### Level 2 — Intermediate

Add the native build profile to `pom.xml` and verify the AOT-generated sources.

```java
// NativeImageIntermediate.java — same service, now with programmatic AOT verification
import org.springframework.aot.hint.*;
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.stereotype.*;

// Verify reflection hints are generated for the Product record
@SpringBootApplication
public class NativeImageIntermediate {
    public static void main(String[] args) {
        var app = new SpringApplication(NativeImageIntermediate.class);
        app.run(args);
    }
}

// RuntimeHints test (run with SpringApplicationTests or standalone)
// This verifies hints at build/test time, not at native run time.
@org.springframework.context.annotation.Configuration
class HintsVerifier {
    @org.springframework.context.annotation.Bean
    public String verifyHints(RuntimeHints hints) {
        // After process-aot, check reflect-config.json includes Product
        // In practice: use RuntimeHintsPredicates in @SpringBootTest
        boolean isNative = System.getProperty(
            "org.graalvm.nativeimage.imagecode") != null;
        System.out.println("Running as native image: " + isNative);
        return "verified";
    }
}

/*  pom.xml additions (not runnable Java — reference only):

<profiles>
  <profile>
    <id>native</id>
    <build>
      <plugins>
        <plugin>
          <groupId>org.graalvm.buildtools</groupId>
          <artifactId>native-maven-plugin</artifactId>
          <executions>
            <execution>
              <id>build-native</id>
              <goals><goal>compile-no-fork</goal></goals>
              <phase>package</phase>
            </execution>
          </executions>
        </plugin>
      </plugins>
    </build>
  </profile>
</profiles>
*/
```

How to run (JVM): `./mvnw spring-boot:run`

How to run (native): `./mvnw -Pnative native:compile && ./target/native-image-intermediate`

After `spring-boot:process-aot`, inspect `target/spring-aot/main/resources/META-INF/native-image/reflect-config.json` — you will find entries for `Product`, `ProductCatalog`, `ProductController`, and Spring's internal classes. The `native-maven-plugin` feeds these into `native-image` automatically.

### Level 3 — Advanced

Custom `native-image.properties` options, build-time initialisation, and a multi-stage Docker build producing a distroless image.

```java
// NativeImageAdvanced.java — production-grade native Spring Boot app
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@Service
class ConfigLoader {
    private final Map<String, String> config;
    ConfigLoader() {
        // Loaded at init-time; native image can initialise this at build time
        // with @BuildTimeInitialization if the data is truly static
        config = Map.of("version", "3.2.0", "env", "prod");
        System.out.println("ConfigLoader initialised");
    }
    public String get(String key) { return config.getOrDefault(key, "?"); }
}

@RestController
class InfoController {
    private final ConfigLoader cfg;
    InfoController(ConfigLoader cfg) { this.cfg = cfg; }
    @GetMapping("/info")
    public Map<String, String> info() {
        return Map.of(
            "version", cfg.get("version"),
            "native",  String.valueOf(
                System.getProperty("org.graalvm.nativeimage.imagecode") != null)
        );
    }
}

@SpringBootApplication
public class NativeImageAdvanced {
    public static void main(String[] args) {
        SpringApplication.run(NativeImageAdvanced.class, args);
    }
}

/*  Multi-stage Dockerfile (reference — not Java):

# Stage 1: build native binary
FROM ghcr.io/graalvm/native-image-community:21 AS builder
WORKDIR /app
COPY . .
RUN ./mvnw -Pnative native:compile -DskipTests

# Stage 2: minimal runtime image
FROM scratch
COPY --from=builder /app/target/native-image-advanced /app
ENTRYPOINT ["/app"]
# Final image: ~60MB, no shell, no JRE, no attack surface
*/
```

How to run: `./mvnw -Pnative native:compile && ./target/native-image-advanced`

The multi-stage Dockerfile uses GraalVM CE 21 for building (the JDK + native-image tool is large) and `FROM scratch` for the runtime layer — only the native binary is copied. `org.graalvm.nativeimage.imagecode` is a system property set automatically inside a native image; it is `null` on JVM and `"runtime"` inside a native binary, letting code detect its execution environment.

## 6. Walkthrough

Tracing `./mvnw -Pnative native:compile` for the Level 3 app:

**Step 1 — `spring-boot:process-aot` (triggered by native profile):**
- Spring starts an analysis-only context.
- AOT processors run over `ConfigLoader`, `InfoController`, `NativeImageAdvanced`.
- Generates `ConfigLoader__BeanDefinitions.java`, `InfoController__BeanDefinitions.java`.
- Generates `reflect-config.json` with entries for all beans and Jackson serialisation targets.
- Outputs to `target/spring-aot/main/`.

**Step 2 — Compile generated sources:**
- `javac` compiles everything in `src/` AND `target/spring-aot/main/sources/` together.
- Output: `.class` files in `target/classes/`.

**Step 3 — `native-image` tool runs:**
- Entry point: `NativeImageAdvanced.main`.
- Loads `reflect-config.json` from `META-INF/native-image/`.
- Performs closed-world analysis: follows `main → SpringApplication.run → context init → ConfigLoader.<init> → Map.of → …`.
- Includes all reachable classes and their reachable members.
- Compiles to native machine code: LLVM-based backend emits object files, links into a native binary.

**Step 4 — Native binary is ready (`./target/native-image-advanced`):**

**Step 5 — Running `./target/native-image-advanced`:**
- No JVM startup.
- Substrate VM (minimal runtime) initialises.
- Spring's generated `ApplicationContextInitializer.initialize()` is called — registers `ConfigLoader` and `InfoController` via their suppliers, no reflection.
- `ConfigLoader()` constructor runs — "ConfigLoader initialised" is printed.
- Tomcat starts, HTTP listener bound.
- **Total elapsed: < 100ms.**

**Request `GET /info`:**
```
→  InfoController.info()
→  cfg.get("version") → "3.2.0"
→  System.getProperty("org.graalvm.nativeimage.imagecode") → "runtime" (non-null)
← {"version":"3.2.0","native":"true"}
```

## 7. Gotchas & takeaways

> **Third-party libraries without native support will break at runtime, not build time.** The binary compiles successfully, but `Class.forName("com.vendor.Driver")` at runtime throws `ClassNotFoundException` because the class was not in the static reachability closure. Always run native integration tests (`@SpringBootTest` with `spring.aot.enabled=true`) in CI to catch missing hints early.

> **`@ConditionalOnProperty` beans excluded at AOT time are gone forever.** If a property is absent when `process-aot` runs, the bean is not included in the generated initialiser. Set required properties in your CI build environment during the AOT step, or use `spring.aot.conditions.enabled=false` during development to include all beans unconditionally.

- GraalVM CE (free) supports native image; GraalVM EE (paid) produces more optimised binaries.
- `native-image` build time is 2–10 minutes depending on app size; cache the output in CI.
- `./mvnw -Pnative native:test` runs your test suite against the native binary — essential for catching reflection gaps.
- Heap is pre-sized at build time via `-R:MaxHeap`; add `springAot.properties` or `native-image.properties` in `META-INF/native-image/` for custom flags.
- Spring Boot's `spring-boot-starter-actuator` adds a `/actuator/health` endpoint that is native-ready; other actuators may need additional hints.
