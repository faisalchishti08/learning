---
card: spring-boot
gi: 268
slug: json-jackson-gson-json-b-auto-config
title: JSON (Jackson / Gson / JSON-B) auto-config
---

## 1. What it is

Spring Boot auto-configures JSON serialisation and deserialisation when the corresponding library is on the classpath:

- **Jackson** (`com.fasterxml.jackson.core:jackson-databind`) — the default. Spring Boot configures an `ObjectMapper` bean with sensible defaults: ISO-8601 dates, empty beans tolerated, modules auto-discovered. Included transitively by `spring-boot-starter-web`.
- **Gson** (`com.google.code.gson:gson`) — configured as `Gson` bean if Jackson is excluded and Gson is on the classpath. Spring Boot supports `GsonAutoConfiguration`.
- **JSON-B** (`jakarta.json.bind:jakarta.json.bind-api`) — a standard Jakarta API; `JsonbAutoConfiguration` activates if a JSON-B provider (Yasson, Eclipse Yasson) is on the classpath.

Only one library is the primary HTTP message converter at a time. Jackson is always preferred unless excluded.

## 2. Why & when

Auto-configuration matters because JSON libraries have dozens of configuration options and misconfiguration is easy:

- Not registering Java 8 date/time module → `LocalDateTime` serialises as a JSON object with `year`, `monthValue`, `dayOfMonth` fields instead of `"2024-03-15T10:30:00"`.
- Not setting `SerializationFeature.WRITE_DATES_AS_TIMESTAMPS=false` → dates become Unix epoch milliseconds.
- Not discovering third-party modules (Kotlin, Joda-Time, Hibernate lazy-load) → incomplete serialisation.

Spring Boot's auto-configuration handles all of these by default. You only need to intervene when the defaults aren't what you want.

Customise via:
- `spring.jackson.*` properties (e.g., `spring.jackson.serialization.write-dates-as-timestamps=false`).
- A `Jackson2ObjectMapperBuilderCustomizer` bean.
- A custom `ObjectMapper` bean (replaces auto-configured one entirely).

## 3. Core concept

Jackson's auto-configuration chain:

1. `JacksonAutoConfiguration` creates a `Jackson2ObjectMapperBuilder` with sensible defaults.
2. The builder finds all `Jackson2ObjectMapperBuilderCustomizer` beans (yours and Spring's) and applies them.
3. The builder produces an `ObjectMapper` bean registered as the primary mapper.
4. `JacksonHttpMessageConvertersConfiguration` wires the `ObjectMapper` into Spring MVC's `MappingJackson2HttpMessageConverter` — used for `@RequestBody`/`@ResponseBody` conversion.

Key `spring.jackson.*` properties:

| Property | Example | Effect |
|---|---|---|
| `spring.jackson.serialization.write-dates-as-timestamps` | `false` | ISO-8601 string dates |
| `spring.jackson.deserialization.fail-on-unknown-properties` | `false` | Ignore unknown JSON fields |
| `spring.jackson.default-property-inclusion` | `non_null` | Skip null fields in output |
| `spring.jackson.property-naming-strategy` | `SNAKE_CASE` | `camelCase` ↔ `snake_case` |
| `spring.jackson.time-zone` | `UTC` | Serialize dates in UTC |

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Jackson auto-configuration pipeline from builder to HTTP message converter">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <rect x="10" y="90" width="150" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="85" y="110" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring.jackson.*</text>
  <text x="85" y="128" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">properties</text>

  <rect x="200" y="70" width="160" height="90" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="280" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ObjectMapper</text>
  <text x="280" y="113" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Builder</text>
  <text x="280" y="131" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ Customizers</text>
  <text x="280" y="147" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ Module discovery</text>

  <rect x="410" y="80" width="130" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="105" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">ObjectMapper</text>
  <text x="475" y="123" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Primary bean</text>
  <text x="475" y="139" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">auto-configured</text>

  <rect x="590" y="80" width="100" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="640" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">HTTP Message</text>
  <text x="640" y="116" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Converter</text>
  <text x="640" y="134" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@RequestBody</text>
  <text x="640" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@ResponseBody</text>

  <line x1="160" y1="115" x2="198" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="360" y1="115" x2="408" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="540" y1="115" x2="588" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <text x="350" y="210" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">spring-boot-starter-web pulls in Jackson; auto-config wires it as the HTTP JSON converter</text>
</svg>

Auto-configuration creates a fully-configured `ObjectMapper` and wires it into Spring MVC's HTTP message converter chain.

## 5. Runnable example

```java
// JsonAutoConfigDemo.java — run with: java JsonAutoConfigDemo.java
// Demonstrates Jackson ObjectMapper configuration patterns and
// common spring.jackson.* property equivalents in code.

import com.fasterxml.jackson.annotation.*;
import com.fasterxml.jackson.databind.*;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import java.time.LocalDateTime;

public class JsonAutoConfigDemo {

    // Domain object — what a Spring REST endpoint would serialise
    record Order(
        int id,
        String customerName,
        LocalDateTime createdAt,
        String internalNote,   // null — should be omitted
        String status
    ) {}

    public static void main(String[] args) throws Exception {
        System.out.println("=== Jackson Auto-config Demo ===\n");

        // --- What Spring Boot auto-configures (simplified equivalent) ---
        ObjectMapper mapper = JsonMapper.builder()
            // Equivalent to spring.jackson.serialization.write-dates-as-timestamps=false
            .configure(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS, false)
            // Equivalent to spring.jackson.deserialization.fail-on-unknown-properties=false
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)
            // Equivalent to spring.jackson.default-property-inclusion=non_null
            .serializationInclusion(JsonInclude.Include.NON_NULL)
            // Registers Java 8 date/time support (auto-discovered by Spring Boot)
            .addModule(new JavaTimeModule())
            .build();

        var order = new Order(42, "Alice Smith",
            LocalDateTime.of(2024, 3, 15, 10, 30), null, "SHIPPED");

        String json = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(order);
        System.out.println("--- Serialised Order ---");
        System.out.println(json);

        // Round-trip deserialisation
        Order restored = mapper.readValue(json, Order.class);
        System.out.println("\n--- Deserialised ---");
        System.out.println("id=" + restored.id() + "  customer=" + restored.customerName()
            + "  createdAt=" + restored.createdAt());

        System.out.println("\n--- Key application.properties equivalents ---");
        System.out.println("""
            spring.jackson.serialization.write-dates-as-timestamps=false
            spring.jackson.deserialization.fail-on-unknown-properties=false
            spring.jackson.default-property-inclusion=non_null
            spring.jackson.time-zone=UTC
            spring.jackson.property-naming-strategy=SNAKE_CASE

            # Or customise programmatically:
            # @Bean
            # Jackson2ObjectMapperBuilderCustomizer customizer() {
            #     return builder -> builder.featuresToDisable(
            #         SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
            # }
            """);

        System.out.println("--- Switch to Gson (exclude Jackson in pom.xml) ---");
        System.out.println("""
            <dependency>
              <groupId>org.springframework.boot</groupId>
              <artifactId>spring-boot-starter-web</artifactId>
              <exclusions>
                <exclusion>
                  <groupId>com.fasterxml.jackson.core</groupId>
                  <artifactId>jackson-databind</artifactId>
                </exclusion>
              </exclusions>
            </dependency>
            <dependency>
              <groupId>com.google.code.gson</groupId>
              <artifactId>gson</artifactId>
            </dependency>
            """);
    }
}
```

**How to run:** `java JsonAutoConfigDemo.java` (requires `jackson-databind` and `jackson-datatype-jsr310` on classpath — these are included with `spring-boot-starter-web`)

## 6. Walkthrough

- **`WRITE_DATES_AS_TIMESTAMPS=false`** — without this, `LocalDateTime.of(2024, 3, 15, 10, 30)` serialises as `[2024,3,15,10,30]` (an array). With `false`, it becomes `"2024-03-15T10:30:00"`. Spring Boot sets this for you via `spring.jackson.serialization.write-dates-as-timestamps=false` in `application.properties`, or automatically if you use Spring MVC's default auto-configuration.
- **`FAIL_ON_UNKNOWN_PROPERTIES=false`** — by default Jackson throws `UnrecognizedPropertyException` if the incoming JSON has a field your class doesn't have. This is correct when you control both ends, but frustrating when consuming external APIs that add fields. Spring Boot's default is `false` — ignores unknown fields silently.
- **`JsonInclude.NON_NULL`** — the `"internalNote": null` field is omitted from the output. Without this, null fields appear in the JSON, leaking implementation details and wasting bandwidth.
- **`JavaTimeModule`** — Spring Boot discovers this module on the classpath automatically via Jackson's `ServiceLoader` mechanism. You only need `jackson-datatype-jsr310` on the classpath; Spring Boot registers it without explicit configuration.
- **Gson switch** — excluding `jackson-databind` and adding `gson` triggers `GsonAutoConfiguration` instead. `GsonHttpMessageConvertersConfiguration` then registers Gson as the HTTP message converter. The REST endpoints continue to work; only the serialisation library changes.

## 7. Gotchas & takeaways

> **Auto-configuring a custom `ObjectMapper` bean disables `JacksonAutoConfiguration`.** If you write `@Bean ObjectMapper objectMapper() { return new ObjectMapper(); }`, you own the full configuration — the auto-configured customizers are bypassed. Prefer a `Jackson2ObjectMapperBuilderCustomizer` bean to add to the existing configuration rather than replacing it.

> **Multiple `ObjectMapper` beans require `@Primary`.** If you need a second `ObjectMapper` (e.g., for a specific endpoint with different naming strategy), define the extra one as `@Qualifier("strict")` and leave the auto-configured one as `@Primary`. Spring MVC always uses the primary mapper for HTTP conversion.

- Add `jackson-datatype-jsr310` to use Java 8+ date/time types — Spring Boot auto-discovers it.
- `spring.jackson.mapper.default-view-inclusion=true` enables `@JsonView` on controller methods.
- `spring.jackson.serialization.indent-output=true` pretty-prints JSON — useful in development, too slow for production.
- `@JsonIgnoreProperties(ignoreUnknown=true)` on a class is the per-class alternative to global `FAIL_ON_UNKNOWN_PROPERTIES=false`.
- For polymorphic types, use `@JsonTypeInfo` + `@JsonSubTypes` — Jackson handles it; Spring Boot's auto-config doesn't interfere.
