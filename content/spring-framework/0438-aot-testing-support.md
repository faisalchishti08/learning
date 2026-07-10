---
card: spring-framework
gi: 438
slug: aot-testing-support
title: "AOT testing support"
---

## 1. What it is

Ahead-of-Time (AOT) testing support lets the Spring TestContext Framework's context-building work happen at *build time* instead of every test run — generating pre-computed bean definitions and initialization code for a test's `ApplicationContext` ahead of time, so that context-heavy test suites (especially in a GraalVM native-image build, where reflection-based runtime context building is expensive or restricted) start faster and work correctly under native compilation.

```
mvn -Pnative test    # or an equivalent Gradle native-test task
   |
   v
Spring's AOT processing generates:
   - pre-computed bean definitions for each distinct test ApplicationContext
   - a generated ApplicationContextInitializer per configuration
   |
   v
tests run against the AOT-generated, pre-processed context setup
```

## 2. Why & when

Spring's normal context startup involves substantial runtime work — classpath scanning, reflection-based bean instantiation, annotation processing — all of which is fine for a JVM running normally, but becomes a real problem under GraalVM native-image compilation, where reflection is restricted (requiring explicit configuration) and startup speed is often the entire point of choosing native compilation in the first place. AOT processing shifts as much of that context-building work as possible from "every time the application (or, here, a test) starts" to "once, at build time," generating code and configuration that a native image (or even a regular JVM, for the startup-speed benefit) can use directly.

This card exists specifically because *testing* under AOT/native-image has its own considerations distinct from AOT-processing a production application: the TestContext Framework needs to identify every distinct `ApplicationContext` configuration a test suite uses (since different test classes can need different contexts) and AOT-process each one, and certain testing features (like `@DirtiesContext`-triggered mid-suite context rebuilding) interact with AOT's build-time-vs-runtime split in ways that need explicit support.

Understanding AOT testing support matters when:

- Your project targets GraalVM native-image compilation and needs its test suite to run correctly (and quickly) against that same native, reflection-restricted environment — testing your actual deployment target, not just a regular JVM approximation of it.
- You're diagnosing why a test that works fine on the JVM behaves differently (or fails) when run in AOT/native mode — often traceable to reflection Spring's AOT processor didn't know to account for.
- You want faster test suite startup even on a regular JVM, since AOT-generated context initialization can be faster than the fully dynamic, reflection-heavy path, independent of native compilation.

## 3. Core concept

```
 Normal (non-AOT) test run:
   test starts -> TestContextManager builds ApplicationContext
                  (classpath scanning, reflection, annotation processing -- every run)

 AOT test run:
   BUILD TIME:  Spring's AOT engine discovers every distinct test
                ApplicationContext configuration used across the test suite
                     |
                     v
                generates optimized bean-definition code + a
                GeneratedApplicationContextInitializer per configuration
                     |
   TEST TIME:   test starts -> TestContextManager uses the
                GENERATED initializer instead of rebuilding
                from scratch -- much less runtime reflection/scanning
```

The distinction is *when* the expensive context-construction analysis happens — AOT moves it from "every test run, every time" to "once, at build time," trading build-time cost for runtime speed and native-image compatibility.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AOT processing at build time generates initializers that test runs use instead of building contexts from scratch">
  <rect x="10" y="20" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">BUILD TIME</text>
  <text x="110" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">AOT processing runs once</text>

  <rect x="10" y="120" width="200" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="142" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">TEST TIME</text>
  <text x="110" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">uses generated initializer</text>

  <rect x="330" y="70" width="290" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="475" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Generated code per distinct</text>
  <text x="475" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">test ApplicationContext configuration</text>

  <line x1="210" y1="45" x2="325" y2="85" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="325" y1="105" x2="210" y2="145" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Build-time analysis feeds generated code that test-time execution consumes, instead of redoing that analysis on every run.

## 5. Runnable example

AOT processing itself is a build-time toolchain step (invoked via Maven/Gradle plugins), not something meaningfully demonstrated as a single standalone `java File.java` snippet the way most other cards in this section are — a genuine AOT run requires a full Maven/Gradle project structure and the `spring-boot-maven-plugin`'s (or the Spring Framework AOT Gradle plugin's) `process-test-aot` goal. This example instead demonstrates the *effect* AOT processing has — using `RuntimeHints`, the mechanism AOT processing relies on to know what reflection a test's context construction needs — since that's the part of AOT testing support most directly relevant to application/test code, runnable in a single file.

### Level 1 — Basic

Register a `RuntimeHints` contribution for a test's custom `BeanFactoryPostProcessor` that uses reflection internally — the kind of registration AOT processing needs in order to correctly pre-compute a context that includes reflection-dependent logic.

```java
import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;
import org.springframework.context.annotation.*;
import org.springframework.context.aot.ImportRuntimeHints;

import java.lang.reflect.Method;

public class AotTestingBasic {

    static class ReflectiveGreeter {
        public String greet(String name) { return "Hello, " + name; } // invoked via reflection below
    }

    // Simulates AOT-relevant reflective usage: calling a method by name via java.lang.reflect.
    static class ReflectionBasedInvoker {
        String invokeGreet(ReflectiveGreeter greeter, String name) throws Exception {
            Method method = ReflectiveGreeter.class.getMethod("greet", String.class);
            return (String) method.invoke(greeter, name);
        }
    }

    // A RuntimeHintsRegistrar tells Spring's AOT engine "this reflective call needs
    // hint registration to work correctly under a reflection-restricted native image."
    static class GreeterRuntimeHints implements RuntimeHintsRegistrar {
        @Override
        public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
            hints.reflection().registerMethod(
                    getGreetMethod(), org.springframework.aot.hint.ExecutableMode.INVOKE);
        }
        private Method getGreetMethod() {
            try { return ReflectiveGreeter.class.getMethod("greet", String.class); }
            catch (NoSuchMethodException e) { throw new RuntimeException(e); }
        }
    }

    @Configuration
    @ImportRuntimeHints(GreeterRuntimeHints.class) // wires the hints registrar into this configuration
    static class Config {
        @Bean ReflectiveGreeter reflectiveGreeter() { return new ReflectiveGreeter(); }
        @Bean ReflectionBasedInvoker reflectionBasedInvoker() { return new ReflectionBasedInvoker(); }
    }

    public static void main(String[] args) throws Exception {
        var context = new AnnotationConfigApplicationContext(Config.class);

        ReflectiveGreeter greeter = context.getBean(ReflectiveGreeter.class);
        ReflectionBasedInvoker invoker = context.getBean(ReflectionBasedInvoker.class);

        String result = invoker.invokeGreet(greeter, "Ada");
        System.out.println("Reflective invocation result: " + result);
        if (!result.equals("Hello, Ada")) throw new AssertionError("Unexpected result");
        System.out.println("On a regular JVM, this works without any hints -- "
                + "the hints exist specifically to make the SAME code work under AOT/native-image.");

        context.close();
    }
}
```

How to run: add `spring-context` to the classpath, then `java AotTestingBasic.java`. This runs correctly on a regular JVM regardless of the hints registration (reflection works unrestricted there) — the hints specifically matter when this same configuration is later AOT-processed for a native image build, where `ReflectionBasedInvoker`'s reflective call to `greet(String)` would otherwise fail without the registered hint telling the native-image builder to retain that method for reflective access.

### Level 2 — Intermediate

A `TestRuntimeHintsRegistrar`-style pattern for test-specific reflection needs — registering hints for a test double (like a Mockito mock's dynamically-generated proxy class) that only exists in the test context, not in production configuration, showing that AOT hint registration applies to test-specific infrastructure too, not just production code.

```java
import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;
import org.springframework.aot.hint.MemberCategory;
import org.springframework.context.annotation.*;
import org.springframework.context.aot.ImportRuntimeHints;

public class AotTestingIntermediate {

    interface NotificationService { void notify(String message); }

    static class OrderService {
        private final NotificationService notificationService;
        OrderService(NotificationService notificationService) { this.notificationService = notificationService; }
        void placeOrder(String orderId) { notificationService.notify("Order placed: " + orderId); }
    }

    static class TestNotificationHints implements RuntimeHintsRegistrar {
        @Override
        public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
            // Registers reflection access for the test-double implementation itself --
            // relevant because AOT processing needs to know about types used ONLY in tests too,
            // not just production types, if the test's context includes them.
            hints.reflection().registerType(NotificationService.class,
                    MemberCategory.INVOKE_DECLARED_METHODS, MemberCategory.INVOKE_PUBLIC_METHODS);
        }
    }

    @Configuration
    @ImportRuntimeHints(TestNotificationHints.class)
    static class TestConfig {
        @Bean
        NotificationService notificationService() {
            // A simple test double implemented as a lambda -- stands in for what would
            // often be a Mockito mock or a hand-written test-specific implementation.
            return message -> System.out.println("[TEST NOTIFICATION] " + message);
        }
        @Bean
        OrderService orderService(NotificationService notificationService) {
            return new OrderService(notificationService);
        }
    }

    public static void main(String[] args) {
        var context = new AnnotationConfigApplicationContext(TestConfig.class);
        OrderService orderService = context.getBean(OrderService.class);

        orderService.placeOrder("order-1");
        System.out.println("Test-specific configuration with its own RuntimeHints ran successfully.");
        System.out.println("Under AOT processing, TestNotificationHints ensures the interface's methods "
                + "remain reflectively accessible in the generated, native-image-compatible context.");

        context.close();
    }
}
```

How to run: add `spring-context` to the classpath, then `java AotTestingIntermediate.java`.

`@ImportRuntimeHints(TestNotificationHints.class)` on a *test* configuration class works identically to how it would on a production configuration class — AOT processing doesn't distinguish "test" from "production" configuration structurally, it just processes whatever `@Configuration` classes a given `ApplicationContext` (test or otherwise) actually uses. This matters because test-specific beans (fakes, stubs, test doubles) can have their own reflection needs that production code never exercises, and AOT hint registration needs to account for those too when a test's context is AOT-processed.

### Level 3 — Advanced

A conditional hints registrar that only contributes hints relevant to a specific test scenario, mirroring the conditional `ContextCustomizerFactory` pattern from the earlier card — demonstrating that AOT hints registration, like context customization, can be selectively applied rather than blanket-registered for every context.

```java
import org.springframework.aot.hint.MemberCategory;
import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;
import org.springframework.context.annotation.*;
import org.springframework.context.aot.ImportRuntimeHints;

import java.lang.annotation.*;

public class AotTestingAdvanced {

    @Target(ElementType.TYPE)
    @Retention(RetentionPolicy.RUNTIME)
    @interface RequiresReflectiveSerialization {
        Class<?> value();
    }

    record ReportRow(String label, double amount) {}

    static class ReportSerializer {
        // Simulates a serialization library that reflectively inspects record components --
        // exactly the kind of reflective access that needs explicit AOT hints to survive
        // native-image compilation, where reflection is closed-world by default.
        String serialize(Object record) {
            StringBuilder sb = new StringBuilder("{");
            for (var component : record.getClass().getRecordComponents()) {
                try {
                    Object value = component.getAccessor().invoke(record);
                    sb.append(component.getName()).append("=").append(value).append(",");
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
            }
            return sb.append("}").toString();
        }
    }

    static class ConditionalSerializationHints implements RuntimeHintsRegistrar {
        @Override
        public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
            // In a real implementation, this would inspect the annotated test class via
            // AnnotatedElementUtils (as the ContextCustomizerFactory card's example did)
            // to decide WHICH types need reflective hints for THIS specific test scenario.
            hints.reflection().registerType(ReportRow.class,
                    MemberCategory.INVOKE_DECLARED_METHODS, MemberCategory.DECLARED_FIELDS);
        }
    }

    @Configuration
    @ImportRuntimeHints(ConditionalSerializationHints.class)
    @RequiresReflectiveSerialization(ReportRow.class)
    static class ReportConfig {
        @Bean ReportSerializer reportSerializer() { return new ReportSerializer(); }
    }

    public static void main(String[] args) {
        var context = new AnnotationConfigApplicationContext(ReportConfig.class);
        ReportSerializer serializer = context.getBean(ReportSerializer.class);

        String serialized = serializer.serialize(new ReportRow("Revenue", 15000.50));
        System.out.println("Serialized via reflection: " + serialized);
        if (!serialized.contains("Revenue")) throw new AssertionError("Expected reflective serialization to work");

        System.out.println("On a regular JVM this works unconditionally; under AOT/native-image, "
                + "ConditionalSerializationHints is what keeps ReportRow's record components "
                + "reflectively accessible after native compilation strips unused reflection metadata.");

        context.close();
    }
}
```

How to run: add `spring-context` to the classpath, then `java AotTestingAdvanced.java`.

`ReportSerializer.serialize(...)` uses `getClass().getRecordComponents()` and reflective accessor invocation — exactly the pattern that works transparently on a regular JVM but requires explicit `RuntimeHints` registration to survive GraalVM native-image's closed-world reflection model, where any reflective access not explicitly registered is simply unavailable at runtime, often failing with a `NoSuchMethodException` or similar rather than a clear "you forgot a hint" message. `ConditionalSerializationHints` registers exactly the reflection needed for `ReportRow` specifically, illustrating that hints registration should be precise and scenario-specific rather than blanket "hint everything," which would bloat the generated native image with retained reflection metadata for types that never actually need it.

## 6. Walkthrough

Trace the conceptual AOT processing flow for `AotTestingAdvanced.ReportConfig` (described here since the actual AOT build-time step requires a full Maven/Gradle native build, outside a single-file example's scope):

1. **Build-time AOT discovery.** When `mvn -Pnative test` (or equivalent) runs, Spring's AOT processing engine discovers that some test class uses `@ContextConfiguration`/`@SpringJUnitConfig` pointing at (directly or transitively) `ReportConfig`.
2. **Configuration processing.** The AOT engine processes `ReportConfig`, finds `@ImportRuntimeHints(ConditionalSerializationHints.class)`, and instantiates that registrar, calling its `registerHints(hints, classLoader)` method.
3. **Hints recorded.** `ConditionalSerializationHints.registerHints` calls `hints.reflection().registerType(ReportRow.class, ...)`, recording that `ReportRow`'s declared methods and fields must remain reflectively accessible — this registration is captured into Spring's AOT-generated metadata, destined for the native-image build's reflection configuration.
4. **Bean definitions generated.** Separately, the AOT engine also generates optimized, non-reflective bean-instantiation code for `reportSerializer()` itself (the `@Bean` method), so that *constructing* the `ReportSerializer` bean at native-image runtime doesn't need reflection at all — only the *internal* reflective work `ReportSerializer.serialize(...)` does at runtime (inspecting `ReportRow`'s components) needs the explicit hint from step 3.
5. **Native image compilation.** GraalVM's native-image tool consumes the generated reflection configuration (derived from the `RuntimeHints` registration) alongside the AOT-generated bean definitions, producing a native executable where `ReportRow`'s components remain reflectively inspectable — without step 3's registration, the native-image builder would have no way to know `ReportRow` needs this, and would (by default) strip that reflection capability, causing `serializer.serialize(...)` to fail at native runtime with a reflection-related error, despite working perfectly on a regular JVM.
6. **Test execution against the native artifact.** The test suite then runs (or, for CI verifying native-image compatibility, is executed) against this compiled native executable, and `serializer.serialize(new ReportRow(...))` succeeds specifically because the hint-driven reflection configuration preserved the access path it needs.

```
BUILD TIME (AOT processing):
   discover ReportConfig -> process @ImportRuntimeHints -> ConditionalSerializationHints.registerHints()
        -> records: ReportRow needs reflective method/field access
   generate optimized bean definitions for reportSerializer()

NATIVE IMAGE COMPILATION:
   consumes generated reflection config -> retains ReportRow's reflective accessibility
   consumes generated bean definitions -> non-reflective bean construction

NATIVE RUNTIME (test or production):
   serializer.serialize(new ReportRow(...)) -- reflective access WORKS, because of step 1's hint
   (without the hint: would fail under native-image's closed-world reflection default)
```

## 7. Gotchas & takeaways

> Gotcha: code that works perfectly on a regular JVM, including passing every test in a normal (non-AOT, non-native) test run, can still fail specifically under native-image compilation if it does reflection (or classpath scanning, dynamic proxying, resource loading) that Spring's AOT engine doesn't already know about and no `RuntimeHints` registrar explicitly declares — the failure only surfaces when actually running the native-compiled artifact, which is exactly why running your test suite *against* an AOT/native build (not just a regular JVM run) is essential if native-image compatibility genuinely matters for your deployment target.

- AOT testing support shifts expensive context-construction work from every test run to a one-time build step, generating code a test suite (and, more importantly, a GraalVM native image) can use directly instead of rebuilding contexts reflectively at every startup.
- `RuntimeHints`/`RuntimeHintsRegistrar` (via `@ImportRuntimeHints`) is how you explicitly declare reflection, resource, or proxy usage the AOT engine can't automatically infer — applicable to both production and test-specific configuration equally.
- Test-specific infrastructure (test doubles, fakes, test-only beans) can have its own reflection needs distinct from production code, and those needs must be accounted for separately when a test's context is AOT-processed.
- Running your test suite against an actual AOT/native-compiled build (not just relying on regular JVM test runs) is the only way to genuinely verify native-image compatibility — reflection gaps that AOT hints didn't cover surface specifically at native runtime, not before.
