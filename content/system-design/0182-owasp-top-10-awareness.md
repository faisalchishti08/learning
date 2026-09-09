---
card: system-design
gi: 182
slug: owasp-top-10-awareness
title: OWASP Top 10 awareness
---

## 1. What it is

The **OWASP Top 10** is a regularly-updated list, published by the Open Worldwide Application Security Project, of the most critical and common web application security risks. It is not a checklist of specific bugs, but a set of *categories* of vulnerability — broken access control, injection, cryptographic failures, and others — each covering a whole family of related mistakes that show up repeatedly across real-world applications.

## 2. Why & when

Most application security incidents are not exotic, novel attacks — they are well-known categories of mistake, made again by a new team unaware of the pattern. Knowing the OWASP Top 10 gives developers a shared vocabulary and a checklist of the highest-impact things to actively watch for during design and code review, rather than discovering them only after an incident. Every developer building anything that handles user input, authentication, or sensitive data should be able to recognize at least the most common categories on sight, since these are exactly the mistakes that security reviews and audits look for first.

## 3. Core concept

- **Broken access control:** failing to properly enforce [authorization](0174-authentication-vs-authorization.md) checks — a classic example is an API endpoint that checks a user is logged in, but never checks whether *this* user is allowed to access the *specific* resource requested.
- **Injection (SQL, command, etc.):** untrusted input is concatenated directly into a query or command string, letting an attacker inject their own logic — the fix is always using parameterized queries or prepared statements, never string concatenation of user input into executable code.
- **Cryptographic failures:** using weak or outdated algorithms, storing passwords without proper hashing, or transmitting sensitive data without encryption ([in transit](0179-encryption-in-transit-tls-at-rest.md) or at rest).
- **Security misconfiguration:** default credentials left unchanged, overly permissive settings left at defaults, or verbose error messages that leak internal implementation details to an attacker.
- **Vulnerable and outdated components:** using a third-party library with a known, publicly disclosed vulnerability, simply because it was never updated — this is one of the easiest categories to prevent, since fixes usually already exist.

## 4. Diagram

```
   user input: username field on a login form
        |
        v
   VULNERABLE (SQL injection):
   query = "SELECT * FROM users WHERE username = '" + input + "'"
   attacker input: "' OR '1'='1"
        |
        v
   resulting query: SELECT * FROM users WHERE username = '' OR '1'='1'
        |
        v
   returns EVERY row - attacker bypasses authentication entirely

   SAFE (parameterized query):
   query = "SELECT * FROM users WHERE username = ?"
   query.setParameter(1, input)   <- the input is NEVER interpreted as part of the query's structure
```
*Caption: concatenating untrusted input directly into a query lets it change the query's actual logic; a parameterized query keeps the input as pure data, no matter what it contains.*

## 5. Runnable example

**Level 1 — Basic.** Demonstrate SQL-injection-style string concatenation and its vulnerability.

**Level 2 — The safe alternative: a parameterized query.** Show the same malicious input treated as pure data, not executable logic.

**Level 3 — Broken access control example.** Show an endpoint that checks authentication but forgets to check authorization for the specific resource.

```java
// OwaspTop10Demo.java
import java.util.*;

public class OwaspTop10Demo {

    static List<Map<String, String>> usersTable = List.of(
        Map.of("username", "alice", "password", "secret1"),
        Map.of("username", "bob", "password", "secret2")
    );

    // Level 1: VULNERABLE - simulates building a query by string concatenation (never do this).
    static List<Map<String, String>> vulnerableLogin(String usernameInput) {
        // Real SQL: "SELECT * FROM users WHERE username = '" + usernameInput + "'"
        // We simulate the INJECTION EFFECT directly: a malicious input can make the "query" match everything.
        if (usernameInput.contains("' OR '1'='1")) {
            System.out.println("  INJECTED LOGIC TRIGGERED - the 'query' now matches every row!");
            return usersTable; // the attacker's payload changed the query's actual meaning
        }
        return usersTable.stream().filter(u -> u.get("username").equals(usernameInput)).toList();
    }

    // Level 2: SAFE - the input is used strictly as DATA, an exact-match lookup, never as part of any logic.
    static List<Map<String, String>> safeParameterizedLogin(String usernameInput) {
        // Real SQL: "SELECT * FROM users WHERE username = ?" with usernameInput bound as a parameter.
        return usersTable.stream().filter(u -> u.get("username").equals(usernameInput)).toList();
    }

    // Level 3: broken access control - checks AUTHENTICATION but forgets per-resource AUTHORIZATION.
    static Map<Integer, String> orderOwners = Map.of(101, "alice", 102, "bob");

    static String vulnerableGetOrder(String loggedInUser, int orderId) {
        // BUG: only checks that SOMEONE is logged in, never checks if THIS user owns THIS order.
        return "order " + orderId + " details returned to " + loggedInUser;
    }

    static String fixedGetOrder(String loggedInUser, int orderId) {
        if (!loggedInUser.equals(orderOwners.get(orderId))) {
            return "403 Forbidden: " + loggedInUser + " does not own order " + orderId;
        }
        return "order " + orderId + " details returned to " + loggedInUser;
    }

    public static void main(String[] args) {
        System.out.println("-- injection --");
        System.out.println("vulnerable login with normal username \"alice\": " + vulnerableLogin("alice").size() + " row(s)");
        System.out.println("vulnerable login with injection payload:");
        System.out.println("  result: " + vulnerableLogin("' OR '1'='1").size() + " row(s) returned (should be 0 or 1!)");

        System.out.println("safe parameterized login with the SAME injection payload as literal data:");
        System.out.println("  result: " + safeParameterizedLogin("' OR '1'='1").size() + " row(s) returned (correctly 0 - no user has this literal username)");

        System.out.println("-- broken access control --");
        System.out.println("vulnerable endpoint - bob requesting alice's order 101: " + vulnerableGetOrder("bob", 101) + " (BUG: bob should not see this)");
        System.out.println("fixed endpoint - bob requesting alice's order 101: " + fixedGetOrder("bob", 101));
        System.out.println("fixed endpoint - alice requesting her OWN order 101: " + fixedGetOrder("alice", 101));
    }
}
```

**How to run:** save as `OwaspTop10Demo.java`, then run `java OwaspTop10Demo.java`.

## 6. Walkthrough

1. `vulnerableLogin("alice")` finds `"alice"` does not contain the injection pattern, so it falls to the normal filter, correctly returning the single matching row.
2. `vulnerableLogin("' OR '1'='1")` finds the input *does* contain the injection pattern, and the method's injection simulation returns the *entire* `usersTable` — modeling exactly what a real SQL injection does: it changes the query's actual logical condition from "username equals this exact string" to "true for every row," bypassing the intended filter completely.
3. `safeParameterizedLogin("' OR '1'='1")` runs the exact same malicious string through a plain, safe equality filter; since no row's `username` literally equals the string `"' OR '1'='1"`, it returns zero rows — the malicious payload is treated as pure data with no special meaning, exactly what a real parameterized query guarantees, since the database never re-interprets bound parameter values as query syntax.
4. `vulnerableGetOrder("bob", 101)` has no ownership check at all — it only implicitly assumes `loggedInUser` being non-null means access is fine, so it happily returns order 101's details to `bob`, even though order 101 actually belongs to `alice` — this is broken access control: authentication (bob is logged in) was checked, but authorization (does bob own *this* order) was not.
5. `fixedGetOrder("bob", 101)` checks `orderOwners.get(101)`, which is `"alice"`, against `loggedInUser` (`"bob"`); since they do not match, it returns a `403 Forbidden` message instead of leaking the order details — and the following call, `fixedGetOrder("alice", 101)`, passes the same check successfully since `alice` is genuinely the order's owner, correctly returning the order details only to its rightful owner.

## 7. Gotchas & takeaways

> Gotcha: "we use an ORM, so we're safe from SQL injection" is a common but incomplete assumption — most ORMs generate parameterized queries safely by default, but string-based query methods within the same ORM (raw/native query strings, dynamically-built `WHERE` clauses via string concatenation) can reintroduce the exact same vulnerability; the safety comes from *always* using parameter binding, not from the mere presence of an ORM.

- The OWASP Top 10 names recurring categories of mistake, not specific bugs — recognizing the category is what lets you catch a new instance of it before it ships.
- Injection vulnerabilities come from letting untrusted input change a query's or command's actual structure; the fix is always keeping input as pure data via parameter binding.
- Broken access control specifically means checking *who* someone is but forgetting to check *what they are allowed to do* to the *specific resource* being requested.
- Related concepts: [Authentication vs authorization](0174-authentication-vs-authorization.md) (the distinction broken access control specifically fails to enforce), [Encryption in transit (TLS) & at rest](0179-encryption-in-transit-tls-at-rest.md) (addresses the cryptographic-failures category), [Secrets management & rotation](0180-secrets-management-rotation.md) (addresses security-misconfiguration risks around hardcoded or stale credentials).
