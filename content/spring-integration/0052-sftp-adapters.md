---
card: spring-integration
gi: 52
slug: sftp-adapters
title: "SFTP adapters"
---

## 1. What it is

SFTP support provides the same inbound-synchronize/outbound-upload adapter pair as FTP (card 0051) — `SftpInboundFileSynchronizingMessageSource` and `SftpMessageHandler` — but built on SSH File Transfer Protocol instead of FTP+TLS. Despite the similar name, SFTP is a fundamentally different protocol from FTPS: it runs entirely over a single SSH connection (the same protocol used for secure shell access), rather than being plain FTP wrapped in a separate TLS layer, and it uses SSH's own authentication mechanisms (password or public-key) rather than FTP's.

## 2. Why & when

You reach for SFTP adapters specifically when the remote system speaks SSH-based file transfer rather than FTP-family protocols:

- **A partner or internal system only exposes SFTP access** — extremely common in enterprise environments, since SFTP reuses existing SSH infrastructure (the same servers, key management, and firewall rules already used for secure shell access) rather than requiring a separate FTP/FTPS service to be stood up and secured independently.
- **You want to authenticate with SSH key pairs rather than passwords** — SFTP's `SessionFactory` configuration supports public-key authentication natively, fitting naturally into infrastructure that already manages SSH keys for other purposes, without needing a separate credential-management story for file transfer specifically.
- **Security posture requires everything to run over a single, well-understood encrypted channel** — SFTP's single-connection SSH model is generally considered simpler to firewall and reason about securely than FTP/FTPS's more complex multi-connection (control + data channel) model.

## 3. Core concept

Think of the difference between SFTP and FTPS like two different secure ways to hand off a package: FTPS is like handing the package through a bank's existing secure pass-through window (FTP's control/data channel structure) that's simply been retrofitted with better locks (TLS); SFTP is like handing the entire package through a courier who already has your building's master security badge (an SSH connection) and uses that single, unified access method for everything — no separate retrofit, just reusing infrastructure that's already secure and already trusted.

```java
@Bean
public SessionFactory<ChannelSftp.LsEntry> sftpSessionFactory() {
    DefaultSftpSessionFactory factory = new DefaultSftpSessionFactory();
    factory.setHost("sftp.partner.example.com");
    factory.setUser("integration-user");
    factory.setPrivateKey(new FileSystemResource("/keys/integration-user.pem")); // SSH key auth, not a password
    return factory;
}

@Bean
@InboundChannelAdapter(value = "incomingSftpFiles", poller = @Poller(fixedDelay = "5000"))
public SftpInboundFileSynchronizingMessageSource sftpInbound(SessionFactory<ChannelSftp.LsEntry> sessionFactory) {
    SftpInboundFileSynchronizingMessageSource source = new SftpInboundFileSynchronizingMessageSource(
        new SftpInboundFileSynchronizer(sessionFactory));
    source.setLocalDirectory(new File("/local/staging"));
    return source;
}
```

The class names and overall shape mirror FTP's adapters almost exactly (card 0051) — the meaningful difference is entirely in the `SessionFactory` implementation and its SSH-specific connection/authentication configuration.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SFTP adapters mirror FTP's structure but authenticate and transfer over a single SSH connection instead of FTP's separate control and data channels, often using key-based rather than password authentication">
  <rect x="20" y="50" width="160" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="100" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">remote SFTP server</text>
  <text x="100" y="87" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">(same daemon as SSH access)</text>

  <line x1="180" y1="70" x2="260" y2="70" stroke="#6db33f" stroke-width="2" marker-end="url(#sf1)"/>
  <text x="220" y="55" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">single SSH connection</text>
  <text x="220" y="90" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">key or password auth</text>

  <rect x="270" y="50" width="150" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="345" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">local staging dir</text>

  <line x1="420" y1="70" x2="480" y2="70" stroke="#79c0ff" stroke-width="2" marker-end="url(#sf2)"/>

  <rect x="490" y="50" width="130" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">flow's channel</text>

  <defs>
    <marker id="sf1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="sf2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Structurally identical to FTP's adapter pair (card 0051); the underlying transport and authentication mechanism is what genuinely differs.

## 5. Runnable example

The scenario: comparing SFTP's key-based authentication concept against FTP's password-based one, then the same synchronization mechanics reused, and finally handling an SFTP-specific concern — host key verification — that FTP/FTPS doesn't have an equivalent of.

### Level 1 — Basic

```java
// KeyVsPasswordAuthDemo.java
// Illustrates the authentication CONCEPT difference between SFTP (key-based) and FTP (password-based),
// since actually establishing an SSH connection requires a real SFTP server.
import java.util.Map;

public class KeyVsPasswordAuthDemo {
    record FtpCredentials(String username, String password) {}
    record SftpCredentials(String username, String privateKeyPath) {}

    static boolean authenticateFtp(FtpCredentials creds, Map<String, String> knownPasswords) {
        return creds.password().equals(knownPasswords.get(creds.username()));
    }

    static boolean authenticateSftp(SftpCredentials creds, Map<String, String> knownKeyFingerprints) {
        // in reality: the private key at privateKeyPath is used to sign a challenge — here, simplified to a lookup
        return creds.privateKeyPath().equals(knownKeyFingerprints.get(creds.username()));
    }

    public static void main(String[] args) {
        Map<String, String> ftpPasswords = Map.of("integration-user", "s3cr3t");
        Map<String, String> sftpKeys = Map.of("integration-user", "/keys/integration-user.pem");

        System.out.println("FTP auth (password-based): "
            + authenticateFtp(new FtpCredentials("integration-user", "s3cr3t"), ftpPasswords));
        System.out.println("SFTP auth (key-based): "
            + authenticateSftp(new SftpCredentials("integration-user", "/keys/integration-user.pem"), sftpKeys));
    }
}
```

How to run: `java KeyVsPasswordAuthDemo.java`. Expected output: `FTP auth (password-based): true` then `SFTP auth (key-based): true` — both succeed here, but the underlying mechanism differs fundamentally: FTP validated a shared secret string, while SFTP (in reality) validates possession of a private key via a cryptographic challenge, never transmitting the key itself over the network.

### Level 2 — Intermediate

The synchronization mechanics themselves are identical to FTP's (card 0051) — reusing that same download-to-local-staging pattern, since from the flow's perspective, once a session is established, SFTP and FTP behave the same way: list remote files, download new ones locally.

```java
// SftpSyncMechanicsDemo.java
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class SftpSyncMechanicsDemo {
    public static void main(String[] args) throws IOException {
        Path remoteSftpDir = Files.createTempDirectory("remote-sftp-demo"); // stands in for the remote SFTP server
        Path localStagingDir = Files.createTempDirectory("local-staging-demo");

        Files.writeString(remoteSftpDir.resolve("partner-export.csv"), "ORD-1,199.99");

        // IDENTICAL synchronization logic to FTP's (card 0051) — the protocol difference is entirely
        // in HOW the session/connection was established, not in this download step itself
        for (File remoteFile : Objects.requireNonNull(remoteSftpDir.toFile().listFiles())) {
            Files.copy(remoteFile.toPath(), localStagingDir.resolve(remoteFile.getName()),
                StandardCopyOption.REPLACE_EXISTING);
            System.out.println("Synchronized via SFTP session: " + remoteFile.getName());
        }
    }
}
```

How to run: `java SftpSyncMechanicsDemo.java`. Expected output: `Synchronized via SFTP session: partner-export.csv` — the actual file-listing-and-download logic is indistinguishable from FTP's equivalent; the meaningful difference lives entirely in the connection setup, not in this synchronization step.

### Level 3 — Advanced

SFTP introduces a security concern FTP/FTPS doesn't have in the same form: host key verification — confirming the remote server is genuinely who it claims to be, based on its SSH host key fingerprint, before trusting it with credentials or data (protecting against man-in-the-middle attacks) — shown here as an explicit check against a known-hosts registry.

```java
// HostKeyVerificationDemo.java
import java.util.Map;

public class HostKeyVerificationDemo {
    static Map<String, String> knownHosts = Map.of(
        "sftp.partner.example.com", "SHA256:abc123trustedFingerprint");

    static boolean connectWithHostKeyVerification(String host, String presentedFingerprint) {
        String trustedFingerprint = knownHosts.get(host);
        if (trustedFingerprint == null) {
            System.out.println("REJECTED: unknown host, no trusted fingerprint on file for " + host);
            return false;
        }
        if (!trustedFingerprint.equals(presentedFingerprint)) {
            System.out.println("REJECTED: host key MISMATCH for " + host
                + " — possible man-in-the-middle attack! Expected " + trustedFingerprint
                + " but got " + presentedFingerprint);
            return false;
        }
        System.out.println("ACCEPTED: host key verified for " + host);
        return true;
    }

    public static void main(String[] args) {
        // scenario 1: the server presents its GENUINE, expected fingerprint
        connectWithHostKeyVerification("sftp.partner.example.com", "SHA256:abc123trustedFingerprint");

        // scenario 2: the server presents a DIFFERENT fingerprint (server key changed, or a MITM attempt)
        connectWithHostKeyVerification("sftp.partner.example.com", "SHA256:xyz789suspiciousFingerprint");
    }
}
```

How to run: `java HostKeyVerificationDemo.java`. Expected output: `ACCEPTED: host key verified for sftp.partner.example.com` for the first connection attempt, then `REJECTED: host key MISMATCH...` for the second — SFTP's session establishment includes this host identity check as a core part of the protocol, something FTP (which has no equivalent host-identity verification built in) and even FTPS (whose certificate validation is a related but structurally different mechanism) handle quite differently.

## 6. Walkthrough

Tracing `HostKeyVerificationDemo` in execution order:

1. The first call, `connectWithHostKeyVerification("sftp.partner.example.com", "SHA256:abc123trustedFingerprint")`, looks up `knownHosts.get("sftp.partner.example.com")`, finding the previously-trusted fingerprint `"SHA256:abc123trustedFingerprint"`.
2. Because the presented fingerprint exactly matches the trusted one, the method prints `ACCEPTED` and returns `true` — in a real SFTP session, this is the point where the SSH handshake would proceed to authentication (the key-based check from Level 1) and then file operations.
3. The second call presents a *different* fingerprint, `"SHA256:xyz789suspiciousFingerprint"`, for the same host.
4. The lookup still finds the trusted fingerprint, but the equality check (`trustedFingerprint.equals(presentedFingerprint)`) fails, since the two strings differ.
5. Because of this mismatch, the method prints a `REJECTED` message specifically flagging the discrepancy as a possible man-in-the-middle attack, and returns `false` — in a real SFTP client library, this exact scenario (a changed or unexpected host key) typically triggers a hard connection failure rather than allowing the connection to silently proceed with a potentially malicious server.
6. This host-key-verification step happens *before* any credentials (a password or private key from Level 1) are ever exchanged — verifying the server's identity first is what prevents an attacker impersonating the legitimate SFTP server from ever having the opportunity to capture credentials in the first place.

```
connect(host, presentedFingerprint="abc123...")
  -> lookup trusted fingerprint for host: "abc123..."
  -> MATCH -> ACCEPTED -> proceed to authentication

connect(host, presentedFingerprint="xyz789...")
  -> lookup trusted fingerprint for host: "abc123..."
  -> MISMATCH -> REJECTED -> connection refused, NO credentials ever exchanged
```

## 7. Gotchas & takeaways

> A common (and dangerous) misconfiguration is disabling host key verification entirely (e.g., an "always accept" or "strict host key checking off" setting) to work around a connection error during initial development — this removes SFTP's core protection against man-in-the-middle attacks and should never be carried into production. If a host key genuinely needs to be updated (a legitimate server key rotation), that should be an explicit, deliberate update to the known-hosts registry, not a blanket disabling of the check itself.

- SFTP adapters (`SftpInboundFileSynchronizingMessageSource`, `SftpMessageHandler`) mirror FTP's adapter pair structurally (card 0051), but run over SSH rather than FTP+TLS — a fundamentally different protocol despite the similar-sounding name.
- SFTP commonly uses SSH key-based authentication rather than passwords, fitting naturally into infrastructure that already manages SSH keys for other access purposes.
- SFTP's single-SSH-connection model is often considered simpler to secure and firewall than FTP/FTPS's separate control-and-data-channel structure.
- Host key verification is an SFTP-specific security step, confirming the remote server's genuine identity before any credentials or data are exchanged — never disable this check in production, even temporarily.
- Once a session is established, the actual file synchronization/upload mechanics (listing, downloading, uploading) are functionally identical between FTP and SFTP — the meaningful engineering differences live entirely in connection setup, authentication, and security posture.
