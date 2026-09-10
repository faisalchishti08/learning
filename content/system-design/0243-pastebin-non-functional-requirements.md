---
card: system-design
gi: 243
slug: pastebin-non-functional-requirements
title: Pastebin — non-functional requirements
---

## 1. What it is

This page covers the **non-functional requirements (NFRs)** facet of the **Pastebin** case study — the quality targets (scale, latency, availability, consistency, durability) the system must meet, as opposed to what it must do functionally (see [functional requirements](0242-pastebin-functional-requirements.md)).

## 2. Why & when

Pastebin's functional requirements look structurally similar to the URL Shortener's, but the NFRs diverge in one crucial way worth stating up front: paste content itself must be stored durably and served back, at a size per item that can be thousands of times larger than a short URL string — this changes which NFR is the dominant design driver. Define these targets right after functional requirements, since they determine whether a simple database can hold paste content directly or whether a separate large-object storage layer is needed.

## 3. Core concept

- **Scale, and specifically storage volume.** Like the URL Shortener, Pastebin is read-heavy (a popular paste is viewed far more often than it is created), but unlike the URL Shortener, each stored item can be substantial (up to FR-3's configured maximum, e.g. 1 MB) rather than a few hundred bytes — this makes total storage volume, not just record count, a first-class capacity concern.
- **Latency.** Both paste creation and paste retrieval are on a user's direct, active critical path (someone is actively waiting to see their pasted content, or to get their shareable link) — unlike the URL Shortener, where creation is less latency-sensitive than the passive redirect click, Pastebin's creation latency matters nearly as much as its retrieval latency, since both are actively-awaited actions.
- **Availability.** The retrieval path should be highly available, mirroring the URL Shortener's redirect-path reasoning — a shared paste link that stops resolving breaks every place it was shared, exactly as a broken short URL would.
- **Consistency.** A newly created paste does not need to be visible from every server instantly — the same brief eventual-consistency window the URL Shortener accepted applies here, since nobody views a paste before it has been shared.
- **Durability.** Once created, a paste's content must not be lost, for as long as its expiration setting (FR-4) says it should exist — this durability requirement is more consequential here than for the URL Shortener, since losing a paste means losing the user's actual content, not just a pointer to content that still exists elsewhere.

## 4. Diagram

```
                    STRICT <-----------------------------> RELAXED

   DURABILITY   |  a created paste's actual CONTENT       |
                |  must not be lost before its              |
                |  expiration (strict: this is the           |
                |  ORIGINAL data, not a pointer)               |

   LATENCY      |  both creation AND retrieval matter -     |
                |  creation is actively awaited too,          |
                |  unlike the URL Shortener's passive click    |
                |  (stricter on creation than URL Shortener)     |

   AVAILABILITY |  retrieval path must stay up                 |

   CONSISTENCY  |                                    | a new paste need not
                |                                    | be visible everywhere
                |                                    | INSTANTLY (relaxed,
                |                                    | same as URL Shortener)
```
*Caption: durability sits even more strictly than the URL Shortener's, since Pastebin stores original content rather than a pointer; creation latency is stricter here too, since a user is actively waiting on it.*

## 5. Runnable example

### Measurable NFR targets

```text
SCALE
  NFR-1: Assume a read:write ratio of roughly 10:1 (views : pastes created)
         - lower than the URL Shortener's 100:1, since a typical paste is
         viewed by a smaller, more targeted audience than a shared link
         that can go viral.
  NFR-2: Design for 1 million new pastes created per day, average size
         10 KB (derived further in capacity estimation).

LATENCY
  NFR-3: Paste creation (POST text -> paste ID): p99 < 200 ms.
  NFR-4: Paste retrieval (GET paste ID -> text): p99 < 150 ms.

AVAILABILITY
  NFR-5: Retrieval path: 99.95% uptime.
  NFR-6: Creation path: 99.9% uptime (slightly lower target, though closer
         to retrieval's than the URL Shortener's creation/redirect gap,
         since creation here is also actively awaited).

CONSISTENCY
  NFR-7: Eventual consistency is acceptable: a newly created paste may
         take up to a few seconds to become retrievable from every region.

DURABILITY
  NFR-8: Once a paste's creation is acknowledged, its content must not be
         lost before its configured expiration, even across a single data
         center failure (durability target: 99.999999999%, matching
         typical object-storage guarantees).
```

## 6. Walkthrough

1. **NFR-1 (10:1 read:write, lower than the URL Shortener's 100:1) is worth stating explicitly as a real difference, not an oversight.** A paste is typically shared with a specific, smaller audience (a coworker debugging a stack trace, a small group reviewing a config file) rather than a link posted publicly and clicked by anyone — this lower ratio still justifies caching, but less aggressively than the URL Shortener's architecture needed.
2. **NFR-3 and NFR-4 (creation and retrieval latency both stricter and closer together) directly reflect FR-1/FR-2's nature**: a user pasting text is actively watching for their shareable link to appear, unlike a URL Shortener creator who can tolerate a slightly slower response since they are filling out a form, not staring at a spinner mid-share. This is a genuine, stated difference from the URL Shortener's NFR reasoning, not a copy-paste of the same numbers.
3. **NFR-5 and NFR-6 (availability, both high, with a smaller gap than the URL Shortener's) again reflect that both paths here matter to an actively-waiting user** — the URL Shortener could justify a bigger availability gap between redirect (visible to a passive random visitor) and creation (visible only to the creator); Pastebin's smaller gap acknowledges both operations matter comparably.
4. **NFR-8 (durability) is the NFR most changed by Pastebin's core structural difference from the URL Shortener.** The URL Shortener's database durability protected a *pointer* — losing it broke a link, but the original long URL still existed wherever it was originally hosted. Here, losing a paste's stored content means the content itself is gone; there is no other copy anywhere else in the world, which is exactly why this facet calls out durability as "more consequential" in Part 3, not merely restating the URL Shortener's equivalent target.
5. **NFR-7 (eventual consistency, same relaxation as the URL Shortener) still holds for the same underlying reason**: nobody views a paste before it has been shared, so a brief window where a freshly created paste is not yet visible from every region causes no real user-facing problem — this is one NFR that transfers directly from the URL Shortener case study without needing to be rethought.

## 7. Gotchas & takeaways

> **Gotcha:** it is tempting to copy the URL Shortener's NFR numbers wholesale for Pastebin, since the two case studies look structurally similar on the surface — but doing so would understate Pastebin's durability requirement (content, not a pointer, is at stake) and overstate its read:write skew (a smaller, more targeted audience per paste than a viral short link). Always re-derive NFRs from the specific system's actual functional requirements and usage pattern, even when reusing a similar case study's method.

- Put a number on every NFR, exactly as with the URL Shortener — but do not assume the numbers themselves transfer; Pastebin's durability, read:write ratio, and creation-latency targets all differ meaningfully from that case study's, for reasons traceable directly to FR-1/FR-2's structural difference.
- The strict durability target (NFR-8) is the single most important NFR to carry forward into [capacity estimation](0244-pastebin-capacity-estimation.md) and [high-level architecture](0246-pastebin-high-level-architecture.md) — it is what will justify storing paste content in durable object storage, not just a database row.
- Both creation and retrieval latency matter comparably here (NFR-3/NFR-4), unlike the URL Shortener's more lopsided targets — this shapes an architecture that cannot treat creation as a "cheaper" path the way that case study could.
- See [Pastebin — capacity estimation](0244-pastebin-capacity-estimation.md) next, where NFR-2's scale numbers and the larger average item size get turned into concrete QPS and storage figures.
