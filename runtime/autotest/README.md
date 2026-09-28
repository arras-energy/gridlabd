# Runtime validation

Runtime validation tests use the standard `gridlabd` autotest mechanism. To start validation of the `runtime` folder after a build do the following.

```bash
gridlabd -W runtime --validate
```

# Upgrading from `tape` to `pandas`

Runtime validation should not use the pre-compiled `tape` module. To use `recorder` and `player` objects include the runtime `pandas` module as follows.

```c
#include "pandas.glm"
```

Note that there are some difference in how the `pandas` runtime classes work. Specifically only `recorder` and `player` objects are supported. All the other classes in `tape` are not supported in the `pandas` module and should not be used in `runtime/autotest` any longer.

# Upgrading `assert`

Runtime validation should not use the pre-compiled `assert` module. To use `assert` objects include the runtime `assert` module as follows.

```c
#include "assert.glm"
```

Note that there are difference in how the `assert` class works. Specifically,

1. The `relation` keywords are `EQ`, `NE`, `LT`, `LE`, `GT`, `GE`, `IN`, and `NI`, instead of `==`, `!=`, `<`, `<=`, `>`, `>=`, `inside`, and `outside`, respecticelly.

2. The `dtype` keyword must be specified for all non-`str` data type comparisons.

3. The `complex` comparisons must include the `part` value to ensure that only real or imaginary part is compared.  In addition, callables are supported for any data type.

# Conventions

The following conventions should be observed when writing runtime autotests.

- **Input files**: Input files should have the same root as the autotest GLM file, e.g., `${modelname/.glm/_in.csv}`.
  
- **Output files**: Output files should be written to a files that have the same root as the autotest GLM file, e.g., `${modelname/.glm/_out.csv}` or `${modelname/.glm/_opt.glm}`.

- **Output checks**: Recorder output should be compared to the original output when the simulation exits successfully, e.g.,

```c
#ifexist "../${modelname/.glm/_out.csv}"
#on_exit 0 diff ../${modelname/.glm/_out.csv} ${modelname/.glm/_out.csv} > gridlabd.diff
#endif
```
