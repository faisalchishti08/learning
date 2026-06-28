---
card: spring-boot
gi: 93
slug: file-output-rotation
title: File output & rotation
---

## 1. What it is

By default Spring Boot logs only to the console (stdout). To write logs to a **file**, you set one of two properties:

- `logging.file.name=app.log` — writes to `app.log` in the current working directory (or an absolute path).
- `logging.file.path=/var/log/myapp` — writes to `spring.log` in the specified directory.

If both are set, `logging.file.name` wins.

Log files are **rotated** automatically by Spring Boot's bundled Logback configuration:
- Default maximum file size: **10 MB**.
- Default maximum history: **7 days** of rotated files kept.
- Default total size cap: **100 MB** across all rotated files.
- Compressed archives: rotated files are compressed to `.gz` by default.

These defaults can be overridden with `logging.logback.rollingpolicy.*` properties without touching any XML.

## 2. Why & when

Console output is ephemeral — once the terminal session ends or the container restarts, logs are gone. File logging is essential when:
- You need to diagnose an issue that happened hours ago.
- Your deployment environment doesn't forward stdout to a log aggregator automatically.
- Audit or compliance requirements mandate log retention.
- You run batch jobs that produce large volumes of output that you want to archive.

In container-native environments (Docker, Kubernetes) with a log aggregator (Fluent Bit, Filebeat), you often ship console logs to the aggregator rather than writing files — the aggregator handles retention. But for VM-based deployments, direct file logging with rotation remains the primary approach.

## 3. Core concept

Spring Boot's `RollingFileAppender` configuration in `file.xml` sets up a **time-based rolling policy** combined with a **size cap**:

```
spring.log            ← current active file
spring.log.2026-06-27.0.gz   ← yesterday's rotation, compressed
spring.log.2026-06-26.0.gz
…  (up to 7 days kept by default)
```

**Rotation triggers:**
1. The active file exceeds `logging.logback.rollingpolicy.max-file-size` (default 10 MB).
2. The date changes at midnight.

**Property reference:**
```properties
logging.file.name=logs/app.log
logging.logback.rollingpolicy.max-file-size=50MB
logging.logback.rollingpolicy.max-history=30
logging.logback.rollingpolicy.total-size-cap=2GB
logging.logback.rollingpolicy.clean-history-on-start=true
logging.logback.rollingpolicy.file-name-pattern=${LOG_FILE}.%d{yyyy-MM-dd}.%i.gz
```

When file logging is active, Spring Boot writes to **both** console and file, each with their own pattern (`logging.pattern.console` and `logging.pattern.file`).

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Log file rotation: active file grows to max-file-size then rotates; old files compressed and kept up to max-history days">
  <rect x="8" y="8" width="664" height="264" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Log File Rotation (time-based + size cap)</text>

  <!-- Active file -->
  <rect x="40" y="55" width="200" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="140" y="75" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">app.log (active)</text>
  <text x="140" y="93" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">currently being written</text>
  <text x="140" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ rotates when &gt;10 MB or midnight</text>

  <!-- Arrow -->
  <defs><marker id="ra" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker></defs>
  <line x1="242" y1="84" x2="275" y2="84" stroke="#f0883e" stroke-width="1.5" marker-end="url(#ra)"/>
  <text x="258" y="78" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">rotate</text>

  <!-- Rotated files stack -->
  <rect x="278" y="45" width="360" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="458" y="59" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">app.log.2026-06-28.0.gz</text>
  <text x="458" y="73" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">today's first rotation — compressed</text>

  <rect x="278" y="88" width="360" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="458" y="102" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">app.log.2026-06-27.0.gz</text>
  <text x="458" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">yesterday — compressed</text>

  <rect x="278" y="131" width="360" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="458" y="145" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">app.log.2026-06-21.0.gz</text>
  <text x="458" y="159" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">oldest kept (7 days default) — deleted next</text>

  <!-- Property box -->
  <rect x="40" y="185" width="600" height="70" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="202" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Key properties (application.properties)</text>
  <text x="60" y="218" fill="#e6edf3" font-size="9" font-family="monospace">logging.file.name=logs/app.log</text>
  <text x="60" y="232" fill="#e6edf3" font-size="9" font-family="monospace">logging.logback.rollingpolicy.max-file-size=50MB</text>
  <text x="60" y="246" fill="#e6edf3" font-size="9" font-family="monospace">logging.logback.rollingpolicy.max-history=30</text>
  <text x="360" y="218" fill="#e6edf3" font-size="9" font-family="monospace">logging.logback.rollingpolicy.total-size-cap=2GB</text>
  <text x="360" y="232" fill="#e6edf3" font-size="9" font-family="monospace">logging.logback.rollingpolicy.clean-history-on-start=false</text>
</svg>

Files are rotated on size or date change; older compressed archives are pruned automatically.

## 5. Runnable example

```java
// FileOutputRotation.java — run: java FileOutputRotation.java  (JDK 17+)
// Simulates log file rotation logic to illustrate when rotation triggers and what is kept.

import java.util.*;
import java.time.LocalDate;

public class FileOutputRotation {

    static final long MAX_FILE_SIZE = 10 * 1024 * 1024L; // 10 MB
    static final int  MAX_HISTORY   = 7;                  // days
    static final long TOTAL_SIZE_CAP = 100 * 1024 * 1024L; // 100 MB

    static class LogRotator {
        private final String baseName;
        private long currentSize = 0;
        private LocalDate currentDate = LocalDate.now();
        private int indexToday = 0;
        private final List<String> archives = new ArrayList<>();
        private long archiveBytes = 0;

        LogRotator(String baseName) { this.baseName = baseName; }

        void write(int bytes, LocalDate logDate) {
            if (!logDate.equals(currentDate)) {
                rotate("date-change → " + currentDate);
                currentDate = logDate;
                indexToday = 0;
            } else if (currentSize + bytes > MAX_FILE_SIZE) {
                rotate("size exceeded (" + (currentSize / 1_048_576) + " MB)");
            }
            currentSize += bytes;
        }

        private void rotate(String reason) {
            String archiveName = baseName + "." + currentDate + "." + indexToday + ".gz";
            long estimatedGz = (long) (currentSize * 0.3);  // ~70% compression
            archives.add(archiveName + " (" + (estimatedGz / 1024) + " KB compressed)");
            archiveBytes += estimatedGz;
            System.out.printf("[ROTATE] %s — reason: %s%n", archiveName, reason);
            System.out.printf("         Current archive count: %d%n", archives.size());
            currentSize = 0;
            indexToday++;
            pruneOldArchives();
        }

        private void pruneOldArchives() {
            LocalDate cutoff = currentDate.minusDays(MAX_HISTORY);
            archives.removeIf(a -> {
                String dateStr = a.split("\\.")[1];
                boolean tooOld = LocalDate.parse(dateStr).isBefore(cutoff);
                if (tooOld) System.out.printf("[PRUNE]  Deleting %s (older than %d days)%n", a, MAX_HISTORY);
                return tooOld;
            });
        }

        void status() {
            System.out.printf("Active log: %s (%.1f MB used)%n", baseName, currentSize / 1_048_576.0);
            System.out.println("Archives  : " + archives.size() + " files");
            archives.forEach(a -> System.out.println("  " + a));
        }
    }

    public static void main(String[] args) {
        LogRotator r = new LogRotator("app.log");

        // Day 1 — one size-based rotation
        LocalDate day1 = LocalDate.of(2026, 6, 22);
        System.out.println("=== Day 1 ===");
        r.write(6 * 1024 * 1024, day1);   // 6 MB
        r.write(5 * 1024 * 1024, day1);   // +5 MB = 11 MB → triggers size rotation
        r.write(3 * 1024 * 1024, day1);   // 3 MB in new file

        // Days 2-8 — date-based rotations
        for (int d = 2; d <= 8; d++) {
            LocalDate day = LocalDate.of(2026, 6, 22 + d - 1);
            System.out.println("\n=== Day " + d + " ===");
            r.write(8 * 1024 * 1024, day);
        }

        System.out.println("\n=== Final status ===");
        r.status();
    }
}
```

**How to run:** `java FileOutputRotation.java`

## 6. Walkthrough

- `MAX_FILE_SIZE = 10 MB` and `MAX_HISTORY = 7 days` mirror Spring Boot's Logback defaults from `file.xml`. These defaults apply automatically when `logging.file.name` is set; no XML needed.
- `write(6 MB, day1)` then `write(5 MB, day1)` — the second write pushes total to 11 MB, exceeding the 10 MB cap. `rotate()` is called with reason `"size exceeded"`. The active file resets to 0 bytes; the archive is given index `0` (`app.log.2026-06-22.0.gz`).
- Each archive size is estimated at 30% of the raw size (`0.3 * currentSize`). Logback's actual `.gz` compression ratio depends on log content; text logs typically compress 70–80%.
- `pruneOldArchives()` simulates Logback's `maxHistory` enforcement. After 7 days have elapsed, the oldest archive is deleted. This prevents unbounded disk growth even if `total-size-cap` is not hit.
- The day-based loop triggers a `rotate()` on each date boundary. Even a 3 MB file is rotated at midnight — because date-change rotation fires before size is considered.
- `status()` at the end shows the final archive list — 7 days of history at most, with the oldest day-1 rotation pruned on day 8.

## 7. Gotchas & takeaways

> **Setting `logging.file.name` or `logging.file.path` does not disable console logging.** Both console and file receive all log events. If you want file-only output, configure a custom `logback-spring.xml` that removes the `ConsoleAppender`.

> **`logging.logback.rollingpolicy.*` properties only work with the default Logback configuration.** If you provide your own `logback-spring.xml`, these properties are ignored — you must configure rolling policy directly in the XML.

- `logging.file.name` accepts a relative path (relative to the current working directory) or an absolute path. For containers, prefer an absolute path to avoid ambiguity.
- `clean-history-on-start=true` deletes old archives on every application startup — useful in CI environments that reuse directories but dangerous in long-running services if you need historical logs.
- The `total-size-cap` property is a hard ceiling across all rotated files. When exceeded, the oldest archives are deleted regardless of `max-history`.
- Rotated files use `.gz` compression by default. To disable, override `logging.logback.rollingpolicy.file-name-pattern` and remove the `.gz` suffix.
- In Kubernetes, mount a persistent volume for the log directory; otherwise log files vanish with the pod.
