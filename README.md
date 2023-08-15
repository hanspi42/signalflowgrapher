# SignalFlowGrapher

## Version 1.1 dev

Intended for use from the autumn term of 2023 onwards. This version does not yet have installers for Windows, MacOS and Linux.

Please report all issues you find to hanspeter.schmid@fhnw.ch or create an issue on github, https://github.com/hanspi42/signalflowgrapher/issues

## License
This package is distributed under the Artistic License 2.0, which you find in the file LICENSE and on the internet on https://opensource.org/licenses/Artistic-2.0.

## Authors of Version 0.2
The first version checed in was the result of a bachelor thesis at the University of Applied Sciences and Arts Northwestern Switzerland, https://www.fhnw.ch/en/. Students: Simon Näf and Nicolai Wassermann. Advisors: Dominik Gruntz and Hanspeter Schmid. Contact author: hanspeter.schmid@fhnw.ch

## Installation with installer

Download the installer from the latest release (1.0): https://github.com/hanspi42/signalflowgrapher/releases

Unfortunately we can only provide an unsigned installer. If you do not wish to accept that risk (or if your system's policy does not allow you), you can always run it in a Python environent, as described below.

## Run in a Python environment

### Installation of plain Python or of Anaconda

- Get the latest version of Python from https://www.python.org/ or of Anaconda from https://www.anaconda.com/products/individual 

### Get the code

- Clone or download from https://github.com/hanspi42/signalflowgrapher, e.g. using `git clone https://github.com/hanspi42/signalflowgrapher`.

### Create and activate virtual environment with Anaconda

This is the prefered way to install it.

- Open an anaconda prompt.
- Open the `signalflowgrapher` directory in an anaconda terminal
- Create virtual environment using command `conda-env create --name sfg --file requirements\sfg.yml`
- Activate virtual environment using the command `conda activate sfg`

### Run application from terminal

- Go to the the `signalflowgrapher` directory in a terminal or an anaconda terminal
- Use `python .\src\main\python\main.py` to start the application

### Create and activate virtual environment with Python

Instead of creating the virtual environent with Anaconda, you can also do the following (but I have not tested it):
- Open the `src` directory in a terminal
- Create virtual environment using the command `python -m venv signalflowgrapher`
- On Windows run `signalflowgrapher\Scripts\activate.bat` or `signalflowgrapher\Scripts\Activate.ps1`
- On Unix or MacOS run `source signalflowgrapher/bin/activate`
- Go to the the `signalflowgrapher` directory in a terminal or an anaconda terminal
- Run `pip install -r requirements/base.txt`

### Run unit tests and format tests

- Go to the `signalflowgrapher\src\main\python` directory in a terminal or an anaconda terminal
- Run `python -m unittest`
- Run `flake8 -v`

## User manual and tips

### Manual
There is none yet, but to familiarize yourself with signal-flow graphs, you can
- watch the signalflowgrapher intro video on https://tube.switch.ch/videos/609c0510
- Watch "Signal-Flow Graphs in 12 short lessons" on https://tube.switch.ch/channels/d206c96c?order=episodes
- Read our papers, https://link.springer.com/article/10.1007%2Fs10470-018-1131-7 and http://rdcu.be/naw5 .

### Tips
- You can get nice SVG versions of the graphs by exporting TikZ, converting it to pdf with pdflatex, and then run https://github.com/dawbarton/pdf2svg

## Credits
Implemention of Johnson's algorithm: https://github.com/qpwo/python-simple-cycles
