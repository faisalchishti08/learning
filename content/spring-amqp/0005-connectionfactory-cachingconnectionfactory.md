---
card: spring-amqp
gi: 5
slug: connectionfactory-cachingconnectionfactory
title: "ConnectionFactory (CachingConnectionFactory)"
---

## 1. What it is

`ConnectionFactory` is Spring AMQP's abstraction over creating connections to a RabbitMQ broker, and `CachingConnectionFactory` is the standard implementation used in almost every real application — it wraps the underlying RabbitMQ Java client's own connection factory, adding connection and channel caching (and pooling) so that opening a connection and creating channels, both genuinely expensive operations, happen only as often as actually necessary rather than once per message sent or received.

## 2. Why & when

You configure `CachingConnectionFactory` explicitly (rather than accepting Boot's defaults blindly) when connection behavior needs tuning for the application's actual traffic pattern:

- **Establishing a raw TCP connection to RabbitMQ, and the AMQP handshake on top of it, is expensive relative to sending a message** — reusing a small number of long-lived connections and channels across many message sends avoids paying that setup cost repeatedly, which matters enormously at any meaningful throughput.
- **Channels (lightweight virtual connections multiplexed over one physical connection) are the right unit to pool for concurrent publishing** — `CachingConnectionFactory`'s channel cache size needs tuning to the application's actual concurrent publishing load; too small a cache creates channel-creation bottlenecks under load, too large wastes broker-side resources.
- **Connections need to recover automatically from a broker restart or network blip** — the underlying RabbitMQ client's automatic connection recovery, which `CachingConnectionFactory` builds on, needs understanding so a temporary network issue doesn't require manual application intervention to reconnect.

## 3. Core concept

Think of opening a raw AMQP connection like establishing a dedicated phone line between two buildings — expensive and slow to set up, so you don't want to hang up and redial for every single sentence you need to say. A channel is like one of several simultaneous conversations that can happen over that same phone line at once (multiplexing) — cheaper to open and close than the line itself, but still worth reusing rather than starting a brand-new conversation thread for every single message. `CachingConnectionFactory` keeps a small pool of already-established lines and already-open conversation threads on hand, handing one out whenever a message needs to go out and returning it to the pool afterward, rather than dialing and hanging up every time.

```java
@Bean
public ConnectionFactory connectionFactory() {
    CachingConnectionFactory factory = new CachingConnectionFactory("rabbitmq-host", 5672);
    factory.setUsername("app-user");
    factory.setPassword("secret");
    factory.setChannelCacheSize(25);      // cache up to 25 channels for reuse
    factory.setCacheMode(CachingConnectionFactory.CacheMode.CHANNEL); // default: cache channels, one connection
    return factory;
}
```

A single underlying connection is established and reused; up to 25 channels are cached and handed out to concurrent publishers rather than each publish operation opening a fresh one.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without caching, every send opens and closes a new connection and channel; with CachingConnectionFactory, one connection stays open and channels are borrowed from a cache and returned after use" >
  <text x="160" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">No caching (naive)</text>
  <rect x="20" y="30" width="280" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="50" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="monospace">open conn -&gt; open ch -&gt; send -&gt; close ch -&gt; close conn</text>
  <text x="160" y="80" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">repeated in full for every single message</text>

  <text x="480" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">CachingConnectionFactory</text>
  <rect x="340" y="30" width="280" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="50" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="monospace">1 connection kept open, channels borrowed/returned</text>
  <text x="480" y="80" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">connection setup cost paid once, not per message</text>
</svg>

Caching amortizes the expensive connection setup cost across every message sent through it.

## 5. Runnable example

The scenario: sending many messages efficiently by reusing connections and channels, simulated with a plain pool-based model standing in for `CachingConnectionFactory` (no real RabbitMQ broker needed to demonstrate the reuse-versus-recreate cost difference), starting with a naive open/close-per-message approach, then adding a channel cache to reuse channels across sends, then adding a cache-size limit with wait behavior to model what happens under high concurrent demand.

### Level 1 — Basic

```java
// ConnectionCachingDemo.java
public class ConnectionCachingDemo {
    static int connectionsOpened = 0;
    static int channelsOpened = 0;

    // Stand-in for the naive, uncached approach: every send opens fresh resources.
    static void sendNaive(String payload) {
        connectionsOpened++;
        channelsOpened++;
        System.out.println("Opened connection #" + connectionsOpened + ", channel #" + channelsOpened
            + ", sent: " + payload);
    }

    public static void main(String[] args) {
        sendNaive("message 1");
        sendNaive("message 2");
        sendNaive("message 3");
        System.out.println("Total connections opened: " + connectionsOpened + ", channels opened: " + channelsOpened);
    }
}
```

How to run: `java ConnectionCachingDemo.java`. Expected output: three send lines each reporting a fresh connection and channel number, ending with `Total connections opened: 3, channels opened: 3` — the naive approach paying the full setup cost for every single message.

### Level 2 — Intermediate

```java
// ConnectionCachingDemo.java
import java.util.*;

public class ConnectionCachingDemo {
    // Real-world concern: reuse one connection and pool channels, since both are expensive to
    // create relative to the cost of actually sending a message over an already-open channel.
    static class CachingConnectionFactory {
        private boolean connectionOpen = false;
        private final Deque<Integer> idleChannels = new ArrayDeque<>();
        private int nextChannelId = 1;
        int connectionsOpenedCount = 0;
        int channelsCreatedCount = 0;

        int borrowChannel() {
            if (!connectionOpen) {
                connectionOpen = true;
                connectionsOpenedCount++;
                System.out.println("Opened the (single) underlying connection");
            }
            if (!idleChannels.isEmpty()) {
                return idleChannels.pop(); // reuse an existing channel
            }
            channelsCreatedCount++;
            return nextChannelId++;
        }

        void returnChannel(int channelId) {
            idleChannels.push(channelId); // back to the pool for the next send
        }
    }

    static void send(CachingConnectionFactory factory, String payload) {
        int channel = factory.borrowChannel();
        System.out.println("Using channel #" + channel + ", sent: " + payload);
        factory.returnChannel(channel);
    }

    public static void main(String[] args) {
        CachingConnectionFactory factory = new CachingConnectionFactory();
        send(factory, "message 1");
        send(factory, "message 2");
        send(factory, "message 3");
        System.out.println("Total connections opened: " + factory.connectionsOpenedCount
            + ", channels created: " + factory.channelsCreatedCount);
    }
}
```

How to run: `java ConnectionCachingDemo.java`. Expected output: the connection opens exactly once; each send reuses channel #1 (returned to the pool after the previous send), ending with `Total connections opened: 1, channels created: 1` — three messages sent using only a single connection and a single channel, reused each time rather than recreated.

### Level 3 — Advanced

```java
// ConnectionCachingDemo.java
import java.util.*;
import java.util.concurrent.*;

public class ConnectionCachingDemo {
    // Production concern: under concurrent load, more than one channel may be needed
    // simultaneously -- CachingConnectionFactory bounds the cache size, and a request beyond
    // that limit either waits or creates a new (uncached) channel, depending on configuration.
    static class BoundedCachingConnectionFactory {
        private final int maxCacheSize;
        private final Deque<Integer> idleChannels = new ArrayDeque<>();
        private int nextChannelId = 1;
        private int inUseCount = 0;

        BoundedCachingConnectionFactory(int maxCacheSize) { this.maxCacheSize = maxCacheSize; }

        synchronized int borrowChannel() {
            inUseCount++;
            if (!idleChannels.isEmpty()) return idleChannels.pop();
            int newChannel = nextChannelId++;
            if (newChannel > maxCacheSize) {
                System.out.println("Cache exhausted (" + maxCacheSize + " channels in flight), creating extra uncached channel #" + newChannel);
            }
            return newChannel;
        }

        synchronized void returnChannel(int channelId) {
            inUseCount--;
            idleChannels.push(channelId);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        BoundedCachingConnectionFactory factory = new BoundedCachingConnectionFactory(2);
        ExecutorService executor = Executors.newFixedThreadPool(4);

        for (int i = 1; i <= 4; i++) {
            int msgNum = i;
            executor.submit(() -> {
                int channel = factory.borrowChannel();
                System.out.println("Message " + msgNum + " using channel #" + channel);
                factory.returnChannel(channel);
            });
        }
        executor.shutdown();
        executor.awaitTermination(2, TimeUnit.SECONDS);
    }
}
```

How to run: `java ConnectionCachingDemo.java`. Expected output: four "Message N using channel #M" lines, with channel numbers reused where possible within the cache size of 2, and at least one "Cache exhausted ... creating extra uncached channel" message if concurrent demand genuinely exceeds the configured cache size — demonstrating the trade-off `channelCacheSize` tuning represents between resource usage and avoiding channel-creation bottlenecks under real concurrent load.

## 6. Walkthrough

Trace how `CachingConnectionFactory` handles a burst of concurrent publish requests.

1. **First request**: the very first call needing a channel triggers the factory to establish the actual underlying TCP connection and AMQP handshake with the broker — this is the one genuinely expensive setup operation, paid once.
2. **Channel borrowed**: that first request also creates (since the cache starts empty) a new channel over the now-open connection, and uses it to send its message.
3. **Channel returned**: once the send completes, the channel is returned to the factory's internal cache rather than being closed — ready for the next request to reuse immediately.
4. **Subsequent requests reuse**: a second request arriving while the first channel is idle in the cache simply borrows that same channel rather than creating a new one, skipping the (smaller, but still non-zero) cost of channel creation.
5. **Concurrent demand within cache size**: if multiple requests arrive simultaneously and the cache has enough previously-created channels to cover them (or room to create more within `channelCacheSize`), each gets its own channel to use concurrently, and all return to the cache when done.
6. **Concurrent demand exceeding cache size**: if concurrent demand genuinely exceeds the configured cache size, the factory either creates additional channels beyond the cache limit (which then aren't kept in the cache afterward) or applies backpressure, depending on configuration — this is the scenario `channelCacheSize` tuning exists to manage, balancing resource usage against contention under real load.

```
first send -> connection opened (once) -> channel created -> used -> returned to cache
second send -> connection already open -> channel reused from cache -> used -> returned
concurrent sends within cache size -> each gets its own cached/created channel, run in parallel
concurrent sends beyond cache size -> extra channel created beyond cache, or caller waits
```

## 7. Gotchas & takeaways

> **Gotcha:** a `channelCacheSize` set far too low for the application's actual concurrent publishing load causes channel-creation to become a bottleneck precisely during the traffic bursts when performance matters most — size the cache to the application's realistic peak concurrent publish/consume demand, not just its average load, and monitor actual channel creation counts in production rather than guessing.

- `CachingConnectionFactory` typically maintains a single underlying connection (in the common `CHANNEL` cache mode) with many cached channels multiplexed over it — this is usually the right default, since channels are cheap relative to connections and the broker handles many channels per connection efficiently.
- Automatic connection recovery (handling a broker restart or network blip transparently) is a feature of the underlying RabbitMQ Java client that `CachingConnectionFactory` builds on — understanding that this recovery is generally automatic (and confirming it's enabled, since it can be turned off) avoids unnecessary manual reconnection logic in application code.
- Never construct a new `ConnectionFactory` (or a new `RabbitTemplate` wrapping one) per message or per request — always share a single, application-scoped instance, since the entire point of the caching behavior is amortizing setup cost across the application's full lifetime, not per-operation.
- Monitor a production application's actual channel usage (via the broker's management UI or Spring AMQP's own metrics) before assuming a given `channelCacheSize` is correctly tuned — the right number depends entirely on real concurrent load, not a fixed rule of thumb.
