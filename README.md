<img src="/icons/copy.svg" align="left" height="64px">

# pathfinder

> A QGIS plugin that helps you locate and work with your layer file paths.

## ✨ Features

- 📋 **Copy Path**: Copy the file path of selected layer(s) to clipboard
- 📋 **Copy Path (\\\\)**: Copy with double backslashes (Windows only, press Shift)
- 📂 **Show in Explorer**: Open file explorer at the layer's location
- 🔄 Works with multiple selected layers
- ⌨️ Keyboard shortcuts support
- 🔧 Highly configurable output format
- 🌐 Internationalization support

## 🚀 Installation

1. Open QGIS
2. Go to **Plugins** → **Manage and Install Plugins**
3. Search for "pathfinder"
4. Click **Install Plugin**

## 📖 Usage

### Context Menu
1. Right-click on a layer in the Layers panel
2. Choose one of the pathfinder actions:
   - Copy Path
   - Copy Path (\\\\)
   - Show in Explorer

### Keyboard Shortcuts

1. Go to **Settings** → **Keyboard Shortcuts**
2. Assign hotkey to any of the pathfinder actions

## ⚙️ Configuration

Access pathfinder settings through:
- The pathfinder icon in the Plugins toolbar
- The pathfinder menu in the Plugins menu

### Formatting Options

- **Quote Character**: Character surrounding individual paths
- **Separator Character**: Character separating multiple paths
- **Prefix/Postfix**: Characters to add before/after paths
- **Single Path Options**: Special handling for single paths
- **Path Content**: Include/exclude filename, layer name, subset string
- **Multiple Paths**: Place each path on a separate line

### Special Features

- **Spreadsheet Layers**: Option to return original data source instead of VRT file
- **Notifications**: Show notification with copied text (configurable duration)
