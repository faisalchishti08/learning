---
card: system-design
gi: 242
slug: pastebin-functional-requirements
title: Pastebin — functional requirements
---

## 1. What it is

This page covers the **functional requirements** facet of the **Pastebin** system-design case study — a service like pastebin.com where a user pastes a block of text, receives a shareable link, and anyone with that link can view the text. Functional requirements are the concrete things the system must do, as opposed to how fast or reliable (a separate facet, [non-functional requirements](0243-pastebin-non-functional-requirements.md)).

## 2. Why & when

Pastebin shares real structural DNA with the [URL Shortener](0224-url-shortener-functional-requirements.md) case study — both generate a short, unique identifier that maps to stored content, and both serve that content back on request — but Pastebin stores the content itself (not just a pointer to it elsewhere), which changes the storage and capacity picture significantly. Nailing down the exact functional requirements first is what reveals this difference clearly, rather than assuming Pastebin is "just a URL shortener for text."

## 3. Core concept

Prioritize using **MoSCoW** (Must / Should / Could):

- **Must have:**
  - Given a block of text, store it and return a unique, shareable link (a "paste ID").
  - Given a paste ID, retrieve and display the original text exactly as submitted.
  - Support a reasonable maximum paste size (e.g. up to a few megabytes of text).
- **Should have:**
  - Support an **expiration** setting on a paste (never, 10 minutes, 1 day, 1 week), after which the content is no longer retrievable.
  - Support **syntax highlighting** hints (the user indicates the content is a specific programming language, and the display applies highlighting).
  - Support a **"burn after reading"** option — the paste is permanently deleted after its first view.
- **Could have:**
  - Let a registered user view a history of pastes they created.
  - Support **private/unlisted pastes** distinguishable from ones intended to be publicly discoverable.
  - Support editing a paste to create a new version, with a link to the version history.
- **Explicitly out of scope for this case study:**
  - Full user account/authentication system beyond associating a paste with its creator.
  - Real-time collaborative editing of a paste (multiple users editing simultaneously).
  - Content moderation or scanning of pasted content.

## 4. Diagram

```
        +-----------------+                          +-----------------+
        |   Anonymous /     |                          |   Any visitor    |
        |   registered user  |                          |  with a link     |
        +--------+----------+                          +--------+--------+
                 |                                              |
      "paste text, get a shareable link"                "view a paste by its link"
      "set expiration" (should)                                 |
      "burn after reading" (should)                              |
      "syntax highlighting hint" (should)                         |
                 |                                              |
                 v                                              v
        +------------------------------------------------------------+
        |                       Pastebin System                        |
        +------------------------------------------------------------+
                 ^
                 |
      "view my paste history" (could)
```
*Caption: the core loop mirrors the URL Shortener's create-then-resolve pattern, but here the system stores the actual content rather than just redirecting to a URL stored elsewhere.*

## 5. Runnable example

### Requirements list

```text
MUST HAVE
  FR-1: Given a block of text, the system stores it and returns a unique
        paste ID / shareable link.
  FR-2: Given a valid paste ID, the system returns the original text
        exactly as submitted.
  FR-3: The system enforces a maximum paste size (e.g. 1 MB, configurable).

SHOULD HAVE
  FR-4: A user may set an expiration on a paste (never / 10 min / 1 day /
        1 week); an expired paste is no longer retrievable.
  FR-5: A user may indicate the content's language, applied as a syntax-
        highlighting hint on display.
  FR-6: A user may mark a paste "burn after reading" - it is permanently
        deleted immediately after its first successful view.

COULD HAVE
  FR-7: A registered user can view a list of pastes they created.
  FR-8: A paste can be marked private/unlisted (not indexed or listed
        publicly, but still viewable via its direct link).
  FR-9: Editing a paste creates a new version, linked to its history.

OUT OF SCOPE
  - Full account/auth system (minimal creator-association only).
  - Real-time collaborative editing.
  - Content moderation / malicious-content scanning.
```

## 6. Walkthrough

1. **FR-1 and FR-2 define the core loop, structurally similar to the URL Shortener's FR-1/FR-2** — but note the key difference stated in Part 2: here the system stores and later returns the *actual content*, not a redirect to content stored elsewhere. This single difference is what the [capacity estimation](0244-pastebin-capacity-estimation.md) facet will show drives a fundamentally larger storage requirement than the URL Shortener ever had.
2. **FR-3 (a maximum paste size) exists specifically because storing full content, unlike storing a short URL string, has no natural upper bound** — a paste could otherwise be arbitrarily large, which would make both storage and bandwidth planning impossible. This requirement did not need an equivalent in the URL Shortener case study, since a URL has a practically-bounded realistic length already.
3. **FR-4 (expiration) directly affects the [data model](0247-pastebin-data-model-schema.md)** the same way the URL Shortener's equivalent requirement did — an `expires_at` field, checked on every retrieval.
4. **FR-6 (burn after reading) has a unique implication this case study did not need before**: retrieval (FR-2) is no longer a pure read — for a burn-after-reading paste, a `GET` request also triggers a delete, meaning the [API design](0245-pastebin-api-design.md) facet must grapple with a read endpoint that is not [idempotent](0210-idempotency-safe-methods.md) for this specific paste type, a genuinely interesting design wrinkle worth flagging explicitly.
5. **FR-5 (syntax highlighting hint) is a display concern, not a storage or retrieval concern** — the system only needs to store the language tag alongside the content and pass it through on retrieval; the actual highlighting logic runs client-side and is out of this system's own scope, similar to how the URL Shortener case study kept analytics dashboards explicitly out of scope while still tracking the underlying click data.

## 7. Gotchas & takeaways

> **Gotcha:** FR-6 (burn after reading) quietly breaks the assumption that `GET /pastes/{id}` is a safe, [idempotent](0210-idempotency-safe-methods.md) operation — a browser prefetching a link, a link-preview bot, or a user accidentally double-clicking could all trigger the "burn" prematurely, before the intended reader ever sees the content. This must be called out explicitly during API design, not discovered after the fact.

- FR-1 and FR-2 form the non-negotiable core, exactly as in the [URL Shortener](0224-url-shortener-functional-requirements.md) case study — every later facet builds outward from a working create-then-retrieve loop.
- The single structural difference from the URL Shortener (storing content directly, not a pointer) is small to state but has large downstream consequences — trace it through [capacity estimation](0244-pastebin-capacity-estimation.md) and [data model & schema](0247-pastebin-data-model-schema.md) to see exactly where it changes the design.
- FR-6's non-idempotent read is a genuinely interesting requirement worth flagging early, since it affects API design decisions (like whether prefetching or link-preview bots need special handling) that a purely read-only system would never need to consider.
- See [Pastebin — non-functional requirements](0243-pastebin-non-functional-requirements.md) next for the scale, latency, and durability targets these functional requirements must be delivered under.
