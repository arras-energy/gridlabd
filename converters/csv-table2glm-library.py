import sys
import pandas

DTYPES = {
    "float64" : "double",
    "int64" : "int64",
    "datetime" : "timestamp",
    "str" : "string",
    "bool" : "bool",
}

def convert(input_file, output_file, options={}):
    """Convert a CSV data table to a GLM library object list

    This converts a CSV data file to a GLM library object list.  The options control
    how the GLM file is generated.  

    ARGUMENTS

        input_file (str) - input file name (csv file)

        ouput_file (str) - output file name (glm file)

    OPTIONS

        class=CLASS (required)

            Specifies the class name to use when generating objects.

        module={MODULE,runtime} (optional)

            Specifies the module to load prior to defining object.  If a module name is
            specified, then the columns of the table must match the properties of the
            class specified, which must be a class defined in the module specified.

        index=COLUMN (optional)

            Specifies the column to use as the object name. If none is specified then
            objects will be anonymous.

        NAME=VALUE (optional, repeated)
    
            Specifies the NAME and VALUE of a define statement.  This permits the use
            of variables in fields, e.g., ${NAME} will be expanded at runtime into VALUE.

    RETURNS

        None
    """

    oclass = None
    module = None
    index = None

    table = pandas.read_csv(input_file)

    with open(output_file,"wt") as fh:

        print(f"// generated by csv-table2glm-library/convert({input_file.__repr__()},{output_file.__repr__()},{options})",file=fh)

        for name, value in options.items():
            if name == 'class':
                oclass = options['class']
            elif name == 'module':
                module = options['module']
                if module != 'runtime':
                    print(f"import {module};",file=fh)
            elif name == 'index':
                index = value
            else:
                print(f"#define {name}={value}",file=fh)

        dtypes = {}
        if module == 'runtime':
            print(f"class {oclass}",file=fh)
            print("{",file=fh)
            for name, dtype in zip(table.columns.to_list(),table.dtypes.to_list()):
                if name != index:
                    dtypes[name] = str(dtype)
                    if str(dtype) in DTYPES.keys():
                        print(f"\t{DTYPES[str(dtype)]} {name}; // {dtype}",file=fh)    
                    else:
                        print(f"\t// unsupported: {dtype} {name}",file=fh)
                else:
                    print(f"\t// index: {dtype} {name}",file=fh)
            print("}",file=fh)
            module = None

        for id, data in table.iterrows():
            if 'class' in data.keys():
                oclass = data['class']
                del data['class']
            elif 'class' in options.keys():
                oclass = options['class']
            else:
                raise Exception("class must defined either in data or in options")
            
            if module:
                print(f"object {module}.{oclass}",file=fh)
            else:
                print(f"object {oclass}",file=fh)
            print("{",file=fh)
            for name, value in data.items():
                if name == index:
                    print(f"\tname \"{value}\";",file=fh)
                elif module != 'runtime' or dtypes[name] in DTYPES.keys():
                    print(f"\t{name} \"{value}\";",file=fh)
                else:
                    print(f"\t// {name}={value}: type {dtype} is not valid in GridLAB-D",file=fh)
            print("}",file=fh)
