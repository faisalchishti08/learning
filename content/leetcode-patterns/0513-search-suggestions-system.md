---
card: leetcode-patterns
gi: 513
slug: search-suggestions-system
title: Search Suggestions System
---

## 1. What it is

Given an array of `products` and a `searchWord`, return a list of lists: for each prefix of `searchWord` typed so far (one character at a time), return up to 3 lexicographically smallest products that start with that prefix. Example: `products = ["mobile","mouse","moneypot","monitor","mousepad"]`, `searchWord = "mouse"` → suggestions grow as each letter of "mouse" is typed, ending with `["mouse","mousepad"]` for the full word.

## 2. Why & when

"Products starting with a given (growing) prefix, smallest first" is a direct trie autocomplete use case, from the [trie signal](0505-trie-signal-prefix-search-word-dictionaries-or-bit-tries.md) family. Storing the top-3 candidates directly at each trie node (kept sorted as you insert) turns every prefix query into an O(1) lookup after the trie is built. Constraints: up to 1000 products, `searchWord` up to 1000 characters.

## 3. Core concept

**Key idea:** sort `products` alphabetically first. Insert each product into a trie, but at every node along its path, append the product to that node's list of suggestions — only if the list has fewer than 3 entries (since products are inserted in sorted order, the first 3 to reach any node are automatically the 3 lexicographically smallest with that prefix). Then, for each prefix of `searchWord`, walk the trie and read off the current node's stored suggestion list directly.

**Steps:**
1. Sort `products` alphabetically.
2. Build a trie; for each product, walk its characters, and at every node visited, add the product to that node's suggestion list if the list has fewer than 3 entries.
3. For each prefix length from 1 to `searchWord.length()`, walk the trie that far; if the path exists, read the current node's suggestion list; if the path breaks at any point, every remaining prefix has no matches (empty lists for the rest).
4. Collect all these lists as the answer.

**Why sorting before inserting avoids a separate sort per query:** since products are inserted in already-sorted order, the first (at most) 3 products to reach a given node are guaranteed to be the 3 smallest with that prefix — no need to sort or filter the results afterward, at query time.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each trie node accumulating up to 3 sorted suggestions as products are inserted in order">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">sorted products: mobile, moneypot, monitor, mouse, mousepad</text>
    <text x="20" y="45" fill="#8b949e">node "m": first 3 inserted -&gt; [mobile, moneypot, monitor]</text>
    <text x="20" y="65" fill="#8b949e">node "mo": same first 3 -&gt; [mobile, moneypot, monitor]</text>
    <text x="20" y="85" fill="#8b949e">node "mou": only mouse, mousepad reach here -&gt; [mouse, mousepad]</text>
    <text x="20" y="115" fill="#3fb950">query prefix "mou" reads that node's list directly: [mouse, mousepad]</text>
  </g>
</svg>

Inserting in sorted order means the first 3 arrivals at each node are already the correct answer.

## 5. Runnable example

```java
// SearchSuggestionsSystem.java
import java.util.*;

public class SearchSuggestionsSystem {

    static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        List<String> suggestions = new ArrayList<>();
    }

    static List<List<String>> suggestedProducts(String[] products, String searchWord) {
        Arrays.sort(products);
        TrieNode root = new TrieNode();

        for (String product : products) {
            TrieNode node = root;
            for (char c : product.toCharArray()) {
                int index = c - 'a';
                if (node.children[index] == null) node.children[index] = new TrieNode();
                node = node.children[index];
                if (node.suggestions.size() < 3) {
                    node.suggestions.add(product);
                }
            }
        }

        List<List<String>> result = new ArrayList<>();
        TrieNode node = root;
        boolean pathBroken = false;
        for (char c : searchWord.toCharArray()) {
            int index = c - 'a';
            if (!pathBroken && node.children[index] != null) {
                node = node.children[index];
                result.add(node.suggestions);
            } else {
                pathBroken = true;
                result.add(new ArrayList<>());
            }
        }
        return result;
    }

    public static void main(String[] args) {
        String[] products = {"mobile", "mouse", "moneypot", "monitor", "mousepad"};
        List<List<String>> suggestions = suggestedProducts(products, "mouse");
        for (List<String> level : suggestions) {
            System.out.println(level);
        }
    }
}
```

**How to run:** save as `SearchSuggestionsSystem.java`, then run `java SearchSuggestionsSystem.java`.

## 6. Walkthrough

Sorted products: `["mobile", "moneypot", "monitor", "mouse", "mousepad"]`. Typing `"mouse"` one letter at a time:

| prefix typed | trie node reached | suggestions stored (first 3 to arrive) |
|---|---|---|
| m | m | [mobile, moneypot, monitor] |
| mo | mo | [mobile, moneypot, monitor] |
| mou | mou | [mouse, mousepad] |
| mous | mous | [mouse, mousepad] |
| mouse | mouse | [mouse, mousepad] |

The final answer is these five lists, matching the expected progressive suggestions as `"mouse"` is typed character by character.

## 7. Gotchas & takeaways

> Gotcha: inserting products in unsorted order and taking "the first 3 to reach a node" would not give the 3 lexicographically smallest — sorting `products` before inserting is what guarantees the stored suggestions are correctly ordered.

- Storing suggestions directly at each trie node during insertion (capped at 3) avoids any sorting or filtering work at query time.
- Once the trie path breaks (a prefix has no matching products), every longer prefix also has no matches — the remaining result lists are all empty.
- Time: O(products · average length) to build the trie, O(searchWord length) to answer all prefix queries.
