---
card: spring-data
gi: 116
slug: json-schema-validation
title: "JSON Schema validation"
---

## 1. What it is

MongoDB **JSON Schema validation** lets a collection reject documents that don't match a defined shape — required fields, field types, allowed value ranges — enforced by the *database itself* at write time, not just by application code. Spring Data MongoDB configures it through `CollectionOptions.empty().validator(...)` when creating (or modifying) a collection.

```java
Document schema = new Document("$jsonSchema", new Document()
    .append("required", List.of("id", "status"))
    .append("properties", new Document("status",
        new Document("enum", List.of("PENDING", "SHIPPED", "DELIVERED")))));

mongoTemplate.createCollection("orders",
    CollectionOptions.empty().validator(Validator.schema(MongoJsonSchema.of(schema))));
```

## 2. Why & when

MongoDB collections are schemaless by default — any document, with any fields of any type, can be inserted. That flexibility is often a feature, but it also means a bug in application code (or a badly-formed document from another service) can silently write malformed data with no error at all. JSON Schema validation adds a guardrail directly at the database layer, independent of whichever application happens to be writing.

Reach for JSON Schema validation when:

- Multiple services or scripts can write to the same collection, and Java-level `@NotNull`/Bean Validation annotations only protect writes that go through *your* application code — a schema validator protects the collection itself, no matter what writes it.
- You want required fields and basic type/range constraints enforced even against direct `mongosh` scripts, admin tooling, or a future service that hasn't been written yet.
- You're migrating from a relational schema and want a safety net during the transition, without giving up MongoDB's flexibility for fields that genuinely vary between documents.

It's not a replacement for application-level validation — it can't express business rules like "total must equal the sum of line items" — but it's a strong last line of defense against structurally broken documents.

## 3. Core concept

```
 db.createCollection("orders", { validator: { $jsonSchema: {
     required: ["id", "status"],
     properties: {
       status: { enum: ["PENDING", "SHIPPED", "DELIVERED"] },
       total:  { bsonType: "double", minimum: 0 }
     }
 }}})

 insert({id: "1", status: "PENDING", total: 50})     -> ACCEPTED (matches schema)
 insert({id: "2", status: "UNKNOWN", total: 50})     -> REJECTED (status not in enum)
 insert({id: "3", total: 50})                        -> REJECTED (status missing, required)
```

The schema is attached to the collection once, at creation time (or via `collMod`), and MongoDB checks every subsequent write against it automatically.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An insert is checked against the collection's JSON Schema; a matching document is accepted, a non-matching one is rejected">
  <rect x="20" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">insert(document)</text>

  <rect x="240" y="20" width="200" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">$jsonSchema validator</text>

  <line x1="200" y1="42" x2="235" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <rect x="480" y="20" width="140" height="45" rx="8" fill="#3fb95022" stroke="#3fb950" stroke-width="1.5"/>
  <text x="550" y="47" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">matches -&gt; accepted</text>
  <line x1="440" y1="35" x2="475" y2="35" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <rect x="480" y="90" width="140" height="45" rx="8" fill="#f8514922" stroke="#f85149" stroke-width="1.5"/>
  <text x="550" y="117" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">fails -&gt; rejected</text>
  <line x1="440" y1="55" x2="475" y2="105" stroke="#f85149" stroke-width="2" marker-end="url(#a2)"/>

  <defs>
    <marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

Every insert or update is checked against the schema before MongoDB commits it — there is no path around this check from any client.

## 5. Runnable example

The scenario: enforcing structure on `orders` documents, evolving from a hand-rolled type check standing in for the schema idea, to a validator that checks required fields and an enum, to one with configurable validation level (`strict` vs `moderate`) and action (`error` vs `warn`) — the two knobs real MongoDB validators expose.

### Level 1 — Basic

Model the core idea: before a document is written, it's checked against a set of required fields and types.

```java
import java.util.*;

public class JsonSchemaLevel1 {
    public static void main(String[] args) {
        SchemaValidator validator = new SchemaValidator();

        Map<String, Object> valid = Map.of("id", "1", "status", "PENDING");
        Map<String, Object> missingField = Map.of("status", "PENDING"); // no "id"

        validator.validate(valid);
        System.out.println("Valid document accepted.");

        try {
            validator.validate(missingField);
        } catch (ValidationException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}

class ValidationException extends RuntimeException { ValidationException(String msg) { super(msg); } }

// Stands in for the database checking a document against a $jsonSchema validator.
class SchemaValidator {
    void validate(Map<String, Object> doc) {
        if (!doc.containsKey("id")) throw new ValidationException("missing required field: id");
        if (!doc.containsKey("status")) throw new ValidationException("missing required field: status");
        if (!(doc.get("status") instanceof String)) throw new ValidationException("status must be a string");
    }
}
```

How to run: `java JsonSchemaLevel1.java`

`validate` checks the two required fields directly, standing in for the `"required": ["id", "status"]` clause of a real `$jsonSchema`. A document missing `id` is rejected with a clear message — the same behavior MongoDB itself would produce, just enforced in Java rather than at the database layer for this level.

### Level 2 — Intermediate

Add an `enum` constraint (mirroring `properties.status.enum`) and a numeric range constraint (mirroring `properties.total.minimum`), matching how real `$jsonSchema` validators combine several rules.

```java
import java.util.*;

public class JsonSchemaLevel2 {
    public static void main(String[] args) {
        SchemaValidator validator = new SchemaValidator();

        List<Map<String, Object>> docs = List.of(
            Map.of("id", "1", "status", "PENDING", "total", 50.0),
            Map.of("id", "2", "status", "UNKNOWN", "total", 50.0),   // bad enum value
            Map.of("id", "3", "status", "SHIPPED", "total", -10.0)   // negative total
        );

        for (Map<String, Object> doc : docs) {
            try {
                validator.validate(doc);
                System.out.println(doc.get("id") + ": accepted");
            } catch (ValidationException e) {
                System.out.println(doc.get("id") + ": rejected - " + e.getMessage());
            }
        }
    }
}

class ValidationException extends RuntimeException { ValidationException(String msg) { super(msg); } }

class SchemaValidator {
    private final List<String> requiredFields = List.of("id", "status");
    private final Set<String> allowedStatuses = Set.of("PENDING", "SHIPPED", "DELIVERED");

    void validate(Map<String, Object> doc) {
        for (String field : requiredFields) {
            if (!doc.containsKey(field)) throw new ValidationException("missing required field: " + field);
        }
        Object status = doc.get("status");
        if (!allowedStatuses.contains(status)) {
            throw new ValidationException("status '" + status + "' not in enum " + allowedStatuses);
        }
        Object total = doc.get("total");
        if (total != null && ((Number) total).doubleValue() < 0) {
            throw new ValidationException("total must be >= 0, was " + total);
        }
    }
}
```

How to run: `java JsonSchemaLevel2.java`

Document `"1"` satisfies every rule and is accepted. Document `"2"` has a `status` outside the allowed enum values and is rejected. Document `"3"` has a valid status but a negative `total`, violating the `minimum` constraint, and is also rejected — together these mirror the combined `required`/`enum`/`minimum` clauses a real `$jsonSchema` validator checks in one pass.

### Level 3 — Advanced

Add MongoDB's two validator knobs: **validation level** (`strict` checks every write, `moderate` only checks writes to documents that already matched the schema) and **validation action** (`error` rejects the write, `warn` logs but allows it) — letting existing non-conforming data coexist during a gradual migration.

```java
import java.util.*;

public class JsonSchemaLevel3 {
    public static void main(String[] args) {
        System.out.println("--- strict + error (default: reject anything invalid) ---");
        SchemaValidator strictError = new SchemaValidator("strict", "error");
        strictError.insert("1", Map.of("id", "1", "status", "PENDING"), true);
        strictError.insert("2", Map.of("id", "2", "status", "UNKNOWN"), true);

        System.out.println("--- strict + warn (log problems, but allow the write, e.g. during a migration) ---");
        SchemaValidator strictWarn = new SchemaValidator("strict", "warn");
        strictWarn.insert("3", Map.of("id", "3", "status", "UNKNOWN"), true);

        System.out.println("--- moderate + error (only re-check documents that already conformed) ---");
        SchemaValidator moderateError = new SchemaValidator("moderate", "error");
        moderateError.insert("4", Map.of("status", "UNKNOWN"), false); // legacy doc, already non-conforming -- skipped
        moderateError.insert("5", Map.of("id", "5", "status", "UNKNOWN"), true); // was valid before -- checked, rejected
    }
}

class SchemaValidator {
    private final List<String> requiredFields = List.of("id", "status");
    private final Set<String> allowedStatuses = Set.of("PENDING", "SHIPPED", "DELIVERED");
    private final String validationLevel;  // "strict" or "moderate"
    private final String validationAction; // "error" or "warn"

    SchemaValidator(String validationLevel, String validationAction) {
        this.validationLevel = validationLevel; this.validationAction = validationAction;
    }

    private List<String> check(Map<String, Object> doc) {
        List<String> errors = new ArrayList<>();
        for (String field : requiredFields) if (!doc.containsKey(field)) errors.add("missing required field: " + field);
        if (doc.containsKey("status") && !allowedStatuses.contains(doc.get("status")))
            errors.add("status '" + doc.get("status") + "' not in enum " + allowedStatuses);
        return errors;
    }

    // insert(doc, alreadyMatchedSchema) -- moderate level SKIPS re-checking documents that were already non-conforming.
    void insert(String id, Map<String, Object> doc, boolean existingDocAlreadyValid) {
        if (validationLevel.equals("moderate") && !existingDocAlreadyValid) {
            System.out.println(id + ": moderate level -- pre-existing invalid document left untouched, no check run");
            return;
        }
        List<String> errors = check(doc);
        if (errors.isEmpty()) { System.out.println(id + ": accepted"); return; }
        if (validationAction.equals("error")) {
            System.out.println(id + ": REJECTED - " + errors);
        } else { // "warn"
            System.out.println(id + ": accepted WITH WARNING - " + errors);
        }
    }
}
```

How to run: `java JsonSchemaLevel3.java`

The three configurations show the same malformed data treated three different ways: `strict`+`error` rejects it outright; `strict`+`warn` accepts it but logs a warning, useful while rolling out a new schema against existing traffic; `moderate`+`error` only enforces the schema on documents that were already conforming, letting known-legacy documents (`existingDocAlreadyValid=false`) pass through untouched while still protecting newly-conforming data going forward.

## 6. Walkthrough

Execution starts in `main` for Level 3. The first block creates a `strict`+`error` validator and inserts document `"1"` (valid — accepted) and document `"2"` (invalid `status` — since level is `strict`, `check` always runs; since action is `error`, the write is rejected and printed as `REJECTED`).

The second block creates a `strict`+`warn` validator and inserts document `"3"` with the same invalid `status`. Because the level is still `strict`, `check` runs and finds the same error — but because the action is `warn` rather than `error`, `insert` prints `accepted WITH WARNING` instead of rejecting: the document is written despite failing validation, with the problem only logged.

The third block creates a `moderate`+`error` validator. Document `"4"` is inserted with `existingDocAlreadyValid=false`, meaning it represents a legacy document that didn't conform to the schema even before this validator existed. Because the level is `moderate`, `insert` checks `existingDocAlreadyValid` first — it's `false`, so `check` never runs at all, and the method returns immediately without validating: MongoDB's `moderate` level only re-validates documents that already matched the schema before, deliberately leaving legacy non-conforming documents alone. Document `"5"`, by contrast, is inserted with `existingDocAlreadyValid=true` (it represents a document that used to pass validation), so `moderate` *does* check it — its `status` is invalid, and since the action is `error`, it's rejected.

```
--- strict + error (default: reject anything invalid) ---
1: accepted
2: REJECTED - [status 'UNKNOWN' not in enum [DELIVERED, PENDING, SHIPPED]]
--- strict + warn (log problems, but allow the write, e.g. during a migration) ---
3: accepted WITH WARNING - [status 'UNKNOWN' not in enum [DELIVERED, PENDING, SHIPPED]]
--- moderate + error (only re-check documents that already conformed) ---
4: moderate level -- pre-existing invalid document left untouched, no check run
5: REJECTED - [status 'UNKNOWN' not in enum [DELIVERED, PENDING, SHIPPED]]
```

In real MongoDB, `validationLevel` and `validationAction` are set via `db.runCommand({collMod: "orders", validator: {...}, validationLevel: "moderate", validationAction: "warn"})`, and Spring Data MongoDB exposes the same two settings through `CollectionOptions.empty().validator(Validator.schema(schema)).validationAction(ValidationAction.WARN).validationLevel(ValidationLevel.MODERATE)` — the standard rollout pattern is to start with `warn`, observe how much existing data would fail, fix it, and only then flip to `error` for full enforcement.

## 7. Gotchas & takeaways

> Gotcha: adding a stricter validator to a collection that already contains non-conforming documents does **not** retroactively fix or reject those existing documents — it only affects future writes. Use `validationLevel: "moderate"` (or run a migration first) to avoid suddenly being unable to update documents that predate the schema.

> Gotcha: `$jsonSchema` validation happens on the MongoDB server, independent of any Spring Data annotation like `@NotNull` — Bean Validation on your Java entities only protects writes that go through your application; a schema validator protects the collection no matter what client writes to it.

- `CollectionOptions.empty().validator(Validator.schema(...))` attaches a `$jsonSchema` to a collection, enforced by the database on every write, from any client.
- `required`, `properties.<field>.enum`, and range constraints like `minimum` are the schema-building blocks, combining the same way Bean Validation annotations do in application code.
- `validationAction`: `error` rejects non-conforming writes; `warn` logs but allows them — useful for a gradual, observed rollout.
- `validationLevel`: `strict` checks every write; `moderate` only re-checks documents that already conformed, letting pre-existing legacy documents remain untouched.
