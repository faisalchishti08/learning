---
card: java
gi: 723
slug: internet-address-resolution-spi
title: Internet-Address Resolution SPI
---

## 1. What it is

**Java 18** (JEP 418) introduces a **Service Provider Interface (SPI)** for hostname and address resolution, letting a Java application plug in a custom `InetAddressResolverProvider` to replace the JDK's default DNS-lookup logic (previously buried inside `java.net.InetAddress` with no supported way to override it). Before this JEP, resolving `InetAddress.getByName("example.com")` meant going through the platform's native resolver via an internal, unpluggable code path; the only override mechanism was the long-unsupported, JDK-internal `sun.net.spi.nameservice` system properties. JEP 418 makes address resolution a first-class, documented extension point: implement `InetAddressResolverProvider`, register it via `ServiceLoader` (the standard Java plugin-discovery mechanism), and every `InetAddress` lookup in the JVM goes through your code instead of (or in addition to) the platform resolver.

## 2. Why & when

Applications sometimes need hostname resolution that doesn't go through the operating system's normal DNS path: testing code that wants deterministic, offline hostname-to-IP mappings without touching a real network; applications running inside container or service-mesh environments with custom service-discovery mechanisms that aren't plain DNS; or tools that want to enforce a specific resolution policy (blocklists, custom TTL handling, resolution metrics) uniformly across an application without changing every call site. Before Java 18, none of this was possible without reaching into unsupported internals (`sun.net.spi.nameservice.*`), which could break on any JDK update since it was never a public contract. JEP 418 exists purely to give this capability a real, stable, documented API surface via `ServiceLoader` — the same general plugin-discovery pattern used by charset providers, locale providers, and many other JDK extension points. Use this SPI when a program needs to intercept or replace *all* hostname resolution JVM-wide, such as in integration test harnesses simulating specific DNS responses, or in specialized networking environments with non-standard service discovery.

## 3. Core concept

```java
// A custom resolver provider (must be registered via ServiceLoader)
public final class FixedMapResolverProvider extends InetAddressResolverProvider {
    @Override
    public InetAddressResolver get(Configuration configuration) {
        return new FixedMapResolver();
    }

    @Override
    public String name() {
        return "fixed-map-resolver";
    }
}
```

Registration is done the standard `ServiceLoader` way: either a `META-INF/services/java.net.spi.InetAddressResolverProvider` file naming the implementation class, or, for a modular application, a `provides ... with ...` clause in `module-info.java`.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="InetAddress.getByName delegates to the resolver returned by an InetAddressResolverProvider located via ServiceLoader, falling back to the platform's built-in resolver if no custom provider is registered">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">InetAddress.getByName("host")</text>

  <line x1="110" y1="70" x2="110" y2="100" stroke="#8b949e" stroke-width="2" marker-end="url(#a5)"/>
  <rect x="20" y="100" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="122" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ServiceLoader looks for</text>
  <text x="110" y="140" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">InetAddressResolverProvider</text>

  <line x1="200" y1="115" x2="330" y2="70" stroke="#3fb950" stroke-width="2" marker-end="url(#a5)"/>
  <text x="300" y="90" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">found</text>
  <rect x="330" y="30" width="200" height="60" rx="8" fill="#1c2430" stroke="#3fb950"/>
  <text x="430" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">custom InetAddressResolver</text>
  <text x="430" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">e.g. fixed map, mock DNS</text>

  <line x1="200" y1="140" x2="330" y2="180" stroke="#f0883e" stroke-width="2" marker-end="url(#a5)"/>
  <text x="300" y="165" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">not found</text>
  <rect x="330" y="150" width="200" height="60" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="430" y="175" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">platform default resolver</text>
  <text x="430" y="195" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">normal OS/DNS lookup</text>

  <defs><marker id="a5" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

If a resolver provider is registered via `ServiceLoader`, it takes over; otherwise the JDK's built-in platform resolver runs exactly as before.

## 5. Runnable example

Scenario: building a test-friendly hostname resolver, growing from a hard-coded single-hostname mapping, to a configurable map-backed resolver supporting multiple hosts and reverse lookups, to a resolver that falls back to the real platform resolver for any hostname it doesn't recognize — a realistic "override some hosts, delegate the rest" pattern used in integration test harnesses.

### Level 1 — Basic

```java
// File: FixedResolver.java
// A minimal InetAddressResolver returning one hard-coded mapping,
// and a provider exposing it — this is what ServiceLoader will discover.
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.net.spi.InetAddressResolver;
import java.net.spi.InetAddressResolverProvider;
import java.util.List;
import java.util.stream.Stream;

public class FixedResolver {

    public static class Provider extends InetAddressResolverProvider {
        @Override
        public InetAddressResolver get(Configuration configuration) {
            return new Resolver();
        }

        @Override
        public String name() {
            return "fixed-resolver-basic";
        }
    }

    static class Resolver implements InetAddressResolver {
        @Override
        public Stream<InetAddress> lookupByName(String host, LookupPolicy lookupPolicy) throws UnknownHostException {
            if (host.equals("test.internal")) {
                return Stream.of(InetAddress.getByAddress(host, new byte[]{10, 0, 0, 1}));
            }
            throw new UnknownHostException(host);
        }

        @Override
        public String lookupByAddress(byte[] addr) throws UnknownHostException {
            throw new UnknownHostException("reverse lookup not supported");
        }
    }

    public static void main(String[] args) throws UnknownHostException {
        InetAddress addr = InetAddress.getByName("test.internal");
        System.out.println("Resolved test.internal to: " + addr.getHostAddress());
    }
}
```

**How to run** (the provider must be registered via `META-INF/services`, so this needs a small project layout):
```
mkdir -p src/META-INF/services
echo "FixedResolver\$Provider" > src/META-INF/services/java.net.spi.InetAddressResolverProvider
javac -d out FixedResolver.java
cp -r src/META-INF out/
java -cp out FixedResolver
```

Expected output:
```
Resolved test.internal to: 10.0.0.1
```

### Level 2 — Intermediate

```java
// File: MapResolver.java
// Extends to a full map of hostnames, including reverse lookup support —
// the real-world shape of a test-fixture DNS override.
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.net.spi.InetAddressResolver;
import java.net.spi.InetAddressResolverProvider;
import java.util.*;
import java.util.stream.Stream;

public class MapResolver {

    static final Map<String, byte[]> HOST_TO_IP = Map.of(
            "test.internal", new byte[]{10, 0, 0, 1},
            "db.internal", new byte[]{10, 0, 0, 2},
            "cache.internal", new byte[]{10, 0, 0, 3});

    public static class Provider extends InetAddressResolverProvider {
        @Override
        public InetAddressResolver get(Configuration configuration) {
            return new Resolver();
        }

        @Override
        public String name() {
            return "fixed-resolver-map";
        }
    }

    static class Resolver implements InetAddressResolver {
        @Override
        public Stream<InetAddress> lookupByName(String host, LookupPolicy lookupPolicy) throws UnknownHostException {
            byte[] ip = HOST_TO_IP.get(host);
            if (ip == null) throw new UnknownHostException(host);
            return Stream.of(InetAddress.getByAddress(host, ip));
        }

        @Override
        public String lookupByAddress(byte[] addr) throws UnknownHostException {
            for (var entry : HOST_TO_IP.entrySet()) {
                if (Arrays.equals(entry.getValue(), addr)) return entry.getKey();
            }
            throw new UnknownHostException("no reverse mapping for " + Arrays.toString(addr));
        }
    }

    public static void main(String[] args) throws UnknownHostException {
        for (String host : HOST_TO_IP.keySet()) {
            System.out.println(host + " -> " + InetAddress.getByName(host).getHostAddress());
        }
        InetAddress dbAddr = InetAddress.getByAddress(new byte[]{10, 0, 0, 2});
        System.out.println("Reverse lookup of 10.0.0.2 -> " + dbAddr.getHostName());
    }
}
```

**How to run:**
```
mkdir -p src/META-INF/services
echo "MapResolver\$Provider" > src/META-INF/services/java.net.spi.InetAddressResolverProvider
javac -d out MapResolver.java
cp -r src/META-INF out/
java -cp out MapResolver
```

Expected output (map iteration order may vary):
```
test.internal -> 10.0.0.1
db.internal -> 10.0.0.2
cache.internal -> 10.0.0.3
Reverse lookup of 10.0.0.2 -> db.internal
```

### Level 3 — Advanced

```java
// File: FallbackResolver.java
// Overrides only a known set of hostnames and delegates everything else to
// the real platform resolver — the production-flavored pattern: intercept
// specific test/internal hosts, don't break resolution for everything else.
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.net.spi.InetAddressResolver;
import java.net.spi.InetAddressResolverProvider;
import java.util.*;
import java.util.stream.Stream;

public class FallbackResolver {

    static final Map<String, byte[]> OVERRIDES = Map.of(
            "test.internal", new byte[]{10, 0, 0, 1});

    public static class Provider extends InetAddressResolverProvider {
        @Override
        public InetAddressResolver get(Configuration configuration) {
            // builtinResolver() gives access to the platform's normal resolver,
            // so hosts we don't override still resolve via real DNS.
            return new Resolver(configuration.builtinResolver());
        }

        @Override
        public String name() {
            return "fallback-resolver";
        }
    }

    static class Resolver implements InetAddressResolver {
        private final InetAddressResolver platformResolver;

        Resolver(InetAddressResolver platformResolver) {
            this.platformResolver = platformResolver;
        }

        @Override
        public Stream<InetAddress> lookupByName(String host, LookupPolicy lookupPolicy) throws UnknownHostException {
            byte[] ip = OVERRIDES.get(host);
            if (ip != null) {
                System.out.println("[override] resolving " + host + " from fixed map");
                return Stream.of(InetAddress.getByAddress(host, ip));
            }
            System.out.println("[delegate] resolving " + host + " via platform resolver");
            return platformResolver.lookupByName(host, lookupPolicy);
        }

        @Override
        public String lookupByAddress(byte[] addr) throws UnknownHostException {
            return platformResolver.lookupByAddress(addr);
        }
    }

    public static void main(String[] args) throws UnknownHostException {
        InetAddress test = InetAddress.getByName("test.internal");
        System.out.println("test.internal -> " + test.getHostAddress());

        InetAddress local = InetAddress.getByName("localhost");
        System.out.println("localhost -> " + local.getHostAddress());
    }
}
```

**How to run:**
```
mkdir -p src/META-INF/services
echo "FallbackResolver\$Provider" > src/META-INF/services/java.net.spi.InetAddressResolverProvider
javac -d out FallbackResolver.java
cp -r src/META-INF out/
java -cp out FallbackResolver
```

Expected output:
```
[override] resolving test.internal from fixed map
test.internal -> 10.0.0.1
[delegate] resolving localhost via platform resolver
localhost -> 127.0.0.1
```

## 6. Walkthrough

1. Before `FallbackResolver.main` even runs, `ServiceLoader` machinery inside `InetAddress` has already scanned the classpath's `META-INF/services/java.net.spi.InetAddressResolverProvider` file, found the line naming `FallbackResolver$Provider`, instantiated it, and called its `get(configuration)` method once, obtaining our custom `Resolver` — this discovery happens automatically the first time any `InetAddress` resolution occurs in the JVM.
2. `Provider.get(configuration)` receives a `Configuration` object and immediately calls `configuration.builtinResolver()` — this is the JDK's real platform resolver, handed to us specifically so a custom provider can *delegate* to normal DNS rather than having to reimplement it. This is the key design point of this JEP 418 example: overriding resolution doesn't mean losing access to real resolution.
3. `main` calls `InetAddress.getByName("test.internal")`. This routes into our registered `Resolver.lookupByName("test.internal", ...)`.
4. Inside `lookupByName`, `OVERRIDES.get("test.internal")` finds a match, so the method prints `[override] ...` and returns a `Stream<InetAddress>` built directly from the hard-coded byte array `{10, 0, 0, 1}` — no real network lookup happens at all for this hostname.
5. `main` next calls `InetAddress.getByName("localhost")`. This again routes into our `Resolver.lookupByName`, but this time `OVERRIDES.get("localhost")` returns `null` — there's no override for it.
6. Because of that, the method falls into the `else` branch, prints `[delegate] ...`, and calls `platformResolver.lookupByName("localhost", lookupPolicy)` — handing the request off to the exact resolver the JDK would have used anyway if no custom provider were registered at all. The result (`127.0.0.1`) comes from real platform resolution, not from our map.
7. Both results flow back up through the same `InetAddress.getByName` call site unchanged — code calling `InetAddress.getByName` has no idea whether an answer came from the override map or from real DNS; the SPI is fully transparent from the caller's point of view.

```
InetAddress.getByName("test.internal")      InetAddress.getByName("localhost")
              |                                            |
              v                                            v
     FallbackResolver.Resolver.lookupByName is invoked for BOTH calls
              |                                            |
       OVERRIDES has it?                           OVERRIDES has it?
              | yes                                        | no
              v                                             v
   return fixed 10.0.0.1                    platformResolver.lookupByName("localhost")
   (no real network access)                          (real platform/DNS lookup)
```

## 7. Gotchas & takeaways

> A registered `InetAddressResolverProvider` intercepts **every** `InetAddress` resolution in the JVM process, not just ones your own code triggers — third-party libraries, HTTP clients, and any other component doing hostname lookups will also go through your resolver. A buggy or overly narrow custom resolver can silently break unrelated parts of an application.
- Registration is standard `ServiceLoader` discovery: a `META-INF/services/java.net.spi.InetAddressResolverProvider` file listing the implementation class name, or a `provides ... with ...` directive in `module-info.java` for modular applications — get either wrong (typo in the file name or class name) and the custom provider is silently never picked up, with resolution quietly falling back to the platform default.
- `configuration.builtinResolver()` (Level 3) is the deliberate escape hatch letting a custom provider delegate selectively — the pattern of "override known/test hosts, delegate everything else to real resolution" is the most common and safest real-world use of this SPI.
- This SPI replaces the old, unsupported, JDK-internal `sun.net.spi.nameservice.*` system properties that some applications relied on for similar purposes before Java 18 — those internal properties could (and eventually did) break across JDK versions since they were never a documented API; `InetAddressResolverProvider` is the stable, supported successor.
- Only one resolver provider can be active per JVM at a time (the first one `ServiceLoader` finds, or the only one present on the module/class path) — if multiple providers are registered, which one wins depends on `ServiceLoader` ordering, so production use should ensure exactly one provider is on the path.
