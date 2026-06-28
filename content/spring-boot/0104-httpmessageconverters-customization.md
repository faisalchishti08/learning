---
card: spring-boot
gi: 104
slug: httpmessageconverters-customization
title: HttpMessageConverters customization
---

## 1. What it is

**`HttpMessageConverter`** is the Spring MVC interface responsible for converting HTTP request bodies to Java objects (deserialization) and Java objects to HTTP response bodies (serialization). Every `@RequestBody` / `@ResponseBody` and `@RestController` method uses converters internally.

Spring Boot auto-configures a standard set of converters when you add `spring-boot-starter-web`:
- `MappingJackson2HttpMessageConverter` — JSON (requires `jackson-databind`).
- `StringHttpMessageConverter` — plain text (`text/plain`, `text/*`).
- `ByteArrayHttpMessageConverter` — raw bytes.
- `ResourceHttpMessageConverter` — `Resource` objects (file downloads).
- `FormHttpMessageConverter` — URL-encoded form data.
- `MappingJackson2XmlHttpMessageConverter` — XML (if `jackson-dataformat-xml` is on the classpath).
- `Jaxb2RootElementHttpMessageConverter` — JAXB XML (if JAXB2 is present).

You customise converters through Spring Boot's `HttpMessageConverters` bean, or by implementing `WebMvcConfigurer.configureMessageConverters()`.

## 2. Why & when

The default converters cover most use cases, but customisation is needed when:
- You want to **configure Jackson** (date format, snake_case serialization, null handling) globally.
- You want to **add a converter** for a custom media type (e.g. Protobuf, CBOR, CSV, YAML).
- You want to **remove a converter** (e.g. remove XML support to prevent accidental XML responses).
- You want to **reorder converters** — the first converter that claims to handle a media type wins.
- You need to set a **Jackson feature flag** (e.g. `FAIL_ON_UNKNOWN_PROPERTIES=false`).

The `ObjectMapper` used by `MappingJackson2HttpMessageConverter` is the same one auto-configured by `JacksonAutoConfiguration` — customise it via `Jackson2ObjectMapperBuilderCustomizer` and all JSON serialization in your app benefits.

## 3. Core concept

Two ways to customise:

**Option 1 — Customise the `ObjectMapper` (most common):**
```java
@Bean
public Jackson2ObjectMapperBuilderCustomizer jsonCustomizer() {
    return builder -> builder
        .featuresToDisable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
        .featuresToDisable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
        .propertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
}
```

**Option 2 — Add converters via `WebMvcConfigurer`:**
```java
@Override
public void configureMessageConverters(List<HttpMessageConverter<?>> converters) {
    // This REPLACES the default list — you must add everything you want
}

@Override
public void extendMessageConverters(List<HttpMessageConverter<?>> converters) {
    // This EXTENDS the default list — safer for adding custom converters
}
```

Use `configureMessageConverters` only when you need to radically change the list; use `extendMessageConverters` when adding or reordering.

## 4. Diagram

<svg viewBox="0 0 680 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HttpMessageConverter chain: request body passes through converters in order, first that can handle wins">
  <rect x="8" y="8" width="664" height="254" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">HttpMessageConverter Selection Chain</text>

  <!-- HTTP request -->
  <rect x="20" y="55" width="120" height="44" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="80" y="73" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">HTTP Request</text>
  <text x="80" y="89" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Content-Type: application/json</text>

  <defs><marker id="hm" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="142" y1="77" x2="165" y2="77" stroke="#8b949e" stroke-width="1.5" marker-end="url(#hm)"/>

  <!-- Converter chain -->
  <rect x="167" y="55" width="130" height="44" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="232" y="73" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">StringConverter</text>
  <text x="232" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">text/* → skip</text>

  <line x1="299" y1="77" x2="320" y2="77" stroke="#8b949e" stroke-width="1" marker-end="url(#hm)"/>

  <rect x="322" y="55" width="160" height="44" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="402" y="73" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">Jackson2Converter</text>
  <text x="402" y="88" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">application/json → MATCH ✓</text>

  <line x1="484" y1="77" x2="505" y2="77" stroke="#8b949e" stroke-width="1" stroke-dasharray="3 2"/>

  <rect x="507" y="55" width="140" height="44" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="577" y="73" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">XmlConverter</text>
  <text x="577" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">not reached</text>

  <!-- Customization paths -->
  <rect x="20" y="140" width="300" height="70" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="170" y="158" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Customise ObjectMapper (common)</text>
  <text x="40" y="174" fill="#e6edf3" font-size="9" font-family="monospace">@Bean Jackson2ObjectMapperBuilderCustomizer</text>
  <text x="40" y="188" fill="#e6edf3" font-size="9" font-family="monospace">  .featuresToDisable(WRITE_DATES_AS_TIMESTAMPS)</text>
  <text x="40" y="202" fill="#8b949e" font-size="9" font-family="sans-serif">  → affects all JSON in/out</text>

  <rect x="360" y="140" width="290" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="505" y="158" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Add converter (rare)</text>
  <text x="380" y="174" fill="#e6edf3" font-size="9" font-family="monospace">extendMessageConverters(converters)</text>
  <text x="380" y="188" fill="#e6edf3" font-size="9" font-family="monospace">  converters.add(new CsvConverter())</text>
  <text x="380" y="202" fill="#8b949e" font-size="9" font-family="sans-serif">  → adds to existing list</text>
</svg>

First converter in the list whose supported types match the `Content-Type` wins.

## 5. Runnable example

```java
// HttpMessageConverters.java — run: java HttpMessageConverters.java  (JDK 17+)
// Simulates converter selection and shows how ObjectMapper customisation flows through.

import java.util.*;

public class HttpMessageConverters {

    // Simulated converter
    interface MsgConverter {
        String name();
        boolean canRead(String contentType);
        boolean canWrite(String acceptType);
        String read(String body);
        String write(Object obj);
    }

    // Simulated StringHttpMessageConverter
    static final MsgConverter STRING_CONV = new MsgConverter() {
        public String name() { return "StringHttpMessageConverter"; }
        public boolean canRead(String ct) { return ct != null && ct.startsWith("text/"); }
        public boolean canWrite(String at) { return at != null && at.startsWith("text/"); }
        public String read(String body) { return body; }
        public String write(Object obj) { return obj.toString(); }
    };

    // Simulated MappingJackson2HttpMessageConverter
    static final MsgConverter JACKSON_CONV = new MsgConverter() {
        private boolean snakeCase = false;
        private boolean writeDatesAsTimestamps = true;

        // Simulates ObjectMapper configuration
        void configure(boolean snake, boolean datesAsTs) {
            this.snakeCase = snake;
            this.writeDatesAsTimestamps = datesAsTs;
        }

        public String name() { return "MappingJackson2HttpMessageConverter"; }
        public boolean canRead(String ct) { return "application/json".equals(ct); }
        public boolean canWrite(String at) { return "application/json".equals(at) || "*/*".equals(at); }

        public String read(String body) { return "Deserialized from JSON: " + body; }
        public String write(Object obj) {
            return "{ \"data\": \"" + obj + "\""
                + (snakeCase ? " /* snake_case names */" : "")
                + (writeDatesAsTimestamps ? "" : " /* ISO date strings */")
                + " }";
        }
    };

    static final List<MsgConverter> CONVERTERS = new ArrayList<>(List.of(STRING_CONV, JACKSON_CONV));

    static MsgConverter selectReadConverter(String contentType) {
        return CONVERTERS.stream().filter(c -> c.canRead(contentType)).findFirst().orElse(null);
    }

    static MsgConverter selectWriteConverter(String acceptType) {
        return CONVERTERS.stream().filter(c -> c.canWrite(acceptType)).findFirst().orElse(null);
    }

    @SuppressWarnings("unchecked")
    public static void main(String[] args) {
        System.out.println("=== Default converter selection ===");
        MsgConverter r1 = selectReadConverter("application/json");
        System.out.println("Reading application/json → " + (r1 != null ? r1.name() : "no match"));
        System.out.println("  Result: " + (r1 != null ? r1.read("{\"name\":\"alice\"}") : "415 Unsupported Media Type"));

        MsgConverter r2 = selectReadConverter("text/plain");
        System.out.println("Reading text/plain → " + (r2 != null ? r2.name() : "no match"));

        System.out.println("\n=== Writing (serialization) ===");
        MsgConverter w1 = selectWriteConverter("application/json");
        System.out.println("Writing for application/json → " + (w1 != null ? w1.name() : "no match"));
        System.out.println("  Result: " + (w1 != null ? w1.write("Order{id=42}") : ""));

        System.out.println("\n=== After ObjectMapper customization (Jackson2ObjectMapperBuilderCustomizer) ===");
        ((MsgConverter & Runnable) () -> {}).run(); // trick to access inner state
        // Re-configure the jackson converter to simulate the customizer
        MappingJackson2Sim jackson = new MappingJackson2Sim();
        jackson.configure(true, false);
        System.out.println("  snakeCase=true, writeDatesAsTimestamps=false");
        System.out.println("  Write result: " + jackson.write("Order{id=42, createdAt=2026-06-28}"));
    }

    // Stand-alone class so we can demonstrate configure()
    static class MappingJackson2Sim {
        boolean snakeCase = false;
        boolean writeDatesAsTimestamps = true;

        void configure(boolean snake, boolean datesAsTs) {
            this.snakeCase = snake;
            this.writeDatesAsTimestamps = datesAsTs;
        }

        String write(Object obj) {
            return "{ \"data\": \"" + obj + "\""
                + (snakeCase ? ", /* all fields in snake_case */" : "")
                + (!writeDatesAsTimestamps ? " \"created_at\": \"2026-06-28T00:00:00Z\"" : "")
                + " }";
        }
    }
}
```

**How to run:** `java HttpMessageConverters.java`

## 6. Walkthrough

- `CONVERTERS` list preserves insertion order — this is the actual order Spring Boot registers converters. `StringHttpMessageConverter` comes before `MappingJackson2HttpMessageConverter`, so plain text bodies are handled first.
- `selectReadConverter("application/json")` iterates the list and returns the first converter whose `canRead` returns true. `STRING_CONV.canRead("application/json")` is false (only `text/*`); `JACKSON_CONV.canRead` returns true. Jackson wins.
- `selectWriteConverter("*/*")` — `STRING_CONV.canWrite("*/*")` returns false, `JACKSON_CONV.canWrite("*/*")` returns true. A `@RestController` method with no explicit `Accept` header causes the browser to send `Accept: */*`, which Jackson accepts.
- `MappingJackson2Sim.configure(true, false)` simulates what `Jackson2ObjectMapperBuilderCustomizer` does. Setting `snakeCase=true` means all Java camelCase field names are serialized as snake_case JSON keys. Setting `writeDatesAsTimestamps=false` means `Instant`/`LocalDate` fields serialize as ISO-8601 strings, not epoch milliseconds.
- In production Spring Boot, define a `@Bean Jackson2ObjectMapperBuilderCustomizer` — Spring Boot uses it to build the shared `ObjectMapper`, which is then injected into `MappingJackson2HttpMessageConverter`. One customizer affects all JSON serialization.

## 7. Gotchas & takeaways

> **`configureMessageConverters` replaces the default list entirely.** If you override this method and add only your custom converter, Jackson, String, and Byte converters are gone. Return `406 Not Acceptable` errors will appear for all standard content types. Use `extendMessageConverters` instead when adding converters.

> **Registering a second `ObjectMapper` bean creates an ambiguous autowiring conflict and Spring Boot may not pick it as the primary.** If you need a customised mapper, either use `Jackson2ObjectMapperBuilderCustomizer` or annotate your `@Bean ObjectMapper` with `@Primary`. Do not register an `ObjectMapper` without `@Primary` alongside the auto-configured one.

- `HttpMessageConverterAutoConfiguration` is separate from `WebMvcAutoConfiguration` — converters are registered centrally and shared by MVC and `RestTemplate`.
- To globally disable field serialization of `null` values, set `spring.jackson.default-property-inclusion=non_null` in `application.properties` — no Java code needed.
- For Protobuf support, add `com.google.protobuf:protobuf-java` and `io.github.marcelbraghetto:spring-protobuf-message-converter` (or a community library); Spring Boot does not auto-configure Protobuf converters.
- Converter selection for the response is also affected by the `Accept` header — if a client sends `Accept: application/xml` and you have no XML converter, Spring returns `406 Not Acceptable`.
- The `spring.jackson.*` property namespace covers common ObjectMapper settings without requiring Java configuration: `spring.jackson.date-format`, `spring.jackson.time-zone`, `spring.jackson.serialization.indent-output=true`, etc.
