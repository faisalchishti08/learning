---
card: java
gi: 308
slug: serialization-serializable
title: Serialization (Serializable)
---

## 1. What it is

Serialization is the process of converting a Java object's in-memory state into a byte stream (for storage or transmission), and deserialization reverses it, reconstructing an equivalent object from those bytes. A class opts into this by implementing the `Serializable` marker interface, which declares **no methods at all** — it simply signals to the JVM "objects of this class may be serialized."

```java
import java.io.*;

public class SerializableDemo {
    public static void main(String[] args) throws Exception {
        Point p = new Point(3, 4);

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(p);

        ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(baos.toByteArray()));
        Point restored = (Point) in.readObject();
        System.out.println(restored);
    }
}

class Point implements Serializable {
    int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }
    public String toString() { return "Point(" + x + ", " + y + ")"; }
}
```

`Point implements Serializable` is what makes `writeObject(p)` legal; without it, `writeObject` throws `NotSerializableException` at runtime — the marker interface is purely a compile-time-invisible, runtime-checked flag.

## 2. Why & when

Objects live in memory as a graph of references, which is meaningless outside the running JVM. Serialization exists to give that in-memory state a portable, storable, transmittable representation: writing an object to a file, sending it over a network connection, or caching it, then reconstructing an equivalent object later, possibly in a different JVM instance or even a different run of the program entirely.

- **Persisting object state** — saving application state (game saves, cached computations) to disk between runs.
- **Passing objects across a network** — historically used by Java RMI (Remote Method Invocation) to pass objects between JVMs.
- **Deep-copying an object graph** — serializing then immediately deserializing an object produces an independent copy, including nested objects, without manually writing copy logic (a somewhat unconventional but real use).

`Serializable` is a marker interface — implementing it is necessary but declares no behavior itself; the actual serialization logic lives in `ObjectOutputStream`/`ObjectInputStream` (covered separately), which use reflection to walk an object's fields automatically. Modern systems often prefer more portable, language-agnostic formats (JSON, Protocol Buffers) for data that crosses process or language boundaries, reserving Java serialization for same-JVM-family scenarios like distributed caches.

## 3. Core concept

```java
import java.io.*;

public class SerializableCore {
    public static void main(String[] args) throws Exception {
        Person p = new Person("Alice", new Address("Paris"));

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(p);

        Person restored = (Person) new ObjectInputStream(new ByteArrayInputStream(baos.toByteArray())).readObject();
        System.out.println(restored.name + " lives in " + restored.address.city);
    }
}

class Address implements Serializable {
    String city;
    Address(String city) { this.city = city; }
}

class Person implements Serializable {
    String name;
    Address address; // must ALSO be Serializable, or serialization fails
    Person(String name, Address address) { this.name = name; this.address = address; }
}
```

Serialization is transitive: because `Person` holds a reference to an `Address` object, that `Address` must **also** implement `Serializable` (which it does here), or the entire operation fails — every reachable object in the graph being serialized must itself be serializable.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An in-memory object graph is converted to a linear byte stream and back into an equivalent but distinct object graph">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="35" width="130" height="70" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="85" y="60" fill="#e6edf3" font-size="10" text-anchor="middle">Person object</text>
  <text x="85" y="78" fill="#8b949e" font-size="8" text-anchor="middle">(in memory, JVM #1)</text>
  <text x="85" y="92" fill="#8b949e" font-size="8" text-anchor="middle">-&gt; Address object</text>

  <line x1="152" y1="70" x2="240" y2="70" stroke="#79c0ff" stroke-width="2" marker-end="url(#s1)"/>
  <text x="196" y="60" fill="#79c0ff" font-size="9" text-anchor="middle">writeObject</text>
  <rect x="245" y="55" width="150" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="75" fill="#e6edf3" font-size="9" text-anchor="middle">byte[] (linear)</text>

  <line x1="397" y1="70" x2="450" y2="70" stroke="#3fb950" stroke-width="2" marker-end="url(#s2)"/>
  <text x="425" y="60" fill="#3fb950" font-size="9" text-anchor="middle">readObject</text>
  <rect x="455" y="35" width="130" height="70" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="520" y="60" fill="#e6edf3" font-size="10" text-anchor="middle">New Person object</text>
  <text x="520" y="78" fill="#8b949e" font-size="8" text-anchor="middle">(equivalent, distinct)</text>
  <text x="520" y="92" fill="#8b949e" font-size="8" text-anchor="middle">-&gt; new Address object</text>
  <defs>
    <marker id="s1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="s2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

The reconstructed object graph is equal in content but a completely distinct set of objects from the original.

## 5. Runnable example

Scenario: saving and restoring a small shopping cart's state, evolved from a basic single-object round-trip into a nested object graph, then into using serialization for a deep-copy utility, revealing that the restored objects are distinct from the originals.

### Level 1 — Basic

```java
import java.io.*;

public class SerializableBasic {
    public static void main(String[] args) throws Exception {
        CartItem item = new CartItem("Widget", 3);

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(item);

        CartItem restored = (CartItem) new ObjectInputStream(new ByteArrayInputStream(baos.toByteArray())).readObject();
        System.out.println("Restored: " + restored);
    }
}

class CartItem implements Serializable {
    String name;
    int quantity;
    CartItem(String name, int quantity) { this.name = name; this.quantity = quantity; }
    public String toString() { return quantity + "x " + name; }
}
```

**How to run:** `java SerializableBasic.java`

A single serializable object round-trips through a byte array — the simplest possible demonstration of the mechanism.

### Level 2 — Intermediate

Same cart, now holding a `List` of multiple `CartItem`s (a whole object graph, not just one object), demonstrating that standard collections are themselves serializable and carry their contents along.

```java
import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class SerializableIntermediate {
    public static void main(String[] args) throws Exception {
        List<CartItem> cart = new ArrayList<>();
        cart.add(new CartItem("Widget", 3));
        cart.add(new CartItem("Gadget", 1));

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject(cart);

        @SuppressWarnings("unchecked")
        List<CartItem> restored = (List<CartItem>) new ObjectInputStream(
            new ByteArrayInputStream(baos.toByteArray())).readObject();

        restored.forEach(System.out::println);
    }
}

class CartItem implements Serializable {
    String name;
    int quantity;
    CartItem(String name, int quantity) { this.name = name; this.quantity = quantity; }
    public String toString() { return quantity + "x " + name; }
}
```

**How to run:** `java SerializableIntermediate.java`

`ArrayList` (like most standard collection classes) implements `Serializable` itself, and it serializes its elements in turn — as long as every element (`CartItem`, here) is also serializable, the whole list round-trips correctly with a single `writeObject`/`readObject` call.

### Level 3 — Advanced

Same cart, now used specifically as a deep-copy utility: serializing an object graph and immediately deserializing it produces an independent copy where mutating the copy does not affect the original — demonstrated and verified explicitly.

```java
import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class SerializableAdvanced {
    @SuppressWarnings("unchecked")
    static <T> T deepCopy(T original) throws IOException, ClassNotFoundException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        new ObjectOutputStream(baos).writeObject((Serializable) original);
        return (T) new ObjectInputStream(new ByteArrayInputStream(baos.toByteArray())).readObject();
    }

    public static void main(String[] args) throws Exception {
        List<CartItem> original = new ArrayList<>();
        original.add(new CartItem("Widget", 3));

        List<CartItem> copy = deepCopy(original);
        copy.get(0).quantity = 99; // mutate the COPY

        System.out.println("Original: " + original.get(0));
        System.out.println("Copy: " + copy.get(0));
        System.out.println("Same object reference? " + (original.get(0) == copy.get(0)));
    }
}

class CartItem implements Serializable {
    String name;
    int quantity;
    CartItem(String name, int quantity) { this.name = name; this.quantity = quantity; }
    public String toString() { return quantity + "x " + name; }
}
```

**How to run:** `java SerializableAdvanced.java`

`deepCopy` writes the entire object graph to an in-memory byte array and immediately reads it back — because deserialization always constructs **brand-new** objects (never returning a reference to anything already in memory), the resulting `copy` shares no object identity with `original`, even though their field values are identical immediately after the copy.

## 6. Walkthrough

Trace `SerializableAdvanced.main` step by step.

**Setup.** `original` is a `List<CartItem>` containing one `CartItem("Widget", 3)`.

**`deepCopy(original)` is called.** Inside, `new ObjectOutputStream(baos).writeObject(original)` walks the object graph starting from `original`: it serializes the `ArrayList`'s internal structure, then serializes the one `CartItem` it contains, capturing `name = "Widget"` and `quantity = 3` as bytes. `baos.toByteArray()` yields this byte representation.

**Deserialization.** `new ObjectInputStream(...).readObject()` reads those bytes and reconstructs the object graph from scratch: a **new** `ArrayList` instance is created, and a **new** `CartItem` instance is created and populated with `name = "Widget"`, `quantity = 3` — critically, this new `CartItem` is a distinct object in memory from the original one, even though its field values currently match.

**Mutating the copy.** `copy.get(0).quantity = 99` changes the `quantity` field of the *new* `CartItem` object inside `copy`. Since `original`'s `CartItem` is an entirely separate object, this assignment has no effect on it whatsoever.

**Verification prints.** `original.get(0)` still shows `quantity = 3`, printed as `"3x Widget"`. `copy.get(0)` shows the mutated `quantity = 99`, printed as `"99x Widget"`. `original.get(0) == copy.get(0)` compares object references (not content) — since these are genuinely two different objects in memory, this is `false`.

```
original: ArrayList -> CartItem{name="Widget", quantity=3}
                |
                v  writeObject (serialize the whole graph to bytes)
              bytes
                |
                v  readObject (deserialize: construct BRAND NEW objects)
copy:     NEW ArrayList -> NEW CartItem{name="Widget", quantity=3}

copy.get(0).quantity = 99   -- only affects the NEW CartItem object

original.get(0) == copy.get(0)  -> false (different objects entirely)
```

**Output:**
```
Original: 3x Widget
Copy: 99x Widget
Same object reference? false
```

## 7. Gotchas & takeaways

> Every object reachable from the one being serialized must itself implement `Serializable` (or be `null`), including objects held in fields, and objects held inside those objects, and so on, transitively. A single non-serializable field anywhere in the reachable graph causes `NotSerializableException` at the point that specific object is encountered — often confusingly deep in a large object graph.

> Deserialization always constructs entirely new objects — `readObject()` never returns a reference to something already in memory, even within the same JVM run that performed the `writeObject` call. This is precisely why serialize-then-deserialize is a legitimate (if somewhat heavyweight) technique for deep-copying an object graph.

- `Serializable` is a marker interface (no methods) that opts a class into Java's built-in object serialization mechanism.
- Serialization is transitive: every reachable, non-transient, non-static field's object must also be serializable.
- Deserialization always produces new object instances, never references to pre-existing ones — useful for deep copies, but also means serialized identity (`==`) is never preserved across the round-trip.
- Standard collection classes (`ArrayList`, `HashMap`, etc.) are serializable and automatically serialize their contents, provided those contents are themselves serializable.
