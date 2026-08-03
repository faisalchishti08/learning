---
card: data-structures
gi: 170
slug: skip-list
title: Skip list
---

## 1. What it is

A **skip list** is a sorted linked list with extra "express lane" layers stacked on top. The bottom layer holds every element in sorted order, like a normal linked list. Each layer above it holds a random subset of the layer below, letting a search skip over many elements at once instead of visiting them one by one.

## 2. Why & when

A plain sorted linked list needs `O(n)` to search, since you can only walk forward one node at a time. A skip list keeps that same simple linked-list structure but adds randomized shortcuts, achieving `O(log n)` expected search, insert, and delete — competitive with a balanced tree like a [red-black tree](0111-red-black-trees.md), but with a much simpler implementation (no rotations). Redis's sorted sets use skip lists internally for exactly this reason.

## 3. Core concept

**The shape.** Multiple linked lists stacked in levels, level `0` at the bottom containing every element. A node present at level `k` is also present at every level below it. Each node has a "height" — how many levels it appears in — chosen randomly when it is inserted (commonly: keep flipping a coin, add a level for each "heads", stop on the first "tails").

**The invariant.** Higher levels always contain a strict subset of the elements in the level below. Roughly half the nodes at any level continue to the next level up, so level `k` has roughly `n / 2^k` nodes.

**Why it makes search fast.** To search for a value, start at the top-left corner (the highest level's head node). Move right while the next node's value is still less than the target; if moving right would overshoot, drop down one level and repeat. Because each level roughly halves the number of nodes to scan, this behaves like binary search over a linked structure — `O(log n)` expected levels, each with `O(1)` expected horizontal moves before dropping down.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A skip list with three levels, showing a search path that skips ahead on higher levels before dropping down">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">L2:</text>
    <circle cx="60" cy="20" r="4" fill="#79c0ff"/><line x1="60" y1="20" x2="300" y2="20" stroke="#79c0ff"/>
    <circle cx="300" cy="20" r="4" fill="#79c0ff"/>
    <text x="60" y="14" font-size="8">1</text><text x="300" y="14" font-size="8">30</text>

    <text x="10" y="80">L1:</text>
    <circle cx="60" cy="80" r="4" fill="#79c0ff"/><line x1="60" y1="80" x2="180" y2="80" stroke="#79c0ff"/>
    <circle cx="180" cy="80" r="4" fill="#79c0ff"/><line x1="180" y1="80" x2="300" y2="80" stroke="#79c0ff"/>
    <circle cx="300" cy="80" r="4" fill="#79c0ff"/>
    <text x="60" y="74" font-size="8">1</text><text x="180" y="74" font-size="8">15</text><text x="300" y="74" font-size="8">30</text>

    <text x="10" y="140">L0:</text>
    <circle cx="60" cy="140" r="4" fill="#e6edf3"/><line x1="60" y1="140" x2="120" y2="140" stroke="#8b949e"/>
    <circle cx="120" cy="140" r="4" fill="#e6edf3"/><line x1="120" y1="140" x2="180" y2="140" stroke="#8b949e"/>
    <circle cx="180" cy="140" r="4" fill="#e6edf3"/><line x1="180" y1="140" x2="240" y2="140" stroke="#8b949e"/>
    <circle cx="240" cy="140" r="4" fill="#e6edf3"/><line x1="240" y1="140" x2="300" y2="140" stroke="#8b949e"/>
    <circle cx="300" cy="140" r="4" fill="#e6edf3"/>
    <text x="60" y="134" font-size="8">1</text><text x="120" y="134" font-size="8">8</text><text x="180" y="134" font-size="8">15</text><text x="240" y="134" font-size="8">22</text><text x="300" y="134" font-size="8">30</text>

    <path d="M 60 20 L 300 20 L 300 80 L 300 140" stroke="#f0883e" stroke-width="2" fill="none" stroke-dasharray="4,2"/>
    <text x="320" y="120" font-size="9" fill="#f0883e">search(30): jump L2 to 30 directly,</text>
    <text x="320" y="135" font-size="9" fill="#f0883e">skipping 8, 15, 22 entirely</text>
  </g>
</svg>

Higher levels skip over many bottom-level nodes; the search only drops down when it would overshoot.

## 5. Runnable example

```java
// SkipList.java
import java.util.*;

public class SkipList {

    // Basic: a skip list supporting insert and search, with randomized level assignment.
    static class SkipListImpl {
        static final int MAX_LEVEL = 16;
        static final double P = 0.5;

        class Node {
            int value;
            Node[] next;
            Node(int value, int level) { this.value = value; next = new Node[level + 1]; }
        }

        Node head = new Node(Integer.MIN_VALUE, MAX_LEVEL);
        int level = 0;
        Random random = new Random(7);

        int randomLevel() {
            int lvl = 0;
            while (random.nextDouble() < P && lvl < MAX_LEVEL) lvl++;
            return lvl;
        }

        void insert(int value) {
            Node[] update = new Node[MAX_LEVEL + 1];
            Node current = head;
            for (int i = level; i >= 0; i--) {
                while (current.next[i] != null && current.next[i].value < value) current = current.next[i];
                update[i] = current;
            }
            int newLevel = randomLevel();
            if (newLevel > level) {
                for (int i = level + 1; i <= newLevel; i++) update[i] = head;
                level = newLevel;
            }
            Node newNode = new Node(value, newLevel);
            for (int i = 0; i <= newLevel; i++) {
                newNode.next[i] = update[i].next[i];
                update[i].next[i] = newNode;
            }
        }

        boolean search(int value) {
            Node current = head;
            for (int i = level; i >= 0; i--) {
                while (current.next[i] != null && current.next[i].value < value) current = current.next[i];
            }
            current = current.next[0];
            return current != null && current.value == value;
        }
    }

    static void basicLevel() {
        SkipListImpl list = new SkipListImpl();
        for (int v : new int[]{1, 8, 15, 22, 30}) list.insert(v);

        System.out.println("basic: search(15) -> " + list.search(15));
        System.out.println("basic: search(99) -> " + list.search(99));
    }

    // Intermediate: measure how many nodes at each level, showing the roughly-halving distribution.
    static void intermediateLevel() {
        SkipListImpl list = new SkipListImpl();
        for (int v = 0; v < 100; v++) list.insert(v * 3);

        int[] countPerLevel = new int[SkipListImpl.MAX_LEVEL + 1];
        for (int lvl = 0; lvl <= list.level; lvl++) {
            SkipListImpl.Node node = list.head.next[lvl];
            while (node != null) { countPerLevel[lvl]++; node = node.next[lvl]; }
        }
        System.out.println("intermediate: node counts per level -> " + Arrays.toString(Arrays.copyOf(countPerLevel, list.level + 1)));
    }

    // Advanced: delete, which must unlink the node from every level it appears in.
    static class DeletableSkipList extends SkipListImpl {
        boolean delete(int value) {
            Node[] update = new Node[MAX_LEVEL + 1];
            Node current = head;
            for (int i = level; i >= 0; i--) {
                while (current.next[i] != null && current.next[i].value < value) current = current.next[i];
                update[i] = current;
            }
            current = current.next[0];
            if (current == null || current.value != value) return false;

            for (int i = 0; i <= level; i++) {
                if (update[i].next[i] != current) break;
                update[i].next[i] = current.next[i];
            }
            while (level > 0 && head.next[level] == null) level--;
            return true;
        }
    }

    static void advancedLevel() {
        DeletableSkipList list = new DeletableSkipList();
        for (int v : new int[]{1, 8, 15, 22, 30}) list.insert(v);

        System.out.println("advanced: delete(15) -> " + list.delete(15));
        System.out.println("advanced: search(15) after delete -> " + list.search(15));
        System.out.println("advanced: search(22) still present -> " + list.search(22));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java SkipList.java`

## 6. Walkthrough

Insert `1, 8, 15, 22, 30` into an empty skip list. Each insert first walks the existing structure top-down to find where the new value belongs at every level (`update[]` records the node before the insertion point at each level), then flips coins to decide the new node's height, then splices it into every level from `0` up to that height.

Trace `search(30)`. Start at the head, at the highest active level. At that level, if there is a shortcut node with value `<= 30`, jump there directly (as the diagram shows, this can skip straight to `30` without visiting `8, 15, 22` at all). If the next node's value would overshoot `30`, drop down one level and repeat the scan from the current position. Once at level `0`, walk to the exact node and confirm its value equals `30`.

Trace `delete(15)`. Same top-down walk to find `update[]` at every level. At each level where `update[i].next[i]` actually equals the node being deleted, unlink it: `update[i].next[i] = node.next[i]`. Then shrink `level` downward if the topmost levels are now empty.

**Complexity.** Search, insert, delete: `O(log n)` expected (randomized, not worst-case guaranteed — an unlucky run of coin flips could in theory produce a taller or flatter structure, but this is exponentially unlikely). Space: `O(n)` expected, since the expected total node-level count is `2n`.

## 7. Gotchas & takeaways

> Skip lists give **expected** `O(log n)`, not guaranteed worst-case `O(log n)` like a balanced tree. In adversarial or pathological cases the randomization could produce a worse shape, but this is exponentially unlikely in practice and never observed in real systems at reasonable sizes.

- The probability `P = 0.5` and `MAX_LEVEL` are tuning parameters. Lower `P` (e.g. `0.25`) means fewer, taller shortcuts and a small memory saving; the standard choice is `0.5`.
- A skip list is a good alternative to a [red-black tree](0111-red-black-trees.md) or [AVL tree](0110-avl-trees-rotations.md) when you want ordered access with simpler code and no rotation logic — this is why Redis chose it for `ZSET`.
- Skip lists support range queries and ordered iteration naturally (just walk level `0`), the same strength a [TreeMap](0113-treemap-treeset-red-black-backed.md) has over a plain hash-based map.
