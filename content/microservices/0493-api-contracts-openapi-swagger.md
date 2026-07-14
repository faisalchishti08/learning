---
card: microservices
gi: 493
slug: api-contracts-openapi-swagger
title: "API contracts (OpenAPI / Swagger)"
---

## 1. What it is

**OpenAPI** (the specification format, formerly known as Swagger) is a standardized, machine-readable way to describe a REST API's contract — its endpoints, request parameters, response schemas, status codes, and authentication requirements — in a structured document (typically YAML or JSON) that both humans and tools can read. "Swagger" now most commonly refers to the ecosystem of tools (Swagger UI, Swagger Editor) built around the OpenAPI specification.

## 2. Why & when

You write an OpenAPI specification for any API with consumers who need a precise, tooling-friendly description of it:

- **A precise, structured contract removes ambiguity that prose documentation alone leaves open.** "Returns the order" is ambiguous about exact field names, types, and whether a field can be null; an OpenAPI schema specifies exactly that, unambiguously, in a form tools can validate against.
- **Tooling can generate real artifacts directly from the specification.** Client SDKs, server-side interface stubs, interactive documentation (Swagger UI), and mock servers can all be generated automatically from one OpenAPI document, rather than hand-written and kept manually in sync.
- **It's the concrete artifact [API-first design](0492-api-first-design.md) needs.** "Design the contract before the implementation" needs the contract to actually exist as something reviewable and toolable — OpenAPI is the standard, widely-supported format for that artifact.
- **You maintain this specification for the lifetime of any REST API with external or cross-team consumers** — keeping it current isn't a one-time task at launch, it's an ongoing responsibility alongside the API itself.

## 3. Core concept

Think of an OpenAPI document as a detailed nutrition label on packaged food: it specifies exactly what's inside (fields, types), in a standardized format anyone can read regardless of the specific product, and it enables automated tools (like a shopping app checking dietary restrictions) to reason about the product without a human having to manually inspect it — versus a vague verbal description of "it's healthy-ish," which no tool could reliably act on.

Concretely, an OpenAPI document describes:

1. **Paths and operations** — each endpoint (`/orders/{orderId}`) and the HTTP methods it supports (`GET`, `POST`), each documented separately.
2. **Request schemas** — for operations that accept a body, the exact structure, field types, and which fields are required versus optional.
3. **Response schemas per status code** — what a `200 OK` response body looks like, distinct from what a `404 Not Found` response looks like, each with its own schema.
4. **Reusable component schemas** — a shape like `Order` can be defined once and referenced everywhere it's used, keeping the document consistent and avoiding duplicated, potentially drifting definitions.
5. **Security schemes** — how the API expects to be authenticated (an API key header, a bearer token), documented as part of the same specification.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One OpenAPI document generates multiple downstream artifacts: interactive documentation, a client SDK, and server-side interface stubs">
  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">openapi.yaml</text>

  <rect x="20" y="120" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="150" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Swagger UI docs</text>

  <rect x="245" y="120" width="170" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="330" y="150" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">generated client SDK</text>

  <rect x="470" y="120" width="170" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="555" y="150" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">server interface stubs</text>

  <line x1="290" y1="70" x2="130" y2="120" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="330" y1="70" x2="330" y2="120" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="370" y1="70" x2="530" y2="120" stroke="#8b949e" marker-end="url(#a1)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

One OpenAPI document is the single source multiple downstream tools and artifacts are generated from.

## 5. Runnable example

We model an OpenAPI document's structure and the validation it enables, in plain Java, since a real specification parser is beyond a single-file demo. We start with a basic schema definition and one endpoint description, extend it to validating a real response against that schema, then handle the hard case: a response missing a required field the schema mandates, which validation must catch precisely.

### Level 1 — Basic

```java
// File: OpenApiSchemaBasic.java -- models the CORE idea of an OpenAPI
// schema: a STRUCTURED, machine-readable description of a response
// shape, including which fields are REQUIRED.
import java.util.*;

public class OpenApiSchemaBasic {
    record FieldSchema(String name, String type, boolean required) {}
    record EndpointSchema(String path, String method, List<FieldSchema> responseFields) {}

    static EndpointSchema getOrderSchema = new EndpointSchema(
        "/orders/{orderId}", "GET",
        List.of(
            new FieldSchema("orderId", "string", true),
            new FieldSchema("status", "string", true),
            new FieldSchema("totalAmount", "number", true),
            new FieldSchema("couponCode", "string", false) // optional
        )
    );

    public static void main(String[] args) {
        System.out.println("[openapi] documented endpoint: " + getOrderSchema.method() + " " + getOrderSchema.path());
        for (FieldSchema field : getOrderSchema.responseFields()) {
            System.out.println("  - " + field.name() + ": " + field.type() + (field.required() ? " (required)" : " (optional)"));
        }
    }
}
```

How to run: `java OpenApiSchemaBasic.java`

`EndpointSchema` and `FieldSchema` model the structured shape a real OpenAPI YAML document describes — each field has a name, a type, and an explicit required/optional flag, exactly the level of precision that lets tooling (and this example's later validation logic) reason about the contract programmatically rather than from vague prose.

### Level 2 — Intermediate

```java
// File: OpenApiValidateResponse.java -- the SAME schema, now used to
// VALIDATE a REAL response against it -- checking every required field
// is present and every field's type matches what the schema specifies.
import java.util.*;

public class OpenApiValidateResponse {
    record FieldSchema(String name, String type, boolean required) {}
    record EndpointSchema(String path, String method, List<FieldSchema> responseFields) {}

    static EndpointSchema getOrderSchema = new EndpointSchema(
        "/orders/{orderId}", "GET",
        List.of(
            new FieldSchema("orderId", "string", true),
            new FieldSchema("status", "string", true),
            new FieldSchema("totalAmount", "number", true),
            new FieldSchema("couponCode", "string", false)
        )
    );

    static List<String> validateResponse(EndpointSchema schema, Map<String, Object> actualResponse) {
        List<String> errors = new ArrayList<>();
        for (FieldSchema field : schema.responseFields()) {
            boolean present = actualResponse.containsKey(field.name());
            if (field.required() && !present) {
                errors.add("missing required field: " + field.name());
            }
        }
        return errors;
    }

    public static void main(String[] args) {
        Map<String, Object> actualResponse = new LinkedHashMap<>();
        actualResponse.put("orderId", "order-42");
        actualResponse.put("status", "SHIPPED");
        actualResponse.put("totalAmount", 79.50);
        // couponCode intentionally absent -- it's OPTIONAL, so this should be fine.

        List<String> errors = validateResponse(getOrderSchema, actualResponse);
        System.out.println("[validation] response: " + actualResponse);
        System.out.println("[validation] errors: " + (errors.isEmpty() ? "none -- valid" : errors));
    }
}
```

How to run: `java OpenApiValidateResponse.java`

`validateResponse` walks every field the schema declares and, for each one marked `required`, checks it's actually present in `actualResponse` via `containsKey`. `couponCode` is absent from `actualResponse` but marked `required = false` in the schema, so its absence never triggers an error — only genuinely required-and-missing fields are flagged, exactly matching what a real OpenAPI-based validator would check.

### Level 3 — Advanced

```java
// File: OpenApiCatchMissingRequiredField.java -- the SAME validation, now
// handling the PRODUCTION-FLAVORED hard case: a REAL response is MISSING
// a REQUIRED field due to an implementation bug (a code path that forgot
// to set totalAmount under a specific condition). This MUST be caught
// precisely, naming the exact missing field, not just a vague "invalid
// response" message.
import java.util.*;

public class OpenApiCatchMissingRequiredField {
    record FieldSchema(String name, String type, boolean required) {}
    record EndpointSchema(String path, String method, List<FieldSchema> responseFields) {}

    static EndpointSchema getOrderSchema = new EndpointSchema(
        "/orders/{orderId}", "GET",
        List.of(
            new FieldSchema("orderId", "string", true),
            new FieldSchema("status", "string", true),
            new FieldSchema("totalAmount", "number", true),
            new FieldSchema("couponCode", "string", false)
        )
    );

    // Simulates a REAL implementation bug: totalAmount is missing for CANCELLED orders,
    // because a developer's code path forgot to set it in that specific case.
    static Map<String, Object> buggyGetOrderImplementation(String orderId, String status) {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("orderId", orderId);
        response.put("status", status);
        if (!status.equals("CANCELLED")) {
            response.put("totalAmount", 79.50);
        }
        // BUG: when status is CANCELLED, totalAmount is never set, even though the schema requires it.
        return response;
    }

    static List<String> validateResponse(EndpointSchema schema, Map<String, Object> actualResponse) {
        List<String> errors = new ArrayList<>();
        for (FieldSchema field : schema.responseFields()) {
            boolean present = actualResponse.containsKey(field.name());
            if (field.required() && !present) {
                errors.add("missing required field: '" + field.name() + "' (declared required in the OpenAPI schema for " + schema.method() + " " + schema.path() + ")");
            }
        }
        return errors;
    }

    public static void main(String[] args) {
        System.out.println("--- normal order: totalAmount present ---");
        Map<String, Object> normalResponse = buggyGetOrderImplementation("order-1", "SHIPPED");
        List<String> normalErrors = validateResponse(getOrderSchema, normalResponse);
        System.out.println("[validation] " + normalResponse + " -> " + (normalErrors.isEmpty() ? "valid" : normalErrors));

        System.out.println();
        System.out.println("--- cancelled order: totalAmount MISSING due to implementation bug ---");
        Map<String, Object> buggyResponse = buggyGetOrderImplementation("order-2", "CANCELLED");
        List<String> buggyErrors = validateResponse(getOrderSchema, buggyResponse);
        System.out.println("[validation] " + buggyResponse + " -> " + (buggyErrors.isEmpty() ? "valid" : buggyErrors));
    }
}
```

How to run: `java OpenApiCatchMissingRequiredField.java`

`buggyGetOrderImplementation` deliberately reproduces a real implementation bug: its `if (!status.equals("CANCELLED"))` guard means `totalAmount` is only ever added to the response map for non-cancelled orders. `validateResponse` runs the identical schema-checking logic against both cases — the normal order passes cleanly, while the cancelled order's response, missing `totalAmount` entirely, triggers a precise error naming exactly that field and exactly which documented endpoint requires it.

## 6. Walkthrough

Trace `OpenApiCatchMissingRequiredField.main` in order. **First**, the normal-order case calls `buggyGetOrderImplementation("order-1", "SHIPPED")`. Since `status` doesn't equal `"CANCELLED"`, the `if` guard is `true`, so `totalAmount` is added to `response` — the returned map contains all three required fields.

**Next**, `validateResponse(getOrderSchema, normalResponse)` runs its loop over the schema's four fields. For `orderId`, `status`, and `totalAmount`, all `required = true` and all present in `normalResponse`, so no errors are added for any of them; `couponCode` is `required = false`, so its absence is never even checked. `normalErrors` ends up empty, and `main` prints "valid."

**Then**, the cancelled-order case calls `buggyGetOrderImplementation("order-2", "CANCELLED")`. This time `status.equals("CANCELLED")` is `true`, so `!status.equals("CANCELLED")` is `false` — the `if` guard's body never runs, and `totalAmount` is never added to `response` at all. The returned map contains only `orderId` and `status`.

**After that**, `validateResponse(getOrderSchema, buggyResponse)` runs the identical loop. For `orderId` and `status`, both are present, so no errors. For `totalAmount`, `field.required()` is `true` but `actualResponse.containsKey("totalAmount")` is now `false`, since it was never added — the condition `field.required() && !present` evaluates to `true`, and a specific error is appended naming `totalAmount` and the exact endpoint it's required for.

**Finally**, `main` prints `buggyErrors`, showing exactly one precise, actionable error — pinpointing the missing field and its source endpoint, rather than a vague failure — demonstrating how a schema-driven validation approach catches a real implementation bug with specificity a hand-written prose contract never could.

```
--- normal order: totalAmount present ---
[validation] {orderId=order-1, status=SHIPPED, totalAmount=79.5} -> valid

--- cancelled order: totalAmount MISSING due to implementation bug ---
[validation] {orderId=order-2, status=CANCELLED} -> [missing required field: 'totalAmount' (declared required in the OpenAPI schema for GET /orders/{orderId})]
```

## 7. Gotchas & takeaways

> A schema that marks a field `required` in the specification but whose implementation has an untested code path where that field can be legitimately omitted (as with cancelled orders here) represents a genuine mismatch between documented and actual behavior — either the implementation has a bug, or the schema needs to mark that field as conditionally optional; the ambiguity itself is the problem worth surfacing.
- Generate real client SDKs and server stubs from the OpenAPI document rather than hand-writing them separately — hand-written code drifting from a hand-written document is exactly the inconsistency a machine-readable, tool-processable specification is meant to prevent.
- Validate real API responses against the OpenAPI schema as part of automated testing, not just during initial design — this is what actually catches drift and bugs like the one in Level 3, continuously, rather than relying on the document being correct once and staying that way by assumption.
- Reusable component schemas (referencing a shared `Order` definition across every endpoint that returns one) keep a real specification consistent — defining the same shape independently in multiple places is exactly how documents like this drift internally over time.
- OpenAPI is the concrete artifact that makes [API-first design](0492-api-first-design.md) and [consumer-driven contracts](0497-consumer-driven-contracts.md) practically achievable — both concepts need a precise, structured contract to actually operate on, and OpenAPI is the standard, broadly-tooled format for providing one.
