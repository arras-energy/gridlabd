[[/Subcommand/Docs]] -- Open online documentation browser

Syntax: gridlabd docs [OPTIONS ...]

Options:

* `-b|--branch BRANCH`: open docs from github branch BRANCH

* `-d|--document NAME`: open document NAME (must include full path)

* `-h|--help|help`: output this help

* `-f|--folder DIR`: open folder DIR (must include root /)

* `-o|--organization ORG`: open docs from github owner ORG

Opens the document browser at the indicated folder and document
on the specified branch of the organization's `gridlabd` project.
The default organization is `arras-energy`, the default branch is
`master`, the default folder is `/`, and the default document is
`README.md`.

Exit codes:

* `0`: ok

* `1`: invalid option

Caveat:

If you do not specify the folder and document, the documentation browser
will reopen the previous document, if any was viewed recently. The default
folder and document will only be opened on the first view in 24 hours.

See Also:

* https://docs.arras.energy/
