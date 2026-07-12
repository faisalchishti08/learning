---
card: microservices
gi: 90
slug: protocol-buffers-protobuf-idl
title: "Protocol Buffers (protobuf) IDL"
---

## 1. What it is

Protocol Buffers' IDL (Interface Definition Language) is the `.proto` file format used to define both a service's data structures (`message`) and its RPC methods (`service`) in one language-neutral, declarative file. A `protoc` compiler then generates client and server code from that single `.proto` file in whichever target language each side needs — Java, Python, Go — so every language's generated types stay structurally in sync with the same shared contract, without any language needing to hand-write its own version.

## 2. Why & when

Without a shared IDL, a team maintaining a Java service and a Python client for it would need to manually keep two independently-written representations of the same data structures in sync — a `message Order` field renamed on one side and not the other becomes a runtime bug discovered late, often in production. The `.proto` file makes the contract the single source of truth: change a field there, regenerate code on both sides, and the compiler (not a human cross-referencing two codebases) catches any place still using the old shape. This is precisely the [schema](0085-json-protobuf-avro-serialization.md)-based approach's payoff at the API-contract level, not just the wire-format level.

Use a `.proto` IDL whenever building a gRPC service (it's the standard, required format), or more broadly whenever a strongly-typed, code-generated, cross-language contract is worth the tooling investment for a given service boundary — internal, high-traffic service-to-service APIs benefit most; public APIs consumed by arbitrary third parties usually favor REST/JSON's broader accessibility instead.

## 3. Core concept

A `.proto` file declares `message` types (data shapes, with numbered fields) and `service` definitions (RPC method signatures referencing those messages) — the same source both sides compile against.

```protobuf
syntax = "proto3";

message Order {
  int32 id = 1;
  string status = 2;
  double total = 3;
}

service OrderService {
  rpc GetOrder(GetOrderRequest) returns (Order);
}

message GetOrderRequest {
  int32 id = 1;
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single proto file is compiled by protoc into generated Java code for the server and generated Python code for the client, both structurally derived from the same shared source">
  <rect x="240" y="20" width="160" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">order.proto</text>

  <rect x="240" y="90" width="160" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="112" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">protoc compiler</text>

  <rect x="60" y="150" width="180" height="35" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="150" y="172" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Generated Java (server)</text>

  <rect x="400" y="150" width="180" height="35" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="490" y="172" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Generated Python (client)</text>

  <line x1="320" y1="70" x2="320" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="280" y1="125" x2="150" y2="150" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="360" y1="125" x2="490" y2="150" stroke="#8b949e" stroke-width="1.5"/>
</svg>

One `.proto` source generates structurally consistent code for every target language.

## 5. Runnable example

Scenario: model what `protoc` code generation conceptually produces, first with hand-written, independently-diverging Java and "Python-flavored" representations of the same `Order` concept (simulating the drift problem), then fixed by deriving both from one shared schema definition read at runtime, then extended to detect exactly the kind of field-shape mismatch a real `protoc`-generated build would catch automatically at compile time.

### Level 1 — Basic

```java
// File: IndependentlyWrittenTypes.java -- two hand-written representations
// of the "same" Order concept, maintained independently -- exactly the
// situation a shared .proto file is meant to prevent.
public class IndependentlyWrittenTypes {
    // Java-side representation, written by the Java team
    record JavaOrder(int id, String status, double total) {}

    // "Python-side" representation, written independently by another team
    // (simulated here in Java) -- notice it's ALREADY drifted: totalAmount vs total
    record PythonStyleOrder(int id, String status, double totalAmount) {}

    public static void main(String[] args) {
        JavaOrder javaOrder = new JavaOrder(42, "PLACED", 19.99);
        System.out.println("Java side has field: total=" + javaOrder.total());

        // a Python client expecting "totalAmount" would get a KeyError against
        // real JSON produced by the Java side's "total" field -- a drift bug
        System.out.println("Python side expects field: totalAmount (MISMATCH -- would break at runtime)");
    }
}
```

**How to run:** `javac IndependentlyWrittenTypes.java && java IndependentlyWrittenTypes` (JDK 17+).

Expected output:
```
Java side has field: total=19.99
Python side expects field: totalAmount (MISMATCH -- would break at runtime)
```

### Level 2 — Intermediate

```java
// File: SharedSchemaDerivedTypes.java -- BOTH "sides" derive their field
// names from ONE shared schema definition -- simulating what protoc's
// code generation guarantees: structural consistency from a single source.
import java.util.*;

public class SharedSchemaDerivedTypes {
    // the SHARED .proto-style schema -- the single source of truth
    static List<String> orderSchemaFields = List.of("id", "status", "total");

    static Map<String, Object> buildFromSchema(int id, String status, double total) {
        Map<String, Object> record = new LinkedHashMap<>();
        record.put(orderSchemaFields.get(0), id);
        record.put(orderSchemaFields.get(1), status);
        record.put(orderSchemaFields.get(2), total);
        return record;
    }

    public static void main(String[] args) {
        // BOTH "generated" clients read field NAMES from the same schema list
        Map<String, Object> javaSideOrder = buildFromSchema(42, "PLACED", 19.99);
        System.out.println("Java side fields: " + javaSideOrder.keySet());
        System.out.println("Python side would generate the SAME field names: " + orderSchemaFields);
        System.out.println("javaSideOrder.get(\"total\") = " + javaSideOrder.get("total"));
    }
}
```

**How to run:** `javac SharedSchemaDerivedTypes.java && java SharedSchemaDerivedTypes` (JDK 17+).

Expected output:
```
Java side fields: [id, status, total]
Python side would generate the SAME field names: [id, status, total]
javaSideOrder.get("total") = 19.99
```

### Level 3 — Advanced

```java
// File: DetectingSchemaDrift.java -- simulate what protoc-generated code
// (and the schema itself) makes structurally impossible: a field renamed
// on ONE side without updating the shared schema. This validator models
// the check a real build would perform.
import java.util.*;

public class DetectingSchemaDrift {
    record SchemaField(String name, int fieldNumber) {}

    static List<SchemaField> orderSchema = List.of(
        new SchemaField("id", 1),
        new SchemaField("status", 2),
        new SchemaField("total", 3)
    );

    // simulates a hand-edited client that drifted from the schema (a mistake this check catches)
    static List<String> driftedClientFieldNames = List.of("id", "status", "totalAmount"); // WRONG: should be "total"

    static List<String> validateAgainstSchema(List<String> clientFieldNames) {
        List<String> errors = new ArrayList<>();
        Set<String> schemaNames = new LinkedHashSet<>();
        for (SchemaField f : orderSchema) schemaNames.add(f.name());

        for (String clientField : clientFieldNames) {
            if (!schemaNames.contains(clientField)) {
                errors.add("client references unknown field '" + clientField + "' -- not present in shared schema");
            }
        }
        return errors;
    }

    public static void main(String[] args) {
        List<String> errors = validateAgainstSchema(driftedClientFieldNames);
        if (errors.isEmpty()) {
            System.out.println("Schema validation PASSED");
        } else {
            System.out.println("Schema validation FAILED:");
            errors.forEach(e -> System.out.println("  - " + e));
        }
    }
}
```

**How to run:** `javac DetectingSchemaDrift.java && java DetectingSchemaDrift` (JDK 17+).

Expected output:
```
Schema validation FAILED:
  - client references unknown field 'totalAmount' -- not present in shared schema
```

## 6. Walkthrough

1. **Level 1** — `JavaOrder` and `PythonStyleOrder` are two independently-declared records meant to represent the same underlying concept, but their third field is named differently (`total` vs `totalAmount`) — exactly the kind of silent divergence that happens when two teams hand-write their own version of "the same" data shape without a single shared source. `main` prints both sides' expectations, making the mismatch explicit in the output.
2. **Level 2 — deriving both sides from one shared source** — `orderSchemaFields` is a single list, standing in for what a `.proto` file's `message Order` declaration would define. `buildFromSchema` constructs a `Map` using field names read *from* that shared list, rather than hard-coded independently. `main` prints the Java side's resulting field set and notes that a Python-generated client would derive the *identical* field names, because both would compile against the same schema source — there's no independent hand-writing step left where drift could sneak in.
3. **Level 3 — validating against the schema catches real drift** — `orderSchema` is now a list of `SchemaField` records, each with both a `name` and a `fieldNumber` (mirroring a real `.proto` file's `field = 1`, `field = 2` tag numbers). `driftedClientFieldNames` deliberately simulates a client that has drifted from this schema — its third field is named `"totalAmount"` instead of the schema's `"total"`, representing a hand-edit made without regenerating from the shared source.
4. **Tracing the validation** — `validateAgainstSchema` builds a `schemaNames` set from `orderSchema` (`{"id", "status", "total"}`), then checks each name in `driftedClientFieldNames` against that set. `"id"` and `"status"` both match and pass silently. `"totalAmount"` does *not* match anything in `schemaNames`, so an error message is added to `errors`. `main` finds `errors` non-empty, prints `"Schema validation FAILED:"`, and lists the one mismatch found.
5. **What this models about real `protoc`-based workflows** — in an actual gRPC project, this entire class of bug is caught even earlier and more strongly than a runtime validator like this one: `protoc` generates strongly-typed code directly from the `.proto` file, so a client referencing a field that doesn't exist in the schema simply fails to *compile*, in whichever language it's generated for — there's no way to accidentally ship code referencing `totalAmount` when the schema says `total`, because the generated `Order` type in every language would never have had a `totalAmount` field to reference in the first place.

## 7. Gotchas & takeaways

> **Gotcha:** the `.proto` file's numbered field tags (`= 1`, `= 2`, `= 3`) are part of the wire format itself, not just documentation — reusing a tag number for a different field's meaning (even after renaming or removing the old field) breaks binary compatibility with any data or client still using the old meaning for that tag. Treat tag numbers as permanent once a schema has shipped, exactly as covered in [schema evolution](0085-json-protobuf-avro-serialization.md).

- A `.proto` file is the single source of truth for both a service's data shapes and its RPC method signatures — one file, compiled into every target language's generated code.
- Sharing one schema source structurally prevents the kind of independent-hand-writing drift that plagues systems where each language team maintains its own copy of "the same" data type.
- In a real `protoc`-based workflow, referencing a field that doesn't exist in the schema is a compile-time error in the generated code, not a runtime surprise — much stronger than the validator simulated in Level 3.
- This is the concrete IDL underneath [gRPC and HTTP/2](0089-grpc-and-http-2.md) — the `service` block in a `.proto` file is what generates the RPC method stubs described in the [RPC model](0088-remote-procedure-call-rpc-model.md).
- Never reuse a numbered field tag for a different meaning once a schema has been used to write real data — this breaks the schema evolution guarantees that make Protobuf safe across rolling deployments.
