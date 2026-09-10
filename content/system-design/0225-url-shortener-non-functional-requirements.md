---
card: system-design
gi: 225
slug: url-shortener-non-functional-requirements
title: URL Shortener — non-functional requirements
---

## 1. What it is

This page covers the **non-functional requirements (NFRs)** facet of the **URL Shortener** case study — the quality targets the system must meet (scale, latency, availability, consistency, durability) as opposed to what it must do functionally (see [functional requirements](0224-url-shortener-functional-requirements.md), a separate facet).

## 2. Why & when

Functional requirements say "redirect a short URL to its original." Non-functional requirements say "...within 100 milliseconds, 99.99% of the time, even under 10,000 redirects per second." Without explicit NFRs, "the redirect works" could mean anything from a snappy sub-100ms response to a barely-acceptable 3-second one — both technically satisfy the functional requirement, but only one is a viable production system. Define NFRs right after functional requirements, before any architecture decision, because they directly determine which architecture choices (caching, replication, consistency model) are even necessary.

## 3. Core concept

- **Scale.** A URL shortener is a classic **read-heavy** system: redirects (reads) vastly outnumber URL creations (writes) — a common assumption is 100:1 or higher, since one shortened link can be clicked thousands of times. This read-heavy skew is the single most important NFR, because it points directly at caching as the dominant design lever.
- **Latency.** Redirects sit on the critical path of someone's click — a slow redirect is a visibly broken experience. Target a low, consistent latency for the redirect path specifically; URL creation can tolerate somewhat higher latency since it happens far less often and is not on a passive visitor's critical path.
- **Availability.** The redirect path should be highly available — a URL shortener that is down means every previously shared short link stops working system-wide, which is highly visible and damaging. Availability targets are usually expressed as a percentage of uptime (e.g. "four nines," 99.99%).
- **Consistency.** A newly created short URL does not need to be instantly visible from every server worldwide — a short window of **eventual consistency** immediately after creation is acceptable, since nobody clicks a link before it has been shared. This relaxed consistency requirement is what makes aggressive caching and replication viable without hurting the user experience.
- **Durability.** Once a short URL is created, its mapping must not be lost — losing it breaks every previously shared link pointing at it, silently and permanently. Durability requirements are strict even though consistency requirements are relaxed; these are two different, independent axes.

## 4. Diagram

```
                    STRICT <-----------------------------> RELAXED

   DURABILITY   |  a created mapping must NEVER be lost  |
                |  (strict: replicate writes durably)     |

   AVAILABILITY |  redirect path must stay up             |
                |  (strict: multi-AZ, no single point       |
                |   of failure on the read path)             |

   LATENCY      |  redirect must be fast (e.g. < 100ms p99)   |
                |  (strict on reads, relaxed on writes)         |

   CONSISTENCY  |                                    | a new URL need not be
                |                                    | visible everywhere
                |                                    | INSTANTLY (relaxed:
                |                                    | eventual consistency
                |                                    | is fine post-creation)
```
*Caption: durability, availability, and read-latency sit on the strict end for this system; consistency deliberately sits on the relaxed end — that asymmetry is what makes the whole design tractable.*

## 5. Runnable example

### Measurable NFR targets

```text
SCALE
  NFR-1: Assume a read:write ratio of at least 100:1 (redirects : creations).
  NFR-2: Design for 100 million new short URLs created per month, and a
         total of 10 billion redirects served per month (derived further in
         capacity estimation).

LATENCY
  NFR-3: Redirect (GET short URL -> 301/302 to original): p99 < 100 ms.
  NFR-4: URL creation (POST long URL -> short URL): p99 < 300 ms.

AVAILABILITY
  NFR-5: Redirect path: 99.99% uptime ("four nines," ~52 minutes of
         downtime per year).
  NFR-6: URL creation path: 99.9% uptime (a brief creation outage is far
         less damaging than a redirect outage, since it affects new links
         only, not links already shared).

CONSISTENCY
  NFR-7: Eventual consistency is acceptable: a newly created short URL may
         take up to a few seconds to become resolvable from every region.

DURABILITY
  NFR-8: Once a short URL creation is acknowledged to the client, its
         mapping must not be lost, even in the event of a single data
         center failure (durability target: 99.999999999%, "11 nines",
         matching typical object-storage durability guarantees).
```

## 6. Walkthrough

1. **NFR-1 (read:write ratio) is the single most consequential number on this page.** It justifies putting a cache in front of the database for redirects (see [high-level architecture](0228-url-shortener-high-level-architecture.md)) — caching a small hot set of frequently-clicked URLs can absorb the overwhelming majority of read traffic, while writes stay infrequent enough to hit the database directly without a caching layer.
2. **NFR-3 vs. NFR-4 (redirect latency stricter than creation latency)** directly reflects who is waiting on each operation: a visitor clicking a link is a passive, unannounced wait that feels broken if slow; a user creating a short URL is actively submitting a form and tolerates a little more latency without the experience feeling broken.
3. **NFR-5 vs. NFR-6 (redirect availability stricter than creation availability)** follows from the same asymmetry as functional requirement FR-3: every short URL, once created, may be shared and clicked for years. An outage in the creation path affects only new link creation during that window; an outage in the redirect path breaks every previously shared link, everywhere, simultaneously — a far larger blast radius, which is why it gets the stricter target.
4. **NFR-7 (eventual consistency is acceptable) is what makes NFR-5's strict availability target achievable at all.** If every redirect had to check a single strongly-consistent source of truth, that source becomes a bottleneck and a single point of failure under NFR-1's read-heavy load. Accepting a brief consistency window after creation lets the design replicate and cache aggressively, trading strict consistency for the availability and latency the redirect path actually needs.
5. **NFR-8 (durability) is deliberately independent of NFR-7 (consistency).** A short URL's mapping being briefly *inconsistent* across replicas right after creation is fine; that same mapping being *lost* entirely is not — durability is about never losing acknowledged data, while consistency is about how quickly all replicas agree on it. Conflating the two is a common design mistake this page's separation is meant to prevent.

## 7. Gotchas & takeaways

> **Gotcha:** treating "eventually consistent" as license to be sloppy about durability is a real design trap. A system can be eventually consistent (replicas catch up over time) while still being fully durable (no acknowledged write is ever lost) — these targets pull in different directions and must each be designed for explicitly, not assumed to come together.

- Put a number on every NFR — "fast" and "highly available" are not targets you can design against or test; "p99 < 100ms" and "99.99% uptime" are.
- The read-heavy skew (NFR-1) is the NFR that most directly drives the [high-level architecture](0228-url-shortener-high-level-architecture.md)'s use of caching — trace that decision back to this specific number when explaining the design.
- Relaxed consistency (NFR-7) paired with strict durability (NFR-8) is a deliberate, common combination for systems like this — do not assume relaxing one requirement means relaxing all of them.
- See [URL Shortener — capacity estimation](0226-url-shortener-capacity-estimation.md) next, where NFR-2's scale numbers get turned into concrete QPS, storage, and bandwidth figures.
