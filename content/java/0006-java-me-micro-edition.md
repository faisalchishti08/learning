---
card: java
gi: 6
slug: java-me-micro-edition
title: Java ME (Micro Edition)
---

## 1. What it is

**Java ME (Micro Edition)** is a stripped-down version of the Java platform designed for resource-constrained devices: mobile phones, PDAs, set-top boxes, embedded controllers, and IoT sensors. It provides a subset of Java SE APIs, a smaller JVM (KVM or CLDC VM), and a set of optional packages targeting specific device categories.

Java ME is not one thing but a family of configurations and profiles:
- **CLDC** (Connected Limited Device Configuration) — for the smallest devices (8–512 KB RAM).
- **CDC** (Connected Device Configuration) — for more capable devices (1+ MB RAM).
- **MIDP** (Mobile Information Device Profile) — the UI/networking profile for CLDC phones.
- **Java Card** — an even more stripped-down variant for SIM cards and smartcards.

## 2. Why & when

From roughly 2000–2012, Java ME was the dominant way to write mobile applications. "J2ME" apps ran on billions of Nokia, Sony Ericsson, and Samsung feature phones before the smartphone era. The game industry shipped casual games (Snake variants, Tetris clones) as MIDlets.

Java ME's relevance today:
- **Legacy maintenance** — enterprises with J2ME point-of-sale terminals, payment kiosks, and industrial devices still run Java ME code.
- **Java Card** — still very active; billions of SIM cards, bank cards, and passports run Java Card applets.
- **Historical context** — understanding Java ME explains why Android chose a Dalvik VM (not Java ME) and why Android's early API looked the way it did.
- **Embedded IoT** — Oracle Java ME Embedded still targets microcontrollers; though Raspberry Pi users typically use full Java SE.

For new projects, Java ME proper has largely been displaced by Android (for phones) and full Java SE on capable embedded hardware (Raspberry Pi). But Java Card remains dominant in secure element contexts.

## 3. Core concept

Java ME achieves size reduction through **configurations** and **profiles**:

```
Java SE (full JVM + full library)
      │
      │ stripped down
      ▼
Java ME
  ├── CLDC (smallest JVM, ~50 KB)
  │     └── MIDP (mobile UI + networking profile)
  │
  ├── CDC (larger JVM, subset of SE)
  │     └── Foundation Profile / Personal Profile
  │
  └── Java Card (smartcard VM, ~100 bytes RAM)
```

Key differences from Java SE:
| Feature | Java SE | Java ME CLDC |
|---|---|---|
| Floating point | Full `double`/`float` | Optional (CLDC 1.0: none; CLDC 1.1: optional) |
| Reflection | Full | None (CLDC 1.0), limited (CLDC 1.1) |
| Class loading | Full | Restricted (no custom class loaders) |
| Finalizers | Present | Absent |
| Threading | `java.lang.Thread` | Subset (no `ThreadGroup`) |
| I/O | `java.io`, `java.nio` | `javax.microedition.io` Generic Connection Framework |

The key abstraction is the **Generic Connection Framework (GCF)**: all I/O (sockets, HTTP, serial, datagram) goes through a single `Connector.open(url)` call, returning a typed `Connection`. This unified interface keeps the footprint tiny.

## 4. Diagram

<svg viewBox="0 0 640 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java ME family: CLDC, CDC, Java Card as subsets of Java SE">
  <!-- Java SE background -->
  <rect x="30" y="20" width="580" height="190" rx="12" fill="#0d1117" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="6,3"/>
  <text x="320" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Java SE (full platform)</text>

  <!-- Java ME band -->
  <rect x="60" y="60" width="520" height="130" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="80" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java ME (subset of SE APIs)</text>

  <!-- CLDC -->
  <rect x="80"  y="95" width="150" height="80" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="155" y="117" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">CLDC</text>
  <text x="155" y="133" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">8–512 KB RAM</text>
  <text x="155" y="147" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">feature phones</text>
  <text x="155" y="161" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">+ MIDP profile</text>

  <!-- CDC -->
  <rect x="255" y="95" width="150" height="80" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="117" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">CDC</text>
  <text x="330" y="133" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">1+ MB RAM</text>
  <text x="330" y="147" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">set-top boxes</text>
  <text x="330" y="161" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">+ Foundation Profile</text>

  <!-- Java Card -->
  <rect x="430" y="95" width="130" height="80" rx="8" fill="#0d1117" stroke="#f85149" stroke-width="1.5"/>
  <text x="495" y="117" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Java Card</text>
  <text x="495" y="133" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">~100 bytes RAM</text>
  <text x="495" y="147" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">SIM / bank cards</text>
  <text x="495" y="161" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">still active today</text>
</svg>

CLDC and CDC are subsets of Java SE APIs; Java Card is a further extreme reduction targeting secure elements.

## 5. Runnable example

Scenario: simulate the Generic Connection Framework (GCF) pattern — Java ME's unified I/O abstraction — using only Java SE classes to demonstrate the design.

### Level 1 — Basic

```java
// MeGcfSimple.java
// Simulates the Java ME Generic Connection Framework API structure
public class MeGcfSimple {

    // Simulated Java ME interfaces
    interface Connection { void close(); }
    interface HttpConnection extends Connection {
        int getResponseCode();
        String getHeaderField(String name);
    }

    // Simulated Connector.open() factory (in Java ME: javax.microedition.io.Connector)
    static Connection open(String url) {
        System.out.println("[GCF] Connector.open(\"" + url + "\")");
        if (url.startsWith("http")) return new SimHttpConnection(url);
        throw new IllegalArgumentException("Unsupported scheme: " + url);
    }

    static class SimHttpConnection implements HttpConnection {
        private final String url;
        SimHttpConnection(String url) { this.url = url; }
        public int getResponseCode()          { return 200; }
        public String getHeaderField(String n){ return n.equalsIgnoreCase("Content-Type") ? "text/html" : null; }
        public void close() { System.out.println("[GCF] connection to " + url + " closed"); }
    }

    public static void main(String[] args) {
        HttpConnection conn = (HttpConnection) open("http://example.com/");
        System.out.println("Response code : " + conn.getResponseCode());
        System.out.println("Content-Type  : " + conn.getHeaderField("Content-Type"));
        conn.close();
    }
}
```

**How to run:** `java MeGcfSimple.java`

This mirrors the actual Java ME GCF: `Connector.open(url)` returns a typed `Connection`. The scheme in the URL determines the connection type — the same factory handles HTTP, sockets, datagrams, and serial ports, keeping the API surface tiny.

### Level 2 — Intermediate

Same GCF simulation extended to cover multiple connection types (HTTP and socket), and a Resource tracker simulating the strict memory discipline required on a 64 KB device.

```java
// MeGcfIntermediate.java
import java.util.*;

public class MeGcfIntermediate {

    interface Connection { void close(); String scheme(); }
    interface HttpConnection extends Connection {
        int getResponseCode(); String getHeader(String name); byte[] getBody();
    }
    interface SocketConnection extends Connection {
        void send(byte[] data); byte[] receive();
    }

    static class GCF {
        static int openConnections = 0;
        static final int MAX_CONNECTIONS = 3;   // simulates tight resource limit

        static Connection open(String url) {
            if (openConnections >= MAX_CONNECTIONS)
                throw new RuntimeException("Too many open connections (ME resource limit)");
            openConnections++;
            if (url.startsWith("http"))   return new FakeHttp(url);
            if (url.startsWith("socket")) return new FakeSocket(url);
            throw new IllegalArgumentException("Unknown scheme: " + url.split(":")[0]);
        }
    }

    static class FakeHttp implements HttpConnection {
        private final String url; private boolean closed;
        FakeHttp(String u) { this.url = u; System.out.println("[GCF] HTTP open: " + u); }
        public int getResponseCode() { return 200; }
        public String getHeader(String n) { return "text/plain"; }
        public byte[] getBody() { return ("Body from " + url).getBytes(); }
        public void close() {
            if (!closed) { closed = true; GCF.openConnections--; System.out.println("[GCF] HTTP closed: " + url); }
        }
        public String scheme() { return "http"; }
    }

    static class FakeSocket implements SocketConnection {
        private final String url; private boolean closed;
        FakeSocket(String u) { this.url = u; System.out.println("[GCF] Socket open: " + u); }
        public void send(byte[] d)  { System.out.println("[Socket] sent " + d.length + " bytes"); }
        public byte[] receive()     { return "ACK".getBytes(); }
        public void close() {
            if (!closed) { closed = true; GCF.openConnections--; System.out.println("[GCF] Socket closed: " + url); }
        }
        public String scheme() { return "socket"; }
    }

    public static void main(String[] args) {
        List<Connection> open = new ArrayList<>();
        try {
            open.add(GCF.open("http://device.local/sensor"));
            open.add(GCF.open("socket://192.168.1.1:9999"));
            open.add(GCF.open("http://device.local/config"));

            // Try exceeding the limit
            GCF.open("http://overload.test/");
        } catch (RuntimeException e) {
            System.out.println("[Resource limit hit] " + e.getMessage());
        } finally {
            for (Connection c : open) c.close();
        }
    }
}
```

**How to run:** `java MeGcfIntermediate.java`

Hitting the connection limit simulates the `java.lang.OutOfMemoryError` or resource exhaustion that was a real problem on J2ME phones with 64 KB of heap. Proper `close()` in `finally` was mission-critical, not just good practice.

### Level 3 — Advanced

Same GCF pattern grown to a full Java ME–style MIDlet lifecycle simulation: `startApp`, `pauseApp`, `destroyApp` lifecycle hooks, a primitive event queue (simulating the LCDUI display loop), and a heartbeat task — reflecting the actual structure of a MIDP 2.0 MIDlet.

```java
// MidletSimulation.java
import java.util.*;
import java.util.concurrent.*;

public class MidletSimulation {

    // Java ME MIDlet lifecycle interface (normally extends javax.microedition.midlet.MIDlet)
    interface Midlet {
        void startApp();
        void pauseApp();
        void destroyApp(boolean unconditional);
    }

    // Simulated platform scheduler
    static class MidletRunner {
        private final Midlet midlet;
        private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        private volatile boolean running;

        MidletRunner(Midlet m) { this.midlet = m; }

        void run() throws InterruptedException {
            System.out.println("[Platform] MIDlet starting...");
            midlet.startApp();
            running = true;

            // Simulate incoming event (e.g. key press) after 2 ticks
            ScheduledFuture<?> task = scheduler.scheduleAtFixedRate(() -> {
                if (running) System.out.println("[Platform] tick (heartbeat)");
            }, 0, 300, TimeUnit.MILLISECONDS);

            Thread.sleep(800);   // simulate user interaction time
            System.out.println("[Platform] background event: pausing MIDlet...");
            midlet.pauseApp();

            Thread.sleep(400);
            System.out.println("[Platform] foregrounded: resuming MIDlet...");
            midlet.startApp();

            Thread.sleep(400);
            System.out.println("[Platform] user exits: destroying MIDlet...");
            midlet.destroyApp(true);
            running = false;
            task.cancel(false);
            scheduler.shutdown();
        }
    }

    // A concrete MIDlet — in real Java ME this extends MIDlet and draws to Display
    static class TemperatureMidlet implements Midlet {
        private int readingCount = 0;

        public void startApp() {
            System.out.println("[TemperatureMidlet] startApp(): initialising sensor connection");
        }
        public void pauseApp() {
            System.out.println("[TemperatureMidlet] pauseApp(): releasing sensor, saving state");
        }
        public void destroyApp(boolean unconditional) {
            System.out.println("[TemperatureMidlet] destroyApp(" + unconditional + "): cleanup, " + readingCount + " readings taken");
        }
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== Java ME MIDlet Lifecycle Simulation ===");
        new MidletRunner(new TemperatureMidlet()).run();
        System.out.println("[Platform] MIDlet stopped. VM may exit.");
    }
}
```

**How to run:** `java MidletSimulation.java`

The `startApp / pauseApp / destroyApp` lifecycle is the actual MIDP 2.0 MIDlet contract. Platform events (incoming call, low battery) trigger `pauseApp`; returning to foreground triggers `startApp` again. Proper resource release in `pauseApp` was mandatory — phones had no virtual memory to fall back on.

## 6. Walkthrough

`MidletRunner.run()` drives the lifecycle in order:

1. **`startApp()`** — the midlet initialises resources (sensor connection, GCF connection). On a real phone this draws the initial screen to `Display.getDisplay(this).setCurrent(form)`.

2. **Heartbeat ticks** — `ScheduledExecutorService` fires every 300 ms, simulating the platform's event loop. A real MIDP display loop is driven by `Display.callSerially()`.

3. **`pauseApp()`** at 800 ms — a platform event (simulated phone call) triggers the pause. The midlet must release the GCF connection, stop animations, and save any volatile state to the Record Management System (RMS — Java ME's persistent storage). Failure to do so causes resource leaks that crash the phone.

4. **`startApp()` again** — user returns to the midlet. Resources are re-acquired.

5. **`destroyApp(true)`** — the user exits or the platform terminates the midlet. `unconditional=true` means "you must exit now." `unconditional=false` (can be rejected by the midlet) was rarely used.

Data/state through the lifecycle:
```
Platform event        → MidletRunner
                           │
          ┌────────────────┴──────────────────┐
     startApp()          pauseApp()       destroyApp()
     acquire resources   release resources  final cleanup
     show UI             save RMS state     exit JVM
```

GCF connection lifecycle mirrors this: `Connector.open()` in `startApp`, `conn.close()` in `pauseApp/destroyApp`. Every resource must pair an open with a close — Java ME had no garbage-collected finalizers on connections.

## 7. Gotchas & takeaways

> **Java ME's CLDC 1.0 had no `float` or `double` arithmetic** — floating-point was optional on the smallest devices. Code that used `Math.sqrt()` would not compile for CLDC 1.0 targets. Always check your target configuration before using math-heavy algorithms.

> **Java ME is not Android.** Android uses its own VM (Dalvik, later ART) and its own API (`android.*`). Java ME MIDlets do not run on Android; Android apps do not run on Java ME devices. They share the Java language but nothing else.

- Java ME family: CLDC (smallest phones), CDC (smarter devices), Java Card (smartcards — still active).
- The Generic Connection Framework (`Connector.open(url)`) unifies all I/O in one tiny API.
- MIDlet lifecycle: `startApp → pauseApp → startApp → destroyApp` — driven by platform events.
- Strict resource discipline was mandatory: no finalizers, no virtual memory, `close()` every connection.
- Java Card is the only Java ME variant still in heavy active use (billions of SIM/bank cards).
- For modern embedded Java, prefer Java SE on capable hardware (Raspberry Pi) or Android for phones.
