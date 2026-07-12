---
card: spring-security
gi: 112
slug: ldap-authorities-population
title: "LDAP authorities population"
---

## 1. What it is

Card 0111's `BindAuthenticator` establishes *who* a user is (their password checked out against the directory), but says nothing about *what they're allowed to do* — that's `LdapAuthoritiesPopulator`'s job, a separate interface invoked immediately after a successful bind to compute the `GrantedAuthority` set for the resulting `Authentication`. The default implementation, `DefaultLdapAuthoritiesPopulator`, searches the directory for **group entries** that list the user's DN as a member (a separate part of the directory tree from the user entries themselves, typically under an `ou=groups` branch), and maps each matching group's name into a `ROLE_`-prefixed authority.

```java
@Bean
public LdapAuthoritiesPopulator authoritiesPopulator(BaseLdapPathContextSource contextSource) {
    DefaultLdapAuthoritiesPopulator populator = new DefaultLdapAuthoritiesPopulator(contextSource, "ou=groups");
    populator.setGroupSearchFilter("(member={0})"); // {0} = the user's DN
    populator.setGroupRoleAttribute("cn");            // which attribute of the group entry becomes the role name
    populator.setRolePrefix("ROLE_");
    populator.setConvertToUpperCase(true);
    return populator;
}
```

## 2. Why & when

LDAP directories model group membership as a genuinely separate concept from user identity — a user entry (`uid=alice,ou=people,...`) doesn't itself list "what groups am I in"; instead, group entries (`cn=admins,ou=groups,...`) list "who are my members," each as a full DN reference. This inverted structure means computing "what authorities does alice have" requires a *search* — find every group entry whose `member` attribute contains alice's DN — rather than a simple attribute read on alice's own entry, and `LdapAuthoritiesPopulator` exists specifically to encapsulate that search so authentication code doesn't need to know LDAP's group-membership modeling details.

Reach for understanding (or customizing) `LdapAuthoritiesPopulator` when:

- Group membership is the organization's primary access-control mechanism — most enterprise LDAP/Active Directory deployments already model roles this way, and mapping it directly into Spring Security authorities avoids duplicating a separate role system in the application.
- The default `member={0})` search filter doesn't match your directory's schema — some LDAP schemas use `uniqueMember` instead of `member`, or store group membership on the *user* entry via a `memberOf` attribute rather than on the group entry, each requiring a different populator configuration or a custom implementation.
- Authorities need to combine multiple sources — group membership *and* an attribute on the user's own entry (a `title` or `employeeType` field, for instance) — which requires a custom `LdapAuthoritiesPopulator` that queries both and merges the results.
- Debugging why an authenticated LDAP user has no authorities at all (login succeeds, but every `@PreAuthorize` check fails) — this almost always traces to the group search filter or search base not matching how the directory is actually structured, not to a problem with the bind itself.

## 3. Core concept

```
LDAP directory structure (typical):
    dc=example,dc=com
        ou=people
            uid=alice,ou=people,dc=example,dc=com          <-- USER entries
            uid=bob,ou=people,dc=example,dc=com
        ou=groups
            cn=engineering,ou=groups,dc=example,dc=com      <-- GROUP entries
                member: uid=alice,ou=people,dc=example,dc=com
                member: uid=bob,ou=people,dc=example,dc=com
            cn=admins,ou=groups,dc=example,dc=com
                member: uid=alice,ou=people,dc=example,dc=com

DefaultLdapAuthoritiesPopulator.getGrantedAuthorities(userData, username):
  1. SEARCH under groupSearchBase (e.g. "ou=groups"), filter (member={0}), {0} = the user's DN
  2. for EACH matching group entry:
       read groupRoleAttribute (e.g. "cn") -> the group's name, e.g. "engineering"
       optionally uppercase it, then prefix with rolePrefix -> "ROLE_ENGINEERING"
  3. return the full set of GrantedAuthority objects

alice's DN appears in BOTH "engineering" and "admins" -> authorities = [ROLE_ENGINEERING, ROLE_ADMINS]
bob's DN appears ONLY in "engineering"                 -> authorities = [ROLE_ENGINEERING]
```

This search happens fresh on every login (not cached across logins), since group membership can change between one login and the next, and the populator has no way to know if it has, short of asking again.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a users DN being used to search group entries whose member attribute contains that DN each matching groups cn attribute becomes a ROLE prefixed authority producing the final authority set for that user">
  <rect x="20" y="30" width="150" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="95" y="50" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif">alice's DN</text>
  <text x="95" y="64" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(bind already succeeded)</text>

  <line x1="170" y1="53" x2="210" y2="53" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#la112)"/>

  <rect x="215" y="20" width="220" height="70" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="325" y="40" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">SEARCH ou=groups</text>
  <text x="325" y="56" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">filter: (member=alice's DN)</text>
  <text x="325" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; matches: engineering, admins</text>

  <line x1="325" y1="90" x2="325" y2="120" stroke="#8b949e" stroke-width="1.6" marker-end="url(#la112b)"/>

  <rect x="220" y="122" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="280" y="146" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">cn=engineering</text>

  <rect x="345" y="122" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="405" y="146" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">cn=admins</text>

  <line x1="280" y1="162" x2="280" y2="185" stroke="#6db33f" stroke-width="1.4" marker-end="url(#la112c)"/>
  <line x1="405" y1="162" x2="405" y2="185" stroke="#6db33f" stroke-width="1.4" marker-end="url(#la112c)"/>

  <rect x="180" y="188" width="320" height="40" rx="7" fill="#1c2430" stroke="#3fb950" stroke-width="1.4"/>
  <text x="340" y="212" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">[ROLE_ENGINEERING, ROLE_ADMINS]</text>

  <defs>
    <marker id="la112" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="la112b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="la112c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Group entries reference members, not the other way around — computing a user's authorities means searching for every group that names them.

## 5. Runnable example

The scenario: a from-scratch directory of user and group entries, a search-based authorities populator growing from a single group match into multiple simultaneous memberships, then into a custom populator merging group-derived authorities with an attribute read directly from the user's own entry.

### Level 1 — Basic

Search group entries for one matching membership.

```java
import java.util.*;

public class LdapAuthoritiesLevel1 {
    record GroupEntry(String cn, Set<String> members) {}

    static class LdapDirectory {
        private final List<GroupEntry> groups = new ArrayList<>();
        void addGroup(GroupEntry group) { groups.add(group); }

        // mirrors the (member={0}) search filter -- find every group entry naming this DN
        List<GroupEntry> findGroupsContaining(String userDn) {
            List<GroupEntry> matches = new ArrayList<>();
            for (GroupEntry g : groups) if (g.members().contains(userDn)) matches.add(g);
            return matches;
        }
    }

    static Set<String> computeAuthorities(LdapDirectory directory, String userDn) {
        Set<String> authorities = new LinkedHashSet<>();
        for (GroupEntry group : directory.findGroupsContaining(userDn)) {
            authorities.add("ROLE_" + group.cn().toUpperCase());
        }
        return authorities;
    }

    public static void main(String[] args) {
        LdapDirectory directory = new LdapDirectory();
        directory.addGroup(new GroupEntry("engineering", Set.of("uid=alice,ou=people,dc=example,dc=com")));

        Set<String> authorities = computeAuthorities(directory, "uid=alice,ou=people,dc=example,dc=com");
        System.out.println("alice's authorities: " + authorities);
    }
}
```

**How to run:** save as `LdapAuthoritiesLevel1.java`, run `java LdapAuthoritiesLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
alice's authorities: [ROLE_ENGINEERING]
```

`findGroupsContaining` mirrors the `(member={0})` search filter, and `computeAuthorities` maps each match's `cn` into a `ROLE_`-prefixed authority — exactly `DefaultLdapAuthoritiesPopulator`'s core job.

### Level 2 — Intermediate

A user in multiple groups simultaneously, and a user in none at all.

```java
import java.util.*;

public class LdapAuthoritiesLevel2 {
    record GroupEntry(String cn, Set<String> members) {}

    static class LdapDirectory {
        private final List<GroupEntry> groups = new ArrayList<>();
        void addGroup(GroupEntry group) { groups.add(group); }
        List<GroupEntry> findGroupsContaining(String userDn) {
            List<GroupEntry> matches = new ArrayList<>();
            for (GroupEntry g : groups) if (g.members().contains(userDn)) matches.add(g);
            return matches;
        }
    }

    static Set<String> computeAuthorities(LdapDirectory directory, String userDn) {
        Set<String> authorities = new LinkedHashSet<>();
        for (GroupEntry group : directory.findGroupsContaining(userDn)) {
            authorities.add("ROLE_" + group.cn().toUpperCase());
        }
        return authorities;
    }

    public static void main(String[] args) {
        LdapDirectory directory = new LdapDirectory();
        String aliceDn = "uid=alice,ou=people,dc=example,dc=com";
        String bobDn = "uid=bob,ou=people,dc=example,dc=com";

        directory.addGroup(new GroupEntry("engineering", Set.of(aliceDn, bobDn)));
        directory.addGroup(new GroupEntry("admins", Set.of(aliceDn))); // alice ONLY

        System.out.println("alice: " + computeAuthorities(directory, aliceDn));
        System.out.println("bob: " + computeAuthorities(directory, bobDn));

        String carolDn = "uid=carol,ou=people,dc=example,dc=com"; // authenticated, but in NO groups
        System.out.println("carol: " + computeAuthorities(directory, carolDn));
    }
}
```

**How to run:** save as `LdapAuthoritiesLevel2.java`, run `java LdapAuthoritiesLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
alice: [ROLE_ENGINEERING, ROLE_ADMINS]
bob: [ROLE_ENGINEERING]
carol: []
```

What changed: alice's DN appears in two group entries' `members` sets, yielding two authorities, while bob appears in only one and carol (who authenticated successfully via card 0111's bind) appears in none — an empty authority set is a completely valid, unremarkable outcome, distinct from a failed login; it simply means this successfully-authenticated user has no directory-derived permissions at all.

### Level 3 — Advanced

A custom populator merging group-derived authorities with an authority computed directly from an attribute on the user's own entry (a `title` field) — a common real-world extension beyond the default group-only behavior.

```java
import java.util.*;

public class LdapAuthoritiesLevel3 {
    record GroupEntry(String cn, Set<String> members) {}
    record UserEntry(String dn, Map<String, String> attributes) {}

    static class LdapDirectory {
        private final List<GroupEntry> groups = new ArrayList<>();
        private final Map<String, UserEntry> usersByDn = new HashMap<>();

        void addGroup(GroupEntry group) { groups.add(group); }
        void addUser(UserEntry user) { usersByDn.put(user.dn(), user); }

        List<GroupEntry> findGroupsContaining(String userDn) {
            List<GroupEntry> matches = new ArrayList<>();
            for (GroupEntry g : groups) if (g.members().contains(userDn)) matches.add(g);
            return matches;
        }

        UserEntry findUser(String dn) { return usersByDn.get(dn); }
    }

    // a CUSTOM LdapAuthoritiesPopulator -- merges group membership AND a user-entry attribute
    static Set<String> computeMergedAuthorities(LdapDirectory directory, String userDn) {
        Set<String> authorities = new LinkedHashSet<>();

        // source 1: group membership, exactly as the default populator does it
        for (GroupEntry group : directory.findGroupsContaining(userDn)) {
            authorities.add("ROLE_" + group.cn().toUpperCase());
        }

        // source 2: an attribute directly on the user's OWN entry -- the default populator never reads this
        UserEntry user = directory.findUser(userDn);
        if (user != null) {
            String title = user.attributes().get("title");
            if ("Senior Engineer".equals(title) || "Staff Engineer".equals(title)) {
                authorities.add("ROLE_SENIOR"); // derived from a job-title attribute, NOT from group membership
            }
        }

        return authorities;
    }

    public static void main(String[] args) {
        LdapDirectory directory = new LdapDirectory();
        String aliceDn = "uid=alice,ou=people,dc=example,dc=com";
        String bobDn = "uid=bob,ou=people,dc=example,dc=com";

        directory.addGroup(new GroupEntry("engineering", Set.of(aliceDn, bobDn)));
        directory.addUser(new UserEntry(aliceDn, Map.of("cn", "Alice Example", "title", "Staff Engineer")));
        directory.addUser(new UserEntry(bobDn, Map.of("cn", "Bob Example", "title", "Junior Engineer")));

        System.out.println("alice (Staff Engineer): " + computeMergedAuthorities(directory, aliceDn));
        System.out.println("bob (Junior Engineer): " + computeMergedAuthorities(directory, bobDn));
    }
}
```

**How to run:** save as `LdapAuthoritiesLevel3.java`, run `java LdapAuthoritiesLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
alice (Staff Engineer): [ROLE_ENGINEERING, ROLE_SENIOR]
bob (Junior Engineer): [ROLE_ENGINEERING]
```

What changed: `computeMergedAuthorities` reads from two genuinely different places in the directory — the group search (source 1, exactly as the default populator does it) and a direct attribute read on the user's own entry (source 2, something a real custom `LdapAuthoritiesPopulator` implementation would add) — alice's `"title"` attribute earns her an additional `ROLE_SENIOR` that has nothing to do with group membership at all, while bob's different title value does not.

## 6. Walkthrough

Trace alice's full authentication-then-authorization sequence from Level 3, picking up immediately after card 0111's bind succeeds.

**Step 1 — the bind succeeds** (card 0111): alice's password was verified by the directory itself. At this point, `SecurityContextHolder` has not yet been populated — the `Authentication` object still needs its authorities computed.

**Step 2 — the authorities populator is invoked**, corresponding to `computeMergedAuthorities(directory, aliceDn)` being called with alice's now-confirmed DN.

**Step 3 — the group search runs first.** `directory.findGroupsContaining(aliceDn)` iterates every `GroupEntry` and checks `members().contains(aliceDn)` — this corresponds to the real LDAP search operation:
```
LDAP Search Request
  Base: ou=groups,dc=example,dc=com
  Filter: (member=uid=alice,ou=people,dc=example,dc=com)
```
The `"engineering"` group matches (alice's DN is in its `members` set); its `cn`, uppercased and prefixed, becomes `"ROLE_ENGINEERING"`.

**Step 4 — the user-entry attribute is read separately.** `directory.findUser(aliceDn)` retrieves alice's own `UserEntry`; `attributes().get("title")` returns `"Staff Engineer"`, which matches the custom condition, adding `"ROLE_SENIOR"`.

**Step 5 — both sources are merged into one final set:** `{ROLE_ENGINEERING, ROLE_SENIOR}` — this becomes the `Collection<GrantedAuthority>` on alice's resulting `Authentication`, populated into `SecurityContextHolder`.

**Step 6 — an example downstream check.** A controller endpoint guarded with `@PreAuthorize("hasRole('SENIOR')")` now permits alice's request, purely because of her `title` attribute — bob, with the same group membership but a different title, would be denied the identical endpoint despite both being in `"engineering"`.

```
alice's DN
   -> group search: member of "engineering" -> ROLE_ENGINEERING
   -> user entry read: title="Staff Engineer" -> ROLE_SENIOR (group-INDEPENDENT source)
   -> merged: {ROLE_ENGINEERING, ROLE_SENIOR}

bob's DN
   -> group search: member of "engineering" -> ROLE_ENGINEERING
   -> user entry read: title="Junior Engineer" -> (no match, nothing added)
   -> merged: {ROLE_ENGINEERING}
```

## 7. Gotchas & takeaways

> **Gotcha:** `LdapAuthoritiesPopulator` runs its search fresh on every single login — it does not cache results across logins, since group membership can change between one login and the next and there's no reliable signal telling the populator to invalidate a cache. If a user is added to a new group at the directory level, that change takes effect the moment they next log in, with no application restart or cache eviction required — but conversely, a currently-active session's authorities are *not* automatically updated if group membership changes mid-session, since the populator only runs at authentication time, not on every subsequent request.

- `LdapAuthoritiesPopulator` is a distinct step from authentication (card 0111) — it runs only after a bind succeeds, and its entire job is computing the authenticated user's `GrantedAuthority` set.
- The default implementation searches for group entries whose membership attribute (commonly `member` or `uniqueMember`) references the user's DN — this is the inverse of how a relational "user has roles" table would typically be modeled, since LDAP groups reference their members rather than users referencing their groups.
- An authenticated user with zero matching groups is a normal, valid outcome (an empty authority set), not an error — it simply means this user has no directory-derived permissions.
- A custom populator can merge group-derived authorities with attributes read directly from the user's own entry, or from any other source entirely, since the interface only requires producing a final `Collection<GrantedAuthority>` by whatever means make sense for your directory's schema.
- Because the search runs fresh on every login, directory-side group changes take effect on next login automatically — but they do not retroactively affect an already-authenticated, still-active session.
