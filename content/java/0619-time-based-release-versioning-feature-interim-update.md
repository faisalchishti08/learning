---
card: java
gi: 619
slug: time-based-release-versioning-feature-interim-update
title: Time-based release versioning ($FEATURE.$INTERIM.$UPDATE)
---

## 1. What it is

Java 10 introduced a new time-based release versioning scheme: `$FEATURE.$INTERIM.$UPDATE.$PATCH`. The `$FEATURE` counter increments every six months (matching the new release cadence), `$INTERIM` is for non-feature releases (typically zero), `$UPDATE` increments for bug-fix updates, and `$PATCH` is for emergency fixes. This replaced the old scheme where version numbers were tied to marketing names (Java 2, J2SE 5.0, Java SE 6) or cryptic internal numbers (1.5.0, 1.6.0, 1.7.0, 1.8.0). The version reported by `java -version` changed from `1.8.0_292` to `10.0.2` — clean, predictable, and directly tied to the release schedule.

## 2. Why & when

The old versioning was inconsistent: `java -version` reported `1.8.0_292` while everyone called it "Java 8," and the internal version had no relationship to the marketing name. The shift to a six-month release cadence (starting with Java 9 in September 2017, then Java 10 in March 2018) made the old scheme untenable — you couldn't keep incrementing `1.x.0` forever. The new scheme is simple: the `$FEATURE` number IS the Java version. Java 10 = `10.0.0`. Java 11 = `11.0.0`. Java 17 = `17.0.0`. The `$UPDATE` counter tracks quarterly patch releases (e.g., `17.0.1`, `17.0.2`). This makes version identification trivial for tooling, scripts, and humans.

## 3. Core concept

```bash
$ java -version
# JDK 8 and earlier:
java version "1.8.0_292"
Java(TM) SE Runtime Environment (build 1.8.0_292-b10)

# JDK 10+:
java version "10.0.2" 2028-07-17
Java(TM) SE Runtime Environment 18.9 (build 10.0.2+13)

# JDK 17:
java version "17.0.5" 2022-10-18 LTS
Java(TM) SE Runtime Environment (build 17.0.5+9-LTS-147)
```

The version string uses the `$FEATURE.$INTERIM.$UPDATE.$PATCH` scheme. At runtime, `Runtime.version()` returns a `Runtime.Version` object with methods like `.feature()`, `.interim()`, `.update()`, and `.patch()` — no more parsing the string.

## 4. Diagram

<svg viewBox="0 0 580 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java 10+ time-based versioning: $FEATURE.$INTERIM.$UPDATE.$PATCH">
  <rect x="20" y="10" width="540" height="170" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#e6edf3" font-size="11" font-family="sans-serif">Example: 17.0.5+9-LTS</text>

  <rect x="30" y="48" width="50" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="55" y="68" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">17</text>
  <text x="55" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">FEATURE</text>

  <rect x="90" y="48" width="30" height="30" rx="4" fill="#79c0ff" stroke="#79c0ff"/>
  <text x="105" y="68" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">0</text>
  <text x="105" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">INTERIM</text>

  <rect x="130" y="48" width="30" height="30" rx="4" fill="#f0883e" stroke="#f0883e"/>
  <text x="145" y="68" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">5</text>
  <text x="145" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">UPDATE</text>

  <rect x="170" y="48" width="30" height="30" rx="4" fill="#8b949e" stroke="#8b949e"/>
  <text x="185" y="68" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">0</text>
  <text x="185" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">PATCH</text>

  <text x="30" y="125" fill="#8b949e" font-size="10" font-family="sans-serif">Six-month feature releases:</text>
  <text x="30" y="143" fill="#8b949e" font-size="9" font-family="monospace">  9 (Sep 2017) → 10 (Mar 2018) → 11 LTS (Sep 2018) → 12 → 13 → ...</text>

  <text x="30" y="168" fill="#8b949e" font-size="10" font-family="sans-serif">LTS releases every 3 years: 11, 17, 21, ... (long-term support)</text>
</svg>

The version number directly encodes the release chronology — `17` means the 17th feature release since the new cadence began.

## 5. Runnable example

Scenario: exploring the new version API and comparing old vs new version strings — starting with reading the runtime version, extending to programmatic version comparison, and finally building a version-aware feature gate.

### Level 1 — Basic

```java
// File: VersionDemo.java

public class VersionDemo {
    public static void main(String[] args) {
        System.out.println("=== Java Version API (JDK 10+) ===\n");

        // The old way (deprecated in JDK 10+)
        String oldVersion = System.getProperty("java.version");
        System.out.println("System property: " + oldVersion);

        // The new way
        Runtime.Version version = Runtime.version();
        System.out.println("Runtime.version(): " + version);
        System.out.println("  .feature(): " + version.feature());
        System.out.println("  .interim(): " + version.interim());
        System.out.println("  .update():  " + version.update());
        System.out.println("  .patch():   " + version.patch());

        // Pre-release info (if any)
        version.pre().ifPresent(pre -> System.out.println("  .pre():     " + pre));
        version.build().ifPresent(build -> System.out.println("  .build():   " + build));
    }
}
```

**How to run:** `java VersionDemo.java`

Expected output (JDK 17 example):
```
=== Java Version API (JDK 10+) ===

System property: 17.0.5
Runtime.version(): 17.0.5+9-LTS-147
  .feature(): 17
  .interim(): 0
  .update():  5
  .patch():   0
  .pre():     LTS
  .build():   9
```

The simplest usage: `Runtime.version()` replaces string parsing of `java.version`. Each component is separately accessible.

### Level 2 — Intermediate

```java
// File: VersionComparison.java

public class VersionComparison {

    static void checkFeature(int required) {
        int current = Runtime.version().feature();
        if (current < required) {
            System.err.println("ERROR: Java " + required +
                " required, running on Java " + current);
        } else {
            System.out.println("✅ Running on Java " + current +
                " (requires " + required + "+)");
        }
    }

    // Compare two versions programmatically
    static void compareVersions() {
        var v8  = Runtime.Version.parse("1.8.0_292");
        var v10 = Runtime.Version.parse("10.0.2");
        var v11 = Runtime.Version.parse("11.0.1");
        var v17 = Runtime.Version.parse("17.0.5");

        System.out.println("\nVersion comparison:");
        System.out.println("  10 > 8:  " + (v10.compareTo(v8) > 0));
        System.out.println("  17 > 11: " + (v17.compareTo(v11) > 0));
        System.out.println("  11 == 11.0.1: " + v11.equals(Runtime.Version.parse("11.0.1")));

        // Old-style versions are parsed correctly
        System.out.println("\nParsing legacy versions:");
        System.out.println("  '1.8.0_292' → feature=" + v8.feature() +
            ", update=" + v8.update());
        System.out.println("  (Java 8 is correctly identified as feature=8)");
    }

    public static void main(String[] args) {
        System.out.println("=== Version Checking & Comparison ===\n");

        checkFeature(11);
        checkFeature(21);
        compareVersions();
    }
}
```

**How to run:** `java VersionComparison.java`

Expected output (on JDK 17):
```
=== Version Checking & Comparison ===

✅ Running on Java 17 (requires 11+)
ERROR: Java 21 required, running on Java 17

Version comparison:
  10 > 8:  true
  17 > 11: true
  11 == 11.0.1: true

Parsing legacy versions:
  '1.8.0_292' → feature=8, update=292
  (Java 8 is correctly identified as feature=8)
```

The real-world concern: `Runtime.Version.parse()` correctly handles both old-style (`1.8.0_292`) and new-style (`11.0.1`) version strings. This enables writing version-aware code that works across JDK versions.

### Level 3 — Advanced

```java
// File: FeatureGate.java
import java.util.*;

public class FeatureGate {

    // Feature flags based on JDK version
    record ApiCapability(String name, int minVersion, boolean available) {}

    static List<ApiCapability> checkCapabilities() {
        int currentFeature = Runtime.version().feature();

        return List.of(
            new ApiCapability("var (type inference)",        10, currentFeature >= 10),
            new ApiCapability("HTTP Client",                 11, currentFeature >= 11),
            new ApiCapability("Switch Expressions",          14, currentFeature >= 14),
            new ApiCapability("Text Blocks",                 15, currentFeature >= 15),
            new ApiCapability("Records",                     16, currentFeature >= 16),
            new ApiCapability("Sealed Classes",              17, currentFeature >= 17),
            new ApiCapability("Pattern Matching (switch)",   21, currentFeature >= 21),
            new ApiCapability("Virtual Threads",             21, currentFeature >= 21),
            new ApiCapability("String Templates (preview)",  21, currentFeature >= 21)
        );
    }

    public static void main(String[] args) {
        int current = Runtime.version().feature();
        System.out.println("=== Feature Availability on Java " + current + " ===\n");

        var capabilities = checkCapabilities();
        for (var c : capabilities) {
            String icon = c.available() ? "✅" : "❌";
            String note = c.available() ? "" : " (requires Java " + c.minVersion() + "+)";
            System.out.printf("  %s %-35s %s%n", icon, c.name(), note);
        }

        // Show the release timeline
        System.out.println("\n=== JDK Release Timeline ===\n");
        System.out.println("2017:  9  (Sep) — Modules");
        System.out.println("2018: 10  (Mar) — var, copyOf");
        System.out.println("2018: 11  (Sep) — LTS — HTTP Client, Epsilon GC");
        System.out.println("2019: 12  (Mar) — Switch preview");
        System.out.println("2019: 13  (Sep) — Text Blocks preview");
        System.out.println("2020: 14  (Mar) — Switch standard, Records preview");
        System.out.println("2020: 15  (Sep) — Text Blocks standard");
        System.out.println("2021: 16  (Mar) — Records standard");
        System.out.println("2021: 17  (Sep) — LTS — Sealed Classes");
        System.out.println("2022: 18, 19");
        System.out.println("2023: 20, 21 (Sep) — LTS — Virtual Threads, Pattern Matching");
        System.out.println("2024: 22, 23");
        System.out.println("2025: 24");
    }
}
```

**How to run:** `java FeatureGate.java`

Expected output (on JDK 17):
```
=== Feature Availability on Java 17 ===

  ✅ var (type inference)                
  ✅ HTTP Client                         
  ✅ Switch Expressions                  
  ✅ Text Blocks                         
  ✅ Records                             
  ✅ Sealed Classes                      
  ❌ Pattern Matching (switch)            (requires Java 21+)
  ❌ Virtual Threads                      (requires Java 21+)
  ❌ String Templates (preview)           (requires Java 21+)

=== JDK Release Timeline ===

2017:  9  (Sep) — Modules
2018: 10  (Mar) — var, copyOf
2018: 11  (Sep) — LTS — HTTP Client, Epsilon GC
2019: 12  (Mar) — Switch preview
2019: 13  (Sep) — Text Blocks preview
2020: 14  (Mar) — Switch standard, Records preview
2020: 15  (Sep) — Text Blocks standard
2021: 16  (Mar) — Records standard
2021: 17  (Sep) — LTS — Sealed Classes
2022: 18, 19
2023: 20, 21 (Sep) — LTS — Virtual Threads, Pattern Matching
2024: 22, 23
2025: 24
```

The production-flavoured feature gate: a version-capability matrix that tells you which Java features are available on the current runtime. This is exactly the kind of logic used in library compatibility layers and build tool plugins.

## 6. Walkthrough

Tracing `Runtime.version()` in the Level 1 example:

1. `Runtime.version()` is called. This is a native-backed method that reads the JVM's build-time version information from internal constants.

2. The JVM returns a `Runtime.Version` object initialised from the build properties:
   - `feature = 17` (from the `java.version` property, parsed as the major component)
   - `interim = 0` (there are no interim releases in the standard cadence)
   - `update = 5` (the fifth quarterly update of Java 17)
   - `patch = 0` (no emergency patch)
   - `pre = Optional.of("LTS")` (the pre-release identifier from the build)
   - `build = Optional.of("9")` (the build number)

3. The `toString()` method formats this as `"17.0.5+9-LTS-147"`, combining `$FEATURE.$INTERIM.$UPDATE+$BUILD-$PRE-$OPT`.

For the legacy parsing in Level 2 (`Runtime.Version.parse("1.8.0_292")`):

1. The parser recognises the old `1.X.0_Y` format. It interprets `1.8.0` as feature 8 (not 1!), interim 0, update 292.
2. This backward-compatible parsing ensures that `Runtime.Version.parse("1.8.0_292").feature()` returns `8`, matching the logical Java version.

## 7. Gotchas & takeaways

> `Runtime.version().feature()` is the recommended way to check the Java version in code. Do NOT parse `System.getProperty("java.version")` manually — the format varies across JDK versions, and hand-rolled regex-based parsers consistently break on pre-release versions, LTS identifiers, or unusual build strings.

- The time-based cadence means there are **no more "major" releases in the traditional sense** — every six months, `$FEATURE` increments by 1. Java 10, 11, 12, 13... are all feature releases of roughly equal scope. LTS releases (11, 17, 21) are designated for extended support but are not technically different from non-LTS releases.
- `$INTERIM` is almost always `0` — this field exists for the possibility of a release between feature releases (like a security-only release with no new features), but in practice it has never been used.
- The `+` in `17.0.5+9-LTS` separates the version from the build metadata. The build number is unique per build and is not part of the version comparison (two versions with different build numbers but same version numbers are considered equal).
- `Runtime.Version` implements `Comparable<Runtime.Version>` — you can compare versions with `.compareTo()`, sort them, check `version.compareTo(required) >= 0`, etc. This replaces fragile string comparisons.
- The `java.specification.version` system property changed from `"1.8"` to `"10"` starting in JDK 10. The `java.version` property reflects the full version string. 