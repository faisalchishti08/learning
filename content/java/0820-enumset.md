---
card: java
gi: 820
slug: enumset
title: EnumSet
---

## 1. What it is

`EnumSet<E extends Enum<E>>` is a specialized [`Set`](0803-set.md) implementation that only holds values from a single enum type, internally represented as a **bit vector** — one bit per possible enum constant — rather than a hash table or tree. Because every operation reduces to bitwise arithmetic on a fixed-size number (or array of numbers, for enums with more than 64 constants), `EnumSet` operations are extremely fast and use far less memory than an equivalent `HashSet<E>`. It's created via static factory methods rather than a constructor: `EnumSet.of(...)`, `EnumSet.allOf(Class)`, `EnumSet.noneOf(Class)`, `EnumSet.range(from, to)`, and `EnumSet.complementOf(otherSet)`.

## 2. Why & when

Whenever a set's element type is a fixed, known-in-advance enum — permissions, feature flags, days of the week, state-machine states — `EnumSet` is a strict upgrade over `HashSet<E>`: same `Set` interface, same semantics, but backed by a bit vector instead of hash buckets, so `add`/`remove`/`contains` become simple bit operations (set a bit, clear a bit, test a bit) instead of hash computation and bucket traversal. It also iterates in the enum constants' declaration order automatically, with no configuration needed. Reach for `EnumSet` any time a `Set<SomeEnum>` is needed — there's essentially no downside relative to `HashSet<SomeEnum>`, and the performance and memory wins are real, especially for sets constructed and checked frequently (permission checks on every request, for example).

## 3. Core concept

```java
enum Permission { READ, WRITE, DELETE, ADMIN }

EnumSet<Permission> userPerms = EnumSet.of(Permission.READ, Permission.WRITE);
EnumSet<Permission> allPerms = EnumSet.allOf(Permission.class);
EnumSet<Permission> noPerms = EnumSet.noneOf(Permission.class);
EnumSet<Permission> readOnly = EnumSet.range(Permission.READ, Permission.READ);
EnumSet<Permission> everythingExceptAdmin = EnumSet.complementOf(EnumSet.of(Permission.ADMIN));

userPerms.contains(Permission.DELETE); // false -- O(1) bit test
```

Internally, `userPerms` is just an integer (or small array of longs) with bits 0 and 1 set — `contains(DELETE)` is a single bitmask test against bit 2, not a hash lookup.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An EnumSet is represented internally as a bit vector, one bit per enum constant">
  <text x="320" y="25" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">EnumSet.of(READ, WRITE) for enum {READ, WRITE, DELETE, ADMIN}</text>

  <g font-family="sans-serif">
    <rect x="150" y="50" width="80" height="50" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
    <text x="190" y="80" fill="#3fb950" font-size="14" text-anchor="middle">1</text>
    <text x="190" y="35" fill="#8b949e" font-size="9" text-anchor="middle">READ</text>

    <rect x="230" y="50" width="80" height="50" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
    <text x="270" y="80" fill="#3fb950" font-size="14" text-anchor="middle">1</text>
    <text x="270" y="35" fill="#8b949e" font-size="9" text-anchor="middle">WRITE</text>

    <rect x="310" y="50" width="80" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
    <text x="350" y="80" fill="#8b949e" font-size="14" text-anchor="middle">0</text>
    <text x="350" y="35" fill="#8b949e" font-size="9" text-anchor="middle">DELETE</text>

    <rect x="390" y="50" width="80" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
    <text x="430" y="80" fill="#8b949e" font-size="14" text-anchor="middle">0</text>
    <text x="430" y="35" fill="#8b949e" font-size="9" text-anchor="middle">ADMIN</text>
  </g>
  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">contains(DELETE) is one bitmask test against bit 2 — no hashing, no bucket traversal</text>
</svg>

*Each enum constant maps to exactly one bit position — every set operation is bitwise arithmetic.*

## 5. Runnable example

Scenario: a role-based permission system, growing from basic permission checks to combining permission sets via set algebra, to a compact, high-frequency access-control check simulating a real request-handling hot path.

### Level 1 — Basic

```java
import java.util.*;

public class PermissionsBasic {
    enum Permission { READ, WRITE, DELETE, ADMIN }

    public static void main(String[] args) {
        EnumSet<Permission> editorPerms = EnumSet.of(Permission.READ, Permission.WRITE);

        System.out.println("editor permissions: " + editorPerms);
        System.out.println("can editor delete? " + editorPerms.contains(Permission.DELETE));
        System.out.println("can editor write? " + editorPerms.contains(Permission.WRITE));
    }
}
```

**How to run:** `java PermissionsBasic.java` (JDK 17+).

Expected output:
```
editor permissions: [READ, WRITE]
can editor delete? false
can editor write? true
```

`EnumSet.of(...)` builds the set directly from the listed constants, and `contains` is a fast bit check rather than a hash lookup — printing the set always shows constants in their declaration order, `READ` before `WRITE`, regardless of the order they were passed to `of(...)`.

### Level 2 — Intermediate

```java
import java.util.*;

public class PermissionsSetAlgebra {
    enum Permission { READ, WRITE, DELETE, ADMIN }

    public static void main(String[] args) {
        EnumSet<Permission> editorPerms = EnumSet.of(Permission.READ, Permission.WRITE);
        EnumSet<Permission> adminPerms = EnumSet.allOf(Permission.class);

        // Union: combine two roles' permissions.
        EnumSet<Permission> combined = EnumSet.copyOf(editorPerms);
        combined.addAll(adminPerms);
        System.out.println("editor + admin combined: " + combined);

        // Complement: everything the editor CANNOT do.
        EnumSet<Permission> editorCannot = EnumSet.complementOf(editorPerms);
        System.out.println("editor cannot: " + editorCannot);

        // Intersection: permissions common to two different roles.
        EnumSet<Permission> viewerPerms = EnumSet.of(Permission.READ);
        EnumSet<Permission> intersection = EnumSet.copyOf(editorPerms);
        intersection.retainAll(viewerPerms);
        System.out.println("editor ∩ viewer: " + intersection);
    }
}
```

**How to run:** `java PermissionsSetAlgebra.java`.

Expected output:
```
editor + admin combined: [READ, WRITE, DELETE, ADMIN]
editor cannot: [DELETE, ADMIN]
editor ∩ viewer: [READ]
```

The real-world concern added: full set algebra — union (`addAll`), complement (`EnumSet.complementOf`), and intersection (`retainAll`) — all reducing to simple bitwise OR, NOT, and AND operations under the hood, making them dramatically cheaper than the equivalent operations on a `HashSet<Permission>`. `EnumSet.copyOf(...)` is used before mutating operations to avoid accidentally modifying the original `editorPerms` set.

### Level 3 — Advanced

```java
import java.util.*;

public class AccessControlHotPath {
    enum Permission { READ, WRITE, DELETE, ADMIN }

    record User(String name, EnumSet<Permission> permissions) {}

    static boolean canPerform(User user, EnumSet<Permission> required) {
        // containsAll is a bitwise AND-and-compare -- extremely cheap, safe to call on every request.
        return user.permissions().containsAll(required);
    }

    public static void main(String[] args) {
        User viewer = new User("viewer", EnumSet.of(Permission.READ));
        User editor = new User("editor", EnumSet.of(Permission.READ, Permission.WRITE));
        User admin = new User("admin", EnumSet.allOf(Permission.class));

        EnumSet<Permission> requiredForDelete = EnumSet.of(Permission.READ, Permission.DELETE);

        for (User user : List.of(viewer, editor, admin)) {
            boolean allowed = canPerform(user, requiredForDelete);
            System.out.println(user.name() + " can perform delete-requiring action: " + allowed);
        }

        // Simulate a hot path: thousands of permission checks, cheap enough to not worry about.
        long start = System.nanoTime();
        int allowedCount = 0;
        for (int i = 0; i < 1_000_000; i++) {
            if (canPerform(editor, requiredForDelete)) allowedCount++;
        }
        long elapsedMillis = (System.nanoTime() - start) / 1_000_000;
        System.out.println("1,000,000 checks completed in " + elapsedMillis + " ms (allowed count: " + allowedCount + ")");
    }
}
```

**How to run:** `java AccessControlHotPath.java`.

Expected output shape (exact timing varies by machine, but stays extremely low):
```
viewer can perform delete-requiring action: false
editor can perform delete-requiring action: false
admin can perform delete-requiring action: true
1,000,000 checks completed in ~5 ms (allowed count: 0)
```

This adds the production-flavored hard case: `containsAll` used as a genuine access-control check — "does this user have every permission this action requires?" — run a million times to demonstrate that `EnumSet`'s bitwise implementation makes this cheap enough to call on every single request without a second thought, which would be a much riskier assumption with a `HashSet<Permission>`-based equivalent under heavy load.

## 6. Walkthrough

Tracing `AccessControlHotPath.main`:

1. Three `User` records are constructed, each holding an `EnumSet<Permission>` representing their role's permissions — `viewer` has just `READ`, `editor` has `READ` and `WRITE`, `admin` has all four constants via `EnumSet.allOf(Permission.class)`.
2. `requiredForDelete` is built as `EnumSet.of(READ, DELETE)` — the two permissions some delete-requiring action needs.
3. The `for` loop calls `canPerform(user, requiredForDelete)` for each user; internally, `user.permissions().containsAll(required)` computes (conceptually) `required`'s bit pattern AND'd against `user.permissions()`'s bit pattern, then checks whether the result equals `required`'s pattern exactly — i.e., every bit set in `required` is also set in the user's permissions. `viewer` (only `READ` set) fails, since `DELETE`'s bit isn't set; `editor` (`READ`, `WRITE`) also fails, missing `DELETE`; `admin` (all bits set) passes.
4. The final loop repeats the identical `canPerform(editor, requiredForDelete)` check one million times, timing the total. Because each check is just a bitmask AND-and-compare — no hashing, no bucket traversal, no object allocation — the whole million-iteration loop completes in a handful of milliseconds, confirming this is genuinely cheap enough for a hot request-handling path.
5. `allowedCount` stays `0` throughout, since `editor` never has `DELETE`, confirming the check's result is stable and consistent across every one of the million repeated calls.

## 7. Gotchas & takeaways

> **Gotcha:** `EnumSet` (like most `Set` implementations) is **not synchronized** — concurrent modification from multiple threads without external synchronization can corrupt it, just as with `HashSet`. If a mutable `EnumSet` is shared across threads, wrap it with `Collections.synchronizedSet(enumSet)` or otherwise guard concurrent access explicitly.

- `EnumSet` stores elements of a single enum type as a bit vector, making every operation a fast bitwise computation rather than a hash lookup.
- It's created via static factories (`of`, `allOf`, `noneOf`, `range`, `complementOf`, `copyOf`), not a public constructor.
- Iteration always follows the enum constants' declaration order, automatically — no comparator or ordering configuration needed.
- Set algebra (union via `addAll`, intersection via `retainAll`, complement via `EnumSet.complementOf`) is dramatically cheaper than the equivalent on a `HashSet<E>`.
- Reach for `EnumSet<E>` by default whenever `E` is an enum type and a `Set<E>` is needed — there's essentially no reason to prefer `HashSet<E>` for this specific case.
