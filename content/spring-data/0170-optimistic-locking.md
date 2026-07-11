---
card: spring-data
gi: 170
slug: optimistic-locking
title: "Optimistic locking"
---

## 1. What it is

Optimistic locking in Spring Data Neo4j uses a `@Version` field on a `@Node` entity to detect concurrent modifications — two saves racing against the same node — and rejects the second one with an exception instead of silently letting it overwrite the first. The same `@Version` mechanism from the JPA and MongoDB sections earlier applies here, unchanged in concept.

```java
@Node
class Customer {
    @Id String id;
    String name;

    @Version Long version;
}
```

## 2. Why & when

Without any locking, two concurrent updates to the same node — say, two requests both editing a customer's profile — can race: the second write silently overwrites the first's changes, and whoever saved last simply wins, with no error and no way to detect it happened. Optimistic locking catches that instead of hiding it.

Reach for optimistic locking when:

- Multiple request threads, services, or users can plausibly update the same node concurrently, and silent last-write-wins would cause a real data-loss bug.
- You want to detect the conflict cheaply — no locks held during the read, just a version check at write time — rather than pessimistically locking the node for the duration of an edit.
- The application can meaningfully respond to a conflict (retry, merge, tell the user "someone else changed this") rather than crash outright.

## 3. Core concept

```
 Thread A: read Customer{id=c1, version=3}
 Thread B: read Customer{id=c1, version=3}        -- both read the SAME version

 Thread A: save Customer{id=c1, version=3}    -- succeeds, version bumped to 4 in the graph
 Thread B: save Customer{id=c1, version=3}    -- version in graph is now 4, not 3
                                                  -> OptimisticLockingFailureException
```

The version check happens at write time, comparing the version the caller last read against the version currently stored — a mismatch means someone else wrote in between.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads read the same version, one save succeeds and bumps the version, the second save fails a version check">
  <rect x="20" y="20" width="270" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="155" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Thread A reads version=3</text>

  <rect x="350" y="20" width="270" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Thread B reads version=3</text>

  <rect x="20" y="90" width="270" height="35" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="112" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">A saves -&gt; version bumped to 4</text>

  <rect x="350" y="90" width="270" height="35" rx="6" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="485" y="112" fill="#e6edf3" font-size="8.2" text-anchor="middle" font-family="sans-serif">B saves version=3 -&gt; graph has 4</text>

  <rect x="350" y="150" width="270" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="485" y="170" fill="#79c0ff" font-size="8.2" text-anchor="middle" font-family="sans-serif">OptimisticLockingFailureException</text>
</svg>

Both threads read the same version; whichever saves second finds the stored version has already moved on and fails.

## 5. Runnable example

The scenario: two concurrent edits to the same customer profile, evolving from unprotected concurrent saves silently losing an update, to a `@Version`-checked save that rejects the stale write, to a retry loop that re-reads and re-applies the change after a conflict — the production-realistic response to a caught conflict.

### Level 1 — Basic

Show the unprotected baseline: two "concurrent" saves, the second silently overwriting the first with no error and no way to detect it happened.

```java
import java.util.*;

public class OptimisticLockingLevel1 {
    public static void main(String[] args) {
        GraphStore store = new GraphStore();
        store.save(new Customer("c1", "Amara", "amara@old.example"));

        // Two threads both read the same starting state.
        Customer readByThreadA = store.findById("c1");
        Customer readByThreadB = store.findById("c1");

        readByThreadA.email = "amara@work.example";
        store.save(readByThreadA); // wins

        readByThreadB.phone = "+234-000-0000"; // a DIFFERENT edit, made against the OLD state
        store.save(readByThreadB); // silently overwrites A's email change back to "amara@old.example"

        Customer found = store.findById("c1");
        System.out.println("email=" + found.email + " phone=" + found.phone); // A's email change is LOST
    }
}

class Customer {
    String id, name, email, phone;
    Customer(String id, String name, String email) { this.id = id; this.name = name; this.email = email; }
}

class GraphStore {
    private final Map<String, Customer> nodes = new HashMap<>();
    void save(Customer c) { nodes.put(c.id, c); } // last write wins, unconditionally
    Customer findById(String id) {
        Customer c = nodes.get(id);
        Customer copy = new Customer(c.id, c.name, c.email); copy.phone = c.phone;
        return copy;
    }
}
```

How to run: `java OptimisticLockingLevel1.java`

Thread B's save silently discards Thread A's email change, because B's in-memory copy was read *before* A's save happened, and nothing checks for that — this is exactly the class of bug optimistic locking exists to catch.

### Level 2 — Intermediate

Add a `@Version` field and a save that checks it, rejecting a save whose version doesn't match what's currently stored.

```java
import java.util.*;

public class OptimisticLockingLevel2 {
    public static void main(String[] args) {
        GraphStore store = new GraphStore();
        store.save(new Customer("c1", "Amara", "amara@old.example", 0L));

        Customer readByThreadA = store.findById("c1");
        Customer readByThreadB = store.findById("c1"); // both read version=1

        readByThreadA.email = "amara@work.example";
        store.save(readByThreadA); // succeeds: version 1 matches, bumped to 2

        readByThreadB.phone = "+234-000-0000";
        try {
            store.save(readByThreadB); // version 1 no longer matches stored version 2
        } catch (OptimisticLockingFailureException e) {
            System.out.println("Conflict detected: " + e.getMessage());
        }

        Customer found = store.findById("c1");
        System.out.println("email=" + found.email + " version=" + found.version); // A's change preserved
    }
}

class OptimisticLockingFailureException extends RuntimeException {
    OptimisticLockingFailureException(String message) { super(message); }
}

class Customer {
    String id, name, email, phone;
    Long version; // @Version
    Customer(String id, String name, String email, Long version) {
        this.id = id; this.name = name; this.email = email; this.version = version;
    }
}

class GraphStore {
    private final Map<String, Customer> nodes = new HashMap<>();
    void save(Customer c) {
        Customer stored = nodes.get(c.id);
        if (stored != null && !stored.version.equals(c.version)) {
            throw new OptimisticLockingFailureException(
                "Customer " + c.id + " was modified concurrently (expected version " + c.version + ", found " + stored.version + ")");
        }
        c.version = (stored == null ? 0L : stored.version) + 1;
        nodes.put(c.id, c);
    }
    Customer findById(String id) {
        Customer c = nodes.get(id);
        Customer copy = new Customer(c.id, c.name, c.email, c.version); copy.phone = c.phone;
        return copy;
    }
}
```

How to run: `java OptimisticLockingLevel2.java`

Thread A's save succeeds and bumps the version from 1 to 2. Thread B's save carries the stale `version=1` it read before A's save, the check in `save()` catches the mismatch against the now-stored `version=2`, and throws instead of silently overwriting — A's email change survives.

### Level 3 — Advanced

Add a retry loop around the conflicting save: on catching the exception, re-read the current state, re-apply the intended change on top of the fresh version, and try again — the realistic production response to a caught conflict, rather than just surfacing the error to the caller.

```java
import java.util.*;
import java.util.function.*;

public class OptimisticLockingLevel3 {
    public static void main(String[] args) {
        GraphStore store = new GraphStore();
        store.save(new Customer("c1", "Amara", "amara@old.example", 0L));

        Customer readByThreadA = store.findById("c1");
        readByThreadA.email = "amara@work.example";
        store.save(readByThreadA); // succeeds first, bumps version 1 -> 2

        // Thread B retries its phone-number update until it succeeds against the CURRENT version.
        saveWithRetry(store, "c1", customer -> customer.phone = "+234-000-0000", 3);

        Customer found = store.findById("c1");
        System.out.println("email=" + found.email + " phone=" + found.phone + " version=" + found.version);
    }

    static void saveWithRetry(GraphStore store, String id, Consumer<Customer> mutation, int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            Customer fresh = store.findById(id); // re-read the CURRENT version on every attempt
            mutation.accept(fresh);
            try {
                store.save(fresh);
                System.out.println("Saved on attempt " + attempt);
                return;
            } catch (OptimisticLockingFailureException e) {
                System.out.println("Attempt " + attempt + " conflicted, retrying: " + e.getMessage());
            }
        }
        throw new IllegalStateException("Gave up after " + maxAttempts + " attempts");
    }
}

class OptimisticLockingFailureException extends RuntimeException {
    OptimisticLockingFailureException(String message) { super(message); }
}

class Customer {
    String id, name, email, phone;
    Long version;
    Customer(String id, String name, String email, Long version) {
        this.id = id; this.name = name; this.email = email; this.version = version;
    }
}

class GraphStore {
    private final Map<String, Customer> nodes = new HashMap<>();
    void save(Customer c) {
        Customer stored = nodes.get(c.id);
        if (stored != null && !stored.version.equals(c.version)) {
            throw new OptimisticLockingFailureException(
                "expected version " + c.version + ", found " + stored.version);
        }
        c.version = (stored == null ? 0L : stored.version) + 1;
        nodes.put(c.id, c);
    }
    Customer findById(String id) {
        Customer c = nodes.get(id);
        Customer copy = new Customer(c.id, c.name, c.email, c.version); copy.phone = c.phone;
        return copy;
    }
}
```

How to run: `java OptimisticLockingLevel3.java`

`saveWithRetry` re-reads the customer fresh on every attempt — so its first attempt already picks up the post-Thread-A `version=2` and the phone-number edit is applied on top of the *current* state, succeeding on the very first try, with no conflict at all this time, because the retry loop always operates against fresh data rather than a stale in-memory copy.

## 6. Walkthrough

Execution starts in `main` for Level 3. Thread A's flow runs first and completes fully: it reads `version=1`, sets a new email, saves, and the store bumps the version to `2`. This finishes before Thread B's retry loop begins in this deliberately sequential demo.

`saveWithRetry` then runs: attempt 1 calls `store.findById("c1")`, which returns the *already-updated* state with `version=2` and Amara's new email intact — the mutation (setting `phone`) is applied to that fresh copy, and the save succeeds immediately, since its version matches what's currently stored:

```
Saved on attempt 1
email=amara@work.example phone=+234-000-0000 version=3
```

In a real concurrent system, Thread B's *first* attempt would likely conflict (if it read `version=1` before Thread A's save landed) — the retry loop's actual value shows up when it catches an `OptimisticLockingFailureException`, discards its stale copy, re-reads the current node, and reapplies just its own intended change (`phone`), rather than reapplying a whole stale object that would clobber Thread A's `email` change again.

## 7. Gotchas & takeaways

> Gotcha: a retry loop that re-saves the *entire* stale object (rather than re-reading fresh and reapplying only the intended field-level change) can still silently clobber a concurrent change — the safety optimistic locking provides depends on the retry logic re-reading current state, not just resubmitting the same stale object with a bumped version number.

> Gotcha: `@Version` fields must not be set manually by application code — Spring Data manages the value entirely; hand-setting or incrementing it defeats the conflict check and can cause legitimate saves to fail or conflicting saves to silently succeed.

- `@Version` detects concurrent modification at write time by comparing the version read against the version currently stored — no locks held during reads, unlike pessimistic locking.
- A version mismatch throws `OptimisticLockingFailureException` rather than silently allowing a last-write-wins overwrite.
- The realistic response to a caught conflict is a retry that re-reads fresh state and reapplies just the intended change — not blindly resubmitting the same stale object.
- The mechanism and annotation are identical to `@Version` in the JPA and MongoDB sections earlier in this course — Spring Data's optimistic locking support is shared across modules.
