import types

NotUnique = object()
ExitMenu = object()

def menu(options):
    options['quit'] = ExitMenu
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
        print "*** Commands ***"
        for i, name in enumerate(names, 1):
            print ("  %2d. [%s]%s" % (i,
                                     name[:prefix_lengths[name]],
                                     name[prefix_lengths[name]:])).ljust(max_length + 8),
            if i % columns == 0 or i == len(names):
                print
        
        input = raw_input("What now> ")
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
            if isinstance(result, types.FunctionType):
                result = result()
            if isinstance(result, types.GeneratorType):
                menu_stack.append(result)
            elif result is ExitMenu:
                menu_stack.pop()
        except StopIteration:
            menu_stack.pop()
