---
card: java
gi: 1050
slug: json-jackson-gson
title: "JSON (Jackson, Gson)"
---

## 1. What it is

Jackson and Gson are libraries that convert between Java objects and JSON text — **serialization** (object → JSON string) and **deserialization** (JSON string → object) — without you hand-writing string-building or parsing code. Jackson's `ObjectMapper.writeValueAsString(obj)` and `readValue(json, Class)` are its two core operations; Gson's `Gson.toJson(obj)` and `fromJson(json, Class)` mirror the same idea with a slightly different API. Both use reflection by default to inspect a class's fields (or getters/setters) and map them to JSON keys automatically, with annotations available to customize field names, ignore fields, or handle values that don't map naturally (dates, custom types).

## 2. Why & when

Hand-writing JSON conversion — manually building a string with the right quoting, brackets, and escaping, or manually parsing a JSON string character by character to extract specific fields — is tedious and error-prone even for simple objects, and becomes genuinely hard to get right for nested objects, lists, and edge cases like special characters needing escaping. Jackson/Gson automate this mapping using reflection: annotate or simply define your class with plain fields, and the library handles the conversion — including nested objects, collections, and null-handling — consistently and correctly, without you writing any manual string manipulation.

Reach for Jackson (the more feature-rich and widely-used choice in the Spring ecosystem, and the default JSON library pulled in by `spring-boot-starter-web`) or Gson (a simpler, lighter alternative popular in Android and smaller projects) whenever your application needs to send or receive JSON — a REST API's request/response bodies, a configuration file, a message queue payload. Use annotations (`@JsonProperty`, `@JsonIgnore` for Jackson; `@SerializedName`, `transient` for Gson) when a Java field's natural name or type doesn't map cleanly to how you need the JSON to look.

## 3. Core concept

```java
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.annotation.JsonProperty;

record User(String name, int age, @JsonProperty("email_address") String email) {}

ObjectMapper mapper = new ObjectMapper();

// Serialization: object -> JSON string
User user = new User("Ana", 30, "ana@example.com");
String json = mapper.writeValueAsString(user);
// {"name":"Ana","age":30,"email_address":"ana@example.com"}

// Deserialization: JSON string -> object
User parsed = mapper.readValue(json, User.class);
System.out.println(parsed.name()); // "Ana"
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Java User object being serialized by Jackson's ObjectMapper into a JSON string, and that same JSON string being deserialized back into an equivalent Java User object">
  <rect x="30" y="60" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">User object</text>

  <rect x="250" y="60" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ObjectMapper</text>

  <rect x="470" y="60" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="540" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JSON string</text>

  <line x1="170" y1="75" x2="250" y2="75" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="210" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">writeValueAsString</text>
  <line x1="470" y1="90" x2="390" y2="90" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="430" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">readValue</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`ObjectMapper` converts in both directions: an object to JSON text, and JSON text back to an equivalent object.

## 5. Runnable example

Scenario: converting a `User` object to and from JSON, evolving from manual string building into Jackson's automatic serialization, including custom field naming and nested objects.

### Level 1 — Basic

```java
// File: ManualJsonBasic.java -- hand-built JSON, no library at all
public class ManualJsonBasic {
    record User(String name, int age) {}

    static String toJson(User user) {
        // Manual string building -- fragile, and doesn't handle escaping,
        // nested objects, or null values correctly at all.
        return "{\"name\":\"" + user.name() + "\",\"age\":" + user.age() + "}";
    }

    public static void main(String[] args) {
        User user = new User("Ana", 30);
        System.out.println(toJson(user));
    }
}
```

**How to run:** save as `ManualJsonBasic.java`, then `javac ManualJsonBasic.java && java ManualJsonBasic` (JDK 17+).

Expected output:
```
{"name":"Ana","age":30}
```

This works for this one simple case, but a name containing a quote character (`"Ana \"Anna\""`) would produce invalid JSON, and there's no corresponding way to parse a JSON string back into a `User` object without writing equally manual, fragile parsing code.

### Level 2 — Intermediate

```java
// File: JacksonBasic.java
import com.fasterxml.jackson.databind.ObjectMapper;

public class JacksonBasic {
    record User(String name, int age) {}

    public static void main(String[] args) throws Exception {
        ObjectMapper mapper = new ObjectMapper();

        User user = new User("Ana", 30);
        String json = mapper.writeValueAsString(user); // serialization
        System.out.println("Serialized: " + json);

        User parsed = mapper.readValue(json, User.class); // deserialization
        System.out.println("Deserialized: " + parsed);
    }
}
```

**How to run:** with `jackson-databind` on the classpath, `javac -cp jackson-databind-2.17.0.jar:jackson-core-2.17.0.jar:jackson-annotations-2.17.0.jar JacksonBasic.java && java -cp .:jackson-databind-2.17.0.jar:jackson-core-2.17.0.jar:jackson-annotations-2.17.0.jar JacksonBasic` (JDK 17+).

Expected output:
```
Serialized: {"name":"Ana","age":30}
Deserialized: JacksonBasic$User[name=Ana, age=30]
```

The real-world concern added: Jackson handles both directions automatically, correctly escaping any special characters and reconstructing a genuine `User` object (via its canonical constructor, since Jackson has built-in support for Java records) from the JSON string — no manual string manipulation involved in either direction.

### Level 3 — Advanced

```java
// File: JacksonAdvanced.java
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;

public class JacksonAdvanced {
    record Address(String city, String country) {}

    record User(
        String name,
        int age,
        @JsonProperty("email_address") String email, // customize the JSON key name
        Address address,                                // nested object -- handled automatically
        List<String> hobbies,
        @JsonIgnore String internalNotes                 // NEVER included in the JSON output
    ) {}

    public static void main(String[] args) throws Exception {
        ObjectMapper mapper = new ObjectMapper();

        User user = new User(
            "Ana", 30, "ana@example.com",
            new Address("Springfield", "USA"),
            List.of("reading", "chess"),
            "flagged for review -- SENSITIVE, must never leak into JSON output"
        );

        String json = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(user);
        System.out.println(json);

        // Deserialize back -- internalNotes will be null, since it was never in the JSON at all.
        User parsed = mapper.readValue(json, User.class);
        System.out.println("internalNotes after round-trip: " + parsed.internalNotes());
    }
}
```

**How to run:** with the same Jackson dependencies as Level 2, compile and run similarly (JDK 17+).

Expected output:
```
{
  "name" : "Ana",
  "age" : 30,
  "email_address" : "ana@example.com",
  "address" : {
    "city" : "Springfield",
    "country" : "USA"
  },
  "hobbies" : [ "reading", "chess" ]
}
internalNotes after round-trip: null
```

The production-flavored hard case: `@JsonProperty("email_address")` renames the JSON key without renaming the Java field, `Address` is nested automatically with zero extra configuration, `List<String>` becomes a JSON array automatically, and `@JsonIgnore` guarantees `internalNotes` — a genuinely sensitive field — never appears in the serialized output at all, regardless of what value it holds.

## 6. Walkthrough

Tracing `mapper.writerWithDefaultPrettyPrinter().writeValueAsString(user)` in `JacksonAdvanced.main`:

1. Jackson inspects `User`'s structure via reflection (using its built-in support for Java records, which reads each record component as a property): `name`, `age`, `email` (annotated `@JsonProperty("email_address")`), `address`, `hobbies`, and `internalNotes` (annotated `@JsonIgnore`).
2. For `name` and `age`, no annotation customization is present, so Jackson uses the record component names directly as JSON keys: `"name"` and `"age"`.
3. For `email`, Jackson sees the `@JsonProperty("email_address")` annotation and uses `"email_address"` as the JSON key instead of `"email"` — the Java field name and the JSON key name are deliberately different.
4. For `address`, Jackson recognizes it as another structured object (an `Address` record) and recursively applies the same serialization process to it, producing a nested JSON object with keys `"city"` and `"country"`.
5. For `hobbies`, Jackson recognizes `List<String>` and serializes it as a JSON array of strings: `[ "reading", "chess" ]`.
6. For `internalNotes`, Jackson sees the `@JsonIgnore` annotation and skips it entirely — it never appears as a key in the output JSON at all, regardless of its actual string value. The resulting JSON (pretty-printed, per `writerWithDefaultPrettyPrinter()`) is printed, and when that JSON is later deserialized back via `readValue`, the reconstructed `User`'s `internalNotes` field is `null` — not because Jackson set it to `null` explicitly, but because the JSON simply never contained that key at all for the record's canonical constructor to populate.

## 7. Gotchas & takeaways

> **Gotcha:** `@JsonIgnore` prevents a field from being *serialized* (written out), but by default doesn't prevent it from being *deserialized* if a matching key happens to appear in incoming JSON — for genuinely sensitive fields that must never be set from untrusted external input either, `@JsonIgnore` alone may not be sufficient; Jackson's `@JsonProperty(access = JsonProperty.Access.WRITE_ONLY)` (or similar access-control annotations) may be needed depending on the exact requirement.

- Jackson and Gson both automate JSON serialization/deserialization using reflection, avoiding manual, error-prone string building and parsing.
- `ObjectMapper.writeValueAsString`/`readValue` (Jackson) and `Gson.toJson`/`fromJson` (Gson) are the respective core conversion methods for each library.
- Jackson has built-in support for Java records, mapping each record component to a JSON property automatically, including its canonical constructor for deserialization.
- `@JsonProperty` customizes a field's JSON key name; `@JsonIgnore` excludes a field from serialization entirely — essential for sensitive or internal-only fields that must never leak into an external API response.
- Nested objects and collections (`List`, `Map`) are handled automatically and recursively — no special configuration is needed for straightforward nested structures.
- Reach for Jackson specifically in Spring-based applications (it's the default, auto-configured JSON library behind `spring-boot-starter-web` — see [Spring Boot](1047-spring-boot.md)); Gson remains a lighter, simpler alternative favored in some non-Spring contexts, particularly Android.
