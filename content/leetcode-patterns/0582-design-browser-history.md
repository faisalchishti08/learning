---
card: leetcode-patterns
gi: 582
slug: design-browser-history
title: Design Browser History
---

## 1. What it is

Design a `BrowserHistory` class modeling a browser's back/forward navigation. `BrowserHistory(homepage)` starts on `homepage`. `visit(url)` visits `url` from the current page **and clears all forward history**. `back(steps)` moves back up to `steps` pages (clamped to the oldest page) and returns the resulting URL. `forward(steps)` moves forward up to `steps` pages (clamped to the newest page) and returns the resulting URL. Example: `BrowserHistory("leetcode.com")`, `visit("google.com")`, `visit("facebook.com")`, `back(1)` → `"google.com"`, `forward(1)` → `"facebook.com"`, `visit("youtube.com")` (clears any forward history), `forward(2)` → `"youtube.com"` (nothing to go forward to).

## 2. Why & when

The defining behavior is that a fresh `visit` **discards** all forward history — you cannot go forward to pages you navigated away from by visiting somewhere new, only by using `back`. This rules out a plain doubly linked list of all visited URLs ever (which would need to delete a whole suffix on every `visit`, an O(n) operation in the worst case) in favor of a resizable array with a single current-position pointer, where "clearing forward history" is just truncating the array, an O(1) amortized operation relative to the discarded pages, and O(1) to *initiate*.

## 3. Core concept

**Key idea:** store visited URLs in an `ArrayList` and track the current position with an integer index, `current`. Forward history is implicitly "everything in the list after `current`" — no separate structure is needed to represent it.

**Steps:**
1. `visit(url)`: truncate the list to keep only indices `0..current` (discard everything after), append `url`, and advance `current` to point at it.
2. `back(steps)`: move `current` back by `steps`, clamped to a minimum of `0` (the oldest page). Return the URL at the new `current`.
3. `forward(steps)`: move `current` forward by `steps`, clamped to a maximum of `list.size() - 1` (the newest page). Return the URL at the new `current`.

**Why truncating on visit, not deleting one-by-one, is correct:** the problem only ever needs "everything after `current`" to vanish as a unit, and a fresh visit is the only event that triggers this — there is no requirement to selectively keep some forward pages and drop others, so a single truncate-then-append operation captures the entire rule.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An array of visited URLs with a current pointer; visiting a new URL truncates everything after the pointer">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#8b949e" font-size="11">before visit("youtube.com"), current at index 1:</text>
    <rect x="20" y="30" width="120" height="35" fill="#161b22" stroke="#30363d"/><text x="80" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">leetcode.com</text>
    <rect x="150" y="30" width="120" height="35" fill="#161b22" stroke="#3fb950"/><text x="210" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">google.com (current)</text>
    <rect x="280" y="30" width="120" height="35" fill="#161b22" stroke="#f85149" stroke-dasharray="3,2"/><text x="340" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">facebook.com (discarded)</text>
    <text x="20" y="110" fill="#8b949e" font-size="11">after visit("youtube.com"):</text>
    <rect x="20" y="120" width="120" height="35" fill="#161b22" stroke="#30363d"/><text x="80" y="142" fill="#e6edf3" text-anchor="middle" font-size="10">leetcode.com</text>
    <rect x="150" y="120" width="120" height="35" fill="#161b22" stroke="#30363d"/><text x="210" y="142" fill="#e6edf3" text-anchor="middle" font-size="10">google.com</text>
    <rect x="280" y="120" width="120" height="35" fill="#161b22" stroke="#3fb950"/><text x="340" y="142" fill="#e6edf3" text-anchor="middle" font-size="10">youtube.com (current)</text>
  </g>
</svg>

Everything after `current` is discarded in one step, then the new URL is appended — forward history to `facebook.com` is gone, matching the rule that visiting clears it.

## 5. Runnable example

**Level 1 — Brute force.** Use a doubly linked list for "unlimited" history and, on every `visit`, walk forward from `current` deleting nodes one by one until reaching the end. O(k) per visit, where `k` is the number of discarded forward pages — correct, but more bookkeeping than necessary.

**KEY INSIGHT:** an `ArrayList` with a single `current` index represents "back" and "forward" implicitly as index arithmetic, and Java's `List.subList(...).clear()` (or an equivalent truncation) discards the forward suffix in one call, with no manual node-by-node deletion.

**Level 2 — Optimal.** `ArrayList<String>` plus an integer `current`, O(1) for `back`/`forward` (pure arithmetic and a get-by-index), O(k) for `visit` proportional to the discarded suffix (unavoidable, since those entries must be removed).

**Level 3 — Hardened.** Clamps `back`/`forward` correctly at both history boundaries (index `0` and the last index) instead of throwing on out-of-range `steps`.

```java
// BrowserHistory.java
import java.util.*;

public class BrowserHistory {

    private final List<String> history = new ArrayList<>();
    private int current;

    public BrowserHistory(String homepage) {
        history.add(homepage);
        current = 0;
    }

    public void visit(String url) {
        // Discard everything after current, then append the new page.
        while (history.size() - 1 > current) {
            history.remove(history.size() - 1);
        }
        history.add(url);
        current++;
    }

    public String back(int steps) {
        current = Math.max(0, current - steps);
        return history.get(current);
    }

    public String forward(int steps) {
        current = Math.min(history.size() - 1, current + steps);
        return history.get(current);
    }

    public static void main(String[] args) {
        BrowserHistory bh = new BrowserHistory("leetcode.com");
        bh.visit("google.com");
        bh.visit("facebook.com");
        System.out.println(bh.back(1));    // google.com
        System.out.println(bh.forward(1)); // facebook.com
        bh.visit("youtube.com");           // clears forward history past current
        System.out.println(bh.forward(2)); // youtube.com, nothing further to go to
        System.out.println(bh.back(2));    // leetcode.com, clamped at the oldest page
    }
}
```

**How to run:** save as `BrowserHistory.java`, then run `java BrowserHistory.java`.

## 6. Walkthrough

Trace `visit("google.com")`, `visit("facebook.com")`, `back(1)`, `visit("youtube.com")`:

| call | history | current | return |
|---|---|---|---|
| (start) | [leetcode.com] | 0 | — |
| visit(google.com) | [leetcode.com, google.com] | 1 | — |
| visit(facebook.com) | [leetcode.com, google.com, facebook.com] | 2 | — |
| back(1) | (unchanged) | 1 | google.com |
| visit(youtube.com) | truncate past index 1 -> [leetcode.com, google.com]; append -> [leetcode.com, google.com, youtube.com] | 2 | — |

`back(1)` only moves the pointer; the list is untouched, so `facebook.com` is still there in case of a later `forward`. But `visit("youtube.com")` truncates it away first, then appends — matching the rule that a fresh visit clears forward history.

## 7. Gotchas & takeaways

> Gotcha: implementing `visit` as a plain `history.add(url)` without first truncating leaves stale forward pages in the list — a later `forward` call would incorrectly resurrect a page that a real browser would have discarded.

- Signal: "back/forward navigation, and a new action clears the forward path" is the single-array-plus-current-pointer signal — forward history is implicit, not a separately stored structure.
- Clamp `back`/`forward` at both ends (`0` and `size() - 1`); the problem defines `steps` beyond the available history as "go as far as possible," not an error.
- Related problems: Design Circular Queue (a fixed-capacity structure with its own wraparound-clamping logic).
