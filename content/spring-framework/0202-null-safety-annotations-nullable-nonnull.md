---
card: spring-framework
gi: 202
slug: null-safety-annotations-nullable-nonnull
title: "Null-safety annotations (@Nullable, @NonNull)"
---

## 1. What it is

Spring provides its own null-safety annotations — `@NonNull`, `@Nullable`, `@NonNullApi`, and `@NonNullFields` — in the `org.springframework.lang` package. These annotate method parameters, return values, and fields to declare nullability contracts explicitly, letting IDEs (IntelliJ, Eclipse) and static analysis tools (NullAway, FindBugs) flag potential `NullPointerException` sites at compile time rather than at runtime.

`@NonNull` asserts a value is never `null`. `@Nullable` asserts it may be `null` and callers must check. `@NonNullApi` applies `@NonNull` as the default for all parameters and return types in a package. `@NonNullFields` applies it to fields.

## 2. Why & when

`NullPointerException` is one of the most common runtime errors in Java. The standard fix is defensive `if (x != null)` guards everywhere, which clutters code without communicating intent. Spring's annotations:

- **Document contracts** — `@Nullable String findByEmail(String email)` clearly says "this can return null; handle it."
- **Enable IDE warnings** — IntelliJ highlights when you dereference a `@Nullable` without a null check.
- **Enable Kotlin interop** — Kotlin's null-safety system reads Spring's annotations, turning `@NonNull` into non-nullable Kotlin types and `@Nullable` into nullable (`?`) types automatically.
- **Work with static analysis** — tools like NullAway enforce the contracts at build time.

Use them on all public API surfaces of Spring beans, especially service and repository interfaces.

## 3. Core concept

Think of `@NonNull`/`@Nullable` as contracts in a service-level agreement. `@NonNull` is a promise: "I guarantee this value is not null — you don't need to check." `@Nullable` is a warning: "I might hand you null — you must handle it."

The annotations themselves are passive — they don't throw at runtime. A tool (IDE, static analyser, or Kotlin compiler) reads them and raises a warning or error.

Package-level defaults with `@NonNullApi` and `@NonNullFields`:

```java
// package-info.java
@NonNullApi
@NonNullFields
package com.example.service;
import org.springframework.lang.*;
```

Everything in that package is `@NonNull` by default. You only annotate the exceptions with `@Nullable`. This is the same convention Spring Framework's own codebase uses.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg">
  <!-- Source code box -->
  <rect x="20" y="40" width="200" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="63" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">@NonNull / @Nullable</text>
  <text x="120" y="83" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">on params, returns, fields</text>
  <line x1="40" y1="95" x2="200" y2="95" stroke="#8b949e" stroke-width="0.5"/>
  <text x="120" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">@NonNullApi</text>
  <text x="120" y="128" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">@NonNullFields</text>
  <text x="120" y="143" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">on package-info.java</text>
  <text x="120" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(sets package default)</text>

  <!-- Arrows to consumers -->
  <line x1="220" y1="80" x2="290" y2="60" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="220" y1="105" x2="290" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="220" y1="130" x2="290" y2="150" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>

  <!-- IDE -->
  <rect x="290" y="40" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="350" y="63" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">IDE warnings</text>

  <!-- Static analysis -->
  <rect x="290" y="88" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="350" y="111" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Static analysis</text>

  <!-- Kotlin -->
  <rect x="290" y="136" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="350" y="159" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Kotlin types</text>

  <!-- No runtime -->
  <rect x="460" y="88" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 2"/>
  <text x="530" y="111" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">no runtime effect</text>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>
</svg>

The annotations are consumed at development/build time by tools; they are transparent at runtime.

## 5. Runnable example

Scenario: a **user lookup service** — first showing raw null returns, then annotating the API surface, then applying package-level defaults with selective `@Nullable` overrides.

### Level 1 — Basic

Un-annotated service: the caller has no hint that `findByEmail` may return null.

```java
// NullSafetyDemo.java
public class NullSafetyDemo {
    public static void main(String[] args) {
        var repo = new UserRepository();
        // No annotation — caller has to guess whether null is possible
        String name = repo.findByEmail("unknown@example.com");
        // NPE risk: caller blindly calls toUpperCase()
        System.out.println(name.toUpperCase()); // throws NPE
    }
}

class UserRepository {
    String findByEmail(String email) {
        if ("alice@example.com".equals(email)) return "Alice";
        return null; // undocumented contract
    }
}
```

How to run: `java NullSafetyDemo.java` — throws `NullPointerException` at runtime

The contract that `findByEmail` may return null is invisible. The caller gets no compile-time warning.

---

### Level 2 — Intermediate

Annotate the API: `@Nullable` on the return type advertises the null possibility; `@NonNull` on the parameter asserts it must not be null.

```java
// NullSafetyDemo.java
// Requires spring-core.jar on classpath for org.springframework.lang annotations
import org.springframework.lang.*;

public class NullSafetyDemo {
    public static void main(String[] args) {
        var repo = new UserRepository();

        // IDE/NullAway will warn here: result of @Nullable method used without null check
        String name = repo.findByEmail("alice@example.com");
        if (name != null) {
            System.out.println("Found: " + name.toUpperCase());
        } else {
            System.out.println("User not found");
        }

        // This would generate an IDE warning: passing @Nullable to @NonNull param
        String name2 = repo.findByEmail("nobody@example.com");
        System.out.println("Safe result: " + (name2 != null ? name2 : "N/A"));
    }
}

class UserRepository {
    @Nullable
    String findByEmail(@NonNull String email) {
        if (email.isBlank()) throw new IllegalArgumentException("email must not be blank");
        if ("alice@example.com".equals(email)) return "Alice";
        return null;
    }

    @NonNull
    String getDisplayName(@NonNull String email) {
        String found = findByEmail(email);
        return found != null ? found : "Anonymous";
    }
}
```

How to run: `java -cp spring-core.jar:. NullSafetyDemo.java`

`@Nullable` on `findByEmail`'s return type makes IDEs warn if you call `.toUpperCase()` without a null check. `@NonNull` on `getDisplayName`'s return type tells callers they never need to null-check it.

---

### Level 3 — Advanced

Apply `@NonNullApi` at package level so `@NonNull` is the default; mark only the exceptions with `@Nullable`. Add a Kotlin-style pattern for safe unwrapping.

```java
// NullSafetyDemo.java
import org.springframework.lang.*;
import java.util.*;

public class NullSafetyDemo {
    public static void main(String[] args) {
        var repo = new UserRepository();

        // findByEmail is @Nullable (exception to the @NonNullApi default)
        // IDEs warn if result is dereferenced without null check
        Optional<String> result = Optional.ofNullable(repo.findByEmail("alice@example.com"));
        result.ifPresentOrElse(
            n -> System.out.println("Found: " + n),
            () -> System.out.println("Not found")
        );

        // save() is @NonNull — IDE trusts no null comes back
        String saved = repo.save(new User("bob@example.com", "Bob"));
        System.out.println("Saved ID: " + saved);

        // buildSummary() parameter is @NonNull — passing null would get IDE warning
        System.out.println(repo.buildSummary("alice@example.com"));
    }
}

// Normally this annotation lives in package-info.java:
// @NonNullApi @NonNullFields package com.example;
// Here we apply directly to the class for the demo
class UserRepository {
    private final Map<String, User> store = new HashMap<>();

    @Nullable  // exception: may return null (override of @NonNullApi default)
    public String findByEmail(String email) {
        User u = store.get(email);
        return u != null ? u.name() : null;
    }

    // @NonNull return is the default under @NonNullApi
    public String save(User user) {
        store.put(user.email(), user);
        return "id:" + user.email().hashCode();
    }

    public String buildSummary(String email) {
        String name = findByEmail(email);
        return name != null
            ? "User{email=" + email + ", name=" + name + "}"
            : "User{email=" + email + ", name=<not found>}";
    }
}

record User(String email, String name) {}
```

How to run: `java -cp spring-core.jar:. NullSafetyDemo.java`

Under `@NonNullApi`, every method return type and parameter is implicitly `@NonNull`. Only `findByEmail` overrides this with `@Nullable`. This inverts the noise: most methods need no annotation, and `@Nullable` stands out as a meaningful signal. `Optional.ofNullable` wraps the nullable result into an explicit null-safe container.

## 6. Walkthrough

**Annotation retention:** All four annotations have `@Retention(RetentionPolicy.RUNTIME)`, so tools can read them via reflection at both compile time and runtime. They carry `@Documented` so they appear in Javadoc.

**IDE processing (IntelliJ example):**
1. IntelliJ's null-analysis engine reads `@Nullable` on `findByEmail`'s return type.
2. When it sees `String name = repo.findByEmail(…)` followed by `name.toUpperCase()`, it detects that `name` could be null and underlines the dereference with a warning: *"Method invocation 'toUpperCase' may produce NullPointerException"*.
3. For `@NonNull` parameters, calling `repo.buildSummary(null)` triggers: *"Passing 'null' argument to parameter annotated as @NotNull"*.

**Kotlin interop:**
When Kotlin compiles against `UserRepository.class`, the Kotlin compiler reads `@Nullable`/`@NonNull` from the class metadata. `findByEmail` becomes `fun findByEmail(email: String): String?` in Kotlin (nullable return) and `save` becomes `fun save(user: User): String` (non-nullable). You get Kotlin's `?` safe-call operators and compile-time null checks for free.

**`@NonNullApi` scope:**
Placed in `package-info.java`, `@NonNullApi` instructs annotation processors to treat all methods' parameters and return types in the package as `@NonNull`. Each method that legitimately returns null must override with `@Nullable`. This is the strategy Spring Framework itself uses: the vast majority of its API is non-null; the nullable parts are explicitly marked.

**No runtime enforcement:**
The annotations themselves do not add null checks. Nothing throws at runtime when you pass null to a `@NonNull` parameter. They are documentation/tooling hints. For runtime enforcement use `Objects.requireNonNull(x)` or Bean Validation's `@NotNull` (which Hibernate Validator does enforce at runtime).

**Output of Level 3:**
```
Found: Alice
Saved ID: 1604273198
User{email=alice@example.com, name=Alice}
```

## 7. Gotchas & takeaways

> **`@NonNull` does not throw at runtime.** Passing `null` to a `@NonNull` parameter silently succeeds unless you add a manual `Objects.requireNonNull(…)` check. The annotation is a hint to tools, not a guard.

> **Spring's `@NonNull` vs JSR-305's `@Nonnull`.** They are different types. IntelliJ understands both. NullAway understands JSR-305. Spring Core deliberately provides its own to avoid the JSR-305 dependency. Pick the one your tool understands, or use `@NonNullApi` at the package level which most modern tools honour.

- `@Nullable` and `@NonNull` apply to elements, not types — they go before the method/parameter/field declaration.
- `@NonNullApi` covers method parameters and return types; it does NOT cover fields — use `@NonNullFields` separately for fields.
- `package-info.java` must be in the same source root and package as the classes it annotates.
- These annotations improve the codebase's null-safety story gradually — you don't need to annotate everything at once. Start with public API surfaces.
- Bean Validation's `@NotNull` (javax/jakarta) is enforced at runtime by validators; Spring's `@NonNull` is not. They serve different purposes and can coexist.
