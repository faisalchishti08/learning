---
card: java
gi: 153
slug: touppercase-tolowercase
title: toUpperCase() / toLowerCase()
---

## 1. What it is

`toUpperCase()` returns a new string with every character converted to its uppercase form; `toLowerCase()` does the reverse, converting every character to lowercase. Like every other transforming `String` method, neither modifies the original string — both return a brand-new `String` object, leaving the original untouched (see the earlier immutability topic).

```java
String mixed = "Hello World";
System.out.println(mixed.toUpperCase()); // "HELLO WORLD"
System.out.println(mixed.toLowerCase()); // "hello world"
System.out.println(mixed);               // "Hello World" — unchanged
```

Characters that have no case (digits, punctuation, symbols) are simply left as they are — `"abc123!".toUpperCase()` produces `"ABC123!"`, with the digits and punctuation unaffected.

## 2. Why & when

Case-normalization is a common step whenever text needs to be compared, displayed, or stored in a consistent form:

- **Case-insensitive comparison workaround** — normalizing both sides to the same case before comparing with `.equals()` is functionally similar to `.equalsIgnoreCase()`, sometimes used when you need the *normalized string itself*, not just a boolean comparison result.
- **Display formatting** — uppercasing a country code, a status label, or an acronym for consistent presentation.
- **Canonicalizing input for storage or lookup** — lowercasing an email address or username before storing it, so `"Alice@Example.com"` and `"alice@example.com"` are recognized as the same account.

Overloaded variants accepting a `Locale` exist (`toUpperCase(Locale.ROOT)`) because case conversion rules vary by language in a small number of edge cases (most famously Turkish, where the uppercase of `'i'` is not the expected `'I'`) — for locale-independent, purely mechanical case conversion (e.g., normalizing internal identifiers, not user-facing language text), `Locale.ROOT` is the safer, more predictable choice than relying on the platform's default locale.

## 3. Core concept

```java
public class CaseDemo {
    public static void main(String[] args) {
        String email = "Alice.Smith@Example.COM";

        String normalized = email.toLowerCase();
        System.out.println("Normalized: " + normalized); // "alice.smith@example.com"

        String status = "active";
        String display = status.toUpperCase();
        System.out.println("Status label: [" + display + "]"); // "[ACTIVE]"
    }
}
```

`email.toLowerCase()` produces a fully lowercased copy suitable for consistent storage or comparison, while the original `email` variable still holds its original mixed-case text — both transformations are independent, non-destructive operations that simply return new strings.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Case conversion diagram: the mixed-case email address Alice dot Smith at Example dot COM is converted by toLowerCase into a fully lowercase new string, while the original string remains unchanged.">
  <rect x="8" y="8" width="684" height="134" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">email.toLowerCase() — original untouched, new string returned</text>

  <rect x="40" y="45" width="300" height="28" rx="4" fill="#1c2430" stroke="#e6edf3" stroke-width="1.5"/>
  <text x="190" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">"Alice.Smith@Example.COM"</text>
  <text x="190" y="87" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">original (unchanged)</text>

  <path d="M 370 59 L 430 59" stroke="#79c0ff" stroke-width="2" marker-end="url(#a)"/>
  <text x="400" y="49" fill="#79c0ff" font-size="8" font-family="sans-serif">toLowerCase()</text>

  <rect x="430" y="45" width="230" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="545" y="64" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">"alice.smith@example.com"</text>
  <text x="545" y="87" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">NEW object returned</text>

  <text x="350" y="120" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Punctuation (the dot and at-sign) has no case, so it passes through both strings unchanged.</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

`toLowerCase()` leaves the original string intact and returns an entirely new, fully lowercased object.

## 5. Runnable example

Scenario: registering user accounts by email, where two people typing the same address with different capitalization should be treated as the same account — starting with a basic case-insensitive registration check using `toLowerCase()` for normalization, then storing normalized emails in a lookup set, then hardening the normalization to also trim whitespace and validate the result isn't empty before using it as a key.

### Level 1 — Basic

```java
public class EmailNormalizeBasic {
    public static void main(String[] args) {
        String registered = "alice@example.com";
        String attempt = "Alice@Example.COM";

        boolean sameAccount = registered.equals(attempt.toLowerCase());
        System.out.println("Same account: " + sameAccount);
    }
}
```

**How to run:** `java EmailNormalizeBasic.java`

`attempt.toLowerCase()` converts `"Alice@Example.COM"` to `"alice@example.com"`, which then matches `registered` exactly under `.equals()` — without the `toLowerCase()` call, the direct comparison would have incorrectly reported these as different accounts.

### Level 2 — Intermediate

Same registration check, now using a `HashSet<String>` of normalized emails to track all currently registered accounts, checking new signups against it.

```java
import java.util.HashSet;
import java.util.Set;

public class EmailNormalizeIntermediate {
    public static void main(String[] args) {
        Set<String> registeredEmails = new HashSet<>();
        registeredEmails.add("alice@example.com".toLowerCase());
        registeredEmails.add("bob@example.com".toLowerCase());

        String[] signupAttempts = { "Alice@Example.com", "carol@example.com", "BOB@EXAMPLE.COM" };

        for (String attempt : signupAttempts) {
            String normalized = attempt.toLowerCase();
            if (registeredEmails.contains(normalized)) {
                System.out.println(attempt + " -> already registered");
            } else {
                registeredEmails.add(normalized);
                System.out.println(attempt + " -> newly registered as " + normalized);
            }
        }
    }
}
```

**How to run:** `java EmailNormalizeIntermediate.java`

Every email is normalized with `toLowerCase()` *before* being added to or checked against `registeredEmails` — this ensures the set's membership check (`.contains(normalized)`) always compares consistently-cased strings, so `"Alice@Example.com"` correctly matches the previously stored `"alice@example.com"`, while `"BOB@EXAMPLE.COM"` also correctly matches `"bob@example.com"`.

### Level 3 — Advanced

Same registration system, now with a **robust normalization helper** that also trims whitespace and rejects an empty result — defending against the kind of messy real-world input (accidental spaces, a blank submission) that raw `toLowerCase()` alone wouldn't catch.

```java
import java.util.HashSet;
import java.util.Set;

public class EmailNormalizeAdvanced {

    static String normalizeEmail(String rawEmail) {
        if (rawEmail == null) {
            throw new IllegalArgumentException("Email cannot be null");
        }
        String normalized = rawEmail.trim().toLowerCase();
        if (normalized.isEmpty()) {
            throw new IllegalArgumentException("Email cannot be blank");
        }
        return normalized;
    }

    public static void main(String[] args) {
        Set<String> registeredEmails = new HashSet<>();
        registeredEmails.add(normalizeEmail("alice@example.com"));

        String[] attempts = { "  Alice@Example.com  ", "BOB@EXAMPLE.COM", "   ", null };

        for (String attempt : attempts) {
            try {
                String normalized = normalizeEmail(attempt);
                boolean isDuplicate = registeredEmails.contains(normalized);
                if (!isDuplicate) registeredEmails.add(normalized);
                System.out.println("[" + attempt + "] -> " + (isDuplicate ? "already registered" : "registered as " + normalized));
            } catch (IllegalArgumentException e) {
                System.out.println("[" + attempt + "] -> rejected: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java EmailNormalizeAdvanced.java`

`normalizeEmail` chains `.trim()` before `.toLowerCase()` (order doesn't matter for correctness here, but trimming first avoids lowercasing characters that will just be discarded anyway), and validates both that the input isn't `null` and that the trimmed-and-lowercased result isn't empty — a string of only spaces (`"   "`) survives `toLowerCase()` unchanged but becomes `""` after `.trim()`, which the explicit `isEmpty()` check catches and rejects with a clear error rather than silently registering a blank "email."

## 6. Walkthrough

Trace `normalizeEmail("  Alice@Example.com  ")`:

**Null check.** The argument is not `null`, so execution proceeds.

**Trimming and lowercasing.** `rawEmail.trim()` removes the leading and trailing spaces, producing an intermediate string `"Alice@Example.com"`. `.toLowerCase()` is called on *that* intermediate result, producing `"alice@example.com"` — the final `normalized` value. Neither the original `rawEmail` nor the trimmed intermediate is modified; each step produces its own new string, exactly as immutability guarantees.

**Empty check.** `normalized.isEmpty()` is `false` (it has real content), so no exception is thrown, and `"alice@example.com"` is returned.

```
rawEmail = "  Alice@Example.com  "
null check: not null -> continue
.trim()       -> "Alice@Example.com"        (new string, spaces removed)
.toLowerCase() -> "alice@example.com"       (new string, case normalized)
isEmpty()? false -> return "alice@example.com"
```

**Back in `main`.** `registeredEmails` already contains `"alice@example.com"` (added before the loop), so `registeredEmails.contains("alice@example.com")` returns `true`, and the program prints `[  Alice@Example.com  ] -> already registered`.

**Full output.** For the four attempts: the trimmed/lowercased `"Alice@Example.com"` reports "already registered"; `"BOB@EXAMPLE.COM"` normalizes to `"bob@example.com"` and is newly registered; `"   "` normalizes to `""`, triggering the `isEmpty()` check and printing `rejected: Email cannot be blank`; and `null` is caught by the null check, printing `rejected: Email cannot be null`.

## 7. Gotchas & takeaways

> **`toUpperCase()`/`toLowerCase()` never modify the original string — always capture the return value** (`str = str.toLowerCase();` or use it directly in an expression), exactly like every other transforming `String` method covered so far. Calling `str.toLowerCase();` on its own line and discarding the result is a silent no-op.

> **Case conversion alone does not handle surrounding whitespace or `null` input** — a string of only spaces still "successfully" converts case (it just stays all spaces), and calling `.toLowerCase()` on `null` throws a `NullPointerException`; a robust normalization routine typically combines trimming, case conversion, and explicit `null`/empty checks together, as shown in Level 3.

- `toUpperCase()`/`toLowerCase()` return a new string with every cased character converted; characters with no case (digits, punctuation) pass through unchanged.
- Use case normalization before storing or comparing user-provided text (emails, usernames) where different capitalizations should be treated as equivalent.
- Combine with `.trim()` and explicit `null`/empty checks for genuinely robust input normalization, rather than relying on case conversion alone.
- For locale-sensitive text (not just internal identifiers), be aware that `toUpperCase()`/`toLowerCase()` have `Locale`-aware overloads, since a small number of languages have case rules that differ from the default.
