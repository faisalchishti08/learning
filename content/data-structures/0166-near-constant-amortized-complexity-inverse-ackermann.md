---
card: data-structures
gi: 166
slug: near-constant-amortized-complexity-inverse-ackermann
title: Near-constant amortized complexity (inverse Ackermann)
---

## 1. What it is

When a disjoint-set structure uses both [union by rank/size](0164-union-by-rank-size.md) and [path compression](0165-path-compression.md), a sequence of `m` `find`/`union` operations on `n` items costs `O(m * α(n))` total, where `α` (alpha) is the **inverse Ackermann function**. `α(n)` grows so slowly that for every value of `n` you could ever store in a computer, `α(n) <= 4`. In practice, this means each operation runs in **essentially constant time**.

## 2. Why & when

You don't need to compute `α(n)` yourself — no library provides it, because it is never the bottleneck. What matters is knowing *why* the combination of both optimizations gives a stronger guarantee than either alone, and that "amortized" here means "the total cost of `m` operations, divided by `m`," not "every single operation individually." This matters when you defend a design choice ("why is union-find fast enough for a million edges?") or when you read complexity claims in papers or interview answers.

## 3. Core concept

**What "amortized" means here.** A single `find` call, mid-sequence, can still cost more than `O(1)` if it happens to walk a currently-tall path. But averaged over the **whole sequence** of operations, the cost per operation is bounded by `O(α(n))`. This is the same style of guarantee as [amortized array doubling](0004-amortized-analysis-dynamic-array-doubling.md) — individual operations vary, but the total is tightly bounded.

**Why union by rank/size alone gives `O(log n)`.** It bounds tree height to `log2(n)`, so every `find` costs at most that many steps — a real, non-amortized bound, but not as tight as what compression adds.

**Why path compression alone gives close to `O(log n)` amortized.** Even without rank/size, repeated compression on the same nodes flattens trees quickly, and a known (harder) analysis shows this alone achieves `O(log n)` amortized per operation.

**Why combining both is qualitatively different.** With both techniques, no tree can regrow tall for long: the rank-based bound stops trees from *becoming* deep during merges, and compression flattens any path a `find` actually visits. The interaction between these two effects is what the inverse Ackermann analysis captures, and it produces a bound so slow-growing that for all practical `n` (up to numbers far larger than the number of atoms in the observable universe), `α(n)` never exceeds `4` or `5`.

**What the inverse Ackermann function is, briefly.** The Ackermann function `A(m, n)` is a famous example of a function that grows faster than any exponential, tower-of-exponentials, or repeated exponential — it is one of the fastest-growing computable functions used in complexity analysis. Its inverse, `α(n)`, is correspondingly one of the **slowest**-growing functions ever used in a real complexity bound. That is why "near-constant" is the accurate, practical way to describe `O(α(n))` — not "technically not constant, so treat it as slow."

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A growth-rate comparison chart showing inverse Ackermann growing far slower than log n, which grows far slower than n">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <line x1="40" y1="170" x2="600" y2="170" stroke="#8b949e"/>
    <line x1="40" y1="20" x2="40" y2="170" stroke="#8b949e"/>
    <text x="320" y="190" text-anchor="middle" font-size="9">n (number of items) --&gt;</text>

    <path d="M 40 170 L 600 20" stroke="#f44336" fill="none" stroke-width="2"/>
    <text x="560" y="30" fill="#f44336" font-size="9">O(n)</text>

    <path d="M 40 170 Q 300 100 600 70" stroke="#f0883e" fill="none" stroke-width="2"/>
    <text x="560" y="80" fill="#f0883e" font-size="9">O(log n)</text>

    <path d="M 40 170 Q 300 165 600 160" stroke="#3fb950" fill="none" stroke-width="2"/>
    <text x="500" y="152" fill="#3fb950" font-size="9">O(alpha(n)) -- stays &lt;= 4 always</text>
  </g>
</svg>

Inverse Ackermann barely rises off the x-axis even as `n` grows without bound — this is what "near-constant" looks like.

## 5. Runnable example

```java
// AmortizedComplexity.java
public class AmortizedComplexity {

    static class OptimizedDSU {
        int[] parent, rank;
        long totalFindSteps = 0; // instrumented to measure real per-operation cost

        OptimizedDSU(int n) {
            parent = new int[n];
            rank = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }

        int find(int x) {
            int steps = 0;
            int root = x;
            while (parent[root] != root) { root = parent[root]; steps++; }
            // path compression: repoint every visited node directly to root
            while (parent[x] != root) {
                int next = parent[x];
                parent[x] = root;
                x = next;
            }
            totalFindSteps += steps;
            return root;
        }

        void union(int x, int y) {
            int rootX = find(x), rootY = find(y);
            if (rootX == rootY) return;
            if (rank[rootX] < rank[rootY]) parent[rootX] = rootY;
            else if (rank[rootX] > rank[rootY]) parent[rootY] = rootX;
            else { parent[rootY] = rootX; rank[rootX]++; }
        }
    }

    // Basic: measure average find cost on a small union-find sequence.
    static void basicLevel() {
        int n = 1000;
        OptimizedDSU dsu = new OptimizedDSU(n);
        for (int i = 1; i < n; i++) dsu.union(i - 1, i);
        for (int i = 0; i < n; i++) dsu.find(i);

        double avgSteps = (double) dsu.totalFindSteps / n;
        System.out.printf("basic: n=%d, average steps per find -> %.3f%n", n, avgSteps);
    }

    // Intermediate: scale n up by 100x and show the average steps per find barely changes.
    static void intermediateLevel() {
        int n = 100_000;
        OptimizedDSU dsu = new OptimizedDSU(n);
        for (int i = 1; i < n; i++) dsu.union(i - 1, i);
        for (int i = 0; i < n; i++) dsu.find(i);

        double avgSteps = (double) dsu.totalFindSteps / n;
        System.out.printf("intermediate: n=%d, average steps per find -> %.3f%n", n, avgSteps);
    }

    // Advanced: interleave random unions and finds (closer to real-world usage) and confirm the average stays tiny.
    static void advancedLevel() {
        int n = 50_000;
        OptimizedDSU dsu = new OptimizedDSU(n);
        java.util.Random rand = new java.util.Random(42);

        for (int op = 0; op < n * 3; op++) {
            int a = rand.nextInt(n), b = rand.nextInt(n);
            if (op % 2 == 0) dsu.union(a, b);
            else dsu.find(a);
        }

        double avgSteps = (double) dsu.totalFindSteps / (n * 3 / 2);
        System.out.printf("advanced: n=%d, random ops, average steps per find -> %.3f%n", n, avgSteps);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java AmortizedComplexity.java`

## 6. Walkthrough

Run `basicLevel()` with `n = 1000` items, unioned into one chain, then `find` called on every item. The very first `find` calls (on the deepest original nodes) cost more steps, but each one flattens the path it visits. By the time all `1000` finds have run, the total step count divided by `1000` gives a small average — nowhere near `1000` or even `log2(1000) ≈ 10`.

Run `intermediateLevel()` with `n = 100,000` — a 100x larger input. If the cost were `O(log n)` per operation, the average should roughly double (since `log2(100,000) ≈ 17` vs `log2(1,000) ≈ 10`). If it behaves like `O(α(n))`, the average should barely move at all, because `α` is essentially flat across this entire range of `n`. Running both and comparing the printed averages is the empirical way to see the inverse-Ackermann bound in action, rather than just taking it on faith.

Run `advancedLevel()` with random interleaved unions and finds on `50,000` items — closer to how union-find is actually used in real algorithms like Kruskal's MST. The average steps per `find` stays small throughout, confirming the near-constant behavior holds under realistic, non-adversarial usage too.

**Complexity.** `O(α(n))` amortized per operation, for a sequence of `m` operations on `n` items, when both union by rank/size and path compression are used together. Since `α(n) <= 4` for any `n` you will ever encounter, this is treated as `O(1)` amortized in practice.

## 7. Gotchas & takeaways

> "Near-constant" is not the same as "constant." A single, unlucky `find` call can still cost more than `O(1)` — the guarantee is about the **total** cost over a sequence of operations, not any one call in isolation. Don't use union-find where you need a hard per-call latency bound (e.g. a real-time system with strict per-operation deadlines).

- You will never need to compute `α(n)` by hand — its only practical use is as the theoretical justification for why union-find "is basically `O(1)`" in complexity discussions.
- This bound requires **both** optimizations together. Either one alone still gives a solid `O(log n)`-class bound, but the combination is what unlocks the inverse-Ackermann result.
- When explaining this in an interview, "amortized near-constant, technically `O(α(n))`, in practice treated as `O(1)`" is the complete, correct answer — no need to explain the Ackermann function's definition unless asked.
