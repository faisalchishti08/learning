---
card: system-design
gi: 224
slug: url-shortener-functional-requirements
title: URL Shortener — functional requirements
---

## 1. What it is

This page covers the **functional requirements** facet of the **URL Shortener** system-design case study — a service like bit.ly that turns a long URL into a short one, and redirects visitors from the short URL back to the original. Functional requirements are the concrete things the system must actually do, as opposed to how fast or reliable it must do them (that is [non-functional requirements](0225-url-shortener-non-functional-requirements.md), a separate facet).

## 2. Why & when

Every other facet of this case study — [capacity estimation](0226-url-shortener-capacity-estimation.md), [API design](0227-url-shortener-api-design.md), [architecture](0228-url-shortener-high-level-architecture.md) — depends on first knowing exactly what the system must do. Skipping straight to architecture without nailing down requirements is how designs end up solving the wrong problem, or gold-plating features nobody asked for. Start any system-design exercise here, and use these requirements as the checklist every later design decision must trace back to.

## 3. Core concept

Prioritize using **MoSCoW** (Must / Should / Could) so scope stays deliberate, not accidental:

- **Must have:**
  - Given a long URL, generate a unique short URL (e.g. `https://short.ly/aZ9kLp`).
  - Given a short URL, redirect the visitor to the original long URL.
  - Short URLs must remain valid and resolve correctly for as long as the system exists (or until explicitly deleted/expired).
- **Should have:**
  - Let a user choose a **custom alias** for their short URL (e.g. `short.ly/my-sale`), subject to availability.
  - Support an **expiration date** on a short URL, after which it no longer redirects.
  - Track basic **click analytics** per short URL (total clicks, and ideally clicks over time).
- **Could have:**
  - Let a registered user manage (view, edit, delete) the set of short URLs they created.
  - Support rate limiting per user/API key to prevent abuse (link-shortening spam).
- **Explicitly out of scope for this case study:**
  - User authentication/account systems beyond what is needed to associate a URL with its creator.
  - Detailed analytics dashboards (geolocation, referrer breakdowns) — only basic click counts are in scope.
  - Content moderation of the URLs being shortened.

## 4. Diagram

```
        +-----------------+                          +-----------------+
        |   Anonymous /    |                          |   Any visitor    |
        |   registered user |                          |  (no account)   |
        +--------+---------+                          +--------+--------+
                 |                                              |
      "shorten a long URL"                            "visit a short URL"
      "set custom alias" (should)                       (redirect to original)
      "set expiration" (should)                                |
                 |                                              |
                 v                                              v
        +------------------------------------------------------------+
        |                     URL Shortener System                    |
        +------------------------------------------------------------+
                 ^
                 |
      "view click analytics" (should)
      "manage my URLs" (could)
```
*Caption: two actors drive this system — the person creating short URLs and the visitor following one. Most "should"/"could" requirements belong to the creator; the "must have" redirect belongs to any visitor.*

## 5. Runnable example

### Requirements list (numbered, for direct reference by later facet pages)

```text
MUST HAVE
  FR-1: Given a long URL, the system creates a unique short URL.
  FR-2: Given a valid short URL, the system redirects the visitor to the
        original long URL.
  FR-3: A short URL remains resolvable indefinitely, unless it has expired
        or been explicitly deleted.

SHOULD HAVE
  FR-4: A user may supply a custom alias instead of a system-generated code,
        if that alias is not already taken.
  FR-5: A user may set an expiration date/time on a short URL.
  FR-6: The system records a click count each time a short URL is visited.

COULD HAVE
  FR-7: A registered user can list, view, and delete the short URLs they created.
  FR-8: The system rate-limits URL creation per API key to deter abuse.

OUT OF SCOPE
  - Full account/auth system (only a minimal creator-association is assumed).
  - Rich analytics (geolocation, referrer breakdown, device type).
  - Content moderation / malicious-URL scanning.
```

## 6. Walkthrough

1. **FR-1 and FR-2 are the reason this system exists** — every other requirement supports or extends this core create-then-redirect loop. Any design that cannot satisfy these two trivially first is not a viable URL shortener, regardless of how well it satisfies the rest.
2. **FR-3 has a direct design implication**: because short URLs must stay valid indefinitely by default, the system cannot silently evict old mappings to save storage — this requirement is exactly what forces the [capacity estimation](0226-url-shortener-capacity-estimation.md) facet to plan for unbounded growth over years, not a rolling window.
3. **FR-4 (custom alias) changes the [key generation](0230-url-shortener-deep-dive-unique-key-generation-collisions.md) approach**: a purely random or sequential key generator does not need to check for a pre-existing key requested by name, but a custom-alias feature does — the system must check availability and reject a conflicting request, which purely auto-generated keys never need to handle.
4. **FR-5 (expiration) affects the [data model](0229-url-shortener-data-model-schema.md)**: the schema needs an `expires_at` field, and the redirect path (FR-2) must check it on every lookup, adding a comparison that a system without expiration would not need.
5. **FR-6 (click analytics) affects the [architecture](0228-url-shortener-high-level-architecture.md)**: recording a click on every redirect is a write on the system's hottest path (redirects vastly outnumber creations in a typical URL shortener), which pushes the design toward an asynchronous, non-blocking way to record clicks rather than a synchronous database write in the redirect's critical path.

## 7. Gotchas & takeaways

> **Gotcha:** treating "should have" and "could have" requirements as equally urgent as "must have" ones is a common mistake that bloats early design discussions. Nail down FR-1 through FR-3 first, and let every later facet page build outward from those — custom aliases, expiration, and analytics are real requirements, but they are additions on top of a working core, not prerequisites for it.

- Every functional requirement here should be traceable to a specific decision in a later facet page — if a requirement does not influence any later design choice, question whether it belongs in scope at all.
- MoSCoW prioritization is not just documentation — "must have" items get designed first and are the parts of the system that absolutely cannot fail; "could have" items can be deferred or simplified under time pressure without compromising the system's core purpose.
- Explicitly listing out-of-scope items is as valuable as listing in-scope ones — it prevents scope creep during later design discussions and interview-style walkthroughs.
- See [URL Shortener — non-functional requirements](0225-url-shortener-non-functional-requirements.md) next for the quality targets (scale, latency, availability) these functional requirements must be delivered under.
