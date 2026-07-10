---
card: java
gi: 819
slug: treeset
title: TreeSet
---

## 1. What it is

`TreeSet` is the standard implementation of [`NavigableSet`](0804-sortedset-navigableset.md), backed by a red-black tree (a self-balancing binary search tree) that keeps every element in continuous sorted order. Every `add`, `remove`, and `contains` call is O(log n), navigating down the tree by comparison rather than by hash code. Crucially, `TreeSet` determines both **ordering** and **uniqueness** using the same mechanism — either the elements' natural ordering (`Comparable.compareTo`) or an explicit `Comparator` supplied at construction — and *not* `equals()`/`hashCode()` at all. Two elements that a `Comparator` (or `compareTo`) judges "equal" (comparison result of `0`) are treated as duplicates by `TreeSet`, even if `equals()` would say they're different.

## 2. Why & when

Anything that needs to stay continuously sorted while being actively modified — a leaderboard, a priority-ordered task list, a schedule — benefits from `TreeSet`'s O(log n) insert-while-sorted behavior, which beats sorting a `List` from scratch (O(n log n)) every time a single element changes. The critical design decision when using `TreeSet` is choosing (or writing) a comparator that captures the **actual** notion of uniqueness intended — because `TreeSet`, unlike `HashSet`, never consults `equals()` to decide whether two elements are "the same." This is a common trap: a `Comparator` written to compare by just one field (say, a person's last name, for sorting a directory) will silently treat two different people who happen to share a last name as duplicates, if that comparator is also used to determine set membership.

## 3. Core concept

```java
TreeSet<String> caseInsensitive = new TreeSet<>(String.CASE_INSENSITIVE_ORDER);
caseInsensitive.add("Alice");
boolean addedAgain = caseInsensitive.add("ALICE"); // different by equals(), but compareTo (via this comparator) treats them as the same

System.out.println(addedAgain);          // false -- rejected as a duplicate
System.out.println(caseInsensitive.size()); // 1

// Yet plain String.equals() disagrees:
System.out.println("Alice".equals("ALICE")); // false
```

`TreeSet`'s uniqueness rule is entirely delegated to whatever comparator (or natural ordering) it was constructed with — `equals()` never enters the picture, which is precisely why this pair, unequal by `equals()`, still collapses into one element inside the set.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="TreeSet determines both order and uniqueness purely through compareTo or a supplied Comparator, never through equals or hashCode">
  <rect x="40" y="30" width="250" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="165" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">HashSet: hashCode() + equals()</text>
  <text x="165" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">determine uniqueness</text>

  <rect x="350" y="30" width="250" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="475" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">TreeSet: compareTo()/Comparator</text>
  <text x="475" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">determines BOTH order AND uniqueness</text>

  <text x="320" y="130" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">If compareTo/Comparator returns 0 for two "unequal" objects,</text>
  <text x="320" y="150" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">TreeSet treats them as duplicates — equals() is never consulted.</text>
</svg>

*Unlike `HashSet`, `TreeSet` never consults `equals()`/`hashCode()` — its comparator alone decides both order and duplicate-detection.*

## 5. Runnable example

Scenario: a directory of unique registered users, growing from basic sorted storage to the case-insensitive-username trap, to a correctly-designed comparator for a custom `User` type that avoids the field-comparison duplicate pitfall entirely.

### Level 1 — Basic

```java
import java.util.*;

public class UsernamesBasic {
    public static void main(String[] args) {
        TreeSet<String> usernames = new TreeSet<>();
        usernames.add("charlie");
        usernames.add("alice");
        usernames.add("bob");

        System.out.println("usernames, sorted: " + usernames);
        System.out.println("first: " + usernames.first() + ", last: " + usernames.last());
    }
}
```

**How to run:** `java UsernamesBasic.java` (JDK 17+).

Expected output:
```
usernames, sorted: [alice, bob, charlie]
first: alice, last: charlie
```

Elements are inserted out of alphabetical order but always iterate sorted — `TreeSet`'s tree structure maintains this continuously, without a separate sort step.

### Level 2 — Intermediate

```java
import java.util.*;

public class UsernamesCaseInsensitiveTrap {
    public static void main(String[] args) {
        TreeSet<String> usernames = new TreeSet<>(String.CASE_INSENSITIVE_ORDER);
        usernames.add("alice");
        boolean addedAgain = usernames.add("Alice"); // same person re-registering with different casing, INTENTIONALLY rejected

        System.out.println("adding 'Alice' after 'alice' reported new: " + addedAgain);
        System.out.println("usernames: " + usernames);

        // But this comparator ALSO silently merges genuinely different usernames that only DIFFER in case:
        boolean bobAdded = usernames.add("BOB");
        boolean bobLowerAdded = usernames.add("bob"); // if these were meant to be different accounts, this is a bug
        System.out.println("'BOB' added: " + bobAdded + ", 'bob' added afterward: " + bobLowerAdded);
    }
}
```

**How to run:** `java UsernamesCaseInsensitiveTrap.java`.

Expected output:
```
adding 'Alice' after 'alice' reported new: false
usernames: [alice]
'BOB' added: true, 'bob' added afterward: false
```

The real-world concern added: `String.CASE_INSENSITIVE_ORDER` is genuinely useful *when case-insensitive uniqueness is the actual intent* (which it is here, for usernames) — but it's worth being deliberate about that choice, since it means `"BOB"` and `"bob"` can never both exist in this set, by design. If two genuinely distinct usernames only differing by case were a legitimate business requirement, this comparator would be the wrong tool entirely.

### Level 3 — Advanced

```java
import java.util.*;

public class UserDirectoryCorrectComparator {
    record User(String id, String lastName) {}

    public static void main(String[] args) {
        // BUGGY comparator: compares only by lastName -- two DIFFERENT users sharing a last name
        // would collapse into one entry, since compareTo returning 0 means "duplicate" to a TreeSet.
        TreeSet<User> buggyDirectory = new TreeSet<>(Comparator.comparing(User::lastName));
        buggyDirectory.add(new User("u1", "Smith"));
        boolean secondSmithAdded = buggyDirectory.add(new User("u2", "Smith")); // different person, same last name!
        System.out.println("buggy directory: second 'Smith' (different user!) added: " + secondSmithAdded);
        System.out.println("buggy directory size: " + buggyDirectory.size() + " (should be 2, lost a real user)");

        // FIXED comparator: break ties on a field that's actually guaranteed unique, like id.
        TreeSet<User> correctDirectory = new TreeSet<>(
            Comparator.comparing(User::lastName).thenComparing(User::id)
        );
        correctDirectory.add(new User("u1", "Smith"));
        boolean secondSmithAddedFixed = correctDirectory.add(new User("u2", "Smith"));
        System.out.println("fixed directory: second 'Smith' added: " + secondSmithAddedFixed);
        System.out.println("fixed directory size: " + correctDirectory.size() + " (correctly keeps both users)");
    }
}
```

**How to run:** `java UserDirectoryCorrectComparator.java`.

Expected output:
```
buggy directory: second 'Smith' (different user!) added: false
buggy directory size: 1 (should be 2, lost a real user)
fixed directory: second 'Smith' added: true
fixed directory size: 2 (correctly keeps both users)
```

This adds the production-flavored hard case: the classic `TreeSet` bug, made concrete with a real domain object. Sorting a user directory by `lastName` alone seems reasonable for *display* purposes, but using that exact comparator to construct the `TreeSet` also makes `lastName` the sole determinant of uniqueness — silently dropping a second, genuinely distinct user who happens to share a last name with an existing one. `thenComparing(User::id)` fixes this by breaking ties on a field guaranteed to be unique, ensuring `compareTo` only returns `0` for objects that are truly the same user.

## 6. Walkthrough

Tracing `UserDirectoryCorrectComparator.main`:

1. `buggyDirectory` is constructed with `Comparator.comparing(User::lastName)` — a comparator that compares two `User` objects purely by their `lastName` field.
2. `buggyDirectory.add(new User("u1", "Smith"))` inserts the first user; the tree now has one node.
3. `buggyDirectory.add(new User("u2", "Smith"))` computes `comparator.compare(existingSmith, newSmith)`, which compares `"Smith".compareTo("Smith")` — returning `0`. A `TreeSet` interprets a `0` comparison result as "this element already exists," so the insertion is silently rejected: `secondSmithAdded` is `false`, and the genuinely distinct second user (`u2`) is lost entirely — never stored, never signaled as an error.
4. `correctDirectory` is constructed with a two-level comparator: `Comparator.comparing(User::lastName).thenComparing(User::id)` — compare by last name first, and only if that comparison is a tie (`0`), fall back to comparing by `id`.
5. `correctDirectory.add(new User("u1", "Smith"))` inserts the first user as before.
6. `correctDirectory.add(new User("u2", "Smith"))` now compares last names first (`"Smith".compareTo("Smith")` = `0`, a tie), so the comparator proceeds to the `thenComparing` clause and compares `"u1".compareTo("u2")`, which is nonzero — the two users are correctly judged distinct, `secondSmithAddedFixed` is `true`, and both are retained in the set.

## 7. Gotchas & takeaways

> **Gotcha:** a `TreeSet` constructed with a comparator that returns `0` for objects meant to be distinct will silently **drop** later insertions — no exception, no warning, just a smaller-than-expected set. This is especially dangerous because it's easy to write a comparator that's perfectly correct for *sorting/display* purposes while being wrong for *uniqueness* purposes, since `TreeSet` conflates the two.

- `TreeSet` maintains sorted order via a red-black tree, with O(log n) `add`/`remove`/`contains`.
- Uniqueness in a `TreeSet` is determined **entirely** by `compareTo`/`Comparator` returning `0`, not by `equals()`/`hashCode()` — the two mechanisms can disagree, and `TreeSet` only ever consults the former.
- A comparator designed purely for sorting/display (e.g., by one field) can silently merge genuinely distinct elements if it's also used to construct the set — break ties with a guaranteed-unique field (like an ID) whenever a comparator's tie-breaking behavior matters for uniqueness.
- `String.CASE_INSENSITIVE_ORDER` and similar comparators are legitimate when the *intent* really is coarser-grained uniqueness — just be deliberate about that choice.
- When uniqueness should track `equals()`/`hashCode()` exactly, and only sorted iteration order is the actual need, consider building the ordering on top of a [`LinkedHashSet`](0818-linkedhashset.md) or sorting a copy instead of relying on `TreeSet`'s comparator-driven identity.
