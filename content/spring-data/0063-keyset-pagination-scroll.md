---
card: spring-data
gi: 63
slug: keyset-pagination-scroll
title: "Keyset pagination (scroll)"
---

## 1. What it is

Spring Data's `scroll(ScrollPosition, ...)` support (via `Window<T>`) implements **keyset pagination**: instead of an `OFFSET` that skips N rows on every request, each page's query filters directly on the last-seen row's sort key (`WHERE total < :lastTotal ORDER BY total DESC LIMIT 20`), so the database jumps straight to the right rows instead of scanning and discarding everything before the offset.

```java
Window<Order> window = orderRepository.findBy(
    (root, query, cb) -> cb.equal(root.get("status"), "SHIPPED"),
    q -> q.sortBy(Sort.by("total").descending()).limit(20));
ScrollPosition next = window.positionAt(window.size() - 1);
```

## 2. Why & when

The previous card's `Page`/`Slice` both rely on `OFFSET`, which the earlier Spring Data Commons paging card also used — and `OFFSET`-based paging gets slower page by page, because the database still has to walk past (and discard) every skipped row even for page 500. Keyset pagination fixes that by encoding "where I left off" as an actual value (the last row's sort key) rather than a row count to skip.

Reach for keyset pagination (`scroll`/`Window`) specifically when:

- You're paging deep into a large, frequently-changing table, where `OFFSET 10000` performance degradation (or rows shifting between pages as new data is inserted) becomes a real problem.
- You're building infinite-scroll or "next batch" APIs where the client only ever needs "give me the next N after the last one I saw," not arbitrary page-number jumping.
- Consistent results matter even as new rows are inserted concurrently — keyset pagination naturally tolerates concurrent inserts better than offset-based paging, since it filters by value, not position.

## 3. Core concept

```
 Offset paging (page N):
   SELECT * FROM orders ORDER BY total DESC LIMIT 20 OFFSET (N * 20)
   -- DB scans and discards N*20 rows every time. Gets slower as N grows.

 Keyset paging (scroll):
   Page 1: SELECT * FROM orders ORDER BY total DESC LIMIT 20
           -- remember last row's total, e.g. 42.50
   Page 2: SELECT * FROM orders WHERE total < 42.50 ORDER BY total DESC LIMIT 20
           -- DB jumps straight to the right rows via an index -- no scan-and-discard
```

Each next request carries the previous page's last sort-key value forward as a `WHERE` filter, instead of an ever-growing `OFFSET`.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Keyset pagination carries the last row's sort key forward as a WHERE filter for the next page">
  <rect x="20" y="60" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="82" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">page 1</text>
  <text x="95" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">total DESC LIMIT 20</text>

  <rect x="245" y="60" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="82" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">last row total=42.50</text>
  <text x="320" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; ScrollPosition</text>

  <rect x="470" y="60" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="82" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">page 2</text>
  <text x="545" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">WHERE total &lt; 42.50</text>

  <line x1="170" y1="85" x2="240" y2="85" stroke="#8b949e" stroke-width="1.4" marker-end="url(#ks)"/>
  <line x1="395" y1="85" x2="465" y2="85" stroke="#8b949e" stroke-width="1.4" marker-end="url(#ks)"/>
  <defs><marker id="ks" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each page's last sort-key value becomes the next page's filter — no row-skipping `OFFSET` involved.

## 5. Runnable example

The scenario: scrolling through orders sorted by total, evolving from a naive offset-based page-by-page walk, to a keyset-based walk using the last seen value, to a reusable scroll loop that stops when no more rows match.

### Level 1 — Basic

Model offset-based paging first, so its cost is visible before comparing it to keyset paging.

```java
import java.util.*;
import java.util.stream.*;

class Order {
    long id; double total;
    Order(long id, double total) { this.id = id; this.total = total; }
    public String toString() { return "{id=" + id + ", total=" + total + "}"; }
}

public class ScrollLevel1 {
    static int rowsScanned = 0;

    // Simulates: findAll(PageRequest.of(page, size, Sort.by("total").descending()))
    static List<Order> pageByOffset(List<Order> sorted, int page, int size) {
        rowsScanned += page * size; // rows the DB has to skip past before returning results
        return sorted.stream().skip((long) page * size).limit(size).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> sorted = IntStream.rangeClosed(1, 10)
            .mapToObj(i -> new Order(i, 1000 - i * 10.0))
            .sorted(Comparator.comparingDouble((Order o) -> o.total).reversed())
            .collect(Collectors.toList());

        List<Order> page0 = pageByOffset(sorted, 0, 3);
        List<Order> page1 = pageByOffset(sorted, 1, 3);
        System.out.println("Page 0: " + page0);
        System.out.println("Page 1: " + page1);
        System.out.println("Rows scanned-and-discarded so far: " + rowsScanned);
    }
}
```

How to run: `java ScrollLevel1.java`

`rowsScanned` tracks the cost `OFFSET` imposes: page 0 skips nothing, but page 1 has to skip past the 3 rows already returned on page 0 — and this skip cost keeps growing with every subsequent page, even though this toy example only has 10 rows.

### Level 2 — Intermediate

Replace the offset with a keyset filter: each page's query filters on the previous page's last-seen `total`, avoiding any skip.

```java
import java.util.*;
import java.util.stream.*;

class Order {
    long id; double total;
    Order(long id, double total) { this.id = id; this.total = total; }
    public String toString() { return "{id=" + id + ", total=" + total + "}"; }
}

public class ScrollLevel2 {
    // Simulates: findBy(status predicate, q -> q.sortBy(Sort.by("total").descending()).limit(size))
    // with a WHERE total < lastTotal filter standing in for the ScrollPosition.
    static List<Order> pageByKeyset(List<Order> sorted, Double lastTotal, int size) {
        return sorted.stream()
            .filter(o -> lastTotal == null || o.total < lastTotal) // WHERE total < :lastTotal
            .limit(size)
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> sorted = IntStream.rangeClosed(1, 10)
            .mapToObj(i -> new Order(i, 1000 - i * 10.0))
            .sorted(Comparator.comparingDouble((Order o) -> o.total).reversed())
            .collect(Collectors.toList());

        List<Order> page0 = pageByKeyset(sorted, null, 3);          // first page: no filter yet
        double lastTotal = page0.get(page0.size() - 1).total;        // remember last row's key
        List<Order> page1 = pageByKeyset(sorted, lastTotal, 3);      // next page: filter on it

        System.out.println("Page 0: " + page0);
        System.out.println("Page 1 (total < " + lastTotal + "): " + page1);
    }
}
```

How to run: `java ScrollLevel2.java`

There is no `.skip(...)` anywhere — `page1` is produced purely by filtering on `lastTotal`, the sort-key value of the last row returned on `page0`. In a real database with an index on `total`, this filter lets the engine jump straight to the right starting point instead of scanning past every earlier row, unlike the `OFFSET` version in Level 1.

### Level 3 — Advanced

Wrap keyset paging in a loop that keeps scrolling until a page comes back short (fewer rows than requested, meaning no more data), matching how a real `Window<T>`-driven scroll loop terminates.

```java
import java.util.*;
import java.util.stream.*;

class Order {
    long id; double total;
    Order(long id, double total) { this.id = id; this.total = total; }
    public String toString() { return "{id=" + id + ", total=" + total + "}"; }
}

// Stands in for org.springframework.data.domain.Window<Order>
record OrderWindow(List<Order> content, boolean hasNext) {}

public class ScrollLevel3 {
    static OrderWindow pageByKeyset(List<Order> sorted, Double lastTotal, int size) {
        List<Order> matched = sorted.stream()
            .filter(o -> lastTotal == null || o.total < lastTotal)
            .limit(size + 1) // fetch one extra to detect a next page, same trick as Slice
            .collect(Collectors.toList());
        boolean hasNext = matched.size() > size;
        List<Order> content = hasNext ? matched.subList(0, size) : matched;
        return new OrderWindow(content, hasNext);
    }

    public static void main(String[] args) {
        List<Order> sorted = IntStream.rangeClosed(1, 10)
            .mapToObj(i -> new Order(i, 1000 - i * 10.0))
            .sorted(Comparator.comparingDouble((Order o) -> o.total).reversed())
            .collect(Collectors.toList());

        Double lastTotal = null;
        int pageNum = 0;
        while (true) {
            OrderWindow window = pageByKeyset(sorted, lastTotal, 4);
            System.out.println("Page " + pageNum + ": " + window.content() + " (hasNext=" + window.hasNext() + ")");
            if (window.content().isEmpty()) break;
            lastTotal = window.content().get(window.content().size() - 1).total;
            pageNum++;
            if (!window.hasNext()) break; // last page reached, stop scrolling
        }
    }
}
```

How to run: `java ScrollLevel3.java`

The `while` loop keeps calling `pageByKeyset` with each page's last `total` as the next filter, exactly like repeatedly calling `orderRepository.findBy(..., q -> q.limit(4)).scroll()` with an updated `ScrollPosition` in a real Spring Data repository — it stops naturally once a page reports `hasNext=false`, having walked through all 10 orders in 3 pages (4, 4, 2) without ever using an `OFFSET`.

## 6. Walkthrough

Execution starts in `main` with `sorted` holding 10 orders with descending totals (990, 980, ..., 900) and `lastTotal = null`, `pageNum = 0`.

**Iteration 1**: `pageByKeyset(sorted, null, 4)` runs — since `lastTotal` is `null`, every order passes the filter; `limit(5)` (size+1) takes the first 5, so `matched.size() == 5 > 4`, meaning `hasNext = true`, and `content` is trimmed to the first 4 (totals 990, 980, 970, 960). This is printed, `lastTotal` becomes `960.0` (the last content row's total), and `pageNum` becomes 1. Since `hasNext` was `true`, the loop continues.

**Iteration 2**: `pageByKeyset(sorted, 960.0, 4)` runs — the filter `total < 960.0` now excludes the first 4 orders already seen, leaving 6 candidates; `limit(5)` takes 5 of them, `hasNext = true` again, `content` is the next 4 (950, 940, 930, 920). `lastTotal` becomes `920.0`, `pageNum` becomes 2.

**Iteration 3**: `pageByKeyset(sorted, 920.0, 4)` runs — only 2 orders remain below `920.0` (910, 900); `matched.size() == 2`, which is not greater than 4, so `hasNext = false` and `content` is those 2 rows as-is. This is printed, and since `hasNext` is now `false`, the loop breaks.

```
iter1: filter none      -> [990,980,970,960] hasNext=true  -> lastTotal=960
iter2: filter <960       -> [950,940,930,920] hasNext=true  -> lastTotal=920
iter3: filter <920       -> [910,900]         hasNext=false -> loop stops
```

In a real Spring Data JPA repository, each iteration corresponds to one call to a `findBy(...)`-based scroll query: `orderRepository.findBy(spec, q -> q.sortBy(Sort.by("total").descending()).limit(4)).scroll(ScrollPosition.keyset())`, returning a `Window<Order>` whose `.positionAt(...)` gives the `ScrollPosition` to pass into the next call — the SQL executed each time is `SELECT * FROM orders WHERE total < ? ORDER BY total DESC LIMIT 5`, with `?` bound to the previous page's last value, letting an index on `total` skip straight to the right rows regardless of how many pages have already been walked.

## 7. Gotchas & takeaways

> Gotcha: keyset pagination requires the sort key (or combination of keys) to be unique enough to produce a stable, unambiguous ordering — sorting only by a non-unique column like `status` without a tiebreaker (e.g., `id`) can cause rows with identical values to be skipped or repeated across pages.

- Keyset pagination (`scroll`/`Window`) filters on the last-seen row's sort key instead of skipping N rows with `OFFSET` — the database can jump straight there via an index.
- It scales far better than offset paging for deep pages or large, frequently-changing tables.
- It's naturally suited to "next batch"/infinite-scroll APIs; it doesn't support jumping to an arbitrary page number the way offset paging does.
- Always sort by a key (or key combination) that's unique enough to guarantee a stable order — otherwise pages can miss or repeat rows.
