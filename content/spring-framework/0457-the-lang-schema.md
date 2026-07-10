---
card: spring-framework
gi: 457
slug: the-lang-schema
title: "The lang schema"
---

## 1. What it is

The `lang` namespace (`xmlns:lang="http://www.springframework.org/schema/lang"`) is the XML entry point for dynamic-language beans covered earlier in this section — `<lang:groovy>`, `<lang:bsh>` (BeanShell), and historically `<lang:jruby>` — each declaring a bean whose implementation is a script rather than a compiled Java class, optionally with `refresh-check-delay` for live reloading. This card focuses on the schema's structure and how it fits alongside the other XML namespaces, since the mechanics of scripted and refreshable beans were already covered in depth in the previous section's dynamic-language cards.

```xml
<lang:groovy id="pricingRule"
    script-source="classpath:PricingRule.groovy"
    refresh-check-delay="5000"/>
```

## 2. Why & when

The `lang` schema exists for one specific purpose: declaring a bean whose class doesn't exist at compile time as ordinary Java, because it's written in a scripting language and compiled by Spring at runtime. This card exists in the Appendix because it's one of the group of XML schemas (alongside `util`, `aop`, `context`, `jee`, `jms`, `task`, and `cache`) that together make up "everything expressible in Spring XML beyond the base `beans` schema" — reach for it exactly when you need a scripted bean, as covered in this guide's earlier Kotlin/Groovy section.

Reach for `lang` elements specifically when:

- You need genuinely runtime-editable business logic — a pricing rule, a validation policy — that a non-Java-deploying operator can change by editing a script file, as covered by the scripted- and refreshable-bean cards earlier in this guide.
- You're maintaining legacy XML configuration that already declares scripted beans this way and need to recognize `<lang:groovy>`/`<lang:bsh>` as the entry point into that mechanism.
- You're auditing a codebase's full set of custom XML namespaces and need to know which elements belong to which schema — `lang` is specifically the scripting-language one, distinct from `util`'s collection helpers or `context`'s annotation activation.

## 3. Core concept

```
 lang namespace elements, one per supported scripting engine:
    <lang:groovy .../>   -- Groovy scripts, compiled via GroovyScriptFactory
    <lang:bsh .../>       -- BeanShell scripts, compiled via BshScriptFactory
    (historically <lang:jruby .../> for JRuby, since removed)

 Each element, at parse time, expands to:
        |
        v
 a ScriptFactoryPostProcessor-managed bean definition
        |
        v
 pointing at a script-source (classpath:, file:, or inline)
        |
        v
 optionally wrapped in a refreshable AOP proxy if refresh-check-delay is set
```

Every `lang` element ultimately produces a normal Spring bean — callers never know or care that the implementation was compiled from a script rather than `javac`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="lang namespace elements point at a script source and produce a normal Spring bean via the appropriate ScriptFactory">
  <rect x="10" y="20" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;lang:groovy&gt;</text>
  <text x="95" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">script-source="classpath:..."</text>

  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">GroovyScriptFactory</text>
  <text x="330" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">compiles the script</text>

  <rect x="480" y="20" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">bean "pricingRule"</text>
  <text x="555" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">normal bean to callers</text>

  <line x1="180" y1="45" x2="235" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="45" x2="475" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each `lang` element names a scripting engine's factory; the resulting bean looks like any other to the rest of the application.

## 5. Runnable example

The scenario: a `ValidationRule` bean, first defined directly (Level 1) as a Groovy script via `<lang:groovy>` with inline script text, then (Level 2) loaded from an actual `.groovy` file on disk, then (Level 3) combined with `<lang:bsh>` to show two different scripting engines coexisting under the same `lang` namespace in one context.

### Level 1 — Basic

Declare a `<lang:groovy>` bean with an inline `<lang:inline-script>` body and confirm it behaves as a normal bean implementing a Java interface.

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import java.nio.charset.StandardCharsets;

public class LangSchemaLevel1 {

    public interface ValidationRule {
        boolean isValid(String input);
    }

    public static void main(String[] args) {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:lang="http://www.springframework.org/schema/lang"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/lang
                       https://www.springframework.org/schema/lang/spring-lang.xsd">

                <lang:groovy id="validationRule" script-interfaces="LangSchemaLevel1$ValidationRule">
                    <lang:inline-script>
                        class NonBlankRule implements LangSchemaLevel1.ValidationRule {
                            boolean isValid(String input) { input != null &amp;&amp; !input.trim().isEmpty() }
                        }
                    </lang:inline-script>
                </lang:groovy>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        ValidationRule rule = ctx.getBean(ValidationRule.class);
        boolean validResult = rule.isValid("hello");
        boolean blankResult = rule.isValid("   ");
        System.out.println("isValid('hello') = " + validResult + ", isValid('   ') = " + blankResult);

        if (!validResult || blankResult)
            throw new AssertionError("Groovy-scripted rule did not behave as expected");
        System.out.println("lang:groovy inline script produced a working ValidationRule bean -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-context`, Groovy, and Spring's scripting support on the classpath, then `java LangSchemaLevel1.java` on JDK 17+.

`script-interfaces` tells Spring which Java interface the compiled script implements, which is what lets `ctx.getBean(ValidationRule.class)` retrieve it by that interface rather than by a Groovy-specific type. `<lang:inline-script>` embeds the Groovy source directly in the XML — convenient for short scripts, though `script-source="classpath:..."` (used in Level 2) is more common for anything beyond a few lines.

### Level 2 — Intermediate

Load the same rule from a real `.groovy` file via `script-source`, matching how `lang` beans are used in practice — script logic kept in its own file, separate from XML wiring.

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class LangSchemaLevel2 {

    public interface ValidationRule {
        boolean isValid(String input);
    }

    public static void main(String[] args) throws IOException {
        File scriptFile = File.createTempFile("NonBlankRule", ".groovy");
        try (FileWriter w = new FileWriter(scriptFile, StandardCharsets.UTF_8)) {
            w.write("""
                class NonBlankRule implements LangSchemaLevel2.ValidationRule {
                    boolean isValid(String input) { input != null && !input.trim().isEmpty() }
                }
                """);
        }

        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:lang="http://www.springframework.org/schema/lang"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/lang
                       https://www.springframework.org/schema/lang/spring-lang.xsd">

                <lang:groovy id="validationRule"
                    script-source="file:%s"
                    script-interfaces="LangSchemaLevel2$ValidationRule"/>
            </beans>
            """.formatted(scriptFile.getAbsolutePath().replace("\\", "/"));

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        ValidationRule rule = ctx.getBean(ValidationRule.class);
        System.out.println("isValid('data') = " + rule.isValid("data"));
        if (!rule.isValid("data"))
            throw new AssertionError("Expected 'data' to be valid");
        System.out.println("lang:groovy loaded from a real file on disk -- PASS");
        ctx.close();
        scriptFile.delete();
    }
}
```

How to run: same classpath as Level 1, `java LangSchemaLevel2.java`.

`script-source="file:%s"` points at a real path on disk rather than embedding the script inline — this is also the form that supports `refresh-check-delay`, covered in the earlier refreshable-beans card, since a live-editable script only makes sense against a real file that can actually change between polls.

### Level 3 — Advanced

Combine two different scripting engines — `<lang:groovy>` and `<lang:bsh>` — in the same context, each implementing the same interface, showing that `lang` beans are interchangeable from the consuming code's point of view regardless of which engine produced them.

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import java.nio.charset.StandardCharsets;
import java.util.Map;

public class LangSchemaLevel3 {

    public interface ValidationRule {
        boolean isValid(String input);
    }

    public static void main(String[] args) {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:lang="http://www.springframework.org/schema/lang"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/lang
                       https://www.springframework.org/schema/lang/spring-lang.xsd">

                <lang:groovy id="nonBlankRule" script-interfaces="LangSchemaLevel3$ValidationRule">
                    <lang:inline-script>
                        class NonBlankRule implements LangSchemaLevel3.ValidationRule {
                            boolean isValid(String input) { input != null &amp;&amp; !input.trim().isEmpty() }
                        }
                    </lang:inline-script>
                </lang:groovy>

                <lang:bsh id="maxLengthRule" script-interfaces="LangSchemaLevel3$ValidationRule">
                    <lang:inline-script>
                        boolean isValid(String input) {
                            return input != null &amp;&amp; input.length() &lt;= 20;
                        }
                    </lang:inline-script>
                </lang:bsh>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        Map<String, ValidationRule> rules = ctx.getBeansOfType(ValidationRule.class);
        System.out.println("scripted rule beans = " + rules.keySet());

        ValidationRule groovyRule = ctx.getBean("nonBlankRule", ValidationRule.class);
        ValidationRule bshRule = ctx.getBean("maxLengthRule", ValidationRule.class);

        boolean groovyResult = groovyRule.isValid("hello");
        boolean bshResult = bshRule.isValid("a-fairly-short-string");

        System.out.println("groovyRule.isValid('hello') = " + groovyResult);
        System.out.println("bshRule.isValid('a-fairly-short-string') = " + bshResult);

        if (rules.size() != 2) throw new AssertionError("Expected exactly two scripted beans");
        if (!groovyResult) throw new AssertionError("Groovy rule should accept 'hello'");
        if (bshResult) throw new AssertionError("BeanShell rule should reject a string over 20 chars");

        System.out.println("lang:groovy and lang:bsh beans coexist under the same interface -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, plus BeanShell (`bsh`) on the classpath. Run `java LangSchemaLevel3.java`.

`ctx.getBeansOfType(ValidationRule.class)` returns both beans keyed by id, regardless of which scripting engine produced them — from the consuming code's perspective, a Groovy-scripted bean and a BeanShell-scripted bean are simply two beans implementing the same interface. This is the same polymorphism any two Java classes implementing an interface would exhibit; the scripting engine is an implementation detail invisible past the `lang:*` declaration.

## 6. Walkthrough

Trace Level 3's context construction and bean lookup.

1. **Context refresh begins parsing**: the `lang` namespace handler processes `<lang:groovy id="nonBlankRule">` first, registering a `ScriptFactoryPostProcessor`-managed bean definition pointed at `GroovyScriptFactory` with the inline script text as its source.
2. **Second element parsed**: `<lang:bsh id="maxLengthRule">` similarly registers a bean definition, this time pointed at `BshScriptFactory`.
3. **Bean instantiation**: for `nonBlankRule`, `GroovyScriptFactory` compiles the inline Groovy source into a class implementing `ValidationRule` and instantiates it; for `maxLengthRule`, `BshScriptFactory` does the same with BeanShell's interpreter, producing a dynamic proxy that implements `ValidationRule` by dispatching method calls into the interpreted script.
4. **`main` retrieves both beans**: first by type (`getBeansOfType`, confirming both are registered under the common interface), then individually by id.
5. **`groovyRule.isValid("hello")`** dispatches into the compiled Groovy class's `isValid` method: `"hello" != null && !"hello".trim().isEmpty()` evaluates `true`.
6. **`bshRule.isValid("a-fairly-short-string")`** dispatches into the BeanShell interpreter running the script's `isValid` method: the string is 21 characters, so `input.length() <= 20` evaluates `false`.
7. **Assertions**: the program checks exactly two beans were found, the Groovy result is `true`, and the BeanShell result is `false`, printing `PASS` only if every check holds.

```
 <lang:groovy id="nonBlankRule">   --GroovyScriptFactory-->  bean implementing ValidationRule
 <lang:bsh id="maxLengthRule">     --BshScriptFactory---->  bean implementing ValidationRule
                                                                       |
                                        both retrievable via getBeansOfType(ValidationRule.class)
```

## 7. Gotchas & takeaways

> **Gotcha:** `script-interfaces` is required whenever calling code needs to reference the scripted bean by a specific Java interface type (as both examples here do) — without it, the bean is still created, but callers can only obtain it by bean name and treat it as `Object`, losing compile-time type safety entirely.

- `lang` is purely the *declaration* namespace for scripted beans; the mechanics of scripting and live-reload were already covered by this guide's dynamic-language-beans and refreshable-beans cards — this card is about recognizing the schema, not re-explaining the mechanism.
- `<lang:inline-script>` is convenient for short, demonstrative scripts; `script-source="file:..."` or `"classpath:..."` is the practical choice for anything maintained as a real source file.
- Different scripting engines (`groovy`, `bsh`, historically `jruby`) can coexist in the same `ApplicationContext`, each producing beans indistinguishable from one another once instantiated, as long as they share a common Java interface.
- `refresh-check-delay` (covered in depth earlier) is available on any `lang` element, not just `<lang:groovy>` — the live-reload mechanism is engine-agnostic.
