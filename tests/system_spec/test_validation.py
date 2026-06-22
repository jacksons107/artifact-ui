import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from system_spec.validation import parse_spec

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "system_spec" / "examples"


def load_example(name: str) -> dict:
    return json.loads((EXAMPLES_DIR / f"{name}.json").read_text())


class TestExamplesStillParse(unittest.TestCase):
    def test_all_examples_still_parse(self):
        for path in sorted(EXAMPLES_DIR.glob("*.json")):
            with self.subTest(example=path.stem):
                data = json.loads(path.read_text())
                parse_spec(data)


class TestSchemaLayerDoesNotChangeAcceptReject(unittest.TestCase):
    def setUp(self):
        self.base = {
            "nodes": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
            "edges": [{"from": "a", "to": "b"}],
        }

    def test_missing_node_id(self):
        data = copy.deepcopy(self.base)
        data["nodes"].append({"label": "no id"})
        with self.assertRaises(ValueError):
            parse_spec(data)

    def test_missing_node_label(self):
        data = copy.deepcopy(self.base)
        data["nodes"].append({"id": "c"})
        with self.assertRaises(ValueError):
            parse_spec(data)

    def test_duplicate_node_id(self):
        data = copy.deepcopy(self.base)
        data["nodes"].append({"id": "a", "label": "Duplicate"})
        with self.assertRaises(ValueError):
            parse_spec(data)

    def test_edge_to_unknown_node(self):
        data = copy.deepcopy(self.base)
        data["edges"].append({"from": "a", "to": "nonexistent"})
        with self.assertRaises(ValueError):
            parse_spec(data)

    def test_single_member_group(self):
        data = copy.deepcopy(self.base)
        data["groups"] = [{"id": "g", "label": "G", "members": ["a"]}]
        with self.assertRaises(ValueError):
            parse_spec(data)

    def test_group_self_membership(self):
        data = copy.deepcopy(self.base)
        data["groups"] = [{"id": "g", "label": "G", "members": ["g", "a"]}]
        with self.assertRaises(ValueError):
            parse_spec(data)

    def test_multi_parent_violation(self):
        data = copy.deepcopy(self.base)
        data["groups"] = [
            {"id": "g1", "label": "G1", "members": ["a", "b"]},
            {"id": "g2", "label": "G2", "members": ["a", "b"]},
        ]
        with self.assertRaises(ValueError):
            parse_spec(data)

    def test_group_cycle(self):
        data = copy.deepcopy(self.base)
        data["groups"] = [
            {"id": "g1", "label": "G1", "members": ["g2", "a"]},
            {"id": "g2", "label": "G2", "members": ["g1", "b"]},
        ]
        with self.assertRaises(ValueError):
            parse_spec(data)

    def test_clone_of_unknown_source(self):
        data = copy.deepcopy(self.base)
        data["groups"] = [{"id": "g", "label": "G", "clone_of": "nonexistent"}]
        with self.assertRaises(ValueError):
            parse_spec(data)

    def test_clone_of_chaining_rejected(self):
        data = {
            "nodes": [
                {"id": "cell_a_worker", "label": "Worker"},
                {"id": "cell_a_db", "label": "DB"},
            ],
            "groups": [
                {"id": "cell_a", "label": "Cell A", "members": ["cell_a_worker", "cell_a_db"]},
                {"id": "cell_b", "label": "Cell B", "clone_of": "cell_a"},
                {"id": "cell_c", "label": "Cell C", "clone_of": "cell_b"},
            ],
        }
        with self.assertRaises(ValueError):
            parse_spec(data)

    def test_clone_of_unprefixed_nested_id(self):
        data = {
            "nodes": [
                {"id": "worker", "label": "Worker"},
                {"id": "db", "label": "DB"},
            ],
            "groups": [
                {"id": "cell_a", "label": "Cell A", "members": ["worker", "db"]},
                {"id": "cell_b", "label": "Cell B", "clone_of": "cell_a"},
            ],
        }
        with self.assertRaises(ValueError):
            parse_spec(data)

    def test_no_nodes(self):
        with self.assertRaises(ValueError):
            parse_spec({"nodes": []})


class TestCloneOfFieldAllowedPreResolution(unittest.TestCase):
    def test_clone_of_passes_schema_validation(self):
        data = {
            "nodes": [
                {"id": "cell_a_worker", "label": "Worker"},
                {"id": "cell_a_db", "label": "DB"},
            ],
            "groups": [
                {"id": "cell_a", "label": "Cell A", "members": ["cell_a_worker", "cell_a_db"], "kind": "deployment"},
                {"id": "cell_b", "label": "Cell B", "clone_of": "cell_a", "kind": "deployment"},
            ],
        }
        spec = parse_spec(data)
        self.assertIn("cell_b_worker", spec["node_ids"])


if __name__ == "__main__":
    unittest.main()
