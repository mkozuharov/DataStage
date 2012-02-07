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

# $Id: Combinators.py 1047 2009-01-15 14:48:58Z graham $
#
"""
Combinators for use with Python code, mostly based on Haskell library elements.

(Also contains some other Haskell-style list/tuple functions functions.)

Strictly speaking, the "curry..." functions are not currying, but partial
application.  Currying is the partial application of a function of n 
arguments to just one argument to yield a new function of (n-1) arguments.
See: http://en.wikipedia.org/wiki/Currying


"""

class compose:
    """
    Function composition (with non-tuple intermediate value):
    See: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52902
    
    compose(f,g,x...)(y...) = f(g(y...),x...))
    
    This extends the traditional functional '.' by allowing additional arguments
    to be bound into the composition;  a kind of curried composition, I suppose.
    """
    def __init__(self, f, g, *args, **kwargs):
        self.f = f
        self.g = g
        self.pending = args[:]
        self.kwargs = kwargs.copy()

    def __call__(self, *args, **kwargs):
        return self.f(self.g(*args, **kwargs), *self.pending, **self.kwargs)

def curry1(func, arg):
    """
    Curry one argument:
    See: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/229472
    """
    import new
    return new.instancemethod(func, arg, object)

def curry(func, *args):
    """
    Curry multiple arguments:
    See: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/229472
    
    As of Python 2.5, a more general version of this is in standard
    module functools:
      http://www.python.org/dev/peps/pep-0309/
      http://docs.python.org/lib/module-functools.html
    """
    def curried(*args2):
        args2 = args + args2
        return func(*args2)
    return curried

# End.
