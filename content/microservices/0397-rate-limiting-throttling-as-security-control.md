---
card: microservices
gi: 397
slug: rate-limiting-throttling-as-security-control
title: "Rate limiting & throttling as a security control"
---

## 1. What it is

**Rate limiting** caps how many requests a caller can make in a given time window; **throttling** is the broader practice of slowing down or shedding excess load, often as a graceful degradation strategy rather than a hard cutoff. Both are usually discussed as reliability tools — protecting a service from being overwhelmed — but they're equally a **security control**: they're often the *only* thing standing between an authenticated, authorized caller and abuse of that legitimate access, whether through brute-force credential guessing, scraping, or a compromised account hammering an endpoint.

## 2. Why & when

Authentication and authorization (covered throughout this section) answer "is this caller allowed to do this at all?" — but neither one answers "how *much* of this should this caller be allowed to do, how *fast*?" You need rate limiting as a security control specifically because:

- **Credential-guessing attacks don't need a stolen credential — they need many attempts.** A login endpoint with no rate limit lets an attacker try thousands of password or [API key](0393-api-keys.md) guesses per second; the same endpoint with a strict per-IP or per-account limit turns brute-forcing from "minutes" into "computationally infeasible."
- **A perfectly legitimate, correctly-authenticated caller can still be the threat.** A leaked API key, a compromised account, or a buggy internal client can generate abusive traffic volumes using entirely valid credentials — rate limiting is the backstop when authentication and authorization both correctly say "yes, this is allowed" but the *volume* is the problem.
- **Denial-of-service resilience.** Even without malicious intent, one runaway client can starve an endpoint for everyone else; rate limiting protects availability, which is itself a security property (the "A" in the classic confidentiality/integrity/availability triad).
- **OWASP API Security Top 10 explicitly calls out "Unrestricted Resource Consumption"** as a top-tier API risk — see [OWASP API Security Top 10](0398-owasp-api-security-top-10.md) — precisely because APIs without rate limits are so commonly exploited for both cost-based and availability-based attacks.

You want rate limiting on every externally-reachable endpoint at minimum, and often on sensitive internal endpoints too — a compromised internal service shouldn't get unlimited-rate access to a downstream service just because it authenticated successfully.

## 3. Core concept

Think of a nightclub with a bouncer at the door. The bouncer already checked IDs (authentication) and confirmed everyone on the guest list is actually invited (authorization) — but the bouncer *also* only lets people in at a pace the room can handle, and if someone tries to duck back outside and immediately re-enter fifty times in a minute, the bouncer starts turning them away regardless of how valid their ID is. The ID check and the pacing check are answering different questions, and a nightclub without the second one gets overwhelmed by a single overeager (or malicious) guest, no matter how legitimate their invitation was.

The two most common algorithms for enforcing a rate limit:

1. **Token bucket** — a bucket holds up to N tokens, refilled at a steady rate; each request consumes one token, and requests are rejected (or queued) when the bucket is empty. This naturally allows short bursts (spend all N tokens at once) while enforcing a steady average rate over time.
2. **Sliding window / fixed window counters** — count requests within a rolling or fixed time window (e.g., "no more than 100 requests per IP per minute") and reject once the count is exceeded; simpler to reason about than token bucket, at the cost of allowing sharper bursts right at window boundaries in the naive fixed-window version.

Rate limits are typically applied at multiple keys simultaneously — per IP address (protects against a single source flooding you, but is weak against distributed attacks or shared corporate NATs), per authenticated account or API key (protects against one compromised or malicious credential, regardless of source IP), and sometimes per endpoint (a login endpoint gets a much stricter limit than a read-only listing endpoint, because the cost of an attacker abusing it differs enormously). Throttling adds graceful responses on top — returning a `429 Too Many Requests` with a `Retry-After` header rather than simply dropping the connection, so well-behaved clients can back off correctly.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Token bucket rate limiting: each request consumes a token from a bucket that refills at a steady rate; requests are allowed while tokens remain and rejected with 429 once the bucket is empty" font-family="sans-serif">
  <rect x="40" y="80" width="140" height="100" rx="10" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="70" fill="#e6edf3" font-size="11" text-anchor="middle">Token bucket (cap=5)</text>
  <circle cx="70" cy="110" r="8" fill="#6db33f"/>
  <circle cx="95" cy="110" r="8" fill="#6db33f"/>
  <circle cx="120" cy="110" r="8" fill="#6db33f"/>
  <circle cx="145" cy="110" r="8" fill="#1c2430" stroke="#8b949e"/>
  <circle cx="170" cy="110" r="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="110" y="155" fill="#8b949e" font-size="9" text-anchor="middle">refills 1 token / 2s</text>

  <rect x="260" y="100" width="100" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="310" y="125" fill="#e6edf3" font-size="10" text-anchor="middle">Request</text>
  <line x1="180" y1="120" x2="260" y2="120" stroke="#8b949e" marker-end="url(#rl)"/>

  <rect x="420" y="60" width="180" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="510" y="85" fill="#6db33f" font-size="10" text-anchor="middle">token available -&gt; 200 OK</text>
  <rect x="420" y="150" width="180" height="40" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="510" y="175" fill="#f85149" font-size="10" text-anchor="middle">bucket empty -&gt; 429 + Retry-After</text>
  <line x1="360" y1="110" x2="420" y2="80" stroke="#6db33f" marker-end="url(#rl)"/>
  <line x1="360" y1="130" x2="420" y2="170" stroke="#f85149" marker-end="url(#rl)"/>
  <defs>
    <marker id="rl" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Each request consumes a token from the bucket if one is available; once the bucket is empty the request is rejected with a 429 and a Retry-After hint, rather than being processed regardless of load.

## 5. Runnable example

Scenario: a login endpoint being brute-forced. We start with no rate limiting at all, add a simple fixed-count limit, then implement a proper token-bucket limiter keyed per-account that also distinguishes a burst of legitimate retries from a sustained attack.

### Level 1 — Basic

```java
// File: NoRateLimit.java -- the login endpoint accepts UNLIMITED attempts.
// An attacker can try as many password guesses as their network allows.
public class NoRateLimit {
    static final String CORRECT_PASSWORD = "correct-horse-battery-staple";

    static boolean attemptLogin(String username, String password) {
        return CORRECT_PASSWORD.equals(password);
    }

    public static void main(String[] args) {
        String[] guesses = {"password", "123456", "letmein", "admin", "qwerty"};
        int attempts = 0;
        for (String guess : guesses) {
            attempts++;
            boolean success = attemptLogin("alice", guess);
            System.out.println("Attempt " + attempts + ": '" + guess + "' -> " + (success ? "SUCCESS" : "failed"));
        }
        System.out.println("Nothing stopped " + attempts + " rapid guesses -- an attacker could try millions more.");
    }
}
```

How to run: `java NoRateLimit.java`

`attemptLogin` performs no accounting of how many times it's been called for a given user. Every guess, correct or not, is processed identically fast, with no penalty for failure — exactly the conditions that make automated password-guessing practical.

### Level 2 — Intermediate

```java
// File: FixedCountLimit.java -- a SIMPLE fixed-window limit: at most 3 login
// attempts per username, reset after the window. Better than nothing, but a
// FIXED window can be gamed right at the boundary, and doesn't distinguish
// a legitimate user who mistyped twice from a scripted attacker.
import java.util.*;

public class FixedCountLimit {
    static final int MAX_ATTEMPTS = 3;
    static final Map<String, Integer> attemptCounts = new HashMap<>();
    static final String CORRECT_PASSWORD = "correct-horse-battery-staple";

    static String attemptLogin(String username, String password) {
        int count = attemptCounts.getOrDefault(username, 0);
        if (count >= MAX_ATTEMPTS) {
            return "429 Too Many Requests -- '" + username + "' exceeded " + MAX_ATTEMPTS + " attempts this window";
        }
        attemptCounts.put(username, count + 1);
        boolean success = CORRECT_PASSWORD.equals(password);
        return success ? "200 OK -- login succeeded" : "401 Unauthorized -- wrong password (attempt " + (count + 1) + ")";
    }

    public static void main(String[] args) {
        String[] guesses = {"password", "123456", "letmein", "admin", "qwerty"};
        for (String guess : guesses) {
            System.out.println(attemptLogin("alice", guess));
        }
    }
}
```

How to run: `java FixedCountLimit.java`

`attemptCounts` tracks a per-username counter. The first three attempts are processed normally (and fail, since none of the guesses are correct); the fourth and fifth are rejected outright with a `429`, before the password is even checked — the attacker's guessing rate has been capped. This is a real improvement, but the limit is global and permanent within this run (there's no time window reset shown), and a distributed attacker could simply spread guesses across many different `username` values or wait out the window, since nothing here varies the response based on *how fast* attempts arrive versus how many total.

### Level 3 — Advanced

```java
// File: TokenBucketPerAccount.java -- a proper TOKEN BUCKET limiter, per
// account, that refills over time (allowing legitimate retries after a pause)
// while still capping burst rate -- and separately tracks a SUSPICIOUS-VELOCITY
// signal to flag likely automated attacks for additional response (e.g. CAPTCHA,
// alerting) rather than just silently blocking.
import java.time.*;
import java.util.*;

public class TokenBucketPerAccount {
    static class Bucket {
        double tokens;
        Instant lastRefill;
        final double capacity;
        final double refillPerSecond;

        Bucket(double capacity, double refillPerSecond, Instant now) {
            this.capacity = capacity;
            this.refillPerSecond = refillPerSecond;
            this.tokens = capacity;
            this.lastRefill = now;
        }

        boolean tryConsume(Instant now) {
            double elapsedSeconds = Duration.between(lastRefill, now).toMillis() / 1000.0;
            tokens = Math.min(capacity, tokens + elapsedSeconds * refillPerSecond);
            lastRefill = now;
            if (tokens >= 1.0) {
                tokens -= 1.0;
                return true;
            }
            return false;
        }
    }

    static final Map<String, Bucket> buckets = new HashMap<>();
    static final Map<String, Integer> rapidFireCount = new HashMap<>();
    static final String CORRECT_PASSWORD = "correct-horse-battery-staple";

    static String attemptLogin(String username, String password, Instant now) {
        Bucket bucket = buckets.computeIfAbsent(username, u -> new Bucket(3, 1.0 / 5.0, now)); // 3 burst, 1 per 5s refill
        if (!bucket.tryConsume(now)) {
            int rapid = rapidFireCount.merge(username, 1, Integer::sum);
            String flag = rapid >= 5 ? " [FLAGGED: sustained rapid-fire pattern -- consider CAPTCHA/alerting]" : "";
            return "429 Too Many Requests -- '" + username + "' rate-limited (retry after ~5s)" + flag;
        }
        boolean success = CORRECT_PASSWORD.equals(password);
        return success ? "200 OK -- login succeeded" : "401 Unauthorized -- wrong password";
    }

    public static void main(String[] args) {
        Instant t = Instant.parse("2026-07-13T00:00:00Z");

        // A legitimate user: mistypes twice, then succeeds, all within a normal pace.
        System.out.println(attemptLogin("alice", "wrong1", t));
        System.out.println(attemptLogin("alice", "wrong2", t.plusSeconds(1)));
        System.out.println(attemptLogin("alice", "correct-horse-battery-staple", t.plusSeconds(2)));

        // An attacker: rapid-fire guesses against a DIFFERENT account, no pauses at all.
        for (int i = 0; i < 6; i++) {
            System.out.println(attemptLogin("bob", "guess" + i, t.plusMillis(i * 50)));
        }

        // Later, after the refill window, bob's bucket has recovered enough for one more try.
        System.out.println(attemptLogin("bob", "guess-later", t.plusSeconds(20)));
    }
}
```

How to run: `java TokenBucketPerAccount.java`

`Bucket.tryConsume` recomputes how many tokens should have refilled since `lastRefill` based on elapsed time, caps at `capacity`, and consumes one token if at least one is available. Alice's three well-paced attempts (a mistype, a mistype, then success) all succeed at the rate-limiting layer, because her bucket never runs dry — this is what distinguishes a real user's normal retry behavior from an automated attack, unlike Level 2's flat count-only limit. Bob's six rapid, sub-second-interval guesses drain his three-token bucket almost immediately, and the remaining attempts are rejected with `429`; once `rapidFireCount` for bob reaches 5, the response is additionally flagged for downstream handling like a CAPTCHA challenge or a security alert — going beyond simple blocking into active abuse detection. Twenty seconds later, bob's bucket has refilled (`20s * (1/5 per s) = 4` tokens, capped at 3), so one further attempt is allowed, showing the limiter recovers over time rather than permanently locking the account out.

## 6. Walkthrough

Trace the `bob` section of `TokenBucketPerAccount.main`. **First**, `buckets.computeIfAbsent("bob", ...)` creates a new `Bucket` with `capacity = 3`, `refillPerSecond = 0.2`, and `tokens = 3` at `t`. The loop runs six times with `i` from 0 to 5, each call at `t.plusMillis(i * 50)` — roughly 50ms apart, far faster than the 5-second refill interval.

**Next**, for `i = 0, 1, 2`: each call to `tryConsume` computes `elapsedSeconds` as a tiny fraction of a second, refills a negligible amount, and finds `tokens >= 1.0` true (starting from 3), so each consumes one token and returns `true` — three attempts succeed at the rate-limit layer (though all still return `401` since none guess the real password). After these three calls, `tokens` is approximately `0`.

**Then**, for `i = 3, 4, 5`: `tryConsume` again computes a negligible refill, finds `tokens < 1.0`, and returns `false` for all three. Each triggers `rapidFireCount.merge("bob", 1, Integer::sum)`, incrementing bob's rapid-fire counter to 1, then 2, then 3 across these three calls — none reach the flag threshold of 5 yet within this loop.

**Finally**, `attemptLogin("bob", "guess-later", t.plusSeconds(20))` runs. `tryConsume` computes `elapsedSeconds = 20`, refills `20 * 0.2 = 4` tokens, capped at `capacity = 3`, so `tokens` becomes `3`, then one is consumed, leaving `2`, and the call returns `true` — bob's bucket has fully recovered after the 20-second gap, and this attempt is processed normally (and fails on password, as expected).

```
200 OK -- login succeeded            (alice, well-paced)
429 ... bob rate-limited (attempts 4-6, no pause)
200 OK / 401 Unauthorized            (bob, 20s later -- bucket refilled)
```

## 7. Gotchas & takeaways

> Rate limiting a login endpoint purely by username can itself be weaponized: an attacker who knows (or guesses) a real username can deliberately trigger the rate limit repeatedly, locking the *legitimate* user out of their own account (a denial-of-service via the security control itself). Combining a per-account limit with a separate, more lenient per-IP limit, and preferring temporary throttling with backoff over hard account lockouts, avoids turning the defense into an attack vector.

- Rate limiting is a security control, not just a reliability one — it's frequently the only defense against brute-force and credential-stuffing attacks against otherwise correctly-authenticated endpoints.
- Token bucket algorithms allow legitimate bursts while still capping sustained rate, which better matches real user behavior than a naive fixed-count-per-window limit.
- Apply limits at multiple keys — per IP, per account, per API key — since each catches a different attack pattern, and combine them so no single key becomes a new denial-of-service vector.
- Return `429 Too Many Requests` with a `Retry-After` header rather than silently dropping requests, so well-behaved clients can back off correctly instead of retrying immediately.
- Rate limiting sits alongside [API keys](0393-api-keys.md) (which give you a stable per-caller key to limit by) and connects to the "Unrestricted Resource Consumption" risk named explicitly in [OWASP API Security Top 10](0398-owasp-api-security-top-10.md).
