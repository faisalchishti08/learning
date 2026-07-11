---
card: spring-security
gi: 41
slug: password-storage-history-upgrades
title: "Password storage history & upgrades"
---

## 1. What it is

Password upgrading is the practice of transparently re-hashing a user's stored password with a stronger algorithm (or stronger parameters of the same algorithm) at the one moment it's guaranteed to be safely available in plaintext: right after the user successfully authenticates, when the raw password they just typed is briefly in memory anyway. `PasswordEncoder.upgradeEncoding(encodedPassword)` signals whether a given stored hash is due for an upgrade, and `UserDetailsPasswordService` (the next card) provides the hook to actually persist the newly re-hashed value — together letting an entire user base migrate to a stronger hash gradually, one login at a time, with zero forced password resets.

```java
// inside DaoAuthenticationProvider's real authentication flow, roughly:
if (passwordEncoder.matches(rawPassword, storedHash)) {
    if (passwordEncoder.upgradeEncoding(storedHash)) {
        String newHash = passwordEncoder.encode(rawPassword); // raw password is available RIGHT NOW, safely
        userDetailsPasswordService.updatePassword(userDetails, newHash); // persisted for NEXT time
    }
    // ... proceed with successful authentication using the ORIGINAL result ...
}
```

## 2. Why & when

A stored password hash cannot be "upgraded" by inspecting it alone — hashing is one-directional by design, so turning an old BCrypt hash into a new Argon2 hash requires the *original raw password*, which the application never has and should never store. The only moment the raw password is legitimately available is during a successful login attempt, when the user has just typed it in — `upgradeEncoding` exists specifically to flag "this stored hash was created with weaker settings than we'd use today," so that exact moment can be used to opportunistically re-hash and persist a stronger version, entirely invisibly to the user.

Reach for password upgrading when:

- Increasing a cost factor over time (BCrypt's work factor, PBKDF2's iteration count) as hardware gets faster — `upgradeEncoding` compares a stored hash's *embedded* parameters against the encoder's *currently configured* parameters and flags a mismatch.
- Migrating from one algorithm to another entirely (the previous card's `DelegatingPasswordEncoder` scenario) — `upgradeEncoding` on the delegating encoder flags any hash whose prefix doesn't match the current default `idForEncode`, letting the gradual migration actually complete over time as users log in, rather than remaining permanently split between old and new algorithms.
- Auditing how much of a user base is still on outdated hash parameters or algorithms — since the upgrade only happens on successful login, inactive accounts remain on their original hash until (and unless) they log in again, worth monitoring for genuinely stale accounts.

## 3. Core concept

```
 upgradeEncoding(storedHash) -- a PURE inspection, reads the stored hash's OWN embedded parameters, answers:
   "would encode()'ing this SAME password again, right now, with CURRENT settings, produce something DIFFERENT?"

 for DelegatingPasswordEncoder:
   upgradeEncoding(stored) = TRUE  if stored's {id} prefix != the CURRENTLY configured idForEncode
                            = FALSE if they already match

 for BCryptPasswordEncoder (a SINGLE algorithm, varying cost factor):
   upgradeEncoding(stored) = TRUE  if stored hash's EMBEDDED cost factor < the CURRENTLY configured cost factor
                            = FALSE if they already match

 the ACTUAL upgrade only ever happens as a SIDE EFFECT of a SUCCESSFUL login,
   because that is the ONLY moment the raw password is legitimately available to re-hash
```

`upgradeEncoding` never re-hashes anything itself — it only signals whether an upgrade *would* be worthwhile, given the raw password becoming available.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A successful login verifies the raw password against an old stored hash upgradeEncoding then checks whether that stored hash uses outdated parameters if so the raw password still in memory is re hashed with current settings and persisted for next time while this login proceeds normally using the original verification result">
  <rect x="15" y="65" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">login succeeds</text>
  <text x="90" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(raw password in memory)</text>

  <rect x="220" y="65" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="310" y="85" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">upgradeEncoding(stored)?</text>
  <text x="310" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">outdated params/algorithm?</text>

  <rect x="455" y="20" width="165" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="537" y="42" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">re-hash + persist NOW</text>

  <rect x="455" y="120" width="165" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="537" y="142" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">leave hash unchanged</text>

  <defs><marker id="a41" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="88" x2="220" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a41)"/>
  <line x1="400" y1="78" x2="455" y2="41" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a41)"/>
  <text x="425" y="55" fill="#8b949e" font-size="6.5" font-family="sans-serif">YES</text>
  <line x1="400" y1="98" x2="455" y2="135" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a41)"/>
  <text x="425" y="118" fill="#8b949e" font-size="6.5" font-family="sans-serif">NO</text>
</svg>

The re-hash always piggybacks on a successful login — never a separate, standalone operation on stored data alone.

## 5. Runnable example

The scenario: model `upgradeEncoding` for a cost-factor comparison, then wire it into a full login flow that opportunistically re-hashes on success, then run it across a small user base to demonstrate gradual migration completing purely through normal login activity, with inactive accounts correctly left behind.

### Level 1 — Basic

`upgradeEncoding` comparing a stored hash's embedded cost factor against the currently configured one.

```java
import java.util.*;

public class PasswordUpgradeLevel1 {
    // models a hash string embedding its OWN cost factor, e.g. "cost=8:<hash>"
    record StoredHash(int embeddedCostFactor, String hashValue) {
        static StoredHash parse(String stored) {
            String[] parts = stored.split(":", 2);
            return new StoredHash(Integer.parseInt(parts[0].substring(5)), parts[1]);
        }
    }

    static int currentCostFactor = 12; // the encoder's CURRENTLY configured cost factor

    static boolean upgradeEncoding(String storedHashString) {
        StoredHash stored = StoredHash.parse(storedHashString);
        return stored.embeddedCostFactor() < currentCostFactor; // TRUE if the stored hash is WEAKER than current config
    }

    public static void main(String[] args) {
        String oldHash = "cost=8:abc123hash"; // created back when cost factor 8 was the default
        String freshHash = "cost=12:xyz789hash"; // created just now, at the current default

        System.out.println("old hash (cost=8) needs upgrade? " + upgradeEncoding(oldHash));
        System.out.println("fresh hash (cost=12) needs upgrade? " + upgradeEncoding(freshHash));
    }
}
```

How to run: `java PasswordUpgradeLevel1.java`

`upgradeEncoding` never touches the raw password at all — it purely compares the stored hash's own embedded cost factor (`8`) against `currentCostFactor` (`12`), correctly flagging the older hash as due for an upgrade while leaving the already-current one alone.

### Level 2 — Intermediate

Wire the upgrade check into a full login flow, re-hashing and persisting only on a successful match.

```java
import java.security.MessageDigest;
import java.util.*;

public class PasswordUpgradeLevel2 {
    static int currentCostFactor = 12;

    record StoredHash(int costFactor, String hashValue) {
        String serialize() { return "cost=" + costFactor + ":" + hashValue; }
        static StoredHash parse(String s) {
            String[] parts = s.split(":", 2);
            return new StoredHash(Integer.parseInt(parts[0].substring(5)), parts[1]);
        }
    }

    static String hashWithCost(String raw, int cost) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest((cost + ":" + raw).getBytes()));
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    static boolean matches(String raw, StoredHash stored) { return hashWithCost(raw, stored.costFactor()).equals(stored.hashValue()); }
    static boolean upgradeEncoding(StoredHash stored) { return stored.costFactor() < currentCostFactor; }

    static Map<String, StoredHash> userStore = new HashMap<>();

    static String login(String username, String rawPassword) {
        StoredHash stored = userStore.get(username);
        if (stored == null || !matches(rawPassword, stored)) return "401 Unauthorized";

        if (upgradeEncoding(stored)) {
            StoredHash upgraded = new StoredHash(currentCostFactor, hashWithCost(rawPassword, currentCostFactor));
            userStore.put(username, upgraded); // PERSISTED now, using the raw password available THIS moment
            System.out.println("  (silently upgraded " + username + "'s stored hash from cost=" + stored.costFactor()
                    + " to cost=" + currentCostFactor + ")");
        }
        return "200 OK, authenticated as " + username;
    }

    public static void main(String[] args) {
        userStore.put("alice", new StoredHash(8, hashWithCost("hunter2", 8))); // registered LONG ago, cost=8

        System.out.println(login("alice", "hunter2"));
        System.out.println("alice's stored hash now: " + userStore.get("alice").serialize());

        System.out.println(login("alice", "hunter2")); // second login: ALREADY at current cost, no further upgrade
    }
}
```

How to run: `java PasswordUpgradeLevel2.java`

alice's first login succeeds against her old `cost=8` hash and, because `upgradeEncoding` returns `true`, immediately re-hashes and persists a `cost=12` version using the raw password she just supplied; her second login (with the same password) finds `upgradeEncoding` now returns `false`, since her stored hash already matches the current cost factor, so no further re-hash happens.

### Level 3 — Advanced

Run the upgrade flow across a small user base with mixed activity, demonstrating gradual, login-driven migration completing for active users while correctly leaving an inactive account behind on its original hash.

```java
import java.security.MessageDigest;
import java.util.*;

public class PasswordUpgradeLevel3 {
    static int currentCostFactor = 12;

    record StoredHash(int costFactor, String hashValue) {
        String serialize() { return "cost=" + costFactor; }
    }

    static String hashWithCost(String raw, int cost) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest((cost + ":" + raw).getBytes()));
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    static boolean matches(String raw, StoredHash stored) { return hashWithCost(raw, stored.costFactor()).equals(stored.hashValue()); }
    static boolean upgradeEncoding(StoredHash stored) { return stored.costFactor() < currentCostFactor; }

    static Map<String, StoredHash> userStore = new LinkedHashMap<>();
    static Map<String, String> knownPasswords = Map.of("alice", "hunter2", "bob", "letmein123", "carol", "p@ssw0rd");

    static void login(String username) {
        StoredHash stored = userStore.get(username);
        String rawPassword = knownPasswords.get(username);
        if (stored == null || !matches(rawPassword, stored)) { System.out.println(username + ": login failed"); return; }

        if (upgradeEncoding(stored)) {
            userStore.put(username, new StoredHash(currentCostFactor, hashWithCost(rawPassword, currentCostFactor)));
        }
        System.out.println(username + ": logged in, stored hash now " + userStore.get(username).serialize());
    }

    public static void main(String[] args) {
        // ALL THREE users originally registered when cost=8 was the default
        userStore.put("alice", new StoredHash(8, hashWithCost("hunter2", 8)));
        userStore.put("bob", new StoredHash(8, hashWithCost("letmein123", 8)));
        userStore.put("carol", new StoredHash(8, hashWithCost("p@ssw0rd", 8)));

        System.out.println("-- alice and bob log in this week, carol has been INACTIVE for months --");
        login("alice");
        login("bob");
        // carol never logs in during this period -- her hash is NEVER touched

        System.out.println();
        System.out.println("final state after this period of activity:");
        userStore.forEach((user, hash) -> System.out.println("  " + user + ": " + hash.serialize()));
    }
}
```

How to run: `java PasswordUpgradeLevel3.java`

alice and bob, who both log in, have their stored hashes silently upgraded to `cost=12`; carol, who never logs in during this period, remains on her original `cost=8` hash — the final state printout shows the migration genuinely partial and activity-driven, exactly matching how this mechanism behaves in a real production user base, where dormant accounts naturally lag behind until (and unless) their owner eventually logs in again.

## 6. Walkthrough

Trace `login("bob")` from Level 3.

1. `stored = userStore.get("bob")` retrieves bob's `StoredHash(8, hashWithCost("letmein123", 8))`, and `rawPassword = knownPasswords.get("bob")` retrieves `"letmein123"` — standing in for what bob actually typed into a real login form.
2. `matches("letmein123", stored)` recomputes `hashWithCost("letmein123", 8)` and compares it against `stored.hashValue()`, which is identical since it was constructed the same way — this returns `true`, so the method does not take the early "login failed" branch.
3. `upgradeEncoding(stored)` checks `stored.costFactor() < currentCostFactor`, i.e. `8 < 12`, which is `true` — bob's stored hash uses outdated parameters relative to the current configuration.
4. Because `upgradeEncoding` returned `true`, the method computes a brand-new `StoredHash(currentCostFactor, hashWithCost(rawPassword, currentCostFactor))` — note this re-hash uses `rawPassword`, the value only available *because* bob just successfully logged in — and persists it via `userStore.put("bob", ...)`, overwriting his old, weaker entry.
5. The final `println` reports bob's stored hash as `"cost=12"`, confirming the upgrade took effect — meanwhile carol, who is never passed to `login` at all during this run, keeps her original `StoredHash(8, ...)` entry completely untouched, which the final `forEach` printout confirms by still showing `"cost=8"` for her specifically.

```
alice logs in  -> matches (cost=8) -> upgradeEncoding=true  -> re-hashed & persisted at cost=12
bob logs in    -> matches (cost=8) -> upgradeEncoding=true  -> re-hashed & persisted at cost=12
carol NEVER logs in during this period -> her stored hash remains at cost=8, untouched
```

## 7. Gotchas & takeaways

> **Gotcha:** relying purely on login-driven upgrades means dormant accounts can remain on outdated, weaker hash parameters indefinitely — as Level 3's carol demonstrates. For applications with meaningful populations of long-dormant accounts, this is worth monitoring explicitly (auditing what fraction of stored hashes are outdated) and potentially supplementing with a forced password reset for accounts that have been both dormant *and* below the current minimum standard for an extended period.

- `upgradeEncoding` is a pure inspection of a stored hash's own embedded parameters against the encoder's current configuration — it never touches or requires the raw password itself.
- The actual re-hash only ever happens as a side effect of a *successful* login, since that is the only moment the raw password is legitimately available in memory to recompute a stronger hash from.
- This mechanism enables gradual, zero-forced-reset migration to stronger hashing parameters or an entirely different algorithm (paired with `DelegatingPasswordEncoder` from the previous card) — but migration completeness is inherently tied to user login activity, not time elapsed.
- Dormant accounts remain on their original hash indefinitely under this mechanism alone; applications with a meaningful population of long-inactive accounts should consider supplementary measures for those specific accounts.
