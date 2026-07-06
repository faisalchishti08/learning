---
card: java
gi: 253
slug: local-classes-inside-methods
title: Local classes (inside methods)
---

## 1. What it is

A local class is a class defined entirely inside a method body (or, less commonly, inside a constructor or a block), scoped just like a local variable — it exists only for the duration of that method's execution and is completely invisible to any code outside it. It can access the enclosing method's local variables (with a restriction covered in the next topic) in addition to the enclosing instance's fields, if the method is not static.

```java
class ReportGenerator {
    String generate(int[] values) {
        class Formatter { // local class — defined entirely inside this method
            String format(int value) {
                return "[" + value + "]";
            }
        }

        Formatter formatter = new Formatter(); // usable only within this method
        StringBuilder sb = new StringBuilder();
        for (int v : values) sb.append(formatter.format(v)).append(" ");
        return sb.toString().trim();
    }
}
```

`Formatter` is declared right inside `generate`, used immediately within the same method, and does not exist anywhere else in the program — no other method of `ReportGenerator`, nor any other class at all, can reference `Formatter` by name, since it is scoped entirely to this one method body.

## 2. Why & when

Local classes exist for situations where a helper class is needed only by one specific method, and giving it broader visibility (as a nested or top-level class) would be unnecessary or even misleading about its scope.

- **Tightly scoped helper logic** — if a class exists purely to support one method's internal algorithm and has no meaning or use anywhere else, defining it locally keeps that scoping explicit and prevents it from cluttering the enclosing class's namespace.
- **Access to local variables and parameters** — a local class can read the enclosing method's local variables and parameters directly (as long as they are final or effectively final, covered next), which is convenient for helper logic that needs to work closely with that method's temporary state.
- **A predecessor to anonymous classes and lambdas** — local classes solve a similar problem to anonymous classes (the next topic) and lambda expressions, but with a named class you can instantiate multiple times or that has more than one method — useful when a simple functional interface's shape (one abstract method) doesn't fit what you need.

Use a local class when you need a full class (potentially with multiple methods, or instantiated more than once) whose entire purpose and lifetime is scoped to a single method — if you only need a single method's worth of behaviour passed around once, an anonymous class or a lambda expression is usually more concise and idiomatic.

## 3. Core concept

```java
class OrderProcessor {
    double calculateTotal(double[] prices, double taxRate) {
        class TaxCalculator { // local class scoped to this one method
            double applyTax(double price) { return price * (1 + taxRate); } // reads the enclosing method's parameter
        }

        TaxCalculator calc = new TaxCalculator();
        double total = 0;
        for (double p : prices) total += calc.applyTax(p);
        return total;
    }
}
```

`TaxCalculator.applyTax` reads `taxRate` directly, a parameter of the enclosing `calculateTotal` method — this works because `taxRate` is effectively final (never reassigned after being set), a requirement the next topic covers precisely; `TaxCalculator` itself is entirely invisible outside `calculateTotal`.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A local class is declared entirely inside a method body, it can access the methods parameters and local variables, and is invisible to any code outside that method">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="60" y="20" width="480" height="115" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="300" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">double calculateTotal(double[] prices, double taxRate) {</text>

  <rect x="90" y="50" width="420" height="60" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="70" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">class TaxCalculator { ... uses taxRate ... }</text>
  <text x="300" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">visible ONLY inside calculateTotal</text>
  <text x="300" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reads the enclosing method's taxRate directly</text>

  <text x="300" y="128" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">}</text>

  <text x="300" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Scoped like a local variable — invisible to any code outside this one method.</text>
</svg>

A local class exists only within its enclosing method, with direct access to that method's parameters and locals.

## 5. Runnable example

Scenario: a text-processing method that validates and formats words, evolved from a simple local class into one using multiple enclosing local variables, then hardened with a case demonstrating a local class instantiated multiple times within its scoping method.

### Level 1 — Basic

```java
public class LocalClassBasic {
    static String processWord(String word) {
        class WordFormatter { // local class
            String format() {
                return word.substring(0, 1).toUpperCase() + word.substring(1).toLowerCase();
            }
        }

        WordFormatter formatter = new WordFormatter();
        return formatter.format();
    }

    public static void main(String[] args) {
        System.out.println(processWord("hELLo")); // "Hello"
    }
}
```

**How to run:** `java LocalClassBasic.java`

`WordFormatter` is declared inside `processWord` and reads `word` (the method's parameter) directly inside `format()` — `WordFormatter` cannot be referenced anywhere outside this method.

### Level 2 — Intermediate

Same idea, now with a local class that uses two enclosing local variables together, and is instantiated once per call to build up a report across multiple words.

```java
import java.util.List;

public class LocalClassIntermediate {
    static String buildReport(List<String> words, String separator) {
        class WordFormatter {
            String format(String word) {
                return word.substring(0, 1).toUpperCase() + word.substring(1).toLowerCase();
            }
        }

        WordFormatter formatter = new WordFormatter(); // one instance, reused for every word
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < words.size(); i++) {
            if (i > 0) sb.append(separator); // separator: the enclosing method's other parameter
            sb.append(formatter.format(words.get(i)));
        }
        return sb.toString();
    }

    public static void main(String[] args) {
        System.out.println(buildReport(List.of("hELLo", "WORLD", "javA"), ", "));
    }
}
```

**How to run:** `java LocalClassIntermediate.java`

`formatter` (one `WordFormatter` instance) is created once and reused across every element of `words` inside the loop, while `separator` — a second enclosing parameter, distinct from `words` — is used directly in the surrounding loop logic, not inside the local class itself; both work together to build the final report string.

### Level 3 — Advanced

Same word-processing idea, now with the local class instantiated multiple times within one method call, each instance configured slightly differently based on a loop variable — demonstrating that a local class, unlike a single lambda, can be instantiated repeatedly with different captured state each time.

```java
import java.util.ArrayList;
import java.util.List;

public class LocalClassAdvanced {
    interface Formatter {
        String format(String word);
    }

    static List<String> buildNumberedReport(List<String> words) {
        List<String> results = new ArrayList<>();

        for (int i = 0; i < words.size(); i++) {
            final int lineNumber = i + 1; // effectively final per iteration -- see next topic for why this matters

            class NumberedFormatter implements Formatter { // a NEW local class instance each iteration
                @Override
                public String format(String word) {
                    String capitalized = word.substring(0, 1).toUpperCase() + word.substring(1).toLowerCase();
                    return lineNumber + ". " + capitalized; // captures THIS iteration's lineNumber
                }
            }

            Formatter formatter = new NumberedFormatter();
            results.add(formatter.format(words.get(i)));
        }
        return results;
    }

    public static void main(String[] args) {
        List<String> report = buildNumberedReport(List.of("hELLo", "WORLD", "javA"));
        for (String line : report) System.out.println(line);
    }
}
```

**How to run:** `java LocalClassAdvanced.java`

Although `NumberedFormatter` is declared once, textually, inside the loop, each iteration creates a genuinely distinct instance of it, capturing that iteration's own `lineNumber` value — Java re-executes the local class declaration and instantiation on each loop pass, so `NumberedFormatter`'s captured `lineNumber` correctly differs for `"Hello"` (`1`), `"World"` (`2`), and `"Java"` (`3`).

## 6. Walkthrough

Trace `buildNumberedReport(List.of("hELLo", "WORLD", "javA"))` iteration by iteration.

**`i = 0`.** `lineNumber` is set to `1`. The local class `NumberedFormatter` is declared (conceptually, "instantiated as a class" for this iteration) and a new instance is created via `new NumberedFormatter()`. Calling `formatter.format("hELLo")`: `capitalized` becomes `"H" + "ello"` = `"Hello"`; the method returns `"1. " + "Hello"` = `"1. Hello"`. This is added to `results`.

**`i = 1`.** `lineNumber` is now `2` (a fresh local variable for this iteration). A *new* `NumberedFormatter` instance is created, capturing this iteration's `lineNumber` (`2`). `formatter.format("WORLD")`: `capitalized` becomes `"W" + "orld"` = `"World"`; returns `"2. World"`. Added to `results`.

**`i = 2`.** `lineNumber` is `3`. Another new `NumberedFormatter` instance captures `3`. `formatter.format("javA")`: `capitalized` becomes `"J" + "ava"` = `"Java"`; returns `"3. Java"`. Added to `results`.

**Loop ends.** `results` is `["1. Hello", "2. World", "3. Java"]`. The final `for` loop in `main` prints each element on its own line.

```
i=0: lineNumber=1, new NumberedFormatter captures 1 -> format("hELLo") -> "1. Hello"
i=1: lineNumber=2, new NumberedFormatter captures 2 -> format("WORLD") -> "2. World"
i=2: lineNumber=3, new NumberedFormatter captures 3 -> format("javA")  -> "3. Java"

results = ["1. Hello", "2. World", "3. Java"]
```

**Final output.**
```
1. Hello
2. World
3. Java
```

## 7. Gotchas & takeaways

> **A local class declared inside a loop is conceptually re-evaluated on each iteration, and each instantiation captures that iteration's own copy of any local variables it reads** — this is why `lineNumber`, declared fresh inside the loop body each pass, correctly differs across the three `NumberedFormatter` instances in the advanced example, even though the class's source code is written only once.

> **A local class cannot have `static` members (with the exception of `static final` constants) in most Java versions before 16, since it is tied to a specific execution of its enclosing method, not a fixed, single class-level slot** — this restriction was relaxed in modern Java (JEP 395-related changes), but understanding local classes as fundamentally method-scoped, transient constructs is the key mental model even where the restriction has loosened.

- A local class is declared entirely inside a method body and is invisible to any code outside that method — its scope matches a local variable's.
- It can access the enclosing method's parameters and local variables (subject to the effectively-final rule, covered next) and the enclosing instance's fields, if the method is not static.
- Local classes are useful when a helper class's entire purpose is scoped to one method, especially when it needs multiple methods or multiple instantiations — beyond what a single lambda or anonymous class conveniently expresses.
- A local class declared inside a loop creates a genuinely new instance, capturing that iteration's own local variable values, on each pass through the loop.
