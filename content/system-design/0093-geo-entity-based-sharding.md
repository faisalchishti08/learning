---
card: system-design
gi: 93
slug: geo-entity-based-sharding
title: Geo / entity-based sharding
---

## 1. What it is

**Geo-based sharding** puts each row on the shard closest to where its data is used or legally required to live, keyed by a geographic attribute such as country or region: a user in India lands on the `ap-south` shard, a user in Germany lands on the `eu-central` shard. **Entity-based sharding** is the same idea applied to a business entity instead of geography: every row belonging to one tenant, account, or organization lives together on one shard, keyed by `tenantId`.

## 2. Why & when

Use geo-based sharding when latency matters (users get faster responses from a nearby shard) or when regulation requires data to stay within a region — for example, the EU's data-residency rules. Use entity-based sharding when your workload is naturally organized around independent groups, such as a multi-tenant SaaS product, because it guarantees that all of one tenant's data — and therefore almost every query that tenant makes — lives on a single shard, avoiding cross-shard joins for that tenant's own data. Both are really the same technique as directory or hash sharding, but with a business-meaningful key (region or tenant) instead of a technical one (user id).

## 3. Core concept

- **Geo-based:** the partition key is a location attribute (country, region code). Rows for the same region co-locate on the same shard, physically placed in or near that region's data center.
- **Latency win:** a request from a French user is served by the `eu-west` shard, which is geographically close, cutting round-trip time versus a shard on another continent.
- **Compliance win:** data-residency laws that require, say, EU citizen data to stay in the EU are satisfied automatically, since that data never leaves its region's shard.
- **Entity-based (tenant-based):** the partition key is a business entity id (`tenantId`, `orgId`). Every row for that tenant — across every table — lives on the same shard.
- **No cross-shard joins for one tenant:** since a tenant's orders, users, and settings all live together, a query scoped to one tenant never needs to fan out to other shards.
- **The imbalance risk:** if one region or one tenant is far larger than the others (a "whale" customer), its shard can become overloaded while smaller shards sit idle — the same skew problem seen in [hot spots & skew](0095-hot-spots-skew.md), just triggered by real-world size differences instead of a bad hash.

## 4. Diagram

```
GEO-BASED:                          ENTITY-BASED (multi-tenant):

  User region "IN" -> ap-south shard    tenant "acme-corp"  -> Shard 1
  User region "DE" -> eu-central shard  tenant "acme-corp"  -> Shard 1  (same tenant, same shard)
  User region "US" -> us-east shard     tenant "globex-inc" -> Shard 2

  A request from Germany is served      A query for "all orders for acme-corp"
  by the nearby eu-central shard,       hits ONLY Shard 1 - no cross-shard
  not a distant one.                    join needed across tenants' data.
```
*Caption: both variants key the shard choice on a business-meaningful attribute (region or tenant) instead of a technical hash.*

## 5. Runnable example

**Level 1 — Basic.** Route users to a shard by their region code.

**Level 2 — Entity-based co-location.** Route multiple record types for the same tenant to the same shard, and confirm no cross-shard join is needed for a tenant-scoped query.

**Level 3 — Whale imbalance.** Show one large tenant overwhelming its shard's row count compared to others.

```java
// GeoEntitySharding.java
import java.util.*;

public class GeoEntitySharding {

    static final Map<String, String> geoShardMap = Map.of(
        "IN", "ap-south", "DE", "eu-central", "US", "us-east"
    );

    static String routeByRegion(String regionCode) { return geoShardMap.get(regionCode); }

    static String routeByTenant(String tenantId, Map<String, String> tenantShardMap) {
        return tenantShardMap.get(tenantId);
    }

    public static void main(String[] args) {
        // Level 1: geo-based routing.
        System.out.println("user in DE -> shard " + routeByRegion("DE"));
        System.out.println("user in IN -> shard " + routeByRegion("IN"));

        // Level 2: entity-based routing - every record type for a tenant goes to the same shard.
        Map<String, String> tenantShardMap = new HashMap<>();
        tenantShardMap.put("acme-corp", "shard1");
        tenantShardMap.put("globex-inc", "shard2");

        System.out.println("acme-corp orders  -> " + routeByTenant("acme-corp", tenantShardMap));
        System.out.println("acme-corp users   -> " + routeByTenant("acme-corp", tenantShardMap));
        System.out.println("acme-corp invoices-> " + routeByTenant("acme-corp", tenantShardMap));
        System.out.println("-> all 3 record types for acme-corp land on shard1: one query, no cross-shard join");

        // Level 3: whale tenant - one tenant has far more rows than the others.
        Map<String, Integer> rowCountPerShard = new TreeMap<>();
        Map<String, Integer> tenantRowCounts = Map.of("acme-corp", 2_000_000, "globex-inc", 3_000, "initech", 5_000);
        for (var entry : tenantRowCounts.entrySet()) {
            String shard = tenantShardMap.getOrDefault(entry.getKey(), "shard3");
            rowCountPerShard.merge(shard, entry.getValue(), Integer::sum);
        }
        System.out.println("row counts per shard: " + rowCountPerShard);
        System.out.println("-> shard1 (acme-corp alone) dwarfs the others: a whale-tenant imbalance");
    }
}
```

**How to run:** save as `GeoEntitySharding.java`, then run `java GeoEntitySharding.java`.

## 6. Walkthrough

1. `geoShardMap` assigns each region code directly to a physically nearby shard name; `routeByRegion("DE")` returns `"eu-central"`, modeling a German user's request being served from a nearby data center.
2. `tenantShardMap` assigns each tenant id to one shard; calling `routeByTenant("acme-corp", ...)` for orders, users, and invoices all return `"shard1"` — showing every record type for that one tenant co-locates on the same shard.
3. The comment confirms the payoff: a query scoped to `acme-corp` (e.g. "join its orders with its users") never needs to leave shard1, because both tables' rows for that tenant live there together.
4. Level 3 assigns very different row counts to each tenant (`acme-corp` with 2,000,000 rows, versus a few thousand for the others), then sums rows per shard using the same `tenantShardMap`.
5. The printed totals show shard1 holding far more rows than shard2 or the default shard3 — a realistic outcome when one tenant is simply much bigger, illustrating why entity-based sharding still needs a plan for a disproportionately large "whale" entity.

## 7. Gotchas & takeaways

> Gotcha: geo- and entity-based sharding assume the underlying real-world groups (regions, tenants) are similar in size. When one is much larger than the rest, its shard becomes a hot spot with no formula to fix it — the usual remedy is to split that one large entity further (sub-shard the whale tenant by another key) while leaving the smaller ones as single shards.

- Geo-based sharding keys on region, improving latency and helping meet data-residency requirements.
- Entity-based sharding keys on a business entity (tenant), co-locating all of that entity's data to avoid cross-shard joins for entity-scoped queries.
- Both inherit the imbalance risk of any sharding scheme when the underlying groups are unevenly sized.
- Related concepts: [Directory-based sharding](0092-directory-based-sharding.md) (the general mechanism these business-meaningful keys often route through), [Hot spots & skew](0095-hot-spots-skew.md) (the imbalance problem a whale region or tenant causes).
