---
card: java
gi: 806
slug: deque
title: Deque
---

## 1. What it is

`Deque<T>` ("deck," short for **d**ouble-**e**nded **queue**) is the [`Queue`](0805-queue.md) subtype that supports insertion and removal at **both ends** — the head and the tail — each in O(1) for the standard implementation, `ArrayDeque`. It offers matching pairs of methods for each end: `addFirst`/`addLast`, `offerFirst`/`offerLast`, `removeFirst`/`removeLast`, `pollFirst`/`pollLast`, `peekFirst`/`peekLast`. Because a stack (last-in-first-out) is just "always push and pop from the same end," `Deque` also directly supports stack operations — `push` (alias for `addFirst`), `pop` (alias for `removeFirst`), and `peek` (alias for `peekFirst`) — making `ArrayDeque` the JDK's recommended replacement for the legacy [`Vector`](0814-vector-legacy-synchronized.md)-based `Stack` class.

## 2. Why & when

A plain `Queue` only ever adds at the tail and removes from the head; a plain [`List`](0802-list.md) can technically insert/remove at either end but pays O(n) for operations at the front (`ArrayList`) or loses random-access speed entirely (`LinkedList` still walks pointers). `Deque` exists for anything that genuinely needs cheap operations at **both** ends: browser back/forward history, undo/redo stacks, sliding-window algorithms, and work-stealing task queues all fit this shape. Reach for `ArrayDeque` whenever a structure alternates between "add/remove from the front" and "add/remove from the back" — it's faster and more memory-efficient than `LinkedList` for nearly every use case, including as a plain stack or plain FIFO queue.

## 3. Core concept

```java
Deque<String> history = new ArrayDeque<>();
history.push("home.html");    // addFirst — treat the deque as a stack
history.push("products.html");
history.push("cart.html");

history.peek();               // "cart.html" — the most recent page
history.pop();                // "cart.html" — go back one page

history.addLast("checkout.html"); // also usable as a plain queue/list from the other end
history.peekLast();               // "checkout.html"
```

The same `Deque` object can be treated as a stack (via `push`/`pop`/`peek`, all operating on the front) or as a double-ended list (via the explicit `First`/`Last` methods) — the interface doesn't force a single mental model.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Deque supports insertion and removal at both the front and the back">
  <g font-family="sans-serif">
    <rect x="230" y="60" width="90" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="275" y="90" fill="#e6edf3" font-size="10" text-anchor="middle">products</text>
    <rect x="320" y="60" width="90" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="365" y="90" fill="#e6edf3" font-size="10" text-anchor="middle">cart</text>
  </g>

  <line x1="230" y1="85" x2="160" y2="85" stroke="#79c0ff" stroke-width="2" marker-end="url(#a806a)"/>
  <text x="140" y="60" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">addFirst /</text>
  <text x="140" y="72" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">removeFirst</text>

  <line x1="410" y1="85" x2="480" y2="85" stroke="#f0883e" stroke-width="2" marker-end="url(#a806b)"/>
  <text x="500" y="60" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">addLast /</text>
  <text x="500" y="72" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">removeLast</text>

  <text x="320" y="145" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Both ends support O(1) insertion and removal — unlike a List's front, unlike a Queue's tail-only insert</text>

  <defs>
    <marker id="a806a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M6,0 L0,3 L6,6 Z" fill="#79c0ff"/></marker>
    <marker id="a806b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

*Both ends of a `Deque` support O(1) insertion and removal — the key capability neither a plain `List`'s front nor a plain `Queue` provides.*

## 5. Runnable example

Scenario: browser navigation history, growing from a simple undo stack to full back/forward navigation to a bounded "recently visited" ring buffer that evicts old entries automatically.

### Level 1 — Basic

```java
import java.util.*;

public class BrowserHistoryBasic {
    public static void main(String[] args) {
        Deque<String> history = new ArrayDeque<>();
        history.push("home.html");
        history.push("products.html");
        history.push("cart.html");

        System.out.println("current page: " + history.peek());
        System.out.println("go back: " + history.pop());
        System.out.println("current page now: " + history.peek());
    }
}
```

**How to run:** `java BrowserHistoryBasic.java` (JDK 17+).

Expected output:
```
current page: cart.html
go back: cart.html
current page now: products.html
```

Used purely as a stack here: `push` and `pop` both operate on the front of the deque, giving last-in-first-out "back" navigation — the most recently visited page is always what `peek`/`pop` return.

### Level 2 — Intermediate

```java
import java.util.*;

public class BrowserHistoryBackForward {
    public static void main(String[] args) {
        Deque<String> back = new ArrayDeque<>();   // pages behind the current one
        Deque<String> forward = new ArrayDeque<>(); // pages ahead, if we've gone back
        String current = "home.html";

        // Visit two new pages.
        back.push(current); current = "products.html";
        back.push(current); current = "cart.html";

        // Go back once: current page moves to "forward", previous page becomes current.
        forward.push(current);
        current = back.pop();
        System.out.println("after going back, current: " + current);

        // Go forward again: reverse of the above.
        back.push(current);
        current = forward.pop();
        System.out.println("after going forward, current: " + current);

        System.out.println("back stack: " + back + ", forward stack: " + forward);
    }
}
```

**How to run:** `java BrowserHistoryBackForward.java`.

Expected output:
```
after going back, current: products.html
after going forward, current: cart.html
back stack: [products.html, home.html], forward stack: []
```

The real-world concern added: real back/forward navigation needs **two** deques — visiting a new page clears any "forward" history (since you've branched off the old path), going back moves the current page onto `forward` and pops the previous one off `back`, and going forward reverses that exact exchange. This mirrors how real browsers implement history.

### Level 3 — Advanced

```java
import java.util.*;

public class RecentlyVisitedRingBuffer {

    static class BoundedHistory {
        private final Deque<String> recent = new ArrayDeque<>();
        private final int capacity;

        BoundedHistory(int capacity) {
            this.capacity = capacity;
        }

        void visit(String page) {
            recent.addFirst(page);           // newest goes to the front
            if (recent.size() > capacity) {
                recent.removeLast();          // evict the oldest when over capacity
            }
        }

        List<String> mostRecentFirst() {
            return new ArrayList<>(recent);
        }
    }

    public static void main(String[] args) {
        BoundedHistory history = new BoundedHistory(3);
        for (String page : List.of("home.html", "products.html", "cart.html", "checkout.html", "receipt.html")) {
            history.visit(page);
            System.out.println("visited " + page + " -> recent: " + history.mostRecentFirst());
        }
    }
}
```

**How to run:** `java RecentlyVisitedRingBuffer.java`.

Expected output:
```
visited home.html -> recent: [home.html]
visited products.html -> recent: [products.html, home.html]
visited cart.html -> recent: [cart.html, products.html, home.html]
visited checkout.html -> recent: [checkout.html, cart.html, products.html]
visited receipt.html -> recent: [receipt.html, checkout.html, cart.html]
```

This adds the production-flavored hard case: a **bounded, self-evicting** structure — a "recently visited pages" widget that should only ever show the last 3 pages. `addFirst` inserts the newest visit at the front; once the deque grows past capacity, `removeLast` evicts the oldest entry from the opposite end. Using both ends of the same `Deque` this way (insert-front, evict-back) is exactly the operation a `List` alone can't do cheaply — removing the last element of an `ArrayList` is O(1), but a `List`'s "remove the logical oldest" only stays O(1) if oldest is defined as the tail, which conveniently it is here.

## 6. Walkthrough

Tracing `RecentlyVisitedRingBuffer.main` across the loop's five iterations:

1. `visit("home.html")` calls `recent.addFirst("home.html")`, making `recent = [home.html]`; size (1) is not over capacity (3), so nothing is evicted.
2. `visit("products.html")` and `visit("cart.html")` follow the same pattern, each time inserting at the front — after three visits, `recent = [cart.html, products.html, home.html]`, exactly at capacity.
3. `visit("checkout.html")` calls `addFirst`, making the deque temporarily hold four elements: `[checkout.html, cart.html, products.html, home.html]`. Since `size() (4) > capacity (3)`, `removeLast()` evicts `home.html` — the oldest visit — bringing the deque back to exactly 3 elements: `[checkout.html, cart.html, products.html]`.
4. `visit("receipt.html")` repeats the same insert-then-evict pattern, evicting `products.html` this time, leaving `[receipt.html, checkout.html, cart.html]`.
5. After each visit, `mostRecentFirst()` copies the deque's current contents into an `ArrayList` (so callers get a stable snapshot, not a live view) and the loop prints it — showing the "recently visited" list always capped at 3 entries, newest first, oldest silently dropped once the cap is exceeded.

## 7. Gotchas & takeaways

> **Gotcha:** `ArrayDeque` does **not allow `null` elements** — `push(null)` or `addFirst(null)` throws `NullPointerException` immediately, unlike `LinkedList` (also a `Deque`) which does permit `null`. If a deque might need to represent "no value," use `Optional` or a sentinel object instead of relying on `null`.

- `Deque<T>` supports O(1) insertion and removal at both the head and tail — the capability neither `List`'s front nor `Queue`'s tail-only model offers cheaply.
- `push`/`pop`/`peek` are stack aliases for `addFirst`/`removeFirst`/`peekFirst` — `ArrayDeque` is the JDK-recommended replacement for the legacy `Stack` class.
- The explicit `*First`/`*Last` method pairs let the same object serve double-ended use cases like back/forward navigation.
- A bounded, self-evicting structure ("keep only the last N") is naturally expressed as insert-one-end, evict-the-other-end on a single `Deque`.
- `ArrayDeque` disallows `null` elements; `LinkedList` (also a valid `Deque`) permits them — a difference worth checking before choosing an implementation.
