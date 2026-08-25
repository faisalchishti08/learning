# Java 14 Features (2020)

Java 14 finalized switch expressions, added helpful NullPointerExceptions, and previewed records and pattern matching.

---

## 1. Switch Expressions (Final) [Java 14]

Arrow syntax and yield are now standard (no `--enable-preview` needed).

```java
public class SwitchExpressionsJ14 {
    enum Season { SPRING, SUMMER, AUTUMN, WINTER }

    public static void main(String[] args) {
        Season season = Season.SUMMER;

        // Arrow syntax — no fall-through, no break
        int daysInSeason = switch (season) {
            case SPRING, SUMMER, AUTUMN -> 91;
            case WINTER -> 90;
        }; // exhaustive enum — no default needed

        System.out.println("Days: " + daysInSeason); // 91

        // Block body with yield
        String description = switch (season) {
            case SPRING -> "warm and fresh";
            case SUMMER -> {
                String heat = "very hot";
                yield "Summer is " + heat; // yield from block
            }
            case AUTUMN -> "cool and colorful";
            case WINTER -> "cold and snowy";
        };
        System.out.println(description); // Summer is very hot

        // Works as statement too
        switch (season) {
            case SUMMER -> System.out.println("Beach time!");
            default -> System.out.println("Not summer");
        }
    }
}
```

---

## 2. Helpful NullPointerExceptions

JVM now provides detailed NPE messages showing exactly which variable was null.

```java
public class HelpfulNPE {
    static class User { String address; }
    static class Address { String city; }

    public static void main(String[] args) {
        User user = new User();
        // user.address is null

        // Before Java 14:
        // NullPointerException (no detail — which variable was null?)

        // Java 14+ (with -XX:+ShowCodeDetailsInExceptionMessages, default in Java 15+):
        // NullPointerException: Cannot read field "city" because "user.address" is null
        //   at HelpfulNPE.main(HelpfulNPE.java:12)

        try {
            String city = user.address.toString(); // NPE with detail
        } catch (NullPointerException e) {
            System.out.println(e.getMessage());
            // Cannot read field "address" because "user" is <null>... 
        }
    }
}
```

---

## 3. Records (Preview) [Java 14]

Concise immutable data classes. Finalized Java 16. See `29-records.md` for full coverage.

```java
// Preview Java 14 — requires --enable-preview
record Point(int x, int y) {} // auto: constructor, getters, equals, hashCode, toString

Point p = new Point(3, 4);
System.out.println(p.x()); // 3
System.out.println(p);     // Point[x=3, y=4]
```

---

## 4. Pattern Matching for instanceof (Preview) [Java 14]

Combine type check and cast. Finalized Java 16.

```java
// Preview Java 14
Object obj = "hello";
if (obj instanceof String s) { // check + bind in one step
    System.out.println(s.toUpperCase()); // HELLO
    // s is String in this scope, no cast needed
}
```

---

## 5. JFR Event Streaming [Java 14]

Stream JVM Flight Recorder events in real-time (was batch-only before).

```java
import jdk.jfr.consumer.*;

try (var stream = RecordingStream.create()) {
    stream.enable("jdk.GarbageCollection").withoutThreshold();
    stream.onEvent("jdk.GarbageCollection", event -> {
        System.out.println("GC pause: " + event.getDuration());
    });
    stream.startAsync();
    Thread.sleep(10_000); // collect for 10 seconds
}
```

---

## Quick Reference

```
Java 14 key features:
  Switch expressions (final)    arrow syntax + yield — production ready
  Helpful NPE messages          "Cannot read field X because Y is null"
  Records (preview)             record Point(int x, int y) {}
  Pattern instanceof (preview)  obj instanceof String s
  JFR Event Streaming           real-time JVM profiling events
  Incubating: Foreign Memory    memory outside JVM heap (→ Panama)
  Removed: CMS GC               G1/ZGC/Shenandoah are replacements
  Deprecated: Solaris/SPARC port
```
