---
card: spring-boot
gi: 80
slug: configurationproperties-validation-validated
title: "@ConfigurationProperties validation (@Validated)"
---

## 1. What it is

Adding `@Validated` to a `@ConfigurationProperties` class activates **Bean Validation (JSR-303 / Jakarta Validation)** on that class at startup. Spring Boot evaluates every constraint annotation you place on the fields — `@NotNull`, `@Min`, `@Max`, `@Size`, `@Pattern`, `@Email`, `@Valid` for nested objects, and so on — and collects **all** failures before throwing a single, descriptive `BindException`. The application does not start if any constraint is violated.

This is the standard way to make misconfigured environments fail fast: instead of discovering at runtime that a required database URL is missing or a thread-pool size is negative, the problem surfaces the moment the application context is created.

## 2. Why & when

Without validation you have two bad options: trust that environment-specific properties are correct (and crash later with a confusing `NullPointerException`), or scatter manual `if (value == null) throw …` checks through your service code.

`@Validated` gives you a third, far better option: **declare constraints once on the properties class and let the framework enforce them at the earliest possible moment**.

Use it when:

- A property is **required** and the app cannot do meaningful work without it (`@NotBlank`, `@NotNull`).
- A numeric property must be in a range (`@Min`, `@Max`, `@Positive`).
- A string property must match a specific format (`@Pattern`, `@Email`, `@URL`).
- A nested configuration object must itself be valid (`@Valid`).
- You want a **clear, consolidated error message** listing every misconfiguration in one place instead of one crash at the first use.

## 3. Core concept

Spring Boot uses the `ConfigurationPropertiesBindingPostProcessor` to bind properties to your class. When `@Validated` is present it also asks the `SmartValidator` to run all JSR-303 constraint annotations.

The validation happens in two phases:

1. **Binding** — property strings are converted and set on the object.
2. **Validation** — the fully populated object (including nested objects when `@Valid` is on a field) is handed to the validator.

All violations from the second phase are gathered into a single `BindException` whose message lists each property path, the rejected value, and the constraint message. This fail-fast-and-report-everything behaviour is different from request-level Bean Validation (which stops at the first error by default).

**Dependency required:** you need a JSR-303 implementation on the classpath. The Spring Boot starter `spring-boot-starter-validation` pulls in Hibernate Validator, which is the standard implementation.

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
```

## 4. Diagram

<svg viewBox="0 0 680 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Startup validation flow: properties bound to class, then validator checks all constraints, errors collected into BindException">
  <rect x="10" y="10" width="660" height="300" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>

  <!-- Title -->
  <text x="340" y="38" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Startup Validation Flow</text>

  <!-- Step 1 -->
  <rect x="30" y="60" width="140" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="100" y="86" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">application</text>
  <text x="100" y="104" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">.properties</text>

  <!-- Arrow 1 -->
  <line x1="172" y1="90" x2="218" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>
  <defs>
    <marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="a3ok" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a3err" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>

  <!-- Step 2: Binding -->
  <rect x="220" y="55" width="150" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="295" y="80" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Binding</text>
  <text x="295" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">ConfigurationProperties</text>
  <text x="295" y="112" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">BindingPostProcessor</text>

  <!-- Arrow 2 -->
  <line x1="372" y1="90" x2="418" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#a2)"/>

  <!-- Step 3: Validation -->
  <rect x="420" y="55" width="150" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="495" y="80" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Validation</text>
  <text x="495" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">SmartValidator</text>
  <text x="495" y="112" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">(Hibernate Validator)</text>

  <!-- OK path -->
  <line x1="495" y1="127" x2="495" y2="180" stroke="#3fb950" stroke-width="2" marker-end="url(#a3ok)"/>
  <text x="510" y="158" fill="#3fb950" font-size="11" font-family="sans-serif">OK</text>
  <rect x="420" y="182" width="150" height="44" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="495" y="200" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">Context starts</text>
  <text x="495" y="216" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">App is live</text>

  <!-- Error path -->
  <line x1="420" y1="160" x2="260" y2="210" stroke="#f85149" stroke-width="2" marker-end="url(#a3err)"/>
  <text x="320" y="200" fill="#f85149" font-size="11" font-family="sans-serif">violations</text>
  <rect x="140" y="212" width="220" height="60" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="250" y="235" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">BindException</text>
  <text x="250" y="253" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">all constraint failures listed</text>
  <text x="250" y="266" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">App does NOT start</text>

  <!-- Legend -->
  <rect x="30" y="200" width="14" height="14" rx="2" fill="#3fb950"/>
  <text x="52" y="212" fill="#8b949e" font-size="10" font-family="sans-serif">All constraints pass</text>
  <rect x="30" y="222" width="14" height="14" rx="2" fill="#f85149"/>
  <text x="52" y="234" fill="#8b949e" font-size="10" font-family="sans-serif">Any violation → fail fast</text>
</svg>

All constraint violations are gathered before the context finishes starting, giving a single diagnostic message that lists every misconfigured property.

## 5. Runnable example

```java
// src/main/java/com/example/demo/ServerProperties.java
package com.example.demo;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;
import org.springframework.validation.annotation.Validated;

@Component
@ConfigurationProperties(prefix = "demo.server")
@Validated
public class ServerProperties {

    /** Required — app cannot work without a host. */
    @NotBlank(message = "demo.server.host must not be blank")
    private String host;

    /** Must be in the valid port range. */
    @Min(value = 1, message = "Port must be >= 1")
    @Max(value = 65535, message = "Port must be <= 65535")
    private int port = 8080;

    /** Must look like a valid e-mail address. */
    @Email(message = "demo.server.admin-email must be a valid email address")
    private String adminEmail;

    /** Must match a simple label pattern. */
    @Pattern(regexp = "^[a-z][a-z0-9-]{2,30}$",
             message = "demo.server.env must start with a letter, be 3-31 chars, lowercase/digits/hyphens")
    private String env;

    /** Nested object — @Valid triggers recursive validation. */
    @Valid
    @NotNull
    private Tls tls = new Tls();

    // --- getters / setters ---
    public String getHost()               { return host; }
    public void setHost(String h)         { this.host = h; }
    public int getPort()                  { return port; }
    public void setPort(int p)            { this.port = p; }
    public String getAdminEmail()         { return adminEmail; }
    public void setAdminEmail(String e)   { this.adminEmail = e; }
    public String getEnv()                { return env; }
    public void setEnv(String e)          { this.env = e; }
    public Tls getTls()                   { return tls; }
    public void setTls(Tls t)            { this.tls = t; }

    /** Nested configuration for TLS settings. */
    public static class Tls {
        @NotBlank(message = "demo.server.tls.keystore-path must not be blank")
        private String keystorePath;

        @Size(min = 8, message = "demo.server.tls.keystore-password must be at least 8 chars")
        private String keystorePassword;

        public String getKeystorePath()             { return keystorePath; }
        public void setKeystorePath(String p)       { this.keystorePath = p; }
        public String getKeystorePassword()          { return keystorePassword; }
        public void setKeystorePassword(String pw)  { this.keystorePassword = pw; }
    }
}

// -----------------------------------------------------------------------
// src/main/java/com/example/demo/DemoApplication.java
package com.example.demo;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class DemoApplication implements CommandLineRunner {

    @Autowired ServerProperties props;

    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }

    @Override
    public void run(String... args) {
        System.out.println("Server host : " + props.getHost());
        System.out.println("Server port : " + props.getPort());
        System.out.println("Admin email : " + props.getAdminEmail());
        System.out.println("Environment : " + props.getEnv());
        System.out.println("Keystore    : " + props.getTls().getKeystorePath());
    }
}
```

`application.properties` with valid values:

```properties
demo.server.host=api.example.com
demo.server.port=9090
demo.server.admin-email=ops@example.com
demo.server.env=production
demo.server.tls.keystore-path=/etc/certs/keystore.p12
demo.server.tls.keystore-password=s3cr3tPW!
```

To trigger a validation failure, remove `demo.server.host` or set `demo.server.port=99999`.

**How to run:** `./mvnw spring-boot:run`. With the valid properties above, the app starts and prints all values. With an invalid property the app exits immediately, printing every violated constraint.

## 6. Walkthrough

- **`@Validated`** on `ServerProperties` is the key annotation. Without it, Spring Boot binds the properties but never runs JSR-303 constraints — the class just silently holds invalid values.
- **`@NotBlank` on `host`** — `@NotBlank` is stricter than `@NotNull`: it rejects blank strings too. Removing the property from `application.properties` makes it `null`, which fails `@NotBlank`.
- **`@Min(1)` + `@Max(65535)` on `port`** — two constraints on one field. If `port=99999`, both validators run and the violation message from `@Max` appears in the `BindException`.
- **`@Email` on `adminEmail`** — Hibernate Validator checks the address format using an RFC-compliant regex. `"not-an-email"` would fail.
- **`@Pattern` on `env`** — the regex enforces a naming convention. The constraint message is attached to the property path `demo.server.env` in the error output.
- **`@Valid` on the nested `tls` field** — without `@Valid`, Spring Boot only validates the top-level object; the `Tls` inner class constraints are ignored. Adding `@Valid` tells the validator to recurse into the nested object and apply `@NotBlank` and `@Size` there too.
- The startup error message looks like: `Property: demo.server.host / Value: null / Reason: must not be blank`. Multiple violations appear as a numbered list in the same exception.

## 7. Gotchas & takeaways

> **`@Valid` on nested fields is required — it is not automatic.** If your `@ConfigurationProperties` class has a field whose type is another object that carries constraints, you must annotate the field with `@Valid` or those inner constraints are silently skipped.

> **`spring-boot-starter-validation` must be on the classpath.** If Hibernate Validator is absent, `@Validated` is silently ignored — no exception, no error, just missing validation. Always confirm the dependency is present.

- `@Validated` is a Spring annotation (not JSR-303), but it triggers the standard JSR-303 validation pipeline.
- Unlike request-body validation (which can stop at the first error), `@ConfigurationProperties` validation collects **all** violations before reporting.
- Constraint messages appear as the property path (e.g. `demo.server.tls.keystore-path`) + the rejected value + the message string.
- For lists of nested objects, place `@Valid` on the list field and add constraints to the element type; Spring Boot validates each element.
- You can define custom `@Constraint` annotations (with a `ConstraintValidator` implementation) and use them on properties classes exactly as you would on JPA entities or REST request bodies.
