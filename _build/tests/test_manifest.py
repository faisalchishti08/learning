import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import manifest

def make_project(n_html, n_css):
    return {
        "file": "webdev.html", "title": "Web Development",
        "sections": [
            {"name": "HTML", "tag": "html", "groups": [
                {"g": "G", "items": ["h%d" % i for i in range(n_html)]}]},
            {"name": "CSS", "tag": "css", "groups": [
                {"g": "G", "items": ["c%d" % i for i in range(n_css)]}]},
        ],
    }

class TestManifest(unittest.TestCase):
    def test_splits_into_phase_cap(self):
        proj = make_project(30, 5)   # HTML must split 12/12/6
        m = manifest.build([proj], lambda p: False)
        phases = m["cards"]["webdev"]["sections"][0]["phases"]
        self.assertEqual([len(p["gis"]) for p in phases], [12, 12, 6])

    def test_next_phase_is_first_pending(self):
        proj = make_project(3, 3)
        # mark all HTML pages (gi 1..3) as existing -> next is CSS phase
        done = {"tutorials/webdev/0001-h0.html", "tutorials/webdev/0002-h1.html",
                "tutorials/webdev/0003-h2.html"}
        m = manifest.build([proj], lambda p: p in done)
        self.assertEqual(m["next_phase"], "webdev/css#1")

    def test_topic_status_reflects_existence(self):
        proj = make_project(2, 0)
        done = {"tutorials/webdev/0001-h0.html"}
        m = manifest.build([proj], lambda p: p in done)
        ts = m["cards"]["webdev"]["sections"][0]["topics"]
        self.assertEqual(ts[0]["status"], "done")
        self.assertEqual(ts[1]["status"], "pending")

    def test_all_done_next_phase_none(self):
        proj = make_project(1, 0)
        m = manifest.build([proj], lambda p: True)
        self.assertIsNone(m["next_phase"])

if __name__ == "__main__":
    unittest.main()
