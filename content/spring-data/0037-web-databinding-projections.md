---
card: spring-data
gi: 37
slug: web-databinding-projections
title: "Web databinding & projections"
---

## 1. What it is

Beyond resolving `Pageable`/`Sort` and converting path variables into entities, Spring Data's web support also lets a controller method accept a projection interface (covered earlier in this section) directly as a `@RequestBody`, letting incoming JSON bind straight to a narrowed, purpose-built interface rather than the full entity — and, combined with `@JsonPath`-based open projections, lets that binding pull values from arbitrarily-nested locations in the incoming request body.

```java
public interface CustomerInput {
    String getFirstName();
    String getLastName();
}

@PostMapping("/customers")
Customer create(@RequestBody CustomerInput input) {
    return repo.save(new Customer(input.getFirstName(), input.getLastName()));
}
```

## 2. Why & when

A `@RequestBody` normally deserializes JSON into a concrete class with a matching constructor or setters — binding it to an *interface* instead means the actual runtime type is a Spring Data-generated proxy, exactly like the read-side interface projections from earlier in this section, just operating on incoming data instead of query results. This is useful specifically for input validation and API-contract narrowing: a `CustomerInput` interface makes explicit exactly which fields a "create customer" endpoint accepts, independent of (and potentially narrower than) whatever fields the full `Customer` entity happens to have.

Reach for projection-based request binding specifically when:

- You want an API's accepted input shape to be an explicit, narrow interface — rather than accepting a full entity (or a loosely-typed `Map`) and hoping callers only send the fields you actually process.
- You're consuming a JSON payload with a different structure than your domain entity (nested fields, differently-named fields) and want to map it declaratively rather than writing manual JSON-tree navigation code.
- You want the same declarative getter-interface style used for read-side projections to also apply on the write/input side, for consistency across a codebase's API layer.

## 3. Core concept

```
 @RequestBody CustomerInput input
        |
        v
 Spring Data's projection-aware HttpMessageConverter support recognizes
 CustomerInput is a projection interface (not a concrete class), and:
   1. deserializes the raw JSON into an intermediate Map/tree representation
   2. wraps it in a PROXY implementing CustomerInput
   3. each getter call on the proxy reads the corresponding value from
      that underlying JSON tree

 CLOSED input projection:
   getFirstName() -- reads JSON field "firstName" directly

 OPEN input projection (via @JsonPath, the write-side analogue of @Value
 for read-side open projections):
   @JsonPath("$.contact.email")
   String getEmail();     -- reads from a NESTED location in the JSON body
```

The mechanism mirrors read-side projections closely: a proxy generated at binding time, backed by the actual incoming data, with closed getters mapping directly and `@JsonPath`-annotated getters reaching into nested structure.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Incoming JSON is wrapped in a generated proxy implementing the projection interface, with getters reading from the parsed JSON tree">
  <rect x="10" y="20" width="220" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">incoming JSON body</text>
  <text x="120" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">{"firstName":"Ada",...}</text>

  <rect x="270" y="20" width="220" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="380" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CustomerInput proxy</text>
  <text x="380" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getFirstName() reads the JSON tree</text>

  <rect x="530" y="20" width="100" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="580" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">"Ada"</text>

  <line x1="230" y1="47" x2="265" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="490" y1="47" x2="525" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The proxy defers reading each field until the corresponding getter is actually called, backed by the parsed request body.

## 5. Runnable example

The scenario: a customer-creation endpoint, evolving from a basic closed input projection, to `@JsonPath` reaching into nested request JSON, to confirming the input projection narrows what the endpoint can access even if the client sends extra fields.

### Level 1 — Basic

Bind `@RequestBody` to a closed projection interface and confirm the flat JSON fields map directly.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.server.ServletWebServerApplicationContext;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@SpringBootApplication
@RestController
public class WebProjectionLevel1 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String firstName;
        private String lastName;
        protected Customer() {}
        public Customer(String firstName, String lastName) { this.firstName = firstName; this.lastName = lastName; }
        public String getFirstName() { return firstName; }
        public String getLastName() { return lastName; }
    }

    public interface CustomerInput {
        String getFirstName();
        String getLastName();
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}

    private final CustomerRepository repo;
    public WebProjectionLevel1(CustomerRepository repo) { this.repo = repo; }

    @PostMapping("/customers")
    public String create(@RequestBody CustomerInput input) {
        Customer saved = repo.save(new Customer(input.getFirstName(), input.getLastName()));
        return "Created: " + saved.getFirstName() + " " + saved.getLastName();
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(WebProjectionLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:webproj1",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/customers"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString("{\"firstName\":\"Ada\",\"lastName\":\"Lovelace\"}"))
            .build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("response = " + response.body());

        if (!response.body().equals("Created: Ada Lovelace"))
            throw new AssertionError("Expected the flat JSON fields to bind directly to CustomerInput");
        System.out.println("Closed input projection bound flat JSON fields correctly -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa`, `spring-boot-starter-web`, and `com.h2database:h2` on the classpath, then `java WebProjectionLevel1.java` on JDK 17+.

`CustomerInput` declares only `getFirstName()`/`getLastName()` — Spring's `HttpMessageConverter` support recognizes it's a projection interface (not a concrete class Jackson could directly instantiate) and, since Spring Data's web support is active, wraps the parsed JSON in a proxy implementing it, reading each getter's value directly from the corresponding JSON field.

### Level 2 — Intermediate

Use `@JsonPath` on an open input projection getter to pull a value from a nested location in the request body.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.server.ServletWebServerApplicationContext;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.web.JsonPath;
import org.springframework.data.web.ProjectedPayload;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@SpringBootApplication
@RestController
public class WebProjectionLevel2 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private String email;
        protected Customer() {}
        public Customer(String name, String email) { this.name = name; this.email = email; }
        public String getName() { return name; }
        public String getEmail() { return email; }
    }

    // @ProjectedPayload enables @JsonPath support for this input projection.
    @ProjectedPayload
    public interface CustomerInput {
        @JsonPath("$.name")
        String getName();

        @JsonPath("$.contact.email") // reaches into a NESTED object in the request body
        String getEmail();
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}

    private final CustomerRepository repo;
    public WebProjectionLevel2(CustomerRepository repo) { this.repo = repo; }

    @PostMapping("/customers")
    public String create(@RequestBody CustomerInput input) {
        Customer saved = repo.save(new Customer(input.getName(), input.getEmail()));
        return "Created: " + saved.getName() + " <" + saved.getEmail() + ">";
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(WebProjectionLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:webproj2",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();
        String nestedJson = "{\"name\":\"Grace Hopper\",\"contact\":{\"email\":\"grace@example.com\",\"phone\":\"555-1234\"}}";
        HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/customers"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(nestedJson))
            .build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("response = " + response.body());

        if (!response.body().equals("Created: Grace Hopper <grace@example.com>"))
            throw new AssertionError("Expected @JsonPath to extract the nested email correctly");
        System.out.println("@JsonPath pulled a value from a nested JSON location -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, plus `com.jayway.jsonpath:json-path` on the classpath (required for `@JsonPath` support). Run `java WebProjectionLevel2.java`.

`@ProjectedPayload` marks `CustomerInput` as supporting `@JsonPath`-based open getters. `getEmail()`'s `@JsonPath("$.contact.email")` reaches into the nested `contact` object in the incoming JSON, even though `CustomerInput` has no `getContact()` method at all — the JSONPath expression navigates the request tree directly, entirely independent of the interface's own declared getter structure.

### Level 3 — Advanced

Confirm the input projection genuinely narrows what data reaches application code, even when the client sends extra, unexpected fields — demonstrating the projection as an API-contract boundary, not merely a convenience.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.server.ServletWebServerApplicationContext;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Arrays;

@SpringBootApplication
@RestController
public class WebProjectionLevel3 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private boolean isAdmin = false; // a SENSITIVE field the input projection deliberately excludes
        protected Customer() {}
        public Customer(String name) { this.name = name; }
        public String getName() { return name; }
        public boolean isAdmin() { return isAdmin; }
    }

    // Deliberately does NOT declare an "isAdmin" getter -- even if a malicious
    // client sends isAdmin:true in the request body, this interface has no way
    // to expose it to the controller at all.
    public interface CustomerInput {
        String getName();
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}

    private final CustomerRepository repo;
    public WebProjectionLevel3(CustomerRepository repo) { this.repo = repo; }

    @PostMapping("/customers")
    public String create(@RequestBody CustomerInput input) {
        // No matter what the raw JSON contained, CustomerInput physically
        // cannot expose an "isAdmin" value -- the entity is always created
        // with the SAFE default (isAdmin=false).
        Customer saved = repo.save(new Customer(input.getName()));
        return "Created: " + saved.getName() + ", isAdmin=" + saved.isAdmin();
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(WebProjectionLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:webproj3",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();
        // A malicious/careless client attempts to sneak in isAdmin:true.
        String maliciousJson = "{\"name\":\"Attacker\",\"isAdmin\":true}";
        HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/customers"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(maliciousJson))
            .build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("response = " + response.body());

        boolean noGetIsAdminMethod = Arrays.stream(CustomerInput.class.getMethods())
            .noneMatch(m -> m.getName().toLowerCase().contains("admin"));

        if (!noGetIsAdminMethod) throw new AssertionError("CustomerInput should have NO way to expose isAdmin at all");
        if (!response.body().equals("Created: Attacker, isAdmin=false"))
            throw new AssertionError("Expected isAdmin to remain false regardless of the attempted injected field");

        System.out.println("Input projection interface narrowed the API contract, ignoring the unexpected isAdmin field -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java WebProjectionLevel3.java`.

The client's JSON body includes `"isAdmin":true`, attempting to influence a field the entity has — but `CustomerInput` declares no `getIsAdmin()`/`isAdmin()` method at all, so there is no possible way for the controller code (or the underlying proxy) to expose that value, regardless of what the raw request body contains. This is the same "narrow the exposed surface via the interface" pattern used for read-side projections earlier in this section, applied here to defend against unintended or malicious over-posting of fields on the write side.

## 6. Walkthrough

Trace the `POST /customers` request in Level 3.

1. **Request arrives** with body `{"name":"Attacker","isAdmin":true}`.
2. **Argument resolution for `@RequestBody CustomerInput input`**: Spring's message-converter machinery recognizes `CustomerInput` as a projection interface (not directly instantiable by Jackson) and parses the raw JSON into an intermediate tree representation, then wraps it in a generated proxy implementing `CustomerInput`.
3. **Proxy construction**: the proxy is built purely from `CustomerInput`'s declared method set — since only `getName()` exists on the interface, the proxy only knows how to answer that one method; it has no method (and therefore no code path) corresponding to `isAdmin`, regardless of what's present in the underlying JSON tree.
4. **Controller method executes**: `input.getName()` returns `"Attacker"` (read correctly from the JSON). There is no `input.getIsAdmin()` call anywhere in the method, because no such method exists to call — `new Customer(input.getName())` uses the entity's constructor, which leaves `isAdmin` at its default value, `false`.
5. **Persistence**: `repo.save(...)` writes this new `Customer` — with `isAdmin` genuinely `false` in the database, not merely `false` in this one response.
6. **Response**: the method returns a string confirming the saved state, including `isAdmin=false`.
7. **Reflection check**: `CustomerInput.class.getMethods()` is inspected directly, confirming no method related to `admin` exists on the interface at all — concrete proof this isn't merely "the controller chose not to read it this time," but a structural impossibility given the interface's declared contract.
8. **Verification**: the program checks both the reflection result and the actual saved entity state, confirming the projection interface's narrow contract successfully prevented the injected field from having any effect.

```
 POST /customers  body: {"name":"Attacker","isAdmin":true}
        |
        v
 CustomerInput proxy generated from the JSON tree
        |
        v
 proxy's method set = ONLY getName()  (isAdmin has NO corresponding method at all)
        |
        v
 controller code CANNOT call anything related to isAdmin -- it doesn't exist
        |
        v
 new Customer("Attacker")  --  isAdmin defaults to false, unaffected by the request body
```

## 7. Gotchas & takeaways

> **Gotcha:** this narrowing protection only holds as long as the controller genuinely relies on the projection interface's declared methods and never falls back to a raw `Map`/`JsonNode` parameter or manual JSON parsing alongside it — mixing an input projection with a separate, unrestricted access path to the same raw request body (for "just this one extra field") reopens exactly the over-posting risk the projection was meant to close.

- Input projections mirror read-side projections closely: a proxy generated at binding time from the actual request data, with closed getters mapping directly and `@JsonPath`-annotated (open) getters reaching into arbitrarily nested request structure.
- `@JsonPath` (requiring `@ProjectedPayload` on the interface and the `json-path` library on the classpath) is the write-side analogue of `@Value`/SpEL for read-side open projections — both let a getter compute or extract a value beyond a simple 1:1 field mapping.
- Declaring a narrow input projection interface is a genuine, structural defense against over-posting (a client sneaking extra, unintended fields into a request body) — the controller code physically cannot access a field the interface doesn't declare a getter for.
- Spring Boot's auto-configuration typically activates this projection-aware request-body binding implicitly, the same way it implicitly activates the rest of Spring Data's web support covered throughout this section.
