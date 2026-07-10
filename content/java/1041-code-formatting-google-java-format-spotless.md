---
card: java
gi: 1041
slug: code-formatting-google-java-format-spotless
title: "Code formatting (google-java-format, Spotless)"
---

## 1. What it is

An auto-formatter rewrites your source code's whitespace, line breaks, and brace placement to match one fixed, deterministic style — **google-java-format** is a specific, opinionated formatter for Java (no configuration options at all, by design) and **Spotless** is a Maven/Gradle plugin that runs a formatter like google-java-format automatically as part of the build, either checking that files are already formatted (`spotlessCheck`, fails the build if not) or actually rewriting them in place (`spotlessApply`). The key distinction from [static analysis (Checkstyle)](1040-static-analysis-spotbugs-pmd-checkstyle-sonarqube.md): a linter *flags* style violations for a human to fix; a formatter *fixes them automatically*, deterministically, with zero human judgment involved.

## 2. Why & when

Formatting disagreements between developers — tabs versus spaces, brace placement, where to break a long line — are genuinely unproductive to litigate case by case in code review, and worse, they pollute diffs: a pull request that reformats a file alongside a genuine logic change makes the actual change much harder to review, since the diff shows every reformatted line as "changed." An auto-formatter removes the disagreement (and the bikeshedding) entirely: everyone runs the same deterministic tool, every file always looks the same regardless of who wrote it or which editor they use, and formatting-only changes stop appearing in diffs once a codebase has been formatted uniformly and stays that way.

Adopt a specific, opinionated auto-formatter (rather than a highly configurable one with dozens of style options) specifically to end formatting debates — the whole value proposition of google-java-format is that it has *no* configuration knobs to argue about. Run it via Spotless (or an equivalent plugin) as part of CI, failing the build if any file isn't already correctly formatted, and provide a one-command fix (`spotlessApply` / `mvn spotless:apply`) so a failed check is trivial to resolve, never a manual formatting chore.

## 3. Core concept

```java
// Before formatting: valid Java, but inconsistent spacing, brace style, and line length
public class Example{
    public   static void main(String[] args)
    {
        int    x=5;
        if(x>0){System.out.println("positive");}
        else{System.out.println("non-positive");}
    }
}

// After google-java-format: one deterministic style, no options to configure or argue about
public class Example {
  public static void main(String[] args) {
    int x = 5;
    if (x > 0) {
      System.out.println("positive");
    } else {
      System.out.println("non-positive");
    }
  }
}
```

```xml
<!-- Minimal Spotless setup in pom.xml -->
<plugin>
    <groupId>com.diffplug.spotless</groupId>
    <artifactId>spotless-maven-plugin</artifactId>
    <version>2.43.0</version>
    <configuration>
        <java>
            <googleJavaFormat/>
        </java>
    </configuration>
    <executions>
        <execution>
            <goals><goal>check</goal></goals> <!-- fails the build if files aren't formatted -->
        </execution>
    </executions>
</plugin>
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inconsistently formatted source code being checked by Spotless, failing the build if not already formatted, versus running spotlessApply which rewrites the file deterministically in place">
  <rect x="30" y="20" width="220" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="140" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">inconsistently formatted .java</text>

  <rect x="330" y="20" width="130" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="395" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">spotlessCheck FAILS</text>

  <rect x="330" y="110" width="130" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="395" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">spotlessApply rewrites</text>

  <rect x="500" y="110" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="560" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">consistent .java</text>

  <line x1="250" y1="40" x2="330" y2="40" stroke="#f0883e" marker-end="url(#a)"/>
  <line x1="250" y1="60" x2="330" y2="120" stroke="#6db33f" marker-end="url(#a)"/>
  <line x1="460" y1="130" x2="500" y2="130" stroke="#6db33f" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`spotlessCheck` fails the build on unformatted code; `spotlessApply` fixes it deterministically with no manual effort.

## 5. Runnable example

Scenario: a small class with inconsistent formatting, evolving through what an auto-formatter would produce and why the CI check that enforces it matters.

### Level 1 — Basic

```java
// File: PriceCalculator.java -- BEFORE formatting: valid, correct Java,
// but with inconsistent spacing, brace placement, and indentation.
public class PriceCalculator{
    public double applyDiscount(double price,boolean isMember)
    {
        if(isMember)
        {
            return price*0.9;
        }
        else{
        return price;
        }
    }

    public static void main(String[] args) {
        PriceCalculator calc=new PriceCalculator();
        System.out.println(calc.applyDiscount(100.0,true));
    }
}
```

**How to run:** save as `PriceCalculator.java`, then `javac PriceCalculator.java && java PriceCalculator` (JDK 17+).

Expected output:
```
90.0
```

The code is completely correct and compiles fine — but its formatting is inconsistent (mixed brace placement, inconsistent spacing around operators, uneven indentation), the kind of thing that would produce a noisy diff and inconsistent style if left to each contributor's personal preference.

### Level 2 — Intermediate

```java
// File: PriceCalculator.java -- AFTER running an auto-formatter (google-java-format
// style): consistent 2-space indentation, braces always on the same line as their
// statement, consistent spacing around every operator -- with ZERO logic changed.
public class PriceCalculator {
  public double applyDiscount(double price, boolean isMember) {
    if (isMember) {
      return price * 0.9;
    } else {
      return price;
    }
  }

  public static void main(String[] args) {
    PriceCalculator calc = new PriceCalculator();
    System.out.println(calc.applyDiscount(100.0, true));
  }
}
```

**How to run:** save as `PriceCalculator.java`, then `javac PriceCalculator.java && java PriceCalculator` (JDK 17+).

Expected output:
```
90.0
```

The real-world concern added: the exact same behavior, but every brace, indentation level, and spacing decision now follows one deterministic, non-negotiable style — no configuration was involved in deciding these choices, since google-java-format intentionally provides none. A diff between the "before" and "after" versions here would show every single line as changed — which is exactly why running the formatter once, project-wide, and keeping it enforced from then on, matters far more than running it occasionally.

### Level 3 — Advanced

```xml
<!-- File: pom.xml -- Spotless configured to FAIL THE BUILD on unformatted code,
     not just to format it -- this is what actually prevents unformatted code
     from ever merging, rather than relying on developers remembering to run
     the formatter manually before committing. -->
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0.0</version>
    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>
    <build>
        <plugins>
            <plugin>
                <groupId>com.diffplug.spotless</groupId>
                <artifactId>spotless-maven-plugin</artifactId>
                <version>2.43.0</version>
                <configuration>
                    <java>
                        <googleJavaFormat/>
                    </java>
                </configuration>
                <executions>
                    <execution>
                        <id>spotless-check</id>
                        <phase>verify</phase>
                        <goals><goal>check</goal></goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

**How to run:** save the "before" (inconsistently-formatted) `PriceCalculator.java` from Level 1 into `src/main/java/`, add this `pom.xml`, then run `mvn verify`. Afterward, run `mvn spotless:apply` to fix it automatically, then `mvn verify` again.

Expected output (first `mvn verify`, against the unformatted file):
```
[ERROR] The following files had format violations:
[ERROR]     src/main/java/PriceCalculator.java
[ERROR] Run 'mvn spotless:apply' to fix these violations.
[INFO] BUILD FAILURE
```

Expected output (after `mvn spotless:apply`, then `mvn verify` again):
```
[INFO] Spotless.Java is keeping 1 files clean
[INFO] BUILD SUCCESS
```

The production-flavored hard case: the build **fails** entirely when unformatted code is present, with an actionable message pointing directly at the one-command fix — this is what actually enforces consistent formatting across a whole team, rather than relying on each contributor remembering to run the formatter voluntarily before every commit.

## 6. Walkthrough

Tracing what happens across the two `mvn verify` runs in the Level 3 example:

1. The first `mvn verify` reaches the `verify` lifecycle phase (after `compile` and `test` have already run — see [Maven lifecycle & POM](1035-maven-lifecycle-pom.md)), which is where the Spotless plugin's `check` goal is bound, per the `<phase>verify</phase>` configuration.
2. Spotless's `check` goal reads `src/main/java/PriceCalculator.java`, runs google-java-format's formatting logic against its content *in memory* (without modifying the actual file), and compares the formatted result against the file's current, unformatted content.
3. Since the file's current content (inconsistent braces, spacing, indentation) doesn't match what google-java-format would produce, Spotless reports this file as having a "format violation" and fails the build, printing the actionable message pointing at `mvn spotless:apply`.
4. Running `mvn spotless:apply` invokes Spotless's `apply` goal, which performs the same formatting computation, but this time **writes** the formatted result back to `PriceCalculator.java`, replacing its content in place — becoming byte-for-byte identical to the Level 2 "after" version shown above.
5. Running `mvn verify` a second time repeats the same comparison from step 2 — but now the file's actual content already matches exactly what google-java-format would produce, so the comparison finds zero violations, and Spotless's `check` goal passes.
6. With no format violations reported, the `verify` phase (and the rest of the build) completes successfully, printing `BUILD SUCCESS` — demonstrating the full enforced cycle: a genuinely failing check that blocks unformatted code from passing CI, paired with a trivial, single-command fix that resolves the failure without any manual formatting work.

## 7. Gotchas & takeaways

> **Gotcha:** running an auto-formatter for the first time on an existing, large codebase produces a single, enormous diff touching nearly every file — this is disruptive to any in-progress branches or pull requests at the time, so teams typically schedule this as a dedicated, one-time "reformat everything" commit, communicated in advance, rather than introducing formatting enforcement gradually or silently.

- An auto-formatter (google-java-format) rewrites whitespace and structure deterministically, with no configuration options — this is deliberate, since the goal is to end formatting debates entirely, not provide another set of options to argue about.
- A build-integrated formatter check (Spotless's `check` goal) *fails the build* on unformatted code, actually enforcing the style rather than relying on developer discipline to run the formatter voluntarily.
- The corresponding `apply` goal fixes violations automatically in one command, keeping the enforcement from being a manual chore.
- This differs from a linter like Checkstyle (see [static analysis](1040-static-analysis-spotbugs-pmd-checkstyle-sonarqube.md)): a formatter *fixes* mechanical style issues automatically; a linter *flags* deeper code-smell or bug-pattern issues that typically still require human judgment to resolve correctly.
- Formatting-only changes, once a codebase is uniformly formatted and the check is enforced, stop appearing in future diffs — every pull request's diff then shows only genuine logic changes, making code review meaningfully easier.
- Introducing formatting enforcement onto an existing large codebase typically requires a single, coordinated "reformat everything" commit first, since retrofitting it gradually leaves inconsistent files that keep failing the check for reasons unrelated to any specific change being reviewed.
