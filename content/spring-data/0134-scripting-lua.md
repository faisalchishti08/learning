---
card: spring-data
gi: 134
slug: scripting-lua
title: "Scripting (Lua)"
---

## 1. What it is

Redis can execute a **Lua script** on the server itself, atomically — the entire script runs as one indivisible unit, with no other client's commands able to interleave partway through, no matter how many Redis operations the script contains. Spring Data Redis exposes this through `RedisScript` plus `redisTemplate.execute(script, keys, args)`.

```java
String luaScript =
    "if redis.call('GET', KEYS[1]) == ARGV[1] then " +
    "  return redis.call('DEL', KEYS[1]) " +
    "else " +
    "  return 0 " +
    "end";

RedisScript<Long> script = RedisScript.of(luaScript, Long.class);
Long result = redisTemplate.execute(script, List.of("lock:order:1"), "instance-A-token");
```

## 2. Why & when

The previous card's distributed lock ended with exactly this problem: a "check owner, then delete" sequence needs to be atomic, but `GET` and `DEL` are two separate round trips, leaving a race window between them. A Lua script closes that gap completely — because the whole script executes as a single atomic step on the Redis server, there's no window for another client's command to sneak in between the check and the action, no matter how much logic the script contains.

Reach for a Lua script when:

- You need multiple Redis operations (a read, a comparison, a conditional write) to happen as one atomic unit, and a plain Redis transaction (`MULTI`/`EXEC`, from the earlier card) isn't expressive enough — a transaction can't make a later command's behavior depend on an earlier command's *result* within the same transaction, but a Lua script can.
- You want to reduce round trips for a multi-step operation that has conditional logic — the entire decision process runs server-side in one call, instead of several separate client-server exchanges.
- You need the exact atomic "compare current value, then act" pattern the distributed-lock release required — this is one of the most common real-world reasons to reach for Lua scripting in Redis.

## 3. Core concept

```
 WITHOUT a script (two separate round trips -- has a race window):
   GET lock:order:1        -- returns "instance-A-token"
   [ ... ANOTHER CLIENT COULD ACT HERE ... ]
   DEL lock:order:1        -- might now be deleting a DIFFERENT client's lock

 WITH a Lua script (ONE atomic round trip -- no race window possible):
   EVAL "if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) else return 0 end"
        1 lock:order:1 instance-A-token
   -- the GET, the comparison, and the DEL all happen as ONE indivisible step on the server
```

Everything inside the script — however many `redis.call(...)` invocations it makes — executes as one atomic unit; no other client's command can be processed by the server in the middle of it.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Lua script runs a GET, a comparison, and a conditional DEL as one atomic step with no interleaving from other clients">
  <rect x="20" y="20" width="600" height="120" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">EVAL script (runs entirely on the server, atomically)</text>

  <rect x="50" y="60" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="125" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">GET lock:order:1</text>

  <rect x="240" y="60" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="315" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">compare to ARGV[1]</text>

  <rect x="430" y="60" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="505" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">conditional DEL</text>

  <line x1="200" y1="77" x2="235" y2="77" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a1)"/>
  <line x1="390" y1="77" x2="425" y2="77" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a1)"/>

  <text x="320" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no other client's command can run between any of these three steps</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

The entire multi-step sequence is one atomic black box from every other client's point of view.

## 5. Runnable example

The scenario: finishing the distributed lock's safe-release problem from the previous card properly, evolving from a basic atomic compare-and-delete script, to a script that also handles a value-based conditional update (only decrementing inventory if enough stock remains), to passing multiple keys and arguments into one script for a more elaborate atomic operation.

### Level 1 — Basic

Model the atomic compare-and-delete Lua script that safely closes the distributed-lock release race from the previous card.

```java
import java.util.*;
import java.util.function.*;

public class LuaScriptingLevel1 {
    public static void main(String[] args) {
        RedisScriptEngine redis = new RedisScriptEngine();
        redis.set("lock:order:1", "instance-A-token");

        // Mirrors: EVAL "if GET(KEYS[1]) == ARGV[1] then DEL(KEYS[1]) else return 0 end" 1 lock:order:1 <token>
        long resultWrongToken = redis.evalCompareAndDelete("lock:order:1", "instance-B-token");
        System.out.println("Release attempt with WRONG token, result: " + resultWrongToken
            + " (0 = not deleted), key still exists: " + (redis.get("lock:order:1") != null));

        long resultRightToken = redis.evalCompareAndDelete("lock:order:1", "instance-A-token");
        System.out.println("Release attempt with RIGHT token, result: " + resultRightToken
            + " (1 = deleted), key still exists: " + (redis.get("lock:order:1") != null));
    }
}

// Stands in for the Redis server executing an EVAL'd Lua script as one atomic unit.
class RedisScriptEngine {
    private final Map<String, String> data = new HashMap<>();
    void set(String key, String value) { data.put(key, value); }
    String get(String key) { return data.get(key); }

    // The ENTIRE method body corresponds to what happens server-side, atomically, for ONE EVAL call.
    long evalCompareAndDelete(String key, String expectedValue) {
        if (expectedValue.equals(data.get(key))) {
            data.remove(key);
            return 1;
        }
        return 0;
    }
}
```

How to run: `java LuaScriptingLevel1.java`

`evalCompareAndDelete` models exactly what the Lua script from the intro snippet does: compare the stored value against the expected token, and only delete if they match — all as a single method call standing in for a single atomic `EVAL`. The wrong-token attempt correctly leaves the key untouched; the right-token attempt correctly removes it — with no possibility, in real Redis, of another client's command running in between the comparison and the deletion.

### Level 2 — Intermediate

Extend the script to a conditional numeric update: decrement inventory only if enough stock remains, atomically — a check-then-act pattern that would otherwise need its own distributed lock to do safely without a script.

```java
import java.util.*;

public class LuaScriptingLevel2 {
    public static void main(String[] args) {
        RedisScriptEngine redis = new RedisScriptEngine();
        redis.setInt("inventory:widget", 3);

        // Mirrors: EVAL "local n = tonumber(GET(KEYS[1])); if n >= tonumber(ARGV[1]) then return DECRBY(KEYS[1], ARGV[1]) else return -1 end"
        long result1 = redis.evalDecrementIfEnough("inventory:widget", 2); // 3 >= 2 -- succeeds
        System.out.println("Requested 2, had 3: result=" + result1 + " (remaining stock: " + redis.getInt("inventory:widget") + ")");

        long result2 = redis.evalDecrementIfEnough("inventory:widget", 5); // 1 >= 5 -- FAILS, no partial decrement
        System.out.println("Requested 5, had 1: result=" + result2 + " (remaining stock: " + redis.getInt("inventory:widget") + ")");
    }
}

class RedisScriptEngine {
    private final Map<String, Integer> intData = new HashMap<>();
    void setInt(String key, int value) { intData.put(key, value); }
    int getInt(String key) { return intData.getOrDefault(key, 0); }

    // Atomically: read current stock, compare against requested amount, decrement ONLY if sufficient -- all server-side.
    long evalDecrementIfEnough(String key, int requested) {
        int current = intData.getOrDefault(key, 0);
        if (current < requested) return -1; // NOT enough stock -- script does nothing further, returns a sentinel
        int updated = current - requested;
        intData.put(key, updated);
        return updated;
    }
}
```

How to run: `java LuaScriptingLevel2.java`

`evalDecrementIfEnough` reads the current stock, compares it against the requested amount, and only writes back a decremented value if there's enough — all within one method standing in for one atomic `EVAL` call. Without this atomicity, a plain "GET, check in Java, DECRBY" sequence would have a race: two concurrent requests could both read `3`, both decide `3 >= 2` is true, and both decrement, ending up at `-1` in stock — selling more than actually exists. The script prevents that entirely by making the whole check-then-act sequence indivisible.

### Level 3 — Advanced

Pass multiple keys and arguments into a single script, atomically moving stock from one location's inventory to another's — a genuinely multi-key operation that needs the whole thing to succeed or fail together, exactly like the earlier multi-document transaction card's motivation, but implemented at the Redis layer via a script instead of `MULTI`/`EXEC`.

```java
import java.util.*;

public class LuaScriptingLevel3 {
    public static void main(String[] args) {
        RedisScriptEngine redis = new RedisScriptEngine();
        redis.setInt("inventory:warehouse-A:widget", 10);
        redis.setInt("inventory:warehouse-B:widget", 2);

        // Mirrors: EVAL script 2 KEYS[1]=source KEYS[2]=dest ARGV[1]=amount
        long result1 = redis.evalTransferStock(
            "inventory:warehouse-A:widget", "inventory:warehouse-B:widget", 4); // enough at source -- succeeds
        System.out.println("Transfer 4 (source has 10): result=" + result1
            + ", A=" + redis.getInt("inventory:warehouse-A:widget") + ", B=" + redis.getInt("inventory:warehouse-B:widget"));

        long result2 = redis.evalTransferStock(
            "inventory:warehouse-A:widget", "inventory:warehouse-B:widget", 100); // not enough -- fails, NEITHER side changes
        System.out.println("Transfer 100 (source has 6): result=" + result2
            + ", A=" + redis.getInt("inventory:warehouse-A:widget") + ", B=" + redis.getInt("inventory:warehouse-B:widget"));
    }
}

class RedisScriptEngine {
    private final Map<String, Integer> intData = new HashMap<>();
    void setInt(String key, int value) { intData.put(key, value); }
    int getInt(String key) { return intData.getOrDefault(key, 0); }

    // KEYS[1]=source, KEYS[2]=dest, ARGV[1]=amount -- moves stock ATOMICALLY between two separate keys.
    long evalTransferStock(String sourceKey, String destKey, int amount) {
        int sourceStock = intData.getOrDefault(sourceKey, 0);
        if (sourceStock < amount) return -1; // insufficient -- script touches NEITHER key, returns a sentinel
        intData.put(sourceKey, sourceStock - amount);
        intData.put(destKey, intData.getOrDefault(destKey, 0) + amount);
        return amount;
    }
}
```

How to run: `java LuaScriptingLevel3.java`

`evalTransferStock` reads both keys' current values, checks whether the source has enough to satisfy the transfer, and only then writes to *both* keys — as one atomic script execution, so no other client can ever observe a state where only one side of the transfer has happened. The second call, requesting more than the source has, correctly modifies neither key: warehouse A's and B's stock remain exactly as they were after the first (successful) transfer.

## 6. Walkthrough

Execution starts in `main` for Level 3. `redis.setInt("inventory:warehouse-A:widget", 10)` and `setInt("inventory:warehouse-B:widget", 2)` seed the two keys.

`redis.evalTransferStock("inventory:warehouse-A:widget", "inventory:warehouse-B:widget", 4)` runs first. Inside, `sourceStock` is read as `10`. The check `10 < 4` is `false`, so the transfer proceeds: `intData.put(sourceKey, 10 - 4)` sets warehouse A to `6`, and `intData.put(destKey, 2 + 4)` sets warehouse B to `6`. The method returns `4`.

`redis.evalTransferStock("inventory:warehouse-A:widget", "inventory:warehouse-B:widget", 100)` runs second. `sourceStock` is now read as `6` (the updated value from the previous call). The check `6 < 100` is `true`, so the method returns `-1` immediately — critically, *before* either `intData.put` call — leaving both warehouse A's and warehouse B's stock completely untouched by this failed attempt.

```
Transfer 4 (source has 10): result=4, A=6, B=6
Transfer 100 (source has 6): result=-1, A=6, B=6
```

In real Redis, this script would be loaded once with `SCRIPT LOAD` (returning a SHA1 hash for cheap re-invocation via `EVALSHA`) and invoked as `EVAL "local source = tonumber(redis.call('GET', KEYS[1]) or 0); if source < tonumber(ARGV[1]) then return -1 end; redis.call('DECRBY', KEYS[1], ARGV[1]); redis.call('INCRBY', KEYS[2], ARGV[1]); return tonumber(ARGV[1])" 2 inventory:warehouse-A:widget inventory:warehouse-B:widget 100` — the `2` tells Redis how many of the following arguments are keys (`KEYS[1]`, `KEYS[2]`) versus plain arguments (`ARGV[1]`), and the entire multi-key read-check-write sequence executes as one atomic unit on the server, exactly as modeled here.

## 7. Gotchas & takeaways

> Gotcha: in a real Redis Cluster (an earlier card), all keys a script touches must map to the same hash slot, or the script fails with a `CROSSSLOT` error — exactly the same constraint multi-key transactions had. Cross-warehouse transfers like this example's would need both `inventory:warehouse-A:widget` and `inventory:warehouse-B:widget` hash-tagged to a shared slot (for example, `inventory:{transfer-group}:warehouse-A:widget`) to work in cluster mode.

> Gotcha: a Lua script that runs a genuinely expensive computation blocks the entire Redis server for its whole duration, since Redis executes commands (including scripts) single-threaded — scripts should stay short and fast; anything computationally heavy belongs in application code, with only the atomic, safety-critical portion pushed into the script.

- Lua scripts execute atomically on the Redis server — the whole script, however many operations it contains, runs as one indivisible unit with no interleaving from other clients.
- Scripts solve exactly the problem plain multi-command sequences can't: making a later operation's behavior depend on an earlier operation's result, all within one atomic step (a Redis transaction alone can't do this).
- `KEYS[]` and `ARGV[]` are how a script receives its keys and plain arguments; in cluster mode, every key a script touches must resolve to the same hash slot.
- Keep scripts short — since Redis executes them without yielding to other clients, a slow script blocks the entire server for its duration.
