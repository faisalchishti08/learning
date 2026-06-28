---
card: spring-boot
gi: 127
slug: ssl-tls-configuration-ssl-bundles
title: SSL/TLS configuration & SSL bundles
---

## 1. What it is

Spring Boot lets you enable HTTPS on the embedded server by setting `server.ssl.*` properties to point at a keystore file. Spring Boot 3.1 introduced **SSL bundles** — a higher-level abstraction that gives a named SSL configuration (`spring.ssl.bundle.*`) which can be referenced in multiple places: the server, `RestClient`, `WebClient`, data sources, etc. SSL bundles separate *what* certificates you use from *where* you use them.

## 2. Why & when

Without HTTPS, all traffic — including credentials and session cookies — travels in plain text. Enable SSL when:

- Serving a browser-facing app (TLS is mandatory for HTTP/2 and `Secure` cookies).
- Exposing a REST API used by external clients.
- Deploying on a machine without a TLS-terminating proxy (NGINX, ALB).

SSL bundles shine when you have mutual TLS (mTLS) or need to reuse the same certificate configuration for the server *and* outbound HTTP clients — a common requirement in microservice meshes.

## 3. Core concept

**Classic approach** — properties on the server:

```properties
server.ssl.key-store=classpath:keystore.p12
server.ssl.key-store-type=PKCS12
server.ssl.key-store-password=secret
server.ssl.key-alias=myapp
server.port=8443
```

**SSL bundle approach** (Spring Boot 3.1+) — define once, use anywhere:

```properties
spring.ssl.bundle.jks.myapp.keystore.location=classpath:keystore.p12
spring.ssl.bundle.jks.myapp.keystore.password=secret
spring.ssl.bundle.jks.myapp.keystore.type=PKCS12
# Reference the bundle from the server
server.ssl.bundle=myapp
```

A bundle can also hold a truststore (for mTLS or trusting internal CAs) and is refreshable at runtime if the underlying file changes.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="105" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">SSL Bundle</text>
  <text x="95" y="122" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">"myapp"</text>
  <rect x="260" y="55" width="160" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="82" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Embedded Server</text>
  <rect x="260" y="115" width="160" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="142" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">RestClient / WebClient</text>
  <rect x="260" y="175" width="160" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="197" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Data source (JDBC)</text>
  <rect x="510" y="100" width="150" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="585" y="120" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">keystore.p12</text>
  <text x="585" y="137" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">truststore.p12</text>
  <line x1="172" y1="110" x2="256" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ssl)"/>
  <line x1="172" y1="110" x2="256" y2="138" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ssl)"/>
  <line x1="172" y1="110" x2="256" y2="192" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ssl)"/>
  <line x1="95" y1="80" x2="505" y2="125" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#ssl2)"/>
  <text x="300" y="55" fill="#8b949e" font-size="10" font-family="sans-serif">references cert files</text>
  <defs>
    <marker id="ssl" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ssl2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

One named SSL bundle holds keystore and truststore; server, clients, and data sources all reference it by name.

## 5. Runnable example

```java
// SslBundleApp.java  —  Spring Boot 3.1+ project with spring-boot-starter-web
// application.properties (create this file alongside):
//
// server.port=8443
// spring.ssl.bundle.jks.myapp.keystore.location=classpath:keystore.p12
// spring.ssl.bundle.jks.myapp.keystore.password=changeit
// spring.ssl.bundle.jks.myapp.keystore.type=PKCS12
// server.ssl.bundle=myapp
//
// Generate keystore once:
// keytool -genkeypair -alias myapp -keyalg RSA -keysize 2048 \
//   -storetype PKCS12 -keystore src/main/resources/keystore.p12 \
//   -validity 365 -storepass changeit \
//   -dname "CN=localhost,OU=Dev,O=Example,L=City,ST=State,C=US"

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.ssl.SslBundles;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class SslBundleApp {
    public static void main(String[] args) {
        SpringApplication.run(SslBundleApp.class, args);
    }
}

@RestController
class SecureController {

    private final SslBundles sslBundles;

    SecureController(SslBundles sslBundles) {
        this.sslBundles = sslBundles;
    }

    @GetMapping("/ssl-info")
    public String sslInfo() {
        // Inspect the bundle programmatically
        var bundle = sslBundles.getBundle("myapp");
        return "Protocol: " + bundle.createSslContext().getProtocol()
                + " | Bundle: myapp";
    }
}
```

**How to run:**
1. Generate `keystore.p12` with the `keytool` command above.
2. Start the app.
3. `curl -k https://localhost:8443/ssl-info` — `-k` skips self-signed cert validation.

## 6. Walkthrough

- `spring.ssl.bundle.jks.myapp.*` defines a JKS-style (or PKCS12) bundle named `myapp`. Spring Boot creates a `SslBundle` bean backed by the specified keystore file.
- `server.ssl.bundle=myapp` tells the embedded server to use the `myapp` bundle for its TLS connector — equivalent to the classic `server.ssl.key-store` approach, but the certificate config is now reusable.
- `SslBundles` is an auto-configured bean. Injecting it into `SecureController` allows reading or creating `SSLContext` objects from any registered bundle — useful when you need to configure outbound HTTP clients with the same certificate.
- `bundle.createSslContext()` returns a standard `javax.net.ssl.SSLContext` you can pass to `OkHttpClient`, `HttpClient`, or any other Java HTTP client.
- For `RestClient` HTTPS with the same bundle, use:
  ```java
  RestClient.builder().requestFactory(
      new JdkClientHttpRequestFactory(
          HttpClient.newBuilder()
              .sslContext(sslBundles.getBundle("myapp").createSslContext())
              .build()))
      .build();
  ```

## 7. Gotchas & takeaways

> Once you set `server.ssl.bundle` (or any `server.ssl.*` property), the embedded server switches to HTTPS only. Plain HTTP port 8080 stops working. Add a second connector via `WebServerFactoryCustomizer` if you need both.

> `spring.ssl.bundle.jks.*` is for JKS/PKCS12 keystores. For PEM certificates (common in Kubernetes), use `spring.ssl.bundle.pem.*` with `certificate` and `private-key` file paths.

- Bundle names are arbitrary strings — use names that describe the purpose (`internal-ca`, `client-auth`) not the technology.
- `SslBundleRegistry` (injected as `SslBundles`) lets you register bundles programmatically at runtime — useful for certificate rotation without restart.
- Passwords can be externalised to environment variables: `spring.ssl.bundle.jks.myapp.keystore.password=${KEYSTORE_PASSWORD}`.
- Self-signed certs work for development; always use a CA-signed cert in production to avoid disabling certificate validation.
