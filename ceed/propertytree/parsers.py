"""Parsing helpers.

AstHelper -- Customised Python literal parsing.
"""

import ast

from collections import OrderedDict

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

    @staticmethod
    def parseOrderedDict(s, valueReplacements={"true": True, "false": False}):
        vr = dict((str(k).lower(), v) for k, v in valueReplacements.items())
        def convertHook(node, convert):
            if isinstance(node, ast.Dict):
                return True, OrderedDict((convert(k), convert(v)) for k, v in zip(node.keys, node.values))
            elif isinstance(node, ast.Name):
                if node.id.lower() in vr:
                    return True, vr[node.id.lower()]
                else:
                    return True, str(node.id)
            return False, None

        return AstHelper.delegate_literal_eval(s, convertHook)
