---
card: java
gi: 312
slug: externalizable-interface
title: Externalizable interface
---

## 1. What it is

`Externalizable` is an alternative to `Serializable` that gives a class **complete manual control** over its serialized form. Instead of the JVM using reflection to automatically write and read every field, a class implementing `Externalizable` must define `writeExternal(ObjectOutput)` and `readExternal(ObjectInput)` itself, explicitly writing and reading exactly the data it chooses, in exactly the format it chooses.

```java
import java.io.*;

public class ExternalizableDemo {
    public static void main(String[] args) throws Exception {
        Point p = new Point(3, 4);
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(p);

        Point restored = (Point) new ObjectInputStream(new ByteArrayInputStream(baos.toByteArray())).readObject();
        System.out.println(restored.x + ", " + restored.y);
    }
}

class Point implements Externalizable {
    int x, y;
    public Point() {} // REQUIRED: public no-arg constructor
    public Point(int x, int y) { this.x = x; this.y = y; }

    public void writeExternal(ObjectOutput out) throws IOException {
        out.writeInt(x);
        out.writeInt(y);
    }
    public void readExternal(ObjectInput in) throws IOException {
        x = in.readInt();
        y = in.readInt();
    }
}
```

`writeExternal`/`readExternal` explicitly write and read exactly two ints — no reflection scans the class's fields at all; the class itself is entirely responsible for defining its wire format, field by field, in whatever order it chooses.

## 2. Why & when

Default `Serializable` behavior — reflectively writing every non-transient field — is convenient but comes with real costs: it's relatively verbose on the wire (class metadata, field names, type descriptors), relies on reflection (which has a runtime cost), and gives you little control over the exact byte layout. `Externalizable` trades that automation for explicit, hand-written control.

- **Compact wire format** — since you write only the bytes you choose, with no automatic field-name or class-metadata overhead beyond a minimal class identifier, `Externalizable` output can be substantially smaller than default `Serializable` output for the same data.
- **Performance** — avoiding reflection-based field enumeration on every serialize/deserialize call can matter for high-throughput scenarios (many objects serialized per second).
- **Explicit versioning control** — because you write the format yourself, you can build in your own versioning scheme (a version byte at the start, custom migration logic) rather than relying solely on `serialVersionUID`.

Reach for `Externalizable` when you need tight control over the serialized format — typically for performance-sensitive code or when interoperating with a specific external binary format — and are willing to accept the added responsibility of writing and maintaining the encode/decode logic by hand. For everyday persistence needs where `Serializable`'s automation is "good enough," it remains the simpler default.

## 3. Core concept

```java
import java.io.*;

public class ExternalizableCore {
    public static void main(String[] args) throws Exception {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(new Money(1050));
        System.out.println("Serialized size: " + baos.toByteArray().length + " bytes");
    }
}

class Money implements Externalizable {
    long cents; // store as cents internally to avoid floating-point issues
    public Money() {}
    public Money(long cents) { this.cents = cents; }

    public void writeExternal(ObjectOutput out) throws IOException {
        out.writeLong(cents); // exactly 8 bytes, nothing else
    }
    public void readExternal(ObjectInput in) throws IOException {
        cents = in.readLong();
    }
}
```

The `Externalizable` mechanism requires a public no-argument constructor because deserialization constructs the object first (via that constructor, bypassing any of the class's other constructors entirely) and only *then* calls `readExternal` to populate its state — this is a structural requirement of the interface, not merely a convention.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Externalizable deserialization first constructs an empty object via its no-arg constructor then calls readExternal to populate it">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="35" width="170" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="62" fill="#e6edf3" font-size="10" text-anchor="middle">1. no-arg constructor</text>
  <line x1="192" y1="57" x2="260" y2="57" stroke="#3fb950" stroke-width="2" marker-end="url(#e1)"/>
  <rect x="265" y="35" width="170" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="350" y="62" fill="#e6edf3" font-size="10" text-anchor="middle">2. readExternal(in)</text>
  <line x1="437" y1="57" x2="500" y2="57" stroke="#3fb950" stroke-width="2" marker-end="url(#e2)"/>
  <rect x="500" y="35" width="80" height="45" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="540" y="62" fill="#e6edf3" font-size="9" text-anchor="middle">populated</text>
  <text x="20" y="110" fill="#8b949e" font-size="9">Unlike Serializable, the no-arg constructor genuinely runs -- fields start at defaults, then readExternal fills them in.</text>
  <defs>
    <marker id="e1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="e2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

`Externalizable` deserialization genuinely constructs then populates, unlike `Serializable`'s field-only reconstruction.

## 5. Runnable example

Scenario: a compact binary log-entry record, evolved from a basic `Externalizable` round-trip into a size comparison against default `Serializable`, then into a version that adds a custom format-version byte to support evolving the wire format safely over time.

### Level 1 — Basic

```java
import java.io.*;

public class ExternalizableBasic {
    public static void main(String[] args) throws Exception {
        LogEntry entry = new LogEntry(1735689600000L, "Server started");

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(entry);

        LogEntry restored = (LogEntry) new ObjectInputStream(
            new ByteArrayInputStream(baos.toByteArray())).readObject();
        System.out.println(restored.timestamp + ": " + restored.message);
    }
}

class LogEntry implements Externalizable {
    long timestamp;
    String message;
    public LogEntry() {}
    public LogEntry(long timestamp, String message) { this.timestamp = timestamp; this.message = message; }

    public void writeExternal(ObjectOutput out) throws IOException {
        out.writeLong(timestamp);
        out.writeUTF(message);
    }
    public void readExternal(ObjectInput in) throws IOException {
        timestamp = in.readLong();
        message = in.readUTF();
    }
}
```

**How to run:** `java ExternalizableBasic.java`

Explicitly writes and reads exactly two fields in a fixed order — no reflection involved, the class alone defines its wire format.

### Level 2 — Intermediate

Same log entry, now compared directly against an equivalent plain `Serializable` class to measure the actual size difference in the serialized output.

```java
import java.io.*;

public class ExternalizableIntermediate {
    public static void main(String[] args) throws Exception {
        ByteArrayOutputStream extBytes = new ByteArrayOutputStream();
        new ObjectOutputStream(extBytes).writeObject(new LogEntryExternalizable(1735689600000L, "Server started"));

        ByteArrayOutputStream serBytes = new ByteArrayOutputStream();
        new ObjectOutputStream(serBytes).writeObject(new LogEntrySerializable(1735689600000L, "Server started"));

        System.out.println("Externalizable size: " + extBytes.toByteArray().length + " bytes");
        System.out.println("Serializable size: " + serBytes.toByteArray().length + " bytes");
    }
}

class LogEntryExternalizable implements Externalizable {
    long timestamp;
    String message;
    public LogEntryExternalizable() {}
    public LogEntryExternalizable(long timestamp, String message) { this.timestamp = timestamp; this.message = message; }
    public void writeExternal(ObjectOutput out) throws IOException {
        out.writeLong(timestamp);
        out.writeUTF(message);
    }
    public void readExternal(ObjectInput in) throws IOException {
        timestamp = in.readLong();
        message = in.readUTF();
    }
}

class LogEntrySerializable implements Serializable {
    private static final long serialVersionUID = 1L;
    long timestamp;
    String message;
    LogEntrySerializable(long timestamp, String message) { this.timestamp = timestamp; this.message = message; }
}
```

**How to run:** `java ExternalizableIntermediate.java`

Both classes hold identical data, but `LogEntryExternalizable`'s output is noticeably smaller — the `Serializable` version's stream includes reflective class-metadata (field names, types) that `Externalizable`'s hand-written format skips entirely, writing only the raw `long` and UTF string bytes.

### Level 3 — Advanced

Same log entry, now with a custom leading version byte in the hand-written format, letting `readExternal` branch on the format version — demonstrating the kind of forward-evolution control `Externalizable` enables that plain `serialVersionUID` bumping does not (which only signals incompatibility, rather than supporting multiple readable formats side by side).

```java
import java.io.*;

public class ExternalizableAdvanced {
    public static void main(String[] args) throws Exception {
        VersionedLogEntry entry = new VersionedLogEntry(1735689600000L, "Disk usage high", "WARN");

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(entry);

        VersionedLogEntry restored = (VersionedLogEntry) new ObjectInputStream(
            new ByteArrayInputStream(baos.toByteArray())).readObject();
        System.out.println(restored);
    }
}

class VersionedLogEntry implements Externalizable {
    static final byte FORMAT_V1 = 1; // timestamp + message
    static final byte FORMAT_V2 = 2; // timestamp + message + severity

    long timestamp;
    String message;
    String severity = "INFO"; // default for V1 data, which has no severity field

    public VersionedLogEntry() {}
    public VersionedLogEntry(long timestamp, String message, String severity) {
        this.timestamp = timestamp; this.message = message; this.severity = severity;
    }

    public void writeExternal(ObjectOutput out) throws IOException {
        out.writeByte(FORMAT_V2); // always write the CURRENT format going forward
        out.writeLong(timestamp);
        out.writeUTF(message);
        out.writeUTF(severity);
    }

    public void readExternal(ObjectInput in) throws IOException {
        byte format = in.readByte();
        timestamp = in.readLong();
        message = in.readUTF();
        if (format >= FORMAT_V2) {
            severity = in.readUTF();
        }
        // if format == FORMAT_V1, severity keeps its default "INFO" -- no bytes to read
    }

    public String toString() { return "[" + severity + "] " + timestamp + ": " + message; }
}
```

**How to run:** `java ExternalizableAdvanced.java`

`writeExternal` always writes the current format (`FORMAT_V2`, including `severity`); `readExternal` checks the format byte it reads and conditionally reads the extra `severity` field only if the format indicates it's present — this is exactly the kind of custom, self-describing versioning scheme `Externalizable` makes possible, letting a single class's `readExternal` correctly handle both old (`FORMAT_V1`, no severity) and new (`FORMAT_V2`, with severity) data.

## 6. Walkthrough

Trace serialization and deserialization of `entry` in `ExternalizableAdvanced.main` step by step.

**`writeExternal` runs during `writeObject`.** `out.writeByte(FORMAT_V2)` writes the single byte `2` first. `out.writeLong(timestamp)` writes the 8-byte timestamp. `out.writeUTF(message)` writes the length-prefixed `"Disk usage high"`. `out.writeUTF(severity)` writes the length-prefixed `"WARN"`. The resulting stream, wrapped in `ObjectOutputStream`'s own minimal class-identifier wrapper, contains exactly these four pieces of data, in this order.

**Deserialization begins.** Because `VersionedLogEntry` implements `Externalizable`, `ObjectInputStream` first constructs a new instance using the public no-argument constructor — at this point, `timestamp = 0`, `message = null`, and `severity = "INFO"` (its declared default), since none of the real constructor logic ran.

**`readExternal` runs.** `byte format = in.readByte()` reads the first byte, `2` (matching `FORMAT_V2`). `timestamp = in.readLong()` reads the next 8 bytes, recovering `1735689600000L`. `message = in.readUTF()` reads the length-prefixed string, recovering `"Disk usage high"`.

**The version check.** `if (format >= FORMAT_V2)` evaluates `2 >= 2`, which is `true` — so `severity = in.readUTF()` executes, reading the final length-prefixed string, `"WARN"`, and overwriting the constructor-assigned default of `"INFO"`.

**Result.** `restored` now holds `timestamp=1735689600000L`, `message="Disk usage high"`, `severity="WARN"` — an exact match for the original `entry`. If this same `readExternal` method were instead given data written by some hypothetical older `FORMAT_V1`-only version of this class (a single byte `1`, followed by just timestamp and message, no severity), the `if` check would evaluate `1 >= 2` as `false`, skip the `severity` read entirely, and `severity` would remain at its constructor-assigned default, `"INFO"` — demonstrating how the version byte lets one `readExternal` implementation correctly handle multiple historical formats.

```
writeExternal output: [byte: 2] [long: 1735689600000] [UTF: "Disk usage high"] [UTF: "WARN"]

readExternal:
  format = readByte() = 2
  timestamp = readLong() = 1735689600000
  message = readUTF() = "Disk usage high"
  format(2) >= FORMAT_V2(2) -> true -> severity = readUTF() = "WARN"

Hypothetical V1 data: [byte: 1] [long: ...] [UTF: ...]   (no severity bytes)
  format(1) >= FORMAT_V2(2) -> false -> severity stays "INFO" (constructor default)
```

**Output:**
```
[WARN] 1735689600000: Disk usage high
```

## 7. Gotchas & takeaways

> `Externalizable` **requires** a `public` no-argument constructor — deserialization calls it directly to create the initial object before `readExternal` populates any state. If the constructor is missing, non-public, or does expensive/unwanted work (since it genuinely runs on every deserialization, unlike `Serializable`'s constructor-bypassing reconstruction), that's a real, observable difference from default serialization behavior that must be accounted for.

> Because `writeExternal`/`readExternal` define the *entire* wire format by hand, there is no automatic safety net for field additions or removals — every format change must be handled explicitly (as the version-byte pattern above does), or old data becomes unreadable or misread. This is the direct trade-off for the compactness and control `Externalizable` provides over `Serializable`'s reflective, more self-describing default.

- `Externalizable` gives a class full manual control over its serialized format via `writeExternal`/`readExternal`, instead of the JVM's automatic, reflective field-by-field approach.
- A `public` no-argument constructor is mandatory — it genuinely executes during deserialization, before `readExternal` populates the object's state.
- The resulting format is typically more compact than default `Serializable` output, since no field-name/type metadata is written.
- Because there's no automatic compatibility handling, any format evolution (adding fields, changing types) must be managed explicitly, often via a custom version marker written as the first byte or field.
