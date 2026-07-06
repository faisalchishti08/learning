---
card: java
gi: 335
slug: field-reflection
title: Field reflection
---

## 1. What it is

Field reflection is using `java.lang.reflect.Field` to inspect and manipulate an object's fields by name, at runtime, without the compiler knowing about them ahead of time. `Class.getDeclaredField(name)` (or `getDeclaredFields()` for all of them) returns a `Field` object describing a field's name, type, and modifiers; calling `field.get(instance)` reads its value and `field.set(instance, value)` writes it — even for `private` fields, if you first call `field.setAccessible(true)` to bypass the normal access-control check.

```java
import java.lang.reflect.Field;

public class FieldReflectionDemo {
    static class Point { private int x = 10; }

    public static void main(String[] args) throws Exception {
        Point p = new Point();
        Field xField = Point.class.getDeclaredField("x");
        xField.setAccessible(true); // required to touch a private field from outside
        System.out.println("x = " + xField.get(p));
        xField.set(p, 99);
        System.out.println("x after set = " + xField.get(p));
    }
}
```

`getDeclaredField("x")` finds the field by its exact name as a string, `setAccessible(true)` overrides Java's normal `private` access check, and `get`/`set` then read and write that specific field on the given instance.

## 2. Why & when

Normal code accesses fields directly (`obj.field`) with full compile-time checking; field reflection exists for the cases where the field to access isn't known until runtime — generic frameworks that need to read or write arbitrary object fields without depending on any specific class.

- **Serialization and mapping frameworks** — libraries like JSON serializers, ORMs, and dependency injection containers use field reflection to read and write object state generically, without every possible class needing to implement a common interface.
- **Testing and debugging tools** — test frameworks sometimes use field reflection to inspect or set up private internal state that isn't exposed through the class's normal public API.
- **Generic utility code** — a "deep copy" or "diff two objects" utility that works across arbitrary classes has to discover their fields reflectively, since it can't know their structure at compile time.

Field reflection bypasses normal encapsulation and type safety — `field.get()` returns `Object`, losing compile-time type information, and `setAccessible(true)` deliberately overrides `private`/`protected` access control, so it should be reserved for genuine framework-level needs, not as a routine substitute for proper getters/setters in application code.

## 3. Core concept

```java
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;

public class FieldReflectionCore {
    static class Config { private String name = "default"; public int version = 1; }

    public static void main(String[] args) throws Exception {
        for (Field field : Config.class.getDeclaredFields()) {
            field.setAccessible(true);
            Config sample = new Config();
            System.out.println(field.getName() + " (" + field.getType().getSimpleName() + ", "
                    + (Modifier.isPrivate(field.getModifiers()) ? "private" : "public")
                    + ") = " + field.get(sample));
        }
    }
}
```

**How to run:** `java FieldReflectionCore.java`

`getDeclaredFields()` returns every field declared directly on the class (regardless of access modifier), and `Modifier.isPrivate(field.getModifiers())` decodes the field's modifiers bitmask into a readable check — this pattern (iterate all fields, inspect each generically) is the basis of most reflection-based tooling.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a Field object obtained by name lets code read or write that field on a specific instance, bypassing normal private access with setAccessible">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="180" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="52" fill="#79c0ff" font-size="10" text-anchor="middle">getDeclaredField("x")</text>

  <text x="215" y="52" fill="#8b949e" font-size="12">→ Field object</text>

  <rect x="20" y="85" width="180" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="107" fill="#6db33f" font-size="10" text-anchor="middle">setAccessible(true)</text>
  <text x="330" y="107" fill="#8b949e" font-size="10">field.get(instance) / field.set(instance, value)</text>
</svg>

## 5. Runnable example

Scenario: a tiny generic object-to-map converter, evolved from one that only handles public fields, into one that also handles private fields via `setAccessible`, into a production-style converter that skips static fields and handles access failures per-field without aborting the whole conversion.

### Level 1 — Basic

```java
import java.lang.reflect.Field;
import java.util.LinkedHashMap;
import java.util.Map;

public class ToMapBasic {
    static class Person { public String name = "Ada"; public int age = 30; }

    public static void main(String[] args) throws Exception {
        Map<String, Object> map = new LinkedHashMap<>();
        Person person = new Person();
        for (Field field : Person.class.getDeclaredFields()) {
            map.put(field.getName(), field.get(person)); // works because fields are public
        }
        System.out.println(map);
    }
}
```

**How to run:** `java ToMapBasic.java`

This works only because both fields happen to be `public`; if `Person` had a `private` field, `field.get(person)` would throw `IllegalAccessException`, since reflection still respects normal access control unless told otherwise.

### Level 2 — Intermediate

```java
import java.lang.reflect.Field;
import java.util.LinkedHashMap;
import java.util.Map;

public class ToMapIntermediate {
    static class Person { private String name = "Ada"; private int age = 30; }

    public static void main(String[] args) throws Exception {
        Map<String, Object> map = new LinkedHashMap<>();
        Person person = new Person();
        for (Field field : Person.class.getDeclaredFields()) {
            field.setAccessible(true); // now works even though fields are private
            map.put(field.getName(), field.get(person));
        }
        System.out.println(map);
    }
}
```

**How to run:** `java ToMapIntermediate.java`

Adding `field.setAccessible(true)` before `get()` lets the code read `private` fields too — the converter now works regardless of the fields' declared access level, which is the point of a genuinely generic utility.

### Level 3 — Advanced

```java
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.LinkedHashMap;
import java.util.Map;

public class ToMapAdvanced {
    static class Person {
        private String name = "Ada";
        private int age = 30;
        private static int instanceCount = 1; // should be skipped -- not per-instance state
    }

    public static void main(String[] args) {
        Person person = new Person();
        Map<String, Object> map = toMap(person);
        System.out.println(map);
    }

    static Map<String, Object> toMap(Object instance) {
        Map<String, Object> map = new LinkedHashMap<>();
        for (Field field : instance.getClass().getDeclaredFields()) {
            if (Modifier.isStatic(field.getModifiers())) {
                continue; // static fields belong to the class, not this instance
            }
            try {
                field.setAccessible(true);
                map.put(field.getName(), field.get(instance));
            } catch (IllegalAccessException e) {
                map.put(field.getName(), "<inaccessible: " + e.getMessage() + ">");
            }
        }
        return map;
    }
}
```

**How to run:** `java ToMapAdvanced.java`

Static fields are explicitly skipped (since `instanceCount` describes the class, not any one `Person`), and each field's access is wrapped in its own `try/catch` so one field failing to read doesn't abort the conversion of the rest — the resulting map correctly contains only `name` and `age`, both successfully read despite being `private`.

## 6. Walkthrough

Execution starts in `main`, which creates one `Person` instance and calls `toMap(person)`.

Inside `toMap`, `instance.getClass()` returns the runtime `Class` object for `Person` (this works even though the parameter is typed as `Object`, since `getClass()` always reports the actual runtime type). `getDeclaredFields()` returns an array containing all three declared fields: `name`, `age`, and `instanceCount`, in declaration order.

The loop processes `name` first: `Modifier.isStatic(field.getModifiers())` is `false`, so the static-skip `continue` is not taken. `field.setAccessible(true)` overrides the normal `private` access check, and `field.get(instance)` returns the string `"Ada"`, which is placed into `map` under the key `"name"`.

The same happens for `age`: `setAccessible(true)` then `get(instance)` returns the boxed `Integer` value `30`, stored under `"age"`.

For `instanceCount`, `Modifier.isStatic(field.getModifiers())` returns `true` this time (it's declared `static`), so the loop's `continue` skips straight to the next iteration — `field.get()` is never called for this field at all, and it never appears in the resulting map.

Back in `main`, the returned `map` — now containing exactly `{name=Ada, age=30}` — is printed via `System.out.println(map)`, using `LinkedHashMap`'s insertion-order iteration so the fields print in the same order they were declared.

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="each declared field is checked for static first, then made accessible and read into the result map, with static fields skipped entirely">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">field "name": not static -&gt; setAccessible(true) -&gt; get(instance) -&gt; "Ada" -&gt; map["name"]="Ada"</text>
  <text x="20" y="55" fill="#79c0ff" font-size="10">field "age": not static -&gt; setAccessible(true) -&gt; get(instance) -&gt; 30 -&gt; map["age"]=30</text>
  <text x="20" y="80" fill="#f85149" font-size="10">field "instanceCount": IS static -&gt; skipped via continue, never read, never added to map</text>
  <text x="20" y="115" fill="#6db33f" font-size="10">Result: {name=Ada, age=30}</text>
</svg>

## 7. Gotchas & takeaways

> `setAccessible(true)` can throw `InaccessibleObjectException` on newer JDKs when the target field belongs to a module that hasn't opened itself to reflection — this is the Java Platform Module System's protection, and no amount of `setAccessible` calls can bypass it without the module explicitly granting access (via `opens` in `module-info.java` or a command-line flag).

- `getDeclaredField(name)`/`getDeclaredFields()` return fields declared directly on that class only — inherited fields from a superclass require walking up via `getSuperclass()` separately.
- `field.get()`/`field.set()` still enforce normal access control by default — `setAccessible(true)` is required to touch `private` or `protected` members from outside their own class.
- Always skip or specifically handle `static` fields when writing per-instance reflective code — they describe the class, not any one object, and reading them per-instance is usually a bug in the utility, not useful data.
- `field.get(instance)` returns `Object`, boxing primitives (an `int` field returns a boxed `Integer`) — this loses compile-time type safety, which is the fundamental tradeoff of reflection.
- Reserve field reflection for genuine framework-level needs (serialization, generic tooling, testing infrastructure) — it bypasses encapsulation and is slower and less safe than direct field access in ordinary application code.
