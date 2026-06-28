---
card: spring-boot
gi: 106
slug: messagecodesresolver
title: MessageCodesResolver
---

## 1. What it is

`MessageCodesResolver` is a Spring MVC interface that generates **error codes** from validation constraint violations. When a field fails validation, Spring MVC asks the resolver for a prioritised list of message codes, then looks each one up in a `MessageSource` (typically `messages.properties`) to find a human-readable error message.

For a `@NotBlank` violation on field `name` of class `OrderRequest`, the default resolver generates these codes in priority order:

```
NotBlank.orderRequest.name      ← most specific (constraint + type + field)
NotBlank.name                   ← medium (constraint + field name)
NotBlank.java.lang.String       ← medium (constraint + field type)
NotBlank                        ← least specific (constraint only)
```

Spring MVC searches each code in the `MessageSource` and uses the first one it finds. If none is found, the constraint's own `message` attribute is used as a fallback.

Spring Boot auto-configures `DefaultMessageCodesResolver` with `PREFIX_ERROR_CODE` style by default, which is the behaviour described above.

## 2. Why & when

`MessageCodesResolver` matters when building forms or APIs that return structured validation error messages. By producing a hierarchy of codes, Spring lets you define:
- A generic message for a constraint type (`NotBlank=This field is required`).
- A field-specific override (`NotBlank.name=Name cannot be empty`).
- A type-specific override (`NotBlank.java.lang.String=Text fields cannot be blank`).

This system eliminates repetitive per-field message definitions — define once at the constraint level, override only where the wording needs to differ.

You need to understand `MessageCodesResolver` when:
- Customising validation error messages in forms or API responses.
- Switching from prefix-based to suffix-based code style (`PREFIX_ERROR_CODE` vs. `POSTFIX_ERROR_CODE`).
- Integrating with a custom error response format that includes error codes for client-side I18N.

## 3. Core concept

Two built-in styles:

**`PREFIX_ERROR_CODE` (default):**
```
NotBlank.orderRequest.name
NotBlank.name
NotBlank.java.lang.String
NotBlank
```

**`POSTFIX_ERROR_CODE`:**
```
orderRequest.name.NotBlank
name.NotBlank
java.lang.String.NotBlank
NotBlank
```

To change the style globally:
```properties
spring.mvc.messagecodesresolver.style=POSTFIX_ERROR_CODE
```

The `messages.properties` file in `src/main/resources` serves as the message catalogue:
```properties
NotBlank.orderRequest.name=Order name is required
NotBlank=This field must not be blank
Size.orderRequest.quantity=Quantity must be between {2} and {1}
```

`{0}` is the field name, `{1}` is the first constraint attribute value, `{2}` is the second.

## 4. Diagram

<svg viewBox="0 0 680 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MessageCodesResolver generates a priority list of codes from a validation error; MessageSource resolves the first matching code to a message string">
  <rect x="8" y="8" width="664" height="254" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">MessageCodesResolver — Validation Error Code Generation</text>

  <!-- Constraint violation input -->
  <rect x="20" y="55" width="200" height="60" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="120" y="73" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Constraint Violation</text>
  <text x="120" y="89" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">annotation: @NotBlank</text>
  <text x="120" y="104" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">field: name (String)</text>
  <text x="120" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">object: OrderRequest</text>

  <!-- Arrow to resolver -->
  <defs><marker id="mr" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="222" y1="85" x2="255" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#mr)"/>

  <!-- Resolver -->
  <rect x="257" y="55" width="180" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="347" y="73" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">MessageCodesResolver</text>
  <text x="347" y="89" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DefaultMessageCodesResolver</text>
  <text x="347" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">PREFIX_ERROR_CODE style</text>

  <!-- Arrow to codes -->
  <line x1="439" y1="85" x2="470" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#mr)"/>

  <!-- Generated codes -->
  <rect x="472" y="48" width="190" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="567" y="65" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Generated codes</text>
  <text x="487" y="81" fill="#e6edf3" font-size="9" font-family="monospace">① NotBlank.orderRequest.name</text>
  <text x="487" y="95" fill="#e6edf3" font-size="9" font-family="monospace">② NotBlank.name</text>
  <text x="487" y="109" fill="#8b949e" font-size="9" font-family="monospace">③ NotBlank.java.lang.String</text>
  <text x="487" y="123" fill="#8b949e" font-size="9" font-family="monospace">④ NotBlank</text>

  <!-- MessageSource lookup -->
  <line x1="567" y1="130" x2="567" y2="155" stroke="#8b949e" stroke-width="1.5" marker-end="url(#mr)"/>

  <rect x="130" y="157" width="480" height="56" rx="6" fill="#0d1117" stroke="#f0883e" stroke-width="1.5"/>
  <text x="370" y="175" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">MessageSource (messages.properties)</text>
  <text x="370" y="191" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">NotBlank.orderRequest.name=Order name is required</text>
  <text x="370" y="205" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">(if not found → check ②, ③, ④ in order)</text>
</svg>

Codes are checked in specificity order; first match in `messages.properties` wins.

## 5. Runnable example

```java
// MessageCodesResolverDemo.java — run: java MessageCodesResolverDemo.java  (JDK 17+)
// Simulates how DefaultMessageCodesResolver generates codes and how MessageSource resolves them.

import java.util.*;

public class MessageCodesResolverDemo {

    // Simulates DefaultMessageCodesResolver with PREFIX_ERROR_CODE style
    static List<String> generateCodes(String annotation, String objectType,
                                       String fieldName, String fieldType) {
        // Object type name: 'OrderRequest' → 'orderRequest' (camelCase)
        String obj = Character.toLowerCase(objectType.charAt(0)) + objectType.substring(1);
        // Field type simple name: 'java.lang.String' → 'java.lang.String'
        return List.of(
            annotation + "." + obj + "." + fieldName,   // most specific
            annotation + "." + fieldName,
            annotation + "." + fieldType,
            annotation                                   // least specific
        );
    }

    // Simulates a MessageSource backed by messages.properties
    static final Map<String, String> MESSAGES = new LinkedHashMap<>(Map.of(
        "NotBlank.orderRequest.name",       "Order name is required",
        "NotBlank",                          "This field must not be blank",
        "Size.orderRequest.quantity",        "Quantity must be between {min} and {max}",
        "Email.orderRequest.customerEmail",  "Please provide a valid email address",
        "NotNull",                           "This field is required"
    ));

    static String resolveMessage(List<String> codes) {
        for (String code : codes) {
            String msg = MESSAGES.get(code);
            if (msg != null) return "Code '" + code + "' → \"" + msg + "\"";
        }
        return "No code found; fallback to annotation message attribute";
    }

    static void validate(String annotation, String objectType,
                         String fieldName, String fieldType) {
        System.out.printf("Violation: @%s on %s.%s (%s)%n",
                annotation, objectType, fieldName, fieldType);
        List<String> codes = generateCodes(annotation, objectType, fieldName, fieldType);
        System.out.println("  Generated codes:");
        codes.forEach(c -> System.out.println("    " + c));
        System.out.println("  Resolved: " + resolveMessage(codes));
        System.out.println();
    }

    public static void main(String[] args) {
        System.out.println("=== PREFIX_ERROR_CODE style (default) ===\n");

        // Case 1: specific message defined
        validate("NotBlank", "OrderRequest", "name", "java.lang.String");

        // Case 2: only generic NotBlank defined
        validate("NotBlank", "OrderRequest", "description", "java.lang.String");

        // Case 3: Size constraint with specific message
        validate("Size", "OrderRequest", "quantity", "java.lang.Integer");

        // Case 4: Email with specific message
        validate("Email", "OrderRequest", "customerEmail", "java.lang.String");

        System.out.println("=== POSTFIX_ERROR_CODE style ===\n");
        // spring.mvc.messagecodesresolver.style=POSTFIX_ERROR_CODE
        String[] postfixCodes = {
            "orderRequest.name.NotBlank",
            "name.NotBlank",
            "java.lang.String.NotBlank",
            "NotBlank"
        };
        System.out.println("Codes for @NotBlank on OrderRequest.name:");
        for (String c : postfixCodes) System.out.println("  " + c);
    }
}
```

**How to run:** `java MessageCodesResolverDemo.java`

## 6. Walkthrough

- `generateCodes` produces the four-level hierarchy. The object type name is camelCase-lowercased: `OrderRequest` → `orderRequest`. This matches how Spring names beans by default.
- **Case 1** (`name` field): the most specific code `NotBlank.orderRequest.name` exists in `MESSAGES` with `"Order name is required"`. The search stops immediately.
- **Case 2** (`description` field): no specific or medium code matches; the fallthrough to `NotBlank` finds `"This field must not be blank"` — the generic message. This is how one message covers all `@NotBlank` violations that lack a specific override.
- **Case 3** (`Size` on `quantity`): `Size.orderRequest.quantity` exists with `"Quantity must be between {min} and {max}"`. In real Spring, `{min}` and `{max}` are replaced with the actual constraint attribute values via `MessageFormat`.
- The `POSTFIX_ERROR_CODE` style reverses the order: `orderRequest.name.NotBlank` instead of `NotBlank.orderRequest.name`. Neither style is universally better; prefix is Spring MVC's default and aligns with `BindingResult.getFieldError().getCodes()`.

## 7. Gotchas & takeaways

> **`messages.properties` must be UTF-8 (or Latin-1 for legacy Spring).** If you include accented characters or non-ASCII in error messages, use `spring.messages.encoding=UTF-8` in `application.properties`. The default encoding is ISO-8859-1, which garbles non-ASCII.

> **Message codes use the *simple* class name, not the fully qualified name.** `OrderRequest` becomes `orderRequest` in codes, not `com.example.request.orderRequest`. If two classes in different packages share a simple name, their codes collide.

- Add `messages.properties` (default locale) and `messages_fr.properties` etc. for I18N — Spring Boot auto-configures the `MessageSource` to scan them.
- `spring.messages.basename=messages,i18n/errors` lets you split messages across multiple files.
- `BindingResult.getFieldError("name").getCodes()` returns the generated codes at runtime — inspect them in tests to verify the exact codes your resolver produces.
- To customise the resolver, declare a `@Bean MessageCodesResolver` and Spring Boot backs off its default.
- `spring.mvc.messagecodesresolver.style=POSTFIX_ERROR_CODE` switches globally without Java config.
