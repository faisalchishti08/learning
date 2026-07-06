---
card: java
gi: 327
slug: inetaddress
title: InetAddress
---

## 1. What it is

`InetAddress` represents an IP address — either IPv4 or IPv6 — and provides the lookup logic that turns a human-readable hostname (like `"example.com"`) into the numeric address a network connection actually uses (like `93.184.216.34`), or the reverse. It is the foundation class underneath `Socket`, `ServerSocket`, and `URLConnection` — anything that talks over the network resolves an `InetAddress` first, even if you never call it explicitly.

```java
import java.net.InetAddress;
import java.net.UnknownHostException;

public class InetAddressDemo {
    public static void main(String[] args) throws UnknownHostException {
        InetAddress address = InetAddress.getByName("localhost");
        System.out.println("Host name: " + address.getHostName());
        System.out.println("IP address: " + address.getHostAddress());
    }
}
```

`InetAddress.getByName("localhost")` performs a DNS-style lookup (for `localhost` it resolves to the loopback address without a real network round trip) and returns an object holding both the resolved name and the numeric address.

## 2. Why & when

Network protocols like TCP and UDP operate on numeric IP addresses, not names — but humans and configuration files use names because they're stable even when the underlying IP changes. `InetAddress` is the class that bridges that gap, and it also carries useful classification methods (loopback, multicast, site-local) for deciding how to treat a resolved address.

- **Resolving a hostname before connecting** — confirming a name resolves, or getting the numeric address for logging or comparison, before opening a `Socket`.
- **Getting the local machine's address** — `InetAddress.getLocalHost()` is commonly used to discover the current machine's own hostname and address for logging or self-identification in a distributed system.
- **Checking address properties** — methods like `isLoopbackAddress()`, `isReachable()`, and `isMulticastAddress()` let code branch on what kind of address it's dealing with, useful in networking diagnostics or configuration validation.

DNS lookups can fail (unknown host, network unreachable) or be slow (real DNS round trips), so `InetAddress.getByName()` declares `UnknownHostException`, and code that resolves addresses should treat it as a genuine failure mode, not an edge case to ignore.

## 3. Core concept

```java
import java.net.InetAddress;
import java.net.UnknownHostException;

public class InetAddressCore {
    public static void main(String[] args) throws UnknownHostException {
        InetAddress local = InetAddress.getLocalHost();
        System.out.println("Local host: " + local.getHostName() + " / " + local.getHostAddress());

        InetAddress loopback = InetAddress.getByName("127.0.0.1");
        System.out.println("Is loopback? " + loopback.isLoopbackAddress());

        InetAddress[] all = InetAddress.getAllByName("localhost");
        System.out.println("Resolved " + all.length + " address(es) for localhost");
    }
}
```

**How to run:** `java InetAddressCore.java`

`getAllByName` returns every address a name resolves to (a hostname can map to multiple IPs, e.g. for load balancing), while `getByName` returns just the first one — `isLoopbackAddress()` confirms `127.0.0.1` is recognized as the loopback range without needing to compare octets manually.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="InetAddress resolves a hostname string to a numeric IP address via DNS lookup">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="45" width="180" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="65" fill="#79c0ff" font-size="10" text-anchor="middle">"example.com"</text>
  <text x="120" y="80" fill="#8b949e" font-size="9" text-anchor="middle">hostname (String)</text>

  <text x="230" y="70" fill="#8b949e" font-size="14">→ getByName() →</text>

  <rect x="380" y="45" width="180" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="65" fill="#6db33f" font-size="10" text-anchor="middle">93.184.216.34</text>
  <text x="470" y="80" fill="#8b949e" font-size="9" text-anchor="middle">InetAddress (numeric IP)</text>
</svg>

`InetAddress` is the object form of "a name that has been resolved to a real network address."

## 5. Runnable example

Scenario: a small host-resolution utility, evolved from a single blind lookup, into one that handles unknown hosts gracefully, into a production-style resolver that checks reachability and reports multiple addresses with timeouts.

### Level 1 — Basic

```java
import java.net.InetAddress;
import java.net.UnknownHostException;

public class ResolveBasic {
    public static void main(String[] args) throws UnknownHostException {
        InetAddress address = InetAddress.getByName("localhost");
        System.out.println("Resolved: " + address.getHostAddress());
    }
}
```

**How to run:** `java ResolveBasic.java`

This resolves `"localhost"` to its loopback address and prints it; because `getByName` declares a checked `UnknownHostException`, `main` simply propagates it — fine for a quick script, but risky in real code where an unresolved host is an expected, recoverable situation.

### Level 2 — Intermediate

```java
import java.net.InetAddress;
import java.net.UnknownHostException;

public class ResolveIntermediate {
    public static void main(String[] args) {
        String[] hosts = { "localhost", "this-host-does-not-exist.invalid" };
        for (String host : hosts) {
            try {
                InetAddress address = InetAddress.getByName(host);
                System.out.println(host + " -> " + address.getHostAddress());
            } catch (UnknownHostException e) {
                System.out.println(host + " -> could not resolve: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java ResolveIntermediate.java`

Each hostname is resolved independently inside its own try/catch, so one unresolvable host (the deliberately invalid one) doesn't stop the loop from resolving the others — this is the real-world shape of a resolver that must tolerate partial failure.

### Level 3 — Advanced

```java
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.io.IOException;

public class ResolveAdvanced {
    public static void main(String[] args) {
        String[] hosts = { "localhost", "this-host-does-not-exist.invalid" };
        for (String host : hosts) {
            resolveAndReport(host);
        }
    }

    static void resolveAndReport(String host) {
        try {
            InetAddress[] addresses = InetAddress.getAllByName(host);
            System.out.println(host + " resolved to " + addresses.length + " address(es):");
            for (InetAddress address : addresses) {
                boolean reachable = false;
                try {
                    reachable = address.isReachable(1000); // 1-second timeout ping-style check
                } catch (IOException e) {
                    // reachability check itself can fail independently of resolution
                }
                System.out.println("  " + address.getHostAddress()
                        + " (loopback=" + address.isLoopbackAddress()
                        + ", reachable=" + reachable + ")");
            }
        } catch (UnknownHostException e) {
            System.out.println(host + " -> DNS resolution failed: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ResolveAdvanced.java`

This version separates two independent failure modes — DNS resolution failing (`UnknownHostException`, caught around the whole lookup) versus a reachability probe failing on an already-resolved address (`IOException`, caught per-address) — and reports both a full list of resolved addresses and their individual reachability, which is the level of detail a real diagnostic tool needs.

## 6. Walkthrough

Execution starts in `main`, which iterates the `hosts` array and calls `resolveAndReport("localhost")` first.

Inside `resolveAndReport`, `InetAddress.getAllByName("localhost")` performs the resolution step: on most systems `"localhost"` resolves via the hosts file (not a real DNS round trip) to one or more loopback addresses (commonly `127.0.0.1`, and possibly `::1` for IPv6). This returns an array of `InetAddress` objects, and the method prints how many were found.

For each resolved address, the code calls `address.isReachable(1000)` inside its own `try/catch` — this sends an ICMP echo or opens a TCP probe to see if the host answers within 1000ms. For a loopback address this reliably returns `true` immediately. The line then prints the numeric IP, whether it is a loopback address, and whether it was reachable.

The loop in `main` then calls `resolveAndReport("this-host-does-not-exist.invalid")`. This time, `InetAddress.getAllByName` itself fails at the resolution step — the `.invalid` TLD is reserved specifically to guarantee lookups never succeed — throwing `UnknownHostException` before any address objects are ever created, so the reachability-checking code inside the try block never runs at all. The outer `catch` prints the resolution failure message instead.

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two-stage check: resolve name to addresses, then probe each address for reachability">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="10">Stage 1: getAllByName(host) -- DNS/hosts-file lookup</text>
  <text x="20" y="50" fill="#f85149" font-size="9">  fails -&gt; UnknownHostException -&gt; stop, report resolution failure</text>
  <text x="20" y="72" fill="#6db33f" font-size="9">  succeeds -&gt; array of InetAddress</text>
  <text x="20" y="94" fill="#e6edf3" font-size="10">Stage 2: for each address, isReachable(timeoutMs) -- network probe</text>
  <text x="20" y="114" fill="#8b949e" font-size="9">  independent per-address try/catch -- one probe failing doesn't stop the others</text>
</svg>

## 7. Gotchas & takeaways

> `isReachable()` can return `false` even for a genuinely reachable host if the target blocks ICMP/echo probes at a firewall — treat it as "probably reachable," not an absolute guarantee, and don't use it alone to decide whether a real connection attempt will succeed.

- `getByName` returns one address (the first resolved); `getAllByName` returns every address the name maps to — use the latter when a host may have multiple IPs.
- DNS lookups are genuinely fallible and can be slow — always handle `UnknownHostException` as an expected case, not a rare edge case.
- `getLocalHost()` returns the machine's own configured hostname/address, which can be surprising in containerized or multi-homed environments — don't assume it matches what other machines use to reach this one.
- `isLoopbackAddress()`, `isReachable()`, and similar classification methods let you branch on address type without manually parsing IP octets.
- Resolution and reachability are two separate steps that fail independently — a name can resolve fine to an address that turns out to be unreachable, and vice versa is not possible (you can't probe reachability without first resolving).
