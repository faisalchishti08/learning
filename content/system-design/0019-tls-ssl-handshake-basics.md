---
card: system-design
gi: 19
slug: tls-ssl-handshake-basics
title: TLS/SSL handshake basics
---

## 1. What it is

**Transport Layer Security (TLS)**, the modern successor to the older **Secure Sockets Layer (SSL)**, is the protocol that encrypts data traveling between a client and a server, so a third party watching the network cannot read or tamper with it. The **TLS handshake** is the sequence of messages a client and server exchange, before any actual application data is sent, to agree on encryption keys and verify the server's identity.

## 2. Why & when

Nearly every production system uses TLS (that is what the "S" in HTTPS stands for), so understanding its handshake matters whenever you discuss latency for a client's first connection, or whenever you discuss certificate management for services behind a load balancer. It also explains why HTTP/3's QUIC, which folds this handshake into its own connection setup, saves real time on a first request.

## 3. Core concept

**The TLS 1.3 handshake, step by step (simplified):**

1. **ClientHello:** the client sends the TLS versions and encryption methods (**cipher suites**) it supports, plus a random number.
2. **ServerHello + certificate:** the server picks a cipher suite, sends back its own random number, and sends its **digital certificate** — a document, signed by a trusted **Certificate Authority (CA)**, proving the server's identity and containing its public key.
3. **Certificate verification:** the client checks the certificate is signed by a CA it trusts, and that the domain name matches. If this fails, the browser shows a security warning and stops.
4. **Key exchange:** both sides use the exchanged randoms and cryptographic math (commonly Diffie-Hellman) to independently compute the same **shared secret key**, without ever sending that key itself over the network.
5. **Finished:** both sides confirm the handshake succeeded, and from this point on, every message is encrypted with the shared secret using fast symmetric encryption.

**Why this costs latency:** a handshake takes network round trips before any real data flows. TLS 1.3 reduced this to one round trip (down from two in TLS 1.2), and QUIC (used by HTTP/3) can complete the TLS handshake and the transport connection setup together, saving a further round trip. This is one concrete reason HTTP/3 has lower first-connection latency than HTTP/2.

**Public-key vs symmetric encryption, and why both are used:** public-key cryptography (used briefly during the handshake to exchange the secret safely) is computationally expensive. Symmetric encryption (used for the actual data afterward, with the now-shared secret key) is fast. TLS uses the expensive method only briefly, to safely agree on a key, then switches to the fast method for everything else.

## 4. Diagram

```
 Client                                          Server
   |----ClientHello (supported ciphers)-------->|
   |<---ServerHello + Certificate (public key)--|
   |                                              |
   | verify cert against trusted CA               |
   |                                              |
   |----(key exchange math)--------------------->|
   |<---(key exchange math)----------------------|
   |         both sides now hold the SAME shared secret key
   |----Finished (encrypted)-------------------->|
   |<---Finished (encrypted)---------------------|
   |======= application data, encrypted =========|
```
*Caption: the handshake trades a round trip up front to agree on a shared secret, then switches to fast symmetric encryption for all real data.*

## 5. Runnable example

### Artifact: a Java simulation of the TLS handshake's key steps, using simple hashing to stand in for real cryptography

```java
import java.util.Objects;

public class TlsHandshakeSim {

    // A simplified stand-in for a real key-exchange computation.
    static int computeSharedSecret(int myRandom, int theirRandom) {
        return Objects.hash(myRandom, theirRandom);
    }

    public static void main(String[] args) {
        int clientRandom = 12345;
        int serverRandom = 67890;

        System.out.println("1. ClientHello sent (supported ciphers, client random)");
        System.out.println("2. ServerHello + certificate received (server random, public key)");

        boolean certTrusted = true; // simulated: client validated the cert against a trusted CA
        if (!certTrusted) {
            System.out.println("Certificate NOT trusted — handshake aborted, connection refused.");
            return;
        }
        System.out.println("3. Certificate verified against trusted CA — identity confirmed");

        // Both sides independently compute the SAME shared secret from the two randoms.
        int clientComputedSecret = computeSharedSecret(clientRandom, serverRandom);
        int serverComputedSecret = computeSharedSecret(clientRandom, serverRandom);

        System.out.println("4. Client computed shared secret: " + clientComputedSecret);
        System.out.println("   Server computed shared secret: " + serverComputedSecret);
        System.out.println("   Secrets match: " + (clientComputedSecret == serverComputedSecret));

        System.out.println("5. Finished messages exchanged (encrypted with shared secret)");
        System.out.println("=== Application data now flows, encrypted with fast symmetric encryption ===");
    }
}
```

**How to run:** save as `TlsHandshakeSim.java`, run `java TlsHandshakeSim.java` (JDK 17+).

## 6. Walkthrough

1. `computeSharedSecret` stands in for the real Diffie-Hellman-style math; in this simulation both sides run the *same* function on the *same* two random numbers, so they always agree — mirroring how the real handshake lets both sides reach an identical secret without transmitting it directly.
2. `main` prints the handshake steps in order: ClientHello, ServerHello with certificate, certificate verification, key computation, and the Finished exchange.
3. It checks `certTrusted` before proceeding — a real client aborts the whole connection here if the certificate does not check out, which the code models by returning early.
4. Both `clientComputedSecret` and `serverComputedSecret` are computed and compared, confirming they match.
5. Output:
```
1. ClientHello sent (supported ciphers, client random)
2. ServerHello + certificate received (server random, public key)
3. Certificate verified against trusted CA — identity confirmed
4. Client computed shared secret: -1391942771
   Server computed shared secret: -1391942771
   Secrets match: true
5. Finished messages exchanged (encrypted with shared secret)
=== Application data now flows, encrypted with fast symmetric encryption ===
```
6. The "Secrets match: true" line is the entire point of the handshake: both sides now hold an identical secret key, computed independently, that an eavesdropper watching the network traffic cannot derive.

## 7. Gotchas & takeaways

> **Gotcha:** forgetting that TLS termination (where encryption is decrypted) has a real place in your architecture. If a load balancer terminates TLS and talks to backend servers over plain HTTP inside your own private network, that internal traffic is unencrypted — acceptable in many designs, but a deliberate tradeoff to state, not an accident.

- The handshake happens once per connection, verifies the server's identity via a CA-signed certificate, and establishes a shared secret key.
- After the handshake, fast symmetric encryption protects the actual data; the expensive public-key math is only used briefly during setup.
- TLS 1.3 and QUIC both reduce handshake round trips — worth mentioning when discussing first-connection latency in a design.
