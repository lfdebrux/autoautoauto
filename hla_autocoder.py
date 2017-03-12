#!/usr/bin/env python3.6

"""
hla_autocoder.py

auto auto auto
"""

__version__ = "0.1.0_20170309"


import xml.etree.ElementTree as ElementTree


def variable_case(string):
    first, rest = string[0], string[1:]
    first = first.lower()
    return first + rest


BasicDataTypes = {
    'HLAASCIIchar': 'char',
    'HLAASCIIstring': 'std::string',
    'HLAboolean': 'bool',
    'HLAbyte': 'Octet',
    'HLAfloat32BE': 'float',
    'HLAfloat32LE': 'float',
    'HLAfloat64BE': 'double',
    'HLAfloat64LE': 'double',
    'HLAinteger16LE': 'Integer16',
    'HLAinteger16BE': 'Integer16',
    'HLAinteger32BE': 'Integer32',
    'HLAinteger32LE': 'Integer32',
    'HLAinteger64BE': 'Integer64',
    'HLAinteger64LE': 'Integer64',
    'HLAoctet': 'Octet',
    'HLAoctetPairBE': 'OctetPair',
    'HLAoctetPairLE': 'OctetPair',
    'HLAunicodeChar': 'wchar_t',
    'HLAunicodeString': 'std::wstring',
}


def is_ctype(typename):
    return typename in BasicDataTypes


def get_ctype(typename):
    try:
        return BasicDataTypes[typename]
    except KeyError:
        raise ValueError(f'{typename} is not a basic datatype')


def to_cliteral(s):
    return f'L"{s}"'


class Federate:
    def __init__(self, classname, *args):
        self.classname = classname
        self.fom = FOM()
        self.interactions = []

        for arg in args:
            if isinstance(arg, FOM):
                self.fom.extend(arg)
            if isinstance(arg, Interaction):
                self.interactions.append(arg)

        self.fom.parse()
        self.resolve()

    def __str__(self):
        fom = str(self.fom)
        interactions = ', '.join(str(i) for i in self.interactions)
        return f"Federate('{self.classname}', {fom}, {interactions})"

    def resolve(self):
        for interaction in self.interactions:
            interaction.resolve(self.fom)


class FOM:
    xmlns = {'hla': 'http://standards.ieee.org/IEEE1516-2010'}

    def __init__(self, *filenames):
        self.filenames = list(filenames)
        self.xml = None
        self.filenames_literal = self._to_literal()

    def __str__(self):
        args = ', '.join(f"'{f}'" for f in self.filenames)
        return f"FOM({args})"

    def _to_literal(self):
        return f"{{ {', '.join(map(to_cliteral, self.filenames))} }}"

    def extend(self, t):
        if isinstance(t, str):
            self.filenames.append(t)
        if isinstance(t, FOM):
            self.filenames.extend(t.filenames)
        if isinstance(t, list):
            for i in t:
                if isinstance(t, str):
                    self.filenames.append(t)
                if isinstance(t, FOM):
                    self.filenames.extend(t.filenames)

        self.filenames_literal = self._to_literal()

    def parse(self):
        '''import all FOM XML trees into one tree'''
        self.xml = ElementTree.Element('root')
        for f in self.filenames:
            newfom = ElementTree.parse(f).getroot()
            self.xml.append(newfom)

    def find(self, match):
        return self.xml.find(match, namespaces=self.xmlns)

    def find_type(self, name):
        """find the datatype of a parameter or attribute"""
        if is_ctype(name):
            return name
        datatype = self.find(f".//*[hla:name='{name}']/hla:dataType")
        if datatype is None:
            raise LookupError(
                f"cannot find parameter or attribute {name} in {str(self)}")
        return datatype.text

    def find_representation(self, typename):
        """find the representation of a datatype"""
        if is_ctype(typename):
            return typename
        representation = self.find(
            f".//hla:dataTypes//*[hla:name='{typename}']/hla:representation")
        if representation is None:
            raise LookupError(
                f"cannot find datatype {typename} in {str(self)}")
        return representation.text


class Interaction:
    def __init__(self, name, *parameters):
        """register that this federate subscribes to an InteractionClass"""
        self.path = name.split('.')
        self.basename = self.path[-1]

        self.name = self.basename

        self.pathname = '.'.join(self.path[:-1])

        if self.pathname:
            if self.path[0] != 'HLAinteractionRoot':
                self.path.insert(0, 'HLAinteractionRoot')
            self.fullname = '.'.join(self.path)
        else:
            self.fullname = None

        self.parameters = list(map(Parameter, parameters))

    def resolve(self, fom):
        """find the basic datatypes for each parameter. requires xml foms"""
        for parameter in self.parameters:
            parameter.resolve(fom)

        if self.fullname:
            # verify fullname
            xpath = '/'.join(
                ['.//hla:interactions']
                + ["hla:interactionClass[hla:name='{}']".format(s)
                    for s in self.path])
            xml_element = fom.find(xpath)
            if not xml_element:
                raise LookupError(f'Interaction: No InteractionClass {self.fullname} found in {fom}')
        else:
            # find using basename
            xml_element = fom.find(f".//hla:interactionClass[hla:name='{self.basename}']")
            if not xml_element:
                raise LookupError(f'Interaction: No InteractionClass {self.basename} found in {fom}')
            # find fullname and pathname
            while True:
                parent = fom.find(f".//hla:interactionClass[hla:name='{self.path[0]}']/../hla:name").text
                self.path.insert(0, parent)
                if parent == 'HLAinteractionRoot':
                    break
            self.pathname = '.'.join(self.path[:-1])
            self.fullname = '.'.join(self.path)

        # verify parameters
        for parameter in self.parameters:
            if not xml_element.find(f"hla:parameter[hla:name='{parameter.name}']", fom.xmlns):
                raise LookupError(f'InteractionClass {self.fullname} has no parameter {parameter.name})')


        self.literalname = to_cliteral(self.fullname)

        self.varname = variable_case(self.basename)
        self.handlename = f'{self.varname}Handle'
        self.handle_define = f'InteractionClassHandle {self.handlename}'
        self.callbackname = f'{self.varname}Callback'

        self.callback_arguments = ', '.join(p.varname for p in self.parameters)
        self.callback_arguments_define = ', '.join(p.cdefine for p in self.parameters)

    def __str__(self):
        args = ','.join([f"'{self.fullname}'"] +
                        [str(p) for p in self.parameters])
        return f'''Interaction({args})'''


class Parameter:
    def __init__(self, name, datatype=None, representation=None):
        self.name = name
        self.datatype = datatype
        self.representation = representation

    def resolve(self, fom):
        """find the basic datatype for the parameter. requires xml fom"""
        datatype = fom.find_type(self.name)
        if datatype:
            self.datatype = datatype
        representation = fom.find_representation(self.datatype)
        if representation:
            self.representation = representation

        self.varname = variable_case(self.name)
        self.literalname = to_cliteral(self.name)
        self.handlename = f'{self.varname}Handle'
        self.handle_define = f'ParameterHandle {self.handlename}'
        self.decodername = f'{self.varname}Decoder'
        self.ctype = get_ctype(self.representation)
        self.cdefine = f'{self.ctype} {self.varname}'
        self.decoder_define = f'{self.representation} {self.decodername}'

    def __str__(self):
        args = [f"'{self.name}'"]
        if self.datatype:
            args += [f"datatype='{self.datatype}'"]
        if self.representation:
            args += [f"representation='{self.representation}'"]
        return f"Parameter({','.join(args)})"


def walk(federate, seq, *, interaction=None):
    '''this function may be the biggest hack I have ever written'''
    result = []

    n = 0
    while n < len(seq):
        line = seq[n]
        try:
            nextline = seq[n+1]
        except IndexError:
            nextline = ''

        if '{$interactions}' in line:
            n += 1
            loop_lines = []
            for l in seq[n:]:
                n += 1
                if '{interactions$}' in l:
                    break
                loop_lines.append(l)
            for interaction in federate.interactions:
                m = 0
                while m < len(loop_lines):
                    l = loop_lines[m]
                    if '{$parameters}' in l:
                        m += 1
                        param_lines = []
                        for k in loop_lines[m:]:
                            m += 1
                            if '{parameters$}' in k:
                                break
                            param_lines.append(k)
                        for parameter in interaction.parameters:
                            for k in param_lines:
                                if '{' in k and '}' in k:
                                    try:
                                        result.append(k.format(federate=federate,
                                                      interaction=interaction,
                                                      parameter=parameter))
                                    except ValueError as e:
                                        raise ValueError(f'Error parsing lines:\n"\n{"".join(param_lines)}"\n{k}"\n{e}')
                                else:
                                    result.append(k)
                    elif '{' in l and '}' in l:
                        m += 1
                        result.append(l.format(federate=federate,
                                      interaction=interaction))
                    else:
                        m += 1
                        result.append(l)
        elif '{$parameters}' in line:
            n += 1
            param_lines = []
            for l in seq[n:]:
                n += 1
                if '{parameters$}' in l:
                    break
                param_lines.append(l)
            for parameter in interaction:
                for l in param_lines:
                    result.append(l.format(federate=federate,
                                  interaction=interaction,
                                  parameter=parameter))
        elif '{interaction' in line:
            if '{parameter' in nextline:
                n += 1
                param_lines = []
                for l in seq[n:]:
                    if 'parameter' in l:
                        param_lines.append(l)
                        n += 1
                    else:
                        break
                for l in param_lines:
                    for interaction in federate.interactions:
                        result.append(line.format(federate=federate,
                                      interaction=interaction))
                        for parameter in interaction.parameters:
                            result.append(l.format(federate=federate,
                                          interaction=interaction,
                                          parameter=parameter))
                        result.append('\n')
                    result.pop()
            else:
                for interaction in federate.interactions:
                    result.append(line.format(federate=federate,
                                              interaction=interaction))
                    # result.append('\n')
                # result.pop()
                n += 1
        elif '{parameter' in line:
            for interaction in federate.interactions:
                for parameter in interaction.parameters:
                    result.append(line.format(federate=federate,
                                              interaction=interaction,
                                              parameter=parameter))
            n += 1
        elif '{federate' in line:
            result.append(line.format(federate=federate))
            n += 1
        else:
            result.append(line)
            n += 1

    return result


def parse(federate, template):
    return ''.join(walk(federate, template.splitlines(keepends=True)))


def run(federate, template, out):
    result = parse(federate, template)
    f = open(out, 'w', newline='\n')
    f.write(result)
    f.close()


if __name__ == '__main__':

    import federate_cpp
    import federate_h

    federate = Federate(
            "Locomotion", FOM("Common.xml", "Locomotion.xml"),
            Interaction("SetVehicleMotion", "speed", "angle"))

    run(federate, federate_cpp.template, "Locomotion.cpp")
    run(federate, federate_h.template, "Locomotion.h")
