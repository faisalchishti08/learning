---
card: spring-data
gi: 188
slug: security-with-spring-data-rest
title: "Security with Spring Data REST"
---

## 1. What it is

Spring Data REST integrates with Spring Security through standard method-security annotations (`@PreAuthorize`, `@Secured`) applied either to custom repository fragment methods or via `RepositoryEventHandler`-based checks — enforcing access control on generated CRUD endpoints exactly as it would on a hand-written `@RestController`.

```java
interface CustomerRepository extends JpaRepository<Customer, String> {
    @PreAuthorize("hasRole('ADMIN')")
    void deleteById(String id); // overriding a CrudRepository method to add a security check
}
```

## 2. Why & when

Everything covered so far in this section made a repository more or less exposed as REST, and shaped what the exposed resource looks like. None of it, on its own, restricts *who* can call which operation — a generated `DELETE /customers/{id}` is reachable by anyone who can reach the API unless something explicitly restricts it. This card closes the loop: securing the generated endpoints the same way any other Spring MVC endpoint would be secured.

Reach for Spring Data REST security integration when:

- Different operations on the same resource need different access levels — anyone can `GET /customers`, but only an admin should be able to `DELETE` one.
- The access rule can be expressed as a standard Spring Security expression (`hasRole`, `hasAuthority`, a SpEL expression referencing the authenticated principal) rather than needing fully custom logic.
- You want the security check enforced consistently regardless of whether the request came through a generated endpoint or a custom `@RepositoryRestController`.

## 3. Core concept

```
 interface CustomerRepository extends JpaRepository<Customer, String> {
     @PreAuthorize("hasRole('ADMIN')")
     void deleteById(String id);          -- only ADMIN can delete
 }

 DELETE /customers/c1   (authenticated as ROLE_USER)
   -> @PreAuthorize check runs BEFORE the method body
   -> hasRole('ADMIN') evaluates to false
   -> 403 Forbidden -- deleteById's body never executes

 DELETE /customers/c1   (authenticated as ROLE_ADMIN)
   -> hasRole('ADMIN') evaluates to true
   -> deleteById proceeds normally -- 204 No Content
```

`@PreAuthorize` intercepts the method call before it runs, the same mechanism Spring Security uses everywhere else in the framework — Spring Data REST doesn't need special-case handling for it.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An incoming delete request is checked against a security expression before the repository method executes, branching to forbidden or success">
  <rect x="20" y="20" width="240" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">DELETE /customers/c1</text>

  <line x1="140" y1="60" x2="140" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a21)"/>

  <rect x="20" y="95" width="240" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="140" y="120" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@PreAuthorize hasRole('ADMIN')</text>

  <line x1="140" y1="135" x2="80" y2="150" stroke="#79c0ff" stroke-width="1.3"/>
  <line x1="140" y1="135" x2="480" y2="150" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a21)"/>

  <rect x="380" y="20" width="240" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">ADMIN -&gt; deleteById runs -&gt; 204</text>

  <rect x="380" y="95" width="240" height="40" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="120" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">USER -&gt; 403 Forbidden</text>

  <defs><marker id="a21" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The security check runs before the method body, deciding whether the operation proceeds or is rejected outright.

## 5. Runnable example

The scenario: securing customer deletion, evolving from an unrestricted operation reachable by any authenticated user, to a role-gated operation, to a fully expression-based rule allowing customers to modify their own data but not anyone else's — an ownership check, the realistic production shape of access control.

### Level 1 — Basic

Show the unrestricted baseline: any authenticated caller can delete any customer, regardless of role.

```java
import java.util.*;

public class RestSecurityLevel1 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepository();
        repo.save(new Customer("c1", "Amara"));

        User regularUser = new User("u1", Set.of("ROLE_USER"));
        repo.deleteById("c1", regularUser); // succeeds -- no restriction at all
        System.out.println("Deleted by regular user: customer removed=" + (repo.findById("c1") == null));
    }
}

class Customer { String id, name; Customer(String id, String name) { this.id = id; this.name = name; } }
class User { String id; Set<String> roles; User(String id, Set<String> roles) { this.id = id; this.roles = roles; } }

class CustomerRepository {
    private final Map<String, Customer> store = new HashMap<>();
    void save(Customer c) { store.put(c.id, c); }
    Customer findById(String id) { return store.get(id); }
    void deleteById(String id, User caller) { store.remove(id); } // NO security check at all
}
```

How to run: `java RestSecurityLevel1.java`

Any `User`, regardless of role, can call `deleteById` and succeed — exactly the gap a real, unsecured generated `DELETE /customers/{id}` endpoint would have.

### Level 2 — Intermediate

Add a `@PreAuthorize`-style role check that rejects the operation for anyone without the `ADMIN` role.

```java
import java.util.*;

public class RestSecurityLevel2 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepository();
        repo.save(new Customer("c1", "Amara"));
        repo.save(new Customer("c2", "Bilal"));

        User regularUser = new User("u1", Set.of("ROLE_USER"));
        User admin = new User("u2", Set.of("ROLE_ADMIN"));

        try {
            repo.deleteById("c1", regularUser);
        } catch (AccessDeniedException e) {
            System.out.println("Regular user rejected: " + e.getMessage());
        }

        repo.deleteById("c2", admin); // succeeds -- admin passes the check
        System.out.println("Admin delete succeeded: c2 removed=" + (repo.findById("c2") == null));
    }
}

class AccessDeniedException extends RuntimeException { AccessDeniedException(String message) { super(message); } }
class Customer { String id, name; Customer(String id, String name) { this.id = id; this.name = name; } }
class User { String id; Set<String> roles; User(String id, Set<String> roles) { this.id = id; this.roles = roles; } }

class CustomerRepository {
    private final Map<String, Customer> store = new HashMap<>();
    void save(Customer c) { store.put(c.id, c); }
    Customer findById(String id) { return store.get(id); }

    // @PreAuthorize("hasRole('ADMIN')")
    void deleteById(String id, User caller) {
        if (!caller.roles.contains("ROLE_ADMIN")) {
            throw new AccessDeniedException("requires ROLE_ADMIN"); // mirrors a 403 Forbidden
        }
        store.remove(id);
    }
}
```

How to run: `java RestSecurityLevel2.java`

`deleteById` now checks `caller.roles` before doing anything else — the regular user's call throws before `store.remove` ever executes, while the admin's call passes the check and proceeds, mirroring how `@PreAuthorize` intercepts the method call before its body runs.

### Level 3 — Advanced

Add an ownership-based rule using an expression referencing the authenticated principal: a customer can update their own record, or an admin can update any record — a SpEL-expression-shaped check, not just a flat role gate.

```java
import java.util.*;

public class RestSecurityLevel3 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepository();
        repo.save(new Customer("c1", "Amara", "amara@old.example"));
        repo.save(new Customer("c2", "Bilal", "bilal@old.example"));

        User amaraUser = new User("c1", Set.of("ROLE_USER")); // principal id matches c1
        User admin = new User("admin1", Set.of("ROLE_ADMIN"));

        // Amara updating her OWN record -- allowed, even without ADMIN role.
        repo.updateEmail("c1", "amara@new.example", amaraUser);
        System.out.println("Amara's own update: " + repo.findById("c1").email);

        try {
            // Amara trying to update SOMEONE ELSE's record -- rejected, she's not that customer and not an admin.
            repo.updateEmail("c2", "hacked@example.com", amaraUser);
        } catch (AccessDeniedException e) {
            System.out.println("Cross-account update rejected: " + e.getMessage());
        }

        // Admin updating ANY record -- allowed regardless of ownership.
        repo.updateEmail("c2", "bilal@new.example", admin);
        System.out.println("Admin update: " + repo.findById("c2").email);
    }
}

class AccessDeniedException extends RuntimeException { AccessDeniedException(String message) { super(message); } }
class Customer { String id, name, email; Customer(String id, String name, String email) { this.id = id; this.name = name; this.email = email; } }
class User { String id; Set<String> roles; User(String id, Set<String> roles) { this.id = id; this.roles = roles; } }

class CustomerRepository {
    private final Map<String, Customer> store = new HashMap<>();
    void save(Customer c) { store.put(c.id, c); }
    Customer findById(String id) { return store.get(id); }

    // @PreAuthorize("#id == authentication.principal.id or hasRole('ADMIN')")
    void updateEmail(String id, String newEmail, User caller) {
        boolean isOwner = caller.id.equals(id);
        boolean isAdmin = caller.roles.contains("ROLE_ADMIN");
        if (!isOwner && !isAdmin) {
            throw new AccessDeniedException("not the resource owner and not an admin");
        }
        store.get(id).email = newEmail;
    }
}
```

How to run: `java RestSecurityLevel3.java`

`updateEmail` checks two independent conditions — `isOwner` (does the caller's principal id match the record being modified?) and `isAdmin` (does the caller hold the admin role?) — allowing the operation if *either* holds, exactly the shape of a `@PreAuthorize("#id == authentication.principal.id or hasRole('ADMIN')")` SpEL expression.

## 6. Walkthrough

Execution starts in `main` for Level 3. `amaraUser` has `id = "c1"`, matching the customer record she's about to update — `repo.updateEmail("c1", ..., amaraUser)` checks `isOwner` (`"c1".equals("c1")` — true) and proceeds without needing the admin role at all:

```
Amara's own update: amara@new.example
```

The second call, `repo.updateEmail("c2", ..., amaraUser)`, checks the same two conditions against a *different* record: `isOwner` is now `"c1".equals("c2")` — false — and `isAdmin` is also false for `amaraUser`, so both conditions fail and the method throws before touching `store`:

```
Cross-account update rejected: not the resource owner and not an admin
```

The third call uses `admin`, whose `isOwner` check also fails (`"admin1".equals("c2")` is false) but whose `isAdmin` check passes — the `||` semantics of the guard mean the update proceeds anyway:

```
Admin update: bilal@new.example
```

In a real Spring Data REST application, this exact three-way branching would be expressed as a single `@PreAuthorize` SpEL expression evaluated by Spring Security's method interceptor before the repository method body ever runs — a failed check throws `AccessDeniedException`, which Spring Security's exception translation converts into an HTTP `403 Forbidden` response, with the underlying data completely untouched.

## 7. Gotchas & takeaways

> Gotcha: `@PreAuthorize` on a repository method only protects calls that go *through* Spring's proxy-based AOP — calling the same logic via a raw, non-Spring-managed reference (a plain `new CustomerRepositoryImpl()` somewhere, bypassing dependency injection) skips the security interceptor entirely, silently leaving the operation unprotected.

> Gotcha: securing the generated CRUD methods (`save`, `deleteById`) doesn't automatically secure *derived query methods* (`findByEmail`) the same way — each method that needs protection generally needs its own `@PreAuthorize` (or a class-level default), since Spring Security doesn't infer sensitivity from a method's name or purpose.

- `@PreAuthorize`/`@Secured` on repository methods integrate Spring Data REST's generated endpoints with standard Spring Security, enforced before the method body executes.
- The same security expressions used anywhere else in Spring Security — role checks, ownership checks referencing the authenticated principal, arbitrary SpEL — apply here without special-casing.
- Ownership-based rules (a user can modify their own data, an admin can modify anyone's) are expressed as a single boolean-combining SpEL expression, not separate hardcoded branches.
- Security only applies to methods actually annotated and only when invoked through Spring's managed proxies — every sensitive operation needs its own explicit check, and bypassing dependency injection bypasses the protection too.
