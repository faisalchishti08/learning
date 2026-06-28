---
card: spring-boot
gi: 72
slug: encrypting-properties-external-secrets-config-import
title: Encrypting properties / external secrets (config import)
---

## 1. What it is

Spring Boot itself has **no built-in property encryption**. What it provides is the plumbing — a flexible config-loading model — that plugs into tools that do. Three patterns are widely used:

1. **Jasypt** (`jasypt-spring-boot`) — a library that decrypts values inline inside `application.properties` / `.yml`. Values are wrapped as `ENC(ciphertext)`.
2. **Spring Cloud Config** — a config server that stores `{cipher}ciphertext` values and decrypts them before sending properties to clients.
3. **External secret managers** — AWS Secrets Manager, HashiCorp Vault, Azure Key Vault, etc. — accessed via `spring.config.import` using a custom URI scheme (`vault://...`, `aws-secretsmanager://...`). The secret manager returns plaintext to the application; encryption at rest is the provider's responsibility.

All three let you keep secrets out of your source repository and your plaintext config files.

## 2. Why & when

Hardcoding `db.password=s3cr3t` in `application.properties` and committing it to git is a security incident waiting to happen. The question is not *whether* to protect secrets but *which pattern fits your setup*:

| Pattern | Best fit |
|---------|---------|
| **Jasypt** | Small team, no cloud infra, quick start. Encrypted values sit in the same properties file. |
| **Spring Cloud Config** | You already run (or want) a centralised config server. One source of truth for all services. |
| **AWS Secrets Manager / Vault** | Cloud-native or enterprise setup. Secrets are managed by a dedicated secrets platform with audit logs, rotation, and access policies. |

Use Jasypt when you want encryption without extra infrastructure. Use a secret manager when your organisation already has one, or when you need audit trails and automatic rotation.

## 3. Core concept

Analogy: think of your application like a post office. The application needs a package (the secret). Jasypt is like a locked mailbox — the package was encrypted before being placed in your local mailbox and your app has the key. Spring Cloud Config is like a secure courier — it carries the package from a central warehouse and decrypts it in transit before handing it over. A secret manager (Vault, AWS SM) is like a bank vault — the app shows its ID, the vault hands over exactly what the app is authorised to see, fully decrypted and audited.

**Jasypt pattern:**
```properties
# application.properties
db.password=ENC(Bf4yth7i8hGPxQy2vv+IiA==)
jasypt.encryptor.password=${JASYPT_MASTER_KEY}   # never commit the master key
```

**Spring Cloud Config encrypted property:**
```properties
# stored on the config server
db.password={cipher}AQBe3x9...
# the server decrypts this before serving it to the client
```

**Vault / AWS Secrets Manager via `spring.config.import`:**
```properties
# application.properties
spring.config.import=vault://secret/myapp,optional:file:./local.properties
# Spring pulls /secret/myapp from Vault at startup; keys become regular properties
```

The external secret managers require a matching Spring extension on the classpath (Spring Cloud Vault, Spring Cloud AWS, etc.) that registers a custom `ConfigDataLocationResolver` for the URI scheme.

## 4. Diagram

<svg viewBox="0 0 700 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three secret patterns: Jasypt inline decryption, Spring Cloud Config server, and external secret managers via spring.config.import">
  <rect width="700" height="300" rx="10" fill="#0d1117"/>

  <!-- Pattern 1: Jasypt -->
  <rect x="15" y="15" width="195" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="113" y="37" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">1. Jasypt (inline)</text>
  <rect x="28" y="46" width="168" height="28" rx="4" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="38" y="65" fill="#e6edf3" font-size="9" font-family="monospace">db.password=ENC(Bf4y...)</text>
  <text x="113" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">↓ master key from env var</text>
  <rect x="28" y="100" width="168" height="28" rx="4" fill="#161b22" stroke="#6db33f" stroke-width="1"/>
  <text x="38" y="119" fill="#6db33f" font-size="9" font-family="monospace">db.password → s3cr3t</text>
  <text x="113" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">decrypted at startup, in-process</text>

  <!-- Pattern 2: Spring Cloud Config -->
  <rect x="225" y="15" width="220" height="130" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="335" y="37" fill="#79c0ff" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">2. Spring Cloud Config</text>
  <rect x="238" y="48" width="93" height="42" rx="4" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="285" y="66" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Config Server</text>
  <text x="285" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">{cipher}AQB...</text>
  <line x1="335" y1="68" x2="358" y2="68" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sa)"/>
  <rect x="360" y="48" width="72" height="42" rx="4" fill="#161b22" stroke="#79c0ff" stroke-width="1"/>
  <text x="396" y="66" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">decrypts</text>
  <text x="396" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">in server</text>
  <text x="335" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">↓ plaintext delivered to app</text>
  <rect x="238" y="120" width="193" height="20" rx="3" fill="#161b22" stroke="#79c0ff" stroke-width="1"/>
  <text x="335" y="134" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">db.password → s3cr3t</text>

  <!-- Pattern 3: Vault / AWS SM -->
  <rect x="460" y="15" width="225" height="130" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="573" y="37" fill="#f0883e" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">3. Vault / AWS SM</text>
  <rect x="473" y="48" width="195" height="24" rx="3" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="570" y="64" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">spring.config.import=vault://secret/app</text>
  <text x="573" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">↓ app authenticates to Vault/SM</text>
  <rect x="473" y="97" width="195" height="34" rx="3" fill="#161b22" stroke="#f0883e" stroke-width="1"/>
  <text x="570" y="113" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">Secret manager returns plaintext</text>
  <text x="570" y="127" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">encrypted at rest, audited</text>

  <!-- Spring Environment at bottom -->
  <rect x="200" y="175" width="300" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="197" fill="#6db33f" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">Spring Environment</text>
  <text x="350" y="215" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">plain-text properties — same for all patterns</text>

  <!-- arrows down to environment -->
  <line x1="113" y1="148" x2="265" y2="175" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sb)"/>
  <line x1="335" y1="148" x2="350" y2="175" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sc)"/>
  <line x1="573" y1="148" x2="435" y2="175" stroke="#f0883e" stroke-width="1.5" marker-end="url(#sd)"/>

  <!-- Key comparison bar -->
  <rect x="15" y="243" width="670" height="42" rx="6" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="35" y="260" fill="#6db33f" font-size="10" font-family="sans-serif">Jasypt: no infra, master key in env var</text>
  <text x="35" y="278" fill="#8b949e" font-size="9" font-family="sans-serif">| Spring CC: one server many apps</text>
  <text x="270" y="260" fill="#79c0ff" font-size="10" font-family="sans-serif">| Vault/SM: audit + rotation built in</text>
  <text x="270" y="278" fill="#8b949e" font-size="9" font-family="sans-serif">| app only needs auth token / IAM role</text>

  <defs>
    <marker id="sa" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="sb" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="sc" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="sd" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

All three patterns deliver plaintext to Spring's `Environment`. The difference is where decryption happens and who manages the encryption keys.

## 5. Runnable example

```java
// File: JasyptDemo.java
// Demonstrates the Jasypt pattern — the lightest-weight option with no extra infra.
// Requires: add to build.gradle:
//   implementation 'com.github.ulisesbocchio:jasypt-spring-boot-starter:3.0.5'
//
// Run with: JASYPT_ENCRYPTOR_PASSWORD=masterKey123 ./gradlew bootRun
//
// src/main/resources/application.properties:
//   jasypt.encryptor.algorithm=PBEWithMD5AndDES
//   app.name=MyService
//   # Generate encrypted value with the Jasypt CLI or the snippet below:
//   app.db.password=ENC(zSgcvp5VKv5dGJlMzwS0lQ==)
//   app.api.key=ENC(KsdW3Pr4Hm8mN7jzQ9vCaA==)
//   # Master key comes from env var — NEVER hardcode it here

package com.example;

import com.ulisesbocchio.jasyptspringboot.annotation.EnableEncryptableProperties;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

// @EnableEncryptableProperties is optional when using the starter — auto-configured
@SpringBootApplication
@EnableEncryptableProperties
public class JasyptDemo implements CommandLineRunner {

    @Value("${app.name}")
    private String appName;

    // Spring sees "ENC(...)" and Jasypt decrypts it transparently
    @Value("${app.db.password}")
    private String dbPassword;

    @Value("${app.api.key}")
    private String apiKey;

    public static void main(String[] args) {
        SpringApplication.run(JasyptDemo.class, args);
    }

    @Override
    public void run(String... args) {
        System.out.println("app.name      : " + appName);
        // In real code you would NOT print secrets — this is for demo only
        System.out.println("db.password   : " + dbPassword);
        System.out.println("api.key       : " + apiKey);
    }
}

// ---- Utility: encrypt a value with Jasypt programmatically ----
// Paste this into a test or main method to generate ENC(...) values.
//
// import org.jasypt.encryption.pbe.StandardPBEStringEncryptor;
//
// StandardPBEStringEncryptor enc = new StandardPBEStringEncryptor();
// enc.setAlgorithm("PBEWithMD5AndDES");
// enc.setPassword("masterKey123");           // same as JASYPT_ENCRYPTOR_PASSWORD
// System.out.println(enc.encrypt("s3cr3t")); // prints base64 ciphertext
// System.out.println(enc.encrypt("abc123")); // wrap result in ENC(...)
```

**How to run:**
1. Add the Jasypt starter to `build.gradle` (shown in comment).
2. Run the encryption utility snippet once to generate your `ENC(...)` values.
3. Paste the `ENC(...)` values into `application.properties`.
4. Start the app with the master key in the environment: `JASYPT_ENCRYPTOR_PASSWORD=masterKey123 ./gradlew bootRun`.
5. The app prints the decrypted values — Spring never sees the raw ciphertext.

## 6. Walkthrough

- **`jasypt-spring-boot-starter`** registers a `EncryptablePropertySource` wrapper around every Spring property source. Whenever Spring reads a value that starts with `ENC(` and ends with `)`, Jasypt intercepts it, decrypts it using the master key, and returns the plaintext.
- **`JASYPT_ENCRYPTOR_PASSWORD=masterKey123`** — Jasypt reads this env var (mapped to `jasypt.encryptor.password`) to unlock the cipher. The master key must never appear in `application.properties` or version control; it is injected at deploy time via a secret in your CI/CD pipeline or a mounted Kubernetes Secret.
- **`@Value("${app.db.password}")`** — from the bean's perspective, this is a normal string injection. Jasypt's interception is transparent; no API call is required.
- **Vault pattern (reference)** — if you use HashiCorp Vault, you would instead add `spring-cloud-starter-vault-config`, set `spring.config.import=vault://secret/myapp` in `application.properties`, and configure `spring.cloud.vault.uri` + an auth token or Kubernetes service account. Spring Cloud Vault registers a `ConfigDataLocationResolver` for the `vault://` scheme and fetches secrets at startup.
- **AWS Secrets Manager pattern (reference)** — add `spring-cloud-starter-aws-secrets-manager-config`, then `spring.config.import=aws-secretsmanager:///myapp/prod`. The library uses your AWS IAM credentials (from the environment, instance profile, or EKS service account) to call the Secrets Manager API and loads the returned JSON as Spring properties.
- **Why all three look the same to beans** — regardless of where decryption happens, by the time the `ApplicationContext` creates beans and injects `@Value`, the `Environment` holds plain strings. Switching from Jasypt to Vault is a config and dependency change — zero Java code changes in your beans.

## 7. Gotchas & takeaways

> The Jasypt master key (`jasypt.encryptor.password`) is itself a secret. If you put it in `application.properties` in plain text, you have gained nothing. It must come from an environment variable, a system property passed to the JVM (`-Djasypt.encryptor.password=...`), or a secret manager — never from a file you commit.

> `{cipher}` values in Spring Cloud Config are decrypted **on the server**, not the client. If your config server has TLS disabled or your network is not encrypted, the plaintext travels over the wire in the clear between the server and your application. Secure the transport layer.

- Never commit encrypted values without also documenting (separately and securely) how to obtain the master key. An `ENC(...)` blob with no accessible key is just data loss.
- Jasypt's default algorithm (`PBEWithMD5AndDES`) is legacy. Use `PBEWITHHMACSHA512ANDAES_256` for new projects; it requires the JCE Unlimited Strength policy (included by default in JDK 9+).
- Secret managers (Vault, AWS SM, Azure KV) add rotation support: the secret manager can update a secret and, with a sidecar or re-fetch on startup, your application can pick up new credentials without a redeploy.
- `spring.config.import=vault://...` requires the matching Spring Cloud extension on the classpath. A missing extension means Boot cannot resolve the `vault://` scheme and will throw `ConfigDataLocationNotFoundException` at startup.
- For local development with a Vault or AWS SM import, wrap it with `optional:` (`optional:aws-secretsmanager:///myapp/prod`) so developers without cloud credentials can still start the app.
