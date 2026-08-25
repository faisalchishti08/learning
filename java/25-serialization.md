# Java Serialization

## Overview

Serialization converts object state to a byte stream (and back). Java has built-in serialization via `Serializable`, but also modern alternatives: **Externalizable** (full manual control), **Records** (Java 16+), and JSON/binary libraries (Gson, Jackson, Protobuf). Built-in serialization has serious security implications.

---

## 1. Java Serialization (Serializable)

### What is it

Any class implementing `java.io.Serializable` can be serialized. The JVM writes class metadata and field values to a stream. The JVM recreates the object on deserialization without calling constructors.

### Visual Diagram

```
Serialization:
  Object → ObjectOutputStream → byte stream → file / network

  Object state written:
    - Class descriptor (name, serialVersionUID, field list)
    - All non-transient, non-static field values
    - Referenced objects (recursively)

  NOT written:
    - transient fields (marked to skip)
    - static fields (class-level, not instance state)

Deserialization:
  byte stream → ObjectInputStream → Object (bypasses constructor!)

Object graph:
  Person {name="Alice", address=Address{city="NYC"}}
  Serializes both Person AND Address (if Address is Serializable)
  Shared references preserved — same object referenced by multiple fields
  stays the same object after deserialization
```

### Example 1 — Basic Serialize/Deserialize

```java
import java.io.*;
import java.nio.file.*;

public class BasicSerialization {
    record Point(int x, int y) implements Serializable {}  // record is Serializable [Java 16+]

    static class Person implements Serializable {
        private static final long serialVersionUID = 1L; // version stamp
        private String name;
        private int age;
        private transient String password; // NOT serialized
        private static int count = 0;      // NOT serialized (static)

        Person(String name, int age, String password) {
            this.name = name;
            this.age = age;
            this.password = password;
            count++;
        }

        @Override public String toString() {
            return "Person{name=" + name + ", age=" + age + ", password=" + password + "}";
        }
    }

    public static void main(String[] args) throws Exception {
        Person alice = new Person("Alice", 30, "secret123");
        System.out.println("Before: " + alice);
        // Person{name=Alice, age=30, password=secret123}

        // Serialize
        try (ObjectOutputStream oos = new ObjectOutputStream(
                new FileOutputStream("/tmp/person.ser"))) {
            oos.writeObject(alice);
        }

        // Deserialize
        Person loaded;
        try (ObjectInputStream ois = new ObjectInputStream(
                new FileInputStream("/tmp/person.ser"))) {
            loaded = (Person) ois.readObject();
        }

        System.out.println("After: " + loaded);
        // Person{name=Alice, age=30, password=null} ← transient = null
    }
}
```

**What this does:** `transient` fields are excluded from serialization — they're `null` (or default value) after deserialization. `serialVersionUID` stamps the class version — mismatch between serialized and current class throws `InvalidClassException`.

### Dry Run — serialVersionUID Mismatch

```
Version 1: class Person { String name; int age; } serialVersionUID=1L
  → Serialized to file

Version 2: class Person { String name; int age; String email; } serialVersionUID=2L
  → Deserialize file → InvalidClassException!
  local class incompatible: stream classdesc serialVersionUID = 1, local class serialVersionUID = 2

Fix: keep serialVersionUID=1L in version 2 → deserialization succeeds, email=null
Rule: if serialVersionUID not declared, JVM auto-computes it from class structure → any change breaks it
```

### Example 2 — Custom Serialization (readObject/writeObject)

```java
import java.io.*;

public class CustomSerialization {
    static class SecureData implements Serializable {
        private static final long serialVersionUID = 1L;
        private String data;
        private transient String decrypted; // not serialized

        SecureData(String data) {
            this.data = data;
            this.decrypted = decrypt(data);
        }

        private String decrypt(String s) { return "DECRYPTED:" + s; }
        private String encrypt(String s) { return s; }

        private void writeObject(ObjectOutputStream oos) throws IOException {
            oos.defaultWriteObject();           // write non-transient fields
            oos.writeObject(encrypt(decrypted)); // custom: write encrypted transient
        }

        private void readObject(ObjectInputStream ois)
                throws IOException, ClassNotFoundException {
            ois.defaultReadObject();            // read non-transient fields
            String encrypted = (String) ois.readObject(); // read custom data
            this.decrypted = decrypt(encrypted); // restore transient
        }

        @Override public String toString() {
            return "SecureData{data=" + data + ", decrypted=" + decrypted + "}";
        }
    }

    public static void main(String[] args) throws Exception {
        SecureData sd = new SecureData("hello");
        System.out.println("Before: " + sd);

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        try (ObjectOutputStream oos = new ObjectOutputStream(baos)) {
            oos.writeObject(sd);
        }

        SecureData loaded;
        try (ObjectInputStream ois = new ObjectInputStream(
                new ByteArrayInputStream(baos.toByteArray()))) {
            loaded = (SecureData) ois.readObject();
        }

        System.out.println("After: " + loaded); // decrypted restored
    }
}
```

**What this does:** `writeObject`/`readObject` hooks intercept the serialization process. `defaultWriteObject()`/`defaultReadObject()` handle the standard fields; custom code handles the rest. Used for lazy initialization, encryption, computed fields.

---

## 2. Externalizable — Full Manual Control

### What is it

`Externalizable` extends `Serializable` and forces full manual implementation of `writeExternal`/`readExternal`. Faster than default serialization but more code. Class must have a public no-arg constructor (called during deserialization).

### Example 1

```java
import java.io.*;

public class ExternalizableDemo {
    static class Config implements Externalizable {
        private String host;
        private int port;
        private String protocol;

        public Config() {} // REQUIRED — Externalizable calls this during deserialization

        public Config(String host, int port, String protocol) {
            this.host = host; this.port = port; this.protocol = protocol;
        }

        @Override
        public void writeExternal(ObjectOutput out) throws IOException {
            out.writeUTF(host);
            out.writeInt(port);
            // skip protocol — we'll default it on read
        }

        @Override
        public void readExternal(ObjectInput in) throws IOException {
            host = in.readUTF();
            port = in.readInt();
            protocol = "https"; // default — wasn't written
        }

        @Override public String toString() {
            return host + ":" + port + " (" + protocol + ")";
        }
    }

    public static void main(String[] args) throws Exception {
        Config cfg = new Config("example.com", 443, "ftp"); // ftp won't be saved

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        try (ObjectOutputStream oos = new ObjectOutputStream(baos)) {
            oos.writeObject(cfg);
        }

        Config loaded;
        try (ObjectInputStream ois = new ObjectInputStream(
                new ByteArrayInputStream(baos.toByteArray()))) {
            loaded = (Config) ois.readObject();
        }

        System.out.println(loaded); // example.com:443 (https) ← ftp replaced by default
    }
}
```

**What this does:** `Externalizable` gives full read/write control — only write what you need, reconstruct on read. Useful for compact serialization formats or interoperability.

---

## 3. Security Warnings

### Visual Diagram — Deserialization Attack

```
DANGER: Deserialization executes code!

Attacker crafts malicious byte stream:
  → ObjectInputStream.readObject() calls readResolve(), readObject() hooks
  → If classpath has vulnerable libraries (Commons Collections, Spring, etc.)
  → Gadget chain executes → arbitrary code execution (RCE)

CVE-2015-4852 (WebLogic), CVE-2016-4438 (Apache Commons Collections):
  Both exploit Java deserialization of untrusted data

Defense:
  1. NEVER deserialize data from untrusted sources
  2. Use ObjectInputFilter [Java 9+] to whitelist classes
  3. Replace Java serialization with JSON (Jackson/Gson) or Protobuf
```

### Example 1 — ObjectInputFilter [Java 9+]

```java
import java.io.*;

public class FilteredDeserialization {
    record SafeData(String name, int value) implements Serializable {}

    public static void main(String[] args) throws Exception {
        SafeData data = new SafeData("test", 42);

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        try (ObjectOutputStream oos = new ObjectOutputStream(baos)) {
            oos.writeObject(data);
        }

        // Filtered deserialization — whitelist allowed classes [Java 9+]
        try (ObjectInputStream ois = new ObjectInputStream(
                new ByteArrayInputStream(baos.toByteArray()))) {

            // Only allow SafeData and Record-related classes
            ObjectInputFilter filter = ObjectInputFilter.Config.createFilter(
                "FilteredDeserialization$SafeData;java.lang.String;!*"
                // !* rejects everything else
            );
            ois.setObjectInputFilter(filter);

            SafeData loaded = (SafeData) ois.readObject();
            System.out.println(loaded); // SafeData[name=test, value=42]
        }
    }
}
```

**What this does:** `ObjectInputFilter` whitelists allowed classes. `!*` at the end rejects all unlisted classes — any gadget class in the attack chain is blocked.

---

## 4. Records and Serialization [Java 16+]

### Example 1 — Records are Serializable

```java
import java.io.*;

public class RecordSerialization {
    // Records implementing Serializable get safe default serialization
    // Uses the canonical constructor for deserialization (not bypass like classes)
    record Point(double x, double y) implements Serializable {
        // serialVersionUID not needed for records — based on record components
    }

    record User(String name, int age) implements Serializable {}

    public static void main(String[] args) throws Exception {
        User user = new User("Alice", 30);

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        try (ObjectOutputStream oos = new ObjectOutputStream(baos)) {
            oos.writeObject(user);
        }

        User loaded;
        try (ObjectInputStream ois = new ObjectInputStream(
                new ByteArrayInputStream(baos.toByteArray()))) {
            loaded = (User) ois.readObject();
        }

        System.out.println(loaded);         // User[name=Alice, age=30]
        System.out.println(loaded.equals(user)); // true (records use component equality)
    }
}
```

**What this does:** Records use their canonical constructor during deserialization — validation in the canonical constructor runs. This is safer than class deserialization which bypasses constructors entirely.

---

## 5. Modern Alternatives to Java Serialization

### Example 1 — JSON with Jackson (recommended for data transfer)

```java
// Add jackson-databind to classpath
// com.fasterxml.jackson.databind.ObjectMapper

import com.fasterxml.jackson.databind.*;
import java.util.*;

public class JacksonDemo {
    record Person(String name, int age, List<String> hobbies) {}

    public static void main(String[] args) throws Exception {
        ObjectMapper mapper = new ObjectMapper();

        Person alice = new Person("Alice", 30, List.of("hiking", "coding"));

        // Serialize to JSON
        String json = mapper.writeValueAsString(alice);
        System.out.println(json);
        // {"name":"Alice","age":30,"hobbies":["hiking","coding"]}

        // Deserialize from JSON
        // (Jackson needs no-arg constructor or @JsonCreator for records in older versions)
        // With jackson-databind 2.12+ records are supported
        String jsonInput = "{\"name\":\"Bob\",\"age\":25,\"hobbies\":[\"gaming\"]}";
        // Map to generic structure (safe for untrusted data)
        Map<?, ?> data = mapper.readValue(jsonInput, Map.class);
        System.out.println(data.get("name")); // Bob
    }
}
```

### Example 2 — Serialization to/from byte[] with ByteArrayStream

```java
import java.io.*;

public class InMemorySerialization {
    static class Config implements Serializable {
        private static final long serialVersionUID = 1L;
        String host = "localhost";
        int port = 8080;
    }

    static byte[] serialize(Object obj) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        try (ObjectOutputStream oos = new ObjectOutputStream(baos)) {
            oos.writeObject(obj);
        }
        return baos.toByteArray();
    }

    @SuppressWarnings("unchecked")
    static <T> T deserialize(byte[] bytes) throws Exception {
        try (ObjectInputStream ois = new ObjectInputStream(
                new ByteArrayInputStream(bytes))) {
            return (T) ois.readObject();
        }
    }

    public static void main(String[] args) throws Exception {
        Config cfg = new Config();
        byte[] bytes = serialize(cfg);
        System.out.println("Serialized size: " + bytes.length + " bytes");

        Config loaded = deserialize(bytes);
        System.out.println(loaded.host + ":" + loaded.port); // localhost:8080
    }
}
```

**What this does:** Utility pattern for in-memory object deep-copy via serialization. Note: slow and fragile — only use when you have no better option.

---

## Quick Reference

```
Serializable:
  implements Serializable                mark class as serializable
  serialVersionUID = 1L                  version stamp (ALWAYS declare!)
  transient field                        exclude from serialization
  writeObject/readObject                 custom hooks
  readResolve/writeReplace               control object identity/substitution

Externalizable:
  implements Externalizable             full manual control
  public no-arg constructor             REQUIRED
  writeExternal/readExternal           you write/read everything

ObjectInputStream/ObjectOutputStream:
  new ObjectOutputStream(stream)
  oos.writeObject(obj)
  new ObjectInputStream(stream)
  ois.readObject()                      cast to expected type

Security [Java 9+]:
  ois.setObjectInputFilter(filter)      whitelist allowed classes
  ObjectInputFilter.Config.createFilter("pkg.SafeClass;!*")

Alternatives to Java serialization:
  Jackson/Gson   → JSON (human-readable, cross-language)
  Protobuf       → binary (compact, schema-based, cross-language)
  Kryo           → fast Java binary (no schema)
  Records        → safe serialization via canonical constructor [Java 16+]

Transient vs static:
  transient: excluded from serialization (instance field)
  static: excluded from serialization (class-level field)
  Both are null/default after deserialization
```
