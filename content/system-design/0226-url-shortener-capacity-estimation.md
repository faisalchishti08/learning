---
card: system-design
gi: 226
slug: url-shortener-capacity-estimation
title: URL Shortener — capacity estimation
---

## 1. What it is

This page covers the **capacity estimation** facet of the **URL Shortener** case study — turning the scale targets from [non-functional requirements](0225-url-shortener-non-functional-requirements.md) into concrete numbers: queries per second (QPS), storage needed per day and over years, and bandwidth. These numbers drive real design decisions later, like whether a single database can handle the load or whether sharding is required.

## 2. Why & when

An architecture designed without capacity numbers is just a guess dressed up as a diagram — you cannot know if a single database instance is enough, or if you need caching, replication, or sharding, without first knowing the actual scale you are designing for. Capacity estimation turns "it needs to be fast and scalable" into specific numbers you can check any later design decision against. Do this right after non-functional requirements are set, and before drawing any architecture.

## 3. Core concept

The estimation method is a chain of back-of-envelope calculations, each one derived from the previous, with assumptions stated explicitly at every step:

1. Start from the **monthly active scale** given in the non-functional requirements (100 million new URLs/month, 10 billion redirects/month).
2. Convert monthly totals to **average QPS** by dividing by the number of seconds in a month (~2.6 million).
3. Estimate **peak QPS** by applying a peak-to-average multiplier (commonly 2-3x for a system without an extreme, predictable single spike).
4. Estimate **storage per record**, multiply by records per day, and project forward across the retention period (here, unbounded, so project across several years) to size total storage.
5. Estimate **bandwidth** from request/response size and QPS, for both the write path (creation) and the read path (redirect).

## 4. Diagram

```
   monthly totals
        |
        v
   divide by seconds/month (~2.6M)  --> average QPS
        |
        v
   multiply by peak factor (2-3x)   --> peak QPS
        |
        v
   record size x records/day        --> storage per day
        |
        v
   storage/day x 365 x retention yrs --> total storage
        |
        v
   QPS x avg payload size            --> bandwidth (read + write, separately)
```
*Caption: each estimate is derived from the one before it — changing an assumption at the top (e.g. monthly URL creations) propagates through every number below it.*

## 5. Runnable example

### Worked calculation

```text
ASSUMPTIONS
  - New URLs created per month:      100,000,000  (100M)
  - Redirects served per month:      10,000,000,000  (10B)
  - Average short-URL record size:   ~500 bytes (URL text, short code, metadata,
                                      timestamps - rounded up for indexes/overhead)
  - Average redirect response size:  ~300 bytes (HTTP 301 + Location header,
                                      negligible body)
  - Retention: unbounded (URLs kept indefinitely per FR-3); estimate 5 years
    forward for a concrete storage number.
  - Peak-to-average multiplier: 3x (no single predictable mega-spike assumed,
    but real-world traffic is bursty, not perfectly flat).

STEP 1: seconds per month
  30 days x 24 hours x 3600 seconds = 2,592,000 seconds/month (~2.6M)

STEP 2: average QPS
  writes (creations):  100,000,000 / 2,592,000  ~=  39 QPS average
  reads  (redirects):  10,000,000,000 / 2,592,000  ~=  3,858 QPS average

STEP 3: peak QPS (x3 multiplier)
  writes: 39 x 3        ~=  117 QPS peak
  reads:  3,858 x 3      ~=  11,574 QPS peak      <- this is the number the
                                                      redirect path must be
                                                      designed to sustain

STEP 4: storage per day, and over 5 years
  new records/day = 100,000,000 / 30  ~=  3,333,333 records/day
  storage/day = 3,333,333 x 500 bytes ~=  1.67 GB/day
  storage over 5 years = 1.67 GB/day x 365 x 5  ~=  3,047 GB  ~=  ~3 TB total

STEP 5: bandwidth
  write bandwidth (peak): 117 QPS x (long URL avg ~150 bytes + short code
                            + metadata ~500 bytes total) ~= ~58.5 KB/s
  read bandwidth (peak):  11,574 QPS x 300 bytes ~= ~3.47 MB/s

SUMMARY
  - Peak read QPS to design for:  ~11,600 QPS
  - Peak write QPS to design for: ~120 QPS
  - Total storage over 5 years:   ~3 TB (fits comfortably on a single
                                    well-provisioned database, or a small
                                    number of shards)
  - Peak read bandwidth:          ~3.5 MB/s (trivially served by a cache)
```

## 6. Walkthrough

1. **Step 1 converts the NFR's monthly figures into a per-second time base**, since QPS (not monthly totals) is the unit that actually determines what a single server or database must sustain. This conversion is mechanical, but skipping it is the most common estimation mistake — comparing a monthly total directly against a server's request-per-second capacity gives a meaningless number.
2. **Step 2 divides each monthly total by seconds-per-month**, producing average QPS: ~39 writes/sec and ~3,858 reads/sec. The read number being roughly 100x the write number is exactly the read:write ratio assumed in [non-functional requirements](0225-url-shortener-non-functional-requirements.md)'s NFR-1 — the estimation confirms the assumption was carried through consistently.
3. **Step 3 applies the peak multiplier**, because average load is not the number a system must survive — the system must survive its *busiest* moments. Multiplying by 3x gives ~11,574 peak read QPS — this is the number that most directly shapes the [high-level architecture](0228-url-shortener-high-level-architecture.md)'s caching decision: no single database instance comfortably serves 11,600 reads per second on its own, but a cache in front of one easily can.
4. **Step 4 works from records-per-day (100M/month divided by ~30) times the assumed record size (500 bytes)**, producing ~1.67 GB/day, then multiplies by 365 days and 5 years to get roughly 3 TB total. This number tells you storage is *not* the bottleneck for this system — 3 TB is a modest amount even for a single well-sized database, meaning storage capacity alone would not force a sharded design (though read QPS still might).
5. **Step 5 multiplies peak QPS by average payload size for each path separately**, since reads and writes have very different QPS and payload characteristics. The resulting ~3.5 MB/s peak read bandwidth is small enough that a well-provisioned cache layer serves it with room to spare — this number rules out network bandwidth as a concern for this specific system, letting the design focus its effort on QPS and latency instead.

## 7. Gotchas & takeaways

> **Gotcha:** using average QPS instead of peak QPS to size infrastructure is a common and dangerous mistake — a system sized for the *average* 3,858 reads/sec will fall over during a real burst well below the 11,574 peak figure. Always design against peak, and treat the peak multiplier itself as an assumption worth stating explicitly, since it can be wrong in either direction.

- Every number in this estimation traces back to an explicitly stated assumption — when presenting or reviewing a capacity estimate, check the assumptions first, since a wrong assumption (e.g. record size, peak multiplier) propagates through every downstream number.
- The read:write QPS gap (roughly 100:1 here) is the number that most directly justifies the caching-heavy [architecture](0228-url-shortener-high-level-architecture.md) this case study lands on — cite this specific estimation when explaining that design choice.
- Storage came out comparatively small (a few TB over 5 years) — this is a common outcome for URL shorteners, and it means the [data model & schema](0229-url-shortener-data-model-schema.md) facet can optimize for fast lookups rather than for minimizing storage footprint.
- Round numbers generously and note the rounding — a back-of-envelope estimate is meant to establish order of magnitude (thousands vs. millions of QPS) for design decisions, not to produce a precise capacity-planning figure for procurement.
