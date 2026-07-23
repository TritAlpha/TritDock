# ShowBox

ShowBox 是一个用于 PyMOL 的 AutoDock Vina 搜索盒可视化插件。它可以根据
PyMOL selection 自动计算盒子中心、绘制可自定义尺寸的搜索盒，并生成 Vina
使用的 `config.conf`。

## 功能

- 根据 PyMOL selection 计算搜索盒中心
- 自定义 `size_x`、`size_y` 和 `size_z`
- 在 PyMOL 中显示黄色搜索盒和红色中心点
- 自动生成 AutoDock Vina `config.conf`
- 从已有 `.conf`、`.config` 或 `.txt` 配置文件加载搜索盒
- 支持 PyMOL 命令行调用

## 文件

```text
pymol_box/
├── ShowBox.py
└── README.md
```

## 安装

1. 打开 PyMOL。
2. 选择 `Plugin → Plugin Manager`。
3. 点击 `Install New Plugin`。
4. 选择 `ShowBox.py`。
5. 安装完成后重启 PyMOL。

插件入口：

```text
Plugin → Legacy Plugins → ShowBox
```

更新插件时，请先在 Plugin Manager 中卸载旧版本，再安装新的
`ShowBox.py`。

## 根据 selection 生成搜索盒

### 1. 载入结构

例如：

```pml
load receptor.pdb, receptor
```

### 2. 创建 selection

可以通过鼠标选择原子，也可以使用 PyMOL 命令。例如选择配体：

```pml
select sele, organic
```

也可以选择指定残基：

```pml
select sele, chain A and resi 100+101+102
```

ShowBox 默认使用名为 `sele` 的 selection。

### 3. 打开 ShowBox

进入：

```text
Plugin → Legacy Plugins → ShowBox
```

窗口参数：

| 参数 | 说明 |
|---|---|
| `PyMOL selection` | 用于计算盒子中心的 selection，默认 `sele` |
| `Size X (Å)` | X 方向盒子长度，默认 22.50 Å |
| `Size Y (Å)` | Y 方向盒子长度，默认 22.50 Å |
| `Size Z (Å)` | Z 方向盒子长度，默认 22.50 Å |
| `Output config` | `config.conf` 保存位置 |

点击 `Generate Box + Config` 后，插件将：

1. 获取 selection 的坐标范围。
2. 使用坐标包围盒的中点作为 Vina box 中心。
3. 在 PyMOL 中生成 `vina_box`。
4. 创建红色中心点 `vina_box_center`。
5. 保存 Vina 配置文件。

默认保存到 `sele` 所属蛋白对象的源文件目录：

```text
/path/to/protein/config.conf
```

插件会跟踪启用后通过 PyMOL 加载的结构文件。如果源文件路径无法取得，
则回退到 PyMOL 当前工作目录。可以使用 `Browse...` 选择其他保存目录。

如果 selection 不存在或不包含原子，插件会显示错误信息。

## 加载已有配置

在 ShowBox 窗口中点击 `Load Config...`，然后选择已有的 Vina 配置文件。

配置文件至少需要包含：

```ini
receptor = preped.pdbqt

size_x = 22.50
size_y = 22.50
size_z = 22.50
center_x = 160.990
center_y = 157.630
center_z = 159.260
```

## 生成的 config.conf

ShowBox 生成的配置示例：

```ini
receptor = preped.pdbqt

size_x = 22.50
size_y = 22.50
size_z = 22.50
center_x = 160.990
center_y = 157.630
center_z = 159.260

exhaustiveness = 8
num_modes = 5
energy_range = 3
cpu = 5
```

`receptor` 使用当前 selection 所属蛋白对象的源文件名，并写在配置文件第一行。
配体文件仍可在运行 Vina 时通过命令行单独指定。

## PyMOL 命令

### 从指定配置显示盒子

```pml
vina_box /path/to/config.conf
```

自定义对象名称、颜色和线宽：

```pml
vina_box /path/to/config.conf, docking_box, cyan, 3
```

### 从 selection 生成盒子和配置

命令格式：

```pml
vina_box_from_selection selection, size_x, size_y, size_z, output_config
```

示例：

```pml
vina_box_from_selection sele, 22.5, 22.5, 22.5, /path/to/config.conf
```

## 删除盒子

```pml
delete vina_box
delete vina_box_center
```

## 注意事项

- 所有盒子尺寸单位均为 Å。
- 盒子中心是 selection 坐标包围盒的中点，不是质量中心。
- 建议让搜索盒完整覆盖结合位点，并在各方向保留适当空间。
- 生成新的盒子时，同名的 `vina_box` 和 `vina_box_center` 会被替换。
- 如果菜单没有出现，请确认插件已启用并重启 PyMOL。
