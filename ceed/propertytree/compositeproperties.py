"""The standard composite properties.

DictionaryProperty -- Generic property based on a dictionary.
"""

import ast

from collections import OrderedDict

from . import Property

class AstHelper(object):

    @staticmethod
    def delegate_literal_eval(node_or_string, convertHook=None):
        """Copied from cpython 2.7 Lib/ast.py @ 74346:66f2bcb47050
        
        Allows an optional 'convertHook' function with the signature:
            convertHook(node, converter) -> handled, value
        
        Safely evaluate an expression node or a string containing a Python
        expression.  The string or node provided may only consist of the following
        Python literal structures: strings, bytes, numbers, tuples, lists, dicts,
        sets, booleans, and None.
        """
        _safe_names = {'None': None, 'True': True, 'False': False}
        if isinstance(node_or_string, basestring):
            node_or_string = ast.parse(node_or_string, mode='eval')
        if isinstance(node_or_string, ast.Expression):
            node_or_string = node_or_string.body
        def _convert(node):
            if convertHook is not None:
                handled, value = convertHook(node, _convert)
                if handled:
                    return value

            if isinstance(node, ast.Str):
                return node.s
            elif isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.Tuple):
                return tuple(map(_convert, node.elts))
            elif isinstance(node, ast.List):
                return list(map(_convert, node.elts))
            elif isinstance(node, ast.Dict):
                return dict((_convert(k), _convert(v)) for k, v
                            in zip(node.keys, node.values))
            elif isinstance(node, ast.Name):
                if node.id in _safe_names:
                    return _safe_names[node.id]
            elif isinstance(node, ast.BinOp) and \
                 isinstance(node.op, (ast.Add, ast.Sub)) and \
                 isinstance(node.right, ast.Num) and \
                 isinstance(node.right.n, complex) and \
                 isinstance(node.left, ast.Num) and \
                 isinstance(node.left.n, (int, long, float)):
                left = node.left.n
                right = node.right.n
                if isinstance(node.op, ast.Add):
                    return left + right
                else:
                    return left - right
            raise ValueError('malformed string')
        return _convert(node_or_string)

class DictionaryProperty(Property):
    """A generic composite property based on a dict (or OrderedDict).
    
    The key-value pairs are used as components. A value can be a Property
    itself, allowing nested properties and the creation of multi-level,
    hierarchical properties.
    
    Example::
        colourProp = DictionaryProperty(
                                        name = "Colour",
                                        value = OrderedDict([
                                                             ("Red", 160),
                                                             ("Green", 255),
                                                             ("Blue", 160)
                                                             ]),
                                        editorOptions = {"instantApply":False, "numeric": {"min":0, "max":255, "step": 8}}
                                        )
        DictionaryProperty("dictionary", OrderedDict([
                                                      ("X", 0),
                                                      ("Y", 0),
                                                      ("Width", 50),
                                                      ("Height", 50),
                                                      ("Colour", colourProp)
                                                      ]),
                           readOnly=False)
    """

    @staticmethod
    def parseOrderedDict(s):
        def convertHook(node, convert):
            if isinstance(node, ast.Dict):
                return True, OrderedDict((convert(k), convert(v)) for k, v in zip(node.keys, node.values))
            return False, None

        return AstHelper.delegate_literal_eval(s, convertHook)

    def createComponents(self):
        self.components = OrderedDict()
        for name, value in self.value.items():
            # if the value of the item is a Property, make sure
            # it's in a compatible state (i.e. readOnly) and add it
            # as a component directly.
            if isinstance(value, Property):
                # make it read only if we're read only
                if self.readOnly:
                    value.readOnly = True
                # ensure it's name is the our key name
                value.name = str(name)
                # add it
                self.components[name] = value
            # if it's any other value, create a Property for it.
            else:
                self.components[name] = Property(name=name, value=value, defaultValue=value, readOnly=self.readOnly, editorOptions=self.editorOptions)

        # call super to have it subscribe to our components;
        # it will call 'getComponents()' to get them.
        super(DictionaryProperty, self).createComponents()

    def hasDefaultValue(self):
        # it doesn't really make sense to maintain a default value for this property.
        # we check whether our components have their default values instead.
        for comp in self.components.values():
            if not comp.hasDefaultValue():
                return False
        return True

    def getComponents(self):
        return self.components

    def valueToString(self):
        gen = ("{%s:%s}" % (prop.name, prop.valueToString()) for prop in self.components.values())
        return ",".join(gen)

    def isStringRepresentationEditable(self):
        return True

    def parseValueString(self, strValue):
        try:
            return DictionaryProperty.parseOrderedDict(strValue)
        except ValueError:
            pass
        return None

    def componentValueChanged(self, component, reason):
        self.value[component.name] = component.value
        self.raiseValueChanged(Property.ChangeValueReason.ComponentValueChanged)

    def updateComponents(self, reason=Property.ChangeValueReason.Unknown):
        # check if our value and our components match
        # and if not, recreate our components.
        # we do this on this Property because our value is a dictionary
        # and its items are not fixed.

        # if our keys are the same as our components' keys, simply update the values
        if self.value.keys() == self.components.keys():
            for name in self.value:
                self.components[name].setValue(self.value[name], reason)
        else:
            # recreate our components
            self.finaliseComponents()
            self.createComponents()
