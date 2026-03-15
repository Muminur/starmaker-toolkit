#!/usr/bin/env bash
# StarMaker Toolkit — One-Click Installer (Linux/macOS)
# Usage: curl -sSL https://raw.githubusercontent.com/Muminur/starmaker-toolkit/main/install.sh | bash
set -e

REPO="https://github.com/Muminur/starmaker-toolkit.git"
INSTALL_DIR="$HOME/.starmaker-toolkit"

echo "============================================"
echo "  StarMaker Toolkit — One-Click Installer"
echo "============================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3.9+ is required but not found."
    echo "Install Python: https://www.python.org/downloads/"
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]); then
    echo "ERROR: Python 3.9+ required, found Python $PY_VERSION"
    exit 1
fi

echo "[1/5] Python $PY_VERSION detected"

# Check pip
if ! python3 -m pip --version &>/dev/null; then
    echo "ERROR: pip is required but not found."
    echo "Install pip: python3 -m ensurepip --upgrade"
    exit 1
fi

echo "[2/5] pip available"

# Check git
if ! command -v git &>/dev/null; then
    echo "ERROR: git is required but not found."
    echo "Install git: https://git-scm.com/downloads"
    exit 1
fi

echo "[3/5] git available"

# Clone or update
if [ -d "$INSTALL_DIR" ]; then
    echo "[4/5] Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull --quiet origin main
else
    echo "[4/5] Cloning StarMaker Toolkit..."
    git clone --quiet "$REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Install with browser extras
echo "[5/5] Installing dependencies..."
python3 -m pip install -e ".[browser]" --quiet

# Create .env from example if not exists
if [ ! -f "$INSTALL_DIR/.env" ] && [ -f "$INSTALL_DIR/.env.example" ]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    echo ""
    echo "Created .env file — edit it to add your API credentials:"
    echo "  $INSTALL_DIR/.env"
fi

# Install Playwright browsers for Camoufox
echo ""
echo "Installing Camoufox browser (for automated publishing)..."
python3 -m playwright install firefox 2>/dev/null || true

echo ""
echo "============================================"
echo "  Installation complete!"
echo "============================================"
echo ""
echo "Get started:"
echo "  starmaker              # Interactive mode"
echo "  starmaker init         # Setup wizard"
echo "  starmaker auto-post --readme /path/to/README.md --dry-run"
echo ""
echo "Set up credentials:"
echo "  Edit $INSTALL_DIR/.env"
echo "  Or run: starmaker setup"
echo ""
echo "Full docs: https://github.com/Muminur/starmaker-toolkit"
