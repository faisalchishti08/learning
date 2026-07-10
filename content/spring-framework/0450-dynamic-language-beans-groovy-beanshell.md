---
card: spring-framework
gi: 450
slug: dynamic-language-beans-groovy-beanshell
title: "Dynamic language beans (Groovy, BeanShell)"
---

## 1. What it is

Spring's dynamic-language bean support (`org.springframework.scripting`) lets a bean's *implementation* be a script file (a `.groovy` file, historically also BeanShell `.bsh` files, though BeanShell support has since been removed from modern Spring versions) rather than a compiled Java or Kotlin class — Spring compiles/interprets the script at application startup and wraps it as an ordinary Spring bean, indistinguishable from any other bean to the rest of the application.

```xml
<lang:groovy id="messageService"
        script-source="classpath:MessageService.groovy"
        refresh-check-delay="5000"/>
```

## 2. Why & when

Most Spring beans are ordinary compiled classes — but occasionally, a specific piece of logic (a business rule, a pricing formula, a validation policy) genuinely benefits from being editable and reloadable *without a full application redeploy*: think a rules engine where business analysts (not developers) tweak a formula, or a plugin-style extension point where behavior needs to change without a build/deploy cycle. Dynamic-language beans exist for exactly this niche — a script file, written in Groovy, implementing a Java interface, loaded and wired into the Spring context like any other bean, with the option (covered in depth in the next card) to be automatically reloaded when the script file changes on disk.

This is a genuinely narrow use case, not a general alternative to writing regular Spring beans:

- Reach for it when a specific, isolated piece of logic needs to be editable at runtime by someone who isn't going through a normal build/deploy pipeline — a scripted pricing rule, a scripted validation policy, a scripted integration adapter for a rapidly-changing third-party API contract.
- It is not appropriate for core application logic, security-sensitive code, or anything where the operational risk of unreviewed runtime script changes outweighs the flexibility benefit.
- BeanShell support has been removed from current Spring Framework versions (it's mentioned here for historical/legacy-codebase context only) — Groovy is the dynamic-language option actually available in modern Spring.

## 3. Core concept

```
 MessageService.groovy   (a script file, NOT a compiled .java/.kt class)
        |
        | implements a Java interface, either explicitly or via duck-typing
        v
 GroovyScriptFactory  (Spring's script-to-bean bridge)
        |
        | compiles/interprets the script at context startup
        v
 ordinary Spring bean, wired via @Autowired / constructor injection
 exactly like any compiled-class bean -- callers never know the
 difference between a scripted bean and a compiled one
```

The defining trait is that from any *calling* code's perspective, a dynamic-language bean is completely indistinguishable from a normal bean — the "script" nature is entirely a configuration-time and (for refreshable beans, next card) an ongoing-monitoring concern, invisible to consumers.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Groovy script file is compiled into an ordinary Spring bean, indistinguishable from compiled-class beans to callers">
  <rect x="10" y="20" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MessageService.groovy</text>
  <text x="95" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a script file</text>

  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">GroovyScriptFactory</text>

  <rect x="480" y="20" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Ordinary bean</text>
  <text x="555" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">callers see no difference</text>

  <line x1="180" y1="45" x2="235" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="45" x2="475" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A script file goes in; an ordinary, indistinguishable Spring bean comes out.

## 5. Runnable example

Since `<lang:groovy>` XML configuration needs a real script *file* on the classpath (awkward to demonstrate as a single self-contained runnable snippet), this example uses `GroovyScriptFactory` and `ScriptSource` programmatically, with the script content as an inline string — the same underlying mechanism XML-based `<lang:groovy>` configuration uses, just constructed in Kotlin/Groovy code directly rather than loaded from a separate file, keeping the example fully self-contained and runnable.

### Level 1 — Basic

Compile an inline Groovy script into a Spring bean implementing a plain Java-style interface, and call it exactly like any other bean.

```groovy
import org.springframework.context.support.GenericApplicationContext
import org.springframework.scripting.support.StaticScriptSource
import org.springframework.scripting.groovy.GroovyScriptFactory
import org.springframework.beans.factory.support.RootBeanDefinition

interface MessageService {
    String getMessage(String name)
}

def scriptSource = new StaticScriptSource('''
class GroovyMessageService implements MessageService {
    String getMessage(String name) {
        return "Hello from Groovy, ${name}!"
    }
}
''')

def context = new GenericApplicationContext()

// This mirrors what <lang:groovy script-source="..."/> does underneath, expressed programmatically.
def beanDefinition = new RootBeanDefinition(GroovyScriptFactory)
beanDefinition.constructorArgumentValues.addGenericArgumentValue('inline-script')
context.registerBeanDefinition('scriptFactory', beanDefinition)

def factory = new GroovyScriptFactory('inline-script')
def messageService = factory.getScriptedObject(scriptSource, MessageService) as MessageService

def result = messageService.getMessage('Ada')
println result
assert result == 'Hello from Groovy, Ada!'
println 'Dynamic Groovy-scripted bean, called like an ordinary bean -- PASS'
```

How to run: add `spring-context`, Groovy (`org.codehaus.groovy:groovy`), and the Groovy scripting support classes (bundled within `spring-context-support` or `spring-context` depending on version) to the classpath, then run with `groovy AppConfig.groovy`.

`StaticScriptSource` supplies the Groovy source as an in-memory string, standing in for what would normally be loaded from a `.groovy` file via `script-source="classpath:MessageService.groovy"` in real XML-based configuration. `GroovyScriptFactory.getScriptedObject(scriptSource, MessageService)` compiles that source at this call and returns an object implementing `MessageService` — the caller's code (`messageService.getMessage('Ada')`) has no idea the implementation came from a runtime-compiled script rather than an ordinary `.class` file.

### Level 2 — Intermediate

Wire a Groovy-scripted bean as a genuine dependency of another, ordinary (compiled) Spring bean — showing dynamic-language beans participate in normal dependency injection, not as an isolated curiosity.

```groovy
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.context.annotation.AnnotationConfigApplicationContext
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.scripting.support.StaticScriptSource
import org.springframework.scripting.groovy.GroovyScriptFactory

interface PricingRule {
    double apply(double basePrice)
}

class OrderService {
    private final PricingRule pricingRule
    OrderService(PricingRule pricingRule) { this.pricingRule = pricingRule }
    double priceFor(double basePrice) { pricingRule.apply(basePrice) }
}

@Configuration
class AppConfig {
    @Bean
    PricingRule pricingRule() {
        def scriptSource = new StaticScriptSource('''
            class SeasonalDiscountRule implements PricingRule {
                double apply(double basePrice) {
                    return basePrice * 0.85  // a 15% seasonal discount, expressed as a "script" a
                                              // business analyst could plausibly edit without a full deploy
                }
            }
        ''')
        def factory = new GroovyScriptFactory('seasonal-discount')
        return factory.getScriptedObject(scriptSource, PricingRule) as PricingRule
    }

    @Bean
    OrderService orderService(PricingRule pricingRule) {
        new OrderService(pricingRule)
    }
}

def context = new AnnotationConfigApplicationContext(AppConfig)
def orderService = context.getBean(OrderService)

def result = orderService.priceFor(100.0)
println "Priced: ${result}"
assert Math.abs(result - 85.0) < 0.01
println 'Groovy-scripted bean wired as a normal dependency of a compiled Spring bean -- PASS'

context.close()
```

How to run: same dependencies as Level 1, then `groovy AppConfig.groovy`.

`OrderService` is an ordinary compiled class, and `@Configuration`'s `@Bean` method for `pricingRule()` happens to build its return value from a Groovy script rather than `new SomeCompiledPricingRule()` — but from `OrderService`'s perspective (and from Spring's dependency-injection machinery's perspective), this is exactly the same as wiring any other `PricingRule` implementation. The point this level makes: dynamic-language beans aren't a separate, parallel configuration universe — they interoperate seamlessly with ordinary compiled beans in the same context, same dependency graph.

### Level 3 — Advanced

A scripted bean implementing a more realistic multi-method interface, plus error handling for a script that fails to compile — demonstrating what happens when the "editable at runtime" flexibility this feature offers goes wrong, and how that failure surfaces.

```groovy
import org.springframework.scripting.groovy.GroovyScriptFactory
import org.springframework.scripting.support.StaticScriptSource
import org.springframework.scripting.ScriptCompilationException

interface ValidationPolicy {
    boolean isValid(String input)
    String describe()
}

// A working, multi-method scripted policy.
def workingScript = new StaticScriptSource('''
class LengthValidationPolicy implements ValidationPolicy {
    boolean isValid(String input) {
        return input != null && input.length() >= 3 && input.length() <= 50
    }
    String describe() {
        return "Requires length between 3 and 50 characters"
    }
}
''')

def factory = new GroovyScriptFactory('length-validation')
def policy = factory.getScriptedObject(workingScript, ValidationPolicy) as ValidationPolicy

println policy.describe()
assert policy.isValid('Ada Lovelace')
assert !policy.isValid('ab')
println 'Working multi-method scripted policy -- PASS'

// A DELIBERATELY BROKEN script, to demonstrate compilation-failure handling --
// this is the realistic downside of runtime-editable business logic: a bad edit
// doesn't fail at build time, it fails when Spring tries to compile/load the script.
def brokenScript = new StaticScriptSource('''
class BrokenPolicy implements ValidationPolicy {
    boolean isValid(String input) {
        return input.length( >= 3   // deliberate syntax error
    }
}
''')

try {
    def brokenFactory = new GroovyScriptFactory('broken-validation')
    brokenFactory.getScriptedObject(brokenScript, ValidationPolicy)
    assert false : 'Expected a compilation failure for the broken script'
} catch (ScriptCompilationException e) {
    println "Correctly caught script compilation failure: ${e.class.simpleName}"
    println 'Broken script correctly failed to load rather than silently producing a bad bean -- PASS'
}
```

How to run: same dependencies as Level 1, then `groovy AppConfig.groovy`.

The working `LengthValidationPolicy` script implements both `isValid` and `describe`, showing a scripted bean isn't limited to trivial single-method interfaces. The deliberately broken second script has a genuine Groovy syntax error; `GroovyScriptFactory.getScriptedObject(...)` throws `ScriptCompilationException` when it tries to compile that malformed source — this is Spring's fail-fast behavior for a bad script, surfacing the problem immediately at bean-creation time (or, for a refreshable bean covered in the next card, at the moment a refresh check detects and attempts to reload the changed file) rather than allowing a half-broken bean into the application context.

## 6. Walkthrough

Trace the broken-script scenario in Level 3:

1. **Script source constructed.** `brokenScript` holds a string of Groovy source with a genuine syntax error — a missing closing parenthesis on `input.length(`.
2. **Factory attempts compilation.** `brokenFactory.getScriptedObject(brokenScript, ValidationPolicy)` asks `GroovyScriptFactory` to compile this source and produce an object implementing `ValidationPolicy`.
3. **Groovy's compiler rejects the source.** Internally, `GroovyScriptFactory` delegates to the actual Groovy compiler (via Groovy's `GroovyClassLoader`), which parses the source and encounters the syntax error — the compiler itself raises a Groovy-level compilation exception.
4. **Spring wraps the failure.** `GroovyScriptFactory` catches that underlying Groovy compilation error and re-throws it wrapped as a `ScriptCompilationException` — a Spring-specific exception type, giving calling code (and, in a real application, Spring's own bean-creation error reporting) a consistent exception type to catch regardless of which dynamic-language technology produced the failure.
5. **Caught and handled.** The `try/catch` block in the example code catches `ScriptCompilationException`, printing a confirmation message rather than letting the exception propagate uncaught and crash the whole script — demonstrating the *type* of failure a broken dynamic-language bean produces, so real application code (or Spring's own context-refresh error handling) knows what to expect and can respond appropriately (log clearly, alert an operator, fall back to a previous known-good script version).

```
brokenFactory.getScriptedObject(brokenScript, ValidationPolicy)
   -> GroovyScriptFactory delegates to Groovy's compiler
   -> Groovy compiler encounters syntax error -> raises a compilation error
   -> GroovyScriptFactory wraps it -> throws ScriptCompilationException
   -> caught by the example's try/catch -> confirmation printed
```

## 7. Gotchas & takeaways

> Gotcha: because a dynamic-language bean's source can genuinely fail to compile — unlike a normal Java/Kotlin class, which is guaranteed to compile successfully before the application even builds, since the build itself would fail otherwise — a Spring application using scripted beans has a *new* class of runtime failure mode that doesn't exist for ordinary compiled beans: a syntactically broken script loaded (or reloaded) at runtime. This is precisely why dynamic-language beans should be reserved for genuinely isolated, low-blast-radius pieces of logic, with the source of truth for those scripts under some form of review or validation process before deployment, rather than treated as a casual alternative to normal Spring bean development.

- Dynamic-language beans let a bean's implementation be a script (Groovy in modern Spring; BeanShell historically, now removed) rather than a compiled class, compiled/interpreted at Spring context startup and wrapped as an ordinary, indistinguishable Spring bean.
- This is a narrow-use-case feature — appropriate for genuinely isolated, runtime-editable logic like scripted business rules, not as a general substitute for writing regular Spring beans.
- Scripted beans participate in normal dependency injection exactly like compiled-class beans — they can be injected into (and can themselves depend on) ordinary beans with no special handling required at the injection points.
- A broken script fails at compile/load time with a `ScriptCompilationException`, a genuinely new failure mode compiled Java/Kotlin beans don't have — plan for this explicitly (validation before deployment, clear error handling) if you adopt this feature for anything beyond low-risk, easily-reverted logic.
