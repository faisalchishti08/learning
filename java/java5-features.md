# Java 5 Features (2004)

Java 5 (J2SE 5.0, Tiger) was the most significant Java release since 1.0 — it introduced generics, enums, annotations, autoboxing, and more.

---

## 1. Generics

Compile-time type safety for collections and algorithms. Eliminates casts and prevents `ClassCastException` at runtime.

```java
// Before Java 5 — raw types, runtime ClassCastException risk
List list = new ArrayList();
list.add("hello");
String s = (String) list.get(0); // cast required

// Java 5+
List<String> typed = new ArrayList<>();
typed.add("hello");
String s2 = typed.get(0); // no cast needed — type checked at compile time

// Generic method
static <T extends Comparable<T>> T max(T a, T b) {
    return a.compareTo(b) >= 0 ? a : b;
}
System.out.println(max(3, 7));        // 7
System.out.println(max("cat", "dog")); // dog
```

---

## 2. Enhanced for Loop (for-each)

Iterate over arrays and `Iterable` without managing index or iterator.

```java
int[] numbers = {1, 2, 3, 4, 5};

// Old way
for (int i = 0; i < numbers.length; i++) {
    System.out.println(numbers[i]);
}

// Java 5+ for-each
for (int n : numbers) {
    System.out.println(n);
}

// Works on any Iterable
List<String> names = List.of("Alice", "Bob");
for (String name : names) {
    System.out.println(name);
}
```

---

## 3. Autoboxing and Unboxing

Automatic conversion between primitives and their wrapper types.

```java
// Autoboxing: primitive → wrapper
Integer i = 42;          // was: Integer i = Integer.valueOf(42)
List<Integer> nums = new ArrayList<>();
nums.add(100);           // autoboxed: nums.add(Integer.valueOf(100))

// Unboxing: wrapper → primitive
int val = i;             // was: int val = i.intValue()
int sum = nums.get(0) + 5; // unboxes to compute

// Integer cache (-128 to 127)
Integer a = 127;
Integer b = 127;
System.out.println(a == b);  // true  (cached instance)
Integer c = 128;
Integer d = 128;
System.out.println(c == d);  // false (different instances!)
System.out.println(c.equals(d)); // true
```

> ⚠️ **Pitfall:** `==` on `Integer` compares references. Only cached range (-128 to 127) guarantees `==` equality. Always use `.equals()`.

---

## 4. Enums

Type-safe enumeration — much safer than `public static final int` constants.

```java
enum Day {
    MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY;

    public boolean isWeekend() {
        return this == SATURDAY || this == SUNDAY;
    }
}

Day today = Day.FRIDAY;
System.out.println(today.isWeekend()); // false
System.out.println(today.ordinal());   // 4
System.out.println(today.name());      // FRIDAY

for (Day d : Day.values()) {
    if (d.isWeekend()) System.out.println(d + " is a weekend");
}
```

---

## 5. Annotations

Metadata markers on code elements. Built-in: `@Override`, `@Deprecated`, `@SuppressWarnings`.

```java
@Override               // compiler checks override is valid
public String toString() { return "..."; }

@Deprecated             // marks method as obsolete
public void oldMethod() {}

@SuppressWarnings("unchecked") // suppress specific warning
public void rawTypeMethod() { /* uses raw types */ }
```

Custom annotations require `@Retention` and `@Target` (see 27-annotations.md).

---

## 6. Varargs

Variable-length argument lists — syntactic sugar for arrays.

```java
static int sum(int... nums) { // nums is int[]
    int total = 0;
    for (int n : nums) total += n;
    return total;
}

System.out.println(sum(1, 2, 3));        // 6
System.out.println(sum(1, 2, 3, 4, 5)); // 15
System.out.println(sum());               // 0 — empty varargs OK

// String.format uses varargs
String s = String.format("%s = %d", "answer", 42); // "answer = 42"
```

---

## 7. Static Imports

Import static members directly — no class name prefix needed.

```java
import static java.lang.Math.*;
import static java.util.Collections.*;

double r = sqrt(16.0);        // not Math.sqrt
double pi = PI;               // not Math.PI
List<Integer> sorted = singletonList(42); // not Collections.singletonList

// Common in tests:
import static org.junit.jupiter.api.Assertions.*;
assertEquals(expected, actual);  // not Assertions.assertEquals
```

---

## 8. Concurrent Utilities (java.util.concurrent)

`ExecutorService`, `Future`, `BlockingQueue`, `ConcurrentHashMap`, `AtomicInteger`, `Semaphore`, `CountDownLatch` — all introduced in Java 5.

```java
import java.util.concurrent.*;

ExecutorService exec = Executors.newFixedThreadPool(4);
Future<Integer> future = exec.submit(() -> 42);
System.out.println(future.get()); // 42
exec.shutdown();

ConcurrentHashMap<String, Integer> map = new ConcurrentHashMap<>();
map.put("a", 1);

AtomicInteger counter = new AtomicInteger(0);
counter.incrementAndGet();
```

---

## Quick Reference

```
Java 5 key features:
  Generics             List<String>, Map<K,V>, bounded types
  for-each             for (T item : collection)
  Autoboxing           int ↔ Integer automatically
  Enums                type-safe constants with methods
  Annotations          @Override, @Deprecated, custom annotations
  Varargs              void method(int... args)
  Static import        import static Math.sqrt;
  java.util.concurrent ExecutorService, Future, ConcurrentHashMap, Atomic*
  printf/format        String.format, System.out.printf
  Scanner              java.util.Scanner for text input
```
