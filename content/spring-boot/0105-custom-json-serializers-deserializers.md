---
card: spring-boot
gi: 105
slug: custom-json-serializers-deserializers
title: Custom JSON serializers/deserializers
---

## 1. What it is

A **custom JSON serializer** controls how Jackson converts a specific Java type to JSON. A **custom deserializer** controls how JSON is converted back to a Java type. You write a class that extends `JsonSerializer<T>` or `JsonDeserializer<T>` and register it with Spring Boot's Jackson configuration.

Spring Boot recognises and auto-registers serializers/deserializers in two ways:

1. **`@JsonComponent`** (Spring Boot annotation) — annotate your serializer/deserializer class and Spring Boot picks it up automatically via component scan.
2. **`Jackson2ObjectMapperBuilderCustomizer`** bean — add modules, serializers, and deserializers programmatically.
3. **`@JsonSerialize` / `@JsonDeserialize`** on the field or class — Jackson-native annotation for type-level registration.

`@JsonComponent` is the most convenient Spring Boot-specific option: it scans for classes annotated with it and registers them in the shared `ObjectMapper` with no additional configuration.

## 2. Why & when

Custom serializers/deserializers are needed when:
- You have a type that Jackson cannot serialize out of the box (e.g. a `Money` value object wrapping `BigDecimal` + currency).
- You want a compact or non-standard JSON representation for an existing type (e.g. serialize an `Instant` as epoch seconds rather than an ISO string).
- You consume an external API that uses a non-standard date format or a numeric boolean (`0`/`1` instead of `true`/`false`).
- You want to mask or redact sensitive fields (e.g. a `Password` type that always serializes as `"***"`).
- You need to flatten a nested Java structure into a simpler JSON shape.

## 3. Core concept

Minimal `@JsonComponent` example:

```java
@JsonComponent
public class MoneyJsonComponent {

    // Nested serializer class — inner static class is the Jackson convention
    public static class Serializer extends JsonSerializer<Money> {
        @Override
        public void serialize(Money m, JsonGenerator gen, SerializerProvider p) throws IOException {
            gen.writeStartObject();
            gen.writeNumberField("amount", m.amount());
            gen.writeStringField("currency", m.currency());
            gen.writeEndObject();
        }
    }

    public static class Deserializer extends JsonDeserializer<Money> {
        @Override
        public Money deserialize(JsonParser p, DeserializationContext ctx) throws IOException {
            ObjectCodec codec = p.getCodec();
            JsonNode node = codec.readTree(p);
            return new Money(node.get("amount").decimalValue(), node.get("currency").textValue());
        }
    }
}
```

`@JsonComponent` supports two inner class styles:
- Nested static `Serializer` + `Deserializer` classes inside one `@JsonComponent` class.
- A single class that directly extends `JsonSerializer` or `JsonDeserializer`, annotated with `@JsonComponent`.

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Custom serializer path: Money Java object goes through MoneySerializer to become JSON; JSON goes through MoneyDeserializer back to Money">
  <rect x="8" y="8" width="664" height="244" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Custom @JsonComponent — Serialization &amp; Deserialization</text>

  <!-- Java object -->
  <rect x="30" y="60" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="80" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">Money</text>
  <text x="120" y="96" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">amount=99.99 | currency=USD</text>

  <!-- Serializer -->
  <defs><marker id="js" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="212" y1="85" x2="258" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#js)"/>
  <text x="235" y="79" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">serialize</text>

  <rect x="260" y="60" width="160" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="340" y="80" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">MoneySerializer</text>
  <text x="340" y="96" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">extends JsonSerializer&lt;Money&gt;</text>

  <!-- JSON -->
  <line x1="422" y1="85" x2="468" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#js)"/>

  <rect x="470" y="60" width="180" height="50" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="560" y="80" fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">JSON output</text>
  <text x="560" y="96" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">{"amount":99.99,"currency":"USD"}</text>

  <!-- Reverse: deserialize -->
  <line x1="560" y1="112" x2="560" y2="152" stroke="#8b949e" stroke-width="1" stroke-dasharray="3 2"/>

  <rect x="470" y="155" width="180" height="50" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="560" y="175" fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">JSON input</text>
  <text x="560" y="191" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">{"amount":99.99,"currency":"USD"}</text>

  <line x1="468" y1="180" x2="422" y2="180" stroke="#8b949e" stroke-width="1.5" marker-end="url(#js)"/>
  <text x="445" y="174" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">deserialize</text>

  <rect x="260" y="155" width="160" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="340" y="175" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">MoneyDeserializer</text>
  <text x="340" y="191" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">extends JsonDeserializer&lt;Money&gt;</text>

  <line x1="258" y1="180" x2="212" y2="180" stroke="#8b949e" stroke-width="1.5" marker-end="url(#js)"/>

  <rect x="30" y="155" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="175" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">Money</text>
  <text x="120" y="191" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">amount=99.99 | currency=USD</text>

  <!-- Label -->
  <text x="340" y="228" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@JsonComponent on MoneyJsonComponent — auto-registered by Spring Boot component scan</text>
</svg>

One `@JsonComponent` class holds both; Spring Boot wires them into the shared `ObjectMapper` automatically.

## 5. Runnable example

```java
// CustomJsonSerializers.java — run: java CustomJsonSerializers.java  (JDK 17+)
// Simulates custom serializer/deserializer logic for a Money value object.

import java.math.BigDecimal;
import java.util.*;

public class CustomJsonSerializers {

    // ── Value object ─────────────────────────────────────────────────────────
    record Money(BigDecimal amount, String currency) {
        @Override public String toString() {
            return amount + " " + currency;
        }
    }

    // ── Custom serializer (equivalent to JsonSerializer<Money>) ──────────────
    static String serializeMoney(Money m) {
        // Jackson would call: gen.writeStartObject(); gen.writeNumberField("amount", …); etc.
        return String.format("{\"amount\":%s,\"currency\":\"%s\"}", m.amount(), m.currency());
    }

    // ── Custom deserializer (equivalent to JsonDeserializer<Money>) ──────────
    static Money deserializeMoney(String json) {
        // Normally: JsonNode node = codec.readTree(parser);
        // Simplified parsing for demo
        String inner = json.replaceAll("[{}]", "");
        Map<String, String> fields = new LinkedHashMap<>();
        for (String pair : inner.split(",")) {
            String[] kv = pair.split(":");
            String key = kv[0].replaceAll("\"", "").trim();
            String val = kv[1].replaceAll("\"", "").trim();
            fields.put(key, val);
        }
        return new Money(new BigDecimal(fields.get("amount")), fields.get("currency"));
    }

    // ── Sensitive-field serializer: always writes "***" ──────────────────────
    record Password(String value) {}
    static String serializePassword(Password p) { return "\"***\""; }

    // ── Compact Instant serializer: epoch seconds (not ISO string) ──────────
    static String serializeInstant(long epochMs) {
        return String.valueOf(epochMs / 1000L);
    }

    public static void main(String[] args) {
        System.out.println("=== Money serializer (@JsonComponent) ===");
        Money price = new Money(new BigDecimal("99.99"), "USD");
        String json = serializeMoney(price);
        System.out.println("Java → JSON: " + json);
        Money back = deserializeMoney(json);
        System.out.println("JSON → Java: " + back);

        System.out.println("\n=== Password masking serializer ===");
        Password pwd = new Password("super-secret");
        System.out.println("Password Java value: " + pwd.value());
        System.out.println("Serialized to JSON : " + serializePassword(pwd));

        System.out.println("\n=== Compact Instant serializer (epoch seconds) ===");
        long nowMs = System.currentTimeMillis();
        System.out.println("Instant (ms)  : " + nowMs);
        System.out.println("Serialized    : " + serializeInstant(nowMs));
        System.out.println("(default ISO  : 2026-06-28T10:15:30.123Z)");

        System.out.println("\n=== Registration methods ===");
        System.out.println("1. @JsonComponent on MoneyJsonComponent class");
        System.out.println("   → Spring Boot component scan finds it, registers in ObjectMapper");
        System.out.println("2. @JsonSerialize(using=MoneySerializer.class) on Money field");
        System.out.println("   → Jackson-native, field-level, no Spring Boot needed");
        System.out.println("3. Jackson2ObjectMapperBuilderCustomizer @Bean");
        System.out.println("   → builder.serializerByType(Money.class, new MoneySerializer())");
    }
}
```

**How to run:** `java CustomJsonSerializers.java`

## 6. Walkthrough

- `serializeMoney(Money m)` — builds the JSON string manually, mirroring what `JsonSerializer.serialize` does using `JsonGenerator`. In real Jackson, you call `gen.writeStartObject()`, `gen.writeNumberField(…)`, `gen.writeEndObject()` to produce the same output.
- `deserializeMoney(String json)` — parses the JSON back into a `Money` record, mirroring `JsonDeserializer.deserialize`. In real Jackson, you use `codec.readTree(parser)` and call `.get("amount").decimalValue()`.
- `serializePassword(Password p)` always returns `"***"` — the field value is never exposed. In real Jackson, `JsonSerializer.serialize(Password value, …)` receives the full `Password` object but can write any value it chooses. This pattern is useful for audit logs.
- `serializeInstant(long epochMs)` writes a numeric epoch second instead of the default ISO-8601 string. This matches APIs that consume Unix timestamps. The corresponding deserializer would call `Instant.ofEpochSecond(node.longValue())`.
- The three registration methods at the end correspond to: (1) Spring Boot's `@JsonComponent` auto-registration, (2) Jackson-native annotation on the field or class, (3) programmatic registration via a builder customizer bean. Method 1 is cleanest for global types; method 2 is most explicit for type-specific control.

## 7. Gotchas & takeaways

> **`@JsonComponent` is Spring Boot specific.** If you use Jackson outside Spring Boot (e.g. in a standalone utility), `@JsonComponent` has no effect. Use `@JsonSerialize` / `@JsonDeserialize` on the type or field instead, which is pure Jackson and works everywhere.

> **`JsonSerializer` for a type and `@JsonSerialize(using=…)` on the same type can conflict.** The annotation takes precedence over the globally registered serializer. If you register a `MoneySerializer` via `@JsonComponent` but also add `@JsonSerialize(using=OtherSerializer.class)` on a field of type `Money`, the field annotation wins for that field.

- Place serializer and deserializer as nested `public static` classes inside one `@JsonComponent` class — Jackson picks up both automatically.
- `@JsonComponent` participates in component scanning — it only works in packages covered by your `@SpringBootApplication` base package.
- For `null` handling, implement `JsonSerializer.isEmpty(SerializerProvider, T)` to control when a field is omitted under `NON_EMPTY` serialization inclusion.
- Thread safety: Jackson reuses serializer/deserializer instances. Do not store per-request state in their fields.
- Use `ObjectMapper.copy()` when you need a scoped `ObjectMapper` with different settings for a single endpoint — the main `ObjectMapper` is shared across all converters.
