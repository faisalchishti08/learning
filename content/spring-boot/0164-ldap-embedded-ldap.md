---
card: spring-boot
gi: 164
slug: ldap-embedded-ldap
title: LDAP / embedded LDAP
---

## 1. What it is

**LDAP** (Lightweight Directory Access Protocol) is a standard protocol for accessing directory services — typically used for user authentication and organisation-wide identity stores (Active Directory, OpenLDAP). Spring Boot auto-configures an `LdapTemplate` via `spring-boot-starter-data-ldap` using `spring.ldap.*` connection properties. **Embedded LDAP** (`spring-boot-starter-data-ldap` + `com.unboundid:unboundid-ldapsdk`) starts an in-memory LDAP server from an LDIF file — useful for testing and development.

## 2. Why & when

LDAP is the universal protocol for enterprise authentication. Use the Spring Boot LDAP support when:

- Authenticating users against **Active Directory** or **OpenLDAP** without a full OAuth2 flow.
- Looking up user attributes (email, department, group membership) from a corporate directory.
- Writing integration tests for LDAP-secured applications without an external LDAP server.
- Managing organisational data stored in directory format (employees, departments, access groups).

Avoid rolling your own LDAP authentication — use Spring Security's LDAP integration which handles bind, password compare, and referrals correctly.

## 3. Core concept

LDAP stores data as a tree of **entries** identified by **Distinguished Names (DNs)**. An entry has an **object class** (schema) and attributes (key-value pairs).

```
dc=example,dc=com                          ← root
  ou=users,dc=example,dc=com              ← organisational unit
    uid=alice,ou=users,dc=example,dc=com  ← user entry
      cn: Alice Smith
      mail: alice@example.com
      userPassword: {SSHA}...
```

`LdapTemplate` queries this tree with filters:

```java
template.search("ou=users", "(uid=alice)", (Attributes attrs) -> {
    return attrs.get("mail").get().toString();  // returns alice@example.com
});
```

## 4. Diagram

<svg viewBox="0 0 680 215" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="85" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="115" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">LdapTemplate</text>
  <rect x="235" y="40" width="195" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="332" y="60" text-anchor="middle" fill="#79c0ff" font-size="11" font-family="sans-serif">Production: Active Directory</text>
  <text x="332" y="76" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">spring.ldap.urls=ldap://ad:389</text>
  <rect x="235" y="100" width="195" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="332" y="120" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Dev/Test: Embedded LDAP</text>
  <text x="332" y="136" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">UnboundID in-memory server</text>
  <rect x="235" y="160" width="195" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="332" y="183" text-anchor="middle" fill="#6db33f" font-size="11" font-family="sans-serif">LDIF seed data loaded at startup</text>
  <line x1="162" y1="110" x2="231" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ld)"/>
  <line x1="162" y1="110" x2="231" y2="122" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ld)"/>
  <line x1="332" y1="147" x2="332" y2="158" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ld2)"/>
  <defs>
    <marker id="ld" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ld2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`LdapTemplate` connects to Active Directory in production; embedded LDAP (UnboundID) in dev/test — same code, different `spring.ldap.*` configuration.

## 5. Runnable example

```java
// LdapApp.java — Spring Boot project with spring-boot-starter-data-ldap
// pom.xml: spring-boot-starter-data-ldap, com.unboundid:unboundid-ldapsdk (test or compile scope)
// application.properties (embedded LDAP auto-enabled when unboundid-ldapsdk is on the classpath):
//   spring.ldap.embedded.port=8389
//   spring.ldap.embedded.ldif=classpath:test-users.ldif
//   spring.ldap.embedded.base-dn=dc=example,dc=com
//   spring.ldap.urls=ldap://localhost:8389
//   spring.ldap.base=dc=example,dc=com
//
// src/main/resources/test-users.ldif:
//   dn: dc=example,dc=com
//   objectclass: top
//   objectclass: domain
//   dc: example
//
//   dn: ou=users,dc=example,dc=com
//   objectclass: top
//   objectclass: organizationalUnit
//   ou: users
//
//   dn: uid=alice,ou=users,dc=example,dc=com
//   objectclass: top
//   objectclass: inetOrgPerson
//   uid: alice
//   cn: Alice Smith
//   sn: Smith
//   mail: alice@example.com

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.query.LdapQueryBuilder;
import org.springframework.web.bind.annotation.*;

import javax.naming.NamingException;
import javax.naming.directory.Attributes;
import java.util.List;
import java.util.Map;

@SpringBootApplication
public class LdapApp {
    public static void main(String[] args) {
        SpringApplication.run(LdapApp.class, args);
    }
}

@RestController
@RequestMapping("/users")
class UserController {

    private final LdapTemplate ldap;

    UserController(LdapTemplate ldap) { this.ldap = ldap; }

    // List all inetOrgPerson entries
    @GetMapping
    public List<Map<String, String>> all() {
        return ldap.search(
            LdapQueryBuilder.query().where("objectClass").is("inetOrgPerson"),
            (Attributes attrs) -> {
                try {
                    return Map.of(
                        "uid",  attr(attrs, "uid"),
                        "cn",   attr(attrs, "cn"),
                        "mail", attr(attrs, "mail")
                    );
                } catch (NamingException e) {
                    throw new RuntimeException(e);
                }
            }
        );
    }

    // Look up a specific user by uid
    @GetMapping("/{uid}")
    public Map<String, String> byUid(@PathVariable String uid) {
        return ldap.searchForObject(
            LdapQueryBuilder.query().where("uid").is(uid),
            (Attributes attrs) -> {
                try {
                    return Map.of(
                        "uid",  attr(attrs, "uid"),
                        "cn",   attr(attrs, "cn"),
                        "mail", attr(attrs, "mail")
                    );
                } catch (NamingException e) {
                    throw new RuntimeException(e);
                }
            }
        );
    }

    private String attr(Attributes a, String key) throws NamingException {
        var v = a.get(key);
        return v == null ? "" : v.get().toString();
    }
}
```

**How to run:**
1. Add `unboundid-ldapsdk` to `pom.xml` (compile scope for embedded LDAP at runtime).
2. Create `src/main/resources/test-users.ldif` with the LDIF shown in comments.
3. Start the app — embedded LDAP starts on port 8389.
4. `curl http://localhost:8080/users` → `[{"uid":"alice","cn":"Alice Smith","mail":"alice@example.com"}]`
5. `curl http://localhost:8080/users/alice` → same entry.

## 6. Walkthrough

- `spring-boot-starter-data-ldap` provides `LdapAutoConfiguration`, which creates `LdapTemplate` and `LdapContextSource` from `spring.ldap.*` properties.
- When `com.unboundid:unboundid-ldapsdk` is on the classpath, `EmbeddedLdapAutoConfiguration` starts an in-memory LDAP server on `spring.ldap.embedded.port` and loads the LDIF file specified by `spring.ldap.embedded.ldif`. This makes `LdapTemplate` work without any external LDAP server.
- `LdapQueryBuilder.query().where("objectClass").is("inetOrgPerson")` builds a filter `(objectClass=inetOrgPerson)` — the standard LDAP object class for person entries with email.
- `ldap.search(query, attributesMapper)` executes the query against `spring.ldap.base` and invokes the mapper for each matching entry's `Attributes`.
- `ldap.searchForObject(query, mapper)` expects exactly one result — throws `IncorrectResultSizeDataAccessException` if zero or multiple entries match.
- For production Active Directory: set `spring.ldap.urls=ldap://your-ad:389`, `spring.ldap.username=cn=serviceaccount,ou=...`, and `spring.ldap.password=...`; remove `spring.ldap.embedded.*` properties.

## 7. Gotchas & takeaways

> LDAP filters with user-supplied values must be **escaped** with `LdapUtils.encodeForFilter(value)`. A filter like `(uid=` + userInput + `)` is vulnerable to LDAP injection — malicious input can alter the query.

> Active Directory returns referrals by default (`LdapReferralException`). Set `spring.ldap.referral=follow` to auto-follow them, or `ignore` to suppress errors if referrals are not needed.

- `spring.ldap.embedded.validation.enabled=false` disables schema validation for the embedded server — useful when your LDIF uses custom attributes.
- `spring.ldap.base` sets the search base DN — all queries are relative to this base. Set it to the highest DN you need to search under.
- `@Entry` (Spring LDAP ORM) maps Java objects to LDAP entries similar to `@Entity` for JPA — an alternative to using `AttributesMapper` directly.
- `LdapTemplate.bind(dn, object, attrs)` creates a new LDAP entry; `rebind` replaces it; `unbind` deletes it.
