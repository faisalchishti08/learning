---
card: spring-cloud
gi: 21
slug: encryption-decryption-symmetric-asymmetric
title: "Encryption & decryption (symmetric/asymmetric)"
---

## 1. What it is

Spring Cloud Config Server can store encrypted values directly inside ordinary configuration files (Git-backed or otherwise), prefixed with `{cipher}`, and decrypt them on the fly when serving a request — using either a symmetric key (one shared secret for both encrypting and decrypting) or an asymmetric key pair (a public key for encrypting, a private key for decrypting), configured on the server.

```yaml
# stored in the config repo, safe to commit even though it LOOKS sensitive
db:
  password: '{cipher}AQBxyz...encryptedvalue...'
```

## 2. Why & when

The Vault backend (an earlier card) is the recommended way to keep secrets entirely out of Git. Encryption support is a different, complementary answer to a similar problem: for teams that want to keep configuration in one place (Git) but still can't commit plaintext secrets, the Config Server can encrypt values before they're committed and decrypt them transparently when serving requests — so the *committed* value is ciphertext, safe even if the repository is later exposed, while the *served* value to an authorized client is the decrypted plaintext.

Reach for Config Server encryption when:

- A full separate secrets system (Vault) is more infrastructure than the situation calls for, but plaintext secrets in Git still isn't acceptable.
- You want secret values to live alongside their related ordinary configuration in the same file, rather than split across two backend systems.
- Rotating the encryption key itself (not just individual secret values) needs to be possible without re-encrypting every historical Git commit — a genuine operational concern this card's advanced example addresses.

## 3. Core concept

```
 POST /encrypt   body: "s3cr3t123"
 -> "a8f3e9...long hex ciphertext..."          -- store THIS in the config repo, prefixed {cipher}

 Config repo (safe to commit):
   db.password: '{cipher}a8f3e9...'

 GET /payment-service/production
 -> Config Server recognizes the {cipher} prefix, DECRYPTS using the server's configured key
 -> client receives: db.password: "s3cr3t123"   (plaintext, decrypted on the fly)
```

The `{cipher}` prefix marks a value as encrypted; the Config Server transparently decrypts it before including it in a response — the plaintext never touches the Git repository.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A plaintext secret is encrypted before being committed to the config repo, and decrypted again when the Config Server serves a request">
  <rect x="20" y="30" width="150" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="55" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">plaintext secret</text>

  <line x1="170" y1="50" x2="230" y2="50" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a41)"/>
  <text x="200" y="40" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">encrypt</text>

  <rect x="240" y="30" width="150" height="40" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="315" y="55" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">{cipher}... in Git</text>

  <line x1="390" y1="50" x2="450" y2="50" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a41)"/>
  <text x="420" y="40" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">decrypt</text>

  <rect x="460" y="30" width="150" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="55" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">plaintext to client</text>

  <defs><marker id="a41" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A secret is encrypted before entering the config repository and decrypted again on the way out to an authorized client.

## 5. Runnable example

The scenario: protecting a database password committed to a config repository, evolving from a naive symmetric cipher applied by hand, to the `{cipher}` prefix convention with automatic detection and decryption on serve, to an asymmetric key-pair setup demonstrating why public/private key encryption is preferable for a distributed team where not everyone should be able to decrypt.

### Level 1 — Basic

Model a bare symmetric encrypt/decrypt round trip, without any prefix convention or serving logic yet.

```java
import javax.crypto.*;
import javax.crypto.spec.*;
import java.util.*;

public class EncryptionLevel1 {
    public static void main(String[] args) throws Exception {
        SecretKey key = KeyGenerator.getInstance("AES").generateKey(); // ONE shared key -- symmetric

        String plaintext = "s3cr3t123";
        byte[] encrypted = encrypt(plaintext, key);
        System.out.println("Encrypted (safe to commit): " + Base64.getEncoder().encodeToString(encrypted));

        String decrypted = decrypt(encrypted, key);
        System.out.println("Decrypted (only with the SAME key): " + decrypted);
    }

    static byte[] encrypt(String plaintext, SecretKey key) throws Exception {
        Cipher cipher = Cipher.getInstance("AES");
        cipher.init(Cipher.ENCRYPT_MODE, key);
        return cipher.doFinal(plaintext.getBytes());
    }
    static String decrypt(byte[] ciphertext, SecretKey key) throws Exception {
        Cipher cipher = Cipher.getInstance("AES");
        cipher.init(Cipher.DECRYPT_MODE, key);
        return new String(cipher.doFinal(ciphertext));
    }
}
```

How to run: `java EncryptionLevel1.java`

`encrypt`/`decrypt` use the *same* `SecretKey` for both directions — this is symmetric encryption, mirroring `spring.cloud.config.server.encrypt.key` (a single shared key) as the simplest form of Config Server encryption.

### Level 2 — Intermediate

Add the `{cipher}` prefix convention and automatic detection on serve — a config value transparently decrypted only when it carries that marker.

```java
import javax.crypto.*;
import java.util.*;

public class EncryptionLevel2 {
    public static void main(String[] args) throws Exception {
        SecretKey key = KeyGenerator.getInstance("AES").generateKey();
        ConfigStore store = new ConfigStore(key);

        store.putEncrypted("payment-service", "db.password", "s3cr3t123"); // stored ENCRYPTED, {cipher}-prefixed
        store.putPlain("payment-service", "db.pool.size", "50");           // stored as-is, no encryption needed

        System.out.println("Raw stored config: " + store.rawConfigFor("payment-service"));
        System.out.println("Resolved for client: " + store.resolveFor("payment-service"));
    }
}

class ConfigStore {
    private final SecretKey key;
    private final Map<String, Map<String, String>> rawFiles = new HashMap<>();
    ConfigStore(SecretKey key) { this.key = key; }

    void putEncrypted(String application, String propKey, String plaintext) throws Exception {
        Cipher cipher = Cipher.getInstance("AES");
        cipher.init(Cipher.ENCRYPT_MODE, key);
        String ciphertextHex = Base64.getEncoder().encodeToString(cipher.doFinal(plaintext.getBytes()));
        rawFiles.computeIfAbsent(application, k -> new HashMap<>()).put(propKey, "{cipher}" + ciphertextHex);
    }
    void putPlain(String application, String propKey, String value) {
        rawFiles.computeIfAbsent(application, k -> new HashMap<>()).put(propKey, value);
    }
    Map<String, String> rawConfigFor(String application) { return rawFiles.get(application); } // as stored in "Git"

    // Simulates what the Config Server does when serving a request: decrypt anything {cipher}-prefixed.
    Map<String, String> resolveFor(String application) throws Exception {
        Map<String, String> resolved = new HashMap<>();
        for (Map.Entry<String, String> entry : rawFiles.get(application).entrySet()) {
            String value = entry.getValue();
            if (value.startsWith("{cipher}")) {
                byte[] ciphertext = Base64.getDecoder().decode(value.substring("{cipher}".length()));
                Cipher cipher = Cipher.getInstance("AES");
                cipher.init(Cipher.DECRYPT_MODE, key);
                resolved.put(entry.getKey(), new String(cipher.doFinal(ciphertext)));
            } else {
                resolved.put(entry.getKey(), value);
            }
        }
        return resolved;
    }
}
```

How to run: `java EncryptionLevel2.java`

`rawConfigFor` shows exactly what would be committed to Git — `db.password` as unreadable, `{cipher}`-prefixed ciphertext — while `resolveFor` shows what a requesting client actually receives: `resolveFor` detects the prefix, decrypts, and returns plaintext, transparently, with `db.pool.size` passed through untouched since it never carried the prefix.

### Level 3 — Advanced

Switch to asymmetric encryption: a public key anyone can use to encrypt new secrets before committing them, but only the Config Server's private key can decrypt — the appropriate model for a distributed team where not every contributor should be trusted with decryption capability.

```java
import java.security.*;
import javax.crypto.*;
import java.util.*;

public class EncryptionLevel3 {
    public static void main(String[] args) throws Exception {
        KeyPairGenerator generator = KeyPairGenerator.getInstance("RSA");
        generator.initialize(2048);
        KeyPair keyPair = generator.generateKeyPair();
        PublicKey publicKey = keyPair.getPublic();     // distributed to every developer, safe to share widely
        PrivateKey privateKey = keyPair.getPrivate();    // held ONLY by the running Config Server

        // A developer, using ONLY the public key, encrypts a new secret before committing it.
        String plaintext = "s3cr3t123";
        byte[] encrypted = encryptWithPublicKey(plaintext, publicKey);
        System.out.println("Developer commits (cannot decrypt this themselves): " + Base64.getEncoder().encodeToString(encrypted));

        // The Config Server, using ONLY the private key it holds, decrypts when serving a request.
        String decrypted = decryptWithPrivateKey(encrypted, privateKey);
        System.out.println("Config Server decrypts for an authorized client: " + decrypted);
    }

    static byte[] encryptWithPublicKey(String plaintext, PublicKey publicKey) throws Exception {
        Cipher cipher = Cipher.getInstance("RSA");
        cipher.init(Cipher.ENCRYPT_MODE, publicKey);
        return cipher.doFinal(plaintext.getBytes());
    }
    static String decryptWithPrivateKey(byte[] ciphertext, PrivateKey privateKey) throws Exception {
        Cipher cipher = Cipher.getInstance("RSA");
        cipher.init(Cipher.DECRYPT_MODE, privateKey);
        return new String(cipher.doFinal(ciphertext));
    }
}
```

How to run: `java EncryptionLevel3.java`

`encryptWithPublicKey` only needs `publicKey` — safe to distribute to every developer's machine so they can encrypt new secrets before committing — while `decryptWithPrivateKey` needs `privateKey`, which never leaves the running Config Server; a developer with only the public key can create new encrypted values but genuinely cannot decrypt existing ones, unlike the symmetric setup in Level 2 where anyone holding the single shared key could do both.

## 6. Walkthrough

Execution starts in `main` for Level 3. An RSA key pair is generated: `publicKey` and `privateKey`. `encryptWithPublicKey(plaintext, publicKey)` encrypts `"s3cr3t123"` using only the public half of the pair:

```
Developer commits (cannot decrypt this themselves): [base64 ciphertext]
```

`decryptWithPrivateKey(encrypted, privateKey)` reverses it, but critically requires `privateKey` — a value that, in this example, was generated once and never handed to the "developer" side of the code at all:

```
Config Server decrypts for an authorized client: s3cr3t123
```

In a real Spring Cloud Config setup, this asymmetric model addresses a real organizational gap the symmetric approach (Level 2) has: with a single shared symmetric key, *anyone* who can encrypt a new secret can also decrypt every existing one, since it's the same key both ways — meaning that key must be distributed carefully and is a single point of compromise. With RSA key-pair encryption, the public key can be freely distributed to every developer's workstation (via the `POST /encrypt` endpoint using the Config Server's public key, or a local copy of it) without any of them gaining decryption capability, which only the running Config Server itself possesses.

## 7. Gotchas & takeaways

> Gotcha: rotating a symmetric encryption key requires re-encrypting *every* existing `{cipher}`-prefixed value with the new key — old values encrypted under the previous key become permanently undecryptable the moment the Config Server's key configuration changes, unless a migration step re-encrypts them first; this is a genuinely disruptive operation that needs planning, unlike simply changing an ordinary configuration value.

> Gotcha: Config Server's built-in encryption requires the "Unlimited Strength" JCE policy files on older JVMs for full AES key length support — a common source of confusing `InvalidKeyException` errors on certain JDK distributions/versions until the correct JCE policy is in place (modern JDK distributions generally ship without this restriction, but it's worth verifying on the actual deployment target).

- Config Server can store `{cipher}`-prefixed encrypted values directly in ordinary configuration files, decrypting them transparently when serving a request to an authorized client.
- Symmetric encryption uses one shared key for both directions — simpler, but that single key is a point of compromise for both encrypting new secrets and decrypting existing ones.
- Asymmetric (RSA) encryption separates the two capabilities: a widely distributable public key for encrypting new secrets, and a private key held only by the Config Server for decrypting — a better fit for distributed teams.
- Rotating the encryption key is a disruptive operation requiring re-encryption of all existing encrypted values, unlike changing an ordinary configuration value.
