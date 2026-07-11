---
card: spring-security
gi: 38
slug: passkeys-webauthn
title: "Passkeys / WebAuthn"
---

## 1. What it is

Passkeys (built on the WebAuthn standard) replace passwords with public-key cryptography: during registration, the user's device (a phone, a security key, a laptop's built-in authenticator) generates a public/private key pair, keeps the private key locked inside secure hardware (never leaving the device), and sends only the *public* key to the server; during login, the server sends a random challenge, the device signs it with the private key, and the server verifies the signature using the stored public key — no shared secret (password) ever exists that could be phished, guessed, or leaked from a server-side breach. Spring Security's support (`http.webAuthn(Customizer.withDefaults())`) integrates this flow via `PublicKeyCredentialUserEntityRepository` and `UserCredentialRepository`.

```java
http.webAuthn(webAuthn -> webAuthn
        .rpName("My Application")
        .rpId("example.com")
        .allowedOrigins("https://example.com"));
```

## 2. Why & when

Passwords are fundamentally phishable — a user can be tricked into typing a real password into a fake login page, and the attacker now has something valid on the real site too. Passkeys structurally eliminate this: the private key never leaves the user's device and the signed challenge is cryptographically bound to the specific origin (domain) that requested it, so even a perfect visual replica of a login page hosted on an attacker's domain cannot obtain a valid signature for the *real* site — the browser/authenticator simply won't produce one for the wrong origin. This also eliminates server-side password storage risk entirely: a breached database of public keys is useless to an attacker, since public keys (by design) reveal nothing usable for impersonation.

Reach for passkeys/WebAuthn when:

- Phishing resistance is a priority — passkeys are the current strongest widely-deployable answer to credential phishing, since the origin-binding is enforced by the authentication protocol itself, not by user vigilance.
- Reducing server-side breach impact — since only public keys are stored, a database compromise cannot yield credentials usable to impersonate users elsewhere (unlike leaked password hashes, which remain crackable, especially for weak passwords).
- Improving user experience — modern devices increasingly support passkeys via biometric unlock (fingerprint, face recognition) backing the same on-device private key, often faster and more convenient than typing a password.

## 3. Core concept

```
 REGISTRATION:
   server sends a registration challenge (random bytes)
   user's device generates a NEW key pair, signs the challenge with the PRIVATE key
   device sends: public key + signed challenge + attestation
   server verifies the signature using the JUST-RECEIVED public key, then STORES the public key (never the private key)

 LOGIN:
   server sends a NEW, random login challenge
   user's device signs THIS challenge using the SAME private key (never transmitted, ever)
   server verifies the signature using the PREVIOUSLY STORED public key
   origin binding: the signature is cryptographically tied to the domain that issued the challenge --
     a phishing site on a DIFFERENT domain cannot obtain a valid signature, even with a perfect UI clone
```

The private key's permanent, hardware-bound confinement to the user's device is what makes both phishing resistance and breach-immunity possible simultaneously.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="During registration a device generates a key pair and sends only the public key to the server during login the server sends a random challenge bound to its own origin the device signs it with the private key which never leaves the device and the server verifies the signature using the stored public key a phishing site on a different origin cannot obtain a valid signature">
  <rect x="15" y="20" width="180" height="42" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="105" y="38" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">device: generate key pair</text>
  <text x="105" y="51" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">private key STAYS on device</text>

  <rect x="15" y="120" width="180" height="42" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="105" y="138" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">device: sign challenge</text>
  <text x="105" y="151" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">bound to real site's origin</text>

  <rect x="440" y="20" width="180" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="530" y="38" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">server: store PUBLIC key only</text>

  <rect x="440" y="120" width="180" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="530" y="138" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">server: verify signature</text>
  <text x="530" y="151" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">using stored public key</text>

  <defs><marker id="a38" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="195" y1="41" x2="440" y2="41" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a38)"/>
  <line x1="195" y1="141" x2="440" y2="141" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a38)"/>
</svg>

The private key (top-left) never crosses this diagram's midline — only its signatures do.

## 5. Runnable example

The scenario: model registration and login using real asymmetric cryptography (Java's built-in `KeyPair`/`Signature` classes standing in for a WebAuthn authenticator), then add origin binding to the signed challenge and show a phishing-style mismatched origin being rejected, then add multi-device (multiple public keys per user) support, a genuine production requirement.

### Level 1 — Basic

Generate a key pair, register the public key, sign a login challenge, and verify it — using real `java.security` cryptography.

```java
import java.security.*;
import java.util.*;

public class PasskeysLevel1 {
    static Map<String, PublicKey> registeredPublicKeys = new HashMap<>(); // username -> public key ONLY

    static KeyPair generateDeviceKeyPair() throws Exception {
        KeyPairGenerator generator = KeyPairGenerator.getInstance("EC");
        return generator.generateKeyPair();
    }

    static void register(String username, PublicKey publicKey) {
        registeredPublicKeys.put(username, publicKey); // the PRIVATE key is NEVER seen by this method at all
    }

    static byte[] deviceSignsChallenge(PrivateKey privateKey, byte[] challenge) throws Exception {
        Signature signature = Signature.getInstance("SHA256withECDSA");
        signature.initSign(privateKey);
        signature.update(challenge);
        return signature.sign();
    }

    static boolean serverVerifies(String username, byte[] challenge, byte[] signedChallenge) throws Exception {
        PublicKey publicKey = registeredPublicKeys.get(username);
        if (publicKey == null) return false;
        Signature signature = Signature.getInstance("SHA256withECDSA");
        signature.initVerify(publicKey);
        signature.update(challenge);
        return signature.verify(signedChallenge);
    }

    public static void main(String[] args) throws Exception {
        KeyPair deviceKeyPair = generateDeviceKeyPair(); // simulates the authenticator's on-device key generation
        register("alice", deviceKeyPair.getPublic());

        byte[] loginChallenge = "random-server-challenge-12345".getBytes();
        byte[] signed = deviceSignsChallenge(deviceKeyPair.getPrivate(), loginChallenge);

        System.out.println("server verifies signature: " + serverVerifies("alice", loginChallenge, signed));
    }
}
```

How to run: `java PasskeysLevel1.java`

`register` only ever receives `deviceKeyPair.getPublic()` — the private key stays entirely local to `main`, modeling how it would remain locked inside real secure hardware; `serverVerifies` correctly confirms the signature using only the stored public key, never needing (or being able to access) the private key at all.

### Level 2 — Intermediate

Add origin binding to the challenge, and show a mismatched-origin verification attempt (modeling a phishing site) being rejected even with a technically valid signature over the wrong data.

```java
import java.security.*;
import java.util.*;

public class PasskeysLevel2 {
    static Map<String, PublicKey> registeredPublicKeys = new HashMap<>();

    static KeyPair generateDeviceKeyPair() throws Exception {
        return KeyPairGenerator.getInstance("EC").generateKeyPair();
    }

    static void register(String username, PublicKey publicKey) { registeredPublicKeys.put(username, publicKey); }

    // origin is bound INTO what gets signed -- not a separate, checkable-after-the-fact field
    static byte[] buildSignedPayload(String challenge, String origin) {
        return (challenge + "|origin=" + origin).getBytes();
    }

    static byte[] deviceSignsChallenge(PrivateKey privateKey, byte[] payload) throws Exception {
        Signature signature = Signature.getInstance("SHA256withECDSA");
        signature.initSign(privateKey);
        signature.update(payload);
        return signature.sign();
    }

    static boolean serverVerifies(String username, byte[] expectedPayload, byte[] signedPayload) throws Exception {
        PublicKey publicKey = registeredPublicKeys.get(username);
        if (publicKey == null) return false;
        Signature signature = Signature.getInstance("SHA256withECDSA");
        signature.initVerify(publicKey);
        signature.update(expectedPayload);
        return signature.verify(signedPayload);
    }

    public static void main(String[] args) throws Exception {
        KeyPair deviceKeyPair = generateDeviceKeyPair();
        register("alice", deviceKeyPair.getPublic());

        String challenge = "random-challenge-12345";
        String realOrigin = "https://example.com";

        // the LEGITIMATE flow: device signs the challenge bound to the REAL site's origin
        byte[] legitPayload = buildSignedPayload(challenge, realOrigin);
        byte[] legitSignature = deviceSignsChallenge(deviceKeyPair.getPrivate(), legitPayload);
        System.out.println("legitimate login (real origin): "
                + serverVerifies("alice", buildSignedPayload(challenge, realOrigin), legitSignature));

        // a PHISHING attempt: attacker's fake site tries to reuse the SAME signature against ITS OWN origin
        String phishingOrigin = "https://examp1e-phishing.com";
        boolean phishingAccepted = serverVerifies("alice", buildSignedPayload(challenge, phishingOrigin), legitSignature);
        System.out.println("phishing site checking against its OWN origin: " + phishingAccepted);
    }
}
```

How to run: `java PasskeysLevel2.java`

The legitimate signature verifies correctly against `realOrigin`'s payload; the exact same signature, checked against a payload built with `phishingOrigin` instead, fails verification — because the origin is baked directly into what was actually signed, a signature produced for one origin is cryptographically meaningless for any other, which is precisely why passkeys resist phishing even when the fake site's UI is a pixel-perfect copy.

### Level 3 — Advanced

Support multiple registered devices (public keys) per user — a genuine production requirement, since users commonly register a passkey on more than one device (a phone and a laptop) — and correctly authenticate using any one of them.

```java
import java.security.*;
import java.util.*;

public class PasskeysLevel3 {
    static Map<String, List<PublicKey>> registeredPublicKeysByUser = new HashMap<>();

    static KeyPair generateDeviceKeyPair() throws Exception {
        return KeyPairGenerator.getInstance("EC").generateKeyPair();
    }

    static void registerDevice(String username, PublicKey publicKey) {
        registeredPublicKeysByUser.computeIfAbsent(username, k -> new ArrayList<>()).add(publicKey);
    }

    static byte[] buildSignedPayload(String challenge, String origin) {
        return (challenge + "|origin=" + origin).getBytes();
    }

    static byte[] deviceSignsChallenge(PrivateKey privateKey, byte[] payload) throws Exception {
        Signature signature = Signature.getInstance("SHA256withECDSA");
        signature.initSign(privateKey);
        signature.update(payload);
        return signature.sign();
    }

    // tries EACH registered public key for this user -- any ONE matching is sufficient
    static boolean serverVerifiesAnyDevice(String username, byte[] expectedPayload, byte[] signedPayload) throws Exception {
        List<PublicKey> keys = registeredPublicKeysByUser.getOrDefault(username, List.of());
        for (PublicKey publicKey : keys) {
            Signature signature = Signature.getInstance("SHA256withECDSA");
            signature.initVerify(publicKey);
            signature.update(expectedPayload);
            if (signature.verify(signedPayload)) return true; // FIRST matching device is enough
        }
        return false;
    }

    public static void main(String[] args) throws Exception {
        KeyPair phoneKeyPair = generateDeviceKeyPair();
        KeyPair laptopKeyPair = generateDeviceKeyPair();
        registerDevice("alice", phoneKeyPair.getPublic());
        registerDevice("alice", laptopKeyPair.getPublic());

        String challenge = "random-challenge-99999";
        String origin = "https://example.com";
        byte[] payload = buildSignedPayload(challenge, origin);

        byte[] signedByPhone = deviceSignsChallenge(phoneKeyPair.getPrivate(), payload);
        byte[] signedByLaptop = deviceSignsChallenge(laptopKeyPair.getPrivate(), payload);

        System.out.println("login via phone's passkey: " + serverVerifiesAnyDevice("alice", payload, signedByPhone));
        System.out.println("login via laptop's passkey: " + serverVerifiesAnyDevice("alice", payload, signedByLaptop));
        System.out.println("registered device count for alice: " + registeredPublicKeysByUser.get("alice").size());
    }
}
```

How to run: `java PasskeysLevel3.java`

`registeredPublicKeysByUser` maps `"alice"` to a *list* of two public keys (phone and laptop); `serverVerifiesAnyDevice` iterates that list and accepts a signature from *either* device — a signature produced by the phone's private key verifies successfully against the phone's registered public key on the first list iteration reaching it, and likewise for the laptop, correctly modeling that a user can log in from any device they've previously registered a passkey on.

## 6. Walkthrough

Trace `serverVerifiesAnyDevice("alice", payload, signedByLaptop)` from Level 3.

1. `registeredPublicKeysByUser.getOrDefault("alice", List.of())` retrieves alice's list of two registered public keys, in the order they were added: `[phoneKeyPair.getPublic(), laptopKeyPair.getPublic()]`.
2. The `for` loop's first iteration tries `phoneKeyPair.getPublic()`: `signature.initVerify` is set up with the phone's public key, `signature.update(expectedPayload)` feeds it the payload, and `signature.verify(signedPayload)` checks whether `signedPayload` (which was actually produced by the *laptop's* private key) is a valid signature under the *phone's* public key — since these are mathematically unrelated key pairs, this check returns `false`.
3. Because the first iteration returned `false`, the loop continues to its second element: `laptopKeyPair.getPublic()`. This time, `signature.verify(signedPayload)` checks the signature against the *correct* public key — the one whose matching private key actually produced `signedByLaptop` — and this returns `true`.
4. The method immediately returns `true` on this match, without needing to check any further entries (there are none left anyway) — the caller sees a successful login, without ever needing to know or care *which* of alice's registered devices produced the signature, only that *some* registered device did.
5. This iterate-until-a-match approach is exactly why supporting multiple registered passkeys per account is straightforward: the server's verification logic doesn't change at all when a user adds a third or fourth device — it simply has one more public key to check in the same loop.

```
registeredPublicKeysByUser["alice"] = [phoneKey, laptopKey]
verify signedByLaptop against phoneKey  -> FALSE (wrong key pair)
verify signedByLaptop against laptopKey -> TRUE  (correct key pair) -> loop returns true immediately
```

## 7. Gotchas & takeaways

> **Gotcha:** losing access to *every* device holding a registered passkey (a phone lost and a laptop wiped, with no recovery mechanism configured) permanently locks a user out of their account, since there is no password to fall back on and the private keys never existed anywhere recoverable by the server. Production passkey implementations must offer some backup/recovery path (a secondary passkey on a different device, a traditional account-recovery flow) precisely because of this.

- Passkeys eliminate phishing risk structurally, by cryptographically binding every signed challenge to the specific origin that issued it — a signature produced for one domain is meaningless to any other, regardless of how convincing a fake site's interface looks.
- Only public keys are ever stored server-side; a full database breach yields nothing usable to impersonate any user, a fundamentally different risk profile from leaked password hashes.
- Supporting multiple registered devices per user is a standard, expected requirement — the server simply checks a signature against each of a user's registered public keys until one matches.
- Because there is no password to serve as a fallback, a lost-device recovery story (additional registered devices, or a separate account-recovery flow) is essential and must be designed deliberately, not left as an afterthought.
