---
card: java
gi: 372
slug: enumset
title: EnumSet
---

## 1. What it is

`EnumSet` is a specialised `Set` implementation, in `java.util`, built exclusively to hold constants of a *single* enum type. Internally, it represents membership as one or more `long` values used as a bitmask, indexed by each constant's `ordinal()` — rather than the hash table or tree structure a general-purpose `HashSet` or `TreeSet` would use. You never call its constructor directly; instead you create one through static factory methods like `EnumSet.of(...)`, `EnumSet.noneOf(...)`, `EnumSet.allOf(...)`, or `EnumSet.range(...)`.

## 2. Why & when

A `HashSet<Day>` would work correctly, but it computes hash codes, handles collisions, and boxes/unboxes internal bookkeeping — all needless overhead when the entire universe of possible elements is a small, fixed, known-in-advance set (an enum's constants). `EnumSet` exploits that closed universe: since there are, say, exactly seven possible `Day` values, membership for all of them can be tracked with a single `long`'s worth of bits, and operations like add, remove, and contains become simple, extremely fast bit operations.

Reach for `EnumSet` any time you need a set of enum constants — flags representing which days a recurring event happens on, which permissions a role has, which features are enabled — instead of a general-purpose `HashSet<SomeEnum>`. It is both faster and more memory-efficient, and it also iterates in the enum's natural declaration order, which a `HashSet` does not guarantee.

## 3. Core concept

```java
import java.util.EnumSet;

public class EnumSetDemo {
    enum Day { MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY }

    public static void main(String[] args) {
        EnumSet<Day> weekend = EnumSet.of(Day.SATURDAY, Day.SUNDAY);
        EnumSet<Day> weekdays = EnumSet.complementOf(weekend); // everything NOT in weekend

        System.out.println("Weekend: " + weekend);
        System.out.println("Weekdays: " + weekdays);
        System.out.println("Is FRIDAY a weekday? " + weekdays.contains(Day.FRIDAY));
    }
}
```

**How to run:** `java EnumSetDemo.java`

`EnumSet.of(Day.SATURDAY, Day.SUNDAY)` builds a set containing exactly those two constants. `EnumSet.complementOf(weekend)` computes every `Day` constant *not* in `weekend` — internally just a bitwise NOT of the underlying bitmask, restricted to valid bits. `weekdays.contains(Day.FRIDAY)` is a single bit-check, returning `true`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="EnumSet represents membership as a bitmask indexed by ordinal, so add, remove and contains are simple bit operations instead of hashing">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">Day ordinals:  MON=0  TUE=1  WED=2  THU=3  FRI=4  SAT=5  SUN=6</text>

  <text x="20" y="65" fill="#8b949e" font-size="10">bit position:</text>
  <text x="120" y="65" fill="#8b949e" font-size="10" font-family="monospace">6 5 4 3 2 1 0</text>

  <text x="20" y="95" fill="#79c0ff" font-size="10">weekend bits:</text>
  <text x="120" y="95" fill="#79c0ff" font-size="10" font-family="monospace">1 1 0 0 0 0 0</text>
  <text x="260" y="95" fill="#8b949e" font-size="9">(SAT, SUN set)</text>

  <text x="20" y="125" fill="#6db33f" font-size="10">weekdays bits:</text>
  <text x="120" y="125" fill="#6db33f" font-size="10" font-family="monospace">0 0 1 1 1 1 1</text>
  <text x="260" y="125" fill="#8b949e" font-size="9">(complement of weekend)</text>

  <text x="20" y="150" fill="#8b949e" font-size="10">contains(FRIDAY) just checks bit 4 -- O(1), no hashing, no object comparisons.</text>
</svg>

## 5. Runnable example

Scenario: tracking which permissions a user role grants, evolved from a `HashSet`-based version, through the equivalent `EnumSet` version, to a version composing sets with union/intersection/complement to answer real access-control questions.

### Level 1 — Basic

```java
import java.util.HashSet;
import java.util.Set;

public class PermissionsHashSet {
    enum Permission { READ, WRITE, DELETE, ADMIN }

    public static void main(String[] args) {
        Set<Permission> editorPerms = new HashSet<>();
        editorPerms.add(Permission.READ);
        editorPerms.add(Permission.WRITE);

        System.out.println("Editor permissions: " + editorPerms);
        System.out.println("Can delete? " + editorPerms.contains(Permission.DELETE));
    }
}
```

**How to run:** `java PermissionsHashSet.java`

This is correct, but a plain `HashSet<Permission>` pays for general-purpose hashing machinery it doesn't need, and its iteration order isn't guaranteed to match declaration order — it may print permissions in an unpredictable sequence.

### Level 2 — Intermediate

```java
import java.util.EnumSet;

public class PermissionsEnumSet {
    enum Permission { READ, WRITE, DELETE, ADMIN }

    public static void main(String[] args) {
        EnumSet<Permission> editorPerms = EnumSet.of(Permission.READ, Permission.WRITE);

        System.out.println("Editor permissions: " + editorPerms); // always declaration order
        System.out.println("Can delete? " + editorPerms.contains(Permission.DELETE));
    }
}
```

**How to run:** `java PermissionsEnumSet.java`

Same behaviour, but `EnumSet` guarantees iteration in declaration order (`READ` before `WRITE`, always) and backs membership with a bitmask instead of a hash table — faster and lighter for this exact use case, with no code-level difference in how it's used.

### Level 3 — Advanced

```java
import java.util.EnumSet;

public class PermissionsAdvanced {
    enum Permission { READ, WRITE, DELETE, ADMIN }

    static EnumSet<Permission> viewerRole = EnumSet.of(Permission.READ);
    static EnumSet<Permission> editorRole = EnumSet.of(Permission.READ, Permission.WRITE);
    static EnumSet<Permission> adminRole = EnumSet.allOf(Permission.class); // every constant

    static boolean canDoEverythingEditorCan(EnumSet<Permission> role) {
        return role.containsAll(editorRole); // set operation, not manual looping
    }

    public static void main(String[] args) {
        EnumSet<Permission> combined = EnumSet.copyOf(viewerRole);
        combined.addAll(EnumSet.of(Permission.DELETE)); // union: viewer + delete

        System.out.println("Combined: " + combined);
        System.out.println("Admin covers editor? " + canDoEverythingEditorCan(adminRole));
        System.out.println("Combined covers editor? " + canDoEverythingEditorCan(combined));

        EnumSet<Permission> readOnlyRestriction = EnumSet.complementOf(EnumSet.of(Permission.READ));
        System.out.println("Not read-only: " + readOnlyRestriction);
    }
}
```

**How to run:** `java PermissionsAdvanced.java`

This layers real set algebra on top of `EnumSet`: `EnumSet.allOf(Permission.class)` grabs every constant at once, `containsAll` checks whether one role's permission set is a superset of another's, `addAll` performs a union, and `complementOf` computes "everything except this" — all expressed as clear, declarative set operations instead of manual loops and `if` checks.

## 6. Walkthrough

Execution starts when the class loads: `viewerRole` is set to `EnumSet.of(READ)`, `editorRole` to `EnumSet.of(READ, WRITE)`, and `adminRole` to `EnumSet.allOf(Permission.class)`, which internally sets every bit for `READ`, `WRITE`, `DELETE`, and `ADMIN` — an efficient single bitmask assignment, not a loop adding four times.

In `main`, `combined = EnumSet.copyOf(viewerRole)` creates a new, independent `EnumSet` with the same bits as `viewerRole` (just `READ` set) — copying, not aliasing, so mutating `combined` won't affect `viewerRole`. `combined.addAll(EnumSet.of(Permission.DELETE))` performs a bitwise OR between `combined`'s bitmask and a bitmask with only the `DELETE` bit set, leaving `combined` with both `READ` and `DELETE` set. This is printed as `Combined: [READ, DELETE]` — note the order matches declaration order (`READ` before `DELETE`), not insertion order.

`canDoEverythingEditorCan(adminRole)` calls `adminRole.containsAll(editorRole)`. Internally, this checks whether every bit set in `editorRole`'s bitmask (`READ`, `WRITE`) is also set in `adminRole`'s bitmask (all four bits) — true, since `adminRole` is a superset of everything. This prints `Admin covers editor? true`.

`canDoEverythingEditorCan(combined)` calls `combined.containsAll(editorRole)`. `combined` has `READ` and `DELETE` set; `editorRole` requires `READ` and `WRITE`. Since `combined` lacks the `WRITE` bit, `containsAll` returns `false`. This prints `Combined covers editor? false`.

`EnumSet.complementOf(EnumSet.of(Permission.READ))` computes the bitwise complement of a set containing only `READ`, restricted to `Permission`'s four valid bits — resulting in `[WRITE, DELETE, ADMIN]`. This is printed as `Not read-only: [WRITE, DELETE, ADMIN]`.

Expected output:
```
Combined: [READ, DELETE]
Admin covers editor? true
Combined covers editor? false
Not read-only: [WRITE, DELETE, ADMIN]
```

## 7. Gotchas & takeaways

> `EnumSet` is not thread-safe — concurrent modification from multiple threads without external synchronization can corrupt it, exactly like `HashSet`. Wrap it with `Collections.synchronizedSet(...)` if it needs to be shared across threads.

- `EnumSet` only ever holds constants of one specific enum type — you cannot mix constants from two different enums in the same `EnumSet`.
- It represents membership as a bitmask indexed by `ordinal()`, making add, remove, and contains extremely fast, single bit operations rather than hash lookups.
- Iteration order always follows the enum's declaration order, not insertion order — a guarantee `HashSet` does not provide.
- Common factory methods: `EnumSet.of(...)` for specific constants, `EnumSet.allOf(Class)` for every constant, `EnumSet.noneOf(Class)` for an empty set, `EnumSet.complementOf(set)` for everything not in a set, and `EnumSet.range(from, to)` for a contiguous declaration-order range.
- Prefer `EnumSet` over `HashSet<SomeEnum>` by default whenever the set's element type is a specific enum — there is essentially no downside and a real, measurable upside in speed and memory use.
