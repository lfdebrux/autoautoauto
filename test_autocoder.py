#!/usr/bin/env python3

import unittest

from fom import Federate, FOM, Interaction
from autocoder import name_re, attribute_walker, find_list_property


class ReTester(unittest.TestCase):

    def assertSearchGroupsEqual(self, string, groups):
        self.assertEqual(
            name_re.search(string).groupdict(),
            groups
        )

    def test_truthiness(self):
        match = name_re.search('cheeseshop')
        self.assertFalse(match)
        match = name_re.search('{parameter.name}')
        self.assertTrue(match)

    def test_empty(self):
        self.assertFalse(name_re.search('{}'))

    def test_groups(self):
        self.assertSearchGroupsEqual(
            '{parameter.name}',
            {'basename': 'name', 'path': 'parameter.name',
             'pathname': 'parameter', 'root': 'parameter'})
        self.assertSearchGroupsEqual(
            '{federation.interaction.parameter.name}',
            {'basename': 'name', 'root': 'federation',
             'path': 'federation.interaction.parameter.name',
             'pathname': 'federation.interaction.parameter'})

    def test_single_line_multiple_match(self):
        match = list(name_re.finditer('{interaction.name} {parameter.name}'))
        self.assertEqual(len(match), 2)
        self.assertEqual(match[0].groupdict(),
                         {'basename': 'name', 'path': 'interaction.name',
                          'pathname': 'interaction', 'root': 'interaction'})
        self.assertEqual(match[1].groupdict(),
                         {'basename': 'name', 'path': 'parameter.name',
                          'pathname': 'parameter', 'root': 'parameter'})


class PropertyWalkerTester(unittest.TestCase):

    federate = Federate(
        "Federate", FOM("FuelEconomyBase.xml"),
        Interaction("LoadScenario", "ScenarioName", "InitialFuelAmount"),
        Interaction("Start", "TimeScaleFactor"))

    def assertWalkEqual(self, path, result):
        self.assertEqual(
            list(attribute_walker(self.federate, path.split('.'))), result)

    def test_property_walk(self):
        self.assertWalkEqual(
            'interactions.parameters.name',
            ['ScenarioName', 'InitialFuelAmount', 'TimeScaleFactor'])

    def test_object_walk(self):
        path = 'interactions.parameters'
        result = list(
            map(str, attribute_walker(self.federate, path.split('.'))))
        expected = list(map(str, [self.federate.interactions[0].parameters[0],
                                  self.federate.interactions[0].parameters[1],
                                  self.federate.interactions[1].parameters[0]])
                        )
        self.assertEqual(result, expected)
        self.assertWalkEqual(path,
                             [self.federate.interactions[0].parameters[0],
                              self.federate.interactions[0].parameters[1],
                              self.federate.interactions[1].parameters[0]])


class FindListPropertyTester(unittest.TestCase):

    ns = {'federate': Federate(
        "Federate", FOM("FuelEconomyBase.xml"),
        Interaction("LoadScenario", "ScenarioName", "InitialFuelAmount"),
        Interaction("Start", "TimeScaleFactor"))}

    def test_find_list_property(self):
        self.assertEqual(
            find_list_property(self.ns, 'interaction'),
            'federate.interactions')
        self.assertEqual(
            find_list_property(self.ns, 'parameter'),
            'federate.interactions.parameters')


if __name__ == '__main__':
    unittest.main()
