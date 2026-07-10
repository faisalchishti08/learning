---
card: java
gi: 982
slug: externalizable-vs-serializable
title: Externalizable vs Serializable
---

## 1. What it is

`Serializable` is a marker interface (it declares no methods at all) that opts a class into Java's default, automatic serialization mechanism — the JVM uses reflection to inspect the object's fields and writes them out (and reads them back) according to a built-in, general-purpose algorithm, one you can customize in limited ways (via `transient` fields, or `writeObject`/`readObject` methods) but don't fully control. `Externalizable` extends `Serializable` but requires implementing exactly two methods yourself — `writeExternal(ObjectOutput out)` and `readExternal(ObjectInput in)` — giving you complete, explicit control over precisely which bytes get written and how they're read back, with no automatic, reflection-based field-by-field serialization happening at all unless you write code to do it yourself. The key structural difference: `Serializable`'s default mechanism figures out what to write by reflecting over the class's fields at serialization time, while `Externalizable` requires you to write that logic explicitly, trading convenience for complete control over the wire format.

## 2. Why & when

`Serializable`'s default mechanism is the right choice for the overwhelming majority of cases — it requires essentially no code (just the marker interface) and correctly handles the common case of "serialize all the non-transient fields, reconstruct them on the other side" without any further thought. `Externalizable` matters specifically when you need precise control over the serialized format that `Serializable`'s default, reflection-based approach cannot give you: a genuinely custom, compact binary layout (skipping the overhead of Java serialization's built-in class-metadata bookkeeping for every single field), backward-compatible versioning logic you want to implement explicitly rather than relying on `serialVersionUID` matching, or — a subtle but important distinction — needing serialization performance closer to hand-written I/O code, since `Externalizable`'s explicit `writeExternal`/`readExternal` methods avoid the reflective field access `Serializable`'s default mechanism relies on, which can matter for very hot, performance-sensitive serialization paths. The tradeoff is real: with `Externalizable`, you are fully responsible for correctly writing and reading every field yourself, in a matching order, with no automatic help — a mistake (writing fields in one order, reading them in a different order) is a real, easy-to-introduce bug that `Serializable`'s automatic mechanism simply cannot produce, since it always handles the write/read symmetry for you.

## 3. Core concept

```java
// Serializable: automatic, reflection-based -- no code needed beyond the marker interface
class SerializablePoint implements Serializable {
    int x, y; // the default mechanism reflects over these fields automatically
}

// Externalizable: fully explicit -- YOU write exactly what gets serialized and how
class ExternalizablePoint implements Externalizable {
    int x, y;

    public ExternalizablePoint() {} // a PUBLIC no-arg constructor is REQUIRED for Externalizable

    public void writeExternal(ObjectOutput out) throws IOException {
        out.writeInt(x);   // YOU decide exactly what bytes get written, and in what order
        out.writeInt(y);
    }

    public void readExternal(ObjectInput in) throws IOException {
        x = in.readInt();  // MUST read back in the EXACT same order written, or data is corrupted
        y = in.readInt();
    }
}
```

`Externalizable` requires a public no-argument constructor (used to create a blank instance before `readExternal` populates it), and every byte written by `writeExternal` must be read back, in the exact same order, by `readExternal` — there is no automatic symmetry checking, unlike `Serializable`'s default mechanism, which always handles this correspondence correctly on its own.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Serializable using automatic, reflection-based field writing, versus Externalizable requiring explicit, manually-matched write and read methods" >
  <rect x="20" y="30" width="280" height="90" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Serializable</text>
  <text x="160" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JVM reflects over fields</text>
  <text x="160" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">automatic write/read symmetry</text>
  <text x="160" y="108" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">no code needed, less control</text>

  <rect x="340" y="30" width="280" height="90" fill="#1c2430" stroke="#f0883e"/>
  <text x="480" y="50" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Externalizable</text>
  <text x="480" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">YOU write writeExternal/readExternal</text>
  <text x="480" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">must match order MANUALLY</text>
  <text x="480" y="108" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">full control, full responsibility</text>
</svg>

*Serializable's default mechanism handles write/read symmetry automatically; Externalizable gives full control but requires you to maintain that symmetry correctly yourself.*

## 5. Runnable example

Scenario: build a small point/coordinate serialization comparison, evolving from a basic Serializable version, to an Externalizable version with explicit, compact control, to a more advanced case demonstrating the real danger of a mismatched write/read order in Externalizable and how to guard against it.

### Level 1 — Basic

```java
import java.io.*;

public class ExternalizableComparisonBasic {
    static class SerializablePoint implements Serializable {
        int x, y;
        SerializablePoint(int x, int y) { this.x = x; this.y = y; }
        public String toString() { return "(" + x + ", " + y + ")"; }
    }

    public static void main(String[] args) throws Exception {
        SerializablePoint point = new SerializablePoint(3, 4);

        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bos)) {
            out.writeObject(point);
        }
        byte[] data = bos.toByteArray();

        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(data))) {
            SerializablePoint restored = (SerializablePoint) in.readObject();
            System.out.println("restored: " + restored);
            System.out.println("serialized size: " + data.length + " bytes");
        }
    }
}
```

**How to run:** `java ExternalizableComparisonBasic.java` (JDK 17+).

Expected output shape:
```
restored: (3, 4)
serialized size: 62 bytes
```

`SerializablePoint` requires no serialization-specific code beyond `implements Serializable` — the JVM's default mechanism reflects over its `x` and `y` fields automatically, writing and reading them symmetrically with zero risk of a write/read order mismatch, at the cost of including class-metadata overhead in the serialized bytes beyond just the two actual integer values.

### Level 2 — Intermediate

```java
import java.io.*;

public class ExternalizableComparisonExplicit {
    static class ExternalizablePoint implements Externalizable {
        int x, y;

        public ExternalizablePoint() {} // REQUIRED: public no-arg constructor
        ExternalizablePoint(int x, int y) { this.x = x; this.y = y; }

        public void writeExternal(ObjectOutput out) throws IOException {
            out.writeInt(x);
            out.writeInt(y);
        }

        public void readExternal(ObjectInput in) throws IOException {
            x = in.readInt(); // MUST match writeExternal's order exactly
            y = in.readInt();
        }

        public String toString() { return "(" + x + ", " + y + ")"; }
    }

    public static void main(String[] args) throws Exception {
        ExternalizablePoint point = new ExternalizablePoint(3, 4);

        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bos)) {
            out.writeObject(point);
        }
        byte[] data = bos.toByteArray();

        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(data))) {
            ExternalizablePoint restored = (ExternalizablePoint) in.readObject();
            System.out.println("restored: " + restored);
            System.out.println("serialized size: " + data.length + " bytes");
        }
    }
}
```

**How to run:** `java ExternalizableComparisonExplicit.java` (JDK 17+).

Expected output shape (noticeably smaller than the Serializable version for the same logical data):
```
restored: (3, 4)
serialized size: 27 bytes
```

The real-world concern added: `ExternalizablePoint` writes only exactly the two raw integers (`writeInt(x)`, `writeInt(y)`), with no reflection-based field discovery and correspondingly less per-object metadata overhead than the default `Serializable` mechanism — this control is the direct payoff `Externalizable` offers, at the cost of needing the required public no-arg constructor and manually-matched `writeExternal`/`readExternal` logic.

### Level 3 — Advanced

```java
import java.io.*;

public class ExternalizableMismatchDanger {
    static class BuggyPoint implements Externalizable {
        int x, y;
        String label = "unset";

        public BuggyPoint() {}
        BuggyPoint(int x, int y, String label) { this.x = x; this.y = y; this.label = label; }

        public void writeExternal(ObjectOutput out) throws IOException {
            out.writeInt(x);
            out.writeUTF(label); // label written SECOND
            out.writeInt(y);
        }

        public void readExternal(ObjectInput in) throws IOException {
            x = in.readInt();
            y = in.readInt();       // BUG: reads an int where a String was actually written next
            label = in.readUTF();   // BUG: reading order does NOT match writeExternal's order
        }

        public String toString() { return "(" + x + ", " + y + ") label=" + label; }
    }

    public static void main(String[] args) {
        BuggyPoint point = new BuggyPoint(3, 4, "origin");

        try {
            ByteArrayOutputStream bos = new ByteArrayOutputStream();
            try (ObjectOutputStream out = new ObjectOutputStream(bos)) {
                out.writeObject(point);
            }
            byte[] data = bos.toByteArray();

            try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(data))) {
                BuggyPoint restored = (BuggyPoint) in.readObject();
                System.out.println("restored: " + restored);
            }
        } catch (Exception e) {
            System.out.println("failed as expected due to write/read order mismatch: " + e.getClass().getSimpleName());
        }
    }
}
```

**How to run:** `java ExternalizableMismatchDanger.java` (JDK 17+).

Expected output shape (the exact exception type may vary, but it reliably fails):
```
failed as expected due to write/read order mismatch: UTFDataFormatException
```

The production-flavored hard case: `writeExternal` writes fields in the order `x, label, y`, but `readExternal` reads them in the mismatched order `x, y, label` — since `Externalizable` provides no automatic verification that these two methods stay in sync, the bytes written for `label` (a UTF-encoded string) are misinterpreted by `readExternal`'s attempt to read an `int` in that position instead, producing garbage or, as here, an outright parsing failure; this exact class of bug is structurally impossible with `Serializable`'s default mechanism, since its automatic, reflection-based approach always keeps writing and reading correctly symmetric without any manual bookkeeping to get wrong.

## 6. Walkthrough

Tracing why `ExternalizableMismatchDanger.main` fails, comparing the mismatched write and read sequences directly:

1. `writeExternal` is called during serialization, writing exactly three values, in this order: an `int` (`x = 3`), a UTF-encoded string (`label = "origin"`, written via `writeUTF`, which itself writes a length prefix followed by the string's encoded bytes), and finally another `int` (`y = 4`).
2. The resulting byte stream, in order, contains: 4 bytes for `x`, then a UTF length prefix plus the encoded bytes for `"origin"`, then 4 bytes for `y` — this exact sequence of bytes is what `readExternal` must correctly parse back, in the same order, to reconstruct the object.
3. `readExternal` is called during deserialization, but its logic reads in a *different* order: first an `int` (correctly reading `x = 3`, since that's genuinely first in the stream), then — incorrectly — attempts to read a *second* `int` where the stream actually contains the UTF-encoded `label` string's length prefix and bytes.
4. `readInt()` interprets whatever bytes happen to be at this position (the beginning of the UTF-encoded string data) as if they were a 4-byte integer — this doesn't necessarily fail outright at this specific step; it may simply produce a nonsensical, garbage integer value for what should have been `y`, silently corrupting that field.
5. The final `readExternal` call, `label = in.readUTF()`, then attempts to read a UTF-encoded string starting from whatever position the stream's read cursor is now at — since the cursor's position has been thrown off by the earlier misread, this call reads from a nonsensical position in the stream, and `readUTF`'s internal validation (checking that the length prefix it reads corresponds to a plausible number of following bytes actually present in the stream) detects the resulting data doesn't form a valid UTF-8 string encoding, throwing `UTFDataFormatException`.
6. This failure — occurring well after the actual root cause (the very first order mismatch between `writeExternal` and `readExternal`) — illustrates precisely the risk `Externalizable` introduces: because there is no compiler or runtime check verifying these two methods stay in sync, a mismatch can propagate several reads deep before finally surfacing as a confusing, seemingly-unrelated exception, or, worse, may not throw an exception at all and instead silently produce corrupted field values, depending on the exact types and data involved.

## 7. Gotchas & takeaways

> **Gotcha:** unlike `Serializable`, `Externalizable` requires the class to have a **public** no-argument constructor — `readExternal` relies on the deserialization machinery being able to construct a blank instance via this constructor before populating its fields; a class without one (or with only a private or package-private no-arg constructor) will fail at deserialization time with `InvalidClassException`, a requirement easy to overlook since `Serializable` itself imposes no such constructor requirement at all.

- `Serializable` opts into automatic, reflection-based serialization with no code beyond the marker interface; `Externalizable` requires explicitly implementing `writeExternal`/`readExternal`, giving full control over the wire format at the cost of full responsibility for correctness.
- `Externalizable` requires a public no-argument constructor, used to construct a blank instance before `readExternal` populates its fields — omitting this constructor causes deserialization to fail.
- `writeExternal` and `readExternal` must read and write fields in exactly the same order — there is no automatic verification of this symmetry, and a mismatch can produce corrupted data or a confusing exception that surfaces well after the actual root-cause line.
- `Externalizable`'s explicit control typically produces a more compact serialized format (no automatic class-metadata overhead per field) and can offer better performance for very hot serialization paths, since it avoids `Serializable`'s reflective field access.
- Prefer `Serializable`'s default mechanism for the overwhelming majority of cases; reach for `Externalizable` specifically when you need precise wire-format control, explicit custom versioning logic, or measurable performance gains that the default mechanism cannot provide.
- See [alternatives to Java serialization (JSON, protobuf)](0981-alternatives-to-java-serialization-json-protobuf.md) for options that avoid Java serialization's format entirely, and [serialization vulnerabilities & filters](0980-serialization-vulnerabilities-filters.md) for the security considerations that apply to both `Serializable` and `Externalizable` alike, since both are part of the same underlying Java serialization mechanism.
