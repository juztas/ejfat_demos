# Quick Build Instructions

## Prerequisites

```bash
# Activate environment
conda activate gnuradio

# Install Jupyter Book
pip install jupyter-book
```

## Build the Book

```bash
# From the jupyter_book_tutorial directory
cd jupyter_book_tutorial

# Build
jupyter-book build .

# Open in browser (macOS)
open _build/html/index.html

# Linux
xdg-open _build/html/index.html
```

## Expected Output

```
Running Jupyter-Book v1.0.0
Source Folder: /path/to/jupyter_book_tutorial
Config Path: /path/to/jupyter_book_tutorial/_config.yml
Output Path: /path/to/jupyter_book_tutorial/_build/html
...
Finished generating HTML for book.
```

## View the Tutorial

Open `_build/html/index.html` in your browser to see the interactive tutorial.

## Rebuild After Changes

```bash
# Clean old build
jupyter-book clean .

# Rebuild
jupyter-book build .
```

## Troubleshooting

**Problem**: `jupyter-book: command not found`
```bash
pip install jupyter-book
```

**Problem**: Build fails with import errors
- Don't worry! Set `execute_notebooks: 'off'` in `_config.yml` to skip execution

**Problem**: Slow build
- First build caches notebooks, subsequent builds are faster
- Or set `execute_notebooks: 'off'` to skip execution

## Next Steps

See `README.md` for complete documentation.
