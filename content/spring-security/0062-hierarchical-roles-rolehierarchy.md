---
card: spring-security
gi: 62
slug: hierarchical-roles-rolehierarchy
title: "Hierarchical roles (RoleHierarchy)"
---

## 1. What it is

`RoleHierarchy` lets an application declare that one role implies another — `ROLE_ADMIN > ROLE_MANAGER`, `ROLE_MANAGER > ROLE_USER` — so that a user granted only `ROLE_ADMIN` is automatically treated as also holding `ROLE_MANAGER` and `ROLE_USER` for the purposes of every authorization check, without that user's `UserDetails` ever needing to list all three roles explicitly. `RoleHierarchyImpl` is the built-in implementation, configured with a simple text-based hierarchy definition.

```java
@Bean
public RoleHierarchy roleHierarchy() {
    return RoleHierarchyImpl.fromHierarchy("""
            ROLE_ADMIN > ROLE_MANAGER
            ROLE_MANAGER > ROLE_USER
            """);
}
```

## 2. Why & when

Without a role hierarchy, every user needs *every* role they should be able to act as explicitly listed on their account — an admin would need `ROLE_ADMIN`, `ROLE_MANAGER`, *and* `ROLE_USER` all granted directly, and every place in the application checking `hasRole("USER")` would otherwise incorrectly deny an admin who was only ever assigned `ROLE_ADMIN` directly. `RoleHierarchy` expresses the natural real-world relationship "a higher role can do everything a lower role can" once, centrally, so user records only need their *highest* actual role, and every `hasRole`/`hasAuthority` check anywhere in the application automatically accounts for the implied lower roles without needing to enumerate them.

Reach for `RoleHierarchy` when:

- Roles in the application genuinely form a natural seniority ordering — admin implies manager implies regular user — and duplicating every implied role onto every admin and manager account would be needless repetition and a maintenance burden if the hierarchy ever changes.
- Avoiding "role explosion," where without a hierarchy, an admin needing access to every regular-user-level feature would require every new regular-user role to also be manually added to every admin and manager account going forward.
- Understanding why a user with only `ROLE_ADMIN` explicitly granted can still pass a `hasRole("USER")` check somewhere in the application — the hierarchy configuration is the mechanism making that work, expanding the effective authority set behind the scenes before any check runs.

## 3. Core concept

```
 hierarchy definition:
   ROLE_ADMIN > ROLE_MANAGER
   ROLE_MANAGER > ROLE_USER

 a user's ACTUALLY GRANTED authorities: {ROLE_ADMIN}

 RoleHierarchy.getReachableGrantedAuthorities({ROLE_ADMIN})
   -> EXPANDS to: {ROLE_ADMIN, ROLE_MANAGER, ROLE_USER}
        (ROLE_ADMIN implies ROLE_MANAGER, which ITSELF implies ROLE_USER -- the expansion is TRANSITIVE)

 EVERY hasRole/hasAuthority check anywhere in the application uses this EXPANDED set,
   NOT the user's raw, originally-granted authorities
```

The hierarchy expansion happens once, transparently, before any access check runs — no individual check needs to know the hierarchy exists.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A user granted only ROLE_ADMIN has that single authority expanded via the configured role hierarchy into ROLE_ADMIN ROLE_MANAGER and ROLE_USER transitively every access check anywhere in the application then uses this expanded set automatically">
  <rect x="15" y="65" width="130" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="80" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">granted:</text>
  <text x="80" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">{ROLE_ADMIN}</text>

  <rect x="200" y="65" width="200" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="300" y="85" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">RoleHierarchy expansion</text>
  <text x="300" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">ADMIN &gt; MANAGER &gt; USER</text>

  <rect x="455" y="65" width="170" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="85" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">effective:</text>
  <text x="540" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">{ADMIN, MANAGER, USER}</text>

  <defs><marker id="a62" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="145" y1="88" x2="200" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a62)"/>
  <line x1="400" y1="88" x2="455" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a62)"/>
</svg>

One explicitly granted authority, expanding transitively into three effective ones — before any check runs.

## 5. Runnable example

The scenario: implement a transitive role-hierarchy expansion, apply it to authorization checks proving an admin passes a `hasRole("USER")` check, then extend the hierarchy with a third level and confirm the transitive expansion continues to work correctly across it.

### Level 1 — Basic

A minimal role hierarchy with one implication, and an expansion function.

```java
import java.util.*;

public class RoleHierarchyLevel1 {
    // hierarchy: ROLE_ADMIN implies ROLE_MANAGER
    static Map<String, String> hierarchy = Map.of("ROLE_ADMIN", "ROLE_MANAGER");

    static Set<String> expandAuthorities(Set<String> grantedAuthorities) {
        Set<String> expanded = new HashSet<>(grantedAuthorities);
        for (String authority : grantedAuthorities) {
            String implied = hierarchy.get(authority);
            if (implied != null) expanded.add(implied);
        }
        return expanded;
    }

    public static void main(String[] args) {
        Set<String> granted = Set.of("ROLE_ADMIN");
        Set<String> effective = expandAuthorities(granted);

        System.out.println("granted: " + granted);
        System.out.println("effective (expanded): " + effective);
        System.out.println("has ROLE_MANAGER (implied, not directly granted)? " + effective.contains("ROLE_MANAGER"));
    }
}
```

How to run: `java RoleHierarchyLevel1.java`

`expandAuthorities` adds `"ROLE_MANAGER"` to the effective set purely because the hierarchy map declares `ROLE_ADMIN` implies it — the user was never directly granted `ROLE_MANAGER`, yet it appears in their effective, expanded authority set.

### Level 2 — Intermediate

Extend to a three-level chain and confirm the expansion is genuinely transitive, not just one hop.

```java
import java.util.*;

public class RoleHierarchyLevel2 {
    static Map<String, String> hierarchy = Map.of(
            "ROLE_ADMIN", "ROLE_MANAGER",
            "ROLE_MANAGER", "ROLE_USER"
    );

    static Set<String> expandAuthorities(Set<String> grantedAuthorities) {
        Set<String> expanded = new HashSet<>(grantedAuthorities);
        Deque<String> toProcess = new ArrayDeque<>(grantedAuthorities);
        while (!toProcess.isEmpty()) {
            String current = toProcess.poll();
            String implied = hierarchy.get(current);
            if (implied != null && expanded.add(implied)) { // add() returns true only if it was NEWLY added
                toProcess.add(implied); // KEEP EXPANDING from this newly-discovered authority too
            }
        }
        return expanded;
    }

    public static void main(String[] args) {
        Set<String> adminGranted = Set.of("ROLE_ADMIN");
        Set<String> adminEffective = expandAuthorities(adminGranted);
        System.out.println("admin granted: " + adminGranted + " -> effective: " + adminEffective);

        Set<String> managerGranted = Set.of("ROLE_MANAGER");
        Set<String> managerEffective = expandAuthorities(managerGranted);
        System.out.println("manager granted: " + managerGranted + " -> effective: " + managerEffective);
    }
}
```

How to run: `java RoleHierarchyLevel2.java`

The admin's expansion reaches all the way down to `ROLE_USER`, two hops away from their directly-granted `ROLE_ADMIN` — the `while` loop keeps processing newly-discovered implied authorities until nothing new is found, correctly handling the transitive `ADMIN > MANAGER > USER` chain, while the manager's expansion (starting one level lower) correctly reaches only `ROLE_USER`, never `ROLE_ADMIN` (since the hierarchy only flows downward, never up).

### Level 3 — Advanced

Apply the expanded authority set to realistic `hasRole` checks across multiple users, confirming access decisions match the intended hierarchy semantics end to end.

```java
import java.util.*;

public class RoleHierarchyLevel3 {
    static Map<String, String> hierarchy = Map.of(
            "ROLE_ADMIN", "ROLE_MANAGER",
            "ROLE_MANAGER", "ROLE_USER"
    );

    static Set<String> expandAuthorities(Set<String> grantedAuthorities) {
        Set<String> expanded = new HashSet<>(grantedAuthorities);
        Deque<String> toProcess = new ArrayDeque<>(grantedAuthorities);
        while (!toProcess.isEmpty()) {
            String current = toProcess.poll();
            String implied = hierarchy.get(current);
            if (implied != null && expanded.add(implied)) toProcess.add(implied);
        }
        return expanded;
    }

    static boolean hasRole(Set<String> grantedAuthorities, String role) {
        return expandAuthorities(grantedAuthorities).contains("ROLE_" + role);
    }

    public static void main(String[] args) {
        Set<String> adminGranted = Set.of("ROLE_ADMIN");
        Set<String> managerGranted = Set.of("ROLE_MANAGER");
        Set<String> regularUserGranted = Set.of("ROLE_USER");

        record Check(String label, Set<String> authorities) {}
        List<Check> users = List.of(
                new Check("admin", adminGranted), new Check("manager", managerGranted), new Check("regular user", regularUserGranted)
        );

        for (Check check : users) {
            System.out.println(check.label() + ": hasRole(USER)=" + hasRole(check.authorities(), "USER")
                    + ", hasRole(MANAGER)=" + hasRole(check.authorities(), "MANAGER")
                    + ", hasRole(ADMIN)=" + hasRole(check.authorities(), "ADMIN"));
        }
    }
}
```

How to run: `java RoleHierarchyLevel3.java`

The admin passes all three checks (`USER`, `MANAGER`, and their own directly-granted `ADMIN`); the manager passes `USER` and `MANAGER` but correctly fails `ADMIN` (the hierarchy never flows upward); the regular user passes only `USER` — exactly the seniority-based access pattern a role hierarchy is meant to express, verified across every combination.

## 6. Walkthrough

Trace `hasRole(managerGranted, "ADMIN")` from Level 3, where `managerGranted = {"ROLE_MANAGER"}`.

1. `hasRole` calls `expandAuthorities({"ROLE_MANAGER"})`; inside, `expanded` starts as `{"ROLE_MANAGER"}` and `toProcess` starts as a queue containing `"ROLE_MANAGER"`.
2. The `while` loop polls `"ROLE_MANAGER"` from `toProcess`; `hierarchy.get("ROLE_MANAGER")` returns `"ROLE_USER"`; `expanded.add("ROLE_USER")` returns `true` (it's new), so `"ROLE_USER"` is also added to `toProcess` for further expansion.
3. The loop polls `"ROLE_USER"` next; `hierarchy.get("ROLE_USER")` returns `null` (nothing is declared to imply anything from `ROLE_USER` downward), so no further expansion happens from this branch, and `toProcess` becomes empty, ending the loop.
4. `expandAuthorities` returns `{"ROLE_MANAGER", "ROLE_USER"}` — critically, `"ROLE_ADMIN"` was never added, since the hierarchy only defines `ROLE_ADMIN implies ROLE_MANAGER`, never the reverse; starting from `ROLE_MANAGER`, there is no path in the hierarchy map that ever reaches `ROLE_ADMIN`.
5. Back in `hasRole`, `.contains("ROLE_ADMIN")` checks this expanded set `{"ROLE_MANAGER", "ROLE_USER"}` for `"ROLE_ADMIN"` — it is absent, so `hasRole(managerGranted, "ADMIN")` returns `false`, correctly reflecting that a manager should never be treated as having admin-level access, even though the hierarchy does let admins act as managers in the opposite direction.

```
expandAuthorities({ROLE_MANAGER}):
  start: expanded={ROLE_MANAGER}, toProcess=[ROLE_MANAGER]
  process ROLE_MANAGER -> implies ROLE_USER -> expanded={ROLE_MANAGER, ROLE_USER}, toProcess=[ROLE_USER]
  process ROLE_USER -> implies nothing -> toProcess=[] -> loop ends
  result: {ROLE_MANAGER, ROLE_USER}   (ROLE_ADMIN never reached -- hierarchy is one-directional)

hasRole(managerGranted, "ADMIN") -> {ROLE_MANAGER, ROLE_USER}.contains("ROLE_ADMIN") -> false
```

## 7. Gotchas & takeaways

> **Gotcha:** a role hierarchy is applied consistently only if it is registered wherever authorization decisions actually happen — both URL-based (`authorizeHttpRequests`) and method-based (`@PreAuthorize`) authorization need to be configured to use the *same* `RoleHierarchy` bean; registering it for one but not the other produces inconsistent behavior, where an admin's implied `ROLE_USER` might work correctly for URL access but unexpectedly fail a method-level `@PreAuthorize("hasRole('USER')")` check, or vice versa.

- `RoleHierarchy` expresses a natural seniority relationship between roles once, centrally, so higher roles automatically satisfy checks written for lower roles, without needing every implied role explicitly granted on every user account.
- Expansion is transitive — a hierarchy chain of `ADMIN > MANAGER > USER` correctly lets an admin satisfy a `hasRole("USER")` check two levels down, not just the immediately adjacent level.
- The hierarchy flows in one direction only — a role lower in the hierarchy never implies a role higher up, exactly as a manager never automatically gains admin-level access.
- The same `RoleHierarchy` bean must be wired into every place authorization decisions happen (URL-based and method-based alike) to ensure consistent behavior across the whole application.
