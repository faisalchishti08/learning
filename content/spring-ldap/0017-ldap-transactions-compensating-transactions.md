---
card: spring-ldap
gi: 17
slug: ldap-transactions-compensating-transactions
title: "LDAP transactions (compensating transactions)"
---

## 1. What it is

LDAP itself has no native, general-purpose multi-operation transaction support the way a relational database does — there's no `BEGIN`/`COMMIT`/`ROLLBACK` spanning several independent operations against arbitrary entries. Spring LDAP's transaction support (`ContextSourceTransactionManager`, card 0018) works around this by recording each operation performed during a "transaction" and, if a later operation in the same block fails, replaying **compensating operations** that undo the effects of the ones that already succeeded — this pattern is called a compensating transaction, and it approximates atomicity without the directory server itself providing it.

## 2. Why & when

A workflow that needs to perform several related directory changes together — creating a user entry and adding that user to a group, for instance — has a real correctness problem if the first operation succeeds and the second fails: the directory is left in an inconsistent partial state (a user that exists but belongs to no group, or a dangling group reference to a user that was never actually created). True database-style transactions would solve this outright, but LDAP servers generally don't support that. Compensating transactions exist as the best available approximation: track what succeeded, and if something later fails, actively undo it rather than leaving it in place.

Use LDAP compensating transactions when:

- A single logical operation (like "add a new user and add them to their department's group") spans more than one directory write, and partial completion would leave the directory in a genuinely bad state.
- The individual operations involved have known, well-defined inverses (a `bind` can be undone by an `unbind`, an attribute add can be undone by a remove) that Spring LDAP's transaction support can generate automatically.

Recognize their limits: this is not a true ACID transaction. There's a window between an operation succeeding and a later compensating rollback where another concurrent reader could see the partial, not-yet-rolled-back state — true isolation isn't provided.

## 3. Core concept

Think of a compensating transaction like a stagehand who, during a live performance, tracks every prop moved and every set piece rearranged. If the show has to stop partway through (an actor misses their cue and the scene can't continue), the stagehand doesn't just abandon the stage in whatever half-changed state it's in — they actively move each prop back to where it was, one by one, undoing the changes in reverse, so the stage ends up looking like the show never started. That's fundamentally different from a real transaction, where the changes would never have been visible on stage at all until the whole scene completed — here, they were visible, and then actively reversed.

```java
@Configuration
@EnableTransactionManagement
public class LdapTransactionConfig {
    @Bean
    public ContextSourceTransactionManager transactionManager(ContextSource contextSource) {
        return new ContextSourceTransactionManager(contextSource);
    }
}

@Service
public class UserProvisioningService {
    @Transactional
    public void provisionUserWithGroup(String uid, String groupDn) {
        ldapTemplate.bind(userDn(uid), null, userAttributes(uid));
        ldapTemplate.modifyAttributes(groupDn, addMemberMod(userDn(uid)));
        // if this second call throws, the transaction manager issues an unbind() to undo the first
    }
}
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="If the second operation in a transactional block fails, a compensating operation undoes the first, rather than leaving a partial state">
  <rect x="20" y="30" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">bind(userDn)</text>

  <rect x="240" y="30" width="180" height="50" rx="6" fill="#1c2430" stroke="#ff7b72" stroke-width="1.5"/>
  <text x="330" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">modifyAttributes()</text>
  <text x="330" y="70" fill="#ff7b72" font-size="8" text-anchor="middle" font-family="sans-serif">throws!</text>

  <line x1="200" y1="55" x2="235" y2="55" stroke="#3fb950" stroke-width="2" marker-end="url(#m1)"/>

  <line x1="330" y1="80" x2="330" y2="120" stroke="#ff7b72" stroke-width="2" marker-end="url(#m2)"/>
  <text x="400" y="105" fill="#ff7b72" font-size="9" text-anchor="middle" font-family="sans-serif">triggers compensation</text>

  <rect x="20" y="130" width="180" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="160" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">unbind(userDn)</text>
  <text x="200" y="145" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif"></text>
  <line x1="240" y1="150" x2="205" y2="150" stroke="#79c0ff" stroke-width="2" marker-end="url(#m3)"/>

  <defs>
    <marker id="m1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="m2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#ff7b72"/></marker>
    <marker id="m3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

When the second operation fails, the transaction manager issues `unbind()` as the recorded compensating action for the earlier successful `bind()`.

## 5. Runnable example

The scenario: provisioning a new user and adding them to a group as one logical unit, starting with the naive unprotected version, then wrapping it transactionally, and finally handling a case where the compensating action itself can fail.

### Level 1 — Basic

```java
// UnprotectedProvisioning.java
import org.springframework.ldap.core.LdapTemplate;
import javax.naming.directory.*;

public class UnprotectedProvisioning {
    private final LdapTemplate template;

    public UnprotectedProvisioning(LdapTemplate template) {
        this.template = template;
    }

    public void provisionUserWithGroup(String uid, String groupDn) {
        Attributes attrs = new BasicAttributes();
        BasicAttribute oc = new BasicAttribute("objectClass");
        oc.add("top"); oc.add("inetOrgPerson");
        attrs.put(oc);
        attrs.put("sn", uid);
        attrs.put("cn", uid);

        template.bind("uid=" + uid + ",ou=people", null, attrs); // succeeds

        ModificationItem[] mods = {
            new ModificationItem(DirContext.ADD_ATTRIBUTE,
                new BasicAttribute("member", "uid=" + uid + ",ou=people,dc=example,dc=com"))
        };
        template.modifyAttributes(groupDn, mods); // if this throws, the user entry above is left dangling
    }
}
```

**How to run:** run against a directory where `groupDn` points to a nonexistent group, forcing the second call to fail. Expected result: the `bind` already succeeded and the user entry `uid=...,ou=people` now exists in the directory, but the method throws before the group modification completes — the directory is left with an orphaned user entry belonging to no group, a real inconsistency with no automatic cleanup.

### Level 2 — Intermediate

Wrapping the same method with `@Transactional` and Spring LDAP's `ContextSourceTransactionManager` makes the failure trigger an automatic compensating `unbind()`, removing the orphaned entry.

```java
// TransactionalProvisioning.java
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
class TransactionConfig {
    @Bean
    public ContextSourceTransactionManager transactionManager(ContextSource contextSource) {
        return new ContextSourceTransactionManager(contextSource);
    }
}

public class TransactionalProvisioning {
    private final LdapTemplate template;

    public TransactionalProvisioning(LdapTemplate template) {
        this.template = template;
    }

    @Transactional
    public void provisionUserWithGroup(String uid, String groupDn) {
        Attributes attrs = new BasicAttributes();
        BasicAttribute oc = new BasicAttribute("objectClass");
        oc.add("top"); oc.add("inetOrgPerson");
        attrs.put(oc);
        attrs.put("sn", uid);
        attrs.put("cn", uid);

        template.bind("uid=" + uid + ",ou=people", null, attrs);

        ModificationItem[] mods = {
            new ModificationItem(DirContext.ADD_ATTRIBUTE,
                new BasicAttribute("member", "uid=" + uid + ",ou=people,dc=example,dc=com"))
        };
        template.modifyAttributes(groupDn, mods); // if this throws, @Transactional triggers unbind() automatically
    }
}
```

**How to run:** run the same failing scenario as Level 1, but through this `@Transactional`-annotated version wired into a Spring context with `TransactionConfig` active. Expected result: after the exception propagates, checking the directory shows `uid=...,ou=people` no longer exists — the transaction manager recorded the successful `bind` and, on the later failure, automatically issued the compensating `unbind()`, leaving the directory as if the whole operation had never been attempted.

### Level 3 — Advanced

The compensating action itself can fail (the directory becomes unreachable in the brief window between the original operation and its compensation, for instance) — a real, if rare, possibility that leaves the directory in the exact inconsistent state compensation was meant to prevent. Production code needs to detect and loudly surface this "compensation failed" scenario rather than letting it pass silently as if everything rolled back cleanly.

```java
// MonitoredTransactionalProvisioning.java
import org.springframework.transaction.annotation.Transactional;
import org.springframework.ldap.core.LdapTemplate;
import javax.naming.directory.*;

public class MonitoredTransactionalProvisioning {
    private final LdapTemplate template;

    public MonitoredTransactionalProvisioning(LdapTemplate template) {
        this.template = template;
    }

    @Transactional
    public void provisionUserWithGroup(String uid, String groupDn) {
        String userDn = "uid=" + uid + ",ou=people";
        try {
            Attributes attrs = new BasicAttributes();
            BasicAttribute oc = new BasicAttribute("objectClass");
            oc.add("top"); oc.add("inetOrgPerson");
            attrs.put(oc);
            attrs.put("sn", uid);
            attrs.put("cn", uid);
            template.bind(userDn, null, attrs);

            ModificationItem[] mods = {
                new ModificationItem(DirContext.ADD_ATTRIBUTE,
                    new BasicAttribute("member", userDn + ",dc=example,dc=com"))
            };
            template.modifyAttributes(groupDn, mods);
        } catch (RuntimeException e) {
            // The transaction manager will attempt compensation, but if the directory is now unreachable,
            // compensation itself can fail — verify afterward rather than assuming rollback always succeeds.
            boolean stillExists = template.findByDn(
                org.springframework.ldap.support.LdapNameBuilder.newInstance(userDn).build(),
                Object.class) != null;
            if (stillExists) {
                // Compensation likely failed to actually remove the orphaned entry — escalate loudly.
                throw new IllegalStateException(
                    "Provisioning failed AND compensation may not have completed for " + userDn, e);
            }
            throw e; // normal failure path: compensation succeeded, rethrow the original cause
        }
    }
}
```

**How to run:** simulate the Level 2 failure scenario, then additionally make the directory briefly unreachable during the compensating `unbind()` window (hard to trigger deterministically, but reasoned about here as a design case). Expected behavior: if compensation succeeds normally, the original exception propagates as in Level 2. If compensation itself failed and the orphaned entry is still present, an `IllegalStateException` is thrown instead, explicitly naming the fact that both the original operation and its compensation may have failed — a much louder, more actionable signal than silently believing the rollback worked.

## 6. Walkthrough

Tracing `provisionUserWithGroup` under `@Transactional` when the group modification fails and compensation succeeds normally, in execution order:

1. Spring's transaction infrastructure, backed by `ContextSourceTransactionManager`, begins tracking operations as the `@Transactional` method starts executing.
2. `template.bind(userDn, ...)` succeeds; the transaction manager records this operation and, internally, the fact that its compensating action would be `unbind(userDn)` if a rollback becomes necessary.
3. `template.modifyAttributes(groupDn, mods)` is attempted against a group DN that doesn't actually exist, and the directory server rejects it, throwing an exception.
4. Because the method is `@Transactional` and an exception has propagated out of it, Spring's transaction infrastructure treats this as a rollback trigger.
5. `ContextSourceTransactionManager` replays its recorded compensating actions in reverse order of the original operations — here, just the one recorded `unbind(userDn)` — actually removing the user entry that had been successfully created in step 2.
6. The original exception (from the failed `modifyAttributes` call) then propagates to the caller, now that compensation has completed — from the caller's perspective, the method failed and the directory reflects no partial changes.

```
@Transactional provisionUserWithGroup(uid, groupDn)
  bind(userDn) succeeds       -> recorded: compensating action = unbind(userDn)
  modifyAttributes(groupDn)   -> throws (group doesn't exist)
  -> rollback triggered -> replay compensations: unbind(userDn)
  -> original exception propagates to caller; directory has no orphaned entry
```

## 7. Gotchas & takeaways

> Spring LDAP's transaction support is a compensating-transaction approximation, not a true ACID transaction — there is a real window during which the successful-but-not-yet-compensated operation is visible to any other reader of the directory, and if the compensating action itself fails, the directory can be left in the very inconsistent state the mechanism was meant to prevent. Treat it as "much better than nothing," not as an unconditional guarantee equivalent to a database transaction.

- Use `@Transactional` with `ContextSourceTransactionManager` whenever a logical operation spans more than one directory write that must not be left half-done.
- The mechanism works by recording each operation's inverse as it succeeds, then replaying those inverses in reverse order if a later operation in the same transactional method fails.
- There is no isolation guarantee — a concurrent reader can observe the intermediate, not-yet-compensated state during the brief window between an operation succeeding and a later failure triggering rollback.
- The compensating action itself can, in principle, fail — production code handling genuinely critical multi-step provisioning workflows should consider verifying the post-failure state (Level 3) rather than assuming rollback always completes cleanly.
- Keep transactional blocks spanning multiple LDAP writes as short and focused as practical — the more operations and the more time elapsed within one transactional method, the larger the window for both concurrent visibility issues and a failed compensation to matter.
