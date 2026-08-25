# Java Generics

Generics allow classes, interfaces, and methods to operate on typed parameters. The type is specified at compile time, giving you type safety without losing flexibility. The compiler checks types; the JVM sees erased types at runtime.

---

## 1. Why Generics

### Before Generics (Java 1.4 and earlier)

Collections held `Object`. Every retrieval required a cast. Nothing stopped you from mixing types in the same collection. Errors appeared at runtime as `ClassCastException`, not at compile time.

```java
// PRE-GENERICS: Java 1.4 style
import java.util.*;

public class PreGenericsDemo {

    public static void main(String[] args) {
        // List held Object — no type information
        List names = new ArrayList();
        names.add("Alice");
        names.add("Bob");
        names.add(42);          // No compile error — 42 is Object
        names.add(new Date());  // Also fine — still just Object

        // Every read requires a cast
        for (Object obj : names) {
            String s = (String) obj;   // ClassCastException when hitting 42 or Date
            System.out.println(s.toUpperCase());
        }
    }
}
// Runtime output:
// ALICE
// BOB
// Exception in thread "main" java.lang.ClassCastException:
//   class java.lang.Integer cannot be cast to class java.lang.String
```

**What this does:** the `42` and `Date` slip in silently. The cast `(String) obj` fails at runtime — not at the point of adding the wrong type, but at the point of reading. The bug is far from the source.

```java
// WITH GENERICS: Java 5+
import java.util.*;

public class WithGenericsDemo {

    public static void main(String[] args) {
        List<String> names = new ArrayList<>();
        names.add("Alice");
        names.add("Bob");
        // names.add(42);       // COMPILE ERROR: incompatible types
        // names.add(new Date()); // COMPILE ERROR

        // No cast needed — compiler knows it's String
        for (String name : names) {
            System.out.println(name.toUpperCase());
        }
    }
}
```

**What this does:** `List<String>` tells the compiler "this list holds only Strings." Adding an `Integer` is a compile error at the call site — the bug is caught early, where the mistake is made. No cast needed on read.

**Before vs after comparison:**

```
PRE-GENERICS                         WITH GENERICS
─────────────────────────────────    ────────────────────────────────
List names = new ArrayList();        List<String> names = new ArrayList<>();
names.add("hello");   // ok          names.add("hello");   // ok
names.add(42);        // silent bug  names.add(42);        // COMPILE ERROR
String s = (String) names.get(0);   String s = names.get(0);  // no cast
// ClassCastException at runtime     // type safety at compile time
```

> ⚠️ **Pitfall:** Generics provide compile-time safety only. At runtime, due to type erasure, `List<String>` and `List<Integer>` are both `List`. The type parameter is gone. This has important consequences (see section 7).

---

## 2. Generic Classes

A generic class has one or more **type parameters** declared in angle brackets after the class name. Each instantiation provides a concrete type for those parameters.

```
Box<String>                Box<Integer>
──────────────────         ──────────────────
│  T = String    │         │  T = Integer    │
│                │         │                 │
│ value: String  │         │ value: Integer  │
│ get(): String  │         │ get(): Integer  │
└────────────────┘         └─────────────────┘

   Both are views of the same Box<T> class,
   type-safe at compile time, same bytecode at runtime.
```

**Naming conventions:**
- `T` — generic Type
- `E` — Element (collections)
- `K` — Key (maps)
- `V` — Value (maps)
- `N` — Number
- `R` — Return type (function interfaces)

```java
// Single type parameter
public class Box<T> {

    private T value;

    public Box(T value) {
        this.value = value;
    }

    public T get()        { return value; }
    public void set(T v)  { this.value = v; }

    @Override
    public String toString() {
        return "Box[" + value + "]";
    }

    public static void main(String[] args) {
        Box<String>  strBox = new Box<>("Hello");
        Box<Integer> intBox = new Box<>(42);

        String s = strBox.get();   // no cast
        int    i = intBox.get();   // no cast (auto-unboxed)

        System.out.println(strBox);  // Box[Hello]
        System.out.println(intBox);  // Box[42]

        // strBox.set(42);  // COMPILE ERROR: 42 is not a String
    }
}
```

**What this does:** `Box<T>` is a container for any type. When you write `Box<String>`, the compiler replaces every `T` occurrence with `String`. `get()` returns `String`, `set()` accepts `String`. The same class definition handles both string and integer boxes with full type safety.

```java
// Multiple type parameters
public class Pair<K, V> {

    private final K key;
    private final V value;

    public Pair(K key, V value) {
        this.key   = key;
        this.value = value;
    }

    public K getKey()   { return key; }
    public V getValue() { return value; }

    public static <K, V> Pair<K, V> of(K key, V value) {
        return new Pair<>(key, value);
    }

    @Override
    public String toString() {
        return "(" + key + ", " + value + ")";
    }

    public static void main(String[] args) {
        Pair<String, Integer> score = new Pair<>("Alice", 95);
        Pair<String, String>  entry = Pair.of("color", "blue");

        System.out.println(score.getKey());    // Alice
        System.out.println(score.getValue());  // 95
        System.out.println(entry);             // (color, blue)
    }
}
```

**What this does:** `Pair<K, V>` mirrors `Map.Entry`. Two independent type parameters allow the key and value to be completely different types. The static factory method `of()` uses diamond inference: the compiler infers `K=String, V=String` from the arguments.

```java
// Generic class with bounded type parameter
public class NumberBox<N extends Number> {

    private N value;

    public NumberBox(N value) { this.value = value; }

    public N get() { return value; }

    // Can call Number methods because N is bounded by Number
    public double doubleValue() { return value.doubleValue(); }

    public static void main(String[] args) {
        NumberBox<Integer> iBox = new NumberBox<>(42);
        NumberBox<Double>  dBox = new NumberBox<>(3.14);

        System.out.println(iBox.doubleValue());  // 42.0
        System.out.println(dBox.doubleValue());  // 3.14

        // NumberBox<String> sBox = new NumberBox<>("x");  // COMPILE ERROR
    }
}
```

**What this does:** `N extends Number` restricts the type to Number and its subclasses (Integer, Double, Long, etc.). Inside the class, Number's methods (`doubleValue()`, `intValue()`) are available on `value`. String fails the bound check at compile time.

> ⚠️ **Pitfall:** Generic type parameters cannot be primitive types. `Box<int>` is illegal. Use wrapper types: `Box<Integer>`. Autoboxing handles most conversions automatically.

---

## 3. Generic Methods

A generic method has its own type parameter, independent of the class's type parameters. The type is inferred from the arguments.

```
Method signature:  <T> List<T> listOf(T first, T second)
                    ↑
                    type parameter declared on the method, before return type

Call:  listOf("a", "b")   →  T inferred as String
Call:  listOf(1, 2)        →  T inferred as Integer
```

```java
import java.util.*;

public class GenericMethodDemo {

    // Generic method: T declared before return type
    public static <T> List<T> listOf(T first, T second) {
        List<T> list = new ArrayList<>();
        list.add(first);
        list.add(second);
        return list;
    }

    // Generic method in non-generic class — T is method-scoped
    public static <T> T firstNonNull(T a, T b) {
        return a != null ? a : b;
    }

    // Generic method: swap array elements
    public static <T> void swap(T[] arr, int i, int j) {
        T temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }

    public static void main(String[] args) {
        // Type inferred from arguments — no explicit type needed
        List<String>  strings = listOf("hello", "world");
        List<Integer> numbers = listOf(1, 2);

        System.out.println(strings);  // [hello, world]
        System.out.println(numbers);  // [1, 2]

        String result = firstNonNull(null, "default");
        System.out.println(result);  // default

        Integer[] arr = {1, 2, 3, 4};
        swap(arr, 0, 3);
        System.out.println(Arrays.toString(arr));  // [4, 2, 3, 1]
    }
}
```

**What this does:** `<T>` before the return type declares `T` as a method-level type parameter. The compiler infers `T=String` from `listOf("hello", "world")`. For `swap`, it infers `T=Integer` from the `Integer[]` array argument. No explicit type specification needed.

```java
// Type inference and when explicit type is needed
import java.util.*;

public class TypeInferenceDemo {

    public static void main(String[] args) {
        // Inferred — compiler figures out T=String from context
        List<String> empty1 = Collections.emptyList();  // T inferred from assignment

        // Explicit — needed when context is ambiguous
        List<String> empty2 = Collections.<String>emptyList();

        // Ambiguous case: method takes Object, inference fails to String
        process(Collections.<String>emptyList());  // explicit needed
        // process(Collections.emptyList());        // might infer List<Object>

        // Java 8+ improved inference — usually explicit not needed
        List<String> list = new ArrayList<>();
        list.addAll(Collections.emptyList());   // T=String inferred from list
    }

    static void process(List<String> list) {
        System.out.println("processing: " + list);
    }
}
```

**What this does:** Java infers type parameters from the assignment target, method arguments, and context. Explicit type syntax (`Collections.<String>emptyList()`) is needed when the compiler can't infer from context. Java 8 improved inference significantly, making explicit types rarely necessary.

```java
// Generic method with bounded type: finds maximum
public class GenericMax {

    // T must implement Comparable<T> to use compareTo
    public static <T extends Comparable<T>> T max(T a, T b) {
        return a.compareTo(b) >= 0 ? a : b;
    }

    // Works for any Comparable: String, Integer, LocalDate, etc.
    public static void main(String[] args) {
        System.out.println(max("apple", "banana"));  // banana (alphabetical)
        System.out.println(max(42, 17));             // 42
        System.out.println(max(3.14, 2.71));         // 3.14
    }
}
```

**What this does:** `<T extends Comparable<T>>` restricts `T` to types that can compare themselves. Inside the method, `a.compareTo(b)` is safe because the bound guarantees it exists. The same method handles strings, integers, and doubles — all are `Comparable`.

> ⚠️ **Pitfall:** Generic method type parameter `<T>` is declared before the return type, not after the method name. `public T static method()` is a syntax error. Correct: `public static <T> T method()`.

---

## 4. Bounded Type Parameters

Bounds constrain which types are acceptable for a type parameter. They also unlock methods of the bound type inside the generic code.

```
Upper bound:   <T extends Animal>
               T can be Animal or any subclass: Dog, Cat, Bird...
               Inside method: you can call Animal's methods on T

Multiple bounds: <T extends Serializable & Comparable<T>>
               T must implement BOTH interfaces
               Class bound (at most one) must come FIRST
```

```java
// Upper bound: T extends Comparable<T>
public class BoundedDemo {

    // Can call compareTo because T is bounded by Comparable
    public static <T extends Comparable<T>> T clamp(T value, T min, T max) {
        if (value.compareTo(min) < 0) return min;
        if (value.compareTo(max) > 0) return max;
        return value;
    }

    // Sum requires T extends Number to call doubleValue()
    public static <T extends Number> double sum(List<T> list) {
        double total = 0;
        for (T item : list) {
            total += item.doubleValue();  // Number method available
        }
        return total;
    }

    public static void main(String[] args) {
        System.out.println(clamp(5, 1, 10));         // 5
        System.out.println(clamp(0, 1, 10));         // 1 (below min)
        System.out.println(clamp(15, 1, 10));        // 10 (above max)
        System.out.println(clamp("dog", "ant", "fox")); // dog

        List<Integer> ints = Arrays.asList(1, 2, 3, 4, 5);
        System.out.println(sum(ints));   // 15.0
    }
}
```

**What this does:** `clamp` works for any `Comparable` type — integers, strings, dates. The bound `T extends Comparable<T>` is recursive: T can compare to itself. `sum` works for any subclass of `Number` because `doubleValue()` is defined on `Number`.

```java
import java.io.*;
import java.util.*;

// Multiple bounds: class first, then interfaces
public class MultiBoundDemo {

    // T must be Serializable AND Comparable<T>
    // Class bound first (if any), interface bounds after
    public static <T extends Serializable & Comparable<T>> void sortAndStore(
            List<T> items, ObjectOutputStream out) throws IOException {

        Collections.sort(items);   // needs Comparable
        out.writeObject(items);    // needs Serializable
    }

    // Bound on class type parameter
    static class SortedList<T extends Comparable<T>> {
        private final List<T> items = new ArrayList<>();

        public void add(T item) {
            items.add(item);
            Collections.sort(items);
        }

        public T get(int i) { return items.get(i); }
        public int size()   { return items.size(); }
    }

    public static void main(String[] args) {
        SortedList<Integer> sl = new SortedList<>();
        sl.add(5);
        sl.add(2);
        sl.add(8);
        sl.add(1);
        System.out.println(sl.get(0));  // 1 (smallest)
        System.out.println(sl.get(3));  // 8 (largest)
    }
}
```

**What this does:** multiple bounds `T extends Serializable & Comparable<T>` require BOTH. The class bound (if any) always comes first; interface bounds follow with `&`. `SortedList<T extends Comparable<T>>` places the bound on the class type parameter, enforcing it at instantiation.

**Dry run — `clamp(0, 1, 10)`:**

| Step | Code                       | Result                   | Notes                       |
|------|----------------------------|--------------------------|-----------------------------|
| 1    | `value.compareTo(min)`     | `0.compareTo(1)` = -1    | 0 < 1, negative result      |
| 2    | `-1 < 0` is true           | return `min` = 1         | value is below minimum      |
| 3    | caller receives 1          |                          | clamped to lower bound      |

> ⚠️ **Pitfall:** Lower bounds (`<T super Dog>`) are NOT allowed on type parameters — only on wildcards. `<T super Dog>` is a syntax error. Lower bounds on wildcards (`? super Dog`) are fine.

---

## 5. Wildcards

Wildcards (`?`) represent an unknown type. They appear in variable types and method parameters, not in type parameter declarations on classes/methods.

```
WILDCARD COMPARISON
───────────────────────────────────────────────────────────────────
                 List<?>        List<? extends T>   List<? super T>
─────────────────────────────────────────────────────────────────
Read from it:    Object only    T (or parent)       Object only
Write to it:     null only      null only           T (or subtype)
Use when:        type unknown   producing data      consuming data
                                (output)            (input)
───────────────────────────────────────────────────────────────────
```

### Unbounded Wildcard `<?>`

```java
import java.util.*;

public class UnboundedWildcard {

    // Accepts List of ANY type — useful when type doesn't matter
    public static void printAll(List<?> list) {
        for (Object item : list) {   // reads as Object only
            System.out.println(item);
        }
    }

    public static int countNonNull(List<?> list) {
        int count = 0;
        for (Object item : list) {
            if (item != null) count++;
        }
        return count;
    }

    public static void main(String[] args) {
        List<String>  strings = Arrays.asList("a", "b", "c");
        List<Integer> numbers = Arrays.asList(1, 2, 3);
        List<Object>  mixed   = Arrays.asList("x", 1, null);

        printAll(strings);              // a, b, c
        printAll(numbers);              // 1, 2, 3
        System.out.println(countNonNull(mixed));  // 2

        // list.add("something");  // COMPILE ERROR even for List<?>
        // Can only add null: list.add(null); — legal but useless
    }
}
```

**What this does:** `List<?>` accepts any `List<X>` regardless of X. The trade-off: you can only read items as `Object`, and you can only write `null`. Use when the type truly doesn't matter — counting, printing, checking size.

### Upper Bounded Wildcard `<? extends T>`

```java
import java.util.*;

public class UpperBoundedWildcard {

    // Can read as Animal — but cannot add anything (except null)
    public static double totalWeight(List<? extends Number> numbers) {
        double total = 0;
        for (Number n : numbers) {   // read as Number — safe
            total += n.doubleValue();
        }
        return total;
        // numbers.add(3);  // COMPILE ERROR — we don't know the exact type
    }

    static class Animal { String name; Animal(String n) { name = n; } }
    static class Dog extends Animal { Dog(String n) { super(n); } }
    static class Cat extends Animal { Cat(String n) { super(n); } }

    public static void printNames(List<? extends Animal> animals) {
        for (Animal a : animals) {   // read as Animal
            System.out.println(a.name);
        }
        // animals.add(new Dog("Rex"));  // COMPILE ERROR
        // animals.add(new Animal("?"));  // COMPILE ERROR
    }

    public static void main(String[] args) {
        List<Integer> ints  = Arrays.asList(1, 2, 3);
        List<Double>  dubs  = Arrays.asList(1.5, 2.5);
        System.out.println(totalWeight(ints));  // 6.0
        System.out.println(totalWeight(dubs));  // 4.0

        List<Dog> dogs = Arrays.asList(new Dog("Rex"), new Dog("Buddy"));
        List<Cat> cats = Arrays.asList(new Cat("Whiskers"));
        printNames(dogs);
        printNames(cats);
    }
}
```

**What this does:** `List<? extends Number>` means "a list of some subtype of Number." You can safely read items as `Number` because whatever the actual type is, it IS-A Number. You cannot write because if the list is actually `List<Integer>` you can't add a `Double`. **Producer: gives you data to read.**

### Lower Bounded Wildcard `<? super T>`

```java
import java.util.*;

public class LowerBoundedWildcard {

    // Can add Dogs — but reads only as Object
    public static void addDogs(List<? super Dog> list) {
        list.add(new Dog("Rex"));   // Dog or subclass — always safe
        list.add(new Dog("Buddy"));
        // list.add(new Animal("?"));  // COMPILE ERROR — might not fit
        // Dog d = list.get(0);        // COMPILE ERROR — might be Animal or Object
        Object obj = list.get(0);      // only Object is safe to read
    }

    static class Animal {}
    static class Dog extends Animal {}
    static class GoldenRetriever extends Dog {}

    public static void main(String[] args) {
        List<Dog>    dogList    = new ArrayList<>();
        List<Animal> animalList = new ArrayList<>();
        List<Object> objList    = new ArrayList<>();

        addDogs(dogList);     // accepts List<Dog>
        addDogs(animalList);  // accepts List<Animal>
        addDogs(objList);     // accepts List<Object>

        // List<GoldenRetriever> grList = new ArrayList<>();
        // addDogs(grList);  // COMPILE ERROR — GoldenRetriever is more specific than Dog
    }
}
```

**What this does:** `List<? super Dog>` means "a list of Dog or any ancestor of Dog." Adding a `Dog` is always safe — whatever the actual list type is, it can hold a Dog. You can't read as Dog because the list might actually contain Animals or Objects. **Consumer: accepts data you write.**

> ⚠️ **Pitfall:** Wildcard capture errors. You cannot call a method that takes `T` on a `?` typed variable directly. The compiler generates "capture#1 of ?" errors. Helper methods with `<T>` are needed for wildcard capture.

---

## 6. PECS Rule

**P**roducer **E**xtends, **C**onsumer **S**uper.

When designing a method that uses a generic collection:
- If the collection **produces** data (you read from it) → `extends`
- If the collection **consumes** data (you write to it) → `super`

```
src (producer) → data flows → dest (consumer)

src:  List<? extends T>   — read items as T
dest: List<? super T>     — add items of type T
```

```java
import java.util.*;

public class PECSDemo {

    // PECS in action: src is producer (extends), dest is consumer (super)
    public static <T> void copy(List<? super T> dest, List<? extends T> src) {
        for (T item : src) {    // read from producer (extends) as T
            dest.add(item);     // write to consumer (super) T
        }
    }

    public static void main(String[] args) {
        List<Integer> integers = Arrays.asList(1, 2, 3, 4, 5);
        List<Number>  numbers  = new ArrayList<>();

        // src=List<Integer>, dest=List<Number>
        // T inferred as Integer
        // ? extends Integer — Integer IS-A Integer ✓
        // ? super Integer   — Number IS-A super of Integer ✓
        copy(numbers, integers);
        System.out.println(numbers);  // [1, 2, 3, 4, 5]

        // More flexible:
        List<Object> objects = new ArrayList<>();
        copy(objects, integers);  // dest accepts Object (super of Integer)
        System.out.println(objects);  // [1, 2, 3, 4, 5]
    }
}
```

**What this does:** `copy` reads from `src` (producer) using `extends`, writes to `dest` (consumer) using `super`. This is exactly the signature of `Collections.copy(dest, src)`. The PECS rule makes the method maximally flexible — src can be `List<Integer>` and dest can be `List<Number>` or `List<Object>`.

```java
// Real-world PECS: processing pipeline
import java.util.*;
import java.util.function.*;

public class PECSPipeline {

    // source: produces T — use extends
    // sink: consumes T — use super
    // transform: Function<T,T> reads and returns T
    public static <T> void pipeline(
            List<? extends T> source,
            List<? super T>   sink,
            Function<T, T>    transform) {

        for (T item : source) {
            sink.add(transform.apply(item));
        }
    }

    public static void main(String[] args) {
        List<String> input  = Arrays.asList("hello", "world");
        List<Object> output = new ArrayList<>();

        pipeline(input, output, String::toUpperCase);
        System.out.println(output);  // [HELLO, WORLD]
    }
}
```

**What this does:** `source` is `? extends T` (we read from it), `sink` is `? super T` (we write to it). `Function<T,T>` transforms items. This pattern appears in stream pipelines and batch processors.

**Dry run — `copy(numbers, integers)`:**

| Step | T inferred | src element read | dest.add() call    | numbers list after |
|------|------------|------------------|--------------------|--------------------|
| 1    | Integer    | 1 (Integer)      | numbers.add(1)     | [1]                |
| 2    | Integer    | 2 (Integer)      | numbers.add(2)     | [1, 2]             |
| 3    | Integer    | 3 (Integer)      | numbers.add(3)     | [1, 2, 3]          |
| 4    | Integer    | 4 (Integer)      | numbers.add(4)     | [1, 2, 3, 4]       |
| 5    | Integer    | 5 (Integer)      | numbers.add(5)     | [1, 2, 3, 4, 5]    |

> ⚠️ **Pitfall:** Don't use PECS when you both read and write from the same collection. In that case, use a concrete type parameter `<T>`, not a wildcard. Wildcards restrict either reading or writing; concrete `<T>` allows both.

---

## 7. Type Erasure

Generics are a compile-time feature only. The compiler uses type information for type checking, then **erases** it before generating bytecode. At runtime, generic types become their erasure (usually `Object` or the bound).

```
Source code (compile time):          Bytecode (runtime):
──────────────────────────           ────────────────────────────
List<String> names                   List names
names.add("Alice")                   names.add("Alice")
String s = names.get(0)             String s = (String) names.get(0)
                                     ↑ compiler inserted cast

Box<Integer>                         Box
Pair<String, Date>                   Pair
<T extends Number>                   Number (erasure = bound)
<T>                                  Object (erasure = Object)
```

### Consequences of Erasure

```java
import java.util.*;

public class TypeErasureConsequences {

    public static void main(String[] args) {
        List<String>  strings = new ArrayList<>();
        List<Integer> numbers = new ArrayList<>();

        // Both are the same class at runtime
        System.out.println(strings.getClass() == numbers.getClass()); // true
        System.out.println(strings.getClass());  // class java.util.ArrayList

        // Cannot use instanceof with parameterized type
        Object obj = new ArrayList<String>();
        System.out.println(obj instanceof ArrayList<?>);      // legal: unbounded wildcard
        // System.out.println(obj instanceof ArrayList<String>); // COMPILE ERROR

        // Cannot create generic arrays
        // String[] arr = new String[10];       // fine
        // T[] arr = new T[10];                  // COMPILE ERROR (in generic class)
        // List<String>[] listArr = new ArrayList<String>[10];  // COMPILE ERROR

        // Cannot use T.class
        // Class<T> c = T.class;  // COMPILE ERROR (in generic class)
    }
}
```

**What this does:** demonstrates the runtime consequences. Two lists with different type parameters are the same class at runtime. `instanceof` with parameterized type is illegal. Generic array creation is illegal. These restrictions exist because type information is erased.

```java
// What bytecode looks like after erasure
// This generic method:
public static <T extends Comparable<T>> T max(T a, T b) {
    return a.compareTo(b) >= 0 ? a : b;
}

// After erasure becomes roughly:
public static Comparable max(Comparable a, Comparable b) {
    return a.compareTo(b) >= 0 ? a : b;
}
// (T erased to its bound: Comparable)

// This generic class:
class Box<T> {
    T value;
    T get() { return value; }
}

// After erasure:
class Box {
    Object value;      // T erased to Object
    Object get() { return value; }  // return type erased too
}
// Compiler inserts casts at call sites automatically
```

**What this does:** shows what the compiler generates. `T extends Comparable<T>` erases to `Comparable`. Unbounded `T` erases to `Object`. The compiler inserts casts at call sites to restore type safety.

### Bridge Methods

```java
// Bridge methods: compiler generates them for covariant return / overrides
interface Producer<T> {
    T produce();
}

class StringProducer implements Producer<String> {
    @Override
    public String produce() {   // specific: returns String
        return "hello";
    }
    // Compiler also generates bridge method:
    // public Object produce() { return produce(); }
    // This bridges the erased interface (Object produce()) to the concrete method
}
```

**What this does:** after erasure, `Producer<T>` becomes `Producer` with `Object produce()`. `StringProducer.produce()` returns `String`, which doesn't match the erased `Object produce()` signature. The compiler generates a synthetic **bridge method** `Object produce()` that calls the real `String produce()`.

### Heap Pollution

```java
import java.util.*;

public class HeapPollution {

    @SuppressWarnings("unchecked")
    static List<String> getList() {
        // Raw type assignment — heap pollution possible
        List raw = new ArrayList();
        raw.add(42);  // Integer sneaks in
        return (List<String>) raw;  // unchecked cast, compiler warns but allows
    }

    public static void main(String[] args) {
        List<String> list = getList();
        // Looks like List<String> but contains Integer
        // ClassCastException here, not at the add site
        String s = list.get(0);  // ClassCastException: Integer cannot be cast to String
    }
}
```

**What this does:** heap pollution means a variable of parameterized type refers to an object that doesn't match the parameter. It happens via raw types or unchecked casts. The exception throws at the read site (far from the corruption), which is exactly the pre-generics problem.

> ⚠️ **Pitfall:** Cannot create `new T()` or `new T[]` in generic code. Workaround: pass a `Class<T>` parameter and use `clazz.getDeclaredConstructor().newInstance()`, or pass a factory `Supplier<T>`.

---

## 8. Raw Types

A **raw type** is a generic class or interface used without type parameters. `List` instead of `List<String>`. Raw types exist solely for backward compatibility with pre-Java-5 code.

```
Raw type:                     Parameterized type:
────────────────────          ────────────────────────
List list = ...               List<String> list = ...
list.add("hello")  ok         list.add("hello")  ok
list.add(42)       ok         list.add(42)       COMPILE ERROR
list.add(new Date()) ok       list.add(new Date()) COMPILE ERROR
Object o = list.get(0)        String s = list.get(0)
// cast needed everywhere     // no cast needed
// runtime ClassCastException // compile-time safety
```

```java
import java.util.*;

public class RawTypeDemo {

    @SuppressWarnings("unchecked")
    public static void main(String[] args) {
        // Raw type — no type parameter
        List rawList = new ArrayList();  // unchecked warning
        rawList.add("hello");
        rawList.add(42);           // no error — raw type accepts anything
        rawList.add(new Object()); // also fine

        // Retrieve requires cast — ClassCastException risk
        String s = (String) rawList.get(0);  // ok
        // String x = (String) rawList.get(1);  // ClassCastException at runtime

        // Raw type assigned to parameterized — still unchecked
        List<String> strings = rawList;  // unchecked warning
        // Now strings supposedly holds only Strings, but actually holds Integer too
        // ClassCastException when you iterate
    }
}
```

**What this does:** raw `List` bypasses all type checking. Adding an Integer to what becomes `List<String>` compiles with a warning but blows up at runtime. This is exactly the pre-generics behavior — raw types retain it for compatibility.

```java
// How raw types corrupt generic collections (heap pollution in action)
import java.util.*;

public class RawTypeCorruption {

    // Legacy method with raw type parameter
    static void addToList(List list, Object item) {
        list.add(item);  // unchecked, but compiles
    }

    public static void main(String[] args) {
        List<String> safeList = new ArrayList<>();
        safeList.add("Alice");

        // Raw type usage bypasses generic type checking
        addToList(safeList, 42);       // Integer smuggled in
        addToList(safeList, new Date()); // Date smuggled in

        // safeList appears to be List<String> but is corrupted
        for (String s : safeList) {    // ClassCastException on Integer
            System.out.println(s.toUpperCase());
        }
    }
}
```

**What this does:** `addToList` takes a raw `List` — all generic info discarded. The corrupted `safeList` compiles fine but explodes on iteration. The for-each loop implicitly casts each element to `String`; when it hits the Integer, ClassCastException.

```java
// @SuppressWarnings("unchecked") — when and why
import java.util.*;

public class SuppressWarningsDemo {

    // Suppress ONLY when you're certain the operation is safe
    // and you've manually verified type correctness
    @SuppressWarnings("unchecked")
    public static <T> T firstElement(Object list) {
        // We know from context this is List<T>, but compiler doesn't
        return (T) ((List<?>) list).get(0);
    }

    // WRONG: suppress on whole class/method hides real warnings
    // @SuppressWarnings("unchecked")  // Too broad — don't do this
    // public class BadPractice { ... }

    // RIGHT: suppress on the smallest possible scope — the single cast
    public static List<String> loadConfig() {
        List raw = loadRawConfig();  // legacy API returns raw type
        @SuppressWarnings("unchecked")
        List<String> typed = raw;   // suppressed only here
        return typed;
    }

    static List loadRawConfig() { return new ArrayList<>(Arrays.asList("a", "b")); }

    public static void main(String[] args) {
        List<String> strings = Arrays.asList("hello", "world");
        String first = firstElement(strings);
        System.out.println(first);  // hello
    }
}
```

**What this does:** `@SuppressWarnings("unchecked")` silences the compiler warning. Use it only when you've manually verified the cast is safe — and always at the narrowest scope (single variable, single method — never class). The annotation is documentation that you've taken responsibility for type safety.

**Dry run — raw type corruption trace:**

| Step | Code                                | List contents              | Types          |
|------|-------------------------------------|----------------------------|----------------|
| 1    | `safeList.add("Alice")`             | ["Alice"]                  | [String]       |
| 2    | `addToList(safeList, 42)`           | ["Alice", 42]              | [String, Integer] |
| 3    | `addToList(safeList, new Date())`   | ["Alice", 42, Date]        | [String, Integer, Date] |
| 4    | for-each: `(String) "Alice"`        | ok                         | String cast ok |
| 5    | for-each: `(String) 42`             | ClassCastException         | Integer → String fail |

> ⚠️ **Pitfall:** Raw types cause unchecked cast warnings that are easy to ignore. Enable `-Xlint:unchecked` in your compiler flags to see full warning details. Every unchecked warning is a potential runtime ClassCastException.

> ⚠️ **Pitfall:** Never use raw types in new code. The only legitimate use of raw types is when interfacing with legacy pre-Java-5 APIs that you cannot modify. Everywhere else, always specify type parameters.
