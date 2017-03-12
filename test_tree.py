
import unittest

import tree

test_tree = {
    "federate": {
        "classname": "Federate",
        "fom": ["FuelEconomyBase.xml"],
        "interactions": [
            {"name": "LoadScenario",
                "parameters": [{"name": "ScenarioName",
                                "datatype": "HLAUnicodeString",
                                "representation": "HLAUnicodeString"},
                               {"name": "InitialFuelAmount",
                                "datatype": "FuelInt32",
                                "representation": "HLAinteger32BE"}]},
            {"name": "Start",
                "parameters": [{"name": "TimeScaleFactor",
                                "datatype": "ScaleFactorFloat32e",
                                "representation": "HLAfloat32BE"}]}
        ]
    }
}


class BranchesTest(unittest.TestCase):

    t = test_tree

    def assertResultLength(self, path, length):
        self.assertEqual(len(tree.branches(self.t, path)), length)

    def assertContainsPath(self, path):
        result = tree.branches(self.t, path)
        for e in path:
            for subtree in result:
                self.assertIn(subtree, result)

    def test_len(self):
        self.assertResultLength(('federate',), 1)
        self.assertResultLength(('federate', 'interactions'), 2)
        self.assertResultLength(('federate', 'interactions', 'parameters'), 3)

    def test_has_path_elements(self):
        self.assertContainsPath(('federate',))
        self.assertContainsPath(('federate', 'interactions'))

if __name__ == '__main__':
    unittest.main()
