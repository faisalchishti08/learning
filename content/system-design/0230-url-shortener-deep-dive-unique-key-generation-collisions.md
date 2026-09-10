---
card: system-design
gi: 230
slug: url-shortener-deep-dive-unique-key-generation-collisions
title: "URL Shortener — deep-dive: unique key generation & collisions"
---

## 1. What it is

This page covers the **deep-dive** facet of the **URL Shortener** case study, focused on the one genuinely hard sub-problem: how the key-generation service (named in [high-level architecture](0228-url-shortener-high-level-architecture.md), storing into the schema from [data model & schema](0229-url-shortener-data-model-schema.md)) produces a `short_code` that is guaranteed unique, efficiently, at the scale established in [capacity estimation](0226-url-shortener-capacity-estimation.md) (~39 creations/sec average, ~117 peak).

## 2. Why & when

Generating a short code sounds trivial — "just create a random string" — until you consider what happens when two concurrent requests generate the same code, or when the encoding scheme itself makes collisions likely as the total number of stored URLs grows. This is the one part of the whole case study that is a genuine algorithm problem, not a component-selection problem, which is why it gets its own deep-dive facet instead of being folded into the architecture page.

## 3. Core concept

- **Base62 encoding.** Short codes use the 62 characters `[a-zA-Z0-9]`. A 7-character Base62 code has `62^7` ≈ 3.5 trillion possible values — comfortably larger than the ~6 billion total URLs the [capacity estimation](0226-url-shortener-capacity-estimation.md) projects over 5 years, with enormous headroom.
- **Approach A: random generation + collision check.** Generate a random 7-character Base62 string, check if it already exists in the database, and retry with a new random string if it does. Simple, but every creation requires a database read before the write, and collision probability (while low per attempt) is not zero.
- **Approach B: counter-based generation.** Maintain a globally unique, monotonically increasing counter (e.g. from a distributed ID generator, or a database sequence); encode each new counter value directly into Base62. This guarantees uniqueness by construction — no collision check needed at all — because no two counter values are ever the same.
- **The counter approach's real challenge is generating the counter itself, safely, under concurrent requests** — a naive shared counter (a single in-memory integer) is not safe if multiple app server instances are creating URLs simultaneously, which is the normal case in the [high-level architecture](0228-url-shortener-high-level-architecture.md)'s horizontally scaled app servers.
- **Trading a range of counter values to each server (or thread) at once** — each server requests and reserves a block of, say, 1,000 consecutive counter values from a central counter source, then hands out codes from its own local block without needing to coordinate again until the block is exhausted. This removes per-request coordination overhead entirely, at the cost of some values from a crashed server's unused block being "wasted" (skipped, never reused) — an acceptable tradeoff given how much headroom the keyspace has.

## 4. Diagram

```
   RANDOM + COLLISION CHECK              COUNTER-BASED (with block allocation)

   generate random 7-char code            App Server A requests a block:
        |                                   central counter: 1,000,000 -> 1,000,999
        v                                   (reserved for server A, 1,000 codes)
   check DB: does it exist?
        |                                 App Server B requests a block:
     yes|  no                              central counter: 1,001,000 -> 1,001,999
        |   \                              (reserved for server B, 1,000 codes)
        v    v
     retry   use it,                     Server A encodes 1,000,000 -> Base62 -> "1LY7VK"
     with     write to DB                Server B encodes 1,001,000 -> Base62 -> "1LY7Vk"
     new                                 (different values, GUARANTEED no collision,
     random                                no DB check needed at all)
     code
```
*Caption: random generation needs a collision check on every single creation; counter-based generation with block allocation removes that check entirely, at the cost of a small, acceptable amount of wasted keyspace if a server crashes mid-block.*

## 5. Runnable example

**Level 1 — Basic.** Base62 encoding of a counter value into a short code.

**Level 2 — Intermediate.** Random generation with a collision check against a simulated existing-codes set, including a retry on collision.

**Level 3 — Advanced.** Counter-based generation with block allocation across multiple simulated app server instances, proving no two instances ever produce the same code.

```java
// UrlShortenerKeyGenDemo.java
import java.util.*;

public class UrlShortenerKeyGenDemo {

    static final String BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";

    // ---------- Level 1: Base62 encoding ----------
    static String toBase62(long value) {
        if (value == 0) return String.valueOf(BASE62_ALPHABET.charAt(0));
        StringBuilder sb = new StringBuilder();
        while (value > 0) {
            sb.append(BASE62_ALPHABET.charAt((int) (value % 62)));
            value /= 62;
        }
        return sb.reverse().toString();
    }

    // ---------- Level 2: random generation + collision check ----------
    static class RandomKeyGenerator {
        Set<String> existingCodes = new HashSet<>(); // stands in for a DB existence check
        Random rnd = new Random(1);
        int collisionRetries = 0;

        String generate() {
            String code;
            do {
                StringBuilder sb = new StringBuilder(7);
                for (int i = 0; i < 7; i++) sb.append(BASE62_ALPHABET.charAt(rnd.nextInt(62)));
                code = sb.toString();
                if (existingCodes.contains(code)) {
                    collisionRetries++;
                    System.out.println("    collision on \"" + code + "\" - retrying with a new random code");
                }
            } while (existingCodes.contains(code));
            existingCodes.add(code);
            return code;
        }
    }

    // ---------- Level 3: counter-based generation with block allocation ----------
    static class CentralCounter {
        long nextCounter = 1_000_000L;
        synchronized long reserveBlock(int blockSize) {
            long start = nextCounter;
            nextCounter += blockSize;
            return start;
        }
    }

    static class AppServerKeyGenerator {
        String serverName;
        CentralCounter central;
        long blockStart, blockEnd, blockCursor;
        int blockSize;

        AppServerKeyGenerator(String serverName, CentralCounter central, int blockSize) {
            this.serverName = serverName; this.central = central; this.blockSize = blockSize;
            requestNewBlock();
        }

        void requestNewBlock() {
            blockStart = central.reserveBlock(blockSize);
            blockEnd = blockStart + blockSize;
            blockCursor = blockStart;
            System.out.println("    " + serverName + " reserved block [" + blockStart + ", " + blockEnd + ")");
        }

        String generate() {
            if (blockCursor >= blockEnd) requestNewBlock(); // block exhausted, get a new one
            long counterValue = blockCursor++;
            return toBase62(counterValue);
        }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - Base62 encoding of counter values:");
        for (long v : new long[]{0, 61, 62, 1_000_000, 3_521_614_606_207L}) {
            System.out.println("  " + v + " -> \"" + toBase62(v) + "\"");
        }

        System.out.println("\nLevel 2 - random generation with collision check:");
        RandomKeyGenerator randomGen = new RandomKeyGenerator();
        for (int i = 0; i < 5; i++) System.out.println("  generated: " + randomGen.generate());
        // Force a collision deliberately to show the retry path:
        randomGen.rnd = new Random(1); // reset seed so the very next value repeats a prior one
        System.out.println("  " + randomGen.generate() + "  <- forced collision + retry happened above");

        System.out.println("\nLevel 3 - counter-based generation, two app servers, block size 5:");
        CentralCounter central = new CentralCounter();
        AppServerKeyGenerator serverA = new AppServerKeyGenerator("server-A", central, 5);
        AppServerKeyGenerator serverB = new AppServerKeyGenerator("server-B", central, 5);

        Set<String> allGenerated = new HashSet<>();
        for (int i = 0; i < 5; i++) {
            String codeA = serverA.generate();
            String codeB = serverB.generate();
            System.out.println("  server-A: \"" + codeA + "\"   server-B: \"" + codeB + "\"");
            allGenerated.add(codeA);
            allGenerated.add(codeB);
        }
        System.out.println("  total codes generated: " + (allGenerated.size()) +
            " (10 requested, 10 unique -> ZERO collisions, no DB check was ever needed)");

        System.out.println("\n  server-A's block exhausted after 5 - requests a new one automatically:");
        System.out.println("  server-A: \"" + serverA.generate() + "\"");
    }
}
```

**How to run:** `java UrlShortenerKeyGenDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `toBase62(0)` returns `"0"` directly (the loop never runs, and the leading zero-value case is handled first). `toBase62(61)` returns `"Z"` — the last character in the 62-character alphabet. `toBase62(62)` returns `"10"` — the encoding rolls over exactly like any positional number system once the value exceeds the base, the same way decimal `10` follows `9`. `toBase62(3_521_614_606_207L)` — close to `62^7 - 1`, the largest 7-character Base62 value — demonstrates the encoding still produces a compact 7-character code even near the top of the keyspace this system was sized for.
2. **Level 2:** `randomGen.generate()` is called five times, each generating a random 7-character code and checking `existingCodes.contains(code)` before accepting it — with a 7-character Base62 keyspace of ~3.5 trillion values, none of the first five calls collide. Resetting `randomGen.rnd` to the same seed used originally and calling `generate()` again forces the *exact same* first random draw as before — since that code is now in `existingCodes`, the `do...while` loop's condition catches it, prints the collision message, and draws again until it finds an unused code.
3. This demonstrates the real mechanism: collision checking works correctly, but it requires an existence check (a database read, in a real system) on every single creation, and — while rare in practice given the keyspace size — the check-and-retry loop has no upper bound on how many attempts it might take under bad luck.
4. **Level 3:** `serverA` and `serverB` are each constructed with their own `AppServerKeyGenerator`, and each constructor call immediately calls `requestNewBlock()`, which calls the shared `central.reserveBlock(5)`. Because `reserveBlock` is `synchronized`, `serverA` gets `[1000000, 1000005)` and `serverB` gets `[1000005, 1000010)` — two genuinely disjoint ranges, reserved through one coordination point.
5. The loop calls `serverA.generate()` and `serverB.generate()` five times each, and each call simply reads and increments its own **local** `blockCursor` — no further coordination with `central` happens during this loop, and no code from `serverA`'s block can ever equal a code from `serverB`'s block, because the underlying counter ranges never overlap. `allGenerated.size()` prints `10` for 10 requests, confirming zero collisions occurred, and critically, no existence check against a database was ever needed to guarantee it. The final call shows `serverA`'s block running out after exactly 5 codes, triggering an automatic `requestNewBlock()` call that reserves the next available range from `central` — `[1000010, 1000015)`, since `serverB` already claimed the block in between.

## 7. Gotchas & takeaways

> **Gotcha:** if an app server crashes mid-block, the unused portion of its reserved counter range is permanently skipped — nobody will ever generate those specific codes. This is an intentional, acceptable tradeoff (the keyspace has trillions of values to spare), but it is worth stating explicitly rather than discovering it as a surprise: block allocation trades a small amount of wasted keyspace for the elimination of per-request coordination.

- Counter-based generation with block allocation is generally the stronger choice for a system creating many URLs concurrently across many servers, because it removes the database existence-check from the creation path's critical work entirely — a direct efficiency win at the scale this system targets.
- Random generation with a collision check is simpler to reason about and implement, and remains a reasonable choice for lower-scale systems where the extra database read per creation is not a meaningful cost.
- Base62's 7-character keyspace (~3.5 trillion values) has enormous headroom over the ~6 billion URLs projected in [capacity estimation](0226-url-shortener-capacity-estimation.md) — there is no pressure to shorten codes further at the cost of a smaller keyspace.
- See [URL Shortener — scaling & tradeoffs](0231-url-shortener-scaling-tradeoffs.md) next for how this key-generation approach, and the rest of the architecture, evolves under even larger scale than originally estimated.
