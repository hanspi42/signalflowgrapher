# A very short manual of the SignalFlowGrapher

Hanspeter Schmid, FHNW/ISE

## Introduction

The signalflowgrapher is a tool that allows you to draw signal-flow graphs, calculate transfer functions (SymPy code is generated for further use in Jupyter notebooks), do graph manipulations (e.g., node elimination and graph transposition), and save a graph as TikZ for use in LaTeX documentation.

To familiarize yourself with signal-flow graphs, you can
- Watch "Signal-Flow Graphs in 12 short lessons" on https://tube.switch.ch/channels/d206c96c?order=episodes .
- See signalflowgrapher in action with a transistor-circuit analysis example on https://tube.switch.ch/videos/609c0510 .
- Read our papers, https://link.springer.com/article/10.1007%2Fs10470-018-1131-7 and http://rdcu.be/naw5 .

## Drawing and editing graphs

- Draw nodes by double-clicking on the canvas. 
- Select a node by clicking on it and giving it a name in the "Name" field. The name is just a name and has no mathemathical meaning.
- Select two (or more) objects by Shift-clicking on the additional objects.
- Select many objects by pressing Alt while drwaing a rectangle.
- Select everything with Ctrl-A.
- Deselect everything with Esc.
- Move selected objects by dragging them with the mouse. If your plan is to move nodes and branches together, move the selection by dragging a node.
- Things will snap to the grid. To disable snapping while moving, press Ctrl.
- Draw branches between two nodes by (a) selecting two branches and pressing the "Insert Branch" button or (b) by clicking on the first node and Ctrl-clicking on the second node.
- Select a branch by clicking on it and giving it a weight in the "Weight" field. The weight will be used in symbolic computations and must be a valid SymPy expression. The background of the "Weight" field becomes green if this condition is fulfilled.
- When a branch is selected, you see the handles of its curve shape. Move the handles to change the branch's curve shape.
- If everything is off grid after loading a file, select all and drag a node back to the grid.
- To move the canvas, click and drag it.
- Beware: Ctrl-X would delete something, but if only one node or one branch is selected, then the focus of the tool is on the "Name" or "Weight" field and Ctrl-A/Ctrl-X will be applied there. So deleting a single node or branch is only possible by pressing the "Remove" button.

## Exports

- To calculate a transfer function, select two nodes. If two nodes are selected and all branches on the graph have valid SymPy expressions as weights, the "Generate Mason" button becomes pressable. Press it, and the "Evaluated Output" shows the transfer function. The "Output" contains the Python code required to generate that result. It is already copied and can be pasted in another tool with Ctrl-V. We recommend a Jupyter notebook.
- To create LaTeX/TikZ files, press "Generate TikZ". This will let you save a .tex file with a name of your choice. If not there already, it will also write an sfgstyle.tex file containing some definitions for LaTeX. To get a nice PDF version, compile your .tex file with LaTeX.

## Graph operations

- The graph operations only work if the graph has the proper shape, defined branches, and the correct objects are selected.
- For "Scale Path", select one or more nodes.
- For the rest, watch Episode 3 of "Signal-Flow Graphs in 12 short lessons" on https://tube.switch.ch/channels/d206c96c?order=episodes and experiment.

