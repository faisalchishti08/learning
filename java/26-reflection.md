# Java Reflection

## Overview

Reflection (`java.lang.reflect`) lets code inspect and manipulate classes, methods, fields, and constructors at runtime — without knowing them at compile time. Used by frameworks (Spring, Hibernate, JUnit), serialization libraries, and dependency injection containers.

---

## 1. Class Object — the Entry Point

### Visual Diagram

```
Every type in Java has exactly one Class<?> object:

  String.class          ← class literal
  "hello".getClass()    ← from instance
  Class.forName("java.lang.String")  ← by name (dynamic)
  int.class             ← primitives have Class objects
  int[].class           ← arrays too

Class object gives access to:
  ├── getName(), getSimpleName(), getPackageName()
  ├── getSuperclass(), getInterfaces()
  ├── getFields() / getDeclaredFields()       public vs all
  ├── getMethods() / getDeclaredMethods()     public vs all (incl. private)
  ├── getConstructors() / getDeclaredConstructors()
  ├── getAnnotations() / getDeclaredAnnotations()
  └── isInterface(), isEnum(), isRecord(), isArray(), isPrimitive()

getDeclaredXxx()  → all (public + private + protected + package), THIS class only
getXxx()          → public only, includes INHERITED
```

### Example 1 — Inspecting a Class

```java
import java.lang.reflect.*;
import java.util.*;

public class ClassInspection {
    record Point(int x, int y) {}

    static class Animal {
        protected String name;
        public Animal(String name) { this.name = name; }
        public String speak() { return "..."; }
    }

    static class Dog extends Animal {
        private int age;
        public Dog(String name, int age) { super(name); this.age = age; }
        @Override public String speak() { return "Woof"; }
        private void fetch() { System.out.println("fetching!"); }
    }

    public static void main(String[] args) {
        Class<?> cls = Dog.class;

        System.out.println("Name: " + cls.getName());             // ...Dog
        System.out.println("Simple: " + cls.getSimpleName());     // Dog
        System.out.println("Super: " + cls.getSuperclass().getSimpleName()); // Animal

        // Interfaces
        System.out.println("Interfaces: " + Arrays.toString(cls.getInterfaces()));

        // Fields (declared = this class only, including private)
        System.out.println("\nDeclared fields:");
        for (Field f : cls.getDeclaredFields()) {
            System.out.println("  " + f.getType().getSimpleName() + " " + f.getName()
                + " [" + Modifier.toString(f.getModifiers()) + "]");
        }
        // int age [private]

        // All public fields including inherited
        System.out.println("\nAll public fields:");
        for (Field f : cls.getFields()) {
            System.out.println("  " + f.getName()); // none — name is protected
        }

        // Methods
        System.out.println("\nDeclared methods:");
        for (Method m : cls.getDeclaredMethods()) {
            System.out.println("  " + m.getName() + "() returns " + m.getReturnType().getSimpleName());
        }

        // Records
        Class<?> pCls = Point.class;
        System.out.println("Is record: " + pCls.isRecord()); // true
        for (RecordComponent rc : pCls.getRecordComponents()) {
            System.out.println("  component: " + rc.getName() + " : " + rc.getType().getSimpleName());
        }
    }
}
```

**What this does:** `getDeclaredFields()` reveals private fields. `getFields()` only returns public (including inherited). `getDeclaredMethods()` reveals private methods. Records expose `getRecordComponents()` [Java 16+].

---

## 2. Instantiation and Method Invocation

### Example 1 — Create Instances at Runtime

```java
import java.lang.reflect.*;

public class DynamicCreation {
    static class Config {
        private String host;
        private int port;

        public Config() { this.host = "localhost"; this.port = 8080; }
        public Config(String host, int port) { this.host = host; this.port = port; }
        @Override public String toString() { return host + ":" + port; }
    }

    public static void main(String[] args) throws Exception {
        // Get class by name (dynamic — class name from config/user input)
        Class<?> cls = Class.forName("DynamicCreation$Config");

        // Invoke no-arg constructor
        Constructor<?> noArg = cls.getConstructor(); // public no-arg
        Object obj1 = noArg.newInstance();
        System.out.println(obj1); // localhost:8080

        // Invoke specific constructor
        Constructor<?> twoArg = cls.getConstructor(String.class, int.class);
        Object obj2 = twoArg.newInstance("example.com", 443);
        System.out.println(obj2); // example.com:443

        // getDeclaredConstructors — includes private constructors
        for (Constructor<?> c : cls.getDeclaredConstructors()) {
            System.out.println("Constructor: " + Arrays.toString(c.getParameterTypes()));
        }
    }
}
```

**What this does:** `Class.forName("name")` loads a class by string name — the foundation of plugin systems and DI containers. `getConstructor(types)` finds the matching constructor; `newInstance()` invokes it.

### Example 2 — Invoke Methods Dynamically

```java
import java.lang.reflect.*;

public class MethodInvocation {
    static class Calculator {
        public int add(int a, int b) { return a + b; }
        private int multiply(int a, int b) { return a * b; }
        public static String describe() { return "Java Calculator"; }
    }

    public static void main(String[] args) throws Exception {
        Calculator calc = new Calculator();

        // Invoke public method
        Method addMethod = Calculator.class.getMethod("add", int.class, int.class);
        Object result = addMethod.invoke(calc, 3, 4);
        System.out.println("add: " + result); // 7

        // Invoke private method — need setAccessible(true)
        Method multiplyMethod = Calculator.class.getDeclaredMethod("multiply", int.class, int.class);
        multiplyMethod.setAccessible(true); // bypasses access checks
        Object product = multiplyMethod.invoke(calc, 5, 6);
        System.out.println("multiply: " + product); // 30

        // Invoke static method (pass null as instance)
        Method describeMethod = Calculator.class.getMethod("describe");
        Object desc = describeMethod.invoke(null); // null for static
        System.out.println("describe: " + desc); // Java Calculator
    }
}
```

**What this does:** `setAccessible(true)` bypasses Java's access control — allows invoking private methods. Used by test frameworks (JUnit), mocking libraries, and serialization engines. In Java 9+ modules, this may require `--add-opens`.

### Dry Run — Method.invoke()

```
addMethod.invoke(calc, 3, 4):
  1. Look up method "add" with params (int, int) on Calculator class
  2. Check access (public — no setAccessible needed)
  3. Box arguments: 3 → Integer(3), 4 → Integer(4)
  4. Call calc.add(3, 4) via JVM intrinsics
  5. Box return: 7 → Integer(7)
  6. Return Integer(7) as Object

Cost: ~10x slower than direct call due to boxing, access checks, reflection overhead
Tip: cache Method objects — getDeclaredMethod() is expensive; invoke() is cheaper
```

---

## 3. Field Access

### Example 1 — Read and Write Fields

```java
import java.lang.reflect.*;

public class FieldAccess {
    static class Person {
        public String name;
        private int age;
        private final String id; // final!

        Person(String name, int age, String id) {
            this.name = name; this.age = age; this.id = id;
        }
        @Override public String toString() { return name + "/" + age + "/" + id; }
    }

    public static void main(String[] args) throws Exception {
        Person p = new Person("Alice", 30, "ID-001");

        // Public field
        Field nameField = Person.class.getField("name");
        System.out.println(nameField.get(p)); // Alice
        nameField.set(p, "Bob");
        System.out.println(nameField.get(p)); // Bob

        // Private field
        Field ageField = Person.class.getDeclaredField("age");
        ageField.setAccessible(true);
        System.out.println(ageField.get(p)); // 30
        ageField.set(p, 99);
        System.out.println(ageField.get(p)); // 99

        // Final field — can be modified via reflection! (dangerous)
        Field idField = Person.class.getDeclaredField("id");
        idField.setAccessible(true);
        idField.set(p, "HACKED"); // modifies final field
        System.out.println(p); // Bob/99/HACKED

        System.out.println(p);
    }
}
```

**What this does:** `setAccessible(true)` also works on fields — including private and final fields. This is how serialization libraries populate objects without constructors.

> ⚠️ **Pitfall:** Modifying `final` fields via reflection produces undefined behavior for primitives/Strings due to constant folding. The field value changes but code that used the old value may have been inlined by JIT. Avoid in production code.

---

## 4. Annotations via Reflection

### Example 1 — Custom Annotation Processing

```java
import java.lang.annotation.*;
import java.lang.reflect.*;

public class AnnotationReflection {
    @Retention(RetentionPolicy.RUNTIME) // must be RUNTIME to be visible via reflection
    @Target(ElementType.METHOD)
    @interface Test {
        String name() default "";
        boolean skip() default false;
    }

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.FIELD)
    @interface Required {}

    static class MyTests {
        @Test(name = "addition")
        public void testAdd() { System.out.println("test: addition OK"); }

        @Test(name = "subtraction", skip = true)
        public void testSubtract() { System.out.println("test: subtraction SKIPPED"); }

        @Test
        public void testMultiply() { System.out.println("test: multiply OK"); }

        public void helperMethod() { System.out.println("not a test"); }
    }

    // Simple test runner
    static void runTests(Object obj) throws Exception {
        for (Method m : obj.getClass().getDeclaredMethods()) {
            if (m.isAnnotationPresent(Test.class)) {
                Test ann = m.getAnnotation(Test.class);
                if (ann.skip()) {
                    System.out.println("SKIP: " + (ann.name().isEmpty() ? m.getName() : ann.name()));
                } else {
                    System.out.print("RUN:  ");
                    m.invoke(obj);
                }
            }
        }
    }

    public static void main(String[] args) throws Exception {
        runTests(new MyTests());
        // RUN:  test: addition OK
        // SKIP: subtraction
        // RUN:  test: multiply OK
    }
}
```

**What this does:** This is exactly how JUnit 4 works — scan methods for `@Test` annotation, invoke them. `RetentionPolicy.RUNTIME` is required for reflection to see annotations. `RetentionPolicy.CLASS` (default) stores in bytecode but not accessible at runtime.

---

## 5. Generic Type Information

### Example 1 — Extracting Generic Types

```java
import java.lang.reflect.*;
import java.util.*;

public class GenericReflection {
    static class DataService {
        public List<String> getNames() { return List.of("a"); }
        public Map<String, Integer> getScores() { return Map.of("a", 1); }
    }

    public static void main(String[] args) throws Exception {
        Method getNamesMethod = DataService.class.getMethod("getNames");
        Type returnType = getNamesMethod.getGenericReturnType();

        if (returnType instanceof ParameterizedType pt) { // pattern matching [Java 16+]
            System.out.println("Raw type: " + pt.getRawType());
            // interface java.util.List
            System.out.println("Type arg: " + pt.getActualTypeArguments()[0]);
            // class java.lang.String
        }

        Method getScoresMethod = DataService.class.getMethod("getScores");
        ParameterizedType mapType = (ParameterizedType) getScoresMethod.getGenericReturnType();
        Type[] args2 = mapType.getActualTypeArguments();
        System.out.println("Map<" + args2[0] + ", " + args2[1] + ">"); // Map<String, Integer>
    }
}
```

**What this does:** Generic type information is erased at runtime for variables/casts, but **method/field signatures retain generic type info in bytecode**. `getGenericReturnType()` exposes this — used by Jackson to deserialize `List<String>` correctly.

---

## 6. Proxy — Dynamic Interface Implementation

### Example 1 — Dynamic Proxy (AOP concept)

```java
import java.lang.reflect.*;

public class DynamicProxyDemo {
    interface Greeter {
        String greet(String name);
        void log(String msg);
    }

    static class RealGreeter implements Greeter {
        @Override public String greet(String name) { return "Hello, " + name; }
        @Override public void log(String msg) { System.out.println("LOG: " + msg); }
    }

    // Timing InvocationHandler
    static class TimingHandler implements InvocationHandler {
        private final Object target;
        TimingHandler(Object target) { this.target = target; }

        @Override
        public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
            long start = System.nanoTime();
            Object result = method.invoke(target, args); // call real method
            long elapsed = System.nanoTime() - start;
            System.out.printf("Method %s took %dµs%n", method.getName(), elapsed / 1000);
            return result;
        }
    }

    public static void main(String[] args) {
        Greeter real = new RealGreeter();
        Greeter proxy = (Greeter) Proxy.newProxyInstance(
            Greeter.class.getClassLoader(),
            new Class<?>[]{ Greeter.class },
            new TimingHandler(real)
        );

        System.out.println(proxy.greet("Alice")); // Hello, Alice + timing
        proxy.log("test message");                 // LOG: test + timing
    }
}
```

**What this does:** `Proxy.newProxyInstance` creates a runtime-generated class that implements the target interface. Every method call goes through the `InvocationHandler`. This is how Spring AOP, transaction management, and Mockito work.

---

## Quick Reference

```
Class<?> entry points:
  String.class                          class literal
  obj.getClass()                        from instance
  Class.forName("pkg.ClassName")        dynamic load

Inspection:
  cls.getDeclaredFields()               all fields (this class)
  cls.getDeclaredMethods()              all methods (this class)
  cls.getDeclaredConstructors()         all constructors (this class)
  cls.getFields/Methods/Constructors()  public only, including inherited

Access bypass:
  field.setAccessible(true)             bypass private/final
  method.setAccessible(true)            bypass private

Invocation:
  method.invoke(obj, args...)           call method
  constructor.newInstance(args...)      create instance
  field.get(obj) / field.set(obj, val)  read/write field

Annotations:
  cls.isAnnotationPresent(Ann.class)    check annotation
  cls.getAnnotation(Ann.class)          get annotation instance
  @Retention(RUNTIME)                   required for reflection visibility

Generics:
  method.getGenericReturnType()         includes generic info
  field.getGenericType()                includes generic info
  ((ParameterizedType)t).getActualTypeArguments()  extract type args

Dynamic Proxy:
  Proxy.newProxyInstance(loader, interfaces[], handler)
  implements InvocationHandler.invoke(proxy, method, args)
```
