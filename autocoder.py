#!/usr/bin/env python3.6

"""
autocoder.py

auto auto auto
"""

import re

name_re = re.compile(r'{(?P<path>(?P<pathname>(?P<root>\w+)(\.\w+)*)\.(?P<basename>\w+))}')

def find_list_property(ns, name, *, level_n=0):
    '''recursively find a property called '{name}s' in the dict of objects ns'''

    list_name = name + 's'
    root_object_name = None

    for key, obj in ns.items():
        if hasattr(obj, list_name):
            if not root_object_name:
                root_object_name = key
            else:
                raise KeyError(f'non-root name {name} is ambiguous')

    if root_object_name:
        return '.'.join([root_object_name, list_name])
    else:

        # TODO: if initial search is unsuccessful, try doing it recursively
        for key, obj in ns.items():
            new_ns = {p: getattr(obj, p)[0] for p in dir(obj) if p.endswith('s')}
            new_list_name = find_list_property(new_ns, name, level_n=level_n+1)
            if new_list_name:
                if not root_object_name:
                    root_object_name = key
                    list_name = new_list_name
                else:
                    raise KeyError(f'non-root name {name} is ambiguous at level {level_n+1}')


        if not root_object_name:
            return None
            # raise KeyError(f'could not find non-root name {name}')

        return '.'.join([root_object_name, list_name])


def attribute_walker(root, path):
    if len(path) == 0:
        return None
    if len(path) == 1:
        name = path[0]
        if name.endswith('s'):
            for e in getattr(root, name):
                yield e
        else:
            yield getattr(root, name)

    else:
        for elem in getattr(root, path[0]):
            yield from attribute_walker(elem, path[1:])


def walk(federate, seq, *, tree_cache=None, interaction=None):
    '''this function may be the biggest hack I have ever written'''
    result = []

    format_ns = {'federate' : federate}
    if interaction:
        format_ns['interaction'] = interaction

    if not tree_cache:
        tree_cache = {}

    n = 0
    while n < len(seq):
        line = seq[n]
        try:
            nextline = seq[n+1]
        except IndexError:
            nextline = ''

        match = name_re.search(line)

        if match:
            m = 0
            for l in seq[n:]:
                m += 1
                if not name_re.search(line):
                    break
            for l in seq[n:n+m]:
                pass

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
        elif match and match['root'].isidentifier():
            name = match['root']
            path = None
            if name in format_ns:
                path = [name]
            elif name in tree_cache:
                path = tree_cache[name]
            else:
                # implicit descent into objects
                path = find_list_property(format_ns, name).split('.')
                tree_cache[name] = path
            if path:
                root = format_ns[path[0]]
                path = path[1:]
                if path:
                    for elem in attribute_walker(root, path):
                        format_ns[name] = elem
                        result.append(line.format(**format_ns))
                    del format_ns[name]
                else:
                    result.append(line.format(**format_ns))
                n += 1
            else:
                raise LookupError(f'name {name} in {match[0]} not found')
            # if '{interaction' in line:
            #     if '{parameter' in nextline:
            #         n += 1
            #         param_lines = []
            #         for l in seq[n:]:
            #             if '{parameter' in l:
            #                 param_lines.append(l)
            #                 n += 1
            #             else:
            #                 break
            #         for l in param_lines:
            #             for interaction in federate.interactions:
            #                 result.append(line.format(federate=federate,
            #                               interaction=interaction))
            #                 for parameter in interaction.parameters:
            #                     result.append(l.format(federate=federate,
            #                                   interaction=interaction,
            #                                   parameter=parameter))
            #                 result.append('\n')
            #             result.pop()
            #     else:
            #         for interaction in federate.interactions:
            #             result.append(line.format(federate=federate,
            #                                       interaction=interaction))
            #             # result.append('\n')
            #         # result.pop()
            #         n += 1
            # elif '{parameter' in line:
            #     for interaction in federate.interactions:
            #         for parameter in interaction.parameters:
            #             result.append(line.format(federate=federate,
            #                                       interaction=interaction,
            #                                       parameter=parameter))
            #     n += 1
            # elif '{federate' in line:
            #     result.append(line.format(federate=federate))
            #     n += 1
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
