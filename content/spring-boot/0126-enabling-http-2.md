---
card: spring-boot
gi: 126
slug: enabling-http-2
title: Enabling HTTP/2
---

## 1. What it is

**HTTP/2** is the second major version of the HTTP protocol. It introduces multiplexing (multiple requests share one TCP connection), header compression (HPACK), and server push. Spring Boot enables HTTP/2 on the embedded server with a single property: `server.http2.enabled=true`. All three embedded containers (Tomcat, Jetty, Undertow) support it, each with slightly different requirements.

## 2. Why & when

HTTP/1.1 opens a new TCP connection per request (or keeps one alive but serialises requests). Under HTTP/2 a single connection carries many requests simultaneously — critical for pages that load dozens of resources (scripts, images, fonts). Latency drops and throughput rises, especially over high-latency links.

Enable HTTP/2 when:

- Your app serves a browser-facing frontend and page load performance matters.
- You're behind a load balancer or API gateway that negotiates HTTP/2 downstream.
- You want the multiplexing benefit for microservice-to-microservice calls using Spring's reactive clients.

Requirement: **HTTP/2 over TLS (h2)** is the standard path in browsers. Cleartext HTTP/2 (h2c) is supported by some containers but not browsers; use it only for internal service-to-service traffic.

## 3. Core concept

HTTP/2 negotiation uses **ALPN (Application-Layer Protocol Negotiation)**, a TLS extension. The client and server agree on `h2` during the TLS handshake — no extra round-trip. This means:

- HTTPS (TLS) is required for browser-facing HTTP/2.
- You need either a keystore or a TLS termination proxy (NGINX, AWS ALB) in front.

**h2c** (HTTP/2 cleartext, no TLS) is supported on Tomcat and Undertow via an upgrade mechanism but is transparent only to HTTP/2-aware clients — browsers don't use it.

For JDK 17+ on Tomcat and Jetty, ALPN is built into the JDK's TLS stack — no extra libraries needed. Earlier JDKs required the Conscrypt or Jetty ALPN agent.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="107" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Browser / Client</text>
  <text x="95" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">TLS + ALPN h2</text>
  <rect x="280" y="60" width="160" height="100" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="360" y="83" text-anchor="middle" fill="#79c0ff" font-size="11" font-family="sans-serif">TLS Handshake</text>
  <text x="360" y="100" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">ALPN: h2 agreed</text>
  <line x1="360" y1="107" x2="360" y2="125" stroke="#6db33f" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="360" y="137" text-anchor="middle" fill="#6db33f" font-size="11" font-family="sans-serif">HTTP/2 frames</text>
  <text x="360" y="152" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">multiplexed streams</text>
  <rect x="510" y="80" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="585" y="108" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Embedded Server</text>
  <text x="585" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">h2 enabled</text>
  <line x1="172" y1="110" x2="276" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#h2a)"/>
  <line x1="442" y1="110" x2="506" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#h2b)"/>
  <defs>
    <marker id="h2a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="h2b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Client and server negotiate `h2` via ALPN during the TLS handshake; subsequent traffic flows as multiplexed HTTP/2 frames over one connection.

## 5. Runnable example

```java
// Http2App.java  —  Spring Boot project with spring-boot-starter-web
// application.properties needed (see below)

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class Http2App {
    public static void main(String[] args) {
        SpringApplication.run(Http2App.class, args);
    }
}

@RestController
class ProtocolController {

    @GetMapping("/protocol")
    public String protocol() {
        return "Running with HTTP/2 enabled (check protocol with curl --http2)";
    }
}

// application.properties:
// server.port=8443
// server.http2.enabled=true
// server.ssl.key-store=classpath:keystore.p12
// server.ssl.key-store-password=changeit
// server.ssl.key-store-type=PKCS12
// server.ssl.key-alias=springboot

// Generate a self-signed keystore for testing (run once in your project root):
// keytool -genkeypair -alias springboot -keyalg RSA -keysize 2048 \
//   -storetype PKCS12 -keystore src/main/resources/keystore.p12 \
//   -validity 365 -storepass changeit \
//   -dname "CN=localhost,OU=Dev,O=Example,L=City,S=State,C=US"
```

**How to run:**

1. Generate the keystore with the `keytool` command shown above.
2. Start the app with `./mvnw spring-boot:run`.
3. Test with curl: `curl --http2 -k https://localhost:8443/protocol`

The `-k` flag skips certificate validation for the self-signed cert. Look for `HTTP/2 200` in verbose output (`curl -v --http2 -k ...`).

## 6. Walkthrough

- `server.http2.enabled=true` tells the embedded container to advertise `h2` in ALPN during the TLS handshake.
- `server.ssl.key-store=classpath:keystore.p12` loads the PKCS12 keystore from `src/main/resources/`. Spring Boot auto-configures TLS on the connector when any `server.ssl.*` property is set.
- TLS is mandatory for browser-facing HTTP/2 (the `h2` ALPN token). Browsers refuse to upgrade to HTTP/2 over plain HTTP.
- `keytool -genkeypair` creates a self-signed certificate for local development. In production, use a CA-signed certificate from Let's Encrypt, AWS ACM, or your PKI.
- After startup, `curl -v --http2 -k https://localhost:8443/protocol` negotiates `h2` and shows `HTTP/2 200` in the response header. Without `--http2`, curl defaults to HTTP/1.1.
- On JDK 17+ with Tomcat 10.1+, no extra libraries are needed — ALPN is built into the JVM's TLS implementation.

## 7. Gotchas & takeaways

> Enabling `server.http2.enabled=true` **without** SSL configuration has no effect for browsers. h2c (cleartext HTTP/2) requires client support and is not negotiated automatically by browsers. Add `server.ssl.*` properties alongside it.

> Self-signed certificates work for development but cause browser warnings and break most HTTP clients in production. Always use a CA-signed certificate in prod.

- On JDK 8 with Tomcat, you need the Tomcat Native library (OpenSSL) or Conscrypt to support ALPN — JDK 8 lacks ALPN in its TLS stack.
- When running behind an NGINX or ALB that terminates TLS, set `server.http2.enabled=true` on the proxy, not on Spring Boot — Spring Boot then receives plain HTTP/1.1 from the proxy.
- h2c (cleartext) is useful for internal gRPC or inter-service HTTP/2; set `server.http2.enabled=true` and no SSL config. Tomcat and Undertow support this; Jetty requires extra configuration.
- HTTP/2 multiplexing benefits are most visible when many small requests hit the server simultaneously; batch-heavy or single-request workloads see less improvement.
