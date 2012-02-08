# ---------------------------------------------------------------------
#
# Copyright (c) 2012 University of Oxford
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# ---------------------------------------------------------------------
import types

NotUnique = object()

class ExitMenu(object):
    def __init__(self, depth=1):
        self.depth = depth

def menu(options,
         with_quit=True,
         question="*** Commands ***",
         prompt="What now> "):
    if with_quit:
        options['quit'] = ExitMenu()
    def unique_prefix(prefix):
        if prefix in names:
            return prefix
        found = None
        for name in names:
            if name.startswith(prefix):
                if found is None:
                    found = name
                else:
                    return NotUnique
        return found
        
    names = sorted(options)
    max_length = max(map(len, names))
    columns = 80 // (max_length + 8)

    prefix_lengths = {}    
    for name in names:
        for i in range(1, len(name)):
            if unique_prefix(name[:i]) == name:
                prefix_lengths[name] = i
                break

    print
    while True:
        print question
        for i, name in enumerate(names, 1):
            print ("  %2d. [%s]%s" % (i,
                                     name[:prefix_lengths[name]],
                                     name[prefix_lengths[name]:])).ljust(max_length + 8),
            if i % columns == 0 or i == len(names):
                print
        
        input = raw_input(prompt)
        if not input:
            print "Please choose an option."
            continue
        try:
            return options[names[int(input)-1]]
        except (ValueError, IndexError):
            pass
        name = unique_prefix(input)
        if name is NotUnique:
            print "Ambiguous option (%s); try more characters." % input
        elif name is None:
            print "That wasn't an option! (%s)" % input
        else:
            return options[name]
    

def interactive(start_menu):
    menu_stack = [start_menu]
    #menu_stack[0].next()
    
    while menu_stack:
        menu = menu_stack[-1]
        
        try:
            result = menu.next()
            if callable(result):
                result = result()
            if isinstance(result, types.GeneratorType):
                menu_stack.append(result)
            elif isinstance(result, ExitMenu):
                menu_stack[-result.depth:] = []
        except StopIteration:
            menu_stack.pop()
        except (KeyboardInterrupt, EOFError):
            print "\n[Backing out of menu]"
            menu_stack.pop()
