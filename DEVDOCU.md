# Developer Documentation for V2.0

## The Existing Application Structure
<img width="4484" height="6524" alt="Klassendiagramm drawio" src="https://github.com/user-attachments/assets/fc1df77d-18cf-41a4-a87c-2e434fd297f7" />


This class diagram provides an overview of the existing application structure. Because the dependencies are very complex, the diagram was simplified:
- All attributes and methods were omitted.
- Only inheritance relationships are shown.
- Only internal modules/classes are displayed; external libraries (e.g., PyQt/PySide, SymPy, Python standard library) are excluded.
- Test classes are omitted, showing only their packages.


## Bug Fixes and Improvements

### Off-Grid-Bug
The bug caused nodes in the Signalflow graph to lose their grid alignment after saving and reopening a file because the grid position was never stored.

#### Fix:
1. Update JSON schema in class `JSONValidator`:
```Python
...
    },
    "grid": {
        "type": "array",
        "items": {"type": "integer"},
        "minItems": 2,
        "maxItems": 2
    }
},
"required": [
    "nodes",
    "branches"
]
}
```
2. Add grid position to the model:

<img width="1564" height="776" alt="Klassendiagramm_Model drawio" src="https://github.com/user-attachments/assets/7bad6655-6b06-4caf-914d-29367fc9be71" />


3. Add grid position handling as shown below 
<img width="6364" height="2448" alt="Sequenzdiagramm_load_nachUpgrade drawio" src="https://github.com/user-attachments/assets/2c65d5f5-6df9-46c0-bb1b-f57991ca8905" />

<img width="4388" height="1288" alt="Sequenzdiagramm_save_nachUpgrade drawio" src="https://github.com/user-attachments/assets/0e5e714b-a2c6-44eb-a3b5-08d4367fa3e7" />



### Undo-Redo Issues
This bug affects the undo‑redo functionality of the Signalflowgrapher. When a user deletes a node and then undoes the deletion, the node is restored at the wrong position if the grid was moved between the delete and the undo. This happens because grid moves only shift the positions of nodes that are currently visible; deleted nodes are invisible and therefore not updated.

#### Fix:
The command classes `removeNodeCommand`, `createNodeCommand`, `removeBranchCommand`, and `createBranchCommand` must be changed:

1. When deleting a node or branch, store the current grid position.
2. When restoring, compute the delta between the old and new grid positions and adjust both the node positions and the branch‑spline positions accordingly.

The implementation example for `removeNodeCommand` is shown below, with the new code marked by the comment `#new`:
```Python
from signalflowgrapher.commands.command_handler import Command
from signalflowgrapher.model.model import ObservableGraph, PositionedNode, Model


class RemoveNodeCommand(Command):
    def __init__(self, graph: ObservableGraph, node: PositionedNode, model: Model):
        self.__graph = graph
        self.__node = node
        self.__model = model                                        #new
        self.__gridpos_atCreation = self.__model.get_grid_position()#new

    def undo(self):
        # Restore node position
        gridpos_new = self.__model.get_grid_position()              #new
        dx = gridpos_new[0] - self.__gridpos_atCreation[0]          #new
        dy = gridpos_new[1] - self.__gridpos_atCreation[1]          #new
        self.__node.move(dx, dy)                                    #new  
        self.__gridpos_atCreation = gridpos_new                     #new

        # Readd node to graph
        self.__graph.add_node(self.__node)

    def redo(self):
        # Remove node
        self.__node.remove()
        # Grid position reset (No position correction is necessary as long as the node is not removed.)
        self.__gridpos_atCreation = self.__model.get_grid_position()#new
```

### Error handling for invalid Sympy expressions
Issue #40 reported that the Signalflowgrapher ignored the "Generate Mason" button when given invalid SymPy expressions. Further investigation showed the same problem affected the "Generate TikZ" button and all other graph operations that parse SymPy strings.

#### Fix:

To fix this, a error‑handling strategy was added to show clear messages to users. The parsing now uses `sympy.parsing.sympy_parser.parse_expr`, which raises an exception for invalid input. Instead of catching this directly (which would produce a generic error), three new helper methods ( `functions—parse_weight`, `parse_factor`, and `parse_nodename`) were created in `signalflow_algorithms.common.utils`. Each calls `parse_expr`, catches its exception, and re‑raises a new, user‑friendly exception that includes the offending expression and its context (node or branch).

These helpers are used throughout the relevant classes, ensuring that any invalid SymPy expression triggers a helpful error dialog. In the SideWidget class, the exception is caught and displayed to the user in a QMessageBox, indicating exactly which node or branch contains the bad expression. As shown below: 

<img width="1171" height="813" alt="sympy_error_box" src="https://github.com/user-attachments/assets/d44a38da-ff46-4fc4-81f3-112c29a831d9" />


### Conflicting Keyboard Shortcuts
In V1.0 of the Signalflow Grapher, keyboard shortcuts conflicted because selecting a node or branch automatically focused the name or weight text field. Consequently, global shortcuts like `Del` and `Ctrl+A` were captured by the text field, preventing actions such as deleting a selected node (the Del key erased the text instead).

#### Fix:
To fix this while still allowing inline editing, the shortcuts were changed to `Ctrl+Shift+Del` for deleting and `Ctrl+Shift+A` for select all. These updates are made in **main_window.ui** under each `<property name="shortcut">` element.

### Invert Path Problem

<img width="493" height="276" alt="invert_path" src="https://github.com/user-attachments/assets/9be39c75-a2a9-4223-90b2-0391b630711e" />


When the user hovers over the "Invert Path" button, the tooltip (see above) says that only a single branch should be selected. If multiple branches are selected, the button remains enabled, allowing a click that causes errors.

#### Fix: 
In the SideWidget class, where the conditional action for the "Invert Path" button is registered, the condition `SpecificNumBranchesSelected(1)` was added. This makes the button active only when exactly one branch is selected.


### New Feature: Center Graph
This new feature lets users center the graph in the graph field. It's handy when the graph has been panned off‑screen and the user wants to bring it back quickly.

- In **main_window.ui**, the **"View"** menu gets a new `QAction` called **"Center Graph"** with the shortcut `Alt+C`.
- The GraphField class receives a `center_graph()` method that:
    1. Computes the graph's bounding box.
    2. Shifts the grid so the graph appears centered within the visible area of the graph field.
    

### New Feature: Copy, Cut, and Paste
This new feature adds copy, cut, and paste actions for nodes and branches in the Signalflowgrapher.

- **UI changes:** The "Edit" menu in **main_window.ui** now includes `QAction` items "Copy", "Cut", and "Paste" with shortcuts `Ctrl+Shift+C`, `Ctrl+Shift+X`, and `Ctrl+Shift+V` to avoid conflicts with text‑field shortcuts.

- **Implementation:**
    - "Copy" and "Cut" serialize the selected nodes/branches to a JSON string and place it on the operating‑system clipboard.
    - "Cut" also removes the selected elements from the graph.
    - "Paste" reads the JSON from the clipboard, deserializes it back into node/branch objects, and inserts them at the current mouse position in the graph canvas.

- **Benefits:**
    - Users can duplicate parts of a graph quickly without manual recreation.
    - The JSON‑based clipboard allows copying between different instances of the Signalflow Graph editor, similar to file‑save/load logic but using the system clipboard instead of a file.

The involved classes and their new/updated methods are illustrated below, with the new additions highlighted in green.

<img width="3684" height="2044" alt="UML_copy_paste drawio" src="https://github.com/user-attachments/assets/a346e18b-8fef-4daa-905b-a5b1dcfa5f87" />


## Porting to Qt6
For Qt6 you can use either PyQt6 or PySide6 as the binding. Pyside6 was chosen for this project, because it is backed by the Qt Company.

### Porting Process
- **Replace all PyQt5 imports with the corresponding PySide6 modules** (e.g., `PySide6.QtCore`, `QtGui`, `QtWidgets`). The old "collective" module `PyQt5.Qt` no longer exists, so each class must be imported explicitly. `pyqtSignal` is swapped for `Signal` from `PySide6.QtCore`.
- **High‑DPI handling** is now automatic in Qt6; no manual scaling code is needed. Scaling works dynamically across monitors, though minor raster‑line thickness artifacts appear at uncommon scaling factors (25 %/75 %). They do not affect functionality.
- **.ui files** are no longer loaded at runtime. Instead, they are converted to Python code with the command `pyside6-uic main_window.ui -o ui_main_window.py`. ⚠️ Only the .ui files should be edited, not the generated classes!
- **Mouse‑position API** changed: `QMouseEvent.pos()` / `globalPos()` (returning `QPoint` with integer coordinates) are replaced by `position()` / `globalPosition()` (returning `QPointF` with floats). The code now calls `.toPoint()` where integer coordinates are required.
- **Multiple inheritance** of Qt widgets that worked indirectly in PyQt5 fails in PySide6/Qt6. The `LabelWidget` class was refactored to drop inheritance from `GraphItem` and instead incorporate its methods/attributes directly, while now inheriting from `ObjectObservable`. As shown below:

    <img width="2768" height="1776" alt="UML_pyside6_labelwidget drawio" src="https://github.com/user-attachments/assets/97a93855-1ba4-4d0e-a60d-bf4e49dd5343" />


- **load non‑Python assets** The original fbs tool does not support PySide6 (except in a paid version). The V2.0 uses `importlib.resources` (standard library since Python 3.7) to load non‑Python assets. Publishing on PyPI would be an alternative in the future, allowing users to simply install via pip.
- **Miscellaneous changes:** `.exec_()` becomes `.exec()`, and Qt enumerations are now scoped (e.g., `Qt.Key_Control` → `Qt.Key.Key_Control`).



