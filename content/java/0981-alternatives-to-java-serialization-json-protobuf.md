---
card: java
gi: 981
slug: alternatives-to-java-serialization-json-protobuf
title: "Alternatives to Java serialization (JSON, protobuf)"
---

## 1. What it is

JSON and Protocol Buffers (protobuf) are two widely-used alternatives to Java's built-in object serialization, both fundamentally different in kind from it: they are **data-only** formats, meaning parsing them can only ever produce plain data structures (strings, numbers, lists, maps, or, for protobuf, instances of classes generated from an explicit schema) — there is no equivalent of Java serialization's `readObject`/`readResolve` mechanism that lets the data itself trigger arbitrary code execution purely as a side effect of being parsed, which is exactly the vulnerability class explored in [serialization vulnerabilities & filters](0980-serialization-vulnerabilities-filters.md). JSON (via a library like Jackson or Gson, since Java has no built-in JSON support) is a human-readable, text-based, schema-optional format, well suited to APIs, configuration, and interoperability with virtually any other language or platform. Protobuf is a binary, schema-first format — you define a message's structure in a `.proto` file, and a code generator produces strongly-typed classes in your target language(s) from that shared schema — trading JSON's flexibility and human-readability for a more compact wire format, faster parsing, and strict, schema-enforced compatibility guarantees across services.

## 2. Why & when

The primary motivation for choosing either alternative over Java's native serialization, beyond the security advantage, is interoperability and long-term compatibility: Java serialization's binary format is Java-specific (a non-Java service cannot easily read it), tightly coupled to the exact class structure at serialization time (a `serialVersionUID` mismatch or an incompatible field change can break deserialization of previously-serialized data), and not really designed as a long-term storage or cross-service wire format at all — it was originally intended more for short-lived RMI calls and JVM-to-JVM communication within a single application's lifetime. JSON is the natural choice for public APIs, browser-facing services, and any context where human-readability during debugging and broad cross-language support matter more than raw performance or the strictest possible schema enforcement. Protobuf is the natural choice for internal service-to-service communication at scale, where the schema is explicitly versioned and shared (typically via `.proto` files checked into source control), parsing performance and wire-size efficiency genuinely matter, and you want the compiler-enforced type safety and explicit backward/forward-compatibility rules protobuf's schema evolution model provides (adding a new optional field, for instance, is designed to be safely ignorable by older consumers that don't know about it yet).

## 3. Core concept

```
Java serialization:  binary, Java-only, tightly coupled to class structure,
                      CAN trigger code execution during deserialization (security risk)

JSON:                 text, human-readable, cross-language, schema-OPTIONAL,
                       data-only (safe to parse untrusted input),
                       via Jackson/Gson (not built into the JDK)

Protobuf:              binary, schema-FIRST (.proto file), cross-language,
                        data-only (safe to parse untrusted input),
                        compact wire format, explicit compatibility rules,
                        strongly-typed generated classes

record User(String name, int age) {}

// JSON (via Jackson), roughly:
{"name": "Ada", "age": 30}

// Protobuf schema (.proto file):
message User {
  string name = 1;
  int32 age = 2;
}
// -> code generator produces a strongly-typed User.java class from this schema
```

Both alternatives share the crucial safety property Java serialization lacks: parsing untrusted JSON or protobuf bytes can only ever produce inert data, never trigger arbitrary code execution as a side effect of the parsing process itself.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three serialization approaches compared: Java native serialization tightly coupled to Java classes with code-execution risk, JSON as a flexible cross-language text format, and protobuf as a schema-first compact binary format" >
  <rect x="20" y="20" width="180" height="120" fill="#1c2430" stroke="#f0883e"/>
  <text x="110" y="40" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Java serialization</text>
  <text x="110" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Java-only, binary</text>
  <text x="110" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">tightly coupled to class</text>
  <text x="110" y="105" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">CAN execute code on parse</text>

  <rect x="230" y="20" width="180" height="120" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">JSON</text>
  <text x="320" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">text, human-readable</text>
  <text x="320" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">cross-language, schema-optional</text>
  <text x="320" y="105" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">data-only, safe to parse</text>

  <rect x="440" y="20" width="180" height="120" fill="#1c2430" stroke="#6db33f"/>
  <text x="530" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Protobuf</text>
  <text x="530" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">binary, compact, schema-first</text>
  <text x="530" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">cross-language, strongly typed</text>
  <text x="530" y="105" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">data-only, safe to parse</text>
</svg>

*Only Java's native serialization risks code execution during parsing; both JSON and protobuf are data-only formats, safe to parse even from untrusted sources.*

## 5. Runnable example

Scenario: serialize and exchange a small user record across three approaches, evolving from a basic JSON representation using Jackson-style annotations conceptually (implemented here with a minimal hand-rolled JSON writer to avoid an external dependency), to a realistic comparison of wire-format size, to a more advanced case demonstrating protobuf-style schema evolution compatibility using a simplified, hand-written stand-in.

### Level 1 — Basic

```java
public class AlternativesJsonBasic {
    record User(String name, int age) {}

    // A minimal, dependency-free JSON writer, standing in for a library like Jackson --
    // real code should use an actual JSON library, but this keeps the example self-contained.
    static String toJson(User user) {
        return "{\"name\":\"" + user.name() + "\",\"age\":" + user.age() + "}";
    }

    public static void main(String[] args) {
        User user = new User("Ada", 30);
        String json = toJson(user);
        System.out.println("JSON: " + json);
        System.out.println("bytes: " + json.getBytes().length);
    }
}
```

**How to run:** `java AlternativesJsonBasic.java` (JDK 17+).

Expected output:
```
JSON: {"name":"Ada","age":30}
bytes: 27
```

The `User` record is represented as human-readable, self-describing text — anyone (or any other programming language's JSON parser) can read this data directly without needing Java-specific knowledge of the `User` class's structure, and, critically, parsing this text can only ever produce plain string/number/map data, never trigger arbitrary code execution.

### Level 2 — Intermediate

```java
import java.io.*;

public class AlternativesFormatSizeComparison {
    record User(String name, int age) implements Serializable {}

    static String toJson(User user) {
        return "{\"name\":\"" + user.name() + "\",\"age\":" + user.age() + "}";
    }

    static byte[] toJavaSerialized(User user) throws IOException {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bos)) {
            out.writeObject(user);
        }
        return bos.toByteArray();
    }

    public static void main(String[] args) throws IOException {
        User user = new User("Ada", 30);

        String json = toJson(user);
        byte[] javaSerialized = toJavaSerialized(user);

        System.out.println("JSON size: " + json.getBytes().length + " bytes");
        System.out.println("Java serialization size: " + javaSerialized.length + " bytes");
        System.out.println("(protobuf for this same message would typically be well under 10 bytes --");
        System.out.println(" its compact binary encoding omits field NAMES entirely, using numbered tags instead)");
    }
}
```

**How to run:** `java AlternativesFormatSizeComparison.java` (JDK 17+).

Expected output shape (illustrative — Java serialization's exact byte count includes substantial class-metadata overhead beyond just the actual data):
```
JSON size: 27 bytes
Java serialization size: 156 bytes
(protobuf for this same message would typically be well under 10 bytes --
 its compact binary encoding omits field NAMES entirely, using numbered tags instead)
```

The real-world concern added: Java's native serialization format includes substantial per-object metadata (fully-qualified class names, field descriptors, version information) beyond just the actual data values themselves, making it considerably larger on the wire than either JSON or, especially, protobuf for the exact same logical data — protobuf's schema-first design means field *names* never need to be repeated in every single message at all (each field is identified by a small numeric tag instead, defined once in the shared `.proto` schema), which is the core reason its wire format is so much more compact than either alternative.

### Level 3 — Advanced

```java
public class AlternativesSchemaEvolution {
    // Simulating protobuf's schema evolution model: an OLDER schema/consumer
    // that doesn't know about a field added LATER should simply ignore it,
    // rather than failing outright -- this is a core protobuf design guarantee.

    record UserV1(String name, int age) {} // the ORIGINAL schema

    record UserV2(String name, int age, String email) {} // schema EVOLVED -- added a field

    // A "v1-aware" parser that only understands the ORIGINAL two fields --
    // simulates an older consumer that hasn't been updated to know about 'email' yet.
    static UserV1 parseAsV1(String rawName, int rawAge, String ignoredExtraField) {
        return new UserV1(rawName, rawAge); // extra field is simply IGNORED, not an error
    }

    public static void main(String[] args) {
        // Simulating a message produced under the NEWER v2 schema:
        UserV2 producedByNewerService = new UserV2("Ada", 30, "ada@example.com");

        // An OLDER consumer, only aware of v1, parses the SAME underlying message,
        // successfully ignoring the field it doesn't recognize:
        UserV1 consumedByOlderService = parseAsV1(
            producedByNewerService.name(),
            producedByNewerService.age(),
            producedByNewerService.email() // the older consumer's code doesn't even name this parameter meaningfully
        );

        System.out.println("newer service's full data: " + producedByNewerService);
        System.out.println("older service's compatible view: " + consumedByOlderService);
    }
}
```

**How to run:** `java AlternativesSchemaEvolution.java` (JDK 17+).

Expected output:
```
newer service's full data: UserV2[name=Ada, age=30, email=ada@example.com]
older service's compatible view: UserV1[name=Ada, age=30]
```

The production-flavored hard case: this simulates protobuf's core schema-evolution guarantee — a message produced under a newer schema (with an added `email` field) can still be successfully consumed by an older service that only understands the original schema, simply ignoring the field it doesn't recognize, rather than failing to parse at all; this forward/backward compatibility is an explicit, deliberate design goal of protobuf's schema evolution rules (adding a new field with a new tag number is always safe for old consumers to ignore), in sharp contrast to Java's native serialization, where changing a class's structure without careful `serialVersionUID` and compatible-field management can easily break deserialization of previously-serialized data outright.

## 6. Walkthrough

Tracing `AlternativesSchemaEvolution.main` end to end:

1. `producedByNewerService` is constructed as a `UserV2`, with all three fields populated: `name = "Ada"`, `age = 30`, `email = "ada@example.com"` — this represents data produced by a service that has already been updated to the newer, three-field schema.
2. `parseAsV1` is called, passing `producedByNewerService`'s `name` and `age` values directly, and its `email` value as the third argument — this simulates an older consumer's parsing logic, one that was written before the schema was ever extended with an `email` field, and therefore has no field or parameter genuinely dedicated to storing or using that value meaningfully.
3. Inside `parseAsV1`, only `rawName` and `rawAge` are actually used to construct the returned `UserV1` — the third parameter, `ignoredExtraField`, is accepted (a real protobuf-generated older parser would similarly accept, but simply skip past, an unrecognized field's bytes in the wire format, guided by the tag-number-based encoding that lets a parser skip past fields it doesn't recognize without needing to understand their meaning) but never stored anywhere.
4. `consumedByOlderService` is therefore a `UserV1` instance containing only `name` and `age` — the `email` information, while it was present in the original data and was successfully passed through this simulated older-consumer parsing path without causing any error, was never actually retained in the older schema's representation, since `UserV1` has no field to hold it.
5. Printing `producedByNewerService` shows all three fields, since `UserV2`'s auto-generated `toString()` reflects `UserV2`'s own three actual components; printing `consumedByOlderService` shows only two fields, since `UserV1`'s auto-generated `toString()` reflects only `UserV1`'s own two actual components — the `email` value, though it passed through the parsing process without error, simply isn't part of what `UserV1` structurally represents.
6. This demonstrates the essential compatibility property protobuf's schema evolution is designed around: an older consumer's code does not need to be updated, and does not fail or crash, when it receives a message containing fields it doesn't yet know about — it simply proceeds with the fields it does understand, correctly ignoring the rest, which is precisely the kind of gradual, independent service-by-service schema evolution that becomes difficult to achieve safely with Java's native serialization, where structural changes to a serialized class are much more likely to break existing deserialization code without careful, deliberate compatibility management.

## 7. Gotchas & takeaways

> **Gotcha:** JSON's schema-optional flexibility is a double-edged sword — without an explicit, enforced schema (via a library like Jackson combined with a validation layer, or a specification like JSON Schema), two services can silently drift out of agreement about a field's expected type or presence, with errors surfacing only at runtime when unexpected data shows up, rather than being caught at compile time or parse time the way protobuf's schema-first, code-generated approach naturally catches many such mismatches; for high-stakes internal service contracts, this is a real reason to prefer protobuf's stricter guarantees over JSON's flexibility.

- JSON and protobuf are both data-only formats — parsing them can only ever produce inert data structures, never trigger arbitrary code execution as a side effect, unlike Java's native serialization.
- JSON favors human-readability, schema flexibility, and broad cross-language/tooling support, making it well suited to public APIs and configuration; protobuf favors compact wire size, parsing performance, and strict, schema-enforced compatibility, making it well suited to high-volume internal service-to-service communication.
- Java's native serialization format includes substantial class-metadata overhead per object, making it noticeably larger on the wire than JSON, and protobuf's field-tag-based encoding (rather than repeating field names) makes it far more compact than either alternative.
- Protobuf's schema evolution model is explicitly designed so an older consumer can safely ignore fields added later by a newer producer, without failing to parse — a deliberate compatibility guarantee much harder to achieve safely with Java's native serialization.
- JSON's schema-optional nature trades away some of the compile-time/parse-time safety protobuf's schema-first, code-generated approach provides — worth weighing deliberately for high-stakes internal contracts.
- See [serialization vulnerabilities & filters](0980-serialization-vulnerabilities-filters.md) for the specific security risk these alternatives structurally avoid, and [Externalizable vs Serializable](0982-externalizable-vs-serializable.md) for finer control over Java's own native serialization format, when it must still be used.
