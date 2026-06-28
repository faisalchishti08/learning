---
card: spring-boot
gi: 249
slug: testing-aot-native
title: Testing AOT / native
---

## 1. What it is

**Testing AOT / native** means verifying that your application works correctly when compiled as a GraalVM native image — not just on the regular JVM. Spring Boot provides two complementary mechanisms:

1. **AOT test processing** (`spring-boot:process-test-aot` / `processTestAot`) — applies the AOT pipeline to your test sources, generating registrars and hints for test beans. Tests run on the JVM but use the AOT-compiled bean wiring, catching AOT-specific issues early without a full native compile.

2. **`nativeTest`** (Maven `-PnativeTest test` / Gradle `nativeTest` task) — compiles your test suite to a native executable and runs it. This is the gold standard: it exercises the exact binary your users will run.

Both leverage GraalVM Native Build Tools' test support (`native-maven-plugin`/`org.graalvm.buildtools.native`).

## 2. Why & when

Tests that pass on the JVM can fail on native because:

- A library uses reflection that lacks native hints.
- A `@Bean` is conditionally created based on runtime class presence, but the condition resolved differently at AOT build time.
- `@TestConfiguration` beans rely on runtime proxy generation that native images don't support.
- Resource files are loaded dynamically and not included in the native image.

Use **AOT test mode** during normal development — it's fast (no native compilation) and catches most issues. Use **`nativeTest`** on CI / pre-release — it's slow (5–15 min compile) but definitive.

## 3. Core concept

Think of it as three test layers:

| Layer | What runs | Catches |
|---|---|---|
| JVM tests | Normal JVM, reflection works | Logic bugs |
| AOT JVM tests | JVM + AOT-generated wiring, no native compile | Bean wiring issues, AOT processing bugs |
| `nativeTest` | True native binary, no JVM | Reflection gaps, resource misses, proxy failures |

Spring's `@SpringBootTest` works in all three modes. The test picks up the AOT-generated application context automatically when `spring.aot.enabled=true` is set, which the AOT test processing phase does for you.

Key annotation: `@DisabledInNativeImage` — skip tests that can't work in native mode (e.g., tests that use Mockito dynamic proxies) rather than breaking the entire native test suite.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three testing layers: JVM, AOT-JVM, and native test modes">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Layer 1: JVM -->
  <rect x="15" y="30" width="190" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">JVM Tests</text>
  <text x="110" y="73" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">mvn test</text>
  <text x="110" y="89" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Fast, catches logic bugs</text>

  <!-- Layer 2: AOT JVM -->
  <rect x="255" y="30" width="190" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">AOT JVM Tests</text>
  <text x="350" y="73" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">process-test-aot + test</text>
  <text x="350" y="89" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Catches AOT wiring issues</text>

  <!-- Layer 3: nativeTest -->
  <rect x="495" y="30" width="190" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="590" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Native Tests</text>
  <text x="590" y="73" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">nativeTest (slow)</text>
  <text x="590" y="89" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Catches reflection gaps</text>

  <!-- coverage arrows -->
  <rect x="15" y="130" width="190" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="110" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">~seconds</text>

  <rect x="255" y="130" width="190" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="350" y="150" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">~minutes (extra AOT phase)</text>

  <rect x="495" y="130" width="190" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="590" y="150" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">5–15 min (native compile)</text>

  <text x="350" y="210" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Run all three on CI; use JVM tests locally for development speed</text>
</svg>

Each layer catches different failure modes; running all three gives complete coverage.

## 5. Runnable example

```java
// TestingAotNativeDemo.java — run with: java TestingAotNativeDemo.java
// Shows the Maven/Gradle commands, annotation usage, and common patterns
// for testing Spring Boot apps in AOT and native modes.

public class TestingAotNativeDemo {

    public static void main(String[] args) {
        System.out.println("=== Testing AOT / Native in Spring Boot ===\n");
        printCommands();
        printTestExamples();
        printCommonFailures();
    }

    static void printCommands() {
        System.out.println("--- Build & test commands ---");
        System.out.println("""
            # 1. Normal JVM tests (fast — use during development)
            mvn test

            # 2. AOT-mode JVM tests (medium — catches AOT wiring issues)
            mvn -Pnative spring-boot:process-test-aot test

            # 3. Native tests (slow — definitive; run on CI)
            mvn -PnativeTest test

            # Gradle equivalents:
            ./gradlew test                  # JVM
            ./gradlew processTestAot test   # AOT JVM
            ./gradlew nativeTest            # Native
            """);
    }

    static void printTestExamples() {
        System.out.println("--- Typical test class patterns ---");
        System.out.println("""
            // Standard integration test — works in all three modes:
            @SpringBootTest
            class OrderServiceTest {
                @Autowired OrderService svc;

                @Test
                void createOrder_savesAndReturns() {
                    var order = svc.create("item-1", 3);
                    assertThat(order.id()).isNotNull();
                }
            }

            // Skip in native only (e.g., Mockito dynamic proxy not supported):
            @DisabledInNativeImage
            @SpringBootTest
            class MockitoProxyTest {
                @MockBean ExternalApi api;  // JDK proxy — fails native
                // ...
            }

            // Register extra hints needed only in test context:
            @ImportRuntimeHints(TestHints.class)
            @SpringBootTest
            class ReflectionTest { ... }
            """);
    }

    static void printCommonFailures() {
        System.out.println("--- Common nativeTest failures and fixes ---");
        String[][] failures = {
            {
                "ClassNotFoundException in native",
                "Missing reflect-config.json entry. Add RuntimeHintsRegistrar or use GraalVM agent."
            },
            {
                "NullPointerException from getResourceAsStream",
                "Resource not included in native image. Add to resource-config.json or hints.resources()."
            },
            {
                "UnsatisfiedLinkError for JNI",
                "Add jni-config.json entry for the native method."
            },
            {
                "@MockBean breaks nativeTest",
                "Mockito uses CGLIB proxies. Use @DisabledInNativeImage on that test class."
            },
            {
                "Condition evaluated wrong (missing bean)",
                "Condition resolved at build time. Ensure build-time properties match expectations."
            },
        };
        for (var f : failures) {
            System.out.printf("  FAIL : %s%n  FIX  : %s%n%n", f[0], f[1]);
        }
    }
}
```

**How to run:** `java TestingAotNativeDemo.java`

## 6. Walkthrough

- **`mvn -Pnative spring-boot:process-test-aot test`** — the AOT phase processes test beans (`@TestConfiguration`, `@MockBean`, etc.) and generates test registrars. Tests then run on the JVM using the generated wiring instead of runtime classpath scanning. This is ~5x faster than `nativeTest` and catches 80 % of native issues.
- **`mvn -PnativeTest test`** — activates the `nativeTest` Maven profile (also in `spring-boot-starter-parent`), which hooks `native-maven-plugin:test` into the `test` phase. It compiles both the app and its test classes to a single native test binary, runs it, and reports failures.
- **`@DisabledInNativeImage`** — Spring's annotation (backed by `NativeDetector.inNativeImage()`) causes JUnit to skip the test when running in native mode. Use it for tests that fundamentally rely on JVM dynamic behaviour (Mockito, CGLIB subclasses, `ProcessBuilder` execution) rather than trying to make them work natively.
- **`@ImportRuntimeHints(TestHints.class)`** on a test class — registers hints specifically for the test context. Test-only hints don't end up in the production native image because `process-test-aot` is a separate lifecycle from `process-aot`.
- **Common failures** — each entry in `printCommonFailures()` maps an observed native exception to its root cause and the minimal fix. The GraalVM tracing agent is the fastest way to discover missing entries: run the test suite with `-agentlib:native-image-agent=...` first.

## 7. Gotchas & takeaways

> **`nativeTest` failures that pass on JVM are almost always missing hints, not logic bugs.** Before re-reading application logic, check `target/spring-aot/` for the generated hint JSONs and compare against what the failing code needs.

> **Mockito and native images don't mix by default.** Mockito generates bytecode at runtime (CGLIB or ByteBuddy). In a native image there is no runtime bytecode generation. Annotate any test using `@MockBean` or `mock(Foo.class)` with `@DisabledInNativeImage`, or migrate to a real in-memory implementation for the native test profile.

- Run `nativeTest` in CI on every PR touching Spring configuration or new dependencies.
- `NativeDetector.inNativeImage()` returns `true` at runtime in a native image — use it for conditional native-safe code paths.
- `TestcontainersPropertySource` and Spring's `@DynamicPropertySource` work in AOT mode if the container starts before AOT analysis (i.e., as a JUnit `@BeforeAll` static field).
- A failing `nativeTest` that passes `test` is signal to add a hint, not to change the test.
- Keep native test build time down by disabling unnecessary auto-configurations in `@SpringBootTest(webEnvironment = NONE)` and using `@MockitoSettings(strictness = LENIENT)` sparingly.
