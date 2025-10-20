# Jupyter Book Tutorial: Running Experiments with Bluesky

This directory contains an interactive Jupyter Book tutorial for running experiments and capturing data with the Bluesky framework.

## About This Tutorial

This is the same content as `TUTORIAL_RUNNING_EXPERIMENTS.md` but converted into an interactive Jupyter Book format with:

- ✅ **Executable code cells** - Run examples directly in your browser
- ✅ **Live visualizations** - See plots and data inline
- ✅ **Easy navigation** - Sidebar, search, and chapter links
- ✅ **Professional formatting** - Publication-quality presentation
- ✅ **Copy-paste ready** - All code blocks have copy buttons

## Tutorial Contents

### Part 1: Getting Started
1. **Introduction** - Prerequisites and setup verification
2. **Quick Start (5 Minutes)** - Run your first experiment immediately
3. **Running Methods** - Four different approaches explained

### Part 2: Understanding the Framework
4. **What Gets Captured** - The Bluesky document model
5. **Verifying Data Capture** - Ensure data was saved correctly

### Part 3: Working with Data
6. **Retrieving and Analyzing Data** - Access and process results
7. **Practical Examples** - Complete working examples

### Part 4: Reference
8. **Troubleshooting** - Solutions to common problems
9. **Next Steps** - Where to go from here

## Prerequisites

Before building or using this tutorial:

1. **Conda environment activated:**
   ```bash
   conda activate gnuradio
   ```

2. **Required packages installed:**
   ```bash
   pip install bluesky ophyd databroker matplotlib pandas scipy openpyxl h5py
   ```

3. **Jupyter Book installed:**
   ```bash
   pip install jupyter-book
   ```

## Building the Book

### Quick Build

```bash
# From the jupyter_book_tutorial directory
jupyter-book build .
```

The built HTML will be in `_build/html/`.

### View the Book

```bash
# Open in browser (macOS)
open _build/html/index.html

# Linux
xdg-open _build/html/index.html

# Windows
start _build/html/index.html
```

### Clean Build (if needed)

```bash
# Remove old build
jupyter-book clean .

# Rebuild from scratch
jupyter-book build .
```

## Using the Interactive Tutorial

### Option 1: View Built HTML

1. Build the book (see above)
2. Open `_build/html/index.html` in your browser
3. Navigate through chapters
4. Code cells are syntax-highlighted but not executable

### Option 2: Use with JupyterLab/Notebook

1. Open individual notebooks:
   ```bash
   jupyter notebook intro.ipynb
   # or
   jupyter lab
   ```
2. Execute code cells interactively
3. Modify and experiment

### Option 3: Deploy as Website

The built HTML can be deployed to:
- GitHub Pages
- Read the Docs
- Netlify
- Any static web hosting

Example for GitHub Pages:
```bash
# After building
pip install ghp-import
ghp-import -n -p -f _build/html
```

## Directory Structure

```
jupyter_book_tutorial/
├── _config.yml              # Jupyter Book configuration
├── _toc.yml                 # Table of contents
├── references.bib           # Bibliography (optional)
├── README.md               # This file
├── intro.ipynb             # Landing page
├── 01_quick_start.ipynb    # Quick start tutorial
├── 02_running_methods.ipynb
├── 03_data_capture.ipynb
├── 04_verification.ipynb
├── 05_retrieval_analysis.ipynb
├── 06_practical_examples.ipynb
├── 07_troubleshooting.ipynb
├── 08_next_steps.ipynb
└── _build/                 # Generated HTML (after building)
    └── html/
        └── index.html      # Main entry point
```

## Customization

### Change Book Title or Author

Edit `_config.yml`:
```yaml
title: "Your Custom Title"
author: "Your Name"
```

### Modify Table of Contents

Edit `_toc.yml` to reorder chapters or add new ones.

### Add New Chapters

1. Create new `.ipynb` file
2. Add entry to `_toc.yml`
3. Rebuild the book

### Change Theme/Styling

In `_config.yml`, modify:
```yaml
html:
  use_issues_button: true
  use_repository_button: true
```

See [Jupyter Book documentation](https://jupyterbook.org/) for all options.

## Features

### Navigation
- **Sidebar**: Chapter list and search
- **Previous/Next**: Buttons at bottom of each page
- **Breadcrumbs**: Current location indicator

### Code Blocks
- **Copy button**: Hover over code blocks
- **Syntax highlighting**: Language-specific colors
- **Line numbers**: Optional

### Special Content Blocks

```{note}
Blue note boxes for tips
```

```{warning}
Yellow warning boxes for cautions
```

```{important}
Red important boxes for critical info
```

## Troubleshooting Build Issues

### Issue: "jupyter-book: command not found"

```bash
pip install jupyter-book
```

### Issue: Import errors in notebooks

Make sure you're in the correct directory:
```bash
cd /path/to/full_system/jupyter_book_tutorial
```

Or notebooks will handle path adjustments automatically.

### Issue: Notebooks fail to execute during build

Set `execute_notebooks: cache` in `_config.yml` (already configured).

Or force no execution:
```yaml
execute:
  execute_notebooks: 'off'
```

### Issue: Build is slow

Use cache mode (default) or skip execution:
```bash
jupyter-book build . --builder html --execute-notebooks cache
```

## Differences from Original Tutorial

### Advantages of Jupyter Book Version:
- ✅ Professional web interface
- ✅ Easy navigation and search
- ✅ Executable code cells
- ✅ Better for distribution
- ✅ Can deploy as website

### When to Use Original Markdown:
- 📄 Quick reference
- 📄 Reading offline
- 📄 Viewing in IDE
- 📄 Simple text search

**Both versions contain the same content** - use whichever format suits your workflow!

## Additional Resources

- **Original Tutorial**: `../TUTORIAL_RUNNING_EXPERIMENTS.md`
- **Quick Reference**: `../QUICK_REFERENCE.md`
- **Main Documentation**: `../README.md`
- **Data Analysis Guide**: `../DATA_RETRIEVAL_AND_ANALYSIS_GUIDE.md`

## Contributing

To add or improve content:

1. Edit the relevant `.ipynb` file
2. Test in Jupyter: `jupyter notebook <file>.ipynb`
3. Rebuild book: `jupyter-book build .`
4. Verify in browser

## License

This tutorial is part of the EJFAT demos and follows the same license as the main project.

## Support

- EJFAT GitHub: https://github.com/JeffersonLab/E2SAR
- Jupyter Book Docs: https://jupyterbook.org/
- Bluesky Docs: https://blueskyproject.io/

---

**Happy Learning!** 🚀
