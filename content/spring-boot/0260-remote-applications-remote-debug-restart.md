---
card: spring-boot
gi: 260
slug: remote-applications-remote-debug-restart
title: Remote applications (remote debug/restart)
---

## 1. What it is

Spring Boot DevTools includes a **remote development mode** that extends automatic restart and resource updates to an application running on a remote server — including inside a Docker container, a cloud VM, or a remote development machine.

Remote DevTools has two components:

1. **Server side** — the `RemoteSpringApplication` servlet endpoint is deployed with the remote app. It accepts encrypted class/resource updates and restart commands from the client.
2. **Client side** — you run `RemoteSpringApplication` locally, pointing at the remote server URL. It watches your local classpath, uploads changed files to the remote server, and triggers remote restarts.

The remote endpoint requires a shared **secret** (`spring.devtools.remote.secret`) for authentication. All communication goes over HTTPS.

## 2. Why & when

Remote DevTools is useful when:

- You **cannot run the app locally** — e.g., it requires GPU, specialised hardware, or data that's too large to copy locally.
- You're **developing inside a Docker container** on your laptop and want restart to be faster than rebuilding the image.
- You're **pair programming** with a remote server as the shared runtime.

It is *not* for production debugging — the secret must be known, the endpoint is an attack surface, and it should be disabled in production (gi 262).

A more modern alternative for Docker-based development is Spring Boot's **Docker Compose integration** (separate feature) or Testcontainers DevMode. Remote DevTools predates those tools but remains useful for SSH-accessible VMs.

## 3. Core concept

The remote DevTools protocol:

1. **Client watches local classpath** — same file watcher as local DevTools.
2. **Changed files are HTTP-POSTed** — the client sends a `multipart` HTTP request with the changed `.class` files to `/.~~spring-boot!~/restart` on the remote server. The request is HMAC-signed with the shared secret.
3. **Remote server writes files** — the server-side handler writes the uploaded classes to the classpath of the running remote app.
4. **Remote restart triggered** — the remote app's DevTools detects the new files and restarts the application classloader, exactly as in local mode.
5. **LiveReload signal forwarded** — the client also proxies the LiveReload signal back to the local browser.

The HMAC signature prevents unauthorised class uploads (which would be a code-execution vulnerability).

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Remote DevTools: local client uploads changed classes to remote server, triggers restart">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Local machine -->
  <rect x="5" y="30" width="250" height="180" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="130" y="55" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Developer Machine</text>

  <rect x="20" y="70" width="220" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="88" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">File Watcher</text>
  <text x="130" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">target/classes (local)</text>

  <rect x="20" y="130" width="220" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="148" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">RemoteSpringApplication</text>
  <text x="130" y="163" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">local client process</text>

  <!-- Remote server -->
  <rect x="450" y="30" width="240" height="180" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="570" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Remote Server / Docker</text>

  <rect x="465" y="70" width="210" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="570" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Boot App</text>
  <text x="570" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ RemoteSpringApplication server</text>

  <rect x="465" y="130" width="210" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="570" y="148" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Remote classloader restart</text>
  <text x="570" y="163" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">on class upload</text>

  <!-- Arrows -->
  <line x1="258" y1="150" x2="448" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#arr)"/>
  <text x="353" y="108" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">HTTPS POST .class files</text>
  <text x="353" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">HMAC-signed (shared secret)</text>

  <line x1="448" y1="160" x2="258" y2="180" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#arr2)"/>
  <text x="353" y="175" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">LiveReload signal forwarded</text>
</svg>

Local `RemoteSpringApplication` uploads changed classes over HTTPS; the remote server restarts its classloader.

## 5. Runnable example

```java
// RemoteDevToolsDemo.java — run with: java RemoteDevToolsDemo.java
// Prints the configuration and commands needed to use remote DevTools
// for Docker and VM deployment scenarios.

public class RemoteDevToolsDemo {

    public static void main(String[] args) {
        System.out.println("=== Remote DevTools Setup ===\n");
        printServerConfig();
        printDockerSetup();
        printClientLaunch();
        printSecurityWarning();
    }

    static void printServerConfig() {
        System.out.println("--- Remote server: application.properties ---");
        System.out.println("""
            # Required: shared secret for HMAC authentication
            spring.devtools.remote.secret=my-super-secret-key

            # Optional: restrict restart endpoint path
            # spring.devtools.remote.context-path=/.~~spring-boot!~
            """);
    }

    static void printDockerSetup() {
        System.out.println("--- Dockerfile for remote DevTools (dev only) ---");
        System.out.println("""
            FROM eclipse-temurin:21-jre
            ARG JAR_FILE=target/*.jar
            COPY ${JAR_FILE} app.jar

            # Expose both app port and debug port
            EXPOSE 8080 5005

            # Enable remote debugging + run app
            ENTRYPOINT ["java",
              "-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005",
              "-jar", "/app.jar"]
            """);

        System.out.println("--- docker-compose.yml (dev profile) ---");
        System.out.println("""
            services:
              app:
                build: .
                ports:
                  - "8080:8080"
                  - "5005:5005"    # JVM remote debug port
                environment:
                  SPRING_DEVTOOLS_REMOTE_SECRET: my-super-secret-key
            """);
    }

    static void printClientLaunch() {
        System.out.println("--- Local client: run RemoteSpringApplication ---");
        System.out.println("""
            # Via Maven (add to your pom as a run configuration):
            mvn spring-boot:run \\
              -Dspring-boot.run.main-class=org.springframework.boot.devtools.RemoteSpringApplication \\
              -Dspring-boot.run.arguments=https://myserver.example.com

            # Via IDE (add a Run Configuration):
            Main class : org.springframework.boot.devtools.RemoteSpringApplication
            Program arg: https://myserver.example.com    (or http://localhost:8080 for Docker)

            # The client reads spring.devtools.remote.secret from local application.properties
            # and uses it to sign all requests.
            """);
    }

    static void printSecurityWarning() {
        System.out.println("--- IMPORTANT: Security considerations ---");
        System.out.println("""
            1. NEVER enable remote DevTools in production (use DevTools only in dev builds).
            2. Use HTTPS — the secret is sent in every request header.
            3. Use a strong random secret (min 32 chars):
               openssl rand -hex 32
            4. Disable in production: remote DevTools is disabled automatically when
               spring-boot-devtools is not in the fat JAR (use <optional>true</optional>).
            5. Firewall: restrict port 8080 to trusted IPs if using remote DevTools.
            """);
    }
}
```

**How to run:** `java RemoteDevToolsDemo.java`

## 6. Walkthrough

- **`spring.devtools.remote.secret`** — required for the remote endpoint to activate. Without it, the `/.~~spring-boot!~/restart` handler is not registered; the endpoint simply doesn't exist. Set it as an environment variable (`SPRING_DEVTOOLS_REMOTE_SECRET`) rather than a property file to avoid committing it to source control.
- **Docker Compose port mapping** — `5005:5005` exposes the JVM debug port separately from the app port. This lets you attach IntelliJ or VS Code's remote debugger while also using DevTools restart. JDWP (`-agentlib:jdwp=...`) enables Java Debug Wire Protocol; `suspend=n` means the app starts immediately without waiting for a debugger.
- **`RemoteSpringApplication` client** — this is a regular main class in the DevTools JAR. Running it locally with the remote URL as an argument starts the watch loop. The client authenticates each upload request with `X-AUTH-TOKEN: HMAC-SHA256(secret, payload)`.
- **HTTPS requirement** — the secret and uploaded `.class` files travel over the wire. Without HTTPS, an attacker on the network could intercept the secret and upload arbitrary bytecode. The remote endpoint is effectively an unauthenticated remote code execution vulnerability if you use HTTP.

## 7. Gotchas & takeaways

> **Remote DevTools sends compiled .class files, not source** — so it only works if your local build produces the same artifact the remote classpath expects. If you've diverged (different JDK version, different dependency versions), uploaded classes may cause `NoClassDefFoundError` or `ClassFormatError` on the remote server.

> **Use remote DevTools only for development VMs, not staging/production.** A shared secret strong enough for development is not the same as a properly managed credential. Rotate it frequently, or better, tear down the dev VM when not in use.

- Remote DevTools works over HTTP/HTTPS only — no SSH tunnelling required (though tunnelling is a valid option for additional security).
- Combine with JDWP remote debug to get both fast restart and breakpoint debugging in the same setup.
- `RemoteSpringApplication` logs each upload: `Remote restart triggered for [...]` — watch this to confirm changes are being picked up.
- For Docker, DevTools remote restart is faster than `docker restart` because it uses the two-classloader model — only the application layer restarts, not the full container.
