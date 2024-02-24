import sys, json

VERBOSE = False

if '-v' in sys.argv or '--verbose' in sys.argv:
    VERBOSE = True
    if '-v' in sys.argv:
        sys.argv.remove('-v')
    if '--verbose' in sys.argv:
        sys.argv.remove('--verbose')

if len(sys.argv) < 4:
    print("Syntax: check_case [-v|--verbose] FILE1.json FILE2.json NAME/PROP [...]")
    exit(1)

try:
    with open(sys.argv[1],'r') as fh:
        ref = json.load(fh)

    with open(sys.argv[2],'r') as fh:
        act = json.load(fh)

    assert(ref['application'] == 'gridlabd')
    assert(act['application'] == 'gridlabd')

    count = 0
    for spec in sys.argv[3:]:
        name,prop = spec.split('/')
        if ref['objects'][name][prop] != act['objects'][name][prop]:
            if VERBOSE:
                print(f"ERROR: {spec} differs --> {ref['objects'][name][prop]} != {act['objects'][name][prop]}", file=sys.stderr)
            count += 1
        else:
            if VERBOSE:
                print(f"{spec} ok --> {ref['objects'][name][prop]} == {act['objects'][name][prop]}", file=sys.stderr)

    if VERBOSE:
        print(f"{count} differences found")

    exit(2 if count>0 else 0)

except Exception as err:
    e_type,e_value,e_trace = sys.exc_info()
    import traceback
    traceback.print_exception(e_type,e_value,e_trace,file=sys.stderr)
    exit(-1)