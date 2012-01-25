################################################################################
#   propertytree - A Qt property editor
#   Copyright © 2012 Pavlos Touboulidis <pav256@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

"""Parsing helpers.

AstHelper -- Customised Python literal parsing.
"""

from ast import Str, Num, Tuple, List, Dict, Name, Expression, parse, BinOp, Add, Sub

from collections import OrderedDict

class AstHelper(object):

    @staticmethod
    def delegate_literal_eval(node_or_string, convertHook=None):
        """Copied from cpython 2.7 Lib/ast.py @ 74346:66f2bcb47050
        
        Intentionally made as few changes as possible and marked them
        so it can be easily upgraded to a later version.
        
        Allows an optional 'convertHook' function with the signature:
            convertHook(node, converter) -> handled, value
        
        Safely evaluate an expression node or a string containing a Python
        expression.  The string or node provided may only consist of the following
        Python literal structures: strings, bytes, numbers, tuples, lists, dicts,
        sets, booleans, and None.
        """
        # avoid making changes to this code (read doc string please)
        #pylint: disable-msg=C0103,W0141,R0911,R0912
        _safe_names = {'None': None, 'True': True, 'False': False}
        if isinstance(node_or_string, basestring):
            node_or_string = parse(node_or_string, mode='eval')
        if isinstance(node_or_string, Expression):
            node_or_string = node_or_string.body
        def _convert(node):
            ### Modification start
            if convertHook is not None:
                handled, value = convertHook(node, _convert)
                if handled:
                    return value
            ### Modification end
            if isinstance(node, Str):
                return node.s
            elif isinstance(node, Num):
                return node.n
            elif isinstance(node, Tuple):
                return tuple(map(_convert, node.elts))
            elif isinstance(node, List):
                return list(map(_convert, node.elts))
            elif isinstance(node, Dict):
                return dict((_convert(k), _convert(v)) for k, v
                            in zip(node.keys, node.values))
            elif isinstance(node, Name):
                if node.id in _safe_names:
                    return _safe_names[node.id]
            elif isinstance(node, BinOp) and \
                 isinstance(node.op, (Add, Sub)) and \
                 isinstance(node.right, Num) and \
                 isinstance(node.right.n, complex) and \
                 isinstance(node.left, Num) and \
                 isinstance(node.left.n, (int, long, float)):
                left = node.left.n
                right = node.right.n
                if isinstance(node.op, Add):
                    return left + right
                else:
                    return left - right
            raise ValueError('malformed string')
        return _convert(node_or_string)

    @staticmethod
    def parseOrderedDict(strValue, valueReplacements=None):
        """Parse a string and return an ordered dictionary; nesting allowed.
        
        The format is similar to Python'strValue dict literal but it doesn't require
        quotes around strings.
        Example: ``{Red:255, Green:0, Blue:0, Awesome: True}``
        
        Values found in the 'valueReplacements' parameter (case insensitive)
        will be replaced. An example would be:
            {"true": True, "false": False}
        so that it would automatically accept 'true' and 'false' (in the string
        value) without quotes and will convert them to True and False.
        """
        vr = dict((str(key).lower(), value) for key, value in valueReplacements.items())
        def convertHook(node, convert):
            if isinstance(node, Dict):
                return True, OrderedDict((convert(key), convert(value)) for key, value in zip(node.keys, node.values))
            elif isinstance(node, Name):
                if node.id.lower() in vr:
                    return True, vr[node.id.lower()]
                else:
                    return True, str(node.id)
            return False, None

        return AstHelper.delegate_literal_eval(strValue, convertHook)
