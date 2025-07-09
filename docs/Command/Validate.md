[[/Command/Validate]] -- Perform model validation check

# Synopsis

Shell:

~~~
gridlabd [OPTIONS ...] --validate[=TIMECSV] [ARGUMENTS ...]
~~~

GLM:

~~~
#option validate
~~~

# Description

Perform model validation check on `autotest` folders starting in the current
working directory. Options provided before the `--validate` command option
are used by the validation procedure. Arguments provided after the
`--validate` command option are passed to the validation tests.

If an autotest filename contains the string `_err` then the autotest must
fail. If an autotest filename contains the string `_opt` then the result of
the autotest is not include the overall validation results.

The output `TIMECSV` records the timing of each autotest in a CSV file with
headings `autotest,status,time`, where `time` is recorded in seconds with 1
usec resolution. The timing outputs can be used to perform regression
analysis. For help with `utilities/regression.py` type the command

    gridlabd utilities/regression.py help

# Example

The following example performs regression analysis on a change to source code:

    gridlabd --validate=before.csv
    # make your changes
    gridlabd --validate=after.csv
    gridlabd python utilities/regression.py before.csv after.csv

# Caveat

Many autotests involve cached network operations. As a result, the first
validation run after a new build often takes much longer than subsequent
runs. Therefore, after a build it is preferable to run validation once
without timing output to ensure all caches are up to date, and then run it
again with timing output so that the timings are based on cached input data.

# Bugs

The validation processor does not accept Ctrl-C (SIGINT) signals. Instead,
these are passed on the current running test, which is therefore interrupted
and exits. Consequently, the validation processor proceeds to the next
autotest. If you want to interrupt the validation processor you need to send
it the `kill` (SIGKILL) signal, e.g., press Ctrl-Z and run the `kill %1`
command.