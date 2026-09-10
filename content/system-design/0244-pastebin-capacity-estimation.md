---
card: system-design
gi: 244
slug: pastebin-capacity-estimation
title: Pastebin — capacity estimation
---

## 1. What it is

This page covers the **capacity estimation** facet of the **Pastebin** case study — turning the scale targets from [non-functional requirements](0243-pastebin-non-functional-requirements.md) into concrete QPS, storage, and bandwidth numbers, following the same method as the [URL Shortener's estimation](0226-url-shortener-capacity-estimation.md), but with a much larger per-item size that changes the resulting storage conclusion significantly.

## 2. Why & when

The [non-functional requirements](0243-pastebin-non-functional-requirements.md) flagged that Pastebin stores actual content (average 10 KB per paste) rather than a short pointer string — this facet is where that difference becomes visible as a genuinely different storage total, directly shaping whether the [high-level architecture](0246-pastebin-high-level-architecture.md) needs a dedicated large-object storage layer.

## 3. Core concept

The estimation method is unchanged from the [URL Shortener's](0226-url-shortener-capacity-estimation.md): monthly totals → average QPS → peak QPS → storage per day and projected forward → bandwidth. What differs here is the *inputs* — a much larger average item size — which is exactly what makes the resulting storage total worth comparing side by side with that case study's.

## 4. Diagram

```
   monthly totals (pastes created, views)
        |
        v
   divide by seconds/month (~2.6M)  --> average QPS
        |
        v
   multiply by peak factor (2-3x)   --> peak QPS
        |
        v
   AVERAGE PASTE SIZE (10 KB) x pastes/day  --> storage per day
        |                                        (this is where Pastebin
        v                                         diverges sharply from the
   storage/day x 365 x retention yrs           URL Shortener's ~500-byte
        --> total storage                       record size)
        |
        v
   QPS x avg payload size  --> bandwidth (read + write)
```
*Caption: the chain is identical to the URL Shortener's; only the per-item size assumption changes — and that single number is what turns a comfortably-small total into one requiring real architectural planning.*

## 5. Runnable example

### Worked calculation

```text
ASSUMPTIONS
  - New pastes created per day:      1,000,000  (1M, per NFR-2)
  - Views per day: 10x creations (per NFR-1's 10:1 ratio) = 10,000,000
  - Average paste size: 10 KB (per NFR-2) - note: FR-3 caps a single
    paste at up to 1 MB, but 10 KB is a realistic AVERAGE across most
    pastes (typically short code snippets or log excerpts).
  - Retention: variable per FR-4 (some pastes never expire); estimate
    2 years forward for a concrete storage number, acknowledging this
    is a rougher estimate than the URL Shortener's "unbounded" case,
    since expiring pastes continuously free up space.
  - Peak-to-average multiplier: 3x, same as the URL Shortener's assumption.

STEP 1: seconds per day
  24 hours x 3600 seconds = 86,400 seconds/day

STEP 2: average QPS
  writes (pastes created): 1,000,000 / 86,400  ~=  12 QPS average
  reads  (views):          10,000,000 / 86,400  ~=  116 QPS average

STEP 3: peak QPS (x3 multiplier)
  writes: 12 x 3   ~=  36 QPS peak
  reads:  116 x 3  ~=  347 QPS peak

  (compare to the URL Shortener's ~11,574 peak read QPS - Pastebin's QPS
  numbers are far LOWER, since NFR-1's 10:1 ratio and smaller absolute
  scale both pull in that direction)

STEP 4: storage per day, and over 2 years
  storage/day = 1,000,000 pastes/day x 10 KB  ~=  10,000,000 KB  ~=  ~10 GB/day
  storage over 2 years = 10 GB/day x 365 x 2  ~=  7,300 GB  ~=  ~7.3 TB total

  (compare to the URL Shortener's ~3 TB over 5 years - Pastebin accumulates
  MORE total storage in LESS time, despite far fewer QPS, purely because
  each stored item is roughly 20x larger)

STEP 5: bandwidth
  write bandwidth (peak): 36 QPS x 10 KB  ~=  360 KB/s
  read bandwidth (peak):  347 QPS x 10 KB  ~=  3,470 KB/s  ~=  ~3.4 MB/s

SUMMARY
  - Peak read QPS to design for:  ~350 QPS (far lower than URL Shortener)
  - Peak write QPS to design for: ~36 QPS
  - Total storage over 2 years:   ~7.3 TB (LARGER than URL Shortener's
                                    5-year total, despite far lower QPS -
                                    this is the key insight this
                                    estimation surfaces)
  - Peak bandwidth:               ~3.8 MB/s combined
```

## 6. Walkthrough

1. **Steps 1-3 follow the exact same mechanical process as the [URL Shortener's estimation](0226-url-shortener-capacity-estimation.md)**, and the resulting QPS numbers (~347 peak reads, ~36 peak writes) come out **far lower** than that case study's (~11,574 peak reads) — a direct consequence of NFR-1's more modest 10:1 ratio and this system's smaller absolute daily volume (1M pastes/day here vs. the URL Shortener's ~3.3M new URLs/day).
2. **Step 4 is where this estimation earns its keep as a distinct exercise, not a copy of the URL Shortener's math.** Multiplying 1,000,000 pastes/day by an average size of 10 KB (not ~500 bytes) gives roughly 10 GB/day — already 6x the URL Shortener's entire *daily* storage growth rate from a system creating 33x more records per day. The average item size, not record count, is what dominates here.
3. **Projected over 2 years (a shorter window than the URL Shortener's 5-year projection, chosen because Pastebin's expiring content continuously frees space), the total comes to roughly 7.3 TB** — genuinely larger than the URL Shortener's entire 5-year total of ~3 TB, despite Pastebin's dramatically lower QPS. This is the single most important conclusion of this estimation: **QPS and storage volume are independent axes**, and a system can be "easy" on one and "hard" on the other.
4. **This directly shapes the [high-level architecture](0246-pastebin-high-level-architecture.md) facet's key decision**: while the URL Shortener could comfortably store its ~500-byte records directly in a normal database row, Pastebin's 10 KB average (with a FR-3-permitted maximum of up to 1 MB) pushes the design toward storing paste content in dedicated large-object/blob storage, with the database holding only metadata and a reference to the blob — a genuinely different architectural shape, directly traceable to this specific number.
5. **Step 5's bandwidth figure (~3.8 MB/s combined) remains modest**, similar in spirit to the URL Shortener's conclusion that bandwidth was not the binding constraint — for Pastebin, the binding constraint that this estimation surfaces is specifically **storage volume**, not QPS and not bandwidth, a distinctly different profile from either of the two case studies before it in this series.

## 7. Gotchas & takeaways

> **Gotcha:** it is easy to look at Pastebin's much lower QPS numbers (Step 3) relative to the URL Shortener and conclude the whole system is "simpler" or "smaller" — but Step 4's storage total tells a different, more important story. Always compute every dimension (QPS, storage, bandwidth) independently rather than assuming a lower number on one axis means a system is easier across the board.

- The defining number for this system's capacity picture is **average item size** (10 KB), not request rate — this single assumption is what should be scrutinized hardest if this estimate needs revisiting, since it propagates directly into the storage total that drives the architecture's biggest decision.
- Pastebin's total storage over 2 years (~7.3 TB) exceeds the URL Shortener's over 5 years (~3 TB) despite dramatically lower QPS — cite this specific comparison when explaining why the two case studies, despite similar functional requirements, land on meaningfully different architectures.
- A shorter retention projection window (2 years, vs. the URL Shortener's 5) is a reasonable adjustment here, since FR-4's expiration options mean this system's storage genuinely does not grow unbounded the way the URL Shortener's (mostly permanent) links do — state this kind of assumption difference explicitly rather than reusing a prior estimate's window out of habit.
- See [Pastebin — API design](0245-pastebin-api-design.md) next for the concrete endpoints that implement FR-1 through FR-6, informed by this facet's size and rate numbers.
