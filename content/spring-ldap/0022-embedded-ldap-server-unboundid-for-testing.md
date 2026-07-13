---
card: spring-ldap
gi: 22
slug: embedded-ldap-server-unboundid-for-testing
title: "Embedded LDAP server (UnboundID) for testing"
---

## 1. What it is

UnboundID's `LDAPListener`/in-memory directory server (packaged for Spring as `spring-boot-starter-data-ldap`'s test support, or used directly via the `com.unboundid:unboundid-ldapsdk` library) is a real, fully-functional LDAP server that runs entirely in-process, in memory, with no external process, network dependency, or installed directory software required. It's the standard way to test Spring LDAP code — including everything covered in cards 0001 through 0021 — against a genuine LDAP protocol implementation, rather than mocking `LdapTemplate` or `DirContext` directly.

## 2. Why & when

Testing LDAP-facing code by mocking `LdapTemplate` or `DirContext` risks the classic mocking trap: tests pass against an idealized mock that doesn't actually enforce LDAP's real behaviors (schema validation, filter evaluation, DN structure rules), so a bug that would be caught by a real directory server slips through untested. Standing up a real external LDAP server for every test run, meanwhile, is slow, environment-dependent, and awkward in CI. The embedded UnboundID server exists to close that gap: it's a genuine LDAP server, so schema violations, filter matching, and DN handling all behave as they would in production, but it starts in milliseconds as part of the test process itself, with no external infrastructure needed.

Use the embedded UnboundID server when:

- Writing integration tests for any `LdapTemplate`-based code (searches, binds, modifications, ODM mappings) that should exercise real LDAP protocol behavior, not a mock's idealized approximation.
- Running LDAP-dependent tests in CI, where standing up and tearing down an external directory server per run would be slow or impractical.
- Local development, where a quick, disposable, pre-seeded directory is more convenient than pointing at a shared test environment.

## 3. Core concept

Think of the embedded UnboundID server as a fully-functional model train set — small enough to set up on a desk and pack away afterward, but running on real train mechanics, not a toy simulation. Tests that run against it are getting genuine signal about how a train (the application's LDAP code) actually behaves on real track (real LDAP protocol semantics), not just a diagram of how tracks are supposed to connect. Spring Boot's testing support wires this up almost invisibly — often just a test-scope dependency and an `application-test.properties` pointing at the embedded server's dynamically-assigned port — so most test code doesn't even need to know it isn't talking to a "real," separately-deployed directory.

```xml
<!-- pom.xml, test scope -->
<dependency>
    <groupId>com.unboundid</groupId>
    <artifactId>unboundid-ldapsdk</artifactId>
    <scope>test</scope>
</dependency>
```

```properties
# application-test.properties
spring.ldap.embedded.base-dn=dc=example,dc=com
spring.ldap.embedded.port=0            # 0 = pick a random free port automatically
spring.ldap.embedded.ldif=classpath:test-data.ldif   # pre-seed with an LDIF file, card 0021
```

With Spring Boot's LDAP auto-configuration (card 0023) active in the test context, an embedded server matching this configuration starts automatically alongside the test's Spring context — no manual server lifecycle code required in most cases.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A test process starts an embedded in-memory LDAP server, seeded from an LDIF file, and the application code under test connects to it via a normal ContextSource">
  <rect x="20" y="30" width="600" height="140" rx="8" fill="none" stroke="#8b949e" stroke-dasharray="4,4"/>
  <text x="320" y="20" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">single test JVM process</text>

  <rect x="50" y="60" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Embedded UnboundID</text>
  <text x="140" y="102" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">in-memory, real LDAP</text>

  <rect x="410" y="60" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Test code</text>
  <text x="500" y="102" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">via LdapTemplate</text>

  <line x1="230" y1="90" x2="405" y2="90" stroke="#3fb950" stroke-width="2" marker-end="url(#r1)"/>
  <line x1="405" y1="105" x2="230" y2="105" stroke="#3fb950" stroke-width="2" marker-end="url(#r2)"/>

  <text x="320" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no external process, no network hop, no installed directory software</text>

  <defs>
    <marker id="r1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="r2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

The embedded server and the test code run in the same process, with no external LDAP infrastructure needed.

## 5. Runnable example

The scenario: integration-testing a `UserLookupService` (built on the patterns from cards 0001–0004) against the embedded UnboundID server, starting with a basic search test, then testing an error path, and finally testing a write operation with per-test cleanup for isolation.

### Level 1 — Basic

```java
// UserLookupServiceTest.java
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;
import com.unboundid.ldap.listener.InMemoryDirectoryServer;
import com.unboundid.ldap.listener.InMemoryDirectoryServerConfig;
import com.unboundid.ldap.listener.InMemoryListenerConfig;

import static org.junit.jupiter.api.Assertions.*;

class UserLookupServiceTest {
    static InMemoryDirectoryServer server;
    static LdapTemplate template;

    @BeforeAll
    static void startServer() throws Exception {
        InMemoryDirectoryServerConfig config = new InMemoryDirectoryServerConfig("dc=example,dc=com");
        config.setListenerConfigs(InMemoryListenerConfig.createLDAPConfig("default", 0)); // 0 = random free port
        server = new InMemoryDirectoryServer(config);
        server.add("dn: dc=example,dc=com", "objectClass: domain", "dc: example");
        server.add("dn: ou=people,dc=example,dc=com", "objectClass: organizationalUnit", "ou: people");
        server.add("dn: uid=jsmith,ou=people,dc=example,dc=com",
            "objectClass: inetOrgPerson", "uid: jsmith", "cn: Jane Smith", "sn: Smith", "mail: jsmith@example.com");
        server.startListening();

        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://localhost:" + server.getListenPort());
        cs.setBase("dc=example,dc=com");
        cs.afterPropertiesSet();
        template = new LdapTemplate(cs);
    }

    @Test
    void findsExistingUserEmail() {
        var results = template.search("ou=people", "(uid=jsmith)",
            (org.springframework.ldap.core.AttributesMapper<String>) attrs -> (String) attrs.get("mail").get());
        assertEquals("jsmith@example.com", results.get(0));
    }
}
```

**How to run:** run with JUnit 5 and the UnboundID SDK on the test classpath — no external LDAP server, Docker, or network access needed at all. Expected result: the test passes, having exercised a genuine LDAP search against a real (if in-memory) directory server, starting fresh in a fraction of a second as part of the test run itself.

### Level 2 — Intermediate

Testing the "not found" path (card 0013's `NameNotFoundException` handling) needs no special server setup at all — searching for an entry that was never seeded naturally exercises that path against real server behavior.

```java
// UserLookupNotFoundTest.java (added to the same test class or a related one)
import org.junit.jupiter.api.Test;
import org.springframework.ldap.NameNotFoundException;

class UserLookupNotFoundTest {
    // assumes `template` from Level 1's setup, pointed at the same embedded server

    @Test
    void lookupOfNonexistentUserThrowsNameNotFound() {
        assertThrows(org.springframework.ldap.NameNotFoundException.class, () ->
            UserLookupServiceTest.template.lookup("uid=nosuchuser,ou=people",
                (org.springframework.ldap.core.AttributesMapper<String>) attrs -> (String) attrs.get("mail").get())
        );
    }
}
```

**How to run:** run this test against the same embedded server used in Level 1, with no `uid=nosuchuser` entry ever seeded. Expected result: the test passes, confirming that `lookup` against a genuinely absent entry throws `org.springframework.ldap.NameNotFoundException` — real server behavior, not a mocked stand-in for it, is what's actually being verified here.

### Level 3 — Advanced

Tests that write to the directory (binding new entries, modifying attributes) need proper isolation between test methods — one test's write shouldn't leak into and affect another test's assumptions about the directory's starting state. This level resets the embedded server's data between tests for full isolation, while still reusing the same running server process for speed.

```java
// IsolatedWriteTest.java
import org.junit.jupiter.api.*;
import org.springframework.ldap.core.LdapTemplate;
import com.unboundid.ldap.listener.InMemoryDirectoryServer;

import static org.junit.jupiter.api.Assertions.*;

class IsolatedWriteTest {
    static InMemoryDirectoryServer server;
    static LdapTemplate template;

    @BeforeAll
    static void startServer() throws Exception {
        // ... same setup as Level 1, omitted for brevity ...
        server = UserLookupServiceTest.server;
        template = UserLookupServiceTest.template;
    }

    @BeforeEach
    void resetData() throws Exception {
        server.clear(); // wipe all entries between tests, keeping the server process itself running
        server.add("dn: dc=example,dc=com", "objectClass: domain", "dc: example");
        server.add("dn: ou=people,dc=example,dc=com", "objectClass: organizationalUnit", "ou: people");
        // re-seed only the baseline data each test needs, explicitly, per test
    }

    @Test
    void bindingNewUserSucceeds() {
        javax.naming.directory.Attributes attrs = new javax.naming.directory.BasicAttributes();
        javax.naming.directory.BasicAttribute oc = new javax.naming.directory.BasicAttribute("objectClass");
        oc.add("top"); oc.add("inetOrgPerson");
        attrs.put(oc);
        attrs.put("sn", "Doe");
        attrs.put("cn", "New Person");

        template.bind("uid=newperson,ou=people", null, attrs);

        var found = template.search("ou=people", "(uid=newperson)", (Object obj) -> obj);
        assertEquals(1, found.size());
    }

    @Test
    void directoryStartsEmptyOfTestSpecificEntries() {
        // Because resetData() ran before this test too, "newperson" from the other test does NOT leak in here.
        var found = template.search("ou=people", "(uid=newperson)", (Object obj) -> obj);
        assertTrue(found.isEmpty());
    }
}
```

**How to run:** run both tests in `IsolatedWriteTest` together, in either order (JUnit doesn't guarantee method order by default). Expected result: both pass regardless of execution order — `server.clear()` plus re-seeding in `@BeforeEach` guarantees each test starts from the same known baseline, so `bindingNewUserSucceeds`'s write never leaks into `directoryStartsEmptyOfTestSpecificEntries`'s assumptions, even though both tests share the same running embedded server instance for speed.

## 6. Walkthrough

Tracing test execution across `IsolatedWriteTest`'s two methods, in execution order (assuming `bindingNewUserSucceeds` runs first):

1. `@BeforeAll startServer()` runs once for the whole test class, starting the embedded UnboundID server (or reusing the one from `UserLookupServiceTest` in this simplified example) — this is the expensive-relative-to-a-test-method setup, done only once.
2. Before `bindingNewUserSucceeds` runs, `@BeforeEach resetData()` executes: `server.clear()` wipes every entry currently in the in-memory directory, and the baseline `dc=example,dc=com`/`ou=people` structure is re-added — the directory is now in a known, minimal starting state.
3. `bindingNewUserSucceeds` runs: it binds `uid=newperson`, then searches for it and asserts exactly one match is found — this passes, since the bind just happened.
4. Before `directoryStartsEmptyOfTestSpecificEntries` runs, `@BeforeEach resetData()` executes *again* — `server.clear()` wipes `newperson` (added by the previous test) along with everything else, and the baseline structure is re-added fresh.
5. `directoryStartsEmptyOfTestSpecificEntries` runs: it searches for `uid=newperson` and asserts the result is empty — this passes, precisely because step 4's reset ran before it and removed the entry the previous test had created.

```
@BeforeAll: start embedded server ONCE

test 1: @BeforeEach resetData() -> clear + reseed baseline
        bindingNewUserSucceeds(): bind(newperson) -> search finds 1 -> PASS

test 2: @BeforeEach resetData() -> clear + reseed baseline  [wipes test 1's newperson]
        directoryStartsEmptyOfTestSpecificEntries(): search finds 0 -> PASS
```

## 7. Gotchas & takeaways

> Sharing one running embedded server instance across multiple test methods (for startup-cost efficiency) without resetting its data between tests is a common source of order-dependent test flakiness — a test that happens to pass when run alone can fail (or worse, pass for the wrong reason) when run after another test that left behind unexpected data. Always reset to a known baseline between tests that perform writes, as shown in Level 3.

- The embedded UnboundID server is a genuine LDAP server, not a mock — tests against it exercise real schema validation, filter evaluation, and DN handling, catching classes of bugs a hand-rolled `LdapTemplate` mock would miss entirely.
- Starting the server with port `0` lets the OS assign a free port automatically, avoiding port conflicts when tests run in parallel or in a shared CI environment.
- Seeding baseline data can be done either via direct `server.add(...)` calls (as shown) or by loading a pre-written LDIF file (card 0021) — the LDIF approach scales better for larger, more realistic seed datasets shared across many tests.
- For any test performing directory writes, reset the server's data (`server.clear()` plus re-seeding) between tests to guarantee isolation — relying on tests running in a specific order, or on one test's leftover state, is fragile and hard to debug when it eventually breaks.
- Because the embedded server runs in-process with no network hop, tests against it are typically very fast — there's rarely a good reason to fall back to mocking `LdapTemplate` directly for integration-style tests when this option is available.
