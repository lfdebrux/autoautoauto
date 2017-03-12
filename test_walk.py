#!/usr/bin/env python3

import unittest

from fom import Federate, FOM, Interaction
from autocoder import walk, parse
# from hla_autocoder import walk, parse


class WalkTester(unittest.TestCase):

    federate = Federate(
        "Federate", FOM("FuelEconomyBase.xml"),
        Interaction("LoadScenario", "ScenarioName", "InitialFuelAmount"),
        Interaction("Start", "TimeScaleFactor"))

    def test(self):
        result = walk(self.federate, self.input)
        self.assertEqual(result, self.output)


class ParseTester(unittest.TestCase):

    federate = Federate(
        "Federate", FOM("FuelEconomyBase.xml"),
        Interaction("LoadScenario", "ScenarioName", "InitialFuelAmount"),
        Interaction("Start", "TimeScaleFactor"))

    def test(self):
        result = parse(self.federate, self.input)
        self.assertEqual(result, self.output)


class NullWalkTest(WalkTester):
    input = []
    output = []


class NullParseTest(ParseTester):
    input = ''
    output = ''


class FederateTestCase(WalkTester):
    input = ['{federate.classname}']
    output = ['Federate']


class InteractionTestCase(WalkTester):
    input = ['{interaction.varname}']
    output = ['loadScenario', 'start']


class ParameterTestCase(WalkTester):
    input = ['{parameter.varname}']
    output = ['scenarioName', 'initialFuelAmount', 'timeScaleFactor']


class RecursionTestCase(WalkTester):
    input = [
        '{interaction.varname}',
        '{parameter.varname}'
    ]

    output = [
        'loadScenario', 'scenarioName', 'initialFuelAmount',
        '\n',
        'start', 'timeScaleFactor'
    ]


class FederateTestCase2(WalkTester):
    input = [
        '#include "RTI/NullFederate.h"',
        '',
        '{federate.classname}::{federate.classname}()'
    ]

    output = [
        '#include "RTI/NullFederate.h"',
        '',
        'Federate::Federate()'
    ]


@unittest.skip("Not yet implemented")
class PublisherImplicitIterations(WalkTester):
    federate = Federate(
        "Federate", FOM("FuelEconomyBase.xml"),
        Interaction("LoadScenario", "ScenarioName", "InitialFuelAmount"),
        # Interaction("ScenarioLoaded", PUBLISH, "FederateName"),
        # Interaction("ScenarioLoadFailure", PUBLISH, "FederateName", "ErrorMessage"),
        Interaction("Start", "TimeScaleFactor"))

    input = [
        'void LocomotionWriter::publishInteractions()',
        '{',
        '  _rtiAmbassador->publishInteractionClass({publisher.handlename});',
        '}',
    ]

    output = [
        'void LocomotionWriter::publishInteractions()',
        '{',
        '  _rtiAmbassador->publishInteractionClass(SetVehicleMotionHandle);',
        '}',
    ]


@unittest.skip("feature not yet implemented")
class InteractionLineTestCase(WalkTester):
    input = [
        'void {interaction.callbackname}({interaction.callback_arguments_define});'
    ]

    output = [
        'void loadScenarioCallback(std::wstring scenarioName, Integer32 initialFuelAmount);',
        '\n',
        'void startCallback(float timeScaleFactor);'
    ]


class InteractionAndParameterTestCase(WalkTester):
    input = [
        '{interaction.handlename} = rti.getInteractionClassHandle({interaction.literalname});',
        '{parameter.handlename} = rti.getParameterHandle({interaction.handlename}, {parameter.literalname});',
    ]

    output = [
        'loadScenarioHandle = rti.getInteractionClassHandle(L"HLAinteractionRoot.LoadScenario");',
        'scenarioNameHandle = rti.getParameterHandle(loadScenarioHandle, L"ScenarioName");',
        'initialFuelAmountHandle = rti.getParameterHandle(loadScenarioHandle, L"InitialFuelAmount");',
        '\n',
        'startHandle = rti.getInteractionClassHandle(L"HLAinteractionRoot.Start");',
        'timeScaleFactorHandle = rti.getParameterHandle(startHandle, L"TimeScaleFactor");',
    ]


class ParseTestCase3(ParseTester):
    input = \
'''
//* {federate.classname}.cpp *//

#include "{federate.classname}.h"

{federate.classname}::{federate.classname}()
{
  std::vector<std::wstring> fomURLs({federate.fom.filenames_literal});

  rti.joinFederationExecution(L"", fomUrls, L"", L"");

  {interaction.handlename} = rti.getInteractionClassHandle({interaction.literalname});
  {parameter.handlename} = rti.getParameterHandle({interaction.handlename}, {parameter.literalname});
}

'''

    output = \
'''
//* Federate.cpp *//

#include "Federate.h"

Federate::Federate()
{
  std::vector<std::wstring> fomURLs({ L"FuelEconomyBase.xml" });

  rti.joinFederationExecution(L"", fomUrls, L"", L"");

  loadScenarioHandle = rti.getInteractionClassHandle(L"HLAinteractionRoot.LoadScenario");
  scenarioNameHandle = rti.getParameterHandle(loadScenarioHandle, L"ScenarioName");
  initialFuelAmountHandle = rti.getParameterHandle(loadScenarioHandle, L"InitialFuelAmount");

  startHandle = rti.getInteractionClassHandle(L"HLAinteractionRoot.Start");
  timeScaleFactorHandle = rti.getParameterHandle(startHandle, L"TimeScaleFactor");
}

'''


class ParseTestCase4(ParseTester):
    input = '''
//* {federate.classname}.h *//

#include "RTI/NullFederate.h"

using namespace rti1516e;

class {federate.classname} : public NullFederate
{
private:
  {interaction.handle_define};
  {parameter.handle_define};
public:
  {federate.classname}();
  virtual ~{federate.classname}() {{}};

  void {interaction.callbackname}({interaction.callback_arguments_define});
};

'''

    output = \
'''
//* Federate.h *//

#include "RTI/NullFederate.h"

using namespace rti1516e;

class Federate : public NullFederate
{
private:
  InteractionClassHandle loadScenarioHandle;
  ParameterHandle scenarioNameHandle;
  ParameterHandle initialFuelAmountHandle;

  InteractionClassHandle startHandle;
  ParameterHandle timeScaleFactorHandle;
public:
  Federate();
  virtual ~Federate() {};

  void loadScenarioCallback(std::wstring scenarioName, Integer32 initialFuelAmount);
  void startCallback(float timeScaleFactor);
};

'''


class SingleParameterLineTestCase(WalkTester):
    input = [
        '{parameter.decoder_define};'
    ]

    output = [
        'HLAunicodeString scenarioNameDecoder;',
        'HLAinteger32BE initialFuelAmountDecoder;',
        'HLAfloat32BE timeScaleFactorDecoder;'
    ]


class InteractionLoopTestCase(ParseTester):
    input = \
'''
  switch (theInteraction) {
  {$interactions}
  case {interaction.handlename}:
  {

  }
  break;
  {interactions$}
  }
'''

    output = \
'''
  switch (theInteraction) {
  case loadScenarioHandle:
  {

  }
  break;
  case startHandle:
  {

  }
  break;
  }
'''


class InteractionAndParamaterLoopTestCase(ParseTester):
    input = \
'''
  switch (theInteraction) {
  {$interactions}
  case {interaction.handlename}:
  {
    {$parameters}
    {parameter.varname}Param(theParameterValues.find({parameter.handlename}));
    {parameters$}
  }
  break;
  {interactions$}
  }
'''

    output = \
'''
  switch (theInteraction) {
  case loadScenarioHandle:
  {
    scenarioNameParam(theParameterValues.find(scenarioNameHandle));
    initialFuelAmountParam(theParameterValues.find(initialFuelAmountHandle));
  }
  break;
  case startHandle:
  {
    timeScaleFactorParam(theParameterValues.find(timeScaleFactorHandle));
  }
  break;
  }
'''


class LookMaNoDoubleBracketsTestCase(ParseTester):
    input = \
'''
  switch (theInteraction) {
  {$interactions}
  case {interaction.handlename}:
  {

  }
  break;
  {interactions$}
  }
'''

    output = \
'''
  switch (theInteraction) {
  case loadScenarioHandle:
  {

  }
  break;
  case startHandle:
  {

  }
  break;
  }
'''


class NoDuplicating(WalkTester):
    input = ['ParameterValueMap parameterMap']
    output = ['ParameterValueMap parameterMap']


class RealWorldTest(ParseTester):
    federate = Federate(
            "Locomotion", FOM("Common.xml", "Locomotion.xml"),
            Interaction("SetVehicleMotion", "speed", "angle"))

    input = \
'''
//* {federate.classname}.cpp *//

#include <iostream>
#include <memory>
#include <sstream>

#include "{federate.classname}.h"

{federate.classname}::{federate.classname}(const std::wstring& localSettingsDesignator, const std::vector<std::wstring>& FOMmoduleUrls,
                                           const std::wstring& federationName, const std::wstring& federateName)
  : HRAFfederateAmbassador(localSettingsDesignator, FOMmoduleUrls, federationName, federateName)
{
}

void {federate.classname}::setUpAfterConnect()
{
  {interaction.varname}Handle = rtiAmbassador->getInteractionClassHandle({interaction.literalname});
  {parameter.varname}Handle = rtiAmbassador->getParameterHandle({interaction.varname}Handle, {parameter.literalname});

  rtiAmbassador->subscribeInteractionClass({interaction.varname}Handle);
}

{$interactions}
void {federate.classname}::{interaction.callbackname}({interaction.callback_arguments_define})
{
  std::cout << "{federate.classname}::{interaction.callbackname}: Received";
  {$parameters}
  std::cout << " {parameter.name} = " << {parameter.varname};
  {parameters$}
  std::cout << "." << std::endl;
}

{interactions$}
void {federate.classname}::receiveInteraction(InteractionClassHandle theInteraction,
                                              const ParameterHandleValueMap& theParameterValues) throw(FederateInternalError)
{
  {$interactions}
  if (theInteraction == {interaction.handlename})
  {
    /* Get Parameters from ValueMap */
    {$parameters}
    ParameterHandleValueMap::const_iterator {parameter.varname}Param(theParameterValues.find({parameter.handlename}));
    if ({parameter.varname}Param == theParameterValues.end())
    {
      std::cerr << "{federate.classname}::receiveInteraction {interaction.name}: Expected parameter {parameter.name}" << std::endl;
      return;
    }

    {parameters$}
    /* Decode Parameters */
    {$parameters}
    {parameter.decodername}.decode({parameter.varname}Param->second);
    {parameters$}

    {$parameters}
    {parameter.cdefine} = {parameter.decodername}.get();
    {parameters$}

    /* call the callback */
    {interaction.callbackname}({interaction.callback_arguments});

    return;
  }
  {interactions$}
}

int main(int argc, char** argv)
{
  {federate.classname} fed(L"crcHost = localhost", {{ L"Common.xml", L"Locomotion.xml" }}, L"TestFederation", L"TestFederate");
  std::wcout << std::endl;

  std::wcout << L"Connecting..." << std::endl;
  try
  {
    fed.connect();
  }
  catch (const rti1516e::Exception& e)
  {
    std::wcerr << L"Connection error: " << e.what() << std::endl;
    return -1;
  }

  std::wcout << L"Hit enter to exit" << std::endl;
  wchar_t emptybuffer[256];
  std::wcin.getline(emptybuffer, sizeof(emptybuffer));

  std::wcout << L"Disconnecting..." << std::endl;
  fed.disconnect();

  std::wcout << L"Quit" << std::endl;
}
'''

    output = \
'''
//* Locomotion.cpp *//

#include <iostream>
#include <memory>
#include <sstream>

#include "Locomotion.h"

Locomotion::Locomotion(const std::wstring& localSettingsDesignator, const std::vector<std::wstring>& FOMmoduleUrls,
                                           const std::wstring& federationName, const std::wstring& federateName)
  : HRAFfederateAmbassador(localSettingsDesignator, FOMmoduleUrls, federationName, federateName)
{
}

void Locomotion::setUpAfterConnect()
{
  setVehicleMotionHandle = rtiAmbassador->getInteractionClassHandle(L"HLAinteractionRoot.HRAFinteractionRoot.Operation.SetVehicleMotion");
  speedHandle = rtiAmbassador->getParameterHandle(setVehicleMotionHandle, L"speed");
  angleHandle = rtiAmbassador->getParameterHandle(setVehicleMotionHandle, L"angle");

  rtiAmbassador->subscribeInteractionClass(setVehicleMotionHandle);
}

void Locomotion::setVehicleMotionCallback(double speed, double angle)
{
  std::cout << "Locomotion::setVehicleMotionCallback: Received";
  std::cout << " speed = " << speed;
  std::cout << " angle = " << angle;
  std::cout << "." << std::endl;
}

void Locomotion::receiveInteraction(InteractionClassHandle theInteraction,
                                              const ParameterHandleValueMap& theParameterValues) throw(FederateInternalError)
{
  if (theInteraction == setVehicleMotionHandle)
  {
    /* Get Parameters from ValueMap */
    ParameterHandleValueMap::const_iterator speedParam(theParameterValues.find(speedHandle));
    if (speedParam == theParameterValues.end())
    {
      std::cerr << "Locomotion::receiveInteraction SetVehicleMotion: Expected parameter speed" << std::endl;
      return;
    }

    ParameterHandleValueMap::const_iterator angleParam(theParameterValues.find(angleHandle));
    if (angleParam == theParameterValues.end())
    {
      std::cerr << "Locomotion::receiveInteraction SetVehicleMotion: Expected parameter angle" << std::endl;
      return;
    }

    /* Decode Parameters */
    speedDecoder.decode(speedParam->second);
    angleDecoder.decode(angleParam->second);

    double speed = speedDecoder.get();
    double angle = angleDecoder.get();

    /* call the callback */
    setVehicleMotionCallback(speed, angle);

    return;
  }
}

int main(int argc, char** argv)
{
  Locomotion fed(L"crcHost = localhost", { L"Common.xml", L"Locomotion.xml" }, L"TestFederation", L"TestFederate");
  std::wcout << std::endl;

  std::wcout << L"Connecting..." << std::endl;
  try
  {
    fed.connect();
  }
  catch (const rti1516e::Exception& e)
  {
    std::wcerr << L"Connection error: " << e.what() << std::endl;
    return -1;
  }

  std::wcout << L"Hit enter to exit" << std::endl;
  wchar_t emptybuffer[256];
  std::wcin.getline(emptybuffer, sizeof(emptybuffer));

  std::wcout << L"Disconnecting..." << std::endl;
  fed.disconnect();

  std::wcout << L"Quit" << std::endl;
}
'''

# Remove base classes from module namespace
# so they aren't seen by the test runner
del(WalkTester)
del(ParseTester)

if __name__ == '__main__':
    unittest.main()
