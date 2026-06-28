---
card: spring-boot
gi: 84
slug: configurationpropertiesbinding-custom-converters
title: "@ConfigurationPropertiesBinding custom converters"
---

## 1. What it is

Spring Boot's built-in `ConversionService` handles common types like `Duration`, `DataSize`, `Period`, `File`, `URL`, enums, and all Java primitives. When you have a **custom domain type** that cannot be constructed from a string by any of these built-in converters, you can write your own.

A `@ConfigurationPropertiesBinding` converter is a Spring bean that implements `org.springframework.core.convert.converter.Converter<String, T>`. Annotating it with `@ConfigurationPropertiesBinding` tells Spring Boot to register it **specifically** in the `ConversionService` used during `@ConfigurationProperties` binding — rather than in the general MVC conversion service. Spring Boot discovers it automatically via component scanning.

The result is that a property value like `"postgres://user:pass@db.local:5432/mydb"` can be transparently bound to a rich `DataSourceDsn` domain object without any manual parsing in your application code.

## 2. Why & when

Built-in converters are fine for standard types. The need for a custom converter appears when:

- You have an existing **DSN (Data Source Name) or URI format** specific to your infrastructure (database, message broker, object storage) that you want parsed into a typed object rather than kept as a raw string.
- An external library defines a type (e.g., `com.acme.ConnectionSpec`) with no Spring-aware factory, and you want to configure it via a property string.
- You have a **compound value** — multiple pieces of data encoded in one string (e.g., `"host:port"`, `"key=value,key=value"`) — that maps to a value object.
- You want to keep property values in a compact, human-readable format in `application.properties` while your application code works with a rich, validated domain object.

## 3. Core concept

The binding pipeline for a `@ConfigurationProperties` field works as follows:

1. Spring resolves the property string from the `Environment`.
2. The `ConfigurationPropertiesBinder` asks the dedicated `ConversionService` whether it can convert `String` to the target field type.
3. If a `@ConfigurationPropertiesBinding` converter exists for that target type, it is invoked.
4. The converter receives the raw string and returns a fully constructed instance of the target type.
5. That instance is set on the field.

The annotation `@ConfigurationPropertiesBinding` is a `@Qualifier` that restricts the converter to the properties-binding `ConversionService`. This is important: a plain `@Component Converter<String, MyType>` without this qualifier would end up registered in the MVC conversion service instead, which can cause unintended side-effects in request parameter binding.

The converter's `convert` method should:
- Parse the string according to your format.
- Throw a descriptive `IllegalArgumentException` (or a subclass) if the string does not conform to the expected format — Spring Boot wraps this in a `BindException` with the property path included.

## 4. Diagram

<svg viewBox="0 0 700 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Custom converter discovery and invocation: annotated converter bean found by component scan, registered in ConfigurationPropertiesBinding ConversionService, invoked during binding">
  <rect x="10" y="10" width="680" height="290" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="350" y="36" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">@ConfigurationPropertiesBinding Converter Lifecycle</text>

  <!-- Step 1: @Component converter -->
  <rect x="25" y="55" width="195" height="80" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="123" y="76" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace" font-weight="bold">DsnConverter</text>
  <text x="123" y="94" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">@Component</text>
  <text x="123" y="110" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">@ConfigurationPropertiesBinding</text>
  <text x="123" y="126" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">Converter&lt;String, DataSourceDsn&gt;</text>

  <!-- Arrow: component scan -->
  <line x1="222" y1="95" x2="270" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#ca1)"/>
  <defs>
    <marker id="ca1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ca2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ca3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="246" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">scan</text>

  <!-- Step 2: Binding ConversionService -->
  <rect x="272" y="55" width="195" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="76" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Binding ConversionService</text>
  <text x="370" y="95" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">@ConfigurationProperties</text>
  <text x="370" y="111" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">Binding only</text>
  <text x="370" y="127" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(separate from MVC)</text>

  <!-- Arrow: invoked during binding -->
  <line x1="469" y1="95" x2="517" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#ca2)"/>
  <text x="493" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">invoke</text>

  <!-- Step 3: conversion -->
  <rect x="519" y="55" width="155" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="597" y="76" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">DataSourceDsn</text>
  <text x="597" y="96" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">scheme: "postgres"</text>
  <text x="597" y="112" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">host: "db.local"</text>
  <text x="597" y="128" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">port: 5432</text>

  <!-- Raw string -->
  <rect x="25" y="165" width="650" height="38" rx="6" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <text x="42" y="180" fill="#8b949e" font-size="10" font-family="monospace">app.dsn =</text>
  <text x="120" y="180" fill="#e6edf3" font-size="10" font-family="monospace">"postgres://user:pass@db.local:5432/mydb"</text>
  <text x="42" y="196" fill="#8b949e" font-size="10" font-family="monospace">                 ↓ DsnConverter.convert(String) → DataSourceDsn</text>

  <!-- Bottom note -->
  <rect x="25" y="222" width="650" height="58" rx="6" fill="#1c2430" stroke="#30363d" stroke-width="1"/>
  <text x="42" y="242" fill="#8b949e" font-size="10" font-family="sans-serif">The @ConfigurationPropertiesBinding qualifier scopes the converter to binding only.</text>
  <text x="42" y="260" fill="#8b949e" font-size="10" font-family="sans-serif">A plain @Component Converter without it lands in the MVC ConversionService — may affect</text>
  <text x="42" y="277" fill="#8b949e" font-size="10" font-family="sans-serif">request parameter binding in controllers unexpectedly.</text>
</svg>

The custom converter is discovered by component scanning, registered only in the properties-binding `ConversionService`, and invoked automatically whenever the binder encounters a field of the matching target type.

## 5. Runnable example

```java
// src/main/java/com/example/demo/DataSourceDsn.java
package com.example.demo;

import java.net.URI;

/**
 * Rich domain object representing a database connection DSN.
 * Format: scheme://user:password@host:port/database
 * Example: postgres://alice:secret@db.local:5432/orders
 */
public class DataSourceDsn {

    private final String scheme;
    private final String username;
    private final String password;
    private final String host;
    private final int    port;
    private final String database;

    public DataSourceDsn(String scheme, String username, String password,
                         String host, int port, String database) {
        this.scheme   = scheme;
        this.username = username;
        this.password = password;
        this.host     = host;
        this.port     = port;
        this.database = database;
    }

    /** Parse from a standard URI string: scheme://user:pass@host:port/db */
    public static DataSourceDsn parse(String raw) {
        URI uri = URI.create(raw);
        if (uri.getScheme() == null || uri.getHost() == null) {
            throw new IllegalArgumentException(
                "Invalid DSN format. Expected scheme://user:pass@host:port/db but got: " + raw);
        }
        String userInfo = uri.getUserInfo();
        String user = "", pass = "";
        if (userInfo != null && userInfo.contains(":")) {
            String[] parts = userInfo.split(":", 2);
            user = parts[0];
            pass = parts[1];
        }
        // getPath() returns "/dbname" — strip the leading slash
        String db = uri.getPath() != null ? uri.getPath().replaceFirst("^/", "") : "";
        return new DataSourceDsn(uri.getScheme(), user, pass, uri.getHost(), uri.getPort(), db);
    }

    public String getScheme()   { return scheme; }
    public String getUsername() { return username; }
    public String getPassword() { return "***"; }    // never log the real password
    public String getHost()     { return host; }
    public int    getPort()     { return port; }
    public String getDatabase() { return database; }

    @Override
    public String toString() {
        return scheme + "://" + username + ":***@" + host + ":" + port + "/" + database;
    }
}

// -----------------------------------------------------------------------
// src/main/java/com/example/demo/DsnConverter.java
package com.example.demo;

import org.springframework.boot.context.properties.ConfigurationPropertiesBinding;
import org.springframework.core.convert.converter.Converter;
import org.springframework.stereotype.Component;

/**
 * Converts a DSN string into a DataSourceDsn domain object during
 * @ConfigurationProperties binding.
 *
 * The @ConfigurationPropertiesBinding qualifier scopes this converter to
 * the properties-binding ConversionService only — it does not affect
 * MVC request-parameter binding.
 */
@Component
@ConfigurationPropertiesBinding
public class DsnConverter implements Converter<String, DataSourceDsn> {

    @Override
    public DataSourceDsn convert(String source) {
        // Throwing IllegalArgumentException causes Spring Boot to wrap it
        // in a BindException with the full property path in the message.
        return DataSourceDsn.parse(source);
    }
}

// -----------------------------------------------------------------------
// src/main/java/com/example/demo/AppProperties.java
package com.example.demo;

import jakarta.validation.constraints.NotNull;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;
import org.springframework.validation.annotation.Validated;

@Component
@ConfigurationProperties(prefix = "app")
@Validated
public class AppProperties {

    /**
     * Full database DSN.
     * Example: postgres://alice:secret@db.local:5432/orders
     */
    @NotNull
    private DataSourceDsn dsn;

    public DataSourceDsn getDsn()              { return dsn; }
    public void setDsn(DataSourceDsn dsn)      { this.dsn = dsn; }
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

    @Autowired AppProperties props;

    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }

    @Override
    public void run(String... args) {
        DataSourceDsn dsn = props.getDsn();
        System.out.println("Scheme   : " + dsn.getScheme());
        System.out.println("User     : " + dsn.getUsername());
        System.out.println("Host     : " + dsn.getHost());
        System.out.println("Port     : " + dsn.getPort());
        System.out.println("Database : " + dsn.getDatabase());
        System.out.println("Full DSN : " + dsn);
    }
}
```

`application.properties`:

```properties
app.dsn=postgres://alice:secret@db.local:5432/orders
```

**How to run:** `./mvnw spring-boot:run`. The DSN string is parsed at startup and the rich `DataSourceDsn` object is available throughout the application. Change the DSN to a malformed string (e.g., `not-a-dsn`) to see a `BindException` with the property path in the error message.

## 6. Walkthrough

- **`DataSourceDsn`** is a plain Java class (no Spring dependencies). It knows how to parse itself from a URI string via the static `DataSourceDsn.parse(String)` factory. Keeping the parsing logic in the domain class (rather than in the converter) makes it testable without Spring.
- **`DsnConverter implements Converter<String, DataSourceDsn>`** — Spring's `Converter` interface has a single method: `DataSourceDsn convert(String source)`. The generic type parameters declare what the converter handles; Spring uses them to match this converter to `DataSourceDsn`-typed fields.
- **`@ConfigurationPropertiesBinding`** on `DsnConverter` — this qualifier is how Spring Boot knows to register the converter in the dedicated properties-binding `ConversionService`. Without it, the converter would be registered in the general `ConversionService` and might interfere with MVC parameter binding.
- **`@Component`** on `DsnConverter` — makes it a Spring bean so it is discovered by component scanning. If you don't use component scanning for the package, you can alternatively declare it as a `@Bean` in a `@Configuration` class.
- **`AppProperties.dsn` field of type `DataSourceDsn`** — during `@ConfigurationProperties` binding, Spring reads the string `"postgres://alice:secret@db.local:5432/orders"` from the environment, notices the target type is `DataSourceDsn`, finds `DsnConverter` registered for that type, and calls `convert`. The returned `DataSourceDsn` instance is set on the field.
- **Error handling** — `DataSourceDsn.parse` throws `IllegalArgumentException` for malformed input. Spring Boot catches this and wraps it in a `BindException`, including the property path (`app.dsn`) and the rejected value in the message. This is the correct contract for a `@ConfigurationPropertiesBinding` converter.
- **`@NotNull` + `@Validated`** on `AppProperties` — after binding, Spring validates that `dsn` is non-null (i.e., the property was present). This works in combination with the custom converter.

## 7. Gotchas & takeaways

> **Omitting `@ConfigurationPropertiesBinding` is a silent footgun.** A `Converter<String, MyType>` without the qualifier gets registered in the general MVC `ConversionService`. It still works for property binding, but it also fires during request-parameter binding in `@Controller` classes — potentially converting `@RequestParam String` values that happen to be parseable as `MyType`. Always add the qualifier.

> **Your `convert` method must throw `IllegalArgumentException` (or a subclass) for invalid input — not return `null`.** Returning `null` bypasses validation and can cause `NullPointerException` later; throwing produces a clear, located `BindException` at startup.

- The converter only needs to handle `String` as input. If you need to convert from other types (e.g., `Integer` → `MyType`), implement additional `Converter<Integer, MyType>` beans separately.
- For a `GenericConverter` (which can handle multiple source/target type pairs in one class), use `@ConfigurationPropertiesBinding` the same way.
- If you have many properties classes in different modules, the converter is registered once and applies to all `@ConfigurationProperties` classes in the application context — you do not need to register it per-class.
- Writing a unit test for the converter is straightforward: instantiate `DsnConverter`, call `convert("postgres://…")`, and assert the fields — no Spring context needed.
- For Spring Boot 3.x (Jakarta namespace), ensure your imports use `jakarta.validation` rather than `javax.validation`.
