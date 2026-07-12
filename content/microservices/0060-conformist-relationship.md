---
card: microservices
gi: 60
slug: conformist-relationship
title: Conformist relationship
---

## 1. What it is

A **Conformist** relationship is an upstream/downstream dependency where the downstream context simply accepts the upstream context's model exactly as-is — no translation, no negotiation, no influence over the upstream's roadmap. This is the honest, deliberate choice when the upstream is a third party (a widely-used payment gateway, a public cloud provider's API) with no reason to prioritize your specific needs, and building an [anticorruption layer](0057-anti-corruption-layer-acl.md) to translate its model would cost more than it's worth for a well-designed, stable upstream.

## 2. Why & when

Conforming isn't a failure to negotiate — it's a legitimate, deliberate architectural choice when the upstream's model is already reasonably clean, and you have no realistic path to influence it anyway (a public payment gateway isn't going to redesign its API around your specific domain's preferences). Building a full anticorruption layer in that situation adds real translation-maintenance cost for a model that's already good enough, and stable enough, that direct use doesn't meaningfully corrupt your own domain.

Choose Conformist deliberately, having weighed it against an ACL — not as a default because building a translation layer felt like too much work. Revisit the choice if the upstream model's quality degrades, its stability decreases, or a genuine mismatch with your domain's vocabulary starts causing real confusion — at that point, upgrading to an ACL becomes worth its cost.

## 3. Core concept

The defining trait, in contrast with the other patterns: downstream code uses the upstream's types, vocabulary, and structure *directly*, with zero translation layer in between.

```
Upstream (PaymentGatewayAPI):  class ChargeRequest { ... }  // upstream's OWN type
        |
Downstream code:               PaymentGatewayAPI.ChargeRequest request = new PaymentGatewayAPI.ChargeRequest(...);
                                // used DIRECTLY, no translation, no downstream-owned equivalent type
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Downstream code uses the upstream payment gateway's own types directly, with no translation layer in between">
  <rect x="60" y="45" width="200" height="55" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">PaymentGatewayAPI</text>
  <text x="160" y="88" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">upstream's own types</text>

  <line x1="260" y1="72" x2="380" y2="72" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a60)"/>
  <text x="320" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">used directly</text>

  <rect x="380" y="45" width="200" height="55" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="480" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Downstream domain code</text>
  <text x="480" y="88" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">NO translation layer</text>
  <defs><marker id="a60" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

No translation boundary — downstream code depends directly on the upstream's own model.

## 5. Runnable example

Scenario: integrating with a well-designed, stable public payment gateway's model, first as a deliberate Conformist choice, then explicitly evaluated against building an ACL, then showing the accepted cost when the upstream does eventually change.

### Level 1 — Basic

```java
// File: ConformToGateway.java -- accept the payment gateway's model
// DIRECTLY, no translation layer.
public class ConformToGateway {
    // stands in for a well-designed, stable THIRD-PARTY payment gateway's own types
    static class PaymentGatewayApi {
        record ChargeRequest(String cardToken, long amountInCents, String currency) { }
        record ChargeResult(String chargeId, String status) { }

        ChargeResult charge(ChargeRequest request) {
            return new ChargeResult("chg_" + request.cardToken(), "succeeded");
        }
    }

    // downstream code uses the gateway's OWN types DIRECTLY -- no translation
    static void processPayment(PaymentGatewayApi gateway) {
        var request = new PaymentGatewayApi.ChargeRequest("tok_visa", 999, "usd");
        var result = gateway.charge(request);
        System.out.println("Charge " + result.chargeId() + ": " + result.status());
    }

    public static void main(String[] args) {
        processPayment(new PaymentGatewayApi());
    }
}
```

**How to run:** `javac ConformToGateway.java && java ConformToGateway` (JDK 17+).

Expected output:
```
Charge chg_tok_visa: succeeded
```

`processPayment` uses `PaymentGatewayApi.ChargeRequest` and `PaymentGatewayApi.ChargeResult` directly — no downstream-owned equivalent types, no translation function. This is a deliberate Conformist choice: the gateway's model is clean and stable enough that direct use is the pragmatic option.

### Level 2 — Intermediate

```java
// File: WeighedDecision.java -- explicitly EVALUATE Conformist vs ACL
// for this specific dependency, and record the reasoning.
public class WeighedDecision {
    record RelationshipDecision(String upstreamName, boolean modelIsClean, boolean modelIsStable, boolean hasInfluenceOverUpstream, String chosenPattern, String reasoning) { }

    static RelationshipDecision evaluate(String upstreamName, boolean modelIsClean, boolean modelIsStable, boolean hasInfluence) {
        if (hasInfluence) {
            return new RelationshipDecision(upstreamName, modelIsClean, modelIsStable, true, "Customer-Supplier", "we have real influence over the upstream's roadmap");
        }
        if (modelIsClean && modelIsStable) {
            return new RelationshipDecision(upstreamName, modelIsClean, modelIsStable, false, "Conformist", "model is clean and stable -- translation cost isn't justified");
        }
        return new RelationshipDecision(upstreamName, modelIsClean, modelIsStable, false, "Anticorruption Layer", "model is messy or unstable -- worth insulating our domain from it");
    }

    public static void main(String[] args) {
        var paymentGateway = evaluate("PaymentGatewayAPI", true, true, false);
        var legacyShipping = evaluate("LegacyShippingSystem", false, false, false);

        System.out.println(paymentGateway.upstreamName() + ": " + paymentGateway.chosenPattern() + " -- " + paymentGateway.reasoning());
        System.out.println(legacyShipping.upstreamName() + ": " + legacyShipping.chosenPattern() + " -- " + legacyShipping.reasoning());
    }
}
```

**How to run:** `javac WeighedDecision.java && java WeighedDecision` (JDK 17+).

Expected output:
```
PaymentGatewayAPI: Conformist -- model is clean and stable -- translation cost isn't justified
LegacyShippingSystem: Anticorruption Layer -- model is messy or unstable -- worth insulating our domain from it
```

`evaluate` makes the decision explicit and comparable: `PaymentGatewayAPI`, clean and stable with no achievable influence, correctly lands on Conformist. `LegacyShippingSystem`, neither clean nor stable, correctly lands on requiring an ACL instead — the same reasoning process, applied consistently, produces two different, well-justified verdicts.

### Level 3 — Advanced

```java
// File: AcceptedCostWhenChanged.java -- the payment gateway DOES eventually
// change its model; show the ACCEPTED cost of having conformed directly.
public class AcceptedCostWhenChanged {
    // Gateway V2: a genuine upstream change -- amount is now a STRING with decimal notation, not cents as a long
    static class PaymentGatewayApiV2 {
        record ChargeRequest(String cardToken, String amount, String currency) { } // BREAKING change to the type itself
        record ChargeResult(String chargeId, String status) { }
        ChargeResult charge(ChargeRequest request) { return new ChargeResult("chg_" + request.cardToken(), "succeeded"); }
    }

    // downstream code, conformed DIRECTLY -- must be updated EVERYWHERE it used the old shape
    static void processPaymentV2(PaymentGatewayApiV2 gateway) {
        var request = new PaymentGatewayApiV2.ChargeRequest("tok_visa", "9.99", "usd"); // updated to match the NEW shape
        var result = gateway.charge(request);
        System.out.println("Charge " + result.chargeId() + ": " + result.status());
    }

    public static void main(String[] args) {
        processPaymentV2(new PaymentGatewayApiV2());
        System.out.println("Every call site using the OLD ChargeRequest shape needed updating -- the accepted cost of Conformist, paid when the upstream changed");
    }
}
```

**How to run:** `javac AcceptedCostWhenChanged.java && java AcceptedCostWhenChanged` (JDK 17+).

Expected output:
```
Charge chg_tok_visa: succeeded
Every call site using the OLD ChargeRequest shape needed updating -- the accepted cost of Conformist, paid when the upstream changed
```

The production-flavored honesty: when `PaymentGatewayApi` genuinely changes its `ChargeRequest` shape (from cents-as-`long` to decimal-as-`String`), every downstream call site using that type directly needs updating — there was no anticorruption layer absorbing the change in one place. This is the accepted, deliberate tradeoff of Conformist: lower ongoing translation-maintenance cost, paid for with direct exposure whenever the upstream does eventually change.

## 6. Walkthrough

1. `processPaymentV2(new PaymentGatewayApiV2())` constructs a `PaymentGatewayApiV2.ChargeRequest("tok_visa", "9.99", "usd")` — note the second argument is now the string `"9.99"`, matching the new upstream shape, rather than the old `999`-cents-as-long representation.
2. `gateway.charge(request)` runs, returning a `ChargeResult` exactly as before — the gateway's *behavior* toward a correctly-shaped request hasn't changed, only the shape of the request itself.
3. The print confirms the call succeeds with the updated code.
4. The final explanatory print states the concrete cost directly: because downstream code used `PaymentGatewayApi.ChargeRequest` directly (the Conformist choice from Level 1), every single call site constructing a `ChargeRequest` needed to be found and updated to match the new shape — there was no single translation function where this update could have been made once, the way an ACL's translator would have absorbed it.

```
Conformist (Level 1):        downstream code uses PaymentGatewayApi.ChargeRequest DIRECTLY, everywhere it's needed
        |
Upstream changes its model   (long cents -> String decimal)
        |
Accepted cost:                EVERY call site using ChargeRequest must be found and updated individually
```

## 7. Gotchas & takeaways

> **Gotcha:** Conformist is a legitimate choice, but it must be a *deliberate* one, made after weighing it against an ACL — defaulting to Conformist purely because building a translation layer felt like unnecessary upfront work, without actually evaluating the upstream's stability and cleanliness, risks an unpleasant surprise exactly like the one shown above, at a moment (an unannounced upstream breaking change) you don't get to choose.

- A Conformist relationship accepts the upstream context's model exactly as-is, with no translation layer and no negotiation over the upstream's roadmap — the deliberate choice for a clean, stable upstream you have no realistic influence over.
- The concrete tradeoff versus an anticorruption layer: lower ongoing translation-maintenance cost, in exchange for direct exposure to the upstream's model everywhere it's used, with no single place absorbing a future change.
- Weigh the choice explicitly per dependency — model cleanliness, model stability, and whether you have any realistic influence over the upstream — rather than defaulting to Conformist simply to avoid the work of building a translator.
- Revisit an existing Conformist relationship if the upstream's model quality or stability degrades over time — what was a reasonable choice initially may no longer be, and upgrading to an ACL at that point becomes worth its cost.
