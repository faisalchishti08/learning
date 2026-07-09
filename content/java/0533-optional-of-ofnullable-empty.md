---
card: java
gi: 533
slug: optional-of-ofnullable-empty
title: Optional.of / ofNullable / empty
---

## 1. What it is

`Optional<T>` is a container object that either holds a non-null value or holds nothing. Three static factory methods create one: `Optional.of(value)` wraps a value that is guaranteed non-null, throwing `NullPointerException` immediately if you pass `null`. `Optional.ofNullable(value)` accepts either a value or `null`, producing a present `Optional` for a value and an empty `Optional` for `null`. `Optional.empty()` explicitly creates an empty `Optional` with no value at all.

## 2. Why & when

`Optional` exists to make the possibility of "no value" an explicit, visible part of a method's return type, instead of a `null` that callers can easily forget to check for. Choosing the right factory method communicates intent clearly: `Optional.of(...)` says "this value is never null here — if it somehow is, that's a bug, fail loudly and immediately." `Optional.ofNullable(...)` says "this value might legitimately be null, and that's fine — wrap it safely either way." `Optional.empty()` says "there's definitively no value to return here."

## 3. Core concept

```java
import java.util.*;

Optional<String> present = Optional.of("hello");        // guaranteed non-null -- throws if null passed
Optional<String> maybeNull = Optional.ofNullable(getNameOrNull()); // safely wraps either case
Optional<String> nothing = Optional.empty();             // explicitly, deliberately empty

// Optional.of(null); // throws NullPointerException immediately, right at creation
```

`Optional.of` is a strict assertion of non-nullness; `Optional.ofNullable` is a defensive wrapper for values that might be null; `Optional.empty` is an explicit "nothing here" value.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Optional.of throws on null, ofNullable safely handles either case, empty is explicitly nothing">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="20" width="180" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="110" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">of("hello") -&gt; Optional[hello]</text>
  <rect x="20" y="60" width="180" height="30" rx="4" fill="#1c2430" stroke="#f85149"/><text x="110" y="80" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">of(null) -&gt; throws NPE</text>
  <rect x="230" y="20" width="200" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="330" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ofNullable("hi") -&gt; Optional[hi]</text>
  <rect x="230" y="60" width="200" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="330" y="80" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ofNullable(null) -&gt; Optional.empty</text>
  <rect x="450" y="40" width="150" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/><text x="525" y="60" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">empty() -&gt; Optional.empty</text>
</svg>

`of` demands a value and fails loudly without one; `ofNullable` accommodates both cases safely; `empty` is the deliberate, explicit "nothing" value.

## 5. Runnable example

Scenario: looking up a user's profile settings, some of which are genuinely optional — evolved from choosing between `of` and `ofNullable` correctly, through a realistic lookup returning `ofNullable`-wrapped results, to a version distinguishing "field genuinely absent" from "a bug produced an unexpected null."

### Level 1 — Basic

```java
import java.util.*;

public class OptionalFactoryBasic {
    public static void main(String[] args) {
        String username = "alice"; // guaranteed non-null in this context
        Optional<String> presentUser = Optional.of(username);
        System.out.println("Present user: " + presentUser);

        String nickname = null; // this field is genuinely optional and may be absent
        Optional<String> maybeNickname = Optional.ofNullable(nickname);
        System.out.println("Maybe nickname: " + maybeNickname);

        Optional<String> noBioYet = Optional.empty();
        System.out.println("Bio: " + noBioYet);
    }
}
```

**How to run:** `java OptionalFactoryBasic.java`

Expected output:
```
Present user: Optional[alice]
Maybe nickname: Optional.empty
Bio: Optional.empty
```

`Optional.of(username)` is used because `username` is known to always be non-null in this context — if it somehow weren't, `Optional.of` would throw immediately, surfacing the bug right at its source. `Optional.ofNullable(nickname)` safely handles `nickname` being `null`, producing an empty `Optional` without throwing. `Optional.empty()` explicitly represents "no bio has been set" with no value involved at all.

### Level 2 — Intermediate

```java
import java.util.*;

public class OptionalLookup {
    record UserProfile(String username, String bio) {}

    static final Map<String, UserProfile> PROFILES = Map.of(
            "alice", new UserProfile("alice", "Loves Java streams"),
            "bob", new UserProfile("bob", null) // bob genuinely has no bio set
    );

    static Optional<UserProfile> findProfile(String username) {
        return Optional.ofNullable(PROFILES.get(username)); // Map.get returns null for a missing key
    }

    public static void main(String[] args) {
        Optional<UserProfile> aliceProfile = findProfile("alice");
        Optional<UserProfile> carolProfile = findProfile("carol"); // doesn't exist at all

        System.out.println("Alice found: " + aliceProfile.isPresent());
        System.out.println("Carol found: " + carolProfile.isPresent());

        aliceProfile.ifPresent(p -> {
            Optional<String> bio = Optional.ofNullable(p.bio());
            System.out.println("Alice's bio present: " + bio.isPresent());
        });
    }
}
```

**How to run:** `java OptionalLookup.java`

Expected output:
```
Alice found: true
Carol found: false
Alice's bio present: true
```

The real-world concern this adds: `Map.get(key)` is a classic source of `null` — it returns `null` both when a key genuinely maps to `null` and when the key simply isn't present at all. Wrapping it with `Optional.ofNullable(PROFILES.get(username))` converts that ambiguous `null` into an explicit `Optional`, so callers of `findProfile` never have to remember to null-check the map's raw return value themselves.

### Level 3 — Advanced

```java
import java.util.*;

public class OptionalContractViolation {
    record ApiResponse(String userId, String displayName) {}

    // A method that PROMISES userId is never null (an API contract) -- Optional.of enforces that promise.
    static Optional<String> extractUserId(ApiResponse response) {
        return Optional.of(response.userId()); // deliberately strict: userId is documented as always present
    }

    // displayName, by contrast, is documented as genuinely optional in the API.
    static Optional<String> extractDisplayName(ApiResponse response) {
        return Optional.ofNullable(response.displayName());
    }

    public static void main(String[] args) {
        ApiResponse validResponse = new ApiResponse("u123", "Alice");
        System.out.println("Valid userId: " + extractUserId(validResponse));
        System.out.println("Valid displayName: " + extractDisplayName(validResponse));

        ApiResponse malformedResponse = new ApiResponse(null, "Bob"); // violates the documented contract
        try {
            extractUserId(malformedResponse); // Optional.of catches the contract violation immediately
        } catch (NullPointerException e) {
            System.out.println("Contract violation caught immediately: userId was unexpectedly null");
        }

        // displayName being null, by contrast, is a perfectly normal, expected case -- no exception.
        ApiResponse noDisplayName = new ApiResponse("u456", null);
        System.out.println("Missing displayName handled safely: " + extractDisplayName(noDisplayName));
    }
}
```

**How to run:** `java OptionalContractViolation.java`

Expected output:
```
Valid userId: Optional[u123]
Valid displayName: Optional[Alice]
Contract violation caught immediately: userId was unexpectedly null
Missing displayName handled safely: Optional.empty
```

This uses `Optional.of` deliberately as a **contract enforcement** tool: `extractUserId` documents (via its use of `Optional.of` rather than `ofNullable`) that `userId` is *supposed* to always be present according to the API's contract — if a malformed response somehow violates that contract, `Optional.of` throws immediately at the point of the violation, rather than letting a silent `null` propagate deeper into the program where it would be much harder to trace back to its actual source. `displayName`, documented as genuinely optional, uses `ofNullable` and handles a missing value gracefully with no exception at all.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `malformedResponse` is deliberately constructed with `userId = null`, violating what the API is documented to guarantee.

`extractUserId(malformedResponse)` is called inside a `try` block. Inside `extractUserId`, `Optional.of(response.userId())` is evaluated: `response.userId()` returns `null` (from the malformed response). `Optional.of(null)` immediately checks its argument for nullness — since it received `null`, it throws `NullPointerException` right at this point, before even constructing an `Optional` instance.

This exception propagates up out of `extractUserId` and is caught by the surrounding `try`/`catch` in `main`. The `catch (NullPointerException e)` block prints `"Contract violation caught immediately: userId was unexpectedly null"` — the key point being *where* the failure is detected: right at the boundary where the malformed data first entered the `Optional`-wrapping code, rather than silently passing `null` deeper into the program where a `NullPointerException` might surface much later, in unrelated code, making the actual root cause far harder to trace.

```
extractUserId(malformedResponse):
  response.userId() -> null
  Optional.of(null) -> throws NullPointerException IMMEDIATELY, at the contract boundary

vs. if this had used Optional.ofNullable instead:
  Optional.ofNullable(null) -> Optional.empty(), no exception
  (the contract violation would go undetected here, potentially causing confusing bugs downstream)
```

Afterward, `noDisplayName` is constructed with `displayName = null` — but since this field is documented as genuinely optional, `extractDisplayName(noDisplayName)` calls `Optional.ofNullable(response.displayName())`, which safely produces `Optional.empty()` with no exception at all, printed as `"Missing displayName handled safely: Optional.empty"` — demonstrating that the *same* underlying `null` value is handled completely differently depending on whether it represents an expected, normal case (`ofNullable`) or a genuine contract violation (`of`).

## 7. Gotchas & takeaways

> Using `Optional.of(...)` on a value that *can* legitimately be `null` turns an entirely normal, expected case into an unhandled `NullPointerException` — the wrong factory method choice can convert benign missing data into a crash. Conversely, using `Optional.ofNullable(...)` where `Optional.of(...)` would be more appropriate silently masks genuine bugs (an unexpected `null` where the contract promised otherwise) as an innocuous empty `Optional`, potentially hiding the problem until much later. Choosing correctly between the two is a real design decision, not an arbitrary style choice.

- `Optional.of(value)` throws `NullPointerException` immediately if `value` is `null` — use it only when `null` genuinely should never happen and represents a bug if it does.
- `Optional.ofNullable(value)` safely handles both a present value and `null`, producing an empty `Optional` for the latter — use it when `null`/absence is a normal, expected possibility.
- `Optional.empty()` explicitly creates an empty `Optional` with no value, useful when a method has determined upfront that there's nothing to return.
- `Map.get(key)`'s `null` return (ambiguous between "key absent" and "key maps to null") is a classic case where `Optional.ofNullable(map.get(key))` cleans up the ambiguity for callers.
- The choice between `of` and `ofNullable` communicates intent and can double as a lightweight, fail-fast contract check — a wrong choice either crashes on expected data or silently swallows genuine bugs.
