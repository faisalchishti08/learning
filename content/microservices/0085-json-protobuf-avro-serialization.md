---
card: microservices
gi: 85
slug: json-protobuf-avro-serialization
title: "JSON / Protobuf / Avro serialization"
---

## 1. What it is

Serialization is the process of converting an in-memory object (a DTO, as covered in [request/response payload design](0084-request-response-payload-design-dtos.md)) into bytes that can be sent over the network, and deserialization is the reverse. The three formats most common in microservices each make a different tradeoff: **JSON** is text-based, human-readable, and self-describing (field names travel with every message), at the cost of larger payloads and slower parsing. **Protobuf** is binary and requires a shared schema (a `.proto` file) known to both sides in advance, producing much smaller, faster-to-parse payloads but nothing a human can read directly. **Avro** is also binary and schema-based, but is especially strong at *schema evolution* — reading data written with an older schema version using a newer one, and vice versa, which matters heavily for event streams with long-lived, replayed data.

## 2. Why & when

The format choice is a genuine tradeoff, not a "pick the best one" decision. JSON's self-describing, human-readable text is invaluable during development and debugging — you can read an HTTP request body directly in a browser's network tab or a log line — but that same self-describing verbosity (repeating field names on every single message) costs bandwidth and parsing time at high volume. Protobuf and Avro trade away human-readability for compactness and speed by moving the schema out of the payload and into a separately shared definition, which pays off enormously for high-throughput internal service-to-service calls or event streams, but adds the operational overhead of managing and distributing that shared schema.

Default to JSON for public-facing REST APIs and anywhere debuggability matters most. Reach for Protobuf when internal service-to-service call volume is high enough that payload size and parsing speed genuinely matter (this is the default choice for gRPC). Reach for Avro specifically for event-streaming systems (like Kafka topics) where messages of different schema versions coexist over time and need to remain readable by both old and new consumers.

## 3. Core concept

JSON repeats every field name in every message; a schema-based format defines field names and types once, and every message on the wire is just the values, ordered or tagged according to that shared schema.

```
JSON (self-describing, ~40 bytes):
{"id":42,"status":"PLACED","total":19.99}

Protobuf (schema-defined separately, far fewer bytes on the wire):
schema: message Order { int32 id = 1; string status = 2; double total = 3; }
wire:   [tag:1,42] [tag:2,"PLACED"] [tag:3,19.99]   <- no field NAMES on the wire at all
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A comparison of JSON, which carries field names in every message, versus Protobuf, which relies on a separately shared schema and sends only compact tagged values on the wire">
  <rect x="20" y="20" width="280" height="130" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JSON</text>
  <text x="160" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">self-describing, human-readable</text>
  <text x="160" y="85" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">{"id":42,"status":"PLACED"}</text>
  <text x="160" y="110" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">larger, slower to parse</text>

  <rect x="340" y="20" width="280" height="130" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Protobuf / Avro</text>
  <text x="480" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">schema shared separately</text>
  <text x="480" y="85" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">[1:42][2:"PLACED"] (binary)</text>
  <text x="480" y="110" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">compact, fast, needs the schema</text>
</svg>

JSON trades payload size for self-describing readability; schema-based formats trade readability for compactness.

## 5. Runnable example

Scenario: an `Order` value, first serialized to JSON manually (to make the field-name repetition concrete), then serialized to a Protobuf-style tagged binary encoding using a shared schema, comparing byte counts directly, then extended to demonstrate schema evolution — adding a new field to the schema in a way that lets an old-schema reader keep working against new-schema data.

### Level 1 — Basic

```java
// File: JsonSerialization.java -- hand-roll a simple JSON serializer to
// make explicit that every field NAME is repeated in every message.
public class JsonSerialization {
    record Order(int id, String status, double total) {}

    static String toJson(Order order) {
        return "{\"id\":" + order.id() + ",\"status\":\"" + order.status() + "\",\"total\":" + order.total() + "}";
    }

    public static void main(String[] args) {
        Order order = new Order(42, "PLACED", 19.99);
        String json = toJson(order);
        System.out.println("JSON: " + json);
        System.out.println("Byte size: " + json.getBytes().length);
    }
}
```

**How to run:** `javac JsonSerialization.java && java JsonSerialization` (JDK 17+).

Expected output:
```
JSON: {"id":42,"status":"PLACED","total":19.99}
Byte size: 41
```

### Level 2 — Intermediate

```java
// File: ProtobufStyleSerialization.java -- simulate a Protobuf-style
// encoding: a SHARED SCHEMA maps each field to a small numeric tag, and
// only tag+value pairs go on the wire -- no field names at all.
import java.util.*;

public class ProtobufStyleSerialization {
    record Order(int id, String status, double total) {}

    // the SCHEMA -- known to both sender and receiver in advance, shared out-of-band
    static Map<String, Integer> schemaTags = Map.of("id", 1, "status", 2, "total", 3);

    static byte[] toProtobufStyle(Order order) {
        StringBuilder sb = new StringBuilder(); // simulate binary wire format as a compact string for readability
        sb.append("[").append(schemaTags.get("id")).append(":").append(order.id()).append("]");
        sb.append("[").append(schemaTags.get("status")).append(":").append(order.status()).append("]");
        sb.append("[").append(schemaTags.get("total")).append(":").append(order.total()).append("]");
        return sb.toString().getBytes();
    }

    public static void main(String[] args) {
        Order order = new Order(42, "PLACED", 19.99);
        byte[] wire = toProtobufStyle(order);
        System.out.println("Wire (simulated): " + new String(wire));
        System.out.println("Byte size: " + wire.length + " (no field NAMES transmitted -- schema is shared separately)");
    }
}
```

**How to run:** `javac ProtobufStyleSerialization.java && java ProtobufStyleSerialization` (JDK 17+).

Expected output:
```
Wire (simulated): [1:42][2:PLACED][3:19.99]
Byte size: 25 (no field NAMES transmitted -- schema is shared separately)
```

Even in this simplified, still-text-based simulation, dropping the field names shrinks the payload noticeably — a real binary Protobuf encoding shrinks it further still by encoding the tag and numeric values in raw bytes rather than digit characters.

### Level 3 — Advanced

```java
// File: SchemaEvolution.java -- demonstrate Avro/Protobuf-style SCHEMA
// EVOLUTION: a writer using a NEWER schema (with an added field) produces
// data that an OLDER-schema reader can still parse correctly, simply by
// ignoring the tag it doesn't recognize -- this is what makes rolling
// deployments across schema versions safe.
import java.util.*;

public class SchemaEvolution {
    // OLD schema: reader only knows about tags 1, 2, 3
    static Map<Integer, String> oldSchemaFieldNames = Map.of(1, "id", 2, "status", 3, "total");

    // NEW schema (writer side): adds tag 4 for a new field, "customerId"
    static Map<String, Integer> newSchemaTags = Map.of("id", 1, "status", 2, "total", 3, "customerId", 4);

    static String writeWithNewSchema(int id, String status, double total, long customerId) {
        return "[1:" + id + "][2:" + status + "][3:" + total + "][4:" + customerId + "]";
    }

    static Map<String, String> readWithOldSchema(String wireData) {
        Map<String, String> parsed = new LinkedHashMap<>();
        for (String field : wireData.replace("]", "").split("\\[")) {
            if (field.isEmpty()) continue;
            String[] parts = field.split(":", 2);
            int tag = Integer.parseInt(parts[0]);
            if (oldSchemaFieldNames.containsKey(tag)) { // old reader recognizes tags 1-3
                parsed.put(oldSchemaFieldNames.get(tag), parts[1]);
            } // tag 4 is silently SKIPPED -- old reader has no name for it, and that's fine
        }
        return parsed;
    }

    public static void main(String[] args) {
        String wireData = writeWithNewSchema(42, "PLACED", 19.99, 999); // written with the NEW schema
        System.out.println("Wire data (new schema, 4 fields): " + wireData);

        Map<String, String> parsedByOldReader = readWithOldSchema(wireData); // read with the OLD schema
        System.out.println("Parsed by OLD-schema reader: " + parsedByOldReader);
        System.out.println("(customerId silently ignored -- old reader still works correctly on new-schema data)");
    }
}
```

**How to run:** `javac SchemaEvolution.java && java SchemaEvolution` (JDK 17+).

Expected output:
```
Wire data (new schema, 4 fields): [1:42][2:PLACED][3:19.99][4:999]
Parsed by OLD-schema reader: {id=42, status=PLACED, total=19.99}
(customerId silently ignored -- old reader still works correctly on new-schema data)
```

## 6. Walkthrough

1. **Level 1** — `toJson` manually builds a JSON string, explicitly writing `"id"`, `"status"`, and `"total"` as literal text alongside their values. `main` prints both the resulting string and its byte length (41 bytes) — every field name is present in the payload itself, which is exactly what makes JSON self-describing: a reader with zero prior knowledge of the schema can still understand the data, at the cost of those repeated name characters.
2. **Level 2 — dropping field names via a shared schema** — `schemaTags` stands in for a `.proto` file: it's the agreement, known to both sides *before* any message is sent, that `"id"` corresponds to tag `1`, `"status"` to tag `2`, and so on. `toProtobufStyle` writes only tag numbers and raw values, never the field names themselves. `main` prints the resulting simulated wire format (`[1:42][2:PLACED][3:19.99]`) at 25 bytes — noticeably smaller than Level 1's 41-byte JSON payload, purely by removing the redundant field-name text, with a real binary Protobuf encoder shrinking this further by encoding the values as raw bytes rather than character digits.
3. **Level 3 — schema evolution in action** — `writeWithNewSchema` represents a *writer* using an updated schema that adds a fourth field, `customerId`, at tag `4`. `readWithOldSchema` represents a *reader* that has only ever seen the old, three-field schema (`oldSchemaFieldNames` maps just tags 1–3) — it hasn't been redeployed to know about tag `4` yet, a completely realistic situation during a rolling deployment where writer and reader services update at different times.
4. **Tracing the mismatch handling** — `main` first calls `writeWithNewSchema(42, "PLACED", 19.99, 999)`, producing wire data with all four tagged fields, including `[4:999]`. It then passes that same wire data into `readWithOldSchema`, which iterates each `[tag:value]` segment; for tags `1`, `2`, and `3`, it finds a matching name in `oldSchemaFieldNames` and adds it to `parsed`. For tag `4`, `oldSchemaFieldNames.containsKey(4)` is `false` — the `if` block is skipped entirely, and that field is silently dropped rather than causing a parse error or crash.
5. **Why this is the actual payoff of schema evolution** — the printed `parsedByOldReader` map contains exactly the three fields the old reader knows about, correctly parsed, with no error raised over the unrecognized fourth field. This is what allows a producer service to be upgraded (adding new fields to its schema) *before* every consumer has been upgraded to understand them — the old consumers keep working correctly on the new, richer data, simply ignoring what they don't yet recognize. JSON achieves a similar practical effect naturally (an old reader that only looks up specific keys by name also ignores unknown keys), but Avro and Protobuf make this evolution guarantee an explicit, first-class part of their schema design rules (e.g., "never reuse a tag number," "new fields must have a default").

## 7. Gotchas & takeaways

> **Gotcha:** Protobuf and Avro's compactness depends entirely on both sides genuinely sharing the same schema (or compatible versions of it) — if the schema definition drifts out of sync between services (a `.proto` file updated in one service's repo but not distributed to another), messages silently decode into garbage rather than failing loudly the way a JSON parse error typically would. Schema distribution and versioning discipline is the real operational cost being traded for the smaller payload.

- JSON's field names travel in every message, making it self-describing and human-readable at the cost of size and parse speed; schema-based formats move that description out into a separately shared, versioned definition.
- Default to JSON for public APIs and anywhere debuggability matters; reach for Protobuf for high-throughput internal calls (especially with gRPC) and Avro specifically for event streams needing strong schema evolution guarantees.
- Schema evolution — old readers safely ignoring fields they don't recognize, new readers supplying sensible defaults for fields missing from older data — is what makes rolling deployments across schema versions safe without a coordinated, simultaneous upgrade of every service.
- The serialization format is chosen *after* the payload shape is already settled via a [DTO](0084-request-response-payload-design-dtos.md) — the format decides how those DTO fields get encoded onto the wire, not what fields exist in the first place.
- Never reuse a numeric tag for a different field's meaning in a schema-based format — doing so breaks every reader that hasn't been updated in perfect lockstep, defeating the entire purpose of schema evolution.
