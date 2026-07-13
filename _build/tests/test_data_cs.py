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

    def test_registered_in_generator_after_webdev_before_core(self):
        files = [p["file"] for p in generate.PROJECTS]
        self.assertIn("system-design.html", files)
        self.assertIn("data-structures.html", files)
        self.assertIn("leetcode-patterns.html", files)
        wd = files.index("webdev.html")
        sd = files.index("system-design.html")
        # first data_core file is spring-framework.html
        core = files.index("spring-framework.html")
        self.assertLess(wd, sd)
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

if __name__ == "__main__":
    unittest.main()
