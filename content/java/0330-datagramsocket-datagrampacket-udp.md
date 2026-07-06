---
card: java
gi: 330
slug: datagramsocket-datagrampacket-udp
title: DatagramSocket / DatagramPacket (UDP)
---

## 1. What it is

`DatagramSocket` and `DatagramPacket` are the classes for sending and receiving UDP datagrams — independent, connectionless packets of data with no built-in delivery guarantee, no ordering guarantee, and no automatic retransmission. Unlike `Socket`/`ServerSocket`, there is no handshake and no persistent connection: each `DatagramPacket` is addressed individually (with its own destination host and port) and simply sent into the network, which may deliver it, drop it, or (rarely) deliver it out of order relative to other packets.

```java
import java.net.*;

public class UdpDemo {
    public static void main(String[] args) throws Exception {
        try (DatagramSocket socket = new DatagramSocket()) {
            byte[] data = "hello".getBytes();
            DatagramPacket packet = new DatagramPacket(
                    data, data.length, InetAddress.getByName("localhost"), 9999);
            socket.send(packet);
            System.out.println("Packet sent (fire and forget, no confirmation of delivery).");
        }
    }
}
```

`socket.send(packet)` returns as soon as the local networking stack accepts the packet for transmission — it gives no information about whether the packet actually reached the destination.

## 2. Why & when

TCP's reliability comes at a cost: connection setup, in-order delivery, and retransmission all add latency and overhead. UDP skips all of that, trading reliability for speed and simplicity — appropriate when occasional packet loss is acceptable, or when the application implements its own lightweight reliability on top.

- **Real-time media and gaming** — video/audio streaming and multiplayer game state updates, where a late retransmitted packet is often more harmful than a dropped one (you'd rather skip a frame than pause to wait for it).
- **Simple request/response protocols where loss is tolerable and cheaply retried** — DNS queries are the classic example: if a UDP query gets no response within a timeout, the client just resends it.
- **Broadcast or multicast style communication** — UDP supports sending one packet to multiple recipients (broadcast/multicast addresses) in ways TCP's point-to-point connections cannot.

Because UDP has no ordering or delivery guarantee, any application that needs reliable, ordered delivery on top of UDP (like a custom "reliable UDP" protocol) has to implement acknowledgments, sequence numbers, and retransmission itself — this is real work, which is why TCP remains the default choice unless UDP's lower latency is specifically needed.

## 3. Core concept

```java
import java.net.*;

public class UdpCore {
    public static void main(String[] args) throws Exception {
        DatagramSocket receiver = new DatagramSocket(0); // OS picks a free port
        int port = receiver.getLocalPort();

        new Thread(() -> {
            try (DatagramSocket sender = new DatagramSocket()) {
                byte[] data = "ping".getBytes();
                sender.send(new DatagramPacket(data, data.length, InetAddress.getByName("localhost"), port));
            } catch (Exception e) { e.printStackTrace(); }
        }).start();

        byte[] buffer = new byte[256];
        DatagramPacket received = new DatagramPacket(buffer, buffer.length);
        receiver.receive(received); // blocks until a packet arrives
        String message = new String(received.getData(), 0, received.getLength());
        System.out.println("Received: " + message + " from " + received.getAddress() + ":" + received.getPort());
        receiver.close();
    }
}
```

**How to run:** `java UdpCore.java`

`receiver.receive(received)` blocks until a datagram arrives, then fills in not just the payload bytes but also `getAddress()`/`getPort()`, telling the receiver exactly who sent it — useful since, unlike a `Socket`, a `DatagramSocket` isn't tied to one specific peer.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="UDP sends independent packets with no handshake and no delivery guarantee, unlike TCP's connected, ordered stream">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="52" fill="#79c0ff" font-size="10" text-anchor="middle">Sender</text>

  <text x="185" y="45" fill="#8b949e" font-size="9">packet 1 →</text>
  <text x="185" y="65" fill="#f85149" font-size="9">packet 2 → (lost)</text>
  <text x="185" y="85" fill="#8b949e" font-size="9">packet 3 →</text>

  <rect x="420" y="30" width="150" height="70" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="495" y="52" fill="#6db33f" font-size="10" text-anchor="middle">Receiver</text>
  <text x="495" y="70" fill="#8b949e" font-size="9" text-anchor="middle">gets 1 and 3</text>
  <text x="495" y="85" fill="#8b949e" font-size="9" text-anchor="middle">no error for lost 2</text>

  <text x="20" y="130" fill="#8b949e" font-size="9">No connection setup, no acknowledgment, no automatic retransmission or reordering.</text>
</svg>

## 5. Runnable example

Scenario: a UDP "ping" utility, evolved from a fire-and-forget send with no confirmation, into a version that waits for a reply with a timeout, into a production-style client that retries on timeout and validates the response actually matches the request.

### Level 1 — Basic

```java
import java.net.*;

public class UdpPingBasic {
    public static void main(String[] args) throws Exception {
        DatagramSocket echoServer = startEchoServer();
        int port = echoServer.getLocalPort();

        try (DatagramSocket client = new DatagramSocket()) {
            byte[] data = "ping".getBytes();
            client.send(new DatagramPacket(data, data.length, InetAddress.getByName("localhost"), port));
            System.out.println("Sent ping, no confirmation of delivery or reply requested.");
        }
        Thread.sleep(100);
        echoServer.close();
    }

    static DatagramSocket startEchoServer() throws Exception {
        DatagramSocket server = new DatagramSocket(0);
        new Thread(() -> {
            try {
                byte[] buffer = new byte[256];
                DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                server.receive(packet);
                server.send(new DatagramPacket(packet.getData(), packet.getLength(), packet.getAddress(), packet.getPort()));
            } catch (Exception e) { /* closed or demo error */ }
        }).start();
        return server;
    }
}
```

**How to run:** `java UdpPingBasic.java`

The client fires a single packet and never checks for a reply at all — if the packet is lost, or the server never responds, the client has no way to know, which is exactly the "fire and forget" nature of raw UDP.

### Level 2 — Intermediate

```java
import java.net.*;

public class UdpPingIntermediate {
    public static void main(String[] args) throws Exception {
        DatagramSocket echoServer = startEchoServer();
        int port = echoServer.getLocalPort();

        try (DatagramSocket client = new DatagramSocket()) {
            client.setSoTimeout(1000); // don't wait forever for a reply
            byte[] data = "ping".getBytes();
            client.send(new DatagramPacket(data, data.length, InetAddress.getByName("localhost"), port));

            byte[] buffer = new byte[256];
            DatagramPacket reply = new DatagramPacket(buffer, buffer.length);
            try {
                client.receive(reply);
                System.out.println("Got reply: " + new String(reply.getData(), 0, reply.getLength()));
            } catch (SocketTimeoutException e) {
                System.out.println("No reply within 1 second -- packet or reply may have been lost.");
            }
        }
        echoServer.close();
    }

    static DatagramSocket startEchoServer() throws Exception {
        DatagramSocket server = new DatagramSocket(0);
        new Thread(() -> {
            try {
                byte[] buffer = new byte[256];
                DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                server.receive(packet);
                server.send(new DatagramPacket(packet.getData(), packet.getLength(), packet.getAddress(), packet.getPort()));
            } catch (Exception e) { /* closed or demo error */ }
        }).start();
        return server;
    }
}
```

**How to run:** `java UdpPingIntermediate.java`

`setSoTimeout(1000)` bounds how long `receive()` will block waiting for a reply, and the code now explicitly handles `SocketTimeoutException` as the expected way a UDP exchange can "fail silently" — no reply arriving is treated as a real, anticipated outcome rather than an unhandled hang.

### Level 3 — Advanced

```java
import java.net.*;
import java.util.Arrays;

public class UdpPingAdvanced {
    public static void main(String[] args) throws Exception {
        DatagramSocket echoServer = startEchoServer();
        int port = echoServer.getLocalPort();
        boolean success = pingWithRetry("localhost", port, 3, 500);
        System.out.println("Final result: " + (success ? "reachable" : "unreachable after retries"));
        echoServer.close();
    }

    static boolean pingWithRetry(String host, int port, int maxAttempts, int timeoutMs) throws Exception {
        try (DatagramSocket client = new DatagramSocket()) {
            client.setSoTimeout(timeoutMs);
            InetAddress address = InetAddress.getByName(host);
            for (int attempt = 1; attempt <= maxAttempts; attempt++) {
                byte[] payload = ("ping-" + attempt).getBytes();
                client.send(new DatagramPacket(payload, payload.length, address, port));

                byte[] buffer = new byte[256];
                DatagramPacket reply = new DatagramPacket(buffer, buffer.length);
                try {
                    client.receive(reply);
                    byte[] received = Arrays.copyOf(reply.getData(), reply.getLength());
                    if (Arrays.equals(received, payload)) { // validate it's OUR reply, not a stale one
                        System.out.println("Attempt " + attempt + " confirmed.");
                        return true;
                    } else {
                        System.out.println("Attempt " + attempt + " got mismatched reply, ignoring.");
                    }
                } catch (SocketTimeoutException e) {
                    System.out.println("Attempt " + attempt + " timed out, retrying...");
                }
            }
        }
        return false;
    }

    static DatagramSocket startEchoServer() throws Exception {
        DatagramSocket server = new DatagramSocket(0);
        new Thread(() -> {
            try {
                while (!server.isClosed()) {
                    byte[] buffer = new byte[256];
                    DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                    server.receive(packet);
                    server.send(new DatagramPacket(packet.getData(), packet.getLength(), packet.getAddress(), packet.getPort()));
                }
            } catch (Exception e) { /* closed */ }
        }).start();
        return server;
    }
}
```

**How to run:** `java UdpPingAdvanced.java`

`pingWithRetry` sends a distinctly-tagged payload each attempt (`"ping-1"`, `"ping-2"`, ...), validates that any reply's bytes exactly match what was sent this attempt (guarding against a stale or mismatched reply being mistaken for confirmation), and retries up to `maxAttempts` times on timeout — a minimal but genuine application-level reliability layer built on top of unreliable UDP.

## 6. Walkthrough

Execution starts in `main`, which starts `echoServer` (a background thread looping on `receive`/`send`) and calls `pingWithRetry("localhost", port, 3, 500)`.

Inside `pingWithRetry`, attempt 1 builds the payload bytes for `"ping-1"` and sends them via `client.send(...)` to the server's port. On the server thread, `server.receive(packet)` unblocks, capturing the payload bytes plus the sender's address and port (recorded automatically in the `DatagramPacket`); the server immediately sends those same bytes back to `packet.getAddress()`/`packet.getPort()` — i.e., back to the client, on the port the client's `DatagramSocket` is using.

Back in the client, `client.receive(reply)` (bounded by the 500ms `setSoTimeout`) unblocks once that reply arrives, and the code copies exactly `reply.getLength()` bytes out of the reply buffer with `Arrays.copyOf` (since a datagram's buffer may be larger than the actual data received). `Arrays.equals(received, payload)` confirms the reply exactly matches what was sent this attempt, so the method prints `"Attempt 1 confirmed."` and returns `true` immediately — no further attempts are needed.

`main` prints `Final result: reachable`, then closes `echoServer`. If the network had dropped either the request or the reply (not simulated here, since this all runs over the loopback interface which essentially never drops packets), `client.receive` would instead throw `SocketTimeoutException` after 500ms, the loop would print a retry message, and attempt 2 would resend a freshly-tagged `"ping-2"` payload — up to `maxAttempts` times before giving up and returning `false`.

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="client sends tagged ping payload, server echoes it back with sender address recorded, client validates the reply matches before confirming">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">1. client.send(DatagramPacket("ping-1", address, port))</text>
  <text x="20" y="55" fill="#6db33f" font-size="10">2. server.receive() unblocks -- captures payload + sender address/port</text>
  <text x="20" y="80" fill="#6db33f" font-size="10">3. server.send(same bytes, back to captured sender address/port)</text>
  <text x="20" y="105" fill="#79c0ff" font-size="10">4. client.receive() unblocks within 500ms timeout window</text>
  <text x="20" y="130" fill="#e6edf3" font-size="10">5. bytes compared to what was sent -- match confirms, mismatch ignored</text>
  <text x="20" y="150" fill="#8b949e" font-size="10">timeout instead of step 4 -&gt; retry with a freshly-tagged payload</text>
</svg>

## 7. Gotchas & takeaways

> `receive()`'s buffer must be sized generously in advance — UDP has no concept of "read what's available"; if the incoming datagram is larger than the buffer, the excess bytes are silently discarded, not queued for a subsequent read.

- UDP has no connection, no ordering guarantee, and no automatic retransmission — `send()` returning successfully only means the local stack accepted the packet, not that it arrived.
- Always set `setSoTimeout()` on a `DatagramSocket` used for request/response patterns — otherwise `receive()` can block forever if a reply never comes.
- A `DatagramPacket` used for receiving records the sender's address and port automatically — useful for replying to whoever sent it, since a `DatagramSocket` (unlike a `Socket`) isn't bound to one specific peer.
- Validate reply contents when correctness matters — a UDP socket can, in principle, receive a packet from any sender on the network, not just the one you expect, so checking that a reply matches what was requested is real defensive practice, not paranoia.
- Choose UDP deliberately for latency-sensitive or loss-tolerant use cases; if you find yourself building acknowledgments, sequencing, and retransmission on top of it, ask whether TCP already solves that problem for you.
