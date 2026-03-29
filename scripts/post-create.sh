#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Setting up development environment..."

# ── Oh My Zsh theme ──
sed -i 's/ZSH_THEME=".*"/ZSH_THEME="ys"/' ~/.zshrc

# ── Persistent shell history (survives container rebuilds) ──
SNIPPET="export HISTFILE=/commandhistory/.zsh_history"
if ! grep -q "$SNIPPET" ~/.zshrc 2>/dev/null; then
    mkdir -p /commandhistory
    touch /commandhistory/.zsh_history
    echo "$SNIPPET" >> ~/.zshrc
fi

# ── Shell completions ──
echo 'eval "$(uv generate-shell-completion zsh)"' >> ~/.zshrc
echo 'eval "$(uvx --generate-shell-completion zsh)"' >> ~/.zshrc

# ── Install all dependencies ──
echo "📦 Installing dependencies with uv..."
uv sync

# ── Set up pre-commit hooks ──
echo "🔗 Installing pre-commit hooks..."
uv run pre-commit install

# ── Verify installation ──
echo ""
echo "✅ Development environment ready!"
echo "   Run 'uv run poe check' to verify everything works."
