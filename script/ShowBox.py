"""PyMOL plugin for visualizing an AutoDock Vina search box."""

import os

from pymol import cmd
from pymol.cgo import BEGIN, COLOR, END, LINES, LINEWIDTH, VERTEX


BOX_KEYS = (
    "center_x",
    "center_y",
    "center_z",
    "size_x",
    "size_y",
    "size_z",
)
_dialog = None
_object_source_directories = {}
_object_source_files = {}
_last_structure_directory = None
_last_structure_file = None


def _install_load_tracker():
    """Track source directories for structures loaded after plugin startup."""
    if getattr(cmd.load, "_showbox_load_tracker", False):
        return

    original_load = cmd.load

    def tracked_load(*args, **kwargs):
        global _last_structure_directory, _last_structure_file

        filename = args[0] if args else kwargs.get("filename")
        before = set(cmd.get_names("objects"))
        result = original_load(*args, **kwargs)

        if not filename:
            return result

        source_file = os.path.abspath(os.path.expanduser(str(filename)))
        if not os.path.isfile(source_file):
            return result

        extension = source_file.lower()
        structure_extensions = (
            ".pdb", ".pdb.gz", ".pdbqt", ".cif", ".mmcif", ".ent",
            ".mol", ".mol2", ".sdf", ".mae", ".pqr",
        )
        if not extension.endswith(structure_extensions):
            return result

        directory = os.path.dirname(source_file)
        after = set(cmd.get_names("objects"))
        loaded_objects = after - before

        explicit_object = kwargs.get("object")
        if explicit_object is None and len(args) > 1:
            explicit_object = args[1]
        if explicit_object:
            loaded_objects.add(str(explicit_object))

        for object_name in loaded_objects:
            _object_source_directories[object_name] = directory
            _object_source_files[object_name] = source_file
        _last_structure_directory = directory
        _last_structure_file = source_file
        return result

    tracked_load._showbox_load_tracker = True
    cmd.load = tracked_load


def _object_names_for_selection(selection):
    known_names = set(cmd.get_names("selections"))
    known_names.update(cmd.get_names("objects"))
    is_simple_name = selection.replace("_", "").isalnum()

    if is_simple_name and selection not in known_names:
        return []

    try:
        return cmd.get_object_list(selection) or []
    except Exception:
        return []


def _default_config_path(selection="sele"):
    """Return config.conf beside the structure owning the selection."""
    object_names = _object_names_for_selection(selection)

    for object_name in object_names:
        directory = _object_source_directories.get(object_name)
        if directory:
            return os.path.join(directory, "config.conf")

    if _last_structure_directory:
        return os.path.join(_last_structure_directory, "config.conf")

    try:
        working_directory = cmd.pwd()
    except Exception:
        working_directory = os.getcwd()
    return os.path.join(working_directory or os.getcwd(), "config.conf")


def _receptor_filename(selection, directory):
    """Return the loaded receptor file name for the selected object."""
    object_names = _object_names_for_selection(selection)
    for object_name in object_names:
        source_file = _object_source_files.get(object_name)
        if source_file:
            return os.path.basename(source_file)

    if _last_structure_file:
        return os.path.basename(_last_structure_file)

    extensions = (
        ".pdbqt", ".pdb", ".pdb.gz", ".cif", ".mmcif", ".ent",
        ".mol2", ".pqr",
    )
    for object_name in object_names:
        for extension in extensions:
            candidate = os.path.join(directory, object_name + extension)
            if os.path.isfile(candidate):
                return os.path.basename(candidate)

    if object_names:
        return object_names[0]
    raise ValueError("Unable to determine the loaded receptor file name")


def _read_vina_config(config_file):
    """Read center and size values from a Vina config file."""
    config_file = os.path.abspath(os.path.expanduser(config_file))
    values = {}

    with open(config_file, "r", encoding="utf-8-sig") as handle:
        for raw_line in handle:
            line = raw_line.split("#", 1)[0].strip()
            if not line or "=" not in line:
                continue

            key, value = (part.strip() for part in line.split("=", 1))
            if key in BOX_KEYS:
                try:
                    values[key] = float(value)
                except ValueError as exc:
                    raise ValueError(
                        "Invalid numeric value for {}: {!r}".format(key, value)
                    ) from exc

    missing = [key for key in BOX_KEYS if key not in values]
    if missing:
        raise ValueError(
            "Missing Vina box values: {}".format(", ".join(missing))
        )

    for key in ("size_x", "size_y", "size_z"):
        if values[key] <= 0:
            raise ValueError("{} must be greater than zero".format(key))

    return config_file, values


def _draw_vina_box(
    values,
    name="vina_box",
    color="yellow",
    line_width=2.0,
    show_center=1,
    zoom=1,
):
    line_width = float(line_width)
    show_center = int(show_center)
    zoom = int(zoom)

    cx, cy, cz = (
        values["center_x"],
        values["center_y"],
        values["center_z"],
    )
    hx, hy, hz = (
        values["size_x"] / 2.0,
        values["size_y"] / 2.0,
        values["size_z"] / 2.0,
    )

    vertices = [
        (cx - hx, cy - hy, cz - hz),
        (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy + hy, cz - hz),
        (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz),
        (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy + hy, cz + hz),
        (cx - hx, cy + hy, cz + hz),
    ]
    edges = (
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    )

    red, green, blue = cmd.get_color_tuple(color)
    cgo = [
        LINEWIDTH,
        line_width,
        BEGIN,
        LINES,
        COLOR,
        red,
        green,
        blue,
    ]
    for start, end in edges:
        cgo.extend([VERTEX, *vertices[start]])
        cgo.extend([VERTEX, *vertices[end]])
    cgo.append(END)

    center_name = "{}_center".format(name)
    cmd.delete(name)
    cmd.delete(center_name)
    cmd.load_cgo(cgo, name)

    if show_center:
        cmd.pseudoatom(
            center_name,
            pos=[cx, cy, cz],
            color="red",
            label="Vina box center",
        )
        cmd.show("spheres", center_name)
        cmd.set("sphere_scale", 0.4, center_name)

    if zoom:
        cmd.zoom(name, buffer=5)

    print(
        "Center: ({:.3f}, {:.3f}, {:.3f}); "
        "Size: ({:.3f}, {:.3f}, {:.3f})".format(
            cx,
            cy,
            cz,
            values["size_x"],
            values["size_y"],
            values["size_z"],
        )
    )
    return name


def show_vina_box(
    config_file,
    name="vina_box",
    color="yellow",
    line_width=2.0,
    show_center=1,
    zoom=1,
):
    """Draw the search box defined by an AutoDock Vina config file."""
    config_file, values = _read_vina_config(config_file)
    result = _draw_vina_box(
        values,
        name=name,
        color=color,
        line_width=line_width,
        show_center=show_center,
        zoom=zoom,
    )
    print("Loaded Vina box from: {}".format(config_file))
    return result


def box_from_selection(
    selection="sele",
    size_x=22.5,
    size_y=22.5,
    size_z=22.5,
    config_file=None,
):
    """Create a box centered on a PyMOL selection and save a Vina config."""
    size_x, size_y, size_z = (
        float(size_x),
        float(size_y),
        float(size_z),
    )
    if min(size_x, size_y, size_z) <= 0:
        raise ValueError("Box sizes must be greater than zero")
    if cmd.count_atoms(selection) < 1:
        raise ValueError(
            "PyMOL selection {!r} contains no atoms".format(selection)
        )

    minimum, maximum = cmd.get_extent(selection)
    values = {
        "center_x": (minimum[0] + maximum[0]) / 2.0,
        "center_y": (minimum[1] + maximum[1]) / 2.0,
        "center_z": (minimum[2] + maximum[2]) / 2.0,
        "size_x": size_x,
        "size_y": size_y,
        "size_z": size_z,
    }

    if not config_file:
        config_file = _default_config_path(selection)
    config_file = os.path.abspath(os.path.expanduser(config_file))
    output_directory = os.path.dirname(config_file)
    if output_directory:
        os.makedirs(output_directory, exist_ok=True)
    receptor_filename = _receptor_filename(selection, output_directory)

    with open(config_file, "w", encoding="utf-8") as handle:
        handle.write(
            "receptor = {}\n\n"
            "size_x = {:.2f}\n"
            "size_y = {:.2f}\n"
            "size_z = {:.2f}\n"
            "center_x = {:.3f}\n"
            "center_y = {:.3f}\n"
            "center_z = {:.3f}\n\n"
            "exhaustiveness = 8\n"
            "num_modes = 5\n"
            "energy_range = 3\n"
            "cpu = 5\n".format(
                receptor_filename,
                values["size_x"],
                values["size_y"],
                values["size_z"],
                values["center_x"],
                values["center_y"],
                values["center_z"],
            )
        )

    _draw_vina_box(values)
    print("Saved Vina config: {}".format(config_file))
    return config_file


def _choose_config_file():
    try:
        from pymol.Qt import QtWidgets

        config_file, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Select AutoDock Vina config",
            os.path.expanduser("~"),
            "Vina config (*.conf *.txt);;All files (*)",
        )
        if config_file:
            show_vina_box(config_file)
    except Exception as exc:
        print("Unable to load Vina box: {}".format(exc))


def _open_box_dialog():
    from pymol.Qt import QtWidgets

    global _dialog
    if _dialog is not None:
        _dialog.show()
        _dialog.raise_()
        _dialog.activateWindow()
        return

    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("AutoDock Vina Box")
    dialog.setMinimumWidth(520)
    layout = QtWidgets.QVBoxLayout(dialog)
    form = QtWidgets.QFormLayout()

    selection_input = QtWidgets.QLineEdit("sele")
    form.addRow("PyMOL selection", selection_input)

    size_inputs = []
    for label in ("Size X (Å)", "Size Y (Å)", "Size Z (Å)"):
        spinbox = QtWidgets.QDoubleSpinBox()
        spinbox.setDecimals(2)
        spinbox.setRange(0.10, 1000.00)
        spinbox.setSingleStep(1.00)
        spinbox.setValue(22.50)
        form.addRow(label, spinbox)
        size_inputs.append(spinbox)

    output_input = QtWidgets.QLineEdit(_default_config_path("sele"))
    output_state = {"manually_changed": False}
    output_row = QtWidgets.QHBoxLayout()
    output_row.addWidget(output_input)
    browse_button = QtWidgets.QPushButton("Browse...")
    output_row.addWidget(browse_button)
    form.addRow("Output config", output_row)
    layout.addLayout(form)

    help_label = QtWidgets.QLabel(
        "Create a PyMOL selection named 'sele', customize the box size, "
        "then click Generate."
    )
    help_label.setWordWrap(True)
    layout.addWidget(help_label)

    buttons = QtWidgets.QHBoxLayout()
    load_button = QtWidgets.QPushButton("Load Config...")
    generate_button = QtWidgets.QPushButton("Generate Box + Config")
    close_button = QtWidgets.QPushButton("Close")
    buttons.addWidget(load_button)
    buttons.addStretch(1)
    buttons.addWidget(generate_button)
    buttons.addWidget(close_button)
    layout.addLayout(buttons)

    def browse_output():
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            dialog,
            "Save AutoDock Vina config",
            output_input.text(),
            "Vina config (*.config *.conf);;All files (*)",
        )
        if filename:
            output_state["manually_changed"] = True
            output_input.setText(filename)

    def mark_output_changed(*_args):
        output_state["manually_changed"] = True

    def refresh_output_path():
        if not output_state["manually_changed"]:
            selection = selection_input.text().strip() or "sele"
            output_input.setText(_default_config_path(selection))

    def generate():
        try:
            refresh_output_path()
            config_file = box_from_selection(
                selection=selection_input.text().strip() or "sele",
                size_x=size_inputs[0].value(),
                size_y=size_inputs[1].value(),
                size_z=size_inputs[2].value(),
                config_file=output_input.text().strip(),
            )
            QtWidgets.QMessageBox.information(
                dialog,
                "Vina Box",
                "Box created and config saved:\n{}".format(config_file),
            )
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                dialog,
                "Unable to create Vina box",
                str(exc),
            )

    browse_button.clicked.connect(browse_output)
    output_input.textEdited.connect(mark_output_changed)
    selection_input.editingFinished.connect(refresh_output_path)
    load_button.clicked.connect(_choose_config_file)
    generate_button.clicked.connect(generate)
    close_button.clicked.connect(dialog.close)

    _dialog = dialog
    dialog.show()


def __init_plugin__(app=None):
    """Register under Plugin -> Legacy Plugins -> ShowBox."""
    _install_load_tracker()
    cmd.extend("vina_box", show_vina_box)

    if app is not None:
        app.menuBar.addmenuitem(
            "Plugin",
            "command",
            label="ShowBox",
            command=_open_box_dialog,
        )


# Also make the command available when the file is loaded with `run`.
cmd.extend("vina_box", show_vina_box)
cmd.extend("vina_box_from_selection", box_from_selection)
