# Developer Documentation for V3.0

V3.0 adds **zoom** (to see a whole graph that is larger than the window) and a **mini map**. Both require a clean separation between model coordinates and what is drawn on screen. This section is the working plan; it is updated at the end of every step. The documentation of V2.0 follows below.

| Step | Title | Status |
|---|---|---|
| 0 | Safety net (tests, consistency checker, snapshots) | done, ready for manual test |
| 1 | Fix inconsistencies and known bugs | planned |
| 2 | Idempotent widget refresh | planned |
| 3 | `ViewTransform` at identity | planned |
| 4 | Pan becomes a view offset | planned |
| 5 | Zoom (wheel and keyboard, everything scales with z) | planned |
| 6 | Mini map | planned |

## Decisions

- **Zoom range 10% to 100%.** The main use case is zooming out to see the whole graph. There is no zoom above 100%. Default is 100%.
- **Everything scales with z**, exactly as in the TikZ output: node size, circle width, branch pen width, arrow size, spline handle size, label font size, label offsets and the grid. The size relationship between lines, text and nodes is therefore identical at every zoom level.
- **Zoom input:** keyboard shortcuts for zoom in, zoom out and reset, and **Ctrl + mouse wheel** (zooming about the mouse pointer). The plain wheel is left unused.
- **The model never contains zoom.** Model coordinates stay in "world units" (= pixels at 100%). Saved files, the clipboard, the TikZ export and the undo stack do not depend on the zoom level. The zoom level is not stored in the file.
- **Pan becomes a view offset** (step 4, agreed), so navigation no longer rewrites the model.
- **Mini map** can be switched on and off (step 6).

## Coordinate handling in V2.0 (summary of the analysis)

- There is **one** coordinate space: model coordinates equal the pixel coordinates of the `GraphField` widget. There is no world-to-view transform.
- **Panning rewrites the model.** `Model.move_graph_relative(dx, dy)` adds the delta to every node and to both spline points of every branch. The sum is kept in `Model.__gridpos` (saved as `grid_pos`) to keep the grid phase, and the Create/Remove commands (`gridpos_atCreation`) use it to correct objects that were detached during a pan.
- The pan amount is stored **four times**: `Model.__gridpos`, `GraphField.__grid_offset`, `FixedGrid.__offset` and `FixedGridWidget.__offset`.
- **Widgets are delta-synchronised**: after creation, `NodeWidget` and the pan handling of `LabelWidget`/`BranchWidget` move by integer deltas. `BranchWidget` and the spline handles keep `int`-truncated copies of model points.

| Datum | Stored in | Absolute / relative |
|---|---|---|
| Node position | `PositionedNode.__x/__y` | absolute, canvas pixels, `int` (schema: integer) |
| Node label offset | `LabeledObject._dx/_dy` | relative to the node centre |
| Spline points | `CurvedBranch.__spline1/2_x/y` | **absolute** (the API is delta-based), may be `float` |
| Branch label offset | `LabeledObject._dx/_dy` | relative to the Bezier mid point (computed by `BranchWidget`) |
| Pan | `Model.__gridpos_x/_y` | running sum of all pans |
| Undo payloads | `Move*Command`, `TransformBranchCommand` | deltas |
| Clipboard, JSON, TikZ | raw model values | absolute + relative as above |

Controller-level invariant: a spline point moves together with its node (`MainController.move_node`). The detailed analysis, with sequence diagrams for create, move, pan, copy/paste, delete/undo and save/load, is kept alongside the project (Claude doc "SignalFlowGrapher - Coordinate Handling Analysis").

## Plan

Every step is one reviewable change set. After each step: run the automated tests, run the manual checklist for that step, then review. The next step starts only after approval.

### Step 0: Safety net (done)

No behaviour change of the application. Adds tests under `src/signalflowgrapher/tests/gui/`:

| File | Purpose |
|---|---|
| `harness.py` | Real `GraphField`, `Model`, controllers and `CommandHandler` in an offscreen window, driven with synthetic mouse events (double click, drag, pan, Ctrl+click, copy/paste, delete, undo/redo, save/load). Uses deterministic ids. |
| `consistency.py` | Compares every widget with the model: node centres, branch caches and Bezier mid points, label positions, spline handles, grid offsets, widget/label maps, graph topology. |
| `test_consistency_checker.py` | Fault injection: 14 deliberately broken states must each be detected ("tests for the tests"). |
| `test_gui_operations.py` | Scenario tests with exact expectations (create, move, handles, labels, pan, center, copy/paste, delete, undo/redo, save/load). |
| `test_gui_fuzz.py` | Seeded random operation sequences with a consistency check after every operation. `SFG_FUZZ_SEEDS` and `SFG_FUZZ_STEPS` scale it up for a soak run. |
| `test_golden.py`, `golden/*.json` | For the 6 example graphs: model, canonical TikZ export and widget geometry at 100% / no pan. Plus a rendering-reproducibility test. |
| `test_io_roundtrip.py` | Load/save round trips, old files without `grid_pos`, schema behaviour. |
| `render_snapshots.py` | Renders scenes to PNG and compares two directories pixel by pixel (for A/B checks before and after a step). |

Run the tests from `src/`:

```
pip install -r ../requirements/base.txt          # dependencies (pytest is optional)
export QT_QPA_PLATFORM=offscreen                 # set automatically by the harness
python -m pytest signalflowgrapher/tests         # or: python -m unittest discover -s signalflowgrapher/tests -t .
```

Expected result at the end of step 0: everything passes, except the **6 expected failures** that document known bugs (next section). Two older tests in `tests/algorithms/test_graph_operations.py` (`TestEliminateNodeOperation.test_get_new_paths` and `test_get_self_loops`) were failing before V3.0 because they patched a module `signalflow_algorithms`, from which the algorithms had been moved into `signalflowgrapher/algorithms` without adapting the tests. Their patch targets were corrected in step 0.

Pixel A/B check before and after a step:

```
python -m signalflowgrapher.tests.gui.render_snapshots render /tmp/before
# ... apply the step ...
python -m signalflowgrapher.tests.gui.render_snapshots render /tmp/after
python -m signalflowgrapher.tests.gui.render_snapshots compare /tmp/before /tmp/after
```

If a Qt version or font change moves widget geometry, regenerate the golden files with `SFG_UPDATE_GOLDEN=1` and review the diff.

#### Known issues found by the safety net

Each is pinned by a test decorated with `@expectedFailure`. The step that fixes it must remove the decorator (an unexpected success is reported as a failure).

| # | Issue | Test | Fix in |
|---|---|---|---|
| K1 | After "move node, undo, redo" (and in some multi-selection undo cases) the **branch label stays at the old position**: redo applies the branch transform before the node move, and branch labels only react to branch events. | `test_known_bug_redo_of_move_leaves_branch_label_stale`, `test_known_bug_random_operations_branch_labels`; the fuzz test tolerates it via `STALE_BRANCH_LABELS` in `consistency.py` | step 2 (remove the tolerance too) |
| K2 | **Paste after a pan is off-grid**: paste snaps to a grid that ignores the pan offset. | `test_known_bug_paste_after_pan_is_off_grid` | 1b |
| K3 | **Paste loses node label offsets** (pasted nodes get `(0, 30)`). | `test_known_bug_paste_loses_node_label_offset` | 1b |
| K4 | **Ctrl+click between two nodes at the same position** raises `ValueError: Unable to calculate angle`; nothing happens for the user. | `test_known_bug_branch_between_coincident_nodes_raises` | 1e |
| K5 | **Invalid files raise `TypeError`** instead of `ValidationError` (`validate_json` creates the exception without its message). | `test_known_bug_invalid_file_raises_validation_error` | 1c |
| K6 | The TikZ export is **not byte-identical between runs** (nodes are numbered in set-iteration order). Harmless; tests compare a canonical form. | `snapshot.tikz_snapshot` | 1f (optional: sort) |

Not a bug (checked): `QPoint(float, float)` in the spline handle's `node_moved_event` truncates silently in PySide6 6.12 instead of raising. Step 1a is therefore a defensive cleanup only.

#### Manual checklist for step 0 (on the unchanged application)

Run once, so that "works" is agreed before anything changes. Use a fresh window.

1. Double-click on the empty canvas: a node appears, snapped to the grid.
2. Create four nodes. Select one, Ctrl+click another: a branch appears with an arrow and weight label.
3. Ctrl+click the same selected node: a self-loop appears.
4. Create a second branch between the same two nodes: it is bent differently from the first.
5. Drag a node: it snaps to the grid, attached branches follow, the branch end near the node moves with it.
6. Hold Ctrl while dragging a node: free movement without snapping.
7. Select two connected nodes and drag one: both move, the branch keeps its shape.
8. Select a branch: two spline handles appear. Drag each: the curve changes, the handle moves opposite to the curve control point.
9. Drag a node label and a branch label: they move, and keep their offset when the node/branch moves later.
10. Drag the empty canvas: everything pans, the grid follows. Create a node afterwards: it is on the panned grid.
11. Use "Center graph": the graph is centred in the window.
12. Alt+drag a rectangle: the enclosed nodes and branches are selected.
13. Undo and redo after each of 5, 8, 9. Note anything that looks wrong (known: a branch label may stay behind after redo of a node move, K1).
14. Copy, paste (Ctrl+C / Ctrl+V) at a different mouse position, cut and paste.
15. Delete a node with attached branches, pan, undo: everything returns at the panned position.
16. Save, close, open the file: the graph and the grid phase are unchanged.
17. Export TikZ and compile it: the picture matches the window.
18. Open each example from `resources/examples`: they look correct, nothing is selected oddly, nothing is cut off.

### Step 1: Fix inconsistencies and known bugs

Separate small commits, each with its test flipped from `@expectedFailure` to a normal test.

- **1a** `int()` in `SplineHandleWidget.node_moved_event` (defensive).
- **1b** Paste: snap with the grid offset (use `FixedGrid.get_grid_position`) and restore node label offsets (K2, K3).
- **1c** JSON schema: validator and `schema.json` agree (`grid_pos`, `version`), `validate_json` raises a proper `ValidationError`, old files keep loading (K5).
- **1d** `Model` becomes the single owner of pan and grid state; remove the copies in `GraphField`, `FixedGrid` and `FixedGridWidget`; one grid-size constant.
- **1e** Ctrl+click between coincident nodes does not raise (K4).
- **1f** Optional: sort nodes/branches in the TikZ export so that the output is byte-identical between runs (K6).
- *Review:* pan, paste, undo/redo after pan, loading old files; automated tests green.

### Step 2: Idempotent widget refresh (no zoom yet)

- A `refresh()` per widget that derives its geometry from the model, replacing delta synchronisation (`move_relative`): 2a nodes and labels, 2b branches with `QPointF` caches, 2c spline handles, 2d pan refreshes everything.
- Fixes K1 by construction (labels are derived from the final state, not from event order). Remove `STALE_BRANCH_LABELS`.
- *Tests:* consistency checker and fuzz tests without tolerance; golden files unchanged; PNG A/B identical to step 0.

### Step 3: `ViewTransform` at identity (z = 1, offset = 0)

- New class `ViewTransform` in the GUI layer with `to_screen`, `to_world`, `scale_delta`, change signal.
- Route widget placement and all input conversions through it: double click, drags (nodes, labels, handles), paste, `center_graph`, grid snapping in world units, grid drawing.
- *Tests:* identical to step 2 (PNG A/B and golden). Unit tests of the transform at other values of z. The consistency checker is adapted once to go through the transform.

### Step 4: Pan becomes a view offset

- Panning changes the view offset only; the model is no longer mutated by navigation. `Model.__gridpos`-based corrections (`gridpos_atCreation` in the four Create/Remove commands) are removed. Old files stay loadable: `grid_pos` becomes a constant world-grid phase.
- Done before zoom because zooming about the mouse pointer needs fractional pan, which would break integer model coordinates.
- *Tests:* save, pan, load; undo after pan; delete, pan, undo; golden files unchanged except the intentionally changed pan semantics (document the diff).

### Step 5: Zoom (10% to 100%)

- **5a** Programmatic zoom (debug shortcut): everything scales with z (node size, circle width, pen widths, arrow and handle sizes, label font and offsets, grid spacing). Prefer one painter transform per widget over scattering `* z` through constants.
- **5b** Zoom input: keyboard shortcuts for zoom in, zoom out and reset to 100% (check the existing shortcuts in `gui/ui/main_window.ui` first), and Ctrl + mouse wheel zooming about the pointer (`t' = t + c * (1 - z'/z)`). Steps in a geometric progression, limits 10% and 100%, zoom level shown in the status bar. A "zoom to fit" command is proposed for the main use case.
- **5c** Zoom-dependent behaviour to decide at the review of 5a (proposals): a minimum click target for tiny nodes at low zoom, hiding grid lines when their spacing is below about 6 px, and `Alt`-drag rubber band working in screen space.
- **5d** Verify that save, TikZ, clipboard and PNG export do not depend on the zoom level (PNG export: current view or always 100%, to be decided).
- *Tests:* at z = 1 identical to step 4; at other z every widget equals `to_screen(model)`; save/TikZ identical at any zoom.

### Step 6: Mini map

- A small overlay widget showing the whole graph (simplified nodes and branches drawn from the model) and a rectangle for the visible area. Click and drag in the mini map pans the view. Switch on/off by menu entry and shortcut; the setting is remembered between sessions, it is not part of the graph file.
- Needs the view offset from step 4 and the zoom from step 5 (the visible rectangle is `to_world(viewport)`).
- *Tests:* mini map content equals the model bounding box; the visible rectangle matches the view at several zoom levels; toggling does not change the model.

---

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


## Test locally

From the directory `signalflowgrapher/src/`, do:

`pip install -e signalflowgrapher`

After the test:

`pip uninstall signalflowgrapher`

## Upload to TestPyPI

`pip install build twine`

`python -m build`

`python -m twine check dist/*`

`python -m twine upload --repository testpypi dist/*`

`conda create --name test1 python`

`conda activate test1`

`python -m pip cache purge`

`pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ signalflowgrapher`

After the test:

`pip uninstall signalflowgrapher`

## Upload to TestPyPI

`python -m twine upload dist/*`
