---
card: spring-ldap
gi: 18
slug: contextsource-transaction-manager
title: "ContextSource transaction manager"
---

## 1. What it is

`ContextSourceTransactionManager` is Spring's `PlatformTransactionManager` implementation for LDAP, plugging Spring LDAP's compensating-transaction mechanism (card 0017) into the standard Spring transaction infrastructure — the same `@Transactional` annotation, the same declarative transaction demarcation used across Spring's JDBC, JPA, and other transaction managers. Registering it as a bean and enabling `@EnableTransactionManagement` is what makes `@Transactional` methods touching `LdapTemplate` participate in compensating rollback at all; without it, `@Transactional` on an LDAP-only method would silently do nothing.

## 2. Why & when

Spring's `@Transactional` annotation is generic — it works with whichever `PlatformTransactionManager` bean is configured for the relevant transaction context, and it has no built-in awareness of LDAP specifically. `ContextSourceTransactionManager` exists to be that concrete manager for LDAP: it wraps a `ContextSource` (card 0002), intercepts `LdapTemplate` operations performed within a transactional method, and manages the compensating-action bookkeeping described in card 0017 behind the scenes.

Configure it whenever:

- Any part of the application uses `@Transactional` on a method that performs more than one `LdapTemplate` write and needs the compensating rollback behavior.
- The application otherwise already uses Spring's declarative transaction model elsewhere (JPA transactions, for instance) and wants LDAP operations to participate in the same familiar annotation-driven style, even though the underlying guarantee is weaker than a database transaction.

If a method only ever performs a single `LdapTemplate` write, wrapping it in `@Transactional` adds no real safety — a single write is already atomic from the directory server's own point of view, with nothing to compensate for.

## 3. Core concept

Think of `ContextSourceTransactionManager` as the stage manager who actually coordinates the stagehand described in card 0017's analogy — Spring's `@Transactional` annotation is the *cue* ("this scene needs to be reversible"), and `ContextSourceTransactionManager` is the one who actually assigns and directs the stagehand, tracking what's been moved and issuing the "put it back" instructions if the scene has to stop. Without a stage manager configured at all, the cue is given but nobody is listening — `@Transactional` becomes a no-op decoration with no manager wired up to act on it.

```java
@Configuration
@EnableTransactionManagement
public class LdapTxConfig {

    @Bean
    public ContextSourceTransactionManager transactionManager(ContextSource contextSource) {
        return new ContextSourceTransactionManager(contextSource);
    }
}
```

Internally, `ContextSourceTransactionManager` works by wrapping the `DirContext` obtained from the underlying `ContextSource` in a transaction-aware proxy for the duration of the transactional method — every `LdapTemplate` call made during that method reuses the same underlying context and has its operations recorded, rather than each call independently obtaining and releasing its own context as it would outside a transaction.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ContextSourceTransactionManager sits between Spring's transaction infrastructure and the ContextSource, recording operations for potential compensation">
  <rect x="20" y="80" width="160" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="100" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Transactional</text>
  <text x="100" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">method</text>

  <rect x="250" y="80" width="220" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ContextSourceTransactionManager</text>
  <text x="360" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">records ops, compensates on failure</text>

  <rect x="540" y="80" width="110" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="595" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ContextSource</text>

  <line x1="180" y1="110" x2="245" y2="110" stroke="#3fb950" stroke-width="2" marker-end="url(#n1)"/>
  <line x1="470" y1="110" x2="535" y2="110" stroke="#3fb950" stroke-width="2" marker-end="url(#n2)"/>

  <defs>
    <marker id="n1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="n2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

`ContextSourceTransactionManager` is the missing link that makes `@Transactional` actually engage Spring LDAP's compensating rollback behavior.

## 5. Runnable example

The scenario: verifying that `@Transactional` genuinely does nothing without the manager configured, then wiring it correctly, and finally handling nested transactional calls correctly.

### Level 1 — Basic

```java
// MissingManagerDemo.java
// Deliberately WITHOUT @EnableTransactionManagement / ContextSourceTransactionManager configured.
import org.springframework.transaction.annotation.Transactional;
import org.springframework.ldap.core.LdapTemplate;
import javax.naming.directory.*;

public class MissingManagerDemo {
    private final LdapTemplate template;

    public MissingManagerDemo(LdapTemplate template) {
        this.template = template;
    }

    @Transactional // has NO effect: no PlatformTransactionManager is configured for this context
    public void provisionUserWithGroup(String uid, String groupDn) {
        template.bind("uid=" + uid + ",ou=people", null, minimalAttrs(uid));
        ModificationItem[] mods = {
            new ModificationItem(DirContext.ADD_ATTRIBUTE,
                new BasicAttribute("member", "uid=" + uid + ",ou=people,dc=example,dc=com"))
        };
        template.modifyAttributes(groupDn, mods); // fails against a bad groupDn
    }

    private static Attributes minimalAttrs(String uid) {
        Attributes attrs = new BasicAttributes();
        BasicAttribute oc = new BasicAttribute("objectClass");
        oc.add("top"); oc.add("inetOrgPerson");
        attrs.put(oc); attrs.put("sn", uid); attrs.put("cn", uid);
        return attrs;
    }
}
```

**How to run:** run this without any transaction manager bean configured, using a bad `groupDn` to force the second call to fail. Expected result: the `bind` succeeds and is **not** rolled back — checking the directory afterward shows the orphaned `uid=...,ou=people` entry still present, exactly as in card 0017's Level 1, because `@Transactional` here has nothing to actually drive it.

### Level 2 — Intermediate

Configuring `ContextSourceTransactionManager` and `@EnableTransactionManagement` correctly is what makes the exact same `@Transactional` method actually trigger compensation.

```java
// ProperlyConfiguredDemo.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.ldap.core.ContextSource;
import org.springframework.ldap.transaction.compensating.manager.ContextSourceTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.ldap.core.LdapTemplate;

import javax.naming.directory.*;

@Configuration
@EnableTransactionManagement
class TxManagerConfig {
    @Bean
    public ContextSourceTransactionManager transactionManager(ContextSource contextSource) {
        return new ContextSourceTransactionManager(contextSource);
    }
}

public class ProperlyConfiguredDemo {
    private final LdapTemplate template;

    public ProperlyConfiguredDemo(LdapTemplate template) {
        this.template = template;
    }

    @Transactional
    public void provisionUserWithGroup(String uid, String groupDn) {
        template.bind("uid=" + uid + ",ou=people", null, minimalAttrs(uid));
        ModificationItem[] mods = {
            new ModificationItem(DirContext.ADD_ATTRIBUTE,
                new BasicAttribute("member", "uid=" + uid + ",ou=people,dc=example,dc=com"))
        };
        template.modifyAttributes(groupDn, mods);
    }

    private static Attributes minimalAttrs(String uid) {
        Attributes attrs = new BasicAttributes();
        BasicAttribute oc = new BasicAttribute("objectClass");
        oc.add("top"); oc.add("inetOrgPerson");
        attrs.put(oc); attrs.put("sn", uid); attrs.put("cn", uid);
        return attrs;
    }
}
```

**How to run:** run the identical failure scenario with `TxManagerConfig` active in the Spring context. Expected result: after the exception, the directory shows **no** orphaned `uid=...,ou=people` entry — the exact same method body as Level 1 now correctly compensates, because a real `PlatformTransactionManager` (`ContextSourceTransactionManager`) is configured and actually driving `@Transactional`'s behavior.

### Level 3 — Advanced

A transactional method calling another transactional method (a provisioning workflow calling a helper method that's separately annotated `@Transactional`) needs to correctly participate in the *same* outer transaction rather than starting an unrelated nested one, so that a failure anywhere in the whole chain compensates everything, not just the inner method's own operations.

```java
// NestedTransactionalDemo.java
import org.springframework.transaction.annotation.Transactional;
import org.springframework.ldap.core.LdapTemplate;
import javax.naming.directory.*;

public class NestedTransactionalDemo {
    private final LdapTemplate template;

    public NestedTransactionalDemo(LdapTemplate template) {
        this.template = template;
    }

    @Transactional // outer transaction boundary
    public void onboardNewHire(String uid, String groupDn, String mailingListDn) {
        createUserEntry(uid);          // participates in the SAME transaction (default propagation: REQUIRED)
        addToGroup(uid, groupDn);      // also participates in the same transaction
        addToMailingList(uid, mailingListDn); // if this fails, ALL prior steps compensate together
    }

    @Transactional
    public void createUserEntry(String uid) {
        template.bind("uid=" + uid + ",ou=people", null, minimalAttrs(uid));
    }

    @Transactional
    public void addToGroup(String uid, String groupDn) {
        ModificationItem[] mods = {
            new ModificationItem(DirContext.ADD_ATTRIBUTE,
                new BasicAttribute("member", "uid=" + uid + ",ou=people,dc=example,dc=com"))
        };
        template.modifyAttributes(groupDn, mods);
    }

    @Transactional
    public void addToMailingList(String uid, String mailingListDn) {
        ModificationItem[] mods = {
            new ModificationItem(DirContext.ADD_ATTRIBUTE,
                new BasicAttribute("uniqueMember", "uid=" + uid + ",ou=people,dc=example,dc=com"))
        };
        template.modifyAttributes(mailingListDn, mods); // fails if mailingListDn is invalid
    }

    private static Attributes minimalAttrs(String uid) {
        Attributes attrs = new BasicAttributes();
        BasicAttribute oc = new BasicAttribute("objectClass");
        oc.add("top"); oc.add("inetOrgPerson");
        attrs.put(oc); attrs.put("sn", uid); attrs.put("cn", uid);
        return attrs;
    }
}
```

**How to run:** call `onboardNewHire(uid, validGroupDn, invalidMailingListDn)` with `TxManagerConfig` active. Expected result: `createUserEntry` and `addToGroup` both succeed initially, but `addToMailingList` fails; because all three inner methods use Spring's default `REQUIRED` propagation, they all join the single outer transaction started by `onboardNewHire`, so the failure triggers compensation for *all* of it — checking the directory afterward shows neither the user entry nor the group membership persisted, not just the mailing list step that directly failed.

## 6. Walkthrough

Tracing `onboardNewHire` failing at the mailing-list step, in execution order:

1. `onboardNewHire`, annotated `@Transactional`, starts the outer transaction via `ContextSourceTransactionManager` — no operations have happened yet, but the transaction context now exists.
2. `createUserEntry(uid)` is called; its own `@Transactional` annotation, under Spring's default `REQUIRED` propagation, detects an already-active transaction and joins it rather than starting a separate one. Its `bind` operation is recorded under the *same* transaction as the outer call.
3. `addToGroup(uid, groupDn)` likewise joins the same transaction; its `modifyAttributes` (an `ADD_ATTRIBUTE` for group membership) is recorded alongside the first operation.
4. `addToMailingList(uid, mailingListDn)` also joins the same transaction, but its `modifyAttributes` call fails because `mailingListDn` doesn't resolve to a real entry.
5. The exception propagates up through `addToMailingList`, then `onboardNewHire`; because it's an unhandled runtime exception reaching the boundary of the outermost `@Transactional` method, Spring's transaction infrastructure marks the whole transaction for rollback.
6. `ContextSourceTransactionManager` replays the recorded compensating actions for *every* operation performed anywhere within the transaction — not just the one that directly failed — in reverse order: first undoing the group membership addition, then undoing the user entry creation.
7. The original exception then propagates to whatever called `onboardNewHire`, and the directory reflects none of the three intended changes.

```
onboardNewHire()                         [outer @Transactional, starts tx]
  createUserEntry()   @Transactional -> joins outer tx -> bind() recorded
  addToGroup()        @Transactional -> joins outer tx -> modifyAttributes() recorded
  addToMailingList()  @Transactional -> joins outer tx -> modifyAttributes() THROWS
-> rollback entire tx -> compensate group-add, then compensate bind (reverse order)
-> exception propagates; directory shows none of the three changes
```

## 7. Gotchas & takeaways

> `@Transactional` on a method is inert — it does absolutely nothing observable — unless a `PlatformTransactionManager` bean is actually configured and `@EnableTransactionManagement` is active for that context. This is easy to miss in a codebase that already uses `@Transactional` extensively for JPA, where it's easy to assume the annotation "just works" the same way for LDAP calls without realizing a *separate*, LDAP-specific manager (`ContextSourceTransactionManager`) needs to be registered too.

- Always verify `ContextSourceTransactionManager` is actually configured (and `@EnableTransactionManagement` active) before relying on `@Transactional` for LDAP compensating rollback — an application with both JPA and LDAP transactions needs both managers configured, and Spring resolves which one applies based on context, qualifiers, or explicit configuration.
- Nested `@Transactional` calls under default `REQUIRED` propagation join the outer transaction, meaning a failure anywhere in the whole call chain compensates every recorded operation across the entire chain, not just the method that directly failed.
- A single-operation method wrapped in `@Transactional` gains no real benefit — the directory server already treats one write as atomic on its own; the manager's value is specifically in coordinating *multiple* operations.
- Because this is a compensating-transaction approximation (card 0017), don't assume the same isolation guarantees as a database transaction manager — a concurrent reader can still observe intermediate states during the window before a failure triggers compensation.
- When debugging an LDAP operation that "should have rolled back but didn't," the first thing to check is whether a `ContextSourceTransactionManager` bean actually exists and is wired up for that execution context — a silently-missing manager is a common, easy-to-overlook root cause.
