---
card: spring-security
gi: 43
slug: inmemoryuserdetailsmanager
title: "InMemoryUserDetailsManager"
---

## 1. What it is

`InMemoryUserDetailsManager` is Spring Security's built-in `UserDetailsService` implementation backed by a simple in-memory map, additionally implementing the broader `UserDetailsManager` interface (`createUser`, `updateUser`, `deleteUser`, `changePassword`, `userExists`) for basic CRUD against that map — constructed directly from one or more `UserDetails` objects, typically built via the `User.withUsername(...)` builder.

```java
@Bean
public UserDetailsService userDetailsService(PasswordEncoder encoder) {
    UserDetails admin = User.withUsername("admin")
            .password(encoder.encode("adminpass"))
            .roles("ADMIN")
            .build();
    UserDetails user = User.withUsername("user")
            .password(encoder.encode("userpass"))
            .roles("USER")
            .build();
    return new InMemoryUserDetailsManager(admin, user);
}
```

## 2. Why & when

Every real production application eventually needs users backed by durable storage (a database), but during early development, in tests, or for a genuinely fixed, small set of service accounts, standing up and maintaining a database purely for a handful of users is disproportionate overhead. `InMemoryUserDetailsManager` provides a complete, real `UserDetailsService` (with actual password hashing, actual authority checks, everything else in the security chain working identically) without any external storage at all — the trade-off being that its data vanishes on every application restart and cannot be shared across multiple application instances.

Reach for `InMemoryUserDetailsManager` when:

- Prototyping or writing integration tests where a small, fixed set of test users is all that's needed, and a real database would be unnecessary setup overhead.
- Configuring a small, genuinely static set of service-to-service credentials that never need to change at runtime and are acceptable to redeploy the application to modify.
- Never reach for it as the user store for a real production application with actual end users — `JdbcUserDetailsManager` (the next card) or a custom `UserDetailsService` backed by a proper database is the correct choice once users need to persist across restarts, register themselves, or scale across multiple instances.

## 3. Core concept

```
 InMemoryUserDetailsManager holds: Map<String, UserDetails>  (username -> UserDetails), entirely in-process memory

 loadUserByUsername(username):
   look up the map directly -- no I/O, no network call, no persistence involved at all

 createUser(UserDetails) / updateUser(UserDetails) / deleteUser(username) / changePassword(old, new):
   mutate the SAME in-memory map directly

 CONSEQUENCE: every one of these changes is LOST the moment the application process restarts --
   there is no durable backing store underneath this map at all
```

Everything about authentication and authorization above this layer works identically to a database-backed setup — only the storage itself is ephemeral.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="InMemoryUserDetailsManager wraps a plain in process map of username to UserDetails loadUserByUsername and CRUD operations all operate directly on this map with no external persistence so all data is lost on application restart">
  <rect x="15" y="55" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="105" y="75" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">InMemoryUserDetailsManager</text>
  <text x="105" y="88" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">loadUserByUsername / CRUD</text>

  <rect x="260" y="55" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="350" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Map&lt;String, UserDetails&gt;</text>
  <text x="350" y="88" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">in-process memory ONLY</text>

  <rect x="500" y="55" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="565" y="75" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">app restart</text>
  <text x="565" y="88" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">-&gt; all data GONE</text>

  <defs><marker id="a43" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="195" y1="80" x2="260" y2="80" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a43)"/>
  <line x1="440" y1="80" x2="500" y2="80" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a43)"/>
</svg>

A complete, working `UserDetailsService` — with zero durability underneath it.

## 5. Runnable example

The scenario: build a minimal `InMemoryUserDetailsManager`-style implementation, exercise its CRUD operations, then demonstrate the core limitation directly — simulating an application restart wiping every change, and contrasting that with a durable alternative.

### Level 1 — Basic

A minimal in-memory manager supporting load and create, backed by a plain `HashMap`.

```java
import java.util.*;

public class InMemoryManagerLevel1 {
    record UserDetails(String username, String password, Set<String> authorities) {}

    static class InMemoryUserDetailsManager {
        private final Map<String, UserDetails> users = new HashMap<>();

        InMemoryUserDetailsManager(UserDetails... initialUsers) {
            for (UserDetails u : initialUsers) users.put(u.username(), u);
        }

        UserDetails loadUserByUsername(String username) {
            UserDetails found = users.get(username);
            if (found == null) throw new NoSuchElementException("no such user: " + username);
            return found;
        }

        void createUser(UserDetails user) { users.put(user.username(), user); }
        boolean userExists(String username) { return users.containsKey(username); }
    }

    public static void main(String[] args) {
        InMemoryUserDetailsManager manager = new InMemoryUserDetailsManager(
                new UserDetails("admin", "hashed-adminpass", Set.of("ROLE_ADMIN"))
        );

        System.out.println("admin exists? " + manager.userExists("admin"));
        System.out.println("loaded: " + manager.loadUserByUsername("admin"));

        manager.createUser(new UserDetails("bob", "hashed-bobpass", Set.of("ROLE_USER")));
        System.out.println("bob exists after createUser? " + manager.userExists("bob"));
    }
}
```

How to run: `java InMemoryManagerLevel1.java`

The constructor pre-populates `users` from any initial `UserDetails` array; `createUser` simply adds another entry to the same map at runtime — `bob`, added after construction, is immediately queryable via `loadUserByUsername` exactly like the initially-configured `admin`.

### Level 2 — Intermediate

Add `updateUser`, `deleteUser`, and `changePassword`, exercising the full CRUD surface `UserDetailsManager` defines.

```java
import java.util.*;

public class InMemoryManagerLevel2 {
    record UserDetails(String username, String password, Set<String> authorities) {}

    static class InMemoryUserDetailsManager {
        private final Map<String, UserDetails> users = new HashMap<>();

        InMemoryUserDetailsManager(UserDetails... initialUsers) {
            for (UserDetails u : initialUsers) users.put(u.username(), u);
        }

        UserDetails loadUserByUsername(String username) {
            UserDetails found = users.get(username);
            if (found == null) throw new NoSuchElementException("no such user: " + username);
            return found;
        }

        void createUser(UserDetails user) { users.put(user.username(), user); }
        void updateUser(UserDetails user) { users.put(user.username(), user); } // SAME mechanics as createUser
        void deleteUser(String username) { users.remove(username); }
        void changePassword(String username, String newHashedPassword) {
            UserDetails existing = loadUserByUsername(username);
            users.put(username, new UserDetails(existing.username(), newHashedPassword, existing.authorities()));
        }
        boolean userExists(String username) { return users.containsKey(username); }
    }

    public static void main(String[] args) {
        InMemoryUserDetailsManager manager = new InMemoryUserDetailsManager(
                new UserDetails("alice", "hashed-oldpass", Set.of("ROLE_USER"))
        );

        System.out.println("before changePassword: " + manager.loadUserByUsername("alice"));
        manager.changePassword("alice", "hashed-newpass");
        System.out.println("after changePassword: " + manager.loadUserByUsername("alice"));

        manager.updateUser(new UserDetails("alice", "hashed-newpass", Set.of("ROLE_USER", "ROLE_ADMIN")));
        System.out.println("after updateUser (added ROLE_ADMIN): " + manager.loadUserByUsername("alice"));

        manager.deleteUser("alice");
        System.out.println("alice exists after deleteUser? " + manager.userExists("alice"));
    }
}
```

How to run: `java InMemoryManagerLevel2.java`

`changePassword` preserves alice's existing `authorities` while only replacing her password; `updateUser` replaces the entire entry (here adding `ROLE_ADMIN`); `deleteUser` removes her entirely — all four operations mutate the identical in-memory `users` map directly, with no separate persistence step involved anywhere.

### Level 3 — Advanced

Demonstrate the core limitation explicitly: simulate an application restart (a fresh manager instance, discarding the old one) and show every runtime change vanishing, then contrast with a manager backed by a durable file, illustrating what persistence would actually require.

```java
import java.util.*;
import java.io.*;
import java.nio.file.*;

public class InMemoryManagerLevel3 {
    record UserDetails(String username, String password, Set<String> authorities) {}

    static class InMemoryUserDetailsManager {
        private final Map<String, UserDetails> users = new HashMap<>();
        InMemoryUserDetailsManager(UserDetails... initial) { for (UserDetails u : initial) users.put(u.username(), u); }
        void createUser(UserDetails u) { users.put(u.username(), u); }
        boolean userExists(String username) { return users.containsKey(username); }
        int userCount() { return users.size(); }
    }

    // a DURABLE alternative: persists to a file, surviving what an in-memory map cannot
    static class FileBackedUserDetailsManager {
        private final Path storageFile;
        FileBackedUserDetailsManager(Path storageFile) { this.storageFile = storageFile; }

        void createUser(String username) throws IOException {
            Files.writeString(storageFile, username + System.lineSeparator(),
                    StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        }

        boolean userExists(String username) throws IOException {
            if (!Files.exists(storageFile)) return false;
            return Files.readAllLines(storageFile).contains(username);
        }
    }

    public static void main(String[] args) throws IOException {
        System.out.println("-- Application run #1 --");
        InMemoryUserDetailsManager run1 = new InMemoryUserDetailsManager(
                new UserDetails("admin", "hashed-adminpass", Set.of("ROLE_ADMIN"))
        );
        run1.createUser(new UserDetails("bob", "hashed-bobpass", Set.of("ROLE_USER")));
        System.out.println("user count during run #1: " + run1.userCount());

        System.out.println();
        System.out.println("-- Application RESTARTS (a NEW manager instance is constructed) --");
        InMemoryUserDetailsManager run2 = new InMemoryUserDetailsManager(
                new UserDetails("admin", "hashed-adminpass", Set.of("ROLE_ADMIN")) // only the HARD-CODED initial user
        );
        System.out.println("user count after restart: " + run2.userCount() + " (bob is GONE -- never persisted anywhere)");

        System.out.println();
        System.out.println("-- contrast: a file-backed manager SURVIVES a restart --");
        Path tempFile = Files.createTempFile("users", ".txt");
        FileBackedUserDetailsManager fileManager1 = new FileBackedUserDetailsManager(tempFile);
        fileManager1.createUser("carol");
        System.out.println("carol exists (before restart): " + fileManager1.userExists("carol"));

        FileBackedUserDetailsManager fileManager2 = new FileBackedUserDetailsManager(tempFile); // simulates a restart
        System.out.println("carol exists (AFTER restart, same file): " + fileManager2.userExists("carol"));
        Files.deleteIfExists(tempFile);
    }
}
```

How to run: `java InMemoryManagerLevel3.java`

`run1` ends with two users (`admin` and `bob`), but `run2` — modeling a fresh application process — is constructed from scratch with only the hard-coded initial user, so `bob` (added at runtime during `run1`) is simply gone; `FileBackedUserDetailsManager`, by contrast, writes to an actual file on disk, so a second instance pointed at the *same* file correctly finds `carol` even after being freshly constructed, demonstrating concretely what real persistence requires that a pure in-memory map cannot provide.

## 6. Walkthrough

Trace the sequence from `run1.createUser(...)` through to `run2.userCount()`.

1. `run1.createUser(new UserDetails("bob", ...))` runs during "Application run #1," calling `users.put("bob", ...)` on `run1`'s own private `users` map — this map exists only as long as the `run1` object itself is reachable in memory.
2. `run1.userCount()` returns `2`, correctly reflecting both `admin` (from the constructor) and `bob` (added afterward) — everything works exactly as expected *within this one running instance*.
3. The comment `"Application RESTARTS"` models the entire JVM process ending and a new one starting — in a real deployment, this is exactly what happens on a server reboot, a redeploy, or a crash-and-restart; critically, `run1`'s `users` map, along with everything it held, ceases to exist entirely at this point, with nothing written anywhere durable.
4. `run2 = new InMemoryUserDetailsManager(new UserDetails("admin", ...))` constructs a *completely new* manager, with its own, separate, freshly-initialized `users` map — it has no knowledge of `run1`'s existence, let alone the `bob` entry created during it.
5. `run2.userCount()` returns `1` — only the hard-coded `admin` user that this constructor call explicitly supplied is present; `bob` is unrecoverable, since nothing about his creation was ever written to any durable medium (a file, a database) that could survive the process boundary between `run1` and `run2`.

```
run1: users = {admin, bob}   (bob created at runtime via createUser)
--- process restart: run1's entire in-memory map is DISCARDED ---
run2: users = {admin}        (only the constructor's hard-coded initial user survives)
```

## 7. Gotchas & takeaways

> **Gotcha:** using `InMemoryUserDetailsManager` in production under the assumption that `createUser`/`changePassword` calls will "just work like a normal user store" is a common mistake for anyone unfamiliar with its ephemeral nature — any user created, updated, or password-changed at runtime is silently lost on the next restart, redeploy, or crash, with no error or warning at the time of loss.

- `InMemoryUserDetailsManager` is a complete, working `UserDetailsService` implementation with zero external storage dependency — ideal for prototyping, testing, and small, genuinely static credential sets.
- All CRUD operations (`createUser`, `updateUser`, `deleteUser`, `changePassword`) mutate an in-process map directly, with no persistence step, meaning every runtime change is lost the moment the application process ends.
- For any real production user base — where users register themselves, change their own passwords, or need to persist across restarts and scale across multiple application instances — a durable, database-backed implementation (`JdbcUserDetailsManager`, or a custom `UserDetailsService`) is required instead.
- The interface contract (`UserDetailsService`, `UserDetailsManager`) is identical regardless of backing storage, which is exactly what makes swapping from `InMemoryUserDetailsManager` to a database-backed implementation later a low-friction migration, requiring no changes to the rest of the security configuration.
