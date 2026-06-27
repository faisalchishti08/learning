import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import topics

PROJ = {
    "file": "webdev.html",
    "sections": [
        {"name": "HTML", "tag": "html", "groups": [
            {"g": "Basics", "items": ["The <!DOCTYPE> declaration", "Semantic elements"]}]},
        {"name": "CSS", "tag": "css", "groups": [
            {"g": "Layout", "items": ["Flexbox: justify-content"]}]},
    ],
}

class TestTopics(unittest.TestCase):
    def test_slugify_basic(self):
        self.assertEqual(topics.slugify("Semantic elements"), "semantic-elements")

    def test_slugify_strips_html_and_symbols(self):
        self.assertEqual(topics.slugify("The <!DOCTYPE> declaration"), "the-doctype-declaration")

    def test_slugify_never_empty(self):
        self.assertEqual(topics.slugify("<<>>"), "topic")

    def test_enumerate_gi_is_sequential_per_card(self):
        ts = topics.enumerate_topics(PROJ)
        self.assertEqual([t["gi"] for t in ts], [1, 2, 3])
        self.assertEqual(ts[2]["section"], "CSS")
        self.assertEqual(ts[2]["slug"], "flexbox-justify-content")

    def test_card_stem(self):
        self.assertEqual(topics.card_stem(PROJ), "webdev")

    def test_page_path_zero_pads(self):
        self.assertEqual(topics.page_path("webdev", 7, "semantic-elements"),
                         "tutorials/webdev/0007-semantic-elements.html")

if __name__ == "__main__":
    unittest.main()
