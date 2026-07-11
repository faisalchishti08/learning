---
card: spring-data
gi: 118
slug: client-side-field-level-encryption
title: "Client-side field-level encryption"
---

## 1. What it is

**Client-side field-level encryption (CSFLE)** encrypts specific document fields *before* they ever leave the application, using keys the MongoDB server never sees — the database stores and returns only ciphertext for those fields, and only a client holding the right key can decrypt them. Spring Data MongoDB integrates this through the MongoDB driver's `ClientEncryption` and `MongoClientSettings.autoEncryptionSettings(...)`, marking specific document fields as encrypted.

```java
@Document("orders")
class Order {
    @Id String id;
    String status;                 // stored in plaintext
    @Encrypted(algorithm = "AEAD_AES_256_CBC_HMAC_SHA_512-Random")
    String customerSsn;             // stored as ciphertext -- MongoDB never sees the real value
}
```

## 2. Why & when

Server-side encryption at rest protects data on disk, but the *running MongoDB server itself* still sees plaintext when a document passes through it — a database administrator with server access, a misconfigured backup, or a compromised server process can all potentially read that data. Client-side field-level encryption closes that gap for specific sensitive fields: encryption and decryption happen entirely in the application layer, so plaintext for those fields never exists anywhere except the authorized client.

Reach for CSFLE when:

- You store genuinely sensitive fields — national ID numbers, payment details, medical data — where regulatory or contractual requirements demand that even privileged database access can't expose the raw value.
- You want defense in depth beyond transport encryption (TLS) and encryption at rest, specifically against threats that have legitimate access to the running database server or its backups.
- You still need to *query* on some of those fields — CSFLE supports both a **deterministic** mode (same plaintext always encrypts to the same ciphertext, enabling equality queries) and a **random** mode (stronger, but not queryable) depending on the field's needs.

It's not free: encrypted fields can't be used in most query operators, can't be indexed the same way as plaintext fields (outside MongoDB's newer Queryable Encryption feature), and every read/write path needs access to the encryption keys — losing the keys means losing the data permanently, with no recovery path.

## 3. Core concept

```
 Application has: dataEncryptionKey (a "DEK", itself protected by a master key in a KMS)

 save(order):
   order.customerSsn = "123-45-6789"                 (plaintext, in memory)
        |  encrypt(customerSsn, dataEncryptionKey)
        v
   order.customerSsn = <ciphertext bytes>              -- THIS is what's sent to MongoDB
        |
        v
   MongoDB stores <ciphertext bytes> -- the server never sees "123-45-6789"

 findById(id):
   MongoDB returns <ciphertext bytes>
        |  decrypt(ciphertext, dataEncryptionKey)   -- ONLY the authorized client can do this
        v
   order.customerSsn = "123-45-6789"                  (plaintext, back in application memory only)
```

Encryption and decryption are entirely client-side operations, wrapped transparently around ordinary save/find calls — the server only ever handles ciphertext.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A plaintext SSN is encrypted before leaving the application and decrypted only after returning from MongoDB, so the server only ever sees ciphertext">
  <rect x="20" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="98" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">plaintext SSN</text>

  <rect x="245" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="93" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">encrypt()</text>
  <text x="320" y="107" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">in the application</text>

  <rect x="470" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="545" y="93" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MongoDB</text>
  <text x="545" y="107" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">stores ciphertext only</text>

  <line x1="170" y1="95" x2="240" y2="95" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="395" y1="95" x2="465" y2="95" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <text x="320" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">decrypt() runs the same way, in reverse, when reading the document back</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Plaintext exists only in the application's memory, on both the write and read paths — MongoDB itself only ever stores and returns ciphertext.

## 5. Runnable example

The scenario: protecting a customer's SSN field on `Order` documents, evolving from manual AES encryption applied by hand before every save, to a transparent wrapper that auto-encrypts/decrypts marked fields around ordinary save/find calls, to a version distinguishing **deterministic** (queryable) from **random** (stronger, non-queryable) encryption per field, matching the real CSFLE algorithm choice.

### Level 1 — Basic

Encrypt and decrypt a field by hand using AES, standing in for the driver's `ClientEncryption.encrypt()`/`decrypt()`.

```java
import javax.crypto.*;
import javax.crypto.spec.*;
import java.security.SecureRandom;
import java.nio.ByteBuffer;
import java.util.*;

public class CsfleLevel1 {
    // Stands in for the data encryption key (DEK) a real KMS would manage and protect.
    static SecretKey dataEncryptionKey() throws Exception {
        KeyGenerator keyGen = KeyGenerator.getInstance("AES");
        keyGen.init(256, new SecureRandom(new byte[]{1,2,3,4})); // fixed seed ONLY so this demo is reproducible
        return keyGen.generateKey();
    }

    static String encrypt(String plaintext, SecretKey key) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        byte[] iv = new byte[12]; new SecureRandom().nextBytes(iv);
        cipher.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(128, iv));
        byte[] ciphertext = cipher.doFinal(plaintext.getBytes());
        ByteBuffer buf = ByteBuffer.allocate(iv.length + ciphertext.length);
        buf.put(iv).put(ciphertext);
        return Base64.getEncoder().encodeToString(buf.array());
    }

    static String decrypt(String encoded, SecretKey key) throws Exception {
        byte[] all = Base64.getDecoder().decode(encoded);
        byte[] iv = Arrays.copyOfRange(all, 0, 12);
        byte[] ciphertext = Arrays.copyOfRange(all, 12, all.length);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(128, iv));
        return new String(cipher.doFinal(ciphertext));
    }

    public static void main(String[] args) throws Exception {
        SecretKey key = dataEncryptionKey();

        String plaintextSsn = "123-45-6789";
        String storedInMongo = encrypt(plaintextSsn, key); // THIS is what actually reaches the database
        System.out.println("Stored in MongoDB (ciphertext): " + storedInMongo);

        String readBack = decrypt(storedInMongo, key);
        System.out.println("Decrypted after reading back: " + readBack);
    }
}
```

How to run: `java CsfleLevel1.java`

`encrypt` runs entirely in application code before any value reaches MongoDB — `storedInMongo` is what the database actually persists, and it bears no resemblance to the real SSN. `decrypt` runs after reading the ciphertext back, using the same key, to recover the original value. A server-side observer, or anyone with only database access and no key, sees only the Base64 ciphertext.

### Level 2 — Intermediate

Wrap encryption/decryption transparently around save/find, so callers work with plain Java objects and never call `encrypt`/`decrypt` directly — matching how `@Encrypted` fields work automatically through Spring Data MongoDB's `MongoEncryptionConverter`.

```java
import javax.crypto.*;
import javax.crypto.spec.*;
import java.security.SecureRandom;
import java.nio.ByteBuffer;
import java.util.*;

public class CsfleLevel2 {
    public static void main(String[] args) throws Exception {
        KeyGenerator keyGen = KeyGenerator.getInstance("AES"); keyGen.init(256);
        FieldEncryptor encryptor = new FieldEncryptor(keyGen.generateKey());
        OrderRepository repo = new OrderRepository(encryptor);

        repo.save(new Order("1", "PENDING", "123-45-6789")); // caller passes PLAINTEXT -- encryption is invisible to it
        System.out.println("Raw stored ciphertext: " + repo.storedDocs.get("1").customerSsn);

        Order found = repo.findById("1");
        System.out.println("Application sees plaintext again: " + found.customerSsn);
    }
}

class Order { String id; String status; String customerSsn; Order(String id, String status, String customerSsn) { this.id = id; this.status = status; this.customerSsn = customerSsn; } }

class FieldEncryptor {
    private final SecretKey key;
    FieldEncryptor(SecretKey key) { this.key = key; }

    String encrypt(String plaintext) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        byte[] iv = new byte[12]; new SecureRandom().nextBytes(iv);
        cipher.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(128, iv));
        byte[] ct = cipher.doFinal(plaintext.getBytes());
        ByteBuffer buf = ByteBuffer.allocate(iv.length + ct.length); buf.put(iv).put(ct);
        return Base64.getEncoder().encodeToString(buf.array());
    }
    String decrypt(String encoded) throws Exception {
        byte[] all = Base64.getDecoder().decode(encoded);
        byte[] iv = Arrays.copyOfRange(all, 0, 12), ct = Arrays.copyOfRange(all, 12, all.length);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(128, iv));
        return new String(cipher.doFinal(ct));
    }
}

// Stands in for a MongoTemplate configured with autoEncryptionSettings -- the @Encrypted field is handled transparently.
class OrderRepository {
    private final FieldEncryptor encryptor;
    final Map<String, Order> storedDocs = new HashMap<>(); // customerSsn here is ALWAYS ciphertext

    OrderRepository(FieldEncryptor encryptor) { this.encryptor = encryptor; }

    void save(Order order) throws Exception {
        Order toStore = new Order(order.id, order.status, encryptor.encrypt(order.customerSsn)); // encrypt on the way IN
        storedDocs.put(order.id, toStore);
    }
    Order findById(String id) throws Exception {
        Order stored = storedDocs.get(id);
        return new Order(stored.id, stored.status, encryptor.decrypt(stored.customerSsn)); // decrypt on the way OUT
    }
}
```

How to run: `java CsfleLevel2.java`

The caller of `save`/`findById` never touches `encrypt`/`decrypt` directly — `OrderRepository` handles both transparently, exactly like a real `MongoTemplate` configured with `autoEncryptionSettings` handles `@Encrypted` fields automatically. Inspecting `repo.storedDocs` directly (standing in for looking at what's actually in MongoDB) shows only ciphertext; going through `findById` recovers the plaintext.

### Level 3 — Advanced

Distinguish **deterministic** encryption (same plaintext always produces the same ciphertext, so equality queries still work) from **random** encryption (stronger, but the field can no longer be queried by value) — the real choice CSFLE forces per field.

```java
import javax.crypto.*;
import javax.crypto.spec.*;
import java.security.SecureRandom;
import java.nio.ByteBuffer;
import java.util.*;

public class CsfleLevel3 {
    public static void main(String[] args) throws Exception {
        KeyGenerator keyGen = KeyGenerator.getInstance("AES"); keyGen.init(256);
        FieldEncryptor encryptor = new FieldEncryptor(keyGen.generateKey());

        String ssn = "123-45-6789";

        // status: not sensitive enough to need encryption at all -- stored plaintext, freely queryable.

        // customerSsn (equality lookups needed, e.g. "find order by SSN"): DETERMINISTIC.
        String det1 = encryptor.encrypt(ssn, EncryptionAlgorithm.DETERMINISTIC);
        String det2 = encryptor.encrypt(ssn, EncryptionAlgorithm.DETERMINISTIC);
        System.out.println("Deterministic ciphertexts match (queryable by equality): " + det1.equals(det2));

        // notes (never queried by value, maximum protection wanted): RANDOM.
        String rand1 = encryptor.encrypt(ssn, EncryptionAlgorithm.RANDOM);
        String rand2 = encryptor.encrypt(ssn, EncryptionAlgorithm.RANDOM);
        System.out.println("Random ciphertexts match (should be false -- NOT queryable): " + rand1.equals(rand2));
    }
}

enum EncryptionAlgorithm { DETERMINISTIC, RANDOM }

class FieldEncryptor {
    private final SecretKey key;
    FieldEncryptor(SecretKey key) { this.key = key; }

    String encrypt(String plaintext, EncryptionAlgorithm algorithm) throws Exception {
        // DETERMINISTIC: IV is DERIVED from the plaintext -- same input always -> same IV -> same ciphertext.
        // RANDOM: IV is genuinely random every time -- same input -> DIFFERENT ciphertext each call.
        byte[] iv = new byte[12];
        if (algorithm == EncryptionAlgorithm.DETERMINISTIC) {
            byte[] hash = plaintext.getBytes(); for (int i = 0; i < iv.length; i++) iv[i] = hash[i % hash.length];
        } else {
            new SecureRandom().nextBytes(iv);
        }
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(128, iv));
        byte[] ct = cipher.doFinal(plaintext.getBytes());
        ByteBuffer buf = ByteBuffer.allocate(iv.length + ct.length); buf.put(iv).put(ct);
        return Base64.getEncoder().encodeToString(buf.array());
    }
}
```

How to run: `java CsfleLevel3.java`

The same SSN, `"123-45-6789"`, is encrypted twice under each algorithm. Under `DETERMINISTIC`, the initialization vector is derived from the plaintext itself, so encrypting the same value twice always produces the same ciphertext — `det1.equals(det2)` is `true`, meaning MongoDB can match documents by an equality query on the encrypted field without ever seeing the plaintext. Under `RANDOM`, the IV is genuinely random each time, so `rand1.equals(rand2)` is `false` — stronger protection (an attacker can't even tell whether two documents share the same underlying value), but the field can no longer be searched by exact match.

## 6. Walkthrough

Execution starts in `main` for Level 3. A single plaintext value, `"123-45-6789"`, is encrypted four times total: twice with `DETERMINISTIC`, twice with `RANDOM`.

For the `DETERMINISTIC` calls, `encrypt` builds its 12-byte IV by cycling the plaintext's own bytes into it (`hash[i % hash.length]`) — since the plaintext is identical both times, the derived IV is identical both times, which means the AES-GCM cipher produces byte-for-byte identical ciphertext both times. `det1.equals(det2)` evaluates to `true` and is printed.

For the `RANDOM` calls, `encrypt` instead fills the IV with `SecureRandom.nextBytes(iv)` — a fresh, unpredictable value on every call, regardless of the plaintext. Even though the plaintext is the same `"123-45-6789"` both times, the different IVs cause AES-GCM to produce completely different ciphertext each time. `rand1.equals(rand2)` evaluates to `false` and is printed.

```
Deterministic ciphertexts match (queryable by equality): true
Random ciphertexts match (should be false -- NOT queryable): false
```

In real CSFLE, this exact trade-off is made per field via the algorithm named in `@Encrypted(algorithm = "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic")` versus `"...-Random"` — a field like `customerSsn` that the application needs to look up by exact value (`repository.findByCustomerSsn(ssn)`) must use the deterministic algorithm so MongoDB can match ciphertexts directly, while a field that's never queried by value, only ever fetched as part of a whole document, should use the random algorithm for its stronger guarantee that identical values don't produce identical, correlatable ciphertext.

## 7. Gotchas & takeaways

> Gotcha: deterministic encryption is queryable by equality, but it leaks a pattern — an attacker who can see the raw ciphertext (say, from a backup) can tell that two documents share the same underlying value, even without knowing what that value is. Only use it for fields that genuinely need equality lookups.

> Gotcha: losing the data encryption key (or the master key protecting it in the KMS) makes every encrypted field permanently unreadable — there is no recovery path, by design. Key management and backup for the KMS is not optional infrastructure; it's as critical as the database itself.

- CSFLE encrypts specific fields entirely client-side — MongoDB the server only ever stores and transmits ciphertext for those fields, never the plaintext.
- `@Encrypted` on a Spring Data MongoDB document field, combined with `autoEncryptionSettings` on the `MongoClient`, makes encryption/decryption transparent around ordinary save/find calls.
- Choose **deterministic** encryption for fields that need equality queries; choose **random** encryption for stronger protection on fields that don't need to be queried by value.
- Encrypted fields generally can't be used with range queries, most operators, or standard indexes — plan which fields truly need this protection, since it comes with real query-capability trade-offs.
