---
card: spring-framework
gi: 163
slug: array-construction
title: "Array construction"
---

## 1. What it is

SpEL supports constructing arrays using `new T[]{elements}` or `new T[size]` syntax. Multi-dimensional arrays use `new T[d1][d2]`. The type `T` must be accessible via SpEL's type system and can be a primitive type or a reference type.

```java
parser.parseExpression("new int[]{1, 2, 3}").getValue();           // int[] {1,2,3}
parser.parseExpression("new String[]{'a','b','c'}").getValue();    // String[] {a,b,c}
parser.parseExpression("new int[5]").getValue();                   // int[5] filled with 0
parser.parseExpression("new int[3][4]").getValue();                // int[3][4] zero-filled 2D
```

## 2. Why & when

- **`@Value` array injection** — `@Value("#{new int[]{1, 2, 4, 8}}")` injects a primitive array without a bean definition.
- **Dynamic-size buffers** — `new byte[payload.size()]` allocates an array sized by a root-object property at evaluation time.
- **Algorithm setup** — SpEL-driven rule engines that need to initialize scratch arrays.
- **Two-dimensional arrays** — `new double[rows][cols]` creates a zero-initialized matrix for configuration-driven grid structures.

## 3. Core concept

| Syntax | Produces |
|---|---|
| `new int[]{1,2,3}` | `int[]` with elements |
| `new String[]{'a','b'}` | `String[]` with elements |
| `new int[5]` | `int[5]`, zero-initialized |
| `new int[3][4]` | `int[3][4]`, zero-initialized |
| `new java.util.Date[2]` | `Date[2]`, `null`-initialized |
| `new int[][]{...}` | NOT supported — use nested lists |

Multi-dim arrays with element initializers (`new int[][]{{1,2},{3,4}}`) are NOT supported in SpEL; use nested inline lists `{{1,2},{3,4}}` instead. Only the first dimension can be sized via `new T[d1][d2]` — the inner dimension must be filled separately via assignment.

## 4. Diagram

<svg viewBox="0 0 700 155" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="15" width="310" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="165" y="36" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Array construction — with elements</text>
  <line x1="20" y1="44" x2="310" y2="44" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="165" y="58"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new int[]{1,2,3}        → int[] [1,2,3]</text>
  <text x="165" y="72"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new String[]{'x','y'}   → String[] [x,y]</text>
  <text x="165" y="86"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new boolean[]{true}     → boolean[] [true]</text>
  <text x="165" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new long[]{42L, 100L}   → long[] [42,100]</text>
  <text x="165" y="117" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Elements: SpEL expressions (variables OK)</text>
  <text x="165" y="131" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new int[]{#a, #b, #a+#b}</text>

  <rect x="375" y="15" width="315" height="130" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="532" y="36" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Array construction — sized</text>
  <line x1="385" y1="44" x2="682" y2="44" stroke="#79c0ff" stroke-width="1" opacity="0.4"/>
  <text x="532" y="58"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new int[5]      → int[5] all zeros</text>
  <text x="532" y="72"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new String[3]   → String[3] all null</text>
  <text x="532" y="86"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new int[3][4]   → int[3][4] zero matrix</text>
  <text x="532" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new int[n]      → int[n] (n=variable)</text>
  <text x="532" y="117" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Size can be any integer expression</text>
  <text x="532" y="131" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new byte[payload.length()]</text>
</svg>

SpEL array construction uses Java's `new T[]{}` initializer form or `new T[size]` blank-allocation form.

## 5. Runnable example

### Level 1 — Basic

Construct typed arrays and inspect their contents.

```java
// SpelArrayConstructionBasic.java
import org.springframework.expression.spel.standard.*;
import java.util.Arrays;

public class SpelArrayConstructionBasic {
    public static void main(String[] args) {
        var p = new SpelExpressionParser();

        // Primitive arrays with elements
        int[] ints = p.parseExpression("new int[]{10, 20, 30}").getValue(int[].class);
        System.out.println(Arrays.toString(ints));              // [10, 20, 30]

        double[] doubles = p.parseExpression("new double[]{1.1, 2.2, 3.3}").getValue(double[].class);
        System.out.println(Arrays.toString(doubles));           // [1.1, 2.2, 3.3]

        boolean[] bools = p.parseExpression("new boolean[]{true, false, true}").getValue(boolean[].class);
        System.out.println(Arrays.toString(bools));             // [true, false, true]

        // Reference type array
        String[] strs = p.parseExpression("new String[]{'x', 'y', 'z'}").getValue(String[].class);
        System.out.println(Arrays.toString(strs));              // [x, y, z]

        // Sized-only arrays (zero/null initialized)
        int[] blank = p.parseExpression("new int[5]").getValue(int[].class);
        System.out.println(Arrays.toString(blank));             // [0, 0, 0, 0, 0]

        String[] blankStrs = p.parseExpression("new String[3]").getValue(String[].class);
        System.out.println(Arrays.toString(blankStrs));         // [null, null, null]

        // 2D array
        int[][] matrix = p.parseExpression("new int[3][4]").getValue(int[][].class);
        System.out.println(matrix.length + " x " + matrix[0].length); // 3 x 4

        // Length
        System.out.println(p.parseExpression("new int[]{1,2,3}.length").getValue()); // 3
    }
}
```

How to run: `java SpelArrayConstructionBasic.java`

`.length` on a SpEL-constructed array works — SpEL resolves the `length` field on array types. `new int[5]` zero-initializes; `new String[3]` null-initializes.

### Level 2 — Intermediate

Dynamic size from context variable; array elements as expressions; indexing constructed arrays.

```java
// SpelArrayConstructionIntermediate.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

public class SpelArrayConstructionIntermediate {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();
        ctx.setVariable("size", 4);
        ctx.setVariable("base", 100);

        // Size from variable
        int[] dynArr = parser.parseExpression("new int[#size]").getValue(ctx, int[].class);
        System.out.println(Arrays.toString(dynArr));             // [0, 0, 0, 0]

        // Elements using variables
        int[] computed = parser.parseExpression(
            "new int[]{#base, #base * 2, #base * 3}").getValue(ctx, int[].class);
        System.out.println(Arrays.toString(computed));           // [100, 200, 300]

        // Index immediately after construction
        System.out.println(parser.parseExpression(
            "new int[]{#base, #base+1, #base+2}[1]").getValue(ctx)); // 101

        // Array length as expression
        System.out.println(parser.parseExpression(
            "new String[]{'a','b','c','d'}.length").getValue(ctx)); // 4

        // Construct and use in comparison
        System.out.println(parser.parseExpression(
            "new int[]{10,20,30}[2] > 25").getValue(ctx, Boolean.class)); // true

        // Array of type references
        Object[] types = parser.parseExpression(
            "new Object[]{T(Integer).MAX_VALUE, T(Long).MAX_VALUE}")
            .getValue(ctx, Object[].class);
        System.out.println(Arrays.toString(types));              // [2147483647, 9223372036854775807]
    }
}
```

How to run: `java SpelArrayConstructionIntermediate.java`

`new int[#size]` evaluates `#size` at runtime to determine the array length. `T(Integer).MAX_VALUE` inside array braces is a valid SpEL sub-expression — array element slots accept any SpEL expression.

### Level 3 — Advanced

`@Value` with array construction; array in service bean; write back to array via `setValue`.

```java
// SpelArrayConstructionAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

@Configuration
class ArrCfg {}

@org.springframework.stereotype.Component
class MatrixConfig {
    @Value("#{new int[]{2, 4, 8, 16, 32}}")
    private int[] powerSeries;

    @Value("#{new String[]{'INFO', 'WARN', 'ERROR'}}")
    private String[] logLevels;

    @Value("#{new double[3][3]}")
    private double[][] identityBase;  // zero matrix (fill identity separately in @PostConstruct)

    public int[] getPowerSeries()      { return powerSeries; }
    public String[] getLogLevels()     { return logLevels; }
    public double[][] getIdentityBase(){ return identityBase; }

    @javax.annotation.PostConstruct
    void initIdentity() {
        for (int i = 0; i < 3; i++) identityBase[i][i] = 1.0; // make it identity
    }
}

public class SpelArrayConstructionAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ArrCfg.class, MatrixConfig.class);
        MatrixConfig cfg = ctx.getBean(MatrixConfig.class);

        System.out.println("powerSeries: " + Arrays.toString(cfg.getPowerSeries()));
        System.out.println("logLevels:   " + Arrays.toString(cfg.getLogLevels()));
        System.out.println("identity[0]: " + Arrays.toString(cfg.getIdentityBase()[0])); // [1.0, 0.0, 0.0]

        // SpEL setValue on array element
        var parser = new SpelExpressionParser();
        var evalCtx = new StandardEvaluationContext();
        int[] arr = new int[]{10, 20, 30};
        evalCtx.setRootObject(arr);
        parser.parseExpression("[1]").setValue(evalCtx, 99);
        System.out.println(Arrays.toString(arr)); // [10, 99, 30]

        ctx.close();
    }
}
```

How to run: `java SpelArrayConstructionAdvanced.java`

`@Value("#{new int[]{2,4,8,16,32}}")` injects a `int[]` bean — note the `#{}` wrapper. `@PostConstruct` fills the identity diagonal after Spring injects the zero-initialized `double[3][3]`. `[1].setValue(evalCtx, 99)` mutates a mutable array element via SpEL.

## 6. Walkthrough

Execution for `"new int[]{#base, #base * 2, #base * 3}"` with `#base = 100`:

1. AST: `ConstructorReference(int[], [VariableRef(base), Multiply(VariableRef(base),2), Multiply(VariableRef(base),3)])`.
2. Resolve element 0: `#base` → `100`.
3. Resolve element 1: `#base * 2` → `200`.
4. Resolve element 2: `#base * 3` → `300`.
5. `Arrays.newInstance(int.class, 3)` → `int[3]`.
6. Fill: `[0]=100, [1]=200, [2]=300`.
7. Return `int[]{100, 200, 300}`.

## 7. Gotchas & takeaways

> Multi-dimensional arrays with element initializers (`new int[][]{{1,2},{3,4}}`) are **not supported** in SpEL. The parser rejects them. Use nested inline lists `{{1,2},{3,4}}` to get a `List<List<Integer>>` instead, or allocate with `new int[m][n]` and fill via `setValue`.

> `new int[5]` and `new int[]{}` are different: the first allocates a zero-filled array of size 5; the second allocates an empty array of size 0. `new int[]{}[0]` throws `EvaluationException` (ArrayIndexOutOfBounds).

- The type name in `new T[...]` must be either a primitive type keyword (`int`, `double`, `boolean`, etc.) or a fully qualified class name. Short names like `Date` are not resolved unless a custom `TypeLocator` is configured.
- `new java.util.Date[2]` constructs a `Date[]` of size 2 with both slots set to `null`, not two `new Date()` instances. Array construction does NOT call the element type's constructor — only allocation happens.
- Arrays constructed in SpEL are regular Java arrays — mutable. Unlike inline lists `{1,2,3}`, they are not wrapped in `Collections.unmodifiableList`.
