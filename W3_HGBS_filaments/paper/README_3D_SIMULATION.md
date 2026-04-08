# 3D SIMULATION SETUP FOR ADVANCED SERVER

**Status**: ✅ Ready to run on advanced server

---

## QUICK ANSWER

**YES**, you can push this folder to GitHub and run on your advanced server, **BUT** there are a few important things to know first:

1. **Only push the 3D simulation files** (don't push large PDFs, logs, cache files)
2. **Install dependencies** on the server first
3. **Run the simplified version** (the comprehensive version has bugs and is much slower)

---

## WHAT TO PUSH TO GITHUB

### Essential Files (Required)
```
run_3d_simulations.py          # Simplified 3D solver (RECOMMENDED)
filament_3d_simulations.py      # Comprehensive solver (has bugs, slower)
run_strategic_validation.py     # Strategic validation script
strategic_3d_validation_results.json  # Previous results (for reference)
benchmark_results.json         # Performance benchmarks
```

### Files to EXCLUDE (use .gitignore)
```
*.pdf              # Large PDF files
*.log              # Log files
*.aux              # LaTeX auxiliary files
*.bbl              # BibTeX files
*.blg              # BibTeX log files
*.out              # Output files
__pycache__/       # Python cache
figures/           # Large figure files
*.tex              # LaTeX source (keep for reference but not needed for 3D)
*.json             # Keep data files but exclude large ones
```

---

## DEPENDENCIES TO INSTALL ON SERVER

```bash
# Python 3.8+ required
python3 --version

# Install scientific packages
pip install numpy scipy h5py

# Or using conda (recommended for HPC)
conda install numpy scipy h5py
```

**Specific versions tested**:
- Python 3.10.12
- NumPy 2.4.0
- SciPy 1.14.1
- h5py 3.13.0

---

## WHICH SCRIPT TO RUN

### Option 1: Simplified Solver (RECOMMENDED)
**File**: `run_3d_simulations.py`

**Pros**:
- ✅ Fast (~50 seconds per simulation)
- ✅ Works correctly
- ✅ Successfully forms cores
- ⚠️ Underpredicts spacing by 60-70% (known limitation)

**Run command**:
```bash
python3 run_3d_simulations.py
```

**Runtime on your server**:
- 4 simulations × ~50 seconds = ~3 minutes total
- Or modify for more simulations (edit the test_cases list)

---

### Option 2: Comprehensive Solver (NOT RECOMMENDED)
**File**: `filament_3d_simulations.py`

**Issues**:
- ❌ Has bugs (we fixed some but may remain)
- ❌ 8-10× slower (~7-10 minutes per simulation)
- ❌ Produces similar underprediction

**Status**: Not production-ready

---

## RECOMMENDED WORKFLOW

### 1. Clean Before Pushing
```bash
# Remove unnecessary files
rm -f *.log *.aux *.bbl *.blg
rm -rf __pycache__/
rm -f benchmark_output.log benchmark_simple.log
```

### 2. Create .gitignore (if not exists)
```bash
cat > .gitignore << 'EOF'
# LaTeX
*.aux
*.bbl
*.blg
*.log
*.out
*.toc
*.fls
*.fdb_latexmk

# PDFs (large files)
*.pdf

# Python
__pycache__/
*.pyc
*.pyo

# Data files (optional)
# *.json
EOF
```

### 3. Push to GitHub
```bash
git init
git add run_3d_simulations.py filament_3d_simulations.py run_strategic_validation.py
git add strategic_3d_validation_results.json benchmark_results.json
git add .gitignore
git commit -m "Add 3D filament simulation code"
git push origin main
```

### 4. On Your Advanced Server
```bash
# Clone repository
git clone <your-repo-url>
cd <repo-name>

# Install dependencies
pip install numpy scipy

# Run the simulation
python3 run_3d_simulations.py
```

---

## EXPECTED RUNTIMES

Based on benchmark results (64³ grid, 3 Myr, 6000 steps):

| Hardware | Time per simulation | 4 simulations | 20 simulations |
|----------|---------------------|---------------|----------------|
| **Your current Mac** | ~50 seconds | ~3 minutes | ~17 minutes |
| **2× faster server** | ~25 seconds | ~1.5 minutes | ~8 minutes |
| **10× faster server** | ~5 seconds | ~20 seconds | ~2 minutes |
| **32-core cluster** | ~2 seconds | ~8 seconds | ~40 seconds |

---

## IF YOU WANT TO MODIFY PARAMETERS

Edit `run_3d_simulations.py` around line 194-199:

```python
test_cases = [
    # (name, L_pc, P_ext, B, description)
    ("Baseline", 0.4, 0, 0, "L/H=10, no pressure, no B-field"),
    ("Best2D", 0.4, 2e5, 0, "Best 2D match (L/H=10, P=2e5)"),
    ("W3_like", 0.32, 5e5, 0, "W3-like (L/H=8, P=5e5)"),
    # Add more cases here...
]
```

---

## OUTPUT FILES

The scripts will create:
- `3d_simulation_results.json` - Results from all simulations
- Console output with progress updates

---

## TROUBLESHOOTING

### If you get import errors:
```bash
pip install --upgrade numpy scipy
```

### If simulations are too slow:
- Reduce `n_steps` parameter (line 219)
- Reduce grid size (change `nz=64, nx=64, ny=64` to smaller values)

### If you want to run the comprehensive solver:
1. First fix remaining bugs (see PEER_REVIEW_COMMENTS.md)
2. Expect 8-10× longer runtimes
3. May need more RAM for larger grids

---

## RECOMMENDATION

For your advanced server:

1. **Start with simplified version** (`run_3d_simulations.py`)
2. **Run 20-50 simulations** to get good statistics
3. **Results will show core formation** but spacings will be 60-70% too small
4. **This is expected** - the simplified solver lacks advection

For publication-quality 3D results, you would need:
- Full advection scheme
- Larger domains (1-2 pc length)
- Higher resolution (128³ or 256³)
- More sophisticated numerical methods
- **10,000+ CPU hours of computation**

---

## SUMMARY

✅ **Yes, you can push this folder to GitHub and run on your advanced server**
✅ **Use `run_3d_simulations.py`** (simplified, working, fast)
⚠️ **Don't use `filament_3d_simulations.py`** (has bugs, slow, no better accuracy)
✅ **Install numpy, scipy on server first**
✅ **Expected runtime: ~3 minutes for 4 simulations, ~17 minutes for 20**

The simplified 3D solver is **fast and works correctly** for demonstrating core formation, even though it doesn't match observations quantitatively (that's what the 2D linear theory is for).
