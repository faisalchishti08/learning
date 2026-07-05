---
card: java
gi: 15
slug: release-cadence-6-month-feature-releases
title: Release cadence (6-month feature releases)
---

## 1. What it is

Since Java 9 (September 2017), Java follows a **strict six-month release cadence**: a new feature release every March and September. Before this, releases were driven by feature completion and could take years (Java 7 took 5 years; Java 8 took 2 years). The cadence means:

- **March release**: Java X (e.g. Java 21 in September 2023, Java 22 in March 2024).
- **September release**: Java X+1 (e.g. Java 23 in September 2024).
- A non-LTS release is supported with patch updates only until the next feature release (6 months).
- **LTS releases** (every 2–3 years) get multi-year patch support.

The model was adopted from successful projects like Firefox and Chrome, trading "big bang" releases for smaller, predictable increments.

## 2. Why & when

The old model caused two problems. First, features were delayed indefinitely because everything had to land in one big release. Second, releases were unpredictable — neither developers nor operations teams knew when the next Java would arrive. The cadence solves both:

- Features that are ready land in the next release; features that miss a train wait 6 months (not years).
- Operations teams plan OS upgrades and can schedule Java upgrades around a fixed calendar.
- Preview features can incubate across one or two releases before finalisation.

The six-month cadence matters to you when:
- Deciding whether to upgrade a production system (LTS or non-LTS strategy).
- Understanding why a feature you read about is "preview" in one release and "final" in the next.
- Choosing a base Docker image and understanding its support window.

## 3. Core concept

The cadence creates two tiers of releases:

```
Java 17 (LTS, Sep 2021)  ←── multi-year patch support (until ~2026 community, 2030 Oracle)
  Java 18 (Mar 2022)
  Java 19 (Sep 2022)
  Java 20 (Mar 2023)
Java 21 (LTS, Sep 2023)  ←── multi-year patch support (until ~2028 community, 2031 Oracle)
  Java 22 (Mar 2024)
  Java 23 (Sep 2024)
  Java 24 (Mar 2025)
Java 25 (LTS, Sep 2025)  ←── multi-year patch support
```

**Feature lifecycle:**
1. **JEP** (Java Enhancement Proposal) describes the feature.
2. **Preview** (`--enable-preview`) — feature is spec-complete but may change. Developers can try it.
3. **Second preview** (optional) — refinements based on feedback.
4. **Final** — feature is permanent; no more changes.

**Incubator modules** (discussed separately) follow a similar pattern for APIs.

The key insight: **non-LTS releases are development releases for staying current with features**. Most production systems target LTS releases (17, 21, 25). Non-LTS releases are for greenfield projects or developers who want the latest APIs immediately.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java release timeline: LTS every 2 years, non-LTS every 6 months">
  <defs>
    <marker id="arc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <!-- Timeline -->
  <line x1="30" y1="95" x2="680" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arc)"/>

  <!-- LTS: 17 -->
  <rect x="30" y="60" width="60" height="70" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2.5"/>
  <text x="60" y="85"  fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">17</text>
  <text x="60" y="100" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">LTS</text>
  <text x="60" y="113" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">Sep 2021</text>

  <!-- non-LTS 18,19,20 -->
  <rect x="105" y="75" width="45" height="40" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="127" y="93"  fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">18</text>
  <text x="127" y="107" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">Mar '22</text>

  <rect x="160" y="75" width="45" height="40" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="182" y="93"  fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">19</text>
  <text x="182" y="107" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">Sep '22</text>

  <rect x="215" y="75" width="45" height="40" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="237" y="93"  fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">20</text>
  <text x="237" y="107" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">Mar '23</text>

  <!-- LTS: 21 -->
  <rect x="272" y="60" width="60" height="70" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2.5"/>
  <text x="302" y="85"  fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">21</text>
  <text x="302" y="100" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">LTS</text>
  <text x="302" y="113" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">Sep 2023</text>

  <!-- non-LTS 22,23,24 -->
  <rect x="345" y="75" width="45" height="40" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="367" y="93"  fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">22</text>
  <text x="367" y="107" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">Mar '24</text>

  <rect x="400" y="75" width="45" height="40" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="422" y="93"  fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">23</text>
  <text x="422" y="107" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">Sep '24</text>

  <rect x="455" y="75" width="45" height="40" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="477" y="93"  fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">24</text>
  <text x="477" y="107" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">Mar '25</text>

  <!-- LTS: 25 -->
  <rect x="514" y="60" width="60" height="70" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2.5"/>
  <text x="544" y="85"  fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">25</text>
  <text x="544" y="100" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">LTS</text>
  <text x="544" y="113" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">Sep 2025</text>

  <!-- LTS support line -->
  <line x1="60" y1="150" x2="270" y2="150" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,2"/>
  <text x="163" y="165" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Java 17 LTS patches</text>
  <line x1="302" y1="150" x2="512" y2="150" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,2"/>
  <text x="405" y="165" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Java 21 LTS patches</text>
</svg>

LTS releases (tall green boxes) receive multi-year patches. Non-LTS releases (grey boxes) last 6 months.

## 5. Runnable example

Scenario: a program that identifies the current Java release, classifies it as LTS or non-LTS, calculates the end-of-life window, and recommends an upgrade path.

### Level 1 — Basic

```java
// ReleaseCadence.java
public class ReleaseCadence {
    public static void main(String[] args) {
        Runtime.Version v = Runtime.version();
        int feature = v.feature();
        boolean isLts = isLts(feature);

        System.out.println("Java version : " + v);
        System.out.println("Feature      : " + feature);
        System.out.println("LTS release  : " + isLts);
        if (!isLts) {
            System.out.println("End of life  : after next 6-month release");
            System.out.println("Recommendation: upgrade to next LTS (21 or 25)");
        }
    }

    static boolean isLts(int feature) {
        return feature == 8 || feature == 11 || feature == 17 || feature == 21 || feature == 25;
    }
}
```

**How to run:** `java ReleaseCadence.java`

On Java 22 (non-LTS) you'd see `LTS release: false` and a recommendation to upgrade to 25.

### Level 2 — Intermediate

Same scenario extended to show the complete release history from Java 9 to present, classifying each release.

```java
// JavaReleaseHistory.java
import java.util.*;

public class JavaReleaseHistory {

    record Release(int version, String date, boolean lts, String keyFeatures) {}

    static final List<Release> HISTORY = List.of(
        new Release(9,  "Sep 2017", false, "modules (JPMS), jshell"),
        new Release(10, "Mar 2018", false, "var (local type inference)"),
        new Release(11, "Sep 2018", true,  "lambda param var, HTTP client, ZGC preview"),
        new Release(12, "Mar 2019", false, "switch expressions (preview)"),
        new Release(13, "Sep 2019", false, "text blocks (preview)"),
        new Release(14, "Mar 2020", false, "records (preview), helpful NPE"),
        new Release(15, "Sep 2020", false, "sealed classes (preview), text blocks final"),
        new Release(16, "Mar 2021", false, "records final, unix domain sockets"),
        new Release(17, "Sep 2021", true,  "sealed classes final, pattern matching if"),
        new Release(18, "Mar 2022", false, "UTF-8 default, simple web server"),
        new Release(19, "Sep 2022", false, "virtual threads (preview), structured concurrency (incubator)"),
        new Release(20, "Mar 2023", false, "virtual threads (2nd preview), scoped values (incubator)"),
        new Release(21, "Sep 2023", true,  "virtual threads final, sequenced collections, pattern switch"),
        new Release(22, "Mar 2024", false, "unnamed variables, FFM API final"),
        new Release(23, "Sep 2024", false, "markdown javadoc, module imports (preview)"),
        new Release(24, "Mar 2025", false, "stream gatherers final, class file API preview"),
        new Release(25, "Sep 2025", true,  "value classes preview (Valhalla)")
    );

    public static void main(String[] args) {
        int current = Runtime.version().feature();

        System.out.printf("%-4s  %-10s  %-5s  %s%n", "Ver", "Date", "LTS?", "Key features");
        System.out.println("-".repeat(80));
        for (Release r : HISTORY) {
            String marker = r.version() == current ? " ← YOU ARE HERE" : "";
            System.out.printf("%3d  %-10s  %-5s  %s%s%n",
                r.version(), r.date(), r.lts() ? "LTS" : "—", r.keyFeatures(), marker);
        }
    }
}
```

**How to run:** `java JavaReleaseHistory.java`

Running this on Java 21 produces `← YOU ARE HERE` next to the Java 21 row, showing exactly where you are in the cadence.

### Level 3 — Advanced

Same scenario grown to a release strategy advisor: given the current date and Java version, it recommends whether to stay, patch-upgrade, or plan a major upgrade — simulating what a DevOps team would build into their dependency audit tooling.

```java
// ReleaseStrategyAdvisor.java
import java.time.*;
import java.util.*;

public class ReleaseStrategyAdvisor {

    record ReleaseInfo(int version, YearMonth ga, boolean lts, YearMonth eolCommunity) {
        boolean isEol(YearMonth now) { return now.isAfter(eolCommunity); }
        long monthsToEol(YearMonth now) {
            return now.until(eolCommunity, java.time.temporal.ChronoUnit.MONTHS);
        }
    }

    // community (free) EOL dates — LTS until next LTS, non-LTS until next release
    static final List<ReleaseInfo> RELEASES = List.of(
        new ReleaseInfo(17, YearMonth.of(2021, 9), true,  YearMonth.of(2026, 9)),
        new ReleaseInfo(18, YearMonth.of(2022, 3), false, YearMonth.of(2022, 9)),
        new ReleaseInfo(19, YearMonth.of(2022, 9), false, YearMonth.of(2023, 3)),
        new ReleaseInfo(20, YearMonth.of(2023, 3), false, YearMonth.of(2023, 9)),
        new ReleaseInfo(21, YearMonth.of(2023, 9), true,  YearMonth.of(2028, 9)),
        new ReleaseInfo(22, YearMonth.of(2024, 3), false, YearMonth.of(2024, 9)),
        new ReleaseInfo(23, YearMonth.of(2024, 9), false, YearMonth.of(2025, 3)),
        new ReleaseInfo(24, YearMonth.of(2025, 3), false, YearMonth.of(2025, 9)),
        new ReleaseInfo(25, YearMonth.of(2025, 9), true,  YearMonth.of(2030, 9))
    );

    public static void main(String[] args) {
        int current    = Runtime.version().feature();
        YearMonth now  = YearMonth.now();

        System.out.println("╔══════════════════════════════════════════╗");
        System.out.println("║     Java Release Strategy Advisor        ║");
        System.out.println("╚══════════════════════════════════════════╝\n");
        System.out.println("Current date : " + now);
        System.out.println("Running Java : " + current);

        Optional<ReleaseInfo> current_info = RELEASES.stream()
            .filter(r -> r.version() == current).findFirst();

        if (current_info.isPresent()) {
            ReleaseInfo ri = current_info.get();
            System.out.println("LTS          : " + ri.lts());
            System.out.println("GA date      : " + ri.ga());
            System.out.println("Community EOL: " + ri.eolCommunity());

            long months = ri.monthsToEol(now);
            String urgency;
            if (ri.isEol(now)) {
                urgency = "EOL — UPGRADE NOW: security patches no longer provided";
            } else if (months < 3) {
                urgency = "URGENT: EOL in " + months + " months";
            } else if (months < 12) {
                urgency = "PLAN UPGRADE: EOL in " + months + " months";
            } else {
                urgency = "SUPPORTED: " + months + " months remaining";
            }
            System.out.println("Status       : " + urgency);
        } else {
            System.out.println("Version " + current + " not in advisory database — check manually.");
        }

        System.out.println("\n[ Full Release Matrix ]");
        System.out.printf("%-4s  %-10s  %-5s  %-12s  %s%n", "Ver", "GA", "LTS?", "Community EOL", "Status");
        System.out.println("-".repeat(65));
        for (ReleaseInfo r : RELEASES) {
            boolean isCurrent = r.version() == current;
            String status = r.isEol(now) ? "EOL" :
                (r.monthsToEol(now) < 6 ? "⚠ ending soon" : "active");
            System.out.printf("%3d%s  %-10s  %-5s  %-12s  %s%n",
                r.version(), isCurrent ? "*" : " ", r.ga(), r.lts() ? "LTS" : "—",
                r.eolCommunity(), status);
        }
        System.out.println("  * = currently running");
    }
}
```

**How to run:** `java ReleaseStrategyAdvisor.java`

On Java 23 (non-LTS, EOL March 2025) running after March 2025, the advisor outputs `EOL — UPGRADE NOW`. This is the kind of check teams embed in their dependency auditing pipeline.

## 6. Walkthrough

Execution in `ReleaseStrategyAdvisor.main`:

1. **`Runtime.version().feature()`** — returns the integer major version. `YearMonth.now()` uses the system clock for the current year/month.

2. **`RELEASES` list** — a hardcoded `List<ReleaseInfo>` with the known release dates and community EOL dates. `eolCommunity` is the month *after* which free patches stop. For non-LTS releases, EOL is 6 months after GA. For LTS, it's 2–4 years (community) or longer (paid Oracle support).

3. **`current_info` lookup** — `stream().filter(r -> r.version() == current).findFirst()` returns an `Optional<ReleaseInfo>`. `Optional.isPresent()` guards against versions added after this program was written.

4. **Urgency classification** — `monthsToEol` uses `YearMonth.until(other, ChronoUnit.MONTHS)` for clean calendar arithmetic. The thresholds (`< 3 months = URGENT`, `< 12 months = PLAN`) are typical DevOps policy thresholds.

5. **Release matrix** — the `for` loop prints every known release with a `*` marker for the current version. `r.isEol(now)` checks if `now` is after `eolCommunity`. The `⚠` marker highlights releases ending within 6 months.

Data state:
```
Runtime.version().feature()  → integer (e.g. 23)
YearMonth.now()              → current calendar month
RELEASES.stream().filter()   → Optional<ReleaseInfo>
ri.monthsToEol(now)          → long (calendar months remaining)
  → urgency string
  → console output
```

## 7. Gotchas & takeaways

> **Non-LTS releases get zero patches after 6 months.** There is no backport of CVEs to Java 22 after Java 23 ships. If you're running Java 22 in production and a critical security flaw is found in month 7, you get no patch — you must upgrade to 23.

> **"LTS" means different things to different vendors.** Oracle provides LTS patches for 8 years (paid). The community (Temurin) provides LTS patches for 3–4 years. Amazon Corretto promises LTS for at least 4 years. Verify the specific vendor's EOL policy for your chosen LTS version.

- Release cadence: every 6 months (March and September) since Java 9.
- LTS: Java 8, 11, 17, 21, 25 — multi-year patch support.
- Non-LTS: 6 months of patches only. Use for greenfield apps, not production services.
- Preview features (`--enable-preview`) span 1–2 releases before finalisation.
- `Runtime.version().feature()` gives the major version; use it to programmatically enforce version policy.
- For version strategy: most teams target the latest LTS release, upgrading to the next LTS when it reaches its first patch release (e.g. 21.0.1).
