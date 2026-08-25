# Java Arrays

## Overview

Arrays are the most basic data structure in Java — a fixed-size, indexed sequence of elements of the same type. They are objects on the heap, but their elements can be primitives or references. Understanding arrays (including multi-dimensional and jagged), the Arrays utility class, and pitfalls like covariance forms the foundation for all collection work.

---

## 1. One-Dimensional Arrays

### What is it

A contiguous block of memory holding a fixed number of elements of the same type. Size is fixed at creation and cannot change.

### Visual Diagram — Array Memory Layout

```
int[] arr = {10, 20, 30, 40, 50};

Stack:    arr ──────────────────────────────────────────►  Heap:
          (reference)
                                     Index:  [0]  [1]  [2]  [3]  [4]
                                     Value:  [10] [20] [30] [40] [50]
                                             ↑
                                          arr[0] = 10
                                          arr.length = 5

Array is an OBJECT on the heap. arr is a reference.
```

### Example 1 — Declaring and Initializing Arrays

```java
public class ArrayBasics {
    public static void main(String[] args) {
        // Form 1: declare + allocate (default values)
        int[] nums = new int[5];          // [0, 0, 0, 0, 0]
        boolean[] flags = new boolean[3]; // [false, false, false]
        String[] names = new String[3];   // [null, null, null]

        // Form 2: declare + initialize with values
        int[] primes = {2, 3, 5, 7, 11};
        String[] fruits = {"Apple", "Banana", "Cherry"};

        // Form 3: declare then initialize later
        double[] scores;
        scores = new double[]{9.5, 8.0, 7.5};  // anonymous array literal

        // Accessing elements
        System.out.println(primes[0]);       // 2 (first element)
        System.out.println(primes[4]);       // 11 (last element)
        System.out.println(primes.length);   // 5 (property, NOT a method — no parens)

        // Modifying
        primes[0] = 100;
        System.out.println(primes[0]);       // 100

        // Iterating
        for (int i = 0; i < primes.length; i++) {
            System.out.print(primes[i] + " ");
        }
        System.out.println(); // 100 3 5 7 11
    }
}
```

**What this does:** Arrays have a fixed `.length` property (NOT `.length()` — that's String). Default values are 0 for numeric types, `false` for boolean, `null` for references. Indices are 0-based, from 0 to `length-1`.

### Example 2 — ArrayIndexOutOfBoundsException

```java
public class ArrayBounds {
    public static void main(String[] args) {
        int[] arr = {1, 2, 3};  // valid indices: 0, 1, 2

        System.out.println(arr[2]);  // 3 — OK

        try {
            System.out.println(arr[3]);  // THROWS ArrayIndexOutOfBoundsException
        } catch (ArrayIndexOutOfBoundsException e) {
            System.out.println("Caught: " + e.getMessage()); // Index 3 out of bounds for length 3
        }

        try {
            System.out.println(arr[-1]); // Also throws — negative index
        } catch (ArrayIndexOutOfBoundsException e) {
            System.out.println("Caught: " + e.getMessage());
        }

        // Safe iteration always: use arr.length
        for (int i = 0; i < arr.length; i++) {
            System.out.print(arr[i] + " ");
        }
    }
}
```

**What this does:** Accessing beyond the valid range throws `ArrayIndexOutOfBoundsException` at runtime. Using `arr.length` in the loop condition prevents this.

### Dry Run — Array Initialization Trace

```java
int[] arr = new int[4];
arr[0] = 10;
arr[1] = arr[0] * 2;
arr[2] = arr[1] + arr[0];
arr[3] = arr.length;
```

| Step | Operation              | arr[0] | arr[1] | arr[2] | arr[3] |
|------|------------------------|--------|--------|--------|--------|
| Init | `new int[4]`           | 0      | 0      | 0      | 0      |
| 1    | `arr[0] = 10`          | 10     | 0      | 0      | 0      |
| 2    | `arr[1] = 10 * 2`      | 10     | 20     | 0      | 0      |
| 3    | `arr[2] = 20 + 10`     | 10     | 20     | 30     | 0      |
| 4    | `arr[3] = arr.length`  | 10     | 20     | 30     | 4      |

### Example 3 — Passing Arrays to Methods

```java
public class ArrayMethods {
    // Modifies original — arrays are passed by reference
    static void doubleAll(int[] arr) {
        for (int i = 0; i < arr.length; i++) {
            arr[i] *= 2;
        }
    }

    // Returns a new array — doesn't modify original
    static int[] doubledCopy(int[] arr) {
        int[] result = new int[arr.length];
        for (int i = 0; i < arr.length; i++) {
            result[i] = arr[i] * 2;
        }
        return result;
    }

    public static void main(String[] args) {
        int[] original = {1, 2, 3, 4, 5};
        doubleAll(original);
        System.out.println(java.util.Arrays.toString(original)); // [2, 4, 6, 8, 10]

        int[] fresh = {1, 2, 3};
        int[] doubled = doubledCopy(fresh);
        System.out.println(java.util.Arrays.toString(fresh));   // [1, 2, 3] unchanged
        System.out.println(java.util.Arrays.toString(doubled)); // [2, 4, 6]
    }
}
```

**What this does:** Passing an array to a method passes the reference — the method can modify the original. To avoid modification, copy the array and return a new one.

> ⚠️ **Pitfall:** `arr.length` not `arr.length()` — length is a field, not a method. `String.length()` is a method. This is a frequent typo.

---

## 2. Two-Dimensional Arrays

### What is it

A 2D array is an array of arrays. Think of it as a grid with rows and columns.

### Visual Diagram — 2D Array Structure

```
int[][] matrix = new int[3][4]; // 3 rows, 4 columns

                 col0  col1  col2  col3
matrix[0] ──►  [  0     0     0     0  ]  ← row 0
matrix[1] ──►  [  0     0     0     0  ]  ← row 1
matrix[2] ──►  [  0     0     0     0  ]  ← row 2

Access: matrix[row][col]
matrix[1][2] = element at row 1, column 2
matrix.length = 3 (number of rows)
matrix[0].length = 4 (number of columns in row 0)
```

### Example 1 — Creating and Iterating 2D Arrays

```java
public class TwoDArray {
    public static void main(String[] args) {
        // Initialize with values
        int[][] grid = {
            {1, 2, 3},
            {4, 5, 6},
            {7, 8, 9}
        };

        // Access individual element
        System.out.println(grid[1][2]); // 6 (row 1, col 2)

        // Iterate with nested for loops
        for (int row = 0; row < grid.length; row++) {
            for (int col = 0; col < grid[row].length; col++) {
                System.out.printf("%3d", grid[row][col]);
            }
            System.out.println();
        }
        // Output:
        //   1  2  3
        //   4  5  6
        //   7  8  9

        // for-each style
        for (int[] row : grid) {
            for (int val : row) {
                System.out.print(val + " ");
            }
            System.out.println();
        }
    }
}
```

**What this does:** `grid.length` is the number of rows. `grid[0].length` is the number of columns in row 0. Each row is itself an array.

### Dry Run — Populating Multiplication Table

```java
int size = 3;
int[][] table = new int[size][size];
for (int i = 0; i < size; i++) {
    for (int j = 0; j < size; j++) {
        table[i][j] = (i+1) * (j+1);
    }
}
```

| i | j | Computation       | table[i][j] |
|---|---|-------------------|-------------|
| 0 | 0 | (0+1)*(0+1) = 1*1 | 1           |
| 0 | 1 | (0+1)*(1+1) = 1*2 | 2           |
| 0 | 2 | (0+1)*(2+1) = 1*3 | 3           |
| 1 | 0 | (1+1)*(0+1) = 2*1 | 2           |
| 1 | 1 | (1+1)*(1+1) = 2*2 | 4           |
| 1 | 2 | (1+1)*(2+1) = 2*3 | 6           |
| 2 | 0 | (2+1)*(0+1) = 3*1 | 3           |
| 2 | 1 | (2+1)*(1+1) = 3*2 | 6           |
| 2 | 2 | (2+1)*(2+1) = 3*3 | 9           |

Final table: `[[1,2,3],[2,4,6],[3,6,9]]`

### Example 2 — Useful 2D Array Operations

```java
public class TwoDOperations {
    public static void main(String[] args) {
        int[][] matrix = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};

        // Sum of all elements
        int total = 0;
        for (int[] row : matrix) {
            for (int val : row) total += val;
        }
        System.out.println("Sum: " + total); // 45

        // Transpose (rows become columns)
        int rows = matrix.length, cols = matrix[0].length;
        int[][] transposed = new int[cols][rows];
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++)
                transposed[j][i] = matrix[i][j];

        // Print transposed
        for (int[] row : transposed) {
            System.out.println(java.util.Arrays.toString(row));
        }
        // [1, 4, 7]
        // [2, 5, 8]
        // [3, 6, 9]
    }
}
```

**What this does:** Standard 2D array operations. Transpose swaps `[i][j]` with `[j][i]`. These patterns appear frequently in coding interviews.

---

## 3. Jagged Arrays

### What is it

A jagged array is a 2D array where each row can have a different length. This is possible because Java 2D arrays are actually arrays of arrays — each row can point to a different-length array.

### Example 1 — Jagged Array

```java
public class JaggedArray {
    public static void main(String[] args) {
        // Create jagged array (rows of different lengths)
        int[][] jagged = new int[4][];  // 4 rows, columns unspecified
        jagged[0] = new int[1];  // row 0: 1 element
        jagged[1] = new int[2];  // row 1: 2 elements
        jagged[2] = new int[3];  // row 2: 3 elements
        jagged[3] = new int[4];  // row 3: 4 elements

        // Fill with row*col values
        for (int i = 0; i < jagged.length; i++) {
            for (int j = 0; j < jagged[i].length; j++) {
                jagged[i][j] = (i + 1) * (j + 1);
            }
        }

        // Print — each row is different length
        for (int[] row : jagged) {
            System.out.println(java.util.Arrays.toString(row));
        }
        // [1]
        // [2, 4]
        // [3, 6, 9]
        // [4, 8, 12, 16]

        // Triangle pattern
        int[][] triangle = {
            {1},
            {1, 2},
            {1, 2, 3},
            {1, 2, 3, 4}
        };
        System.out.println("Rows: " + triangle.length);          // 4
        System.out.println("Last row length: " + triangle[3].length); // 4
    }
}
```

**What this does:** Jagged arrays are useful for triangular structures, Pascal's triangle, adjacency lists in graphs, and any structure where row lengths vary. Must use `jagged[i].length` for each row's length, not a fixed constant.

---

## 4. Arrays Utility Class

### What is it

`java.util.Arrays` provides static utility methods for common array operations: sorting, searching, copying, filling, comparing, and converting.

### Example 1 — Sorting and Searching

```java
import java.util.Arrays;

public class ArraysSort {
    public static void main(String[] args) {
        int[] nums = {5, 2, 8, 1, 9, 3};

        // Sort (ascending)
        Arrays.sort(nums);
        System.out.println(Arrays.toString(nums)); // [1, 2, 3, 5, 8, 9]

        // Sort a range (from index 1 inclusive to 4 exclusive)
        int[] partial = {5, 2, 8, 1, 9, 3};
        Arrays.sort(partial, 1, 4);  // sorts only indices 1,2,3
        System.out.println(Arrays.toString(partial)); // [5, 1, 2, 8, 9, 3]

        // Binary search (array MUST be sorted first!)
        int[] sorted = {1, 3, 5, 7, 9, 11, 13};
        int idx = Arrays.binarySearch(sorted, 7);
        System.out.println("Index of 7: " + idx); // 3

        int notFound = Arrays.binarySearch(sorted, 6);
        System.out.println("6 not found: " + notFound); // negative value: -(insertion_point + 1)

        // Sort String array (lexicographic)
        String[] words = {"banana", "apple", "cherry", "date"};
        Arrays.sort(words);
        System.out.println(Arrays.toString(words)); // [apple, banana, cherry, date]

        // Sort with comparator (descending)
        String[] words2 = {"banana", "apple", "cherry"};
        Arrays.sort(words2, (a, b) -> b.compareTo(a));  // reverse order
        System.out.println(Arrays.toString(words2)); // [cherry, banana, apple]
    }
}
```

**What this does:** `Arrays.sort()` uses dual-pivot Quicksort for primitives (O(n log n)) and TimSort for objects. `Arrays.binarySearch()` requires a sorted array — returns index if found, negative value if not (the negative value encodes the insertion point).

### Example 2 — Copying, Filling, and Comparing

```java
import java.util.Arrays;

public class ArraysCopyFill {
    public static void main(String[] args) {
        int[] original = {1, 2, 3, 4, 5};

        // Copy entire array
        int[] copy1 = Arrays.copyOf(original, original.length);
        System.out.println(Arrays.equals(original, copy1));   // true

        // Copy with different length (truncates or pads with 0s)
        int[] shorter = Arrays.copyOf(original, 3);    // [1, 2, 3]
        int[] longer  = Arrays.copyOf(original, 7);    // [1, 2, 3, 4, 5, 0, 0]
        System.out.println(Arrays.toString(shorter)); // [1, 2, 3]
        System.out.println(Arrays.toString(longer));  // [1, 2, 3, 4, 5, 0, 0]

        // Copy range [from, to)
        int[] range = Arrays.copyOfRange(original, 1, 4);  // [2, 3, 4]
        System.out.println(Arrays.toString(range));

        // Fill entire array with a value
        int[] filled = new int[5];
        Arrays.fill(filled, 7);
        System.out.println(Arrays.toString(filled)); // [7, 7, 7, 7, 7]

        // Fill range
        int[] partial = {1, 2, 3, 4, 5};
        Arrays.fill(partial, 1, 4, 0);  // fill indices 1,2,3 with 0
        System.out.println(Arrays.toString(partial)); // [1, 0, 0, 0, 5]

        // Deep equals for multi-dimensional
        int[][] a = {{1,2},{3,4}};
        int[][] b = {{1,2},{3,4}};
        System.out.println(Arrays.equals(a, b));      // false (compares references!)
        System.out.println(Arrays.deepEquals(a, b));  // true  (compares content recursively)
    }
}
```

**What this does:** `Arrays.copyOf` is a clean way to copy or resize an array. `Arrays.equals` compares element-by-element for 1D arrays. For multi-dimensional, use `Arrays.deepEquals`.

### Dry Run — Arrays.sort (conceptual for small array)

```java
int[] arr = {5, 2, 8, 1, 3};
Arrays.sort(arr);
```

Dual-pivot Quicksort partitions around two pivots. Simplified trace:

| Pass | Array State      | Action                     |
|------|------------------|----------------------------|
| Init | [5, 2, 8, 1, 3]  | pick pivots 5 and 3        |
| 1    | [2, 1, 3, 5, 8]  | partition: <3 left, >5 right |
| 2    | [1, 2, 3, 5, 8]  | sort [2,1] and done        |
| Done | [1, 2, 3, 5, 8]  | sorted                     |

### Example 3 — asList and stream

```java
import java.util.Arrays;
import java.util.List;

public class ArraysConvert {
    public static void main(String[] args) {
        String[] arr = {"a", "b", "c"};

        // Arrays.asList — fixed-size list backed by array
        List<String> list = Arrays.asList(arr);
        list.set(0, "A");                  // OK — modifies backing array!
        System.out.println(arr[0]);        // A (changed!)
        // list.add("d");                  // UnsupportedOperationException — fixed size!

        // For a proper mutable list:
        List<String> mutable = new java.util.ArrayList<>(Arrays.asList(arr));
        mutable.add("d");                  // OK
        System.out.println(mutable);       // [A, b, c, d]

        // Stream from array [Java 8+]
        int[] nums = {1, 2, 3, 4, 5};
        int sum = Arrays.stream(nums).sum();
        System.out.println("Sum: " + sum); // 15

        int max = Arrays.stream(nums).max().getAsInt();
        System.out.println("Max: " + max); // 5

        // Convert int[] → Integer[] via stream
        Integer[] boxed = Arrays.stream(nums).boxed().toArray(Integer[]::new);
        System.out.println(Arrays.toString(boxed)); // [1, 2, 3, 4, 5]

        // Parallel sort [Java 8+] — uses fork/join, faster for large arrays
        int[] large = new int[1_000_000];
        Arrays.fill(large, (int)(Math.random() * 1000));
        Arrays.parallelSort(large);  // uses multiple CPU cores
    }
}
```

**What this does:** `Arrays.asList()` returns a fixed-size view backed by the original array. Wrap with `new ArrayList<>(...)` for a mutable list. `Arrays.stream()` enables stream operations. `Arrays.parallelSort()` uses multiple cores for large arrays.

> ⚠️ **Pitfall:** `Arrays.asList(arr).add(x)` throws `UnsupportedOperationException` because the list is fixed-size. Wrap with `new ArrayList<>()` to get a resizable list.

---

## 5. Varargs

### What is it

Varargs (`...`) lets a method accept zero or more arguments of a type. The compiler packages them into an array automatically.

### Visual Diagram

```
void method(int... nums) is compiled as: void method(int[] nums)

Caller writes:    method(1, 2, 3)        → compiler packages as int[]{1, 2, 3}
                  method(1)              → int[]{1}
                  method()               → int[]{} (empty array)
                  method(new int[]{1,2}) → passed directly (not wrapped again)
```

### Example 1 — Basic Varargs

```java
public class Varargs {
    // Varargs parameter MUST be last
    static int sum(int... numbers) {
        int total = 0;
        for (int n : numbers) {
            total += n;
        }
        return total;
    }

    static void print(String prefix, Object... values) {
        System.out.print(prefix + ": ");
        for (Object v : values) {
            System.out.print(v + " ");
        }
        System.out.println();
    }

    public static void main(String[] args) {
        System.out.println(sum());          // 0
        System.out.println(sum(5));         // 5
        System.out.println(sum(1, 2, 3));   // 6
        System.out.println(sum(1, 2, 3, 4, 5)); // 15

        // Passing existing array
        int[] existing = {10, 20, 30};
        System.out.println(sum(existing));  // 60

        print("Values", "a", "b", "c");    // Values: a b c
        print("Empty");                    // Empty: (nothing)
    }
}
```

**What this does:** Varargs is syntactic sugar over arrays. The `...` means 0 or more arguments. You can also pass an existing array directly. The varargs parameter must be the last parameter.

### Example 2 — Varargs with Generics Warning

```java
import java.util.Arrays;
import java.util.List;

public class VarargsHeapPollution {
    // @SafeVarargs suppresses unchecked warning
    @SafeVarargs
    static <T> List<T> listOf(T... elements) {
        return Arrays.asList(elements);
    }

    public static void main(String[] args) {
        List<String> names = listOf("Alice", "Bob", "Charlie");
        System.out.println(names); // [Alice, Bob, Charlie]
    }
}
```

**What this does:** Generic varargs creates a warning about heap pollution. `@SafeVarargs` suppresses it when you know the method is safe (doesn't store the varargs array reference).

> ⚠️ **Pitfall:** Two varargs overloads are ambiguous: `method(int... a, int... b)` is illegal. You can only have one varargs parameter, and it must be last.

---

## 6. Array Covariance Pitfall

### What is it

Array types in Java are **covariant** — if `B extends A`, then `B[]` is a subtype of `A[]`. This sounds useful but leads to a runtime exception.

### Visual Diagram

```
String extends Object → String[] can be assigned to Object[]

Object[] arr = new String[3];  ← compiles OK (covariant)
arr[0] = "hello";              ← OK (String is-a Object)
arr[0] = 42;                   ← compiles OK... but THROWS at runtime!
                                  (arr is actually String[], can't hold int!)
```

### Example 1 — ArrayStoreException

```java
public class ArrayCovariance {
    public static void main(String[] args) {
        String[] strings = new String[3];
        Object[] objects = strings;  // covariant: String[] is-a Object[]

        objects[0] = "hello";  // OK — String is-a Object, fits in String[]
        objects[1] = 42;       // compiles fine, but throws at runtime:
                                // ArrayStoreException: java.lang.Integer

        // Why? The actual array is String[], not Object[].
        // Every write to Object[] is checked at runtime to ensure
        // the actual element type matches.
    }
}
```

**What this does:** Java checks the actual array type at runtime for every write. Even though `objects` is declared as `Object[]`, the actual object is `String[]`, so storing an `Integer` throws `ArrayStoreException`.

### Example 2 — Why Generics Don't Have This Problem

```java
import java.util.ArrayList;
import java.util.List;

public class GenericsVsArrays {
    public static void main(String[] args) {
        // Arrays: covariant (unsafe)
        Object[] arr = new String[3];
        // arr[0] = 42;  // ArrayStoreException at runtime

        // Generic collections: invariant (safe at compile time)
        // List<Object> list = new ArrayList<String>(); // COMPILE ERROR!
        // This protects you at compile time — no runtime surprise

        // Use wildcard when you need flexibility:
        List<? extends Object> readOnly = new ArrayList<String>();
        // readOnly.add("hello"); // COMPILE ERROR — can't add to wildcard list
        Object o = readOnly.get(0); // OK — can read as Object
    }
}
```

**What this does:** Generic types are invariant (not covariant), which prevents the array covariance bug at compile time. This is one reason generics are safer than raw arrays for polymorphic code.

> ⚠️ **Pitfall:** Array covariance is a known Java design flaw. Prefer `List<T>` over arrays when working with polymorphic types.

---

## Quick Reference

```
Declare:    int[] arr = new int[5];     // default 0s
            int[] arr = {1, 2, 3};      // initializer
Access:     arr[i]                      // 0-based index
Length:     arr.length                  // field, not method!
2D:         int[][] grid = new int[rows][cols];
            grid[row][col]
            grid.length = rows
            grid[0].length = cols per row
Jagged:     int[][] jag = new int[n][]; // second dim unset
            jag[i] = new int[rowLen];

Arrays utility:
  Arrays.toString(arr)         → "[1, 2, 3]"
  Arrays.deepToString(arr2d)   → "[[1,2],[3,4]]"
  Arrays.sort(arr)             → in-place ascending sort
  Arrays.binarySearch(arr, x)  → index (arr must be sorted!)
  Arrays.copyOf(arr, len)      → new array of given length
  Arrays.copyOfRange(arr,f,t)  → copy from f (incl) to t (excl)
  Arrays.fill(arr, val)        → all elements = val
  Arrays.equals(a, b)          → element-by-element compare
  Arrays.deepEquals(a, b)      → for multi-dimensional
  Arrays.asList(arr)           → fixed-size List (backed by array)
  Arrays.stream(arr)           → IntStream/Stream for processing
  Arrays.parallelSort(arr)     → multi-core sort [Java 8+]

Common pitfalls:
  arr.length (not arr.length())
  asList is fixed-size — can't add/remove
  Arrays.equals on 2D compares references — use deepEquals
  Array covariance → ArrayStoreException
  BinarySearch requires sorted array
```
