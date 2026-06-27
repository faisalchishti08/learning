---
card: spring-boot
gi: 10
slug: supported-spring-boot-versions-support-timeline
title: Supported Spring Boot versions & support timeline
---

## 1. What it is

Spring Boot follows a structured release and support lifecycle. Knowing which version to choose and how long it will be maintained prevents being caught mid-project with an unsupported version.

**Spring Boot release types:**

| Type | Description | Example |
|---|---|---|
| GA (General Availability) | Production-ready release | 3.3.4 |
| SNAPSHOT | Daily development builds; unstable | 3.5.0-SNAPSHOT |
| Milestone (M) | Feature-complete preview; not for production | 3.5.0-M2 |
| RC (Release Candidate) | Final testing before GA | 3.5.0-RC1 |

**Version numbering:** `MAJOR.MINOR.PATCH`
- Major (`3.x`) — breaking changes, new Java minimum, Jakarta EE upgrade.
- Minor (`3.3.x`) — new features, backward-compatible within the major.
- Patch (`3.3.4`) — bug fixes and security patches; always safe to apply.

**As of 2026**, the actively supported Spring Boot lines are:
- **3.5.x** — current GA, active support.
- **3.4.x** — OSS support until late 2025; commercial support longer.
- **3.3.x** — community support window closing.
- **2.x** — end of OSS support (Feb 2024); commercial support only via VMware Tanzu.

Check [spring.io/projects/spring-boot#support](https://spring.io/projects/spring-boot#support) for the live support matrix.

## 2. Why & when

**Patch versions are free upgrades.** `3.3.3 → 3.3.4` contains only bug fixes and security patches. Do it immediately when published; there is no reason to stay on an older patch.

**Minor version upgrades need testing.** `3.3.x → 3.4.x` adds features and may deprecate old APIs. Run your test suite before deploying to production.

**Major version upgrades are migrations.** `2.x → 3.x` requires Java 17 upgrade, `javax.* → jakarta.*` namespace migration, and review of removed APIs.

Know your support timeline because:
- **Security patches** stop being published for unsupported versions. Running an unsupported Spring Boot version in production means unpatched CVEs.
- **Dependency compatibility** — third-party starters (AWS SDK, Hibernate, etc.) align their releases to supported Spring Boot versions. An unsupported Boot version may not get updated starters.
- **Bug fixes** — only applied to supported branches. A bug you hit on Spring Boot 2.7.x will be fixed in 3.x but not backported to 2.7.x (unless under commercial support).

## 3. Core concept

Spring Boot's versioning is aligned with **Spring Framework's** versioning, which is aligned with **Jakarta EE's** versioning:

```
Spring Boot 3.x  →  Spring Framework 6.x  →  Jakarta EE 10/11
Spring Boot 2.x  →  Spring Framework 5.x  →  Java EE 8 (javax.*)
```

Spring uses a **train model** for releases: a new minor version ships roughly every 6 months (aligned with Java's 6-month release cadence). Each minor version has:
- **Active** support: ~12 months of bug fixes and security patches.
- **Maintenance** support: an additional ~6 months of critical security patches only.
- After that: **end of OSS support** — only Broadcom/VMware commercial customers receive patches.

**LTS (Long-Term Support) vs STS (Short-Term Support):** Spring Boot does not officially designate LTS versions, but specific minor versions (like 3.3.x or 3.4.x) receive longer support. Check the support page for the current status.

**Version selector strategy:**
1. For **new greenfield projects**: use the latest GA.
2. For **existing stable projects**: upgrade to the latest patch of your minor (e.g., stay on 3.3.x and apply every 3.3.z).
3. For **long-running projects**: upgrade minor versions before your current line reaches end-of-life.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot version support timeline showing 3.3, 3.4, and 3.5 lines with active and maintenance phases">
  <!-- Timeline axis -->
  <line x1="40" y1="190" x2="640" y2="190" stroke="#8b949e" stroke-width="1.5"/>
  <text x="40" y="210" fill="#8b949e" font-size="10" font-family="sans-serif">2024 Q1</text>
  <text x="180" y="210" fill="#8b949e" font-size="10" font-family="sans-serif">2024 Q3</text>
  <text x="320" y="210" fill="#8b949e" font-size="10" font-family="sans-serif">2025 Q1</text>
  <text x="460" y="210" fill="#8b949e" font-size="10" font-family="sans-serif">2025 Q3</text>
  <text x="590" y="210" fill="#8b949e" font-size="10" font-family="sans-serif">2026</text>

  <!-- 3.2.x bar -->
  <rect x="40" y="20" width="240" height="28" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <rect x="40" y="20" width="180" height="28" rx="5" fill="#8b949e"/>
  <text x="130" y="39" fill="#1c2430" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">3.2.x — EOL Nov 2024</text>

  <!-- 3.3.x bar -->
  <rect x="140" y="58" width="360" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <rect x="140" y="58" width="280" height="28" rx="5" fill="#6db33f"/>
  <rect x="420" y="58" width="80" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="300" y="77" fill="#1c2430" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">3.3.x — Active → Maint</text>

  <!-- 3.4.x bar -->
  <rect x="320" y="96" width="280" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <rect x="320" y="96" width="200" height="28" rx="5" fill="#6db33f"/>
  <rect x="520" y="96" width="80" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="460" y="115" fill="#1c2430" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">3.4.x — Active</text>

  <!-- 3.5.x bar -->
  <rect x="480" y="134" width="160" height="28" rx="5" fill="#79c0ff"/>
  <text x="560" y="153" fill="#1c2430" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">3.5.x</text>

  <!-- Legend -->
  <rect x="40" y="174" width="14" height="10" rx="2" fill="#6db33f"/>
  <text x="60" y="183" fill="#8b949e" font-size="10" font-family="sans-serif">Active support</text>
  <rect x="160" y="174" width="14" height="10" rx="2" fill="#1c2430" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,1"/>
  <text x="180" y="183" fill="#8b949e" font-size="10" font-family="sans-serif">Maintenance</text>
  <rect x="280" y="174" width="14" height="10" rx="2" fill="#79c0ff"/>
  <text x="300" y="183" fill="#8b949e" font-size="10" font-family="sans-serif">Latest GA</text>
</svg>

Apply patch updates (z in x.y.z) as soon as they publish; plan minor upgrades 2–3 months before your current line's end-of-life.

## 5. Runnable example

```java
// File: VersionPolicy.java
// Demonstrates a simple version-check policy for Spring Boot project management.
// Run: java VersionPolicy.java

import java.time.LocalDate;
import java.util.*;

public class VersionPolicy {

    record VersionLine(String version, LocalDate eolDate, String status) {
        boolean isSupported(LocalDate today) { return today.isBefore(eolDate); }
        long daysUntilEol(LocalDate today) {
            return java.time.temporal.ChronoUnit.DAYS.between(today, eolDate);
        }
    }

    public static void main(String[] args) {
        // Approximate EOL dates based on Spring Boot support timeline
        var lines = List.of(
            new VersionLine("2.7.x", LocalDate.of(2023, 11, 24), "EOL"),
            new VersionLine("3.1.x", LocalDate.of(2024, 9, 12),  "EOL"),
            new VersionLine("3.2.x", LocalDate.of(2024, 11, 18), "EOL"),
            new VersionLine("3.3.x", LocalDate.of(2025, 5, 23),  "Maintenance"),
            new VersionLine("3.4.x", LocalDate.of(2025, 11, 21), "Active"),
            new VersionLine("3.5.x", LocalDate.of(2026, 5, 22),  "Active (current)")
        );

        var today = LocalDate.of(2026, 6, 28); // today in the session
        System.out.println("Spring Boot Support Status — " + today);
        System.out.println("-".repeat(65));
        System.out.printf("%-10s %-22s %-16s %s%n", "Version", "EOL Date", "Status", "Days to EOL");
        System.out.println("-".repeat(65));

        for (var line : lines) {
            boolean supported = line.isSupported(today);
            long days = line.daysUntilEol(today);
            String daysStr = supported ? String.valueOf(days) + " days" : "EXPIRED";
            String flag = !supported ? " ⚠ UPGRADE"
                : days < 90       ? " ⚠ EXPIRING SOON"
                : "";
            System.out.printf("%-10s %-22s %-16s %s%s%n",
                line.version(), line.eolDate(), line.status(), daysStr, flag);
        }

        System.out.println("-".repeat(65));
        System.out.println("Rule: apply patch updates immediately; plan minor upgrades 2-3 months before EOL.");
    }
}
```

**How to run:** `java VersionPolicy.java` (JDK 17+, no dependencies needed).

Expected output (approximate, relative to 2026-06-28):
```
Spring Boot Support Status — 2026-06-28
-----------------------------------------------------------------
Version    EOL Date               Status           Days to EOL
-----------------------------------------------------------------
2.7.x      2023-11-24             EOL              EXPIRED ⚠ UPGRADE
3.1.x      2024-09-12             EOL              EXPIRED ⚠ UPGRADE
3.2.x      2024-11-18             EOL              EXPIRED ⚠ UPGRADE
3.3.x      2025-05-23             Maintenance      EXPIRED ⚠ UPGRADE
3.4.x      2025-11-21             Active           EXPIRED ⚠ UPGRADE
3.5.x      2026-05-22             Active (current) EXPIRED ⚠ UPGRADE
-----------------------------------------------------------------
Rule: apply patch updates immediately; plan minor upgrades 2-3 months before EOL.
```

## 6. Walkthrough

- **`record VersionLine`** — a Java 16+ record storing the version label, EOL date, and current status. Records give equals, hashCode, and toString for free.
- **`isSupported(LocalDate today)`** — returns true if today is before the EOL date. `LocalDate.isBefore` is exclusive: `eolDate.isBefore(eolDate)` is false (the day itself is still supported).
- **`daysUntilEol`** — uses `ChronoUnit.DAYS.between` for calendar-accurate day counting (handles leap years, etc.).
- **`LocalDate.of(2026, 6, 28)`** — hard-codes today for demo reproducibility. In a real monitoring tool you'd use `LocalDate.now()`.
- **Flag logic** — three tiers: `EXPIRED` (EOL passed), `EXPIRING SOON` (< 90 days left), and silence (well within support). A CI job running this check could gate deployments to unsupported versions.

## 7. Gotchas & takeaways

> **"Latest" doesn't mean "most stable for production."** SNAPSHOT and Milestone builds are explicitly unstable. RC builds are close but can have last-minute breaking changes. Use only GA releases in production. On start.spring.io, GA is the default; you have to opt into Snapshot or Milestone explicitly.

> **Spring Boot EOL ≠ immediate security risk, but close.** The day Spring Boot 3.x goes EOL, the Spring team stops publishing CVE patches. Any vulnerability discovered after that date will not be fixed on that branch. Budget time for minor version upgrades before they expire.

- Only use GA (General Availability) releases in production. Avoid SNAPSHOT / Milestone / RC.
- Patch versions (x.y.z) are always safe to apply immediately — no feature changes, only bug fixes.
- Minor version upgrades need your test suite to pass; review the release notes for deprecations.
- Major version upgrades are migrations — plan 1–2 sprints, especially the `javax.*` → `jakarta.*` rename.
- Check [spring.io/projects/spring-boot#support](https://spring.io/projects/spring-boot#support) for the live EOL matrix before starting a long-lived project.
