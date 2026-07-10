---
card: java
gi: 969
slug: nested-patterns
title: Nested patterns
---

## 1. What it is

Nested patterns are what you get when a record pattern's component sub-pattern is itself another record pattern, arbitrarily many levels deep — `Line(Point(int x1, int y1), Point(int x2, int y2))` nests two levels; a tree-shaped data structure processed recursively can, through repeated pattern matching at each recursive call, effectively handle unlimited depth, even though any single pattern expression itself has a fixed, finite nesting level written directly in the source code. The distinguishing challenge nested patterns raise beyond a single-level record pattern is combinatorial: when nested types are themselves [sealed](0961-sealed-permits-clauses.md) hierarchies (not just plain records), a `switch` matching several levels deep must account for every valid *combination* of variants at each level, and the compiler's exhaustiveness checking extends to verify all of these combinations are covered, not just the outer level.

## 2. Why & when

Nested patterns are essential for processing tree-shaped or recursively-structured data — abstract syntax trees, JSON-like nested documents, linked data structures — where the natural way to express "what should happen" genuinely depends on the *combination* of an outer node's kind and its children's kinds together, not just the outer node in isolation. Without nested patterns, processing such structures requires either deeply nested `if`/`switch` blocks (one level of dispatch per level of nesting, each requiring its own accessor calls to reach the next level down) or auxiliary helper methods purely to avoid that nesting — both noticeably more verbose and harder to read than a single, flat nested pattern expressing the same multi-level match directly. Recursive data structures specifically combine nested patterns with recursive function calls: a tree-processing function typically matches one or two levels of nesting explicitly in each `switch` case, then recurses into any remaining sub-structure by calling itself again — this is exactly the same technique used in the [sealed + records + pattern matching synergy](0963-sealed-records-pattern-matching-synergy.md) arithmetic-expression example, applied here specifically to genuinely tree-shaped, recursively-nested data.

## 3. Core concept

```
sealed interface Tree permits Leaf, Node {}
record Leaf(int value) implements Tree {}
record Node(Tree left, Tree right) implements Tree {}

// A pattern nesting exactly ONE level -- matches a Node whose LEFT child is
// specifically a Leaf, without yet knowing anything about the right child's shape:
case Node(Leaf(int leftValue), Tree right) -> ...

// A pattern nesting TWO levels -- both children specifically constrained to be Leaves:
case Node(Leaf(int lv), Leaf(int rv)) -> ...

// Combinatorial exhaustiveness: for a Node's two Tree-typed children, EACH child
// could independently be a Leaf OR a Node -- a switch distinguishing all combinations
// at depth 2 has up to 2 x 2 = 4 meaningful shape combinations to consider, though
// you rarely need to enumerate every combination explicitly -- a partial-depth
// pattern (like the ONE-level example above) plus recursion handles the rest.
```

Nested patterns let you match as many levels deep as your case actually needs to distinguish, while recursion (calling the same function again on an unmatched sub-structure) handles arbitrary remaining depth without needing an impossibly long, fully-enumerated pattern.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A binary tree of Node and Leaf variants, with a nested pattern matching two levels deep at the top, and recursion handling deeper, unmatched sub-trees below" >
  <rect x="260" y="10" width="120" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="29" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Node (root)</text>

  <rect x="120" y="60" width="110" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="175" y="79" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Leaf(3) -- matched</text>

  <rect x="410" y="60" width="110" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="465" y="79" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">Node -- NOT matched here</text>

  <rect x="360" y="110" width="110" height="30" fill="none" stroke="#8b949e" stroke-dasharray="3"/>
  <text x="415" y="129" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">handled via RECURSION</text>
  <rect x="480" y="110" width="110" height="30" fill="none" stroke="#8b949e" stroke-dasharray="3"/>
  <text x="535" y="129" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">handled via RECURSION</text>

  <line x1="290" y1="40" x2="175" y2="60" stroke="#8b949e"/>
  <line x1="350" y1="40" x2="465" y2="60" stroke="#8b949e"/>
  <line x1="440" y1="90" x2="415" y2="110" stroke="#8b949e" stroke-dasharray="3"/>
  <line x1="490" y1="90" x2="535" y2="110" stroke="#8b949e" stroke-dasharray="3"/>

  <text x="320" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">The pattern matches exactly as deep as this case needs; deeper structure recurses back through the same function</text>
</svg>

*A nested pattern matches a fixed depth explicitly; recursion handles whatever additional depth the tree actually has.*

## 5. Runnable example

Scenario: build a small binary tree evaluator using nested patterns and recursion, evolving from a basic single-level sealed tree, to a realistic sum-of-leaves function demonstrating recursive nested matching, to a more advanced case with a genuinely combinatorial two-level pattern optimizing a specific structural shape before falling back to plain recursion.

### Level 1 — Basic

```java
public class NestedPatternBasic {
    sealed interface Tree permits Leaf, Node {}
    record Leaf(int value) implements Tree {}
    record Node(Tree left, Tree right) implements Tree {}

    static int sum(Tree tree) {
        return switch (tree) {
            case Leaf(int v) -> v;
            case Node(Tree l, Tree r) -> sum(l) + sum(r); // recurse into EACH child
        };
    }

    public static void main(String[] args) {
        Tree tree = new Node(new Leaf(3), new Node(new Leaf(4), new Leaf(5)));
        System.out.println("sum: " + sum(tree));
    }
}
```

**How to run:** `java NestedPatternBasic.java` (JDK 21+; record patterns require Java 21+).

Expected output:
```
sum: 12
```

`sum` matches exactly one level deep at a time — a `Leaf` returns its value directly; a `Node` deconstructs into two `Tree`-typed children (`l`, `r`, deliberately left unspecialized) and recurses on each — this single, one-level pattern, combined with recursion, correctly handles a tree of any depth, since each recursive call independently re-matches whatever sub-tree it's given.

### Level 2 — Intermediate

```java
public class NestedPatternDepthTwo {
    sealed interface Tree permits Leaf, Node {}
    record Leaf(int value) implements Tree {}
    record Node(Tree left, Tree right) implements Tree {}

    static int sum(Tree tree) {
        return switch (tree) {
            // TWO-level nested pattern: an explicit fast path for a Node whose
            // children are BOTH Leaves, avoiding two separate recursive calls.
            case Node(Leaf(int lv), Leaf(int rv)) -> lv + rv;
            case Node(Tree l, Tree r) -> sum(l) + sum(r); // general case: recurse
            case Leaf(int v) -> v;
        };
    }

    public static void main(String[] args) {
        Tree shallow = new Node(new Leaf(3), new Leaf(4));         // matches the fast path
        Tree deep = new Node(new Leaf(3), new Node(new Leaf(4), new Leaf(5))); // falls to general case
        System.out.println("shallow sum: " + sum(shallow));
        System.out.println("deep sum: " + sum(deep));
    }
}
```

**How to run:** `java NestedPatternDepthTwo.java` (JDK 21+).

Expected output:
```
shallow sum: 7
deep sum: 12
```

The real-world concern added: the first case now nests two levels deep (`Node(Leaf(int lv), Leaf(int rv))`), directly destructuring both children's values when they're both leaves, entirely without a recursive call — this is purely an optimization for a common shallow-tree shape; the second, more general `Node(Tree l, Tree r)` case still handles any other `Node` shape (including one where a child is itself a deeper `Node`) via ordinary recursion, demonstrating that a more specific nested pattern can coexist with a more general fallback pattern, exactly like guarded patterns' priority-ordering.

### Level 3 — Advanced

```java
public class NestedPatternCombinatorial {
    sealed interface Tree permits Leaf, Node {}
    record Leaf(int value) implements Tree {}
    record Node(Tree left, Tree right) implements Tree {}

    // Simplification pass: if BOTH children are Leaves with the SAME value,
    // collapse the Node into a single Leaf with double that value.
    // Otherwise, recursively simplify each child independently and rebuild the Node.
    static Tree simplify(Tree tree) {
        return switch (tree) {
            case Node(Leaf(int lv), Leaf(int rv)) when lv == rv ->
                new Leaf(lv * 2);
            case Node(Tree l, Tree r) ->
                new Node(simplify(l), simplify(r));
            case Leaf(int v) -> tree;
        };
    }

    static String render(Tree tree) {
        return switch (tree) {
            case Leaf(int v) -> String.valueOf(v);
            case Node(Tree l, Tree r) -> "(" + render(l) + " + " + render(r) + ")";
        };
    }

    public static void main(String[] args) {
        Tree tree = new Node(
            new Node(new Leaf(3), new Leaf(3)),   // both children equal -- collapses to Leaf(6)
            new Node(new Leaf(4), new Leaf(5))     // unequal -- stays as-is
        );
        System.out.println("before: " + render(tree));
        Tree simplified = simplify(tree);
        System.out.println("after:  " + render(simplified));
    }
}
```

**How to run:** `java NestedPatternCombinatorial.java` (JDK 21+).

Expected output:
```
before: ((3 + 3) + (4 + 5))
after:  (6 + (4 + 5))
```

The production-flavored hard case: `simplify`'s first case combines a two-level nested pattern *with* a guard (`when lv == rv`), catching the specific combinatorial shape "a `Node` whose two children are both `Leaf`s with equal values" and collapsing it — while any `Node` not matching that exact combination (including the second, `(4 + 5)` sub-tree, whose leaves are unequal) falls through to the general recursive case, which rebuilds the `Node` from its independently-simplified children; this demonstrates nested patterns handling a genuinely combinatorial, multi-variant condition (matching specific combinations of child *shapes and values* together) that a single-level pattern or a simple recursive call alone could not express as directly.

## 6. Walkthrough

Tracing `simplify(tree)` end to end from `NestedPatternCombinatorial.main`, where `tree = Node(Node(Leaf(3), Leaf(3)), Node(Leaf(4), Leaf(5)))`:

1. `simplify` is called on the outer `Node` — the first case, `case Node(Leaf(int lv), Leaf(int rv)) when lv == rv`, attempts to match: is the outer value a `Node`? Yes. Are *both* its children specifically `Leaf`s? No — the outer `Node`'s children are themselves both `Node`s (`Node(Leaf(3), Leaf(3))` and `Node(Leaf(4), Leaf(5))`), not `Leaf`s, so this two-level pattern fails to match at the outer level, and the `switch` proceeds to the next case.
2. `case Node(Tree l, Tree r)` matches (any `Node`, regardless of its children's specific shape), binding `l` to the left `Node(Leaf(3), Leaf(3))` and `r` to the right `Node(Leaf(4), Leaf(5))` — this case's body recursively calls `simplify(l)` and `simplify(r)` independently, then rebuilds a new `Node` from both results.
3. The recursive call `simplify(l)`, where `l = Node(Leaf(3), Leaf(3))`, re-enters `simplify` fresh: this time, the first case's pattern *does* match — the outer value is a `Node`, and both its children genuinely are `Leaf`s (`Leaf(3)` and `Leaf(3)`), binding `lv = 3` and `rv = 3`.
4. The guard `lv == rv` evaluates `3 == 3`, which is `true`, so this case is selected: it returns `new Leaf(lv * 2)`, which is `new Leaf(6)` — the sub-tree `Node(Leaf(3), Leaf(3))` has been collapsed into a single `Leaf(6)`.
5. The recursive call `simplify(r)`, where `r = Node(Leaf(4), Leaf(5))`, similarly matches the two-level `Leaf`/`Leaf` pattern, binding `lv = 4` and `rv = 5` — but this time the guard `lv == rv` evaluates `4 == 5`, which is `false`, so this case does not match, and the `switch` falls through to the general `Node(Tree l, Tree r)` case, which recurses into each of *its* children (`Leaf(4)` and `Leaf(5)`, both of which immediately hit the final `case Leaf(int v) -> tree` and return themselves unchanged) and rebuilds an equivalent `Node(Leaf(4), Leaf(5))`, unchanged in shape.
6. Back at the outermost call, the rebuilt `Node` combines the two recursive results: `new Node(Leaf(6), Node(Leaf(4), Leaf(5)))` — this is exactly what `render` prints as `(6 + (4 + 5))`, confirming that the leftmost sub-tree was correctly collapsed via the combinatorial nested-and-guarded pattern, while the rightmost sub-tree, not matching that specific combination, was correctly preserved through ordinary recursive reconstruction.

## 7. Gotchas & takeaways

> **Gotcha:** a deeply nested pattern with many levels can become genuinely hard to read if pushed too far in a single case label — as a practical guideline, match explicitly only as many levels as a given case's logic genuinely needs to distinguish (often just one or two), and let recursion handle any remaining depth, exactly as the general fallback cases do in the examples above, rather than trying to write one enormous pattern attempting to enumerate an entire tree's shape in a single expression.

- Nested patterns let a record pattern's component be itself another record pattern, matching multiple levels of structure in one expression — genuinely combinatorial when the nested types are themselves sealed hierarchies with multiple variants at each level.
- Recursive data structures (trees, linked structures) are typically processed by matching one or two levels of nesting explicitly per case, then recursing into any remaining, unmatched sub-structure by calling the same function again.
- A more specific, deeper nested pattern (with or without a guard) can act as an optimized fast path, coexisting with a more general, shallower fallback pattern that handles everything else via recursion — case order determines which is tried first, exactly as with guarded patterns.
- Combining nested patterns with guards lets a single case express a genuinely combinatorial condition — matching a specific combination of child shapes *and* values together — that would otherwise require significantly more verbose manual accessor-chaining and conditional logic.
- Keep individual nested patterns to as few levels as a given case genuinely needs; excessive nesting in a single pattern trades away the readability nested patterns are meant to provide in the first place.
- See [record deconstruction patterns](0968-record-deconstruction-patterns.md) for the broader mechanics nested patterns build on, and [sealed + records + pattern-matching synergy](0963-sealed-records-pattern-matching-synergy.md) for the general design style recursive, sealed, record-based data structures fit into.
