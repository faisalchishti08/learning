---
card: java
gi: 978
slug: selectors-event-loops
title: Selectors & event loops
---

## 1. What it is

A `Selector` (part of Java NIO, `java.nio.channels.Selector`) lets a single thread monitor multiple channels (typically network sockets) simultaneously, asking the operating system "tell me which of these channels are actually ready for an operation (accepting a connection, reading, writing) right now," rather than dedicating one thread per connection and having each thread block waiting on its own single channel. A channel registers with a selector for specific interest operations (`OP_ACCEPT`, `OP_READ`, `OP_WRITE`) via `SelectableChannel.register(selector, ops)`, producing a `SelectionKey` that tracks that registration; calling `selector.select()` blocks until at least one registered channel becomes ready for one of its interested operations, at which point it returns, and the application inspects `selector.selectedKeys()` to find out which channels need attention and handles each one in turn — this loop (select, inspect ready keys, handle each, repeat) is exactly what's meant by an "event loop."

## 2. Why & when

This model matters because the traditional one-thread-per-connection approach to network servers doesn't scale well to a very large number of simultaneous connections — each thread consumes a full OS thread stack's worth of memory (historically a real constraint, though [virtual threads](0900-virtual-threads-model-loom.md) have substantially changed this specific tradeoff in recent Java versions) and incurs real context-switching overhead as the OS scheduler juggles many threads, most of which are simply blocked waiting for I/O most of the time. A selector-based event loop instead uses one (or a small, fixed number of) threads to efficiently monitor potentially thousands of connections at once, doing actual work only when the OS reports a specific channel is genuinely ready, which is the same fundamental architecture underlying high-performance servers and frameworks (Netty, Node.js's event loop, and Java's own internal NIO-based server implementations) built to handle very high connection counts efficiently. The tradeoff: event-loop-based code is structurally more complex than straightforward blocking, one-thread-per-connection code — instead of writing linear "read this, process it, write a response" logic in one place, you must structure your handling around discrete "here's a ready event, handle it, return control to the loop" callbacks, since a single event-loop thread must never block for long inside any one channel's handling, or it would stall every other channel it's simultaneously responsible for.

## 3. Core concept

```java
Selector selector = Selector.open();
serverChannel.register(selector, SelectionKey.OP_ACCEPT);

while (true) {
    selector.select();  // BLOCKS until at least one registered channel is ready

    Iterator<SelectionKey> it = selector.selectedKeys().iterator();
    while (it.hasNext()) {
        SelectionKey key = it.next();
        it.remove(); // MUST remove -- selectedKeys() does not clear itself automatically

        if (key.isAcceptable()) {
            // a new connection is ready to be accepted
        } else if (key.isReadable()) {
            // this channel has data ready to be read WITHOUT blocking
        } else if (key.isWritable()) {
            // this channel is ready to accept more written data WITHOUT blocking
        }
    }
}
```

The critical, easy-to-miss detail: `selector.selectedKeys()` returns a *live* set that keeps accumulating ready keys across calls unless you explicitly remove each key from it after handling — forgetting `it.remove()` causes already-handled keys to be processed repeatedly on every subsequent loop iteration.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One selector thread monitoring several registered channels, blocking on select until any become ready, then dispatching to a small handler for each ready channel in turn" >
  <rect x="20" y="60" width="140" height="60" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="85" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Selector</text>
  <text x="90" y="102" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ONE thread, blocking select()</text>

  <rect x="220" y="20" width="90" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="265" y="39" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Channel A</text>
  <rect x="220" y="70" width="90" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="265" y="89" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Channel B</text>
  <rect x="220" y="120" width="90" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="265" y="139" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Channel C</text>

  <line x1="160" y1="90" x2="220" y2="35" stroke="#8b949e"/>
  <line x1="160" y1="90" x2="220" y2="85" stroke="#8b949e"/>
  <line x1="160" y1="90" x2="220" y2="135" stroke="#8b949e"/>

  <rect x="440" y="70" width="180" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="530" y="89" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">only Channel B is READY</text>
  <line x1="310" y1="85" x2="440" y2="85" stroke="#f0883e" marker-end="url(#a)"/>

  <text x="320" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">select() returns; only ready channels are handled, no blocking on the others</text>
</svg>

*One selector thread monitors many channels simultaneously, waking only when at least one channel is genuinely ready, and handling only that channel.*

## 5. Runnable example

Scenario: build a small single-threaded echo server using a selector-based event loop, evolving from a basic accept-and-echo server handling one connection at a time conceptually, to a realistic multi-connection version demonstrating the selector's core value, to a more advanced case correctly handling partial reads and writes without blocking the event loop.

### Level 1 — Basic

```java
import java.io.*;
import java.net.*;
import java.nio.*;
import java.nio.channels.*;
import java.util.*;

public class SelectorBasicEcho {
    public static void main(String[] args) throws IOException {
        ServerSocketChannel serverChannel = ServerSocketChannel.open();
        serverChannel.bind(new InetSocketAddress("localhost", 0));
        serverChannel.configureBlocking(false);
        int port = serverChannel.socket().getLocalPort();
        System.out.println("listening on port " + port);

        Selector selector = Selector.open();
        serverChannel.register(selector, SelectionKey.OP_ACCEPT);

        // Simulate a client connecting and sending one message, then exit after handling it.
        new Thread(() -> {
            try (Socket client = new Socket("localhost", port)) {
                client.getOutputStream().write("hello\n".getBytes());
                byte[] response = new byte[64];
                int n = client.getInputStream().read(response);
                System.out.println("client received: " + new String(response, 0, n).trim());
            } catch (IOException e) { e.printStackTrace(); }
        }).start();

        int handled = 0;
        while (handled < 1) {
            selector.select();
            Iterator<SelectionKey> it = selector.selectedKeys().iterator();
            while (it.hasNext()) {
                SelectionKey key = it.next();
                it.remove();
                if (key.isAcceptable()) {
                    SocketChannel client = serverChannel.accept();
                    client.configureBlocking(false);
                    client.register(selector, SelectionKey.OP_READ);
                } else if (key.isReadable()) {
                    SocketChannel client = (SocketChannel) key.channel();
                    ByteBuffer buf = ByteBuffer.allocate(64);
                    int n = client.read(buf);
                    buf.flip();
                    client.write(buf); // echo back what was read
                    handled++;
                }
            }
        }
        serverChannel.close();
    }
}
```

**How to run:** `java SelectorBasicEcho.java` (JDK 17+).

Expected output shape (order between the two threads' prints may vary slightly):
```
listening on port 54321
client received: hello
```

The single event-loop thread registers the server channel for `OP_ACCEPT`, and upon a connection, registers the new client channel for `OP_READ` — when `select()` reports the client channel is readable, the loop reads its data and echoes it straight back, all without ever dedicating a separate thread to this one connection.

### Level 2 — Intermediate

```java
import java.io.*;
import java.net.*;
import java.nio.*;
import java.nio.channels.*;
import java.util.*;

public class SelectorMultiConnection {
    public static void main(String[] args) throws IOException, InterruptedException {
        ServerSocketChannel serverChannel = ServerSocketChannel.open();
        serverChannel.bind(new InetSocketAddress("localhost", 0));
        serverChannel.configureBlocking(false);
        int port = serverChannel.socket().getLocalPort();

        Selector selector = Selector.open();
        serverChannel.register(selector, SelectionKey.OP_ACCEPT);

        int clientCount = 3;
        for (int i = 0; i < clientCount; i++) {
            final int id = i;
            new Thread(() -> {
                try (Socket client = new Socket("localhost", port)) {
                    client.getOutputStream().write(("msg-from-client-" + id + "\n").getBytes());
                    byte[] response = new byte[64];
                    int n = client.getInputStream().read(response);
                    System.out.println("client " + id + " received: " + new String(response, 0, n).trim());
                } catch (IOException e) { e.printStackTrace(); }
            }).start();
        }

        int handled = 0;
        while (handled < clientCount) {
            selector.select();
            Iterator<SelectionKey> it = selector.selectedKeys().iterator();
            while (it.hasNext()) {
                SelectionKey key = it.next();
                it.remove();
                if (key.isAcceptable()) {
                    SocketChannel client = serverChannel.accept();
                    client.configureBlocking(false);
                    client.register(selector, SelectionKey.OP_READ);
                } else if (key.isReadable()) {
                    SocketChannel client = (SocketChannel) key.channel();
                    ByteBuffer buf = ByteBuffer.allocate(64);
                    int n = client.read(buf);
                    buf.flip();
                    client.write(buf);
                    handled++;
                }
            }
        }
        serverChannel.close();
        Thread.sleep(100);
    }
}
```

**How to run:** `java SelectorMultiConnection.java` (JDK 17+).

Expected output shape (order between client threads may vary):
```
client 0 received: msg-from-client-0
client 1 received: msg-from-client-1
client 2 received: msg-from-client-2
```

The real-world concern added: three separate client connections are handled by a single selector loop running on one thread — as each client connects and sends its message at its own pace, `select()` wakes exactly when a specific channel becomes ready (either a new connection to accept, or data to read from an already-connected client), and the loop dispatches to the right handling logic for whichever channel triggered that wakeup, demonstrating the core scalability benefit: one thread genuinely servicing multiple independent connections concurrently.

### Level 3 — Advanced

```java
import java.io.*;
import java.net.*;
import java.nio.*;
import java.nio.channels.*;
import java.util.*;

public class SelectorPartialReadWrite {
    public static void main(String[] args) throws IOException, InterruptedException {
        ServerSocketChannel serverChannel = ServerSocketChannel.open();
        serverChannel.bind(new InetSocketAddress("localhost", 0));
        serverChannel.configureBlocking(false);
        int port = serverChannel.socket().getLocalPort();

        Selector selector = Selector.open();
        serverChannel.register(selector, SelectionKey.OP_ACCEPT);

        new Thread(() -> {
            try (Socket client = new Socket("localhost", port)) {
                String bigMessage = "X".repeat(5000) + "\n"; // large enough to potentially need multiple reads
                client.getOutputStream().write(bigMessage.getBytes());
                InputStream in = client.getInputStream();
                ByteArrayOutputStream received = new ByteArrayOutputStream();
                byte[] chunk = new byte[256];
                int n;
                while ((n = in.read(chunk)) != -1 && received.size() < bigMessage.length()) {
                    received.write(chunk, 0, n);
                }
                System.out.println("client received total bytes: " + received.size());
            } catch (IOException e) { e.printStackTrace(); }
        }).start();

        Map<SocketChannel, ByteArrayOutputStream> buffers = new HashMap<>();
        int handled = 0;
        while (handled < 1) {
            selector.select();
            Iterator<SelectionKey> it = selector.selectedKeys().iterator();
            while (it.hasNext()) {
                SelectionKey key = it.next();
                it.remove();
                if (key.isAcceptable()) {
                    SocketChannel client = serverChannel.accept();
                    client.configureBlocking(false);
                    client.register(selector, SelectionKey.OP_READ);
                    buffers.put(client, new ByteArrayOutputStream());
                } else if (key.isReadable()) {
                    SocketChannel client = (SocketChannel) key.channel();
                    ByteBuffer buf = ByteBuffer.allocate(1024);
                    int n = client.read(buf); // may return LESS than the full message -- NEVER blocks
                    if (n > 0) {
                        buf.flip();
                        buffers.get(client).write(buf.array(), 0, buf.remaining());
                    }
                    if (n == -1 || buffers.get(client).toString().endsWith("\n")) {
                        byte[] fullMessage = buffers.get(client).toByteArray();
                        client.write(ByteBuffer.wrap(fullMessage)); // echo everything back
                        handled++;
                    }
                }
            }
        }
        serverChannel.close();
        Thread.sleep(100);
    }
}
```

**How to run:** `java SelectorPartialReadWrite.java` (JDK 17+).

Expected output shape:
```
client received total bytes: 5001
```

The production-flavored hard case: a single `channel.read()` call is never guaranteed to return the entire message at once — the OS may deliver data in whatever chunks happen to arrive over the network, and a non-blocking read simply returns however many bytes are currently available (possibly zero, possibly the whole message, possibly a partial chunk), so this handler accumulates received bytes across potentially several separate `OP_READ` events for the *same* channel into a per-channel buffer (tracked in the `buffers` map, keyed by channel), only treating the message as complete once a terminating newline has actually been received — this is exactly the kind of complexity a real, robust event-loop-based server must correctly handle, since a naive single-read-equals-whole-message assumption would silently corrupt or truncate any message that happens to arrive in more than one network packet.

## 6. Walkthrough

Tracing the selector-based handling of one client's message in `SelectorPartialReadWrite.main`, focusing on the possibility of a partial read:

1. When the client connects, `key.isAcceptable()` is true for the server channel's `SelectionKey`; the server accepts the new connection, configures the resulting `SocketChannel` as non-blocking, registers it for `OP_READ` with the same selector, and creates a fresh, empty `ByteArrayOutputStream` for it in the `buffers` map — this per-channel buffer is what accumulates partial data across potentially multiple read events.
2. As the client sends its 5001-byte message, the underlying OS network stack may deliver it to the server in one or several separate chunks, depending on network conditions entirely outside the application's control — each time at least one byte becomes available to read on this channel, `select()` wakes with this channel's key marked readable.
3. On each such wakeup, `client.read(buf)` is called — since the channel is non-blocking, this call returns immediately with however many bytes are currently available (which could be anywhere from 1 byte up to the full 5001, or even 0 if the channel was marked readable for a different reason, like the remote side closing the connection), never blocking to wait for more.
4. Whatever bytes were read in this particular call are appended to that channel's accumulator in the `buffers` map — critically, this is *added to* the existing accumulated data from any prior reads of this same channel, not replacing it, which is exactly what correctly reassembles a message that arrived across multiple separate reads.
5. After each read, the code checks whether the accumulated data so far ends with the message's terminating newline character — only once it does (meaning the *complete* message has now been received, however many separate reads it took to arrive) does the handler consider the message finished, write the complete accumulated bytes back to the client as an echo, and increment `handled` to eventually let the main loop terminate.
6. If the accumulated data does not yet end with a newline (meaning only a partial message has arrived so far), the loop simply continues — `select()` is called again, and if more data later becomes available on this same channel, the exact same read-and-accumulate process repeats, correctly building up the complete message over however many separate `OP_READ` events it actually takes, rather than incorrectly assuming a single `read` call always delivers an entire logical message.

## 7. Gotchas & takeaways

> **Gotcha:** forgetting to call `it.remove()` after handling each `SelectionKey` inside the `selectedKeys()` iteration is one of the single most common and confusing selector-based bugs — the selected-keys set does not clear itself automatically between `select()` calls, so a key left unremoved will be processed again on every subsequent loop iteration, typically causing already-handled events to be handled repeatedly (often manifesting as duplicate reads, duplicate writes, or a loop that never seems to make forward progress correctly).

- A `Selector` lets one thread monitor multiple registered channels simultaneously, blocking in `select()` only until at least one channel becomes genuinely ready for an operation it's interested in.
- The event-loop pattern — select, iterate ready keys, handle each, repeat — lets a small, fixed number of threads efficiently service potentially thousands of connections, avoiding the memory and context-switching overhead of a traditional one-thread-per-connection model.
- `selector.selectedKeys()` returns a live set that accumulates across calls — you must explicitly call `it.remove()` after handling each key, or already-handled keys will be reprocessed on every subsequent loop iteration.
- A non-blocking `read()` call on a ready channel is never guaranteed to return an entire logical message at once — robust event-loop code must accumulate partial reads across potentially multiple `OP_READ` events per channel, tracking each channel's own accumulation state separately.
- Because a single event-loop thread services every registered channel, handler logic must never block for long inside any one channel's handling, or it stalls every other channel that same thread is responsible for.
- See [backpressure](0975-backpressure.md) for a related concern in asynchronous data processing, and [direct vs heap ByteBuffers](0977-direct-vs-heap-bytebuffers.md) for the buffer types typically used alongside selector-based channel I/O.
