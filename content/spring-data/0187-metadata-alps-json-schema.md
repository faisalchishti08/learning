---
card: spring-data
gi: 187
slug: metadata-alps-json-schema
title: "Metadata (ALPS / JSON Schema)"
---

## 1. What it is

Spring Data REST can expose machine-readable *metadata* about each resource — not the data itself, but a description of its shape: which fields exist, their types, which are required, which operations are supported. Two formats are supported: ALPS (Application-Level Profile Semantics, via an `ALPS`-typed `Accept` header) and JSON Schema (via a resource's `/customers/schema` / profile endpoint).

```
GET /customers/search   with  Accept: application/alps+json
-> describes available search methods, their parameters, and return types

GET /profile/customers  with  Accept: application/schema+json
-> a JSON Schema describing the Customer resource's fields, types, and constraints
```

## 2. Why & when

The HAL Explorer (previous card) is for a human clicking through an API. Metadata is the machine-readable equivalent — a client program, an API gateway, or a code generator that wants to understand a resource's shape programmatically, without a human reading documentation or reverse-engineering it from sample responses.

Reach for metadata endpoints when:

- Building a generic client or admin UI that should adapt automatically to whatever fields and constraints a resource actually has, rather than hardcoding them.
- Generating client-side validation that mirrors the server's Bean Validation constraints (the earlier validation card) automatically, instead of duplicating `@NotBlank`/`@Size` rules by hand in a separate client codebase.
- An API gateway or documentation tool needs to enumerate available search methods and resources without a human-maintained API spec kept manually in sync.

## 3. Core concept

```
 @Entity
 class Customer {
     @NotBlank String name;
     @Email String email;
 }

 GET /profile/customers  (Accept: application/schema+json)
 ->
 {
   "type": "object",
   "properties": {
     "name":  { "type": "string" },
     "email": { "type": "string", "format": "email" }
   },
   "required": ["name"]
 }

 A generic client reads THIS, not the Java source, to know Customer needs a non-blank name and a valid email.
```

The schema is derived automatically from the entity's own mapping and validation annotations — it's generated, not hand-maintained separately.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Entity annotations are introspected and rendered into a JSON Schema description consumed by a generic client">
  <rect x="20" y="45" width="200" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="68" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Customer entity</text>
  <text x="120" y="84" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@NotBlank, @Email</text>

  <line x1="220" y1="72" x2="280" y2="72" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a20)"/>

  <rect x="290" y="45" width="150" height="55" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="365" y="77" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JSON Schema</text>

  <line x1="440" y1="72" x2="500" y2="72" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a20)"/>

  <rect x="510" y="45" width="110" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="565" y="77" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">generic client</text>

  <defs><marker id="a20" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Entity annotations flow automatically into a generated schema, which a generic client can adapt to without hardcoding.

## 5. Runnable example

The scenario: describing a `Customer` resource's shape programmatically, evolving from a hardcoded client that only works for one specific entity shape, to a generated JSON-Schema-style description derived from annotations, to a generic form-renderer that adapts its output entirely based on that generated schema — no knowledge of `Customer` baked in.

### Level 1 — Basic

Show the hardcoded baseline: a client with `Customer`'s field names and rules baked directly into its own code.

```java
public class MetadataLevel1 {
    public static void main(String[] args) {
        System.out.println(renderCustomerForm()); // knows about "name" and "email" specifically, hardcoded
    }

    // Hardcoded for Customer specifically -- adding a new entity means writing a whole new method.
    static String renderCustomerForm() {
        return "Form: [name: text, required] [email: text, format=email]";
    }
}
```

How to run: `java MetadataLevel1.java`

`renderCustomerForm` only ever knows how to render a `Customer` — a second entity (`Order`, say) would need its own hand-written rendering method, with no shared, generic logic between them.

### Level 2 — Intermediate

Generate a schema-like description from `Customer`'s annotations, decoupling the description from any specific rendering logic.

```java
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class MetadataLevel2 {
    public static void main(String[] args) {
        Map<String, FieldSchema> schema = generateSchema(Customer.class);
        System.out.println("GET /profile/customers ->");
        for (Map.Entry<String, FieldSchema> entry : schema.entrySet()) {
            FieldSchema fs = entry.getValue();
            System.out.println("  " + entry.getKey() + ": type=" + fs.type + ", required=" + fs.required + ", format=" + fs.format);
        }
    }

    @Retention(RetentionPolicy.RUNTIME) @interface NotBlank {}
    @Retention(RetentionPolicy.RUNTIME) @interface Email {}

    record FieldSchema(String type, boolean required, String format) {}

    // Introspects the entity's annotations -- the SAME generation logic Spring Data REST performs internally.
    static Map<String, FieldSchema> generateSchema(Class<?> entityClass) {
        Map<String, FieldSchema> schema = new LinkedHashMap<>();
        for (Field field : entityClass.getDeclaredFields()) {
            if (field.getName().equals("id")) continue;
            boolean required = field.isAnnotationPresent(NotBlank.class);
            String format = field.isAnnotationPresent(Email.class) ? "email" : null;
            schema.put(field.getName(), new FieldSchema("string", required, format));
        }
        return schema;
    }
}

class Customer {
    String id;
    @MetadataLevel2.NotBlank String name;
    @MetadataLevel2.Email String email;
}
```

How to run: `java MetadataLevel2.java`

`generateSchema` works against *any* entity class passed to it — the description of `Customer`'s shape (required `name`, `email`-formatted `email`) is derived entirely from its annotations, with no `Customer`-specific code written anywhere in `generateSchema` itself.

### Level 3 — Advanced

Build a generic form renderer that consumes the generated schema and produces UI descriptions for *any* entity, demonstrating the schema's actual payoff: one renderer, many entity shapes, zero per-entity rendering code.

```java
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class MetadataLevel3 {
    public static void main(String[] args) {
        System.out.println("Rendering form for Customer:");
        System.out.println(renderForm(generateSchema(Customer.class)));

        System.out.println("\nRendering form for Product:");
        System.out.println(renderForm(generateSchema(Product.class))); // SAME renderer, different entity
    }

    @Retention(RetentionPolicy.RUNTIME) @interface NotBlank {}
    @Retention(RetentionPolicy.RUNTIME) @interface Email {}

    record FieldSchema(String type, boolean required, String format) {}

    static Map<String, FieldSchema> generateSchema(Class<?> entityClass) {
        Map<String, FieldSchema> schema = new LinkedHashMap<>();
        for (Field field : entityClass.getDeclaredFields()) {
            if (field.getName().equals("id")) continue;
            boolean required = field.isAnnotationPresent(NotBlank.class);
            String format = field.isAnnotationPresent(Email.class) ? "email" : null;
            String type = field.getType() == int.class ? "number" : "string";
            schema.put(field.getName(), new FieldSchema(type, required, format));
        }
        return schema;
    }

    // Generic: adapts entirely to whatever schema it's given, no entity-specific code inside it.
    static String renderForm(Map<String, FieldSchema> schema) {
        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, FieldSchema> entry : schema.entrySet()) {
            FieldSchema fs = entry.getValue();
            sb.append("[").append(entry.getKey()).append(": ").append(fs.type);
            if (fs.required) sb.append(", required");
            if (fs.format != null) sb.append(", format=").append(fs.format);
            sb.append("] ");
        }
        return sb.toString().trim();
    }
}

class Customer {
    String id;
    @MetadataLevel3.NotBlank String name;
    @MetadataLevel3.Email String email;
}

class Product {
    String id;
    @MetadataLevel3.NotBlank String name;
    int stockCount;
}
```

How to run: `java MetadataLevel3.java`

`renderForm` is called with two entirely different entity schemas — `Customer` and `Product` — and produces a correctly shaped form for each, without a single line of `if (entity instanceof Customer)`-style branching; it's driven purely by the generated schema data, exactly how a real generic admin UI or client SDK consuming ALPS/JSON Schema metadata from Spring Data REST would work.

## 6. Walkthrough

Execution starts in `main` for Level 3. `generateSchema(Customer.class)` introspects `Customer`'s fields, producing a schema with `name` (required, string) and `email` (string, format `email`). `renderForm` consumes that schema and builds a form description purely from its contents:

```
Rendering form for Customer:
[name: string, required] [email: string, format=email]
```

The second call repeats the exact same two steps against `Product.class` instead — `generateSchema` finds `name` (required, string) and `stockCount` (a plain, non-required `number`, since it's an `int` field with no annotations), and the *same* `renderForm` method renders a completely different-looking form:

```
Rendering form for Product:
[name: string, required] [stockCount: number]
```

In a real Spring Data REST application, `GET /profile/customers` (or the ALPS-typed equivalent) performs exactly this introspection automatically, at request time, deriving the metadata from the entity's actual JPA/Bean Validation annotations — any change to the entity (a new `@NotBlank` field, a renamed property) is reflected in the next metadata request immediately, with zero manual synchronization required between the entity class and its published schema.

## 7. Gotchas & takeaways

> Gotcha: generated metadata reflects the entity's *persistence and validation* annotations, which don't always perfectly match the intended *public API* contract — a field marked `@JsonIgnore` (from the earlier item/collection customization card) for serialization purposes might still appear in a naively generated schema if the schema generator doesn't account for the same visibility rules, producing a schema that describes fields the actual JSON responses never include.

> Gotcha: consuming generated schema metadata to drive a fully generic client UI is powerful, but it also means UI/UX quality is capped by what the schema can express — Bean Validation constraints translate reasonably well to form validation, but nuanced business rules (the kind that need `@HandleBeforeCreate`, from an earlier card) have no representation in the schema at all, so a purely schema-driven client will miss them entirely.

- Metadata endpoints (ALPS, JSON Schema) expose a resource's shape machine-readably, generated automatically from entity mapping and validation annotations.
- This enables generic clients, admin UIs, and code generators that adapt to a resource's actual shape without hardcoding field names or duplicating validation rules.
- The schema is only as accurate as what can be introspected from annotations — custom business validation and serialization customizations may not be reflected unless the generator specifically accounts for them.
- Changes to an entity's fields or constraints are reflected in the next metadata request automatically, keeping the published schema and the actual entity shape in sync without manual maintenance.
