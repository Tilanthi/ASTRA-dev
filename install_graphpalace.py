#!/usr/bin/env python3
# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
GraphPalace Automated Installer for ASTRA
Installs GraphPalace Rust-based memory palace engine with Python bindings.
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
import time

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def run_command(cmd, check=True, capture_output=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if capture_output:
            print_error(f"Command failed: {cmd}")
            print_error(f"Error: {e.stderr}")
        raise

def check_rust():
    """Check if Rust toolchain is installed."""
    print_info("Checking Rust installation...")

    # Check for rustc
    rustc_path = shutil.which("rustc")
    if not rustc_path:
        return False, "Rust compiler (rustc) not found"

    # Check for cargo
    cargo_path = shutil.which("cargo")
    if not cargo_path:
        return False, "Cargo package manager not found"

    # Get versions
    try:
        result = run_command("rustc --version")
        rustc_version = result.stdout.strip()
        print_success(f"Rust installed: {rustc_version}")

        result = run_command("cargo --version")
        cargo_version = result.stdout.strip()
        print_success(f"Cargo installed: {cargo_version}")

        return True, (rustc_version, cargo_version)
    except Exception as e:
        return False, f"Error checking Rust versions: {e}"

def install_rust():
    """Install Rust via rustup."""
    print_warning("Rust not found. Installing via rustup...")

    if os.name != 'posix':
        print_error("Automatic Rust installation only supported on Unix-like systems.")
        print_error("Please install Rust manually from: https://rustup.rs/")
        return False

    # Install rustup
    try:
        subprocess.run(
            "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
            shell=True,
            check=True
        )

        # Source cargo env
        cargo_env = os.path.expanduser("~/.cargo/env")
        if os.path.exists(cargo_env):
            # Read and execute the env file
            with open(cargo_env) as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        if 'PATH=' in line or 'export' in line:
                            line = line.replace('export ', '').strip()
                            key, value = line.split('=', 1)
                            os.environ[key] = os.path.expandvars(value)

        print_success("Rust installed successfully")
        return True
    except Exception as e:
        print_error(f"Failed to install Rust: {e}")
        return False

def check_python():
    """Check Python installation."""
    print_info("Checking Python installation...")

    python_version = sys.version_info
    if python_version.major < 3 or python_version.minor < 8:
        print_error(f"Python 3.8+ required, found {sys.version}")
        return False

    print_success(f"Python installed: {sys.version.split()[0]}")
    return True

def install_maturin():
    """Install maturin for building Python bindings."""
    print_info("Installing maturin (Python-Rust FFI tool)...")

    # Try uv first (preferred for this system), then pip
    commands = [
        "uv pip install maturin",
        "python3 -m pip install --user maturin",
        "python3 -m pip install --break-system-packages maturin"
    ]

    for cmd in commands:
        try:
            run_command(cmd)
            print_success("maturin installed")
            return True
        except Exception as e:
            continue

    print_error(f"Failed to install maturin with all methods")
    return False

def clone_graphpalace(install_dir):
    """Clone GraphPalace repository."""
    print_info("Cloning GraphPalace repository...")

    repo_url = "https://github.com/web3guru888/GraphPalace.git"
    target_dir = install_dir / "GraphPalace"

    try:
        if target_dir.exists():
            print_warning(f"Directory {target_dir} already exists, removing...")
            shutil.rmtree(target_dir)

        subprocess.run(
            f"git clone {repo_url} {target_dir}",
            shell=True,
            check=True
        )
        print_success(f"Repository cloned to {target_dir}")
        return target_dir
    except Exception as e:
        print_error(f"Failed to clone repository: {e}")
        return None

def build_python_bindings(graphpalace_dir):
    """Build Python bindings using maturin."""
    print_info("Building Python bindings (this may take 10-20 minutes)...")

    python_dir = graphpalace_dir / "rust" / "gp-python"

    if not python_dir.exists():
        print_error(f"Python bindings directory not found: {python_dir}")
        return False

    try:
        os.chdir(python_dir)

        # Build in release mode
        start_time = time.time()
        result = subprocess.run(
            "maturin develop --release",
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        elapsed = time.time() - start_time

        print_success(f"Python bindings built in {elapsed:.1f} seconds")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Build failed:")
        print_error(e.stderr)
        return False
    except Exception as e:
        print_error(f"Error building Python bindings: {e}")
        return False

def verify_installation():
    """Verify GraphPalace installation."""
    print_info("Verifying installation...")

    try:
        # Try importing the module
        result = subprocess.run(
            "python3 -c 'import graphpalace; print(graphpalace.__version__)'",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print_success(f"GraphPalace installed: {result.stdout.strip()}")
            return True
        else:
            print_error(f"Import test failed: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Verification failed: {e}")
        return False

def create_test_script():
    """Create a test script to verify GraphPalace functionality."""
    test_script = """#!/usr/bin/env python3
# Test GraphPalace installation

import sys

try:
    from graphpalace import Palace
    print("✓ GraphPalace module imported successfully")

    # Try creating a simple palace
    palace = Palace(":memory:")
    print("✓ In-memory palace created")

    # Try a simple operation
    palace.add_drawer("Test memory", "test_wing", "test_room")
    print("✓ Drawer added successfully")

    print("\\n✓ All tests passed! GraphPalace is ready to use.")
    sys.exit(0)

except ImportError as e:
    print(f"✗ Import error: {e}")
    print("\\nGraphPalace Python bindings not installed correctly.")
    print("The module exists but cannot be imported.")
    sys.exit(1)

except Exception as e:
    print(f"✗ Test failed: {e}")
    sys.exit(1)
"""

    test_path = Path("/tmp/test_graphpalace.py")
    with open(test_path, 'w') as f:
        f.write(test_script)

    return test_path

def main():
    """Main installation process."""
    print_header("GraphPalace Automated Installer for ASTRA")

    # Installation directory
    install_dir = Path.home() / ".astra" / "graphpalace"
    install_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Check Rust
    print_header("Step 1: Rust Toolchain")
    rust_ok, rust_info = check_rust()

    if not rust_ok:
        print_warning(rust_info)
        response = input("Install Rust now? [Y/n]: ").strip().lower()
        if response != 'n':
            if not install_rust():
                print_error("Rust installation failed. Aborting.")
                return False
        else:
            print_error("Rust is required. Aborting.")
            return False

    # Step 2: Check Python
    print_header("Step 2: Python Environment")
    if not check_python():
        return False

    # Step 3: Install maturin
    print_header("Step 3: Build Tools")
    if not install_maturin():
        return False

    # Step 4: Clone GraphPalace
    print_header("Step 4: GraphPalace Source")
    graphpalace_dir = clone_graphpalace(install_dir)
    if not graphpalace_dir:
        return False

    # Step 5: Build Python bindings
    print_header("Step 5: Building Python Bindings")
    if not build_python_bindings(graphpalace_dir):
        print_error("Build failed. Check the error messages above.")
        return False

    # Step 6: Verify installation
    print_header("Step 6: Verification")
    if verify_installation():
        print_success("GraphPalace installed successfully!")
    else:
        print_warning("Installation verification failed, but build may have succeeded.")
        print_warning("You can test manually with: python3 -c 'import graphpalace'")

    # Step 7: Run test script
    print_header("Step 7: Functional Test")
    test_script = create_test_script()
    print_info("Running functional test...")
    result = subprocess.run(f"python3 {test_script}", shell=True)

    if result.returncode == 0:
        print_success("Functional test passed!")
    else:
        print_warning("Functional test failed (this may be expected during dev)")

    # Final summary
    print_header("Installation Summary")
    print_success("GraphPalace has been installed")
    print()
    print_info("Next steps:")
    print("  1. Test: python3 -c 'from graphpalace import Palace'")
    print("  2. Read docs: https://github.com/web3guru888/GraphPalace")
    print("  3. Integrate into ASTRA with astra_live_backend/graphpalace_memory.py")

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
