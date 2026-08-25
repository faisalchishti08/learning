# Java Optional

## Overview

`Optional<T>` (Java 8+) is a container object that may or may not hold a non-null value. It forces callers to think about the "no value" case, replacing implicit null checks with explicit, readable API calls.

---

## 1. Why Optional Exists

### Plain English

Before Optional, Java methods returned `null` to mean "no result". Callers either forgot to check, or the codebase filled up with `if (x != null)` everywhere. Tony Hoare called his invention of null the "billion dollar mistake" — null has no type safety, no documentation value, and causes `NullPointerException`, historically the most common exception in Java.

### Technical

`Optional<T>` is a value type (a box) that wraps a value OR represents absence. The method signature `Optional<User> findById(long id)` tells the caller: *this may not return anything — handle both cases*. A signature `User findById(long id)` carries no such contract.

### When to use

| Use Optional | Do NOT use Optional |
|---|---|
| Method return type when value may be absent | Field type in a class |
| Chaining transformations on possibly-absent values | Method parameter |
| | Collection element type |
| | `Optional<List<T>>` — return empty list instead |

```
Optional as a box:

  Present:               Empty:
  ┌─────────────┐        ┌─────────────┐
  │  "Alice"    │        │   (empty)   │
  └─────────────┘        └─────────────┘
  Optional<String>       Optional<String>
  .get() → "Alice"       .get() → NoSuchElementException
```

---

## 2. Creating Optional

### `Optional.of(value)` — value must not be null

```java
Optional<String> name = Optional.of("Alice");
System.out.println(name); // Optional[Alice]
```

**What this does:** wraps "Alice" in an Optional. If `null` is passed, throws `NullPointerException` immediately — not later.

---

### `Optional.ofNullable(value)` — safe, null becomes empty

```java
String rawName = null; // could be from DB, config, user input
Optional<String> name = Optional.ofNullable(rawName);
System.out.println(name); // Optional.empty

String realName = "Bob";
Optional<String> name2 = Optional.ofNullable(realName);
System.out.println(name2); // Optional[Bob]
```

**What this does:** if value is null returns `Optional.empty()`, else wraps it. Use this when the source is untrusted (DB result, external API, legacy code).

---

### `Optional.empty()` — explicit no-value

```java
public Optional<User> findByEmail(String email) {
    User user = db.query(email);
    if (user == null) {
        return Optional.empty(); // explicit: nothing found
    }
    return Optional.of(user);
}
```

**What this does:** returns a typed empty Optional. The caller's type system now knows to handle the absent case.

---

### Dry Run — of vs ofNullable vs empty

| Expression | Input | Result | Throws? |
|---|---|---|---|
| `Optional.of("hi")` | `"hi"` | `Optional[hi]` | No |
| `Optional.of(null)` | `null` | — | `NullPointerException` |
| `Optional.ofNullable("hi")` | `"hi"` | `Optional[hi]` | No |
| `Optional.ofNullable(null)` | `null` | `Optional.empty` | No |
| `Optional.empty()` | — | `Optional.empty` | No |

> ⚠️ **Pitfall:** `Optional.of(null)` throws NPE at creation time, not at `.get()`. This is intentional — fail fast. Always use `ofNullable` when the value might be null.

---

## 3. Checking and Getting Safely

### `isPresent()` / `isEmpty()` [Java 11+]

```java
Optional<String> opt = Optional.ofNullable(getValue());

if (opt.isPresent()) {
    System.out.println("Got: " + opt.get());
}

// Java 11+
if (opt.isEmpty()) {
    System.out.println("Nothing here");
}
```

**What this does:** `isPresent()` returns true if value present. `isEmpty()` [Java 11+] is the negation — cleaner for guard clauses.

---

### `get()` — dangerous without a check

```java
Optional<String> opt = Optional.of("hello");
String val = opt.get(); // fine here
System.out.println(val); // hello

Optional<String> empty = Optional.empty();
String boom = empty.get(); // throws NoSuchElementException
```

**What this does:** extracts the value. On empty Optional throws `NoSuchElementException`. Raw `.get()` without a preceding `isPresent()` is considered an anti-pattern (see section 7).

---

### `orElse(default)` — eager, always evaluates default

```java
String name = Optional.ofNullable(getName()).orElse("Anonymous");
System.out.println(name); // "Anonymous" if getName() returned null
```

**What this does:** returns the value if present, else returns the provided default. The default expression is **always evaluated**, even if the Optional is present.

---

### `orElseGet(Supplier)` — lazy, only evaluates if empty

```java
String name = Optional.ofNullable(getName())
    .orElseGet(() -> computeExpensiveDefault()); // only called if empty
```

**What this does:** takes a `Supplier<T>` — the lambda runs only if the Optional is empty. Prefer over `orElse` when the default is expensive (DB call, object creation).

---

### `orElseThrow()` [Java 10+] and `orElseThrow(Supplier)`

```java
// Java 10+: throws NoSuchElementException with message
User user = findById(id).orElseThrow();

// Custom exception (any Java 8+)
User user2 = findById(id)
    .orElseThrow(() -> new UserNotFoundException("User " + id + " not found"));
```

**What this does:** if present returns value; if empty throws. The no-arg version [Java 10+] throws `NoSuchElementException`. The Supplier version throws your custom exception — use this in service layers.

---

### Dry Run — orElse vs orElseGet

```java
static String expensive() {
    System.out.println("computing...");
    return "DEFAULT";
}

Optional<String> present = Optional.of("Alice");
Optional<String> empty   = Optional.empty();

present.orElse(expensive());      // prints "computing..." even though present!
empty.orElse(expensive());        // prints "computing..."

present.orElseGet(() -> expensive()); // "computing..." NOT printed
empty.orElseGet(() -> expensive());   // prints "computing..."
```

| Optional | Method | Default evaluated? | Result |
|---|---|---|---|
| `Optional["Alice"]` | `orElse(expensive())` | Yes (eager) | `"Alice"` |
| `Optional.empty` | `orElse(expensive())` | Yes (eager) | `"DEFAULT"` |
| `Optional["Alice"]` | `orElseGet(()->expensive())` | No (lazy) | `"Alice"` |
| `Optional.empty` | `orElseGet(()->expensive())` | Yes (lazy) | `"DEFAULT"` |

> ⚠️ **Pitfall:** `orElse(new HeavyObject())` always constructs `HeavyObject` even when the Optional has a value. Use `orElseGet(() -> new HeavyObject())` for any non-trivial default.

---

## 4. Transforming

### `map(Function)` — transform if present

```java
Optional<String> name = Optional.of("alice");

Optional<String> upper = name.map(String::toUpperCase);
System.out.println(upper); // Optional[ALICE]

Optional<String> empty = Optional.<String>empty().map(String::toUpperCase);
System.out.println(empty); // Optional.empty
```

**What this does:** applies the function if value is present, returns `Optional<R>`. If empty, returns `Optional.empty` without calling the function. The inner type changes but stays wrapped in Optional.

---

### `flatMap(Function<T, Optional<R>>)` — avoid nested Optional

Without flatMap — the nested problem:
```java
public Optional<String> getCity(Optional<User> optUser) {
    // map returns Optional<Optional<String>> — wrong!
    Optional<Optional<String>> nested = optUser.map(user -> user.getCity()); 
    // getCity() already returns Optional<String>
    return nested.get(); // awkward and dangerous
}
```

With flatMap — correct:
```java
public Optional<String> getCity(Optional<User> optUser) {
    return optUser.flatMap(user -> user.getCity()); // Optional<String> directly
}
```

Progressive example:
```java
Optional<String> userId = Optional.of("42");

// map: String → Optional<User>  gives Optional<Optional<User>> — BAD
Optional<Optional<User>> bad  = userId.map(id -> findUser(id));

// flatMap: String → Optional<User>  gives Optional<User> — GOOD
Optional<User> good = userId.flatMap(id -> findUser(id));

// Chain multiple flatMaps cleanly
Optional<String> city = Optional.of("42")
    .flatMap(id   -> findUser(id))       // Optional<User>
    .flatMap(user -> user.getAddress())  // Optional<Address>
    .map(addr     -> addr.getCity());    // Optional<String>
```

**What this does:** when your mapping function itself returns an Optional, `flatMap` unwraps the outer layer so you don't get `Optional<Optional<T>>`.

---

### `filter(Predicate)` — keep if condition met, else empty

```java
Optional<Integer> age = Optional.of(17);

Optional<Integer> adult = age.filter(a -> a >= 18);
System.out.println(adult); // Optional.empty (17 < 18)

Optional<Integer> teen = age.filter(a -> a >= 13);
System.out.println(teen);  // Optional[17]
```

**What this does:** if value present AND predicate is true, returns the same Optional. If predicate false or already empty, returns empty. Useful for conditional unwrapping without if-else.

---

### `or(Supplier<Optional>)` [Java 9+] — fallback Optional

```java
Optional<String> primary   = Optional.empty();
Optional<String> secondary = Optional.of("fallback");

// or() returns another Optional, unlike orElse which returns a value
Optional<String> result = primary.or(() -> secondary);
System.out.println(result); // Optional[fallback]

// Chain multiple fallbacks
Optional<User> user = findInCache(id)
    .or(() -> findInDB(id))
    .or(() -> findInLdap(id));
```

**What this does:** [Java 9+] returns the Optional itself if present, otherwise calls the Supplier to produce a fallback Optional. Unlike `orElseGet`, this stays in Optional-land — useful for chaining optional sources.

---

### Dry Run — filter + map chain

```java
Optional<String> input = Optional.of("  hello  ");

Optional<String> result = input
    .map(String::trim)         // "hello"
    .filter(s -> s.length() > 3) // true, passes through
    .map(String::toUpperCase); // "HELLO"
```

| Step | Value | Operation | Result |
|---|---|---|---|
| Start | `"  hello  "` | — | `Optional["  hello  "]` |
| `map(trim)` | `"  hello  "` | `trim()` | `Optional["hello"]` |
| `filter(len>3)` | `"hello"` (len=5) | 5>3 → true | `Optional["hello"]` |
| `map(toUpperCase)` | `"hello"` | `toUpperCase()` | `Optional["HELLO"]` |

---

## 5. Side Effects

### `ifPresent(Consumer)` — act only if present

```java
Optional<String> name = Optional.ofNullable(getUsername());

name.ifPresent(n -> System.out.println("Welcome, " + n));
// If empty: nothing happens. If present: prints welcome message.
```

**What this does:** runs the Consumer if value is present, does nothing if empty. No return value — pure side effect.

---

### `ifPresentOrElse(Consumer, Runnable)` [Java 9+]

```java
Optional<User> user = findById(id);

user.ifPresentOrElse(
    u  -> System.out.println("Found: " + u.getName()),
    () -> System.out.println("User not found, using guest session")
);
```

**What this does:** [Java 9+] runs the Consumer if present, runs the Runnable if empty. Replaces the common `if (opt.isPresent()) {...} else {...}` pattern.

---

```java
// Real-world: audit logging pattern
Optional<Order> order = orderService.find(orderId);

order.ifPresentOrElse(
    o  -> auditLog.record("ORDER_FOUND", o.getId()),
    () -> auditLog.record("ORDER_MISSING", orderId)
);
```

**What this does:** exactly one of the two branches always runs — cleaner than `isPresent()` + `if/else`.

> ⚠️ **Pitfall:** `ifPresentOrElse` is Java 9+. If targeting Java 8, use `opt.map(...).orElseGet(...)` or explicit `if (opt.isPresent())`.

---

## 6. Stream Integration

### `stream()` [Java 9+] — 0 or 1 element stream

```java
Optional<String> opt = Optional.of("hello");

opt.stream().forEach(System.out::println); // prints "hello"

Optional<String> empty = Optional.empty();
empty.stream().forEach(System.out::println); // prints nothing
```

**What this does:** [Java 9+] converts Optional to a Stream of 0 or 1 element. On empty Optional returns an empty Stream.

---

### Filter a list of Optionals

```java
List<Optional<String>> optionals = List.of(
    Optional.of("Alice"),
    Optional.empty(),
    Optional.of("Bob"),
    Optional.empty(),
    Optional.of("Carol")
);

// Java 9+: stream() elegantly flattens
List<String> names = optionals.stream()
    .flatMap(Optional::stream) // each Optional → 0 or 1 element
    .collect(Collectors.toList());

System.out.println(names); // [Alice, Bob, Carol]
```

**What this does:** `flatMap(Optional::stream)` converts each present Optional to a 1-element stream and each empty Optional to an empty stream, effectively filtering and unwrapping in one step.

---

### Real-world: resolve first non-empty result from multiple sources

```java
// Java 9+
Optional<Config> config = Stream.of(
        loadFromEnv(),      // Optional<Config>
        loadFromFile(),     // Optional<Config>
        loadDefaults()      // Optional<Config>
    )
    .flatMap(Optional::stream)
    .findFirst();
```

**What this does:** tries each source in order, takes the first that has a value. Cleaner than chained `or()` when sources come from a list.

> ⚠️ **Pitfall:** `Optional.stream()` is Java 9+. In Java 8, use `.filter(Optional::isPresent).map(Optional::get)` instead.

---

## 7. Anti-patterns

### Anti-pattern 1: Optional as a field

```java
// BAD: Optional is not Serializable, adds overhead, field always exists
class User {
    private Optional<String> nickname; // WRONG
}

// GOOD: use nullable field + Optional at the return boundary
class User {
    private String nickname; // null means absent

    public Optional<String> getNickname() {
        return Optional.ofNullable(nickname);
    }
}
```

**What this does:** the fix moves Optional to the API boundary (return type) where it belongs. The field itself stays a plain nullable type.

---

### Anti-pattern 2: Optional as method parameter

```java
// BAD: callers must wrap values just to call this method
public void sendEmail(Optional<String> to, String subject) { ... }
sendEmail(Optional.of("a@b.com"), "Hi");

// GOOD: use method overloading or @Nullable annotation
public void sendEmail(String to, String subject) { ... }
public void sendEmail(String subject) { sendEmail(DEFAULT_EMAIL, subject); }
```

**What this does:** Optional parameters force callers to wrap values unnecessarily. Overloading or null (with clear docs) is simpler.

---

### Anti-pattern 3: `Optional.get()` without check

```java
// BAD: NoSuchElementException if empty
String name = optional.get();

// GOOD: use orElse / orElseThrow / map
String name = optional.orElse("default");
String name2 = optional.orElseThrow(() -> new IllegalStateException("expected name"));
```

**What this does:** raw `.get()` is no safer than a null dereference. Always use the safe terminal methods.

---

### Anti-pattern 4: `isPresent()` + `get()` instead of `map()` / `ifPresent()`

```java
// BAD: verbose, imperative, defeats the purpose
if (optional.isPresent()) {
    String upper = optional.get().toUpperCase();
    System.out.println(upper);
}

// GOOD: functional, reads as a pipeline
optional.map(String::toUpperCase).ifPresent(System.out::println);
```

**What this does:** `isPresent()` + `get()` is just `if (x != null) use(x)` in disguise. The functional style is the whole point of Optional.

---

### Anti-pattern 5: `Optional<List<T>>`

```java
// BAD: two levels of "might be absent" — caller has to check both
public Optional<List<Order>> getOrders(long userId) { ... }

// GOOD: return empty list for "no results"
public List<Order> getOrders(long userId) {
    // return Collections.emptyList() or List.of() when no orders found
}
```

**What this does:** an absent list and an empty list mean the same thing in nearly all real code. Returning `Optional<List>` just forces double unwrapping. Same applies to `Optional<Collection>`, `Optional<Map>`, etc.

---

### Anti-pattern 6: wrapping primitives without needing to

```java
// BAD: boxing overhead
Optional<Integer> count = Optional.of(42);

// GOOD for primitive-heavy code: use OptionalInt, OptionalLong, OptionalDouble
OptionalInt count = OptionalInt.of(42);
int val = count.orElse(0);
```

**What this does:** `OptionalInt` / `OptionalLong` / `OptionalDouble` avoid boxing when you only need a primitive result. They have a smaller API than `Optional<T>` (no `map`, no `flatMap`).

---

### Quick Reference

```
Creating:
  Optional.of(val)            → present, throws NPE if null
  Optional.ofNullable(val)    → present or empty based on null
  Optional.empty()            → always empty

Getting:
  get()                       → value or NoSuchElementException (anti-pattern alone)
  orElse(def)                 → value or def (eager)
  orElseGet(supplier)         → value or supplier.get() (lazy)
  orElseThrow()               → value or NoSuchElementException [Java 10+]
  orElseThrow(supplier)       → value or your exception

Checking:
  isPresent()                 → boolean
  isEmpty()                   → boolean [Java 11+]

Transforming:
  map(fn)                     → Optional<R>
  flatMap(fn→Optional<R>)     → Optional<R>   (fn returns Optional)
  filter(pred)                → Optional<T>
  or(supplier→Optional<T>)    → Optional<T>   [Java 9+]

Side effects:
  ifPresent(consumer)         → void
  ifPresentOrElse(c, r)       → void          [Java 9+]

Streams:
  stream()                    → Stream<T>     [Java 9+]
```
