---
card: spring-boot
gi: 5
slug: embedded-servers-concept
title: Embedded servers concept
---

## 1. What it is

An **embedded server** is a web server (Tomcat, Jetty, or Undertow) that is packaged *inside* your application JAR rather than installed separately on the host machine. When you run `java -jar app.jar`, the server starts as part of your application process — no external server installation, no WAR deployment, no `server.xml` editing.

Spring Boot supports three embedded servlet containers:

| Server | Default starter | Notes |
|---|---|---|
| Apache Tomcat | `spring-boot-starter-web` (included) | Default choice; battle-tested, widely used |
| Eclipse Jetty | `spring-boot-starter-jetty` | Lightweight; good for long-lived connections |
| Undertow | `spring-boot-starter-undertow` | High-throughput non-blocking; no JSP support |

There is also `spring-boot-starter-webflux` which uses **Netty** as its default reactive server.

## 2. Why & when

**Traditional deployment** (pre-Spring Boot): you install Tomcat 9 on a Linux VM, configure it in `/opt/tomcat/conf/`, deploy your application as a `myapp.war` file by dropping it in `webapps/`. When the Tomcat version needs updating, you update the server on every machine your app runs on.

**Problems this creates:**
- Server version mismatch between dev laptop, CI, staging, and production.
- Shared server hosts multiple apps — one app's config change can affect others.
- Deployment ceremony: package WAR → upload → restart Tomcat → wait.

**Embedded servers solve this** by making the server a dependency, just like any other library. The server version is pinned in `pom.xml`. Every environment runs the exact same version. Deployment is `scp app.jar server: && java -jar app.jar`. Container orchestrators (Docker, Kubernetes) work naturally because the JAR is a self-contained process.

Embedded servers are the right choice for **new Spring Boot applications**. The external WAR approach is still available if you're deploying to an enterprise server you don't control.

## 3. Core concept

The embedded server lifecycle is managed by Spring Boot's `WebServer` abstraction:

1. `SpringApplication.run()` detects that `spring-boot-starter-web` (Tomcat) is on the classpath.
2. It creates a `TomcatServletWebServerFactory` (or Jetty/Undertow equivalent).
3. The factory creates and starts the embedded server, registers the `DispatcherServlet`, and returns a `WebServer` handle.
4. The `ApplicationContext` holds the `WebServer`. When the context closes (SIGTERM, test teardown), it calls `webServer.stop()`.

Configuration without touching `server.xml`:

```properties
server.port=8080               # port (0 = random, useful in tests)
server.servlet.context-path=/api
server.tomcat.max-threads=200
server.ssl.key-store=classpath:keystore.p12
```

The fat JAR created by `mvn package` (or `./gradlew bootJar`) contains:
- `/BOOT-INF/classes/` — your compiled classes
- `/BOOT-INF/lib/` — all dependency JARs including the embedded server JARs
- `/org/springframework/boot/loader/` — Spring Boot's custom class loader that knows how to launch from nested JARs

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparison of external WAR deployment versus embedded server fat JAR deployment">
  <!-- Left side: traditional WAR -->
  <rect x="20" y="20" width="290" height="220" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="165" y="46" fill="#8b949e" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Traditional WAR</text>

  <!-- External Tomcat box -->
  <rect x="36" y="56" width="258" height="80" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="76" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">External Tomcat (pre-installed)</text>
  <rect x="60" y="86" width="100" height="36" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="110" y="109" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">myapp.war</text>
  <rect x="172" y="86" width="100" height="36" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="222" y="109" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">otherapp.war</text>

  <text x="165" y="158" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Deploy: upload WAR → restart server</text>
  <text x="165" y="174" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Risk: shared server, version drift</text>
  <text x="165" y="190" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Env consistency: depends on admin</text>

  <!-- Right side: embedded -->
  <rect x="350" y="20" width="290" height="220" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="46" fill="#6db33f" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Embedded Server (Fat JAR)</text>

  <!-- Fat JAR box -->
  <rect x="366" y="56" width="258" height="80" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="495" y="76" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">app.jar (self-contained)</text>
  <rect x="380" y="86" width="108" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="434" y="104" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">your code</text>
  <text x="434" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">BOOT-INF/classes</text>
  <rect x="500" y="86" width="110" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="555" y="104" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Tomcat 10.1</text>
  <text x="555" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">BOOT-INF/lib</text>

  <text x="495" y="158" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Deploy: java -jar app.jar</text>
  <text x="495" y="174" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Isolated: one process, one server</text>
  <text x="495" y="190" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Env consistency: guaranteed by JAR</text>
</svg>

WAR deploys into a shared external server; fat JAR carries the server inside — deploy anywhere Java runs.

## 5. Runnable example

```java
// File: EmbeddedServerDemo.java
// Shows the embedded-server lifecycle pattern in pure Java.
// Run: java EmbeddedServerDemo.java

import java.net.ServerSocket;
import java.net.Socket;
import java.io.*;

public class EmbeddedServerDemo {

    // Minimal embedded HTTP server — the idea behind Spring Boot's embedded Tomcat
    static class TinyEmbeddedServer {
        private ServerSocket serverSocket;
        private volatile boolean running;

        void start(int port) throws IOException {
            serverSocket = new ServerSocket(port);
            running = true;
            System.out.println("[Server] Started on port " + port);

            // Accept one request then stop (demo purposes)
            try (Socket client = serverSocket.accept()) {
                var reader = new BufferedReader(new InputStreamReader(client.getInputStream()));
                var writer = new PrintWriter(client.getOutputStream(), true);

                // Read request line
                String requestLine = reader.readLine();
                System.out.println("[Server] Received: " + requestLine);

                // Send response
                String body = "Hello from the embedded server!";
                writer.println("HTTP/1.1 200 OK");
                writer.println("Content-Type: text/plain");
                writer.println("Content-Length: " + body.length());
                writer.println();
                writer.println(body);
            }
        }

        void stop() throws IOException {
            running = false;
            if (serverSocket != null) serverSocket.close();
            System.out.println("[Server] Stopped.");
        }
    }

    public static void main(String[] args) throws Exception {
        var server = new TinyEmbeddedServer();

        // Start server in a background thread (just like Spring Boot does)
        var thread = new Thread(() -> {
            try { server.start(18080); }
            catch (IOException e) { /* server closed */ }
        });
        thread.setDaemon(true);
        thread.start();

        Thread.sleep(200); // wait for server to bind

        // Act as the client
        try (var socket = new Socket("localhost", 18080);
             var out = new PrintWriter(socket.getOutputStream(), true);
             var in = new BufferedReader(new InputStreamReader(socket.getInputStream()))) {

            out.println("GET / HTTP/1.1");
            out.println("Host: localhost");
            out.println();

            String line;
            while ((line = in.readLine()) != null) {
                System.out.println("[Client] " + line);
            }
        }

        server.stop();
    }
}
```

**How to run:** `java EmbeddedServerDemo.java` (JDK 17+, no dependencies needed).

Expected output:
```
[Server] Started on port 18080
[Server] Received: GET / HTTP/1.1
[Client] HTTP/1.1 200 OK
[Client] Content-Type: text/plain
[Client] Content-Length: 31
[Client]
[Client] Hello from the embedded server!
[Server] Stopped.
```

## 6. Walkthrough

- **`TinyEmbeddedServer`** — a minimal HTTP server using Java's `ServerSocket`. This is the concept behind Tomcat Embed: the server starts as a Java object in the same JVM as your application code.
- **`new ServerSocket(port)`** — binds to a port. In Spring Boot, `TomcatServletWebServerFactory.getWebServer()` does the equivalent for Tomcat.
- **`serverSocket.accept()`** — blocks until a client connects. Real Tomcat uses a thread pool (NIO connector) to handle thousands of connections.
- **`Thread` + `setDaemon(true)`** — the server runs on a background (daemon) thread. The JVM exits when only daemon threads are left. Spring Boot's embedded server uses a non-daemon thread so the app keeps running until explicitly stopped.
- **`Thread.sleep(200)`** — waits for the server thread to bind the port before the client connects. Spring Boot's `SpringApplication.run()` returns only after the server is ready — no sleep needed.
- **Client block** — sends a raw HTTP request and reads the response. This is what a browser or `RestTemplate` does under the hood.

## 7. Gotchas & takeaways

> **`server.port=0` starts the server on a random available port.** This is extremely useful in tests: inject `@LocalServerPort` to find out which port was chosen, preventing port conflicts in parallel test runs.

> **The fat JAR is not a WAR.** You cannot drop a `*-SNAPSHOT.jar` produced by `./mvnw package` into an external Tomcat's `webapps/`. If you need to deploy to an external container, add `spring-boot-starter-tomcat` as `provided` scope and extend `SpringBootServletInitializer`. For new projects, prefer the embedded approach.

- `java -jar app.jar` starts everything — no pre-installed server needed.
- Server choice is a one-line change in `pom.xml`: exclude `spring-boot-starter-tomcat`, add `spring-boot-starter-jetty`.
- `server.port`, `server.ssl.*`, `server.tomcat.*` properties configure the embedded server without touching any XML.
- Docker images built from Spring Boot fat JARs are simple: `FROM eclipse-temurin:17-jre`, `COPY app.jar .`, `CMD ["java","-jar","app.jar"]`.
- Use `server.port=0` in tests to avoid port-conflict failures in CI environments running parallel builds.
