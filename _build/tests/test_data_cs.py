import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import data_cs, topics, generate

STEMS = ["system-design", "data-structures", "leetcode-patterns"]

def by_stem():
    return {topics.card_stem(p): p for p in data_cs.PROJECTS}

class TestMetadata(unittest.TestCase):
    def test_three_projects(self):
        self.assertEqual(len(data_cs.PROJECTS), 3)

    def test_files_and_logos(self):
        m = by_stem()
        self.assertEqual(set(m), set(STEMS))
        self.assertEqual(m["system-design"]["logo"], "SD")
        self.assertEqual(m["data-structures"]["logo"], "DS")
        self.assertEqual(m["leetcode-patterns"]["logo"], "LC")

    def test_category_is_cs_interview_prep(self):
        for p in data_cs.PROJECTS:
            self.assertEqual(p["cat"], "CS & Interview Prep")

    def test_required_keys_and_types(self):
        for p in data_cs.PROJECTS:
            for k in ("file", "title", "logo", "cat", "subtitle", "sections"):
                self.assertIn(k, p)
            self.assertIsInstance(p["sections"], list)

    def test_registered_in_generator_after_java_before_webdev_and_core(self):
        files = [p["file"] for p in generate.PROJECTS]
        self.assertIn("system-design.html", files)
        self.assertIn("data-structures.html", files)
        self.assertIn("leetcode-patterns.html", files)
        java = files.index("java.html")
        sd = files.index("system-design.html")
        wd = files.index("webdev.html")
        # first data_core file is spring-framework.html
        core = files.index("spring-framework.html")
        self.assertLess(java, sd)
        self.assertLess(sd, wd)
        self.assertLess(sd, core)

class TestStructuralInvariants(unittest.TestCase):
    """Runs for whatever sections exist; tightened as later tasks add content."""
    def test_items_are_nonempty_strings(self):
        for p in data_cs.PROJECTS:
            for s in p["sections"]:
                self.assertIsInstance(s["name"], str)
                for g in s["groups"]:
                    self.assertTrue(g["items"])
                    for it in g["items"]:
                        self.assertIsInstance(it, str)
                        self.assertTrue(it.strip())

    def test_section_tags_unique_per_subject(self):
        for p in data_cs.PROJECTS:
            tags = [s["tag"] for s in p["sections"]]
            self.assertEqual(len(tags), len(set(tags)), p["file"])

    def test_slugs_unique_per_subject(self):
        for p in data_cs.PROJECTS:
            if not p["sections"]:
                continue
            slugs = [t["slug"] for t in topics.enumerate_topics(p)]
            dupes = sorted({s for s in slugs if slugs.count(s) > 1})
            self.assertEqual(dupes, [], "%s dup slugs: %s" % (p["file"], dupes))

class TestSystemDesign(unittest.TestCase):
    def sd(self):
        return by_stem()["system-design"]

    def test_has_21_sections(self):
        self.assertEqual(len(self.sd()["sections"]), 21)

    def test_concept_and_usecase_tags_present(self):
        tags = [s["tag"] for s in self.sd()["sections"]]
        for t in ("fundamentals", "caching", "consistency", "resiliency",
                  "api-design", "use-cases"):
            self.assertIn(t, tags)

    def test_usecase_section_has_29_designs_each_9_steps(self):
        uc = [s for s in self.sd()["sections"] if s["tag"] == "use-cases"][0]
        self.assertEqual(len(uc["groups"]), 29)
        for g in uc["groups"]:
            self.assertEqual(len(g["items"]), 9)
            self.assertTrue(g["items"][-1].endswith("Spring/Java implementation approach"))

    def test_total_topic_count_floor(self):
        # 20 concept sections * multiple groups + 29*9 use-case items
        n = len(topics.enumerate_topics(self.sd()))
        self.assertGreaterEqual(n, 450)

class TestDataStructures(unittest.TestCase):
    def ds(self):
        return by_stem()["data-structures"]

    def test_has_16_sections(self):
        self.assertEqual(len(self.ds()["sections"]), 16)

    def test_expected_tags_present(self):
        tags = [s["tag"] for s in self.ds()["sections"]]
        for t in ("foundations", "arrays", "linked-lists", "hashing", "trees",
                  "heaps", "tries", "graphs", "union-find", "jcf"):
            self.assertIn(t, tags)

    def test_java_implementation_group_common(self):
        # most structure sections carry a Java-implementation group
        hits = 0
        for s in self.ds()["sections"]:
            if any("Java" in g["g"] for g in s["groups"]):
                hits += 1
        self.assertGreaterEqual(hits, 8)

    def test_total_topic_count_floor(self):
        n = len(topics.enumerate_topics(self.ds()))
        self.assertGreaterEqual(n, 200)


class TestLeetCode(unittest.TestCase):
    def lc(self):
        return by_stem()["leetcode-patterns"]

    def test_min_pattern_count(self):
        self.assertGreaterEqual(len(self.lc()["sections"]), 35)

    def test_expected_tags_present(self):
        tags = [s["tag"] for s in self.lc()["sections"]]
        for t in ("two-pointers", "sliding-window", "backtracking",
                  "dp-01-knapsack", "topo-sort", "trie"):
            self.assertIn(t, tags)

    def test_each_pattern_has_concept_group_and_problems(self):
        for s in self.lc()["sections"]:
            names = [g["g"].lower() for g in s["groups"]]
            self.assertTrue(any("pattern" in n or "when" in n for n in names),
                            "%s missing concept group" % s["tag"])
            problem_items = sum(len(g["items"]) for g in s["groups"]
                                if "pattern" not in g["g"].lower()
                                and "when" not in g["g"].lower())
            self.assertGreaterEqual(problem_items, 8, "%s < 8 problems" % s["tag"])

    def test_total_problem_count_floor(self):
        # Curated, duplicate-free set across 36 patterns (concept items + named problems).
        n = len(topics.enumerate_topics(self.lc()))
        self.assertGreaterEqual(n, 620)


class TestGeneratedOutput(unittest.TestCase):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def read(self, name):
        with open(os.path.join(self.ROOT, name), encoding="utf-8") as f:
            return f.read()

    def test_subject_pages_exist_and_titled(self):
        self.assertIn("System Design", self.read("system-design.html"))
        self.assertIn("Data Structures", self.read("data-structures.html"))
        self.assertIn("LeetCode Patterns", self.read("leetcode-patterns.html"))

    def test_index_has_category_and_three_cards(self):
        idx = self.read("index.html")
        self.assertIn("CS & Interview Prep", idx)
        self.assertIn('href="system-design.html"', idx)
        self.assertIn('href="data-structures.html"', idx)
        self.assertIn('href="leetcode-patterns.html"', idx)

    def test_manifest_lists_new_cards(self):
        import json
        man = json.loads(self.read("content/_manifest.json"))
        for stem in ("system-design", "data-structures", "leetcode-patterns"):
            self.assertIn(stem, man["cards"])


if __name__ == "__main__":
    unittest.main()
