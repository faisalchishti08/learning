---
card: spring-ldap
gi: 21
slug: parsing-ldif-files
title: "Parsing LDIF files"
---

## 1. What it is

LDIF (LDAP Data Interchange Format) is the standard plain-text file format for representing directory entries — a sequence of DN-plus-attributes blocks separated by blank lines, used for exporting, importing, and bulk-loading directory data. Spring LDAP's `LdifParser` (in `org.springframework.ldap.ldif.parser`) reads an LDIF file or stream and produces a sequence of `LdapAttributes` objects, one per entry, that can then be fed directly into `LdapTemplate.bind` or ODM-based creation.

## 2. Why & when

Directory data frequently needs to move in bulk — seeding a test environment with a realistic set of entries, migrating data from one directory server to another, or loading an initial dataset when standing up a new directory — and LDIF is the near-universal format directory servers and tools use for exactly this. Hand-writing code to parse LDIF's specific text format (DN lines, attribute lines, continuation lines for wrapped values, base64-encoded binary values) would be reinventing something Spring LDAP already provides; `LdifParser` exists so applications can consume standard LDIF files without implementing that parsing themselves.

Reach for `LdifParser` when:

- Seeding a test or development directory with a known, version-controlled set of entries from an `.ldif` file.
- Migrating or bulk-loading entries exported from another directory server or system.
- Building a one-time or repeatable data-loading utility that needs to read a standard LDIF export.

## 3. Core concept

Think of an LDIF file as a stack of index cards, one card per directory entry, each card starting with the entry's full address (its `dn:` line) followed by a list of labeled facts about it (`cn: Jane Smith`, `mail: jsmith@example.com`). `LdifParser` is a machine that reads through the stack of cards one at a time, converting each card's plain text into a structured `LdapAttributes` object your code can work with directly — rather than requiring your own program to understand where one card's information ends and the next begins, or how a long value that wraps across several lines (a continuation line, indicated by a leading space) is supposed to be reassembled.

```
dn: uid=jsmith,ou=people,dc=example,dc=com
objectClass: inetOrgPerson
uid: jsmith
cn: Jane Smith
sn: Smith
mail: jsmith@example.com

dn: uid=adavis,ou=people,dc=example,dc=com
objectClass: inetOrgPerson
uid: adavis
cn: Anne Davis
sn: Davis
mail: adavis@example.com
```

```java
Resource resource = new ClassPathResource("seed-data.ldif");
LdifParser parser = new LdifParser(resource);
parser.open();
while (parser.hasMoreRecords()) {
    LdapAttributes attrs = parser.getRecord();
    ldapTemplate.bind(attrs.getName(), null, attrs);
}
parser.close();
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LdifParser reads an LDIF file entry by entry, producing an LdapAttributes object per blank-line-separated block, fed into bind">
  <rect x="20" y="30" width="180" height="140" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="110" y="20" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">seed-data.ldif</text>
  <text x="110" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">dn: uid=jsmith,...</text>
  <text x="110" y="70" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">cn: Jane Smith</text>
  <text x="110" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(blank line)</text>
  <text x="110" y="115" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">dn: uid=adavis,...</text>
  <text x="110" y="130" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">cn: Anne Davis</text>

  <line x1="200" y1="100" x2="260" y2="100" stroke="#3fb950" stroke-width="2" marker-end="url(#q1)"/>
  <text x="230" y="90" fill="#3fb950" font-size="8" text-anchor="middle" font-family="sans-serif">parse</text>

  <rect x="270" y="60" width="160" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">LdapAttributes #1</text>
  <rect x="270" y="105" width="160" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="127" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">LdapAttributes #2</text>

  <line x1="430" y1="77" x2="480" y2="77" stroke="#6db33f" stroke-width="1.5" marker-end="url(#q2)"/>
  <line x1="430" y1="122" x2="480" y2="122" stroke="#6db33f" stroke-width="1.5" marker-end="url(#q3)"/>
  <text x="550" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">bind() each</text>

  <defs>
    <marker id="q1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="q2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="q3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Each blank-line-separated LDIF block becomes one `LdapAttributes` object, ready to be bound into the directory.

## 5. Runnable example

The scenario: bulk-loading a seed dataset from an LDIF file, starting with a basic load, then skipping entries that already exist (idempotent reload), and finally reporting a clear summary of successes and failures across a large file.

### Level 1 — Basic

```java
// BasicLdifLoad.java
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.core.LdapAttributes;
import org.springframework.ldap.ldif.parser.LdifParser;

public class BasicLdifLoad {
    public static void main(String[] args) throws Exception {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://localhost:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=admin,dc=example,dc=com");
        cs.setPassword("adminpass");
        cs.afterPropertiesSet();

        LdapTemplate template = new LdapTemplate(cs);

        Resource resource = new ClassPathResource("seed-data.ldif");
        LdifParser parser = new LdifParser(resource);
        parser.open();

        int count = 0;
        while (parser.hasMoreRecords()) {
            LdapAttributes attrs = parser.getRecord();
            template.bind(attrs.getName(), null, attrs);
            count++;
        }
        parser.close();

        System.out.println("Loaded " + count + " entries.");
    }
}
```

**How to run:** with `seed-data.ldif` (two entries, as shown in part 3) on the classpath and a writable directory available, run `java BasicLdifLoad.java`. Expected output: `Loaded 2 entries.` — both `jsmith` and `adavis` now exist in the directory.

### Level 2 — Intermediate

Running the same loader twice (a repeated test setup, or a rerun after a partial failure) fails on the second run, since `bind` throws `NameAlreadyBoundException` (card 0007) for entries that already exist. Making the load idempotent means skipping entries already present rather than crashing partway through.

```java
// IdempotentLdifLoad.java
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.LdapAttributes;
import org.springframework.ldap.ldif.parser.LdifParser;
import org.springframework.ldap.NameAlreadyBoundException;

public class IdempotentLdifLoad {
    private final LdapTemplate template;

    public IdempotentLdifLoad(LdapTemplate template) {
        this.template = template;
    }

    public void loadFrom(String classpathResource) throws Exception {
        Resource resource = new ClassPathResource(classpathResource);
        LdifParser parser = new LdifParser(resource);
        parser.open();

        while (parser.hasMoreRecords()) {
            LdapAttributes attrs = parser.getRecord();
            try {
                template.bind(attrs.getName(), null, attrs);
            } catch (NameAlreadyBoundException e) {
                System.out.println("Already exists, skipping: " + attrs.getName());
            }
        }
        parser.close();
    }
}
```

**How to run:** call `loadFrom("seed-data.ldif")` twice in a row against the same directory. Expected result: the first call loads both entries normally; the second call logs `Already exists, skipping: uid=jsmith,...` and the same for `adavis`, completing successfully rather than throwing partway through — the same LDIF file can now be safely reloaded any number of times.

### Level 3 — Advanced

A large LDIF file (hundreds or thousands of entries, common for a realistic test dataset or a migration) can have some entries fail for reasons other than "already exists" — a malformed entry, a schema violation, a transient connectivity issue. Aborting the whole load on the first such failure wastes all the successfully-loaded entries' progress; this level continues past individual failures and reports a complete summary.

```java
// ResilientLdifLoad.java
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.LdapAttributes;
import org.springframework.ldap.ldif.parser.LdifParser;
import org.springframework.ldap.NameAlreadyBoundException;
import org.springframework.ldap.NamingException;

import java.util.ArrayList;
import java.util.List;

public class ResilientLdifLoad {
    private final LdapTemplate template;

    public ResilientLdifLoad(LdapTemplate template) {
        this.template = template;
    }

    public record LoadSummary(int succeeded, int skipped, List<String> failed) {}

    public LoadSummary loadFrom(String classpathResource) throws Exception {
        Resource resource = new ClassPathResource(classpathResource);
        LdifParser parser = new LdifParser(resource);
        parser.open();

        int succeeded = 0;
        int skipped = 0;
        List<String> failed = new ArrayList<>();

        while (parser.hasMoreRecords()) {
            LdapAttributes attrs = parser.getRecord();
            try {
                template.bind(attrs.getName(), null, attrs);
                succeeded++;
            } catch (NameAlreadyBoundException e) {
                skipped++;
            } catch (NamingException e) {
                // A real failure (schema violation, malformed entry, transient error) — record it, keep going.
                failed.add(attrs.getName().toString() + ": " + e.getMessage());
            }
        }
        parser.close();
        return new LoadSummary(succeeded, skipped, failed);
    }
}
```

**How to run:** call `loadFrom("large-seed-data.ldif")` on a file containing, say, 500 well-formed entries and 3 entries deliberately missing a required attribute (triggering `ObjectClassViolationException`, a `NamingException` subtype). Expected result: `LoadSummary` reports `succeeded=497`, `skipped=0` (assuming a clean directory), and `failed` containing 3 entries with their specific DNs and error messages — the load processes the entire file rather than stopping at the first bad entry, and the caller gets a complete, actionable picture of exactly what did and didn't load.

## 6. Walkthrough

Tracing `loadFrom` processing a file with one entry that fails partway through a longer load, in execution order:

1. `parser.open()` opens the underlying LDIF resource for reading, positioning at the start of the file.
2. The `while (parser.hasMoreRecords())` loop begins; each iteration, `parser.hasMoreRecords()` checks whether another blank-line-separated block remains, and `parser.getRecord()` reads and parses the next one into an `LdapAttributes` object, advancing the parser's internal position past that block.
3. For each successfully parsed record, `template.bind(attrs.getName(), null, attrs)` attempts to create the corresponding entry; on success, `succeeded` is incremented, and the loop continues to the next record.
4. When a record corresponds to an entry missing a schema-required attribute, `bind` throws a `NamingException` subtype (not `NameAlreadyBoundException`, so it falls to the broader `catch (NamingException e)` block); this record's DN and the error message are appended to `failed`, and — critically — the loop does *not* terminate here, moving on to parse and attempt the next record.
5. Once `parser.hasMoreRecords()` returns `false` (the end of the file has been reached), the loop exits, `parser.close()` releases the underlying resource, and the accumulated `succeeded`, `skipped`, and `failed` counts/list are packaged into the returned `LoadSummary`.

```
loadFrom("large-seed-data.ldif")
  parser.open()
  loop: hasMoreRecords()? -> getRecord() -> bind()
     success              -> succeeded++
     NameAlreadyBoundException -> skipped++
     other NamingException     -> failed.add(dn + reason)   [loop continues, does NOT abort]
  (repeat until no more records)
  parser.close()
  -> LoadSummary(succeeded, skipped, failed)
```

## 7. Gotchas & takeaways

> Aborting an entire bulk load on the first entry that fails (rather than continuing and reporting a summary, as in Level 3) is a common but costly mistake for any realistically-sized dataset — a single malformed entry out of hundreds shouldn't sacrifice all the successfully-processed ones or force a manual restart from a known-good point in the file.

- `LdifParser` handles LDIF's own format details (continuation lines, base64-encoded values, comment lines) so calling code works entirely in terms of parsed `LdapAttributes` objects, never raw LDIF text.
- Always call `parser.open()` before the read loop and `parser.close()` afterward (or in a `finally`/try-with-resources equivalent) to ensure the underlying resource is properly released, especially if a load is interrupted partway through.
- Making a bulk load idempotent (Level 2, catching `NameAlreadyBoundException` per entry) is valuable for any seed-data script that might reasonably be rerun — test setup scripts in particular benefit from being safely repeatable.
- For any file large enough that a single bad entry is a real possibility, prefer continuing past per-entry failures and reporting a complete summary (Level 3) over letting one malformed entry abort the entire load silently partway through.
- LDIF is also the natural format for *exporting* data out of a directory (the reverse of parsing) — while this card focuses on reading LDIF in, the same `LdapAttributes` structures obtained from a search can, with the appropriate writer, be serialized back out to LDIF for backup or migration purposes.
