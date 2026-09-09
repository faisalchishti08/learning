---
card: system-design
gi: 179
slug: encryption-in-transit-tls-at-rest
title: Encryption in transit (TLS) & at rest
---

## 1. What it is

**Encryption in transit** protects data while it travels across a network, using TLS (Transport Layer Security) to encrypt the connection between a client and a server so anyone intercepting the traffic sees only unreadable ciphertext. **Encryption at rest** protects data while it is stored — on a disk, in a database, in a backup file — so that anyone who gains access to the raw storage (a stolen disk, an unauthorized database file copy) still cannot read the actual data without the encryption key.

## 2. Why & when

Data is vulnerable at every point it exists: while moving between a client and server (over a network an attacker on that network path could observe), and while sitting on a disk (which could be physically stolen, improperly discarded, or copied by an attacker who compromised the storage layer without ever touching the live application). Encrypting only one of these leaves the other completely exposed — TLS alone does nothing if an attacker copies the database file directly off disk; disk encryption alone does nothing if traffic is sent in plaintext over the network. Use both together for any system handling sensitive data: TLS for every network hop, and at-rest encryption for every persistent store holding that data.

## 3. Core concept

- **TLS handshake:** the client and server negotiate a shared symmetric session key using asymmetric cryptography (the server's certificate and public key), then use that fast symmetric key to encrypt all the actual traffic for the rest of the connection.
- **Certificate validation:** the client checks the server's certificate is signed by a trusted certificate authority (CA) and matches the domain being connected to — skipping this check (or ignoring certificate errors) defeats TLS's entire purpose, since it opens the door to a man-in-the-middle attack.
- **Encryption at rest, application-level vs. storage-level:** storage-level encryption (full-disk encryption, database-level transparent encryption) protects against a stolen disk but not against a compromised application with normal database access; application-level encryption (encrypting specific sensitive fields before writing them) additionally protects against a compromised database itself, at the cost of needing key management logic in the application.
- **Key management is the hard part of both:** TLS session keys are ephemeral and negotiated per connection, but the server's long-lived private key (and any at-rest encryption key) must be protected carefully — losing control of that key defeats the encryption entirely, regardless of the algorithm's strength.
- **Encryption is not the same as access control:** encrypting data at rest does not by itself prevent an authorized application process (with the decryption key) from reading data it should not — access control and encryption are complementary, not substitutes for each other.

## 4. Diagram

```
   client                                    server
     |-- TLS handshake: verify server cert ---->|
     |<-- negotiate shared session key ----------|
     |=========== ENCRYPTED CONNECTION =========|   <- encryption IN TRANSIT
     |-- encrypted request ---------------------->|
     |<-- encrypted response ---------------------|
                                                    |
                                                    v
                                          +--------------------+
                                          | database on disk    |
                                          | data stored ENCRYPTED| <- encryption AT REST
                                          +--------------------+
                                          (a stolen disk reveals only ciphertext)
```
*Caption: TLS protects data on the wire between client and server; at-rest encryption separately protects the same data once it is sitting in storage.*

## 5. Runnable example

**Level 1 — Basic.** Simulate a plaintext connection being fully readable if intercepted, versus an encrypted one.

**Level 2 — Symmetric encryption at rest, applied before writing to storage.** Model application-level field encryption.

**Level 3 — Combine both, and show what an attacker sees at each layer if they only compromise one of the two.** Network interception vs. stolen storage.

```java
// EncryptionInTransitAtRestDemo.java
import java.util.*;
import javax.crypto.*;
import javax.crypto.spec.*;
import java.security.*;
import java.util.Base64;

public class EncryptionInTransitAtRestDemo {

    // A simplified XOR "cipher" standing in for real TLS/AES - illustrates the CONCEPT, not production crypto.
    static byte[] xorCipher(byte[] data, byte[] key) {
        byte[] result = new byte[data.length];
        for (int i = 0; i < data.length; i++) result[i] = (byte) (data[i] ^ key[i % key.length]);
        return result;
    }

    // Level 1: what an attacker sees on the wire, WITH and WITHOUT TLS-style encryption.
    static void demonstrateTransitEncryption(String message, byte[] sessionKey) {
        System.out.println("plaintext connection: an eavesdropper reads exactly: \"" + message + "\"");
        byte[] encrypted = xorCipher(message.getBytes(), sessionKey);
        System.out.println("TLS-encrypted connection: an eavesdropper only sees: " + Base64.getEncoder().encodeToString(encrypted));
        byte[] decryptedByServer = xorCipher(encrypted, sessionKey); // only the server (with the session key) can do this
        System.out.println("the server, holding the session key, decrypts it back to: \"" + new String(decryptedByServer) + "\"");
    }

    // Level 2 & 3: encryption at rest - the database stores only ciphertext; a stolen copy of it reveals nothing.
    static Map<String, byte[]> databaseOnDisk = new HashMap<>();

    static void storeEncryptedRecord(String recordId, String sensitiveData, byte[] atRestKey) {
        databaseOnDisk.put(recordId, xorCipher(sensitiveData.getBytes(), atRestKey));
    }

    static String readAndDecryptRecord(String recordId, byte[] atRestKey) {
        byte[] ciphertext = databaseOnDisk.get(recordId);
        return new String(xorCipher(ciphertext, atRestKey));
    }

    public static void main(String[] args) {
        byte[] sessionKey = "tls-session-key!".getBytes();
        byte[] atRestKey = "database-at-rest-key".getBytes();

        System.out.println("-- encryption in transit --");
        demonstrateTransitEncryption("credit-card-number:4111-1111-1111-1111", sessionKey);

        System.out.println("-- encryption at rest --");
        storeEncryptedRecord("user-17", "SSN:123-45-6789", atRestKey);
        System.out.println("what a stolen copy of the database file actually contains: " + Base64.getEncoder().encodeToString(databaseOnDisk.get("user-17")));
        System.out.println("what the application, holding the at-rest key, reads: " + readAndDecryptRecord("user-17", atRestKey));

        // Level 3: an attacker who only stole the disk (no session key) CANNOT read this, even knowing it's XOR-based.
        System.out.println("attacker with the stolen disk but WITHOUT the at-rest key tries some guesses:");
        byte[] wrongKeyAttempt = xorCipher(databaseOnDisk.get("user-17"), "wrong-guess-key-12".getBytes());
        System.out.println("  result of a wrong-key guess: " + new String(wrongKeyAttempt) + " (garbage, not the real data)");
    }
}
```

**How to run:** save as `EncryptionInTransitAtRestDemo.java`, then run `java EncryptionInTransitAtRestDemo.java`.

## 6. Walkthrough

1. `demonstrateTransitEncryption` first prints the plaintext message directly, modeling what an eavesdropper on an unencrypted connection would see in full.
2. It then computes `encrypted = xorCipher(message.getBytes(), sessionKey)` and prints its base64 form — this is what an eavesdropper on a TLS-protected connection would actually observe on the wire: unreadable ciphertext, not the original message.
3. `decryptedByServer = xorCipher(encrypted, sessionKey)` reverses the operation using the *same* session key (the XOR operation is symmetric: applying it twice with the same key returns the original), modeling how the legitimate server, having negotiated that key during the TLS handshake, can decrypt the traffic while an outside observer cannot.
4. `storeEncryptedRecord("user-17", "SSN:123-45-6789", atRestKey)` encrypts the sensitive string before ever storing it in `databaseOnDisk`, so the map only ever holds ciphertext — printing its contents directly shows unreadable bytes, exactly what a stolen copy of the raw database file would contain.
5. `readAndDecryptRecord("user-17", atRestKey)` decrypts correctly because the application holds the correct `atRestKey`; the final attempt uses a deliberately wrong key, producing garbage output instead of the real SSN — demonstrating that possessing the encrypted data alone (as a disk thief would) is useless without also possessing the correct decryption key.

## 7. Gotchas & takeaways

> Gotcha: encrypting data at rest but then logging that same sensitive data in plaintext (application logs, debug output, error messages) completely defeats the purpose of encrypting it in the database — encryption at rest only protects data sitting in the encrypted store itself; every other place the same data flows through (logs, caches, backups) needs its own equivalent protection.

- Encryption in transit and at rest protect data at two different, independent points of exposure — network interception and storage compromise — and neither substitutes for the other.
- TLS's certificate validation step is what actually prevents a man-in-the-middle attack; skipping or ignoring certificate errors defeats the whole mechanism.
- Protecting the encryption keys themselves (TLS private keys, at-rest encryption keys) is the hardest and most critical part of making either form of encryption actually effective.
- Related concepts: [API keys & mutual TLS (mTLS)](0178-api-keys-mutual-tls-mtls.md) (TLS's certificate mechanism extended to verify the client too), [Secrets management & rotation](0180-secrets-management-rotation.md) (how the encryption keys themselves should be stored and rotated), [Spring Cloud Vault for secrets](0185-spring-cloud-vault-for-secrets.md) (a concrete tool for managing these keys in a Spring application).
