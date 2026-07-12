---
card: spring-security
gi: 111
slug: ldap-authentication-bindauthenticator
title: "LDAP authentication (BindAuthenticator)"
---

## 1. What it is

`BindAuthenticator` is Spring Security LDAP's primary way of checking a username/password pair: rather than fetching a user's stored password hash and comparing it locally (the way `DaoAuthenticationProvider` works against a JDBC `UserDetailsService`), it attempts to open a fresh LDAP connection **as the user themselves**, using the submitted username and password as the bind credentials — if the directory server accepts that bind, the credentials are correct; if it rejects it, they aren't. This means the application's authentication code never sees, stores, or compares a password hash at all — the directory server is the sole arbiter of whether a password is correct, which is precisely LDAP's traditional authentication model in enterprise environments.

```java
@Bean
public AuthenticationManager ldapAuthenticationManager(BaseLdapPathContextSource contextSource) {
    LdapBindAuthenticationManagerFactory factory = new LdapBindAuthenticationManagerFactory(contextSource);
    factory.setUserDnPatterns("uid={0},ou=people"); // {0} is replaced with the submitted username
    factory.setUserDetailsContextMapper(new PersonContextMapper());
    return factory.createAuthenticationManager();
}
```

## 2. Why & when

Every prior authentication mechanism in this course either checks a locally-stored credential (`formLogin()` against a `UserDetailsService`) or delegates entirely to an external federated identity system (OAuth2/OIDC, SAML). LDAP-based authentication sits in between: the directory server is neither "just another user store you query" nor "a full external identity provider with tokens and redirects" — it's a purpose-built protocol for exactly this kind of centralized, enterprise-wide credential store, and `BindAuthenticator`'s design (delegate the actual password check to the directory itself) exists because LDAP servers are specifically built to perform that check securely and consistently across every application that needs it, without ever handing out the underlying password hash to be compared elsewhere.

Reach for `BindAuthenticator`/LDAP authentication when:

- An organization already runs an LDAP directory (OpenLDAP, or the LDAP-compatible interface many Active Directory deployments expose) as its central identity store, and adding SAML/OIDC infrastructure on top would be more machinery than the situation needs — a direct LDAP bind is often the simplest integration path for an internal application.
- Password policy, complexity rules, and rotation are already enforced and audited at the directory level — delegating the actual check to the directory avoids re-implementing or duplicating any of that logic in the application.
- The application needs group membership or other directory attributes (department, job title) alongside authentication — LDAP naturally carries this as part of the same directory entry the bind succeeded against.
- The alternative, `PasswordComparisonAuthenticator` (fetching a stored password attribute and comparing it locally, rather than binding), is available but generally discouraged — it requires the application to have read access to password attributes and to implement the comparison itself, reintroducing exactly the "who's responsible for comparing credentials correctly" question LDAP bind authentication is designed to avoid.

## 3. Core concept

```
BindAuthenticator.authenticate(username, password):
  1. resolve the user's DISTINGUISHED NAME (DN) from the username, via a configured pattern
       e.g. userDnPatterns="uid={0},ou=people"  + base DN "dc=example,dc=com"
       -> "uid=alice,ou=people,dc=example,dc=com"
  2. open a NEW LDAP connection, attempting to BIND as that DN with the SUBMITTED password
       -- this is a REAL LDAP bind operation, not a local hash comparison
  3. bind SUCCEEDS -> credentials correct; the connection is used to also fetch attributes,
                       then immediately discarded (it was only ever used to TEST the password)
     bind FAILS    -> credentials incorrect (wrong password, unknown DN, account locked -- directory decides)
  4. build a UserDetails from the fetched attributes (mapped via a UserDetailsContextMapper)

The application NEVER sees, stores, or compares a password hash --
the directory server alone decides whether the bind succeeds.
```

Because the bind is a fresh, throwaway connection used only to test the password, a failed bind reveals nothing more specific than "this DN/password combination was rejected" — exactly the same non-specific failure signal `DaoAuthenticationProvider` gives for a wrong password, avoiding a username-enumeration side channel.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a submitted username being turned into a distinguished name via a pattern then a fresh LDAP connection attempting to bind as that DN with the submitted password if the bind succeeds attributes are fetched and a UserDetails is built if it fails authentication fails">
  <rect x="20" y="30" width="180" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">username="alice"</text>
  <text x="110" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">password="secret123"</text>

  <line x1="200" y1="55" x2="245" y2="55" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#ld111)"/>

  <rect x="250" y="30" width="200" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="350" y="50" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">userDnPatterns resolves DN</text>
  <text x="350" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">uid=alice,ou=people,dc=...</text>

  <line x1="350" y1="80" x2="350" y2="110" stroke="#8b949e" stroke-width="1.6" marker-end="url(#ld111b)"/>

  <rect x="250" y="112" width="200" height="46" rx="7" fill="#1c2430" stroke="#f0883e" stroke-width="1.4"/>
  <text x="350" y="132" fill="#f0883e" font-size="9.5" text-anchor="middle" font-family="sans-serif">FRESH bind attempt</text>
  <text x="350" y="148" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">connect AS this DN + password</text>

  <line x1="350" y1="158" x2="220" y2="185" stroke="#f85149" stroke-width="1.5" marker-end="url(#ld111c)"/>
  <line x1="350" y1="158" x2="480" y2="185" stroke="#3fb950" stroke-width="1.5" marker-end="url(#ld111d)"/>

  <rect x="120" y="188" width="200" height="20" rx="5" fill="#1c2430" stroke="#f85149" stroke-width="1.2"/>
  <text x="220" y="202" fill="#f85149" font-size="8.5" text-anchor="middle" font-family="sans-serif">bind FAILS -&gt; auth rejected</text>

  <rect x="380" y="188" width="200" height="20" rx="5" fill="#1c2430" stroke="#3fb950" stroke-width="1.2"/>
  <text x="480" y="202" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">bind SUCCEEDS -&gt; fetch attrs</text>

  <defs>
    <marker id="ld111" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="ld111b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="ld111c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="ld111d" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

The password itself is never compared locally — only the directory server's willingness to accept a bind decides success or failure.

## 5. Runnable example

The scenario: a from-scratch LDAP directory simulation and bind authenticator, growing from a single DN pattern into fetching attributes on success, then into handling a DN that resolves but a bind that still fails (wrong password) versus a username with no corresponding DN at all — both must fail identically, revealing nothing to an attacker about which case occurred.

### Level 1 — Basic

Resolve a DN from a username pattern, attempt a bind.

```java
import java.util.*;

public class LdapBindLevel1 {
    record DirectoryEntry(String dn, String password, Map<String, String> attributes) {}

    static class LdapDirectory {
        private final Map<String, DirectoryEntry> entriesByDn = new HashMap<>();
        void addEntry(DirectoryEntry entry) { entriesByDn.put(entry.dn(), entry); }

        // simulates a REAL LDAP bind attempt -- a fresh connection, live check against the directory
        boolean bind(String dn, String password) {
            DirectoryEntry entry = entriesByDn.get(dn);
            return entry != null && entry.password().equals(password);
        }
    }

    static class BindAuthenticator {
        private final LdapDirectory directory;
        private final String userDnPattern; // e.g. "uid={0},ou=people,dc=example,dc=com"

        BindAuthenticator(LdapDirectory directory, String userDnPattern) {
            this.directory = directory;
            this.userDnPattern = userDnPattern;
        }

        boolean authenticate(String username, String password) {
            String dn = userDnPattern.replace("{0}", username);
            return directory.bind(dn, password);
        }
    }

    public static void main(String[] args) {
        LdapDirectory directory = new LdapDirectory();
        directory.addEntry(new DirectoryEntry("uid=alice,ou=people,dc=example,dc=com", "secret123",
                Map.of("cn", "Alice Example")));

        BindAuthenticator authenticator = new BindAuthenticator(directory, "uid={0},ou=people,dc=example,dc=com");

        System.out.println("correct password: " + authenticator.authenticate("alice", "secret123"));
        System.out.println("wrong password: " + authenticator.authenticate("alice", "WRONG"));
    }
}
```

**How to run:** save as `LdapBindLevel1.java`, run `java LdapBindLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
correct password: true
wrong password: false
```

`authenticate` resolves the DN by substituting the username into the configured pattern, then attempts a bind — the directory itself (`LdapDirectory.bind`) is the sole arbiter of whether the password matches, exactly mirroring `BindAuthenticator`'s delegation to a real directory server.

### Level 2 — Intermediate

On a successful bind, fetch the entry's attributes and build a `UserDetails`-equivalent object — mirroring `UserDetailsContextMapper`.

```java
import java.util.*;

public class LdapBindLevel2 {
    record DirectoryEntry(String dn, String password, Map<String, String> attributes) {}
    record LdapUserDetails(String username, String displayName, List<String> authorities) {}

    static class LdapAuthenticationException extends RuntimeException {
        LdapAuthenticationException(String message) { super(message); }
    }

    static class LdapDirectory {
        private final Map<String, DirectoryEntry> entriesByDn = new HashMap<>();
        void addEntry(DirectoryEntry entry) { entriesByDn.put(entry.dn(), entry); }

        boolean bind(String dn, String password) {
            DirectoryEntry entry = entriesByDn.get(dn);
            return entry != null && entry.password().equals(password);
        }

        DirectoryEntry fetch(String dn) { return entriesByDn.get(dn); } // separate READ, using the now-bound connection
    }

    static class BindAuthenticator {
        private final LdapDirectory directory;
        private final String userDnPattern;

        BindAuthenticator(LdapDirectory directory, String userDnPattern) {
            this.directory = directory;
            this.userDnPattern = userDnPattern;
        }

        LdapUserDetails authenticate(String username, String password) {
            String dn = userDnPattern.replace("{0}", username);
            if (!directory.bind(dn, password)) {
                throw new LdapAuthenticationException("bind failed for " + username);
            }
            // the bind SUCCEEDED -- now use that same authenticated context to read attributes
            DirectoryEntry entry = directory.fetch(dn);
            return new LdapUserDetails(username, entry.attributes().get("cn"), List.of("ROLE_USER"));
        }
    }

    public static void main(String[] args) {
        LdapDirectory directory = new LdapDirectory();
        directory.addEntry(new DirectoryEntry("uid=alice,ou=people,dc=example,dc=com", "secret123",
                Map.of("cn", "Alice Example", "department", "Engineering")));

        BindAuthenticator authenticator = new BindAuthenticator(directory, "uid={0},ou=people,dc=example,dc=com");

        LdapUserDetails details = authenticator.authenticate("alice", "secret123");
        System.out.println("authenticated: " + details);
    }
}
```

**How to run:** save as `LdapBindLevel2.java`, run `java LdapBindLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
authenticated: LdapUserDetails[username=alice, displayName=Alice Example, authorities=[ROLE_USER]]
```

What changed: after the bind succeeds, `authenticate` fetches the entry's attributes and builds an `LdapUserDetails` from them — mirroring how a real `BindAuthenticator` uses the just-established, successfully-bound connection both to confirm the password and to read the user's directory attributes in the same round trip.

### Level 3 — Advanced

Distinguish (from the *caller's* point of view, deliberately) a username with no matching DN at all from a DN that exists but whose password is wrong — both must fail identically, since revealing the difference would let an attacker enumerate valid usernames.

```java
import java.util.*;

public class LdapBindLevel3 {
    record DirectoryEntry(String dn, String password, Map<String, String> attributes) {}
    record LdapUserDetails(String username, String displayName, List<String> authorities) {}

    static class LdapAuthenticationException extends RuntimeException {
        LdapAuthenticationException(String message) { super(message); }
    }

    static class LdapDirectory {
        private final Map<String, DirectoryEntry> entriesByDn = new HashMap<>();
        void addEntry(DirectoryEntry entry) { entriesByDn.put(entry.dn(), entry); }

        // returns an OPAQUE boolean either way -- "no such DN" and "wrong password" look IDENTICAL to the caller
        boolean bind(String dn, String password) {
            DirectoryEntry entry = entriesByDn.get(dn);
            if (entry == null) return false;      // DN does not exist
            return entry.password().equals(password); // DN exists, password checked
        }

        DirectoryEntry fetch(String dn) { return entriesByDn.get(dn); }
    }

    static class BindAuthenticator {
        private final LdapDirectory directory;
        private final String userDnPattern;

        BindAuthenticator(LdapDirectory directory, String userDnPattern) {
            this.directory = directory;
            this.userDnPattern = userDnPattern;
        }

        LdapUserDetails authenticate(String username, String password) {
            String dn = userDnPattern.replace("{0}", username);
            // the SAME generic failure message regardless of WHY the bind failed
            if (!directory.bind(dn, password)) {
                throw new LdapAuthenticationException("Bad credentials");
            }
            DirectoryEntry entry = directory.fetch(dn);
            return new LdapUserDetails(username, entry.attributes().get("cn"), List.of("ROLE_USER"));
        }
    }

    public static void main(String[] args) {
        LdapDirectory directory = new LdapDirectory();
        directory.addEntry(new DirectoryEntry("uid=alice,ou=people,dc=example,dc=com", "secret123",
                Map.of("cn", "Alice Example")));

        BindAuthenticator authenticator = new BindAuthenticator(directory, "uid={0},ou=people,dc=example,dc=com");

        System.out.println("--- genuinely unknown username ---");
        try {
            authenticator.authenticate("nonexistent-user", "anything");
        } catch (LdapAuthenticationException e) {
            System.out.println("rejected: " + e.getMessage());
        }

        System.out.println("--- known username, wrong password ---");
        try {
            authenticator.authenticate("alice", "WRONG-password");
        } catch (LdapAuthenticationException e) {
            System.out.println("rejected: " + e.getMessage());
        }

        System.out.println("--- both failures produced an IDENTICAL message, revealing nothing about which case occurred ---");
    }
}
```

**How to run:** save as `LdapBindLevel3.java`, run `java LdapBindLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
--- genuinely unknown username ---
rejected: Bad credentials
--- known username, wrong password ---
rejected: Bad credentials
--- both failures produced an IDENTICAL message, revealing nothing about which case occurred ---
```

What changed: `LdapDirectory.bind` deliberately collapses "DN doesn't exist" and "DN exists but password is wrong" into the same `false` return value, and `BindAuthenticator.authenticate` throws the same generic `"Bad credentials"` message either way — an attacker probing with a list of usernames gets no signal distinguishing "this account doesn't exist" from "this account exists but you guessed wrong," which is exactly the property that prevents username enumeration via the login endpoint.

## 6. Walkthrough

Trace alice's successful authentication from Level 2, then the unknown-username case from Level 3, end to end.

**Step 1 — the login form submission:**
```
POST /login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=alice&password=secret123
```

**Step 2 — DN resolution.** `userDnPattern.replace("{0}", "alice")` computes `"uid=alice,ou=people,dc=example,dc=com"` — this is purely local string substitution, no network activity yet.

**Step 3 — the bind attempt, a real LDAP operation:**
```
LDAP Bind Request
  DN: uid=alice,ou=people,dc=example,dc=com
  Password: secret123
```
This corresponds to `directory.bind(dn, password)`. Inside, `entriesByDn.get(dn)` finds alice's entry, and `entry.password().equals("secret123")` is `true` — the (simulated) directory server accepts the bind.

**Step 4 — attribute fetch, using the now-authenticated context.** `directory.fetch(dn)` retrieves the same entry's `attributes` map — in a real LDAP client, this reuses the connection that was just successfully bound, rather than opening a separate one.

**Step 5 — `UserDetails` construction.** `new LdapUserDetails("alice", entry.attributes().get("cn"), List.of("ROLE_USER"))` builds the object that becomes this request's authenticated principal — `"cn"` (`"Alice Example"`) came directly from the directory entry's own attributes, requiring no separate database lookup.

**Step 6 — the response:**
```
HTTP/1.1 302 Found
Location: /
Set-Cookie: JSESSIONID=...
```

**Contrast — the unknown-username case.** `userDnPattern.replace("{0}", "nonexistent-user")` computes a DN for a user that was never added to the directory. `directory.bind(...)` looks it up, finds `entriesByDn.get(dn)` returns `null`, and returns `false` immediately — the same boolean result a *wrong password* for a real user would have produced. `BindAuthenticator.authenticate` throws the identical `"Bad credentials"` message in both cases.

```
alice + correct password:  DN resolves -> bind SUCCEEDS -> fetch attrs -> AUTHENTICATED
alice + wrong password:    DN resolves -> bind FAILS    -> "Bad credentials" (generic)
unknown-user + anything:   DN resolves (syntactically) -> bind FAILS (no such DN) -> "Bad credentials" (SAME message)
```

## 7. Gotchas & takeaways

> **Gotcha:** never let an authentication failure message (or its timing, or its HTTP status) differ based on whether the *username* was valid — `BindAuthenticator`'s design (one opaque bind operation, one generic failure) is specifically what prevents an attacker from using the login form itself as a username-enumeration oracle. Custom LDAP integration code that adds its own "check if the DN exists first, then bind" logic risks reintroducing exactly this leak if the two failure paths aren't kept indistinguishable.

- `BindAuthenticator` delegates the actual password check to the directory server itself, via a live bind attempt — the application never stores, sees, or compares a password hash.
- `userDnPatterns` defines how a submitted username becomes the distinguished name the bind is attempted against; getting this pattern wrong causes every login to fail with the same generic "Bad credentials," regardless of how correct the password was.
- A successful bind is typically also used to fetch the user's directory attributes in the same operation, which a `UserDetailsContextMapper` then turns into a `UserDetails`/`GrantedAuthority` set.
- An unknown username and a known username with a wrong password must produce identical failure behavior — this is a deliberate security property, not an implementation shortcut, and any custom LDAP authentication code should preserve it.
- `PasswordComparisonAuthenticator` (comparing a fetched password attribute locally) is the alternative to binding, but it requires read access to password data and reimplements comparison logic the directory is already built to perform correctly — bind authentication is the generally preferred default.
