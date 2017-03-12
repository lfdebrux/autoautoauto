#!/usr/bin/env python3

import xml.etree.ElementTree as ElementTree

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


def variable_case(string):
    first, rest = string[0], string[1:]
    first = first.lower()
    return first + rest


def is_ctype(typename):
    return typename in BasicDataTypes


def get_ctype(typename):
    try:
        return BasicDataTypes[typename]
    except KeyError:
        raise ValueError(f'{typename} is not a basic datatype')


def to_cliteral(s):
    return f'L"{s}"'

class FOM:
    def __init__(self, *filenames):
        self.filenames = list(filenames)
        self.filenames_literal = self._to_literal()

    def __repr__(self):
        args = ', '.join(f"'{f}'" for f in self.filenames)
        return f"FOM({args})"

    def _to_literal(self):
        return f"{{ {', '.join(map(to_cliteral, self.filenames))} }}"

    def extend(self, t):
        if isinstance(t, str):
            self.filenames.append(t)
        elif isinstance(t, FOM):
            self.filenames.extend(t.filenames)
        elif isinstance(t, list):
            for i in t:
                if isinstance(t, str):
                    self.filenames.append(t)
                if isinstance(t, FOM):
                    self.filenames.extend(t.filenames)
        else:
            raise ValueError(f"Expected FOM or list of FOMs, got {type(t)}")

        self.filenames_literal = self._to_literal()


class XmlFom:
    xmlns = {'hla': 'http://standards.ieee.org/IEEE1516-2010'}

    def __init__(self, fom: FOM):
        self.fom = fom
        self.parse()

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

        # parse the name
        # we use a convoluted method to allow lots of ways of specifying a name
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

    def resolve(self, fom: XmlFom):
        """find the basic datatypes for each parameter. requires xml foms"""
        for parameter in self.parameters:
            parameter.resolve(fom)

        if self.fullname:
            # verify fullname
            xpath = '/'.join(
                ['.//hla:interactions'] +
                ["hla:interactionClass[hla:name='{}']".format(s) for s in self.path]
                )
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

    def __repr__(self):
        args = []
        if self.fullname:
            args.append(f"'{self.fullname}'")
        else:
            args.append(f"'{self.name}'")
        args += [str(p) for p in self.parameters]
        args = ', '.join(args)
        return f'''Interaction({args})'''


class Parameter:
    def __init__(self, name, datatype=None, representation=None):
        self.name = name
        self.datatype = datatype
        self.representation = representation

    def resolve(self, fom:XmlFom):
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

    def __repr__(self):
        args = [f"'{self.name}'"]
        if self.datatype:
            args += [f"datatype='{self.datatype}'"]
        if self.representation:
            args += [f"representation='{self.representation}'"]
        return f"Parameter({', '.join(args)})"

class Federate:
    def __init__(self, *args):
        self.fom = FOM()
        self.interactions = []

        for arg in args:
            if isinstance(arg, FOM):
                self.fom.extend(arg)
            elif isinstance(arg, Interaction):
                self.interactions.append(arg)
            else:
                raise ValueError(f'Unrecognised argument {arg}')

        self.xml = XmlFom(self.fom)
        self.xml.parse()
        self.resolve()

    def __repr__(self):
        fom = str(self.fom)
        interactions = ', '.join(str(i) for i in self.interactions)
        return f"Federate({fom}, {interactions})"

    def resolve(self):
        for interaction in self.interactions:
            interaction.resolve(self.xml)

