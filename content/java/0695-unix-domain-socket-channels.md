---
card: java
gi: 695
slug: unix-domain-socket-channels
title: Unix-domain socket channels
---

## 1. What it is

**Java 16** added standard support for **Unix-domain sockets** (JEP 380) in the `java.nio.channels` API — `SocketChannel`, `ServerSocketChannel`, and the new `UnixDomainSocketAddress` class now work with sockets addressed by a **filesystem path** rather than a host/port pair. A Unix-domain socket is an inter-process communication mechanism, available on Unix-like systems (Linux, macOS) and, since Windows 10, on Windows too, that lets two processes on the **same machine** communicate through a named path in the filesystem (like `/tmp/my-app.sock`) instead of going through the full TCP/IP networking stack.

## 2. Why & when

Many applications only ever need to communicate between processes running on the *same host* — a local daemon and its CLI client, sidecar processes in a container pod, or components of a larger application split into separate processes for isolation. Using TCP sockets (`127.0.0.1:port`) for this works, but carries real overhead and rough edges that don't apply when both endpoints are on the same machine: TCP's connection-establishment overhead, the network stack's checksumming and buffering machinery, and the practical annoyance of managing port numbers (avoiding collisions, deciding who owns which port). Unix-domain sockets address all of this: they're addressed by filesystem path (so permissions can be controlled via ordinary file permissions), avoid the TCP/IP stack's overhead since the OS kernel can shuttle data directly between the two processes, and eliminate port-number management entirely. Before Java 16, using Unix-domain sockets from Java meant a third-party native-binding library; from Java 16 onward, it's a standard, first-class part of `java.nio.channels`. Reach for it when building same-host inter-process communication — a local service and its CLI, or communication between sidecar containers sharing a filesystem volume — where the two endpoints are guaranteed to be on the same machine.

## 3. Core concept

```java
import java.net.UnixDomainSocketAddress;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.nio.file.Path;

Path socketPath = Path.of("/tmp/my-app.sock");
UnixDomainSocketAddress address = UnixDomainSocketAddress.of(socketPath);

// Server side
ServerSocketChannel server = ServerSocketChannel.open(java.net.StandardProtocolFamily.UNIX);
server.bind(address);

// Client side
SocketChannel client = SocketChannel.open(address);
```

The API mirrors ordinary TCP socket channel usage almost exactly — the only differences are the `StandardProtocolFamily.UNIX` argument and using a filesystem-path-based `UnixDomainSocketAddress` instead of an `InetSocketAddress`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two processes on the same machine communicate through a Unix-domain socket addressed by a filesystem path, bypassing the TCP/IP network stack">
  <rect x="20" y="60" width="180" height="70" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="88" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Process A</text>
  <text x="110" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">server</text>

  <rect x="440" y="60" width="180" height="70" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="530" y="88" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Process B</text>
  <text x="530" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">client</text>

  <rect x="240" y="70" width="160" height="50" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="320" y="92" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">/tmp/my-app.sock</text>
  <text x="320" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">filesystem path, same host</text>

  <line x1="200" y1="95" x2="240" y2="95" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <line x1="400" y1="95" x2="440" y2="95" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>

  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Two same-machine processes connect through a filesystem path, without any TCP/IP networking involved.

## 5. Runnable example

Scenario: a tiny same-machine echo service — first a basic server that accepts one connection and echoes back what it reads, with a client sending a message, then a version handling multiple sequential client connections in a loop, then a small request/response protocol layered on top (a simple line-based "ping" command returning "pong" plus a timestamp).

### Level 1 — Basic

```java
// File: UnixSocketEchoBasic.java
import java.net.StandardProtocolFamily;
import java.net.UnixDomainSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.nio.file.Files;
import java.nio.file.Path;

public class UnixSocketEchoBasic {
    public static void main(String[] args) throws Exception {
        Path socketPath = Files.createTempFile("echo", ".sock");
        Files.delete(socketPath); // the path must not exist yet for bind()
        UnixDomainSocketAddress address = UnixDomainSocketAddress.of(socketPath);

        try (ServerSocketChannel server = ServerSocketChannel.open(StandardProtocolFamily.UNIX)) {
            server.bind(address);

            Thread serverThread = new Thread(() -> {
                try (SocketChannel accepted = server.accept()) {
                    ByteBuffer buffer = ByteBuffer.allocate(256);
                    int read = accepted.read(buffer);
                    buffer.flip();
                    accepted.write(buffer); // echo back exactly what was read
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
            });
            serverThread.start();

            try (SocketChannel client = SocketChannel.open(address)) {
                client.write(ByteBuffer.wrap("hello over a unix socket".getBytes()));
                ByteBuffer response = ByteBuffer.allocate(256);
                client.read(response);
                response.flip();
                byte[] bytes = new byte[response.remaining()];
                response.get(bytes);
                System.out.println("Client received: " + new String(bytes));
            }
            serverThread.join();
        } finally {
            Files.deleteIfExists(socketPath);
        }
    }
}
```

**How to run (Linux or macOS — Unix-domain sockets aren't available in every environment, e.g. some container sandboxes):**
```
java UnixSocketEchoBasic.java
```

Expected output:
```
Client received: hello over a unix socket
```

### Level 2 — Intermediate

```java
// File: UnixSocketMultiClient.java
import java.net.StandardProtocolFamily;
import java.net.UnixDomainSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.nio.file.Files;
import java.nio.file.Path;

public class UnixSocketMultiClient {
    public static void main(String[] args) throws Exception {
        Path socketPath = Files.createTempFile("multi", ".sock");
        Files.delete(socketPath);
        UnixDomainSocketAddress address = UnixDomainSocketAddress.of(socketPath);

        try (ServerSocketChannel server = ServerSocketChannel.open(StandardProtocolFamily.UNIX)) {
            server.bind(address);

            Thread serverThread = new Thread(() -> {
                try {
                    for (int i = 0; i < 3; i++) {
                        try (SocketChannel accepted = server.accept()) {
                            ByteBuffer buffer = ByteBuffer.allocate(256);
                            int read = accepted.read(buffer);
                            buffer.flip();
                            byte[] bytes = new byte[buffer.remaining()];
                            buffer.get(bytes);
                            String reply = "echo: " + new String(bytes);
                            accepted.write(ByteBuffer.wrap(reply.getBytes()));
                        }
                    }
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
            });
            serverThread.start();

            for (int i = 1; i <= 3; i++) {
                try (SocketChannel client = SocketChannel.open(address)) {
                    client.write(ByteBuffer.wrap(("message " + i).getBytes()));
                    ByteBuffer response = ByteBuffer.allocate(256);
                    client.read(response);
                    response.flip();
                    byte[] bytes = new byte[response.remaining()];
                    response.get(bytes);
                    System.out.println(new String(bytes));
                }
            }
            serverThread.join();
        } finally {
            Files.deleteIfExists(socketPath);
        }
    }
}
```

**How to run:**
```
java UnixSocketMultiClient.java
```

Expected output:
```
echo: message 1
echo: message 2
echo: message 3
```

### Level 3 — Advanced

```java
// File: UnixSocketPingProtocol.java
import java.net.StandardProtocolFamily;
import java.net.UnixDomainSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.nio.file.Files;
import java.nio.file.Path;

public class UnixSocketPingProtocol {
    static String handleRequest(String request) {
        if (request.equals("PING")) {
            return "PONG " + System.currentTimeMillis();
        }
        return "ERROR unknown command: " + request;
    }

    public static void main(String[] args) throws Exception {
        Path socketPath = Files.createTempFile("ping", ".sock");
        Files.delete(socketPath);
        UnixDomainSocketAddress address = UnixDomainSocketAddress.of(socketPath);

        try (ServerSocketChannel server = ServerSocketChannel.open(StandardProtocolFamily.UNIX)) {
            server.bind(address);

            Thread serverThread = new Thread(() -> {
                try (SocketChannel accepted = server.accept()) {
                    ByteBuffer buffer = ByteBuffer.allocate(256);
                    int read = accepted.read(buffer);
                    buffer.flip();
                    byte[] bytes = new byte[buffer.remaining()];
                    buffer.get(bytes);
                    String request = new String(bytes);
                    String response = handleRequest(request);
                    accepted.write(ByteBuffer.wrap(response.getBytes()));
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
            });
            serverThread.start();

            try (SocketChannel client = SocketChannel.open(address)) {
                client.write(ByteBuffer.wrap("PING".getBytes()));
                ByteBuffer response = ByteBuffer.allocate(256);
                client.read(response);
                response.flip();
                byte[] bytes = new byte[response.remaining()];
                response.get(bytes);
                String reply = new String(bytes);
                System.out.println("Server replied: " + reply.split(" ")[0]); // print just "PONG", timestamp varies
            }
            serverThread.join();
        } finally {
            Files.deleteIfExists(socketPath);
        }
    }
}
```

**How to run:**
```
java UnixSocketPingProtocol.java
```

Expected output:
```
Server replied: PONG
```

Level 3 layers a minimal request/response **protocol** on top of the raw byte channel: the client sends the literal string `"PING"`, `handleRequest` on the server side interprets it and replies with `"PONG <timestamp>"`, and since the timestamp varies every run, the client only prints the fixed `"PONG"` portion — the same design pattern (parse a request, dispatch to a handler, format a response) that a real same-host RPC protocol over a Unix-domain socket would use, just reduced to its simplest possible form.

## 6. Walkthrough

1. `main` creates a temporary file path via `Files.createTempFile(...)` purely to get a unique, collision-free filename, then immediately deletes it with `Files.delete(socketPath)` — this is necessary because `ServerSocketChannel.bind()` requires the socket path to **not** already exist as a regular file; the OS creates the special socket file at that path during `bind()` itself.
2. `ServerSocketChannel.open(StandardProtocolFamily.UNIX)` opens a server channel specifically for the Unix-domain protocol family (as opposed to the default `INET`/`INET6` used for ordinary TCP), and `.bind(address)` binds it to the filesystem path wrapped in `UnixDomainSocketAddress`.
3. A separate `serverThread` is started to run `server.accept()` — this blocks until a client connects, so it must run concurrently with the client-side code below (running both in the same thread would deadlock, since `accept()` would block forever waiting for a connection the client hasn't made yet).
4. Back in the main thread, `SocketChannel.open(address)` connects a client channel to the same socket path — the OS kernel matches this connection attempt against the listening server channel bound to that exact path.
5. Once connected, `client.write(ByteBuffer.wrap("PING".getBytes()))` sends the literal bytes `P`, `I`, `N`, `G` through the socket; on the server side, `accepted.read(buffer)` (inside `serverThread`) receives those same bytes into its own `ByteBuffer`.
6. `handleRequest("PING")` checks the received string against the known `"PING"` command and returns `"PONG " + System.currentTimeMillis()` — a response string that includes a real, always-changing timestamp appended after a space.
7. The server writes that response back through the same connected channel (`accepted.write(...)`), and the client's `client.read(response)` receives it into its own buffer.
8. Back in the client, `new String(bytes)` reconstructs the full response string (e.g. `"PONG 1751234567890"`), and `reply.split(" ")[0]` extracts just the first word (`"PONG"`), discarding the variable timestamp before printing — ensuring the printed output is exactly reproducible across runs despite the underlying protocol genuinely including a real, changing timestamp.
9. Both `SocketChannel`s and the `ServerSocketChannel` are opened inside `try`-with-resources blocks, so each is automatically closed once its block exits; `serverThread.join()` ensures the main thread waits for the server-side handling to fully complete before the program proceeds to clean up the socket file in the `finally` block.

```
main thread                              serverThread
   │                                          │
   │                                    server.accept() (blocks)
SocketChannel.open(address) ─────────────────►│ (connection established)
   │                                          │
client.write("PING") ─────────────────────────►│ accepted.read(...) -> "PING"
   │                                    handleRequest("PING") -> "PONG <ts>"
   │◄──────────────────────────────────── accepted.write("PONG <ts>")
client.read(...) -> "PONG <ts>"                │
print "PONG" (timestamp stripped)              │
```

## 7. Gotchas & takeaways

> `ServerSocketChannel.bind(address)` requires that **no file already exists** at the target path — the OS creates the special Unix-domain socket file during `bind()`. If a stale socket file from a previous, uncleanly-terminated run is still present at that path, `bind()` fails; production code typically checks for and removes a stale socket file (after confirming no other process is actually using it) before binding.

- Unix-domain sockets only work for **same-machine** communication — they cannot be used across a network the way TCP sockets can; if the two endpoints might ever run on different hosts, use ordinary TCP sockets instead.
- The socket file created at the bound path should be cleaned up (deleted) when the server shuts down — an abandoned socket file left on disk after a crash can block a future `bind()` attempt at the same path until manually removed.
- Availability depends on the OS: Linux and macOS have long supported Unix-domain sockets; Windows gained support starting with Windows 10 (1803) — code intending to run across all three should check for `UnsupportedOperationException` or otherwise handle environments lacking support.
- Beyond simple byte throughput, Unix-domain sockets on many platforms also support passing file descriptors and credentials between processes at the OS level — capabilities Java's `java.nio.channels` API in this JEP does not expose, so if you need those specific OS-level features, you'd still need a native-interop layer.
- Compared to loopback TCP (`127.0.0.1`), Unix-domain sockets typically have lower latency and overhead for same-host IPC, since the kernel can shuttle data directly without traversing the full network stack.
