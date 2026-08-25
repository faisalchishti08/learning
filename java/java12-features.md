# Java 12 Features (2019)

Java 12 introduced switch expressions (preview) and other smaller improvements.

---

## 1. Switch Expressions (Preview)

Classic `switch` is a statement. Java 12 added expression form with `->` syntax (preview, finalized Java 14).

```java
// Classic switch statement — fall-through, break required
int day = 3;
String type;
switch (day) {
    case 1: case 7:
        type = "weekend"; break;
    case 2: case 3: case 4: case 5: case 6:
        type = "weekday"; break;
    default:
        type = "unknown";
}

// Java 12 switch expression (preview, enable with --enable-preview)
// Arrow syntax — no fall-through, no break needed
String type2 = switch (day) {
    case 1, 7 -> "weekend";   // multiple cases per arm
    case 2, 3, 4, 5, 6 -> "weekday";
    default -> "unknown";
};

// Block body with yield
String type3 = switch (day) {
    case 1, 7 -> "weekend";
    default -> {
        System.out.println("Weekday: " + day);
        yield "weekday"; // yield returns value from block
    }
};
```

**Note:** Switch expressions became standard in Java 14.

---

## 2. Teeing Collector

Collect stream into two collectors simultaneously, merge results.

```java
import java.util.stream.*;
import java.util.*;

public class TeeingDemo {
    record Stats(long count, OptionalDouble avg) {}

    public static void main(String[] args) {
        List<Integer> nums = List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);

        // teeing — applies two collectors and merges their results
        Stats stats = nums.stream().collect(
            Collectors.teeing(
                Collectors.counting(),            // collector 1: count
                Collectors.averagingInt(n -> n),  // collector 2: average
                (count, avg) -> new Stats(count, OptionalDouble.of(avg)) // merger
            )
        );
        System.out.println("Count: " + stats.count()); // 10
        System.out.println("Avg: " + stats.avg().getAsDouble()); // 5.5

        // Find both min and max in one pass
        var minMax = nums.stream().collect(
            Collectors.teeing(
                Collectors.minBy(Integer::compareTo),
                Collectors.maxBy(Integer::compareTo),
                (min, max) -> Map.of("min", min.orElseThrow(), "max", max.orElseThrow())
            )
        );
        System.out.println(minMax); // {min=1, max=10}
    }
}
```

---

## 3. String Indent and Transform [Java 12]

```java
public class StringMethods12 {
    public static void main(String[] args) {
        // indent(n) — adds n spaces to each line, normalizes newlines
        String code = "void foo() {\n    return;\n}";
        System.out.println(code.indent(4));
        //     void foo() {
        //         return;
        //     }

        // Negative indent removes leading whitespace
        String indented = "    hello\n    world";
        System.out.println(indented.indent(-2));
        //   hello
        //   world

        // transform — apply a function to the string (pipe syntax)
        String result = "  hello world  "
            .transform(String::strip)
            .transform(String::toUpperCase)
            .transform(s -> s.replace(" ", "_"));
        System.out.println(result); // HELLO_WORLD
    }
}
```

---

## 4. Compact Number Format

```java
import java.text.*;
import java.util.*;

public class CompactFormat {
    public static void main(String[] args) {
        NumberFormat compact = NumberFormat.getCompactNumberInstance(
            Locale.US, NumberFormat.Style.SHORT);

        System.out.println(compact.format(1_000));        // 1K
        System.out.println(compact.format(1_500_000));    // 2M
        System.out.println(compact.format(1_234_567_890)); // 1B

        NumberFormat compactLong = NumberFormat.getCompactNumberInstance(
            Locale.US, NumberFormat.Style.LONG);
        System.out.println(compactLong.format(1_500_000)); // 2 million
    }
}
```

---

## Quick Reference

```
Java 12 key features:
  Switch expression (preview)  ->  arrow syntax, yield, multi-case
  Collectors.teeing           two collectors, merge result [Java 12]
  String.indent(n)            add/remove leading whitespace per line
  String.transform(fn)        pipeline transform
  CompactNumberFormat         1K, 2M, 1B formatting
  Shenandoah GC (exp.)        low-pause concurrent GC
  JVM constants API           more stable classfile constants
```
