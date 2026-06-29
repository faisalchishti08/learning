---
card: spring-framework
gi: 8
slug: licensing-apache-license-2-0
title: Licensing (Apache License 2.0)
---

## 1. What it is

The Spring Framework (and all Spring projects: Spring Boot, Spring Data, Spring Security, etc.) is released under the **Apache License, Version 2.0** (AL 2.0). This is one of the most permissive and widely-adopted open source licenses.

The full license text is at: `https://www.apache.org/licenses/LICENSE-2.0`

Every Spring JAR contains a `LICENSE` file with the AL 2.0 text and a `NOTICE` file listing attribution requirements.

## 2. Why & when

**Apache License 2.0 is business-friendly.** It allows you to:

- **Use** Spring in commercial products, proprietary applications, and SaaS products without paying royalties.
- **Modify** Spring source code and distribute the modified version.
- **Sublicense** — embed Spring in products you sell under any license (proprietary or open source).
- **Patent protection** — AL 2.0 includes an express patent license from all contributors, and a patent retaliation clause (if you sue someone for patent infringement related to Spring, your patent license is terminated).

Things AL 2.0 **requires**:
- Include the original copyright notice and the license text in any distribution that contains Spring.
- If you modify Spring source files, state that you made changes.
- Include the `NOTICE` file if one exists.

Things AL 2.0 **does not require**:
- Open-sourcing your own application code (unlike GPL).
- Paying any fees or royalties.
- Seeking permission before using Spring commercially.

**This matters in practice when:** your legal or procurement team asks "can we use this in production?". The answer for Apache 2.0 software is yes, with the attribution requirements above. Most organisations already have a blanket policy permitting AL 2.0 software.

## 3. Core concept

AL 2.0 compared to other common licenses:

| License | Use commercially? | Modify? | Must open-source your app? | Patent grant? |
|---|---|---|---|---|
| **Apache 2.0** | Yes | Yes | No | Yes |
| MIT | Yes | Yes | No | No |
| GPL v2 | Yes | Yes | Yes (if distributed) | No |
| GPL v3 | Yes | Yes | Yes (if distributed) | Yes |
| LGPL | Yes | Yes | No (linking only) | No |
| SSPL | Limited | Yes | Yes (if offered as service) | No |

The key advantage of AL 2.0 over MIT is the **patent termination clause**: contributors to Spring grant you a license to their patents. If you use Spring and then sue a Spring contributor for patent infringement related to Spring code, your patent license automatically terminates. This makes Spring safer to use in environments with active patent litigation concerns.

The VMware (now Broadcom) transfer of the Spring trademark and commercial support business does not affect the Apache 2.0 license on the open-source code — the code remains free and open forever under AL 2.0.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Apache License 2.0 grants and requirements for Spring users">
  <defs>
    <marker id="la" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="lw" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>

  <!-- Spring source -->
  <rect x="240" y="10" width="220" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="35" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Framework (Apache 2.0)</text>

  <!-- Grants -->
  <rect x="10" y="80" width="280" height="90" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="102" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Grants to you (free)</text>
  <text x="150" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">• Use in commercial products</text>
  <text x="150" y="137" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">• Modify source code</text>
  <text x="150" y="154" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">• Sublicense / embed</text>
  <text x="150" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">• Patent license (contributor patents)</text>

  <!-- Requirements -->
  <rect x="410" y="80" width="280" height="90" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="550" y="102" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Requires from you</text>
  <text x="550" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">• Keep copyright + license text</text>
  <text x="550" y="137" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">• State changes if you modify Spring</text>
  <text x="550" y="154" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">• Include NOTICE file</text>
  <text x="550" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">• (Does NOT require open-sourcing your app)</text>

  <line x1="350" y1="50" x2="210" y2="78" stroke="#6db33f" stroke-width="1.5" marker-end="url(#la)"/>
  <line x1="350" y1="50" x2="490" y2="78" stroke="#f0883e" stroke-width="1.5" marker-end="url(#lw)"/>

  <text x="350" y="200" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Your application code stays proprietary — AL 2.0 has no copyleft (share-alike) requirement</text>
</svg>

Apache 2.0 is "use freely, attribute appropriately."

## 5. Runnable example

We'll write a license checker that reads a list of a project's dependencies and flags any non-permissive license — exactly the kind of check a compliance script or CI gate performs.

### Level 1 — Basic

Classify licenses by permissiveness and flag risky ones.

```java
// LicenseCheckerDemo.java — run with: java LicenseCheckerDemo.java

import java.util.*;

public class LicenseCheckerDemo {

    enum PermissiveLevel { PERMISSIVE, WEAK_COPYLEFT, STRONG_COPYLEFT, NETWORK_COPYLEFT, UNKNOWN }

    record Dependency(String groupId, String artifactId, String version, String license) {}

    static final Map<String, PermissiveLevel> LICENSE_CLASSIFICATIONS = Map.of(
        "Apache-2.0", PermissiveLevel.PERMISSIVE,
        "MIT",        PermissiveLevel.PERMISSIVE,
        "BSD-2-Clause", PermissiveLevel.PERMISSIVE,
        "BSD-3-Clause", PermissiveLevel.PERMISSIVE,
        "LGPL-2.1",   PermissiveLevel.WEAK_COPYLEFT,
        "LGPL-3.0",   PermissiveLevel.WEAK_COPYLEFT,
        "GPL-2.0",    PermissiveLevel.STRONG_COPYLEFT,
        "GPL-3.0",    PermissiveLevel.STRONG_COPYLEFT,
        "AGPL-3.0",   PermissiveLevel.NETWORK_COPYLEFT,
        "SSPL-1.0",   PermissiveLevel.NETWORK_COPYLEFT
    );

    // Typical Spring Boot 3 project dependencies
    static final List<Dependency> PROJECT_DEPS = List.of(
        new Dependency("org.springframework",      "spring-core",          "6.1.4",  "Apache-2.0"),
        new Dependency("org.springframework.boot", "spring-boot",          "3.2.2",  "Apache-2.0"),
        new Dependency("org.springframework.data", "spring-data-jpa",      "3.2.2",  "Apache-2.0"),
        new Dependency("com.fasterxml.jackson",    "jackson-databind",     "2.16.1", "Apache-2.0"),
        new Dependency("org.hibernate.orm",        "hibernate-core",       "6.4.2",  "LGPL-2.1"),
        new Dependency("ch.qos.logback",           "logback-classic",      "1.4.14", "LGPL-2.1"),
        new Dependency("org.slf4j",                "slf4j-api",            "2.0.11", "MIT"),
        new Dependency("io.micrometer",            "micrometer-core",      "1.12.2", "Apache-2.0"),
        new Dependency("org.postgresql",           "postgresql",           "42.7.1", "BSD-2-Clause"),
        new Dependency("com.example",              "internal-lib",         "1.0.0",  "GPL-2.0")  // problematic!
    );

    public static void main(String[] args) {
        System.out.println("=== License Compliance Check ===\n");
        System.out.printf("%-45s %-12s %-22s%n", "Artifact", "License", "Classification");
        System.out.println("-".repeat(82));

        List<Dependency> issues = new ArrayList<>();
        for (Dependency d : PROJECT_DEPS) {
            PermissiveLevel level = LICENSE_CLASSIFICATIONS.getOrDefault(d.license(), PermissiveLevel.UNKNOWN);
            String flag = (level == PermissiveLevel.STRONG_COPYLEFT || level == PermissiveLevel.NETWORK_COPYLEFT)
                ? " ⚠ REVIEW REQUIRED" : "";
            System.out.printf("%-45s %-12s %-22s%s%n",
                d.groupId() + ":" + d.artifactId(), d.license(), level, flag);
            if (!flag.isEmpty()) issues.add(d);
        }

        if (!issues.isEmpty()) {
            System.out.println("\n=== Issues requiring legal review ===");
            issues.forEach(d -> System.out.println("  " + d.groupId() + ":" + d.artifactId()
                + " (" + d.license() + ") — may require open-sourcing your application code"));
        } else {
            System.out.println("\nAll licenses are permissive or weak-copyleft — no strong copyleft detected.");
        }
    }
}
```

How to run: `java LicenseCheckerDemo.java`

The output shows every dependency's license and classification. `GPL-2.0` is flagged — if your application links to a GPL library in a distributed product, you may need to release your own code under GPL. Legal counsel decides on a case-by-case basis.

### Level 2 — Intermediate

Add NOTICE file generation — the attribution requirement that AL 2.0 mandates when you distribute software that uses Apache-licensed libraries.

```java
// LicenseCheckerV2.java — run with: java LicenseCheckerV2.java
// Generates a NOTICE file for AL 2.0 attribution requirements.

import java.util.*;
import java.time.Year;

public class LicenseCheckerV2 {

    record Dependency(String name, String version, String license,
                      String copyright, String noticeText) {}

    static final List<Dependency> SPRING_STACK = List.of(
        new Dependency(
            "Spring Framework", "6.1.4", "Apache-2.0",
            "Copyright 2002-" + Year.now() + " VMware, Inc.",
            "This product includes software developed by the Spring Framework project."),
        new Dependency(
            "Spring Boot", "3.2.2", "Apache-2.0",
            "Copyright 2012-" + Year.now() + " the original author or authors.",
            "Spring Boot is built on top of the Spring Framework."),
        new Dependency(
            "Jackson Databind", "2.16.1", "Apache-2.0",
            "Copyright (c) 2012- FasterXML, LLC",
            "Jackson JSON processor. https://github.com/FasterXML/jackson"),
        new Dependency(
            "Micrometer", "1.12.2", "Apache-2.0",
            "Copyright (c) 2017-" + Year.now() + " VMware, Inc.",
            "Application metrics facade for the JVM.")
    );

    public static void main(String[] args) {
        System.out.println("=== Generating NOTICE file for Apache 2.0 compliance ===\n");

        StringBuilder notice = new StringBuilder();
        notice.append("NOTICE\n");
        notice.append("======\n\n");
        notice.append("This product includes software under the Apache License, Version 2.0.\n\n");
        notice.append("Third-party components:\n");
        notice.append("-".repeat(60)).append("\n\n");

        for (Dependency d : SPRING_STACK) {
            if ("Apache-2.0".equals(d.license())) {
                notice.append(d.name()).append(" ").append(d.version()).append("\n");
                notice.append(d.copyright()).append("\n");
                notice.append("License: ").append(d.license()).append("\n");
                notice.append("Note: ").append(d.noticeText()).append("\n\n");
            }
        }

        notice.append("Full license text:\n");
        notice.append("  https://www.apache.org/licenses/LICENSE-2.0\n\n");
        notice.append("You may obtain a copy of each component's source under its respective license.\n");

        System.out.println(notice);
        System.out.println("=== Attribution requirements met ===");
        System.out.println("  Include this NOTICE file in your distribution.");
        System.out.println("  Include LICENSE (Apache 2.0 text) in your distribution.");
        System.out.println("  Your application code remains proprietary.");
    }
}
```

How to run: `java LicenseCheckerV2.java`

The generated NOTICE file lists every Apache 2.0 library with its copyright. This is what you'd include in the `META-INF/` folder of your JAR, or in a `third-party-licenses/` directory in your release package.

### Level 3 — Advanced

Full compliance report with SPDX expressions, risk matrix, and CI gate decision for an enterprise build pipeline.

```java
// LicenseCheckerV3.java — run with: java LicenseCheckerV3.java
// Enterprise compliance: SPDX identifiers, risk matrix, CI gate.

import java.util.*;
import java.util.stream.*;

public class LicenseCheckerV3 {

    enum Risk { APPROVED, REVIEW, BLOCKED }

    record LicensePolicy(String spdxId, Risk risk, String notes) {}

    static final Map<String, LicensePolicy> POLICY = new LinkedHashMap<>();
    static {
        POLICY.put("Apache-2.0",   new LicensePolicy("Apache-2.0", Risk.APPROVED,
            "Standard Spring/ASF license — approved for all use cases"));
        POLICY.put("MIT",          new LicensePolicy("MIT",        Risk.APPROVED,
            "Permissive — no patent grant, but low risk"));
        POLICY.put("BSD-2-Clause", new LicensePolicy("BSD-2-Clause", Risk.APPROVED,
            "Permissive — approved"));
        POLICY.put("BSD-3-Clause", new LicensePolicy("BSD-3-Clause", Risk.APPROVED,
            "Permissive with non-endorsement clause — approved"));
        POLICY.put("LGPL-2.1",     new LicensePolicy("LGPL-2.1",   Risk.REVIEW,
            "Weak copyleft — linking OK in most cases; legal must confirm"));
        POLICY.put("LGPL-3.0",     new LicensePolicy("LGPL-3.0",   Risk.REVIEW,
            "Weak copyleft — linking OK; extra provisions for hardware"));
        POLICY.put("GPL-2.0",      new LicensePolicy("GPL-2.0",    Risk.BLOCKED,
            "Strong copyleft — distribution may require open-sourcing app"));
        POLICY.put("GPL-3.0",      new LicensePolicy("GPL-3.0",    Risk.BLOCKED,
            "Strong copyleft — distribution may require open-sourcing app"));
        POLICY.put("AGPL-3.0",     new LicensePolicy("AGPL-3.0",   Risk.BLOCKED,
            "Network copyleft — SaaS use triggers copyleft obligation"));
    }

    record Dependency(String artifact, String version, String spdxLicense) {}

    static final List<Dependency> DEPS = List.of(
        new Dependency("org.springframework:spring-core",       "6.1.4",  "Apache-2.0"),
        new Dependency("org.springframework.boot:spring-boot",  "3.2.2",  "Apache-2.0"),
        new Dependency("org.hibernate.orm:hibernate-core",      "6.4.2",  "LGPL-2.1"),
        new Dependency("ch.qos.logback:logback-classic",        "1.4.14", "LGPL-2.1"),
        new Dependency("org.slf4j:slf4j-api",                   "2.0.11", "MIT"),
        new Dependency("io.micrometer:micrometer-core",         "1.12.2", "Apache-2.0"),
        new Dependency("org.postgresql:postgresql",             "42.7.1", "BSD-2-Clause"),
        new Dependency("com.example:internal-commons",          "2.0.0",  "Apache-2.0"),
        new Dependency("org.example:old-library",               "0.9.0",  "GPL-2.0"),
        new Dependency("io.example:analytics",                  "1.0.0",  "AGPL-3.0")
    );

    public static void main(String[] args) {
        System.out.println("=== Enterprise License Compliance Report ===\n");

        Map<Risk, List<Dependency>> byRisk = new EnumMap<>(Risk.class);
        for (Dependency d : DEPS) {
            LicensePolicy policy = POLICY.getOrDefault(d.spdxLicense(),
                new LicensePolicy(d.spdxLicense(), Risk.REVIEW, "Unknown license — manual review"));
            byRisk.computeIfAbsent(policy.risk(), k -> new ArrayList<>()).add(d);
        }

        System.out.printf("%-50s %-14s %-8s %s%n", "Artifact", "License", "Risk", "Notes");
        System.out.println("-".repeat(110));
        for (Dependency d : DEPS) {
            LicensePolicy p = POLICY.getOrDefault(d.spdxLicense(),
                new LicensePolicy(d.spdxLicense(), Risk.REVIEW, "Unknown"));
            System.out.printf("%-50s %-14s %-8s %s%n",
                d.artifact(), d.spdxLicense(), p.risk(), p.notes());
        }

        System.out.println("\n=== Summary ===");
        for (Risk r : Risk.values()) {
            List<Dependency> list = byRisk.getOrDefault(r, List.of());
            System.out.printf("  %-8s %d artifact(s)%n", r, list.size());
            list.forEach(d -> System.out.println("    " + d.artifact() + " (" + d.spdxLicense() + ")"));
        }

        boolean blocked = byRisk.containsKey(Risk.BLOCKED) && !byRisk.get(Risk.BLOCKED).isEmpty();
        System.out.println("\n=== CI Gate Decision ===");
        if (blocked) {
            System.out.println("  BUILD FAIL — BLOCKED licenses detected.");
            System.out.println("  Remove or replace: " +
                byRisk.get(Risk.BLOCKED).stream()
                    .map(Dependency::artifact).collect(Collectors.joining(", ")));
        } else {
            System.out.println("  BUILD PASS — No blocked licenses.");
        }
    }
}
```

How to run: `java LicenseCheckerV3.java`

The CI gate exits with a conceptual BUILD FAIL when GPL/AGPL libraries are in the dependency tree. In a real pipeline this would use tools like `license-maven-plugin`, `fossa`, or `snyk` — the logic is the same as our classifier.

## 6. Walkthrough

**Level 1 — classification scan:**
Each dependency is looked up in `LICENSE_CLASSIFICATIONS`. `GPL-2.0` maps to `STRONG_COPYLEFT` — the flag `⚠ REVIEW REQUIRED` is appended. In practice, Hibernate 6 uses LGPL 2.1 (weak copyleft) which requires legal review but is generally acceptable for linking without open-sourcing your app.

**Level 2 — NOTICE generation:**
The NOTICE file loops over AL 2.0 dependencies and formats: name, version, copyright line, and the NOTICE text from the original library. When you ship a JAR that bundles Spring, this generated file satisfies AL 2.0's attribution requirement.

**Level 3 — CI gate flow:**
1. All `DEPS` are classified against `POLICY`.
2. `byRisk` groups them: APPROVED (7), REVIEW (2 — Hibernate + Logback), BLOCKED (2 — GPL-2.0, AGPL-3.0).
3. Because `BLOCKED` is non-empty, the gate prints `BUILD FAIL` and lists the problematic artifacts.
4. Developers must replace `old-library` and `analytics` with permissively-licensed alternatives (or obtain a commercial license) before the build is permitted.

**Real tooling:** `license-maven-plugin` generates `THIRD-PARTY.txt`; `fossa` integrates into GitHub PR checks; `Snyk` flags license issues alongside security vulnerabilities. All use the same SPDX license identifier taxonomy.

## 7. Gotchas & takeaways

> **Apache 2.0 does not prevent commercial use.** A common misconception is that "open source = can't use commercially". Under AL 2.0, Broadcom (the Spring trademark holder) gives away the source code for free — you can build any product on it without paying. What you cannot do is remove the copyright notices or claim you wrote it.

> **LGPL and dynamic linking.** Libraries like Hibernate ORM (LGPL 2.1) are fine to *use* in a closed-source product as long as you link dynamically (as a separate JAR) and allow users to replace the LGPL component. Maven's dependency mechanism satisfies this — Spring Boot's fat JAR bundles everything, but users can exclude and replace Hibernate via Maven exclusions. Most enterprises obtain a legal opinion on this; it is generally considered safe.

- Spring's own license never changes retroactively — past releases stay AL 2.0 forever.
- Broadcom commercialises Spring via VMware Spring commercial subscriptions (support, SLAs), not by changing the license.
- The Apache Software Foundation's CLA (Contributor License Agreement) grants the ASF the right to relicense contributions, which protects the project from a single contributor revoking their contribution's license.
- `SPDX-License-Identifier: Apache-2.0` in a file header is the machine-readable way to assert AL 2.0 license — used by GitHub's license detection and `fossa`.
- If you fork Spring and distribute the fork, you must keep all copyright notices and the license file. You can add your own code alongside under any license, but the Spring core must remain AL 2.0.
