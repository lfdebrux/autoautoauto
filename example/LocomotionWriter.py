
from hla_autocoder import Federate, FOM, Interaction, run

federate = Federate(
            "LocomotionWriter", FOM("Common.xml", "Locomotion.xml"),
            Interaction("SetVehicleMotion", "speed", "angle"))

header = \
'''
//* LocomotionWriter.h *//

#include <string>

#include "HRAFfederateAmbassador.h"

using namespace rti1516e;

class LocomotionWriter : public HRAFfederateAmbassador
{
private:
  std::auto_ptr<RTIambassador> _rtiAmbassador;

  const std::wstring _federationName = L"TestFederation";

  InteractionClassHandle {interaction.handlename};
  ParameterHandle {parameter.handlename};

  {parameter.representation} {parameter.varname}Encoder;

protected:
  virtual void setUpAfterConnect();

public:
  {federate.classname}(const std::wstring& localSettingsDesignator, const std::vector<std::wstring>& FOMmoduleUrls,
                       const std::wstring& federationName, const std::wstring& federateName);

  virtual void setVehicleMotion(double angle, double speed);
};
'''

cpp = \
'''
//* LocomotionWriter.cpp *//

#include <iostream>
#include <memory>
#include <sstream>

#include "RTI/VariableLengthData.h"

#include "LocomotionWriter.h"

LocomotionWriter::LocomotionWriter(const std::wstring& localSettingsDesignator, const std::vector<std::wstring>& FOMmoduleUrls,
                                   const std::wstring& federationName, const std::wstring& federateName)
  : HRAFfederateAmbassador(localSettingsDesignator, FOMmoduleUrls, federationName, federateName)
{
}

void LocomotionWriter::setUpAfterConnect()
{
  {interaction.handlename} = _rtiAmbassador->getInteractionClassHandle({interaction.literalname});
  {parameter.handlename} = _rtiAmbassador->getParameterHandle({interaction.handlename}, {parameter.literalname});

  _rtiAmbassador->publishInteractionClass(setVehicleMotionHandle);
}

void setVehicleMotion(double angle, double speed)
{
  ParameterHandleValueMap parameterMap;

  {parameter.varname}Encoder.set({parameter.varname});

  parameterMap[{parameter.handlename}] = {parameter.varname}Encoder.encode();

  rtiAmbassador->sendInteraction(setVehicleMotionHandle, parameterMap, /* Empty Tag */ rti1516e::VariableLengthData());
}
'''

if __name__ == '__main__':
    run(federate, header, "LocomotionWriter.h")
    run(federate, cpp, "LocomotionWriter.cpp")
