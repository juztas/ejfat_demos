# 🚀 START HERE

## Quick Start (3 Steps)

### Step 1: Install Jupyter Book
```bash
pip install jupyter-book
```

### Step 2: Build the Tutorial
```bash
jupyter-book build .
```

### Step 3: Open in Browser
```bash
# macOS
open _build/html/index.html

# Linux
xdg-open _build/html/index.html

# Windows
start _build/html/index.html
```

## That's It!

You now have a professional, interactive web-based tutorial for running experiments with Bluesky.

## What You Get

- ✅ 8 interactive chapters
- ✅ Executable code examples
- ✅ Navigation sidebar with search
- ✅ Copy-paste ready code blocks
- ✅ Professional formatting

## First Time Using Jupyter Book?

**Q: What is Jupyter Book?**
A: A tool that creates beautiful, publication-quality websites from Jupyter notebooks.

**Q: Do I need to know anything special?**
A: No! Just run the three commands above.

**Q: Can I edit the notebooks?**
A: Yes! Edit any `.ipynb` file and rebuild.

**Q: How do I run the code interactively?**
A: Open notebooks in JupyterLab: `jupyter lab intro.ipynb`

## Troubleshooting

**Build fails?**
- Make sure `jupyter-book` is installed: `pip install jupyter-book`
- Try: `jupyter-book clean . && jupyter-book build .`

**Can't see the website?**
- Check that `_build/html/index.html` exists
- Try opening it directly from your file manager

**Want to skip notebook execution?**
- Edit `_config.yml`, set `execute_notebooks: 'off'`

## Next Steps

1. **Browse** the tutorial in your web browser
2. **Try** the code examples in JupyterLab
3. **Read** `README.md` for full documentation
4. **Explore** other chapters

## Need More Help?

- **Complete README**: [README.md](README.md)
- **Build Instructions**: [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)
- **Conversion Summary**: [../JUPYTER_BOOK_CONVERSION_SUMMARY.md](../JUPYTER_BOOK_CONVERSION_SUMMARY.md)

---

**Happy Learning!** 📚
