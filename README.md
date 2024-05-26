# Application generator

## Requirements
### Latex
Needs pdflatex to run

### Python 
Run `pip install -r requirements.txt`

## Examples
`python generate.py`
-> generates the default cover letter and vitea in the `out` directory
`python generate.py personal`
-> generates the cover letter and vitea in the `out` directory, but applies overrides/extensions in subfolders with the name `personal`.

There can be a multiple of overrides applied, e.g. 
`python generate.py personal company_x`
with the later overrides taking precedence

## Parameters
`-v`: verbose latex output (spams the console but does show latex problems) 
`-u`: concatenate the output to one large file
-> add the files referenced in the `supplements/supplements` file, or in ``supplements/supplements-{override}`,
if there is such a file that matches an override

## Automatic generating
It may be helpful to combine this with a file watcher, e.g. https://marketplace.visualstudio.com/items?itemName=appulate.filewatcher
and configure it to change when a `*.tex` file changes.


