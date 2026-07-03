---
card: spring-framework
gi: 173
slug: templated-expressions
title: Templated expressions
---

## 1. What it is

By default the SpEL parser treats the entire input string as a single expression. **Template mode** mixes literal text and embedded SpEL expressions in one string. Expressions are delimited by `#{` … `}`; everything else is literal text passed through unchanged.

```java
// Without template mode — the whole string must be a valid SpEL expression
parser.parseExpression("'Hello ' + name").getValue(ctx);

// With template mode — free text with #{…} embedded expressions
parser.parseExpression("Hello, #{name}! You have #{count} messages.",
                        new TemplateParserContext())
      .getValue(ctx, String.class);
// → "Hello, Alice! You have 3 messages."
```

`TemplateParserContext` implements `ParserContext` and tells the parser the prefix (`#{`) and suffix (`}`) that mark expression segments. You can supply a custom `ParserContext` to use different delimiters such as `${` … `}` or `<<` … `>>`.

## 2. Why & when

- **Notification and email bodies** — compose a welcome or alert message with user-specific data injected via `#{…}`.
- **Log and audit messages** — `"User #{userId} changed #{field} from #{oldVal} to #{newVal}"` builds a rich message in one expression.
- **SQL fragment building** — generate a readable clause like `"WHERE status = '#{status}' AND region = '#{region}'"` for logging (never for execution — use prepared statements for that).
- **`@Value` labels** — `@Value("app-#{environment}-v#{version}")` produces a bean name string with mixed literal and expression parts.
- **Spring MessageSource or template engines** — SpEL template mode is the basis for how Thymeleaf and Spring Expression language annotations compose messages.
- **Unit-test assertions** — build expected strings programmatically while keeping the template readable.

## 3. Core concept

The `TemplateParserContext` turns parsing into a two-pass process:

1. **Scan** — the parser splits the input into alternating literal and expression segments based on the delimiters.
2. **Evaluate** — literal segments are emitted as-is; each `#{…}` segment is parsed and evaluated as a full SpEL expression; results are converted to `String` via `toString()` and concatenated.

```
Input: "Hello, #{name.toUpperCase()}! Age: #{age >= 18 ? 'adult' : 'minor'}."
         ┌──literal──┐ ┌──expression──┐  ┌──literal──┐ ┌──────expression──────┐ ┌lit┐
Output:  "Hello, "   + "ALICE"          + "! Age: "   + "adult"                + "."
       = "Hello, ALICE! Age: adult."
```

| Mode | Call | The string means… |
|---|---|---|
| Expression (default) | `parseExpression("2 + 2")` | entire string is one SpEL expression |
| Template | `parseExpression("val: #{2+2}", new TemplateParserContext())` | `"val: "` is literal; `2+2` is expression → `"val: 4"` |
| Custom delimiters | `parseExpression("val: ${2+2}", new TemplateParserContext("${", "}"))` | same but uses `${…}` |

Inside `#{…}` any SpEL expression is valid: method calls, ternary, safe navigation, collection operators — the full language.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="ta173" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Input string at top -->
  <rect x="10" y="10" width="680" height="34" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="20" y="32" fill="#e6edf3" font-size="11" font-family="monospace">Hello, #{name.toUpperCase()}! You have #{count} messages. #{count == 1 ? '' : 's'}</text>

  <!-- Labels below input -->
  <!-- Literal 1: "Hello, " -->
  <rect x="10" y="55" width="55" height="20" rx="3" fill="#8b949e" opacity="0.25"/>
  <text x="37" y="69" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">literal</text>

  <!-- Expr 1: name.toUpperCase() -->
  <rect x="68" y="55" width="130" height="20" rx="3" fill="#6db33f" opacity="0.3"/>
  <text x="133" y="69" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">#{name.toUpperCase()}</text>

  <!-- Literal 2 -->
  <rect x="202" y="55" width="80" height="20" rx="3" fill="#8b949e" opacity="0.25"/>
  <text x="242" y="69" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">literal</text>

  <!-- Expr 2: count -->
  <rect x="285" y="55" width="60" height="20" rx="3" fill="#6db33f" opacity="0.3"/>
  <text x="315" y="69" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">#{count}</text>

  <!-- Literal 3 -->
  <rect x="349" y="55" width="80" height="20" rx="3" fill="#8b949e" opacity="0.25"/>
  <text x="389" y="69" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">literal</text>

  <!-- Expr 3: conditional -->
  <rect x="433" y="55" width="240" height="20" rx="3" fill="#6db33f" opacity="0.3"/>
  <text x="553" y="69" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">#{count == 1 ? '' : 's'}</text>

  <!-- Arrow down to evaluation -->
  <line x1="350" y1="80" x2="350" y2="108" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ta173)"/>
  <text x="380" y="98" fill="#8b949e" font-size="9" font-family="sans-serif">evaluate + concatenate</text>

  <!-- Evaluation box -->
  <rect x="10" y="112" width="680" height="34" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="20" y="134" fill="#8b949e" font-size="11" font-family="monospace">Hello, </text>
  <text x="70" y="134" fill="#6db33f" font-size="11" font-family="monospace">ALICE</text>
  <text x="106" y="134" fill="#8b949e" font-size="11" font-family="monospace">! You have </text>
  <text x="204" y="134" fill="#6db33f" font-size="11" font-family="monospace">3</text>
  <text x="218" y="134" fill="#8b949e" font-size="11" font-family="monospace"> messages. </text>
  <text x="306" y="134" fill="#6db33f" font-size="11" font-family="monospace">s</text>

  <!-- Legend -->
  <rect x="10" y="158" width="12" height="12" rx="2" fill="#8b949e" opacity="0.4"/>
  <text x="28" y="169" fill="#8b949e" font-size="9" font-family="sans-serif">literal text (passed through)</text>
  <rect x="200" y="158" width="12" height="12" rx="2" fill="#6db33f" opacity="0.5"/>
  <text x="218" y="169" fill="#6db33f" font-size="9" font-family="sans-serif">#{…} expression (evaluated, converted to String)</text>
  <text x="10" y="188" fill="#8b949e" font-size="9" font-family="sans-serif">Custom delimiters: new TemplateParserContext("${", "}")  or  new TemplateParserContext("«", "»")</text>
</svg>

Each `#{…}` segment is a full SpEL expression; literal segments are emitted verbatim; results concatenate left-to-right into the final string.

## 5. Runnable example

All three levels build a notification system — the same message template growing from a simple greeting to a production-ready multi-template service.

### Level 1 — Basic

A welcome message template with two `#{…}` expression slots. Variables are bound in `StandardEvaluationContext`.

```java
// SpelTemplateBasic.java
import org.springframework.expression.*;
import org.springframework.expression.common.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;

public class SpelTemplateBasic {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx    = new StandardEvaluationContext();
        var tmpl   = new TemplateParserContext();

        // Bind variables
        ctx.setVariable("name",  "Alice");
        ctx.setVariable("count", 3);

        // Simple greeting template
        String greeting = parser.parseExpression(
            "Hello, #{#name}! You have #{#count} new messages.",
            tmpl).getValue(ctx, String.class);
        System.out.println(greeting);
        // Hello, Alice! You have 3 new messages.

        // Expression inside #{} can be arbitrarily complex
        ctx.setVariable("count", 1);
        String singular = parser.parseExpression(
            "Hello, #{#name}! You have #{#count} new message#{#count == 1 ? '' : 's'}.",
            tmpl).getValue(ctx, String.class);
        System.out.println(singular);
        // Hello, Alice! You have 1 new message.

        // Method calls and arithmetic inside #{}
        ctx.setVariable("price", 29.99);
        ctx.setVariable("qty",   4);
        String order = parser.parseExpression(
            "Order total: $#{#price * #qty} for #{#qty} item#{#qty == 1 ? '' : 's'}.",
            tmpl).getValue(ctx, String.class);
        System.out.println(order);
        // Order total: $119.96 for 4 items.
    }
}
```

How to run: `java SpelTemplateBasic.java`

`TemplateParserContext` (from `org.springframework.expression.common`) defines the `#{` / `}` delimiters. Everything outside those delimiters is emitted verbatim. Inside `#{}` the variable `#name` uses the `#` prefix because it is a context variable (not a root property). The ternary `#count == 1 ? '' : 's'` evaluates to an empty string or `"s"` — SpEL concatenates the result with surrounding literal text.

### Level 2 — Intermediate

Same notification system — add method calls on objects, safe navigation, Elvis defaults, and reuse the parsed expression for multiple evaluations.

```java
// SpelTemplateIntermediate.java
import org.springframework.expression.*;
import org.springframework.expression.common.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.time.*;
import java.time.format.*;

class UserProfile {
    private String firstName, lastName, email;
    private int unreadCount;
    UserProfile(String f, String l, String e, int u) {
        firstName=f; lastName=l; email=e; unreadCount=u;
    }
    public String getFirstName()   { return firstName; }
    public String getLastName()    { return lastName; }
    public String getEmail()       { return email; }
    public int getUnreadCount()    { return unreadCount; }
    public String getFullName()    { return firstName + " " + lastName; }
    public String getInitials()    { return "" + firstName.charAt(0) + lastName.charAt(0); }
}

public class SpelTemplateIntermediate {
    public static void main(String[] args) {
        var parser  = new SpelExpressionParser();
        var tmpl    = new TemplateParserContext();
        String date = LocalDate.now().format(DateTimeFormatter.ofPattern("MMM d, yyyy"));

        // Parse ONCE, evaluate MANY times (more efficient than re-parsing)
        Expression welcomeExpr = parser.parseExpression(
            "Dear #{fullName},\n" +
            "Welcome! Your account (#{email}) is active as of #{#today}.\n" +
            "Unread messages: #{unreadCount > 0 ? unreadCount : 'none'}.",
            tmpl);

        UserProfile alice = new UserProfile("Alice", "Smith", "alice@example.com", 5);
        UserProfile bob   = new UserProfile("Bob",   "Jones", "bob@example.com",   0);

        for (var user : new UserProfile[]{alice, bob}) {
            var ctx = new StandardEvaluationContext(user); // root object = user
            ctx.setVariable("today", date);
            System.out.println(welcomeExpr.getValue(ctx, String.class));
            System.out.println("---");
        }

        // Safe navigation and Elvis in templates
        var parser2 = new SpelExpressionParser();
        var ctx2    = new StandardEvaluationContext();
        ctx2.setVariable("profile", null); // missing profile

        String badge = parser2.parseExpression(
            "[#{#profile?.getInitials() ?: '??'}] #{#profile?.getFullName() ?: 'Guest User'}",
            tmpl).getValue(ctx2, String.class);
        System.out.println(badge); // [??] Guest User

        ctx2.setVariable("profile", alice);
        String badge2 = parser2.parseExpression(
            "[#{#profile?.getInitials() ?: '??'}] #{#profile?.getFullName() ?: 'Guest User'}",
            tmpl).getValue(ctx2, String.class);
        System.out.println(badge2); // [AS] Alice Smith
    }
}
```

How to run: `java SpelTemplateIntermediate.java`

`new StandardEvaluationContext(user)` sets `user` as the *root object*, so `fullName`, `email`, and `unreadCount` resolve directly as root properties (no `#` prefix needed). Calling `parser.parseExpression(...)` once and reusing the `Expression` object is more efficient than re-parsing for each user — the AST is built once. `#profile?.getInitials() ?: '??'` combines safe navigation and Elvis inside a `#{}` expression slot.

### Level 3 — Advanced

A Spring-managed template service holds named templates as beans; a custom `TemplateParserContext` uses `${` … `}` delimiters (matching property-injection style) to avoid confusion with SpEL `#{}`.

```java
// SpelTemplateAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.expression.*;
import org.springframework.expression.common.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

// Custom context: uses ${…} delimiters instead of #{…}
class DollarParserContext implements ParserContext {
    public static final DollarParserContext INSTANCE = new DollarParserContext();
    public boolean isTemplate()          { return true; }
    public String getExpressionPrefix()  { return "${"; }
    public String getExpressionSuffix()  { return "}"; }
}

class NotificationTemplate {
    private final String name;
    private final String body;
    NotificationTemplate(String name, String body) { this.name=name; this.body=body; }
    public String getName() { return name; }
    public String getBody() { return body; }
}

class TemplateRegistry {
    private final Map<String, NotificationTemplate> templates = new LinkedHashMap<>();
    void register(NotificationTemplate t) { templates.put(t.getName(), t); }
    public NotificationTemplate get(String name) { return templates.get(name); }
    public Map<String, NotificationTemplate> getTemplates() { return templates; }
}

@Configuration
class TemplateCfg {
    @Bean
    public TemplateRegistry templateRegistry() {
        var registry = new TemplateRegistry();
        registry.register(new NotificationTemplate("welcome",
            "Hi ${firstName}, welcome to ${appName}! " +
            "Your plan: ${plan.toUpperCase()}."));
        registry.register(new NotificationTemplate("invoice",
            "Invoice #${invoiceId}: $${amount} due on ${dueDate}. " +
            "Status: ${paid ? 'PAID' : 'OUTSTANDING'}."));
        return registry;
    }
}

@org.springframework.stereotype.Service
class NotificationService {
    @Autowired private TemplateRegistry registry;
    private final SpelExpressionParser parser = new SpelExpressionParser();

    public String render(String templateName, Map<String, Object> data) {
        NotificationTemplate t = registry.get(templateName);
        if (t == null) throw new IllegalArgumentException("Unknown template: " + templateName);
        var ctx = new StandardEvaluationContext();
        data.forEach(ctx::setVariable);
        return parser.parseExpression(t.getBody(), DollarParserContext.INSTANCE)
                     .getValue(ctx, String.class);
    }
}

public class SpelTemplateAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(
            TemplateCfg.class, NotificationService.class);
        var svc = ctx.getBean(NotificationService.class);

        // Welcome email
        System.out.println(svc.render("welcome", Map.of(
            "firstName", "Alice",
            "appName",   "BookHub",
            "plan",      "premium"
        )));
        // Hi Alice, welcome to BookHub! Your plan: PREMIUM.

        // Invoice notification
        System.out.println(svc.render("invoice", Map.of(
            "invoiceId", "INV-2024-007",
            "amount",    "149.99",
            "dueDate",   "2024-08-15",
            "paid",      false
        )));
        // Invoice #INV-2024-007: $149.99 due on 2024-08-15. Status: OUTSTANDING.

        ctx.close();
    }
}
```

How to run: `java SpelTemplateAdvanced.java`

`DollarParserContext` implements `ParserContext` with `${` and `}` as delimiters — a common choice when templates coexist with Spring's `@Value` `#{…}` notation, avoiding visual confusion. `NotificationService.render` is generic: it accepts any template name and a `Map<String, Object>` — SpEL evaluates `${firstName}` by resolving variable `firstName` from the context. Storing templates in a `TemplateRegistry` bean means they can be loaded from a database or config file and hot-reloaded without code changes.

## 6. Walkthrough

Tracing `svc.render("welcome", Map.of("firstName","Alice","appName","BookHub","plan","premium"))` end-to-end.

**Step 1 — `render` called:**
- `templateName = "welcome"`, `data = {firstName=Alice, appName=BookHub, plan=premium}`
- `registry.get("welcome")` returns the `NotificationTemplate` whose body is `"Hi ${firstName}, welcome to ${appName}! Your plan: ${plan.toUpperCase()}."`

**Step 2 — Build context:**
- A fresh `StandardEvaluationContext` is created.
- `data.forEach(ctx::setVariable)` binds: `#firstName = "Alice"`, `#appName = "BookHub"`, `#plan = "premium"`.

**Step 3 — Parse with `DollarParserContext`:**

The parser scans the body and splits it at `${…}`:

| Segment type | Content |
|---|---|
| Literal | `"Hi "` |
| Expression | `firstName` |
| Literal | `", welcome to "` |
| Expression | `appName` |
| Literal | `"! Your plan: "` |
| Expression | `plan.toUpperCase()` |
| Literal | `"."` |

**Step 4 — Evaluate each expression segment:**

- `firstName` → looks up variable `#firstName` → `"Alice"`
- `appName` → looks up variable `#appName` → `"BookHub"`
- `plan.toUpperCase()` → looks up `#plan = "premium"`, calls `.toUpperCase()` → `"PREMIUM"`

**Step 5 — Concatenate:**

```
"Hi " + "Alice" + ", welcome to " + "BookHub" + "! Your plan: " + "PREMIUM" + "."
= "Hi Alice, welcome to BookHub! Your plan: PREMIUM."
```

**Request → Response view for `render()`:**

```
Caller
  │
  │  render("welcome", {firstName="Alice", appName="BookHub", plan="premium"})
  ▼
NotificationService.render()
  │  1. registry.get("welcome") → template body string
  │  2. build StandardEvaluationContext, bind variables
  │  3. parser.parseExpression(body, DollarParserContext.INSTANCE) → Expression AST
  │  4. expression.getValue(ctx, String.class)
  │       ├─ literal "Hi "
  │       ├─ eval firstName → "Alice"
  │       ├─ literal ", welcome to "
  │       ├─ eval appName → "BookHub"
  │       ├─ literal "! Your plan: "
  │       ├─ eval plan.toUpperCase() → "PREMIUM"
  │       └─ literal "."
  │  5. concat all → result string
  ▼
"Hi Alice, welcome to BookHub! Your plan: PREMIUM."
```

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="wt173" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
  <!-- Template string -->
  <rect x="5" y="5" width="690" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="15" y="24" fill="#8b949e" font-size="10" font-family="monospace">Hi ${firstName}, welcome to ${appName}! Your plan: ${plan.toUpperCase()}.</text>

  <!-- Parse arrow -->
  <line x1="350" y1="38" x2="350" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#wt173)"/>
  <text x="480" y="54" fill="#8b949e" font-size="9" font-family="sans-serif">parse with DollarParserContext</text>

  <!-- Segments row -->
  <rect x="5"   y="63" width="28"  height="22" rx="3" fill="#8b949e" opacity="0.3"/>
  <text x="19"  y="78" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">Hi ·</text>
  <rect x="36"  y="63" width="80"  height="22" rx="3" fill="#6db33f" opacity="0.35"/>
  <text x="76"  y="78" fill="#6db33f" font-size="7" text-anchor="middle" font-family="monospace">${firstName}</text>
  <rect x="119" y="63" width="90"  height="22" rx="3" fill="#8b949e" opacity="0.3"/>
  <text x="164" y="78" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">, welcome to ·</text>
  <rect x="212" y="63" width="70"  height="22" rx="3" fill="#6db33f" opacity="0.35"/>
  <text x="247" y="78" fill="#6db33f" font-size="7" text-anchor="middle" font-family="monospace">${appName}</text>
  <rect x="285" y="63" width="80"  height="22" rx="3" fill="#8b949e" opacity="0.3"/>
  <text x="325" y="78" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">! Your plan: ·</text>
  <rect x="368" y="63" width="145" height="22" rx="3" fill="#6db33f" opacity="0.35"/>
  <text x="440" y="78" fill="#6db33f" font-size="7" text-anchor="middle" font-family="monospace">${plan.toUpperCase()}</text>
  <rect x="516" y="63" width="12"  height="22" rx="3" fill="#8b949e" opacity="0.3"/>
  <text x="522" y="78" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">.</text>

  <!-- Eval arrow -->
  <line x1="350" y1="89" x2="350" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#wt173)"/>
  <text x="400" y="104" fill="#8b949e" font-size="9" font-family="sans-serif">evaluate + concat</text>

  <!-- Result string -->
  <rect x="5" y="114" width="690" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="15" y="133" fill="#8b949e" font-size="10" font-family="monospace">Hi </text>
  <text x="37" y="133" fill="#6db33f" font-size="10" font-family="monospace">Alice</text>
  <text x="74" y="133" fill="#8b949e" font-size="10" font-family="monospace">, welcome to </text>
  <text x="171" y="133" fill="#6db33f" font-size="10" font-family="monospace">BookHub</text>
  <text x="222" y="133" fill="#8b949e" font-size="10" font-family="monospace">! Your plan: </text>
  <text x="319" y="133" fill="#6db33f" font-size="10" font-family="monospace">PREMIUM</text>
  <text x="373" y="133" fill="#8b949e" font-size="10" font-family="monospace">.</text>

  <text x="350" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">green = evaluated expression result · grey = literal text</text>
</svg>

The parser builds the AST once; each re-evaluation only re-runs the expression segments — literal segments are stored as constants in the AST and never re-parsed.

## 7. Gotchas & takeaways

> **Without `TemplateParserContext`, `#{` has no special meaning** — the whole string is parsed as one SpEL expression. Forgetting to pass the context gives a `SpelParseException` because `"Hello, #{name}"` is not valid SpEL. Always pass the `ParserContext` argument when your string contains literal text.

> **`null` results inside `#{…}` become the string `"null"`.** `"Status: #{status}"` where `status == null` produces `"Status: null"`, not an empty string. Guard with Elvis: `"Status: #{status ?: 'unknown'}"`.

- Parse the `Expression` object once, call `getValue(ctx)` many times — parsing is relatively expensive; evaluation is cheap. Caching the parsed expression is especially important in hot paths like per-request notification rendering.
- Literal text is part of the AST — modifying a template string requires re-parsing. If template bodies come from external storage, parse on load or on first use and cache.
- Custom delimiters (`new TemplateParserContext("${", "}")`) are useful when templates are embedded alongside Spring's `@Value` `#{…}` or Thymeleaf `${…}` syntax to reduce visual confusion. The delimiters are purely syntactic — the inner language is identical SpEL regardless.
- `#{}` inside a literal `#{…}` block cannot be nested — `"#{#{inner}}"` is a parse error. Build the inner value separately and bind it as a variable, then reference it from the template.
- `TemplateParserContext.DEFAULT_TEMPLATE_PARSER_CONTEXT` is a pre-built `TemplateParserContext` instance using `#{` / `}` — use it instead of `new TemplateParserContext()` to avoid unnecessary allocations when parsing many templates.
