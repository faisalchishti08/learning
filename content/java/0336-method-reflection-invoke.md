---
card: java
gi: 336
slug: method-reflection-invoke
title: Method reflection & invoke()
---

## 1. What it is

Method reflection uses `java.lang.reflect.Method` to look up and call a method by name, at runtime, without the compiler ever seeing a direct call to it. `Class.getDeclaredMethod(name, parameterTypes...)` finds a specific method by its name and exact parameter types, returning a `Method` object; calling `method.invoke(instance, args...)` then actually runs that method on the given object with the given arguments — even for `private` methods, once `setAccessible(true)` has been called.

```java
import java.lang.reflect.Method;

public class MethodReflectionDemo {
    static class Greeter {
        public String greet(String name) { return "Hello, " + name + "!"; }
    }

    public static void main(String[] args) throws Exception {
        Greeter greeter = new Greeter();
        Method method = Greeter.class.getDeclaredMethod("greet", String.class);
        Object result = method.invoke(greeter, "Ada");
        System.out.println(result);
    }
}
```

`getDeclaredMethod("greet", String.class)` locates the method by matching both its name and its exact parameter types, and `invoke(greeter, "Ada")` calls it as if you had written `greeter.greet("Ada")` directly, but resolved entirely at runtime.

## 2. Why & when

Ordinary method calls are checked at compile time — the compiler verifies the method exists, its parameter types match, and access is permitted. Method reflection exists for the cases where none of that can be known until runtime: a framework calling a method whose name comes from an annotation, a configuration file, or a plugin's declared contract.

- **Frameworks that call methods by convention or configuration** — dependency injection containers calling `@PostConstruct`-annotated methods, test frameworks calling every method named `test*`, or web frameworks routing an HTTP request to a controller method chosen by a URL mapping.
- **Generic tooling** — a command dispatcher that maps string commands to methods, or a serialization library invoking getter/setter methods generically across arbitrary classes.
- **Bridging dynamic and static worlds** — scripting engines or plugin systems that need to call into ordinary compiled Java code using names only known at runtime.

`invoke()` wraps any exception thrown by the target method inside an `InvocationTargetException` — the *original* exception is available via `getCause()` — and reflective calls carry real overhead (much higher than a direct call) and lose all compile-time type checking, so they should be reserved for cases where the method to call is genuinely not known until runtime.

## 3. Core concept

```java
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

public class MethodReflectionCore {
    static class Calculator {
        public int divide(int a, int b) { return a / b; }
    }

    public static void main(String[] args) throws Exception {
        Calculator calc = new Calculator();
        Method divide = Calculator.class.getDeclaredMethod("divide", int.class, int.class);
        try {
            Object result = divide.invoke(calc, 10, 0); // triggers ArithmeticException inside divide
            System.out.println(result);
        } catch (InvocationTargetException e) {
            System.out.println("Target method threw: " + e.getCause()); // the REAL exception
        }
    }
}
```

**How to run:** `java MethodReflectionCore.java`

`divide`'s own `int a / int b` throws `ArithmeticException` for the division by zero, but reflection wraps it: `invoke()` throws `InvocationTargetException`, and the *original* `ArithmeticException` is only recoverable via `e.getCause()` — a detail that trips up code that only catches the outer exception type.

## 4. Diagram

<svg viewBox="0 0 620 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="getDeclaredMethod finds a Method by name and parameter types; invoke calls it on an instance, wrapping any thrown exception in InvocationTargetException">
  <rect x="8" y="8" width="604" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="230" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="135" y="52" fill="#79c0ff" font-size="10" text-anchor="middle">getDeclaredMethod(name, types)</text>

  <text x="265" y="52" fill="#8b949e" font-size="12">→ Method object</text>

  <rect x="20" y="85" width="230" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="135" y="107" fill="#6db33f" font-size="10" text-anchor="middle">method.invoke(instance, args)</text>

  <text x="400" y="52" fill="#8b949e" font-size="9">success → return value (Object)</text>
  <text x="400" y="107" fill="#f85149" font-size="9">failure inside method → InvocationTargetException</text>
</svg>

## 5. Runnable example

Scenario: a tiny string-command dispatcher, evolved from a single hardcoded reflective call, into one that dispatches by command name from a lookup, into a production-style dispatcher that handles missing commands, argument mismatches, and exceptions thrown by the target method distinctly.

### Level 1 — Basic

```java
import java.lang.reflect.Method;

public class CommandDispatchBasic {
    static class Commands {
        public String hello(String name) { return "Hello, " + name + "!"; }
    }

    public static void main(String[] args) throws Exception {
        Commands commands = new Commands();
        Method method = Commands.class.getDeclaredMethod("hello", String.class);
        Object result = method.invoke(commands, "Ada");
        System.out.println(result);
    }
}
```

**How to run:** `java CommandDispatchBasic.java`

This hardcodes exactly one method call resolved reflectively — there's no actual dispatch logic yet, and no handling for what happens if the method name were wrong or the method itself threw an exception.

### Level 2 — Intermediate

```java
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

public class CommandDispatchIntermediate {
    static class Commands {
        public String hello(String name) { return "Hello, " + name + "!"; }
        public String shout(String text) { return text.toUpperCase() + "!!!"; }
    }

    public static void main(String[] args) {
        Commands commands = new Commands();
        dispatch(commands, "hello", "Ada");
        dispatch(commands, "shout", "welcome");
        dispatch(commands, "unknownCommand", "x");
    }

    static void dispatch(Commands commands, String commandName, String arg) {
        try {
            Method method = Commands.class.getDeclaredMethod(commandName, String.class);
            Object result = method.invoke(commands, arg);
            System.out.println(commandName + "(" + arg + ") -> " + result);
        } catch (NoSuchMethodException e) {
            System.out.println(commandName + " -> unknown command.");
        } catch (IllegalAccessException | InvocationTargetException e) {
            System.out.println(commandName + " -> failed to execute: " + e.getMessage());
        }
    }
}
```

**How to run:** `java CommandDispatchIntermediate.java`

Looking up the method by name now happens inside `dispatch` itself, and `NoSuchMethodException` (unknown command) is handled distinctly from a reflective invocation failure — an unrecognized command name now produces a clear message instead of crashing the whole dispatcher.

### Level 3 — Advanced

```java
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

public class CommandDispatchAdvanced {
    static class Commands {
        public String hello(String name) { return "Hello, " + name + "!"; }
        public String shout(String text) { return text.toUpperCase() + "!!!"; }
        public String fail(String text) { throw new IllegalStateException("command '" + text + "' always fails"); }
    }

    public static void main(String[] args) {
        Commands commands = new Commands();
        dispatch(commands, "hello", "Ada");
        dispatch(commands, "fail", "boom");
        dispatch(commands, "unknownCommand", "x");
    }

    static void dispatch(Commands commands, String commandName, String arg) {
        try {
            Method method = Commands.class.getDeclaredMethod(commandName, String.class);
            method.setAccessible(true);
            Object result = method.invoke(commands, arg);
            System.out.println(commandName + "(" + arg + ") -> " + result);
        } catch (NoSuchMethodException e) {
            System.out.println(commandName + " -> unknown command.");
        } catch (InvocationTargetException e) {
            Throwable actualError = e.getCause(); // unwrap to the REAL exception
            System.out.println(commandName + " -> command itself threw: "
                    + actualError.getClass().getSimpleName() + ": " + actualError.getMessage());
        } catch (IllegalAccessException e) {
            System.out.println(commandName + " -> not accessible: " + e.getMessage());
        }
    }
}
```

**How to run:** `java CommandDispatchAdvanced.java`

The `fail` command's `IllegalStateException` is deliberately triggered to demonstrate the wrapping behavior: `invoke()` throws `InvocationTargetException`, and the code unwraps it with `e.getCause()` to report the *actual* exception type and message the command threw, rather than just printing the generic reflective wrapper exception, which is the detail most reflection-based dispatchers get wrong on a first attempt.

## 6. Walkthrough

Execution starts in `main`, which calls `dispatch` three times with different command names.

**`dispatch(commands, "hello", "Ada")`:** `Commands.class.getDeclaredMethod("hello", String.class)` finds the matching method, `setAccessible(true)` ensures it's callable regardless of modifiers, and `method.invoke(commands, "Ada")` runs `commands.hello("Ada")` under the hood, returning `"Hello, Ada!"`. This is printed as `hello(Ada) -> Hello, Ada!`.

**`dispatch(commands, "fail", "boom")`:** the method lookup succeeds the same way, but `method.invoke(commands, "boom")` now runs `commands.fail("boom")`, whose body immediately throws `new IllegalStateException("command 'boom' always fails")`. Reflection does not let this exception propagate directly — the JVM wraps it inside a fresh `InvocationTargetException`, which is what `invoke()` actually throws. The `catch (InvocationTargetException e)` block runs, and `e.getCause()` retrieves the original `IllegalStateException` — its class name and message are printed as `fail -> command itself threw: IllegalStateException: command 'boom' always fails`.

**`dispatch(commands, "unknownCommand", "x")`:** this time, `getDeclaredMethod("unknownCommand", String.class)` itself fails, since no such method exists on `Commands` — it throws `NoSuchMethodException` before `invoke` is ever reached, so the target class's methods are never touched at all. The `catch (NoSuchMethodException e)` block prints `unknownCommand -> unknown command.`

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="three dispatch calls take three different paths: success, exception thrown and unwrapped from InvocationTargetException, and method not found">
  <rect x="8" y="8" width="624" height="164" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#6db33f" font-size="10">hello/Ada: getDeclaredMethod OK -&gt; invoke OK -&gt; "Hello, Ada!"</text>
  <text x="20" y="60" fill="#f85149" font-size="10">fail/boom: getDeclaredMethod OK -&gt; invoke runs fail() -&gt; IllegalStateException thrown inside</text>
  <text x="20" y="82" fill="#f85149" font-size="10">          -&gt; wrapped as InvocationTargetException -&gt; e.getCause() unwraps to the real exception</text>
  <text x="20" y="112" fill="#79c0ff" font-size="10">unknownCommand/x: getDeclaredMethod itself throws NoSuchMethodException</text>
  <text x="20" y="134" fill="#79c0ff" font-size="10">                 -&gt; invoke() never reached, method body never runs</text>
</svg>

## 7. Gotchas & takeaways

> Catching only `InvocationTargetException` and printing it directly shows an unhelpful wrapper message — always call `.getCause()` to get the actual exception the invoked method threw, which is what you (and your logs) actually need to see.

- `getDeclaredMethod(name, parameterTypes...)` must match both the name *and* the exact parameter types — overloaded methods require picking the right overload's exact parameter type list.
- `invoke()` never lets the target method's exceptions propagate directly — it always wraps them in `InvocationTargetException`, whose `getCause()` holds the original exception.
- `setAccessible(true)` is required to invoke `private`/`protected` methods reflectively, same as with field reflection.
- Reflective calls have real performance overhead compared to direct calls (though the JVM optimizes repeated invocations of the same `Method` object over time) — avoid it in hot paths unless there's no static alternative.
- Distinguish `NoSuchMethodException` (the lookup itself failed — wrong name or parameter types) from `InvocationTargetException` (the lookup succeeded, but the method's own body threw) — they represent different failure stages and usually need different handling.
