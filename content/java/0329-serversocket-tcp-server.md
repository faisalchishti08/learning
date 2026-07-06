---
card: java
gi: 329
slug: serversocket-tcp-server
title: ServerSocket (TCP server)
---

## 1. What it is

`java.net.ServerSocket` is the server-side counterpart to `Socket`. It binds to a local port and listens for incoming TCP connection attempts; each call to `accept()` blocks until a client connects, then returns a brand-new `Socket` representing that one specific client connection — the `ServerSocket` itself never sends or receives application data, it only produces connected `Socket` objects, one per accepted client.

```java
import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;

public class ServerSocketDemo {
    public static void main(String[] args) throws IOException {
        try (ServerSocket server = new ServerSocket(8080)) {
            System.out.println("Listening on port 8080...");
            Socket client = server.accept(); // blocks until a client connects
            BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
            System.out.println("Client said: " + in.readLine());
            client.close();
        }
    }
}
```

`server.accept()` is a blocking call — the thread that calls it does nothing else until a client actually connects, at which point it returns the per-client `Socket` used for that connection's own reading and writing.

## 2. Why & when

Any Java process that needs to accept incoming network connections — a custom protocol server, a simple HTTP server, a chat server — starts with a `ServerSocket` bound to a known port. Real frameworks (embedded Tomcat inside Spring Boot, for instance) use `ServerSocket` internally, but understanding the raw class clarifies what "listening on a port" actually means underneath any higher-level abstraction.

- **Accepting connections from multiple clients** — a single `ServerSocket` can `accept()` in a loop indefinitely, handing each accepted `Socket` off to its own thread (or task) so clients are served concurrently rather than one at a time.
- **Building or testing a custom protocol server** — before adopting a framework, a raw `ServerSocket` loop is the simplest way to prototype and understand a server-side wire protocol.
- **Binding to port 0** to let the OS choose a free ephemeral port — extremely useful in tests, so a test server never collides with a port already in use on the test machine.

A naive server that calls `accept()` and then handles the client synchronously on the same thread can only serve one client at a time — any real server either spawns a new thread per connection or uses a thread pool / non-blocking I/O to serve clients concurrently.

## 3. Core concept

```java
import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;

public class ServerSocketCore {
    public static void main(String[] args) throws IOException {
        try (ServerSocket server = new ServerSocket(0)) {
            int port = server.getLocalPort();
            System.out.println("Server listening on port " + port);

            new Thread(() -> {
                try (Socket client = new Socket("localhost", port)) {
                    PrintWriter out = new PrintWriter(client.getOutputStream(), true);
                    out.println("ping");
                } catch (IOException e) { e.printStackTrace(); }
            }).start();

            try (Socket accepted = server.accept();
                 BufferedReader in = new BufferedReader(new InputStreamReader(accepted.getInputStream()))) {
                System.out.println("Server received: " + in.readLine());
            }
        }
    }
}
```

**How to run:** `java ServerSocketCore.java`

`server.getLocalPort()` reveals the OS-assigned port after binding to port 0, and `server.accept()` blocks in the main thread until the background client thread's connection attempt completes, at which point it returns the connected `Socket` for that one client.

## 4. Diagram

<svg viewBox="0 0 620 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ServerSocket listens on a port; each accept() call returns a new per-client Socket while the listener keeps accepting more">
  <rect x="8" y="8" width="604" height="154" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="55" fill="#6db33f" font-size="10" text-anchor="middle">ServerSocket (listening)</text>

  <text x="210" y="55" fill="#8b949e" font-size="10">accept() →</text>

  <rect x="300" y="30" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="375" y="52" fill="#79c0ff" font-size="9" text-anchor="middle">Socket (client A)</text>
  <rect x="300" y="75" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="375" y="97" fill="#79c0ff" font-size="9" text-anchor="middle">Socket (client B)</text>
  <rect x="300" y="120" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="375" y="142" fill="#79c0ff" font-size="9" text-anchor="middle">Socket (client C)</text>

  <text x="470" y="55" fill="#8b949e" font-size="9">handled on own thread</text>
  <text x="470" y="97" fill="#8b949e" font-size="9">handled on own thread</text>
  <text x="470" y="142" fill="#8b949e" font-size="9">handled on own thread</text>
</svg>

One `ServerSocket` keeps listening while each accepted connection becomes its own independent `Socket`, typically handed to its own thread.

## 5. Runnable example

Scenario: a single-threaded uppercase-echo server, evolved from handling exactly one client and exiting, into a multi-client server using one thread per connection, into a production-style server using a bounded thread pool with graceful shutdown.

### Level 1 — Basic

```java
import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;

public class UpperServerBasic {
    public static void main(String[] args) throws IOException {
        try (ServerSocket server = new ServerSocket(0)) {
            int port = server.getLocalPort();
            System.out.println("Listening on " + port);

            new Thread(() -> sendOneMessage(port, "hello")).start();

            try (Socket client = server.accept(); // only ever accepts ONE client, then exits
                 BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
                 PrintWriter out = new PrintWriter(client.getOutputStream(), true)) {
                String line = in.readLine();
                out.println(line.toUpperCase());
            }
        }
    }

    static void sendOneMessage(int port, String message) {
        try (Socket client = new Socket("localhost", port)) {
            PrintWriter out = new PrintWriter(client.getOutputStream(), true);
            BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
            out.println(message);
            System.out.println("Client got: " + in.readLine());
        } catch (IOException e) { e.printStackTrace(); }
    }
}
```

**How to run:** `java UpperServerBasic.java`

This server calls `accept()` exactly once, handles that one client, then the `try-with-resources` block ends and the server socket closes — a second client connecting afterward would simply be refused, which is fine for a demo but useless as a real server.

### Level 2 — Intermediate

```java
import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;

public class UpperServerIntermediate {
    public static void main(String[] args) throws IOException, InterruptedException {
        ServerSocket server = new ServerSocket(0);
        int port = server.getLocalPort();
        System.out.println("Listening on " + port);

        Thread acceptLoop = new Thread(() -> {
            try {
                while (!server.isClosed()) {
                    Socket client = server.accept(); // loop: keep accepting new clients
                    new Thread(() -> handleClient(client)).start(); // one thread per client
                }
            } catch (IOException e) { /* expected once server.close() runs */ }
        });
        acceptLoop.start();

        // simulate three concurrent clients
        Thread[] clients = new Thread[3];
        for (int i = 0; i < 3; i++) {
            int id = i;
            clients[i] = new Thread(() -> sendOneMessage(port, "hello-" + id));
            clients[i].start();
        }
        for (Thread t : clients) t.join();

        Thread.sleep(200); // let server-side handler threads finish printing
        server.close();
        acceptLoop.join();
    }

    static void handleClient(Socket client) {
        try (client; BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
             PrintWriter out = new PrintWriter(client.getOutputStream(), true)) {
            out.println(in.readLine().toUpperCase());
        } catch (IOException e) { /* connection dropped */ }
    }

    static void sendOneMessage(int port, String message) {
        try (Socket client = new Socket("localhost", port)) {
            PrintWriter out = new PrintWriter(client.getOutputStream(), true);
            BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
            out.println(message);
            System.out.println("Client got: " + in.readLine());
        } catch (IOException e) { e.printStackTrace(); }
    }
}
```

**How to run:** `java UpperServerIntermediate.java`

The `acceptLoop` thread now calls `accept()` repeatedly in a `while` loop, spawning a brand-new thread for each accepted client so all three simulated clients are served concurrently instead of being forced to wait in line — this is the minimum shape of a real multi-client server.

### Level 3 — Advanced

```java
import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class UpperServerAdvanced {
    public static void main(String[] args) throws IOException, InterruptedException {
        ServerSocket server = new ServerSocket(0);
        int port = server.getLocalPort();
        ExecutorService pool = Executors.newFixedThreadPool(4); // bounded, unlike unlimited threads
        System.out.println("Listening on " + port);

        Thread acceptLoop = new Thread(() -> {
            try {
                while (!server.isClosed()) {
                    Socket client = server.accept();
                    pool.submit(() -> handleClient(client));
                }
            } catch (IOException e) { /* expected once server.close() runs */ }
        });
        acceptLoop.start();

        Thread[] clients = new Thread[5];
        for (int i = 0; i < 5; i++) {
            int id = i;
            clients[i] = new Thread(() -> sendOneMessage(port, "hello-" + id));
            clients[i].start();
        }
        for (Thread t : clients) t.join();

        server.close();          // stop accepting new connections
        acceptLoop.join();
        pool.shutdown();         // let in-flight tasks finish
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("Server shut down cleanly.");
    }

    static void handleClient(Socket client) {
        try (client; BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
             PrintWriter out = new PrintWriter(client.getOutputStream(), true)) {
            out.println(in.readLine().toUpperCase());
        } catch (IOException e) { /* connection dropped */ }
    }

    static void sendOneMessage(int port, String message) {
        try (Socket client = new Socket("localhost", port)) {
            PrintWriter out = new PrintWriter(client.getOutputStream(), true);
            BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
            out.println(message);
            System.out.println("Client got: " + in.readLine());
        } catch (IOException e) { e.printStackTrace(); }
    }
}
```

**How to run:** `java UpperServerAdvanced.java`

Instead of spawning an unbounded number of raw threads (which can exhaust system resources under heavy load), client handling is submitted to a fixed-size `ExecutorService` thread pool of 4 workers, and shutdown is orderly: `server.close()` stops new connections, `acceptLoop.join()` confirms the accept loop has exited, and `pool.shutdown()` plus `awaitTermination` let any already-accepted clients finish being handled before the program declares itself shut down.

## 6. Walkthrough

Execution starts in `main`: it creates the `ServerSocket` on an OS-assigned port and a fixed thread pool of 4 workers, then starts `acceptLoop`, which immediately calls `server.accept()` and blocks, waiting for the first connection.

`main` then starts five client threads almost simultaneously, each calling `sendOneMessage`, which opens its own `Socket` to the server's port, writes a line like `"hello-0"`, and blocks on `in.readLine()` waiting for a reply.

Each of these five connection attempts causes `acceptLoop`'s blocked `server.accept()` call to return a new, distinct `Socket` — one per client, in whatever order the OS delivers them. For each one, `acceptLoop` calls `pool.submit(() -> handleClient(client))`, handing the socket to the thread pool rather than processing it inline, then immediately loops back to `accept()` again for the next connection. Because the pool has 4 workers, up to 4 clients are processed in parallel; if a 5th connection arrives before any worker frees up, its task simply waits in the pool's internal queue briefly.

Inside `handleClient`, each worker reads one line from its client (e.g., `"hello-3"`), converts it to uppercase (`"HELLO-3"`), writes that back, and the try-with-resources closes that client's socket. Back on each client thread, `in.readLine()` unblocks with the uppercased reply and prints `Client got: HELLO-3`.

Once all five client threads have been joined in `main`, it calls `server.close()`, which causes the still-blocked `accept()` call inside `acceptLoop` (waiting for a 6th connection that never comes) to throw an `IOException`, which the loop's catch block treats as the expected shutdown signal, ending `acceptLoop`. `main` then joins `acceptLoop`, calls `pool.shutdown()` to stop accepting new tasks, and `awaitTermination(5, SECONDS)` blocks briefly until any in-flight `handleClient` tasks finish, after which it prints `Server shut down cleanly.`

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="accept loop hands each connection to a bounded thread pool; five clients are served across four workers; shutdown closes server then drains the pool">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#6db33f" font-size="10">acceptLoop: while(!closed) { accept() -&gt; pool.submit(handleClient) }</text>
  <text x="20" y="55" fill="#79c0ff" font-size="10">5 client threads connect concurrently, each sends one line, waits for reply</text>
  <text x="20" y="80" fill="#8b949e" font-size="10">pool (4 workers): up to 4 handled in parallel, 5th queued briefly if all busy</text>
  <text x="20" y="105" fill="#e6edf3" font-size="10">each worker: readLine() -&gt; toUpperCase() -&gt; println() -&gt; close client socket</text>
  <text x="20" y="130" fill="#f85149" font-size="10">shutdown: server.close() unblocks accept() with IOException -&gt; acceptLoop exits</text>
  <text x="20" y="155" fill="#8b949e" font-size="10">pool.shutdown() + awaitTermination() drains any still-running handleClient tasks</text>
</svg>

## 7. Gotchas & takeaways

> Handling each client synchronously on the thread that calls `accept()` (no per-client thread or pool) makes the server serve exactly one client at a time — every other client waits in the OS-level connection backlog queue until the current one finishes, which looks like the server "hanging" under any real load.

- `ServerSocket.accept()` blocks until a client connects and returns a brand-new `Socket` per client — the listening socket itself never carries application data.
- A production server needs a loop around `accept()` plus concurrent handling (thread-per-connection or a thread pool) — a single `accept()` call only ever serves one client.
- Prefer a bounded `ExecutorService` over spawning unlimited raw threads — an unbounded thread-per-client design can exhaust memory or OS thread limits under a connection flood.
- Binding to port `0` lets the OS assign a free ephemeral port — use `getLocalPort()` to discover it; this is especially useful for tests that must not hardcode a port that might already be in use.
- Shutdown order matters: close the `ServerSocket` first to stop new connections, then drain any in-flight work (e.g., `ExecutorService.shutdown()` + `awaitTermination`) rather than killing everything abruptly.
