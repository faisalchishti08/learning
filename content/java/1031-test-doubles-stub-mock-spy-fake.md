---
card: java
gi: 1031
slug: test-doubles-stub-mock-spy-fake
title: "Test doubles (stub/mock/spy/fake)"
---

## 1. What it is

**Test double** is the umbrella term for any object substituted for a real dependency during testing (as a stand-in, the way a stunt double stands in for an actor). The four most common kinds, distinguished by *what they're for*, not just how they're built: a **stub** returns canned answers to calls, with no behavior beyond that. A **mock** additionally records how it was called, so the test can `verify` those interactions afterward. A **spy** wraps a *real* object, letting most calls pass through to the genuine implementation while selectively watching or overriding specific ones. A **fake** is a lightweight, but genuinely working, alternative implementation — an in-memory database standing in for a real one, functionally real but not production-grade.

## 2. Why & when

These four aren't interchangeable synonyms — using the wrong kind for a given test either under-specifies what's actually being checked or adds unnecessary coupling to internal call patterns. A **stub** is the right choice when a test only cares about the *result* your code under test produces given a certain input from its dependency — it doesn't care whether or how many times the dependency was called. A **mock** is the right choice when the *fact that a specific interaction happened* is itself part of what's being tested (verifying an email was sent, a log entry was written). A **spy** is useful when you want mostly-real behavior but need to override or observe just one specific method — testing a class against a real collaborator's real logic, while still being able to simulate one specific failure path. A **fake** is worth building when a proper in-memory alternative (a `HashMap`-backed repository standing in for a database) is reusable across many tests and behaves close enough to the real thing to give genuine confidence, not just canned answers.

Reach for a stub for read-only "given this input, return this" scenarios. Reach for a mock (with `verify`) when testing that your code correctly triggers a side effect on a collaborator. Reach for a spy when testing code that depends heavily on a real object's real behavior, needing to override or watch just a narrow slice of it. Reach for a fake when you're testing extensively against the same kind of dependency across many tests, and a shared, reusable, working substitute pays for itself.

## 3. Core concept

```java
interface UserRepository {
    User findById(String id);
    void save(User user);
}
record User(String id, String name) {}

// STUB: canned answers, no interaction tracking, no real logic
class StubUserRepository implements UserRepository {
    public User findById(String id) { return new User(id, "Canned Name"); }
    public void save(User user) { /* does nothing -- not checked */ }
}

// FAKE: a genuinely working, lightweight alternative implementation
class FakeUserRepository implements UserRepository {
    private final java.util.Map<String, User> storage = new java.util.HashMap<>();
    public User findById(String id) { return storage.get(id); }
    public void save(User user) { storage.put(user.id(), user); } // ACTUALLY stores and retrieves
}

// MOCK and SPY are usually created via a framework (see Mockito), not hand-written:
// mock(UserRepository.class)       -- fully fake, behavior fully scripted
// spy(new RealUserRepository())    -- wraps a REAL implementation, mostly delegates to it
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four test doubles arranged by how much real behavior they contain: stub with canned answers, mock adding interaction tracking, spy wrapping a real object, and fake being a genuinely working lightweight implementation">
  <rect x="20" y="70" width="140" height="60" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="90" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Stub</text>
  <text x="90" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">canned answers only</text>

  <rect x="180" y="70" width="140" height="60" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="250" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Mock</text>
  <text x="250" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">+ records interactions</text>

  <rect x="340" y="70" width="140" height="60" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="410" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spy</text>
  <text x="410" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">wraps a REAL object</text>

  <rect x="500" y="70" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="570" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Fake</text>
  <text x="570" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">genuinely working, lightweight</text>

  <text x="330" y="30" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">increasing "real" behavior -&gt;</text>
</svg>

Each test double serves a different testing need — from a stub's minimal canned answers to a fake's genuinely working (but lightweight) implementation.

## 5. Runnable example

Scenario: testing a `UserService` against a `UserRepository` dependency, evolving through a stub, then a mock verifying an interaction, and finally a hand-built fake used across multiple test scenarios.

### Level 1 — Basic

```java
// File: src/test/java/UserServiceStubTest.java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

record User(String id, String name) {}
interface UserRepository {
    User findById(String id);
    void save(User user);
}

class UserService {
    private final UserRepository repository;
    UserService(UserRepository repository) { this.repository = repository; }
    String greet(String id) {
        User user = repository.findById(id);
        return "Hello, " + user.name() + "!";
    }
}

// STUB: only cares about the RETURN VALUE for a given input; no interaction tracking at all.
class StubUserRepository implements UserRepository {
    public User findById(String id) { return new User(id, "Ana"); }
    public void save(User user) { /* not used by this test, left empty */ }
}

class UserServiceStubTest {
    @Test
    void greetsUserByName() {
        UserService service = new UserService(new StubUserRepository());
        assertEquals("Hello, Ana!", service.greet("u1"));
    }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test`.

Expected output:
```
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
```

`StubUserRepository` gives a fixed, canned answer regardless of the `id` passed in — perfectly adequate here, since this test only cares about the greeting message `greet` produces, not about which `id` was actually looked up.

### Level 2 — Intermediate

```java
// File: src/test/java/UserServiceMockTest.java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.*;

record User(String id, String name) {}
interface UserRepository {
    User findById(String id);
    void save(User user);
}

class UserService {
    private final UserRepository repository;
    UserService(UserRepository repository) { this.repository = repository; }

    void registerUser(String id, String name) {
        repository.save(new User(id, name)); // a side effect with no return value to check
    }
}

class UserServiceMockTest {
    @Test
    void registeringUserSavesToRepository() {
        UserRepository mockRepository = mock(UserRepository.class);
        UserService service = new UserService(mockRepository);

        service.registerUser("u1", "Ana");

        // MOCK: what's being tested here is the INTERACTION itself -- that save()
        // was called with the exact expected User -- not any return value.
        verify(mockRepository).save(new User("u1", "Ana"));
    }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test`.

Expected output:
```
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
```

The real-world concern added: `registerUser` calls a `void` method with a side effect — there's no return value to assert on at all — so a mock's `verify` is the *only* way to confirm `repository.save(...)` was actually called with the right argument. Note: this test relies on `User` being a `record` (records generate `equals()` automatically), which is what lets `verify(...).save(new User("u1", "Ana"))` match by value.

### Level 3 — Advanced

```java
// File: src/test/java/UserServiceFakeTest.java
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import java.util.HashMap;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

record User(String id, String name) {}
interface UserRepository {
    User findById(String id);
    void save(User user);
}

class UserService {
    private final UserRepository repository;
    UserService(UserRepository repository) { this.repository = repository; }

    void registerUser(String id, String name) { repository.save(new User(id, name)); }
    String greet(String id) {
        User user = repository.findById(id);
        return user == null ? "Hello, stranger!" : "Hello, " + user.name() + "!";
    }
}

// FAKE: a genuinely working, in-memory implementation -- reusable across MANY
// tests, behaving close enough to a real database-backed repository to give
// real confidence, not just scripted canned answers.
class FakeUserRepository implements UserRepository {
    private final Map<String, User> storage = new HashMap<>();
    public User findById(String id) { return storage.get(id); }
    public void save(User user) { storage.put(user.id(), user); }
}

class UserServiceFakeTest {
    private FakeUserRepository repository;
    private UserService service;

    @BeforeEach
    void setUp() {
        repository = new FakeUserRepository();
        service = new UserService(repository);
    }

    @Test
    void greetsRegisteredUserByName() {
        service.registerUser("u1", "Ana");
        assertEquals("Hello, Ana!", service.greet("u1")); // uses the SAME fake for both write and read
    }

    @Test
    void greetsUnknownUserAsStranger() {
        assertEquals("Hello, stranger!", service.greet("unknown-id"));
    }

    @Test
    void registeringMultipleUsersKeepsThemSeparate() {
        service.registerUser("u1", "Ana");
        service.registerUser("u2", "Ben");
        assertEquals("Hello, Ana!", service.greet("u1"));
        assertEquals("Hello, Ben!", service.greet("u2"));
    }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test -Dtest=UserServiceFakeTest`.

Expected output:
```
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0
```

The production-flavored hard case: `FakeUserRepository` genuinely stores and retrieves data (unlike a stub's fixed canned answers), letting `registerUser` followed by `greet` in the *same test* exercise a real write-then-read round trip — something a simple stub, which would just always return the same canned `User` regardless of what was "saved," couldn't verify at all.

## 6. Walkthrough

Tracing `registeringMultipleUsersKeepsThemSeparate` in `UserServiceFakeTest`:

1. `@BeforeEach setUp()` runs first (per JUnit's lifecycle), constructing a fresh `FakeUserRepository` (with an empty internal `HashMap`) and a fresh `UserService` wrapping it.
2. `service.registerUser("u1", "Ana")` calls `UserService.registerUser`, which calls `repository.save(new User("u1", "Ana"))` — dispatching to `FakeUserRepository.save`, which runs `storage.put("u1", new User("u1", "Ana"))`, genuinely storing this entry in the map.
3. `service.registerUser("u2", "Ben")` repeats the process, storing a second, separate entry: `storage.put("u2", new User("u2", "Ben"))`. The map now holds two distinct entries.
4. `service.greet("u1")` calls `UserService.greet`, which calls `repository.findById("u1")` — dispatching to `FakeUserRepository.findById`, which runs `storage.get("u1")`, genuinely retrieving the previously-stored `User("u1", "Ana")` from the map (not a canned, fixed value).
5. Since the retrieved `user` is non-null, `greet` returns `"Hello, " + "Ana" + "!"` = `"Hello, Ana!"`, matching the assertion.
6. `service.greet("u2")` repeats the same real lookup process for `"u2"`, retrieving `User("u2", "Ben")` and returning `"Hello, Ben!"` — confirming the fake genuinely distinguishes between the two separately-registered users, a level of realistic behavior a stub (which would just return one fixed canned `User` regardless of the `id` passed in) fundamentally cannot provide.

## 7. Gotchas & takeaways

> **Gotcha:** "mock" is often used loosely to mean "any fake test object," but the four terms describe genuinely different tools — using Mockito's `mock()` where a simple stub (or, better, a shared fake) would serve just as well adds unnecessary interaction-tracking machinery and `verify` calls that don't actually correspond to anything meaningful being tested.

- A **stub** returns canned answers with no interaction tracking — right when only the *result* matters.
- A **mock** additionally records interactions for later `verify` — right when a specific *call happening* is itself the behavior under test, especially for `void` side-effecting methods.
- A **spy** wraps a real object, letting most calls pass through genuinely while selectively overriding or watching specific ones — right when you need mostly-real behavior with a narrow, deliberate exception.
- A **fake** is a lightweight but genuinely working alternative implementation — right when reused across many tests, giving real confidence through actual (if simplified) behavior rather than scripted responses.
- See [Mockito (mock/when/verify)](1030-mockito-mock-when-verify.md) for the concrete framework mechanics behind creating mocks and spies without hand-writing them.
- Choosing the right test double for a given test isn't just a style preference — a mock's `verify` calls couple a test to *how* your code calls its dependency, while a stub or fake only cares about *what* your code produces; picking the wrong one can make tests brittle (breaking on refactors that don't change behavior) or under-specified (missing bugs in how a dependency is actually used).
