---
card: java
gi: 310
slug: objectoutputstream-objectinputstream
title: ObjectOutputStream / ObjectInputStream
---

## 1. What it is

`ObjectOutputStream` and `ObjectInputStream` are the classes that actually **perform** Java serialization and deserialization — wrapping another byte stream, they add `writeObject(Object)` and `readObject()`, which use reflection to walk a `Serializable` object's fields and convert them to/from bytes automatically, without you writing any field-by-field encoding logic.

```java
import java.io.*;

public class ObjectStreamDemo {
    public static void main(String[] args) throws Exception {
        try (ObjectOutputStream out = new ObjectOutputStream(new FileOutputStream("book.ser"))) {
            out.writeObject(new Book("Effective Java", 412));
        }

        try (ObjectInputStream in = new ObjectInputStream(new FileInputStream("book.ser"))) {
            Book book = (Book) in.readObject();
            System.out.println(book.title + ", " + book.pages + " pages");
        }
    }
}

class Book implements Serializable {
    String title;
    int pages;
    Book(String title, int pages) { this.title = title; this.pages = pages; }
}
```

`writeObject` handles the entire object automatically via reflection — no `writeInt`/`writeUTF` calls for each field are needed, unlike the manual, per-field approach `DataOutputStream` requires; `readObject` returns `Object`, so a cast to the expected type (`(Book)`) is always necessary.

## 2. Why & when

`DataOutputStream` requires manually writing each field in a chosen order; `ObjectOutputStream` automates this entirely for any `Serializable` class, including deeply nested object graphs, using reflection to discover and encode every field without you specifying them one by one.

- **Zero boilerplate for arbitrary object graphs** — one `writeObject` call serializes an entire object, including nested objects, collections, and arrays, with no per-field code required.
- **Type and structure preserved automatically** — the serialized form records enough information (class name, field layout) that `readObject` can reconstruct an object of the correct type without you specifying field order or count.
- **Multiple objects, one stream** — a single `ObjectOutputStream` can serialize multiple objects in sequence via repeated `writeObject` calls; `readObject` is called the same number of times, in the same order, to read them back.

Use `ObjectOutputStream`/`ObjectInputStream` for same-JVM-family persistence or transmission of moderately complex object graphs where full automation outweighs the format's Java-specific, non-portable, and moderately verbose binary representation. For cross-language interoperability or long-term storage where forward/backward compatibility matters, JSON, Protocol Buffers, or similar schema-based formats are usually a better fit.

## 3. Core concept

```java
import java.io.*;

public class ObjectStreamCore {
    public static void main(String[] args) throws Exception {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(baos)) {
            out.writeObject(new Note("first"));
            out.writeObject(new Note("second"));
            out.writeObject(new Note("third"));
        }

        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(baos.toByteArray()))) {
            for (int i = 0; i < 3; i++) {
                Note note = (Note) in.readObject();
                System.out.println(note.text);
            }
        }
    }
}

class Note implements Serializable {
    String text;
    Note(String text) { this.text = text; }
}
```

Multiple `writeObject` calls on the same stream produce a sequence of serialized objects, one after another, read back with the same number of `readObject` calls in the same order — analogous to how `DataOutputStream`'s multiple `writeInt`/`writeUTF` calls must be read back in matching order, just operating on whole objects instead of primitives.

## 4. Diagram

<svg viewBox="0 0 600 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple writeObject calls append serialized objects to a stream in order, matched by the same number of readObject calls">
  <rect x="8" y="8" width="584" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="35" width="160" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="100" y="60" fill="#e6edf3" font-size="9" text-anchor="middle">writeObject(a) writeObject(b) writeObject(c)</text>
  <line x1="180" y1="55" x2="240" y2="55" stroke="#79c0ff" stroke-width="2" marker-end="url(#o1)"/>
  <rect x="245" y="35" width="120" height="40" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="305" y="60" fill="#e6edf3" font-size="9" text-anchor="middle">bytes: a | b | c</text>
  <line x1="365" y1="55" x2="425" y2="55" stroke="#3fb950" stroke-width="2" marker-end="url(#o2)"/>
  <rect x="430" y="35" width="150" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="505" y="60" fill="#e6edf3" font-size="9" text-anchor="middle">readObject x3 -&gt; a,b,c</text>
  <defs>
    <marker id="o1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="o2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Objects are serialized and deserialized in strict call order — there is no random access into the middle of an object stream.

## 5. Runnable example

Scenario: a small "save game" system, evolved from a single-object save/load into saving a list of game entities, then into a version that reads back an unknown number of saved objects using `EOFException` to detect the end, mirroring the pattern used for `DataInputStream`.

### Level 1 — Basic

```java
import java.io.*;

public class ObjectStreamBasic {
    public static void main(String[] args) throws Exception {
        PlayerState player = new PlayerState("Hero", 5, 80);

        try (ObjectOutputStream out = new ObjectOutputStream(new FileOutputStream("save.dat"))) {
            out.writeObject(player);
        }

        try (ObjectInputStream in = new ObjectInputStream(new FileInputStream("save.dat"))) {
            PlayerState loaded = (PlayerState) in.readObject();
            System.out.println(loaded.name + ", level " + loaded.level + ", HP " + loaded.hp);
        }
    }
}

class PlayerState implements Serializable {
    String name;
    int level;
    int hp;
    PlayerState(String name, int level, int hp) { this.name = name; this.level = level; this.hp = hp; }
}
```

**How to run:** `java ObjectStreamBasic.java`

Saves and reloads a single game-state object, the most basic form of save/load persistence.

### Level 2 — Intermediate

Same save system, now persisting a `List` of multiple entities (the player plus several enemies) as one serialized object graph via a single `writeObject`/`readObject` pair.

```java
import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class ObjectStreamIntermediate {
    public static void main(String[] args) throws Exception {
        List<Entity> entities = new ArrayList<>();
        entities.add(new Entity("Hero", 80));
        entities.add(new Entity("Goblin", 20));
        entities.add(new Entity("Dragon", 500));

        try (ObjectOutputStream out = new ObjectOutputStream(new FileOutputStream("save2.dat"))) {
            out.writeObject(entities); // the whole list, in one call
        }

        @SuppressWarnings("unchecked")
        List<Entity> loaded;
        try (ObjectInputStream in = new ObjectInputStream(new FileInputStream("save2.dat"))) {
            loaded = (List<Entity>) in.readObject();
        }

        loaded.forEach(System.out::println);
    }
}

class Entity implements Serializable {
    String name;
    int hp;
    Entity(String name, int hp) { this.name = name; this.hp = hp; }
    public String toString() { return name + " (HP " + hp + ")"; }
}
```

**How to run:** `java ObjectStreamIntermediate.java`

One `writeObject(entities)` call serializes the entire `ArrayList` and all three `Entity` objects it contains; one `readObject()` call reconstructs the equivalent list — no manual iteration needed on either side.

### Level 3 — Advanced

Same save system, now writing each entity as a **separate** serialized object in the stream (rather than one list), and reading them back one at a time until `EOFException` signals no more remain — useful when the total count isn't known or stored up front, or when entities are appended incrementally over time.

```java
import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class ObjectStreamAdvanced {
    public static void main(String[] args) throws Exception {
        Entity[] entities = {
            new Entity("Hero", 80), new Entity("Goblin", 20), new Entity("Dragon", 500)
        };

        try (ObjectOutputStream out = new ObjectOutputStream(new FileOutputStream("save3.dat"))) {
            for (Entity e : entities) {
                out.writeObject(e); // each entity is its OWN top-level object in the stream
            }
        }

        List<Entity> loaded = new ArrayList<>();
        try (ObjectInputStream in = new ObjectInputStream(new FileInputStream("save3.dat"))) {
            while (true) {
                try {
                    loaded.add((Entity) in.readObject());
                } catch (EOFException e) {
                    break; // no more objects in the stream
                }
            }
        }

        System.out.println("Loaded " + loaded.size() + " entities:");
        loaded.forEach(System.out::println);
    }
}

class Entity implements Serializable {
    String name;
    int hp;
    Entity(String name, int hp) { this.name = name; this.hp = hp; }
    public String toString() { return name + " (HP " + hp + ")"; }
}
```

**How to run:** `java ObjectStreamAdvanced.java`

Writing each `Entity` as its own `writeObject` call (rather than one list containing all three) means the stream doesn't know or store a total count — reading proceeds in an unbounded loop, exactly mirroring the `DataInputStream`/`EOFException` pattern used for unknown-count binary records, just operating on whole objects instead of primitives.

## 6. Walkthrough

Trace the reading loop in `ObjectStreamAdvanced.main` step by step.

**File contents.** `save3.dat` contains three independently-serialized `Entity` objects back to back, with no overall count or wrapping list structure stored anywhere.

**First loop iteration.** `in.readObject()` reads the first serialized object's bytes, reconstructs an `Entity` with `name="Hero"`, `hp=80`, and returns it (as `Object`, cast to `Entity`). `loaded.add(...)` appends it. No exception, loop continues.

**Second and third iterations.** Identically reconstruct and add `Entity("Goblin", 20)` and `Entity("Dragon", 500)`.

**Fourth iteration attempt.** `in.readObject()` is called again, but the stream has no more object data — internally, `ObjectInputStream` detects it has reached the true end of the underlying byte stream while expecting to read further object header bytes, and throws `EOFException`. The `catch (EOFException e) { break; }` clause catches it, ending the loop.

**After the loop.** `loaded` contains exactly the three `Entity` objects, in the order they were written. `loaded.size()` confirms `3`, and `forEach` prints each one via its `toString()`.

```
save3.dat: [Entity "Hero"/80] [Entity "Goblin"/20] [Entity "Dragon"/500]   (no count stored)

Read loop:
  iter 1: readObject -> Hero/80     -> added
  iter 2: readObject -> Goblin/20   -> added
  iter 3: readObject -> Dragon/500  -> added
  iter 4: readObject -> EOFException -> break
```

**Output:**
```
Loaded 3 entities:
Hero (HP 80)
Goblin (HP 20)
Dragon (HP 500)
```

## 7. Gotchas & takeaways

> `readObject()` returns `Object` and always requires an explicit cast to the actual expected type — an incorrect cast (e.g. casting to the wrong class) throws `ClassCastException` at runtime, not a compile-time error, since the compiler has no way to know what type was actually serialized into the stream.

> Reading more objects than were written (or reading in the wrong order when multiple different types were interleaved) causes `EOFException` or `ClassCastException` respectively — the stream carries no structural metadata beyond each individual object's own type information; you must track how many objects (and of what types, in what order) you wrote if you intend to read them back deterministically.

- `ObjectOutputStream`/`ObjectInputStream` automate full object-graph serialization via reflection, with no manual per-field encoding needed.
- Multiple `writeObject` calls append a sequence of independent serialized objects; matching `readObject` calls, in the same order, read them back.
- `readObject()` always returns `Object`, requiring an explicit cast — an incorrect cast fails at runtime with `ClassCastException`.
- `EOFException` from `readObject()` is a reliable, expected signal for "no more objects in the stream" when the count wasn't recorded separately.
