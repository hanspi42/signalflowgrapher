# Developer Documentation for V3.0

V3.0 adds **zoom** (to see a whole graph that is larger than the window) and a **mini map**. Both require a clean separation between model coordinates and what is drawn on screen. This section is the working plan; it is updated at the end of every step. The documentation of V2.0 follows below.

| Step | Title | Status |
|---|---|---|
| 0 | Safety net (tests, consistency checker, snapshots) | done, tested |
| 1 | Fix inconsistencies and known bugs, new file version | done, tested |
| 2 | Idempotent widget refresh | done, tested |
| 2b | Remove deprecated Qt and library calls | done, tested |
| 3 | `ViewTransform` at identity | done, tested |
| 4 | Pan becomes a view offset | done, tested |
| 5 | Zoom (wheel and keyboard, everything scales with z) | done, tested |
| 5b | Zoom up to 200%, keyboard shortcuts without numpad | done, tested |
| 6 | Mini map | done, ready for manual test |

## Decisions

- **Zoom range 10% to 200%** (it was 10% to 100% in the first version of step 5, changed after its review). The main use is zooming out to see the whole graph; up to 200% is for working on details. Default is 100%.
- **Everything scales with z**, exactly as in the TikZ output: node size, circle width, branch pen width, arrow size, spline handle size, label font size, label offsets and the grid. The size relationship between lines, text and nodes is therefore identical at every zoom level.
- **Zoom input:** keyboard shortcuts for zoom in, zoom out and reset, and **Ctrl + mouse wheel** (zooming about the mouse pointer). The plain wheel is left unused.
- **The model never contains zoom.** Model coordinates stay in "world units" (= pixels at 100%). Saved files, the clipboard, the TikZ export and the undo stack do not depend on the zoom level. The zoom level is not stored in the file.
- **Pan becomes a view offset** (step 4, agreed), so navigation no longer rewrites the model. A saved file remembers the part of the graph that was shown (`view_origin`), not the zoom.
- **Mini map** (step 6): shows all nodes and branches (no labels, no arrows) and a rectangle for the visible area; click and drag moves the view; it can be switched on and off, and the choice is remembered between sessions (not in the graph file).

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

File format: `"version": "3.0"` is written since step 1g; `grid_pos` (not `grid`, as the V2.0 text below says) holds the pan. Controller-level invariant: a spline point moves together with its node (`MainController.move_node`). The detailed analysis, with sequence diagrams for create, move, pan, copy/paste, delete/undo and save/load, is kept alongside the project (Claude doc "SignalFlowGrapher - Coordinate Handling Analysis").

## Plan

Every step is one reviewable change set. After each step: run the automated tests, run the manual checklist for that step, then review. The next step starts only after approval.

### Step 0: Safety net (done)

No behaviour change of the application. Adds tests under `src/signalflowgrapher/tests/gui/`:

| File | Purpose |
|---|---|
| `harness.py` | Real `GraphField`, `Model`, controllers and `CommandHandler` in an offscreen window, driven with synthetic mouse events (double click, drag, pan, Ctrl+click, copy/paste, delete, undo/redo, save/load). Uses deterministic ids. |
| `consistency.py` | Compares every widget with the model through the view transform: node centres, branch caches and Bezier mid points, label positions, spline handles, grid offsets, widget/label maps, integer node coordinates and label offsets, the view origin that the model remembers, glyph sizes (node widgets, label fonts, branch widgets cover their curve and have the current zoom), graph topology. |
| `test_consistency_checker.py` | Fault injection: 17 deliberately broken states must each be detected ("tests for the tests"). |
| `test_gui_operations.py` | Scenario tests with exact expectations (create, move, handles, labels, pan, center, copy/paste, delete, undo/redo, save/load). |
| `test_gui_fuzz.py` | Seeded random operation sequences with a consistency check after every operation. `SFG_FUZZ_SEEDS` and `SFG_FUZZ_STEPS` scale it up for a soak run. |
| `test_deprecations.py`, `deprecation_scenario.py` | Runs a broad scenario in a fresh process and fails if the application's own modules issue a `DeprecationWarning` (also at import time). |
| `test_view_transform.py` | Step 3: the `ViewTransform` class, and every conversion between world and screen coordinates with real zoom and offset values (widgets, mouse input, grid snapping and drawing, paste, pan, center). |
| `test_pan_view_offset.py` | Step 4: a pan changes only the view; the view is remembered in the file; files of the old pan semantics look the same pixel by pixel. |
| `test_zoom.py` | Step 5: zoom operations and limits, wheel, keyboard actions in the real main window, measured scaling of every drawn part, minimum click areas, grid hiding, zoom to fit, exports independent of the zoom. |
| `test_minimap.py` | Step 6: what the mini map shows (all nodes and branches, no labels, no arrows, the shown rectangle), how it is drawn (measured in its picture), clicking and dragging, overlay behaviour, the menu entry and shortcut, the remembered choice. |
| `test_widget_refresh.py` | Step 2: refresh is idempotent, events carry no state, event order does not matter, a pan does not rebuild branch shapes. |
| `test_golden.py`, `golden/*.json` | For the 6 example graphs: model, canonical TikZ export and widget geometry at 100% / no pan. Plus a rendering-reproducibility test. |
| `test_io_roundtrip.py` | Load/save round trips, old files without `grid_pos`, schema behaviour. |
| `render_snapshots.py` | Renders scenes to PNG and compares two directories pixel by pixel (for A/B checks before and after a step). |

Run the tests from `src/`:

```
pip install -r ../requirements/base.txt          # dependencies (pytest is optional)
export QT_QPA_PLATFORM=offscreen                 # set automatically by the harness
python -m pytest signalflowgrapher/tests         # or: python -m unittest discover -s signalflowgrapher/tests -t .
```

Expected result: everything passes. Known but unfixed defects are documented as tests named `test_known_bug_*` with `@expectedFailure`; at the end of step 0 there were 6 of them, after step 1 there were 2, after step 2 there are none. Two older tests in `tests/algorithms/test_graph_operations.py` (`TestEliminateNodeOperation.test_get_new_paths` and `test_get_self_loops`) were failing before V3.0 because they patched a module `signalflow_algorithms`, from which the algorithms had been moved into `signalflowgrapher/algorithms` without adapting the tests. Their patch targets were corrected in step 0.

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

| # | Issue | Test | Status |
|---|---|---|---|
| K1 | After "move node, undo, redo" (and in some multi-selection undo cases) the **branch label stays at the old position**: redo applies the branch transform before the node move, and branch labels only react to branch events. | `test_redo_of_move_updates_the_branch_label`, `test_sequences_that_used_to_leave_stale_branch_labels` | fixed in step 2 (the tolerance `STALE_BRANCH_LABELS` was removed from the checker) |
| K2 | **Paste after a pan was off-grid**: paste snapped to a grid that ignored the pan offset. | `test_paste_after_pan_stays_on_the_panned_grid` | fixed in step 1b |
| K3 | **Paste lost node label offsets** (pasted nodes got `(0, 30)`). | `test_paste_keeps_node_label_offset` | fixed in step 1b |
| K4 | **Ctrl+click between two nodes at the same position** raised `ValueError: Unable to calculate angle` (and a second such branch would have looped forever). A second node cannot be created on an occupied point with the mouse (the widget under the pointer takes the double click), so this is only reachable by other means, for example dragging nodes onto each other; there is no manual check for it. | `TestCoincidentNodes` | fixed in step 1e |
| K5 | **Invalid files raised `TypeError`** instead of `ValidationError` (`validate_json` created the exception without its message). | `test_invalid_file_raises_validation_error_with_message` | fixed in step 1c |
| K6 | The TikZ export was **not byte-identical between runs** (nodes were numbered in set-iteration order). | `TestTikzExport` | fixed in step 1f |

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
13. Undo and redo after each of 5, 8, 9. Note anything that looks wrong (in V2.0 and up to step 1 a branch label could stay behind after redo of a node move, K1; fixed in step 2).
14. Copy, paste (Ctrl+C / Ctrl+V) at a different mouse position, cut and paste.
15. Delete a node with attached branches, pan, undo: everything returns at the panned position.
16. Save, close, open the file: the graph and the grid phase are unchanged.
17. Export TikZ and compile it: the picture matches the window.
18. Open each example from `resources/examples`: they look correct, nothing is selected oddly, nothing is cut off.

### Step 1: Fix inconsistencies and known bugs, new file version (done)

Separate small changes; the application behaves as before except for the fixed bugs and the new file version. The tests of K2 to K6 were changed from `@expectedFailure` to normal tests.

- **1a** `int()` in `SplineHandleWidget.node_moved_event` (defensive; PySide6 6.12 truncates floats silently anyway). Test: `test_handle_follows_node_with_integer_origin`.
- **1b** Paste (K2, K3): snaps with the pan offset, using the fixed grid (Ctrl is held while pasting, which switches the active grid off, so the paste code uses `GraphField.__fixed_grid` explicitly), and restores node label offsets. `MainController.create_node` got optional parameters `label_dx` (default 0) and `label_dy` (default 30).
- **1c** JSON schema (K5): the validator now declares `grid_pos` (the key the writer has always used; the old declaration `grid` was never matched, so `grid_pos` was not validated). `grid_pos` and `version` stay optional. `validate_json` re-raises the original `ValidationError` with its message. `resources/schema.json` is regenerated from the validator and a test keeps them equal (`JSONValidator.schema`). Old files keep loading.
- **1d** The model is the only owner of the pan. `GraphField.__grid_offset` and the copies in `FixedGrid` and `FixedGridWidget` are removed; `FixedGrid(size, offset_source)` and `FixedGridWidget(size, offset_source)` read `Model.get_grid_position` when they snap or paint, and `GraphField` triggers a repaint on `GraphMovedEvent` and `GraphChangedEvent`. One grid size constant, `GRID_SIZE` in `gui/grid.py`. The consistency checker verifies that `GraphField` has no copy of the pan state.
- **1e** Branch between nodes at the same position (K4): the branch is created as an arc below the nodes with label offset `(0, 30)`, and the step size of the overlap loop in `create_branch_auto_pos` has a minimum of 30 for coinciding nodes (it was 0, so the loop never ended). Layouts for all other node positions are unchanged.
- **1f** Old tests repaired in step 0. The TikZ export sorts nodes and branches by id, so the numbering is reproducible (K6).
- **1g** File format version: files are written with `"version": "3.0"` (`FILE_FORMAT_VERSION` in `io/json.py`). Files with version `2.0`, any other version or no version are still read; there is no version check on load. The version of the Python package in `pyproject.toml` (2.1.3) is not changed by this step; it belongs to the release.
- The fuzz tests no longer avoid coinciding nodes.

*Manual checklist for step 1* (in addition to the checklist of step 0):

1. Pan the canvas by an amount that is not a multiple of 30 pixels, then select some nodes, copy and paste: the pasted nodes lie on the grid lines that are visible on the canvas.
2. Drag the label of a node away from its default place, copy the node, paste it: the pasted node's label has the same offset.
3. Pan, save, open the file: grid lines and nodes are at the same place. Open the saved file in a text editor: `"version": "3.0"` and `"grid_pos"` are present.
4. Open files from `resources/examples` (version 2.0) and a file without `grid_pos`: both load.
5. Damage a file (for example write `"x": 1.5` for a node) and open it: the dialog "Error while opening file. See log for details" appears, the log names the reason, and the graph that was open stays unchanged.
6. Pan with the mouse, Ctrl while dragging a node, "Center graph", "Toggle grid" (if available in your menu): the grid always stays aligned with the nodes.
7. Export TikZ twice from the same graph: the two files are identical.

### Step 2: Idempotent widget refresh (done)

No zoom yet; the application looks and behaves as before, except that K1 is fixed. Widgets no longer follow the model by adding up the deltas of events. Every widget has `refresh(force=False)`, which derives its position and shape from the **current state of the model**.

Rules (relied upon by steps 3 to 6):

1. `refresh()` is idempotent: the result depends only on the model, never on which events arrived, how often, or in which order. The `dx`/`dy` of an event are not used by any widget (`move_relative` was removed from `GraphItem` and `LabelWidget`).
2. `GraphField.refresh_widgets(force=False)` refreshes everything: nodes and branches, then handles, then labels (a label is placed relative to its owner widget, so owners come first). With `force=True` every widget is recomputed completely. A zoom change will be "refresh everything".
3. Event handlers only decide *which* widgets are affected and call their `refresh()`: a node move refreshes the node widget, the attached branch widgets, the handles of the node and the labels of the node **and of the attached branches** (that last part is the fix of K1).
4. `GraphMovedEvent` (pan) calls `refresh_widgets()`.

What changed, per widget:

| Widget | Before | Now |
|---|---|---|
| `NodeWidget` | moved by event deltas | `refresh()` places the centre on the node; also used when the widget is created |
| `BranchWidget` | cached int points updated per event, `graph_moved_event` moved the widget | constructor reads the model; `refresh()` reads all four points (start, end, spline1, spline2). Unchanged shape that was only moved (pan) is moved, not rebuilt (same result, much cheaper); otherwise `updateGeometry()` |
| Spline handles | origin and spline passed in at creation, updated per event | read from the model (`_model_origin()`, `_model_spline()`); `refresh()` rebuilds the geometry if either changed |
| `LabelWidget` | moved by delta on pan, repositioned on some events | `refresh()` repositions from the owner widget; branch labels react to node moves; `math.floor` instead of `int` so that a move of the owner by whole pixels moves the label by exactly that, also at negative coordinates |
| `BranchWidget.get_branch_middle` | path length recomputed at every call | middle point cached in `updateGeometry()` (otherwise every label refresh of a pan recomputed it: 45% slower pans) |

Deviations from the original plan:

- The branch widget caches **stay `QPoint`** (int-truncated). Switching to `QPointF` would change how fractional spline points are drawn and break the requirement that the output is pixel-identical to step 1. `QPointF` comes with step 3, when the transform makes fractions unavoidable.
- The step description said "2d: pan refreshes everything"; this is rule 4.

Checks done: all tests pass without any tolerance; the PNG renders of all 9 scenes are pixel-identical to step 1 (`render_snapshots compare`); the golden files are unchanged; 150 fuzz seeds of 100 steps (with undo, redo, delete, paste, handles) are clean; a pan step on a graph with 168 nodes and 216 branches takes the same time as before (about 47 ms in the offscreen test), a node move step as well.

*Manual checklist for step 2* (in addition to the earlier checklists):

1. Create two nodes with a branch, drag the branch label away, drag a node, press undo, then redo: the branch label moves with the branch at every step (this was K1).
2. Repeat 1 with several nodes selected, and with a node that has two branches.
3. Undo and redo a label drag, a spline handle drag, a paste, a delete: everything returns to where it was.
4. Select a branch (handles visible) and drag one of its nodes: the handle follows; then pan: handles, branch, labels and nodes move together.
5. Pan far to the left/top (until the graph is outside the window) and back: nothing has shifted relative to the rest (compare the label positions).
6. Open the largest example (`SC_analysis__schmid18/fig_12.sfg`) and pan and drag nodes: it should feel as fast as in step 1.
7. Look at all examples: they look exactly as before.

### Step 2b: Remove deprecated Qt and library calls (done)

The test runs produced hundreds of `DeprecationWarning`s from the application code. They are removed, so that real problems are not hidden in the noise and the program keeps working with future PySide6 versions. No change of behaviour.

| Where | Before | Now |
|---|---|---|
| `graph_item.py`, `branch_widget.py`, `label_widget.py` (7 places) | `event.globalPos()` | `event.globalPosition().toPoint()` (this is what `globalPos()` returned internally, so the positions are identical) |
| `label_widget.py` | `QFontDatabase()` instance to call `addApplicationFont` | the static call `QFontDatabase.addApplicationFont(...)` |
| `label_widget.py` | `importlib.resources.path(...)` | `resources.as_file(resources.files(...).joinpath(...))` (Python 3.9 and later; the project requires 3.10) |

Not changed: `tools/register.py` and `tools/deregister.py` also use `importlib.resources.path`. They change the operating system's file associations, are not covered by any test, and issue no warning in the test runs; they should be migrated when they can be tested on each operating system.

`test_deprecations.py` keeps it that way: it fails if any `DeprecationWarning` comes from a file of the application. Checked: the test fails on the step 2 code (77 warnings) and passes now; the renders of all 9 scenes are still pixel-identical to step 1; pytest and unittest report 0 warnings.

*Manual checklist for step 2b:* nothing new to look at in the window. Start the program from a terminal with `python -W default -m signalflowgrapher` (or your usual command with `-W default`), use it for a minute (create, drag, pan, labels, handles, open an example) and check that no `DeprecationWarning` appears in the terminal.

### Step 3: `ViewTransform` at identity (done)

The application still runs at zoom 1 and offset (0, 0), so it looks and behaves as before (pixel-identical renders, same timing). What changed is that no place assumes any more that model coordinates and screen pixels are the same thing.

**Two coordinate systems.**

- *World* coordinates are the coordinates of the model: node positions, spline points, label offsets. They are what files, the clipboard, the TikZ export and the undo stack contain. World coordinates never depend on the view.
- *Screen* coordinates are pixels of the `GraphField` widget: where widgets are placed and where mouse events happen.
- `ViewTransform` (`gui/view_transform.py`, owned by `GraphField`, available as `graph_field.view`) maps between them: `screen = zoom * world + offset`. It has `to_screen`, `to_world` (exact), `to_screen_point` (whole pixel), `to_world_delta`, `to_screen_delta`, `set(zoom, offset)`, `reset()` and the Qt signal `changed`. `GraphField` reacts to `changed` with `refresh_widgets(force=True)` and a repaint of the grid, so changing the view is "refresh everything" (step 2).

**Rules** (steps 4 to 6 build on them):

1. Widgets are placed from the model through the transform, never from other widgets' positions. All widgets use the one rule `ViewTransform.to_screen_point` (round down to a pixel), so a branch ends exactly at the node it belongs to. It rounds down instead of truncating towards zero as V2.0 did; this differs only for fractional negative coordinates (a spline at y = -110.5 is drawn at -111 instead of -110, off screen), and makes a move by whole pixels an exact translation.
2. Mouse input is converted at the boundary and nothing else in the program sees screen distances: double click and paste use `to_world`, drags use `to_world_delta` (`GraphField.__relative_grid_move`); a pan is a change of the view offset (`GraphField.__pan_view`, since step 4, in screen pixels, no conversion needed). The rubber band stays in screen space (it compares with widget geometry).
3. `Grid` works purely in world units: `relative_move(dx, dy, center)` takes the distance in world units and the world position of the dragged widget. Each draggable widget provides `get_world_center()` (node: exact model position; label: converted from its screen position; handle: mirrored spline point from the model). Moves are applied in whole world units; with a zoom a screen pixel is more than one unit, so the fraction is carried to the next mouse move (`Grid` deviation, now also for `NoneGrid` when Ctrl is held). Node coordinates and node label offsets therefore stay integers at every zoom, as the file format requires.
4. Label offsets are in world units and scale with the zoom (`to_screen_delta`).
5. The grid is drawn where the view maps the world grid lines: spacing `30 * zoom`, phase from the pan and the view offset.
6. What does **not** scale yet: sizes of glyphs (node circle, line widths, arrows, handle size, label font). That is step 5.

**Pan** was still a change of the model in this step (distance converted with `to_world_delta`, the fraction of a world unit carried to the next mouse move). This transitional code was replaced in step 4.

Deviation from the original plan: the caches of `BranchWidget` and the spline handles stay `QPoint` (now screen pixels from `to_screen_point`), not `QPointF`. With the pixel rule above, branch ends coincide with node widgets and the output at zoom 1 stays pixel-identical; `QPointF` is only worth it if sub-pixel curves are wanted at low zoom, to be decided at the review of step 5.

Checks done:

- All tests pass at identity with the checker adapted once to go through the transform; renders of all 9 scenes are pixel-identical to step 1; golden files unchanged; timing unchanged (pan step 45 to 50 ms on a graph with 168 nodes and 216 branches, as before).
- `test_view_transform.py` exercises 8 views (zoom 0.1 to 2, with and without offset): widgets follow the view, the model and the undo stack do not change with the view, the saved file does not depend on the view, double click, node/label/handle drags (grid and Ctrl), paste, pan and center produce the right world distances, node label offsets stay integers, the grid lines are drawn at the expected pixels (checked in the rendered picture).
- Mutation check: 14 deliberate breaks of single conversions (for example "drag distance not divided by the zoom", "paste position not converted", "grid drawn without zoom") are all caught by the tests.
- The fuzz tests also run with a random view that changes during the sequence (210 seeds of 100 steps: clean).

*Manual checklist for step 3:* at 100% nothing should look or behave differently, and there is no way to zoom in the window yet (the debug shortcut comes with step 5a). Repeat the checklists of steps 0 to 2 quickly, paying attention to: dragging nodes, labels and handles (snapping to the grid, Ctrl for free movement), panning with the mouse, "Center graph", paste at the mouse position after a pan, grid lines staying aligned with the nodes, and the look of the examples. Anything that is even one pixel different from step 2 is a regression.

### Step 4: Pan becomes a view offset (done)

Panning now changes only `ViewTransform.offset`. No coordinate of the graph changes by navigation any more, and the undo history is not involved. At zoom 1 the pictures are exactly what the old pan produced.

What changed:

| Part | Before | Now |
|---|---|---|
| `GraphField` pan and "Center graph" | `Model.move_graph_relative` added the distance to every node and spline point; fractions of a world unit had to be carried | `__pan_view` adds the screen distance to the view offset (a plain float, nothing to round, nothing to carry) |
| `Model.move_graph_relative`, `GraphMovedEvent` | moved the graph, told all widgets | removed (with `GraphItem.graph_moved_event` and the equivalent methods of the label and branch widgets); the widgets follow the `changed` signal of the view |
| Grid position (`Model.get_grid_position`, `grid_pos` in the file) | the accumulated pan | a **constant** of the graph: the world position of a grid line crossing. Grid lines are at this position plus multiples of 30 in world coordinates. Pan and zoom do not change it, so nodes that snap to the grid stay on it |
| `CreateNodeCommand`, `RemoveNodeCommand`, `CreateBranchCommand`, `RemoveBranchCommand` | remembered the pan at creation and shifted the objects by the pan difference when re-adding them (`gridpos_atCreation`) | no compensation; the `model` parameter of the constructors is removed. Objects keep their world coordinates |
| `FixedGrid`, `FixedGridWidget` | grid lines at `pan mod 30` | lines at `grid position mod 30` in world coordinates, mapped to the screen by the view (this was already prepared in step 3) |
| Widgets on a view change | `refresh_widgets(force=True)` | `refresh_widgets()`: a branch widget whose shape is only moved is moved, not rebuilt, so a pan costs the same as before (about 43 ms per step on a graph with 168 nodes and 216 branches, before: about 47 ms) |

**What a file remembers: `view_origin`.** In V2.0 the pan was part of the coordinates, so a file opened showing what was on the screen when it was saved. To keep that, the file now has the optional key `view_origin` (a pair of numbers): the world position at the top left corner of the window when it was saved. Loading shows the graph from there, at zoom 100% (the zoom is not saved). `Model.get_view_origin()` / `set_view_origin()` hold it; the `GraphField` keeps the model up to date whenever the view changes and applies it when a graph is loaded. Files without the key (all files of V2.0 and of the steps 1 to 3) are shown from (0, 0). A new graph starts with the grid position (0, 0) and the view at (0, 0). Panning is not part of the undo history and does not make the file "modified".

*This is a decision that was not in the plan; it is easy to remove if you do not want the view in the file* (`view_origin` in `io/json.py`, `io_controller.py`, `Model` and `GraphField.__show_view_origin_of_model`).

**Compatibility.**

- Files of V2.0 and steps 1 to 3 (coordinates shifted by the pan, `grid_pos` = accumulated pan) load unchanged and look exactly as before: the grid lines come out at the same place (`grid_pos mod 30`), which a test shows pixel by pixel.
- Files written now can be opened by V2.0: the coordinates are consistent, `grid_pos` is just a grid position, and the unknown key `view_origin` is ignored. V2.0 then shows the graph from the origin instead of the saved view; "Center graph" helps.
- The file format version stays "3.0"; `view_origin` is an additive optional key (schema and `resources/schema.json` updated).

Checks done:

- All 282 earlier tests pass after adapting the tests that described the old pan (they asserted that a pan shifted every coordinate and the grid position); `test_pan_view_offset.py` adds the new behaviour (graph, grid position and undo history untouched by pans; undo, redo, delete, paste and create after pans; the file; old files; the schema).
- `TestPanLooksLikeTheOldPan`: for four examples and four pan distances, the picture of the graph panned with the view is **identical pixel by pixel** to the picture of a file as V2.0 would have saved it after the same pan (all coordinates shifted, shift added to `grid_pos`).
- The 9 reference renders are identical to those of step 1 (including the panned scene); golden files unchanged.
- Mutation check: 13 deliberate breaks (pan ignoring a direction, reversed pan, saved view not applied or not written or not read, grid position following the pan again, a new graph keeping the old view, the view change rebuilding every widget, and others) are all caught.
- Fuzz: 160 seeds of 100 steps (60 of them with random zoom and offset changing during the sequence) are clean; the checker also verifies after every operation that the model's view origin is the world position at the top left of the window.

*Manual checklist for step 4* (in addition to the earlier ones):

1. Pan with the mouse: the graph, labels, handles and grid move together and smoothly, as before (also on the largest example `fig_12.sfg`).
2. Pan far away, create nodes there, pan back, drag, undo, redo: nothing jumps.
3. Delete a node, pan, undo: the node comes back at its old place in the graph (not shifted).
4. Pan, then paste: the pasted nodes are on visible grid lines.
5. Pan the window to a different part of the graph, save, close the program, open the file: you see the same part of the graph. Repeat with "Center graph" before saving.
6. Open an example and a file that you saved with the previous step after panning: they look exactly as they did before.
7. Open a saved file in a text editor: `grid_pos` is the same after panning (it no longer accumulates), `view_origin` is there.
8. "New" resets the view and the grid to the origin.

### Step 5: Zoom (done; range and keys changed in step 5b)

The graph can be zoomed with the keyboard, the menu and Ctrl + mouse wheel (the range is 10% to 200%, the keys are those of step 5b below). Everything that is drawn scales with the zoom, so node size, line widths, arrows and text keep their relation, as in the TikZ output. At 100% the pictures are identical to step 1 (pixel by pixel, all 9 reference scenes).

**Operating it**

| Action | Menu (View) | Keys / mouse |
|---|---|---|
| Zoom in | Zoom In | `Alt+I` (also `Ctrl++`, `Ctrl+=`); `Ctrl` + wheel away from you |
| Zoom out | Zoom Out | `Alt+U` (also `Ctrl+-`); `Ctrl` + wheel towards you |
| Back to 100% | Zoom 100% | `Alt+O` |
| Show the whole graph | Zoom to Fit | `Alt+Z` |

The zoom is shown in the status bar. A step (one key press, one wheel notch) changes the zoom by the factor 2^(1/4), so four steps halve or double it; a part of a notch (touchpad) is the same part of a step. The range is 10% to 200%: zooming in at 200% or out at 10% does nothing, and the limits and 100% are reached exactly. The wheel and `Zoom In/Out` zoom around the mouse pointer or, for the keyboard, the centre of the window: the part of the graph there stays where it is. The plain wheel (without `Ctrl`) is not used. Turns of the wheel that arrive together are added up and zoomed in one go. "Zoom to fit" shows the whole graph centred, as large as fits but not beyond 100% (on an empty graph it does nothing). The zoom is not saved in the file; a file opens at 100% (see step 4).

**Correction of the plan.** The formula for zooming around a point was wrong in the plan (`t' = t + c * (1 - z'/z)`), it is only right when the offset `t` is 0. The world point under the pointer `c` stays fixed if `t' = c - z' * (c - t) / z`. This is implemented (`GraphField.set_zoom`) and tested with 200 random zooms, offsets and anchors.

**What scales, and how** (`gui/glyphs.py` has all dimensions at 100% in one place):

| Part | At zoom z |
|---|---|
| Node | radius, circle line width and the selection number are drawn in a painter that is scaled by z around the centre of the widget. The widget has an even size (so its centre is on a pixel): `2 * ceil(11 * z)`, but at least 10 pixels |
| Branch | line width 3 and arrow line width 1 times z; arrow length, height and curvature times z; the area around the line and the arrow that is kept free for anti-aliasing times z |
| Spline handle | knob radius, circle line width times z |
| Label | font size `13 pt * z` (at 100% exactly as before); label offsets times z (step 3) |
| Grid | spacing `30 * z` (step 3) |

A widget remembers the zoom it was built for and rebuilds itself when the zoom differs, also if its points did not move (`BranchWidget`, handles, labels, nodes). A pan is still only a move of the widgets. `QLabel` does not recompute its size for a label without text (a node without a name) after a font change; this is worked around in `LabelWidget.__apply_zoom` and tested.

**Decisions made in this step** (change them at the review if you want something else):

1. **Minimum click areas.** Nodes can always be grabbed on a circle of at least 10 pixels, branches along a line at least 6 pixels wide (8 at 100%), the arrow and the handle knob (radius at least 5 pixels, line 4 pixels) as well. The *drawing* is exactly scaled; only the area that reacts to the mouse does not get smaller. Labels get no minimum (their text is the click area).
2. **The grid is not drawn when its lines are less than 6 pixels apart** (zoom below 20%): it would be a grey area. Snapping to the grid still works.
3. **Thin lines are not made thicker.** A branch of width 3 is 0.3 pixels wide at 10% and therefore a faint grey line. This keeps the proportions as in TikZ; if it is too faint to see, a minimum line width can be added in `glyphs.py`.
4. **Rubber band** (`Alt`+drag) stays in screen space and works at every zoom.
5. **PNG export is unchanged: it saves what is shown**, so at 50% the picture is the 50% view. Save, TikZ and the clipboard do not depend on the zoom at all (tested); "always 100%" or "the whole graph" for PNG would be a separate change.
6. **Sub-pixel curves:** the caches of branches and handles stay whole pixels (as decided in step 3), the curves look fine at 10% to 50% in the renders.

Performance (offscreen, graph with 168 nodes and 216 branches): a pan step about 40 ms (unchanged), also at 50%; a zoom step about 220 ms, where all widgets are rebuilt (about 30 ms for the biggest example, 21 nodes and 27 branches). Repaints are suspended during a zoom and wheel events are added up, so a fast spin does not queue up work.

Checks done:

- All earlier tests pass; at 100% the 9 reference renders are identical to step 1; golden files unchanged.
- `test_zoom.py` (59 tests): operations and exact limits; the anchor stays under the pointer (200 random cases); wheel (direction, notches, parts, `Ctrl` needed, anchor, limits, coalescing); the real main window (menu entries, shortcuts, **no shortcut is used twice in the whole window**, status bar); **measured in the rendered pictures** that node circle, line width, arrow, handle knob and text are the size at 100% times the zoom (zoom 2, 1.5, 1, 0.75, 0.5, 0.25) and that their relations stay; minimum click areas at zoom 1 to 0.1; grid hiding at the 6 pixel limit; zoom to fit for all examples in three window sizes (the whole graph is inside the window); TikZ, file and clipboard identical at every zoom.
- The consistency checker verifies after every fuzz step that the node widgets have the right size, labels the right font size, branches cover their curve and were built for the current zoom.
- Mutation check: 24 deliberate breaks (the old wrong formula, no limit at 100% or 10%, no snap to exactly 100%, plain wheel zooming, reversed wheel, nodes/pens/arrow/handle/font not scaled, widgets not rebuilt after a zoom, no minimum click areas, grid not hidden, zoom to fit not centred, status bar not updated, missing shortcut, and others) are all caught. Three of them were not caught at first and led to new tests (handle drawing, a branch whose points do not change when the zoom does, rounding at 100%).
- Fuzz: 200 seeds of 100 steps with random zoom operations (steps around random anchors, wheel, zoom to fit, directly set views) interleaved with all other operations are clean.

*Manual checklist for step 5* (in addition to the earlier ones):

1. `Ctrl` + wheel zooms around the mouse pointer: the part of the graph under the pointer does not move. Try it with the pointer over empty canvas **and over a node, a branch, a label and a spline handle** (a real wheel is handed from these widgets to the canvas by Qt; this cannot be tested with synthetic events). The wheel without `Ctrl` does nothing.
2. `Alt+I`, `Alt+U`, `Alt+O`, `Alt+Z` (see step 5b) and the entries of the View menu do the same; the status bar shows the zoom; nothing zooms in beyond 200% or out beyond 10%.
3. Zoom out to 50%, 25%, 10%: nodes, lines, arrows and text shrink together and look like a smaller version of the same picture. At 10% the grid is gone, at 25% it is visible.
4. At 25% and 10%: select, drag nodes (with and without `Ctrl`), drag labels and spline handles, create nodes by double click, `Alt`-drag a rubber band, copy and paste, undo and redo. Everything must be grabbable (also a tiny node and a thin branch) and everything must land on the grid.
5. Pan while zoomed out; "Center graph"; zoom to fit on the examples and on a big graph that is larger than the window.
6. Zoom, then save, close, open: the file opens at 100%, showing the same top left part of the graph as when it was saved. Export TikZ at 100% and at 30%: the files are the same.
7. At 100% nothing looks different from step 4 (compare with a few examples).
8. Zoom out with a big graph and turn the wheel quickly: the program stays responsive and ends at the zoom of all notches together.

### Step 5b: Zoom up to 200%, keyboard shortcuts without numpad (done)

Two changes after the review of step 5.

**1. The range is 10% to 200%** (`MAX_ZOOM = 2.0` in `gui/view_transform.py`). Everything above 100% works like below it: nodes, lines, arrows, handles and text are drawn at twice the size at 200% (measured in the rendered pictures, like at the smaller zooms), the grid lines are 60 pixels apart, the minimum click areas do not matter. Four steps in double the zoom and the limit is reached exactly, as at the lower end. "Zoom to fit" is still **limited to 100%**: it shows the whole graph and does not enlarge a small one (change the `1.0` in `GraphField.zoom_to_fit` if you want that to use up to 200%).

**2. Shortcuts that work without numpad and without Shift.** On a Swiss keyboard `+` is `Shift+1`, so `Ctrl++` needs three keys. The View menu now shows:

| Action | Shortcut | Also works |
|---|---|---|
| Zoom In | `Alt+I` | `Ctrl++`, `Ctrl+=` |
| Zoom Out | `Alt+U` | `Ctrl+-` |
| Zoom 100% | `Alt+O` | - |
| Zoom to Fit | `Alt+Z` | - |

`U`, `I` and `O` are neighbours on the top letter row (out, in, 100%), and they follow the `Alt+letter` scheme that the program already uses (`Alt+C` centre graph, `Alt+P`, `Alt+M`, `Alt+G`, `Alt+Z`). None of the keys is used by another action (`Ctrl+O` is Open, `Alt+O` is different); `Ctrl+0` is not used any more. The usual keys of other programs (`Ctrl++`, `Ctrl+=`, `Ctrl+-`) were kept as additional shortcuts because they cost nothing and help people with a numpad or another layout; to remove them, delete the extra entries in `MainWindow.__init__` (the first shortcut of the list is the one that the menu shows). The `.ui` file was changed and `ui_main_window.py` regenerated with `pyside6-uic main_window.ui -o ui_main_window.py` (see the note on `.ui` files in the V2.0 section "Porting Process" below; only the `.ui` file is edited by hand).

Checks done:

- The zoom tests were adapted to the new limit and extended: exactly 200% after four steps in, a fifth does nothing, in and out return to exactly 100%, reset to 100% from every zoom (also keeping the centre of the window), anchor invariance up to 200%, wheel at the limits, measured scaling of node, line, arrow, handle and text at 200% and 150%, minimum click areas at 200%, the status bar shows 200%.
- **The shortcuts are tested by pressing the real key combinations in the real main window** (`QTest.keySequence`): `Alt+I`, `Ctrl++` and `Ctrl+=` zoom in, `Alt+U` and `Ctrl+-` zoom out, `Alt+O` gives 100% from 10%, 50%, 150% and 200%, `Alt+Z` zooms to fit, `Ctrl+0` does nothing. A test also checks that no shortcut is used twice in the whole window.

- **The mutation checks of steps 3 to 5b were repeated from scratch** with a stricter runner (it works on a copy of the source, writes no bytecode and restores files from their saved text; the earlier runner could leave stale cached code behind when a mutation did not change the size of a file). Of 60 deliberate breaks, 54 are caught; 5 target code that was replaced in later steps (the transitional pan code of step 3 and two shortcut lists) and are covered by newer mutations; **1 was not caught: a new graph did not reset the grid position**, because the test never started from a graph with a grid position other than (0, 0). That test (`test_new_graph_starts_at_the_origin`) now loads such a file first, and the mutation is caught. The current code of the "view change refreshes the widgets" behaviour got two new mutations (zoom change, pan), both caught. Corrects the statements "all caught" for steps 3 and 4 above.
- At 100% the 9 reference renders are still identical to step 1; fuzz: 100 more seeds of 100 steps with random zoom operations (now up to 200%) are clean.

*Manual checklist for step 5b:*

1. `Alt+I` zooms in beyond 100% up to exactly 200% (status bar), `Alt+U` zooms out down to 10%, `Alt+O` returns to 100% from anywhere. Check that the shortcuts work while the cursor is in the node name field of the side panel as well.
2. At 150% and 200% everything looks like an enlarged version of the 100% picture (nodes, lines, arrows, text); dragging, handles, labels, rubber band and paste work; the grid lines are 60 pixels apart at 200%.
3. `Ctrl+wheel` goes up to 200% as well. Pan and "Center graph" at 200%.
4. "Zoom to fit" on a small graph stays at 100% (does not enlarge).
5. The menu entries show the new shortcuts.

### Step 6: Mini map (done)

A small map of the whole graph lies over the bottom right corner of the canvas and shows which part of it is visible. Switch it on and off in the View menu (**Mini Map**, `Alt+N`). It is off until you switch it on, and the choice is remembered for the next start.

**What it shows** (as defined for this step):

- **All nodes and all branches.** Branches are drawn as thin lines along their real curves, nodes as dots. A node or branch is never left out, however large the graph is.
- **No labels** (neither node names nor branch weights) **and no arrows.** The picture does not change at all when a name, a weight or the position of a label changes (tested pixel by pixel). Labels do not count when the map decides how much to show.
- **A rectangle for the part that the canvas shows** (highlight colour, light fill). It follows every pan and zoom.

**How it is drawn.** Everything comes from the model, not from the widgets of the canvas (`gui/mini_map.py`). The map shows the graph and the visible part together, in the largest scale that fits both into the map (with 8 pixels of space at the border), centred. If you pan or zoom away from the graph the scale becomes smaller so that the rectangle stays in the map; the map is opaque, 220 x 160 pixels, 10 pixels from the corner. The extent of a branch is that of its curve, not only of its end points, so curves that bulge out of the hull of their nodes (self-loops!) are inside the map too.

**Using it.** A click or drag with the left mouse button moves the view; the zoom does not change.

- A press *outside* the rectangle shows the part around the clicked position (the rectangle jumps there); a press *inside* it grabs the rectangle without a jump and pulls it with the mouse.
- While the mouse drags, the scale of the map is frozen (otherwise it would rescale under the mouse as soon as the rectangle leaves the graph); it fits again when the button is released.
- The view moves in whole pixels, so a drag moves the widgets like a pan does and does not rebuild them.
- It is a movement of the view like a pan: it does not change the graph, the selection or the undo history, and the file is not "modified". The wheel and other mouse buttons are not used by the map (the wheel goes to the canvas, `Ctrl` + wheel zooms). The map never takes the keyboard focus.

**Switching and remembering.** `View > Mini Map` is a checkable menu entry; `Alt+N` (it was free; the letters C, G, M, P, Z, I, U and O are used by other actions). The choice is stored by `utils/settings.py` (`AppSettings`) in the settings of the user, an ini file (on Linux `~/.config/signalflowgrapher/signalflowgrapher.ini`), with the key `view/minimap`; it is not part of a graph file. The default is off (`DEFAULT_MINIMAP_VISIBLE`).

**How it sits on the canvas.** The map is a child widget of `GraphField` that is not part of the graph (no model object, not in the maps of widgets, ignored by "Center graph" and the rubber band). Every widget that is created later (nodes, branches, labels, spline handles) would lie over it, so `GraphField.childEvent` raises the map whenever a widget is added; it is moved to its corner at every resize and repainted at every change of the graph or the view. Pictures of the graph (**Save as PNG**) are made with `GraphField.render_graph`, which leaves the map out: it is an aid for working, not part of the drawing.

**Tests never touch the settings of the user.** The test harness redirects the settings folder of the whole test process to a temporary folder. (While developing this step the first version of the tests wrote the choice into the real settings file; `AppSettings` now uses an explicit ini format, because `QSettings(organization, application)` uses the native format of the system (the registry on Windows), which a test cannot redirect in the same way on every system.)

Decisions made in this step (change them at the review if you want something else):

1. **Default off**, so that the program looks as before until the map is wanted. One constant to change.
2. **Fixed size and place** (220 x 160 pixels, bottom right). It cannot be moved or resized; if the corner is in your way, switch it off.
3. **The selection is not shown** in the map (only nodes, branches and the shown rectangle, as defined).
4. A press inside the rectangle does not jump; a press outside does.

Performance (offscreen, graph with 168 nodes and 216 branches, on a machine that was twice as slow as at step 5): one paint of the map takes about 9 ms; a pan step costs about 2 ms more with the map on, a zoom step about 16 ms more; with the map off nothing changes (same numbers as step 5b measured side by side).

Checks done:

- All earlier tests pass; the 9 reference renders are identical to step 1 (the map is off by default); golden files unchanged.
- `test_minimap.py` (48 tests): the extent of the graph equals the extent of all nodes and the *sampled curves* (also self-loops); the shown part equals the canvas in world units for 8 views; everything is inside the map at every zoom and offset (also far away); **in the picture** every node is a dark dot, every branch is visible along its whole curve for all six examples, a long straight branch is as thick in the middle as at its ends (no arrow), names, weights and label positions do not change the picture, the rectangle is drawn where it is reported, nothing of the canvas underneath shines through; clicks, drags, no jump inside, frozen scale while dragging, whole pixels and no rebuild of branch widgets, other buttons and the wheel ignored, graph/zoom/selection/history untouched, a double click creates no node; the map is in the corner at every window size, over everything created later (checked with the real hit test `childAt`), repainted after pan, zoom, new node, move, undo and new graph; the real main window (menu entry, `Alt+N` pressed for real, choice stored), Save as PNG through the real menu action has no map; the remembered choice is applied at a program start (fresh processes: default off, on, kept, off).
- The consistency checker verifies after every fuzz step that a visible map is in its corner, over all other widgets and contains the whole graph and the shown part; the fuzz tests switch the map on and off and drag in it (90 more seeds of 100 steps with the map and random zoom operations are clean).
- Mutation check on a copy of the source: 33 deliberate breaks (arrows drawn on branches, names drawn, nodes or branches or the rectangle not drawn, the extent ignoring curves or counting labels, no padding, the map rescaling while dragging, a jump from inside, the wrong direction, offsets not rounded, other buttons or the wheel used, focus taken, visible at start, translucent, wrong corner, not raised over new widgets, not repainted after a view or graph change, PNG export containing the map, menu entry not connected, choice not stored or not applied, default on, and others) are all caught. Two were not caught at first (the right and middle button, the translucent background); their tests were weak and have been strengthened.

*Manual checklist for step 6* (in addition to the earlier ones):

1. `View > Mini Map` (and `Alt+N`) shows and hides the map in the bottom right corner; close the program and start it again: it comes back as you left it. The map is off at the very first start.
2. Open the examples: all nodes and branches are in the map, as thin lines and dots; no names, weights or arrows. Self-loops and the long curves are completely inside the map.
3. The blue rectangle is the part that the canvas shows: zoom (`Alt+U`, `Alt+I`, `Ctrl` + wheel), pan and "Center graph" and watch it follow; zoomed far out it covers the whole graph and more.
4. Click outside the rectangle: the canvas shows the part around that place. Press inside it and drag: the rectangle follows the mouse without a jump. Drag beyond the border of the map. Dragging should feel about as smooth as panning.
5. While the map is on: create nodes and branches (also under the map), select a branch (spline handles appear), drag nodes: the map stays on top of everything and keeps showing the current graph. Undo and redo update it.
6. Clicks in the map do not clear the selection, create nodes or change the file ("modified" state).
7. Resize the window: the map stays in the corner.
8. *Save as PNG* with the map on: the picture has no map.
9. `Ctrl` + wheel with the pointer over the map zooms the canvas; the plain wheel does nothing.

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
