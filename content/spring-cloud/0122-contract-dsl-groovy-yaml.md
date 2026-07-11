---
card: spring-cloud
gi: 122
slug: contract-dsl-groovy-yaml
title: "Contract DSL (Groovy/YAML)"
---

## 1. What it is

Spring Cloud Contract's Groovy DSL and equivalent YAML format are two interchangeable ways of writing the same contract definition — a `request` block (method, URL, headers, body, and matching rules) paired with a `response` block (status, headers, body) — with the DSL additionally supporting dynamic matchers (regex patterns, type matchers) so a contract can assert "this field must be a valid email format" rather than requiring an exact hardcoded string match, letting contracts stay meaningful across realistic, varying data.

```groovy
Contract.make {
    request {
        method POST()
        url '/orders'
        body(customerEmail: $(regex(email())), amount: 49.99)
    }
    response {
        status CREATED()
        body(id: $(anyPositiveInt()), status: "PENDING")
    }
}
```

```yaml
request:
  method: POST
  url: /orders
  body:
    customerEmail: "test@example.com"
    amount: 49.99
  matchers:
    body:
      - path: $.customerEmail
        type: by_regex
        predefined: email
```

## 2. Why & when

A contract asserting an exact, hardcoded value for every field (`customerEmail: "test@example.com"`, matched literally) is brittle in a subtle way: it forces every request the real implementation handles to use that exact literal value to pass verification, even though the real API obviously needs to accept *any* validly-formatted email, not one specific string. Matchers solve this by separating what's used to generate example requests/responses (a concrete value, needed for the actual HTTP call the generated tests make) from what's actually asserted (a pattern or type constraint, checked against the real response) — a regex matcher on an email field lets the contract assert "this must look like an email" without over-constraining the producer's implementation to return that one specific test email address.

Reach for advanced DSL features (matchers, dynamic values) when:

- A field's exact value is inherently variable in real usage (an ID, a timestamp, a generated token) but the contract still needs to assert *something* meaningful about its shape or type — `anyPositiveInt()`, `anyUuid()`, and similar built-in matchers express "must be a valid X" without pinning down one specific literal.
- A field must match a specific format without being one fixed value — `regex(email())`, or a custom regex pattern, expresses format constraints precisely.
- Choosing between the Groovy DSL and YAML format for a given team — Groovy offers more expressive power (helper functions, programmatic contract generation) while YAML is often preferred for teams wanting a format with no Groovy/JVM-specific syntax to learn, especially useful if non-JVM consumer teams need to read or even author contracts themselves.

## 3. Core concept

```
 a contract field can specify TWO things simultaneously:
   the value used to build the actual example request/response (for running real HTTP calls in tests)
   the matcher used to assert against the ACTUAL value received (for verifying correctness)

 customerEmail: $(regex(email()))
   -- when GENERATING a request: substitutes a valid example email (e.g. "abc123@example.com")
   -- when VERIFYING a response:  asserts the ACTUAL value matches the email regex pattern
                                   (not that it equals one specific hardcoded string)

 anyPositiveInt() similarly generates an example positive integer, but asserts only "is a positive integer"
```

This two-purpose design (a concrete generation value plus an assertion pattern) is what lets contracts be both runnable (real HTTP calls need real values) and appropriately loose (assertions shouldn't over-constrain naturally-variable fields).

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A contract field using a regex matcher serves two purposes generating a concrete example value for running real test requests and asserting a pattern constraint against the actual value received rather than an exact literal match">
  <rect x="230" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="48" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">$(regex(email()))</text>

  <rect x="30" y="110" width="220" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="140" y="130" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">generation</text>
  <text x="140" y="144" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">concrete example: "abc@example.com"</text>

  <rect x="390" y="110" width="220" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="500" y="130" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">assertion</text>
  <text x="500" y="144" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">matches EMAIL PATTERN, not one literal</text>

  <defs><marker id="a122" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="280" y1="66" x2="150" y2="110" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a122)"/>
  <line x1="360" y1="66" x2="490" y2="110" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a122)"/>
</svg>

One DSL declaration, two distinct downstream uses — a concrete value for running tests, a loose pattern for asserting correctness.

## 5. Runnable example

The scenario: model a contract field defined with both a generation value and a matcher pattern, used first to build an example request, then to verify an arbitrary real response against the pattern rather than the literal example value. Start with exact-literal matching (the brittle baseline), then add regex-pattern matching, then add multiple matcher types together (regex plus a numeric-range matcher) on a realistic multi-field contract.

### Level 1 — Basic

Exact-literal matching — the brittle baseline before matchers are introduced.

```java
import java.util.*;

public class ContractDslLevel1 {
    record Contract(Map<String, String> requestBody, Map<String, String> expectedResponseBody) {}

    static boolean verifyExact(Map<String, String> actual, Map<String, String> expected) {
        return actual.equals(expected); // requires an EXACT match, field by field
    }

    public static void main(String[] args) {
        Contract contract = new Contract(
                Map.of("customerEmail", "test@example.com"),
                Map.of("id", "42", "status", "PENDING")
        );

        Map<String, String> realResponse = Map.of("id", "43", "status", "PENDING"); // id is DIFFERENT -- realistic!

        System.out.println("exact match against real response: " + verifyExact(realResponse, contract.expectedResponseBody()));
    }
}
```

How to run: `java ContractDslLevel1.java`

`verifyExact` returns `false`, because the real response's `id` (`"43"`) doesn't literally equal the contract's hardcoded example `id` (`"42"`) — this is exactly the brittleness problem: an `id` field is inherently variable in real usage, and exact-literal matching wrongly treats that natural variability as a contract violation.

### Level 2 — Intermediate

Add regex-pattern matching for the variable `id` field, correctly distinguishing "this looks like a valid positive integer" from "this equals one specific literal."

```java
import java.util.*;
import java.util.regex.Pattern;

public class ContractDslLevel2 {
    interface Matcher { boolean matches(String actualValue); }

    record RegexMatcher(String pattern) implements Matcher {
        public boolean matches(String actualValue) { return Pattern.matches(pattern, actualValue); }
    }
    record ExactMatcher(String expectedValue) implements Matcher {
        public boolean matches(String actualValue) { return expectedValue.equals(actualValue); }
    }

    record Contract(Map<String, Matcher> responseMatchers) {}

    static boolean verify(Map<String, String> actual, Contract contract) {
        for (Map.Entry<String, Matcher> entry : contract.responseMatchers().entrySet()) {
            String actualValue = actual.get(entry.getKey());
            if (!entry.getValue().matches(actualValue)) {
                System.out.println("FAILED: field '" + entry.getKey() + "' value '" + actualValue + "' does not match");
                return false;
            }
        }
        return true;
    }

    public static void main(String[] args) {
        Contract contract = new Contract(Map.of(
                "id", new RegexMatcher("\\d+"),          // "any positive integer" -- not one fixed literal
                "status", new ExactMatcher("PENDING")     // status IS asserted as an exact literal, deliberately
        ));

        Map<String, String> realResponse = Map.of("id", "43", "status", "PENDING"); // id VARIES, that's fine now

        System.out.println("regex-aware match against real response: " + verify(realResponse, contract));
    }
}
```

How to run: `java ContractDslLevel2.java`

`verify` now returns `true`, because `id`'s `RegexMatcher("\\d+")` correctly accepts `"43"` as "a valid sequence of digits," while `status`'s `ExactMatcher` still requires the literal `"PENDING"` — this mirrors the real DSL's ability to mix matcher types per field: some fields genuinely do need exact assertions (an enum-like status value), while others (an auto-generated ID) need only a shape/type assertion.

### Level 3 — Advanced

Add multiple matcher types on a richer, multi-field contract (regex for an email, a numeric-range matcher for an amount, an exact matcher for a status) and demonstrate the contract correctly rejecting a response that violates just one of several matchers.

```java
import java.util.*;
import java.util.regex.Pattern;

public class ContractDslLevel3 {
    interface Matcher { boolean matches(Object actualValue); }

    record RegexMatcher(String pattern) implements Matcher {
        public boolean matches(Object actualValue) { return Pattern.matches(pattern, (String) actualValue); }
    }
    record ExactMatcher(Object expectedValue) implements Matcher {
        public boolean matches(Object actualValue) { return expectedValue.equals(actualValue); }
    }
    record RangeMatcher(double min, double max) implements Matcher {
        public boolean matches(Object actualValue) {
            double v = (Double) actualValue;
            return v >= min && v <= max;
        }
    }

    record Contract(Map<String, Matcher> responseMatchers) {}

    static List<String> verify(Map<String, Object> actual, Contract contract) {
        List<String> violations = new ArrayList<>();
        for (Map.Entry<String, Matcher> entry : contract.responseMatchers().entrySet()) {
            Object actualValue = actual.get(entry.getKey());
            if (!entry.getValue().matches(actualValue)) {
                violations.add("field '" + entry.getKey() + "' value '" + actualValue + "' violates its matcher");
            }
        }
        return violations;
    }

    public static void main(String[] args) {
        Contract contract = new Contract(Map.of(
                "customerEmail", new RegexMatcher("^[\\w.]+@[\\w.]+$"),
                "amount", new RangeMatcher(0.01, 10000.00),
                "status", new ExactMatcher("PENDING")
        ));

        Map<String, Object> validResponse = Map.of("customerEmail", "abc@example.com", "amount", 49.99, "status", "PENDING");
        Map<String, Object> invalidResponse = Map.of("customerEmail", "abc@example.com", "amount", 99999.99, "status", "PENDING");

        System.out.println("valid response violations: " + verify(validResponse, contract));
        System.out.println("invalid response violations: " + verify(invalidResponse, contract));
    }
}
```

How to run: `java ContractDslLevel3.java`

`validResponse` produces an empty violations list — every field satisfies its matcher; `invalidResponse` produces exactly one violation, for `amount` (`99999.99` falls outside the `RangeMatcher(0.01, 10000.00)` bounds), while `customerEmail` and `status` are correctly reported as fine, since only `amount` actually violates its constraint — this field-by-field independence is exactly how a real Spring Cloud Contract verification reports precisely which part of a response diverged from the contract, rather than a single opaque pass/fail.

## 6. Walkthrough

Trace `verify(invalidResponse, contract)` in Level 3.

1. `verify` iterates `contract.responseMatchers()`'s three entries, in some order — for each, it looks up the corresponding value in `actual` (here, `invalidResponse`) and calls that field's matcher.
2. For `"customerEmail"`, `RegexMatcher("^[\\w.]+@[\\w.]+$").matches("abc@example.com")` evaluates `Pattern.matches(...)` against that string — it matches the pattern, so `matches` returns `true`, and no violation is added for this field.
3. For `"amount"`, `RangeMatcher(0.01, 10000.00).matches(99999.99)` casts the value to `double` and checks `v >= 0.01 && v <= 10000.00` — `99999.99` is well above `10000.00`, so this evaluates `false`, and `matches` returns `false`.
4. Because `matches` returned `false` for `"amount"`, the `if (!entry.getValue().matches(actualValue))` check is `true`, so a violation string is added: `"field 'amount' value '99999.99' violates its matcher"`.
5. For `"status"`, `ExactMatcher("PENDING").matches("PENDING")` checks `"PENDING".equals("PENDING")`, which is `true`, so no violation is added for this field.
6. `verify` returns a list containing exactly one violation string — the `amount` field's — correctly and specifically identifying which single field, out of three, actually diverged from the contract, rather than a single all-or-nothing verdict that would leave a developer guessing which part of the response was actually wrong.

```
verify(invalidResponse, contract):
  customerEmail: matches regex        -> OK, no violation
  amount:        99999.99 not in [0.01, 10000.00] -> VIOLATION added
  status:        exact match "PENDING" -> OK, no violation

result: ["field 'amount' value '99999.99' violates its matcher"]   <- ONE specific, actionable violation
```

## 7. Gotchas & takeaways

> **Gotcha:** the value used to *generate* an example request or response (needed for the actual HTTP calls Spring Cloud Contract's generated tests make) and the matcher used to *verify* the real response are conceptually two separate things, even when written together in one DSL expression like `$(regex(email()))` — forgetting this can lead to confusion about why a contract's generated example uses one specific value while still asserting a much looser pattern; both roles are intentional and serve different needs (a runnable HTTP call needs a concrete value; a meaningful assertion needs an appropriately-scoped pattern).

- Matchers exist specifically to avoid over-constraining naturally-variable fields (IDs, timestamps, generated tokens) to one exact literal value, while still asserting something meaningful about their format or type — this is what keeps contracts both precise and realistic.
- Choosing exact matching versus a looser matcher per field is a deliberate design decision for each contract — fields with a genuinely fixed, small set of valid values (an enum-like status) are often best matched exactly, while inherently variable fields need pattern or type matchers instead.
- Groovy and YAML are two syntaxes for the identical underlying contract model — the choice between them is largely a team/tooling preference (Groovy's programmatic expressiveness versus YAML's simpler, JVM-agnostic syntax), not a difference in what contracts are capable of expressing.
- Reporting violations field-by-field, as Level 3 modeled, rather than a single pass/fail verdict, is what makes contract verification failures immediately actionable — a developer seeing exactly which field and why doesn't need to manually diff an entire response to find the actual problem.
