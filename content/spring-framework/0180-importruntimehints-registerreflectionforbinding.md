---
card: spring-framework
gi: 180
slug: importruntimehints-registerreflectionforbinding
title: "@ImportRuntimeHints / @RegisterReflectionForBinding"
---

## 1. What it is

Two annotations that declare native-image hints without writing a `RuntimeHintsRegistrar` by hand:

**`@ImportRuntimeHints(MyRegistrar.class)`** — attaches one or more `RuntimeHintsRegistrar` implementations to a class. During AOT processing Spring discovers the annotation and invokes each registrar. Place it on a `@Configuration`, `@Component`, or `@SpringBootApplication` class.

```java
@ImportRuntimeHints(MyRegistrar.class)
@Configuration
class AppConfig { }
```

**`@RegisterReflectionForBinding(MyDto.class)`** — a shortcut that registers a class (typically a Jackson-serialised DTO or record) with the full set of member categories needed for binding: all public constructors, methods, and fields. Equivalent to calling `hints.reflection().registerType(...)` with `INVOKE_PUBLIC_CONSTRUCTORS`, `PUBLIC_FIELDS`, and `INVOKE_PUBLIC_METHODS`.

```java
@RegisterReflectionForBinding({UserDto.class, OrderDto.class})
@Service
class ApiService { ... }
```

Both annotations are processed only during `spring-boot:process-aot` — they have no effect at JVM runtime.

## 2. Why & when

- **`@ImportRuntimeHints`** when you need custom logic in the registrar: dynamic class discovery, `resources().registerPattern(...)`, `proxies()`, `serialization()`, or conditional registration based on classpath presence.
- **`@RegisterReflectionForBinding`** for the simple, common case: a DTO / record / POJO deserialized from JSON, XML, or form data. One annotation, covers the standard binding categories.
- **Avoid duplicating**: if a registrar is already registered via `META-INF/spring/aot.factories` (e.g., from a library), adding `@ImportRuntimeHints` for the same registrar on your application class registers it twice — hints are merged (not duplicated in the binary), but the registrar is invoked twice.
- `@RegisterReflectionForBinding` does NOT register the type for Java serialization (`ObjectOutputStream`). If you also need that, add an explicit `hints.serialization().registerType(...)` call in a registrar.

## 3. Core concept

`@RegisterReflectionForBinding` is implemented internally as a `@ImportRuntimeHints` with a built-in `ReflectionForBindingRegistrar` that calls:

```java
hints.reflection().registerType(declaredType,
    MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
    MemberCategory.INVOKE_DECLARED_CONSTRUCTORS,
    MemberCategory.PUBLIC_FIELDS,
    MemberCategory.DECLARED_FIELDS,
    MemberCategory.INVOKE_PUBLIC_METHODS,
    MemberCategory.INVOKE_DECLARED_METHODS
);
```

It also recursively registers all field types, generic parameter types, and return types reachable from the declared class.

`@ImportRuntimeHints` is the general escape hatch when the annotation shortcut is insufficient. It accepts an array of `RuntimeHintsRegistrar` classes:

```java
@ImportRuntimeHints({SecurityHints.class, SerializationHints.class})
@SpringBootApplication
class App { ... }
```

Both annotations are `@Repeatable` — stack multiple of them or use an array value for multiple registrar/type declarations.

| Annotation | Handles | Recursive | Use when |
|---|---|---|---|
| `@RegisterReflectionForBinding` | reflection only (all categories) | yes | DTO/POJO for binding |
| `@ImportRuntimeHints` | any hint type | no (you control the registrar) | custom/complex hints |

## 4. Diagram

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="iha" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ihb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- @ImportRuntimeHints path -->
  <rect x="5" y="15" width="245" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="127" y="34" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@ImportRuntimeHints</text>
  <text x="127" y="48" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">value = MyRegistrar.class</text>
  <text x="127" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">on @Configuration / @Component / @SpringBootApplication</text>

  <!-- @RegisterReflectionForBinding path -->
  <rect x="5" y="95" width="245" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="127" y="114" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@RegisterReflectionForBinding</text>
  <text x="127" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">value = {UserDto.class, OrderDto.class}</text>
  <text x="127" y="142" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">on any @Component / @Configuration</text>

  <!-- AOT engine box -->
  <rect x="295" y="50" width="140" height="50" rx="6" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="2"/>
  <text x="365" y="72" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">AOT engine</text>
  <text x="365" y="86" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">process-aot</text>

  <line x1="252" y1="45"  x2="293" y2="68" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#iha)"/>
  <line x1="252" y1="125" x2="293" y2="82" stroke="#6db33f" stroke-width="1.5" marker-end="url(#iha)"/>

  <!-- RuntimeHints -->
  <rect x="485" y="50" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="73" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RuntimeHints</text>
  <text x="555" y="87" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">populated with hints</text>
  <line x1="437" y1="75" x2="483" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#iha)"/>

  <!-- Note at bottom -->
  <text x="350" y="155" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@RegisterReflectionForBinding internally delegates to a built-in RuntimeHintsRegistrar</text>
  <text x="350" y="168" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">that registers all member categories recursively. Both annotations run at AOT build time only.</text>
</svg>

Both annotations instruct the AOT engine to populate `RuntimeHints`; `@RegisterReflectionForBinding` delegates to a built-in registrar covering all binding member categories.

## 5. Runnable example

The scenario is a **REST API for a user management service** — a `UserDto` and `OrderDto` need Jackson binding, plus a custom registrar for dynamic reflection — growing to a full Spring Boot REST app.

### Level 1 — Basic

Show `@RegisterReflectionForBinding` registering a DTO type and introspect the resulting hints.

```java
// ImportHintsBasic.java
import org.springframework.aot.hint.*;
import org.springframework.context.annotation.*;

// DTOs that need Jackson binding hints
record UserDto(String id, String name, String email) {}
record OrderDto(String orderId, String userId, double total) {}

// @RegisterReflectionForBinding is processed by the AOT engine;
// here we simulate the output by invoking the internal registrar directly.
public class ImportHintsBasic {
    public static void main(String[] args) {
        var hints = new RuntimeHints();

        // Equivalent to what @RegisterReflectionForBinding produces:
        hints.reflection().registerType(UserDto.class,
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
            MemberCategory.INVOKE_DECLARED_CONSTRUCTORS,
            MemberCategory.PUBLIC_FIELDS,
            MemberCategory.DECLARED_FIELDS,
            MemberCategory.INVOKE_PUBLIC_METHODS,
            MemberCategory.INVOKE_DECLARED_METHODS);
        hints.reflection().registerType(OrderDto.class,
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
            MemberCategory.INVOKE_DECLARED_CONSTRUCTORS,
            MemberCategory.PUBLIC_FIELDS,
            MemberCategory.DECLARED_FIELDS,
            MemberCategory.INVOKE_PUBLIC_METHODS,
            MemberCategory.INVOKE_DECLARED_METHODS);

        // Verify
        hints.reflection().typeHints()
             .forEach(th -> System.out.printf(
                 "%-30s → %d categories%n",
                 th.getType().getSimpleName(),
                 th.getMemberCategories().size()));
        // UserDto  → 6 categories
        // OrderDto → 6 categories

        // Demonstrate the reflection actually works (JVM)
        try {
            var ctor  = UserDto.class.getDeclaredConstructors()[0];
            var user  = (UserDto) ctor.newInstance("u1", "Alice", "alice@ex.com");
            System.out.println("Reflective: " + user);
        } catch (Exception e) { e.printStackTrace(); }
    }
}
```

How to run: `java ImportHintsBasic.java`

`INVOKE_PUBLIC_CONSTRUCTORS` and `INVOKE_DECLARED_CONSTRUCTORS` together cover all access levels; `INVOKE_PUBLIC_METHODS` covers Jackson's use of getters. `@RegisterReflectionForBinding` on a class does all of this in one annotation — the code above is what it generates internally, shown explicitly for learning purposes.

### Level 2 — Intermediate

Combine `@RegisterReflectionForBinding` (for DTOs) with `@ImportRuntimeHints` (for custom registrar handling resources and proxies) on a Spring service.

```java
// ImportHintsIntermediate.java
import org.springframework.aot.hint.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.*;

// ---- DTOs ----
record UserDto(String id, String name, String email) {}
record AuditEvent(String action, String userId, long timestamp) {}

// ---- Custom registrar for non-DTO hints ----
class UserServiceHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader cl) {
        // Resource: SQL templates loaded at runtime
        hints.resources().registerPattern("sql/user-*.sql");
        // Serialisation: AuditEvent stored in session
        hints.serialization().registerType(AuditEvent.class);
        System.out.println("[AOT] UserServiceHints registered");
    }
}

// ---- Service class: uses both annotations ----
// @RegisterReflectionForBinding handles the DTOs for Jackson
// @ImportRuntimeHints handles resources + serialization
@RegisterReflectionForBinding({UserDto.class, AuditEvent.class})
@ImportRuntimeHints(UserServiceHints.class)
@Service
class UserService {
    private final List<UserDto> users = new ArrayList<>();

    public UserDto createUser(String id, String name, String email) {
        var user = new UserDto(id, name, email);
        users.add(user);
        return user;
    }

    public List<UserDto> listUsers() { return List.copyOf(users); }
}

@Configuration
@ComponentScan
class InterConfig { }

public class ImportHintsIntermediate {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(InterConfig.class);
        var svc = ctx.getBean(UserService.class);
        svc.createUser("u1", "Alice", "alice@ex.com");
        svc.createUser("u2", "Bob",   "bob@ex.com");
        System.out.println("Users: " + svc.listUsers());

        // In production, during process-aot:
        // 1. @RegisterReflectionForBinding → hints for UserDto, AuditEvent (all member cats)
        // 2. @ImportRuntimeHints(UserServiceHints.class) → resources + serialization hints
        // Both go into the same RuntimeHints instance → single reflect-config.json
        ctx.close();
    }
}
```

How to run: `java ImportHintsIntermediate.java`

Placing both `@RegisterReflectionForBinding` and `@ImportRuntimeHints` on the same class is perfectly valid — they are additive. During `process-aot`, `@RegisterReflectionForBinding` generates reflection hints for `UserDto` and `AuditEvent`; `@ImportRuntimeHints(UserServiceHints.class)` additionally registers SQL resource patterns and `AuditEvent` serialization hints. Both sets merge into a single `RuntimeHints` object.

### Level 3 — Advanced

A Spring Boot REST API using `@RegisterReflectionForBinding` on the controller and `@ImportRuntimeHints` on the application class for library-level hints.

```java
// ImportHintsAdvanced.java — Spring Boot REST API
import org.springframework.aot.hint.*;
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

// ---- API DTOs ----
record CreateUserRequest(String name, String email) {}
record UserResponse(String id, String name, String email, String status) {}
record ErrorResponse(String code, String message) {}

// ---- Library hints (for a hypothetical legacy crypto lib) ----
class LegacyCryptoHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader cl) {
        hints.reflection().registerType(
            TypeReference.of("com.legacy.CryptoHelper"),
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
            MemberCategory.INVOKE_PUBLIC_METHODS);
        hints.resources().registerPattern("crypto/keystore.jks");
    }
}

@Service
class UserRegistrationService {
    private final Map<String, UserResponse> store = new ConcurrentHashMap<>();
    private final AtomicInteger counter = new AtomicInteger(1);

    public UserResponse register(CreateUserRequest req) {
        String id = "u" + counter.getAndIncrement();
        var response = new UserResponse(id, req.name(), req.email(), "ACTIVE");
        store.put(id, response);
        return response;
    }
    public List<UserResponse> findAll() { return List.copyOf(store.values()); }
}

// @RegisterReflectionForBinding covers all DTOs for Jackson serialization
@RegisterReflectionForBinding({
    CreateUserRequest.class, UserResponse.class, ErrorResponse.class
})
@RestController
@RequestMapping("/users")
class UserController {
    private final UserRegistrationService svc;
    UserController(UserRegistrationService svc) { this.svc = svc; }

    @PostMapping
    public UserResponse create(@RequestBody CreateUserRequest req) {
        return svc.register(req);
    }

    @GetMapping
    public List<UserResponse> list() { return svc.findAll(); }
}

// @ImportRuntimeHints on @SpringBootApplication for library-level hints
@ImportRuntimeHints(LegacyCryptoHints.class)
@SpringBootApplication
public class ImportHintsAdvanced {
    public static void main(String[] args) {
        SpringApplication.run(ImportHintsAdvanced.class, args);
    }
}
```

How to run: `./mvnw spring-boot:run` — test with `curl -XPOST localhost:8080/users -H 'Content-Type:application/json' -d '{"name":"Alice","email":"alice@ex.com"}'`

`@RegisterReflectionForBinding` on `UserController` registers all three DTO classes for the full binding category set needed by Jackson. `@ImportRuntimeHints(LegacyCryptoHints.class)` on `@SpringBootApplication` ensures the legacy crypto library's classes are included in the native binary — placed at the top-level application class since it applies globally. During `./mvnw -Pnative native:compile`, all these hints flow into `reflect-config.json` and `resource-config.json`.

## 6. Walkthrough

Tracing what happens when `spring-boot:process-aot` runs on `ImportHintsAdvanced`:

**Step 1 — AOT engine starts analysis context:**
- Discovers all `@Component` / `@Configuration` / `@RestController` beans.
- Collects all annotations on each bean's class for AOT processing.

**Step 2 — Process `UserController`:**
- AOT engine sees `@RegisterReflectionForBinding({CreateUserRequest.class, UserResponse.class, ErrorResponse.class})`.
- Invokes the internal `ReflectionForBindingRegistrar` for each type.
- For `UserResponse`:
  - `hints.reflection().registerType(UserResponse.class, INVOKE_PUBLIC_CONSTRUCTORS, INVOKE_DECLARED_CONSTRUCTORS, PUBLIC_FIELDS, DECLARED_FIELDS, INVOKE_PUBLIC_METHODS, INVOKE_DECLARED_METHODS)` — all 6 categories.
  - Recursively visits field types: `String` (already JDK-included, no extra hint needed).

**Step 3 — Process `ImportHintsAdvanced`:**
- AOT engine sees `@ImportRuntimeHints(LegacyCryptoHints.class)`.
- Instantiates `new LegacyCryptoHints()`.
- Calls `registerHints(hints, classLoader)`.
- Inside: registers `com.legacy.CryptoHelper` (by `TypeReference.of(String)` — no classpath presence required at AOT time) and `crypto/keystore.jks` resource.

**Step 4 — Serialisation:**
- `reflect-config.json` contains entries for all three DTOs + `CryptoHelper`.
- `resource-config.json` contains `crypto/keystore.jks`.

**Step 5 — Native runtime (`POST /users`):**
- Jackson receives `{"name":"Alice","email":"alice@ex.com"}`.
- Jackson calls `CreateUserRequest.class.getDeclaredConstructors()[0].newInstance("Alice","alice@ex.com")` — succeeds because `INVOKE_DECLARED_CONSTRUCTORS` was registered.
- Response serialisation: Jackson calls `getId()`, `getName()`, etc. — succeeds because `INVOKE_PUBLIC_METHODS` was registered.
- Response: `{"id":"u1","name":"Alice","email":"alice@ex.com","status":"ACTIVE"}`

## 7. Gotchas & takeaways

> **`@RegisterReflectionForBinding` does NOT register for Java `ObjectOutputStream` serialization.** It only covers reflection-based binding (Jackson, Spring MVC model binding). If you need `ObjectOutputStream` / `ObjectInputStream` for the same class, add a separate `hints.serialization().registerType(...)` call.

> **Placing `@RegisterReflectionForBinding` on an interface registers the interface, not its implementations.** For a polymorphic Jackson type hierarchy, annotate each concrete subclass individually (or use a `RuntimeHintsRegistrar` that iterates the known subtypes).

- `@RegisterReflectionForBinding` is composable with `@Service`, `@Configuration`, `@RestController`, and any other Spring annotation — the AOT engine handles it wherever it appears on a Spring-managed bean class.
- `@ImportRuntimeHints` accepts an array: `@ImportRuntimeHints({HintsA.class, HintsB.class})` — each registrar is invoked in array order.
- If a `RuntimeHintsRegistrar` registered via `@ImportRuntimeHints` has Spring bean dependencies, those are NOT injected — registrars must be instantiatable with `new` (no-arg constructor). Use `classLoader.loadClass()` or `ClassUtils.resolveClassName()` for dynamic type references instead.
- Both annotations are meta-annotatable: you can create a custom annotation like `@MyApiHints` that is itself annotated with `@ImportRuntimeHints` and `@RegisterReflectionForBinding` — useful for module-level hint bundles.
