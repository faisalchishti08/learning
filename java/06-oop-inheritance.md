# Java OOP — Inheritance & Polymorphism

## Overview

Inheritance lets a new class absorb the members of an existing class and specialize them. Java supports **single inheritance** for classes (one parent only) and **multiple inheritance** for interfaces. This file covers `extends`, `super`, method overriding vs overloading, `final`, `instanceof`, and the universal base class `Object`.

---

## 1. extends — The IS-A Relationship

### What is it

`class Dog extends Animal` means every `Dog` IS-A `Animal`. The child (subclass) inherits all **public** and **protected** members from the parent (superclass). What is NOT inherited:

- `private` fields and methods (exist in the object's memory but not accessible by name)
- Constructors (constructors are never inherited)
- `static` members are not truly inherited either — they're accessible via the subclass name, but they belong to the declaring class

**Single inheritance only:** A class can extend exactly one class. It can implement multiple interfaces.

### Visual Diagram — Inheritance Hierarchy with Visible Members

```
class Animal                          (parent / superclass)
┌──────────────────────────────────┐
│  private  String dna             │  ← NOT inherited (inaccessible by name)
│  protected String name           │  ← inherited (visible to Dog)
│  public   void eat()             │  ← inherited (visible everywhere)
│  public   void breathe()         │  ← inherited (visible everywhere)
└──────────────────────────────────┘
          ▲  extends
          │
class Dog                             (child / subclass)
┌──────────────────────────────────┐
│  inherits: name, eat(), breathe()│
│  adds:     String breed          │  ← Dog-specific field
│  adds:     void fetch()          │  ← Dog-specific method
│  overrides: toString()           │  ← replaces Animal's toString
└──────────────────────────────────┘

A Dog object in heap contains BOTH Animal's fields and Dog's fields:
┌──────────────────────────────────────┐
│  Dog @A1                             │
│  [Animal part]  dna = "ACGT"         │
│  [Animal part]  name = "Rex"         │
│  [Dog part]     breed = "Husky"      │
└──────────────────────────────────────┘
```

### Code Example 1 — Basic extends

```java
public class Animal {
    protected String name;
    protected int    age;

    public Animal(String name, int age) {
        this.name = name;
        this.age  = age;
    }

    public void eat() {
        System.out.println(name + " is eating.");
    }

    public void breathe() {
        System.out.println(name + " is breathing.");
    }
}

public class Dog extends Animal {
    private String breed;

    public Dog(String name, int age, String breed) {
        super(name, age);        // call Animal's constructor
        this.breed = breed;
    }

    public void fetch() {
        System.out.println(name + " fetches the ball!");  // name inherited
    }
}
```

**What this does:** `Dog` inherits `name`, `age`, `eat()`, `breathe()` from `Animal`. `Dog` adds `breed` and `fetch()`. The `super(name, age)` call is mandatory because `Animal` has no no-arg constructor.

### Code Example 2 — Polymorphic reference

```java
Animal a = new Dog("Rex", 3, "Husky");  // Animal reference, Dog object
a.eat();       // inherited — works
a.fetch();     // COMPILE ERROR — Animal type doesn't declare fetch()

Dog d = (Dog) a;   // downcast
d.fetch();     // works: Rex fetches the ball!
```

**What this does:** An `Animal` reference can hold a `Dog` object (IS-A holds). But through that reference, only `Animal`'s public API is visible at compile time.

### Code Example 3 — What private members do in subclasses

```java
public class Vehicle {
    private int engineCode = 9999;    // private — not accessible by name in subclass

    protected int getEngineCode() { return engineCode; }  // accessor is protected
}

public class Car extends Vehicle {
    void printEngine() {
        // System.out.println(engineCode);  // COMPILE ERROR — private
        System.out.println(getEngineCode()); // OK — uses protected accessor
    }
}
```

**What this does:** `private` fields exist inside every `Car` object's memory (because Car IS-A Vehicle), but the name `engineCode` is inaccessible. Access must go through an inherited accessor.

### Code Example 4 — Multi-level inheritance chain

```java
public class LivingThing {
    public void metabolize() { System.out.println("Metabolizing"); }
}

public class Animal extends LivingThing {
    public void eat() { System.out.println("Eating"); }
}

public class Dog extends Animal {
    public void fetch() { System.out.println("Fetching"); }
}

Dog d = new Dog("Rex", 2, "Husky");
d.metabolize();   // inherited from LivingThing (2 levels up)
d.eat();          // inherited from Animal
d.fetch();        // defined in Dog
```

**What this does:** Inheritance chains can be multiple levels deep. A `Dog` inherits everything from `Animal` which inherits everything from `LivingThing`. All three method calls succeed.

> ⚠️ **Pitfall:** Java has no **multiple class inheritance** (`class Dog extends Animal, Pet` is illegal). Use interfaces for multiple IS-A relationships: `class Dog extends Animal implements Pet, Trainable`.

---

## 2. super Keyword

### What is it

`super` refers to the **parent class** portion of the current object. Two distinct uses:

1. **`super.method()`** — invoke the parent's version of a method (often called from within an overriding method)
2. **`super(args)`** — invoke the parent's constructor; must be the **first statement** in a child constructor

**Implicit super():** If a child constructor does NOT explicitly call `super(args)` or `this(args)`, the compiler automatically inserts `super()` (no-arg). If the parent has no accessible no-arg constructor, this causes a compile error.

### Code Example 1 — super.method()

```java
public class Animal {
    public String describe() {
        return "I am an animal";
    }
}

public class Dog extends Animal {
    @Override
    public String describe() {
        return super.describe() + ", specifically a dog";  // call parent first
    }
}

Dog d = new Dog("Rex", 3, "Husky");
System.out.println(d.describe());
// I am an animal, specifically a dog
```

**What this does:** `super.describe()` calls the `Animal` version of `describe()` from inside `Dog`'s override. Without `super.`, `this.describe()` would recurse infinitely.

### Code Example 2 — super(args) in constructor

```java
public class Animal {
    protected String name;

    public Animal(String name) {
        this.name = name;
        System.out.println("Animal ctor: " + name);
    }
}

public class Mammal extends Animal {
    protected boolean hasFur;

    public Mammal(String name, boolean hasFur) {
        super(name);          // must be first — calls Animal(String)
        this.hasFur = hasFur;
        System.out.println("Mammal ctor: hasFur=" + hasFur);
    }
}

public class Dog extends Mammal {
    private String breed;

    public Dog(String name, String breed) {
        super(name, true);    // must be first — calls Mammal(String, boolean)
        this.breed = breed;
        System.out.println("Dog ctor: breed=" + breed);
    }
}
```

**What this does:** Each level delegates to its parent constructor via `super(args)`. Parent constructors always run before the child's body.

### Dry Run — 3-level Constructor Chain (Animal → Mammal → Dog)

```
Call: new Dog("Rex", "Husky")

Step  Constructor / Statement           Output printed               State after
----  ---------------------------------  ---------------------------  ----------------------
1     Dog("Rex","Husky") entered         —                            —
2     super("Rex", true) → Mammal ctor   —                            (jumping to Mammal)
3     Mammal("Rex", true) entered        —                            —
4     super("Rex") → Animal ctor         —                            (jumping to Animal)
5     Animal("Rex") entered              —                            —
6     this.name = "Rex"                  —                            name="Rex"
7     println("Animal ctor: Rex")        Animal ctor: Rex             name="Rex"
8     Animal ctor returns                —                            (back to Mammal)
9     this.hasFur = true                 —                            hasFur=true
10    println("Mammal ctor: hasFur=true") Mammal ctor: hasFur=true   hasFur=true
11    Mammal ctor returns                —                            (back to Dog)
12    this.breed = "Husky"               —                            breed="Husky"
13    println("Dog ctor: breed=Husky")   Dog ctor: breed=Husky        breed="Husky"
14    Dog ctor returns                   —                            object complete

Console output (in order):
  Animal ctor: Rex
  Mammal ctor: hasFur=true
  Dog ctor: breed=Husky

Final object state: name="Rex", hasFur=true, breed="Husky"
```

### Code Example 3 — Implicit super() and compile error

```java
public class Parent {
    Parent(int x) { System.out.println("Parent: " + x); }
    // No no-arg constructor!
}

public class Child extends Parent {
    Child() {
        // Compiler inserts: super(); ← but Parent() doesn't exist!
        // COMPILE ERROR: no default constructor in Parent
    }

    Child(int x) {
        super(x);   // explicit super call — OK
    }
}
```

**What this does:** The implicit `super()` insertion only works if the parent has an accessible no-arg constructor. If you add a parameterized constructor to a parent without keeping a no-arg constructor, all child constructors that don't explicitly call `super(args)` will fail to compile.

### Code Example 4 — super in method to extend behavior

```java
public class Logger {
    public void log(String msg) {
        System.out.println("[LOG] " + msg);
    }
}

public class TimestampLogger extends Logger {
    @Override
    public void log(String msg) {
        super.log(msg);                                // delegate to parent
        System.out.println("  at: " + System.currentTimeMillis());
    }
}

TimestampLogger tl = new TimestampLogger();
tl.log("Server started");
// [LOG] Server started
//   at: 1748800000000
```

**What this does:** `super.log(msg)` reuses the parent's logic rather than duplicating it. The child adds timestamp behavior on top.

> ⚠️ **Pitfall:** `super(args)` and `this(args)` are mutually exclusive in the same constructor — you cannot have both as the first statement. A constructor can start with ONE of them, not both.

---

## 3. Method Overriding vs Overloading

### What is it

**Overriding:** Redefining a parent method in the child with the **exact same signature** (name + parameter types). Resolution is at **runtime** (dynamic dispatch). Annotate with `@Override`.

**Overloading:** Multiple methods in the **same class** with the **same name but different parameters**. Resolution is at **compile time** (static dispatch). Return type alone does not distinguish overloads.

Rules for overriding:
- Same method name, same parameter types (in same order)
- Return type must be identical **or a subtype** (covariant return type)
- Access modifier can be **widened** but not narrowed (e.g., `protected` → `public` OK; `public` → `private` NOT OK)
- Cannot override `final`, `static`, or `private` methods
- Must not throw new or broader checked exceptions

### Visual Diagram — Compile-time vs Runtime Dispatch

```
OVERLOADING (compile-time / static dispatch)
────────────────────────────────────────────
Animal a = new Dog(...);
a.eat();           // only one eat() exists — no choice to make at compile time

class Printer {
    void print(int x)    { ... }   ← selected by compiler based on arg type
    void print(String s) { ... }   ← selected by compiler based on arg type
}
Printer p = new Printer();
p.print(42);       // compiler picks print(int)   — resolved at compile time
p.print("hi");     // compiler picks print(String) — resolved at compile time


OVERRIDING (runtime / dynamic dispatch)
────────────────────────────────────────
Animal a = new Dog(...);    // declared type: Animal; runtime type: Dog
a.breathe();

  Compiler: "Animal declares breathe() — OK, the call is valid"
  JVM at runtime: "actual object is Dog; Dog overrides breathe()?
                   YES → call Dog.breathe()"

  → runtime type wins, always
```

### Code Example 1 — Basic override with @Override

```java
public class Shape {
    public double area() {
        return 0.0;
    }
}

public class Circle extends Shape {
    private double radius;

    Circle(double radius) { this.radius = radius; }

    @Override
    public double area() {
        return Math.PI * radius * radius;   // replaces Shape's version
    }
}

Shape s = new Circle(5.0);
System.out.println(s.area());   // 78.539... — Dog's area() is called
```

**What this does:** `@Override` tells the compiler "this must match a parent method." If the signature is wrong (typo, wrong params), you get a compile error instead of silently creating a new unrelated method.

### Code Example 2 — Covariant return type

```java
public class Animal {
    public Animal create() {
        return new Animal("generic", 0);
    }
}

public class Dog extends Animal {
    @Override
    public Dog create() {       // return type is Dog (subtype of Animal) — valid!
        return new Dog("puppy", 0, "mixed");
    }
}

Animal a = new Dog("Rex", 3, "Husky");
Animal result = a.create();     // runtime calls Dog.create(), returns Dog
System.out.println(result.getClass().getSimpleName());  // Dog
```

**What this does:** Covariant return types allow the override to return a more specific type. This is useful in factory methods and builder patterns.

### Code Example 3 — Overloading (same class, different params)

```java
public class Formatter {
    // Three overloads of format()
    public String format(int n) {
        return "[int:" + n + "]";
    }

    public String format(double d) {
        return "[double:" + d + "]";
    }

    public String format(String s) {
        return "[str:" + s + "]";
    }

    public String format(int n, String label) {
        return "[" + label + ":" + n + "]";
    }
}

Formatter f = new Formatter();
System.out.println(f.format(42));          // [int:42]
System.out.println(f.format(3.14));        // [double:3.14]
System.out.println(f.format("hello"));     // [str:hello]
System.out.println(f.format(7, "id"));     // [id:7]
```

**What this does:** The compiler picks the right overload based on argument types at compile time. Overloading is not polymorphism — it is compile-time method selection.

### Code Example 4 — Access widening (valid) vs narrowing (invalid)

```java
public class Parent {
    protected void report() { System.out.println("Parent"); }
}

public class Child extends Parent {
    @Override
    public void report() {   // widened from protected → public: VALID
        System.out.println("Child");
    }
}

public class BadChild extends Parent {
    // @Override
    // private void report() { }   // narrowed from protected → private: COMPILE ERROR
}
```

**What this does:** An override can grant MORE access (e.g., `protected` → `public`) because callers who previously could call `report()` on a `Parent` reference still can. Narrowing would break existing callers.

> ⚠️ **Pitfall:** Overloads are selected by the **declared** type of the argument, not the runtime type. `void handle(Animal a)` and `void handle(Dog d)` — calling `handle(animalRef)` where `animalRef` actually points to a `Dog` will still call `handle(Animal a)` if the declared type is `Animal`. This surprises many developers who expect runtime dispatch.

> ⚠️ **Pitfall:** Forgetting `@Override` and having a typo in the method name. Without `@Override`, you silently create a new method that never gets called as an override. Always use `@Override`.

---

## 4. final

### What is it

`final` means "cannot be changed after this point." Applies at three levels:

| Context       | Meaning                                          |
|---------------|--------------------------------------------------|
| `final class`  | Cannot be subclassed                             |
| `final method` | Cannot be overridden in subclasses               |
| `final variable` | Can only be assigned once                     |

**Effectively final [Java 8+]:** A variable not declared `final` but never reassigned after initialization. Local variables used in lambdas and anonymous classes must be final or effectively final.

### Code Example 1 — final class

```java
public final class String { ... }    // JDK — cannot extend String
public final class Integer { ... }   // JDK — cannot extend Integer

// Attempting to extend:
// public class MyString extends String { }  // COMPILE ERROR
```

**What this does:** `final class` guarantees the behavior of the class cannot be changed by subclassing. JDK uses this for security (e.g., `String`'s immutability would break if subclasses could override it).

### Code Example 2 — final method

```java
public class Template {
    // Algorithm skeleton — order cannot be changed by subclasses
    public final void execute() {
        step1();
        step2();
        step3();
    }

    protected void step1() { System.out.println("Default step1"); }
    protected void step2() { System.out.println("Default step2"); }
    protected void step3() { System.out.println("Default step3"); }
}

public class ConcreteTemplate extends Template {
    @Override
    protected void step2() { System.out.println("Custom step2"); }
    // Trying to override execute() → COMPILE ERROR
}
```

**What this does:** `final` on `execute()` locks the algorithm structure (Template Method pattern). Subclasses can customize individual steps but not the overall order.

### Code Example 3 — final variable (field, local, parameter)

```java
public class Circle {
    private final double radius;    // must be set in constructor; never changes

    Circle(double radius) {
        this.radius = radius;       // OK — first and only assignment
        // this.radius = 5.0;       // COMPILE ERROR — already assigned
    }

    double area() {
        final double PI = Math.PI;  // local final — computed once
        // PI = 3.0;                // COMPILE ERROR
        return PI * radius * radius;
    }

    void scale(final double factor) {   // parameter declared final
        // factor = 2.0;               // COMPILE ERROR
        System.out.println(radius * factor);
    }
}
```

**What this does:** A `final` field must be assigned exactly once — either at declaration or in every constructor path. A `final` local variable must be assigned before use and cannot be reassigned.

### Code Example 4 — Effectively final [Java 8+]

```java
public class EffectivelyFinalDemo {
    public static void main(String[] args) {
        int threshold = 10;          // NOT declared final, but never reassigned
        // threshold = 20;           // uncommenting this breaks lambdas below

        List<Integer> numbers = List.of(1, 5, 15, 20, 3);

        numbers.stream()
               .filter(n -> n > threshold)   // threshold is effectively final — OK
               .forEach(System.out::println);
        // prints: 15, 20

        String prefix = "ID-";               // effectively final
        numbers.stream()
               .map(n -> prefix + n)         // OK — prefix never reassigned
               .forEach(System.out::println);
    }
}
```

**What this does:** [Java 8+] Lambdas and anonymous classes can capture local variables that are either explicitly `final` or effectively final (assigned once, never reassigned). The compiler checks this — mutating a captured variable is a compile error.

> ⚠️ **Pitfall:** `final` on a reference type means the **reference** cannot be reassigned — not that the object is immutable. `final List<String> list = new ArrayList<>();` — you can still call `list.add("x")`. The variable `list` just can't be made to point to a different `ArrayList`.

---

## 5. instanceof and Pattern Matching

### What is it

`instanceof` tests whether an object is an instance of a given type (or a subtype). Returns `boolean`.

Key rules:
- **Always `false` for `null`** — `null instanceof Anything` is always `false`, never throws NPE
- Classic pattern requires explicit cast after the test
- **Pattern matching** [Java 16+]: `obj instanceof TypeName varName` — binds a new variable and avoids the cast

### Code Example 1 — Classic instanceof + cast

```java
void describe(Object obj) {
    if (obj instanceof Dog) {
        Dog d = (Dog) obj;          // explicit downcast
        System.out.println("Dog breed: " + d.breed);
    } else if (obj instanceof Animal) {
        Animal a = (Animal) obj;
        System.out.println("Animal name: " + a.name);
    } else {
        System.out.println("Unknown: " + obj);
    }
}
```

**What this does:** Classic `instanceof` followed by a cast. Redundant — the type check already guarantees the cast is safe, but you must still write it.

### Code Example 2 — instanceof with null

```java
Dog  d   = new Dog("Rex", 3, "Husky");
Animal a = null;
Object o = null;

System.out.println(d instanceof Animal);   // true  (Dog IS-A Animal)
System.out.println(a instanceof Animal);   // false (null is never instanceof anything)
System.out.println(o instanceof Object);   // false (null again)

// Safe null check pattern:
String s = null;
if (s instanceof String) {   // false — no NPE, safe
    System.out.println(s.length());
}
```

**What this does:** `null instanceof X` is always `false` — no NullPointerException. This makes `instanceof` a safe null-and-type check in one operation.

### Code Example 3 — Pattern matching instanceof [Java 16+]

```java
// [Java 16+]
void describe(Object obj) {
    if (obj instanceof Dog d) {
        // d is automatically cast and in scope here
        System.out.println("Dog: " + d.breed);
    } else if (obj instanceof Animal a) {
        System.out.println("Animal: " + a.name);
    } else if (obj instanceof String s && s.length() > 5) {
        // pattern variable can be used in same condition with &&
        System.out.println("Long string: " + s);
    } else {
        System.out.println("Other: " + obj);
    }
}
```

**What this does:** Pattern matching eliminates the redundant cast. The variable `d` is automatically bound to the result of the type test. Using `&&` extends the condition using the pattern variable in the same expression.

### Code Example 4 — Scope rules for pattern variables [Java 16+]

```java
// [Java 16+]
void scopeDemo(Object obj) {
    if (obj instanceof String s) {
        System.out.println(s.toUpperCase());   // s in scope here — OK
    }
    // System.out.println(s);                 // COMPILE ERROR — s out of scope

    // Negation: s is in scope in the else branch if you negate
    if (!(obj instanceof String s)) {
        System.out.println("Not a string");
        // s NOT in scope here
    } else {
        System.out.println(s.toUpperCase());   // s IS in scope in else
    }

    // Short-circuit: using || does NOT bring pattern variable into scope after
    // if (obj instanceof String s || obj instanceof Integer i) { }
    // → COMPILE ERROR: s and i not definitely assigned in body
}
```

**What this does:** Pattern variables are in scope only where the type test is known to have succeeded. The compiler tracks this through control flow — negation flips the scope to the else branch.

> ⚠️ **Pitfall:** Before [Java 16], the common mistake is checking `instanceof` then casting to a *different* type by typo. `@SuppressWarnings` won't catch it. With pattern matching, the variable is automatically typed correctly, eliminating this class of bug.

---

## 6. Object Class Methods

### What is it

Every class in Java implicitly extends `java.lang.Object`. `Object` defines several methods that are universally available and frequently overridden:

| Method        | Default behavior                     | Override reason                         |
|---------------|--------------------------------------|-----------------------------------------|
| `equals()`    | Reference equality (`==`)            | Value equality (compare fields)         |
| `hashCode()`  | Derived from memory address          | Consistent with equals, needed for Maps |
| `toString()`  | `ClassName@hexHashCode`              | Readable string representation          |
| `clone()`     | Shallow copy (requires Cloneable)    | Deep copy or immutability               |
| `getClass()`  | Returns runtime `Class<?>` object    | Rarely overridden; useful for reflection|

### equals() Contract

All five rules must hold:

```
1. Reflexive:    x.equals(x)           → true (always)
2. Symmetric:    x.equals(y)           → y.equals(x) must be same
3. Transitive:   x.equals(y) && y.equals(z) → x.equals(z)
4. Consistent:   repeated calls return same result (no side effects)
5. Null-safe:    x.equals(null)        → false (never throw NPE)
```

### hashCode() Contract

```
1. Consistency: same object → same hashCode (within one JVM run)
2. If x.equals(y) is true → x.hashCode() == y.hashCode() MUST hold
3. If x.equals(y) is false → hashCodes MAY differ (not required, but preferred for performance)
```

**Critical rule:** If you override `equals()`, you MUST override `hashCode()`. Violating this breaks `HashMap`, `HashSet`, `Hashtable`.

### Code Example 1 — Default equals and toString

```java
Dog a = new Dog("Rex", 3, "Husky");
Dog b = new Dog("Rex", 3, "Husky");   // same values, different object

System.out.println(a.equals(b));     // false — default equals uses ==
System.out.println(a == b);          // false — different references
System.out.println(a.toString());    // Dog@1b6d3586 (or similar)
System.out.println(a.hashCode());    // some memory-derived integer
System.out.println(b.hashCode());    // different from a's
```

**What this does:** Default `Object.equals()` is reference equality. Two distinct objects created with identical values are NOT equal by default. Default `toString()` is nearly useless for debugging.

### Code Example 2 — Correct equals() implementation

```java
public class Money {
    private final int    cents;
    private final String currency;

    Money(int cents, String currency) {
        this.cents    = cents;
        this.currency = currency;
    }

    @Override
    public boolean equals(Object obj) {
        // 1. Same reference shortcut
        if (this == obj) return true;

        // 2. Null check + type check (instanceof handles null safely)
        if (!(obj instanceof Money)) return false;

        // 3. Cast
        Money other = (Money) obj;

        // 4. Compare fields
        return this.cents == other.cents
            && this.currency.equals(other.currency);
    }

    @Override
    public int hashCode() {
        return 31 * cents + currency.hashCode();
    }

    @Override
    public String toString() {
        return currency + " " + (cents / 100.0);
    }
}

Money m1 = new Money(500, "USD");
Money m2 = new Money(500, "USD");
Money m3 = new Money(500, "EUR");

System.out.println(m1.equals(m2));   // true — value equality
System.out.println(m1.equals(m3));   // false — different currency
System.out.println(m1.equals(null)); // false — null safe
System.out.println(m1);              // USD 5.0
```

**What this does:** Correct `equals()` checks: self-equality shortcut, null/type guard via `instanceof`, field comparison. `hashCode()` combines the same fields using 31-based prime mixing.

### Code Example 3 — hashCode contract in action (HashMap)

```java
import java.util.HashMap;

// WITHOUT hashCode override — broken behavior
public class BadKey {
    int id;
    BadKey(int id) { this.id = id; }

    @Override
    public boolean equals(Object obj) {
        if (!(obj instanceof BadKey)) return false;
        return this.id == ((BadKey) obj).id;
    }
    // hashCode NOT overridden — default memory-based hash
}

HashMap<BadKey, String> map = new HashMap<>();
BadKey k1 = new BadKey(42);
map.put(k1, "found");

BadKey k2 = new BadKey(42);          // equals(k1) is true
System.out.println(map.get(k2));     // null! — wrong bucket due to different hashCode

// ─────────────────────────────────────────────────────
// WITH both overridden — correct behavior
public class GoodKey {
    int id;
    GoodKey(int id) { this.id = id; }

    @Override
    public boolean equals(Object obj) {
        if (!(obj instanceof GoodKey)) return false;
        return this.id == ((GoodKey) obj).id;
    }

    @Override
    public int hashCode() { return Integer.hashCode(id); }
}

HashMap<GoodKey, String> map2 = new HashMap<>();
GoodKey g1 = new GoodKey(42);
map2.put(g1, "found");

GoodKey g2 = new GoodKey(42);
System.out.println(map2.get(g2));   // "found" — same bucket, equals match
```

**What this does:** `HashMap` first uses `hashCode()` to find the bucket, then `equals()` to confirm. If `hashCode()` returns different values for equal objects, they land in different buckets and `get()` returns `null` even though logically the key exists.

### Dry Run — HashMap lookup with hashCode + equals

```
map.put(k1, "found"):
  Step 1: k1.hashCode() = 12345  → bucket 45 (12345 % buckets)
  Step 2: store entry (k1, "found") in bucket 45

map.get(k2)  [k1.equals(k2) is true, but hashCode different]
  Step 1: k2.hashCode() = 98765  → bucket 17  ← WRONG bucket!
  Step 2: bucket 17 is empty → return null    ← key "not found"

map.get(g2)  [g1.equals(g2) is true, hashCode equal]
  Step 1: g2.hashCode() = 42      → bucket 2
  Step 2: bucket 2 has (g1,"found"); g1.equals(g2) → true → return "found"
```

### Code Example 4 — clone() and shallow copy danger

```java
import java.util.ArrayList;
import java.util.List;

public class Team implements Cloneable {
    String name;
    List<String> members;   // mutable reference field

    Team(String name) {
        this.name    = name;
        this.members = new ArrayList<>();
    }

    @Override
    protected Object clone() throws CloneNotSupportedException {
        return super.clone();   // SHALLOW clone — members list is shared!
    }
}

Team original = new Team("Alpha");
original.members.add("Alice");
original.members.add("Bob");

Team copy = (Team) original.clone();   // shallow clone
copy.members.add("Charlie");           // mutates SHARED list!

System.out.println(original.members);  // [Alice, Bob, Charlie] — unexpected!

// Deep clone fix:
public class TeamDeep implements Cloneable {
    String name;
    List<String> members;

    TeamDeep(String name) {
        this.name    = name;
        this.members = new ArrayList<>();
    }

    @Override
    protected TeamDeep clone() throws CloneNotSupportedException {
        TeamDeep copy    = (TeamDeep) super.clone();
        copy.members = new ArrayList<>(this.members);  // copy the list too
        return copy;
    }
}
```

**What this does:** `super.clone()` copies field values — for reference fields, it copies the reference, not the pointed-to object. Both `original` and `copy` share the same `List` object. Deep cloning means separately copying every mutable reference field.

### Code Example 5 — getClass() vs instanceof

```java
Dog  d = new Dog("Rex", 3, "Husky");
Animal a = d;

System.out.println(d.getClass());              // class Dog
System.out.println(d.getClass().getSimpleName()); // Dog
System.out.println(a.getClass().getSimpleName()); // Dog — runtime type!
System.out.println(a.getClass() == Dog.class);    // true

// instanceof checks IS-A (includes supertypes)
System.out.println(d instanceof Dog);     // true
System.out.println(d instanceof Animal);  // true  (IS-A holds)

// getClass() checks EXACT runtime type
System.out.println(d.getClass() == Animal.class);  // false (exact type is Dog)
System.out.println(d.getClass() == Dog.class);     // true
```

**What this does:** `instanceof` returns `true` for the actual type and all supertypes. `getClass() ==` is a strict exact-type check. In `equals()`, using `getClass() == obj.getClass()` enforces that equals only holds between objects of the exact same class (not subclasses), whereas `instanceof` allows subtype equality.

> ⚠️ **Pitfall:** Using `getClass()` in `equals()` (strict) vs `instanceof` (lenient) is a design choice with consequences. `instanceof` breaks the symmetric contract when subclasses add fields and override equals with different logic: `animal.equals(dog)` might return `true` but `dog.equals(animal)` might return `false`. Using `getClass()` avoids this asymmetry.

> ⚠️ **Pitfall:** `Objects.equals(a, b)` from `java.util.Objects` (note the s) handles null safely: `Objects.equals(null, null)` returns `true`, `Objects.equals(null, "x")` returns `false`. Prefer this over `a.equals(b)` when either side might be `null`.

---

## Full equals + hashCode + toString Implementation

```java
import java.util.Objects;

public final class Point {
    private final int x;
    private final int y;

    public Point(int x, int y) {
        this.x = x;
        this.y = y;
    }

    public int getX() { return x; }
    public int getY() { return y; }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (!(obj instanceof Point)) return false;
        Point other = (Point) obj;
        return this.x == other.x && this.y == other.y;
    }

    @Override
    public int hashCode() {
        return Objects.hash(x, y);    // uses prime multiplication internally
    }

    @Override
    public String toString() {
        return "Point(" + x + ", " + y + ")";
    }
}

// Verification
Point p1 = new Point(3, 4);
Point p2 = new Point(3, 4);
Point p3 = new Point(0, 0);

// equals
System.out.println(p1.equals(p2));   // true
System.out.println(p1.equals(p3));   // false
System.out.println(p1.equals(null)); // false

// hashCode consistent with equals
System.out.println(p1.hashCode() == p2.hashCode());  // true (required)
System.out.println(p1.hashCode() == p3.hashCode());  // likely false (not required to differ)

// toString
System.out.println(p1);   // Point(3, 4)

// Works correctly in collections
Set<Point> set = new HashSet<>();
set.add(p1);
System.out.println(set.contains(p2));   // true — hashCode + equals both correct
```

**What this does:** A complete, correct value-type implementation. `Objects.hash(x, y)` is shorthand that internally applies prime-multiplied hashing across the arguments. Declaring the class `final` avoids the equals-symmetry problem with subclasses.

---

## Quick Reference Summary

```
Topic                Key Rule
-------------------  -------------------------------------------------------
extends              IS-A; single parent; inherits public + protected members
super()              must be first stmt; implicit no-arg if not written
super.method()       call parent's version; avoids infinite recursion
@Override            always annotate overrides; compile checks signature
Overloading          same class, different params; compile-time dispatch
Overriding           same signature in child; runtime dispatch
final class          no subclassing (String, Integer)
final method         no overriding
final variable       assign once; field in constructor; local before use
Effectively final    [Java 8+] not declared final but never reassigned
instanceof null      always false, never NPE
Pattern matching     [Java 16+] if (obj instanceof Type var) — no cast needed
equals() contract    reflexive, symmetric, transitive, consistent, null-safe
hashCode() contract  equal objects → equal hash (MUST); override both together
clone() shallow      copies references, not pointed-to objects
getClass() vs instanceof  exact type vs IS-A check
```
