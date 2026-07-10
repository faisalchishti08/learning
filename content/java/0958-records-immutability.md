---
card: java
gi: 958
slug: records-immutability
title: Records & immutability
---

## 1. What it is

Records guarantee **shallow immutability**: every component's backing field is implicitly `final`, meaning the field itself can never be reassigned after construction — there is no way to write `point.x = 5` on a record instance, and no setter methods are ever generated. What records do *not* guarantee is **deep immutability**: if a component's declared type is itself mutable (a `List`, an array, a mutable custom class), the record's field will always point to the *same* object, but that object's own internal state can still be changed through any reference to it, including references obtained elsewhere before or after the record was constructed — this is exactly the scenario explored practically in [auto-generated equals/hashCode/toString/accessors](0956-auto-generated-equals-hashcode-tostring-accessors.md). Genuine, deep immutability for a record with mutable-typed components requires deliberate extra work: defensively copying mutable arguments in the canonical constructor (so the record holds its *own* private copy, unreachable by any external reference), and returning defensive copies from accessors if a component's mutable internals must be exposed at all.

## 2. Why & when

Understanding exactly where a record's immutability guarantee stops matters because it's easy to assume "record" means "fully, deeply immutable" and be surprised later when a record's observed behavior (its `toString()` output, its `equals()` result, its `hashCode()`) changes over time despite never calling any setter — the actual cause being that some *other* code mutated a list, array, or mutable object that a record's field happens to reference. This becomes a real, practical concern anytime you design a record with a component whose type is a mutable collection or a mutable custom class, and it's the reason experienced Java developers default to defensively copying such components in the canonical constructor — accepting the caller's mutable list, but immediately copying it into the record's own private, and ideally itself immutable (`List.copyOf`), internal representation — so the record's *effective* behavior matches the deep immutability its name implies, even though the language itself only strictly guarantees the shallow version.

## 3. Core concept

```
record Team(String name, List<String> members) {}

Team t = new Team("Alpha", myMutableList);
myMutableList.add("Zoe");    // t.members() now ALSO shows "Zoe" -- t's FIELD didn't change,
                              // but the LIST OBJECT it points to did, and both t and
                              // myMutableList are looking at that SAME object

// The fix: defensive copy in the canonical constructor
record TeamSafe(String name, List<String> members) {
    TeamSafe {
        members = List.copyOf(members);   // makes an UNMODIFIABLE, INDEPENDENT copy --
    }                                      // now truly, deeply immutable
}

TeamSafe ts = new TeamSafe("Alpha", myMutableList);
myMutableList.add("Zoe");    // ts.members() is UNAFFECTED -- it has its own independent, frozen copy
```

Shallow immutability (the field itself never changes) is a language guarantee for every record automatically; deep immutability (the referenced data never changes either) requires a deliberate defensive-copy step the language does not perform for you.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A record's field pointing to the same mutable list object as an external reference, versus a defensively-copied field pointing to its own independent, frozen copy" >
  <text x="160" y="16" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Without defensive copy</text>
  <rect x="20" y="30" width="120" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="49" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Team.members field</text>
  <rect x="20" y="80" width="120" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="80" y="99" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">myMutableList ref</text>
  <rect x="200" y="55" width="140" height="30" fill="#1c2430" stroke="#e6edf3"/>
  <text x="270" y="74" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">SAME list object</text>
  <line x1="140" y1="45" x2="200" y2="65" stroke="#8b949e"/>
  <line x1="140" y1="95" x2="200" y2="75" stroke="#8b949e"/>
  <text x="270" y="110" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">mutating via EITHER reference affects BOTH</text>

  <text x="500" y="16" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">With defensive copy</text>
  <rect x="400" y="30" width="120" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="460" y="49" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">TeamSafe.members</text>
  <rect x="400" y="90" width="120" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="460" y="109" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">myMutableList ref</text>
  <rect x="550" y="20" width="80" height="25" fill="#1c2430" stroke="#6db33f"/>
  <text x="590" y="37" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">frozen copy</text>
  <rect x="550" y="95" width="80" height="25" fill="#1c2430" stroke="#f0883e"/>
  <text x="590" y="112" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">original</text>
  <line x1="520" y1="42" x2="550" y2="32" stroke="#8b949e"/>
  <line x1="520" y1="105" x2="550" y2="107" stroke="#8b949e"/>
  <text x="590" y="140" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">independent objects -- mutating one never affects the other</text>
</svg>

*Without a defensive copy, a record's mutable-typed component shares the same object with any external reference; a defensive copy in the canonical constructor severs that link.*

## 5. Runnable example

Scenario: build a small "team roster" record, exposing exactly where shallow immutability's guarantee ends — starting with a basic record showing the field-reassignment guarantee that *does* hold, then the mutable-component leak that the guarantee does *not* cover, then the full, correct defensive-copy fix applied both at construction and at the accessor level.

### Level 1 — Basic

```java
import java.util.*;

public class RecordImmutabilityBasic {
    record Point(int x, int y) {}

    public static void main(String[] args) {
        Point p = new Point(1, 2);
        System.out.println(p);
        // p.x = 5;  // COMPILE ERROR -- there is no setter, and the field is implicitly final
        System.out.println("record fields cannot be reassigned -- this is always guaranteed, for every record");
    }
}
```

**How to run:** `java RecordImmutabilityBasic.java` (JDK 17+).

Expected output:
```
RecordImmutabilityBasic$Point[x=1, y=2]
record fields cannot be reassigned -- this is always guaranteed, for every record
```

With purely primitive components, a record's immutability guarantee is total and unambiguous: there is no way to change `p`'s `x` or `y` after construction whatsoever — this is the shallow-immutability guarantee working exactly as expected, with nothing more to worry about, precisely because primitives have no separate "referenced object" that could be mutated independently.

### Level 2 — Intermediate

```java
import java.util.*;

public class RecordImmutabilityLeak {
    record Team(String name, List<String> members) {}

    public static void main(String[] args) {
        List<String> roster = new ArrayList<>(List.of("Ada", "Grace"));
        Team team = new Team("Alpha", roster);
        System.out.println("before: " + team);

        roster.add("Barbara"); // mutating the ORIGINAL list, via the ORIGINAL reference

        System.out.println("after:  " + team); // team's field never changed -- but its CONTENT did
    }
}
```

**How to run:** `java RecordImmutabilityLeak.java` (JDK 17+).

Expected output:
```
before: RecordImmutabilityLeak$Team[name=Alpha, members=[Ada, Grace]]
after:  RecordImmutabilityLeak$Team[name=Alpha, members=[Ada, Grace, Barbara]]
```

The real-world concern added: `team.members()` never returns a different *object* — it's always the same `roster` list reference — but that object's own contents were mutated via a completely separate variable (`roster`), and since the record's field still points to that exact same, now-mutated object, `team`'s observed state changes too, despite no code ever touching `team` directly; this is precisely the shallow-versus-deep immutability gap.

### Level 3 — Advanced

```java
import java.util.*;

public class RecordImmutabilityFixed {
    record Team(String name, List<String> members) {
        Team {
            members = List.copyOf(members); // DEFENSIVE COPY: independent AND unmodifiable
        }
        // Accessor is auto-generated here and already safe, because 'members' itself now
        // holds an unmodifiable list -- but if a component were, say, a mutable array,
        // you would ALSO need to override the accessor to return a defensive copy on read.
    }

    public static void main(String[] args) {
        List<String> roster = new ArrayList<>(List.of("Ada", "Grace"));
        Team team = new Team("Alpha", roster);
        System.out.println("before: " + team);

        roster.add("Barbara"); // mutating the ORIGINAL list -- team's copy is unaffected
        System.out.println("after external mutation:  " + team);

        try {
            team.members().add("Charlie"); // attempting to mutate the record's OWN copy
        } catch (UnsupportedOperationException e) {
            System.out.println("caught: " + e.getClass().getSimpleName() + " -- List.copyOf() is unmodifiable");
        }
    }
}
```

**How to run:** `java RecordImmutabilityFixed.java` (JDK 17+).

Expected output:
```
before: RecordImmutabilityFixed$Team[name=Alpha, members=[Ada, Grace]]
after external mutation:  RecordImmutabilityFixed$Team[name=Alpha, members=[Ada, Grace]]
caught: UnsupportedOperationException -- List.copyOf() is unmodifiable
```

The production-flavored hard case: `List.copyOf(members)` inside the compact canonical constructor does two things at once — it creates a genuinely *independent* copy (severing any link to the caller's original `roster` list, so external mutation no longer affects the record) and that copy is itself *unmodifiable* (so even code holding `team.members()` directly cannot mutate it), together providing the full, deep immutability guarantee a record's name implies, achieved here through deliberate, explicit defensive copying rather than anything the language does automatically.

## 6. Walkthrough

Tracing `RecordImmutabilityFixed.main` end to end:

1. `roster` is created as a mutable `ArrayList` containing `["Ada", "Grace"]`, and `new Team("Alpha", roster)` is called — this invokes the compact canonical constructor, binding its implicit `members` parameter to the `roster` reference itself (not yet a copy).
2. Inside the compact constructor body, `members = List.copyOf(members)` reassigns the local `members` parameter to a brand-new list object — one that contains the same elements as `roster` at this exact moment (`["Ada", "Grace"]`), but is an entirely separate object in memory, and is additionally wrapped to be unmodifiable.
3. The compact constructor body completes normally, so the compiler's implicit field assignment now runs: `Team`'s actual `members` field is set to *this newly-created copy* — not to `roster` — meaning from this point on, `team.members` and the original `roster` variable refer to two completely different list objects that merely happened to start out with identical contents.
4. `roster.add("Barbara")` mutates the *original* list — but since `team`'s `members` field was never pointed at that object in the first place (only at the independent copy made during construction), this mutation has absolutely no effect on `team`; printing `team` afterward still shows `[Ada, Grace]`, confirming the defensive copy successfully severed the link.
5. `team.members().add("Charlie")` calls the record's auto-generated accessor, which returns the record's own internal list — the one created by `List.copyOf` — and then attempts to mutate it directly; because `List.copyOf` specifically returns an unmodifiable list implementation, this `add` call throws `UnsupportedOperationException` immediately, rather than silently succeeding and corrupting the record's supposedly-immutable state.
6. The caught exception is printed, confirming both halves of the fix worked together: the record is immune to *external* mutation (via the original `roster` reference, since it now holds its own independent copy) and immune to mutation *through its own accessor* (since that copy is itself unmodifiable) — together providing the complete, deep immutability guarantee that `List.copyOf` inside the canonical constructor was specifically chosen to deliver, addressing exactly the gap the shallow-immutability-only version from Level 2 left open.

## 7. Gotchas & takeaways

> **Gotcha:** `List.copyOf` (and `Set.copyOf`, `Map.copyOf`) throw `NullPointerException` if given a `null` argument, or if the collection contains any `null` elements — this is a deliberate design choice (these methods assume genuinely immutable, null-free data), but it means adopting the defensive-copy pattern shown above can introduce a new failure mode (rejecting nulls that a more permissive, non-defensive version would have silently accepted) that's worth being aware of and validating for explicitly if `null` values are a legitimate possibility for your use case.

- Records guarantee shallow immutability automatically: every component's field is implicitly final and can never be reassigned — there is no setter, and no way to change which object a record's field refers to after construction.
- Records do not guarantee deep immutability: if a component's type is itself mutable, the object it refers to can still be mutated through any other reference to that same object, changing the record's observed behavior (`toString()`, `equals()`, `hashCode()`) without ever touching the record directly.
- The standard fix is a defensive copy inside the canonical constructor (`List.copyOf(members)`, or equivalent for other mutable types), which both severs the link to the caller's original object and, ideally, produces an unmodifiable copy that resists mutation through the record's own accessor as well.
- Achieving full, deep immutability for a record with mutable-typed components requires this deliberate extra step — it is not something the record keyword provides automatically.
- `List.copyOf`/`Set.copyOf`/`Map.copyOf` reject `null` collections and `null` elements outright, which is worth accounting for explicitly if your defensive-copy strategy needs to tolerate nulls.
- See [auto-generated equals/hashCode/toString/accessors](0956-auto-generated-equals-hashcode-tostring-accessors.md) for the concrete failure mode (broken `HashSet`/`HashMap` lookups) this immutability gap can cause in practice, and [record components & canonical constructor](0954-record-components-canonical-constructor.md) for how the canonical constructor is exactly where this defensive-copy logic belongs.
