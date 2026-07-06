---
card: java
gi: 250
slug: static-nested-classes
title: Static nested classes
---

## 1. What it is

A static nested class is a class declared `static` inside another class. It behaves like an ordinary top-level class in almost every respect — it does not hold an implicit reference to an instance of the enclosing class, and can be instantiated with `new Outer.Nested(...)` without needing an `Outer` instance at all. It is simply namespaced inside `Outer` for organizational purposes.

```java
class Car {
    String model;
    Car(String model) { this.model = model; }

    static class EngineSpec { // static nested class — no implicit link to any Car instance
        int horsepower;
        EngineSpec(int horsepower) { this.horsepower = horsepower; }
    }
}

public class StaticNestedDemo {
    public static void main(String[] args) {
        Car.EngineSpec spec = new Car.EngineSpec(300); // no Car instance needed
        System.out.println("Horsepower: " + spec.horsepower);
    }
}
```

`EngineSpec` is created with `new Car.EngineSpec(300)` — no `Car` object exists anywhere in this program, yet `EngineSpec` instantiates just fine, because a `static` nested class is entirely independent of any enclosing instance; it is nested purely for naming and organizational convenience.

## 2. Why & when

Static nested classes exist to group a helper class tightly with the class it conceptually belongs to, without requiring an instance relationship between them.

- **Logical grouping without instance coupling** — `EngineSpec` is clearly related to `Car` (it describes a car's engine), but doesn't need to reference any particular `Car` object to exist meaningfully; nesting it inside `Car` documents that relationship in the code's structure, without paying for an implicit reference it doesn't need.
- **Namespacing to avoid top-level clutter** — a large codebase can end up with many small, closely related helper classes; nesting them as `static` classes inside the class they support (`Car.EngineSpec` rather than a separate top-level `EngineSpec`) keeps related code together and avoids polluting the top-level namespace.
- **Builder and data-holder patterns** — a very common, idiomatic use is a `static class Builder` nested inside the class it builds, or a `static class Result` nested inside a class whose methods return it — both patterns rely on the nested class being usable without needing an instance of the enclosing class.

Use a `static` nested class whenever a helper type is closely associated with the enclosing class conceptually, but does not need to access the enclosing class's instance state — if it *does* need that access, you likely want an inner (non-static) class instead, covered in the next topic.

## 3. Core concept

```java
class LinkedListImpl<T> {
    static class Node<T> { // static: does not need to reference any LinkedListImpl instance
        T value;
        Node<T> next;
        Node(T value) { this.value = value; }
    }

    Node<T> head;

    void addFirst(T value) {
        Node<T> newNode = new Node<>(value); // instantiated directly, no enclosing instance required
        newNode.next = head;
        head = newNode;
    }
}
```

`Node<T>` is declared `static` because a node's identity and data are entirely self-contained — it never needs to reach back into the specific `LinkedListImpl` instance that created it, which is exactly the signal that a static nested class (rather than an inner class) is the right choice here.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A static nested class lives inside the enclosing class purely for namespacing, it can be instantiated directly with no enclosing instance required, unlike a non-static inner class">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>

  <rect x="150" y="20" width="300" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="300" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">class Car { static class EngineSpec { ... } }</text>

  <line x1="300" y1="55" x2="300" y2="80" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="150" y="85" width="300" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="107" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">new Car.EngineSpec(300); — no Car instance needed</text>

  <text x="300" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Nested purely for naming/grouping — behaves like an independent top-level class.</text>
</svg>

A static nested class is nested purely for organization; it instantiates independently, with no link to an enclosing instance.

## 5. Runnable example

Scenario: a simple binary tree built from a static nested `Node` class, evolved from a basic node structure into a working tree with insertion, then hardened with a nested `static` builder-style helper class for constructing trees from arrays.

### Level 1 — Basic

```java
public class StaticNestedBasic {
    static class Node {
        int value;
        Node left, right;
        Node(int value) { this.value = value; }
    }

    public static void main(String[] args) {
        Node root = new Node(50); // Node instantiated with no enclosing tree object at all
        root.left = new Node(30);
        root.right = new Node(70);

        System.out.println(root.value + " -> " + root.left.value + ", " + root.right.value);
    }
}
```

**How to run:** `java StaticNestedBasic.java`

Each `Node` is created directly with `new Node(...)`, with no enclosing instance of any kind — `Node` is a fully self-contained static nested class, referencing only its own `value`, `left`, and `right` fields.

### Level 2 — Intermediate

Same `Node`, now used inside a `BinarySearchTree` class that performs real insertion logic — demonstrating that the static nested class serves as the tree's internal building block without needing to reference the tree itself.

```java
public class StaticNestedIntermediate {
    static class BinarySearchTree {
        static class Node { // nested inside BinarySearchTree, but still static
            int value;
            Node left, right;
            Node(int value) { this.value = value; }
        }

        Node root;

        void insert(int value) {
            root = insertRec(root, value);
        }

        private Node insertRec(Node node, int value) {
            if (node == null) return new Node(value);
            if (value < node.value) node.left = insertRec(node.left, value);
            else if (value > node.value) node.right = insertRec(node.right, value);
            return node;
        }

        boolean contains(int value) {
            Node current = root;
            while (current != null) {
                if (value == current.value) return true;
                current = (value < current.value) ? current.left : current.right;
            }
            return false;
        }
    }

    public static void main(String[] args) {
        BinarySearchTree tree = new BinarySearchTree();
        for (int v : new int[]{50, 30, 70, 20, 40}) tree.insert(v);

        System.out.println(tree.contains(40)); // true
        System.out.println(tree.contains(99)); // false
    }
}
```

**How to run:** `java StaticNestedIntermediate.java`

`Node` is nested two levels deep (`StaticNestedIntermediate.BinarySearchTree.Node`) but remains `static`, so it never carries a reference back to any particular `BinarySearchTree` instance — `insertRec` builds up the tree structure purely through `Node`'s own `left`/`right` references, entirely independent of the enclosing tree object's identity.

### Level 3 — Advanced

Same tree, now with a `static` nested `Builder` class implementing the builder pattern — a very common, idiomatic real-world use of static nested classes — allowing a tree to be constructed fluently from a sequence of values, then validated for a balance property.

```java
public class StaticNestedAdvanced {
    static class BinarySearchTree {
        static class Node {
            int value;
            Node left, right;
            Node(int value) { this.value = value; }
        }

        Node root;

        void insert(int value) { root = insertRec(root, value); }

        private Node insertRec(Node node, int value) {
            if (node == null) return new Node(value);
            if (value < node.value) node.left = insertRec(node.left, value);
            else if (value > node.value) node.right = insertRec(node.right, value);
            return node;
        }

        int height() { return heightRec(root); }

        private int heightRec(Node node) {
            if (node == null) return 0;
            return 1 + Math.max(heightRec(node.left), heightRec(node.right));
        }

        static class Builder { // static nested builder — no BinarySearchTree instance needed to start building
            BinarySearchTree tree = new BinarySearchTree();

            Builder add(int value) {
                tree.insert(value);
                return this; // fluent chaining
            }

            BinarySearchTree build() { return tree; }
        }
    }

    public static void main(String[] args) {
        BinarySearchTree tree = new BinarySearchTree.Builder()
            .add(50).add(30).add(70).add(20).add(40).add(60).add(80)
            .build();

        System.out.println("Height: " + tree.height());              // 3 — balanced insertion order
        System.out.println("Contains 60: " + tree.contains60(tree)); // helper defined below, for clarity
    }

    // Small helper outside the nested hierarchy, just to check a value using the tree built above
    static boolean contains60(BinarySearchTree t) {
        BinarySearchTree.Node current = t.root;
        while (current != null) {
            if (current.value == 60) return true;
            current = (60 < current.value) ? current.left : current.right;
        }
        return false;
    }
}
```

**How to run:** `java StaticNestedAdvanced.java`

`new BinarySearchTree.Builder()` is created directly, with no `BinarySearchTree` instance needed beforehand — the `Builder`'s job is precisely to construct one; each `.add(value)` call inserts into its internally held `tree` and returns `this` for fluent chaining, and `.build()` finally hands back the completed `BinarySearchTree`, all made possible because `Builder`, like `Node`, is a static nested class requiring no enclosing instance to exist.

## 6. Walkthrough

Trace the construction chain in `StaticNestedAdvanced.main`.

**`new BinarySearchTree.Builder()`.** Creates a `Builder` instance, whose constructor implicitly runs field initializers: `tree = new BinarySearchTree()`, an empty tree with `root = null`.

**`.add(50)`.** Calls `tree.insert(50)`, which calls `insertRec(null, 50)` (since `root` is `null`): the base case `node == null` is `true`, so it returns `new Node(50)`. `root` is now this new node. `.add` returns `this` (the `Builder`), enabling the next chained call.

**`.add(30)`.** `tree.insert(30)` calls `insertRec(root, 30)`, where `root.value` is `50`: `30 < 50` is `true`, so it recurses into `insertRec(node.left, 30)`, i.e. `insertRec(null, 30)`, returning `new Node(30)`, assigned to `root.left`.

**`.add(70)`, `.add(20)`, `.add(40)`, `.add(60)`, `.add(80)`.** Each follows the same recursive comparison logic, building out the tree: `70` becomes `root.right`; `20` becomes `root.left.left`; `40` becomes `root.left.right`; `60` becomes `root.right.left`; `80` becomes `root.right.right`.

**`.build()`.** Simply returns the `tree` field, now populated with all seven values in a balanced shape (since the insertion order happens to build a balanced tree here).

**`tree.height()`.** Calls `heightRec(root)`. `root` (`50`) is non-null: `1 + max(heightRec(root.left), heightRec(root.right))`. `heightRec(root.left)` (node `30`): `1 + max(heightRec(20-node), heightRec(40-node))` — both `20` and `40` are leaves (`heightRec` on their `null` children returns `0`), so each contributes `1 + max(0,0) = 1`; so `heightRec(30-node) = 1 + max(1,1) = 2`. Symmetrically, `heightRec(root.right)` (node `70`, with leaf children `60` and `80`) is also `2`. So `heightRec(root) = 1 + max(2,2) = 3`.

**`contains60(tree)`.** Starts at `root` (`50`): `60 != 50`, and `60 < 50` is `false`, so moves to `current.right` (`70`). `60 != 70`, and `60 < 70` is `true`, so moves to `current.left` (`60`). `current.value == 60` is `true`, returns `true`.

```
Builder chain inserts: 50 -> 30 -> 70 -> 20 -> 40 -> 60 -> 80

Resulting tree shape:
          50
        /    \
      30      70
     /  \    /  \
   20   40  60   80

height(): 1 + max(height(left subtree)=2, height(right subtree)=2) = 3
contains60: 50 -> 70 (60>=50) -> 60 (60<70) -> found -> true
```

**Final output.**
```
Height: 3
Contains 60: true
```

## 7. Gotchas & takeaways

> **A static nested class cannot directly access the enclosing class's instance fields or methods** — since it carries no implicit reference to any enclosing instance, referencing `BinarySearchTree`'s instance state directly from inside `Node` (if `Node` needed to, which it doesn't here) would be a compile error; it can only work with data explicitly passed to it, exactly like a top-level class would.

> **The builder pattern (a `static` nested `Builder` class) is one of the most common, idiomatic real-world uses of static nested classes** — it lets complex object construction be expressed fluently (`new X.Builder().add(...).add(...).build()`) while keeping the builder's implementation tightly scoped and namespaced under the class it constructs.

- A static nested class behaves like an independent top-level class, nested purely for logical grouping and namespacing — it holds no implicit reference to any enclosing instance.
- It can be instantiated directly via `Outer.Nested(...)` without needing any `Outer` instance to exist first.
- Use it when a helper type is conceptually tied to its enclosing class but doesn't need access to that class's instance state — common examples include internal data structures (like a linked list's `Node`) and builder classes.
- If a nested class *does* need to access the enclosing instance's state, a non-static inner class (the next topic) is the appropriate choice instead.
