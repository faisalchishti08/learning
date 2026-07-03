---
card: spring-framework
gi: 169
slug: functions
title: "Functions"
---

## 1. What it is

SpEL allows registering Java **static methods** as named functions on a `StandardEvaluationContext`. Once registered, the function is callable from any expression evaluated against that context using the `#functionName(args)` syntax. Functions bridge the gap between SpEL's built-in operators and arbitrary Java utility logic.

```java
Method reverseStr = StringUtils.class.getDeclaredMethod("reverse", String.class);
ctx.registerFunction("reverse", reverseStr);

parser.parseExpression("#reverse('hello')").getValue(ctx); // olleh
```

## 2. Why & when

- **Custom utility logic** — expose domain-specific methods (e.g., `#formatCurrency(amount, locale)`) without requiring the root object to carry all helper methods.
- **Reusable filters** — `list.?[#isValidEmail(email)]` calls a validation function per element.
- **Security expressions** — Spring Security uses internally registered functions (e.g., `hasRole`, `hasAuthority`, `isAuthenticated`) as SpEL functions in `@PreAuthorize`.
- **Testing** — register mock/stub functions that intercept logic in expression-driven rule engines.

## 3. Core concept

Registration:

```java
ctx.registerFunction("funcName", SomeClass.class.getDeclaredMethod("staticMethod", ArgType.class));
```

Requirements:
- The method **must be static**.
- The method must be accessible (public, or `method.setAccessible(true)` called first).
- Arguments are coerced via SpEL's `ConversionService` — passing an `int` where `long` is expected works.
- Functions are stored in the `EvaluationContext`'s variable map as `java.lang.reflect.Method` values.

`#functionName()` in an expression resolves the name against variables first; if the value is a `Method`, SpEL invokes it as a function. This means `ctx.setVariable("fn", method)` and `ctx.registerFunction("fn", method)` are equivalent.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg">
  <!-- Static method -->
  <rect x="10" y="20" width="175" height="80" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="97" y="40"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Static Method</text>
  <line x1="18" y1="48" x2="177" y2="48" stroke="#79c0ff" stroke-width="1" opacity="0.4"/>
  <text x="97" y="62"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">public static String</text>
  <text x="97" y="76"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">  reverse(String s)</text>
  <text x="97" y="90"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Class.getDeclaredMethod(...)</text>

  <!-- registerFunction -->
  <rect x="240" y="20" width="220" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="40"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ctx.registerFunction</text>
  <line x1="248" y1="48" x2="452" y2="48" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="350" y="62"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">("reverse", method)</text>
  <text x="350" y="76"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">stored in ctx variable map</text>
  <text x="350" y="90"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">as Method object</text>

  <!-- Usage -->
  <rect x="515" y="20" width="175" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="602" y="40"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Expression</text>
  <line x1="523" y1="48" x2="682" y2="48" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="602" y="62"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">#reverse('hello')</text>
  <text x="602" y="76"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ "olleh"</text>
  <text x="602" y="90"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">args coerced if needed</text>

  <defs>
    <marker id="a169" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="187" y1="60" x2="237" y2="60" stroke="#6db33f" stroke-width="2" marker-end="url(#a169)"/>
  <line x1="462" y1="60" x2="512" y2="60" stroke="#6db33f" stroke-width="2" marker-end="url(#a169)"/>

  <rect x="10" y="120" width="680" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="137" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Functions are just variables holding a Method object — #funcName(args) resolves, detects Method, invokes via reflection</text>
  <text x="350" y="152" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Spring Security: hasRole(), hasAuthority(), isAuthenticated() — pre-registered as functions</text>
</svg>

SpEL functions are static Java methods registered on the `EvaluationContext` variable map; `#fn(args)` invokes them via reflection.

## 5. Runnable example

### Level 1 — Basic

Register and call static utility methods as SpEL functions.

```java
// SpelFunctionsBasic.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.lang.reflect.*;

class StringUtils {
    public static String reverse(String s) {
        return new StringBuilder(s).reverse().toString();
    }
    public static boolean isPalindrome(String s) {
        String clean = s.toLowerCase().replaceAll("[^a-z0-9]", "");
        return clean.equals(new StringBuilder(clean).reverse().toString());
    }
    public static String initials(String fullName) {
        String[] parts = fullName.trim().split("\\s+");
        StringBuilder sb = new StringBuilder();
        for (String p : parts) if (!p.isEmpty()) sb.append(p.charAt(0));
        return sb.toString().toUpperCase();
    }
}

public class SpelFunctionsBasic {
    public static void main(String[] args) throws NoSuchMethodException {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();

        ctx.registerFunction("reverse",
            StringUtils.class.getDeclaredMethod("reverse", String.class));
        ctx.registerFunction("isPalindrome",
            StringUtils.class.getDeclaredMethod("isPalindrome", String.class));
        ctx.registerFunction("initials",
            StringUtils.class.getDeclaredMethod("initials", String.class));

        System.out.println(parser.parseExpression("#reverse('hello')").getValue(ctx));
        System.out.println(parser.parseExpression("#reverse(#reverse('world'))").getValue(ctx)); // world
        System.out.println(parser.parseExpression("#isPalindrome('racecar')").getValue(ctx));    // true
        System.out.println(parser.parseExpression("#isPalindrome('hello')").getValue(ctx));      // false
        System.out.println(parser.parseExpression("#initials('Alice Bob Smith')").getValue(ctx)); // ABS

        // Use in conditional
        System.out.println(parser.parseExpression(
            "#isPalindrome('madam') ? 'yes' : 'no'").getValue(ctx)); // yes

        // Use as part of larger expression
        ctx.setVariable("name", "Anna");
        System.out.println(parser.parseExpression(
            "#isPalindrome(#name)").getValue(ctx, Boolean.class)); // true
    }
}
```

How to run: `java SpelFunctionsBasic.java`

`getDeclaredMethod("reverse", String.class)` gets the `Method` object via reflection. `registerFunction` stores it under the name. Calling `#reverse(...)` in an expression invokes `StringUtils.reverse(...)`.

### Level 2 — Intermediate

Functions in collection filters and projections; multi-arg functions; chained function calls.

```java
// SpelFunctionsIntermediate.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;
import java.lang.reflect.*;

class Validators {
    public static boolean isValidEmail(String email) {
        return email != null && email.matches("[\\w._%+\\-]+@[\\w.\\-]+\\.[a-zA-Z]{2,}");
    }
    public static boolean isStrongPassword(String pw) {
        return pw != null && pw.length() >= 8
            && pw.matches(".*[A-Z].*") && pw.matches(".*[0-9].*");
    }
    public static String maskEmail(String email) {
        int at = email.indexOf('@');
        if (at < 2) return email;
        return email.charAt(0) + "***" + email.substring(at);
    }
    public static double discount(double price, int pct) {
        return price * (1.0 - pct / 100.0);
    }
}

public class SpelFunctionsIntermediate {
    public static void main(String[] args) throws NoSuchMethodException {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();

        ctx.registerFunction("isEmail",    Validators.class.getDeclaredMethod("isValidEmail", String.class));
        ctx.registerFunction("strongPwd",  Validators.class.getDeclaredMethod("isStrongPassword", String.class));
        ctx.registerFunction("maskEmail",  Validators.class.getDeclaredMethod("maskEmail", String.class));
        ctx.registerFunction("discount",   Validators.class.getDeclaredMethod("discount", double.class, int.class));

        // Filter list of emails
        List<String> emails = List.of("alice@example.com", "not-an-email", "bob@test.org", "bad@");
        ctx.setRootObject(emails);
        System.out.println(parser.parseExpression("?[#isEmail(#this)]").getValue(ctx, List.class));
        // → [alice@example.com, bob@test.org]

        // Project: mask valid emails
        System.out.println(parser.parseExpression(
            "?[#isEmail(#this)].![#maskEmail(#this)]").getValue(ctx, List.class));
        // → [a***@example.com, b***@test.org]

        // Multi-arg function
        ctx.setVariable("price", 100.0);
        ctx.setVariable("pct",   15);
        System.out.println(parser.parseExpression(
            "#discount(#price, #pct)").getValue(ctx, Double.class)); // 85.0

        // Function in conditional
        ctx.setVariable("pwd", "Secret1");
        System.out.println(parser.parseExpression(
            "#strongPwd(#pwd) ? 'strong' : 'weak'").getValue(ctx)); // strong
    }
}
```

How to run: `java SpelFunctionsIntermediate.java`

`?[#isEmail(#this)]` calls `isValidEmail` for each element using `#this`. `?[...].![#maskEmail(#this)]` chains filter then projection, passing each element through `maskEmail`. Multi-arg function `#discount(#price, #pct)` passes two context variables.

### Level 3 — Advanced

Functions as building blocks in a rule engine; function composition; shared context with per-call variables.

```java
// SpelFunctionsAdvanced.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.lang.reflect.*;
import java.util.*;

class RuleFunctions {
    public static boolean between(double val, double lo, double hi) {
        return val >= lo && val <= hi;
    }
    public static String classify(double score) {
        if (score >= 90) return "A";
        if (score >= 80) return "B";
        if (score >= 70) return "C";
        if (score >= 60) return "D";
        return "F";
    }
    public static double weighted(double score, double weight) {
        return score * weight;
    }
    public static String formatScore(String name, double score) {
        return name + ": " + String.format("%.1f", score) + " (" + classify(score) + ")";
    }
}

class Student {
    public String name;
    public double exam, homework, participation;
    Student(String name, double exam, double hw, double part) {
        this.name = name; this.exam = exam; this.homework = hw; this.participation = part;
    }
    public String getName()          { return name; }
    public double getExam()          { return exam; }
    public double getHomework()      { return homework; }
    public double getParticipation() { return participation; }
}

public class SpelFunctionsAdvanced {
    public static void main(String[] args) throws NoSuchMethodException {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();

        ctx.registerFunction("between",      RuleFunctions.class.getDeclaredMethod("between", double.class, double.class, double.class));
        ctx.registerFunction("classify",     RuleFunctions.class.getDeclaredMethod("classify", double.class));
        ctx.registerFunction("weighted",     RuleFunctions.class.getDeclaredMethod("weighted", double.class, double.class));
        ctx.registerFunction("formatScore",  RuleFunctions.class.getDeclaredMethod("formatScore", String.class, double.class));

        List<Student> students = List.of(
            new Student("Alice",   95, 88, 90),
            new Student("Bob",     62, 75, 80),
            new Student("Charlie", 78, 85, 70));
        ctx.setRootObject(students);

        // Compute weighted total for each student
        System.out.println(parser.parseExpression(
            "![#weighted(exam,0.5) + #weighted(homework,0.3) + #weighted(participation,0.2)]")
            .getValue(ctx, List.class));

        // Format grade report
        System.out.println(parser.parseExpression(
            "![#formatScore(name, #weighted(exam,0.5) + #weighted(homework,0.3) + #weighted(participation,0.2))]")
            .getValue(ctx, List.class));

        // Filter: passing grade (total >= 70)
        System.out.println(parser.parseExpression(
            "?[(#weighted(exam,0.5)+#weighted(homework,0.3)+#weighted(participation,0.2)) >= 70].![name]")
            .getValue(ctx, List.class));

        ctx.close();
    }
}
```

How to run: `java SpelFunctionsAdvanced.java`

`#weighted(exam, 0.5)` calls `RuleFunctions.weighted(exam, 0.5)` where `exam` resolves to `#this.exam` for the current list element. Composing `#formatScore(name, #weighted(...) + ...)` passes the result of one function call as an argument to another — full function composition in SpEL.

## 6. Walkthrough

Execution for `"#formatScore(name, #weighted(exam,0.5)+#weighted(homework,0.3)+#weighted(participation,0.2))"` on element `Alice`:

1. `#this = Alice (Student{exam=95, homework=88, participation=90})`.
2. `name` → `"Alice"`.
3. `#weighted(95, 0.5)` → `RuleFunctions.weighted(95.0, 0.5)` → `47.5`.
4. `#weighted(88, 0.3)` → `26.4`.
5. `#weighted(90, 0.2)` → `18.0`.
6. `47.5 + 26.4 + 18.0` → `91.9`.
7. `#formatScore("Alice", 91.9)` → `RuleFunctions.formatScore("Alice", 91.9)` → `"Alice: 91.9 (A)"`.

## 7. Gotchas & takeaways

> Functions must be **static** methods. Registering an instance method causes `EvaluationException: Method 'xxx' is not static` at evaluation time. If you need instance method behavior, expose it through a bean reference (`@myBean.method(args)`) instead.

> `registerFunction` is a convenience over `setVariable` — both store the `Method` object under the name. The difference is that `registerFunction` validates the method is accessible; `setVariable` does not check. Prefer `registerFunction` for clarity.

- Overloaded function names are not supported — the last `registerFunction("name", method)` call wins. For multiple arities, use different function names (`reverse1`, `reverse2`) or a variadic method.
- Function argument coercion follows SpEL's `ConversionService`. Passing an `int` where a `double` parameter is expected converts automatically. Passing a `String` where a numeric type is expected also converts if `ConversionService` supports it.
- In Spring Security, `hasRole('ADMIN')` in `@PreAuthorize` is a registered function. Looking at `SecurityExpressionRoot` shows the full list of pre-registered functions and how they map to methods.
