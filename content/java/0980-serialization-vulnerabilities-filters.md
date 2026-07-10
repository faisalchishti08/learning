---
card: java
gi: 980
slug: serialization-vulnerabilities-filters
title: Serialization vulnerabilities & filters
---

## 1. What it is

Java's built-in object serialization (`ObjectOutputStream`/`ObjectInputStream`) has a specific, well-documented security weakness: deserializing data means the JVM will instantiate whatever classes the serialized stream *says* it contains, running their constructors and, in certain circumstances, arbitrary code paths reachable during deserialization (`readObject`, `readResolve`, and similar methods) — if that stream comes from an untrusted or unauthenticated source, an attacker can craft a malicious payload referencing classes already present on the target application's classpath whose deserialization side effects can be chained together into arbitrary code execution, a class of attack generally known as a "deserialization gadget chain." `ObjectInputFilter` (standardized as a core JDK feature in Java 9, later strengthened) is the primary defense: a filter installed on an `ObjectInputStream` (or, since Java 17, configurable process-wide via the `jdk.serialFilter` system property) that inspects each class the stream is about to deserialize and can reject it outright — by class name, by an allowlist/denylist pattern, by object graph depth, or by total object count — before the dangerous instantiation and reconstruction logic ever runs.

## 2. Why & when

This matters anywhere your application deserializes data from a source it does not fully control or trust — an untrusted network client sending serialized objects, a message queue whose messages might have been tampered with, or even, in some cases, application-internal data whose provenance turns out to be less trustworthy than initially assumed. The attack works because deserialization is fundamentally different from ordinary parsing: parsing JSON or XML only ever produces plain data structures (strings, numbers, maps), with no way for the *data itself* to cause arbitrary class instantiation or method execution as a side effect of merely being parsed — but Java's native object serialization format explicitly encodes which classes to instantiate and can trigger real code execution (via `readObject` and related mechanisms) purely as a consequence of the deserialization process itself, which is precisely the surface a gadget-chain attack exploits. The practical guidance, in order of preference: avoid Java's native serialization entirely for any data crossing a trust boundary, using a format like JSON or Protocol Buffers instead (explored in [alternatives to Java serialization](0981-alternatives-to-java-serialization-json-protobuf.md)), which have no equivalent code-execution-during-parsing risk; if native serialization genuinely cannot be avoided, always install an `ObjectInputFilter` restricting deserialization to a specific, minimal allowlist of expected classes, rejecting everything else by default.

## 3. Core concept

```java
// VULNERABLE: deserializing untrusted data with no filter at all --
// the stream can instantiate ANY class present on the classpath.
ObjectInputStream in = new ObjectInputStream(untrustedInputStream);
Object obj = in.readObject(); // if 'untrustedInputStream' is attacker-controlled, this is dangerous

// PROTECTED: an ObjectInputFilter restricts deserialization to an explicit ALLOWLIST.
ObjectInputFilter filter = ObjectInputFilter.Config.createFilter(
    "com.example.MyDto;com.example.MyOtherDto;!*" // allow ONLY these classes, reject everything else
);
ObjectInputStream in2 = new ObjectInputStream(untrustedInputStream);
in2.setObjectInputFilter(filter);
Object safeObj = in2.readObject(); // throws InvalidClassException if the stream references anything not allowed
```

The filter pattern syntax reads left to right: `com.example.MyDto` allows exactly that class, `!*` rejects everything else not already explicitly matched — an allowlist-first, deny-by-default approach is the recommended, safe default posture for any deserialization of untrusted data.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An untrusted serialized stream being checked by an ObjectInputFilter against an allowlist before any class is instantiated, rejecting anything not explicitly permitted" >
  <rect x="20" y="60" width="150" height="40" fill="#1c2430" stroke="#f0883e"/>
  <text x="95" y="85" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Untrusted byte stream</text>

  <rect x="220" y="60" width="180" height="40" fill="#1c2430" stroke="#6db33f"/>
  <text x="310" y="80" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ObjectInputFilter</text>
  <text x="310" y="93" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">checks class BEFORE instantiation</text>

  <rect x="450" y="20" width="160" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="39" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">allowed -&gt; instantiated</text>

  <rect x="450" y="90" width="160" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="530" y="109" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">rejected -&gt; exception, NO instantiation</text>

  <line x1="170" y1="80" x2="220" y2="80" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="400" y1="70" x2="450" y2="35" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="400" y1="90" x2="450" y2="105" stroke="#8b949e" marker-end="url(#a)"/>
</svg>

*The filter inspects each class the stream references before any instantiation happens, blocking anything not explicitly allowed.*

## 5. Runnable example

Scenario: build a small object-receiving service and progressively secure it against deserialization risk — starting with a basic unfiltered deserialization, then adding an explicit allowlist filter, then handling a rejected class gracefully as a genuine security control rather than an unexpected crash.

### Level 1 — Basic

```java
import java.io.*;

public class SerializationFilterBasic {
    record SafeDto(String name, int value) implements Serializable {}

    public static void main(String[] args) throws Exception {
        SafeDto original = new SafeDto("widget", 42);

        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bos)) {
            out.writeObject(original);
        }
        byte[] serialized = bos.toByteArray();

        // NO filter installed here -- this stream would accept ANY serializable class.
        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(serialized))) {
            SafeDto deserialized = (SafeDto) in.readObject();
            System.out.println("deserialized: " + deserialized);
        }
    }
}
```

**How to run:** `java SerializationFilterBasic.java` (JDK 17+; records implementing `Serializable` work with ordinary Java serialization).

Expected output:
```
deserialized: SafeDto[name=widget, value=42]
```

This establishes an unfiltered baseline: the deserialization works correctly for this known, trusted data, but nothing here would stop this exact same `ObjectInputStream` from also accepting and instantiating an entirely different, unexpected class if the byte stream happened to reference one instead — there is no restriction on what classes this stream is willing to deserialize.

### Level 2 — Intermediate

```java
import java.io.*;

public class SerializationFilterAllowlist {
    record SafeDto(String name, int value) implements Serializable {}
    record UnexpectedClass(String payload) implements Serializable {}

    static byte[] serialize(Object obj) throws IOException {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bos)) {
            out.writeObject(obj);
        }
        return bos.toByteArray();
    }

    static Object deserializeWithFilter(byte[] data, String filterPattern) throws Exception {
        ObjectInputFilter filter = ObjectInputFilter.Config.createFilter(filterPattern);
        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(data))) {
            in.setObjectInputFilter(filter);
            return in.readObject();
        }
    }

    public static void main(String[] args) throws Exception {
        String allowlist = "SerializationFilterAllowlist$SafeDto;!*"; // allow ONLY SafeDto

        byte[] safeBytes = serialize(new SafeDto("widget", 42));
        byte[] unexpectedBytes = serialize(new UnexpectedClass("suspicious payload"));

        Object result1 = deserializeWithFilter(safeBytes, allowlist);
        System.out.println("allowed class deserialized: " + result1);

        try {
            deserializeWithFilter(unexpectedBytes, allowlist);
        } catch (InvalidClassException e) {
            System.out.println("rejected as expected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java SerializationFilterAllowlist.java` (JDK 17+).

Expected output:
```
allowed class deserialized: SafeDto[name=widget, value=42]
rejected as expected: filter status: REJECTED
```

The real-world concern added: the filter pattern explicitly allows only `SafeDto` and rejects everything else (`!*`); attempting to deserialize a *different* class (`UnexpectedClass`) — even one that's perfectly legitimate and harmless in this contrived example — is rejected before instantiation, throwing `InvalidClassException` rather than silently proceeding; in a real attack scenario, this exact mechanism is what prevents a malicious gadget-chain class from ever being instantiated in the first place, regardless of how cleverly crafted the malicious byte stream might otherwise be.

### Level 3 — Advanced

```java
import java.io.*;

public class SerializationFilterProcessWide {
    record SafeDto(String name, int value) implements Serializable {}

    public static void main(String[] args) throws Exception {
        // Simulate configuring a PROCESS-WIDE default filter (Java 17+), which applies
        // to EVERY ObjectInputStream in the JVM that doesn't set its own more specific filter --
        // this is the recommended defense-in-depth layer for an entire application, not
        // just individual deserialization call sites.
        ObjectInputFilter processWideFilter = ObjectInputFilter.Config.createFilter(
            "java.lang.*;SerializationFilterProcessWide$SafeDto;maxdepth=5;maxrefs=100;!*"
        );
        ObjectInputFilter.Config.setSerialFilter(processWideFilter);

        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bos)) {
            out.writeObject(new SafeDto("widget", 42));
        }
        byte[] data = bos.toByteArray();

        // NOTE: this stream sets NO filter of its own -- it will use the PROCESS-WIDE
        // default filter configured above automatically.
        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(data))) {
            Object result = in.readObject();
            System.out.println("deserialized under process-wide filter: " + result);
        }
    }
}
```

**How to run:** `java SerializationFilterProcessWide.java` (JDK 17+; `ObjectInputFilter.Config.setSerialFilter` establishes a JVM-wide default filter).

Expected output:
```
deserialized under process-wide filter: SafeDto[name=widget, value=42]
```

The production-flavored hard case: `maxdepth=5` and `maxrefs=100` add further protection beyond just class-name allowlisting — limiting how deeply nested an object graph is allowed to be and how many total object references a single stream may contain, which guards against a different but related attack: a maliciously crafted stream using only "allowed" classes but structured as an extremely deep or extremely large object graph specifically designed to exhaust memory or CPU during deserialization (a denial-of-service vector, distinct from the code-execution gadget-chain risk); configuring this as the *process-wide* default (rather than per-stream) ensures every `ObjectInputStream` in the application benefits from this baseline protection automatically, even ones a developer might forget to configure individually.

## 6. Walkthrough

Tracing what happens when `deserializeWithFilter(unexpectedBytes, allowlist)` is called in `SerializationFilterAllowlist.main`:

1. `unexpectedBytes` contains a serialized `UnexpectedClass` instance — the byte stream itself encodes, among other things, the fully-qualified class name of the object it represents, which `ObjectInputStream` must consult in order to know what kind of object to reconstruct.
2. `in.setObjectInputFilter(filter)` has already installed the allowlist filter (`"SerializationFilterAllowlist$SafeDto;!*"`) on this specific `ObjectInputStream` before `readObject()` is called.
3. When `in.readObject()` begins processing the stream, it first reads the encoded class name from the stream's header — before proceeding to actually instantiate anything, it consults the installed filter, passing it information about the class being requested (`UnexpectedClass`).
4. The filter evaluates its pattern rules against this class name in order: `SerializationFilterAllowlist$SafeDto` does not match `UnexpectedClass`, so that specific allow rule doesn't apply; the filter then reaches the final `!*` rule, which rejects anything not already explicitly allowed — since nothing before it matched, this catch-all rejection applies.
5. Because the filter's verdict is "reject," `ObjectInputStream` throws `InvalidClassException` immediately, at this exact point — critically, *before* any constructor, `readObject` method, or other class-specific deserialization logic for `UnexpectedClass` has run at all; the class was never actually instantiated or given any opportunity to execute code.
6. The surrounding `catch` block in `main` catches this exception and prints its message, confirming the rejection happened as intended — this is exactly the security property the filter provides: a malicious or unexpected class referenced in an untrusted stream is stopped at the class-name-checking stage, before its potentially dangerous deserialization-time code (a crafted `readObject` override forming part of a gadget chain, for instance) ever gets a chance to run.

## 7. Gotchas & takeaways

> **Gotcha:** an allowlist filter is only as good as its completeness — if the allowlist accidentally includes a class that is itself part of a known gadget chain (some common utility or collection classes have historically been implicated in real-world gadget chains), the filter provides no protection against that specific class being exploited; keeping an allowlist as small and specific as possible, limited strictly to your application's own actual DTOs, and periodically reviewing it against newly-discovered gadget-chain research, is an ongoing security maintenance responsibility, not a one-time configuration task.

- Java's native object serialization can instantiate arbitrary classes and trigger code execution as a side effect of deserialization itself, which untrusted input can exploit via "gadget chain" attacks — a fundamentally different risk profile than plain data-only formats like JSON.
- `ObjectInputFilter` inspects each class a stream references before instantiation, letting you reject anything not explicitly allowed — an allowlist-first, deny-by-default (`!*`) approach is the recommended safe posture.
- Beyond class-name filtering, `maxdepth` and `maxrefs` guard against a separate denial-of-service risk: maliciously deep or maliciously large object graphs built entirely out of otherwise-allowed classes.
- A process-wide default filter (`ObjectInputFilter.Config.setSerialFilter`, Java 17+) provides baseline protection across every `ObjectInputStream` in an application automatically, as defense-in-depth beyond per-stream filters a developer might forget to configure.
- The strongest defense is avoiding native Java serialization for untrusted data entirely — see [alternatives to Java serialization (JSON, protobuf)](0981-alternatives-to-java-serialization-json-protobuf.md) for formats with no equivalent code-execution-during-parsing risk.
- An allowlist is only as safe as its contents — accidentally including a class implicated in a known gadget chain defeats the filter's protection for that specific class, making periodic review essential.
