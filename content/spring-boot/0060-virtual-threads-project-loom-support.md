---
card: spring-boot
gi: 60
slug: virtual-threads-project-loom-support
title: Virtual threads (Project Loom) support
---

## 1. What it is

**Virtual threads** are ultra-lightweight threads introduced as a stable feature in Java 21 (Project Loom). Spring Boot 3.2 added first-class support: one property switches the entire servlet container and `@Async` executor to use virtual threads instead of platform (OS) threads.

A **platform thread** is a thin Java wrapper around an actual OS thread — expensive to create, memory-hungry (~1 MB stack), and limited in number (typically thousands per machine). A **virtual thread** is managed entirely by the JVM, costs a few hundred bytes, and you can run **millions** concurrently on the same hardware.

In a Spring Boot web application, each HTTP request normally occupies a platform thread for its full duration. With virtual threads enabled, each request still gets its own thread (same programming model), but that thread is cheap enough that blocking on a database query or an HTTP call wastes nothing.

## 2. Why & when

Traditional blocking I/O on platform threads causes **thread starvation**: while a thread waits for a database row, it does nothing yet holds an OS thread — a scarce, expensive resource. The two classic escape routes are:

- **Reactive / async code** (Reactor, CompletableFuture) — solves the problem but forces a completely different, harder-to-read programming model.
- **Scale horizontally** — throw more servers at the problem.

Virtual threads offer a third path: **keep the simple, sequential, blocking code you already know** and gain reactive-level throughput automatically.

Enable virtual threads when:
- Your app is I/O-bound (database, HTTP, file).
- You want higher request throughput without rewriting to reactive.
- You are on Java 21+ and Spring Boot 3.2+.

Skip or be cautious when:
- Your code uses `synchronized` blocks heavily (they pin carrier threads; use `ReentrantLock` instead).
- You are already using Reactive (WebFlux) — virtual threads add no benefit there.

## 3. Core concept

Virtual threads **mount onto carrier threads** (a small pool of real OS threads) when they have work to do, and **unmount** the instant they block on I/O. The JVM scheduler sees the block, parks the virtual thread, and immediately gives the carrier thread to another virtual thread that is ready to run.

```
Virtual thread A (waiting for DB) ──unmounts──▶ carrier freed
Virtual thread B (computing)      ──mounts────▶ runs on same carrier
Virtual thread A (DB result back)  ──mounts────▶ resumes
```

From the application code's perspective nothing changes: you still call `Thread.sleep()`, JDBC, or `RestTemplate` and it just works. The JVM handles the juggling invisibly.

Spring Boot's auto-configuration:
1. Detects `spring.threads.virtual.enabled=true` in `application.properties`.
2. Creates a `VirtualThreadTaskExecutor` (backed by `Thread.ofVirtual().factory()`).
3. Replaces the default Tomcat/Jetty thread pool and the `@Async` executor with that factory.

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Virtual threads mount and unmount from carrier threads during blocking I/O">
  <defs>
    <marker id="arr" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/>
    </marker>
    <marker id="arrB" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Carrier thread row -->
  <rect x="20" y="40" width="640" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="34" y="67" fill="#6db33f" font-size="12" font-family="sans-serif" font-weight="bold">Carrier thread (OS thread × 2)</text>
  <rect x="190" y="48" width="110" height="28" rx="5" fill="#6db33f" fill-opacity="0.25" stroke="#6db33f" stroke-width="1"/>
  <text x="245" y="67" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Carrier-1</text>
  <rect x="315" y="48" width="110" height="28" rx="5" fill="#6db33f" fill-opacity="0.25" stroke="#6db33f" stroke-width="1"/>
  <text x="370" y="67" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Carrier-2</text>

  <!-- Virtual thread A -->
  <rect x="20" y="120" width="200" height="36" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="143" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">VT-A: handles request</text>

  <!-- Arrow: VT-A mounts Carrier-1 -->
  <line x1="160" y1="120" x2="245" y2="76" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arrB)"/>
  <text x="175" y="102" fill="#8b949e" font-size="10" font-family="sans-serif">mounts</text>

  <!-- VT-A blocks on DB -->
  <rect x="240" y="120" width="200" height="36" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="340" y="138" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">VT-A: waiting for DB</text>
  <text x="340" y="152" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(parked — carrier freed)</text>

  <!-- VT-B runs on freed carrier -->
  <rect x="460" y="120" width="200" height="36" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="560" y="143" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">VT-B: runs on Carrier-1</text>
  <line x1="500" y1="120" x2="245" y2="76" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="370" y="102" fill="#8b949e" font-size="10" font-family="sans-serif">mounts freed carrier</text>

  <!-- Timeline label -->
  <line x1="20" y1="210" x2="660" y2="210" stroke="#8b949e" stroke-width="1" marker-end="url(#arr)"/>
  <text x="340" y="228" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">time →</text>
  <text x="340" y="245" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Carrier thread never idles — another virtual thread gets it the instant VT-A parks</text>
</svg>

While VT-A blocks on a database query it unmounts from the carrier; VT-B immediately uses that same carrier thread — no OS thread ever sits idle.

## 5. Runnable example

The snippet below is a self-contained Spring Boot 3.2 application. It exposes a `/hello` endpoint, enables virtual threads, then shows at startup which thread type is being used.

```java
// VirtualThreadsDemo.java — run with: java -cp "spring-boot-starter-web.jar:." VirtualThreadsDemo.java
// Or paste into a Spring Initializr project (Spring Boot 3.2+, Java 21+)
// and set spring.threads.virtual.enabled=true in application.properties.

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class VirtualThreadsDemo {

    public static void main(String[] args) {
        // Enable virtual threads programmatically (alternative to application.properties)
        System.setProperty("spring.threads.virtual.enabled", "true");
        SpringApplication.run(VirtualThreadsDemo.class, args);
    }

    @GetMapping("/hello")
    public String hello() throws InterruptedException {
        Thread current = Thread.currentThread();
        // Virtual threads report isVirtual() == true
        String threadType = current.isVirtual() ? "virtual" : "platform";
        // Simulate a blocking I/O call — costs nothing on a virtual thread
        Thread.sleep(50);
        return "Hello from a " + threadType + " thread: " + current;
    }
}
```

**application.properties** (place next to the source or in `src/main/resources/`):
```properties
spring.threads.virtual.enabled=true
```

**How to run:** Create a Spring Boot 3.2+ project via [start.spring.io](https://start.spring.io) with Java 21 and the **Spring Web** dependency. Drop this class in and run `./mvnw spring-boot:run`. Then `curl http://localhost:8080/hello`.

Expected output fragment:
```
Hello from a virtual thread: VirtualThread[#xx]/runnable@ForkJoinPool-1-worker-1
```

## 6. Walkthrough

- `System.setProperty("spring.threads.virtual.enabled", "true")` — sets the property before the context starts, equivalent to putting it in `application.properties`. Spring Boot's `TomcatVirtualThreadsWebServerFactoryCustomizer` picks this up and replaces Tomcat's executor.
- `@SpringBootApplication` — triggers auto-configuration; no extra `@Bean` needed for virtual threads when the property is set.
- `Thread.currentThread().isVirtual()` — available since Java 21; returns `true` for virtual threads. This line proves the auto-config actually switched the executor.
- `Thread.sleep(50)` — on a platform thread this would block the OS thread for 50 ms. On a virtual thread the JVM parks it immediately, freeing the carrier for other work. No change in code; massive difference in resource use under load.
- The thread name (`VirtualThread[#xx]/runnable@ForkJoinPool-1-worker-1`) shows: thread id #xx is a virtual thread currently carried by a ForkJoinPool worker — the default carrier pool.
- Under concurrent load (e.g. 10 000 simultaneous requests), all 10 000 get their own virtual thread. With platform threads, Tomcat's default pool of 200 would force the remaining 9 800 to queue.

## 7. Gotchas & takeaways

> **`synchronized` blocks pin the carrier thread.** If your code (or a library) uses `synchronized` for anything that can block (e.g. JDBC drivers before Java 23, old Hibernate versions), the virtual thread cannot unmount and the carrier is stuck for the full duration — negating the benefit. Replace `synchronized` with `java.util.concurrent.locks.ReentrantLock` or upgrade to JDBC drivers that use `ReentrantLock` internally.

> **ThreadLocal works but can leak.** Virtual threads still support `ThreadLocal`, but because millions of them can exist, storing large objects in `ThreadLocal` causes massive memory pressure. Prefer `ScopedValue` (Java 21 preview, stable in 23) for propagating context in virtual-thread-heavy code.

- Requires **Java 21+** and **Spring Boot 3.2+**; the single property `spring.threads.virtual.enabled=true` is enough.
- Virtual threads shine for **I/O-bound** workloads; CPU-bound work sees no benefit (the CPU is busy either way).
- No code changes needed: your blocking `RestTemplate`, JDBC, and `Thread.sleep()` calls all benefit automatically.
- Do **not** mix with WebFlux (Reactor) — they solve the same problem differently; enabling virtual threads on a reactive stack wastes configuration effort.
- Monitor with `jcmd <pid> Thread.dump_to_file -format=json threads.json` to inspect virtual thread state in production; standard thread dumps now include virtual threads.
- Pool sizes (e.g. database connection pool) still matter — virtual threads can create thousands of DB connections if unbounded; configure HikariCP's `maximum-pool-size` appropriately.
