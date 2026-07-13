---
card: microservices
gi: 238
slug: encryption-decryption-of-config-values
title: "Encryption/decryption of config values"
---

## 1. What it is

Encryption of configuration values means storing a sensitive setting in its encrypted form wherever it's persisted (a Git-backed [Config Server](0231-spring-cloud-config-server.md) file, a database row) and decrypting it only at the point an authorized application actually needs the plaintext — Spring Cloud Config Server supports this natively, letting an encrypted value (prefixed `{cipher}`) sit safely in an otherwise plaintext, Git-tracked configuration file.

## 2. Why & when

[Dedicated secret stores](0236-spring-cloud-vault-for-secrets.md) like Vault are the strongest option for genuine secrets, but not every team's infrastructure includes a full Vault deployment, and even where one exists, some workflows benefit from keeping a value physically alongside its related configuration in the same Git-tracked file rather than in an entirely separate system. Config Server's built-in encryption support addresses this middle ground: a value can be encrypted once (via the server's `/encrypt` endpoint) and the resulting ciphertext committed directly into an otherwise ordinary, Git-tracked YAML file — safe to commit because the ciphertext is meaningless without the decryption key, which the Config Server holds separately and never commits alongside it.

Use Config Server's built-in encryption for secrets that benefit from living alongside their related configuration in a single Git-tracked file, in setups without (or in addition to) a full Vault deployment. For secrets needing fine-grained access control, automatic rotation, or dynamic secret generation (temporary, auto-expiring database credentials, for instance), a dedicated secret store like Vault remains the stronger choice.

## 3. Core concept

Config Server exposes `/encrypt` and `/decrypt` endpoints backed by a key it holds (a symmetric key or an asymmetric key pair); a value encrypted through `/encrypt` is safe to commit as ciphertext (prefixed `{cipher}`) into an ordinary configuration file, and Config Server automatically decrypts any `{cipher}`-prefixed value before returning it to a requesting, authorized client.

```java
// step 1: encrypt the value ONCE, via the Config Server's /encrypt endpoint
// POST /encrypt  body: "hunter2"
// response: "AQBxyz...encryptedBase64String...=="

// step 2: commit the CIPHERTEXT directly into an otherwise plaintext, Git-tracked file
// order-service-production.yaml:
// db:
//   password: '{cipher}AQBxyz...encryptedBase64String...=='   -- SAFE to commit; meaningless without the key

// step 3: a requesting CLIENT never sees the ciphertext -- Config Server decrypts BEFORE returning the response
// GET /order-service/production -> { "db.password": "hunter2" }  -- Config Server decrypted it server-side
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A plaintext secret is encrypted once via the Config Server's encrypt endpoint, the resulting ciphertext is committed safely to Git, and the Config Server decrypts it automatically before serving the value to an authorized requesting client" >
  <rect x="20" y="65" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="90" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Plaintext secret</text>

  <rect x="220" y="55" width="150" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="295" y="78" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">/encrypt endpoint</text>
  <text x="295" y="94" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">-> {cipher}ciphertext</text>

  <rect x="440" y="20" width="160" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="520" y="45" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Git repo (ciphertext safe)</text>

  <rect x="440" y="110" width="160" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="520" y="135" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Client GET -> decrypted plaintext</text>

  <line x1="150" y1="85" x2="218" y2="85" stroke="#8b949e" marker-end="url(#arr238)"/>
  <line x1="370" y1="70" x2="438" y2="40" stroke="#8b949e" marker-end="url(#arr238)"/>
  <line x1="438" y1="45" x2="373" y2="90" stroke="#8b949e" marker-end="url(#arr238)"/>
  <line x1="373" y1="95" x2="438" y2="128" stroke="#8b949e" marker-end="url(#arr238)"/>

  <defs>
    <marker id="arr238" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Only ciphertext ever reaches Git; only an authorized Config Server request ever sees the decrypted plaintext.

## 5. Runnable example

Scenario: a configuration file that starts with a plaintext secret unsafe to commit, refactors to encrypt the value before storage (mirroring Config Server's `/encrypt` endpoint) so only ciphertext is ever committed, and finally demonstrates the automatic decryption a requesting client receives, plus what happens when decryption is attempted with the wrong key — a common real failure mode when a key is lost or rotated incorrectly.

### Level 1 — Basic

```java
// File: PlaintextInConfigFile.java -- the secret is stored, and would be
// COMMITTED to Git, in PLAIN TEXT.
import java.util.*;

public class PlaintextInConfigFile {
    static Map<String, String> configFile = Map.of("db.password", "hunter2"); // UNSAFE to commit as-is

    public static void main(String[] args) {
        System.out.println("Config file contents (as would be committed): " + configFile);
        System.out.println("Anyone with Git access sees the PLAINTEXT password.");
    }
}
```

**How to run:** `javac PlaintextInConfigFile.java && java PlaintextInConfigFile` (JDK 17+).

### Level 2 — Intermediate

```java
// File: EncryptedBeforeStorage.java -- the value is ENCRYPTED once via
// a simulated /encrypt endpoint; only the CIPHERTEXT is ever "committed."
import javax.crypto.*;
import javax.crypto.spec.*;
import java.util.*;
import java.security.*;
import java.util.Base64;

public class EncryptedBeforeStorage {
    static SecretKey configServerKey; // held ONLY by the Config Server, never committed anywhere

    static String encrypt(String plaintext) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        byte[] iv = new byte[12]; new SecureRandom().nextBytes(iv);
        cipher.init(Cipher.ENCRYPT_MODE, configServerKey, new GCMParameterSpec(128, iv));
        byte[] ciphertext = cipher.doFinal(plaintext.getBytes());
        byte[] combined = new byte[iv.length + ciphertext.length];
        System.arraycopy(iv, 0, combined, 0, iv.length);
        System.arraycopy(ciphertext, 0, combined, iv.length, ciphertext.length);
        return "{cipher}" + Base64.getEncoder().encodeToString(combined); // mirrors Config Server's {cipher} prefix convention
    }

    public static void main(String[] args) throws Exception {
        KeyGenerator keyGen = KeyGenerator.getInstance("AES"); keyGen.init(256);
        configServerKey = keyGen.generateKey();

        String encryptedPassword = encrypt("hunter2"); // STEP 1: encrypt via the "/encrypt endpoint"
        Map<String, String> configFile = Map.of("db.password", encryptedPassword); // STEP 2: commit the CIPHERTEXT

        System.out.println("Config file contents (as would ACTUALLY be committed): " + configFile);
        System.out.println("This is SAFE to commit -- meaningless without configServerKey, which is NEVER committed.");
    }
}
```

**How to run:** `javac EncryptedBeforeStorage.java && java EncryptedBeforeStorage` (JDK 17+).

Expected output (ciphertext value varies per run due to a random IV, structure is stable):
```
Config file contents (as would ACTUALLY be committed): {db.password={cipher}AbCdEf...==}
This is SAFE to commit -- meaningless without configServerKey, which is NEVER committed.
```

### Level 3 — Advanced

```java
// File: DecryptionForAuthorizedClientAndWrongKeyFailure.java -- the
// Config Server decrypts {cipher}-prefixed values automatically for a
// serving response, and demonstrates the failure mode when decryption
// is attempted with the WRONG key -- e.g. after an incomplete key rotation.
import javax.crypto.*;
import javax.crypto.spec.*;
import java.util.*;
import java.security.*;
import java.util.Base64;

public class DecryptionForAuthorizedClientAndWrongKeyFailure {
    static String encrypt(SecretKey key, String plaintext) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        byte[] iv = new byte[12]; new SecureRandom().nextBytes(iv);
        cipher.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(128, iv));
        byte[] ciphertext = cipher.doFinal(plaintext.getBytes());
        byte[] combined = new byte[iv.length + ciphertext.length];
        System.arraycopy(iv, 0, combined, 0, iv.length);
        System.arraycopy(ciphertext, 0, combined, iv.length, ciphertext.length);
        return "{cipher}" + Base64.getEncoder().encodeToString(combined);
    }

    static String decrypt(SecretKey key, String cipherPrefixed) throws Exception {
        String base64 = cipherPrefixed.substring("{cipher}".length()); // strip the CONVENTION prefix
        byte[] combined = Base64.getDecoder().decode(base64);
        byte[] iv = Arrays.copyOfRange(combined, 0, 12);
        byte[] ciphertext = Arrays.copyOfRange(combined, 12, combined.length);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(128, iv));
        return new String(cipher.doFinal(ciphertext)); // throws if the key is WRONG
    }

    public static void main(String[] args) throws Exception {
        KeyGenerator keyGen = KeyGenerator.getInstance("AES"); keyGen.init(256);
        SecretKey correctKey = keyGen.generateKey();
        SecretKey wrongKey = keyGen.generateKey(); // simulates a DIFFERENT key, e.g. from an incomplete rotation

        String storedCiphertext = encrypt(correctKey, "hunter2");
        System.out.println("Stored (as committed to Git): " + storedCiphertext.substring(0, 20) + "...");

        String decrypted = decrypt(correctKey, storedCiphertext); // AUTHORIZED client, correct key
        System.out.println("Decrypted for authorized client: " + decrypted);

        try {
            decrypt(wrongKey, storedCiphertext); // simulates a MISCONFIGURED Config Server, or a key rotation gone wrong
        } catch (Exception e) {
            System.out.println("Caught expected decryption failure with wrong key: " + e.getClass().getSimpleName());
        }
    }
}
```

**How to run:** `javac DecryptionForAuthorizedClientAndWrongKeyFailure.java && java DecryptionForAuthorizedClientAndWrongKeyFailure` (JDK 17+).

Expected output (ciphertext prefix varies per run):
```
Stored (as committed to Git): {cipher}AbCdEfGhIjK...
Decrypted for authorized client: hunter2
Caught expected decryption failure with wrong key: AEADBadTagException
```

## 6. Walkthrough

1. **Level 1, the unsafe baseline** — `configFile` holds `"hunter2"` directly; if this map represented the literal contents of a file committed to Git, the plaintext password would be permanently recoverable from that repository's history, the same risk covered generally in [secrets management & encryption](0222-secrets-management-encryption.md).
2. **Level 2, encrypting before anything is stored** — `encrypt` uses AES/GCM with a randomly generated initialization vector (`iv`) for each call, and prefixes the result with the literal string `"{cipher}"`, mirroring Spring Cloud Config Server's own convention for marking a value as encrypted; `configServerKey`, the only thing capable of reversing this encryption, is generated in memory and never appears in `configFile` itself.
3. **Level 2, what actually gets committed** — the printed `configFile` shows `db.password` mapped to a `{cipher}`-prefixed base64 string rather than `"hunter2"`; this ciphertext is safe to commit to Git precisely because it's computationally infeasible to recover the plaintext from it without `configServerKey`, which lives only on the Config Server, never in the repository.
4. **Level 3, the authorized decryption path** — `decrypt(correctKey, storedCiphertext)` strips the `"{cipher}"` prefix, extracts the stored IV and ciphertext, and reverses the exact AES/GCM operation `encrypt` performed, successfully recovering `"hunter2"` — this models exactly what a real Config Server does internally before returning a value to a client that requested it, transparently to that client.
5. **Level 3, the wrong-key failure** — `decrypt(wrongKey, storedCiphertext)` attempts the identical decryption process but with a different `SecretKey`; AES/GCM's authentication tag verification fails because the ciphertext was never encrypted with `wrongKey`, and the operation throws an exception (`AEADBadTagException`) rather than silently returning corrupted or incorrect plaintext — this fail-loud behavior is a deliberate property of authenticated encryption modes like GCM, and it's exactly the failure a real Config Server would surface if its decryption key were lost, misconfigured, or rotated incompletely (old ciphertext still referencing a key the server no longer has).
6. **Level 3, why this scenario matters operationally** — the caught exception in `main` demonstrates a realistic operational failure mode: if a Config Server's encryption key is ever rotated without also re-encrypting every previously stored `{cipher}`-prefixed value with the new key, every one of those old values becomes permanently undecryptable with the new key, surfacing as exactly this kind of authentication failure at the moment a client requests that configuration — a strong reason key rotation for this mechanism needs a deliberate re-encryption step, not just swapping the key in place.

## 7. Gotchas & takeaways

> **Gotcha:** rotating the Config Server's encryption key without re-encrypting every existing `{cipher}`-prefixed value stored under the old key permanently breaks decryption of those values, as Level 3's wrong-key failure demonstrates — key rotation for this mechanism requires decrypting every affected value with the old key and re-encrypting it with the new one as an explicit migration step, not simply replacing the key configuration.

- Spring Cloud Config Server supports encrypting individual configuration values, letting `{cipher}`-prefixed ciphertext sit safely alongside ordinary, Git-tracked configuration in the same file.
- Encryption happens once, via a dedicated endpoint; decryption happens automatically and transparently server-side whenever a `{cipher}`-prefixed value is served to a requesting client.
- This is a lighter-weight middle ground between fully plaintext configuration and a dedicated secret store like [Spring Cloud Vault](0236-spring-cloud-vault-for-secrets.md), suited to setups that want encrypted secrets living alongside their related configuration.
- Authenticated encryption (like AES/GCM) fails loudly with the wrong key rather than silently returning corrupted data, which is the correct behavior but requires the failure to be anticipated operationally.
- Rotating the encryption key requires explicitly re-encrypting every previously stored value under the new key; simply changing the key configuration permanently breaks decryption of everything encrypted under the old one.
