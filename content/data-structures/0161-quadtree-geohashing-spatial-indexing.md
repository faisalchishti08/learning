---
card: data-structures
gi: 161
slug: quadtree-geohashing-spatial-indexing
title: Quadtree & geohashing (spatial indexing)
---

## 1. What it is

A **quadtree** indexes 2D space by recursively splitting a region into four equal quadrants — northwest, northeast, southwest, southeast — whenever a quadrant holds more points than a set limit. **Geohashing** is a different approach to the same problem: it encodes a coordinate as a single string, where each added character narrows the location into a smaller rectangle, so two nearby points tend to share a long common prefix.

## 2. Why & when

Both solve "find everything near this location" for map-like data — nearby drivers in a ride-sharing app, nearby stores, or map tiles to render. A quadtree is a real tree structure you build and query in memory, good when you control the data structure directly (game engines, in-process spatial indexes). Geohashing turns location into a **string**, which you can store as an ordinary indexed column in any database or key-value store — no custom tree code needed, at the cost of some accuracy at cell boundaries.

## 3. Core concept

**The quadtree's shape.** Each node covers a rectangular region. A node starts as a leaf holding up to `capacity` points. Once it would exceed `capacity`, it **subdivides** into four children — NW, NE, SW, SE — each covering one quarter of the parent's region, and its points are redistributed into whichever child region contains them.

**The invariant.** Every point is stored in the smallest quadrant whose region contains it. Regions never overlap and their union is always the full covered area.

**Why it makes queries fast.** A range query ("find all points inside this rectangle") only descends into a child quadrant if that quadrant's region **intersects** the query rectangle. Quadrants entirely outside the query are skipped in `O(1)`, without visiting a single point inside them — the same pruning idea as a [k-d tree](0160-k-d-tree-spatial-partitioning.md), but splitting evenly into 4 fixed quadrants instead of adapting the split point to the data.

**Geohashing's shape.** Interleave bits from the latitude and longitude, halving the possible range with each bit: does the point fall in the top or bottom half of the current latitude range, then the left or right half of the current longitude range, alternating. Group the resulting bits into base-32 characters. The result is a string like `"9q8yy"`, where each extra character shrinks the represented rectangle further.

**Why prefixes matter.** Because each character narrows the cell, two geohash strings that share a long prefix are guaranteed to be geographically close — this lets you find nearby points using ordinary string prefix queries (`LIKE '9q8yy%'`), which every database already indexes efficiently.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A quadtree subdividing a region into four quadrants, next to a geohash string narrowing a coordinate one character at a time">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="20" y="20" width="180" height="180" fill="none" stroke="#79c0ff" stroke-width="2"/>
    <line x1="110" y1="20" x2="110" y2="200" stroke="#79c0ff"/>
    <line x1="20" y1="110" x2="200" y2="110" stroke="#79c0ff"/>
    <rect x="110" y="20" width="45" height="45" fill="none" stroke="#f0883e"/>
    <line x1="132" y1="20" x2="132" y2="65" stroke="#f0883e"/>
    <line x1="110" y1="42" x2="155" y2="42" stroke="#f0883e"/>
    <text x="110" y="14" font-size="9">quadtree: NE quadrant subdivided further</text>

    <g transform="translate(280,0)">
      <text x="0" y="20" font-size="9">geohash narrowing:</text>
      <rect x="0" y="30" width="320" height="20" fill="#161b22" stroke="#8b949e"/>
      <text x="4" y="45" font-size="9">char 1 "9": narrows to 1/32 of the globe</text>
      <rect x="0" y="60" width="160" height="20" fill="#161b22" stroke="#8b949e"/>
      <text x="4" y="75" font-size="9">char 2 "q": narrows further</text>
      <rect x="0" y="90" width="80" height="20" fill="#161b22" stroke="#8b949e"/>
      <text x="4" y="105" font-size="9">char 3 "8": ~city-block size</text>
      <text x="0" y="140" font-size="9" fill="#8b949e">"9q8yy" and "9q8yz" share a 4-char</text>
      <text x="0" y="155" font-size="9" fill="#8b949e">prefix -&gt; they are geographically close</text>
    </g>
  </g>
</svg>

Quadtree: each split covers a shrinking region. Geohash: each character shrinks the encoded rectangle.

## 5. Runnable example

```java
// QuadtreeGeohash.java
import java.util.*;

public class QuadtreeGeohash {

    record Point(double x, double y, String label) {}

    // Basic: a quadtree that subdivides once a node exceeds capacity.
    static class Quadtree {
        double x, y, w, h; // region: top-left (x,y), width w, height h
        int capacity;
        List<Point> points = new ArrayList<>();
        Quadtree nw, ne, sw, se;
        boolean divided = false;

        Quadtree(double x, double y, double w, double h, int capacity) {
            this.x = x; this.y = y; this.w = w; this.h = h; this.capacity = capacity;
        }

        boolean contains(Point p) {
            return p.x() >= x && p.x() < x + w && p.y() >= y && p.y() < y + h;
        }

        void subdivide() {
            double hw = w / 2, hh = h / 2;
            nw = new Quadtree(x, y, hw, hh, capacity);
            ne = new Quadtree(x + hw, y, hw, hh, capacity);
            sw = new Quadtree(x, y + hh, hw, hh, capacity);
            se = new Quadtree(x + hw, y + hh, hw, hh, capacity);
            divided = true;
        }

        void insert(Point p) {
            if (!contains(p)) return;
            if (points.size() < capacity && !divided) { points.add(p); return; }
            if (!divided) subdivide();
            nw.insert(p); ne.insert(p); sw.insert(p); se.insert(p);
        }
    }

    static void basicLevel() {
        Quadtree tree = new Quadtree(0, 0, 100, 100, 2);
        for (Point p : new Point[]{
            new Point(10, 10, "A"), new Point(20, 15, "B"), new Point(80, 80, "C"), new Point(15, 90, "D")}) {
            tree.insert(p);
        }
        System.out.println("basic: root divided after 3rd point in same quadrant -> " + tree.divided);
    }

    // Intermediate: range query, pruning quadrants that don't intersect the query rectangle.
    static boolean intersects(Quadtree q, double qx, double qy, double qw, double qh) {
        return !(qx > q.x + q.w || qx + qw < q.x || qy > q.y + q.h || qy + qh < q.y);
    }

    static void queryRange(Quadtree q, double qx, double qy, double qw, double qh, List<Point> results) {
        if (!intersects(q, qx, qy, qw, qh)) return;
        for (Point p : q.points) {
            if (p.x() >= qx && p.x() <= qx + qw && p.y() >= qy && p.y() <= qy + qh) results.add(p);
        }
        if (q.divided) {
            queryRange(q.nw, qx, qy, qw, qh, results);
            queryRange(q.ne, qx, qy, qw, qh, results);
            queryRange(q.sw, qx, qy, qw, qh, results);
            queryRange(q.se, qx, qy, qw, qh, results);
        }
    }

    static void intermediateLevel() {
        Quadtree tree = new Quadtree(0, 0, 100, 100, 2);
        for (Point p : new Point[]{
            new Point(10, 10, "A"), new Point(20, 15, "B"), new Point(80, 80, "C"), new Point(15, 90, "D")}) {
            tree.insert(p);
        }
        List<Point> results = new ArrayList<>();
        queryRange(tree, 0, 0, 30, 30, results);
        System.out.println("intermediate: points in [0,0]-[30,30] -> " + results);
    }

    // Advanced: a simplified geohash-style encoder, interleaving lat/lon bits into a bit string.
    static String simpleGeohashBits(double lat, double lon, int bits) {
        double latMin = -90, latMax = 90, lonMin = -180, lonMax = 180;
        StringBuilder result = new StringBuilder();
        boolean useLon = true;
        for (int i = 0; i < bits; i++) {
            if (useLon) {
                double mid = (lonMin + lonMax) / 2;
                if (lon >= mid) { result.append('1'); lonMin = mid; } else { result.append('0'); lonMax = mid; }
            } else {
                double mid = (latMin + latMax) / 2;
                if (lat >= mid) { result.append('1'); latMin = mid; } else { result.append('0'); latMax = mid; }
            }
            useLon = !useLon;
        }
        return result.toString();
    }

    static void advancedLevel() {
        String hashA = simpleGeohashBits(40.7128, -74.0060, 20); // New York
        String hashB = simpleGeohashBits(40.7300, -73.9950, 20); // nearby point in New York
        String hashC = simpleGeohashBits(34.0522, -118.2437, 20); // Los Angeles

        System.out.println("advanced: New York bits      -> " + hashA);
        System.out.println("advanced: nearby NY point     -> " + hashB);
        System.out.println("advanced: Los Angeles bits    -> " + hashC);
        System.out.println("advanced: NY vs nearby shared prefix length -> " + commonPrefixLength(hashA, hashB));
        System.out.println("advanced: NY vs LA shared prefix length     -> " + commonPrefixLength(hashA, hashC));
    }

    static int commonPrefixLength(String a, String b) {
        int i = 0;
        while (i < a.length() && i < b.length() && a.charAt(i) == b.charAt(i)) i++;
        return i;
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java QuadtreeGeohash.java`

## 6. Walkthrough

Build a quadtree over a 100x100 region with capacity `2`. Insert `A(10,10)`, `B(20,15)`, `C(80,80)`, `D(15,90)`. `A` and `B` both fall in the top-left region and fit within capacity `2`, so the root stays a leaf holding `[A, B]`. Once a third point that also lands in the same small area arrives, that node would exceed capacity `2` and calls `subdivide()`, creating four child quadrants and redistributing its points into whichever child actually contains each one.

Now query the rectangle `[0,0]` to `[30,30]`. Starting at the root: does the root's region intersect the query? Yes (it always does, since the root covers everything). Check the root's own points if it is still a leaf, or descend into children whose regions intersect `[0,0]-[30,30]` if it has divided. `C` at `(80,80)` and `D` at `(15,90)` sit in regions that do not intersect the query rectangle, so those branches are skipped entirely — only `A` and `B` are checked and returned.

For geohashing: encode New York `(40.7128, -74.0060)` and a nearby point `(40.7300, -73.9950)` into bit strings by repeatedly halving the latitude and longitude ranges. Because both points fall in nearly the same half at almost every step, their bit strings share a long common prefix. A far-away point like Los Angeles diverges from New York within the first few bits, giving a short common prefix.

**Complexity.** Quadtree: insert `O(log n)` average (depends on point distribution — a skewed distribution can make some branches deep). Range query: `O(log n + k)` for `k` results found, after pruning non-intersecting quadrants. Geohash: encoding is `O(bits)` — constant for a fixed precision — and prefix search is as fast as the underlying string index (typically `O(log n)` for a B-tree-backed database index).

## 7. Gotchas & takeaways

> Geohashing has a boundary problem: two points can be extremely close in real distance but land on opposite sides of a cell boundary, giving them completely different prefixes despite being neighbors. Production geohash queries typically check the 8 neighboring cells too, not just an exact prefix match.

- A quadtree with a skewed point distribution (everyone clustered in one corner) can subdivide very deeply in that corner while staying shallow elsewhere — capacity limits bound memory, not guaranteed balance.
- Geohash precision trades off directly with string length: more characters means a smaller, more precise cell, and a shorter shared-prefix requirement for "nearby."
- Choose a quadtree when you own the data structure and need exact range/nearest queries in memory. Choose geohashing when you want to piggyback on an existing database's string index instead of writing custom spatial code.
