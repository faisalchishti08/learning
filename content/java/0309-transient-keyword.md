---
card: java
gi: 309
slug: transient-keyword
title: transient keyword
---

## 1. What it is

`transient` is a field modifier that tells Java's built-in serialization mechanism to **skip** that field entirely — its value is never written during `writeObject`, and after deserialization, a `transient` field is left at its type's default value (`null` for objects, `0`/`false`/etc. for primitives), regardless of what it held before serialization.

```java
import java.io.*;

public class TransientDemo {
    public static void main(String[] args) throws Exception {
        Session s = new Session("alice", "secret-token-123");

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(s);

        Session restored = (Session) new ObjectInputStream(new ByteArrayInputStream(baos.toByteArray())).readObject();
        System.out.println("username: " + restored.username);           // "alice" -- preserved
        System.out.println("temporaryToken: " + restored.temporaryToken); // null -- NOT preserved
    }
}

class Session implements Serializable {
    String username;
    transient String temporaryToken; // deliberately excluded from serialization

    Session(String username, String temporaryToken) {
        this.username = username;
        this.temporaryToken = temporaryToken;
    }
}
```

`username` survives the round-trip because it's an ordinary field; `temporaryToken`, marked `transient`, comes back as `null` even though the original object held `"secret-token-123"` — the serialization mechanism simply never wrote it in the first place.

## 2. Why & when

Not every field belongs in a serialized snapshot. Some fields hold data that is sensitive, meaningless outside the current runtime, or trivially recomputable — serializing them anyway would be wasteful, incorrect, or a security risk.

- **Sensitive data** — passwords, session tokens, or API keys held in memory shouldn't end up persisted to a file or sent over a network as part of an object's serialized form.
- **Runtime-only state** — a field holding a `Thread`, a database `Connection`, or a file handle has no meaningful serialized representation (these resources aren't serializable at all, and even if they were, reconnecting is what should happen on the receiving end, not blindly restoring a dead handle).
- **Derivable/cacheable data** — a field that's just a cached computation from other fields can be marked `transient` and recomputed after deserialization, rather than bloating the serialized size.

Mark any field `transient` that holds sensitive information, a non-serializable resource, or purely-derived data that can (and should) be recomputed rather than persisted. Combine with a custom `readObject` method (an advanced technique) if the field needs to be *repopulated* with something other than its default value immediately after deserialization.

## 3. Core concept

```java
import java.io.*;

public class TransientCore {
    public static void main(String[] args) throws Exception {
        Circle c = new Circle(5.0);
        System.out.println("Before: area = " + c.area);

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(c);
        Circle restored = (Circle) new ObjectInputStream(new ByteArrayInputStream(baos.toByteArray())).readObject();

        System.out.println("After: radius = " + restored.radius + ", area = " + restored.area); // area is 0.0!
    }
}

class Circle implements Serializable {
    double radius;
    transient double area; // derived from radius -- no need to serialize it

    Circle(double radius) {
        this.radius = radius;
        this.area = Math.PI * radius * radius;
    }
}
```

`area` is `0.0` after deserialization — its default `double` value — even though the original object had a correctly computed area, because `transient` fields are never written or restored by the default serialization mechanism, and here nothing recomputes it afterward.

## 4. Diagram

<svg viewBox="0 0 600 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ordinary fields are written to and read from the byte stream, a transient field is skipped entirely on write and defaults on read">
  <rect x="8" y="8" width="584" height="124" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="160" height="80" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="100" y="52" fill="#e6edf3" font-size="10" text-anchor="middle">username = "alice"</text>
  <text x="100" y="72" fill="#f85149" font-size="10" text-anchor="middle">transient token = "..."</text>
  <line x1="182" y1="45" x2="260" y2="45" stroke="#3fb950" stroke-width="2" marker-end="url(#t1)"/>
  <text x="100" y="95" fill="#8b949e" font-size="8" text-anchor="middle">before serialization</text>

  <rect x="265" y="30" width="150" height="80" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="340" y="55" fill="#e6edf3" font-size="9" text-anchor="middle">byte stream</text>
  <text x="340" y="72" fill="#e6edf3" font-size="9" text-anchor="middle">username: written</text>
  <text x="340" y="88" fill="#f85149" font-size="9" text-anchor="middle">token: SKIPPED</text>

  <text x="490" y="45" fill="#8b949e" font-size="9" text-anchor="middle">after deserialization:</text>
  <text x="490" y="62" fill="#e6edf3" font-size="9" text-anchor="middle">username = "alice"</text>
  <text x="490" y="79" fill="#f85149" font-size="9" text-anchor="middle">token = null (default)</text>
  <defs>
    <marker id="t1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

`transient` fields never make the trip; they come back at their type's default value, not their pre-serialization value.

## 5. Runnable example

Scenario: a user session object holding both durable profile data and sensitive/derived transient data, evolved from a basic transient-field demonstration into a version that recomputes a derived transient field automatically after deserialization using a custom `readObject` method.

### Level 1 — Basic

```java
import java.io.*;

public class TransientBasic {
    public static void main(String[] args) throws Exception {
        UserSession session = new UserSession("alice", "abc123token");

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(session);

        UserSession restored = (UserSession) new ObjectInputStream(
            new ByteArrayInputStream(baos.toByteArray())).readObject();

        System.out.println("username: " + restored.username);
        System.out.println("authToken: " + restored.authToken); // null
    }
}

class UserSession implements Serializable {
    String username;
    transient String authToken;

    UserSession(String username, String authToken) {
        this.username = username;
        this.authToken = authToken;
    }
}
```

**How to run:** `java TransientBasic.java`

Confirms the basic behavior: the sensitive `authToken` field never survives serialization, protecting it from ending up in any persisted or transmitted form of the object.

### Level 2 — Intermediate

Same session object, now with a derived `transient` field (a session's remaining validity window, computed from a creation timestamp), demonstrating that recomputable data is also a good `transient` candidate — not just sensitive data.

```java
import java.io.*;

public class TransientIntermediate {
    public static void main(String[] args) throws Exception {
        UserSession session = new UserSession("alice");
        System.out.println("Before: expiresAtMillis = " + session.expiresAtMillis);

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(session);

        UserSession restored = (UserSession) new ObjectInputStream(
            new ByteArrayInputStream(baos.toByteArray())).readObject();

        System.out.println("After: createdAtMillis = " + restored.createdAtMillis);
        System.out.println("After: expiresAtMillis = " + restored.expiresAtMillis); // 0 -- lost!
    }
}

class UserSession implements Serializable {
    String username;
    long createdAtMillis;
    transient long expiresAtMillis; // derived: createdAtMillis + a fixed duration

    UserSession(String username) {
        this.username = username;
        this.createdAtMillis = System.currentTimeMillis();
        this.expiresAtMillis = createdAtMillis + 3600_000; // 1 hour validity
    }
}
```

**How to run:** `java TransientIntermediate.java`

`createdAtMillis` (an ordinary field) survives; `expiresAtMillis` (transient) comes back as `0`, even though it's easily recomputable from `createdAtMillis` — this version deliberately shows the gap that needs fixing.

### Level 3 — Advanced

Same session object, now fixing the gap with a custom `readObject` method: after the default deserialization restores the ordinary fields, custom logic recomputes the transient `expiresAtMillis` field automatically, so callers never see the "lost" default value.

```java
import java.io.*;

public class TransientAdvanced {
    public static void main(String[] args) throws Exception {
        UserSession session = new UserSession("alice");

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(session);

        UserSession restored = (UserSession) new ObjectInputStream(
            new ByteArrayInputStream(baos.toByteArray())).readObject();

        System.out.println("createdAtMillis matches: " + (session.createdAtMillis == restored.createdAtMillis));
        System.out.println("expiresAtMillis recomputed correctly: " + (session.expiresAtMillis == restored.expiresAtMillis));
    }
}

class UserSession implements Serializable {
    String username;
    long createdAtMillis;
    transient long expiresAtMillis;

    UserSession(String username) {
        this.username = username;
        this.createdAtMillis = System.currentTimeMillis();
        this.expiresAtMillis = createdAtMillis + 3600_000;
    }

    // Custom deserialization hook: called automatically by ObjectInputStream.readObject().
    private void readObject(ObjectInputStream in) throws IOException, ClassNotFoundException {
        in.defaultReadObject(); // restores all NON-transient fields normally first
        this.expiresAtMillis = this.createdAtMillis + 3600_000; // recompute the transient field
    }
}
```

**How to run:** `java TransientAdvanced.java`

Defining a `private void readObject(ObjectInputStream in)` method with this exact signature lets `ObjectInputStream` call it automatically during deserialization instead of doing only the default field-restoration — `in.defaultReadObject()` performs that normal restoration first (populating `username` and `createdAtMillis`), after which the custom code recomputes `expiresAtMillis` from the now-available `createdAtMillis`, closing the gap that Level 2 exposed.

## 6. Walkthrough

Trace deserialization of `restored` in `TransientAdvanced.main` step by step.

**`readObject()` is invoked on the new `ObjectInputStream`.** Internally, because `UserSession` defines a private method with the exact signature `readObject(ObjectInputStream)`, the serialization mechanism calls **that** method instead of performing only its own default behavior — this is a documented "magic method" hook, discovered by the runtime via reflection, not by any interface method declaration.

**Inside the custom `readObject`.** `in.defaultReadObject()` is called first — this performs the standard behavior (the same thing that would happen with no custom method at all): it reads `username` and `createdAtMillis` from the byte stream and assigns them to the new `UserSession` object's fields. At this point, `expiresAtMillis` is still at its default, `0`, exactly as in Level 2.

**Recomputing the transient field.** The line `this.expiresAtMillis = this.createdAtMillis + 3600_000` runs immediately after `defaultReadObject()`, using the just-restored `createdAtMillis` to recompute the exact same derived value the original object had — since the formula is deterministic and `createdAtMillis` was preserved, this recomputation produces a value identical to the original `session.expiresAtMillis`.

**Back in `main`.** `session.createdAtMillis == restored.createdAtMillis` compares two `long` primitives by value — both hold the same millisecond timestamp, so this is `true`. `session.expiresAtMillis == restored.expiresAtMillis` similarly compares by value — both now hold `createdAtMillis + 3600_000`, computed independently but identically, so this is also `true`.

```
Original session:  createdAtMillis=T, expiresAtMillis=T+3600000

Serialize: writes username, createdAtMillis (transient expiresAtMillis skipped)

Deserialize (custom readObject):
  1. defaultReadObject() -> username restored, createdAtMillis restored = T
  2. custom code: expiresAtMillis = createdAtMillis + 3600000 = T + 3600000   (recomputed, matches original)
```

**Output:**
```
createdAtMillis matches: true
expiresAtMillis recomputed correctly: true
```

## 7. Gotchas & takeaways

> A `transient` field is not merely "not guaranteed to serialize correctly" — it is **never** written by default serialization, full stop, and always comes back at its type's default value (`null`, `0`, `false`) unless a custom `readObject` method explicitly repopulates it, as shown in Level 3. Assuming a transient field will "usually" retain its value is a bug waiting to surface.

> The `readObject`/`writeObject` custom-hook mechanism relies on Java finding a method with an *exact* private signature (`private void readObject(ObjectInputStream in) throws IOException, ClassNotFoundException`) via reflection — there's no `@Override` or interface to catch a typo in the signature; a slightly wrong signature is silently ignored, and default behavior applies with no warning.

- `transient` excludes a field from Java's default serialization — it's never written, and comes back at its default value on deserialization.
- Use it for sensitive data (tokens, passwords), non-serializable runtime resources (connections, threads), and derivable/cacheable data.
- A custom `private void readObject(ObjectInputStream)` method can repopulate a transient field immediately after `defaultReadObject()` restores the ordinary fields.
- Because the custom-hook signature is checked only by reflection at runtime, a typo in it fails silently rather than producing a compile error — verify behavior with an actual round-trip test.
