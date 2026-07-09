---
card: java
gi: 699
slug: migrate-jdk-source-to-git-github
title: Migrate JDK source to Git/GitHub
---

## 1. What it is

**JEP 357**, delivered in **Java 16**, moved the OpenJDK project's own source code from a **Mercurial** forest of repositories (hosted at `hg.openjdk.java.net`) to a single unified **Git** repository hosted on **GitHub** (`github.com/openjdk/jdk`). This is not a language feature or a library API — it is an engineering change to how the JDK's own source is stored, versioned, and reviewed. Contributors now `git clone` one repository instead of juggling several Mercurial repositories (one for `jdk`, one for `langtools`, one for `hotspot`, and so on), and code review moves through GitHub pull requests via OpenJDK's **Skara** tooling instead of Mercurial-based mailing-list patches.

## 2. Why & when

Before Java 16, building or contributing to OpenJDK meant cloning a "forest" of separate Mercurial repositories that had to be kept in sync with a helper script, and code review happened through a webrev-and-mailing-list process that was unfamiliar to most developers outside the OpenJDK community. Git and GitHub, by contrast, were already the tools most Java developers used every day for their own projects. JEP 357 consolidated the JDK's repositories into one Git repository and adopted GitHub pull requests for review, lowering the barrier to contributing and aligning OpenJDK's workflow with the tooling the wider Java ecosystem already knew. This is purely a project-infrastructure change: it doesn't add a class, method, or JVM flag, but it does change how you'd go about building OpenJDK from source, tracking a JDK bug fix back to its commit, or verifying exactly which source revision a given JDK build was produced from — all of which now mean using standard Git commands and browsing GitHub instead of Mercurial and webrevs.

## 3. Core concept

```bash
# Before Java 16 — a forest of Mercurial repositories:
hg clone https://hg.openjdk.java.net/jdk/jdk16
# (plus separate get_source.sh bookkeeping for sub-repos in some earlier releases)

# From Java 16 onward — a single Git repository on GitHub:
git clone https://github.com/openjdk/jdk.git
cd jdk
git log --oneline -5
```

Nothing here is an API you call from Java code — it's the toolchain and workflow used to obtain, browse, and contribute to the JDK's own source.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before Java 16, OpenJDK source lived in multiple Mercurial repositories reviewed via mailing-list webrevs; Java 16 onward it lives in one Git repository on GitHub reviewed via pull requests">
  <rect x="20" y="20" width="280" height="180" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Before Java 16</text>
  <rect x="45" y="55" width="100" height="28" rx="4" fill="#161b22" stroke="#8b949e"/>
  <text x="95" y="73" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">hg: jdk</text>
  <rect x="155" y="55" width="100" height="28" rx="4" fill="#161b22" stroke="#8b949e"/>
  <text x="205" y="73" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">hg: hotspot</text>
  <rect x="45" y="90" width="100" height="28" rx="4" fill="#161b22" stroke="#8b949e"/>
  <text x="95" y="108" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">hg: langtools</text>
  <rect x="155" y="90" width="100" height="28" rx="4" fill="#161b22" stroke="#8b949e"/>
  <text x="205" y="108" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">hg: nashorn</text>
  <text x="160" y="145" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">multiple repos, kept in sync</text>
  <text x="160" y="163" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">review: mailing list + webrevs</text>

  <rect x="340" y="20" width="280" height="180" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 16+</text>
  <rect x="400" y="60" width="160" height="50" rx="4" fill="#161b22" stroke="#6db33f"/>
  <text x="480" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">github.com/openjdk/jdk</text>
  <text x="480" y="98" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">single Git repository</text>
  <text x="480" y="145" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">one clone, one history</text>
  <text x="480" y="163" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">review: GitHub pull requests (Skara)</text>
</svg>

A forest of Mercurial repositories and mailing-list review becomes one Git repository on GitHub reviewed through pull requests.

## 5. Runnable example

Scenario: a small "build provenance" reporting tool — the kind of thing a release engineer might write to record exactly what source a build came from, which is precisely the concern JEP 357 made easier for the JDK project itself once it lived in one Git repository instead of several Mercurial ones. The example starts by reading the running JVM's own built-in version metadata, then extends to parsing that metadata into structured fields, then finally combines it with live Git commit information from the local repository this file lives in, producing one unified provenance report — mirroring how an OpenJDK build now embeds a single Git commit identity instead of several Mercurial changeset numbers.

### Level 1 — Basic

```java
// File: BuildInfoBasic.java
public class BuildInfoBasic {
    public static void main(String[] args) {
        System.out.println("java.version:     " + System.getProperty("java.version"));
        System.out.println("java.vm.version:  " + System.getProperty("java.vm.version"));
        System.out.println("java.vm.info:     " + System.getProperty("java.vm.info"));
        System.out.println("Runtime.version():" + Runtime.version());
    }
}
```

**How to run:**
```
java BuildInfoBasic.java
```

Expected output shape (exact values depend on which JDK build you run this with):
```
java.version:     21.0.3
java.vm.version:  21.0.3+9-LTS
java.vm.info:     mixed mode, sharing
Runtime.version():21.0.3+9-LTS
```

### Level 2 — Intermediate

```java
// File: BuildInfoParsed.java
public class BuildInfoParsed {
    public static void main(String[] args) {
        Runtime.Version v = Runtime.version();

        System.out.println("Feature version:  " + v.feature());
        System.out.println("Interim version:  " + v.interim());
        System.out.println("Update version:   " + v.update());
        System.out.println("Patch version:    " + v.patch());
        System.out.println("Build number:     " + v.build().map(String::valueOf).orElse("(none)"));
        System.out.println("Optional field:   " + v.optional().orElse("(none)"));
        System.out.println("Is pre-release?   " + v.pre().isPresent());
    }
}
```

**How to run:**
```
java BuildInfoParsed.java
```

Expected output shape (a build number wrapped in `Optional` is present whenever the JDK was built with one, which is the normal case for shipped releases):
```
Feature version:  21
Interim version:  0
Update version:   3
Patch version:    0
Build number:     9
Optional field:   LTS
Is pre-release?   false
```

### Level 3 — Advanced

```java
// File: ProvenanceReport.java
import java.io.IOException;
import java.util.List;

public class ProvenanceReport {

    static String runGit(String... args) {
        try {
            List<String> command = new java.util.ArrayList<>(List.of("git"));
            command.addAll(List.of(args));
            Process process = new ProcessBuilder(command)
                    .redirectErrorStream(true)
                    .start();
            String output = new String(process.getInputStream().readAllBytes()).trim();
            int exitCode = process.waitFor();
            return exitCode == 0 && !output.isEmpty() ? output : "(unavailable)";
        } catch (IOException | InterruptedException e) {
            return "(git not available: " + e.getMessage() + ")";
        }
    }

    public static void main(String[] args) {
        Runtime.Version v = Runtime.version();

        System.out.println("=== JVM build provenance ===");
        System.out.println("Runtime.version(): " + v);
        System.out.println("Vendor:            " + System.getProperty("java.vendor"));
        System.out.println("VM name:           " + System.getProperty("java.vm.name"));

        System.out.println();
        System.out.println("=== Source repository provenance (this checkout) ===");
        System.out.println("Git commit:        " + runGit("rev-parse", "--short", "HEAD"));
        System.out.println("Git branch:        " + runGit("rev-parse", "--abbrev-ref", "HEAD"));
        System.out.println("Working tree:      "
                + (runGit("status", "--porcelain").equals("(unavailable)") ? "clean" : "has local changes"));
    }
}
```

**How to run:**
```
java ProvenanceReport.java
```

Expected output shape (Git fields degrade to `(unavailable)` gracefully when run outside a Git checkout or without Git installed, rather than crashing):
```
=== JVM build provenance ===
Runtime.version(): 21.0.3+9-LTS
Vendor:            Eclipse Adoptium
VM name:           OpenJDK 64-Bit Server VM

=== Source repository provenance (this checkout) ===
Git commit:        4e2a9c1
Git branch:        main
Working tree:      clean
```

## 6. Walkthrough

1. `ProvenanceReport.main` starts by reading the *JVM's own* build identity through `Runtime.version()` and a few `System` properties (`java.vendor`, `java.vm.name`) — this is metadata the JDK already carries with every release, regardless of which version control system produced it.
2. It then calls `runGit(...)` three times to gather provenance for the *local source checkout this program is part of* — the short commit hash, the current branch name, and whether the working tree has uncommitted changes.
3. Inside `runGit`, a `ProcessBuilder` launches the real `git` executable as a subprocess (`redirectErrorStream(true)` merges stderr into stdout so error text doesn't get lost), reads all of its output, waits for it to exit, and returns that output — or a clearly labeled fallback string if `git` isn't installed or the command fails, so the program never throws past this point.
4. The two sections of output are printed one after another: first the JVM's self-reported build identity, then the Git-based provenance of the source tree — deliberately mirroring the two things JEP 357 unified for the JDK project itself. Before Java 16, tracing a JDK build back to its exact source state meant correlating a build number against changeset IDs across *several* Mercurial repositories; from Java 16 on, it means checking one Git commit hash in one repository.
5. This program is a small, self-contained analogue of that same idea applied to any Java project: pairing `Runtime.version()` (or an application's own version string) with `git rev-parse HEAD` gives a build a verifiable link back to the exact source commit it was built from — useful for release engineering, incident triage ("which commit is actually deployed?"), and reproducible builds.

```
main()
  -> read Runtime.version(), java.vendor, java.vm.name   (JVM's own provenance)
  -> runGit("rev-parse","--short","HEAD")                (source commit)
  -> runGit("rev-parse","--abbrev-ref","HEAD")           (source branch)
  -> runGit("status","--porcelain")                      (working tree cleanliness)
  -> print combined provenance report
```

## 7. Gotchas & takeaways

> `runGit` calling out to a real `git` subprocess means this example's Git section only works if run from inside a Git working directory with `git` on the `PATH`; if you copy the file elsewhere or `git` isn't installed, the Git fields print `(unavailable)` rather than crash — but the JVM-provenance section above it always works, since that metadata comes from the running JVM itself, not an external tool.

- JEP 357 changed **where and how OpenJDK's own source is stored and reviewed** (one Git repository on GitHub, reviewed via pull requests) — it added no Java language feature, API, or JVM flag for application developers to use.
- If you build OpenJDK from source, the practical difference is a single `git clone` instead of managing a Mercurial forest, and following the `github.com/openjdk/jdk` contribution workflow (Skara-based PRs) instead of mailing-list webrevs.
- The same "pair a runtime version with a source commit" pattern shown in `ProvenanceReport` is a useful practice for your own applications too: embedding a build's Git commit hash into a manifest attribute, `/version` endpoint, or startup log line gives you the same traceability OpenJDK gained project-wide from this migration.
- Because Git was already the tool most Java developers used for their own code, this migration mainly *lowered the friction of contributing to OpenJDK itself* — it's a project-health change more than a technical one.
- Don't confuse this with a JVM version-control feature at runtime — there is no `java.vm.scm` property or similar; the Git/GitHub migration is entirely about the OpenJDK project's engineering process, observable only if you go looking at `github.com/openjdk/jdk` yourself.
