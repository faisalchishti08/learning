---
card: spring-boot
gi: 202
slug: process-monitoring-pid-files
title: Process monitoring & PID files
---

## 1. What it is

Spring Boot can write the **process ID (PID)** of the running application to a file at startup. This PID file is used by Unix service managers (`systemd`, `init.d`, `supervisord`) to identify the process for stop/restart/health-check operations. Spring Boot provides two listeners — `ApplicationPidFileWriter` and `WebServerPortFileWriter` — that write PID and HTTP port files when the application starts.

## 2. Why & when

PID files are essential when running Spring Boot as a **system service**:
- `systemctl stop myapp` uses the PID file to send `SIGTERM` to the right process.
- `init.d` scripts read `/var/run/myapp/myapp.pid` to check if the app is running.
- Monitoring tools poll the PID to verify the process is alive.

If you deploy Spring Boot as a `.jar` with `spring-boot:run` or `java -jar` under `systemd`, you typically don't need a PID file (systemd tracks the process itself). PID files matter most for legacy `init.d`-style deployments or custom process supervisors.

## 3. Core concept

**Register PID file writer** in `application.properties`:
```properties
spring.pid.file=/var/run/myapp/myapp.pid
spring.pid.fail-on-write-error=true
```

Or programmatically:
```java
SpringApplication app = new SpringApplication(MyApp.class);
app.addListeners(new ApplicationPidFileWriter("/var/run/myapp/myapp.pid"));
app.addListeners(new WebServerPortFileWriter("/var/run/myapp/myapp.port"));
app.run(args);
```

The PID file is written on the `ApplicationStartedEvent`. On JVM shutdown (normal exit or `SIGTERM`), Spring Boot deletes the PID file automatically.

**Using as a service (`init.d`):** Spring Boot's executable JAR embeds an `init.d`-compatible start/stop script. When installed as a service:
```bash
sudo ln -s /opt/myapp/myapp.jar /etc/init.d/myapp
sudo service myapp start   # writes PID to /var/run/myapp/myapp.pid
sudo service myapp stop    # reads PID, sends SIGTERM, deletes file
sudo service myapp status  # checks if PID is alive
```

## 4. Diagram

<svg viewBox="0 0 680 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot starts, ApplicationPidFileWriter writes PID file; systemd/init.d reads PID to send SIGTERM; on shutdown PID file is deleted">
  <!-- Spring Boot startup -->
  <rect x="10" y="30" width="155" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="87" y="52" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Boot</text>
  <text x="87" y="68" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">ApplicationStartedEvent</text>
  <text x="87" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">PID = OS process id</text>

  <!-- Arrow to writer -->
  <line x1="167" y1="60" x2="225" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#pma)"/>

  <!-- Listener -->
  <rect x="230" y="38" width="185" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="322" y="57" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">ApplicationPidFileWriter</text>
  <text x="322" y="73" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">writes PID to /var/run/myapp.pid</text>

  <!-- Arrow to PID file -->
  <line x1="417" y1="60" x2="470" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#pma)"/>

  <!-- PID file -->
  <rect x="475" y="38" width="130" height="45" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="56" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">myapp.pid</text>
  <text x="540" y="72" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">content: 12345</text>

  <!-- systemd / init.d reads PID -->
  <rect x="475" y="110" width="195" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="572" y="129" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">systemd / init.d</text>
  <text x="572" y="144" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reads PID → kill -SIGTERM 12345</text>
  <text x="572" y="157" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">status: kill -0 12345</text>

  <line x1="540" y1="85" x2="540" y2="108" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#pmb)"/>

  <!-- Shutdown -->
  <rect x="10" y="120" width="155" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="87" y="140" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">JVM Shutdown Hook</text>
  <text x="87" y="155" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">deletes PID file on exit</text>

  <line x1="167" y1="145" x2="473" y2="60" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>

  <defs>
    <marker id="pma" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="pmb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

PID file written at startup, deleted at shutdown; service managers use it to stop or monitor the process.

## 5. Runnable example

```java
// ProcessMonitoringDemo.java — simulates PID file lifecycle
// How to run: java ProcessMonitoringDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: spring.pid.file=/var/run/myapp.pid in application.properties

import java.io.*;
import java.nio.file.*;

public class ProcessMonitoringDemo {

    // Simulates ApplicationPidFileWriter
    static class PidFileWriter {
        private final Path pidFile;

        PidFileWriter(String path) {
            this.pidFile = Path.of(path);
        }

        void write(long pid) throws IOException {
            Files.createDirectories(pidFile.getParent());
            Files.writeString(pidFile, String.valueOf(pid));
            System.out.println("[PidFileWriter] Wrote PID " + pid + " → " + pidFile);
        }

        void delete() {
            try {
                Files.deleteIfExists(pidFile);
                System.out.println("[PidFileWriter] Deleted PID file: " + pidFile);
            } catch (IOException e) {
                System.err.println("[PidFileWriter] Could not delete PID file: " + e.getMessage());
            }
        }

        long read() throws IOException {
            return Long.parseLong(Files.readString(pidFile).trim());
        }

        boolean exists() { return Files.exists(pidFile); }
    }

    // Simulates WebServerPortFileWriter
    static class PortFileWriter {
        private final Path portFile;
        PortFileWriter(String path) { this.portFile = Path.of(path); }

        void write(int port) throws IOException {
            Files.createDirectories(portFile.getParent());
            Files.writeString(portFile, String.valueOf(port));
            System.out.println("[PortFileWriter] Wrote port " + port + " → " + portFile);
        }

        void delete() throws IOException { Files.deleteIfExists(portFile); }
    }

    // Simulate service manager commands
    static void serviceStatus(PidFileWriter pidWriter) throws IOException {
        if (!pidWriter.exists()) {
            System.out.println("[service myapp status] => STOPPED (no PID file)");
            return;
        }
        long pid = pidWriter.read();
        // kill -0 checks process existence without sending a signal
        boolean alive = ProcessHandle.of(pid).isPresent();
        System.out.println("[service myapp status] => " + (alive ? "RUNNING (pid=" + pid + ")" : "DEAD (stale PID file)"));
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Process Monitoring & PID Files Demo ===\n");

        // Use temp directory for demo
        String tmpDir = System.getProperty("java.io.tmpdir") + "/myapp-demo";
        PidFileWriter pidWriter  = new PidFileWriter(tmpDir + "/myapp.pid");
        PortFileWriter portWriter = new PortFileWriter(tmpDir + "/myapp.port");

        // Register shutdown hook (mirrors Spring Boot's cleanup)
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("\n[ShutdownHook] Cleaning up PID file...");
            pidWriter.delete();
        }));

        System.out.println("--- Application startup ---");
        long pid = ProcessHandle.current().pid();
        pidWriter.write(pid);
        portWriter.write(8080);

        System.out.println("\n--- Service manager queries ---");
        serviceStatus(pidWriter);

        System.out.println("\nPID file content: " + pidWriter.read());
        System.out.println("PID file path:    " + tmpDir + "/myapp.pid");

        System.out.println("\n--- init.d / systemd usage ---");
        System.out.println("# Install as init.d service:");
        System.out.println("sudo ln -s /opt/myapp/myapp.jar /etc/init.d/myapp");
        System.out.println("sudo service myapp start");
        System.out.println("sudo service myapp stop");
        System.out.println("sudo service myapp status");
        System.out.println();
        System.out.println("# application.properties:");
        System.out.println("spring.pid.file=/var/run/myapp/myapp.pid");
        System.out.println("spring.pid.fail-on-write-error=true");
        System.out.println();
        System.out.println("# Programmatic registration:");
        System.out.println("SpringApplication app = new SpringApplication(MyApp.class);");
        System.out.println("app.addListeners(new ApplicationPidFileWriter(\"/var/run/myapp.pid\"));");
        System.out.println("app.addListeners(new WebServerPortFileWriter(\"/var/run/myapp.port\"));");

        System.out.println("\n--- Simulating shutdown (ShutdownHook fires on exit) ---");
        // JVM shutdown hook fires automatically at process exit — see registration above
    }
}
```

**How to run:** `java ProcessMonitoringDemo.java`

## 6. Walkthrough

- **`PidFileWriter.write(pid)`**: mirrors `ApplicationPidFileWriter` — creates parent directories and writes the OS PID to the file. `ProcessHandle.current().pid()` is the JDK 9+ API that returns the current process ID.
- **`PortFileWriter.write(8080)`**: mirrors `WebServerPortFileWriter` — writes the HTTP port so external tools know which port the app is listening on (useful when `server.port=0` picks a random port).
- **`serviceStatus`**: simulates `kill -0 <pid>` — `ProcessHandle.of(pid).isPresent()` checks process existence without sending a signal. If the PID file exists but the process is gone, it reports `DEAD (stale PID file)`.
- **Shutdown hook**: mirrors Spring Boot's cleanup — the PID file is deleted when the JVM exits so service managers don't see a stale PID after restart.

## 7. Gotchas & takeaways

> `spring.pid.fail-on-write-error=true` causes the application to **fail to start** if the PID file cannot be written (e.g., directory doesn't exist or wrong permissions). Set this in production to catch misconfiguration early rather than silently ignoring it.

> If the JVM is killed with `kill -9` (SIGKILL), the shutdown hook **does not run** and the PID file is not deleted. The next start attempt may fail if `fail-on-write-error=true` and the stale file is not cleaned up. Always clean up stale PID files in your init/service script's pre-start logic.

- `spring.pid.file` is the simplest configuration — no code changes needed.
- `WebServerPortFileWriter` is useful with `server.port=0` (random port) — other processes can read the port file to discover which port was assigned.
- For `systemd` deployments, prefer `Type=notify` or `Type=simple` with `WatchdogSec` instead of PID files — systemd tracks the process directly.
- The executable JAR's embedded init.d script reads `spring.pid.file` automatically.
