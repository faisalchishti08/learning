---
card: spring-integration
gi: 53
slug: tcp-udp-support
title: "TCP & UDP support"
---

## 1. What it is

Spring Integration's TCP/UDP support provides adapters for raw socket-level communication — `TcpInboundGateway`/`TcpOutboundGateway` for connection-oriented, reliable, ordered TCP exchanges (typically request/reply), and `TcpInboundChannelAdapter`/`TcpOutboundChannelAdapter` for one-way TCP messaging, plus `UnicastReceivingChannelAdapter`/`UnicastSendingMessageHandler` for connectionless UDP. Both sit one level below the higher-level, structured protocols (HTTP, card 0054; JMS, card 0057) covered elsewhere in this section — TCP/UDP support is for when a flow needs to speak directly at the socket level, often to integrate with custom or legacy protocols that don't fit any higher-level abstraction.

## 2. Why & when

You reach for TCP/UDP support specifically when the integration point is a raw socket protocol rather than something already wrapped in HTTP, JMS, or another structured messaging layer:

- **You're integrating with a legacy system or custom protocol that communicates over raw TCP** — many older financial, industrial, and telecom systems expose fixed-format or custom-delimited TCP protocols with no HTTP or message-broker layer at all; TCP support lets a flow speak that protocol directly.
- **Low-latency, connection-persistent communication matters** — a TCP connection, once established, avoids the overhead of repeated connection setup that a request-per-HTTP-call pattern would incur, useful for high-frequency, low-latency exchanges between two systems.
- **UDP's connectionless, best-effort delivery model fits the use case** — telemetry, certain real-time data feeds, or broadcast-style updates where occasional message loss is acceptable in exchange for lower overhead and no connection-management cost — `UnicastReceivingChannelAdapter`/`UnicastSendingMessageHandler` handle that model directly.

## 3. Core concept

Think of TCP like a phone call: a connection is established once, both sides stay connected for the duration, and every word spoken arrives in order, exactly as spoken — reliable, but with real setup and teardown cost for each call. UDP is more like a sequence of postcards: quick and cheap to send, with no ongoing connection, no delivery guarantee, and no ordering guarantee across multiple postcards — fine for a quick weather update, unacceptable for a legally binding contract that needs guaranteed, ordered delivery.

```java
@Bean
public TcpNetServerConnectionFactory serverConnectionFactory() {
    TcpNetServerConnectionFactory factory = new TcpNetServerConnectionFactory(9999);
    factory.setSerializer(new ByteArrayCrLfSerializer());   // defines message BOUNDARIES on the raw byte stream
    factory.setDeserializer(new ByteArrayCrLfSerializer());
    return factory;
}

@Bean
public TcpInboundGateway tcpInboundGateway(TcpNetServerConnectionFactory serverConnectionFactory) {
    TcpInboundGateway gateway = new TcpInboundGateway();
    gateway.setConnectionFactory(serverConnectionFactory);
    gateway.setRequestChannelName("tcpRequests");
    return gateway;
}
```

A raw TCP byte stream has no inherent concept of "one message" — the `Serializer`/`Deserializer` pair is what defines message boundaries (a delimiter like CRLF, a length-prefix header, or a custom format), turning a continuous byte stream into discrete messages the rest of the flow can work with.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="TCP: a persistent connection carries an ordered, reliable stream of delimited messages between client and server. UDP: independent, connectionless datagrams sent without ordering or delivery guarantees.">
  <text x="150" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">TCP (connection-oriented)</text>
  <rect x="20" y="35" width="110" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">client</text>
  <line x1="130" y1="55" x2="230" y2="55" stroke="#6db33f" stroke-width="2" marker-end="url(#tu1)" marker-start="url(#tu2)"/>
  <text x="180" y="42" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">persistent, ordered</text>
  <rect x="240" y="35" width="110" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="295" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">server</text>

  <text x="500" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">UDP (connectionless)</text>
  <rect x="410" y="35" width="110" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="465" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">sender</text>
  <line x1="520" y1="45" x2="590" y2="45" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#tu3)"/>
  <line x1="520" y1="65" x2="590" y2="65" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#tu3)"/>
  <text x="555" y="35" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">independent datagrams</text>
  <rect x="600" y="35" width="30" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="615" y="59" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">rx</text>

  <text x="320" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Serializer/Deserializer define MESSAGE BOUNDARIES on the raw byte stream</text>

  <defs>
    <marker id="tu1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="tu2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M7,0 L0,3 L7,6 Z" fill="#6db33f"/></marker>
    <marker id="tu3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

TCP's persistent, ordered connection versus UDP's independent, connectionless datagrams — a fundamental reliability/overhead tradeoff.

## 5. Runnable example

The scenario: a raw TCP request/reply exchange and a UDP one-way send, using real local sockets (genuinely runnable, since both endpoints are on `localhost`), starting with a basic TCP echo exchange, then message-boundary handling for multiple messages on one connection, and finally UDP's best-effort, connectionless send.

### Level 1 — Basic

```java
// BasicTcpEchoDemo.java
// Uses REAL local TCP sockets — this genuinely runs end to end, since both the "server" and "client"
// are simple java.net socket code running on localhost, no external server needed.
import java.io.*;
import java.net.*;

public class BasicTcpEchoDemo {
    public static void main(String[] args) throws Exception {
        ServerSocket serverSocket = new ServerSocket(0); // port 0 = pick any free port
        int port = serverSocket.getLocalPort();

        Thread server = new Thread(() -> {
            try (Socket client = serverSocket.accept();
                 BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
                 PrintWriter out = new PrintWriter(client.getOutputStream(), true)) {
                String request = in.readLine(); // ONE line = ONE message (the delimiter defines the boundary)
                System.out.println("[server] received: " + request);
                out.println("ECHO: " + request); // reply
            } catch (IOException ignored) {}
        });
        server.start();

        try (Socket clientSocket = new Socket("localhost", port);
             PrintWriter out = new PrintWriter(clientSocket.getOutputStream(), true);
             BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()))) {
            out.println("hello-tcp-server"); // send request
            String reply = in.readLine();     // block for reply
            System.out.println("[client] received reply: " + reply);
        }
        server.join();
    }
}
```

How to run: `java BasicTcpEchoDemo.java`. Expected output: `[server] received: hello-tcp-server` then `[client] received reply: ECHO: hello-tcp-server` — a genuine TCP connection, established over `localhost`, carried a request and its correlated reply, exactly the request/reply exchange a real `TcpInboundGateway`/`TcpOutboundGateway` pair would perform, just without Spring Integration's own wiring around it.

### Level 2 — Intermediate

A single persistent TCP connection carrying multiple distinct messages, each delimited by a newline — demonstrating that message boundaries on a raw byte stream must be explicitly defined (here, by reading line by line), since TCP itself has no inherent concept of "one message" versus "part of a larger message."

```java
// MultiMessageTcpConnectionDemo.java
import java.io.*;
import java.net.*;

public class MultiMessageTcpConnectionDemo {
    public static void main(String[] args) throws Exception {
        ServerSocket serverSocket = new ServerSocket(0);
        int port = serverSocket.getLocalPort();

        Thread server = new Thread(() -> {
            try (Socket client = serverSocket.accept();
                 BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
                 PrintWriter out = new PrintWriter(client.getOutputStream(), true)) {
                String line;
                while ((line = in.readLine()) != null) { // each readLine() call = one delimited MESSAGE
                    System.out.println("[server] message boundary found: " + line);
                    out.println("ACK: " + line);
                }
            } catch (IOException ignored) {}
        });
        server.start();

        try (Socket clientSocket = new Socket("localhost", port);
             PrintWriter out = new PrintWriter(clientSocket.getOutputStream(), true);
             BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()))) {
            for (String msg : new String[]{"order-1", "order-2", "order-3"}) {
                out.println(msg); // SAME connection, THREE separate messages
                System.out.println("[client] ack received: " + in.readLine());
            }
        }
        Thread.sleep(100);
    }
}
```

How to run: `java MultiMessageTcpConnectionDemo.java`. Expected output: three `[server] message boundary found: order-N` / `[client] ack received: ACK: order-N` pairs — all three messages traveled over the *same* TCP connection (no reconnection between them), each correctly recognized as a separate message purely because of the newline delimiter each `println` added, exactly what a configured `ByteArrayCrLfSerializer`/`Deserializer` pair does for a real `TcpNetServerConnectionFactory`.

### Level 3 — Advanced

A UDP send: connectionless, best-effort, no reply expected by the transport itself (any "reply" would need to be its own separate, independent UDP datagram) — using real `DatagramSocket`s locally to show the fundamentally different delivery model from TCP's connection-oriented reliability.

```java
// UdpDatagramDemo.java
import java.net.*;
import java.nio.charset.StandardCharsets;

public class UdpDatagramDemo {
    public static void main(String[] args) throws Exception {
        DatagramSocket receiverSocket = new DatagramSocket(0);
        int port = receiverSocket.getLocalPort();

        Thread receiver = new Thread(() -> {
            byte[] buffer = new byte[1024];
            try {
                DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                receiverSocket.receive(packet); // waits for ONE independent datagram — no connection setup at all
                String received = new String(packet.getData(), 0, packet.getLength(), StandardCharsets.UTF_8);
                System.out.println("[UDP receiver] got datagram: " + received);
            } catch (Exception ignored) {}
        });
        receiver.start();
        Thread.sleep(100); // give the receiver a moment to start listening

        try (DatagramSocket senderSocket = new DatagramSocket()) {
            byte[] payload = "telemetry-reading-42".getBytes(StandardCharsets.UTF_8);
            DatagramPacket packet = new DatagramPacket(payload, payload.length,
                InetAddress.getLoopbackAddress(), port);
            senderSocket.send(packet); // fire-and-forget: NO connection, NO delivery confirmation from the transport
            System.out.println("[UDP sender] datagram sent — no acknowledgment expected or received from UDP itself");
        }
        receiver.join();
    }
}
```

How to run: `java UdpDatagramDemo.java`. Expected output: `[UDP sender] datagram sent — no acknowledgment expected or received from UDP itself` followed by `[UDP receiver] got datagram: telemetry-reading-42` — the send completed instantly with no handshake or connection setup, and (in this local, reliable scenario) the datagram did arrive, but nothing about UDP itself guaranteed that; a real network with packet loss could have dropped it silently, with neither side automatically aware.

## 6. Walkthrough

Tracing `MultiMessageTcpConnectionDemo` in execution order:

1. The client establishes one TCP connection via `new Socket("localhost", port)` — this connection setup (the TCP three-way handshake, happening beneath the Java socket API) occurs exactly once, before any messages are sent.
2. The client's `for` loop sends three separate `println` calls over that *same* connection's output stream — each call writes bytes followed by a newline character onto the underlying TCP byte stream, but from TCP's own perspective, this is just a continuous stream of bytes with no inherent "message" boundaries at all.
3. On the server side, `in.readLine()` is what actually imposes message boundaries onto that raw byte stream — it reads bytes until it encounters a newline, treating everything up to that point as one complete message, then returns control so the next `readLine()` call can find the next one.
4. For each message the server reads, it immediately writes back an acknowledgment (also newline-terminated) on the same connection, and the client's own `in.readLine()` call (blocked waiting) picks that up as the correlated reply for that specific message.
5. This send-then-block-for-reply pattern repeats for all three messages, all multiplexed over the one persistent connection — no new connection handshake occurs between messages two and three, which is exactly the connection-reuse efficiency TCP-based integration is often chosen for over a fresh-connection-per-request model.
6. In a real Spring Integration TCP setup, `ByteArrayCrLfSerializer`/`Deserializer` (or another configured serializer, like a length-header-based one) performs exactly this same delimiting role automatically — the manual `readLine()`/`println()` pairing here stands in for what that configured serializer pair handles behind the scenes.

```
client connects (ONE TCP handshake)
  send "order-1\n" -> server readLine() -> "order-1" -> reply "ACK: order-1\n" -> client readLine()
  send "order-2\n" -> server readLine() -> "order-2" -> reply "ACK: order-2\n" -> client readLine()
  send "order-3\n" -> server readLine() -> "order-3" -> reply "ACK: order-3\n" -> client readLine()
  (SAME connection reused for all three round trips)
```

## 7. Gotchas & takeaways

> UDP's lack of delivery guarantee means a `UnicastSendingMessageHandler`'s `send()` call returning successfully only confirms the datagram left the local machine — it says absolutely nothing about whether it actually arrived. Any flow relying on UDP for anything where message loss matters needs its own application-level acknowledgment/retry logic built on top (the receiving side explicitly confirming receipt via its own separate reply datagram); never assume UDP delivery succeeded just because the send call didn't throw an exception.

- Spring Integration's TCP support (`TcpInboundGateway`/`TcpOutboundGateway` for request/reply, `TcpInboundChannelAdapter`/`TcpOutboundChannelAdapter` for one-way) provides connection-oriented, reliable, ordered socket communication; UDP support (`UnicastReceivingChannelAdapter`/`UnicastSendingMessageHandler`) provides connectionless, best-effort datagram communication.
- Use TCP/UDP support for raw socket-level integration with legacy or custom protocols that don't fit HTTP, JMS, or another higher-level structured protocol.
- A `Serializer`/`Deserializer` pair is what defines message boundaries on TCP's otherwise-continuous byte stream (a delimiter, a length header, or a custom format) — TCP itself has no inherent concept of discrete messages.
- A single TCP connection can carry many sequential messages, reused across requests, avoiding the connection-setup overhead of a fresh connection per exchange.
- UDP trades reliability for low overhead — a successful `send()` call only confirms local transmission, never delivery; any use case where loss matters needs application-level acknowledgment built on top.
