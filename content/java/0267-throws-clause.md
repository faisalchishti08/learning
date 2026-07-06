---
card: java
gi: 267
slug: throws-clause
title: throws clause
---

## 1. What it is

The `throws` clause appears on a method's signature, after the parameter list, listing the checked exceptions (covered in an earlier topic) that method might propagate to its caller without catching them itself. It is purely a declaration — it does not itself throw anything — and its main effect is compiler enforcement: any checked exception listed there must be either caught or re-declared by every caller of that method.

```java
import java.io.IOException;

public class ThrowsClauseDemo {
    static void readFile(String path) throws IOException { // declares: I might propagate an IOException
        if (path == null) throw new IOException("path is null");
        System.out.println("Reading: " + path);
    }

    public static void main(String[] args) throws IOException { // propagating further, rather than catching
        readFile(null);
    }
}
```

`readFile` declares `throws IOException`, informing every caller that this checked exception is a real possibility they must plan for; `main` chooses to propagate the obligation further by declaring its own `throws IOException`, rather than catching it with a `try`/`catch` — both are legal responses to a `throws` declaration, and the choice depends on whether the calling code has enough context to actually handle the failure.

## 2. Why & when

The `throws` clause exists to make a method's checked-exception contract visible directly in its signature, turning what would otherwise be a hidden possibility into something the compiler actively verifies every caller has acknowledged.

- **Documenting failure modes in the method's public contract** — anyone reading `readFile`'s signature immediately knows it can fail with an `IOException`, without needing to read the method's implementation; this is enforced documentation, not just a comment that could grow stale.
- **Enabling the checked-exception compiler enforcement chain** — as covered in the checked-exceptions topic, every method that calls one declaring a `throws` clause for a checked exception must itself catch it or re-declare it, and `throws` is the mechanism that carries this obligation up through each layer of the call chain.
- **Multiple exceptions can be declared together** — a method can declare `throws IOException, SQLException` (comma-separated) if it might propagate either; this doesn't mean it always throws both, just that either one is a possibility a caller needs to be prepared for.

Add a `throws` clause to a method's signature whenever it can propagate a checked exception it does not catch itself — this includes both exceptions the method throws directly and checked exceptions thrown by other methods it calls without catching; never add `throws` for unchecked exceptions (`RuntimeException` subtypes), since the compiler does not require or check this for them, and doing so would only add noise without any enforcement benefit.

## 3. Core concept

```java
import java.io.IOException;

class ConfigLoader {
    String load(String path) throws IOException { // checked: caller MUST catch or re-declare
        if (path == null) throw new IOException("path is null");
        return "loaded: " + path;
    }
}

class ConfigService {
    // Option A: catch it here, and DON'T declare throws (since it's now fully handled internally)
    String loadWithDefault(String path) {
        try {
            return new ConfigLoader().load(path);
        } catch (IOException e) {
            return "default-config";
        }
    }

    // Option B: don't catch it, re-declare throws to pass the obligation to THIS method's own callers
    String loadOrFail(String path) throws IOException {
        return new ConfigLoader().load(path);
    }
}
```

`loadWithDefault` fully absorbs the checked exception with a `try`/`catch`, so it needs no `throws` clause of its own (the obligation ends here); `loadOrFail` does not catch it at all, so it must re-declare `throws IOException`, passing the same obligation on to whoever calls `loadOrFail` — both are valid, deliberate design choices depending on whether a sensible default exists at this layer.

## 4. Diagram

<svg viewBox="0 0 600 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A throws clause on a method signature declares a checked exception the method might propagate, every caller must either catch it or re-declare throws on their own signature, passing the obligation further up the chain">
  <rect x="8" y="8" width="584" height="164" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="200" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="140" y="42" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">load() throws IOException</text>

  <line x1="140" y1="55" x2="140" y2="80" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="40" y="85" width="220" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="107" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">caller catches it -- obligation ends</text>

  <rect x="330" y="85" width="220" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="440" y="107" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">caller re-declares throws -- passes it on</text>

  <text x="300" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Each layer chooses: catch it here, or declare throws and pass the obligation further up.</text>
</svg>

Each caller of a `throws`-declaring method must either catch the checked exception or re-declare it, passing the obligation on.

## 5. Runnable example

Scenario: a small user-registration flow with a checked validation exception propagating through several layers, evolved from a single throwing method into a full chain demonstrating both catching and re-declaring at different points.

### Level 1 — Basic

```java
public class ThrowsClauseBasic {
    static class InvalidEmailException extends Exception { // checked
        InvalidEmailException(String message) { super(message); }
    }

    static void validateEmail(String email) throws InvalidEmailException {
        if (!email.contains("@")) {
            throw new InvalidEmailException("missing '@' in: " + email);
        }
    }

    public static void main(String[] args) {
        try {
            validateEmail("not-an-email");
        } catch (InvalidEmailException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ThrowsClauseBasic.java`

`validateEmail` declares `throws InvalidEmailException`, and `main` catches it directly — one layer, straightforward acknowledgment of the checked exception.

### Level 2 — Intermediate

Same validation, now called from an intermediate method that does not catch it, instead re-declaring `throws` itself — demonstrating the obligation passing through a middle layer of the call chain.

```java
public class ThrowsClauseIntermediate {
    static class InvalidEmailException extends Exception {
        InvalidEmailException(String message) { super(message); }
    }

    static void validateEmail(String email) throws InvalidEmailException {
        if (!email.contains("@")) {
            throw new InvalidEmailException("missing '@' in: " + email);
        }
    }

    // Intermediate layer: does NOT catch, re-declares throws to pass the obligation further
    static void registerUser(String name, String email) throws InvalidEmailException {
        validateEmail(email);
        System.out.println("Registered: " + name + " <" + email + ">");
    }

    public static void main(String[] args) {
        try {
            registerUser("Alex", "invalid-email");
        } catch (InvalidEmailException e) {
            System.out.println("Registration failed: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ThrowsClauseIntermediate.java`

`registerUser` calls `validateEmail` without catching its checked exception, so `registerUser` itself must declare `throws InvalidEmailException` — the obligation flows from `validateEmail` through `registerUser` and is finally caught in `main`, the outermost layer in this chain.

### Level 3 — Advanced

Same registration flow, now with two different checked exceptions from two different validation steps, combined in one `throws` clause, and handled with differentiated recovery at the top level — demonstrating multiple checked exceptions declared together and distinguished by their actual types.

```java
public class ThrowsClauseAdvanced {
    static class InvalidEmailException extends Exception {
        InvalidEmailException(String message) { super(message); }
    }

    static class WeakPasswordException extends Exception {
        WeakPasswordException(String message) { super(message); }
    }

    static void validateEmail(String email) throws InvalidEmailException {
        if (!email.contains("@")) throw new InvalidEmailException("missing '@' in: " + email);
    }

    static void validatePassword(String password) throws WeakPasswordException {
        if (password.length() < 8) throw new WeakPasswordException("password too short: " + password.length() + " chars");
    }

    // Declares BOTH checked exceptions -- either might propagate from this method
    static void registerUser(String name, String email, String password)
            throws InvalidEmailException, WeakPasswordException {
        validateEmail(email);       // might throw InvalidEmailException
        validatePassword(password); // might throw WeakPasswordException
        System.out.println("Registered: " + name + " <" + email + ">");
    }

    public static void main(String[] args) {
        String[][] attempts = {
            { "Alex", "alex@example.com", "supersecure" },
            { "Sam", "bad-email", "supersecure" },
            { "Jordan", "jordan@example.com", "short" }
        };

        for (String[] attempt : attempts) {
            try {
                registerUser(attempt[0], attempt[1], attempt[2]);
            } catch (InvalidEmailException e) {
                System.out.println("Email problem for " + attempt[0] + ": " + e.getMessage());
            } catch (WeakPasswordException e) {
                System.out.println("Password problem for " + attempt[0] + ": " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java ThrowsClauseAdvanced.java`

`registerUser` declares `throws InvalidEmailException, WeakPasswordException` (comma-separated), acknowledging that either checked exception is a real possibility depending on which validation step fails first — `main` catches each type separately, with tailored messages, since the two represent genuinely different problems a user might need to fix differently.

## 6. Walkthrough

Trace the loop in `ThrowsClauseAdvanced.main` over all three attempts.

**`attempt = {"Alex", "alex@example.com", "supersecure"}`.** `registerUser("Alex", "alex@example.com", "supersecure")`: `validateEmail("alex@example.com")` checks `contains("@")` — `true`, so no exception. `validatePassword("supersecure")` checks `length() < 8` — `"supersecure"` has 11 characters, so `11 < 8` is `false`, no exception. Both validations pass, so `"Registered: Alex <alex@example.com>"` prints, and `registerUser` returns normally.

**`attempt = {"Sam", "bad-email", "supersecure"}`.** `registerUser("Sam", "bad-email", "supersecure")`: `validateEmail("bad-email")` checks `contains("@")` — `false` (no `@` present), so `InvalidEmailException("missing '@' in: bad-email")` is thrown immediately — `validatePassword` is never even called, since the method exits at this point. The `catch (InvalidEmailException e)` clause in `main` catches it. Prints `"Email problem for Sam: missing '@' in: bad-email"`.

**`attempt = {"Jordan", "jordan@example.com", "short"}`.** `registerUser("Jordan", "jordan@example.com", "short")`: `validateEmail("jordan@example.com")` passes (`contains("@")` is `true`). `validatePassword("short")` checks `length() < 8` — `"short"` has 5 characters, `5 < 8` is `true`, so `WeakPasswordException("password too short: 5 chars")` is thrown. The `catch (WeakPasswordException e)` clause catches it. Prints `"Password problem for Jordan: password too short: 5 chars"`.

```
{"Alex", "alex@example.com", "supersecure"}:
  validateEmail: contains("@") true -> passes
  validatePassword: length 11, 11<8 false -> passes
  -> "Registered: Alex <alex@example.com>"

{"Sam", "bad-email", "supersecure"}:
  validateEmail: contains("@") false -> throws InvalidEmailException -- validatePassword never runs
  -> caught -> "Email problem for Sam: missing '@' in: bad-email"

{"Jordan", "jordan@example.com", "short"}:
  validateEmail: passes
  validatePassword: length 5, 5<8 true -> throws WeakPasswordException
  -> caught -> "Password problem for Jordan: password too short: 5 chars"
```

**Final output.**
```
Registered: Alex <alex@example.com>
Email problem for Sam: missing '@' in: bad-email
Password problem for Jordan: password too short: 5 chars
```

## 7. Gotchas & takeaways

> **A `throws` clause is only ever required (and only ever checked by the compiler) for checked exceptions — never for unchecked `RuntimeException` subtypes.** Writing `void foo() throws NullPointerException` is legal but has zero enforcement effect and is widely considered misleading noise, since it looks like a meaningful contract but the compiler treats it as pure documentation with no actual obligation attached; omit `throws` for unchecked exceptions entirely.

> **Declaring `throws Exception` (the broad supertype) technically satisfies the compiler for any checked exception a method might throw, but it destroys the precision the `throws` clause is meant to provide** — callers can no longer tell from the signature alone which *specific* checked exceptions to expect, forcing them to either catch the overly broad `Exception` type or read the method's implementation to find out what can actually go wrong; always declare the most specific checked exception types a method can genuinely throw.

- The `throws` clause on a method signature declares which checked exceptions that method might propagate to its caller without catching them itself.
- Every caller of a method with a `throws` clause must either catch the declared exception(s) or re-declare them on its own signature, passing the obligation further up the call chain.
- Multiple checked exceptions can be declared together, comma-separated, when a method might propagate any one of several distinct checked failure types.
- Never add `throws` for unchecked exceptions (no enforcement benefit, just noise); always declare the most specific checked exception types possible, avoiding an overly broad `throws Exception`.
