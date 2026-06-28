---
card: spring-boot
gi: 218
slug: jsontest
title: "@JsonTest"
---

## 1. What it is

`@JsonTest` is the smallest Spring Boot test slice — it loads **only the JSON marshalling infrastructure**: Jackson's `ObjectMapper` (with all auto-configured modules and customizations), `JacksonTester<T>`, and optionally `JsonbTester` (JSON-B) or `GsonTester` (Gson) if those libraries are on the classpath. Nothing else — no web, no JPA, no services. Its purpose is to verify JSON serialization and deserialization in isolation.

## 2. Why & when

Use `@JsonTest` to verify that:
- `@JsonProperty("snake_case")` renames fields as expected.
- `@JsonInclude(NON_NULL)` excludes null fields from output.
- `@JsonIgnore` omits sensitive fields (passwords, tokens).
- `@JsonFormat(pattern="yyyy-MM-dd")` formats dates correctly.
- Custom `JsonSerializer` / `JsonDeserializer` implementations work.
- Nested objects and collections serialize to the correct JSON structure.

If your `ObjectMapper` has complex module registration (e.g., `JavaTimeModule`, `Jdk8Module`) and you rely on auto-configuration, `@JsonTest` guarantees the same `ObjectMapper` configuration as production — unlike constructing one manually in a plain JUnit test.

## 3. Core concept

```java
@JsonTest
class OrderJsonTest {

    @Autowired JacksonTester<Order> json;

    @Test
    void serialize_snakeCaseAndDateFormat() throws Exception {
        Order order = new Order("ORD-1", "alice", 99.99, LocalDate.of(2024, 4, 1));

        // .write() → serialize
        assertThat(json.write(order))
            .hasJsonPathStringValue("$.order_id", "ORD-1")   // @JsonProperty("order_id")
            .hasJsonPathNumberValue("$.total", 99.99)
            .hasJsonPathStringValue("$.date", "2024-04-01"); // @JsonFormat

        // .parse() → deserialize
        Order parsed = json.parse("{\"order_id\":\"ORD-2\",\"total\":50.0}").getObject();
        assertThat(parsed.getId()).isEqualTo("ORD-2");
    }

    @Test
    void nullFields_excluded() throws Exception {
        Order order = new Order("ORD-1", null, 0, null); // null customer and date
        assertThat(json.write(order)).doesNotHaveJsonPath("$.customer");
    }
}
```

`JacksonTester<T>` wraps the `ObjectMapper` and provides assertions. It must be initialized with `JacksonTester.initFields(this, mapper)` in a plain unit test, but `@JsonTest` does this automatically.

## 4. Diagram

<svg viewBox="0 0 680 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@JsonTest loads only Jackson ObjectMapper with auto-configured modules; JacksonTester wraps it for .write() and .parse() assertions; no web, JPA, or services loaded">
  <!-- Java object -->
  <rect x="10" y="55" width="120" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="78" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Java Object</text>
  <text x="70" y="95" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Order(id,customer,</text>
  <text x="70" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">total, date)</text>

  <!-- Serialize arrow -->
  <line x1="132" y1="76" x2="200" y2="76" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jna)"/>
  <text x="165" y="68" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">.write(obj)</text>

  <!-- JacksonTester + ObjectMapper -->
  <rect x="205" y="25" width="270" height="130" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">@JsonTest Slice</text>
  <rect x="218" y="58" width="244" height="30" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="75" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">ObjectMapper (auto-configured)</text>
  <text x="340" y="86" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">JavaTimeModule, Jdk8Module, etc.</text>
  <rect x="218" y="96" width="244" height="28" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="114" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">JacksonTester&lt;T&gt; (autowired)</text>
  <rect x="218" y="132" width="244" height="16" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="340" y="144" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">No web, JPA, services, security</text>

  <!-- Parse arrow -->
  <line x1="205" y1="105" x2="135" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jnb)"/>
  <text x="170" y="117" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">.parse(json)</text>

  <!-- JSON string -->
  <rect x="487" y="55" width="183" height="70" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="578" y="78" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">JSON String</text>
  <text x="578" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">{"order_id":"ORD-1",</text>
  <text x="578" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif"> "total":99.99,"date":"2024-04-01"}</text>

  <line x1="477" y1="76" x2="488" y2="76" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jna)"/>
  <line x1="477" y1="105" x2="488" y2="105" stroke="#79c0ff" stroke-width="1.5"/>

  <defs>
    <marker id="jna" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="jnb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`JacksonTester.write(obj)` serializes to JSON for assertion; `.parse(json)` deserializes for round-trip verification — all using the real auto-configured `ObjectMapper`.

## 5. Runnable example

```java
// JsonTestDemo.java — simulates @JsonTest JacksonTester assertion patterns
// How to run: java JsonTestDemo.java  (JDK 17+, no dependencies)
// Real use: @JsonTest + @Autowired JacksonTester<Order> in test class

import java.util.*;
import java.util.regex.*;

public class JsonTestDemo {

    record Order(
        String id,           // @JsonProperty("order_id") → serializes as "order_id"
        String customer,     // @JsonInclude(NON_NULL) → excluded if null
        double total,
        String date,         // @JsonFormat(pattern="yyyy-MM-dd")
        String passwordHash  // @JsonIgnore → always excluded
    ) {}

    // Simulates Jackson ObjectMapper serialization (with annotations applied)
    static String serialize(Order o) {
        List<String> fields = new ArrayList<>();
        fields.add("\"order_id\":\"" + o.id() + "\"");
        if (o.customer() != null)
            fields.add("\"customer\":\"" + o.customer() + "\"");  // @JsonInclude(NON_NULL)
        fields.add("\"total\":" + o.total());
        if (o.date() != null)
            fields.add("\"date\":\"" + o.date() + "\"");
        // passwordHash is @JsonIgnore — never included
        return "{" + String.join(",", fields) + "}";
    }

    // Simulates Jackson deserialization
    static Order deserialize(String json) {
        String id       = extract(json, "order_id");
        String customer = extract(json, "customer");
        String totalStr = extract(json, "total");
        String date     = extract(json, "date");
        double total    = totalStr != null ? Double.parseDouble(totalStr) : 0.0;
        return new Order(id, customer, total, date, null);
    }

    static String extract(String json, String field) {
        Pattern p = Pattern.compile("\"" + field + "\":\\s*\"?([^,}\"]+)\"?");
        Matcher m = p.matcher(json);
        return m.find() ? m.group(1) : null;
    }

    // Simulates JacksonTester<Order> assertion methods
    static class JsonAssertion {
        final String json;
        JsonAssertion(String json) { this.json = json; }

        JsonAssertion hasJsonPath(String path, String expected, String label) {
            String field = path.replace("$.", "");
            String value = extract(json, field);
            if (!expected.equals(value))
                throw new AssertionError(label + ": " + path + " = " + value + " expected " + expected);
            System.out.println("  ✓ " + label + " [" + path + " = \"" + value + "\"]");
            return this;
        }

        JsonAssertion doesNotHavePath(String path, String label) {
            String field = path.replace("$.", "");
            if (json.contains("\"" + field + "\""))
                throw new AssertionError(label + ": path " + path + " should NOT be present in " + json);
            System.out.println("  ✓ " + label + " [" + path + " absent]");
            return this;
        }
    }

    static void expect(boolean c, String m) {
        if (!c) throw new AssertionError("FAIL: " + m);
        System.out.println("  ✓ " + m);
    }

    public static void main(String[] args) {
        System.out.println("=== @JsonTest / JacksonTester Demo ===\n");

        // Test 1: serialization with @JsonProperty and @JsonFormat
        System.out.println("--- Test 1: serialize with annotations ---");
        Order order = new Order("ORD-1", "alice", 99.99, "2024-04-01", "hashed_secret");
        String json = serialize(order);
        System.out.println("  serialized: " + json);

        new JsonAssertion(json)
            .hasJsonPath("$.order_id",  "ORD-1",      "@JsonProperty: 'id' → 'order_id'")
            .hasJsonPath("$.customer",  "alice",       "customer field present")
            .hasJsonPath("$.date",      "2024-04-01",  "@JsonFormat: date as string")
            .doesNotHavePath("$.passwordHash",          "@JsonIgnore: passwordHash absent")
            .doesNotHavePath("$.password_hash",         "@JsonIgnore: no variant present");

        // Test 2: @JsonInclude(NON_NULL) — null customer excluded
        System.out.println("\n--- Test 2: null field excluded (NON_NULL) ---");
        Order noCustomer = new Order("ORD-2", null, 49.99, null, null);
        String json2 = serialize(noCustomer);
        System.out.println("  serialized: " + json2);

        new JsonAssertion(json2)
            .doesNotHavePath("$.customer", "@JsonInclude(NON_NULL): customer absent")
            .doesNotHavePath("$.date",     "@JsonInclude(NON_NULL): null date absent")
            .hasJsonPath("$.order_id", "ORD-2", "id still present");

        // Test 3: deserialization (parse)
        System.out.println("\n--- Test 3: deserialize (parse) ---");
        String inbound = "{\"order_id\":\"ORD-3\",\"customer\":\"bob\",\"total\":150.0,\"date\":\"2024-05-15\"}";
        Order parsed = deserialize(inbound);
        expect("ORD-3".equals(parsed.id()),         "parsed id");
        expect("bob".equals(parsed.customer()),     "parsed customer");
        expect(parsed.total() == 150.0,             "parsed total");
        expect("2024-05-15".equals(parsed.date()),  "parsed date");
        expect(parsed.passwordHash() == null,       "@JsonIgnore field not populated");

        // Test 4: round-trip
        System.out.println("\n--- Test 4: round-trip serialize → parse ---");
        Order original = new Order("ORD-4", "carol", 299.00, "2024-06-01", "secret");
        Order roundTrip = deserialize(serialize(original));
        expect(original.id().equals(roundTrip.id()),           "round-trip id");
        expect(original.customer().equals(roundTrip.customer()), "round-trip customer");
        expect(original.total() == roundTrip.total(),          "round-trip total");
        expect(roundTrip.passwordHash() == null,               "@JsonIgnore not in round-trip");

        System.out.println("\n--- Real @JsonTest ---");
        System.out.println("""
@JsonTest
class OrderJsonTest {
    @Autowired JacksonTester<Order> json;

    @Test void serialize() throws Exception {
        var order = new Order("ORD-1","alice",99.99,LocalDate.of(2024,4,1));
        assertThat(json.write(order))
            .hasJsonPathStringValue("$.order_id", "ORD-1")
            .hasJsonPathNumberValue("$.total", 99.99)
            .hasJsonPathStringValue("$.date", "2024-04-01")
            .doesNotHaveJsonPath("$.password_hash");
    }

    @Test void deserialize() throws Exception {
        var order = json.parse("{\\"order_id\\":\\"ORD-2\\",\\"total\\":50.0}").getObject();
        assertThat(order.getId()).isEqualTo("ORD-2");
    }
}""");

        System.out.println("\nAll tests passed.");
    }
}
```

**How to run:** `java JsonTestDemo.java`

## 6. Walkthrough

- **Test 1 (serialization annotations)**: confirms `@JsonProperty("order_id")` renames `id` → `order_id` in the JSON output, `@JsonFormat` formats the date as a string, and `@JsonIgnore` fully excludes `passwordHash` from serialization — critical for security.
- **Test 2 (NON_NULL)**: null `customer` and null `date` are absent from the JSON. `@JsonInclude(NON_NULL)` is a common pattern for API responses where optional fields should be omitted.
- **Test 3 (parse/deserialize)**: the `inbound` JSON string (from an external API or HTTP request) is deserialized into an `Order`. `@JsonIgnore` on `passwordHash` means even if someone sends `"passwordHash":"exploit"` in the request body, the field is not populated.
- **Test 4 (round-trip)**: serializes then deserializes and asserts equality — the most comprehensive test of JSON mapping correctness.

## 7. Gotchas & takeaways

> The `@JsonTest` `ObjectMapper` is the **auto-configured** one — it includes `JavaTimeModule`, `Jdk8Module`, and any `Jackson2ObjectMapperBuilderCustomizer` beans. This means `@JsonTest` is the safest way to verify date serialization; a manually created `new ObjectMapper()` in a plain unit test won't have the Spring Boot customizations.

> `JacksonTester<T>` fields in `@JsonTest` are `@Autowired` automatically. In a plain unit test (no Spring context), you must initialize them manually: `JacksonTester.initFields(this, new ObjectMapper())` — otherwise they remain `null` and NPE on use.

- `json.write(obj).getJson()` returns the raw JSON string for assertion with AssertJ string matchers.
- `json.write(obj).hasJsonPathStringValue("$.key", "val")` uses JsonPath under the hood.
- `json.parseObject("{...}")` is shorthand for `.parse(...).getObject()`.
- Test custom `JsonSerializer` by registering it in a `@TestConfiguration` `@Bean ObjectMapper()`.
- `@JsonTest` does not load `@Component` beans — if your `ObjectMapper` customization comes from a `@Component`, it must be in a `@TestConfiguration` imported into the test.
