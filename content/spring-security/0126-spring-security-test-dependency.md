---
card: spring-security
gi: 126
slug: spring-security-test-dependency
title: "spring-security-test dependency"
---

## 1. What it is

`spring-security-test` is a separate, test-scoped artifact from the core `spring-security-*` libraries — it contains every testing annotation and utility this section covers (`@WithMockUser`, `SecurityMockMvcRequestPostProcessors`, `SecurityMockMvcResultMatchers`, and more), none of which are available on the main classpath by design, since they exist purely to make writing security-aware tests convenient and have no place in production code.

```xml
<dependency>
    <groupId>org.springframework.security</groupId>
    <artifactId>spring-security-test</artifactId>
    <scope>test</scope>
</dependency>
```
```gradle
testImplementation "org.springframework.security:spring-security-test"
```

## 2. Why & when

Every earlier card in this course covered how a `SecurityFilterChain`, `AuthenticationManager`, or `AuthorizationManager` behaves at runtime — but verifying that behavior in a test requires either standing up a full authentication flow for every single test method (slow, and testing the framework's own login mechanics repeatedly rather than the application logic a given test actually cares about) or a purpose-built set of test utilities that let a test *declare* "run this as an authenticated user with these authorities" directly, without re-deriving that state through a real login. `spring-security-test` exists specifically to be that shortcut — and its test-only scope exists because shipping it as part of a production artifact would bundle test-only conveniences (and their transitive dependencies) into a deployed application for no benefit.

Reach for adding `spring-security-test` when:

- Writing any `@WebMvcTest`, `@SpringBootTest`, or standalone `MockMvc`-based test that needs to simulate an authenticated request — this dependency is the prerequisite for every annotation and utility the rest of this section covers.
- Testing WebFlux/reactive endpoints with `WebTestClient` and needing the equivalent `mutateWith(mockUser())`-style security customization (card 0134).
- Testing method-security-annotated service methods directly, without going through a web layer at all (card 0136) — `@WithMockUser` works equally well on a plain `@Test` method exercising a `@PreAuthorize`-annotated service.
- Debugging a test failure like `NoClassDefFoundError` or `ClassNotFoundException` referencing a class like `WithMockUser` or `SecurityMockMvcRequestPostProcessors` — this almost always means the dependency is missing, or was accidentally scoped to `compile`/`main` instead of `test` (functionally harmless but a signal something in the build configuration is off) or, more commonly, entirely absent.

## 3. Core concept

```
Production classpath:                    Test classpath (with spring-security-test added):
    spring-security-core                     spring-security-core
    spring-security-config                   spring-security-config
    spring-security-web                      spring-security-web
                                              + spring-security-test  <-- TEST-SCOPED ONLY
                                                  @WithMockUser
                                                  @WithAnonymousUser
                                                  @WithUserDetails
                                                  @WithSecurityContext
                                                  SecurityMockMvcRequestPostProcessors
                                                  SecurityMockMvcResultMatchers
                                                  SecurityMockServerConfigurers (WebTestClient)

Spring Boot's dependency management (spring-boot-starter-test does NOT include this automatically) --
it must be added EXPLICITLY alongside spring-boot-starter-security, as its own line,
scoped to test.
```

Every capability the remaining cards in this section describe is only reachable once this one dependency is present and correctly scoped.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing production code depending on spring security core config and web while test code additionally depends on spring security test which provides annotations and utilities never present in the deployed production artifact">
  <rect x="20" y="20" width="280" height="140" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="160" y="42" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Production artifact</text>
  <text x="160" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">spring-security-core</text>
  <text x="160" y="83" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">spring-security-config</text>
  <text x="160" y="101" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">spring-security-web</text>

  <rect x="330" y="20" width="290" height="140" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Test classpath ONLY</text>
  <text x="475" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">(everything from production, PLUS:)</text>
  <text x="475" y="85" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">spring-security-test</text>
  <text x="475" y="103" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@WithMockUser, RequestPostProcessors,</text>
  <text x="475" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ResultMatchers, mutateWith(...)</text>

  <text x="320" y="10" fill="#8b949e" font-size="1"> </text>
</svg>

Test-only utilities never ship in the deployed artifact — the boundary is enforced by the dependency's `test` scope.

## 5. Runnable example

The scenario: since this card is about a build dependency rather than runtime behavior, the example demonstrates the *effect* of the dependency being present versus absent — modeling a minimal test-utility class that only "exists" (is callable) when a simulated classpath includes it, then verifying a test can't accidentally leak a test-only utility into production logic.

### Level 1 — Basic

A minimal simulation: a test utility class only usable when explicitly "included."

```java
import java.util.*;

public class TestDependencyLevel1 {
    // stands in for spring-security-test's utilities being present (or not) on a classpath
    static class SimulatedClasspath {
        private final Set<String> includedArtifacts;
        SimulatedClasspath(Set<String> includedArtifacts) { this.includedArtifacts = includedArtifacts; }

        boolean isAvailable(String artifactId) { return includedArtifacts.contains(artifactId); }
    }

    static void useTestUtility(SimulatedClasspath classpath) {
        if (!classpath.isAvailable("spring-security-test")) {
            throw new NoSuchElementException("spring-security-test is not on the classpath -- add it as a test-scoped dependency");
        }
        System.out.println("using @WithMockUser and friends successfully");
    }

    public static void main(String[] args) {
        SimulatedClasspath productionOnly = new SimulatedClasspath(Set.of("spring-security-core", "spring-security-web"));
        SimulatedClasspath withTestDependency = new SimulatedClasspath(
                Set.of("spring-security-core", "spring-security-web", "spring-security-test"));

        try {
            useTestUtility(productionOnly);
        } catch (NoSuchElementException e) {
            System.out.println("without the dependency: " + e.getMessage());
        }

        useTestUtility(withTestDependency);
    }
}
```

**How to run:** save as `TestDependencyLevel1.java`, run `java TestDependencyLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
without the dependency: spring-security-test is not on the classpath -- add it as a test-scoped dependency
using @WithMockUser and friends successfully
```

`SimulatedClasspath` stands in for a real Maven/Gradle dependency resolution: without `spring-security-test` present, any attempt to use its utilities fails immediately (in reality, at compile time, since the classes wouldn't even resolve) — adding the dependency is what unlocks every capability the rest of this section describes.

### Level 2 — Intermediate

Demonstrate the *scope* boundary: a test-scoped dependency's classes must never be reachable from production code, even accidentally.

```java
import java.util.*;

public class TestDependencyLevel2 {
    enum Scope { MAIN, TEST }
    record Dependency(String artifactId, Scope scope) {}

    static class BuildConfiguration {
        private final List<Dependency> dependencies = new ArrayList<>();
        void add(Dependency dep) { dependencies.add(dep); }

        // simulates a build tool checking: can THIS scope reach an artifact of THAT scope?
        boolean isReachableFrom(String artifactId, Scope callingScope) {
            for (Dependency dep : dependencies) {
                if (dep.artifactId().equals(artifactId)) {
                    // MAIN code can only see MAIN-scoped deps; TEST code can see BOTH
                    return dep.scope() == Scope.MAIN || callingScope == Scope.TEST;
                }
            }
            return false;
        }
    }

    public static void main(String[] args) {
        BuildConfiguration build = new BuildConfiguration();
        build.add(new Dependency("spring-security-core", Scope.MAIN));
        build.add(new Dependency("spring-security-test", Scope.TEST));

        System.out.println("MAIN code can reach spring-security-core: " + build.isReachableFrom("spring-security-core", Scope.MAIN));
        System.out.println("MAIN code can reach spring-security-test: " + build.isReachableFrom("spring-security-test", Scope.MAIN));
        System.out.println("TEST code can reach spring-security-test: " + build.isReachableFrom("spring-security-test", Scope.TEST));
        System.out.println("TEST code can reach spring-security-core: " + build.isReachableFrom("spring-security-core", Scope.TEST));
    }
}
```

**How to run:** save as `TestDependencyLevel2.java`, run `java TestDependencyLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
MAIN code can reach spring-security-core: true
MAIN code can reach spring-security-test: false
TEST code can reach spring-security-test: true
TEST code can reach spring-security-core: true
```

What changed: `isReachableFrom` now enforces the actual scope-visibility rule a real build tool applies — production (`MAIN`-scoped) code cannot compile against a `TEST`-scoped dependency at all, which is precisely why `@WithMockUser` and friends could never accidentally end up compiled into a deployed production JAR, regardless of what an individual developer might attempt.

### Level 3 — Advanced

Model a realistic build-validation check: verifying every test class that references a Security testing utility has the dependency correctly declared, and catching the common misconfiguration of the dependency being present but wrongly scoped as `compile`/`implementation` instead of `test`.

```java
import java.util.*;

public class TestDependencyLevel3 {
    enum Scope { MAIN, TEST }
    record Dependency(String artifactId, Scope scope) {}
    record SourceFile(String path, Scope ownScope, Set<String> referencedArtifacts) {}

    static class BuildValidationException extends RuntimeException {
        BuildValidationException(String message) { super(message); }
    }

    static class BuildValidator {
        private final Map<String, Dependency> dependencies = new HashMap<>();
        void addDependency(Dependency dep) { dependencies.put(dep.artifactId(), dep); }

        void validate(SourceFile file) {
            for (String artifact : file.referencedArtifacts()) {
                Dependency dep = dependencies.get(artifact);
                if (dep == null) {
                    throw new BuildValidationException(file.path() + " references \"" + artifact + "\" which is not a declared dependency at all");
                }
                if (file.ownScope() == Scope.MAIN && dep.scope() == Scope.TEST) {
                    throw new BuildValidationException(file.path() + " is PRODUCTION code but references \""
                            + artifact + "\", a TEST-scoped dependency -- this must never compile");
                }
            }
        }

        void flagOverlyBroadScope(Dependency dep) {
            if (dep.artifactId().equals("spring-security-test") && dep.scope() == Scope.MAIN) {
                System.out.println("WARNING: spring-security-test is scoped MAIN instead of TEST -- "
                        + "it will be bundled into the production artifact unnecessarily");
            }
        }
    }

    public static void main(String[] args) {
        BuildValidator validator = new BuildValidator();
        validator.addDependency(new Dependency("spring-security-core", Scope.MAIN));
        validator.addDependency(new Dependency("spring-security-test", Scope.TEST));

        SourceFile productionService = new SourceFile("src/main/java/OrderService.java", Scope.MAIN,
                Set.of("spring-security-core"));
        SourceFile properTest = new SourceFile("src/test/java/OrderServiceTest.java", Scope.TEST,
                Set.of("spring-security-core", "spring-security-test"));
        SourceFile misplacedProductionCode = new SourceFile("src/main/java/BrokenService.java", Scope.MAIN,
                Set.of("spring-security-test")); // MISTAKE: production code referencing a test utility

        validator.validate(productionService);
        System.out.println("production service: OK, no test-only dependencies referenced");

        validator.validate(properTest);
        System.out.println("proper test: OK, correctly uses spring-security-test");

        try {
            validator.validate(misplacedProductionCode);
        } catch (BuildValidationException e) {
            System.out.println("caught misconfiguration: " + e.getMessage());
        }

        // separately, flag a dependency that's declared with the WRONG scope entirely
        validator.flagOverlyBroadScope(new Dependency("spring-security-test", Scope.MAIN));
    }
}
```

**How to run:** save as `TestDependencyLevel3.java`, run `java TestDependencyLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
production service: OK, no test-only dependencies referenced
proper test: OK, correctly uses spring-security-test
caught misconfiguration: src/main/java/BrokenService.java is PRODUCTION code but references "spring-security-test", a TEST-scoped dependency -- this must never compile
WARNING: spring-security-test is scoped MAIN instead of TEST -- it will be bundled into the production artifact unnecessarily
```

What changed: `BuildValidator` now checks two distinct misconfiguration classes — production code illegitimately referencing a test-only artifact (which a real build tool prevents at compile time, not merely flags), and the dependency itself being declared with an overly broad scope (which compiles fine but bloats the production artifact unnecessarily) — both are real, if uncommon, build-configuration mistakes worth knowing to look for.

## 6. Walkthrough

Trace what happens from adding this dependency to a test successfully using `@WithMockUser` (previewed here; covered fully in card 0127).

**Step 1 — the dependency is declared, correctly scoped:**
```xml
<dependency>
    <groupId>org.springframework.security</groupId>
    <artifactId>spring-security-test</artifactId>
    <scope>test</scope>
</dependency>
```
This corresponds to `build.add(new Dependency("spring-security-test", Scope.TEST))` in Level 2/3's model.

**Step 2 — a test class is written, referencing a testing annotation:**
```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Test
    @WithMockUser(roles = "ADMIN")
    void adminCanViewOrders() throws Exception {
        mockMvc.perform(get("/api/orders")).andExpect(status().isOk());
    }
}
```
Because this file lives under `src/test/java` (`Scope.TEST` in the model), and `spring-security-test` is a declared dependency, the reference resolves and compiles successfully — corresponding to `validator.validate(properTest)` passing without incident.

**Step 3 — build tooling enforces the boundary automatically.** If a developer mistakenly imported `@WithMockUser` into a class under `src/main/java`, the build would fail to compile that class at all, since `spring-security-test`'s classes are simply not on the `main` compilation classpath — corresponding to the `BuildValidationException` thrown for `misplacedProductionCode` in Level 3.

**Step 4 — the resulting production artifact (a JAR or WAR) never contains any of `spring-security-test`'s classes**, since test-scoped dependencies are excluded from the packaged output entirely — this is the concrete payoff of getting the scope right: zero risk of test-only conveniences (and their footprint) shipping to production, and zero possibility of a test utility being mistakenly called from real application logic.

```
declare dependency, scope=test
        |
        v
test code compiles against it successfully  (production code CANNOT, even if someone tries)
        |
        v
test runs, @WithMockUser works exactly as documented
        |
        v
production JAR/WAR built -- spring-security-test's classes are NOT included at all
```

## 7. Gotchas & takeaways

> **Gotcha:** `spring-security-test` is not automatically pulled in by `spring-boot-starter-test` — it must be declared explicitly, alongside `spring-boot-starter-security`, as its own dependency line with an explicit test scope. Assuming it comes along "for free" with the general test starter is a common first-time setup mistake that surfaces as a compile error the moment `@WithMockUser` or similar is first used.

- `spring-security-test` is a separate, test-scoped artifact containing every security testing utility this section covers — it is never bundled into a production artifact.
- It must be added explicitly to the build; it is not a transitive dependency of `spring-boot-starter-test` or `spring-boot-starter-security` on its own.
- The test scope is enforced by the build tool itself — production code simply cannot compile against test-scoped classes, making this a structural guarantee, not merely a convention developers must remember to follow.
- A `ClassNotFoundException`/`NoClassDefFoundError`/compile error referencing any testing annotation from this section (`@WithMockUser`, `SecurityMockMvcRequestPostProcessors`, etc.) is almost always traceable to this dependency being missing.
- Every subsequent card in this Testing section assumes this dependency is already present and correctly scoped — it is the foundation the rest of the section builds on.
