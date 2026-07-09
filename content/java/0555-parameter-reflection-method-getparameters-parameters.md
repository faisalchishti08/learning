---
card: java
gi: 555
slug: parameter-reflection-method-getparameters-parameters
title: Parameter reflection (Method.getParameters, -parameters)
---

## 1. What it is

Before Java 8, reflecting on a method's parameters gave you their types (`getParameterTypes()`) but never their **names** — compiled `.class` files simply didn't retain that information by default, so reflective code saw parameters only as `arg0`, `arg1`, and so on, if it needed to refer to them by name at all. `Method.getParameters()` (returning `Parameter[]`) exposes richer per-parameter information — including the actual source-code name, but *only* if the class was compiled with the `-parameters` javac flag, which explicitly tells the compiler to retain parameter names in the compiled bytecode.

## 2. Why & when

Frameworks that need to know a method's actual parameter names at runtime — dependency injection containers matching constructor parameters to bean names, JSON deserialization libraries inferring field names from constructor parameters, testing frameworks reporting readable parameter names in failure messages — depend on this reflection capability. Without `-parameters`, these frameworks either require explicit annotations naming each parameter, or fall back to less helpful generic names. Understanding this flag and its effect is essential context for why some reflection-heavy frameworks require a specific compiler configuration to work as expected.

## 3. Core concept

```java
import java.lang.reflect.*;

class Greeter {
    String greet(String name, int times) {
        return name.repeat(times);
    }
}

Method method = Greeter.class.getDeclaredMethod("greet", String.class, int.class);
Parameter[] parameters = method.getParameters();

for (Parameter p : parameters) {
    System.out.println(p.getName() + ": " + p.getType().getSimpleName());
    System.out.println("  isNamePresent: " + p.isNamePresent());
}
// Without -parameters: "arg0: String", "arg1: int", isNamePresent: false
// With -parameters:    "name: String", "times: int", isNamePresent: true
```

`Parameter.getName()` always returns *something*, but whether that something is the real source name or a generic stand-in name (`arg0`, `arg1`, ...) depends entirely on whether `-parameters` was used at compile time — `isNamePresent()` tells you which case you're in.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="the -parameters compiler flag determines whether reflection sees real parameter names or generic stand-in names">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="11" font-family="sans-serif">javac Greeter.java (no -parameters):</text>
  <rect x="280" y="15" width="150" height="30" rx="4" fill="#1c2430" stroke="#f85149"/><text x="355" y="35" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">arg0, arg1</text>

  <text x="20" y="75" fill="#8b949e" font-size="11" font-family="sans-serif">javac -parameters Greeter.java:</text>
  <rect x="280" y="60" width="150" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="355" y="80" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">name, times</text>
  <text x="20" y="115" fill="#8b949e" font-size="10" font-family="sans-serif">Real source names are only retained in bytecode when the -parameters flag is used.</text>
</svg>

The same source code compiles to bytecode with either generic stand-in names or real parameter names, depending purely on this one compiler flag.

## 5. Runnable example

Scenario: building a minimal reflection-based dependency injector that matches constructor parameters by name — evolved from basic parameter reflection showing the `-parameters` flag's effect, through inspecting richer parameter metadata (modifiers, annotations), to a version implementing name-based constructor argument matching, the exact technique frameworks like Spring use internally.

### Level 1 — Basic

```java
import java.lang.reflect.*;

public class ParameterReflectionBasic {
    static class Greeter {
        String greet(String name, int times) {
            return name.repeat(times);
        }
    }

    public static void main(String[] args) throws NoSuchMethodException {
        Method method = Greeter.class.getDeclaredMethod("greet", String.class, int.class);
        Parameter[] parameters = method.getParameters();

        for (Parameter p : parameters) {
            System.out.println(p.getName() + " (" + p.getType().getSimpleName() + "), isNamePresent=" + p.isNamePresent());
        }
    }
}
```

**How to run:** `javac -parameters ParameterReflectionBasic.java && java ParameterReflectionBasic`

Expected output (when compiled WITH `-parameters`):
```
name (String), isNamePresent=true
times (int), isNamePresent=true
```

Expected output (when compiled WITHOUT `-parameters`, i.e. just `javac ParameterReflectionBasic.java`):
```
arg0 (String), isNamePresent=false
arg1 (int), isNamePresent=false
```

`method.getParameters()` returns a `Parameter[]` in declaration order. `p.getName()` returns either the real source-code name (`"name"`, `"times"`) or a generic stand-in name (`"arg0"`, `"arg1"`), entirely depending on whether the `-parameters` compiler flag was used — `p.isNamePresent()` tells the caller definitively which case applies, so code relying on real parameter names can detect and handle the absence gracefully rather than silently working with meaningless stand-in names.

### Level 2 — Intermediate

```java
import java.lang.reflect.*;
import java.lang.annotation.*;

public class ParameterReflectionMetadata {
    @Retention(RetentionPolicy.RUNTIME)
    @interface Required {}

    static class UserService {
        void createUser(@Required String username, String nickname, final int age) {}
    }

    public static void main(String[] args) throws NoSuchMethodException {
        Method method = UserService.class.getDeclaredMethod("createUser", String.class, String.class, int.class);

        for (Parameter p : method.getParameters()) {
            boolean isRequired = p.isAnnotationPresent(Required.class);
            boolean isFinal = Modifier.isFinal(p.getModifiers());
            System.out.println(p.getName() + ": required=" + isRequired + ", final=" + isFinal);
        }
    }
}
```

**How to run:** `javac -parameters ParameterReflectionMetadata.java && java ParameterReflectionMetadata`

Expected output:
```
username: required=true, final=false
nickname: required=false, final=false
age: required=false, final=true
```

The real-world concern this adds: `Parameter` exposes more than just a name — `.isAnnotationPresent(...)` checks for annotations placed directly on that specific parameter (`@Required` on `username`), and `.getModifiers()` (combined with `Modifier.isFinal(...)`) reveals modifiers like `final` (present on `age`). This richer per-parameter metadata is exactly what frameworks use to build validation, dependency injection, and similar parameter-driven behavior entirely through reflection.

### Level 3 — Advanced

```java
import java.lang.reflect.*;
import java.util.*;

public class ParameterReflectionInjector {
    static class OrderService {
        private final String customerId;
        private final double amount;

        // A constructor a mini dependency-injection framework would need to call by NAME.
        public OrderService(String customerId, double amount) {
            this.customerId = customerId;
            this.amount = amount;
        }

        @Override public String toString() {
            return "OrderService(customerId=" + customerId + ", amount=" + amount + ")";
        }
    }

    // A minimal "injector": given a name->value map, matches constructor parameters BY NAME.
    static Object instantiate(Class<?> clazz, Map<String, Object> availableValues) throws Exception {
        Constructor<?> constructor = clazz.getDeclaredConstructors()[0];
        Parameter[] parameters = constructor.getParameters();

        Object[] arguments = new Object[parameters.length];
        for (int i = 0; i < parameters.length; i++) {
            String paramName = parameters[i].getName();
            if (!availableValues.containsKey(paramName)) {
                throw new IllegalArgumentException("No value available for parameter: " + paramName);
            }
            arguments[i] = availableValues.get(paramName);
        }

        return constructor.newInstance(arguments);
    }

    public static void main(String[] args) throws Exception {
        Map<String, Object> values = Map.of("customerId", "CUST-42", "amount", 199.99);

        Object created = instantiate(OrderService.class, values);
        System.out.println("Created: " + created);
    }
}
```

**How to run:** `javac -parameters ParameterReflectionInjector.java && java ParameterReflectionInjector`

Expected output:
```
Created: OrderService(customerId=CUST-42, amount=199.99)
```

This implements the core technique real dependency-injection frameworks use internally: `instantiate(...)` reflects on `OrderService`'s constructor, reads each parameter's real name via `getParameters()[i].getName()` (requiring `-parameters` to have been used at compile time), and looks up a matching value from a name-keyed map — entirely without the caller needing to know or specify the constructor's parameter *order*, only providing values keyed by the parameters' actual names. `constructor.newInstance(arguments)` then invokes the constructor with the correctly-matched, correctly-ordered argument array.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `values` is a `Map<String, Object>` with two entries: `"customerId" -> "CUST-42"`, `"amount" -> 199.99`.

`instantiate(OrderService.class, values)` is called. Inside, `clazz.getDeclaredConstructors()[0]` retrieves `OrderService`'s single constructor. `constructor.getParameters()` returns a `Parameter[]` with two entries, in declaration order: `customerId` (type `String`) at index `0`, `amount` (type `double`) at index `1` — assuming the class was compiled with `-parameters`, so these are the real names, not `arg0`/`arg1`.

The `for` loop processes each parameter by index. For `i = 0`: `parameters[0].getName()` is `"customerId"`. `availableValues.containsKey("customerId")` is `true` (the map has this key), so `arguments[0] = availableValues.get("customerId")` is `"CUST-42"`.

For `i = 1`: `parameters[1].getName()` is `"amount"`. `availableValues.containsKey("amount")` is `true`, so `arguments[1] = availableValues.get("amount")` is `199.99` (boxed as `Double`, since the map's value type is `Object`).

```
constructor parameters (in declaration order): [customerId: String, amount: double]

i=0: paramName="customerId" -> availableValues has it -> arguments[0] = "CUST-42"
i=1: paramName="amount"     -> availableValues has it -> arguments[1] = 199.99

arguments array, correctly ORDERED to match the constructor's parameter positions:
  ["CUST-42", 199.99]
```

Once both arguments are resolved and placed into the `arguments` array in the correct positional order (matching the constructor's actual parameter sequence, even though `values` itself is an unordered map), `constructor.newInstance(arguments)` is called — this invokes `OrderService`'s constructor exactly as if `new OrderService("CUST-42", 199.99)` had been written directly, since `Double` auto-unboxes to `double` for the second argument. The resulting `OrderService` instance has `customerId = "CUST-42"` and `amount = 199.99`.

`main` prints `created`, whose `toString()` produces `"OrderService(customerId=CUST-42, amount=199.99)"` — demonstrating that an object was constructed correctly purely by matching named values to named constructor parameters via reflection, exactly the mechanism dependency injection frameworks rely on internally.

## 7. Gotchas & takeaways

> Code that depends on `Parameter.getName()` returning real, meaningful names will silently receive generic `arg0`/`arg1`/... stand-in names if the class wasn't compiled with `-parameters` — this doesn't cause a compile error or an exception, just quietly wrong (or at least unhelpful) behavior at runtime. Always check `Parameter.isNamePresent()` before relying on parameter names for anything functionally important, and ensure your build configuration (Maven, Gradle, or a manual `javac` invocation) actually includes the `-parameters` flag if any dependency-injection or similar framework in your project needs it.

- Before Java 8's `Method.getParameters()`, reflective code had no way to retrieve a method or constructor's actual parameter names, only their types.
- `Parameter.getName()` returns either the real source-code name or a generic stand-in name (`arg0`, `arg1`, ...), depending entirely on whether the class was compiled with the `-parameters` javac flag.
- `Parameter.isNamePresent()` reliably tells you which case applies — always check it before depending on real parameter names for framework-level logic.
- `Parameter` also exposes annotations (`isAnnotationPresent`) and modifiers (`getModifiers`) specific to that individual parameter, richer than what was available via the older `getParameterTypes()`/`getParameterAnnotations()` methods alone.
- Frameworks that match values to constructor or method parameters by name (dependency injection, JSON deserialization, some testing tools) depend entirely on `-parameters` being enabled at compile time — a common, easy-to-miss build configuration requirement worth checking when such a framework doesn't behave as expected.
