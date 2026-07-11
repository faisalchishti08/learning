---
card: spring-security
gi: 45
slug: userdetailspasswordservice-password-upgrade
title: "UserDetailsPasswordService (password upgrade)"
---

## 1. What it is

`UserDetailsPasswordService` is the single-method interface (`updatePassword(UserDetails, newPassword)`) that gives `DaoAuthenticationProvider` a way to actually *persist* an upgraded password hash back to storage — it's the missing piece connecting the earlier `upgradeEncoding` signal to a real, saved effect: `DaoAuthenticationProvider` checks `passwordEncoder.upgradeEncoding(storedHash)` after a successful login, and if a `UserDetailsPasswordService` bean is present, calls its `updatePassword` with the freshly re-hashed value, letting that implementation write it wherever the application's real user store lives.

```java
public interface UserDetailsPasswordService {
    UserDetails updatePassword(UserDetails user, String newPassword);
}

@Bean
public UserDetailsPasswordService userDetailsPasswordService(UserRepository repository) {
    return (user, newPassword) -> {
        repository.updatePasswordByUsername(user.getUsername(), newPassword); // an actual DB write
        return user; // DaoAuthenticationProvider expects the (possibly updated) UserDetails back
    };
}
```

## 2. Why & when

`upgradeEncoding` (from two cards back) only ever *answers a question* — "would re-hashing this password right now produce something different from what's stored" — it never writes anything anywhere; some separate piece has to actually perform and persist that write, and that piece necessarily depends on the application's specific storage technology (a JPA repository, a JDBC template, a call to an external identity service). `UserDetailsPasswordService` is exactly that seam: implement its one method against whatever storage backs the application's `UserDetailsService`, and `DaoAuthenticationProvider` will call it automatically at exactly the right moment, with no other wiring needed.

Reach for implementing `UserDetailsPasswordService` when:

- Any custom `UserDetailsService` is backed by real, durable storage (a database) and password-parameter or algorithm upgrades (from the earlier cards in this section) should actually take effect and persist, not just be silently detected and discarded.
- `JdbcUserDetailsManager` (the previous card) already implements this interface itself, using its own `changePassword`-style SQL under the hood — no additional wiring is needed when using it directly.
- Debugging why `upgradeEncoding` reports `true` on every login for a given user, yet the stored hash never actually changes — the most common cause is simply that no `UserDetailsPasswordService` bean is registered at all, so `DaoAuthenticationProvider` has nowhere to send the upgraded value.

## 3. Core concept

```
 DaoAuthenticationProvider.authenticate(unverified), on a SUCCESSFUL match:
   1. passwordEncoder.matches(rawPassword, storedHash)  -- TRUE
   2. IF passwordEncoder.upgradeEncoding(storedHash) is TRUE:
        IF a UserDetailsPasswordService bean IS registered:
            String newHash = passwordEncoder.encode(rawPassword)  -- using CURRENT settings
            userDetailsPasswordService.updatePassword(userDetails, newHash)  -- PERSISTED, via whatever storage this implements
        ELSE:
            -- upgradeEncoding's signal is simply DISCARDED -- nothing is ever upgraded, silently, forever
   3. proceed with the (already-verified) authentication result regardless
```

Without a registered `UserDetailsPasswordService`, `upgradeEncoding`'s signal has nowhere to go — it is computed every login and thrown away every time.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="After a successful password match DaoAuthenticationProvider checks upgradeEncoding if true and a UserDetailsPasswordService bean exists it re hashes the raw password with current settings and calls updatePassword to persist it if no such bean is registered the upgrade signal is silently discarded every single login">
  <rect x="15" y="65" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">password matches</text>
  <text x="90" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">upgradeEncoding=true</text>

  <rect x="220" y="20" width="200" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="320" y="38" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">bean registered:</text>
  <text x="320" y="51" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">updatePassword() persists it</text>

  <rect x="220" y="110" width="200" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="128" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">NO bean registered:</text>
  <text x="320" y="141" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">signal silently discarded</text>

  <defs><marker id="a45" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="83" x2="220" y2="41" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a45)"/>
  <line x1="165" y1="93" x2="220" y2="131" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a45)"/>
</svg>

The same "upgrade needed" signal produces a genuinely persisted improvement or nothing at all, depending purely on whether this bean exists.

## 5. Runnable example

The scenario: model `DaoAuthenticationProvider`'s upgrade dispatch with and without a registered `UserDetailsPasswordService`, then implement a real persisting version, then run it across repeated logins to show the upgrade happening exactly once and never redundantly re-triggering.

### Level 1 — Basic

The dispatch logic without any registered service — confirming the upgrade signal is computed but has nowhere to go.

```java
import java.util.*;

public class PasswordUpgradeServiceLevel1 {
    record StoredUser(String username, int costFactor, String passwordHash) {}
    static Map<String, StoredUser> userStore = new HashMap<>();
    static final int CURRENT_COST_FACTOR = 12;

    static boolean upgradeEncoding(StoredUser user) { return user.costFactor() < CURRENT_COST_FACTOR; }

    // NO UserDetailsPasswordService registered -- represented simply as "null"
    static void authenticateAndMaybeUpgrade(String username, String rawPassword, Object userDetailsPasswordService) {
        StoredUser user = userStore.get(username);
        System.out.println("login for " + username + ": password matched (assumed for this example)");

        if (upgradeEncoding(user)) {
            if (userDetailsPasswordService == null) {
                System.out.println("  upgrade needed, but NO UserDetailsPasswordService registered -- signal DISCARDED");
            } else {
                System.out.println("  upgrade needed and WOULD be persisted here");
            }
        } else {
            System.out.println("  no upgrade needed");
        }
    }

    public static void main(String[] args) {
        userStore.put("alice", new StoredUser("alice", 8, "hashed-hunter2-cost8"));
        authenticateAndMaybeUpgrade("alice", "hunter2", null); // NOTHING registered
        System.out.println("alice's stored cost factor STILL: " + userStore.get("alice").costFactor());
    }
}
```

How to run: `java PasswordUpgradeServiceLevel1.java`

`upgradeEncoding` correctly detects that alice's `costFactor` (8) is below `CURRENT_COST_FACTOR` (12), but because `userDetailsPasswordService` is `null`, the method can only print that the signal is discarded — the final check confirms `userStore.get("alice").costFactor()` remains `8`, completely unchanged.

### Level 2 — Intermediate

Implement a real, persisting `UserDetailsPasswordService` and confirm the upgrade actually takes effect this time.

```java
import java.util.*;

public class PasswordUpgradeServiceLevel2 {
    record StoredUser(String username, int costFactor, String passwordHash) {}
    static Map<String, StoredUser> userStore = new HashMap<>();
    static final int CURRENT_COST_FACTOR = 12;

    interface UserDetailsPasswordService { void updatePassword(String username, String newHash, int newCostFactor); }

    static UserDetailsPasswordService realPasswordService = (username, newHash, newCostFactor) -> {
        StoredUser existing = userStore.get(username);
        userStore.put(username, new StoredUser(existing.username(), newCostFactor, newHash)); // an ACTUAL persisted write
    };

    static boolean upgradeEncoding(StoredUser user) { return user.costFactor() < CURRENT_COST_FACTOR; }

    static void authenticateAndMaybeUpgrade(String username, String rawPassword, UserDetailsPasswordService service) {
        StoredUser user = userStore.get(username);
        if (upgradeEncoding(user)) {
            String newHash = "hashed-" + rawPassword + "-cost" + CURRENT_COST_FACTOR; // simulates re-encoding
            if (service != null) {
                service.updatePassword(username, newHash, CURRENT_COST_FACTOR);
                System.out.println(username + ": upgraded and PERSISTED to cost " + CURRENT_COST_FACTOR);
            }
        } else {
            System.out.println(username + ": already at current cost, no upgrade needed");
        }
    }

    public static void main(String[] args) {
        userStore.put("bob", new StoredUser("bob", 8, "hashed-letmein123-cost8"));

        authenticateAndMaybeUpgrade("bob", "letmein123", realPasswordService);
        System.out.println("bob's stored cost factor now: " + userStore.get("bob").costFactor());
    }
}
```

How to run: `java PasswordUpgradeServiceLevel2.java`

With a real `realPasswordService` supplied, `authenticateAndMaybeUpgrade` calls `service.updatePassword`, which actually mutates `userStore` in place — the final check confirms bob's stored `costFactor` has genuinely changed from `8` to `12`, unlike Level 1's discarded signal.

### Level 3 — Advanced

Run repeated logins across multiple users, confirming the upgrade happens exactly once per user (on their first login after the cost factor increase) and never redundantly re-triggers on subsequent logins.

```java
import java.util.*;

public class PasswordUpgradeServiceLevel3 {
    record StoredUser(String username, int costFactor, String passwordHash) {}
    static Map<String, StoredUser> userStore = new HashMap<>();
    static Map<String, Integer> upgradeCallCounts = new HashMap<>(); // tracks HOW MANY times each user was upgraded
    static final int CURRENT_COST_FACTOR = 12;

    interface UserDetailsPasswordService { void updatePassword(String username, String newHash, int newCostFactor); }

    static UserDetailsPasswordService realPasswordService = (username, newHash, newCostFactor) -> {
        StoredUser existing = userStore.get(username);
        userStore.put(username, new StoredUser(existing.username(), newCostFactor, newHash));
        upgradeCallCounts.merge(username, 1, Integer::sum);
    };

    static boolean upgradeEncoding(StoredUser user) { return user.costFactor() < CURRENT_COST_FACTOR; }

    static void login(String username, String rawPassword) {
        StoredUser user = userStore.get(username);
        if (upgradeEncoding(user)) {
            String newHash = "hashed-" + rawPassword + "-cost" + CURRENT_COST_FACTOR;
            realPasswordService.updatePassword(username, newHash, CURRENT_COST_FACTOR);
        }
    }

    public static void main(String[] args) {
        userStore.put("carol", new StoredUser("carol", 8, "hashed-p@ssw0rd-cost8"));

        for (int i = 1; i <= 3; i++) {
            login("carol", "p@ssw0rd");
            System.out.println("after login #" + i + ": costFactor=" + userStore.get("carol").costFactor()
                    + ", total upgrade calls so far=" + upgradeCallCounts.getOrDefault("carol", 0));
        }
    }
}
```

How to run: `java PasswordUpgradeServiceLevel3.java`

Login #1 finds `upgradeEncoding` returns `true` (carol's stored `costFactor` is `8`), triggering exactly one call to `realPasswordService.updatePassword`, which updates her stored `costFactor` to `12`; logins #2 and #3 then find `upgradeEncoding` returns `false` (her `costFactor` already matches the current setting), so no further upgrade call happens — `upgradeCallCounts` for carol stays at `1` across all three logins, confirming the upgrade is genuinely idempotent and never redundantly repeated.

## 6. Walkthrough

Trace all three `login("carol", "p@ssw0rd")` calls in Level 3's `main`.

1. Login #1: `user = userStore.get("carol")` retrieves `StoredUser("carol", 8, "hashed-p@ssw0rd-cost8")`; `upgradeEncoding(user)` checks `8 < 12`, which is `true`, so the method computes `newHash = "hashed-p@ssw0rd-cost12"` and calls `realPasswordService.updatePassword("carol", newHash, 12)`.
2. Inside `updatePassword`, `userStore.put("carol", new StoredUser("carol", 12, newHash))` replaces carol's entry entirely, and `upgradeCallCounts.merge("carol", 1, Integer::sum)` sets her count to `1` (since it didn't exist before, `merge` simply inserts `1`).
3. The `println` after login #1 reads `userStore.get("carol").costFactor()` as `12` (just updated) and `upgradeCallCounts.getOrDefault("carol", 0)` as `1`.
4. Login #2: `user = userStore.get("carol")` now retrieves the *updated* `StoredUser("carol", 12, ...)` from step 2; `upgradeEncoding(user)` checks `12 < 12`, which is `false` — the entire `if` block is skipped, and `updatePassword` is never called this time.
5. The `println` after login #2 confirms `costFactor` is still `12` (unchanged from login #1) and the upgrade call count is still `1` (not incremented again) — login #3 repeats the identical outcome as login #2, for the identical reason: carol's stored cost factor already matches the current configuration, so there's nothing left to upgrade.

```
login #1: costFactor=8  -> upgradeEncoding=true  -> UPDATE persisted -> costFactor=12, upgradeCalls=1
login #2: costFactor=12 -> upgradeEncoding=false -> no update        -> costFactor=12, upgradeCalls=1 (unchanged)
login #3: costFactor=12 -> upgradeEncoding=false -> no update        -> costFactor=12, upgradeCalls=1 (unchanged)
```

## 7. Gotchas & takeaways

> **Gotcha:** forgetting to register a `UserDetailsPasswordService` bean is a silent gap — there is no error, warning, or exception when `upgradeEncoding` returns `true` but no service is present to act on it; the application simply continues authenticating successfully forever, with stored hashes never actually improving, which is easy to miss without deliberately checking for this bean's presence during a security review.

- `UserDetailsPasswordService` is the missing link between `upgradeEncoding`'s detection and an actual, persisted improvement to a stored password hash — without a registered implementation, the detection signal is computed and silently discarded on every login.
- `JdbcUserDetailsManager` already implements this interface using its own SQL update logic — applications using it directly get working password upgrades with no additional wiring.
- A custom `UserDetailsService` backed by real storage should almost always be paired with a corresponding `UserDetailsPasswordService` implementation, or password-parameter/algorithm upgrades configured elsewhere in the security setup will never actually take effect.
- The upgrade is naturally idempotent: once a user's stored hash matches the current configuration, `upgradeEncoding` returns `false` on all subsequent logins, and no redundant re-upgrade work ever happens.
