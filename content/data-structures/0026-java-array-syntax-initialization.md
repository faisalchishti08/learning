---
card: data-structures
gi: 26
slug: java-array-syntax-initialization
title: Java array syntax & initialization
---

## 1. What it is

Java offers several ways to declare and fill an array: `new int[5]` (size only, default-filled), `{1, 2, 3}` (an array literal), `new int[]{1, 2, 3}` (an explicit "new array" literal, needed outside a declaration), and multi-dimensional forms like `new int[3][4]`. Each form controls both the array's size and its starting contents, and every element you do not explicitly set gets a type-specific **default value**.

## 2. Why & when

Knowing the exact syntax rules avoids two common mistakes: assuming an array literal (`{1,2,3}`) works anywhere (it only works directly in a declaration), and assuming a freshly created array of objects is empty rather than full of `null`s. Picking the right initialization form also communicates intent — `new int[n]` says "I know the size, fill it later"; `{1,2,3}` says "here are the exact starting values."

## 3. Core concept

**Default values depend on the element type.** `new int[5]` fills every slot with `0`; `new boolean[5]` fills with `false`; `new double[5]` fills with `0.0`; and `new String[5]` (or any object type) fills every slot with `null`, since object array slots are references, not the objects themselves.

**Array-literal shorthand only works at the declaration site.** `int[] arr = {1, 2, 3};` is valid, but `arr = {4, 5, 6};` (a later reassignment) is a compile error — the compiler only allows the bare `{...}` shorthand when it can immediately infer the array type from a declaration. Anywhere else, you need the explicit form: `arr = new int[]{4, 5, 6};`.

**Declaring the bracket position is flexible but has a convention.** `int[] arr` and `int arr[]` both compile (the second is a legacy C-style form), but modern Java style always puts the brackets with the type: `int[] arr`. For multi-dimensional arrays, `new int[3][4]` allocates both dimensions eagerly; `new int[3][]` allocates only the outer array, leaving each row to be assigned separately (this is how jagged arrays are built).

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four array declaration forms and the resulting contents: sized with defaults, literal, explicit new-array literal, and a 2D array">
  <g font-family="sans-serif" font-size="11">
    <text x="150" y="18" fill="#8b949e">new int[3]</text>
    <rect x="150" y="24" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="165" y="40" fill="#e6edf3" text-anchor="middle" font-size="10">0</text>
    <rect x="180" y="24" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="195" y="40" fill="#e6edf3" text-anchor="middle" font-size="10">0</text>
    <rect x="210" y="24" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="225" y="40" fill="#e6edf3" text-anchor="middle" font-size="10">0</text>

    <text x="150" y="70" fill="#8b949e">new String[3]</text>
    <rect x="150" y="76" width="42" height="24" fill="#161b22" stroke="#79c0ff"/><text x="171" y="92" fill="#e6edf3" text-anchor="middle" font-size="9">null</text>
    <rect x="192" y="76" width="42" height="24" fill="#161b22" stroke="#79c0ff"/><text x="213" y="92" fill="#e6edf3" text-anchor="middle" font-size="9">null</text>
    <rect x="234" y="76" width="42" height="24" fill="#161b22" stroke="#79c0ff"/><text x="255" y="92" fill="#e6edf3" text-anchor="middle" font-size="9">null</text>

    <text x="150" y="122" fill="#8b949e">{1, 2, 3}</text>
    <rect x="150" y="128" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="165" y="144" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <rect x="180" y="128" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="195" y="144" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <rect x="210" y="128" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="225" y="144" fill="#e6edf3" text-anchor="middle" font-size="10">3</text>

    <text x="450" y="18" fill="#8b949e">only valid at the declaration site;</text>
    <text x="450" y="35" fill="#8b949e">elsewhere use new int[]{...}</text>
    <text x="450" y="90" fill="#79c0ff">object slots default to null,</text>
    <text x="450" y="107" fill="#79c0ff">primitive slots default per type</text>
  </g>
</svg>

Different declaration forms fill an array's slots differently — sized-only forms use type defaults, literal forms set exact values.

## 5. Runnable example

```java
// JavaArraySyntaxInitialization.java
import java.util.Arrays;

public class JavaArraySyntaxInitialization {

    // Basic: sized declarations get type-specific default values.
    static void basicLevel() {
        int[] ints = new int[3];
        boolean[] bools = new boolean[3];
        String[] strings = new String[3];
        System.out.println("basic: int defaults -> " + Arrays.toString(ints));       // [0, 0, 0]
        System.out.println("basic: boolean defaults -> " + Arrays.toString(bools));   // [false, false, false]
        System.out.println("basic: String defaults -> " + Arrays.toString(strings));  // [null, null, null]
    }

    // Intermediate: literal shorthand at declaration, versus the explicit form required elsewhere.
    static int[] makeArray(boolean useDefaults) {
        if (useDefaults) {
            return new int[]{9, 9, 9}; // explicit "new array" form -- required here, not a declaration
        }
        return new int[]{1, 2, 3};
    }

    static void intermediateLevel() {
        int[] literalAtDeclaration = {4, 5, 6}; // shorthand ONLY legal right here
        System.out.println("intermediate: literal at declaration -> " + Arrays.toString(literalAtDeclaration));

        int[] fromMethod = makeArray(true);
        System.out.println("intermediate: explicit new-array literal from a method -> " + Arrays.toString(fromMethod));
    }

    // Advanced: multi-dimensional forms -- eager 2D allocation versus a jagged array built row by row.
    static void advancedLevel() {
        int[][] eager = new int[2][3]; // both dimensions allocated immediately, all zero-filled
        System.out.println("advanced: eager 2D -> " + Arrays.deepToString(eager));

        int[][] jagged = new int[2][]; // only the outer array allocated; rows are null until assigned
        jagged[0] = new int[]{1, 2};
        jagged[1] = new int[]{3, 4, 5, 6};
        System.out.println("advanced: jagged rows -> " + Arrays.deepToString(jagged));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `JavaArraySyntaxInitialization.java`, then run `java JavaArraySyntaxInitialization.java`.

## 6. Walkthrough

1. `basicLevel()` creates three sized-only arrays. `int[]` slots default to `0`, `boolean[]` slots default to `false`, and `String[]` slots default to `null` — the default always matches the element type's "zero value" (primitives) or the empty reference (`null`, for objects).
2. `intermediateLevel()` shows the bare `{4, 5, 6}` literal working only because it sits directly in a declaration (`int[] literalAtDeclaration = {4, 5, 6};`).
3. Inside `makeArray`, the same shorthand would not compile as a `return {9, 9, 9};` — the method must use the explicit `new int[]{9, 9, 9}` form, since it is not a variable declaration.
4. `advancedLevel()`'s `eager` array allocates both dimensions immediately: `new int[2][3]` creates the outer array *and* two fully-formed, zero-filled inner rows in one step.
5. The `jagged` array allocates only the outer `int[2]` first, leaving both rows `null`; each row is then assigned separately with its own length (`2` and `4`), producing rows of different sizes — this is only possible because the outer allocation and the row allocations are separate steps.

## 7. Gotchas & takeaways

> Gotcha: reading an unassigned row of a `new int[n][]` array (before you assign that row) throws `NullPointerException`, not `ArrayIndexOutOfBoundsException` — the row itself is `null` until you explicitly create it with `new int[someLength]`.

- Sized-only array declarations fill every slot with the type's default value: `0`/`0.0` for numeric primitives, `false` for `boolean`, `null` for any object type.
- The bare `{...}` literal shorthand only compiles directly in a declaration; anywhere else, use the explicit `new int[]{...}` form.
- `new int[n][m]` eagerly allocates every row; `new int[n][]` allocates only the outer array, letting you build jagged rows one at a time.
- Related concepts: [Arrays as objects in the JVM](0013-arrays-as-objects-in-the-jvm.md), [Multi-dimensional & jagged arrays](0016-multi-dimensional-jagged-arrays.md).
