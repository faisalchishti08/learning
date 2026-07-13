---
card: spring-ldap
gi: 7
slug: binding-unbinding-entries
title: "Binding & unbinding entries"
---

## 1. What it is

In LDAP terminology, **binding** an entry means creating a brand-new entry at a specific DN in the directory (not to be confused with the "bind" used for authentication, which is an unrelated overloaded use of the same word). **Unbinding** means deleting an entry at a given DN. `LdapTemplate.bind(dn, contextObject, attributes)` and `LdapTemplate.unbind(dn)` are the create and delete operations of Spring LDAP's CRUD story, complementing `search`/`lookup` (reads, card 0004) and `modifyAttributes` (updates, card 0008).

## 2. Why & when

Directories aren't just read from — applications provisioning new users, creating groups, or registering new organizational units need a way to add entries, and offboarding or cleanup workflows need a way to remove them. `bind` and `unbind` exist as the directory equivalent of `INSERT` and `DELETE` in a relational database, and like those operations, they're one-shot: a bind either succeeds in creating the whole entry, or fails outright (an entry already existing at that DN, for instance, throws `NameAlreadyBoundException`) — there's no partial bind.

Use `bind` when:

- Provisioning a new user, group, or organizational unit as part of an onboarding or setup workflow.
- Migrating data into a directory from another system for the first time.

Use `unbind` when:

- Offboarding a user or decommissioning a group.
- Cleaning up test entries created during automated testing.

## 3. Core concept

Think of `bind` as filing a brand-new folder in a specific drawer of the filing cabinet — you specify exactly which drawer and label (the DN), and hand over the folder's contents (attributes). If a folder with that exact label already exists in that drawer, the filing clerk refuses (the directory refuses a duplicate DN). `unbind` is the reverse: pulling a folder out of its drawer and shredding it — after that, nothing exists at that DN anymore, and any DN previously pointing to it is now dangling.

```java
Attributes attrs = new BasicAttributes();
attrs.put("objectClass", new BasicAttribute("objectClass", "inetOrgPerson")); // simplified; real code adds all required objectClasses
attrs.put("sn", "Smith");
attrs.put("cn", "Jane Smith");

ldapTemplate.bind("uid=jsmith,ou=people", null, attrs);
// ... later ...
ldapTemplate.unbind("uid=jsmith,ou=people");
```

A binding entry must satisfy the directory schema's requirements for whatever `objectClass` values it declares — LDAP servers reject entries missing attributes their declared object classes require (`ObjectClassViolationException`), the directory-schema equivalent of a database `NOT NULL` constraint failing.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="bind creates a new entry at a DN; unbind removes the entry at a DN">
  <rect x="30" y="30" width="220" height="50" rx="6" fill="none" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="140" y="60" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(nothing at this DN)</text>

  <line x1="270" y1="55" x2="330" y2="55" stroke="#3fb950" stroke-width="2" marker-end="url(#g1)"/>
  <text x="300" y="45" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">bind()</text>

  <rect x="340" y="30" width="220" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="450" y="60" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Entry exists at DN</text>

  <line x1="450" y1="80" x2="450" y2="120" stroke="#ff7b72" stroke-width="2" marker-end="url(#g2)"/>
  <text x="480" y="105" fill="#ff7b72" font-size="9" text-anchor="middle" font-family="sans-serif">unbind()</text>

  <rect x="340" y="130" width="220" height="45" rx="6" fill="none" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="450" y="157" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(nothing at this DN again)</text>

  <defs>
    <marker id="g1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="g2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#ff7b72"/></marker>
  </defs>
</svg>

`bind` moves a DN from empty to occupied; `unbind` reverses it — both are all-or-nothing operations.

## 5. Runnable example

The scenario: provision and later remove a user entry, starting with the bare operations, then guarding against duplicate binds, and finally making the provisioning step idempotent for safe retries.

### Level 1 — Basic

```java
// ProvisionUser.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;

import javax.naming.directory.*;

public class ProvisionUser {
    public static void main(String[] args) {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://localhost:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=admin,dc=example,dc=com");
        cs.setPassword("adminpass");
        cs.afterPropertiesSet();

        LdapTemplate template = new LdapTemplate(cs);

        Attributes attrs = new BasicAttributes();
        BasicAttribute objectClass = new BasicAttribute("objectClass");
        objectClass.add("top");
        objectClass.add("inetOrgPerson");
        attrs.put(objectClass);
        attrs.put("sn", "Doe");
        attrs.put("cn", "New Employee");

        template.bind("uid=newuser,ou=people", null, attrs);
        System.out.println("Bound uid=newuser");

        template.unbind("uid=newuser,ou=people");
        System.out.println("Unbound uid=newuser");
    }
}
```

**How to run:** run against a writable directory with `ou=people,dc=example,dc=com` already present. Expected output: `Bound uid=newuser` followed by `Unbound uid=newuser` — the entry exists briefly, then is removed.

### Level 2 — Intermediate

Calling `bind` a second time for a DN that's already occupied (say, a retried provisioning request) throws `NameAlreadyBoundException` — an unhandled exception that a naive retry loop would crash on.

```java
// SafeProvisionUser.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.NameAlreadyBoundException;

import javax.naming.directory.*;

public class SafeProvisionUser {
    private final LdapTemplate template;

    public SafeProvisionUser(LdapTemplate template) {
        this.template = template;
    }

    public boolean provision(String uid, String surname, String commonName) {
        Attributes attrs = new BasicAttributes();
        BasicAttribute objectClass = new BasicAttribute("objectClass");
        objectClass.add("top");
        objectClass.add("inetOrgPerson");
        attrs.put(objectClass);
        attrs.put("sn", surname);
        attrs.put("cn", commonName);

        try {
            template.bind("uid=" + uid + ",ou=people", null, attrs);
            return true;
        } catch (NameAlreadyBoundException e) {
            // Entry already provisioned — likely a retried request, not a real failure.
            System.out.println("uid=" + uid + " already provisioned, skipping.");
            return false;
        }
    }
}
```

**How to run:** call `provision("newuser", "Doe", "New Employee")` twice in a row. Expected result: the first call returns `true` and creates the entry; the second call catches `NameAlreadyBoundException`, logs a message, and returns `false` instead of crashing — a retried provisioning request is now safe.

### Level 3 — Advanced

True idempotency means the *outcome* is the same whether the operation ran once or was retried after a partial failure (e.g. the bind succeeded but the response was lost, so the caller retries believing it failed). This level checks existence first and treats "already exists with the same target attributes" as success rather than merely "don't crash."

```java
// IdempotentProvisionUser.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.NameAlreadyBoundException;
import org.springframework.ldap.NameNotFoundException;

import javax.naming.directory.*;

public class IdempotentProvisionUser {
    private final LdapTemplate template;

    public IdempotentProvisionUser(LdapTemplate template) {
        this.template = template;
    }

    public enum Result { CREATED, ALREADY_EXISTS_MATCHING, CONFLICT }

    public Result provision(String uid, String surname, String commonName) {
        String dn = "uid=" + uid + ",ou=people";
        Attributes attrs = new BasicAttributes();
        BasicAttribute objectClass = new BasicAttribute("objectClass");
        objectClass.add("top");
        objectClass.add("inetOrgPerson");
        attrs.put(objectClass);
        attrs.put("sn", surname);
        attrs.put("cn", commonName);

        try {
            template.bind(dn, null, attrs);
            return Result.CREATED;
        } catch (NameAlreadyBoundException e) {
            // Check whether the existing entry matches what we intended to create.
            try {
                Attributes existing = template.lookup(dn, (Object obj) -> (Attributes) obj);
                String existingSn = (String) existing.get("sn").get();
                if (surname.equals(existingSn)) {
                    return Result.ALREADY_EXISTS_MATCHING; // safe retry: same intended state
                }
                return Result.CONFLICT; // a *different* entry occupies this DN — needs human attention
            } catch (NameNotFoundException race) {
                // Deleted between the failed bind and this lookup — rare, but handle it rather than crash.
                return Result.CONFLICT;
            }
        }
    }
}
```

**How to run:** call `provision("newuser", "Doe", "New Employee")` twice — expect `CREATED` then `ALREADY_EXISTS_MATCHING`, confirming the retry recognizes the existing entry matches the intended state. Then call `provision("newuser", "Someone-Else", "Different Person")` against the same still-existing `uid=newuser`: expect `CONFLICT`, since the existing entry's `sn` doesn't match what this call intended — surfacing a real naming collision instead of silently accepting or silently failing.

## 6. Walkthrough

Tracing a retried `provision("newuser", "Doe", "New Employee")` call, in execution order:

1. `template.bind(dn, null, attrs)` is attempted; because a prior call already succeeded in creating this exact DN, the directory server rejects the bind with a "name already bound" error.
2. Spring LDAP translates the underlying JNDI exception into `NameAlreadyBoundException`, caught by the surrounding `catch` block.
3. Rather than immediately treating this as a failure, the code performs a `lookup(dn, ...)` to read what's actually there now.
4. The existing entry's `sn` attribute is compared against the `surname` this call intended to set.
5. Since both calls used `"Doe"`, the comparison matches, and `Result.ALREADY_EXISTS_MATCHING` is returned — telling the caller "the desired end state already holds," which is the correct outcome for a safely-retried provisioning request.
6. If a *different* `surname` had been intended (a genuine naming collision, not a retry of the same request), the mismatch would instead produce `Result.CONFLICT`, signaling that this needs human attention rather than being silently accepted or silently treated as a harmless retry.

```
provision("newuser","Doe",...)
  bind(dn, attrs) -> NameAlreadyBoundException
     -> lookup(dn) -> existing.sn == "Doe"?
          yes -> ALREADY_EXISTS_MATCHING  (safe: retry of the same intent)
          no  -> CONFLICT                 (unsafe: different intent, same DN)
```

## 7. Gotchas & takeaways

> A directory entry must satisfy every attribute its declared `objectClass` values require, or `bind` fails with `ObjectClassViolationException` — for `inetOrgPerson`, both `sn` and `cn` are mandatory. Forgetting a required attribute is one of the most common first-time errors when binding a new entry, and the resulting error message names the missing attribute clearly if read carefully.

- `bind` in Spring LDAP means "create a new entry," unrelated to the authentication "bind" performed when a `ContextSource` (card 0002) connects — the same word, two different LDAP meanings.
- `bind` is all-or-nothing: a partially-invalid attribute set fails the entire creation, leaving no entry behind, rather than creating a partial one.
- `unbind` on a DN that doesn't exist throws `NameNotFoundException` — guard against this the same way a duplicate `bind` needs guarding, if the delete might be retried or run against an already-cleaned-up entry.
- True idempotent provisioning (Level 3) means checking not just "does something exist here" but "does the right thing exist here" — a naive existence check alone can mask a real naming conflict between two different intended entries.
- For entries with several required attributes, building the `Attributes`/`BasicAttribute` structure by hand (as shown) is verbose; for anything beyond a couple of attributes, consider building via `DirContextAdapter` for the more ergonomic `setAttributeValue` API instead.
