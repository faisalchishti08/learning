---
card: java
gi: 5
slug: jakarta-ee-java-ee-enterprise-edition
title: Jakarta EE / Java EE (Enterprise Edition)
---

## 1. What it is

**Jakarta EE** (formerly Java EE — Java Platform, Enterprise Edition) is a set of specifications that extend Java SE for building large-scale, multi-tier enterprise applications. Where Java SE provides the language, JVM, and core libraries, Jakarta EE adds APIs for web applications (Servlets, JSP, JSF), RESTful web services (JAX-RS), persistence (JPA), messaging (JMS), dependency injection (CDI), transactions (JTA), and more.

Jakarta EE is not a product — it is a collection of specifications. Implementations include **WildFly (JBoss)**, **GlassFish**, **Payara**, **Open Liberty**, and **TomEE**. Spring Boot is a popular *alternative* that cherry-picks some Jakarta EE specs (JPA, Bean Validation) while replacing others (CDI → Spring's DI, Servlets → Spring MVC/WebFlux).

## 2. Why & when

Java EE was created in 1999 to address the complexity of distributed, transactional enterprise software that Java SE alone could not handle: connection pooling, distributed transactions, message queues, session beans managing stateful workflows. The cost: complexity and heavyweight containers.

Jakarta EE matters today because:
- Many large enterprises still run on Jakarta EE application servers (WebSphere, WildFly, Payara).
- Spring Boot relies on Jakarta EE specs under the hood: Hibernate implements JPA, Tomcat implements Servlet, Bean Validation (Hibernate Validator) is a Jakarta EE spec.
- Jakarta EE 10 (2022) is modern, modular, and runs on GraalVM.
- Understanding the specs helps you debug Spring applications — a `@Transactional` annotation in Spring calls the Jakarta Transactions API under the covers.

You use Jakarta EE directly when deploying WARs/EARs to an application server, or indirectly through Spring Boot every day.

## 3. Core concept

Jakarta EE defines a **container model**: your application code runs inside a *container* (the application server) that provides services — lifecycle management, transaction demarcation, security, dependency injection — without you wiring them explicitly.

Key specs and their roles:

| Spec | Package (new) | What it does |
|---|---|---|
| Servlet | `jakarta.servlet` | HTTP request/response cycle |
| JAX-RS | `jakarta.ws.rs` | RESTful web services |
| JPA | `jakarta.persistence` | ORM / database persistence |
| CDI | `jakarta.enterprise.inject` | Dependency injection |
| JTA | `jakarta.transaction` | Distributed transactions |
| JMS | `jakarta.jms` | Message queues |
| Bean Validation | `jakarta.validation` | Constraint validation |
| EJB | `jakarta.ejb` | (Legacy) Enterprise beans |

**The namespace migration:** In 2019 Oracle transferred Java EE to the Eclipse Foundation. The new home required renaming all `javax.*` packages to `jakarta.*` (completed in Jakarta EE 9). This is why Spring Boot 3.x requires Jakarta EE 9+ — it migrated from `javax.servlet` to `jakarta.servlet`.

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Jakarta EE sits on top of Java SE, with application server as the container">
  <defs>
    <marker id="ajee" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- Java SE base -->
  <rect x="40" y="190" width="600" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="212" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Java SE (JVM + core libs)</text>
  <text x="340" y="229" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">java.lang · java.util · java.io · java.net · java.security</text>

  <!-- Jakarta EE container -->
  <rect x="40" y="100" width="600" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="340" y="120" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Jakarta EE Application Server Container</text>

  <!-- Spec boxes inside -->
  <rect x="55"  y="128" width="80" height="38" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="95"  y="145" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Servlet</text>
  <text x="95"  y="158" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">JAX-RS</text>

  <rect x="145" y="128" width="80" height="38" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="185" y="145" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">JPA</text>
  <text x="185" y="158" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">JTA</text>

  <rect x="235" y="128" width="80" height="38" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="275" y="145" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">CDI</text>
  <text x="275" y="158" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Bean Val.</text>

  <rect x="325" y="128" width="80" height="38" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="365" y="145" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">JMS</text>
  <text x="365" y="158" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">EJB</text>

  <rect x="415" y="128" width="80" height="38" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="455" y="145" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">JSON-P</text>
  <text x="455" y="158" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">JSON-B</text>

  <rect x="505" y="128" width="120" height="38" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="565" y="145" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Security · WebSocket</text>
  <text x="565" y="158" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Concurrency</text>

  <!-- Application -->
  <rect x="200" y="28" width="280" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="340" y="52" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Your Application (WAR / EAR)</text>
  <text x="340" y="70" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">uses Jakarta EE APIs</text>
  <line x1="340" y1="88" x2="340" y2="99" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ajee)"/>
  <line x1="340" y1="180" x2="340" y2="189" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ajee)"/>
</svg>

Your app uses Jakarta EE APIs; the container provides the implementation; Java SE is the foundation.

## 5. Runnable example

Scenario: a minimal Jakarta EE–style Bean Validation check, using the `jakarta.validation` spec API. This spec is also used by Spring Boot via Hibernate Validator — the same code compiles under both.

### Level 1 — Basic

```java
// JeeNamespace.java
// Shows the javax -> jakarta namespace migration: the key breaking change between EE 8 and EE 9+
public class JeeNamespace {
    public static void main(String[] args) {
        System.out.println("Jakarta EE namespace migration:");
        System.out.println("  Jakarta EE ≤ 8 (Java EE) : javax.servlet, javax.persistence, javax.inject ...");
        System.out.println("  Jakarta EE  ≥ 9           : jakarta.servlet, jakarta.persistence, jakarta.inject ...");
        System.out.println();
        System.out.println("Spring Boot 2.x → Spring Boot 3.x required updating ALL imports.");
        System.out.println("Any Jakarta EE spec on classpath: " + hasJakartaValidation());
    }

    static String hasJakartaValidation() {
        try {
            Class.forName("jakarta.validation.Validation");
            return "jakarta.validation.Validation FOUND";
        } catch (ClassNotFoundException e1) {
            try {
                Class.forName("javax.validation.Validation");
                return "javax.validation.Validation FOUND (old javax namespace)";
            } catch (ClassNotFoundException e2) {
                return "neither on classpath (need Hibernate Validator JAR)";
            }
        }
    }
}
```

**How to run:** `java JeeNamespace.java`

No extra JARs needed — this probes the classpath reflectively. On a plain JDK you'll see "neither on classpath"; on a Spring Boot project classpath you'd find `jakarta.validation`.

### Level 2 — Intermediate

Same scenario: manually simulate what Bean Validation's `@NotBlank` + `@Size` would do — write the constraint logic by hand to show what the spec abstracts away.

```java
// ManualBeanValidation.java
import java.util.*;

public class ManualBeanValidation {

    record User(String name, String email, int age) {}

    // Simulate @NotBlank + @Size(min=3, max=50) + @Min(18) without any framework
    static List<String> validate(User u) {
        List<String> errors = new ArrayList<>();
        if (u.name() == null || u.name().isBlank())
            errors.add("name: must not be blank");
        else if (u.name().length() < 3 || u.name().length() > 50)
            errors.add("name: size must be between 3 and 50 (was " + u.name().length() + ")");

        if (u.email() == null || !u.email().contains("@"))
            errors.add("email: must be a well-formed email address");

        if (u.age() < 18)
            errors.add("age: must be greater than or equal to 18 (was " + u.age() + ")");

        return errors;
    }

    public static void main(String[] args) {
        List<User> users = List.of(
            new User("Alice", "alice@example.com", 25),
            new User("",      "bob-at-example",    16),
            new User("Jo",    "jo@x.com",          30)
        );

        for (User u : users) {
            List<String> errors = validate(u);
            if (errors.isEmpty()) {
                System.out.println("VALID   : " + u);
            } else {
                System.out.println("INVALID : " + u);
                errors.forEach(e -> System.out.println("  -> " + e));
            }
        }
        System.out.println("\nIn real Jakarta EE / Spring Boot: replace this with @Valid + BindingResult.");
    }
}
```

**How to run:** `java ManualBeanValidation.java`

This is what `@NotBlank`, `@Size`, `@Min` do internally — the Jakarta EE Bean Validation spec defines the contract; Hibernate Validator implements it; Spring Boot auto-configures it. Now you've seen the mechanics by hand.

### Level 3 — Advanced

Same scenario grown to model a full Jakarta EE service request lifecycle: CDI-style injection simulation, manual transaction boundary, and structured constraint violations — mimicking what happens inside an EE container without one.

```java
// EELifecycleSimulation.java
import java.util.*;
import java.util.function.*;

public class EELifecycleSimulation {

    // ── Domain ───────────────────────────────────────────────────────────
    record User(String name, String email, int age) {}

    record ValidationError(String field, String message) {
        @Override public String toString() { return field + ": " + message; }
    }

    // ── "CDI bean" — simulated injectable service ─────────────────────
    static class UserRepository {
        private final Map<String, User> store = new LinkedHashMap<>();
        private boolean txActive = false;

        void beginTransaction() { txActive = true; System.out.println("  [JTA] transaction begin"); }
        void commit()           { txActive = false; System.out.println("  [JTA] transaction committed"); }
        void rollback()         { txActive = false; System.out.println("  [JTA] transaction ROLLED BACK"); }

        void save(User u) {
            if (!txActive) throw new IllegalStateException("No active transaction");
            store.put(u.email(), u);
            System.out.println("  [JPA] persisted: " + u);
        }

        Collection<User> findAll() { return store.values(); }
    }

    // ── "Bean Validation" — simulated constraint checking ────────────
    static List<ValidationError> validate(User u) {
        List<ValidationError> errors = new ArrayList<>();
        if (u.name() == null || u.name().isBlank()) errors.add(new ValidationError("name", "must not be blank"));
        else if (u.name().length() < 2)             errors.add(new ValidationError("name", "size must be >= 2"));
        if (u.email() == null || !u.email().contains("@")) errors.add(new ValidationError("email", "invalid email"));
        if (u.age() < 0 || u.age() > 150)           errors.add(new ValidationError("age", "must be 0..150"));
        return errors;
    }

    // ── "JAX-RS resource method" — simulated HTTP handler ────────────
    static Map<String,Object> createUser(UserRepository repo, User incoming) {
        System.out.println("\n[Servlet/JAX-RS] POST /users  body=" + incoming);

        // Bean Validation
        List<ValidationError> errors = validate(incoming);
        if (!errors.isEmpty()) {
            System.out.println("[Bean Validation] 400 Bad Request");
            errors.forEach(e -> System.out.println("  " + e));
            return Map.of("status", 400, "errors", errors);
        }

        // JTA transaction boundary
        repo.beginTransaction();
        try {
            repo.save(incoming);
            repo.commit();
            System.out.println("[JAX-RS] 201 Created: " + incoming.email());
            return Map.of("status", 201, "user", incoming);
        } catch (Exception ex) {
            repo.rollback();
            return Map.of("status", 500, "error", ex.getMessage());
        }
    }

    public static void main(String[] args) {
        UserRepository repo = new UserRepository();   // simulated @Inject

        List<User> requests = List.of(
            new User("Alice",  "alice@corp.com", 28),
            new User("",       "bad-email",      17),    // two validation errors
            new User("Bob",    "bob@corp.com",   35)
        );

        for (User req : requests) {
            Map<String,Object> response = createUser(repo, req);
            System.out.println("[Response] " + response.get("status"));
        }

        System.out.println("\n=== Final user store ===");
        repo.findAll().forEach(System.out::println);
    }
}
```

**How to run:** `java EELifecycleSimulation.java`

This simulates what an EE container does: receive HTTP → validate → open transaction → persist → commit/rollback → return response. No framework needed — you see the raw mechanics.

## 6. Walkthrough

Execution begins in `main`, which creates a `UserRepository` (simulating CDI injection) and processes three HTTP POST requests in sequence.

**Request 1 — Happy path (`alice@corp.com`):**
```
[Servlet/JAX-RS] POST /users  body=User[name=Alice, email=alice@corp.com, age=28]
  [JTA] transaction begin
  [JPA] persisted: User[name=Alice, email=alice@corp.com, age=28]
  [JTA] transaction committed
[Response] 201
```

Flow: `createUser` → `validate` (no errors) → `repo.beginTransaction()` → `repo.save()` → `repo.commit()` → return `201`. This mirrors exactly what a `@POST @Transactional` JAX-RS resource method does inside WildFly.

**Request 2 — Validation failure (blank name, bad email, underage):**
```
[Servlet/JAX-RS] POST /users  body=User[name=, email=bad-email, age=17]
[Bean Validation] 400 Bad Request
  name: must not be blank
  email: invalid email
[Response] 400
```

`validate()` returns two errors before the transaction even begins. In a real EE container this is handled by `@Valid` on the method parameter — the container calls the Bean Validation engine before invoking the method. No transaction is opened for invalid input.

**Request 3 — Happy path (`bob@corp.com`):** same as request 1.

**Final store:** only Alice and Bob were persisted; the invalid request never reached JPA.

Data state transformations:
```
Incoming User (JSON body from HTTP)
    ↓  Bean Validation (@NotBlank, @Size, @Min)
Validated User
    ↓  JTA begin transaction
    ↓  JPA EntityManager.persist()
    ↓  JTA commit
    ↓  HTTP 201 response
Stored in DB
```

## 7. Gotchas & takeaways

> **The `javax` → `jakarta` namespace migration is a binary-incompatible change.** If your classpath mixes Jakarta EE 8 (`javax.*`) and Jakarta EE 9+ (`jakarta.*`) artifacts you will get `ClassNotFoundException` or `NoSuchMethodError` at runtime, not a compile error. Spring Boot 3 requires Jakarta EE 9+ throughout.

> **CDI proxies and final classes don't mix.** CDI creates subclass-based proxies; a `final` class cannot be subclassed, so CDI injection silently fails or throws at startup. Always make CDI-managed beans non-final (or use Quarkus/Micronaut which use build-time proxies).

- Jakarta EE = collection of specs (Servlet, JPA, CDI, JAX-RS, JTA, …) that run inside a container.
- The container provides DI, transactions, lifecycle management — you write business logic, the container handles the plumbing.
- Spring Boot is not Jakarta EE but heavily uses its specs (JPA via Hibernate, Servlet via Tomcat, Bean Validation via Hibernate Validator).
- LTS pairing: Spring Boot 3.x = Jakarta EE 10 (packages `jakarta.*`); Spring Boot 2.x = Java EE 8 (packages `javax.*`).
- `@Transactional` in both CDI and Spring delegates to the JTA API — same spec, different containers.
- For greenfield projects, Quarkus and Micronaut implement Jakarta EE specs with compile-time optimisation suitable for containers and serverless.
