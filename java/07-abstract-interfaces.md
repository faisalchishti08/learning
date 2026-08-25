# Java Abstract Classes and Interfaces

---

## 1. Abstract Classes

### What and Why

An **abstract class** is a class that cannot be instantiated directly. It exists to be extended. It can hold shared fields and concrete (fully implemented) methods that all subclasses inherit, while also declaring abstract methods that each subclass *must* provide its own implementation of.

**Why it exists:** Sometimes you want to define a partial blueprint. A `Shape` knows how to `toString()` itself and has a `color` field, but it cannot meaningfully compute its own `area()` — only `Circle` and `Rectangle` can do that. Abstract classes encode exactly that split: "here is the shared code, here is the contract you must fulfill."

```
┌─────────────────────────────────┐
│       <<abstract>> Shape        │
│─────────────────────────────────│
│ - color: String                 │  ← concrete field
│─────────────────────────────────│
│ + getColor(): String   [conc.]  │  ← concrete method (shared)
│ + describe(): void     [conc.]  │  ← concrete method (shared)
│ + area(): double       [abst.]  │  ← ABSTRACT — no body here
└─────────────┬───────────────────┘
              │ extends
    ┌─────────┴──────────┐
    │                    │
┌───▼──────┐      ┌──────▼──────┐
│  Circle  │      │  Rectangle  │
│──────────│      │─────────────│
│ r: double│      │ w,h: double │
│──────────│      │─────────────│
│ area()   │      │ area()      │  ← each provides its own body
└──────────┘      └─────────────┘
```

### Example 1 — Minimal abstract class

```java
abstract class Shape {
    private String color;

    Shape(String color) {          // abstract classes CAN have constructors
        this.color = color;        // called via super() from subclass
    }

    String getColor() {            // concrete — all subclasses inherit this
        return color;
    }

    abstract double area();        // no body — subclasses must override
}

class Circle extends Shape {
    private double radius;

    Circle(String color, double radius) {
        super(color);              // calls Shape's constructor
        this.radius = radius;
    }

    @Override
    double area() {
        return Math.PI * radius * radius;
    }
}
```

**What this does:** `Shape` cannot be created with `new Shape(...)` — compiler error. `Circle` extends it, calls `super(color)` to initialize the shared field, and provides the required `area()` implementation.

> ⚠️ **Pitfall:** Forgetting `super(color)` in the subclass constructor leaves `color` uninitialized (null for String). Abstract classes with constructors must have their constructor explicitly chained via `super()` from every concrete subclass.

---

### Example 2 — Concrete + abstract methods combined

```java
abstract class Vehicle {
    private String brand;
    private int year;

    Vehicle(String brand, int year) {
        this.brand = brand;
        this.year = year;
    }

    // concrete: shared logic
    void describe() {
        System.out.println(brand + " (" + year + ") — " + fuelType());
    }

    // concrete: shared logic
    int age() {
        return 2026 - year;
    }

    // abstract: each vehicle type knows its own fuel
    abstract String fuelType();

    // abstract: each vehicle type has different max speed
    abstract int maxSpeedKph();
}

class ElectricCar extends Vehicle {
    ElectricCar(String brand, int year) { super(brand, year); }

    @Override String fuelType()     { return "Electric"; }
    @Override int maxSpeedKph()     { return 250; }
}

class DieselTruck extends Vehicle {
    DieselTruck(String brand, int year) { super(brand, year); }

    @Override String fuelType()     { return "Diesel"; }
    @Override int maxSpeedKph()     { return 140; }
}
```

**What this does:** `describe()` is concrete and calls `fuelType()`, which is abstract. This is the **Template Method** pattern — the abstract class controls the algorithm skeleton, subclasses fill in the blanks.

---

### Example 3 — Abstract class with state and partial override

```java
abstract class Employee {
    protected String name;
    protected double baseSalary;

    Employee(String name, double baseSalary) {
        this.name = name;
        this.baseSalary = baseSalary;
    }

    abstract double bonus();          // each type calculates differently

    double totalCompensation() {       // final shape of the formula is shared
        return baseSalary + bonus();
    }

    void printPayslip() {
        System.out.printf("%s: base=%.0f bonus=%.0f total=%.0f%n",
            name, baseSalary, bonus(), totalCompensation());
    }
}

class SalesEmployee extends Employee {
    private double salesRevenue;

    SalesEmployee(String name, double base, double revenue) {
        super(name, base);
        this.salesRevenue = revenue;
    }

    @Override
    double bonus() { return salesRevenue * 0.05; }  // 5% of sales
}

class Engineer extends Employee {
    private int performanceRating;    // 1–5

    Engineer(String name, double base, int rating) {
        super(name, base);
        this.performanceRating = rating;
    }

    @Override
    double bonus() { return baseSalary * 0.10 * performanceRating; }
}
```

**What this does:** `totalCompensation()` and `printPayslip()` are concrete and reused. The variation point — `bonus()` — is abstract. Each subclass wires in its own formula.

#### Dry Run — `printPayslip()` for `SalesEmployee`

| Step | Code executed | Value |
|------|---------------|-------|
| 1 | `new SalesEmployee("Alice", 60000, 200000)` | `name="Alice"`, `baseSalary=60000`, `salesRevenue=200000` |
| 2 | `printPayslip()` calls `bonus()` | dispatches to `SalesEmployee.bonus()` |
| 3 | `bonus()` → `200000 * 0.05` | `10000.0` |
| 4 | `totalCompensation()` → `60000 + 10000` | `70000.0` |
| 5 | `printf` formats and prints | `Alice: base=60000 bonus=10000 total=70000` |

---

### Example 4 — Abstract class extending another abstract class

```java
abstract class Animal {
    abstract void breathe();
    void sleep() { System.out.println("zzz"); }
}

abstract class Mammal extends Animal {
    @Override
    void breathe() { System.out.println("inhale air"); }  // satisfies Animal
    abstract void feedYoung();                              // adds new contract
}

class Dog extends Mammal {
    @Override
    void feedYoung() { System.out.println("nurse pups"); }
    // breathe() inherited from Mammal, sleep() from Animal
}
```

**What this does:** An abstract class can extend another abstract class and choose *which* abstract methods to implement. `Dog` only needs to satisfy the one remaining abstract method.

> ⚠️ **Pitfall:** If `Dog` fails to implement `feedYoung()`, the compiler will refuse to compile it unless `Dog` is also declared `abstract`.

---

## 2. Interfaces — Pre-Java 8

### What and Why

An **interface** is a pure contract. Before Java 8, it could contain *only* method signatures (implicitly `public abstract`) and constants (implicitly `public static final`). Every implementing class must provide bodies for every method.

**Why multiple interfaces matter:** Java permits only single class inheritance (`extends` one class). But a class can `implement` any number of interfaces. This enables **capability composition** — a `Duck` can be both `Flyable` and `Swimmable` without any inheritance hierarchy conflict.

```
              ┌─────────────────┐
              │  <<interface>>  │
              │    Printable    │
              │─────────────────│
              │ + print(): void │
              └────────┬────────┘
                       │ implements
          ┌────────────┼────────────┐
          │                         │
┌─────────▼────────┐      ┌─────────▼──────────┐
│    Invoice       │      │    ReportDocument   │
│──────────────────│      │────────────────────│
│ (unrelated hier.)│      │ (unrelated hier.)   │
│ + print(): void  │      │ + print(): void     │
└──────────────────┘      └────────────────────┘
```

### Example 1 — Basic contract

```java
interface Drawable {
    int MAX_SIZE = 1000;      // implicitly public static final
    void draw();              // implicitly public abstract
    void resize(int factor);  // implicitly public abstract
}

class Square implements Drawable {
    private int side;
    Square(int side) { this.side = side; }

    @Override
    public void draw()              { System.out.println("Drawing square " + side); }

    @Override
    public void resize(int factor)  { side *= factor; }
}
```

**What this does:** `Square` is forced to implement both `draw()` and `resize()`. `MAX_SIZE` is shared across all implementors as a constant.

> ⚠️ **Pitfall:** Interface methods are implicitly `public`. If you implement them without `public` in the class body, the compiler complains because you'd be reducing visibility (a class method can't be less visible than the interface method).

---

### Example 2 — Multiple interface implementation

```java
interface Flyable {
    void fly();
}

interface Swimmable {
    void swim();
}

interface Runnable {          // not java.lang.Runnable — just an example
    void run();
}

class Duck implements Flyable, Swimmable, Runnable {
    @Override public void fly()  { System.out.println("Duck flaps wings"); }
    @Override public void swim() { System.out.println("Duck paddles"); }
    @Override public void run()  { System.out.println("Duck waddles"); }
}

class Penguin implements Swimmable, Runnable {
    @Override public void swim() { System.out.println("Penguin torpedoes"); }
    @Override public void run()  { System.out.println("Penguin shuffles"); }
}
```

**What this does:** `Duck` and `Penguin` share no inheritance hierarchy, yet both can be referenced as `Swimmable`. Code that only cares about swimming can treat both identically.

---

### Example 3 — Interface as parameter type (polymorphism)

```java
interface Sortable {
    int compareTo(Object other);
}

class Temperature implements Sortable {
    double celsius;
    Temperature(double c) { this.celsius = c; }

    @Override
    public int compareTo(Object other) {
        Temperature t = (Temperature) other;
        return Double.compare(this.celsius, t.celsius);
    }
}

class Utility {
    static void printOrdered(Sortable a, Sortable b) {
        if (a.compareTo(b) <= 0)
            System.out.println(a + " comes first");
        else
            System.out.println(b + " comes first");
    }
}
```

**What this does:** `Utility.printOrdered` works for *any* class that implements `Sortable` — it has no knowledge of `Temperature`. This is the core power of interface-based programming.

---

## 3. Interfaces — Post-Java 8 (`default` and `static`)

### What and Why

Java 8 had to add `forEach()`, `stream()`, `sort()` etc. to `Collection`, `List`, `Iterable` without breaking the millions of existing implementations. The solution: **default methods** — interface methods with a body that serve as a fallback. Implementing classes that don't override them inherit the default body.

**`static` methods** on interfaces serve as utility/factory helpers scoped to the interface (e.g., `Comparator.comparing(...)`).

```
┌──────────────────────────────────────────┐
│           <<interface>> Validator        │
│──────────────────────────────────────────│
│ + validate(String): boolean  [abstract]  │
│ + isValid(String): boolean   [default]   │  ← has a body
│ + of(String): Validator      [static]    │  ← utility factory
└───────────┬──────────────────────────────┘
            │ implements (inherits default)
┌───────────▼───────────┐  ┌────────────────────────┐
│    EmailValidator     │  │   PhoneValidator        │
│       overrides       │  │  inherits default isValid│
│       validate()      │  └────────────────────────┘
└───────────────────────┘
```

### Example 1 — `default` method

```java
interface Greeting {
    String greet(String name);                      // abstract

    default String greetFormally(String name) {     // default — has body
        return "Dear " + name + ", " + greet(name);
    }
}

class CasualGreeting implements Greeting {
    @Override
    public String greet(String name) { return "Hey " + name + "!"; }
    // greetFormally() inherited for free
}

class FrenchGreeting implements Greeting {
    @Override
    public String greet(String name) { return "Bonjour " + name; }

    @Override
    public String greetFormally(String name) {   // overrides the default
        return "Monsieur/Madame " + name + ", " + greet(name);
    }
}
```

**What this does:** `CasualGreeting` gets `greetFormally()` without implementing it. `FrenchGreeting` customizes it. If a future version of `Greeting` adds another `default` method, neither class breaks.

---

### Example 2 — `static` method on interface

```java
interface MathOp {
    int apply(int a, int b);                       // abstract

    static MathOp add()      { return (a, b) -> a + b; }   // [Java 8+] lambda
    static MathOp multiply() { return (a, b) -> a * b; }

    default MathOp andThen(MathOp next) {          // default method
        return (a, b) -> next.apply(this.apply(a, b), b);
    }
}

// Usage
MathOp doubleAdd = MathOp.add().andThen(MathOp.add());   // (a+b)+b
System.out.println(doubleAdd.apply(3, 4));  // (3+4)+4 = 11
```

**What this does:** `MathOp.add()` is called on the interface name, not on an instance. It returns a ready-made implementation. `andThen` is a default method that chains operations.

#### Dry Run — `doubleAdd.apply(3, 4)`

| Step | Expression | Value |
|------|-----------|-------|
| 1 | `MathOp.add()` returns | `(a,b) -> a+b` |
| 2 | `.andThen(MathOp.add())` wraps it | `(a,b) -> outerAdd.apply(a,b) + b` wait — `next.apply(this.apply(a,b), b)` |
| 3 | `doubleAdd.apply(3, 4)` → `this.apply(3,4)` | `3+4 = 7` |
| 4 | `next.apply(7, 4)` | `7+4 = 11` |
| 5 | Result | `11` |

---

### Example 3 — Evolving an existing interface safely

```java
// Before Java 8 — adding a new method here would break ALL implementations
interface DataProcessor {
    void process(String data);

    // Added in a later version — default prevents breaking change
    default void processAll(String[] items) {
        for (String item : items) process(item);
    }

    default String preprocess(String data) {
        return data.trim().toLowerCase();
    }
}

class LogProcessor implements DataProcessor {
    @Override
    public void process(String data) {
        System.out.println("LOG: " + data);
    }
    // processAll() and preprocess() inherited, no code change needed
}

class ValidatingProcessor implements DataProcessor {
    @Override
    public void process(String data) {
        String clean = preprocess(data);   // uses inherited default
        if (!clean.isEmpty()) System.out.println("VALID: " + clean);
    }
}
```

**What this does:** `LogProcessor` was written before `processAll()` existed. Adding it as a `default` means `LogProcessor` compiles and runs unchanged while automatically gaining the new capability.

> ⚠️ **Pitfall:** A default method silently changes behavior for all implementors that don't override it. If `processAll()` has a bug, every implementing class is affected. Default methods are for backward compatibility, not primary behavior.

---

## 4. Private Interface Methods [Java 9+]

### What and Why

When multiple `default` methods share helper logic, there was no clean way to extract it before Java 9 — you'd have to duplicate the helper code or make it `public` (exposing internal logic). **Private interface methods** solve this: extract shared logic into a non-visible helper that only the interface's own `default`/`static` methods can call.

```
┌────────────────────────────────────────────────────┐
│           <<interface>> Logger [Java 9+]           │
│────────────────────────────────────────────────────│
│ + logInfo(String): void      [default]             │
│ + logWarning(String): void   [default]             │
│          ↓ both call ↓                             │
│ - formatMessage(String,String): String  [private]  │  ← NOT visible outside
└────────────────────────────────────────────────────┘
```

### Example 1 — Shared helper extracted to private method

```java
interface Logger {                                          // [Java 9+]
    void writeLog(String message);                         // abstract

    default void logInfo(String msg) {
        writeLog(formatMessage("INFO", msg));              // calls private helper
    }

    default void logWarning(String msg) {
        writeLog(formatMessage("WARN", msg));              // same private helper
    }

    default void logError(String msg) {
        writeLog(formatMessage("ERROR", msg));
    }

    private String formatMessage(String level, String msg) {   // private!
        return "[" + level + "] " + java.time.LocalTime.now() + " — " + msg;
    }
}

class ConsoleLogger implements Logger {
    @Override
    public void writeLog(String message) {
        System.out.println(message);
    }
    // all three default log methods inherited and working
}
```

**What this does:** Without `private formatMessage()`, the `[LEVEL] timestamp` format string would be duplicated in each `default` method. `formatMessage` is invisible to `ConsoleLogger` and callers — it's a pure internal concern of the interface.

---

### Example 2 — `private static` method for static helpers

```java
interface Validator {                                      // [Java 9+]
    boolean validate(String input);

    static Validator nonEmpty() {
        return input -> !sanitize(input).isEmpty();        // calls private static
    }

    static Validator maxLength(int max) {
        return input -> sanitize(input).length() <= max;
    }

    private static String sanitize(String input) {        // private static
        return input == null ? "" : input.trim();
    }

    default Validator and(Validator other) {
        return input -> this.validate(input) && other.validate(input);
    }
}

// Usage
Validator usernameValidator = Validator.nonEmpty().and(Validator.maxLength(20));
System.out.println(usernameValidator.validate("  alice  "));   // true
System.out.println(usernameValidator.validate(""));            // false
```

**What this does:** Both `nonEmpty()` and `maxLength()` need to sanitize input the same way. `private static sanitize()` centralizes that without making it part of the public API.

#### Dry Run — `usernameValidator.validate("  alice  ")`

| Step | Expression | Value |
|------|-----------|-------|
| 1 | `and(...)` returns composite | `input -> nonEmpty.validate(input) && maxLength.validate(input)` |
| 2 | Call `.validate("  alice  ")` | enters composite lambda |
| 3 | `nonEmpty.validate("  alice  ")` → `sanitize("  alice  ")` | `"alice"` |
| 4 | `"alice".isEmpty()` | `false`, so `!false = true` |
| 5 | `maxLength.validate("  alice  ")` → `sanitize(...)` | `"alice"` |
| 6 | `"alice".length() <= 20` | `5 <= 20 = true` |
| 7 | `true && true` | `true` |

> ⚠️ **Pitfall:** Private interface methods are *only* accessible within the interface itself. If you try to call `Validator.sanitize()` from outside the interface, it won't compile — it's not even visible. This is by design.

---

## 5. Interface vs Abstract Class — Decision Guide

### Core Differences Table

| Aspect | Abstract Class | Interface |
|--------|---------------|-----------|
| Instantiation | Cannot be instantiated directly | Cannot be instantiated directly |
| Fields | Can have instance fields (state) | Only `public static final` constants |
| Constructor | Yes — called via `super()` | No constructor |
| Method types | abstract + concrete (any visibility) | abstract, default, static, private [9+] |
| Inheritance | Single (`extends` one class) | Multiple (`implements` many) |
| Access modifiers | `private`, `protected`, `public` | All public (or `private` for helpers [9+]) |
| IS-A vs CAN-DO | IS-A relationship | CAN-DO capability |
| When to change | Shared implementation evolves | Contract evolves (default methods protect) |

### When to Choose Abstract Class

- Subclasses are strongly IS-A related ("a `Cat` IS-A `Animal`")
- You need shared **mutable state** (instance fields) across subclasses
- You need a **constructor** to enforce invariants
- You want `protected` methods callable only by subclasses
- Partial implementation: most methods shared, one or two vary

```java
// CORRECT use of abstract class: shared state + IS-A
abstract class BankAccount {
    protected double balance;         // shared state — interface can't do this
    protected String accountNumber;

    BankAccount(String accNum, double initialBalance) {  // enforced invariant
        if (initialBalance < 0) throw new IllegalArgumentException("negative balance");
        this.accountNumber = accNum;
        this.balance = initialBalance;
    }

    void deposit(double amount) { balance += amount; }  // shared concrete method

    abstract void withdraw(double amount);              // varies per account type
}
```

### When to Choose Interface

- Capability orthogonal to class hierarchy (`Serializable`, `Comparable`, `Runnable`)
- You need **multiple "inheritance"** of behavior
- You're defining a **callback contract** or plugin point
- The IS-A is not the right framing ("a `Timer` CAN-DO `Runnable`")

```java
// CORRECT use of interface: capability, multiple, unrelated hierarchies
interface Auditable {
    void auditEvent(String event, String user);

    default void auditCreate(String user) { auditEvent("CREATE", user); }
    default void auditDelete(String user) { auditEvent("DELETE", user); }
}

// Completely unrelated classes can both be Auditable
class Order       implements Auditable { ... }
class UserAccount implements Auditable { ... }
class FileAsset   implements Auditable { ... }
```

> ⚠️ **Pitfall:** Post-Java 8, interfaces can have default methods with implementation, which narrows the gap. The key remaining difference is **state** — interfaces cannot hold instance fields. If you need `protected double balance`, you need an abstract class.

---

## 6. Diamond Problem and Resolution

### What and Why

If two interfaces both declare a `default` method with the same signature, and a class implements both, which method does the class inherit? This is the **diamond problem**. Java requires the implementing class to **explicitly override** the conflicting method, and optionally delegate to a specific interface's default using `InterfaceName.super.method()`.

```
         ┌─────────────────────────┐
         │    <<interface>> A      │
         │  default greet():       │
         │    "Hello from A"       │
         └────────┬────────────────┘
                  │
       ┌──────────┴──────────┐
       │                     │
┌──────▼──────┐        ┌─────▼───────┐
│ <<i/f>> B   │        │ <<i/f>> C   │
│ default     │        │ default     │
│ greet():    │        │ greet():    │
│ "From B"    │        │ "From C"    │
└──────┬──────┘        └──────┬──────┘
       │                      │
       └──────────┬───────────┘
                  │ implements
           ┌──────▼──────┐
           │      D      │
           │  MUST override greet()  │
           └─────────────┘
```

### Example 1 — Two conflicting defaults

```java
interface Left {
    default String label() { return "LEFT"; }
}

interface Right {
    default String label() { return "RIGHT"; }
}

class Center implements Left, Right {
    @Override
    public String label() {
        // Must override — compiler forces it
        // Can delegate to either:
        return Left.super.label() + "+" + Right.super.label();
    }
}
```

**What this does:** `Left.super.label()` is the syntax for calling a specific interface's default method. Without the override, the compiler gives: *"class Center inherits unrelated defaults for label() from types Left and Right."*

---

### Example 2 — Three-level diamond with full resolution

```java
interface Vehicle {
    default String describe() { return "Vehicle"; }
}

interface Car extends Vehicle {
    @Override
    default String describe() { return "Car (via Vehicle)"; }
}

interface ElectricPowered extends Vehicle {
    @Override
    default String describe() { return "Electric (via Vehicle)"; }
}

// Tesla implements Car and ElectricPowered — conflict!
class Tesla implements Car, ElectricPowered {
    @Override
    public String describe() {
        // Prefer Car's version, append Electric info
        return Car.super.describe() + " + " + ElectricPowered.super.describe();
    }
}

// But if one interface extends another directly, it wins automatically:
interface SpecialCar extends Car {
    // inherits Car's describe() — more specific than Vehicle's
}
class Sedan implements SpecialCar, Vehicle {
    // NO conflict — Car.describe() is more specific, wins automatically
}
```

**What this does:** Java's rule: *more specific interface wins*. If `B extends A`, and both have a `default foo()`, then `B.foo()` wins automatically. Conflict only arises when neither interface is more specific than the other.

#### Dry Run — Conflict resolution rule lookup

| Scenario | Rule | Winner |
|----------|------|--------|
| `B extends A`, both have `default f()` | More specific wins | `B.f()` — no override needed |
| `B` and `C` unrelated, both have `default f()` | Tie — must override | Class must provide `f()` |
| Class has `f()`, interface has `default f()` | Class always wins | Class `f()` — no override needed |
| `B extends A`, class implements `A` too | `B` more specific | `B.f()` — no conflict |

> ⚠️ **Pitfall:** `InterfaceName.super.method()` syntax is *only* valid inside an implementing class or sub-interface. You cannot do `someVariable.InterfaceName.super.method()` — it's not a runtime dispatch, it's a compile-time qualifier inside the class body.

---

### Example 3 — Class implementation always beats interface default

```java
interface Describable {
    default String describe() { return "from interface"; }
}

class Base {
    public String describe() { return "from Base class"; }
}

class Child extends Base implements Describable {
    // No conflict! Class method always wins over interface default
    // Child.describe() → "from Base class"
}
```

**What this does:** A concrete method in a superclass always takes priority over an interface `default` method. This is Java's third rule for method resolution. No override needed in `Child`.

---

## 7. Functional Interfaces

### What and Why

A **functional interface** has exactly one abstract method (SAM = Single Abstract Method). This single method is the interface's "action." Functional interfaces are the entry point for **lambda expressions** and **method references** in Java — a lambda is a shorthand for an anonymous class implementing a functional interface.

The `@FunctionalInterface` annotation is optional but recommended: it instructs the compiler to error if someone accidentally adds a second abstract method.

```
┌─────────────────────────────────────────────┐
│    <<@FunctionalInterface>> Transformer<T>  │
│─────────────────────────────────────────────│
│ + transform(T): T         [abstract — SAM]  │  ← exactly 1 abstract
│ + identity(): Transformer [static]          │  ← static methods: OK
│ + andThen(Transformer): T [default]         │  ← default methods: OK
└─────────────────────────────────────────────┘
         ↑
         implemented by a lambda: t -> t.toUpperCase()
```

### Example 1 — Defining a functional interface

```java
@FunctionalInterface
interface StringTransformer {
    String transform(String input);            // SAM — exactly one abstract

    static StringTransformer identity() {      // static: allowed
        return s -> s;
    }

    default StringTransformer andThen(StringTransformer next) {  // default: allowed
        return s -> next.transform(this.transform(s));
    }
}

// Three ways to implement it:
// 1. Anonymous class (old way)
StringTransformer upper = new StringTransformer() {
    @Override public String transform(String s) { return s.toUpperCase(); }
};

// 2. Lambda (Java 8+)
StringTransformer trim = s -> s.trim();

// 3. Method reference (Java 8+)
StringTransformer reverse = s -> new StringBuilder(s).reverse().toString();
```

**What this does:** All three implementations are equivalent. The lambda is the shortest. Method reference would apply if the method signature matched exactly (see lambdas file).

---

### Example 2 — Built-in functional interfaces

```java
import java.util.function.*;

// Function<T,R> — takes T, returns R
Function<String, Integer> strLen = s -> s.length();
System.out.println(strLen.apply("hello"));     // 5

// Predicate<T> — takes T, returns boolean
Predicate<Integer> isEven = n -> n % 2 == 0;
System.out.println(isEven.test(4));            // true

// Consumer<T> — takes T, returns void
Consumer<String> printer = s -> System.out.println(">> " + s);
printer.accept("world");                       // >> world

// Supplier<T> — takes nothing, returns T
Supplier<Double> random = Math::random;
System.out.println(random.get());              // 0.something

// BiFunction<T,U,R> — takes T and U, returns R
BiFunction<String, Integer, String> repeat = (s, n) -> s.repeat(n);
System.out.println(repeat.apply("ab", 3));     // ababab
```

**What this does:** Java 8's `java.util.function` package provides ~43 ready-made functional interfaces covering all common SAM shapes. You rarely need to define your own.

---

### Example 3 — @FunctionalInterface enforces the contract

```java
@FunctionalInterface
interface Calculator {
    int calculate(int a, int b);    // SAM

    // Adding this would cause compile error:
    // int anotherCalc(int a);      // ERROR: multiple non-overriding abstract methods

    // These are fine alongside SAM:
    default Calculator negate() { return (a, b) -> -calculate(a, b); }
    static Calculator addition() { return (a, b) -> a + b; }
}

Calculator add = (a, b) -> a + b;
Calculator addNeg = add.negate();
System.out.println(add.calculate(3, 4));       // 7
System.out.println(addNeg.calculate(3, 4));    // -7
```

**What this does:** `@FunctionalInterface` is a safety net. Without it, someone might add a second abstract method and silently break all lambdas targeting that interface.

> ⚠️ **Pitfall:** `java.lang.Object` methods (`equals`, `hashCode`, `toString`) do NOT count toward the abstract method count. An interface can declare `boolean equals(Object o)` and still be functional — that declaration is considered "already implemented" by `Object`. Full lambda coverage: `13-lambdas.md`.

---

## Quick Reference

```
Abstract Class                  Interface (Java 8+)
──────────────────────────────  ──────────────────────────────────────────
abstract class Foo {            interface Bar {
  private int x;                  int CONST = 0;               // static final
  Foo(int x) { this.x = x; }     void abstractMethod();       // abstract
  void concrete() { ... }        default void d() { ... }     // default [8+]
  abstract void toImpl();        static void s() { ... }      // static [8+]
}                                private void p() { ... }     // private [9+]
                                 private static void ps() {}  // private static [9+]
                                }
```
