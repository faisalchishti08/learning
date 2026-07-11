---
card: spring-security
gi: 44
slug: jdbcuserdetailsmanager
title: "JdbcUserDetailsManager"
---

## 1. What it is

`JdbcUserDetailsManager` is Spring Security's built-in `UserDetailsManager` implementation backed by a relational database, using a predefined default schema (`users` and `authorities` tables) and default SQL queries, both fully overridable for applications with their own existing user table structure. Unlike `InMemoryUserDetailsManager`, every operation (`loadUserByUsername`, `createUser`, `updateUser`, `deleteUser`, `changePassword`) actually issues SQL against a real `DataSource`, so all data genuinely persists across application restarts.

```java
@Bean
public UserDetailsManager userDetailsManager(DataSource dataSource) {
    JdbcUserDetailsManager manager = new JdbcUserDetailsManager(dataSource);
    // override the default queries to match an EXISTING application schema, if needed:
    manager.setUsersByUsernameQuery(
        "SELECT username, password, enabled FROM app_users WHERE username = ?");
    manager.setAuthoritiesByUsernameQuery(
        "SELECT username, role AS authority FROM app_user_roles WHERE username = ?");
    return manager;
}
```

## 2. Why & when

A real application's users must survive restarts, redeployments, and scale across multiple application server instances sharing one database — exactly the durability `InMemoryUserDetailsManager` cannot provide. `JdbcUserDetailsManager` gives that durability while requiring minimal setup: its default schema and queries work immediately against a database matching its expected table structure, and every query is independently overridable for applications with a pre-existing, differently-shaped user table, without needing to write an entire custom `UserDetailsService` from scratch.

Reach for `JdbcUserDetailsManager` when:

- A relational database is already the application's chosen persistence technology, and its default (or a lightly customized) schema is an acceptable fit for the user table's shape.
- Migrating from `InMemoryUserDetailsManager` (prototyping) to real persistence — the `UserDetailsManager` interface stays identical, so the rest of the security configuration needs no changes at all, only the bean definition itself.
- The application already has an existing users table with a different structure — overriding the default SQL queries (`setUsersByUsernameQuery`, `setAuthoritiesByUsernameQuery`, and their create/update/delete counterparts) lets `JdbcUserDetailsManager` work against that existing shape directly, rather than requiring a schema migration to match its defaults.

## 3. Core concept

```
 DEFAULT schema JdbcUserDetailsManager expects:

   users table:        username | password | enabled
   authorities table:   username | authority

 loadUserByUsername(username):
   SELECT username, password, enabled FROM users WHERE username = ?
   SELECT username, authority FROM authorities WHERE username = ?
   -- combines BOTH result sets into ONE UserDetails object

 createUser(UserDetails) / updateUser(...) / deleteUser(...) / changePassword(...):
   each issues the CORRESPONDING INSERT/UPDATE/DELETE against the SAME two tables

 EVERY query is INDIVIDUALLY overridable via setXxxQuery(...) methods,
   letting JdbcUserDetailsManager adapt to an EXISTING, differently-shaped schema
```

Two queries combine into one `UserDetails` object — the user's core fields from one table, their authorities from another.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JdbcUserDetailsManager issues one query against a users table for username password and enabled and a second query against an authorities table for the same username combining both result sets into a single UserDetails object all changes persist durably in the underlying relational database">
  <rect x="15" y="20" width="180" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="38" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">users table</text>
  <text x="105" y="51" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">username, password, enabled</text>

  <rect x="15" y="105" width="180" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="123" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">authorities table</text>
  <text x="105" y="136" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">username, authority</text>

  <rect x="260" y="65" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="85" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">JdbcUserDetailsManager</text>
  <text x="350" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">joins both queries</text>

  <rect x="490" y="65" width="130" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="93" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">UserDetails</text>

  <defs><marker id="a44" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="195" y1="41" x2="260" y2="80" stroke="#8b949e" stroke-width="1" marker-end="url(#a44)"/>
  <line x1="195" y1="126" x2="260" y2="96" stroke="#8b949e" stroke-width="1" marker-end="url(#a44)"/>
  <line x1="440" y1="88" x2="490" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a44)"/>
</svg>

Two separate tables, one combined `UserDetails` result — durably backed the whole way through.

## 5. Runnable example

The scenario: model `JdbcUserDetailsManager`'s two-query-combine pattern against simulated database tables (plain in-memory structures standing in for real JDBC result sets, since a live database connection isn't available in a single runnable file), then add the full CRUD surface issuing corresponding statements, then demonstrate the override mechanism adapting to a differently-shaped, pre-existing schema.

### Level 1 — Basic

Two simulated tables and a `loadUserByUsername` that joins across both, mirroring the real default queries.

```java
import java.util.*;

public class JdbcManagerLevel1 {
    record UsersRow(String username, String password, boolean enabled) {}
    record AuthoritiesRow(String username, String authority) {}
    record UserDetails(String username, String password, boolean enabled, Set<String> authorities) {}

    // simulated database tables (standing in for real JDBC ResultSets against an actual DataSource)
    static List<UsersRow> usersTable = List.of(new UsersRow("alice", "hashed-hunter2", true));
    static List<AuthoritiesRow> authoritiesTable = List.of(
            new AuthoritiesRow("alice", "ROLE_USER"), new AuthoritiesRow("alice", "ROLE_ADMIN")
    );

    static UserDetails loadUserByUsername(String username) {
        UsersRow userRow = usersTable.stream().filter(r -> r.username().equals(username)).findFirst()
                .orElseThrow(() -> new NoSuchElementException("no such user: " + username));
        Set<String> authorities = authoritiesTable.stream()
                .filter(r -> r.username().equals(username))
                .map(AuthoritiesRow::authority)
                .collect(java.util.stream.Collectors.toSet());
        return new UserDetails(userRow.username(), userRow.password(), userRow.enabled(), authorities);
    }

    public static void main(String[] args) {
        System.out.println(loadUserByUsername("alice"));
    }
}
```

How to run: `java JdbcManagerLevel1.java`

`loadUserByUsername` performs two independent lookups (`usersTable` for the core record, `authoritiesTable` for the role set) and combines their results into one `UserDetails` object — exactly mirroring `JdbcUserDetailsManager`'s real default behavior of issuing two separate SQL queries and merging their results.

### Level 2 — Intermediate

Add the full CRUD surface, mutating the simulated tables directly — modeling the corresponding real SQL `INSERT`/`UPDATE`/`DELETE` statements.

```java
import java.util.*;
import java.util.stream.Collectors;

public class JdbcManagerLevel2 {
    record UsersRow(String username, String password, boolean enabled) {}
    record AuthoritiesRow(String username, String authority) {}
    record UserDetails(String username, String password, boolean enabled, Set<String> authorities) {}

    static List<UsersRow> usersTable = new ArrayList<>();
    static List<AuthoritiesRow> authoritiesTable = new ArrayList<>();

    static UserDetails loadUserByUsername(String username) {
        UsersRow userRow = usersTable.stream().filter(r -> r.username().equals(username)).findFirst()
                .orElseThrow(() -> new NoSuchElementException("no such user"));
        Set<String> authorities = authoritiesTable.stream().filter(r -> r.username().equals(username))
                .map(AuthoritiesRow::authority).collect(Collectors.toSet());
        return new UserDetails(userRow.username(), userRow.password(), userRow.enabled(), authorities);
    }

    // models: INSERT INTO users (username, password, enabled) VALUES (?, ?, ?)
    //          INSERT INTO authorities (username, authority) VALUES (?, ?)  (one row PER authority)
    static void createUser(UserDetails user) {
        usersTable.add(new UsersRow(user.username(), user.password(), user.enabled()));
        for (String authority : user.authorities()) authoritiesTable.add(new AuthoritiesRow(user.username(), authority));
    }

    // models: UPDATE users SET password = ? WHERE username = ?
    static void changePassword(String username, String newPassword) {
        int idx = usersTable.indexOf(usersTable.stream().filter(r -> r.username().equals(username)).findFirst().get());
        UsersRow old = usersTable.get(idx);
        usersTable.set(idx, new UsersRow(old.username(), newPassword, old.enabled()));
    }

    // models: DELETE FROM authorities WHERE username = ?; DELETE FROM users WHERE username = ?
    static void deleteUser(String username) {
        authoritiesTable.removeIf(r -> r.username().equals(username));
        usersTable.removeIf(r -> r.username().equals(username));
    }

    public static void main(String[] args) {
        createUser(new UserDetails("bob", "hashed-oldpass", true, Set.of("ROLE_USER")));
        System.out.println("after createUser: " + loadUserByUsername("bob"));

        changePassword("bob", "hashed-newpass");
        System.out.println("after changePassword: " + loadUserByUsername("bob"));

        deleteUser("bob");
        System.out.println("usersTable after deleteUser: " + usersTable);
        System.out.println("authoritiesTable after deleteUser: " + authoritiesTable);
    }
}
```

How to run: `java JdbcManagerLevel2.java`

`createUser` inserts one row per authority into `authoritiesTable`, exactly matching the real schema's one-row-per-authority design; `deleteUser` removes from `authoritiesTable` *before* `usersTable`, avoiding leaving orphaned authority rows behind — mirroring the correct real-world statement ordering to respect referential integrity between the two tables.

### Level 3 — Advanced

Override the query logic to adapt to a differently-shaped, pre-existing schema — modeling `setUsersByUsernameQuery`/`setAuthoritiesByUsernameQuery` customization for an application with its own legacy user table structure.

```java
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;

public class JdbcManagerLevel3 {
    record UserDetails(String username, String password, boolean enabled, Set<String> authorities) {}

    // a LEGACY, differently-shaped schema this application already has:
    //   app_accounts: account_name | pwd_hash | active
    //   account_roles: account_name | role_name
    record AppAccountsRow(String accountName, String pwdHash, boolean active) {}
    record AccountRolesRow(String accountName, String roleName) {}

    static List<AppAccountsRow> appAccounts = List.of(new AppAccountsRow("carol", "hashed-carolpass", true));
    static List<AccountRolesRow> accountRoles = List.of(new AccountRolesRow("carol", "ADMIN"));

    // a CONFIGURABLE manager: the actual "query" logic is INJECTED, exactly like setUsersByUsernameQuery does
    static class ConfigurableUserDetailsManager {
        Function<String, UserDetails> loadUserFunction;

        ConfigurableUserDetailsManager(Function<String, UserDetails> loadUserFunction) {
            this.loadUserFunction = loadUserFunction;
        }

        UserDetails loadUserByUsername(String username) { return loadUserFunction.apply(username); }
    }

    public static void main(String[] args) {
        // this LAMBDA plays the role of the overridden SQL queries, adapted to the LEGACY schema's column/table names
        Function<String, UserDetails> legacySchemaLoader = username -> {
            AppAccountsRow account = appAccounts.stream().filter(r -> r.accountName().equals(username)).findFirst()
                    .orElseThrow(() -> new NoSuchElementException("no such account: " + username));
            Set<String> roles = accountRoles.stream().filter(r -> r.accountName().equals(username))
                    .map(r -> "ROLE_" + r.roleName()) // legacy schema stores "ADMIN", Spring Security expects "ROLE_ADMIN"
                    .collect(Collectors.toSet());
            return new UserDetails(account.accountName(), account.pwdHash(), account.active(), roles);
        };

        ConfigurableUserDetailsManager manager = new ConfigurableUserDetailsManager(legacySchemaLoader);
        System.out.println(manager.loadUserByUsername("carol"));
    }
}
```

How to run: `java JdbcManagerLevel3.java`

`legacySchemaLoader` reads from tables and columns with entirely different names (`app_accounts`, `account_name`, `pwd_hash`) than `JdbcUserDetailsManager`'s built-in defaults, and even translates the stored role format (`"ADMIN"`) into Spring Security's expected `"ROLE_ADMIN"` convention — this is precisely the kind of adaptation `setUsersByUsernameQuery`/`setAuthoritiesByUsernameQuery` enable in the real class, letting it work against a pre-existing schema without requiring any migration of that schema itself.

## 6. Walkthrough

Trace `manager.loadUserByUsername("carol")` from Level 3.

1. `manager.loadUserByUsername("carol")` calls `loadUserFunction.apply("carol")`, which invokes `legacySchemaLoader` — the injected function standing in for the overridden SQL queries.
2. Inside `legacySchemaLoader`, `appAccounts.stream().filter(r -> r.accountName().equals("carol")).findFirst()` searches the legacy `appAccounts` list, finds `new AppAccountsRow("carol", "hashed-carolpass", true)`, and unwraps it via `.orElseThrow(...)` into `account`.
3. `accountRoles.stream().filter(r -> r.accountName().equals("carol"))` filters `accountRoles` down to just carol's entries — here, the single entry `AccountRolesRow("carol", "ADMIN")` — and `.map(r -> "ROLE_" + r.roleName())` transforms `"ADMIN"` into `"ROLE_ADMIN"`, collecting the result into a `Set<String>` containing exactly `{"ROLE_ADMIN"}`.
4. `new UserDetails(account.accountName(), account.pwdHash(), account.active(), roles)` constructs the final, standard-shaped `UserDetails` object: `username = "carol"`, `password = "hashed-carolpass"`, `enabled = true`, `authorities = {"ROLE_ADMIN"}` — this object looks *identical in shape* to what a default-schema `JdbcUserDetailsManager` would have produced, despite being sourced from an entirely differently-named, differently-structured underlying schema.
5. This is the key benefit the override mechanism provides: everything *above* `loadUserByUsername` in Spring Security's authentication and authorization machinery (the `DaoAuthenticationProvider`, the `@PreAuthorize` role checks) operates on the standard `UserDetails` shape and the `ROLE_`-prefixed authority convention, completely unaware of — and unaffected by — the legacy schema's actual table and column names underneath.

```
appAccounts:   [{accountName=carol, pwdHash=hashed-carolpass, active=true}]
accountRoles:  [{accountName=carol, roleName=ADMIN}]
                         |
                         v  legacySchemaLoader translates BOTH into standard shape
UserDetails(username=carol, password=hashed-carolpass, enabled=true, authorities={ROLE_ADMIN})
```

## 7. Gotchas & takeaways

> **Gotcha:** overriding only some of `JdbcUserDetailsManager`'s queries (say, `setUsersByUsernameQuery` but forgetting `setCreateUserSql` or `setChangePasswordSql`) leaves the un-overridden operations still targeting the *default* schema's table names — if the application's actual schema doesn't have those default tables, calling an un-overridden CRUD method fails at runtime with a SQL error, even though `loadUserByUsername` itself works perfectly. Every method actually used must have its corresponding query overridden consistently.

- `JdbcUserDetailsManager` provides durable, database-backed user storage with a working default schema and query set, requiring minimal setup for applications willing to adopt (or migrate to) that default shape.
- `loadUserByUsername` combines results from two separate queries (core user fields, and authorities) into one `UserDetails` object — understanding this two-query structure clarifies what each override method actually replaces.
- Every query is individually overridable, letting the class adapt to an existing, differently-shaped legacy schema without requiring that schema to be migrated to match the defaults.
- The `UserDetailsManager` interface itself is identical to `InMemoryUserDetailsManager`'s, meaning migrating from an in-memory prototype to real, durable persistence typically requires changing only the bean definition, not the surrounding security configuration.
