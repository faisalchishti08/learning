---
card: spring-framework
gi: 451
slug: refreshable-beans
title: "Refreshable beans"
---

## 1. What it is

Refreshable beans are dynamic-language beans (from the previous card) configured with a `refresh-check-delay` — a polling interval at which Spring checks whether the underlying script file's last-modified timestamp has changed, and if so, recompiles the script and swaps the bean's implementation live, without restarting the application or its `ApplicationContext`. Callers holding a reference to the bean continue calling the same object; internally, Spring routes those calls through to whichever version of the compiled script is currently active.

```xml
<lang:groovy id="pricingRule"
        script-source="classpath:PricingRule.groovy"
        refresh-check-delay="5000"/>  <!-- checks for changes every 5 seconds -->
```

## 2. Why & when

The previous card established that dynamic-language beans exist for genuinely isolated, runtime-editable logic — refreshable beans are what makes that "runtime-editable" property actually useful in practice: without a refresh mechanism, changing a script's `.groovy` file would still require restarting the application (or at least reloading that part of the context) to pick up the change, largely defeating the point of using a script instead of a compiled class in the first place. `refresh-check-delay` closes that gap, letting a running application periodically notice a changed script file and swap in the new behavior live.

Reach for refreshable beans specifically when:

- The whole value proposition of a scripted bean (from the previous card) is editability *without* a redeploy — refreshable beans deliver that, letting an operator or business analyst edit the script file directly on a running server and see the change take effect within one polling interval.
- You're comfortable with the operational trade-off: a script change takes effect live, in a running production process, without going through your normal deployment pipeline's review/rollback safety nets — appropriate only for low-risk, easily-reverted logic, exactly as the previous card's gotcha emphasized.

## 3. Core concept

```
 PricingRule.groovy on disk, lastModified = T0
        |
        v
 RefreshableScriptTargetSource wraps the bean, tracks lastModified
        |
        v
 Proxy object returned to callers -- looks like a normal PricingRule to them
        |
        | every refresh-check-delay milliseconds:
        v
 checks: has the FILE's lastModified changed since T0?
    /                                    \
  no                                     yes (edited to T1)
   |                                      |
   v                                      v
 keep using the                     recompile the script
 currently-compiled                 swap the proxy's target
 target object                      to the NEWLY compiled object
                                     (subsequent calls hit the new version)
```

Callers hold a reference to a proxy, not the underlying scripted object directly — the proxy is what makes live-swapping possible without callers needing to re-fetch the bean or be notified of the change themselves.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A refreshable bean proxy periodically checks the script file and swaps its target when the file changes">
  <rect x="10" y="20" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller code</text>

  <rect x="230" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Refreshable proxy</text>
  <text x="320" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">stable reference</text>

  <rect x="470" y="20" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Compiled target</text>
  <text x="545" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">swappable underneath</text>

  <rect x="230" y="110" width="180" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Script file on disk</text>
  <text x="320" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">polled every N ms</text>

  <line x1="160" y1="43" x2="225" y2="43" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="410" y1="43" x2="465" y2="43" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="320" y1="108" x2="320" y2="70" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The caller's reference never changes; what's behind it can, on the next poll after a file edit.

## 5. Runnable example

Real `refresh-check-delay` behavior monitors an actual file on disk — this example writes a genuine temporary `.groovy` file, uses it with `ResourceScriptSource` (the file-backed counterpart to the previous card's `StaticScriptSource`), edits the file mid-run, and observes the refresh actually happening, making the whole mechanism concretely runnable and observable in one script.

### Level 1 — Basic

Write a real `.groovy` file, load it as a scripted bean, then edit the file and manually check `ResourceScriptSource.isModified()` to see the change-detection mechanism directly, before layering the automatic polling behavior on top in later levels.

```groovy
import org.springframework.scripting.groovy.GroovyScriptFactory
import org.springframework.scripting.support.ResourceScriptSource
import org.springframework.core.io.FileSystemResource

interface PricingRule {
    double apply(double basePrice)
}

def scriptFile = File.createTempFile('PricingRule', '.groovy')
scriptFile.text = '''
class DiscountRule implements PricingRule {
    double apply(double basePrice) { basePrice * 0.9 }  // 10% off
}
'''

def scriptSource = new ResourceScriptSource(new FileSystemResource(scriptFile))
def factory = new GroovyScriptFactory('pricing-rule')

def rule = factory.getScriptedObject(scriptSource, PricingRule) as PricingRule
println "Initial price for 100.0: ${rule.apply(100.0)}"
assert Math.abs(rule.apply(100.0) - 90.0) < 0.01

println "Was modified since last check? ${scriptSource.isModified()}"
assert !scriptSource.isModified() : "Should NOT report modified before any edit and after a check"

// Edit the file on disk, simulating an operator changing the pricing rule live.
Thread.sleep(1100) // ensure the filesystem timestamp resolution registers a real change
scriptFile.text = '''
class DiscountRule implements PricingRule {
    double apply(double basePrice) { basePrice * 0.75 }  // now 25% off
}
'''

println "Was modified after editing the file? ${scriptSource.isModified()}"
assert scriptSource.isModified() : "Should report modified after the file was actually edited"

println 'Change-detection mechanism (isModified) correctly observed the file edit -- PASS'
scriptFile.delete()
```

How to run: add `spring-context`, Groovy, and Spring's scripting support to the classpath, then run with `groovy AppConfig.groovy`.

`ResourceScriptSource` wraps a real file resource and tracks its last-modified timestamp; `isModified()` compares the file's *current* last-modified time against what it was the last time `isModified()` (or an actual script retrieval) was called — this is the underlying primitive `refresh-check-delay`'s automatic polling builds on top of. `Thread.sleep(1100)` before the edit exists because many filesystems have only second-level timestamp resolution — without a real time gap, a rapid edit-then-check could produce an identical timestamp and be missed.

### Level 2 — Intermediate

Wrap the scripted bean in Spring's actual `RefreshableScriptTargetSource`/AOP proxy machinery — the real mechanism `refresh-check-delay` uses in production, rather than manually checking `isModified()` — and observe the proxy automatically serving the old behavior until a refresh check occurs, then the new behavior afterward.

```groovy
import org.springframework.aop.framework.ProxyFactory
import org.springframework.aop.target.dynamic.RefreshableTargetSource
import org.springframework.scripting.groovy.GroovyScriptFactory
import org.springframework.scripting.support.ResourceScriptSource
import org.springframework.scripting.support.ScriptFactoryPostProcessor
import org.springframework.core.io.FileSystemResource
import org.springframework.context.support.GenericApplicationContext
import org.springframework.beans.factory.support.RootBeanDefinition
import org.springframework.beans.MutablePropertyValues

interface PricingRule {
    double apply(double basePrice)
}

def scriptFile = File.createTempFile('PricingRule', '.groovy')
scriptFile.text = '''
class DiscountRule implements PricingRule {
    double apply(double basePrice) { basePrice * 0.9 }  // 10% off
}
'''

def context = new GenericApplicationContext()

// This mirrors what <lang:groovy refresh-check-delay="..."/> configures underneath --
// ScriptFactoryPostProcessor is the machinery that builds a refreshable AOP proxy
// around the scripted target, checking the delay on each proxied method invocation.
def bd = new RootBeanDefinition(GroovyScriptFactory)
bd.setBeanClassName('org.springframework.scripting.groovy.GroovyScriptFactory')
bd.getConstructorArgumentValues().addGenericArgumentValue('pricingRuleScriptFactory')
def pv = new MutablePropertyValues()
context.registerBeanDefinition('scriptFactoryPostProcessor', new RootBeanDefinition(ScriptFactoryPostProcessor))
context.registerBeanDefinition('pricingRule', bd)

// Simplification for a single runnable file: directly using RefreshableTargetSource,
// the same class ScriptFactoryPostProcessor uses internally for refresh-check-delay support.
def scriptSource = new ResourceScriptSource(new FileSystemResource(scriptFile))
def factory = new GroovyScriptFactory('pricing-rule')

class ScriptRefreshableTargetSource extends RefreshableTargetSource {
    GroovyScriptFactory factory
    def scriptSource
    Object freshTargetObject() { factory.getScriptedObject(scriptSource, PricingRule) }
}

def targetSource = new ScriptRefreshableTargetSource(factory: factory, scriptSource: scriptSource)
targetSource.targetClass = PricingRule
targetSource.refreshCheckDelay = 500 // check for changes at most every 500ms

def proxyFactory = new ProxyFactory()
proxyFactory.setTargetSource(targetSource)
proxyFactory.setInterfaces([PricingRule] as Class[])
def rule = proxyFactory.getProxy() as PricingRule

println "Before edit: ${rule.apply(100.0)}"
assert Math.abs(rule.apply(100.0) - 90.0) < 0.01

Thread.sleep(1100)
scriptFile.text = '''
class DiscountRule implements PricingRule {
    double apply(double basePrice) { basePrice * 0.75 }  // now 25% off
}
'''

Thread.sleep(700) // longer than refreshCheckDelay -- give it a chance to notice and reload

println "After edit + refresh window: ${rule.apply(100.0)}"
assert Math.abs(rule.apply(100.0) - 75.0) < 0.01
println 'RefreshableTargetSource-backed proxy live-swapped its target after the file edit -- PASS'

scriptFile.delete()
```

How to run: same dependencies as Level 1, then `groovy AppConfig.groovy`.

`RefreshableTargetSource` is the real AOP `TargetSource` implementation `refresh-check-delay` configures in production `<lang:groovy>` beans — its `freshTargetObject()` method (overridden here) is called whenever a refresh check determines the script has changed, producing a newly-compiled instance to become the proxy's new target. `proxyFactory.getProxy()` returns a genuine dynamic proxy — `rule` in this code is *not* the scripted `DiscountRule` instance itself, it's a proxy delegating to whichever `DiscountRule` instance is currently "fresh," which is exactly the indirection that makes live-swapping transparent to calling code.

### Level 3 — Advanced

A refresh check racing with the script being edited mid-write (a realistic operational hazard: an operator's editor might write a file in multiple steps, or a deploy script might briefly leave a syntactically incomplete file) — demonstrating that a refresh failure doesn't take down the whole application, and the proxy continues serving the last-known-good target until a subsequent, successful refresh occurs.

```groovy
import org.springframework.aop.framework.ProxyFactory
import org.springframework.aop.target.dynamic.RefreshableTargetSource
import org.springframework.scripting.groovy.GroovyScriptFactory
import org.springframework.scripting.support.ResourceScriptSource
import org.springframework.core.io.FileSystemResource

interface PricingRule {
    double apply(double basePrice)
}

def scriptFile = File.createTempFile('PricingRule', '.groovy')
scriptFile.text = '''
class DiscountRule implements PricingRule {
    double apply(double basePrice) { basePrice * 0.9 }
}
'''

def scriptSource = new ResourceScriptSource(new FileSystemResource(scriptFile))
def factory = new GroovyScriptFactory('pricing-rule')

class ResilientRefreshableTargetSource extends RefreshableTargetSource {
    GroovyScriptFactory factory
    def scriptSource
    int refreshFailures = 0

    Object freshTargetObject() {
        try {
            return factory.getScriptedObject(scriptSource, PricingRule)
        } catch (Exception e) {
            refreshFailures++
            println "  Refresh attempt failed (${e.class.simpleName}) -- KEEPING the last-known-good target"
            throw e // RefreshableTargetSource itself catches this and retains the old target
        }
    }
}

def targetSource = new ResilientRefreshableTargetSource(factory: factory, scriptSource: scriptSource)
targetSource.targetClass = PricingRule
targetSource.refreshCheckDelay = 300

def proxyFactory = new ProxyFactory()
proxyFactory.setTargetSource(targetSource)
proxyFactory.setInterfaces([PricingRule] as Class[])
def rule = proxyFactory.getProxy() as PricingRule

println "Initial (working script): ${rule.apply(100.0)}"
assert Math.abs(rule.apply(100.0) - 90.0) < 0.01

// Simulate a BROKEN mid-write: the file is now syntactically invalid.
Thread.sleep(1100)
scriptFile.text = 'class DiscountRule implements PricingRule { double apply(double basePrice) { basePrice * 0.75  // truncated, invalid'
Thread.sleep(500) // give it time to attempt (and fail) a refresh

println "During broken script window: ${rule.apply(100.0)}"
assert Math.abs(rule.apply(100.0) - 90.0) < 0.01 : "Expected the OLD, still-working target to remain in use"
println 'Broken script did NOT crash the application -- last-known-good target kept serving requests'

// Now "finish the edit" -- fix the file into a valid script.
Thread.sleep(1100)
scriptFile.text = '''
class DiscountRule implements PricingRule {
    double apply(double basePrice) { basePrice * 0.75 }
}
'''
Thread.sleep(500)

println "After the fix: ${rule.apply(100.0)}"
assert Math.abs(rule.apply(100.0) - 75.0) < 0.01
println "Total refresh failures encountered along the way: ${targetSource.refreshFailures}"
println 'Recovered automatically once the script became valid again -- PASS'

scriptFile.delete()
```

How to run: same dependencies as Level 1, then `groovy AppConfig.groovy`.

`RefreshableTargetSource`'s built-in refresh logic catches exceptions thrown from `freshTargetObject()` and, on failure, simply keeps the *previous* target object rather than propagating the exception up through the proxy to calling code — the `try/catch` inside `freshTargetObject()` here exists only to log the failure count for demonstration purposes, since the base class already handles the resilience behavior. This is the concrete safety net that makes refreshable beans operationally viable despite the "runtime-editable" risk the previous card flagged: a bad or incomplete edit degrades to "still running the old version" rather than crashing the application or serving a half-broken bean.

## 6. Walkthrough

Trace the broken-script window in Level 3:

1. **Working state established.** The proxy's current target is a compiled `DiscountRule` applying a 10% discount (`basePrice * 0.9`); `rule.apply(100.0)` returns `90.0`, confirmed by the first assertion.
2. **File corrupted mid-edit.** `scriptFile.text = '...truncated, invalid'` writes a syntactically broken Groovy source to the file — simulating an operator's editor mid-save, or a deployment script that hasn't finished writing the new version yet.
3. **A refresh check occurs.** Because `refreshCheckDelay = 300`, within roughly 300ms of the file's last-modified timestamp changing, the next call to `rule.apply(...)` (proxied through `RefreshableTargetSource`) triggers a refresh check, detects the file has changed, and calls `freshTargetObject()` to attempt recompilation.
4. **Compilation fails.** `factory.getScriptedObject(scriptSource, PricingRule)` tries to compile the truncated, invalid source and throws a compilation exception — the same `ScriptCompilationException` category covered in the previous card.
5. **`RefreshableTargetSource` retains the old target.** The base class's refresh logic catches this failure internally and does *not* replace the currently-active target — the proxy continues delegating to the still-valid, previously-compiled `DiscountRule` instance from step 1.
6. **Calls during the broken window still succeed.** `rule.apply(100.0)` during this period still returns `90.0` — the caller experiences zero disruption, with no indication anything went wrong except (in a real application) whatever logging the refresh failure produced.
7. **File fixed.** `scriptFile.text = '...valid 25% discount script...'` writes a syntactically correct replacement.
8. **Next refresh check succeeds.** After the next `refreshCheckDelay` window elapses and a call triggers another check, the file's timestamp has changed *again* (to this latest, valid edit), `freshTargetObject()` successfully compiles the new script, and the proxy's target is swapped to this newly-compiled `DiscountRule` applying a 25% discount.
9. **Subsequent calls reflect the fix.** `rule.apply(100.0)` now returns `75.0`, confirming the proxy picked up the corrected script once it became valid, having transparently ridden out the broken intermediate state without any caller-visible failure.

```
t=0:    script valid (10% off)         -> rule.apply(100) = 90
t=1.1s: script CORRUPTED (mid-edit)
        refresh check -> compile FAILS -> old target RETAINED
t=1.6s: rule.apply(100) = 90   (still the OLD target -- no disruption)
t=2.7s: script FIXED (25% off)
        refresh check -> compile SUCCEEDS -> target SWAPPED
t=3.2s: rule.apply(100) = 75   (NEW target now active)
```

## 7. Gotchas & takeaways

> Gotcha: `refresh-check-delay` is a *minimum* interval between checks, triggered lazily on the next actual method call through the proxy, not a background timer guaranteeing the check happens exactly on schedule — a refreshable bean that goes unused for a long stretch won't refresh until the next time something actually calls it, even if the script file changed hours earlier. If a use case genuinely needs the refresh to happen promptly regardless of call traffic, this lazy-check-on-invocation behavior (rather than an active background poller) is an important operational detail to understand.

- Refreshable beans layer a `refresh-check-delay`-driven polling mechanism on top of dynamic-language beans, checking a script file's last-modified timestamp and recompiling/swapping the bean's implementation live when it changes, without an application restart.
- Callers interact with a stable AOP proxy, never the underlying compiled script object directly — this indirection is what makes the live-swap transparent, since the caller's reference never needs to change.
- `RefreshableTargetSource`'s built-in resilience means a broken or mid-edit script fails a refresh attempt safely, retaining the last-known-good target rather than crashing the application or serving a half-broken bean — a critical safety property for a feature that intentionally allows runtime code changes.
- The refresh check is lazy, triggered on the next actual method call through the proxy rather than by a guaranteed background timer — a script change won't take effect until something next actually invokes the bean, which may be later than the configured `refresh-check-delay` alone would suggest.
