---
card: spring-security
gi: 113
slug: embedded-ldap-server-for-testing
title: "Embedded LDAP server for testing"
---

## 1. What it is

Testing LDAP authentication (cards 0111–0112) against a real, external directory server is impractical for automated tests — it requires a running server, network access, and test data that's isolated from whatever else uses that directory. Spring Security's `spring-security-test` (backed by UnboundID's embedded LDAP server) solves this by starting a genuine, in-process, in-memory LDAP server at test startup, populated from an LDIF (LDAP Data Interchange Format) file, torn down automatically when the test context closes. Spring Boot's autoconfiguration makes this nearly invisible: with `spring-boot-starter-data-ldap` and an embedded server dependency on the classpath, declaring `spring.ldap.embedded.ldif=classpath:test-users.ldif` is often the entire setup required.

```yaml
spring:
  ldap:
    embedded:
      ldif: classpath:test-users.ldif
      base-dn: dc=example,dc=com
      port: 0   # 0 = pick a random free port, avoiding collisions between parallel test runs
```
```
# test-users.ldif
dn: ou=people,dc=example,dc=com
objectClass: organizationalUnit
ou: people

dn: uid=alice,ou=people,dc=example,dc=com
objectClass: inetOrgPerson
uid: alice
cn: Alice Example
sn: Example
userPassword: secret123
```

## 2. Why & when

Every prior card in this LDAP mini-series described behavior — bind authentication, group-based authority population — that can only actually be exercised against something that speaks the LDAP protocol; unit-testing it with mocked directory calls would leave the real LDAP query syntax (search filters, DN patterns) completely unverified, exactly the kind of gap where a subtly wrong filter passes every mocked test yet fails against a real directory. An embedded LDAP server closes that gap by giving tests a real, protocol-compliant server to authenticate and search against, without any of the operational burden of standing up (and tearing down, and network-isolating) an actual external directory for CI.

Reach for an embedded LDAP server when:

- Writing integration tests for `BindAuthenticator` or `LdapAuthoritiesPopulator` configuration — these components' correctness genuinely depends on LDAP search filters and DN patterns matching real server behavior, which no amount of mocking fully verifies.
- CI pipelines need LDAP-backed tests to run hermetically, without any dependency on a shared external directory server that other tests (or other teams) might also be modifying concurrently.
- Prototyping or demoing an LDAP integration locally without provisioning a real directory server — an embedded instance, seeded from a small LDIF file, is often faster to get running than any real OpenLDAP or Active Directory setup.
- Verifying LDIF test fixtures themselves are well-formed and produce the expected directory structure — a fixture with a typo in its DN hierarchy fails loudly against a real (even if embedded) LDAP server, rather than silently succeeding against an overly permissive mock.

## 3. Core concept

```
Test lifecycle with an embedded LDAP server:

  1. test context starts
  2. embedded server boots, in-process, on a random (or configured) port
  3. LDIF file is loaded -- every dn/objectClass/attribute entry it defines becomes a REAL directory entry
  4. test code runs against a REAL BaseLdapPathContextSource pointed at this embedded server
       -- BindAuthenticator, LdapAuthoritiesPopulator, etc. all behave EXACTLY as they would in production
  5. test context closes -> embedded server shuts down, all data discarded

KEY properties:
    genuinely speaks the LDAP protocol -- no mocking of search filters or bind semantics
    fully isolated -- no shared state between test runs, no external network dependency
    fast -- in-process, in-memory, no real network round trip
    disposable -- LDIF-defined state is rebuilt fresh (or per test class) every run
```

Because the embedded server is a real LDAP implementation, any test that passes against it gives meaningfully higher confidence than one that only exercises mocked directory calls.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing an ldif fixture file being loaded into an in process embedded ldap server at test startup real BindAuthenticator and LdapAuthoritiesPopulator code under test running actual LDAP operations against it and the server being torn down at test end">
  <rect x="20" y="30" width="160" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="100" y="50" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">test-users.ldif</text>
  <text x="100" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fixture, on classpath</text>

  <line x1="180" y1="55" x2="225" y2="55" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#el113)"/>
  <text x="200" y="45" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">load</text>

  <rect x="230" y="20" width="220" height="70" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="340" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">embedded LDAP server</text>
  <text x="340" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">in-process, random port</text>
  <text x="340" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">REAL LDAP protocol behavior</text>

  <line x1="340" y1="90" x2="340" y2="120" stroke="#6db33f" stroke-width="1.6" marker-end="url(#el113b)"/>

  <rect x="230" y="122" width="220" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="340" y="142" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif">BindAuthenticator / populator</text>
  <text x="340" y="158" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">under test -- unmodified production code</text>

  <line x1="450" y1="147" x2="500" y2="147" stroke="#f0883e" stroke-width="1.5" marker-end="url(#el113c)"/>

  <rect x="505" y="122" width="115" height="50" rx="7" fill="#1c2430" stroke="#f0883e" stroke-width="1.3"/>
  <text x="562" y="142" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">test assertions</text>
  <text x="562" y="158" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">real pass/fail signal</text>

  <defs>
    <marker id="el113" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="el113b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="el113c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

The exact same production `BindAuthenticator`/`LdapAuthoritiesPopulator` code runs unmodified against the embedded server — only the server underneath changes between test and production.

## 5. Runnable example

The scenario: simulate an embedded LDAP server's lifecycle — parsing a minimal LDIF-equivalent fixture into an in-memory directory, running real bind and group-search logic against it, and tearing it down — growing from a single test case into a suite exercising both success and failure paths, then into isolating fixture state per test so tests can't leak state into one another.

### Level 1 - Basic

Parse a tiny fixture into a directory and run a bind test against it.

```java
import java.util.*;

public class EmbeddedLdapLevel1 {
    record DirectoryEntry(String dn, Map<String, String> attributes) {}

    // stands in for the embedded LDAP server, seeded from an LDIF-equivalent fixture
    static class EmbeddedLdapServer {
        private final Map<String, DirectoryEntry> entries = new LinkedHashMap<>();

        void loadFixture(List<DirectoryEntry> fixtureEntries) {
            for (DirectoryEntry e : fixtureEntries) entries.put(e.dn(), e);
            System.out.println("embedded server started, loaded " + fixtureEntries.size() + " entries");
        }

        boolean bind(String dn, String password) {
            DirectoryEntry entry = entries.get(dn);
            return entry != null && password.equals(entry.attributes().get("userPassword"));
        }

        void shutdown() { entries.clear(); System.out.println("embedded server shut down, all data discarded"); }
    }

    public static void main(String[] args) {
        EmbeddedLdapServer server = new EmbeddedLdapServer();
        server.loadFixture(List.of(
                new DirectoryEntry("uid=alice,ou=people,dc=example,dc=com",
                        Map.of("cn", "Alice Example", "userPassword", "secret123"))));

        // test code -- runs against the REAL (embedded) server, not a mock
        boolean result = server.bind("uid=alice,ou=people,dc=example,dc=com", "secret123");
        System.out.println("bind test result: " + result);

        server.shutdown();
    }
}
```

**How to run:** save as `EmbeddedLdapLevel1.java`, run `java EmbeddedLdapLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
embedded server started, loaded 1 entries
bind test result: true
embedded server shut down, all data discarded
```

`EmbeddedLdapServer` mirrors the lifecycle Spring Boot's embedded LDAP autoconfiguration manages transparently: load fixture data at startup, serve real bind/search operations during the test, discard everything at shutdown — no test leaves behind state that could affect a subsequent run.

### Level 2 — Intermediate

A small test suite exercising both a successful and a failing bind, plus a group-membership search — mirroring a real `BindAuthenticator`/`LdapAuthoritiesPopulator` integration test.

```java
import java.util.*;

public class EmbeddedLdapLevel2 {
    record DirectoryEntry(String dn, Map<String, String> attributes, Set<String> memberOfGroups) {}

    static class EmbeddedLdapServer {
        private final Map<String, DirectoryEntry> entries = new LinkedHashMap<>();
        void loadFixture(List<DirectoryEntry> fixtureEntries) {
            for (DirectoryEntry e : fixtureEntries) entries.put(e.dn(), e);
        }
        boolean bind(String dn, String password) {
            DirectoryEntry entry = entries.get(dn);
            return entry != null && password.equals(entry.attributes().get("userPassword"));
        }
        Set<String> groupsFor(String dn) {
            DirectoryEntry entry = entries.get(dn);
            return entry != null ? entry.memberOfGroups() : Set.of();
        }
        void shutdown() { entries.clear(); }
    }

    static int passed = 0, failed = 0;

    static void assertTrue(String testName, boolean condition) {
        if (condition) { passed++; System.out.println("PASS: " + testName); }
        else { failed++; System.out.println("FAIL: " + testName); }
    }

    public static void main(String[] args) {
        EmbeddedLdapServer server = new EmbeddedLdapServer();
        server.loadFixture(List.of(
                new DirectoryEntry("uid=alice,ou=people,dc=example,dc=com",
                        Map.of("userPassword", "secret123"), Set.of("engineering", "admins")),
                new DirectoryEntry("uid=bob,ou=people,dc=example,dc=com",
                        Map.of("userPassword", "hunter2"), Set.of("engineering"))));

        assertTrue("alice binds with correct password", server.bind("uid=alice,ou=people,dc=example,dc=com", "secret123"));
        assertTrue("alice bind fails with wrong password", !server.bind("uid=alice,ou=people,dc=example,dc=com", "WRONG"));
        assertTrue("bob binds with his own correct password", server.bind("uid=bob,ou=people,dc=example,dc=com", "hunter2"));
        assertTrue("alice is in the admins group", server.groupsFor("uid=alice,ou=people,dc=example,dc=com").contains("admins"));
        assertTrue("bob is NOT in the admins group", !server.groupsFor("uid=bob,ou=people,dc=example,dc=com").contains("admins"));

        server.shutdown();
        System.out.println(passed + " passed, " + failed + " failed");
    }
}
```

**How to run:** save as `EmbeddedLdapLevel2.java`, run `java EmbeddedLdapLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
PASS: alice binds with correct password
PASS: alice bind fails with wrong password
PASS: bob binds with his own correct password
PASS: alice is in the admins group
PASS: bob is NOT in the admins group
5 passed, 0 failed
```

What changed: the fixture now includes multiple users with different group memberships, and the test suite exercises both authentication (Level 1's concern) and authorization (card 0112's group search) against the same embedded server instance — exactly the shape of a real Spring Security LDAP integration test verifying both `BindAuthenticator` and `LdapAuthoritiesPopulator` configuration together.

### Level 3 — Advanced

Isolate fixture state per test method — a fresh embedded server (or freshly-reloaded fixture) for each test, so one test's data mutations can never leak into another's, mirroring how a real embedded LDAP server is typically restarted (or its data reset) between test classes.

```java
import java.util.*;
import java.util.function.*;

public class EmbeddedLdapLevel3 {
    record DirectoryEntry(String dn, Map<String, String> attributes, Set<String> memberOfGroups) {}

    static class EmbeddedLdapServer {
        private final Map<String, DirectoryEntry> entries = new LinkedHashMap<>();
        void loadFixture(List<DirectoryEntry> fixtureEntries) {
            entries.clear(); // RESET before loading -- guarantees no leftover state from a previous test
            for (DirectoryEntry e : fixtureEntries) entries.put(e.dn(), e);
        }
        boolean bind(String dn, String password) {
            DirectoryEntry entry = entries.get(dn);
            return entry != null && password.equals(entry.attributes().get("userPassword"));
        }
        // a MUTATING operation a test might perform -- e.g. simulating a password change
        void updatePassword(String dn, String newPassword) {
            DirectoryEntry existing = entries.get(dn);
            entries.put(dn, new DirectoryEntry(dn, Map.of("userPassword", newPassword), existing.memberOfGroups()));
        }
        int entryCount() { return entries.size(); }
    }

    static List<DirectoryEntry> standardFixture() {
        return List.of(new DirectoryEntry("uid=alice,ou=people,dc=example,dc=com",
                Map.of("userPassword", "secret123"), Set.of("engineering")));
    }

    static void runTest(String testName, Consumer<EmbeddedLdapServer> testBody) {
        EmbeddedLdapServer server = new EmbeddedLdapServer();
        server.loadFixture(standardFixture()); // FRESH fixture, every single test
        testBody.accept(server);
        System.out.println("completed: " + testName + " (final entry count: " + server.entryCount() + ")");
    }

    public static void main(String[] args) {
        // test 1: mutates alice's password mid-test
        runTest("password change test", server -> {
            boolean beforeChange = server.bind("uid=alice,ou=people,dc=example,dc=com", "secret123");
            server.updatePassword("uid=alice,ou=people,dc=example,dc=com", "new-password-456");
            boolean oldPasswordAfterChange = server.bind("uid=alice,ou=people,dc=example,dc=com", "secret123");
            boolean newPasswordWorks = server.bind("uid=alice,ou=people,dc=example,dc=com", "new-password-456");
            System.out.println("  before change (old pw): " + beforeChange
                    + ", after change (old pw): " + oldPasswordAfterChange
                    + ", after change (new pw): " + newPasswordWorks);
        });

        // test 2: runs AFTER test 1 -- must see alice's ORIGINAL password, unaffected by test 1's mutation
        runTest("independent second test", server -> {
            boolean originalPasswordStillWorks = server.bind("uid=alice,ou=people,dc=example,dc=com", "secret123");
            System.out.println("  original password still works (test 1's mutation did NOT leak in): " + originalPasswordStillWorks);
        });
    }
}
```

**How to run:** save as `EmbeddedLdapLevel3.java`, run `java EmbeddedLdapLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
completed: password change test (final entry count: 1)
  before change (old pw): true, after change (old pw): false, after change (new pw): true
completed: independent second test (final entry count: 1)
  original password still works (test 1's mutation did NOT leak in): true
```

What changed: `runTest` reloads the fixture fresh for every single test via `loadFixture`'s `entries.clear()` — test 1 mutates alice's password mid-test, but test 2, running afterward, sees the original, unmutated fixture data, exactly as if it were running against a brand-new embedded server. This is precisely the isolation guarantee that makes embedded LDAP servers safe to use across a large test suite without tests interfering with one another.

## 6. Walkthrough

Trace test 1's password-change scenario from Level 3, step by step.

**Step 1 — test setup.** `runTest("password change test", ...)` constructs a fresh `EmbeddedLdapServer` and calls `loadFixture(standardFixture())` — this corresponds to Spring Boot's embedded LDAP autoconfiguration starting a brand-new in-process server and loading `test-users.ldif` at the start of a test method (or test class, depending on configuration).

**Step 2 — the first bind, before any mutation:**
```
LDAP Bind Request
  DN: uid=alice,ou=people,dc=example,dc=com
  Password: secret123
```
`server.bind(..., "secret123")` finds alice's entry (freshly loaded from the fixture) and confirms the password matches — `beforeChange` is `true`.

**Step 3 — a mutation, simulating something changing at the directory level mid-test.** `server.updatePassword(..., "new-password-456")` replaces alice's stored entry with one carrying the new password — this models, for instance, a test verifying that a password-change feature actually takes effect against the directory.

**Step 4 — binding with the old password now fails.** `server.bind(..., "secret123")` — the *same* password that worked in step 2 — now finds alice's entry has a different `userPassword` value, so the bind fails; `oldPasswordAfterChange` is `false`.

**Step 5 — binding with the new password succeeds.** `server.bind(..., "new-password-456")` matches the just-updated entry; `newPasswordWorks` is `true`.

**Step 6 — the critical isolation check, in the second, independent test.** `runTest("independent second test", ...)` constructs an *entirely new* `EmbeddedLdapServer` and reloads `standardFixture()` fresh — `entries.clear()` inside `loadFixture` guarantees this new instance starts with zero carried-over state from test 1, regardless of what test 1 did to its own server instance. `server.bind(..., "secret123")` — alice's *original* password — succeeds, proving test 1's mutation had no way to leak into test 2.

```
test 1: fresh server -> bind(old pw)=true -> mutate password -> bind(old pw)=false, bind(new pw)=true
                                                                        |
                                                          (server instance discarded)
                                                                        v
test 2: FRESH server, FRESH fixture -> bind(old pw)=true   <-- unaffected by test 1's mutation
```

## 7. Gotchas & takeaways

> **Gotcha:** if fixture reloading (or server restart) between tests is skipped for the sake of speed — reusing one embedded server instance across an entire test suite without resetting its state — tests that mutate directory data (password changes, group membership updates) can silently leak state into later tests, producing order-dependent test failures that are notoriously hard to diagnose. Always reset or reload fixture state between tests unless you have a specific, deliberate reason not to.

- An embedded LDAP server gives tests real LDAP protocol behavior — genuine bind semantics, genuine search filter evaluation — without any external server dependency, closing a real gap that mocked directory calls can't cover.
- LDIF fixture files define the directory's initial state declaratively; Spring Boot's embedded LDAP autoconfiguration loads them automatically when `spring.ldap.embedded.ldif` is configured.
- The exact same production `BindAuthenticator`/`LdapAuthoritiesPopulator` configuration under test runs unmodified against the embedded server — only the server implementation underneath differs from a production deployment.
- Test isolation depends on resetting or reloading directory state between tests — a shared, un-reset embedded server instance across many tests reintroduces the same cross-test state leakage that in-memory databases and other shared test fixtures are equally vulnerable to.
- Using a random port (`port: 0`) for the embedded server avoids port collisions when tests run in parallel, which is otherwise a common and confusing source of intermittent CI failures.
