---
card: java
gi: 328
slug: socket-tcp-client
title: Socket (TCP client)
---

## 1. What it is

`java.net.Socket` is the client-side endpoint of a TCP connection. Creating a `Socket` and pointing it at a host and port performs the TCP three-way handshake and, once it returns successfully, gives you an `InputStream` and `OutputStream` pair for exchanging bytes with the server — TCP guarantees that bytes arrive in order and without loss (retransmitting as needed), which is why it's the default choice for anything that needs reliable delivery, like HTTP, database connections, or a custom line-based protocol.

```java
import java.io.*;
import java.net.Socket;

public class SocketDemo {
    public static void main(String[] args) throws IOException {
        try (Socket socket = new Socket("example.com", 80)) {
            OutputStream out = socket.getOutputStream();
            out.write("GET / HTTP/1.0\r\n\r\n".getBytes());
            out.flush();

            InputStream in = socket.getInputStream();
            byte[] buffer = new byte[512];
            int n = in.read(buffer);
            System.out.println(new String(buffer, 0, n));
        }
    }
}
```

`new Socket("example.com", 80)` blocks until the TCP handshake completes (or fails), after which writing to `getOutputStream()` sends bytes to the server and reading from `getInputStream()` receives the server's reply.

## 2. Why & when

Whenever a Java program needs to talk to another process over the network using a reliable, ordered byte stream — rather than the fire-and-forget, possibly-out-of-order delivery of UDP — `Socket` is the building block, whether used directly or wrapped by a higher-level library (an HTTP client, a JDBC driver, an RPC framework all use sockets underneath).

- **Talking to a server that speaks a known text or binary protocol** — HTTP, SMTP, a custom line-based protocol, or any protocol where message order and completeness matter.
- **Building or testing a custom client/server protocol** — before reaching for a full framework, a raw `Socket` is the simplest way to understand and prototype a wire protocol.
- **Any long-lived, two-way connection** — a socket, once open, can be written to and read from repeatedly for as long as it stays open, unlike a single request/response `URLConnection`.

`Socket` operations are blocking by default — `connect`, `read`, and `write` calls can all pause the calling thread until data is available or the network responds — so real clients typically either use timeouts (`setSoTimeout`) or run socket I/O on a dedicated thread so it doesn't freeze the rest of the application.

## 3. Core concept

```java
import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;

public class SocketCore {
    public static void main(String[] args) throws IOException, InterruptedException {
        ServerSocket server = new ServerSocket(0); // port 0 = let the OS pick a free port
        int port = server.getLocalPort();

        Thread serverThread = new Thread(() -> {
            try (Socket conn = server.accept();
                 BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                 PrintWriter out = new PrintWriter(conn.getOutputStream(), true)) {
                String line = in.readLine();
                out.println("echo: " + line);
            } catch (IOException e) {
                e.printStackTrace();
            }
        });
        serverThread.start();

        try (Socket client = new Socket("localhost", port);
             PrintWriter out = new PrintWriter(client.getOutputStream(), true);
             BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()))) {
            out.println("hello server");
            System.out.println("Client received: " + in.readLine());
        }
        serverThread.join();
        server.close();
    }
}
```

**How to run:** `java SocketCore.java`

The client's `new Socket("localhost", port)` connects to the server's `accept()`ed connection; both sides then use `PrintWriter`/`BufferedReader` wrappers so they can exchange whole lines of text instead of raw bytes.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="TCP client socket connects to server, sends request bytes, reads response bytes over the same connection">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>
  <rect x="30" y="40" width="160" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="60" fill="#79c0ff" font-size="10" text-anchor="middle">Client</text>
  <text x="110" y="75" fill="#8b949e" font-size="9" text-anchor="middle">new Socket(host, port)</text>

  <text x="200" y="55" fill="#8b949e" font-size="9">write() →</text>
  <text x="200" y="90" fill="#8b949e" font-size="9">← read()</text>

  <rect x="410" y="40" width="160" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="490" y="60" fill="#6db33f" font-size="10" text-anchor="middle">Server</text>
  <text x="490" y="75" fill="#8b949e" font-size="9" text-anchor="middle">accepted connection</text>

  <text x="150" y="130" fill="#8b949e" font-size="9">Same TCP connection carries both directions, in order, reliably.</text>
</svg>

## 5. Runnable example

Scenario: a simple line-based echo client, evolved from a bare connect-and-read attempt with no error handling, into one with connection timeouts and read timeouts, into a production-style client that retries on connection failure and cleanly reports each distinct failure mode.

### Level 1 — Basic

```java
import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;

public class EchoClientBasic {
    public static void main(String[] args) throws IOException, InterruptedException {
        ServerSocket server = new ServerSocket(0);
        int port = server.getLocalPort();
        Thread serverThread = startEchoServer(server);

        Socket client = new Socket("localhost", port); // no timeout, no error handling
        PrintWriter out = new PrintWriter(client.getOutputStream(), true);
        BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
        out.println("hello");
        System.out.println("Received: " + in.readLine());
        client.close();

        serverThread.join();
        server.close();
    }

    static Thread startEchoServer(ServerSocket server) {
        Thread t = new Thread(() -> {
            try (Socket conn = server.accept();
                 BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                 PrintWriter out = new PrintWriter(conn.getOutputStream(), true)) {
                out.println("echo: " + in.readLine());
            } catch (IOException e) { /* demo server, ignored */ }
        });
        t.start();
        return t;
    }
}
```

**How to run:** `java EchoClientBasic.java`

This works for the happy path, but if the server were slow, unreachable, or the connection dropped mid-read, `readLine()` could block forever — there is no timeout anywhere, which is unacceptable outside a quick demo.

### Level 2 — Intermediate

```java
import java.io.*;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;

public class EchoClientIntermediate {
    public static void main(String[] args) throws IOException, InterruptedException {
        ServerSocket server = new ServerSocket(0);
        int port = server.getLocalPort();
        Thread serverThread = startEchoServer(server);

        Socket client = new Socket();
        client.connect(new InetSocketAddress("localhost", port), 2000); // 2s connect timeout
        client.setSoTimeout(2000); // 2s read timeout

        try (PrintWriter out = new PrintWriter(client.getOutputStream(), true);
             BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()))) {
            out.println("hello with timeout");
            System.out.println("Received: " + in.readLine());
        } finally {
            client.close();
        }

        serverThread.join();
        server.close();
    }

    static Thread startEchoServer(ServerSocket server) {
        Thread t = new Thread(() -> {
            try (Socket conn = server.accept();
                 BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                 PrintWriter out = new PrintWriter(conn.getOutputStream(), true)) {
                out.println("echo: " + in.readLine());
            } catch (IOException e) { /* demo server, ignored */ }
        });
        t.start();
        return t;
    }
}
```

**How to run:** `java EchoClientIntermediate.java`

Using the no-argument `Socket()` constructor plus `connect(address, timeoutMs)` bounds how long the handshake can take, and `setSoTimeout(ms)` bounds how long any subsequent `read` can block — so a hung or unreachable server now produces a timely exception instead of hanging the client forever.

### Level 3 — Advanced

```java
import java.io.*;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketTimeoutException;

public class EchoClientAdvanced {
    public static void main(String[] args) throws IOException, InterruptedException {
        ServerSocket server = new ServerSocket(0);
        int port = server.getLocalPort();
        Thread serverThread = startEchoServer(server);

        String reply = sendWithRetry("localhost", port, "hello robustly", 3);
        System.out.println("Final result: " + reply);

        serverThread.join();
        server.close();
    }

    static Thread startEchoServer(ServerSocket server) {
        Thread t = new Thread(() -> {
            try (Socket conn = server.accept();
                 BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                 PrintWriter out = new PrintWriter(conn.getOutputStream(), true)) {
                out.println("echo: " + in.readLine());
            } catch (IOException e) { /* demo server, ignored */ }
        });
        t.start();
        return t;
    }

    static String sendWithRetry(String host, int port, String message, int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try (Socket client = new Socket()) {
                client.connect(new InetSocketAddress(host, port), 1000);
                client.setSoTimeout(1000);
                PrintWriter out = new PrintWriter(client.getOutputStream(), true);
                BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
                out.println(message);
                return in.readLine();
            } catch (SocketTimeoutException e) {
                System.out.println("Attempt " + attempt + " timed out, retrying...");
            } catch (IOException e) {
                System.out.println("Attempt " + attempt + " failed: " + e.getMessage() + ", retrying...");
            }
        }
        return null; // all attempts exhausted
    }
}
```

**How to run:** `java EchoClientAdvanced.java`

`sendWithRetry` distinguishes a timeout (`SocketTimeoutException`, worth retrying since the server might just be briefly slow) from other connection failures (generic `IOException`, e.g. connection refused), retries up to `maxAttempts` times, and uses try-with-resources on the `Socket` so each failed attempt's connection is always closed before the next attempt opens a new one.

## 6. Walkthrough

Execution starts in `main`: it starts a background echo server on an OS-assigned port, then calls `sendWithRetry("localhost", port, "hello robustly", 3)`.

Inside `sendWithRetry`, attempt 1 opens `new Socket()` (unconnected) and calls `client.connect(new InetSocketAddress(host, port), 1000)` — this performs the TCP handshake against the local echo server, which succeeds quickly since it's on the same machine. `setSoTimeout(1000)` then bounds any subsequent read to one second.

The client writes `"hello robustly"` via `out.println`, which sends the bytes `hello robustly\n` over the socket. On the server side, the background thread's `server.accept()` had already returned a connected `Socket conn` waiting for input; `in.readLine()` on the server unblocks, reading the line, and the server immediately writes back `"echo: hello robustly\n"` via its own `PrintWriter`, then the try-with-resources block closes the server's connection.

Back on the client, `in.readLine()` reads that reply, returning the string `"echo: hello robustly"` from `sendWithRetry` — since this succeeded on the first attempt, the retry loop never needs a second iteration, and the try-with-resources on `client` closes the socket automatically.

`main` prints `Final result: echo: hello robustly`, then joins the server thread and closes the `ServerSocket`.

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="client connects, writes message, server reads and echoes, client reads reply, both sides close">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">1. client.connect(host, port, timeout=1000) -- TCP handshake</text>
  <text x="20" y="52" fill="#79c0ff" font-size="10">2. client writes "hello robustly\n"</text>
  <text x="20" y="74" fill="#6db33f" font-size="10">3. server.accept()'d connection reads the line, writes "echo: hello robustly\n"</text>
  <text x="20" y="96" fill="#79c0ff" font-size="10">4. client reads reply within setSoTimeout(1000) window</text>
  <text x="20" y="118" fill="#8b949e" font-size="10">5. try-with-resources closes client socket; server closes its connection</text>
  <text x="20" y="140" fill="#e6edf3" font-size="10">Result printed: "echo: hello robustly" (first attempt succeeded, no retry needed)</text>
</svg>

## 7. Gotchas & takeaways

> Forgetting `setSoTimeout()` (or a connect timeout) means a client can hang indefinitely on a slow, unresponsive, or firewalled server — always set explicit timeouts on sockets used outside of a trusted, fully-controlled local test.

- `new Socket(host, port)` connects immediately with no timeout; use `new Socket()` plus `connect(address, timeoutMs)` when you need to bound connection time.
- `setSoTimeout(ms)` bounds blocking reads, not the initial connection — you need both for a fully timeout-safe client.
- Wrap raw streams in `BufferedReader`/`PrintWriter` (or similar) for line-based text protocols; work with raw `InputStream`/`OutputStream` bytes for binary protocols.
- Always close sockets (ideally via try-with-resources) — an unclosed socket leaks a file descriptor and, on the server side, can leave a connection half-open.
- Distinguish timeout failures (worth retrying — the peer might just be briefly slow) from connection-refused or other I/O failures (retrying immediately is less likely to help) when designing retry logic.
