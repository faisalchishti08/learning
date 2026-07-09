---
card: java
gi: 660
slug: reimplemented-legacy-socket-api
title: Reimplemented legacy Socket API
---

## 1. What it is

**JEP 353**, delivered in **Java 13**, replaced the underlying implementation of the legacy `java.net.Socket` and `java.net.ServerSocket` APIs with a new implementation called `NioSocketImpl`, which is built on top of the same internal infrastructure as `java.nio`. The old implementation (`PlainSocketImpl`), dating back to Java 1.0, was written using thread-per-connection, native-heavy code that was difficult to maintain and, crucially, didn't work well with fibers/virtual threads work happening in parallel OpenJDK projects (this was groundwork for what became Project Loom). The `Socket`/`ServerSocket` public APIs themselves **did not change at all** — same classes, same method signatures, same behavior from an application's point of view. This is a "replace the engine, keep the car" change.

## 2. Why & when

`PlainSocketImpl` had accumulated decades of subtle behavior differences from its NIO-based counterpart, used stack sizes and thread-per-connection patterns poorly suited to high-connection-count servers, and its implementation in a mix of Java and old native (JNI) code made it hard to fix bugs or optimize without risking regressions. `NioSocketImpl` shares infrastructure with the already-well-tested, better-performing NIO channel implementation, giving `Socket`/`ServerSocket` improved scalability (particularly relevant for servers handling many concurrent connections with blocking I/O) and paving the way for future features like virtual threads to work correctly with classic blocking socket code. As an application developer using plain `Socket`/`ServerSocket`, you don't need to change anything — your existing code just runs on a better-implemented, more scalable foundation starting in Java 13. This matters most if you write servers handling many simultaneous blocking-I/O connections, or if you were relying on any undocumented quirk of the old implementation (rare, but the JEP explicitly warns of a small number of edge-case behavior differences).

## 3. Core concept

```java
// Your code doesn't change at all — same familiar Socket/ServerSocket API.
try (ServerSocket server = new ServerSocket(8080)) {
    while (true) {
        Socket client = server.accept();      // blocks until a connection arrives
        // handle client...
    }
}

// What changed is invisible to you: internally, Socket now delegates to
// NioSocketImpl instead of the old PlainSocketImpl, sharing infrastructure
// with java.nio.channels.SocketChannel under the hood.
```

If you ever needed to opt back into the legacy implementation (e.g. to work around an unexpected behavior difference during the transition), the system property `-Djdk.net.usePlainSocketImpl=true` was provided as an escape hatch — later removed once the new implementation matured.

## 4. Diagram

<svg viewBox="0 0 620 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Socket and ServerSocket keep the same public API but switch their internal implementation from PlainSocketImpl to NioSocketImpl">
  <rect x="10" y="20" width="220" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Public API (unchanged)</text>
  <text x="25" y="75" fill="#e6edf3" font-size="10" font-family="monospace">java.net.Socket</text>
  <text x="25" y="95" fill="#e6edf3" font-size="10" font-family="monospace">java.net.ServerSocket</text>
  <text x="25" y="125" fill="#8b949e" font-size="9" font-family="sans-serif">Same methods, same</text>
  <text x="25" y="138" fill="#8b949e" font-size="9" font-family="sans-serif">behavior for your code.</text>

  <line x1="230" y1="85" x2="280" y2="85" stroke="#8b949e" stroke-width="2" marker-end="url(#si1)"/>

  <rect x="290" y="20" width="150" height="55" rx="6" fill="#1c2430" stroke="#f85149" opacity="0.6"/>
  <text x="365" y="42" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">PlainSocketImpl</text>
  <text x="365" y="58" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">(pre-Java 13, retired)</text>

  <rect x="290" y="95" width="150" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="365" y="117" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">NioSocketImpl</text>
  <text x="365" y="133" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">(Java 13+, default)</text>

  <text x="460" y="60" fill="#8b949e" font-size="9" font-family="sans-serif">shares infrastructure with</text>
  <text x="460" y="118" fill="#79c0ff" font-size="9" font-family="sans-serif">java.nio.channels.SocketChannel</text>

  <defs><marker id="si1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The `Socket`/`ServerSocket` classes are a thin, stable public facade; Java 13 swapped what sits behind that facade without touching the facade itself.

## 5. Runnable example

Scenario: a simple client-server exchange using plain blocking sockets — first the basic accept/read/write pattern (unchanged code that now runs on the new implementation), then adding proper timeout and multi-client handling, then a small multi-threaded echo server demonstrating the kind of many-concurrent-connections scenario the reimplementation specifically targets.

### Level 1 — Basic

```java
// File: SimpleEchoServer.java
import java.io.*;
import java.net.*;

public class SimpleEchoServer {
    public static void main(String[] args) throws IOException {
        try (ServerSocket server = new ServerSocket(0)) { // port 0 = pick a free port
            int port = server.getLocalPort();
            System.out.println("Server listening on port " + port);

            Thread serverThread = new Thread(() -> {
                try (Socket client = server.accept();
                     BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
                     PrintWriter out = new PrintWriter(client.getOutputStream(), true)) {
                    String line = in.readLine();
                    System.out.println("Server received: " + line);
                    out.println("echo: " + line);
                } catch (IOException e) {
                    throw new RuntimeException(e);
                }
            });
            serverThread.start();

            try (Socket clientSocket = new Socket("localhost", port);
                 PrintWriter out = new PrintWriter(clientSocket.getOutputStream(), true);
                 BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()))) {
                out.println("hello from client");
                System.out.println("Client received: " + in.readLine());
            }

            serverThread.join();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

**How to run:** `java SimpleEchoServer.java` (no special flags — this is standard `Socket`/`ServerSocket` usage that automatically runs on `NioSocketImpl` in Java 13+).

Expected output:
```
Server listening on port 54231
Server received: hello from client
Client received: echo: hello from client
```
(the port number will vary each run since `0` requests any free ephemeral port)

### Level 2 — Intermediate

```java
// File: TimeoutEchoServer.java
import java.io.*;
import java.net.*;

public class TimeoutEchoServer {
    public static void main(String[] args) throws Exception {
        try (ServerSocket server = new ServerSocket(0)) {
            server.setSoTimeout(2000); // accept() gives up after 2 seconds if no client connects
            int port = server.getLocalPort();
            System.out.println("Server listening on port " + port + " with 2s accept timeout");

            Thread serverThread = new Thread(() -> {
                try {
                    Socket client = server.accept();
                    client.setSoTimeout(1000); // reads also time out after 1 second
                    try (BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
                         PrintWriter out = new PrintWriter(client.getOutputStream(), true)) {
                        String line = in.readLine();
                        out.println("echo: " + line);
                    }
                } catch (SocketTimeoutException e) {
                    System.out.println("Server: accept() or read timed out");
                } catch (IOException e) {
                    throw new RuntimeException(e);
                }
            });
            serverThread.start();

            try (Socket clientSocket = new Socket("localhost", port);
                 PrintWriter out = new PrintWriter(clientSocket.getOutputStream(), true);
                 BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()))) {
                out.println("ping");
                System.out.println("Client received: " + in.readLine());
            }

            serverThread.join();
        }
    }
}
```

**How to run:** `java TimeoutEchoServer.java`

Expected output:
```
Server listening on port 54871 with 2s accept timeout
Client received: echo: ping
```

`setSoTimeout` makes blocking calls (`accept()`, socket reads) throw `SocketTimeoutException` instead of blocking forever — behavior fully preserved by `NioSocketImpl`, exercising exactly the kind of timeout semantics application code depends on.

### Level 3 — Advanced

```java
// File: MultiClientEchoServer.java
import java.io.*;
import java.net.*;
import java.util.concurrent.*;

public class MultiClientEchoServer {
    public static void main(String[] args) throws Exception {
        try (ServerSocket server = new ServerSocket(0)) {
            int port = server.getLocalPort();
            System.out.println("Server listening on port " + port);
            ExecutorService pool = Executors.newFixedThreadPool(4);

            Thread acceptorThread = new Thread(() -> {
                try {
                    for (int i = 0; i < 5; i++) {
                        Socket client = server.accept();
                        pool.submit(() -> handle(client, "client"));
                    }
                } catch (IOException e) {
                    // server socket closed after all clients handled — expected
                }
            });
            acceptorThread.start();

            CountDownLatch done = new CountDownLatch(5);
            for (int i = 0; i < 5; i++) {
                final int id = i;
                pool.submit(() -> {
                    try (Socket s = new Socket("localhost", port);
                         PrintWriter out = new PrintWriter(s.getOutputStream(), true);
                         BufferedReader in = new BufferedReader(new InputStreamReader(s.getInputStream()))) {
                        out.println("message-" + id);
                        System.out.println("Client " + id + " got: " + in.readLine());
                    } catch (IOException e) {
                        throw new RuntimeException(e);
                    } finally {
                        done.countDown();
                    }
                });
            }

            done.await(5, TimeUnit.SECONDS);
            pool.shutdown();
        }
    }

    static void handle(Socket client, String label) {
        try (client; BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
             PrintWriter out = new PrintWriter(client.getOutputStream(), true)) {
            String line = in.readLine();
            out.println("echo: " + line);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
}
```

**How to run:** `java MultiClientEchoServer.java`

Expected output (client order may interleave differently each run):
```
Server listening on port 55102
Client 0 got: echo: message-0
Client 1 got: echo: message-1
Client 2 got: echo: message-2
Client 3 got: echo: message-3
Client 4 got: echo: message-4
```

Level 3 runs 5 concurrent blocking client connections against one server, each handled by a pooled thread doing blocking `accept()`/read/write calls — exactly the many-concurrent-blocking-connections pattern where `NioSocketImpl`'s improved internal scalability over the old `PlainSocketImpl` matters most, even though the code itself uses nothing but the familiar `Socket`/`ServerSocket` API.

## 6. Walkthrough

1. `main` starts a `ServerSocket` on an OS-chosen free port and launches an `acceptorThread` that loops calling `server.accept()` up to 5 times — each call **blocks** the acceptor thread until a client connects; this blocking behavior is provided by `NioSocketImpl` under the hood but looks and behaves identically to the pre-Java-13 implementation from the caller's perspective.
2. Concurrently, `main` submits 5 client tasks to the same thread pool. Each task opens `new Socket("localhost", port)`, which performs a TCP handshake against the listening server socket.
3. On the server side, each successful `accept()` call returns a connected `Socket` representing that specific client connection; the acceptor thread immediately hands it off to the pool via `pool.submit(() -> handle(client, "client"))` and loops back to `accept()` again, ready for the next connection — this is what lets the server handle multiple clients without one client's slow I/O blocking the acceptance of the next.
4. Inside `handle`, `in.readLine()` blocks until the corresponding client writes and flushes a line (via `PrintWriter`'s auto-flush, enabled by the `true` constructor argument). Once the client's `out.println("message-" + id)` sends its line, `readLine()` unblocks with that string.
5. `handle` immediately writes back `"echo: " + line` via `out`, and the try-with-resources block closes `client`'s streams and the socket itself as `handle` returns.
6. Back on the client side, `in.readLine()` — which was blocked waiting for the server's reply — unblocks with the echoed string, and `System.out.println("Client " + id + " got: " + in.readLine())` prints it.
7. Each client task calls `done.countDown()` in its `finally` block regardless of success or failure, and `main`'s `done.await(5, TimeUnit.SECONDS)` blocks until all 5 clients have finished (or the 5-second timeout elapses), after which the thread pool shuts down and the program exits.

```
acceptorThread:  accept()──►handle(c0)  accept()──►handle(c1)  accept()──►handle(c2) ...
client tasks:     c0 connect→write→read reply     c1 connect→write→read reply   ... (concurrent)
```

## 7. Gotchas & takeaways

> The JEP explicitly notes a small number of **edge-case behavior differences** between the old and new implementations (mostly around obscure timing/exception details in rarely-exercised paths). If a server exhibits an unexpected behavior change after upgrading to Java 13+, the `-Djdk.net.usePlainSocketImpl=true` system property was provided (in early Java 13/14 releases) as a temporary escape hatch to revert to the legacy implementation while you investigate — though this flag was eventually removed as `NioSocketImpl` matured, so it isn't a long-term fix.

- Application code using `Socket`/`ServerSocket` requires **zero changes** — this is purely an internal implementation swap.
- The new `NioSocketImpl` shares infrastructure with `java.nio.channels.SocketChannel`, giving better scalability for servers handling many concurrent blocking connections.
- This reimplementation was explicitly groundwork for later virtual-threads (Project Loom) work — blocking socket calls needed an implementation compatible with lightweight thread scheduling.
- `setSoTimeout`, blocking semantics, and all standard `Socket`/`ServerSocket` behaviors are fully preserved — existing timeout- and exception-handling code continues to work unchanged.
- If you rely on very obscure legacy socket edge-case behavior, test carefully on Java 13+; the vast majority of code is unaffected, but the JEP itself acknowledges rare corner cases.
