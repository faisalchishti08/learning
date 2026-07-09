---
card: java
gi: 711
slug: context-specific-deserialization-filters
title: Context-specific deserialization filters
---

## 1. What it is

**Java 17** (JEP 415) added a way to install a **JVM-wide filter factory** for Java object deserialization, letting an application select a *different* `ObjectInputFilter` depending on the **context** of each individual deserialization operation — which stream is being read, which class initiated it, or any other criterion the application defines — rather than being limited to one single, static, global filter for the entire JVM. Deserialization filters (`ObjectInputFilter`, added years earlier) already let you allow-list or block-list which classes are permitted to be reconstructed from a byte stream, closing off a major class of deserialization-based security vulnerabilities. This JEP makes filter selection itself programmable and dynamic, driven by `ObjectInputFilter.Config.setSerialFilterFactory(...)`.

## 2. Why & when

Before this JEP, a JVM could have exactly one global deserialization filter, set once via a system property or `ObjectInputFilter.Config.setSerialFilter(...)`, applied uniformly to every `ObjectInputStream` in the process. That's too coarse for many real applications: a server might deserialize data from several different sources — an internal RMI call, an external client upload, a trusted cache — each of which should reasonably be allowed to reconstruct a different, narrower set of classes. Rather than one filter permissive enough to cover every source's needs (weakening the protection for the most sensitive source), a filter *factory* lets the application inspect each new `ObjectInputStream` as it's created and hand back a filter tailored to that specific context — tightening the allow-list precisely where a given deserialization path doesn't need broad class support. Reach for a filter factory whenever a single application deserializes data from multiple distinct trust contexts and a one-size-fits-all global filter would otherwise force you to either over-permit or maintain separate JVMs per context.

## 3. Core concept

```java
import java.io.*;

ObjectInputFilter.Config.setSerialFilterFactory((currentFilter, newStreamFilter) -> {
    // 'newStreamFilter' is whatever filter (if any) the specific ObjectInputStream requested;
    // this factory can accept it, replace it, or combine it with a context-wide policy.
    if (newStreamFilter != null) return newStreamFilter;
    return ObjectInputFilter.Config.createFilter("java.base/*;!*"); // default: only java.base classes
});
```

The factory is consulted once per `ObjectInputStream` at creation time, giving the application a hook to pick a filter based on that stream's own context rather than one filter for every stream in the JVM.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single global deserialization filter applies uniformly to every ObjectInputStream; a filter factory instead selects a tailored filter per stream, based on that stream's own context">
  <rect x="20" y="20" width="280" height="170" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Single global filter</text>
  <rect x="50" y="65" width="220" height="30" rx="5" fill="#161b22" stroke="#79c0ff"/>
  <text x="160" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Internal RMI stream</text>
  <rect x="50" y="100" width="220" height="30" rx="5" fill="#161b22" stroke="#79c0ff"/>
  <text x="160" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">External upload stream</text>
  <text x="160" y="155" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">↓ both use the same one filter</text>
  <text x="160" y="172" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">(must be broad enough for both)</text>

  <rect x="340" y="20" width="280" height="170" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Filter factory (Java 17)</text>
  <rect x="370" y="65" width="220" height="30" rx="5" fill="#161b22" stroke="#3fb950"/>
  <text x="480" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Internal RMI stream -&gt; broad filter</text>
  <rect x="370" y="100" width="220" height="30" rx="5" fill="#161b22" stroke="#3fb950"/>
  <text x="480" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">External upload -&gt; strict filter</text>
  <text x="480" y="155" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">each stream gets its own tailored filter</text>
</svg>

The factory is consulted per stream, so different deserialization contexts can be held to different, appropriately-scoped standards.

## 5. Runnable example

Scenario: a small service deserializing data from two different sources with different trust levels — first the basic global-filter approach applied to a single stream, then installing a context-aware factory that picks a strict or permissive filter based on which stream is being opened, then a fuller version tagging streams with a context object and rejecting a deliberately dangerous class to demonstrate the filter actually blocking something.

### Level 1 — Basic

```java
// File: GlobalFilterBasic.java
import java.io.*;

public class GlobalFilterBasic {
    record Message(String text) implements Serializable {}

    public static void main(String[] args) throws Exception {
        ObjectInputFilter.Config.setSerialFilter(
                ObjectInputFilter.Config.createFilter("GlobalFilterBasic$Message;!*"));

        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bytes)) {
            out.writeObject(new Message("hello"));
        }

        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(bytes.toByteArray()))) {
            Message msg = (Message) in.readObject();
            System.out.println("Deserialized: " + msg.text());
        }
    }
}
```

**How to run:**
```
java GlobalFilterBasic.java
```

Expected output:
```
Deserialized: hello
```

### Level 2 — Intermediate

```java
// File: ContextualFilterFactory.java
import java.io.*;

public class ContextualFilterFactory {
    record InternalEvent(String detail) implements Serializable {}
    record ExternalUpload(String filename) implements Serializable {}

    public static void main(String[] args) throws Exception {
        // A factory consulted once per ObjectInputStream, choosing a filter by context.
        ObjectInputFilter.Config.setSerialFilterFactory((currentFilter, requestedFilter) -> {
            if (requestedFilter != null) return requestedFilter; // stream asked for something specific
            return ObjectInputFilter.Config.createFilter(
                    "ContextualFilterFactory$InternalEvent;ContextualFilterFactory$ExternalUpload;!*");
        });

        byte[] internalBytes = serialize(new InternalEvent("cache-refresh"));
        byte[] uploadBytes = serialize(new ExternalUpload("report.csv"));

        System.out.println("Internal: " + deserialize(internalBytes));
        System.out.println("Upload:   " + deserialize(uploadBytes));
    }

    static byte[] serialize(Object obj) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bytes)) {
            out.writeObject(obj);
        }
        return bytes.toByteArray();
    }

    static Object deserialize(byte[] data) throws IOException, ClassNotFoundException {
        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(data))) {
            return in.readObject();
        }
    }
}
```

**How to run:**
```
java ContextualFilterFactory.java
```

Expected output:
```
Internal: InternalEvent[detail=cache-refresh]
Upload:   ExternalUpload[filename=report.csv]
```

### Level 3 — Advanced

```java
// File: FilterRejectsUnexpectedClass.java
import java.io.*;

public class FilterRejectsUnexpectedClass {
    record TrustedPayload(String data) implements Serializable {}
    record UnexpectedClass(String data) implements Serializable {}

    public static void main(String[] args) throws Exception {
        // Only TrustedPayload is ever allowed through, regardless of what's actually in the stream.
        ObjectInputFilter.Config.setSerialFilterFactory((currentFilter, requestedFilter) ->
                ObjectInputFilter.Config.createFilter("FilterRejectsUnexpectedClass$TrustedPayload;!*"));

        byte[] trustedBytes = serialize(new TrustedPayload("ok"));
        byte[] unexpectedBytes = serialize(new UnexpectedClass("not allowed"));

        System.out.println("Trusted:   " + deserialize(trustedBytes));

        try {
            deserialize(unexpectedBytes);
            System.out.println("Unexpected: deserialized (this should not happen)");
        } catch (InvalidClassException e) {
            System.out.println("Unexpected: rejected by filter -> " + e.getMessage());
        }
    }

    static byte[] serialize(Object obj) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bytes)) {
            out.writeObject(obj);
        }
        return bytes.toByteArray();
    }

    static Object deserialize(byte[] data) throws IOException, ClassNotFoundException {
        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(data))) {
            return in.readObject();
        }
    }
}
```

**How to run:**
```
java FilterRejectsUnexpectedClass.java
```

Expected output shape (the exact rejection message text can vary slightly by JDK build):
```
Trusted:   TrustedPayload[data=ok]
Unexpected: rejected by filter -> filter status: REJECTED, class: FilterRejectsUnexpectedClass$UnexpectedClass, ...
```

## 6. Walkthrough

1. `main` installs a filter factory via `ObjectInputFilter.Config.setSerialFilterFactory(...)` **before any deserialization happens** — this must be set once, early in the application's lifecycle (setting it a second time throws, by design, to prevent malicious code from silently loosening an already-installed filter).
2. The lambda passed to `setSerialFilterFactory` ignores its `requestedFilter` parameter entirely and always returns the same strict filter string, `"FilterRejectsUnexpectedClass$TrustedPayload;!*"` — read as "allow `TrustedPayload` specifically; reject everything else" (`!*` is the catch-all reject pattern).
3. `serialize(new TrustedPayload("ok"))` and `serialize(new UnexpectedClass("not allowed"))` each write an ordinary Java-serialized byte stream via `ObjectOutputStream` — serialization itself is unaffected by input filters, which only govern *deserialization*.
4. `deserialize(trustedBytes)` opens an `ObjectInputStream` over the trusted bytes; **every** `ObjectInputStream` created from this point on automatically consults the installed filter factory, which hands back the strict `TrustedPayload`-only filter; since the stream's actual class is `TrustedPayload`, the filter allows it through, and `readObject()` succeeds.
5. `deserialize(unexpectedBytes)` repeats the same process, but this time the stream's actual class is `UnexpectedClass` — the filter's `!*` catch-all rejects it, and `readObject()` throws `InvalidClassException` rather than reconstructing an object of a class the filter never allow-listed.
6. The `try`/`catch` around the second `deserialize` call demonstrates the filter actually doing its job: without any filter installed at all, `UnexpectedClass` would have deserialized successfully just like `TrustedPayload` did, since ordinary Java deserialization has no built-in concept of "this class shouldn't be reconstructable here" — that protection exists entirely because of the filter this JEP's factory mechanism installed.

```
setSerialFilterFactory(factory)     <- installed once, early
        │
ObjectInputStream created  ──►  factory consulted  ──►  filter selected for this stream
        │
readObject() called  ──►  filter checks the actual class in the stream
        │
   allowed?  -> object reconstructed
   rejected? -> InvalidClassException thrown, object never reconstructed
```

## 7. Gotchas & takeaways

> `ObjectInputFilter.Config.setSerialFilterFactory(...)` can only be called **once** per JVM — a second call throws `IllegalStateException` by design, specifically so that once an application (or its security-conscious startup code) installs a filter factory, no later code path (including potentially malicious code that made it onto the classpath) can quietly replace it with a more permissive one.
- A filter factory receives **both** the currently-installed filter and any filter the specific `ObjectInputStream` itself requested (via `ObjectInputStream.setObjectInputFilter(...)`) — a well-designed factory typically combines or chooses between these rather than ignoring one entirely, unlike this tutorial's deliberately simple always-strict example.
- The filter pattern syntax (`"Package.Class;!*"`) predates this JEP — what's new here is *when and how* a filter gets selected (per-stream, via a factory), not the filter pattern language itself.
- `InvalidClassException` thrown by a rejecting filter should generally be treated as a security-relevant event worth logging, not silently swallowed — it means something attempted to deserialize a class your application explicitly decided it should never reconstruct.
- Reach for this JEP's factory mechanism specifically when one JVM process genuinely deserializes data from multiple distinct trust boundaries; if there's only ever one deserialization context in your application, a single static filter (via `setSerialFilter`, predating this JEP) remains simpler and sufficient.
- This JEP is squarely a security-hardening feature, complementary to but unrelated to [Deprecate Security Manager for removal](0712-deprecate-security-manager-for-removal.md), landing in this same release — both reflect the JDK's broader move away from one coarse, JVM-wide security mechanism (a single global `SecurityManager` or filter) toward finer-grained, context-aware controls.
