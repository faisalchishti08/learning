---
card: java
gi: 248
slug: interface-inheritance-extends
title: Interface inheritance (extends)
---

## 1. What it is

An interface can extend one or more other interfaces using `extends` (not `implements` — that keyword is reserved for classes fulfilling an interface). Unlike classes, which can extend only one other class, an interface can extend *multiple* interfaces at once, inheriting and combining all of their abstract method signatures and constants into one larger contract.

```java
interface Movable {
    void move();
}

interface Resizable {
    void resize();
}

interface Shape extends Movable, Resizable { // interface extending MULTIPLE interfaces at once
    void draw();
}

class Circle implements Shape { // must implement ALL THREE methods: move, resize, draw
    @Override public void move() { System.out.println("Moving"); }
    @Override public void resize() { System.out.println("Resizing"); }
    @Override public void draw() { System.out.println("Drawing"); }
}
```

`Shape extends Movable, Resizable` combines both interfaces' method signatures with its own `draw()` method into one larger contract; any class that `implements Shape` must supply concrete implementations for all three methods — `move`, `resize`, and `draw` — since implementing `Shape` implicitly means implementing everything `Shape` itself extends.

## 2. Why & when

Interface inheritance lets you build larger, more specific contracts out of smaller, more general ones, and — unlike class inheritance — lets an interface combine several unrelated parent contracts at once.

- **Composing narrower interfaces into broader ones** — small, focused interfaces (`Movable`, `Resizable`) can be combined into a richer one (`Shape`) that represents "all of these capabilities together," without forcing every capability into one giant interface from the start.
- **Multiple interface inheritance, something classes cannot do** — since `interface X extends A, B, C` is legal (unlike `class X extends A, B, C`, which is a compile error), interfaces provide a form of multiple inheritance that regular classes cannot achieve on their own.
- **Building interface hierarchies that mirror real relationships** — a more specific interface (say, `AdvancedShape extends Shape`) can add further requirements on top of an already-established, broader contract, letting code depend on exactly the level of specificity it needs.

Use interface inheritance when you have a natural "broader contract built from narrower ones" relationship among your interfaces — reach for it especially when several smaller, focused interfaces (each capturing one capability) are frequently needed together, and bundling them into one combined interface would simplify implementing classes and calling code alike.

## 3. Core concept

```java
interface Named {
    String getName();
}

interface Aged {
    int getAge();
}

interface Person extends Named, Aged { // combines two interfaces into one broader contract
    default String describe() { return getName() + " (" + getAge() + ")"; } // default method, covered soon
}

class Student implements Person {
    String name; int age;
    Student(String name, int age) { this.name = name; this.age = age; }
    @Override public String getName() { return name; }
    @Override public int getAge() { return age; }
}
```

`Person` extends both `Named` and `Aged`, inheriting their abstract methods and adding a `default` method (`describe`, explored in the next few topics) that uses both — `Student` must implement `getName()` and `getAge()` to satisfy `Person`, and automatically gains `describe()` for free, since it has a real body already provided by `Person`.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two narrow interfaces Movable and Resizable are combined via extends into a broader Shape interface which adds its own draw method, an implementing class must satisfy all three method signatures">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">interface Movable</text>

  <rect x="380" y="20" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">interface Resizable</text>

  <line x1="130" y1="50" x2="270" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="470" y1="50" x2="330" y2="90" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="200" y="95" width="200" height="40" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="112" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">interface Shape</text>
  <text x="300" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">extends both, adds draw()</text>

  <line x1="300" y1="135" x2="300" y2="155" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="180" y="160" width="240" height="20" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="174" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">class Circle implements Shape — needs move, resize, draw</text>
</svg>

An interface can `extend` multiple other interfaces at once, combining all their contracts into one broader interface.

## 5. Runnable example

Scenario: a document-processing system where small interfaces are progressively combined into richer ones, evolved from two narrow interfaces into a combined contract, then extended further into an even more specific one.

### Level 1 — Basic

```java
public class InterfaceExtendsBasic {
    interface Readable {
        String read();
    }

    interface Writable {
        void write(String content);
    }

    interface Document extends Readable, Writable { } // combines both, adds nothing new itself

    static class TextFile implements Document {
        String content = "";
        @Override public String read() { return content; }
        @Override public void write(String content) { this.content = content; }
    }

    public static void main(String[] args) {
        Document doc = new TextFile();
        doc.write("Hello, world");
        System.out.println(doc.read());
    }
}
```

**How to run:** `java InterfaceExtendsBasic.java`

`Document extends Readable, Writable` with no additional methods of its own — it exists purely to bundle the two smaller contracts into one name; `TextFile` must implement both `read()` and `write(String)` to satisfy `Document`, and a `Document`-typed reference can call either method.

### Level 2 — Intermediate

Same document system, now with `Document` adding its own method on top of the two it extends, and a second, more specific interface, `VersionedDocument`, extending `Document` further.

```java
public class InterfaceExtendsIntermediate {
    interface Readable { String read(); }
    interface Writable { void write(String content); }

    interface Document extends Readable, Writable {
        default int wordCount() { // default method using the inherited read()
            String content = read();
            return content.isBlank() ? 0 : content.trim().split("\\s+").length;
        }
    }

    interface VersionedDocument extends Document { // extends an interface that itself extends two others
        int getVersion();
    }

    static class TextFile implements VersionedDocument {
        String content = "";
        int version = 1;
        @Override public String read() { return content; }
        @Override public void write(String content) {
            this.content = content;
            version++; // each write bumps the version
        }
        @Override public int getVersion() { return version; }
    }

    public static void main(String[] args) {
        VersionedDocument doc = new TextFile();
        doc.write("The quick brown fox");
        System.out.println("Word count: " + doc.wordCount());   // inherited from Document
        System.out.println("Version: " + doc.getVersion());      // declared directly on VersionedDocument
    }
}
```

**How to run:** `java InterfaceExtendsIntermediate.java`

`VersionedDocument extends Document`, which itself `extends Readable, Writable` — so `TextFile`, by implementing `VersionedDocument`, must ultimately satisfy `read()`, `write(String)`, and `getVersion()`, while getting `wordCount()` for free as an inherited `default` method built on top of `read()`; this chain of extension (interface extending interface extending two more interfaces) composes cleanly into one final, rich contract.

### Level 3 — Advanced

Same document hierarchy, now with a class that only partially satisfies the full chain shown as a compile-time failure (in comments), plus a utility method demonstrating that code can depend on exactly the narrowest interface it actually needs, ignoring the richer ones entirely.

```java
import java.util.List;

public class InterfaceExtendsAdvanced {
    interface Readable { String read(); }
    interface Writable { void write(String content); }
    interface Document extends Readable, Writable {
        default int wordCount() {
            String content = read();
            return content.isBlank() ? 0 : content.trim().split("\\s+").length;
        }
    }
    interface VersionedDocument extends Document {
        int getVersion();
    }

    static class TextFile implements VersionedDocument {
        String content = "";
        int version = 1;
        @Override public String read() { return content; }
        @Override public void write(String content) { this.content = content; version++; }
        @Override public int getVersion() { return version; }
    }

    // The following would NOT compile if uncommented -- missing getVersion() required by VersionedDocument:
    // static class BrokenFile implements VersionedDocument {
    //     public String read() { return ""; }
    //     public void write(String c) { }
    //     // missing getVersion() -> compile error: BrokenFile is not abstract and does not override
    //     // abstract method getVersion() in VersionedDocument
    // }

    // This utility depends on the NARROWEST interface it actually needs -- just Readable
    static void printWordCounts(List<Readable> items) {
        for (Readable r : items) {
            String content = r.read();
            int count = content.isBlank() ? 0 : content.trim().split("\\s+").length;
            System.out.println("Words: " + count);
        }
    }

    public static void main(String[] args) {
        TextFile file = new TextFile();
        file.write("A rich contract built from small pieces");

        // TextFile satisfies Readable, Writable, Document, AND VersionedDocument all at once
        System.out.println(file instanceof Readable);          // true
        System.out.println(file instanceof VersionedDocument); // true

        printWordCounts(List.of(file)); // only needs Readable — TextFile is accepted automatically
    }
}
```

**How to run:** `java InterfaceExtendsAdvanced.java`

`TextFile` satisfies `Readable`, `Writable`, `Document`, and `VersionedDocument` simultaneously, since each interface in the chain builds on the ones before it — `printWordCounts`, which only declares a need for `Readable`, happily accepts `file` without knowing or caring about its richer capabilities, demonstrating that a class implementing a deep interface chain remains usable anywhere any single interface in that chain is expected.

## 6. Walkthrough

Trace `main` in `InterfaceExtendsAdvanced` from construction through the final call.

**`TextFile file = new TextFile()`.** A new `TextFile` is created with `content = ""` and `version = 1`.

**`file.write("A rich contract built from small pieces")`.** Dispatches to `TextFile.write`, setting `content` to the given string and incrementing `version` to `2`.

**`file instanceof Readable`.** `TextFile implements VersionedDocument`, which `extends Document`, which `extends Readable, Writable` — so `TextFile` transitively satisfies `Readable` through this whole chain. The check is `true`.

**`file instanceof VersionedDocument`.** `TextFile` directly declares `implements VersionedDocument`. The check is `true`.

**`printWordCounts(List.of(file))`.** `List.of(file)` produces a `List<TextFile>`, which is assignable to the parameter type `List<Readable>` since `TextFile` is-a `Readable` (through the interface chain). Inside `printWordCounts`, the loop calls `r.read()` — dispatching to `TextFile.read()`, returning `"A rich contract built from small pieces"`. `content.isBlank()` is `false`, so `content.trim().split("\\s+")` splits on whitespace: `["A", "rich", "contract", "built", "from", "small", "pieces"]`, a 7-element array, so `count` is `7`. Prints `"Words: 7"`.

```
new TextFile() -> content="", version=1
file.write("A rich contract built from small pieces") -> content set, version=2

file instanceof Readable          -> true (via VersionedDocument -> Document -> Readable, Writable)
file instanceof VersionedDocument -> true (declared directly)

printWordCounts([file]):
  r.read() -> "A rich contract built from small pieces"
  split on whitespace -> 7 words
  prints "Words: 7"
```

**Final output.**
```
true
true
Words: 7
```

## 7. Gotchas & takeaways

> **An interface uses `extends` (never `implements`) to inherit from other interfaces, and — unlike a class — can extend multiple interfaces at once**, separated by commas: `interface Shape extends Movable, Resizable { }`. This is legal specifically because interfaces only ever declare contracts (in the classic model), so there is no risk of the "diamond problem" ambiguity that blocks multiple class inheritance.

> **Implementing the most specific interface in a chain (like `VersionedDocument`) requires satisfying every abstract method declared anywhere in that chain**, not just the ones declared directly on it — forgetting even one inherited abstract method (as the commented-out `BrokenFile` demonstrates) is caught at compile time, listing exactly which interface and method are missing.

- Interfaces use `extends` to inherit from other interfaces, and can extend multiple interfaces simultaneously, unlike classes.
- A class implementing the most specific interface in a chain must supply implementations for every abstract method across the entire chain.
- Building broader interfaces out of narrower ones (`Shape extends Movable, Resizable`) lets you compose rich contracts from small, focused pieces.
- Code can depend on the narrowest interface it actually needs; a class implementing a deep interface chain remains usable wherever any interface in that chain is expected.
