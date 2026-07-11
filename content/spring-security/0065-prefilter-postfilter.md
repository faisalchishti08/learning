---
card: spring-security
gi: 65
slug: prefilter-postfilter
title: "@PreFilter / @PostFilter"
---

## 1. What it is

`@PreFilter` and `@PostFilter` apply an authorization expression to *each element* of a collection-shaped method argument or return value, removing elements that don't satisfy the expression rather than granting or denying access to the call as a whole — `@PreFilter` filters an incoming collection argument before the method body runs, and `@PostFilter` filters the method's returned collection after it runs, both using `filterObject` inside the expression to refer to the current element being evaluated.

```java
@PreFilter("filterObject.ownerId == authentication.principal.id")
public void deleteDocuments(List<Document> documents) {
    // by the time this method body runs, "documents" ALREADY contains ONLY the caller's own documents --
    // any documents belonging to someone else have been REMOVED from the list before this line
}

@PostFilter("filterObject.ownerId == authentication.principal.id or filterObject.classification == 'PUBLIC'")
public List<Document> findAllDocuments() {
    return documentRepository.findAll(); // returns EVERYTHING; @PostFilter trims it down AFTERWARD
}
```

## 2. Why & when

`@PreAuthorize`/`@PostAuthorize` (the previous card) make an all-or-nothing decision for the entire method call — but many real operations work on a *collection*, where the correct behavior isn't "deny the whole call" but rather "process only the elements the caller is actually allowed to see or affect," silently dropping the rest. `@PreFilter`/`@PostFilter` express exactly this element-wise filtering, letting a caller with partial access still successfully complete an operation against the subset they're entitled to, rather than being denied the entire call because *some* elements in the collection weren't theirs.

Reach for `@PreFilter` when:

- A method receives a collection and should silently operate only on the elements the caller owns or is otherwise entitled to affect — a bulk delete or bulk update where unauthorized elements should simply be excluded rather than causing the whole call to fail.

Reach for `@PostFilter` when:

- A method returns a collection assembled without per-caller filtering built into the query itself (a repository's `findAll()`), and the results need trimming down to only what the current caller may see — understanding that, like `@PostAuthorize`, this means the *full* underlying dataset is always fetched first, with filtering happening in application memory afterward, which can be a real performance concern for very large collections better filtered at the database query level instead.

## 3. Core concept

```
 @PreFilter("expression"):
   BEFORE the method body runs:
     for EACH element in the collection argument:
       evaluate "expression" with filterObject bound to THAT element
       KEEP the element if true, REMOVE it if false
   the METHOD BODY then runs against the ALREADY-FILTERED collection

 @PostFilter("expression"):
   the METHOD BODY runs FIRST, UNCONDITIONALLY, producing a collection
   AFTER it returns:
     for EACH element in the RETURNED collection:
       evaluate "expression" with filterObject bound to THAT element
       KEEP the element if true, REMOVE it if false
   the CALLER receives only the SURVIVING elements
```

Neither annotation denies the call itself — both simply shrink the collection down to whatever subset the expression accepts.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PreFilter removes disallowed elements from an incoming collection argument before the method body runs against the already reduced collection PostFilter lets the method body produce a full collection first then removes disallowed elements afterward before the caller ever sees the result">
  <rect x="15" y="20" width="280" height="60" rx="9" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="155" y="40" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">@PreFilter</text>
  <text x="155" y="53" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">filter the ARGUMENT first,</text>
  <text x="155" y="66" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">THEN run the method body</text>

  <rect x="345" y="20" width="280" height="60" rx="9" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="485" y="40" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">@PostFilter</text>
  <text x="485" y="53" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">run the method body FIRST,</text>
  <text x="485" y="66" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">THEN filter the RETURN value</text>

  <rect x="180" y="115" width="280" height="42" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="140" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">only the ALLOWED elements survive</text>

  <defs><marker id="a65" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="155" y1="80" x2="270" y2="115" stroke="#8b949e" stroke-width="1" marker-end="url(#a65)"/>
  <line x1="485" y1="80" x2="370" y2="115" stroke="#8b949e" stroke-width="1" marker-end="url(#a65)"/>
</svg>

Neither side denies the whole call — both simply shrink the collection to what the caller is entitled to.

## 5. Runnable example

The scenario: implement both filtering mechanisms faithfully, starting with `@PostFilter` reducing an over-fetched dataset, then `@PreFilter` trimming a bulk-operation argument before the operation runs, then combine both in a realistic scenario proving neither ever denies the entire call, only individual elements.

### Level 1 — Basic

`@PostFilter`-style: fetch everything, then filter the returned collection down to what the caller may see.

```java
import java.util.*;
import java.util.function.Predicate;

public class PreFilterLevel1 {
    record Authentication(String principalId) {}
    record Document(long id, String ownerId, String classification) {}

    static Authentication currentUser = new Authentication("5");

    static List<Document> allDocuments = List.of(
            new Document(1L, "5", "PRIVATE"),   // owned by the current user
            new Document(2L, "999", "PRIVATE"), // owned by someone else, NOT public
            new Document(3L, "999", "PUBLIC")   // owned by someone else, but PUBLIC
    );

    // models: @PostFilter("filterObject.ownerId == authentication.principal.id or filterObject.classification == 'PUBLIC'")
    static List<Document> findAllDocuments() {
        List<Document> unfiltered = allDocuments; // the METHOD BODY -- fetches EVERYTHING, unconditionally
        Predicate<Document> visibleToCaller = doc ->
                doc.ownerId().equals(currentUser.principalId()) || doc.classification().equals("PUBLIC");
        return unfiltered.stream().filter(visibleToCaller).toList(); // the FILTER, applied AFTER
    }

    public static void main(String[] args) {
        List<Document> visible = findAllDocuments();
        System.out.println("caller sees " + visible.size() + " of " + allDocuments.size() + " total documents: " + visible);
    }
}
```

How to run: `java PreFilterLevel1.java`

`findAllDocuments` fetches all three documents unconditionally, then filters them down to the two the current user (`"5"`) may actually see: their own private document, and the other user's public one — the second, other user's private document is silently excluded, never appearing in the caller's result at all.

### Level 2 — Intermediate

`@PreFilter`-style: filter a bulk-operation's incoming collection argument before the operation runs against it.

```java
import java.util.*;
import java.util.function.Predicate;

public class PreFilterLevel2 {
    record Authentication(String principalId) {}
    record Document(long id, String ownerId) {}

    static Authentication currentUser = new Authentication("5");
    static List<Long> deletedDocumentIds = new ArrayList<>();

    // models: @PreFilter("filterObject.ownerId == authentication.principal.id")
    static void deleteDocuments(List<Document> requestedDocuments) {
        Predicate<Document> ownedByCaller = doc -> doc.ownerId().equals(currentUser.principalId());
        List<Document> filtered = requestedDocuments.stream().filter(ownedByCaller).toList(); // filtered FIRST

        // the METHOD BODY now runs against the ALREADY-FILTERED list -- it never even SEES the excluded documents
        for (Document doc : filtered) {
            deletedDocumentIds.add(doc.id());
            System.out.println("  deleting document " + doc.id() + " (owned by " + doc.ownerId() + ")");
        }
    }

    public static void main(String[] args) {
        List<Document> requested = List.of(
                new Document(1L, "5"),   // owned by the caller
                new Document(2L, "999"), // owned by someone else -- will be SILENTLY excluded
                new Document(3L, "5")    // owned by the caller
        );

        deleteDocuments(requested);
        System.out.println("actually deleted: " + deletedDocumentIds + " (out of " + requested.size() + " requested)");
    }
}
```

How to run: `java PreFilterLevel2.java`

Three documents were requested for deletion, but only two (`1` and `3`, both owned by the caller) are actually processed — document `2`, owned by someone else, is filtered out *before* the method's deletion loop even begins, so it's never printed, never touched, and never appears in `deletedDocumentIds` at all; critically, the call as a whole still succeeds, rather than being denied outright because of the one unauthorized element.

### Level 3 — Advanced

Combine `@PreFilter` and `@PostFilter` in one realistic scenario — a bulk archive operation that filters its input, then a subsequent listing operation that filters its output — proving neither mechanism ever denies the entire call, only adjusts which elements participate.

```java
import java.util.*;
import java.util.function.Predicate;

public class PreFilterLevel3 {
    record Authentication(String principalId) {}
    record Document(long id, String ownerId, boolean archived, String classification) {}

    static Authentication currentUser = new Authentication("5");
    static List<Document> documentStore = new ArrayList<>(List.of(
            new Document(1L, "5", false, "PRIVATE"),
            new Document(2L, "999", false, "PRIVATE"),
            new Document(3L, "5", false, "PRIVATE"),
            new Document(4L, "999", false, "PUBLIC")
    ));

    // @PreFilter: only the caller's OWN documents are actually archived, silently skipping the rest
    static void archiveDocuments(List<Long> requestedIds) {
        List<Document> candidates = documentStore.stream().filter(d -> requestedIds.contains(d.id())).toList();
        List<Document> filtered = candidates.stream().filter(d -> d.ownerId().equals(currentUser.principalId())).toList();

        for (Document doc : filtered) {
            int idx = documentStore.indexOf(doc);
            documentStore.set(idx, new Document(doc.id(), doc.ownerId(), true, doc.classification()));
        }
        System.out.println("archived: " + filtered.stream().map(Document::id).toList() + " (out of requested " + requestedIds + ")");
    }

    // @PostFilter: everything NON-ARCHIVED is fetched, then filtered down to what the caller may see
    static List<Document> listActiveDocuments() {
        List<Document> unfiltered = documentStore.stream().filter(d -> !d.archived()).toList();
        Predicate<Document> visible = d -> d.ownerId().equals(currentUser.principalId()) || d.classification().equals("PUBLIC");
        return unfiltered.stream().filter(visible).toList();
    }

    public static void main(String[] args) {
        System.out.println("active documents BEFORE archiving: " + listActiveDocuments());

        archiveDocuments(List.of(1L, 2L, 3L)); // requests 3 documents, but only 1 and 3 belong to the caller

        System.out.println("active documents AFTER archiving: " + listActiveDocuments());
    }
}
```

How to run: `java PreFilterLevel3.java`

`archiveDocuments(List.of(1L, 2L, 3L))` archives only documents `1` and `3` (owned by the caller), silently skipping document `2` (owned by someone else) despite it being explicitly requested; the subsequent `listActiveDocuments()` call reflects this — document `4` (someone else's, but public) remains visible throughout, while documents `1` and `3` disappear from the active list once archived, and document `2` remains un-archived and correctly still hidden from the caller (since it was never theirs to see in the first place).

## 6. Walkthrough

Trace `archiveDocuments(List.of(1L, 2L, 3L))` from Level 3.

1. `candidates = documentStore.stream().filter(d -> requestedIds.contains(d.id())).toList()` selects the three documents whose IDs (`1`, `2`, `3`) appear in `requestedIds` — this yields `[Document(1,"5",...), Document(2,"999",...), Document(3,"5",...)]`, in that order.
2. `filtered = candidates.stream().filter(d -> d.ownerId().equals(currentUser.principalId())).toList()` applies the `@PreFilter`-equivalent step: it keeps only documents whose `ownerId` equals `"5"` — document `1` (`ownerId="5"`) passes, document `2` (`ownerId="999"`) is excluded, document `3` (`ownerId="5"`) passes; `filtered` becomes `[Document(1,...), Document(3,...)]`.
3. The `for` loop iterates only over this already-filtered list — for each of documents `1` and `3`, it finds their index in `documentStore` and replaces the entry with an otherwise-identical `Document` but `archived = true`; document `2`'s entry in `documentStore` is never touched at all during this loop, since it was excluded before the loop even began.
4. The final `println` reports `filtered.stream().map(Document::id).toList()` as `[1, 3]` — confirming exactly which documents were actually archived, distinct from the three that were originally requested.
5. Note that the method never threw any exception or denied the call as a whole, despite one of the three requested document IDs belonging to someone else — this is the defining characteristic of filter-style authorization: the call succeeds, just against a silently narrowed set of elements, in clear contrast to `@PreAuthorize`/`@PostAuthorize`'s all-or-nothing outcome from the previous card.

```
requestedIds = [1, 2, 3]
candidates (matching requested IDs)   = [Doc(1,"5"), Doc(2,"999"), Doc(3,"5")]
filtered (owned by caller "5" only)    = [Doc(1,"5"), Doc(3,"5")]       <- Doc(2,"999") silently excluded
archived (loop over "filtered" only)   = documents 1 and 3 updated; document 2 UNTOUCHED
```

## 7. Gotchas & takeaways

> **Gotcha:** `@PostFilter` operates on whatever collection the method actually returns, fetched in full *before* filtering — for a method backed by a database query returning a very large result set, this means the full, unfiltered dataset is loaded into application memory before any filtering happens, which can be a serious performance and memory concern at scale; pushing the equivalent filtering condition into the database query itself (a `WHERE owner_id = ? OR classification = 'PUBLIC'` clause) is almost always preferable for large datasets, reserving `@PostFilter` for smaller collections or cases where query-level filtering genuinely isn't feasible.

- `@PreFilter`/`@PostFilter` narrow a collection down to the elements an expression accepts, rather than denying the entire method call — the call itself always succeeds, just potentially against a smaller set of elements than originally requested or returned.
- `@PreFilter` filters an incoming collection argument before the method body runs against it; `@PostFilter` filters the method's own returned collection afterward, both using `filterObject` to refer to the current element inside the expression.
- `@PostFilter`'s "fetch everything, then filter in memory" approach is a real performance consideration for large datasets — database-level filtering is generally preferable when the underlying query can express the same condition directly.
- These annotations complement, rather than replace, `@PreAuthorize`/`@PostAuthorize` — a single application commonly uses filter-style annotations for collection-shaped operations and authorize-style annotations for single-object, all-or-nothing operations.
