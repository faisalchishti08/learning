# Java 10 Features (2018)

Java 10 introduced local variable type inference (`var`) and collection copy methods.

---

## 1. Local Variable Type Inference — `var`

Compiler infers the type of local variables from the initializer.

```java
import java.util.*;
import java.util.stream.*;

public class VarDemo {
    public static void main(String[] args) {
        // var — compiler infers type
        var name     = "Alice";           // String
        var age      = 30;                // int
        var list     = new ArrayList<String>(); // ArrayList<String>
        var pi       = 3.14;              // double

        // In for-each
        var names = List.of("Alice", "Bob", "Charlie");
        for (var n : names) {
            System.out.println(n.toUpperCase()); // n is String — methods available
        }

        // In try-with-resources
        try (var br = new java.io.BufferedReader(new java.io.FileReader("/dev/null"))) {
            var line = br.readLine(); // line is String
        } catch (java.io.IOException e) {}

        // Traditional for loop
        for (var i = 0; i < 5; i++) {
            System.out.print(i + " "); // 0 1 2 3 4
        }
    }
}
```

### When var Works / Doesn't Work

```java
// Works:
var x = 42;                  // local variable with initializer
var list = new ArrayList<>();  // but — inferred as ArrayList<Object>!

// DOES NOT WORK:
var x;                       // no initializer — compiler can't infer
var x = null;                // can't infer from null alone
var arr = {1, 2, 3};        // array initializer without new[]

// NOT allowed on:
private var field = "hello"; // fields — use explicit type
var method() { return 1; }  // return types
void process(var param) {}   // parameters
```

> ⚠️ **Pitfall:** `var list = new ArrayList<>()` infers `ArrayList<Object>` — always specify the type: `var list = new ArrayList<String>()`.

### When to Use var

```java
// GOOD: removes redundant type when obvious from right side
var map = new HashMap<String, List<Integer>>();    // type clear from RHS
var entry = map.entrySet().iterator().next();      // long type, clear from method

// BAD: hides type, reduces readability
var result = process();  // what does process() return? Unclear
var x = getValue();      // int? String? double? — unclear without context
```

---

## 2. Collection Copy Methods [Java 10]

`List.copyOf`, `Set.copyOf`, `Map.copyOf` — immutable copies.

```java
import java.util.*;

List<String> original = new ArrayList<>(List.of("Alice", "Bob"));
original.add("Charlie");

// copyOf — immutable snapshot (does not update with original)
List<String> copy = List.copyOf(original); // [Alice, Bob, Charlie]

original.add("Dave"); // modifying original
System.out.println(copy); // [Alice, Bob, Charlie] — unchanged

// copy.add("Eve"); // throws UnsupportedOperationException

// Set.copyOf / Map.copyOf
Set<Integer> setOrig = new HashSet<>(Set.of(1, 2, 3));
Set<Integer> setCopy = Set.copyOf(setOrig);

Map<String, Integer> mapOrig = new HashMap<>(Map.of("a", 1));
Map<String, Integer> mapCopy = Map.copyOf(mapOrig);
```

---

## 3. Optional.orElseThrow() (no-arg)

```java
import java.util.*;

Optional<String> opt = Optional.of("hello");
Optional<String> empty = Optional.empty();

// Before Java 10: opt.get() — throws NoSuchElementException with bad message
// Java 10: orElseThrow() — same as get() but explicit intent
String val = opt.orElseThrow(); // "hello"

try {
    empty.orElseThrow(); // NoSuchElementException: No value present
} catch (NoSuchElementException e) {
    System.out.println(e.getMessage()); // No value present
}
```

---

## 4. Collectors.toUnmodifiableList/Set/Map [Java 10]

```java
import java.util.*;
import java.util.stream.*;

List<String> names = List.of("Alice", "Bob", "Charlie");

// Collect to unmodifiable list directly
List<String> unmod = names.stream()
    .filter(n -> n.length() > 3)
    .collect(Collectors.toUnmodifiableList());

// unmod.add("Dave"); // throws UnsupportedOperationException

// Set and Map variants
Set<Integer> lengths = names.stream()
    .map(String::length)
    .collect(Collectors.toUnmodifiableSet());

Map<String, Integer> lengthMap = names.stream()
    .collect(Collectors.toUnmodifiableMap(s -> s, String::length));
```

---

## 5. G1 GC Improvements

Java 10 made G1 GC the default (it was already default in Java 9 for server VMs, Java 10 confirmed universally).

```bash
# G1 full GC is now parallel (was single-threaded in Java 9)
java -XX:+UseG1GC -XX:ParallelGCThreads=4 MyApp
```

---

## Quick Reference

```
Java 10 key features:
  var              local variable type inference
                   works: local vars with initializer, for-each, try-with-resources
                   not: fields, params, return types, null initializer
  List.copyOf(c)   immutable copy
  Set.copyOf(c)    immutable copy
  Map.copyOf(m)    immutable copy
  Optional.orElseThrow()  no-arg version (explicit intent)
  Collectors.toUnmodifiableList/Set/Map
  Parallel G1 Full GC    G1 full GC uses multiple threads now
  Application Class-Data Sharing (AppCDS)  faster startup
```
