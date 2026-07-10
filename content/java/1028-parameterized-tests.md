---
card: java
gi: 1028
slug: parameterized-tests
title: Parameterized tests
---

## 1. What it is

A **parameterized test** runs the exact same test logic once for each of several different input values, instead of writing a separate, near-identical `@Test` method per input. JUnit 5's `@ParameterizedTest` annotation, combined with a source of arguments — `@ValueSource` for simple single values, `@CsvSource` for multiple parameters per run, or `@MethodSource` for arguments computed by a helper method — feeds each set of values into the same test method body in turn, reporting each run as its own separate pass/fail result.

## 2. Why & when

Testing the same logic across several inputs by writing `isEvenTest1`, `isEvenTest2`, `isEvenTest3` (each nearly identical except for one literal value) means every genuinely new case requires copy-pasting a whole method, and a bug fix to the shared assertion logic has to be repeated in every copy. Parameterized tests separate the *logic being tested* (written once) from the *data driving it* (a list of inputs), so adding a new test case is just adding one more row of data, and the test method itself never needs to change or be duplicated.

Reach for a parameterized test whenever you find yourself about to write several `@Test` methods that share identical assertion logic and differ only in their input values — boundary conditions for a validation function, several rows of expected input/output pairs for a calculation, edge cases like empty strings, nulls, or negative numbers. It's unnecessary for genuinely distinct test *scenarios* that don't share the same assertion shape — those are better as separate, clearly-named `@Test` methods.

## 3. Core concept

```java
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertEquals;

class NumberUtilsTest {

    @ParameterizedTest
    @ValueSource(ints = {2, 4, 6, 100})
    void isEvenReturnsTrueForEvenNumbers(int number) {
        assertTrue(NumberUtils.isEven(number)); // runs ONCE per value in the array
    }

    @ParameterizedTest
    @CsvSource({
        "2, 3, 5",   // a, b, expectedSum
        "0, 0, 0",
        "-5, 5, 0"
    })
    void addReturnsCorrectSum(int a, int b, int expectedSum) {
        assertEquals(expectedSum, NumberUtils.add(a, b));
    }
}
class NumberUtils {
    static boolean isEven(int n) { return n % 2 == 0; }
    static int add(int a, int b) { return a + b; }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One parameterized test method being invoked four separate times, once per value in a ValueSource array, each invocation reported as its own pass or fail result">
  <rect x="30" y="70" width="180" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">isEvenReturnsTrue...(n)</text>

  <rect x="290" y="10" width="80" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="30" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">n=2 ✓</text>
  <rect x="290" y="55" width="80" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">n=4 ✓</text>
  <rect x="290" y="100" width="80" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">n=6 ✓</text>
  <rect x="290" y="145" width="80" height="20" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="159" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">n=100 ✓</text>

  <line x1="210" y1="90" x2="290" y2="25" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="210" y1="90" x2="290" y2="70" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="210" y1="90" x2="290" y2="115" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="210" y1="90" x2="290" y2="155" stroke="#8b949e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One test method body is invoked four separate times, once per value supplied by `@ValueSource`, each reported independently.

## 5. Runnable example

Scenario: testing an `isEven` and `add` utility, evolving from copy-pasted per-value test methods into fully parameterized tests using `@ValueSource`, `@CsvSource`, and `@MethodSource`.

### Level 1 — Basic

```java
// File: src/test/java/NumberUtilsBasicTest.java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertTrue;

class NumberUtilsBasicTest {
    @Test
    void isEvenTrueForTwo() { assertTrue(NumberUtils.isEven(2)); }

    @Test
    void isEvenTrueForFour() { assertTrue(NumberUtils.isEven(4)); }

    @Test
    void isEvenTrueForSix() { assertTrue(NumberUtils.isEven(6)); }
}

class NumberUtils {
    static boolean isEven(int n) { return n % 2 == 0; }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test`.

Expected output:
```
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0
```

Three nearly-identical test methods, differing only in the literal number passed to `isEven` — adding a fourth number to test means copy-pasting a fourth method, and any shared assertion logic (here, just `assertTrue`) would need updating in every copy if it ever changed.

### Level 2 — Intermediate

```java
// File: src/test/java/NumberUtilsIntermediateTest.java
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import static org.junit.jupiter.api.Assertions.assertTrue;

class NumberUtilsIntermediateTest {
    @ParameterizedTest
    @ValueSource(ints = {2, 4, 6, 100})
    void isEvenReturnsTrueForEvenNumbers(int number) {
        assertTrue(NumberUtils.isEven(number));
    }
}

class NumberUtils {
    static boolean isEven(int n) { return n % 2 == 0; }
}
```

**How to run:** place in a Maven project's test source root (with `junit-jupiter-params` on the test classpath — see the `pom.xml` snippet in [Maven dependencies & scopes](1036-maven-dependencies-scopes.md)), then run `mvn test`.

Expected output:
```
[INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0
```

The real-world concern added: one test method, `isEvenReturnsTrueForEvenNumbers`, is invoked four separate times — once per value in `{2, 4, 6, 100}` — each reported as its own pass/fail result (`"Tests run: 4"`), with zero duplicated method bodies. Adding a fifth number to test means adding one more value to the array, not writing a new method.

### Level 3 — Advanced

```java
// File: src/test/java/NumberUtilsAdvancedTest.java
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.MethodSource;
import java.util.stream.Stream;
import static org.junit.jupiter.api.Assertions.assertEquals;

class NumberUtilsAdvancedTest {

    @ParameterizedTest
    @CsvSource({
        "2, 3, 5",
        "0, 0, 0",
        "-5, 5, 0",
        "100, -50, 50"
    })
    void addReturnsCorrectSum(int a, int b, int expectedSum) {
        assertEquals(expectedSum, NumberUtils.add(a, b));
    }

    // MethodSource: for cases too complex to express as a simple CSV row --
    // here, generating a range of boundary values programmatically.
    static Stream<Arguments> divisionCases() {
        return Stream.of(
            Arguments.of(10, 2, 5),
            Arguments.of(9, 3, 3),
            Arguments.of(Integer.MAX_VALUE, 1, Integer.MAX_VALUE), // an edge case worth naming explicitly
            Arguments.of(-10, 2, -5)
        );
    }

    @ParameterizedTest
    @MethodSource("divisionCases")
    void divideReturnsCorrectQuotient(int a, int b, int expectedQuotient) {
        assertEquals(expectedQuotient, NumberUtils.divide(a, b));
    }
}

class NumberUtils {
    static boolean isEven(int n) { return n % 2 == 0; }
    static int add(int a, int b) { return a + b; }
    static int divide(int a, int b) { return a / b; }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test -Dtest=NumberUtilsAdvancedTest`.

Expected output:
```
[INFO] Tests run: 8, Failures: 0, Errors: 0, Skipped: 0
```

The production-flavored hard case: `@MethodSource("divisionCases")` pulls its arguments from a `static` helper method returning a `Stream<Arguments>` — necessary once test data needs to be *computed* (here, including `Integer.MAX_VALUE` as a deliberately-named boundary case) rather than written as simple literal values in an annotation. `8` total test runs reflects `4` `@CsvSource` rows plus `4` `@MethodSource` cases.

## 6. Walkthrough

Tracing how JUnit executes `divideReturnsCorrectQuotient` with `@MethodSource("divisionCases")`:

1. Before running any invocation of `divideReturnsCorrectQuotient`, JUnit calls the `static` method `divisionCases()` (matched by name to the string `"divisionCases"` in the `@MethodSource` annotation) to obtain the full stream of arguments.
2. `divisionCases()` returns a `Stream<Arguments>` containing four `Arguments.of(...)` entries — JUnit consumes this stream, treating each `Arguments` instance as one full parameter set for one invocation of the test method.
3. For the first entry, `Arguments.of(10, 2, 5)`, JUnit invokes `divideReturnsCorrectQuotient(10, 2, 5)` — inside, `NumberUtils.divide(10, 2)` computes `10 / 2 = 5`, matching `expectedQuotient` (`5`), so `assertEquals` passes.
4. This repeats for `Arguments.of(9, 3, 3)` (`9 / 3 = 3`, matches) and `Arguments.of(-10, 2, -5)` (`-10 / 2 = -5`, matches).
5. For `Arguments.of(Integer.MAX_VALUE, 1, Integer.MAX_VALUE)`, JUnit invokes the test with `a = Integer.MAX_VALUE`, `b = 1`, `expectedQuotient = Integer.MAX_VALUE` — `NumberUtils.divide(Integer.MAX_VALUE, 1)` computes `Integer.MAX_VALUE / 1`, which is simply `Integer.MAX_VALUE` (no overflow occurs for this particular operation), matching the expected value.
6. Each of these four invocations is tracked and reported by JUnit as its own separate test result — if, say, the `Integer.MAX_VALUE` case had failed while the other three passed, the test report would show exactly which specific parameter combination failed, rather than a single ambiguous failure covering all four cases at once.

## 7. Gotchas & takeaways

> **Gotcha:** `@CsvSource` rows are plain strings parsed as CSV — a value containing a literal comma needs careful quoting (or an alternative source like `@CsvFileSource`), and every value arrives as a `String` by default before JUnit converts it to the target parameter type, which can behave unexpectedly for less common types without an explicit converter.

- `@ParameterizedTest` runs one test method body once per set of supplied arguments, reporting each invocation as its own independent pass/fail result.
- `@ValueSource` supplies simple single-parameter values (`int`, `String`, etc.); `@CsvSource` supplies multiple parameters per test run as comma-separated rows; `@MethodSource` pulls arguments from a `static` helper method, needed when the data is computed or too complex for a literal annotation value.
- Reach for a parameterized test specifically when several test cases share identical assertion logic and differ only in input values — not for genuinely distinct scenarios that deserve their own clearly-named `@Test` methods.
- Naming boundary/edge cases explicitly in a `@MethodSource` helper (as with `Integer.MAX_VALUE` above) documents *why* that particular value matters, which a bare literal in a `@CsvSource` row can't communicate on its own.
- See [assertions (assertEquals, assertThrows, assertAll)](1027-assertions-assertequals-assertthrows-assertall.md) for what the assertion logic inside a parameterized test method typically looks like.
- Don't force genuinely different test scenarios into one parameterized test just to reduce the method count — if the assertions or setup meaningfully diverge between "cases," separate, clearly-named tests communicate intent better than a shared parameterized method with special-casing inside it.
