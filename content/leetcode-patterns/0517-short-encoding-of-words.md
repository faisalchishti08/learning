---
card: leetcode-patterns
gi: 517
slug: short-encoding-of-words
title: Short Encoding of Words
---

## 1. What it is

Given a list of `words`, find the length of the shortest reference string `s` that can encode all of them: `s` ends with `#`, and every word can be found as a suffix of some segment of `s` (segments are separated by `#`). Words that are suffixes of other words do not need their own separate encoding. Example: `words = ["time", "me", "bell"]` → `10` (encode as `"time#bell#"`; `"me"` is a suffix of `"time"`, so it is not encoded separately).

## 2. Why & when

"Is this word a suffix of another word" is a prefix question in reverse — reverse every word, and a suffix relationship becomes a prefix relationship, which a trie answers naturally, from the [trie signal](0505-trie-signal-prefix-search-word-dictionaries-or-bit-tries.md) family. A word needs no separate encoding exactly when it is a suffix of some other word, i.e. when its **reversed** form is a strict prefix of another reversed word. Constraints: up to 2000 words, each up to 7 characters.

## 3. Core concept

**Key idea:** reverse every word and insert all the reversed words into a trie. A word only needs its own encoding if its reversed form is **not** a strict prefix of any other reversed word — equivalently, if its trie node (after insertion) has no children (it is a leaf). Sum `word.length() + 1` (for the `#` separator) over every word whose reversed node is a leaf.

**Steps:**
1. Reverse every word and insert it into a trie, tracking which original word ends at each node.
2. After all insertions, for each word, check whether its reversed form's end node has any children in the trie.
3. If it has no children, this word is not a suffix of any other word, so it needs its own encoding: add `word.length() + 1` to the total.
4. If it does have children, some other (longer) word has this word as a suffix, so this word is already covered — skip it.
5. Return the total.

**Why reversing turns "is a suffix of" into "is a prefix of" (a trie's native strength):** a trie is built to answer prefix questions efficiently, walking from the root downward. Suffix relationships read from the *end* of a string backward — reversing every word before insertion realigns "suffix of" with the trie's natural root-to-leaf direction, letting the same structure answer both kinds of question.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reversed words inserted into a trie; only leaf nodes need their own encoding">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">words = [time, me, bell]. reversed = [emit, em, lleb]</text>
    <text x="20" y="45" fill="#8b949e">insert "emit": e -&gt; m -&gt; i -&gt; t (leaf)</text>
    <text x="20" y="65" fill="#8b949e">insert "em": e -&gt; m (this node now HAS a child 'i', so "em" is NOT a leaf)</text>
    <text x="20" y="90" fill="#3fb950">"me" (reversed "em") is a prefix of "emit" -&gt; "me" needs no separate encoding</text>
    <text x="20" y="115" fill="#8b949e">insert "lleb": separate branch, ends as a leaf -&gt; "bell" needs its own encoding</text>
    <text x="20" y="140" fill="#3fb950">total: (time#=5) + (bell#=5) = 10. "me" contributes nothing.</text>
  </g>
</svg>

A word's reversed form ending at a leaf (no children) means it needs its own encoding; ending mid-path means it is already covered.

## 5. Runnable example

```java
// ShortEncodingOfWords.java
import java.util.*;

public class ShortEncodingOfWords {

    static class TrieNode {
        TrieNode[] children = new TrieNode[26];
    }

    static int minimumLengthEncoding(String[] words) {
        TrieNode root = new TrieNode();
        Map<TrieNode, Integer> endNodeToLength = new HashMap<>();

        for (String word : words) {
            TrieNode node = root;
            for (int i = word.length() - 1; i >= 0; i--) {
                int index = word.charAt(i) - 'a';
                if (node.children[index] == null) node.children[index] = new TrieNode();
                node = node.children[index];
            }
            endNodeToLength.put(node, word.length());
        }

        int total = 0;
        for (Map.Entry<TrieNode, Integer> entry : endNodeToLength.entrySet()) {
            boolean isLeaf = true;
            for (TrieNode child : entry.getKey().children) {
                if (child != null) { isLeaf = false; break; }
            }
            if (isLeaf) total += entry.getValue() + 1;
        }
        return total;
    }

    public static void main(String[] args) {
        System.out.println(minimumLengthEncoding(new String[]{"time", "me", "bell"})); // 10
        System.out.println(minimumLengthEncoding(new String[]{"t"}));                  // 2
        System.out.println(minimumLengthEncoding(new String[]{"me", "time"}));         // 5 (order doesn't matter)
    }
}
```

**How to run:** save as `ShortEncodingOfWords.java`, then run `java ShortEncodingOfWords.java`.

## 6. Walkthrough

For `words = ["time", "me", "bell"]`, reversed: `"emit"`, `"em"`, `"lleb"`.

| word | reversed | end node's children | leaf? | contributes |
|---|---|---|---|---|
| time | emit | none (last char 't' in reverse) | yes | 4+1=5 |
| me | em | has child 'i' (from "emit") | no | 0 |
| bell | lleb | none | yes | 4+1=5 |

Total: `5 + 0 + 5 = 10`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: using a `Set<TrieNode>` of end nodes without mapping back to each word's length (or forgetting duplicate words entirely map to the same node) can double-count or miscompute — storing `end node -> word length` in a map, keyed by node identity, naturally deduplicates identical words too.

- Reversing every word before inserting turns "is a suffix of" into "is a prefix of," which a trie answers directly by checking whether an end node has children.
- Only leaf end-nodes (no children) contribute to the encoding; non-leaf end-nodes are suffixes of some longer word already in the trie.
- Time: O(total characters across all words) to build the trie and check leaf status for every word.
