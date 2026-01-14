# SignalFlowGrapher

<img width="1220" height="860" alt="SFGrapher" src="https://github.com/user-attachments/assets/9186c224-5ff4-4209-8240-3a01c367d51d" />

## Version 2.0 dev
If you want to try this development version, you can do this as follows:


This version does not have installers yet. Please follow the steps in the section [Getting started](##Getting-started).

Please report all issues you find to hanspeter.schmid@fhnw.ch or create an issue on github, https://github.com/hanspi42/signalflowgrapher/issues

## Getting started
Clone or download from https://github.com/hanspi42/signalflowgrapher, e.g. using git clone https://github.com/hanspi42/signalflowgrapher.

### Install Dependencies
To install the dependencies, you can use either Miniforge or Python environments.

#### With Miniforge
- If you do not have it yet, download Miniforge from https://conda-forge.org/download/ and install it.
- Open a miniforge prompt.
- `cd` to the top directory of this repository.
- Build a python environment with `conda env create --file=requirements/sfg.yml`.
- Activate the evironment with `conda activate sfg`.
- `cd src/main/python`.
- Start the signalflowgrapher with `python main.py`.

#### With Python evironments
- Get the latest version of Python from https://www.python.org/
- Open the repository’s root directory in a terminal
- Create virtual environment using the command `python -m venv signalflowgrapher`
- On Windows run `signalflowgrapher\Scripts\activate.bat` or `signalflowgrapher\Scripts\Activate.ps1`
- On Unix or MacOS run `source signalflowgrapher/bin/activate`
- Run `pip install -r requirements/base.txt`

### Run application from terminal
- Use `python .\src\main\python\main.py` to start the application


**Note regarding macOS:** For MacOS on ARM processors, use an use an x86_64 Python installation (read this: https://github.com/hanspi42/signalflowgrapher/issues/48#issue-1906889457).

## User manual and tips

### Manual
There is none yet, but to familiarize yourself with signal-flow graphs, you can
- watch the signalflowgrapher intro video on https://tube.switch.ch/videos/609c0510
- Watch "Signal-Flow Graphs in 12 short lessons" on https://tube.switch.ch/channels/d206c96c?order=episodes
- Read our papers, https://link.springer.com/article/10.1007%2Fs10470-018-1131-7 and http://rdcu.be/naw5 .

### Tips
- You can get nice SVG versions of the graphs by exporting TikZ, converting it to pdf with pdflatex, and then run https://github.com/dawbarton/pdf2svg

## For Developers

### Developer documentation
See more details in [Developer documentation for V2.0](DEVDOCU.md).


### Run unit tests and format tests

- Go to the `signalflowgrapher\src\main\python` directory in a terminal or an anaconda terminal
- Run `python -m unittest`
- Run `flake8 -v`

## License
This package is distributed under the Artistic License 2.0, which you find in the file LICENSE and on the internet on https://opensource.org/licenses/Artistic-2.0.

## Authors of Version 0.2
The first version checed in was the result of a bachelor thesis at the University of Applied Sciences and Arts Northwestern Switzerland, https://www.fhnw.ch/en/. Students: Simon Näf and Nicolai Wassermann. Advisors: Dominik Gruntz and Hanspeter Schmid. Contact author: hanspeter.schmid@fhnw.ch

## Credits
Implemention of Johnson's algorithm: https://github.com/qpwo/python-simple-cycles
