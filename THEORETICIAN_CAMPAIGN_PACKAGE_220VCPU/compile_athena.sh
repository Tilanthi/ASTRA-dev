#!/bin/bash
# Compile Athena++ for filament fragmentation problem

set -e

echo "=========================================="
echo "Athena++ Compilation"
echo "=========================================="
echo ""

# Check if Athena++ directory exists
if [ ! -d "athena-public-version" ]; then
    echo "Cloning Athena++..."
    git clone https://github.com/PrincetonUniversity/athena-public-version
    cd athena-public-version
    git checkout v21.0
    cd ..
else
    echo "Athena++ directory already exists"
fi

cd athena-public-version

echo ""
echo "Configuring Athena++..."
./configure --h5double --mpi --prob=filament_spacing

echo ""
echo "Compiling Athena++..."
make clean
make all -j 16

echo ""
echo "=========================================="
echo "Compilation complete!"
echo "=========================================="
echo ""

# Verify executable
if [ -f "bin/athena" ]; then
    echo "✓ Athena++ executable found: bin/athena"
    ls -lh bin/athena
else
    echo "✗ Athena++ executable not found!"
    echo "Compilation may have failed. Check the output above."
    exit 1
fi

echo ""
echo "Ready to run simulations!"
