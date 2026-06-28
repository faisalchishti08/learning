---
card: spring-boot
gi: 128
slug: graceful-shutdown
title: Graceful shutdown
---

## 1. What it is

**Graceful shutdown** lets an embedded server finish processing in-flight requests before it actually stops, instead of dropping connections immediately. Spring Boot 2.3+ supports it for all four embedded containers (Tomcat, Jetty, Undertow, Reactor Netty) via a single property: `server.shutdown=graceful`.

## 2. Why & when

When a rolling deployment restarts a pod or instance, any in-flight requests are abruptly terminated without graceful shutdown — the client sees a connection reset or incomplete response. This is especially painful for long-running requests (file uploads, report generation, batch-like API calls).

Enable graceful shutdown whenever:

- You run in Kubernetes, ECS, or any orchestrator that issues `SIGTERM` before killing the process.
- Your API handles requests that take more than a few hundred milliseconds.
- You care about zero-error rolling deployments.

Pair it with `spring.lifecycle.timeout-per-shutdown-phase` to cap the wait time.

## 3. Core concept

On shutdown (SIGTERM, `actuator/shutdown`, or `SpringApplication.exit()`):

1. Spring Boot stops accepting **new** requests immediately (the port closes).
2. It waits for **in-flight** requests to complete.
3. After all complete (or the timeout elapses), it proceeds with bean destruction.

The wait timeout is configured with:

```properties
server.shutdown=graceful
spring.lifecycle.timeout-per-shutdown-phase=30s
```

The timeout is per *phase* in the `SmartLifecycle` shutdown sequence. Requests still running after the timeout are abandoned and the shutdown continues.

Analogy: a restaurant that says "we're closing — no new orders — but we'll finish cooking what's already on the grill."

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="110" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">SIGTERM received</text>
  <rect x="225" y="60" width="160" height="45" rx="6" fill="#1c2430" stroke="#e05252" stroke-width="1.5"/>
  <text x="305" y="87" text-anchor="middle" fill="#e05252" font-size="12" font-family="sans-serif">Reject NEW requests</text>
  <rect x="225" y="125" width="160" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="305" y="145" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Wait for in-flight</text>
  <text x="305" y="162" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">(up to timeout)</text>
  <rect x="470" y="90" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="560" y="115" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Bean destroy / JVM exit</text>
  <line x1="152" y1="105" x2="221" y2="85" stroke="#6db33f" stroke-width="1.5" marker-end="url(#gs)"/>
  <line x1="152" y1="105" x2="221" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#gs)"/>
  <line x1="387" y1="148" x2="466" y2="113" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#gs2)"/>
  <line x1="387" y1="82" x2="466" y2="107" stroke="#e05252" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#gs3)"/>
  <defs>
    <marker id="gs" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="gs2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="gs3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#e05252"/></marker>
  </defs>
</svg>

On SIGTERM: new requests rejected immediately, in-flight requests drain up to the timeout, then JVM exits cleanly.

## 5. Runnable example

```java
// GracefulShutdownApp.java  —  Spring Boot 2.3+ project with spring-boot-starter-web
// application.properties:
//   server.shutdown=graceful
//   spring.lifecycle.timeout-per-shutdown-phase=20s

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class GracefulShutdownApp {
    public static void main(String[] args) {
        SpringApplication.run(GracefulShutdownApp.class, args);
    }
}

@RestController
class SlowController {

    // Simulates a slow request (e.g. report generation)
    @GetMapping("/slow")
    public String slow(@RequestParam(defaultValue = "5") int seconds)
            throws InterruptedException {
        System.out.println("Request started, will take " + seconds + "s");
        Thread.sleep(seconds * 1000L);
        System.out.println("Request completed");
        return "Done after " + seconds + "s";
    }
}
```

**How to run:**

1. Add `server.shutdown=graceful` and `spring.lifecycle.timeout-per-shutdown-phase=20s` to `application.properties`.
2. Start the app.
3. In terminal A: `curl http://localhost:8080/slow?seconds=8`
4. Immediately in terminal B: send `SIGTERM` — `kill -TERM <pid>` or `Ctrl+C` if running in foreground.
5. Observe: terminal A gets a response after 8 seconds; the process then exits cleanly.

## 6. Walkthrough

- `server.shutdown=graceful` switches the embedded server's shutdown mode. Default is `immediate` — the server closes the port and kills all connections at once.
- With `graceful`, when SIGTERM arrives Spring Boot calls `WebServer.shutDownGracefully()`. The server stops accepting new connections (the OS-level listener closes) but keeps processing active threads.
- `spring.lifecycle.timeout-per-shutdown-phase=20s` caps how long Spring waits in each lifecycle phase. If a request takes longer than 20 seconds it is abandoned and shutdown continues anyway — preventing an app from hanging forever.
- `Thread.sleep(seconds * 1000L)` in `SlowController` simulates work. In production this would be a database query or file operation.
- Log output confirms the order: "Request completed" appears *before* the Spring shutdown log lines, proving the graceful wait worked.
- For Kubernetes: pair with a `preStop` hook (`sleep 5`) to give the load balancer time to remove the pod from rotation before SIGTERM arrives; otherwise, new requests arrive during the drain window.

## 7. Gotchas & takeaways

> Graceful shutdown waits for **request threads** to finish, not for async tasks (`@Async`, CompletableFutures, scheduled jobs). If those need draining too, implement `DisposableBean` or `SmartLifecycle` on those components.

> The timeout is per *shutdown phase*, not total. If you have multiple `SmartLifecycle` components, each phase gets its own `timeout-per-shutdown-phase` budget.

- Default timeout is 30 seconds when `spring.lifecycle.timeout-per-shutdown-phase` is not set.
- Kubernetes `terminationGracePeriodSeconds` must be longer than your Spring timeout, or the kubelet force-kills the pod before Spring finishes draining.
- `server.shutdown=graceful` works with all four embedded containers — no extra configuration per container.
- Clients hitting the closed port during drain see connection refused immediately; only the already-connected in-flight requests are given time to complete.
- Test graceful shutdown with `SpringApplication.exit(context)` in integration tests using `@SpringBootTest(webEnvironment = RANDOM_PORT)`.
