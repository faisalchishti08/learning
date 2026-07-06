---
card: java
gi: 311
slug: serialversionuid
title: serialVersionUID
---

## 1. What it is

`serialVersionUID` is a `static final long` field a `Serializable` class can declare to explicitly version its serialized form. During deserialization, Java compares the `serialVersionUID` stored in the byte stream against the one defined in the currently-loaded class; if they don't match, deserialization fails immediately with `InvalidClassException`, even if the class otherwise looks compatible.

```java
import java.io.*;

public class SerialVersionDemo {
    public static void main(String[] args) throws Exception {
        Config c = new Config("dark-mode");
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(c);

        Config restored = (Config) new ObjectInputStream(new ByteArrayInputStream(baos.toByteArray())).readObject();
        System.out.println(restored.setting);
    }
}

class Config implements Serializable {
    private static final long serialVersionUID = 1L; // explicit version marker
    String setting;
    Config(String setting) { this.setting = setting; }
}
```

`private static final long serialVersionUID = 1L` is the conventional declaration; without it, Java computes one automatically from the class's structure (fields, methods, interfaces) at both serialization and deserialization time, comparing the two.

## 2. Why & when

If you don't declare `serialVersionUID`, the JVM computes one automatically based on a hash of the class's structural details. This computed value is fragile — recompiling the class with even a trivial change (adding a method, changing field order in source, using a different compiler version) can produce a *different* computed UID, breaking compatibility with previously-serialized data even though the class is functionally unchanged. Declaring it explicitly removes this fragility.

- **Stable compatibility across recompiles** — an explicit `serialVersionUID` stays the same across builds unless you change it yourself, so previously-serialized data remains loadable after routine code changes (adding a method, changing a comment, etc.) that don't affect the field structure.
- **Explicit incompatibility signaling** — deliberately changing the value when you make a breaking change to a class's serialized form forces old data to fail fast with a clear `InvalidClassException`, rather than deserializing into a subtly wrong or corrupted object.
- **IDE and compiler warnings** — most IDEs and the `serial` lint warning specifically flag a `Serializable` class missing an explicit `serialVersionUID`, precisely because the automatic, computed alternative is considered a pitfall.

Always declare `serialVersionUID` explicitly on every `Serializable` class, even if just as `1L` — the specific numeric value doesn't matter for correctness, only that it stays stable (or is deliberately incremented) as the class evolves. Never rely on the auto-computed default in real code.

## 3. Core concept

```java
import java.io.*;

public class SerialVersionCore {
    public static void main(String[] args) throws Exception {
        Widget w = new Widget("Gadget");
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(w);
        byte[] savedBytes = baos.toByteArray(); // simulates data saved with UID 42

        // Deserializing with the SAME class definition (same UID = 42) succeeds:
        Widget restored = (Widget) new ObjectInputStream(new ByteArrayInputStream(savedBytes)).readObject();
        System.out.println("Restored: " + restored.name);
    }
}

class Widget implements Serializable {
    private static final long serialVersionUID = 42L;
    String name;
    Widget(String name) { this.name = name; }
}
```

As long as the `Widget` class definition used for deserialization declares the identical `serialVersionUID` (here, `42L`) that was in effect when the bytes were originally written, deserialization succeeds — mismatching values, simulated by imagining a future version of `Widget` declaring a different UID, would cause `InvalidClassException` on this exact same byte data.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Serialized bytes carry a UID which must match the loaded classs UID at deserialization time or the operation fails">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="220" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="52" fill="#e6edf3" font-size="10" text-anchor="middle">serialized bytes</text>
  <text x="130" y="70" fill="#8b949e" font-size="9" text-anchor="middle">stored UID: 42</text>

  <rect x="330" y="30" width="220" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="440" y="52" fill="#e6edf3" font-size="10" text-anchor="middle">loaded class</text>
  <text x="440" y="70" fill="#8b949e" font-size="9" text-anchor="middle">declared UID: 42</text>

  <text x="290" y="60" fill="#3fb950" font-size="14" text-anchor="middle">==</text>
  <text x="290" y="105" fill="#3fb950" font-size="10" text-anchor="middle">match -&gt; deserialize succeeds</text>
  <text x="290" y="125" fill="#f85149" font-size="10" text-anchor="middle">mismatch -&gt; InvalidClassException</text>
</svg>

The UID comparison happens before any field data is even read — a mismatch fails fast.

## 5. Runnable example

Scenario: a persisted user-preferences object, evolved from a basic explicit-UID round-trip into a simulation of adding a field (safe, UID unchanged), then into a simulation of an incompatible structural change (deliberate UID bump), showing exactly when and why `InvalidClassException` occurs.

### Level 1 — Basic

```java
import java.io.*;

public class SerialVersionBasic {
    public static void main(String[] args) throws Exception {
        Preferences prefs = new Preferences("dark");

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(prefs);

        Preferences restored = (Preferences) new ObjectInputStream(
            new ByteArrayInputStream(baos.toByteArray())).readObject();
        System.out.println("Theme: " + restored.theme);
    }
}

class Preferences implements Serializable {
    private static final long serialVersionUID = 1L;
    String theme;
    Preferences(String theme) { this.theme = theme; }
}
```

**How to run:** `java SerialVersionBasic.java`

An explicit `serialVersionUID = 1L` round-trips normally — establishing the baseline before simulating class evolution.

### Level 2 — Intermediate

Same class, now evolved to add a new field (`fontSize`) while keeping the **same** `serialVersionUID` — a real round-trip confirming that a class carrying an additional field with a sensible default still serializes and deserializes cleanly, which is the backward-compatible shape of change the stable UID is meant to protect.

```java
import java.io.*;

public class SerialVersionIntermediate {
    public static void main(String[] args) throws Exception {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(new Preferences("dark", 16));

        Preferences restored = (Preferences) new ObjectInputStream(
            new ByteArrayInputStream(baos.toByteArray())).readObject();
        System.out.println("theme=" + restored.theme + ", fontSize=" + restored.fontSize);
    }
}

class Preferences implements Serializable {
    private static final long serialVersionUID = 1L; // stays the same across this evolution
    String theme;
    int fontSize = 12; // NEW field since Level 1, with a sensible default

    Preferences(String theme, int fontSize) { this.theme = theme; this.fontSize = fontSize; }
}
```

**How to run:** `java SerialVersionIntermediate.java`

The class now has one more field than the Level 1 version, but because `serialVersionUID` is still declared explicitly (and deliberately left unchanged), the round-trip works exactly as before — in a real deployment, this same unchanged UID is precisely what would let a newer build of this class successfully read data that an older build (without `fontSize`) had written, with `fontSize` simply taking its default value for that older data.

### Level 3 — Advanced

Same preferences class, now demonstrating what an actual `serialVersionUID` **mismatch** looks like: the serialized bytes are patched in place to flip the UID value embedded in the stream, so that reading them back with the unchanged `Preferences` class genuinely triggers `InvalidClassException` — a real, reproducible failure, not a simulated one.

```java
import java.io.*;
import java.util.Arrays;

public class SerialVersionAdvanced {
    static class Preferences implements Serializable {
        private static final long serialVersionUID = 555L;
        String theme;
        Preferences(String theme) { this.theme = theme; }
    }

    // Locates the 8 big-endian bytes of the given UID inside the stream and flips one bit,
    // simulating data that was written by a class declaring a DIFFERENT serialVersionUID.
    static byte[] corruptStoredUid(byte[] data, long originalUid) {
        byte[] uidBytes = new byte[8];
        for (int i = 0; i < 8; i++) {
            uidBytes[i] = (byte) (originalUid >>> (8 * (7 - i)));
        }
        for (int i = 0; i <= data.length - 8; i++) {
            if (Arrays.equals(Arrays.copyOfRange(data, i, i + 8), uidBytes)) {
                byte[] patched = data.clone();
                patched[i + 7] ^= 0x01; // flip the least significant bit of the stored UID
                return patched;
            }
        }
        throw new IllegalStateException("UID pattern not found in stream");
    }

    public static void main(String[] args) throws Exception {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(new Preferences("dark"));
        byte[] originalData = baos.toByteArray();
        byte[] corruptedData = corruptStoredUid(originalData, 555L);

        try {
            new ObjectInputStream(new ByteArrayInputStream(corruptedData)).readObject();
            System.out.println("Unexpected: no exception was thrown");
        } catch (InvalidClassException e) {
            System.out.println("Caught InvalidClassException, as expected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java SerialVersionAdvanced.java`

`corruptStoredUid` finds the exact 8 bytes representing `555L` (the declared UID) inside the serialized stream and flips one bit, producing a byte array that looks, to `ObjectInputStream`, exactly like data written by a class declaring a *different* `serialVersionUID` — reading it back against the real, unmodified `Preferences` class (still declaring `555L`) now genuinely reproduces the mismatch condition and its resulting `InvalidClassException`.

## 6. Walkthrough

Trace `SerialVersionAdvanced.main` step by step.

**Writing the original data.** `new Preferences("dark")` is serialized. The resulting bytes embed both the field data (`theme = "dark"`) **and** a class descriptor recording the class's fully-qualified name and its `serialVersionUID`, `555L`, stored as 8 big-endian bytes somewhere in that descriptor.

**Locating and patching the UID.** `corruptStoredUid` computes the 8-byte big-endian representation of `555L` and scans `originalData` byte by byte, looking for that exact 8-byte sequence — it appears exactly once, inside the class descriptor written by `ObjectOutputStream`. `patched[i + 7] ^= 0x01` flips the very last bit of that 8-byte region, turning the stored UID from `555L` into `554L` (an adjacent value) without altering anything else in the stream, including the actual field data (`theme = "dark"`).

**Attempting to read the patched data.** `new ObjectInputStream(new ByteArrayInputStream(corruptedData)).readObject()` begins reading: it parses the class descriptor, extracts the class name (`Preferences`) and the now-corrupted UID, `554L`. It resolves the class name to the actual, currently-loaded `Preferences` class, which declares `serialVersionUID = 555L`. Comparing `554L` (from the stream) against `555L` (from the loaded class) finds a mismatch.

**The mismatch is detected before any field data is touched.** Java throws `InvalidClassException` immediately, naming the class and the conflicting UIDs in its message — the `theme` field's actual bytes, still intact and correct in the stream, are never even reached, because the class descriptor check happens first.

**Back in `main`.** The `catch (InvalidClassException e)` block catches exactly this exception and prints its message, confirming the mismatch was detected exactly as the UID mechanism is designed to do.

```
Original stream bytes:  [... class descriptor: name="Preferences", UID=555L (8 bytes) ...][theme="dark" field data]

corruptStoredUid flips one bit in the UID's 8 bytes:  555L -> 554L
                                                       (field data bytes are untouched)

readObject() on patched stream, using the real Preferences class (UID=555L):
  stream UID = 554L   vs.   loaded class UID = 555L
  MISMATCH -> InvalidClassException, thrown immediately, before theme is read
```

**Output:**
```
Caught InvalidClassException, as expected: SerialVersionAdvanced$Preferences; local class incompatible: stream classdesc serialVersionUID = 554, local class serialVersionUID = 555
```

## 7. Gotchas & takeaways

> Omitting `serialVersionUID` doesn't make a class "version-independent" — it makes it *more* fragile, because the JVM computes a UID from structural details (fields, method signatures, interfaces) that can change between compilations for reasons completely unrelated to the serialized data's actual shape, silently breaking compatibility with previously-serialized data in ways that are hard to diagnose.

> Bumping `serialVersionUID` is a deliberate, explicit signal that old data is now incompatible — do it precisely when you make a breaking structural change (renaming/removing a field in an incompatible way), and deliberately avoid it when making backward-compatible changes (like adding a new field with a sensible default), so old data can still be read correctly.

- `serialVersionUID` is a version marker compared between the serialized byte stream and the currently-loaded class during deserialization.
- Always declare it explicitly (any stable `long` value, conventionally starting at `1L`) — never rely on the JVM's auto-computed default, which is fragile across recompiles.
- A mismatch throws `InvalidClassException` immediately, before any field data is processed — a deliberate fail-fast behavior.
- Keep the UID unchanged for backward-compatible changes (like adding a field with a default); bump it deliberately for breaking changes to signal incompatibility explicitly.
