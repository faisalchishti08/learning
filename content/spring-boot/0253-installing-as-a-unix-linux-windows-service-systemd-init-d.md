---
card: spring-boot
gi: 253
slug: installing-as-a-unix-linux-windows-service-systemd-init-d
title: Installing as a Unix/Linux/Windows service (systemd, init.d)
---

## 1. What it is

Spring Boot can package an executable JAR that runs as a managed **OS service** — a process supervised by the operating system that starts automatically on boot, restarts on failure, and integrates with system logging.

Two mechanisms are supported:

- **systemd** (modern Linux) — the preferred approach on Ubuntu 16+, RHEL 7+, Debian 8+. You write a `.service` unit file and `systemctl` manages the lifecycle.
- **init.d / SysV init** (older Linux) — Spring Boot can create a "fully executable" JAR with a shell script prefix that `init.d` directly invokes as a service.
- **Windows Service** — the executable JAR is wrapped via `winsw` (Windows Service Wrapper) or deployed as a Procrun-managed service.

The `spring-boot-maven-plugin` / Gradle equivalent creates the fully-executable JAR when `executable = true` is set.

## 2. Why & when

Use OS service installation when:

- You're deploying to a **dedicated server or VM** (not a container platform).
- You want the app to **auto-start after a reboot** without a container orchestrator.
- You need **system-level restart policies** (backoff, max restarts) without running Kubernetes.
- You want logs integrated with the system journal (`journalctl`).

For containerised deployments (Kubernetes, ECS, Cloud Run) you don't use systemd — the container orchestrator handles lifecycle. OS service installation is for bare-metal or VM deployments.

## 3. Core concept

A fully-executable Spring Boot JAR is a ZIP file with a **shell script prepended** to it. On Linux the file is marked executable (`chmod +x`), and the OS runs the prepended script rather than passing the file to `java -jar`. The script then calls `java -jar <this-file>` with proper flags.

The `systemd` unit file is the modern and preferred approach because:
- Fine-grained dependency ordering (`After=network.target`).
- Resource limits (`MemoryMax`, `CPUQuota`).
- Journal integration (no separate log rotation config).
- Sandboxing (`PrivateTmp=yes`, `NoNewPrivileges=yes`).

Key files:
- `/etc/systemd/system/myapp.service` — unit file
- `/etc/myapp/application.properties` — externalized config (not inside JAR)
- `/opt/myapp/myapp.jar` — the executable JAR

## 4. Diagram

<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot service managed by systemd on Linux showing unit file and lifecycle">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- systemd box -->
  <rect x="10" y="80" width="140" height="100" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="80" y="105" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">systemd</text>
  <text x="80" y="123" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">PID 1</text>
  <text x="80" y="141" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">reads .service</text>
  <text x="80" y="157" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">manages lifecycle</text>

  <!-- unit file -->
  <rect x="200" y="40" width="180" height="120" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="290" y="63" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">myapp.service</text>
  <text x="210" y="83" fill="#6db33f" font-size="9" font-family="monospace">[Unit]</text>
  <text x="210" y="98" fill="#8b949e" font-size="9" font-family="monospace">After=network.target</text>
  <text x="210" y="113" fill="#6db33f" font-size="9" font-family="monospace">[Service]</text>
  <text x="210" y="128" fill="#8b949e" font-size="9" font-family="monospace">ExecStart=/opt/.../app.jar</text>
  <text x="210" y="143" fill="#8b949e" font-size="9" font-family="monospace">Restart=on-failure</text>
  <text x="210" y="155" fill="#8b949e" font-size="9" font-family="monospace">MemoryMax=512M</text>

  <!-- Spring Boot process -->
  <rect x="430" y="80" width="160" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="105" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Spring Boot</text>
  <text x="510" y="123" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Java process</text>
  <text x="510" y="141" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">stdout → journal</text>
  <text x="510" y="157" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">SIGTERM → graceful</text>

  <!-- arrows -->
  <line x1="150" y1="130" x2="198" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="380" y1="100" x2="428" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <text x="350" y="230" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">systemctl start/stop/restart myapp — survives reboots, logs in journalctl</text>
</svg>

systemd reads the unit file, launches the JAR process, and manages restarts, logging, and resource limits.

## 5. Runnable example

```java
// OsServiceDemo.java — run with: java OsServiceDemo.java
// Prints the complete configuration needed to install a Spring Boot app
// as a systemd service on Linux, and as an init.d service (legacy),
// plus the Windows Service Wrapper (winsw) config.

public class OsServiceDemo {

    public static void main(String[] args) {
        System.out.println("=== Installing Spring Boot as an OS Service ===\n");
        printMavenConfig();
        printSystemdUnit();
        printInitD();
        printWindowsService();
        printUsefulCommands();
    }

    static void printMavenConfig() {
        System.out.println("--- pom.xml: make JAR fully executable (init.d only) ---");
        System.out.println("""
            <plugin>
              <groupId>org.springframework.boot</groupId>
              <artifactId>spring-boot-maven-plugin</artifactId>
              <configuration>
                <executable>true</executable>   <!-- prepend shell script -->
              </configuration>
            </plugin>
            <!-- NOTE: not required for systemd — systemd uses ExecStart=java -jar -->
            """);
    }

    static void printSystemdUnit() {
        System.out.println("--- /etc/systemd/system/myapp.service (PREFERRED) ---");
        System.out.println("""
            [Unit]
            Description=My Spring Boot Application
            After=network.target

            [Service]
            User=myapp
            ExecStart=/usr/bin/java -jar /opt/myapp/myapp.jar \\
              --spring.config.location=/etc/myapp/
            SuccessExitStatus=143
            TimeoutStopSec=30
            Restart=on-failure
            RestartSec=5
            StandardOutput=journal
            StandardError=journal
            MemoryMax=512M
            NoNewPrivileges=yes
            PrivateTmp=yes

            [Install]
            WantedBy=multi-user.target
            """);
    }

    static void printInitD() {
        System.out.println("--- init.d installation (legacy systems) ---");
        System.out.println("""
            # After building with <executable>true</executable>:
            sudo cp target/myapp.jar /etc/init.d/myapp
            sudo chmod +x /etc/init.d/myapp

            # Config file (optional, same name as service in /etc/myapp/):
            # /etc/myapp/myapp.conf
            JAVA_OPTS="-Xmx512m"
            RUN_ARGS="--spring.config.location=/etc/myapp/"

            # Enable auto-start:
            sudo update-rc.d myapp defaults   # Debian/Ubuntu
            sudo chkconfig myapp on           # RHEL/CentOS
            """);
    }

    static void printWindowsService() {
        System.out.println("--- Windows: winsw (Windows Service Wrapper) ---");
        System.out.println("""
            <!-- myapp.xml alongside myapp.jar: -->
            <service>
              <id>myapp</id>
              <name>My Spring Boot App</name>
              <description>Spring Boot Application</description>
              <executable>java</executable>
              <arguments>-jar "%BASE%\\myapp.jar" --spring.config.location=%BASE%\\</arguments>
              <logmode>rotate</logmode>
              <stoptimeout>30 sec</stoptimeout>
            </service>

            <!-- Install: -->
            <!-- winsw.exe install -->
            <!-- sc start myapp   -->
            """);
    }

    static void printUsefulCommands() {
        System.out.println("--- systemd day-2 commands ---");
        String[][] cmds = {
            {"sudo systemctl enable myapp",    "Auto-start on boot"},
            {"sudo systemctl start myapp",     "Start now"},
            {"sudo systemctl stop myapp",      "Graceful stop (sends SIGTERM, waits TimeoutStopSec)"},
            {"sudo systemctl restart myapp",   "Restart"},
            {"sudo systemctl status myapp",    "Show PID, uptime, last log lines"},
            {"journalctl -u myapp -f",         "Follow logs"},
            {"journalctl -u myapp --since '1h ago'", "Last hour of logs"},
        };
        for (var c : cmds) {
            System.out.printf("  %-45s  %s%n", c[0], c[1]);
        }
    }
}
```

**How to run:** `java OsServiceDemo.java`

## 6. Walkthrough

- **`<executable>true</executable>`** — tells `spring-boot-maven-plugin` to prepend a shell script to the JAR. The resulting file is both a valid ZIP (Java can read it as a JAR) and an executable shell script (the OS can run it directly). Only needed for init.d; systemd's `ExecStart` specifies `java -jar` explicitly, which is cleaner.
- **`SuccessExitStatus=143`** — `143 = 128 + SIGTERM(15)`. When systemd stops the service it sends SIGTERM; the JVM exits with code 143. Without this, systemd treats the exit as a failure and may restart unnecessarily.
- **`TimeoutStopSec=30`** — matches `spring.lifecycle.timeout-per-shutdown-phase=30s`. Together they ensure systemd waits long enough for graceful shutdown before force-killing.
- **`User=myapp`** — run as a dedicated non-root user. Create with `useradd -r -s /bin/false myapp`. The service directory `/opt/myapp/` should be owned by this user.
- **`--spring.config.location=/etc/myapp/`** — externalises configuration so you can change properties without rebuilding the JAR. The directory is scanned for `application.properties` and `application-<profile>.properties`.
- **`journalctl -u myapp -f`** — follows the journal in real time. Spring Boot logs to stdout by default; systemd routes stdout to the journal automatically when `StandardOutput=journal`.

## 7. Gotchas & takeaways

> **Never run Spring Boot as root.** Create a dedicated service account. If the app is compromised, a non-root process with `NoNewPrivileges=yes` has far less blast radius than a root process.

> **The `<executable>true</executable>` JAR includes a 50–100 KB shell script prefix** which confuses some antivirus software and `jar tf` output. For new installations, prefer systemd with an explicit `ExecStart=java -jar` — you get the same management without embedding a shell script in your binary.

- After changing the unit file run `sudo systemctl daemon-reload` before `systemctl restart`.
- Set `JAVA_OPTS` or pass JVM flags in `ExecStart` — e.g., `-Xmx512m -Dspring.profiles.active=prod`.
- Use `LimitNOFILE=65536` in the `[Service]` section if the app opens many file descriptors (e.g., a busy HTTP server).
- For high-availability, consider two instances behind a load balancer rather than relying on `Restart=on-failure` alone.
- Logrotate is not needed when `StandardOutput=journal`; the journal has built-in rotation via `journald.conf`.
