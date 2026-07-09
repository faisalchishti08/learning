---
card: java
gi: 537
slug: map-flatmap-filter
title: map() / flatMap() / filter()
---

## 1. What it is

`Optional` supports the same three core transformation operations as `Stream`, adapted for a container that holds at most one value. `Optional.map(function)` transforms the held value if present, wrapping the result back in an `Optional` — an empty `Optional` stays empty, untouched. `Optional.flatMap(function)` is for when the transformation function itself returns an `Optional`, avoiding a nested `Optional<Optional<T>>`. `Optional.filter(predicate)` keeps the value only if it satisfies the predicate, turning a present-but-unsatisfying `Optional` into an empty one.

## 2. Why & when

These three methods let you build a chain of transformations and checks on a potentially-absent value without ever needing an explicit `isPresent()` check or unguarded `get()` call — each step in the chain automatically short-circuits to "stay empty" the moment any prior step encounters absence, exactly like a stream's pipeline propagates emptiness. This is what makes `Optional` genuinely useful beyond just being a fancy `null` wrapper: it lets you express a sequence of "if present, then do this, then that" logic as one fluent, readable chain.

## 3. Core concept

```java
import java.util.*;

record Address(String city) {}
record Person(String name, Optional<Address> address) {}

Optional<Person> maybePerson = Optional.of(new Person("Alice", Optional.of(new Address("Boston"))));

// map: transform the value if present
Optional<String> upperName = maybePerson.map(p -> p.name().toUpperCase()); // Optional[ALICE]

// flatMap: the function itself returns an Optional -- avoids Optional<Optional<Address>>
Optional<Address> address = maybePerson.flatMap(Person::address);

// filter: keep only if the value satisfies a condition
Optional<Person> longName = maybePerson.filter(p -> p.name().length() > 10); // Optional.empty -- "Alice" is short
```

`map` transforms, `flatMap` transforms-and-flattens (for functions that already return an `Optional`), `filter` conditionally empties — all three propagate emptiness automatically without any explicit checks.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="map transforms a present value, flatMap avoids nested Optionals, filter conditionally empties">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="20" width="150" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="95" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Optional[Alice]</text>
  <text x="200" y="40" fill="#8b949e" font-size="10" font-family="sans-serif">.map(toUpperCase)</text>
  <line x1="170" y1="35" x2="290" y2="35" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowOM)"/>
  <rect x="300" y="20" width="150" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="375" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Optional[ALICE]</text>

  <rect x="20" y="70" width="150" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="95" y="90" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Optional[Person]</text>
  <text x="200" y="90" fill="#8b949e" font-size="10" font-family="sans-serif">.flatMap(getAddress)</text>
  <line x1="170" y1="85" x2="290" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowOM2)"/>
  <rect x="300" y="70" width="150" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="375" y="90" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Optional[Address]</text>
  <text x="20" y="130" fill="#8b949e" font-size="10" font-family="sans-serif">flatMap avoids Optional&lt;Optional&lt;Address&gt;&gt; when getAddress() itself returns an Optional.</text>
  <defs>
    <marker id="arrowOM" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="arrowOM2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`map` produces `Optional<R>` from a plain `R`-returning function; `flatMap` avoids double-nesting when the function itself already returns an `Optional<R>`.

## 5. Runnable example

Scenario: safely navigating a chain of nested, potentially-absent fields to extract a customer's city — evolved from a plain `map` transformation, through `flatMap` for navigating nested `Optional`-returning fields, to a version combining all three operations into one fluent, null-safe chain.

### Level 1 — Basic

```java
import java.util.*;

public class OptionalMapBasic {
    public static void main(String[] args) {
        Optional<String> name = Optional.of("alice");
        Optional<String> noName = Optional.empty();

        Optional<Integer> nameLength = name.map(String::length);
        Optional<Integer> noNameLength = noName.map(String::length); // stays empty -- map never runs

        System.out.println("Name length: " + nameLength);
        System.out.println("No-name length: " + noNameLength);
    }
}
```

**How to run:** `java OptionalMapBasic.java`

Expected output:
```
Name length: Optional[5]
No-name length: Optional.empty
```

`name.map(String::length)` transforms `"alice"` into `5` (its length), wrapping the result as `Optional[5]`. `noName.map(String::length)` never even invokes `String::length`, since `noName` is already empty — `map` on an empty `Optional` simply stays empty, with no attempt to call the function on a nonexistent value.

### Level 2 — Intermediate

```java
import java.util.*;

public class OptionalFlatMap {
    record Address(String city) {}
    record Customer(String name, Optional<Address> address) {}

    public static void main(String[] args) {
        Customer withAddress = new Customer("Alice", Optional.of(new Address("Boston")));
        Customer withoutAddress = new Customer("Bob", Optional.empty());

        Optional<Customer> customer1 = Optional.of(withAddress);
        Optional<Customer> customer2 = Optional.of(withoutAddress);

        // flatMap: Customer::address ITSELF returns Optional<Address> -- avoids Optional<Optional<Address>>
        Optional<Address> address1 = customer1.flatMap(Customer::address);
        Optional<Address> address2 = customer2.flatMap(Customer::address);

        System.out.println("Address 1: " + address1);
        System.out.println("Address 2: " + address2);
    }
}
```

**How to run:** `java OptionalFlatMap.java`

Expected output:
```
Address 1: Optional[Address[city=Boston]]
Address 2: Optional.empty
```

The real-world concern this adds: `Customer::address` itself returns `Optional<Address>`, not a plain `Address`. Using `.map(Customer::address)` here would produce the awkward `Optional<Optional<Address>>` — a nested structure that's cumbersome to work with further. `.flatMap(Customer::address)` instead "flattens" the result, producing a plain `Optional<Address>` directly: present when the customer has an address, empty both when the customer itself is absent *and* when the customer exists but has no address on file, with no distinction needed between those two empty cases.

### Level 3 — Advanced

```java
import java.util.*;

public class OptionalChained {
    record Address(String city, String zipCode) {}
    record Customer(String name, Optional<Address> address) {}

    static final Map<String, Customer> CUSTOMERS = Map.of(
            "alice", new Customer("Alice", Optional.of(new Address("Boston", "02101"))),
            "bob", new Customer("Bob", Optional.empty()),
            "carol", new Customer("Carol", Optional.of(new Address("B", "00000"))) // city name too short
    );

    static Optional<Customer> findCustomer(String name) {
        return Optional.ofNullable(CUSTOMERS.get(name));
    }

    static Optional<String> resolveShippingCity(String customerName) {
        return findCustomer(customerName)
                .flatMap(Customer::address)          // navigate into the nested Optional<Address>
                .map(Address::city)                  // extract the city name
                .filter(city -> city.length() >= 2);  // reject implausibly short city names
    }

    public static void main(String[] args) {
        System.out.println("alice: " + resolveShippingCity("alice").orElse("NO VALID CITY"));
        System.out.println("bob: " + resolveShippingCity("bob").orElse("NO VALID CITY"));
        System.out.println("carol: " + resolveShippingCity("carol").orElse("NO VALID CITY"));
        System.out.println("dave: " + resolveShippingCity("dave").orElse("NO VALID CITY"));
    }
}
```

**How to run:** `java OptionalChained.java`

Expected output:
```
alice: Boston
bob: NO VALID CITY
carol: NO VALID CITY
dave: NO VALID CITY
```

This chains all three operations into one fluent pipeline: `flatMap` navigates from `Customer` into its nested `Optional<Address>`, `map` extracts the plain `city` string, and `filter` rejects implausibly short city names — each step automatically propagating emptiness from any prior step, with `.orElse(...)` supplying a final fallback. `alice` passes every step cleanly. `bob` fails at the `flatMap` step (no address at all). `carol` passes `flatMap` and `map` but fails `filter` (city `"B"` is too short). `dave` fails at the very first step, `findCustomer`, since he isn't in the map at all.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `resolveShippingCity("alice")` is called first.

`findCustomer("alice")` returns `Optional.ofNullable(CUSTOMERS.get("alice"))` — since `"alice"` is a key, this is `Optional.of(Customer("Alice", Optional.of(Address("Boston", "02101"))))`.

`.flatMap(Customer::address)` calls `Customer::address` on the held `Customer`, which itself returns `Optional.of(Address("Boston", "02101"))` — `flatMap` uses this directly as its result (no extra wrapping), so the chain now holds `Optional.of(Address("Boston", "02101"))`.

`.map(Address::city)` extracts the `city` field from the held `Address`: `"Boston"`. The chain now holds `Optional.of("Boston")`.

`.filter(city -> city.length() >= 2)` checks `"Boston".length() >= 2`, i.e. `6 >= 2`, `true` — the predicate passes, so the `Optional` remains `Optional.of("Boston")`, unchanged.

`resolveShippingCity("alice")` returns `Optional.of("Boston")`, and `.orElse("NO VALID CITY")` returns `"Boston"` directly, printed as `"alice: Boston"`.

For `resolveShippingCity("bob")`: `findCustomer("bob")` returns `Optional.of(Customer("Bob", Optional.empty()))`. `.flatMap(Customer::address)` calls `Customer::address`, which returns `Optional.empty()` (Bob has no address) — `flatMap` uses this directly, so the chain becomes `Optional.empty()`. Both `.map(Address::city)` and `.filter(...)` have nothing to operate on and simply pass the emptiness through unchanged. `.orElse("NO VALID CITY")` returns the fallback, printed as `"bob: NO VALID CITY"`.

```
alice: findCustomer->present -> flatMap(address)->present(Boston) -> map(city)->"Boston" -> filter(len>=2) T -> "Boston"
bob:   findCustomer->present -> flatMap(address)->EMPTY (no address) -> map/filter skipped -> "NO VALID CITY"
carol: findCustomer->present -> flatMap(address)->present("B") -> map(city)->"B" -> filter(len>=2) FALSE -> EMPTY -> "NO VALID CITY"
dave:  findCustomer->EMPTY (not in map) -> everything downstream skipped -> "NO VALID CITY"
```

For `resolveShippingCity("carol")`: the chain reaches `Optional.of("B")` after `map`, but `.filter(city -> city.length() >= 2)` checks `"B".length() >= 2`, i.e. `1 >= 2`, `false` — the predicate fails, so `filter` discards the value, producing `Optional.empty()`. The fallback prints as `"carol: NO VALID CITY"`.

For `resolveShippingCity("dave")`: `findCustomer("dave")` returns `Optional.empty()` immediately, since `"dave"` isn't a key in `CUSTOMERS` at all — every subsequent step (`flatMap`, `map`, `filter`) has nothing to operate on and passes the emptiness straight through, printed as `"dave: NO VALID CITY"`.

## 7. Gotchas & takeaways

> Using `.map(...)` where `.flatMap(...)` was needed produces a nested `Optional<Optional<T>>`, which is awkward to work with and usually a sign the wrong method was chosen — if the function you're passing already returns an `Optional`, that's the signal to use `flatMap` instead of `map`, mirroring the exact same distinction as `Stream.map` versus `Stream.flatMap` (see [[flatmap]]).

- `Optional.map(function)` transforms a present value, wrapping the result in a new `Optional`; an empty `Optional` stays empty untouched.
- `Optional.flatMap(function)` is for functions that themselves return an `Optional`, avoiding a nested `Optional<Optional<T>>`.
- `Optional.filter(predicate)` keeps the value only if it satisfies the predicate, turning a present-but-failing value into `Optional.empty()`.
- All three methods automatically propagate emptiness from any earlier point in the chain — once a chain becomes empty, every subsequent `map`/`flatMap`/`filter` call simply passes that emptiness through with no further work attempted.
- Chaining `flatMap`/`map`/`filter` together is the idiomatic way to safely navigate a sequence of potentially-absent, nested fields without ever writing an explicit `isPresent()` check or unguarded `get()` call.
