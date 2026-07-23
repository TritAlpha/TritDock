# ShowBox

ShowBox is a lightweight [PyMOL](https://www.pymol.org/) plugin for visualizing
[AutoDock Vina](https://vina.scripps.edu/) docking search boxes. It can also
create a search box and Vina configuration file from an atom selection in
PyMOL.

## Features

- Read `center_x/y/z` and `size_x/y/z` values from a Vina configuration file
- Draw a docking search box and optionally mark its center in PyMOL
- Calculate the box center from a PyMOL atom selection
- Set custom box dimensions along the X, Y, and Z axes
- Save the generated parameters to an editable Vina `config.conf` file
- Use either the graphical interface or PyMOL commands

## Requirements

- PyMOL 2.x
- Python 3, as provided by PyMOL
- PyMOL's Qt interface, if you want to use the graphical dialog

ShowBox only uses PyMOL and the Python standard library. No additional Python
dependencies are required.

## Installation

### Option 1: Install as a PyMOL plugin

1. Download this repository.
2. Open `Plugin → Plugin Manager` in PyMOL.
3. Choose the option to install from a local file and select
   `script/ShowBox.py`.
4. Open `ShowBox` from the `Plugin` menu after installation.

The exact menu names may vary slightly between PyMOL versions.

### Option 2: Load the script directly

Run the following command in the PyMOL command line:

```pml
run /path/to/ShowBox/script/ShowBox.py
```

This makes the `vina_box` and `vina_box_from_selection` commands available,
but does not add the graphical dialog to the Plugin menu.

## Usage

### Display a box from an existing configuration

Run:

```pml
vina_box /path/to/config.conf
```

ShowBox creates two PyMOL objects:

- `vina_box`: the wireframe search box
- `vina_box_center`: a red marker at the box center

Optional arguments can be supplied as follows:

```pml
vina_box /path/to/config.conf, my_box, cyan, 3, 1, 1
```

The complete command syntax is:

```text
vina_box config_file [, name [, color [, line_width [, show_center [, zoom ]]]]]
```

Use `1` to enable `show_center` or `zoom`, and `0` to disable it.

### Generate a box from an atom selection

Load a receptor and select the atoms that should define the center of the
docking box:

```pml
load /path/to/receptor.pdbqt
select sele, chain A and resi 123
vina_box_from_selection sele, 22.5, 22.5, 22.5
```

ShowBox will:

1. Calculate the center of the selected atoms' bounding box.
2. Draw a docking box with the specified dimensions.
3. Write `config.conf` next to the loaded receptor structure.

The complete command syntax is:

```text
vina_box_from_selection selection [, size_x [, size_y [, size_z [, config_file ]]]]
```

To specify a custom output path:

```pml
vina_box_from_selection sele, 24, 24, 24, /path/to/docking.conf
```

All box dimensions are measured in Å.

### Use the graphical interface

Open `Plugin → ShowBox`, then:

1. Create an atom selection in PyMOL. The default selection name is `sele`.
2. Enter the selection name.
3. Set the box dimensions along the X, Y, and Z axes.
4. Confirm the configuration output path.
5. Click `Generate Box + Config`.

Use `Load Config...` to display a box from an existing Vina configuration.

## Configuration Format

The configuration file must contain all six center and size values:

```ini
center_x = 165.716
center_y = 162.430
center_z = 140.979

size_x = 22.50
size_y = 22.50
size_z = 22.50
```

Blank lines, unknown fields, and text following a `#` comment marker are
ignored. Each box dimension must be greater than zero.

A configuration generated from a selection also includes the receptor file
name and a set of default Vina parameters:

```ini
receptor = receptor.pdbqt

exhaustiveness = 8
num_modes = 5
energy_range = 3
cpu = 5
```

Review and adjust these values for your docking workflow before running Vina.

## Example Data

The `data/` directory contains:

- `preped.pdbqt`: an example receptor structure
- `config.conf`: a matching Vina configuration

To load the example:

```pml
load /path/to/ShowBox/data/preped.pdbqt
run /path/to/ShowBox/script/ShowBox.py
vina_box /path/to/ShowBox/data/config.conf
```

## Troubleshooting

### The selection contains no atoms

Make sure the selection name is correct. You can check it in PyMOL with:

```pml
count_atoms sele
```

The result must be greater than `0`.

### The configuration cannot be loaded

Make sure that all six center and size fields are present, their values are
numeric, and `size_x`, `size_y`, and `size_z` are greater than zero.

### The receptor filename is incorrect

Load the receptor structure before creating the selection and generating the
configuration. ShowBox will prefer the source filename of the loaded
structure. You should still verify that the generated `receptor` path is
correct for the directory from which you will run Vina.

## Project Structure

```text
ShowBox/
├── data/
│   ├── config.conf
│   └── preped.pdbqt
├── script/
│   └── ShowBox.py
└── README.md
```
