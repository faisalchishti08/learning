---
card: spring-data
gi: 148
slug: geo-queries
title: "Geo queries"
---

## 1. What it is

Elasticsearch has native support for geographic data — `GeoPoint` fields storing latitude/longitude — and geo-specific queries: **distance** queries ("within 5km of this point"), **bounding box** queries ("within this rectangle"), and distance-based **sorting** ("nearest first"). Spring Data Elasticsearch maps a `GeoPoint` field directly and exposes geo-aware derived query methods and `Criteria` conditions.

```java
@Document(indexName = "orders")
class Order {
    @Id String id;
    @GeoPointField GeoPoint deliveryLocation;
}

interface OrderRepository extends ElasticsearchRepository<Order, String> {
    List<Order> findByDeliveryLocationNear(GeoPoint point, Distance distance);
}
```

## 2. Why & when

Computing "which of these points are within 5km of me" or "sort these by distance from me" involves real geographic math (accounting for the Earth's curvature, not flat Euclidean distance) — doing this correctly and efficiently in application code, especially across a large dataset, is both error-prone and slow. Elasticsearch's `geo_point` field type and geo queries push this computation to where the data already lives, using spatial indexing structures purpose-built for it.

Reach for geo queries when:

- You need "find things near this location" — nearby stores, delivery zones, points of interest within a radius.
- You need "find things within this rectangular area" — a bounding box query, useful for map-viewport-based searches ("show me everything currently visible on the map").
- You want results sorted by distance from a reference point — "nearest first," a standard requirement for any location-aware search feature.

## 3. Core concept

```
 Order documents, each with a deliveryLocation (lat, lon):
   order-1: (40.7128, -74.0060)  -- New York
   order-2: (34.0522, -118.2437) -- Los Angeles
   order-3: (40.7306, -73.9352)  -- Brooklyn (close to New York)

 geo_distance query: point=(40.7128, -74.0060), distance="20km"
        -> matches order-1 (0km away) and order-3 (~8km away)
        -> does NOT match order-2 (~3,900km away)

 sort by _geo_distance from (40.7128, -74.0060):
        -> order-1 (0km), order-3 (~8km), order-2 (~3,900km)   -- nearest first
```

Both filtering ("is this within range?") and sorting ("how close is this?") use the same underlying great-circle distance calculation, computed server-side.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A geo distance query draws a radius around a point; only documents whose location falls within that radius match">
  <circle cx="220" cy="90" r="80" fill="#3fb95015" stroke="#3fb950" stroke-width="1.5" stroke-dasharray="4,3"/>
  <circle cx="220" cy="90" r="4" fill="#6db33f"/>
  <text x="220" y="115" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">reference point</text>

  <circle cx="240" cy="70" r="5" fill="#3fb950"/>
  <text x="240" y="55" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">order-3 (inside radius)</text>

  <circle cx="480" cy="60" r="5" fill="#f85149"/>
  <text x="480" y="45" fill="#f85149" font-size="8.5" text-anchor="middle" font-family="sans-serif">order-2 (outside radius)</text>

  <text x="320" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">geo_distance query: only points inside the dashed radius match</text>
</svg>

Points inside the query's radius match; points outside, no matter how close to matching, do not.

## 5. Runnable example

The scenario: finding and sorting orders by delivery location, evolving from a basic distance calculation and radius filter, to sorting matching results by distance, to a bounding-box query for a map-viewport-style search.

### Level 1 — Basic

Model a `geo_distance` filter: compute the distance between two points and check it against a radius.

```java
import java.util.*;
import java.util.stream.*;

public class GeoQueriesLevel1 {
    public static void main(String[] args) {
        GeoPoint newYork = new GeoPoint(40.7128, -74.0060);
        List<Order> orders = List.of(
            new Order("1", new GeoPoint(40.7128, -74.0060)),  // New York itself
            new Order("2", new GeoPoint(34.0522, -118.2437)), // Los Angeles -- far
            new Order("3", new GeoPoint(40.7306, -73.9352))   // Brooklyn -- close
        );

        // Mirrors: Criteria.where("deliveryLocation").within(newYork, "20km")
        List<Order> withinRange = orders.stream()
            .filter(o -> haversineKm(newYork, o.deliveryLocation) <= 20.0)
            .collect(Collectors.toList());

        System.out.println("Orders within 20km of New York: " + withinRange.stream().map(o -> o.id).collect(Collectors.toList()));
    }

    // The haversine formula -- computes great-circle distance between two lat/lon points, accounting for Earth's curvature.
    static double haversineKm(GeoPoint a, GeoPoint b) {
        double earthRadiusKm = 6371.0;
        double dLat = Math.toRadians(b.lat - a.lat);
        double dLon = Math.toRadians(b.lon - a.lon);
        double h = Math.sin(dLat / 2) * Math.sin(dLat / 2)
            + Math.cos(Math.toRadians(a.lat)) * Math.cos(Math.toRadians(b.lat)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        return earthRadiusKm * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
    }
}

class GeoPoint { double lat; double lon; GeoPoint(double lat, double lon) { this.lat = lat; this.lon = lon; } }

class Order { String id; GeoPoint deliveryLocation; Order(String id, GeoPoint deliveryLocation) { this.id = id; this.deliveryLocation = deliveryLocation; } }
```

How to run: `java GeoQueriesLevel1.java`

`haversineKm` computes the actual great-circle distance between two coordinates, the same underlying calculation Elasticsearch's `geo_point` field type uses internally — this is why geo queries can't just use simple Euclidean (Pythagorean) distance on raw lat/lon numbers, which would give meaningfully wrong answers, especially over longer distances. Filtering by `<= 20.0` km mirrors `Criteria.where("deliveryLocation").within(point, "20km")`.

### Level 2 — Intermediate

Sort matching results by distance, nearest first, matching `_geo_distance` sorting.

```java
import java.util.*;
import java.util.stream.*;

public class GeoQueriesLevel2 {
    public static void main(String[] args) {
        GeoPoint newYork = new GeoPoint(40.7128, -74.0060);
        List<Order> orders = List.of(
            new Order("1", new GeoPoint(40.7128, -74.0060)),  // exactly New York
            new Order("2", new GeoPoint(34.0522, -118.2437)), // Los Angeles -- far
            new Order("3", new GeoPoint(40.7306, -73.9352)),  // Brooklyn -- close
            new Order("4", new GeoPoint(40.6892, -74.0445))   // Statue of Liberty -- also close
        );

        // Mirrors: sort by _geo_distance from newYork, ascending
        List<Order> sortedByDistance = orders.stream()
            .sorted(Comparator.comparingDouble(o -> haversineKm(newYork, o.deliveryLocation)))
            .collect(Collectors.toList());

        for (Order o : sortedByDistance) {
            System.out.printf("  %s: %.1f km away%n", o.id, haversineKm(newYork, o.deliveryLocation));
        }
    }

    static double haversineKm(GeoPoint a, GeoPoint b) {
        double earthRadiusKm = 6371.0;
        double dLat = Math.toRadians(b.lat - a.lat);
        double dLon = Math.toRadians(b.lon - a.lon);
        double h = Math.sin(dLat / 2) * Math.sin(dLat / 2)
            + Math.cos(Math.toRadians(a.lat)) * Math.cos(Math.toRadians(b.lat)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        return earthRadiusKm * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
    }
}

class GeoPoint { double lat; double lon; GeoPoint(double lat, double lon) { this.lat = lat; this.lon = lon; } }

class Order { String id; GeoPoint deliveryLocation; Order(String id, GeoPoint deliveryLocation) { this.id = id; this.deliveryLocation = deliveryLocation; } }
```

How to run: `java GeoQueriesLevel2.java`

`Comparator.comparingDouble` sorts orders by their haversine distance from `newYork`, ascending — nearest first, mirroring `SortOptions.of(s -> s.geoDistance(g -> g.field("deliveryLocation").location(...).order(SortOrder.Asc)))`. Order `1` (exactly at the reference point) sorts first at `0.0` km, followed by the two nearby New York-area points, with Los Angeles sorting last, far behind the others.

### Level 3 — Advanced

Implement a bounding-box query: match documents whose location falls within a rectangular area defined by two corner points, matching a map-viewport-style search.

```java
import java.util.*;
import java.util.stream.*;

public class GeoQueriesLevel3 {
    public static void main(String[] args) {
        // A bounding box roughly covering the New York City area.
        GeoPoint topLeft = new GeoPoint(40.85, -74.05);     // northwest corner
        GeoPoint bottomRight = new GeoPoint(40.65, -73.85);  // southeast corner

        List<Order> orders = List.of(
            new Order("1", new GeoPoint(40.7128, -74.0060)), // Manhattan -- INSIDE the box
            new Order("2", new GeoPoint(34.0522, -118.2437)), // Los Angeles -- WAY outside
            new Order("3", new GeoPoint(40.7306, -73.9352)),  // Brooklyn -- INSIDE the box
            new Order("4", new GeoPoint(41.0, -73.7))         // just north, outside the box's latitude range
        );

        // Mirrors: Criteria.where("deliveryLocation").boundedBy(topLeft, bottomRight) -- a geo_bounding_box query
        List<Order> insideBox = orders.stream()
            .filter(o -> withinBoundingBox(o.deliveryLocation, topLeft, bottomRight))
            .collect(Collectors.toList());

        System.out.println("Orders within the NYC bounding box: " + insideBox.stream().map(o -> o.id).collect(Collectors.toList()));
    }

    static boolean withinBoundingBox(GeoPoint point, GeoPoint topLeft, GeoPoint bottomRight) {
        boolean latInRange = point.lat <= topLeft.lat && point.lat >= bottomRight.lat;
        boolean lonInRange = point.lon >= topLeft.lon && point.lon <= bottomRight.lon;
        return latInRange && lonInRange;
    }
}

class GeoPoint { double lat; double lon; GeoPoint(double lat, double lon) { this.lat = lat; this.lon = lon; } }

class Order { String id; GeoPoint deliveryLocation; Order(String id, GeoPoint deliveryLocation) { this.id = id; this.deliveryLocation = deliveryLocation; } }
```

How to run: `java GeoQueriesLevel3.java`

`withinBoundingBox` checks that a point's latitude falls between the box's north and south edges and its longitude falls between the west and east edges — a simpler check than the haversine distance calculation, since a bounding box is defined by straight coordinate ranges rather than a radius. Order `4`, despite being reasonably close to New York in absolute terms, falls just outside the box's latitude range (`41.0 > 40.85`) and is correctly excluded — exactly how a map-viewport search only returns what's currently visible within the rectangle, not everything nearby in general.

## 6. Walkthrough

Execution starts in `main` for Level 3. `topLeft` (`40.85, -74.05`) and `bottomRight` (`40.65, -73.85`) define a rectangular region. Four orders are defined, including order `4` at `(41.0, -73.7)`, deliberately placed just north of the box.

`withinBoundingBox(o.deliveryLocation, topLeft, bottomRight)` is checked for each order. For order `1` (`40.7128, -74.0060`): `latInRange` checks `40.7128 <= 40.85` (true) and `40.7128 >= 40.65` (true), so `latInRange` is `true`; `lonInRange` checks `-74.0060 >= -74.05` (true) and `-74.0060 <= -73.85` (true), so `lonInRange` is `true` too — both conditions hold, so order `1` is included. Order `3` passes the same two checks similarly and is also included.

For order `2` (Los Angeles, `34.0522, -118.2437`): `latInRange` already fails (`34.0522 <= 40.85` is true, but `34.0522 >= 40.65` is false), so the whole check short-circuits to `false` — excluded, as expected for a point on the opposite coast.

For order `4` (`41.0, -73.7`): `latInRange` checks `41.0 <= 40.85` — this is `false`, since `41.0` exceeds the box's northern edge — so `latInRange` is `false`, and order `4` is excluded despite its longitude (`-73.7`) actually falling within the box's east-west range.

```
Orders within the NYC bounding box: [1, 3]
```

In real Elasticsearch, a `geo_bounding_box` query performs exactly this coordinate-range check, but using the `geo_point` field's spatial index to efficiently narrow down candidates rather than checking every document individually — and Spring Data Elasticsearch exposes it through `Criteria.where("deliveryLocation").boundedBy(topLeft, bottomRight)`, producing the equivalent `bool`-wrapped `geo_bounding_box` clause under the hood.

## 7. Gotchas & takeaways

> Gotcha: a bounding box that crosses the antimeridian (longitude ±180°) needs special handling — a naive "west longitude <= point <= east longitude" check (as this simplified example implements) breaks down when the box wraps around from, say, 170° to -170°. Real Elasticsearch bounding-box queries handle this correctly internally; a hand-rolled version needs explicit wraparound logic.

> Gotcha: sorting by `_geo_distance` computes a real distance for every matching document to determine sort order, which is more expensive than sorting by an indexed field value — for very large result sets, consider narrowing with a `geo_distance` or `geo_bounding_box` filter first, so the (more expensive) distance sort only has to run over the already-filtered, smaller candidate set.

- `GeoPoint` fields and Elasticsearch's geo queries handle real geographic (great-circle) distance calculations server-side, avoiding the complexity and cost of doing this correctly in application code.
- `geo_distance` queries filter by radius from a reference point; `geo_bounding_box` queries filter by a rectangular region — choose based on whether the access pattern is "nearby" or "currently visible on a map."
- Sorting by `_geo_distance` returns results nearest-first, the standard requirement for location-aware search features.
- Filter with a distance or bounding-box query before sorting by distance on a large result set, since the distance sort itself is more expensive than sorting an indexed field.
