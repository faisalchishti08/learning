---
card: spring-data
gi: 107
slug: geospatial-queries
title: "GeoSpatial queries"
---

## 1. What it is

MongoDB has native support for geospatial data (`GeoJsonPoint`, and query operations like "find documents near this point" or "find documents within this area"), and Spring Data MongoDB exposes it through derived query keywords (`findByLocationNear`, `findByLocationWithin`) and `Criteria` methods (`.near(...)`, `.within(...)`), backed by a `2dsphere` index for efficient execution.

```java
@Document("stores")
class Store {
    @Id String id;
    @GeoSpatialIndexed GeoJsonPoint location; // stored as GeoJSON, indexed for spatial queries
}

interface StoreRepository extends MongoRepository<Store, String> {
    List<Store> findByLocationNear(Point point, Distance distance); // derived geospatial query
}
```

## 2. Why & when

Every query mechanism covered so far — derived methods, `@Query`, `Criteria`/`Query`, aggregation — deals with exact-match or comparison conditions on ordinary fields. Geospatial queries are qualitatively different: "how far is this point from that point" and "is this point inside this polygon" require specialized math and (for any real performance) a specialized index type — plain B-tree indexes can't efficiently answer "what's nearby."

Reach for geospatial queries specifically when:

- The domain genuinely involves location data — store locators, delivery-radius checks, "find nearby" features — anything where physical distance or containment within an area is a real query requirement.
- You need "nearest N results" ordered by distance (`findByLocationNear`), which MongoDB computes and sorts server-side using the geospatial index, rather than fetching everything and computing distances in application code.
- You need "is this point within this boundary" (`findByLocationWithin`), for use cases like "show me stores inside this delivery zone."

## 3. Core concept

```
 @GeoSpatialIndexed GeoJsonPoint location;   -- requires a 2dsphere index for efficient geo queries

 findByLocationNear(Point origin, Distance maxDistance)
   -- MongoDB computes actual geodesic/planar distance using the 2dsphere index
   -- returns matching documents, typically already sorted nearest-first

 findByLocationWithin(Circle area) / findByLocationWithin(Polygon area)
   -- MongoDB checks point-in-shape containment using the index
   -- returns documents whose location falls inside the given area
```

Both query types rely on a `2dsphere` index to avoid computing distance/containment against every document in the collection.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A geospatial index lets MongoDB efficiently find points near a location or within a bounded area">
  <circle cx="320" cy="90" r="4" fill="#79c0ff"/>
  <text x="320" y="75" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">origin</text>
  <circle cx="320" cy="90" r="60" fill="none" stroke="#6db33f" stroke-width="1.3" stroke-dasharray="4,3"/>
  <text x="320" y="160" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">findByLocationNear(origin, maxDistance)</text>

  <circle cx="280" cy="70" r="3" fill="#e6edf3"/>
  <circle cx="350" cy="110" r="3" fill="#e6edf3"/>
  <circle cx="300" cy="130" r="3" fill="#e6edf3"/>
  <circle cx="450" cy="40" r="3" fill="#8b949e"/>
  <text x="450" y="30" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">too far, excluded</text>
</svg>

Points inside the search radius are returned; points outside it are excluded — the `2dsphere` index lets MongoDB determine this efficiently without checking every document.

## 5. Runnable example

The scenario: finding stores near a customer's location, evolving from a naive distance computation over every store (no index), to a `findByLocationNear`-style query using an index-like spatial structure, to a `findByLocationWithin`-style containment check against a bounded delivery zone.

### Level 1 — Basic

Model computing distance to every store directly, standing in for the "no geospatial index" baseline — correct, but doesn't scale.

```java
import java.util.*;
import java.util.stream.*;

record Point(double lat, double lon) {}
class Store { String id; Point location; Store(String id, Point location) { this.id = id; this.location = location; } }

public class GeoLevel1 {
    // Simplified Euclidean distance (real geospatial queries use proper geodesic math -- simplified here for clarity).
    static double distance(Point a, Point b) {
        double dLat = a.lat() - b.lat(), dLon = a.lon() - b.lon();
        return Math.sqrt(dLat * dLat + dLon * dLon);
    }

    static List<Store> findNearby(List<Store> stores, Point origin, double maxDistance) {
        return stores.stream()
            .filter(s -> distance(s.location, origin) <= maxDistance) // checks EVERY store, no index
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Store> stores = List.of(
            new Store("store-A", new Point(40.71, -74.00)),
            new Store("store-B", new Point(40.75, -73.98)),
            new Store("store-C", new Point(34.05, -118.24)) // far away (Los Angeles vs New York)
        );
        Point customerLocation = new Point(40.72, -74.01);

        List<Store> nearby = findNearby(stores, customerLocation, 0.1);
        System.out.println("Nearby stores: " + nearby.stream().map(s -> s.id).toList());
    }
}
```

How to run: `java GeoLevel1.java`

`findNearby` computes the distance to *every* store, filtering afterward — correct for this small list, but this is exactly the pattern a `2dsphere` index exists to avoid at scale: without an index, MongoDB (or any database) would have to perform this same distance computation against every single document in the collection.

### Level 2 — Intermediate

Model `findByLocationNear` using a simplified spatial grid (standing in for the `2dsphere` index), letting the search skip most stores entirely by only checking those in nearby grid cells.

```java
import java.util.*;
import java.util.stream.*;

record Point(double lat, double lon) {}
class Store { String id; Point location; Store(String id, Point location) { this.id = id; this.location = location; } }

// Stands in for MongoDB's 2dsphere index: groups points into coarse grid cells for fast "nearby" lookups.
class SimpleGeoIndex {
    private final Map<String, List<Store>> gridCells = new HashMap<>();
    private static String cellKey(Point p) { return (int) p.lat() + "," + (int) p.lon(); } // coarse 1-degree cells

    void add(Store store) { gridCells.computeIfAbsent(cellKey(store.location), k -> new ArrayList<>()).add(store); }

    List<Store> candidatesNear(Point origin) {
        // Only examines stores in the SAME (or adjacent) grid cell, not the whole collection.
        return gridCells.getOrDefault(cellKey(origin), List.of());
    }
}

public class GeoLevel2 {
    static double distance(Point a, Point b) {
        double dLat = a.lat() - b.lat(), dLon = a.lon() - b.lon();
        return Math.sqrt(dLat * dLat + dLon * dLon);
    }

    // findByLocationNear(origin, maxDistance) -- uses the index to narrow candidates FIRST.
    static List<Store> findByLocationNear(SimpleGeoIndex index, Point origin, double maxDistance) {
        List<Store> candidates = index.candidatesNear(origin); // INDEX narrows this down first
        System.out.println("  Index narrowed search to " + candidates.size() + " candidate(s) (not the whole collection)");
        return candidates.stream().filter(s -> distance(s.location, origin) <= maxDistance).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        SimpleGeoIndex index = new SimpleGeoIndex();
        List<Store> stores = List.of(
            new Store("store-A", new Point(40.71, -74.00)),
            new Store("store-B", new Point(40.75, -73.98)),
            new Store("store-C", new Point(34.05, -118.24))
        );
        stores.forEach(index::add);

        Point customerLocation = new Point(40.72, -74.01);
        List<Store> nearby = findByLocationNear(index, customerLocation, 0.1);
        System.out.println("Nearby stores: " + nearby.stream().map(s -> s.id).toList());
    }
}
```

How to run: `java GeoLevel2.java`

`index.candidatesNear(origin)` narrows the search to just the grid cell containing the customer's location (in this dataset, just `store-A` and `store-B`, since `store-C` is in a completely different cell) *before* any distance computation runs — standing in for how a real `2dsphere` index lets MongoDB skip the vast majority of documents in a large collection, examining only those in the relevant spatial region.

### Level 3 — Advanced

Add a `findByLocationWithin`-style containment check against a bounded delivery zone (modeled as a simple bounding box, standing in for MongoDB's `Circle`/`Polygon`/`GeoJsonPolygon` shapes).

```java
import java.util.*;
import java.util.stream.*;

record Point(double lat, double lon) {}
record BoundingBox(double minLat, double maxLat, double minLon, double maxLon) {
    boolean contains(Point p) { return p.lat() >= minLat && p.lat() <= maxLat && p.lon() >= minLon && p.lon() <= maxLon; }
}
class Store { String id; Point location; Store(String id, Point location) { this.id = id; this.location = location; } }

public class GeoLevel3 {
    // findByLocationWithin(deliveryZone) -- MongoDB's Circle/Polygon containment check, simplified to a bounding box here.
    static List<Store> findByLocationWithin(List<Store> stores, BoundingBox deliveryZone) {
        return stores.stream().filter(s -> deliveryZone.contains(s.location)).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Store> stores = List.of(
            new Store("store-A", new Point(40.71, -74.00)),  // inside the NYC delivery zone
            new Store("store-B", new Point(40.90, -73.50)),  // just outside the zone
            new Store("store-C", new Point(34.05, -118.24))  // far outside (Los Angeles)
        );

        // A bounding box roughly covering the New York metro area.
        BoundingBox nycDeliveryZone = new BoundingBox(40.50, 40.80, -74.20, -73.80);

        List<Store> withinZone = findByLocationWithin(stores, nycDeliveryZone);
        System.out.println("Stores within delivery zone: " + withinZone.stream().map(s -> s.id).toList());
    }
}
```

How to run: `java GeoLevel3.java`

`store-A` falls within the bounding box and is included; `store-B` (`lat=40.90`, just above `maxLat=40.80`) falls just outside and is excluded; `store-C` (Los Angeles) is far outside entirely — matching how a real `findByLocationWithin(Circle)`/`findByLocationWithin(GeoJsonPolygon)` query returns only documents whose location genuinely falls inside the specified area, with MongoDB using the `2dsphere` index to perform this containment check efficiently rather than checking every document's coordinates individually.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, three stores are built, with `store-A` deliberately placed inside the intended delivery zone, `store-B` placed just outside it, and `store-C` placed far away entirely. `nycDeliveryZone` is defined as a bounding box covering roughly the New York metro area (`lat` between `40.50` and `40.80`, `lon` between `-74.20` and `-73.80`).

`findByLocationWithin(stores, nycDeliveryZone)` runs. For `store-A` (`lat=40.71, lon=-74.00`): `40.71` falls within `[40.50, 40.80]` and `-74.00` falls within `[-74.20, -73.80]` — both conditions in `BoundingBox.contains` are satisfied, so `store-A` is included.

For `store-B` (`lat=40.90, lon=-73.50`): `40.90` does *not* fall within `[40.50, 40.80]` (it exceeds `maxLat`), so `contains` returns `false` immediately — `store-B` is excluded, even though its longitude alone would have been within range.

For `store-C` (`lat=34.05, lon=-118.24`): neither coordinate falls anywhere near the delivery zone's range — clearly excluded.

The final filtered list contains only `store-A`, printed as "Stores within delivery zone: [store-A]".

```
nycDeliveryZone: lat=[40.50,40.80], lon=[-74.20,-73.80]

store-A (40.71,-74.00): lat OK, lon OK -> INCLUDED
store-B (40.90,-73.50): lat FAILS (40.90 > 40.80) -> excluded
store-C (34.05,-118.24): lat FAILS, lon FAILS -> excluded

result: [store-A]
```

In a real Spring Data MongoDB application, `storeRepository.findByLocationWithin(new Circle(new Point(-74.00, 40.71), new Distance(10, Metrics.KILOMETERS)))` (or a `GeoJsonPolygon` for an arbitrarily-shaped delivery zone) sends a geospatial containment query to MongoDB, which uses the `2dsphere` index on `Store.location` to efficiently return only documents whose location genuinely falls inside the specified shape — for a large store collection, this is dramatically faster than fetching every store and computing containment in application code, exactly mirroring the benefit the earlier `findByLocationNear` example demonstrated for nearest-neighbor search.

## 7. Gotchas & takeaways

> Gotcha: `GeoJsonPoint` stores coordinates as `[longitude, latitude]` — the reverse of the more common "latitude, longitude" convention used in everyday speech and many other APIs — swapping the two when constructing a `GeoJsonPoint` is a very common and easy-to-miss bug that silently places data at the wrong location on the globe (or an invalid one, if the swapped latitude value exceeds the valid longitude range).

- Geospatial queries (`findByLocationNear`, `findByLocationWithin`) require a `2dsphere` index (`@GeoSpatialIndexed`) on the location field to execute efficiently — without one, MongoDB would have to check every document individually.
- `findByLocationNear` finds documents close to a point, typically returned sorted nearest-first; `findByLocationWithin` finds documents contained inside a specified shape (circle, polygon).
- Both query types push the distance/containment computation to the database server, avoiding the need to fetch every document and compute geometry in application code.
- Double-check coordinate order (`[longitude, latitude]` for GeoJSON) when constructing points — a swapped pair is a silent, hard-to-notice bug.
