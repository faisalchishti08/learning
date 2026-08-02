---
card: data-structures
gi: 131
slug: spell-check-dictionary-lookup
title: Spell-check & dictionary lookup
---

## 1. What it is

A trie-backed **spell-checker** confirms whether a typed word exists in a dictionary (an exact `search`), and — the harder, more useful part — suggests corrections for a misspelled word by finding dictionary words within a small **edit distance** (typically 1 or 2 character changes: insertions, deletions, or substitutions).

## 2. Why & when

Exact dictionary lookup is just the trie's `search` operation. The real value of a trie here is suggesting corrections *efficiently*: instead of comparing a misspelled word against every dictionary entry one by one, you walk the trie once, allowing a small, bounded number of mismatches along the way — pruning entire subtrees the moment too many edits have been used, which a plain list-based comparison cannot do.

## 3. Core concept

**Exact lookup — the easy part.** This is exactly the trie's `search` method from [Insert / search / startsWith](0129-insert-search-startswith.md): walk the tree following the typed word's characters; if the walk succeeds and lands on an `isEndOfWord` node, the word is correctly spelled.

**Suggesting corrections — bounded edit-distance search.** To find dictionary words within `k` edits of a misspelled word, perform a **DFS over the trie itself** (not over the dictionary as a flat list) that tracks how many edits have been used so far. At each trie node, try three kinds of moves against the target word's next character:

- **Match:** if the trie edge's character equals the target's current character, advance both without using an edit.
- **Substitute:** try every other trie edge from this node, using up one edit, and advance both.
- **Insert / delete:** try advancing only the target's index (skip a target character) or only the trie's position (skip a trie character), each using up one edit.

Prune any branch immediately once its edit count exceeds `k` — this is what keeps the search fast, since it avoids exploring parts of the trie that can never produce a valid suggestion.

**Why searching the trie beats searching the dictionary list.** Many dictionary words share prefixes. Once a branch has used up its edit budget, the *entire* remaining subtree under that branch is pruned in one step — a flat list has no equivalent shortcut, since every word must be checked independently.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Searching a trie for words within edit distance 1 of the misspelled word ct, finding cat via one substitution and cot via one substitution, while pruning branches that would need two or more edits">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">misspelled input: "ct"   (max 1 edit allowed)</text>
    <circle cx="80" cy="50" r="12" fill="#161b22" stroke="#8b949e"/><text x="80" y="54" fill="#e6edf3" text-anchor="middle" font-size="8">c</text>
    <circle cx="160" cy="30" r="12" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/><text x="160" y="34" fill="#e6edf3" text-anchor="middle" font-size="8">a*</text>
    <circle cx="160" cy="70" r="12" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/><text x="160" y="74" fill="#e6edf3" text-anchor="middle" font-size="8">o*</text>
    <line x1="92" y1="50" x2="148" y2="34" stroke="#8b949e"/>
    <line x1="92" y1="50" x2="148" y2="66" stroke="#8b949e"/>
    <text x="220" y="30" fill="#79c0ff" font-size="9">"cat": substitute t-&gt;a costs 1 edit -- within budget</text>
    <text x="220" y="70" fill="#79c0ff" font-size="9">"cot": substitute t-&gt;o costs 1 edit -- within budget</text>
    <circle cx="160" cy="110" r="12" fill="#161b22" stroke="#8b949e"/><text x="160" y="114" fill="#e6edf3" text-anchor="middle" font-size="8">a</text>
    <circle cx="220" cy="110" r="12" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="220" y="114" fill="#e6edf3" text-anchor="middle" font-size="6">rt*</text>
    <line x1="92" y1="52" x2="148" y2="106" stroke="#8b949e"/>
    <line x1="172" y1="110" x2="208" y2="110" stroke="#8b949e"/>
    <text x="300" y="150" fill="#f0883e" text-anchor="middle" font-size="9">"cart": needs 2 edits (insert 'a' -&gt; substitute -&gt; insert 'r') -- pruned, exceeds budget</text>
  </g>
</svg>

Starting from `"ct"` with an edit budget of `1`, the search reaches `"cat"` and `"cot"` (each one substitution away), but prunes the `"cart"` branch, since matching it would need more than one edit.

## 5. Runnable example

```java
// SpellCheck.java
import java.util.HashMap;
import java.util.Map;
import java.util.ArrayList;
import java.util.List;

public class SpellCheck {

    static class TrieNode {
        Map<Character, TrieNode> children = new HashMap<>();
        boolean isEndOfWord = false;
    }

    static class Dictionary {
        TrieNode root = new TrieNode();

        void insert(String word) {
            TrieNode current = root;
            for (char c : word.toCharArray()) current = current.children.computeIfAbsent(c, key -> new TrieNode());
            current.isEndOfWord = true;
        }

        // Basic: exact spell-check -- is this word in the dictionary at all?
        boolean isCorrectlySpelled(String word) {
            TrieNode current = root;
            for (char c : word.toCharArray()) {
                current = current.children.get(c);
                if (current == null) return false;
            }
            return current.isEndOfWord;
        }
    }

    static void basicLevel() {
        Dictionary dict = new Dictionary();
        for (String w : new String[]{"cat", "car", "cot", "cart"}) dict.insert(w);

        System.out.println("basic: isCorrectlySpelled(\"cat\") -> " + dict.isCorrectlySpelled("cat"));
        System.out.println("basic: isCorrectlySpelled(\"ct\")  -> " + dict.isCorrectlySpelled("ct"));
    }

    // Intermediate + Advanced: suggest corrections within a given edit-distance budget, pruning as we go.
    static void suggest(TrieNode node, char[] target, int targetIndex, int editsUsed, int maxEdits,
                         StringBuilder soFar, List<String> results) {
        if (editsUsed > maxEdits) return; // PRUNE: this branch can no longer produce a valid suggestion

        if (targetIndex == target.length) {
            if (node.isEndOfWord && editsUsed <= maxEdits) results.add(soFar.toString());
            // still allow further insertions beyond the target's length, within budget
            for (Map.Entry<Character, TrieNode> entry : node.children.entrySet()) {
                soFar.append(entry.getKey());
                suggest(entry.getValue(), target, targetIndex, editsUsed + 1, maxEdits, soFar, results); // insert extra char
                soFar.deleteCharAt(soFar.length() - 1);
            }
            return;
        }

        for (Map.Entry<Character, TrieNode> entry : node.children.entrySet()) {
            char edgeChar = entry.getKey();
            soFar.append(edgeChar);

            int costHere = (edgeChar == target[targetIndex]) ? 0 : 1; // match costs 0; substitute costs 1
            suggest(entry.getValue(), target, targetIndex + 1, editsUsed + costHere, maxEdits, soFar, results);

            suggest(entry.getValue(), target, targetIndex, editsUsed + 1, maxEdits, soFar, results); // delete a target char
            soFar.deleteCharAt(soFar.length() - 1);
        }
    }

    static List<String> suggestCorrections(Dictionary dict, String misspelled, int maxEdits) {
        List<String> results = new ArrayList<>();
        suggest(dict.root, misspelled.toCharArray(), 0, 0, maxEdits, new StringBuilder(), results);
        return new ArrayList<>(new java.util.LinkedHashSet<>(results)); // de-duplicate: multiple edit paths can reach the same word
    }

    static void intermediateLevel() {
        Dictionary dict = new Dictionary();
        for (String w : new String[]{"cat", "cot", "cart"}) dict.insert(w);

        List<String> suggestions = suggestCorrections(dict, "ct", 1);
        java.util.Collections.sort(suggestions);
        System.out.println("intermediate: suggestions for \"ct\" within 1 edit -> " + suggestions);
    }

    static void advancedLevel() {
        Dictionary dict = new Dictionary();
        for (String w : new String[]{"cat", "cot", "cart", "dog"}) dict.insert(w);

        List<String> suggestions = suggestCorrections(dict, "ct", 2);
        java.util.Collections.sort(suggestions);
        System.out.println("advanced: suggestions for \"ct\" within 2 edits -> " + suggestions + " (now 'cart' is reachable too)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `SpellCheck.java`, then run `java SpellCheck.java`.

## 6. Walkthrough

1. `basicLevel()` checks `"cat"` (correctly spelled, since it was inserted) and `"ct"` (not spelled correctly — no such word was ever inserted, and the walk actually fails partway since there is no direct `c -> t` edge).
2. `intermediateLevel()` calls `suggestCorrections(dict, "ct", 1)`. The search tries matching `c` against the target's `c` (cost 0), then at the next trie level, tries each child against the target's `t`: `a` and `o` both cost 1 substitution each (`a != t`, `o != t`), landing exactly on `"cat"` and `"cot"`'s end-of-word nodes with `editsUsed = 1`, within budget. The `"cart"` branch would need an insertion plus a substitution plus another insertion — more than 1 edit — so it gets pruned before it can complete.
3. `advancedLevel()` raises the budget to 2 edits, which now admits `"cart"`: matching `c` (cost 0), inserting past `a` (cost 1, skipping a trie character with target's `t` still pending), substituting `r` for `t` (cost 2)... the search explores multiple such paths, and any path landing on an `isEndOfWord` node within the 2-edit budget contributes `"cart"` to the results.

## 7. Gotchas & takeaways

> Gotcha: multiple different edit paths can reach the same dictionary word (e.g. "substitute then match" versus "match then substitute" landing on the same node) — deduplicate the results, or a single close match can appear many times in the suggestion list.

- Exact spell-check is just the trie's `search` operation — walk the string, check `isEndOfWord`.
- Suggesting corrections searches the *trie itself*, not the dictionary as a flat list, tracking an edit budget and pruning any branch that exceeds it.
- Pruning is what makes this efficient — once a branch's edit count exceeds the budget, its entire remaining subtree is skipped in one step.
- Related concepts: [Insert / search / startsWith](0129-insert-search-startswith.md), [Autocomplete & prefix queries](0130-autocomplete-prefix-queries.md).
