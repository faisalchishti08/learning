---
card: spring-framework
gi: 23
slug: filesystemxmlapplicationcontext
title: FileSystemXmlApplicationContext
---

## 1. What it is

`FileSystemXmlApplicationContext` loads Spring bean definitions from XML files using **filesystem paths** rather than classpath paths. You give it an absolute or relative path to a file on disk and Spring reads the XML directly.

```java
// Absolute path
ApplicationContext ctx =
    new FileSystemXmlApplicationContext("/etc/myapp/beans.xml");

// Relative to the JVM working directory
ApplicationContext ctx2 =
    new FileSystemXmlApplicationContext("config/beans.xml");

// Explicit prefix (same as default for this class)
ApplicationContext ctx3 =
    new FileSystemXmlApplicationContext("file:/opt/app/beans.xml");
```

`ClassPathXmlApplicationContext` looks inside JARs and the classpath; `FileSystemXmlApplicationContext` looks on the filesystem — useful when configuration must live outside the deployment artifact so operators can edit it without repackaging.

In one sentence: **`FileSystemXmlApplicationContext` is the `ApplicationContext` variant that loads XML bean definitions from filesystem paths, enabling externalized configuration that changes without redeploying the app.**

## 2. Why & when

Choose `FileSystemXmlApplicationContext` when:

- **Configuration must be externalized.** Database credentials, environment-specific URLs, or feature toggles need to live outside the JAR so operations teams can change them without a rebuild.
- **Running configuration management tools.** Ansible, Chef, or Puppet can write `/etc/myapp/beans.xml`; the app reads it directly.
- **Integration testing against real files.** A test creates a temporary file, writes XML, points `FileSystemXmlApplicationContext` at it — no classpath manipulation needed.
- **Command-line tools or scripts** where the config path is a command-line argument.

For applications packaged as executable JARs (Spring Boot), externalized config is better handled via `application.properties` and Spring profiles. `FileSystemXmlApplicationContext` is most useful in pre-Boot Spring apps or tools that need full control of config file location.

## 3. Core concept

`FileSystemXmlApplicationContext` shares the same `AbstractXmlApplicationContext` inheritance chain as `ClassPathXmlApplicationContext`. The only difference is in resource resolution:

```
ClassPathXmlApplicationContext   → ClassPathResource   (classpath:)
FileSystemXmlApplicationContext  → FileSystemResource  (file:)
```

A `FileSystemResource` resolves relative paths against the **JVM working directory** (`System.getProperty("user.dir")`), not the classpath. Absolute paths (`/opt/app/beans.xml`) always resolve as expected.

```
new FileSystemXmlApplicationContext("beans.xml")
  → FileSystemResource("beans.xml")       // relative to working dir
  → [same refresh() lifecycle as CPXAC]
  → all singletons ready
```

Key implication: if you package your app as a JAR and run it from `/opt/myapp`, then `"config/beans.xml"` resolves to `/opt/myapp/config/beans.xml` — outside the JAR, exactly what externalized config requires.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="FileSystemXmlApplicationContext resolving filesystem path vs ClassPathXmlApplicationContext resolving classpath">
  <defs>
    <marker id="a23" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Filesystem path -->
  <rect x="10" y="20" width="180" height="56" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">/etc/myapp/beans.xml</text>
  <text x="100" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">FileSystemResource (disk)</text>

  <!-- FSXAC -->
  <rect x="265" y="10" width="185" height="70" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="357" y="35" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">FileSystemXml</text>
  <text x="357" y="51" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">ApplicationContext</text>
  <text x="357" y="69" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">same refresh() lifecycle</text>

  <line x1="190" y1="48" x2="263" y2="45" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a23)"/>

  <!-- Classpath path -->
  <rect x="10" y="125" width="180" height="56" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="100" y="147" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">classpath:beans.xml</text>
  <text x="100" y="165" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ClassPathResource (JAR/dir)</text>

  <!-- CPXAC -->
  <rect x="265" y="115" width="185" height="70" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="357" y="140" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">ClassPathXml</text>
  <text x="357" y="156" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">ApplicationContext</text>
  <text x="357" y="174" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">same refresh() lifecycle</text>

  <line x1="190" y1="153" x2="263" y2="153" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a23)"/>

  <!-- Beans -->
  <rect x="530" y="50" width="140" height="96" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="600" y="72" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">ApplicationContext</text>
  <text x="600" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">beans ready</text>
  <text x="600" y="107" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">deps injected</text>
  <text x="600" y="124" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">same API either way</text>

  <line x1="450" y1="45" x2="528" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a23)"/>
  <line x1="450" y1="153" x2="528" y2="120" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a23)"/>

  <text x="340" y="205" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Only the resource type differs — the context API, DI, and lifecycle are identical</text>
</svg>

Both classes produce identical `ApplicationContext` behaviour. The difference is purely in where the XML is found: disk for `FileSystemXmlApplicationContext`, classpath for `ClassPathXmlApplicationContext`.

## 5. Runnable example

Scenario: a monitoring tool that reads alert thresholds from an external XML config file. The file lives on disk (outside the JAR) so ops teams can adjust limits without redeployment. We evolve from reading a fixed file to watching for hot reloads.

### Level 1 — Basic

Read alert config from a filesystem path; if the file does not exist, use defaults.

```java
// FsxacDemo.java — run with: java FsxacDemo.java
import java.io.*;
import java.util.*;

public class FsxacDemo {

    record AlertConfig(double cpuWarnPct, double memWarnPct) {}

    static class AlertService {
        private final AlertConfig config;
        AlertService(AlertConfig config) { this.config = config; }
        void check(double cpu, double mem) {
            System.out.printf("  CPU=%.0f%% (warn>%.0f%%): %s%n",
                cpu, config.cpuWarnPct(), cpu > config.cpuWarnPct() ? "WARN" : "OK");
            System.out.printf("  MEM=%.0f%% (warn>%.0f%%): %s%n",
                mem, config.memWarnPct(), mem > config.memWarnPct() ? "WARN" : "OK");
        }
    }

    // Simulates FileSystemXmlApplicationContext reading from a path
    static class FsContext {
        private final String configPath;
        private AlertService alertService;

        FsContext(String configPath) {
            this.configPath = configPath;
            refresh();
        }

        void refresh() {
            System.out.println("[FS-CTX] Loading from: " + new File(configPath).getAbsolutePath());
            AlertConfig config;
            File f = new File(configPath);
            if (f.exists()) {
                // In real life: parse XML. Here: read simple key=value lines.
                try {
                    Properties p = new Properties();
                    p.load(new FileReader(f));
                    config = new AlertConfig(
                        Double.parseDouble(p.getProperty("cpu.warn.pct", "80")),
                        Double.parseDouble(p.getProperty("mem.warn.pct", "90"))
                    );
                    System.out.println("[FS-CTX] Loaded from file: " + config);
                } catch (Exception e) {
                    config = new AlertConfig(80.0, 90.0);
                    System.out.println("[FS-CTX] Parse error — using defaults: " + config);
                }
            } else {
                config = new AlertConfig(80.0, 90.0);
                System.out.println("[FS-CTX] File not found — using defaults: " + config);
            }
            alertService = new AlertService(config);
        }

        AlertService getAlertService() { return alertService; }
    }

    public static void main(String[] args) throws Exception {
        // Use a temp file to simulate an external config on disk
        File configFile = File.createTempFile("monitor-beans", ".properties");
        configFile.deleteOnExit();

        System.out.println("=== Run 1: file not yet written (defaults) ===");
        FsContext ctx1 = new FsContext("/nonexistent/path/beans.properties");
        ctx1.getAlertService().check(65.0, 92.0);

        System.out.println("\n=== Run 2: config written to disk ===");
        try (var w = new FileWriter(configFile)) {
            w.write("cpu.warn.pct=70\n");
            w.write("mem.warn.pct=85\n");
        }
        FsContext ctx2 = new FsContext(configFile.getAbsolutePath());
        ctx2.getAlertService().check(75.0, 80.0);
    }
}
```

How to run: `java FsxacDemo.java`

Run 1 uses defaults (80% / 90%) because the file does not exist. Run 2 reads real thresholds from the temp file on disk. The path is absolute — in production this would be `/etc/monitoring/beans.xml`, edited by an operator without touching the JAR.

### Level 2 — Intermediate

Add multiple config files. A base config provides defaults; a site-specific override file (on the filesystem) can change selected values. The last file wins — same behaviour as Spring's multi-file context.

```java
// FsxacDemo2.java — run with: java FsxacDemo2.java
import java.io.*;
import java.util.*;

public class FsxacDemo2 {

    record AlertConfig(double cpuWarnPct, double memWarnPct, String severity) {}

    static class AlertService {
        private final AlertConfig config;
        AlertService(AlertConfig config) { this.config = config; }
        void check(double cpu, double mem) {
            boolean cpuWarn = cpu > config.cpuWarnPct();
            boolean memWarn = mem > config.memWarnPct();
            System.out.printf("  CPU=%.0f%% → %s | MEM=%.0f%% → %s | severity=%s%n",
                cpu, cpuWarn ? "WARN" : "OK",
                mem, memWarn ? "WARN" : "OK",
                (cpuWarn || memWarn) ? config.severity() : "none");
        }
    }

    static Properties loadProperties(File... files) throws Exception {
        Properties merged = new Properties();
        for (File f : files) {
            if (!f.exists()) { System.out.println("  [SKIP] " + f.getName() + " not found"); continue; }
            Properties p = new Properties();
            p.load(new FileReader(f));
            merged.putAll(p);
            System.out.println("  [LOAD] " + f.getAbsolutePath() + " → " + p.keySet());
        }
        return merged;
    }

    static class MultiFileFsContext {
        private final File[] files;
        private AlertService alertService;

        MultiFileFsContext(File... files) throws Exception {
            this.files = files;
            refresh();
        }

        void refresh() throws Exception {
            System.out.println("[FS-CTX] Merging " + files.length + " config file(s)...");
            Properties p = loadProperties(files);
            AlertConfig config = new AlertConfig(
                Double.parseDouble(p.getProperty("cpu.warn.pct", "80")),
                Double.parseDouble(p.getProperty("mem.warn.pct", "90")),
                p.getProperty("alert.severity", "MEDIUM")
            );
            alertService = new AlertService(config);
            System.out.println("[FS-CTX] Active config: " + config + "\n");
        }

        AlertService getAlertService() { return alertService; }
    }

    public static void main(String[] args) throws Exception {
        File base     = File.createTempFile("base-beans",     ".properties");
        File override = File.createTempFile("site-beans",     ".properties");
        base.deleteOnExit(); override.deleteOnExit();

        // Write base config (defaults for all environments)
        try (var w = new FileWriter(base)) {
            w.write("cpu.warn.pct=80\n");
            w.write("mem.warn.pct=90\n");
            w.write("alert.severity=LOW\n");
        }

        System.out.println("=== Production site override: stricter thresholds ===");
        try (var w = new FileWriter(override)) {
            w.write("cpu.warn.pct=60\n");      // override: stricter CPU threshold
            w.write("alert.severity=HIGH\n");  // override: higher severity
            // mem.warn.pct NOT overridden → stays 90 from base
        }

        // base loaded first, override loaded second — later wins on conflicts
        MultiFileFsContext ctx = new MultiFileFsContext(base, override);
        ctx.getAlertService().check(65.0, 88.0);  // cpu > 60 → WARN/HIGH
        ctx.getAlertService().check(55.0, 88.0);  // cpu ≤ 60 → OK
    }
}
```

How to run: `java FsxacDemo2.java`

Base provides defaults; the site override on the filesystem changes `cpu.warn.pct` and `alert.severity` without touching `mem.warn.pct`. This is the standard pattern for multi-environment Spring deployments: `base-beans.xml` in the JAR, `production-beans.xml` on the filesystem.

### Level 3 — Advanced

Add hot reload: a background watcher detects when the config file is modified on disk and calls `refresh()` on the context — picking up new thresholds without restarting the JVM.

```java
// FsxacDemo3.java — run with: java FsxacDemo3.java
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.atomic.*;

public class FsxacDemo3 {

    record AlertConfig(double cpuWarnPct, double memWarnPct, String severity) {}

    static class AlertService {
        private final AlertConfig config;
        AlertService(AlertConfig config) { this.config = config; }
        void check(double cpu, double mem) {
            boolean w = cpu > config.cpuWarnPct() || mem > config.memWarnPct();
            System.out.printf("  cpu=%.0f%% mem=%.0f%% thresholds=(%.0f%%/%.0f%%) → %s%n",
                cpu, mem, config.cpuWarnPct(), config.memWarnPct(),
                w ? "ALERT[" + config.severity() + "]" : "OK");
        }
    }

    // Refreshable context — config reloaded when file changes
    static class RefreshableFsContext {
        private final File configFile;
        private volatile AlertService alertService;
        private volatile long lastModified = -1;

        RefreshableFsContext(File configFile) throws Exception {
            this.configFile = configFile;
            refresh();
        }

        synchronized void refresh() throws Exception {
            long mod = configFile.lastModified();
            if (mod == lastModified) return;
            lastModified = mod;
            Properties p = new Properties();
            if (configFile.exists()) p.load(new FileReader(configFile));
            AlertConfig config = new AlertConfig(
                Double.parseDouble(p.getProperty("cpu.warn.pct", "80")),
                Double.parseDouble(p.getProperty("mem.warn.pct", "90")),
                p.getProperty("alert.severity", "MEDIUM")
            );
            alertService = new AlertService(config);
            System.out.println("  [RELOAD] New config: cpu>" + config.cpuWarnPct()
                + "% mem>" + config.memWarnPct() + "% sev=" + config.severity());
        }

        AlertService getAlertService() { return alertService; }

        // Returns a Runnable that polls for file changes
        Runnable watcherTask() {
            return () -> {
                while (!Thread.interrupted()) {
                    try { refresh(); Thread.sleep(100); }
                    catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                    catch (Exception e) { System.out.println("  [WATCH ERROR] " + e.getMessage()); }
                }
            };
        }
    }

    static void writeConfig(File f, String cpu, String mem, String sev) throws Exception {
        try (var w = new FileWriter(f)) {
            w.write("cpu.warn.pct=" + cpu + "\n");
            w.write("mem.warn.pct=" + mem + "\n");
            w.write("alert.severity=" + sev + "\n");
        }
    }

    public static void main(String[] args) throws Exception {
        File configFile = File.createTempFile("hot-reload-beans", ".properties");
        configFile.deleteOnExit();

        // Initial config
        writeConfig(configFile, "80", "90", "LOW");
        RefreshableFsContext ctx = new RefreshableFsContext(configFile);

        Thread watcher = new Thread(ctx.watcherTask(), "config-watcher");
        watcher.setDaemon(true);
        watcher.start();

        System.out.println("=== Initial thresholds (80%/90% LOW) ===");
        ctx.getAlertService().check(75.0, 85.0);
        ctx.getAlertService().check(85.0, 95.0);

        // Ops team modifies file on disk — simulates operator edit
        System.out.println("\n[OPS] Tightening thresholds on disk...");
        Thread.sleep(150);  // let watcher see the old file first
        writeConfig(configFile, "60", "75", "CRITICAL");
        Thread.sleep(200);  // allow watcher to detect change

        System.out.println("\n=== After hot reload (60%/75% CRITICAL) ===");
        ctx.getAlertService().check(65.0, 70.0);  // cpu triggers now
        ctx.getAlertService().check(50.0, 80.0);  // mem triggers now

        watcher.interrupt();
    }
}
```

How to run: `java FsxacDemo3.java`

After the ops team writes new thresholds to the file on disk, the watcher thread detects the `lastModified` change and calls `refresh()`, atomically replacing `alertService`. The next `getAlertService().check(...)` call uses the new thresholds — no restart required. Real Spring does not include a file watcher by default, but Spring Cloud Config and custom `ApplicationListener<ContextRefreshedEvent>` provide similar behaviour.

## 6. Walkthrough

**Level 3 — hot reload sequence:**

1. `configFile` written with `cpu=80, mem=90, sev=LOW`.
2. `RefreshableFsContext` constructor → `refresh()` → loads file → creates `AlertService(80, 90, LOW)`.
3. Background `watcher` thread starts; polls every 100 ms via `refresh()`.
4. `check(75, 85)` → both within limits → OK. `check(85, 95)` → both above → ALERT[LOW].
5. `writeConfig(configFile, "60", "75", "CRITICAL")` overwrites the file on disk.
6. 200 ms later, `watcher` calls `refresh()` → `configFile.lastModified()` changed → reloads → new `AlertService(60, 75, CRITICAL)` assigned atomically.
7. `check(65, 70)` → cpu=65 > 60 → ALERT[CRITICAL]. `check(50, 80)` → mem=80 > 75 → ALERT[CRITICAL].

**Data state at each stage:**

| Stage | Config on disk | Active `AlertConfig` |
|---|---|---|
| Startup | cpu=80, mem=90, sev=LOW | `(80, 90, LOW)` |
| After ops edit | cpu=60, mem=75, sev=CRITICAL | `(60, 75, CRITICAL)` |
| `check(65, 70)` | — | cpu 65 > 60 → ALERT/CRITICAL |
| `check(50, 80)` | — | mem 80 > 75 → ALERT/CRITICAL |

## 7. Gotchas & takeaways

> **Relative paths resolve to the JVM working directory, not the classpath.** `new FileSystemXmlApplicationContext("beans.xml")` looks in `System.getProperty("user.dir")`. If the JVM is started from `/home/user`, it looks at `/home/user/beans.xml` — not inside the JAR. This is surprising when compared to `ClassPathXmlApplicationContext`.

> **Use `file:` prefix to force filesystem resolution in any `ApplicationContext`.** Inside any Spring XML file or `@Value`, `file:/opt/app/beans.xml` always means the filesystem. Omitting the prefix inside a `ClassPathXmlApplicationContext` will resolve to the classpath, not the filesystem.

- Absolute paths (`/etc/myapp/beans.xml`) behave predictably regardless of working directory; prefer them in production deployments.
- `FileSystemXmlApplicationContext` triggers `refresh()` in its constructor — any file-not-found or XML parse error throws before the constructor returns, failing the app at startup.
- Hot config reloading requires explicit refresh calls or a scheduled watcher. Spring Cloud Config and Spring Boot Actuator's `/actuator/refresh` endpoint provide this out-of-the-box.
- `FileSystemResource` can also be used directly in `@Value("file:/etc/myapp/data.json")` or with `ResourceLoader` to read arbitrary files outside the classpath.
- In Docker containers, mount the external config directory as a volume (`-v /host/config:/etc/myapp`) and point `FileSystemXmlApplicationContext` at `/etc/myapp/beans.xml` — the container sees the host file without baking credentials into the image.
