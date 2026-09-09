---
card: system-design
gi: 148
slug: per-user-vs-global-quotas
title: Per-user vs global quotas
---

## 1. What it is

A **per-user quota** limits how many requests one individual client (a user ID, an API key, or an IP address) can make. A **global quota** limits the total number of requests the whole service accepts, summed across every client. Both use the same underlying algorithms — [token bucket](0143-token-bucket.md), [fixed window](0145-fixed-window-counter.md), and so on — but they differ in what the counter is keyed by: one key per client, versus one single key for everyone.

## 2. Why & when

These two quota types protect against different problems. A per-user quota stops one client from monopolizing the service or abusing an API, while letting every other client operate normally. A global quota protects the service itself (or a shared downstream dependency, such as a third-party API with a total account-wide limit) from being overwhelmed, no matter which clients the load comes from. Most production systems need both at once: a per-user quota for fairness and abuse prevention, and a global quota as a hard ceiling that protects the system even if many different users, none individually abusive, happen to spike traffic together.

## 3. Core concept

- **Per-user key:** the rate-limit counter's key includes the client identity, e.g. `ratelimit:user-42:window-X`; each client gets an independent bucket or counter.
- **Global key:** a single fixed key, e.g. `ratelimit:global:window-X`, shared by every request regardless of who sent it.
- **Layered quotas:** many systems check the per-user quota first, then the global quota, and reject the request if either one is exceeded — a request must pass both checks to proceed.
- **Different limits, different purposes:** a per-user limit is usually about fairness ("no single user gets more than their fair share"); a global limit is usually about capacity ("the system as a whole cannot exceed what it can safely handle").
- **Tiered per-user quotas:** many APIs vary the per-user limit itself by plan or tier (e.g. free tier gets 100 requests/hour, paid tier gets 10,000/hour), still checked against the same global ceiling underneath.

## 4. Diagram

```
   request from user-A  ---> check per-user quota (user-A's own bucket)
                                     |
                                allowed? --- no --> REJECT (429, user-A over their limit)
                                     |
                                    yes
                                     |
                                     v
                        check global quota (one shared bucket, ALL users)
                                     |
                                allowed? --- no --> REJECT (429, system-wide capacity reached)
                                     |
                                    yes
                                     v
                              request proceeds
```
*Caption: a request must pass the per-user check and the global check, in order, before it is allowed through.*

## 5. Runnable example

**Level 1 — Basic.** Independent per-user counters, one bucket per client.

**Level 2 — Add a global counter.** A single shared bucket that every request also has to pass, on top of its own per-user bucket.

**Level 3 — Layered check.** Combine both checks in the correct order, and show one user being blocked by their own limit while another is blocked by the global ceiling.

```java
// QuotaDemo.java
import java.util.*;

public class QuotaDemo {

    // A simple fixed counter with a limit - reused for both per-user and global quotas.
    static class SimpleCounter {
        final int limit;
        int count = 0;
        SimpleCounter(int limit) { this.limit = limit; }
        boolean tryConsume() {
            if (count >= limit) return false;
            count++;
            return true;
        }
    }

    static class QuotaChecker {
        final Map<String, SimpleCounter> perUserCounters = new HashMap<>();
        final int perUserLimit;
        final SimpleCounter globalCounter; // Level 2: one shared counter for everyone

        QuotaChecker(int perUserLimit, int globalLimit) {
            this.perUserLimit = perUserLimit;
            this.globalCounter = new SimpleCounter(globalLimit);
        }

        // Level 3: check per-user first, then global, in that order.
        String checkRequest(String userId) {
            SimpleCounter userCounter = perUserCounters.computeIfAbsent(userId, k -> new SimpleCounter(perUserLimit));
            if (!userCounter.tryConsume()) {
                return "REJECTED (429: " + userId + " exceeded their per-user quota of " + perUserLimit + ")";
            }
            if (!globalCounter.tryConsume()) {
                return "REJECTED (429: global quota of " + globalCounter.limit + " reached)";
            }
            return "ALLOWED";
        }
    }

    public static void main(String[] args) {
        // per-user limit 3, global limit 5 (deliberately tighter than 2 users * 3 each = 6)
        QuotaChecker checker = new QuotaChecker(3, 5);

        // user-A sends 4 requests - the 4th should hit their OWN per-user limit.
        for (int i = 1; i <= 4; i++) {
            System.out.println("user-A request " + i + ": " + checker.checkRequest("user-A"));
        }
        // user-B sends 3 requests - within their own limit, but the global bucket is nearly empty by now.
        for (int i = 1; i <= 3; i++) {
            System.out.println("user-B request " + i + ": " + checker.checkRequest("user-B"));
        }
    }
}
```

**How to run:** save as `QuotaDemo.java`, then run `java QuotaDemo.java`.

## 6. Walkthrough

1. `user-A`'s first 3 requests each call `checkRequest`, which finds (or creates) `user-A`'s own `SimpleCounter(3)`; each passes the per-user check, then the shared `globalCounter.tryConsume()`, bringing the global count from 0 to 3.
2. `user-A`'s 4th request calls `userCounter.tryConsume()` on their own counter, which is already at `count = 3 == limit`, so it returns `false` immediately — the method returns the per-user rejection message without ever touching `globalCounter`.
3. `user-B`'s first request creates their own separate `SimpleCounter(3)` (starting at 0, independent of `user-A`'s counter), passes their per-user check, then calls `globalCounter.tryConsume()`, which brings the global count from 3 to 4 — still under the global limit of 5, so it is allowed.
4. `user-B`'s second request passes their own per-user check (now at 2 of 3) and pushes the global counter to 5, exactly at its limit — still allowed, since the check is `count >= limit`, not `count > limit`.
5. `user-B`'s third request passes their own per-user check easily (they are only at 2 of 3), but `globalCounter.tryConsume()` now finds `count = 5 >= limit = 5` and returns `false` — this request is rejected by the *global* quota, not `user-B`'s own quota, showing the two limits are independent failure modes that a client-facing error message should distinguish.

## 7. Gotchas & takeaways

> Gotcha: checking the global quota *before* the per-user quota lets one heavy user's requests consume shared global capacity even while being rejected for their own separate violation somewhere else in the check order — always check the cheaper, more specific (per-user) limit first, so a request that is going to be rejected anyway does not also waste global capacity.

- Per-user and global quotas answer different questions: "is this one client being fair?" versus "can the system handle the combined load right now?"
- A request commonly must pass both checks, per-user first, to avoid wasting shared capacity on requests that were going to be rejected anyway.
- Tiered per-user limits (by plan or role) sit on top of this same mechanism — only the per-user limit value changes, not the underlying algorithm.
- Related concepts: [Centralized counter (Redis) rate limiting](0147-centralized-counter-redis-rate-limiting.md) (where these counters live across a fleet of servers), [Rate-limit response headers & 429 handling](0149-rate-limit-response-headers-429-handling.md) (telling the caller which quota they hit), [Token bucket](0143-token-bucket.md) (a richer algorithm either quota type can be built on).
