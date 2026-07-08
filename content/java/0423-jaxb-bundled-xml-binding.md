---
card: java
gi: 423
slug: jaxb-bundled-xml-binding
title: JAXB bundled (XML binding)
---

## 1. What it is

JAXB (Java Architecture for XML Binding) is a framework for automatically converting Java objects to XML (**marshalling**) and XML back into Java objects (**unmarshalling**), driven by annotations like `@XmlRootElement` and `@XmlElement` rather than hand-written parsing code. Starting with Java 6, JAXB was **bundled directly with the JDK** — no separate dependency needed — making annotation-driven XML binding a standard, always-available part of the platform for the first time.

## 2. Why & when

Before JAXB, converting a Java object to XML (or parsing XML back into an object) meant writing that conversion logic by hand, field by field, using a lower-level XML API like DOM or SAX — tedious, repetitive, and easy to get subtly wrong (missed escaping, inconsistent structure). JAXB automated this: annotate a class once with `@XmlRootElement`, `@XmlElement`, etc., and a `Marshaller`/`Unmarshaller` handles the conversion generically via reflection, for any annotated class, with no per-class parsing code required. Bundling it with the JDK (Java 6 through 8) meant every Java application had this capability for free, which made it the default choice for XML-based configuration files, SOAP web service payloads (JAX-WS, covered next, uses JAXB internally), and data interchange formats.

**Important, and worth knowing if you're working on a modern JDK:** JAXB was removed from the JDK's default set of modules starting in Java 11 (it was deprecated for removal in Java 9's modularization, then dropped). On Java 11+, using JAXB requires adding an external dependency (`jakarta.xml.bind:jakarta.xml.bind-api` plus a runtime implementation like `org.glassfish.jaxb:jaxb-runtime`) — it is no longer bundled. Since this tutorial series targets code that runs standalone on modern JDKs, the runnable examples below build a small **hand-written stand-in** using reflection and StAX (itself still bundled) to demonstrate the same core idea JAXB automated — annotation/convention-driven object-to-XML binding — while staying honest that real JAXB requires that external dependency today.

## 3. Core concept

```java
// What real JAXB looked like when it was bundled (Java 6-8) -- shown for reference, not runnable as-is on 11+:
//
// @XmlRootElement
// class Person {
//     @XmlElement String name;
//     @XmlElement int age;
// }
//
// JAXBContext context = JAXBContext.newInstance(Person.class);
// Marshaller marshaller = context.createMarshaller();
// marshaller.marshal(new Person(), System.out);            // Java object -> XML
// Person p = (Person) context.createUnmarshaller()
//     .unmarshal(new File("person.xml"));                  // XML -> Java object
```

The runnable examples below replicate this idea generically using reflection to discover a class's fields (playing the role JAXB's annotations would) and `javax.xml.stream` (StAX, still bundled — see the next tutorial) to actually read and write the XML.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Marshalling walks an object's fields via reflection to produce XML; unmarshalling walks XML elements to populate an object's fields, the two directions of the same binding">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="120" y="55" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Java object (fields)</text>
  <rect x="430" y="30" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="520" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">XML document</text>

  <line x1="210" y1="42" x2="425" y2="42" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ak1)"/>
  <text x="320" y="34" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">marshal (reflection -&gt; StAX writer)</text>

  <line x1="425" y1="60" x2="210" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ak2)"/>
  <text x="320" y="75" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">unmarshal (StAX reader -&gt; reflection)</text>

  <text x="320" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Both directions are driven by the SAME field-naming convention, kept consistently in sync.</text>
  <defs><marker id="ak1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker><marker id="ak2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

Marshalling and unmarshalling are mirror-image operations driven by the same field-to-element convention.

## 5. Runnable example

Scenario: converting a `Person` object to XML and back — the same binding logic, evolved from one-way marshalling (object to XML), through a full round trip (XML back to a new object), to handling a nested object (`Person` containing an `Address`), which is where real binding frameworks earn their keep.

### Level 1 — Basic

```java
import javax.xml.stream.*;
import java.io.StringWriter;
import java.lang.reflect.Field;

public class MiniJaxbMarshalBasic {
    static class Person {
        String name;
        int age;
        Person(String name, int age) { this.name = name; this.age = age; }
    }

    static String marshal(Object obj) throws Exception {
        StringWriter sw = new StringWriter();
        XMLStreamWriter writer = XMLOutputFactory.newInstance().createXMLStreamWriter(sw);
        writer.writeStartDocument();
        writer.writeStartElement(obj.getClass().getSimpleName()); // root element = class name
        for (Field field : obj.getClass().getDeclaredFields()) {
            field.setAccessible(true);
            writer.writeStartElement(field.getName()); // one child element per field
            writer.writeCharacters(String.valueOf(field.get(obj)));
            writer.writeEndElement();
        }
        writer.writeEndElement();
        writer.writeEndDocument();
        writer.close();
        return sw.toString();
    }

    public static void main(String[] args) throws Exception {
        Person person = new Person("Alice", 30);
        System.out.println(marshal(person));
    }
}
```

**How to run:** `java MiniJaxbMarshalBasic.java`

`marshal` uses reflection (`getDeclaredFields()`) to discover `Person`'s fields generically — no `Person`-specific code was written to produce the XML, exactly the point of an annotation/convention-driven binding framework: one generic marshaller handles any class shaped this way.

### Level 2 — Intermediate

```java
import javax.xml.stream.*;
import java.io.StringWriter;
import java.io.StringReader;
import java.lang.reflect.Field;

public class MiniJaxbRoundTrip {
    static class Person {
        String name;
        int age;
        Person() {}
        Person(String name, int age) { this.name = name; this.age = age; }
        public String toString() { return "Person{name=" + name + ", age=" + age + "}"; }
    }

    static String marshal(Object obj) throws Exception {
        StringWriter sw = new StringWriter();
        XMLStreamWriter writer = XMLOutputFactory.newInstance().createXMLStreamWriter(sw);
        writer.writeStartDocument();
        writer.writeStartElement(obj.getClass().getSimpleName());
        for (Field field : obj.getClass().getDeclaredFields()) {
            field.setAccessible(true);
            writer.writeStartElement(field.getName());
            writer.writeCharacters(String.valueOf(field.get(obj)));
            writer.writeEndElement();
        }
        writer.writeEndElement();
        writer.writeEndDocument();
        writer.close();
        return sw.toString();
    }

    static <T> T unmarshal(String xml, Class<T> type) throws Exception {
        T instance = type.getDeclaredConstructor().newInstance();
        XMLStreamReader reader = XMLInputFactory.newInstance().createXMLStreamReader(new StringReader(xml));
        String currentField = null;
        while (reader.hasNext()) {
            int event = reader.next();
            if (event == XMLStreamConstants.START_ELEMENT) {
                String elementName = reader.getLocalName();
                if (!elementName.equals(type.getSimpleName())) {
                    currentField = elementName; // remember which field's text comes next
                }
            } else if (event == XMLStreamConstants.CHARACTERS && currentField != null) {
                String text = reader.getText().trim();
                if (!text.isEmpty()) {
                    Field field = type.getDeclaredField(currentField);
                    field.setAccessible(true);
                    if (field.getType() == int.class) {
                        field.set(instance, Integer.parseInt(text));
                    } else {
                        field.set(instance, text);
                    }
                }
            } else if (event == XMLStreamConstants.END_ELEMENT) {
                currentField = null;
            }
        }
        reader.close();
        return instance;
    }

    public static void main(String[] args) throws Exception {
        Person original = new Person("Alice", 30);
        String xml = marshal(original);
        System.out.println("Marshalled: " + xml);

        Person roundTripped = unmarshal(xml, Person.class);
        System.out.println("Unmarshalled: " + roundTripped);
    }
}
```

**How to run:** `java MiniJaxbRoundTrip.java`

`unmarshal` walks the XML via a StAX `XMLStreamReader`, tracking which field name the current text content belongs to, and uses reflection to set that field on a freshly-constructed instance — completing the round trip. Note the type-aware conversion: `int` fields are parsed with `Integer.parseInt`, while `String` fields are assigned directly.

### Level 3 — Advanced

```java
import javax.xml.stream.*;
import java.io.StringWriter;
import java.io.StringReader;
import java.lang.reflect.Field;
import java.util.*;

public class MiniJaxbNested {
    static class Address {
        String city;
        String zip;
        Address() {}
        Address(String city, String zip) { this.city = city; this.zip = zip; }
        public String toString() { return "Address{city=" + city + ", zip=" + zip + "}"; }
    }

    static class Person {
        String name;
        Address address;
        Person() {}
        Person(String name, Address address) { this.name = name; this.address = address; }
        public String toString() { return "Person{name=" + name + ", address=" + address + "}"; }
    }

    static boolean isSimple(Class<?> type) {
        return type == String.class || type == int.class || type == Integer.class;
    }

    static void marshalObject(XMLStreamWriter writer, Object obj) throws Exception {
        for (Field field : obj.getClass().getDeclaredFields()) {
            field.setAccessible(true);
            Object value = field.get(obj);
            writer.writeStartElement(field.getName());
            if (isSimple(field.getType()) || value == null) {
                writer.writeCharacters(String.valueOf(value));
            } else {
                marshalObject(writer, value); // recurse into the nested object's own fields
            }
            writer.writeEndElement();
        }
    }

    static String marshal(Object obj) throws Exception {
        StringWriter sw = new StringWriter();
        XMLStreamWriter writer = XMLOutputFactory.newInstance().createXMLStreamWriter(sw);
        writer.writeStartDocument();
        writer.writeStartElement(obj.getClass().getSimpleName());
        marshalObject(writer, obj);
        writer.writeEndElement();
        writer.writeEndDocument();
        writer.close();
        return sw.toString();
    }

    // Unmarshal using a stack of "current object" so nested elements populate the right instance
    static Object unmarshalObject(XMLStreamReader reader, Class<?> type) throws Exception {
        Object instance = type.getDeclaredConstructor().newInstance();
        Deque<Object> stack = new ArrayDeque<>();
        Deque<String> fieldStack = new ArrayDeque<>();
        stack.push(instance);

        String currentField = null;
        while (reader.hasNext()) {
            int event = reader.next();
            if (event == XMLStreamConstants.START_ELEMENT) {
                String elementName = reader.getLocalName();
                Object top = stack.peek();
                Field field = findField(top.getClass(), elementName);
                if (field == null) continue; // the outer root element itself
                if (isSimple(field.getType())) {
                    currentField = elementName;
                } else {
                    Object nested = field.getType().getDeclaredConstructor().newInstance();
                    field.setAccessible(true);
                    field.set(top, nested);
                    stack.push(nested);
                    fieldStack.push(elementName);
                    currentField = null;
                }
            } else if (event == XMLStreamConstants.CHARACTERS && currentField != null) {
                String text = reader.getText().trim();
                if (!text.isEmpty()) {
                    Field field = findField(stack.peek().getClass(), currentField);
                    field.setAccessible(true);
                    field.set(stack.peek(), text);
                }
            } else if (event == XMLStreamConstants.END_ELEMENT) {
                if (!fieldStack.isEmpty() && reader.getLocalName().equals(fieldStack.peek())) {
                    stack.pop();
                    fieldStack.pop();
                }
                currentField = null;
            }
        }
        return instance;
    }

    static Field findField(Class<?> type, String name) {
        try { return type.getDeclaredField(name); } catch (NoSuchFieldException e) { return null; }
    }

    static <T> T unmarshal(String xml, Class<T> type) throws Exception {
        XMLStreamReader reader = XMLInputFactory.newInstance().createXMLStreamReader(new StringReader(xml));
        Object result = unmarshalObject(reader, type);
        reader.close();
        return type.cast(result);
    }

    public static void main(String[] args) throws Exception {
        Person original = new Person("Alice", new Address("Springfield", "12345"));
        String xml = marshal(original);
        System.out.println("Marshalled: " + xml);

        Person roundTripped = unmarshal(xml, Person.class);
        System.out.println("Unmarshalled: " + roundTripped);
    }
}
```

**How to run:** `java MiniJaxbNested.java`

`marshalObject` now **recurses** whenever a field's type isn't a simple value (`Address` is not `String`/`int`), writing a nested element structure. `unmarshalObject` mirrors this with a stack: entering a nested element pushes a freshly-created instance of that field's type (and remembers which element name will close it), so subsequent simple fields populate the *correct* current object, and popping the stack on the matching end-element returns focus to the parent.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `original` is a `Person` named `"Alice"` with an `Address("Springfield", "12345")`.

**Marshalling:** `marshal(original)` opens a document and writes a root `<Person>` element, then calls `marshalObject(writer, original)`. This iterates `Person`'s fields: `name` (a `String`, "simple") is written directly as `<name>Alice</name>`. `address` is **not** simple (its type is `Address`), so instead of writing text, `marshalObject` recurses: it opens `<address>`, then iterates *`Address`'s* fields — `city` and `zip`, both simple — writing `<city>Springfield</city>` and `<zip>12345</zip>`, before closing `</address>`. The result is a properly nested XML document.

**Unmarshalling:** `unmarshal(xml, Person.class)` creates an empty `Person` and pushes it onto `stack`. The reader processes events in order. `START_ELEMENT` `"Person"` is the root — `findField(Person.class, "Person")` returns `null` (no such field), so it's skipped. `START_ELEMENT` `"name"` — `findField` finds `Person.name`, whose type (`String`) is simple, so `currentField = "name"`. The next `CHARACTERS` event yields `"Alice"`, which is set directly onto the top-of-stack `Person` via reflection.

`END_ELEMENT` `"name"` clears `currentField` (it doesn't match anything on `fieldStack`, which is still empty, so no pop happens). `START_ELEMENT` `"address"` — `findField` finds `Person.address`, whose type (`Address`) is **not** simple: a new empty `Address` instance is created, assigned to the `Person`'s `address` field, and *pushed* onto `stack` (now `[Address, Person]`), with `"address"` pushed onto `fieldStack` to remember what will eventually close this nesting level.

Now `START_ELEMENT` `"city"` — `findField` is called against `stack.peek()`'s class, which is now `Address` (not `Person`!) — correctly finding `Address.city`. `currentField = "city"`, and the following `CHARACTERS` event (`"Springfield"`) is set onto the `Address` instance (the current top of stack), not the `Person`. The same happens for `"zip"` → `"12345"`.

`END_ELEMENT` `"address"` matches `fieldStack.peek()` (`"address"`), so both stacks pop — `stack` returns to just `[Person]`, restoring focus to the outer object for any subsequent (in this case, none) top-level fields.

Expected output:
```
Marshalled: <?xml version="1.0" ?><Person><name>Alice</name><address><city>Springfield</city><zip>12345</zip></address></Person>
Unmarshalled: Person{name=Alice, address=Address{city=Springfield, zip=12345}}
```

## 7. Gotchas & takeaways

> Real JAXB (`javax.xml.bind`/`jakarta.xml.bind`) is **not available on the default classpath of Java 11 and later** — it was bundled from Java 6 through 8, marked deprecated-for-removal during Java 9's modularization, and fully removed in Java 11. Any tutorial, Stack Overflow answer, or legacy codebase using `import javax.xml.bind.*` needs an explicit `jakarta.xml.bind-api` + runtime dependency added to compile and run on a modern JDK — it will not work out of the box the way it did on Java 8.

- JAXB automated object-to-XML binding via annotations (`@XmlRootElement`, `@XmlElement`) rather than hand-written per-class parsing code, and was bundled with the JDK from Java 6 through 8.
- The core technique — reflecting over a class's structure to generically marshal/unmarshal any annotated (or, here, convention-following) class — is what any binding framework, JAXB included, does under the hood.
- On Java 9 and 10 it still worked but was deprecated; on Java 11+ it requires an explicit external dependency, since it was fully removed from the default module set.
- StAX (`javax.xml.stream`, covered in the next tutorial) remains bundled on all modern JDKs and is a solid, low-level foundation for building or understanding binding logic yourself.
- Nested object structures require **recursive** marshalling and a **stack-based** approach to unmarshalling, since XML nesting must map onto the nested structure of the object graph, not a flat field list.
