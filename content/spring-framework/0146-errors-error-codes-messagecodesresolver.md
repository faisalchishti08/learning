---
card: spring-framework
gi: 146
slug: errors-error-codes-messagecodesresolver
title: "Errors & error codes (MessageCodesResolver)"
---

## 1. What it is

When `Validator.validate()` calls `errors.rejectValue("amount", "amount.negative")`, Spring does not store just one error code — it generates a hierarchy of codes via `MessageCodesResolver`. `DefaultMessageCodesResolver` produces codes like `"amount.negative.order.amount"`, `"amount.negative.amount"`, `"amount.negative.double"`, `"amount.negative"`. The first code that resolves to a message in a `MessageSource` is used for display.

```
reject("amount.negative") on field "amount" of type double in object "order"
→ codes: [
    "amount.negative.order.amount",   // most specific: code.objectName.field
    "amount.negative.amount",         // code.field
    "amount.negative.double",         // code.fieldType
    "amount.negative"                 // code only (least specific)
  ]
```

## 2. Why & when

- **Internationalization** — store messages in `messages.properties` keyed by error code. Spring picks the most specific match.
- **Override granularity** — a generic `"field.required"` message suffices for most fields; a specific `"field.required.order.customerId"` overrides it just for `customerId` on `Order`.
- **Custom resolvers** — implement `MessageCodesResolver` to use your own code-naming conventions.
- **MVC error display** — Spring MVC's `<form:errors>` and Thymeleaf `#fields.errors()` iterate `BindingResult.getAllErrors()` and resolve messages via the code hierarchy.

## 3. Core concept

`DefaultMessageCodesResolver` generates codes for `rejectValue(field, code)`:

1. `code.objectName.field`
2. `code.field`
3. `code.fieldType` (simple type name, lowercase)
4. `code` alone

For `reject(code)` (global error):

1. `code.objectName`
2. `code`

`Errors` interface hierarchy:
- `Errors` — base: `reject`, `rejectValue`, `hasErrors`, `getAllErrors`, `getFieldErrors`
- `BindingResult extends Errors` — adds `getModel()`, `getTarget()`, `addAllErrors()`
- `BindException extends Exception implements BindingResult` — throwable form

Typical `messages.properties` file:

```properties
amount.negative=Amount must be positive
amount.negative.order.amount=Order amount must be a positive value greater than zero
field.required=This field is required
field.required.customer.email=A valid email address is required for account creation
```

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <!-- rejectValue call -->
  <rect x="10" y="30" width="200" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="52" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">errors.rejectValue("amount",</text>
  <text x="110" y="68" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">"amount.negative")</text>

  <!-- MessageCodesResolver -->
  <rect x="265" y="20" width="175" height="70" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="352" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">MessageCodesResolver</text>
  <text x="352" y="58" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">amount.negative.order.amount</text>
  <text x="352" y="72" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">amount.negative.amount</text>
  <text x="352" y="84" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">amount.negative.double</text>

  <!-- MessageSource -->
  <rect x="500" y="30" width="190" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="595" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">MessageSource</text>
  <text x="595" y="68" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">resolves first matching code</text>
  <text x="595" y="82" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">→ display message</text>

  <defs>
    <marker id="a146" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="b146" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="212" y1="55" x2="262" y2="55" stroke="#79c0ff" stroke-width="2" marker-end="url(#a146)"/>
  <line x1="442" y1="55" x2="497" y2="55" stroke="#6db33f" stroke-width="2" marker-end="url(#b146)"/>

  <!-- Hierarchy annotation -->
  <text x="350" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">4 codes generated (most specific → least specific)</text>

  <rect x="10" y="140" width="200" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="158" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Errors (interface)</text>
  <text x="110" y="172" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">reject / rejectValue / hasErrors</text>

  <rect x="265" y="140" width="175" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="352" y="158" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">BindingResult extends Errors</text>
  <text x="352" y="172" fill="#79c0ff" font-size="9"  text-anchor="middle" font-family="sans-serif">getTarget / getModel</text>

  <rect x="500" y="140" width="190" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="595" y="158" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">BindException</text>
  <text x="595" y="172" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">extends Exception, BindingResult</text>
</svg>

`MessageCodesResolver` expands one code into a specificity hierarchy; `MessageSource` resolves the first match.

## 5. Runnable example

### Level 1 — Basic

Demonstrate the code expansion produced by `DefaultMessageCodesResolver`; show how messages resolve.

```java
// ErrorCodesBasic.java
import org.springframework.context.support.*;
import org.springframework.validation.*;

class Invoice {
    private String invoiceId;
    private double amount;
    private String currency;

    Invoice(String invoiceId, double amount, String currency) {
        this.invoiceId = invoiceId;
        this.amount    = amount;
        this.currency  = currency;
    }

    public String getInvoiceId() { return invoiceId; }
    public double getAmount()    { return amount; }
    public String getCurrency()  { return currency; }
}

public class ErrorCodesBasic {
    public static void main(String[] args) {
        Invoice inv = new Invoice("", -10, "invalid");

        // Create a BeanPropertyBindingResult to capture errors
        Errors errors = new BeanPropertyBindingResult(inv, "invoice");

        // Reject several fields
        ValidationUtils.rejectIfEmptyOrWhitespace(errors, "invoiceId",
            "field.required");
        errors.rejectValue("amount", "amount.negative",
            new Object[]{0}, "Amount must be > {0}");
        errors.rejectValue("currency", "currency.invalid",
            "Currency must be a 3-letter ISO code");
        errors.reject("invoice.invalid",
            "Invoice cannot be saved in its current state");

        System.out.println("=== All errors (" + errors.getErrorCount() + ") ===");
        for (ObjectError e : errors.getAllErrors()) {
            System.out.println("\n  code(s): " + java.util.Arrays.toString(e.getCodes()));
            System.out.println("  default message: " + e.getDefaultMessage());
            if (e instanceof FieldError fe) {
                System.out.println("  field: " + fe.getField() +
                    " rejected value: " + fe.getRejectedValue());
            }
        }

        // Show code hierarchy for the amount field
        System.out.println("\n=== MessageCodesResolver expansion ===");
        var resolver = new DefaultMessageCodesResolver();
        String[] codes = resolver.resolveMessageCodes("amount.negative", "invoice", "amount", double.class);
        for (String code : codes) System.out.println("  " + code);
    }
}
```

How to run: `java ErrorCodesBasic.java`

`DefaultMessageCodesResolver.resolveMessageCodes` directly shows the full code expansion: `amount.negative.invoice.amount`, `amount.negative.amount`, `amount.negative.double`, `amount.negative`. Codes are ordered most-specific to least-specific.

### Level 2 — Intermediate

`MessageSource` resolution with a properties file; show that the most specific matching code wins.

```java
// ErrorCodesMessages.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.support.*;
import org.springframework.validation.*;
import java.nio.file.*;
import java.util.*;

class Shipment {
    private String trackingId;
    private int weight;
    private String destination;

    Shipment(String trackingId, int weight, String destination) {
        this.trackingId  = trackingId;
        this.weight      = weight;
        this.destination = destination;
    }

    public String getTrackingId()  { return trackingId;  }
    public int getWeight()         { return weight;      }
    public String getDestination() { return destination; }
}

class ShipmentValidator implements Validator {
    @Override
    public boolean supports(Class<?> c) { return Shipment.class.isAssignableFrom(c); }

    @Override
    public void validate(Object t, Errors errors) {
        Shipment s = (Shipment) t;
        ValidationUtils.rejectIfEmptyOrWhitespace(errors, "trackingId", "field.required");
        if (s.getWeight() <= 0) errors.rejectValue("weight", "field.positive");
        if (s.getWeight() > 30_000) errors.rejectValue("weight", "weight.exceeds.max",
            new Object[]{30_000}, "Weight exceeds {0}g limit");
        ValidationUtils.rejectIfEmptyOrWhitespace(errors, "destination", "field.required");
    }
}

@Configuration
class MsgCfg {
    @Bean
    ReloadableResourceBundleMessageSource messageSource() {
        var ms = new ReloadableResourceBundleMessageSource();
        ms.setBasename("classpath:validation-messages");
        ms.setDefaultEncoding("UTF-8");
        return ms;
    }
}

public class ErrorCodesMessages {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("validation-messages.properties"),
            "field.required=This field is required\n" +
            "field.required.shipment.trackingId=A tracking ID is mandatory for all shipments\n" +
            "field.positive=Value must be positive\n" +
            "weight.exceeds.max=Package weight {0}g exceeds the 30000g limit\n");

        var ctx = new AnnotationConfigApplicationContext(MsgCfg.class);
        MessageSource ms = ctx.getBean(MessageSource.class);

        Shipment s = new Shipment("", 0, "");  // all fields invalid
        Errors errors = new BeanPropertyBindingResult(s, "shipment");
        new ShipmentValidator().validate(s, errors);

        System.out.println("=== Resolved messages ===");
        for (ObjectError e : errors.getAllErrors()) {
            String msg = ms.getMessage(e, Locale.ENGLISH);
            if (e instanceof FieldError fe) {
                System.out.println("  field=" + fe.getField() + ": " + msg);
                System.out.println("    codes=" + Arrays.toString(e.getCodes()));
            } else {
                System.out.println("  global: " + msg);
            }
        }

        ctx.close();
        Files.deleteIfExists(Path.of("validation-messages.properties"));
    }
}
```

How to run: `java ErrorCodesMessages.java`

The `trackingId` field uses `"field.required"` code. `MessageSource` resolves `"field.required.shipment.trackingId"` first (the most specific code) → returns the specific message. All other fields fall through to the generic `"field.required"` message.

### Level 3 — Advanced

Custom `MessageCodesResolver` with a PREFIX strategy; `BindException` for exception-based error handling; multi-locale message resolution.

```java
// ErrorCodesAdvanced.java
import org.springframework.context.support.*;
import org.springframework.validation.*;
import java.nio.file.*;
import java.util.*;

class PaymentRequest {
    private String paymentMethod;
    private double amount;
    private String currency;
    private String reference;

    PaymentRequest(String paymentMethod, double amount, String currency, String ref) {
        this.paymentMethod = paymentMethod;
        this.amount        = amount;
        this.currency      = currency;
        this.reference     = ref;
    }

    public String getPaymentMethod() { return paymentMethod; }
    public double getAmount()        { return amount; }
    public String getCurrency()      { return currency; }
    public String getReference()     { return reference; }
}

class PaymentValidator implements Validator {
    private static final Set<String> METHODS = Set.of("CARD", "BANK_TRANSFER", "CRYPTO");

    @Override
    public boolean supports(Class<?> c) { return PaymentRequest.class.isAssignableFrom(c); }

    @Override
    public void validate(Object t, Errors errors) {
        PaymentRequest p = (PaymentRequest) t;
        ValidationUtils.rejectIfEmptyOrWhitespace(errors, "paymentMethod", "required");
        if (p.getPaymentMethod() != null && !METHODS.contains(p.getPaymentMethod())) {
            errors.rejectValue("paymentMethod", "invalid",
                new Object[]{METHODS}, "Must be one of {0}");
        }
        if (p.getAmount() <= 0) errors.rejectValue("amount", "positive");
        if (p.getAmount() > 50_000) errors.rejectValue("amount", "too.large");
        ValidationUtils.rejectIfEmptyOrWhitespace(errors, "currency", "required");
    }
}

public class ErrorCodesAdvanced {
    public static void main(String[] args) throws Exception {
        // Message files for two locales
        Files.writeString(Path.of("pay-messages.properties"),
            "required=Required\n" +
            "required.paymentRequest.paymentMethod=Payment method is required\n" +
            "invalid=Invalid value\n" +
            "positive=Must be a positive number\n" +
            "too.large=Exceeds maximum allowed value\n" +
            "too.large.paymentRequest.amount=Payment exceeds the $50,000 limit\n");

        Files.writeString(Path.of("pay-messages_fr.properties"),
            "required=Obligatoire\n" +
            "required.paymentRequest.paymentMethod=Mode de paiement obligatoire\n" +
            "positive=Doit etre un nombre positif\n" +
            "too.large.paymentRequest.amount=Paiement depasse la limite de 50 000 dollars\n");

        var ms = new ReloadableResourceBundleMessageSource();
        ms.setBasename("classpath:pay-messages");
        ms.setDefaultEncoding("UTF-8");

        // Show code expansion with PREFIX strategy
        System.out.println("=== PREFIX strategy code expansion ===");
        var prefixResolver = new DefaultMessageCodesResolver();
        prefixResolver.setMessageCodeFormatter(DefaultMessageCodesResolver.Format.PREFIX_ERROR_CODE);
        String[] prefixCodes = prefixResolver.resolveMessageCodes(
            "required", "paymentRequest", "paymentMethod", String.class);
        System.out.println("PREFIX codes: " + Arrays.toString(prefixCodes));

        String[] postfixCodes = new DefaultMessageCodesResolver().resolveMessageCodes(
            "required", "paymentRequest", "paymentMethod", String.class);
        System.out.println("POSTFIX codes (default): " + Arrays.toString(postfixCodes));

        // Validate and resolve in two locales
        var request = new PaymentRequest("UNKNOWN", -50.0, "", "REF-001");
        Errors errors = new BeanPropertyBindingResult(request, "paymentRequest");
        new PaymentValidator().validate(request, errors);

        for (Locale locale : List.of(Locale.ENGLISH, Locale.FRENCH)) {
            System.out.println("\n=== " + locale.getDisplayLanguage() + " ===");
            for (ObjectError e : errors.getAllErrors()) {
                String msg = ms.getMessage(e, locale);
                String field = e instanceof FieldError fe ? "[" + fe.getField() + "] " : "[global] ";
                System.out.println("  " + field + msg);
            }
        }

        // BindException — throwable form of BindingResult
        System.out.println("\n=== BindException ===");
        var goodRequest = new PaymentRequest("CARD", 100.0, "USD", "REF-002");
        Errors result = new BeanPropertyBindingResult(goodRequest, "paymentRequest");
        new PaymentValidator().validate(goodRequest, result);
        if (result.hasErrors()) {
            throw new BindException(result);
        }
        System.out.println("No errors — BindException would not be thrown");

        Files.deleteIfExists(Path.of("pay-messages.properties"));
        Files.deleteIfExists(Path.of("pay-messages_fr.properties"));
    }
}
```

How to run: `java ErrorCodesAdvanced.java`

`DefaultMessageCodesResolver.Format.PREFIX_ERROR_CODE` changes code order: most-specific first is the same, but code format differs (`required.paymentRequest.paymentMethod` vs `required.paymentMethod`). Multi-locale resolution shows the same error codes resolving to different messages. `BindException` wraps `BindingResult` as a checked exception for service-layer contracts.

## 6. Walkthrough

Code resolution for `rejectValue("paymentMethod", "required")` on object name `"paymentRequest"`:

1. `DefaultMessageCodesResolver` called with: `errorCode="required"`, `objectName="paymentRequest"`, `field="paymentMethod"`, `fieldType=String.class`.
2. Generates: `["required.paymentRequest.paymentMethod", "required.paymentMethod", "required.java.lang.String", "required"]`.
3. `ms.getMessage(error, Locale.ENGLISH)` tries each code in order.
4. `"required.paymentRequest.paymentMethod"` → found in `pay-messages.properties` → `"Payment method is required"`.
5. Resolution stops at the first match — more specific wins.

## 7. Gotchas & takeaways

> `errors.rejectValue("field", "code", "default message")` stores the default message ONLY as a fallback. If any code in the generated hierarchy resolves in the `MessageSource`, the `MessageSource` value is used, NOT the default message. Developers often put the human-readable message in the `defaultMessage` parameter and wonder why it doesn't appear — because the `MessageSource` has a matching key.

> `BindingResult` must appear immediately after the `@ModelAttribute` / `@RequestBody` parameter in Spring MVC controller methods. If you put another parameter between them, Spring throws `IllegalStateException` at startup.

- `DefaultMessageCodesResolver.Format.PREFIX_ERROR_CODE` (codes like `required.objectName.field`) was introduced to reverse the postfix style — useful when your existing message key convention puts the code first.
- `MessageCodesResolver` can be replaced globally on a `DataBinder` or in Spring MVC via `WebBindingInitializer.setMessageCodesResolver(...)`.
- For i18n, always provide at least the generic code (`"required"`) in all locale message files; specific codes are optional overrides.
- `ObjectError.getCodes()` on a resolved error returns all generated codes — use this in tests to assert the exact code hierarchy Spring produces.
