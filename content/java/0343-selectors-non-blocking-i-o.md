---
card: java
gi: 343
slug: selectors-non-blocking-i-o
title: Selectors & non-blocking I/O
---

## 1. What it is

A `Selector` lets a single thread monitor multiple channels at once, and be told which of them are actually ready for an operation (accepting a connection, reading, or writing) — instead of dedicating one blocked thread per channel, as a traditional thread-per-connection server does. To use a `Selector`, a channel must first be switched into non-blocking mode (`configureBlocking(false)`), then registered with the selector for the specific operations it's interested in; calling `selector.select()` then blocks only until *at least one* registered channel becomes ready, returning the set of ready channels for the calling thread to handle.

```java
import java.nio.channels.*;

public class SelectorDemo {
    public static void main(String[] args) throws Exception {
        Selector selector = Selector.open();
        ServerSocketChannel server = ServerSocketChannel.open();
        server.bind(new java.net.InetSocketAddress(0));
        server.configureBlocking(false); // required before registering with a Selector
        server.register(selector, SelectionKey.OP_ACCEPT);

        System.out.println("Listening on port " + server.socket().getLocalPort()
                + " using a single thread via Selector.");
        selector.close();
        server.close();
    }
}
```

`configureBlocking(false)` is mandatory — a `Selector` can only manage channels operating in non-blocking mode, since the whole point is that no single channel's operation is allowed to block the monitoring thread.

## 2. Why & when

A thread-per-connection server (one `Socket`/thread per client) is simple but doesn't scale past a few thousand concurrent connections, since each blocked thread still consumes real OS resources (stack memory, scheduling overhead) even while doing nothing. Selectors flip that model: one thread efficiently waits on many channels simultaneously, only doing work for the ones that are actually ready, which scales to far more concurrent connections per thread.

- **High-concurrency network servers** — handling thousands of simultaneous connections without needing thousands of threads, common in load balancers, proxies, and high-throughput network services.
- **Event-driven architectures** — a `Selector`-based loop is the low-level building block underneath many event-driven I/O frameworks (like Netty), which build higher-level abstractions on top of this same readiness-notification model.
- **Resource-constrained environments** — where thread overhead (memory, context-switching cost) genuinely matters more than the added code complexity of managing non-blocking state machines per connection.

The tradeoff is real complexity: instead of writing straightforward sequential blocking code per connection, non-blocking I/O requires tracking each connection's partial progress (a half-read request, a partially-written response) across multiple `select()` cycles, since no single operation is allowed to simply block and wait until it's "done."

## 3. Core concept

```java
import java.nio.ByteBuffer;
import java.nio.channels.*;
import java.util.Iterator;
import java.util.Set;

public class SelectorCore {
    public static void main(String[] args) throws Exception {
        Selector selector = Selector.open();
        ServerSocketChannel server = ServerSocketChannel.open();
        server.bind(new java.net.InetSocketAddress(0));
        server.configureBlocking(false);
        server.register(selector, SelectionKey.OP_ACCEPT);
        int port = server.socket().getLocalPort();

        new Thread(() -> {
            try (SocketChannel client = SocketChannel.open(new java.net.InetSocketAddress("localhost", port))) {
                client.write(ByteBuffer.wrap("hi".getBytes()));
                Thread.sleep(200);
            } catch (Exception e) { e.printStackTrace(); }
        }).start();

        selector.select(2000); // blocks up to 2s until something is ready
        Set<SelectionKey> readyKeys = selector.selectedKeys();
        System.out.println("Ready channels: " + readyKeys.size());
        for (SelectionKey key : readyKeys) {
            if (key.isAcceptable()) System.out.println("A connection is ready to accept.");
        }
        selector.close();
        server.close();
    }
}
```

**How to run:** `java SelectorCore.java`

`selector.select(2000)` blocks the single monitoring thread until either something becomes ready or 2 seconds pass, and `selectedKeys()` returns exactly the subset of registered channels that are actually ready right now — the thread never has to poll or block on any one specific channel.

## 4. Diagram

<svg viewBox="0 0 620 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="one thread registers many channels with a Selector; select() blocks until any of them is ready, then returns just the ready subset for handling">
  <rect x="8" y="8" width="604" height="154" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="130" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="85" y="50" fill="#8b949e" font-size="9" text-anchor="middle">channel A</text>
  <rect x="20" y="70" width="130" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="85" y="90" fill="#6db33f" font-size="9" text-anchor="middle">channel B (ready)</text>
  <rect x="20" y="110" width="130" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="85" y="130" fill="#8b949e" font-size="9" text-anchor="middle">channel C</text>

  <text x="185" y="75" fill="#8b949e" font-size="10">registered with →</text>

  <rect x="330" y="65" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="405" y="90" fill="#79c0ff" font-size="10" text-anchor="middle">Selector (1 thread)</text>

  <text x="500" y="90" fill="#8b949e" font-size="9">select() returns { B }</text>
</svg>

## 5. Runnable example

Scenario: a single-threaded echo server, evolved from an accept-only selector loop that doesn't yet handle any client data, into one that also accepts and reads from clients using the same selector, into a production-style server correctly distinguishing accept-ready, read-ready, and write-ready channels within one loop.

### Level 1 — Basic

```java
import java.net.InetSocketAddress;
import java.nio.channels.*;
import java.util.Iterator;
import java.util.Set;

public class SelectorEchoBasic {
    public static void main(String[] args) throws Exception {
        Selector selector = Selector.open();
        ServerSocketChannel server = ServerSocketChannel.open();
        server.bind(new InetSocketAddress(0));
        server.configureBlocking(false);
        server.register(selector, SelectionKey.OP_ACCEPT);
        int port = server.socket().getLocalPort();
        System.out.println("Listening on " + port);

        new Thread(() -> {
            try (SocketChannel client = SocketChannel.open(new InetSocketAddress("localhost", port))) {
                Thread.sleep(100);
            } catch (Exception e) { e.printStackTrace(); }
        }).start();

        selector.select(1000);
        Set<SelectionKey> ready = selector.selectedKeys();
        System.out.println("Ready keys: " + ready.size());
        for (SelectionKey key : ready) {
            if (key.isAcceptable()) {
                SocketChannel client = server.accept(); // never reads from it -- incomplete
                System.out.println("Accepted a connection, but not handling data yet.");
            }
        }
        selector.close();
        server.close();
    }
}
```

**How to run:** `java SelectorEchoBasic.java`

This accepts the incoming connection but does nothing further with it — the accepted `SocketChannel` isn't registered for reading, so any data the client sends would simply never be processed, an incomplete first step toward a real server.

### Level 2 — Intermediate

```java
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.*;
import java.util.Iterator;
import java.util.Set;

public class SelectorEchoIntermediate {
    public static void main(String[] args) throws Exception {
        Selector selector = Selector.open();
        ServerSocketChannel server = ServerSocketChannel.open();
        server.bind(new InetSocketAddress(0));
        server.configureBlocking(false);
        server.register(selector, SelectionKey.OP_ACCEPT);
        int port = server.socket().getLocalPort();

        new Thread(() -> {
            try (SocketChannel client = SocketChannel.open(new InetSocketAddress("localhost", port))) {
                client.write(ByteBuffer.wrap("ping".getBytes()));
                Thread.sleep(300);
            } catch (Exception e) { e.printStackTrace(); }
        }).start();

        long deadline = System.currentTimeMillis() + 2000;
        while (System.currentTimeMillis() < deadline) {
            selector.select(500);
            Iterator<SelectionKey> it = selector.selectedKeys().iterator();
            while (it.hasNext()) {
                SelectionKey key = it.next();
                it.remove(); // MUST remove -- selectedKeys() does not clear itself
                if (key.isAcceptable()) {
                    SocketChannel client = server.accept();
                    client.configureBlocking(false);
                    client.register(selector, SelectionKey.OP_READ); // now also watch for data
                    System.out.println("Accepted and registered a client for reading.");
                } else if (key.isReadable()) {
                    SocketChannel client = (SocketChannel) key.channel();
                    ByteBuffer buffer = ByteBuffer.allocate(256);
                    int n = client.read(buffer);
                    if (n > 0) {
                        buffer.flip();
                        byte[] data = new byte[n];
                        buffer.get(data);
                        System.out.println("Read: " + new String(data));
                    }
                    key.cancel();
                    client.close();
                }
            }
        }
        selector.close();
        server.close();
    }
}
```

**How to run:** `java SelectorEchoIntermediate.java`

The accepted client channel is itself set non-blocking and registered for `OP_READ`, so the same `Selector` loop now handles both new connections and incoming data — critically, `it.remove()` is called for every processed key, since `selectedKeys()` returns an accumulating set that the loop is responsible for clearing entries from as they're handled.

### Level 3 — Advanced

```java
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.*;
import java.util.Iterator;

public class SelectorEchoAdvanced {
    public static void main(String[] args) throws Exception {
        Selector selector = Selector.open();
        ServerSocketChannel server = ServerSocketChannel.open();
        server.bind(new InetSocketAddress(0));
        server.configureBlocking(false);
        server.register(selector, SelectionKey.OP_ACCEPT);
        int port = server.socket().getLocalPort();

        new Thread(() -> {
            try (SocketChannel client = SocketChannel.open(new InetSocketAddress("localhost", port))) {
                client.write(ByteBuffer.wrap("hello-server".getBytes()));
                ByteBuffer replyBuf = ByteBuffer.allocate(256);
                client.read(replyBuf);
                replyBuf.flip();
                byte[] reply = new byte[replyBuf.remaining()];
                replyBuf.get(reply);
                System.out.println("Client got echo: " + new String(reply));
            } catch (Exception e) { e.printStackTrace(); }
        }).start();

        long deadline = System.currentTimeMillis() + 3000;
        while (System.currentTimeMillis() < deadline) {
            selector.select(500);
            Iterator<SelectionKey> it = selector.selectedKeys().iterator();
            while (it.hasNext()) {
                SelectionKey key = it.next();
                it.remove();
                try {
                    if (key.isAcceptable()) {
                        SocketChannel client = server.accept();
                        client.configureBlocking(false);
                        client.register(selector, SelectionKey.OP_READ);
                    } else if (key.isReadable()) {
                        SocketChannel client = (SocketChannel) key.channel();
                        ByteBuffer buffer = ByteBuffer.allocate(256);
                        int n = client.read(buffer);
                        if (n == -1) {
                            key.cancel();
                            client.close();
                        } else if (n > 0) {
                            buffer.flip();
                            key.attach(buffer); // stash the data to write back on OP_WRITE
                            key.interestOps(SelectionKey.OP_WRITE);
                        }
                    } else if (key.isWritable()) {
                        SocketChannel client = (SocketChannel) key.channel();
                        ByteBuffer buffer = (ByteBuffer) key.attachment();
                        client.write(buffer);
                        if (!buffer.hasRemaining()) {
                            key.cancel();
                            client.close();
                        }
                    }
                } catch (Exception e) {
                    key.cancel();
                    key.channel().close();
                }
            }
        }
        selector.close();
        server.close();
    }
}
```

**How to run:** `java SelectorEchoAdvanced.java`

This version handles the full read-then-write cycle non-blockingly: after reading a client's data, the key's interest is switched to `OP_WRITE` (via `interestOps`) and the data is attached to the key (`attach`) so it's available when the write-ready event fires — and every branch is wrapped so a single misbehaving connection (which throws an exception) is closed and skipped without crashing the whole selector loop.

## 6. Walkthrough

Execution starts in `main`, which sets up the listening `ServerSocketChannel` registered for `OP_ACCEPT`, then starts a background client thread that connects, writes `"hello-server"`, and waits to read a reply.

The main loop calls `selector.select(500)` repeatedly. On the first iteration where the client's connection attempt has landed, `selectedKeys()` contains a key with `isAcceptable()` true: the server accepts the connection, sets the new `SocketChannel` non-blocking, and registers it for `OP_READ`.

On a later iteration, the client's `client.write(...)` call has delivered `"hello-server"`'s bytes, so the accepted channel's key becomes readable. `key.isReadable()` is true; `client.read(buffer)` reads the bytes into `buffer`, returning `n > 0`. `buffer.flip()` switches it to read-out mode, `key.attach(buffer)` stores this exact buffer on the key (so it can be retrieved later without a separate map), and `key.interestOps(SelectionKey.OP_WRITE)` tells the selector this channel should now be monitored for write-readiness instead of read-readiness.

On a subsequent `select()` call, the same channel's key becomes writable (a socket is nearly always immediately writable once its outbound buffer has room, so this typically fires on the very next iteration). `key.isWritable()` is true; `key.attachment()` retrieves the previously-stashed buffer containing `"hello-server"`, and `client.write(buffer)` writes as many of its remaining bytes as the socket will currently accept. Since `buffer.hasRemaining()` becomes `false` (the whole small message fits in one write), the key is cancelled and the channel closed — this specific connection's lifecycle is complete.

Meanwhile, the client thread's `client.read(replyBuf)` receives those same bytes back, and prints `Client got echo: hello-server`.

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="one connection progresses through accept, read, then write readiness states across successive select() calls, with data attached to the key between the read and write phases">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">select() cycle 1: key.isAcceptable() -&gt; accept() -&gt; register new channel for OP_READ</text>
  <text x="20" y="55" fill="#6db33f" font-size="10">select() cycle 2: key.isReadable() -&gt; read bytes -&gt; attach(buffer) -&gt; interestOps(OP_WRITE)</text>
  <text x="20" y="80" fill="#6db33f" font-size="10">select() cycle 3: key.isWritable() -&gt; attachment() retrieves buffer -&gt; write(buffer) -&gt; done -&gt; close</text>
  <text x="20" y="115" fill="#8b949e" font-size="10">One thread, one Selector, one channel moving through 3 distinct readiness states --</text>
  <text x="20" y="135" fill="#8b949e" font-size="10">no thread was ever blocked waiting on this specific connection at any point.</text>
</svg>

## 7. Gotchas & takeaways

> `selector.selectedKeys()` returns a set that accumulates ready keys and does **not** clear itself automatically — you must explicitly call `iterator.remove()` for each key you process, or already-handled keys will keep reappearing on every subsequent `select()` call.

- Channels must be `configureBlocking(false)` before registering with a `Selector` — blocking-mode channels cannot be registered at all.
- `select()` blocks (optionally with a timeout) until at least one registered channel is ready for one of its registered operations, then returns; it does not itself perform any I/O.
- Use `key.attach(object)`/`key.attachment()` to associate per-connection state (like a partially-read buffer) with a `SelectionKey`, since the selector loop is otherwise stateless between calls.
- Switching `key.interestOps(...)` lets the same channel be monitored for different events (accept, read, write) at different points in its lifecycle, as its processing needs change.
- Non-blocking, selector-based I/O trades simple, sequential blocking code for real complexity (explicit state tracking per connection) — reserve it for genuinely high-concurrency scenarios where thread-per-connection doesn't scale.
