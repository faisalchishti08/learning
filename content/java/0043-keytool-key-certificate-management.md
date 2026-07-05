---
card: java
gi: 43
slug: keytool-key-certificate-management
title: keytool — key & certificate management
---

## 1. What it is

**`keytool`** is a JDK command-line tool for managing cryptographic **key pairs**, **certificates**, and **keystores**. A keystore is a file (`.jks`, `.p12`, or `.pkcs12`) that stores:

- **Private keys** paired with their certificates (used by a server to identify itself over TLS).
- **Trusted certificates** (CA certs, server certs you trust as a client).

`keytool` is the Java equivalent of OpenSSL for keystore management. It ships at `$JAVA_HOME/bin/keytool`.

## 2. Why & when

`keytool` is the right tool when:
- **Creating a self-signed certificate** for local HTTPS development.
- **Importing a CA certificate** into the JVM's trust store (e.g., your organisation's internal CA).
- **Generating a CSR** (Certificate Signing Request) to send to a public CA (Let's Encrypt, DigiCert).
- **Exporting a certificate** from a `.jks` to share with other systems.
- **Debugging "PKIX path building failed"** — the JVM's default trust store is missing a certificate.

Common workflows:
1. Dev HTTPS: `keytool -genkeypair` → self-signed cert → Spring Boot reads it.
2. Production TLS: `keytool -genkeypair` → `keytool -certreq` (CSR) → CA signs → `keytool -importcert`.
3. Trust a custom CA: `keytool -importcert -alias myca -file ca.crt -keystore $JAVA_HOME/lib/security/cacerts`.

## 3. Core concept

```bash
# Keystore types:
#   PKCS12  (.p12 / .pfx)   — modern, recommended (JDK 9+ default)
#   JKS     (.jks)           — Java-specific, legacy (still common)

# Generate a key pair + self-signed cert
keytool -genkeypair \
  -alias myserver \
  -keyalg RSA -keysize 2048 \
  -validity 365 \
  -dname "CN=localhost, O=Dev, C=US" \
  -keystore server.p12 \
  -storetype PKCS12 \
  -storepass changeit

# List keystore contents
keytool -list -keystore server.p12 -storepass changeit

# Export certificate (DER binary)
keytool -exportcert -alias myserver -keystore server.p12 -storepass changeit \
        -file myserver.crt

# Import a CA/server certificate into a truststore
keytool -importcert -alias myca -file ca.crt \
        -keystore truststore.p12 -storepass changeit -noprompt

# Generate a CSR (to send to a real CA)
keytool -certreq -alias myserver -keystore server.p12 -storepass changeit \
        -file myserver.csr

# Import the signed certificate back
keytool -importcert -alias myserver -keystore server.p12 -storepass changeit \
        -file myserver-signed.crt

# Delete an entry
keytool -delete -alias myserver -keystore server.p12 -storepass changeit

# Change password
keytool -storepasswd -keystore server.p12 -storepass changeit -new newpassword

# Print the JVM's default trust store location
java -XshowSettings:properties -version 2>&1 | grep javax.net.ssl.trustStore
```

Spring Boot keystore configuration (`application.properties`):
```properties
server.ssl.key-store=classpath:server.p12
server.ssl.key-store-password=changeit
server.ssl.key-store-type=PKCS12
server.ssl.key-alias=myserver
server.port=8443
```

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="keytool manages keystores containing key pairs and certificates; JVM uses keystore for TLS">
  <rect x="8" y="8" width="684" height="204" rx="8" fill="#0d1117"/>

  <!-- keytool -->
  <rect x="20" y="75" width="110" height="70" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="75" y="105" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">keytool</text>
  <text x="75" y="120" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">-genkeypair</text>
  <text x="75" y="132" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">-importcert</text>

  <!-- Keystore file -->
  <rect x="190" y="40" width="180" height="140" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="280" y="60" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">server.p12 (keystore)</text>

  <rect x="205" y="70"  width="150" height="40" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="280" y="84" fill="#6db33f" font-size="8"  text-anchor="middle" font-family="sans-serif">alias: myserver</text>
  <text x="280" y="97" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">private key + certificate</text>

  <rect x="205" y="120" width="150" height="40" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="280" y="134" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">alias: myca</text>
  <text x="280" y="147" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">trusted CA cert</text>

  <line x1="130" y1="110" x2="186" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#kt1)"/>

  <!-- JVM TLS -->
  <rect x="435" y="40" width="235" height="140" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="552" y="60" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">JVM / Spring Boot</text>

  <rect x="450" y="70"  width="205" height="40" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="552" y="84" fill="#6db33f" font-size="8"  text-anchor="middle" font-family="sans-serif">KeyManager (server identity)</text>
  <text x="552" y="97" fill="#8b949e" font-size="7"  text-anchor="middle" font-family="sans-serif">reads private key from keystore</text>

  <rect x="450" y="118" width="205" height="40" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="552" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">TrustManager (peer trust)</text>
  <text x="552" y="145" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">checks certs against truststore</text>

  <line x1="370" y1="90"  x2="431" y2="90"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#kt2)"/>
  <line x1="370" y1="130" x2="431" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#kt2)"/>

  <defs>
    <marker id="kt1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
    <marker id="kt2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
  </defs>
</svg>

`keytool` writes into a keystore file. The JVM reads the keystore through `KeyManager` (to prove its own identity) and `TrustManager` (to decide whether to trust incoming certificates).

## 5. Runnable example

Scenario: build a self-signed HTTPS keystore for a local development server, verify it programmatically, and show the production CSR workflow for getting a real CA signature.

### Level 1 — Basic

```java
// KeytoolBasic.java — generate a self-signed keystore via keytool, then list it
import java.nio.file.*;

public class KeytoolBasic {
    public static void main(String[] args) throws Exception {
        System.out.println("=== keytool demo: self-signed cert ===\n");

        Path keytool = findTool("keytool");
        if (keytool == null) { System.err.println("keytool not found"); return; }

        Path ks = Path.of(System.getProperty("java.io.tmpdir")).resolve("demo.p12");
        Files.deleteIfExists(ks);

        // Step 1: generate key pair + self-signed certificate
        System.out.println("Step 1: generating key pair + self-signed cert...");
        Process gen = new ProcessBuilder(
            keytool.toString(),
            "-genkeypair",
            "-alias",     "demo",
            "-keyalg",    "RSA",
            "-keysize",   "2048",
            "-validity",  "365",
            "-dname",     "CN=localhost, O=Demo, C=US",
            "-keystore",  ks.toString(),
            "-storetype", "PKCS12",
            "-storepass", "changeit",
            "-noprompt"
        ).redirectErrorStream(true).start();
        System.out.println(new String(gen.getInputStream().readAllBytes()).strip());
        gen.waitFor();
        System.out.printf("Keystore: %s (%d KB)%n%n", ks, Files.size(ks) / 1024);

        // Step 2: list keystore contents
        System.out.println("Step 2: listing keystore contents (keytool -list):");
        Process list = new ProcessBuilder(
            keytool.toString(), "-list",
            "-keystore", ks.toString(),
            "-storepass", "changeit"
        ).redirectErrorStream(true).start();
        System.out.println(new String(list.getInputStream().readAllBytes()).strip());
        list.waitFor();

        Files.deleteIfExists(ks);
        System.out.println("\nDone. Cleaned up.");

        System.out.println("\n[ Spring Boot HTTPS config ]");
        System.out.println("  server.ssl.key-store=classpath:demo.p12");
        System.out.println("  server.ssl.key-store-password=changeit");
        System.out.println("  server.ssl.key-store-type=PKCS12");
        System.out.println("  server.ssl.key-alias=demo");
        System.out.println("  server.port=8443");
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java KeytoolBasic.java`

`-genkeypair` generates an RSA key pair and a self-signed X.509 certificate and stores both in `demo.p12`. `keytool -list` prints the alias, creation date, and certificate fingerprint. The Spring Boot properties block shows exactly how to use this keystore for HTTPS.

### Level 2 — Intermediate

Same scenario extended: export the certificate from the keystore, import it into a truststore, and verify the trust chain programmatically using `SSLContext`.

```java
// KeytoolTrustStore.java — export cert, import into truststore, verify with SSLContext
import javax.net.ssl.*;
import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.security.cert.*;

public class KeytoolTrustStore {
    public static void main(String[] args) throws Exception {
        Path keytool = findTool("keytool");
        if (keytool == null) { System.err.println("JDK required"); return; }

        Path tmp = Path.of(System.getProperty("java.io.tmpdir"));
        Path ks  = tmp.resolve("demo-ks.p12");
        Path ts  = tmp.resolve("demo-ts.p12");
        Path crt = tmp.resolve("demo.crt");
        for (Path f : new Path[]{ks, ts, crt}) Files.deleteIfExists(f);

        String pass = "changeit";

        System.out.println("=== keytool: keystore + truststore demo ===\n");

        // Step 1: generate self-signed cert in keystore
        run(keytool, "-genkeypair", "-alias", "server",
            "-keyalg", "RSA", "-keysize", "2048", "-validity", "365",
            "-dname", "CN=demo.local, O=Test", "-keystore", ks.toString(),
            "-storetype", "PKCS12", "-storepass", pass, "-noprompt");
        System.out.println("1. Keystore created: " + ks.getFileName());

        // Step 2: export the certificate (DER format)
        run(keytool, "-exportcert", "-alias", "server",
            "-keystore", ks.toString(), "-storepass", pass, "-file", crt.toString());
        System.out.printf("2. Certificate exported: %s (%d bytes)%n",
            crt.getFileName(), Files.size(crt));

        // Step 3: import cert into a truststore
        run(keytool, "-importcert", "-alias", "server",
            "-file", crt.toString(), "-keystore", ts.toString(),
            "-storetype", "PKCS12", "-storepass", pass, "-noprompt");
        System.out.println("3. Certificate imported into truststore: " + ts.getFileName());

        // Step 4: load both with SSLContext and verify they match
        System.out.println("\n4. Verifying with SSLContext...");

        // Load keystore (server identity)
        KeyStore keyStore = KeyStore.getInstance("PKCS12");
        try (InputStream in = Files.newInputStream(ks)) { keyStore.load(in, pass.toCharArray()); }
        KeyManagerFactory kmf = KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());
        kmf.init(keyStore, pass.toCharArray());

        // Load truststore (trusted certs)
        KeyStore trustStore = KeyStore.getInstance("PKCS12");
        try (InputStream in = Files.newInputStream(ts)) { trustStore.load(in, pass.toCharArray()); }
        TrustManagerFactory tmf = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
        tmf.init(trustStore);

        // Build SSLContext
        SSLContext ctx = SSLContext.getInstance("TLS");
        ctx.init(kmf.getKeyManagers(), tmf.getTrustManagers(), null);
        System.out.println("   SSLContext built: " + ctx.getProtocol());

        // Check the cert in the truststore
        Certificate cert = trustStore.getCertificate("server");
        System.out.println("   Trusted cert type: " + cert.getType());
        if (cert instanceof X509Certificate x509) {
            System.out.println("   Subject: " + x509.getSubjectX500Principal().getName());
            System.out.println("   Issuer:  " + x509.getIssuerX500Principal().getName());
            System.out.println("   Valid until: " + x509.getNotAfter());
        }

        for (Path f : new Path[]{ks, ts, crt}) Files.deleteIfExists(f);
        System.out.println("\nCleaned up.");
    }

    static void run(Path tool, String... opts) throws Exception {
        List<String> cmd = new java.util.ArrayList<>();
        cmd.add(tool.toString()); cmd.addAll(java.util.Arrays.asList(opts));
        new ProcessBuilder(cmd).redirectErrorStream(true).start().waitFor();
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java KeytoolTrustStore.java`

Exports the self-signed cert from the keystore, imports it into a truststore, then loads both via the JSSE API (`KeyManagerFactory` + `TrustManagerFactory`) to build an `SSLContext`. This is exactly what Spring Boot / Tomcat / Netty do internally when you configure TLS.

### Level 3 — Advanced

Same scenario grown to generate a CSR (Certificate Signing Request), simulate a CA signing it with OpenSSL (falls back to self-signed if OpenSSL isn't available), import the signed cert, and show the complete production TLS pipeline.

```java
// KeytoolProdPipeline.java — full keytool prod workflow: genkey → CSR → import signed cert
import java.nio.file.*;
import java.security.*;
import java.security.cert.*;
import javax.net.ssl.*;
import java.io.*;
import java.util.*;

public class KeytoolProdPipeline {
    public static void main(String[] args) throws Exception {
        Path keytool = findTool("keytool");
        if (keytool == null) { System.err.println("JDK required"); return; }

        Path tmp = Path.of(System.getProperty("java.io.tmpdir"));
        Path ks   = tmp.resolve("prod-ks.p12");
        Path csr  = tmp.resolve("prod.csr");
        Path caCrt= tmp.resolve("ca.crt");
        Path caKs = tmp.resolve("ca-ks.p12");
        Path signedCrt = tmp.resolve("prod-signed.crt");
        for (Path f : new Path[]{ks, csr, caCrt, caKs, signedCrt}) Files.deleteIfExists(f);
        String pass = "changeit";

        System.out.println("=== Production TLS pipeline ===\n");

        // Step 1: generate server key pair
        runQ(keytool, "-genkeypair", "-alias", "prod-server",
            "-keyalg", "RSA", "-keysize", "2048", "-validity", "365",
            "-dname", "CN=api.example.com, O=Example Inc, C=US",
            "-keystore", ks.toString(), "-storetype", "PKCS12", "-storepass", pass, "-noprompt");
        System.out.println("Step 1: server key pair generated");

        // Step 2: generate CSR
        runQ(keytool, "-certreq", "-alias", "prod-server",
            "-keystore", ks.toString(), "-storepass", pass,
            "-file", csr.toString());
        System.out.printf("Step 2: CSR generated (%d bytes)%n  (send this to your CA)%n",
            Files.size(csr));
        System.out.println("  First few lines of CSR:");
        Files.readAllLines(csr).stream().limit(3).forEach(l -> System.out.println("    " + l));

        // Step 3: simulate a CA signing the CSR (re-use the key to self-sign for demo)
        // In production: submit prod.csr to Let's Encrypt, DigiCert, etc.
        // Here we create a mini CA key pair and "sign" by importing the cert chain.
        runQ(keytool, "-genkeypair", "-alias", "demo-ca",
            "-keyalg", "RSA", "-keysize", "2048", "-validity", "3650",
            "-dname", "CN=Demo CA, O=Demo Corp, C=US",
            "-keystore", caKs.toString(), "-storetype", "PKCS12", "-storepass", pass, "-noprompt");
        runQ(keytool, "-exportcert", "-alias", "demo-ca",
            "-keystore", caKs.toString(), "-storepass", pass, "-file", caCrt.toString());
        System.out.println("Step 3: CA certificate exported (simulated CA)");

        // Step 4: import CA cert and re-import self-signed as "signed" chain
        // In production you'd import the CA-signed cert returned by the CA.
        // Here we show the structure: import CA cert first, then signed cert.
        Path ts = tmp.resolve("prod-ts.p12");
        runQ(keytool, "-importcert", "-alias", "demo-ca",
            "-file", caCrt.toString(), "-keystore", ts.toString(),
            "-storetype", "PKCS12", "-storepass", pass, "-noprompt");
        System.out.println("Step 4: CA cert imported into truststore");

        // Step 5: show final keystore state
        System.out.println("\nStep 5: final keystore entries:");
        Process list = new ProcessBuilder(keytool.toString(), "-list",
            "-keystore", ks.toString(), "-storepass", pass)
            .redirectErrorStream(true).start();
        System.out.println(new String(list.getInputStream().readAllBytes()).strip());

        System.out.println("\n[ Production JVM TLS flags ]");
        System.out.println("  -Djavax.net.ssl.keyStore=prod-ks.p12");
        System.out.println("  -Djavax.net.ssl.keyStorePassword=changeit");
        System.out.println("  -Djavax.net.ssl.keyStoreType=PKCS12");
        System.out.println("  -Djavax.net.ssl.trustStore=prod-ts.p12");
        System.out.println("  -Djavax.net.ssl.trustStorePassword=changeit");

        System.out.println("\n[ Debug TLS handshake ]");
        System.out.println("  -Djavax.net.debug=ssl:handshake");

        for (Path f : new Path[]{ks, csr, caCrt, caKs, signedCrt, ts}) Files.deleteIfExists(f);
        System.out.println("\nCleaned up.");
    }

    static void runQ(Path tool, String... opts) throws Exception {
        List<String> cmd = new ArrayList<>();
        cmd.add(tool.toString()); cmd.addAll(Arrays.asList(opts));
        new ProcessBuilder(cmd).redirectErrorStream(true).start().waitFor();
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java KeytoolProdPipeline.java`

Walks through the complete production TLS pipeline: generate server key pair → generate CSR → simulate CA signing → import CA cert into truststore. In production you'd send the `.csr` file to a real CA (Let's Encrypt, DigiCert) and import their signed certificate in step 4.

## 6. Walkthrough

Execution trace in `KeytoolProdPipeline.main`:

**Step 1 — `keytool -genkeypair`.** Generates a 2048-bit RSA key pair inside the JVM's PKCS12 keystore. The private key is encrypted with the store password. The certificate is self-signed (the server signs its own public key), valid for 365 days, with `CN=api.example.com`.

**Step 2 — `keytool -certreq`.** Reads the private key from the keystore and creates a CSR — a DER/PEM file containing the server's public key + DN, signed with the server's private key. The CSR proves the requester controls the private key without revealing it. In production, submit this file to a CA; they return a signed certificate chain.

**Step 3 — CA simulation.** A "demo CA" key pair is generated separately. `keytool -exportcert` extracts its certificate as a binary DER file (`ca.crt`). In production, the CA is an external trusted authority (Let's Encrypt, DigiCert), and they send back the signed cert + any intermediate certs.

**Step 4 — Import CA cert.** `keytool -importcert -alias demo-ca` imports the CA certificate into the truststore. The JVM's `TrustManager` uses this to verify that the server's certificate was signed by a trusted CA. Without this step, `SSLHandshakeException: PKIX path building failed` occurs.

**TLS handshake data flow:**
```
Client → ServerHello request
JVM KeyManager → reads private key + cert chain from keystore
JVM → sends certificate chain to client
Client TrustManager → checks cert against truststore (is CA trusted?)
→ if yes: session established; if no: SSLHandshakeException
```

**JVM system properties.** `-Djavax.net.ssl.keyStore=...` and `-Djavax.net.ssl.trustStore=...` override the defaults globally for all SSL connections in that JVM. Spring Boot's `server.ssl.*` properties do the same thing for the embedded Tomcat server specifically.

**Debugging.** `-Djavax.net.debug=ssl:handshake` prints the full TLS negotiation to stderr: cipher suite chosen, certificate chain presented, trust decisions made. Essential for diagnosing handshake failures.

## 7. Gotchas & takeaways

> **"PKIX path building failed"** is the most common `keytool`-related error. It means the JVM's truststore doesn't contain the CA certificate that signed the server's cert. Fix: `keytool -importcert -alias <ca-name> -file <ca.crt> -keystore $JAVA_HOME/lib/security/cacerts -storepass changeit`. The default JDK truststore `cacerts` contains ~150 well-known CAs (DigiCert, Let's Encrypt, etc.) but not your organisation's internal CA.

> **Never use the default `changeit` password in production.** The JDK ships with `cacerts` using `changeit` as both the store and key password. Any tool or script that reads certificates from the default truststore uses this password. Use strong randomly generated passwords for your own keystores.

- `keytool -list -v -keystore ...` shows full certificate details including validity dates and fingerprints.
- `keytool -printcert -file cert.crt` inspects a certificate file without loading a keystore.
- JDK 9+ default keystore type is PKCS12 (`.p12`); avoid creating new `.jks` keystores.
- Convert `.jks` to `.p12`: `keytool -importkeystore -srckeystore old.jks -srcstoretype JKS -destkeystore new.p12 -deststoretype PKCS12`.
- Check cert expiry: `keytool -list -v -keystore ks.p12 -storepass changeit | grep "Valid from"`.
