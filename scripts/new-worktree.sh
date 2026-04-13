#!/usr/bin/env bash
# new-worktree.sh — Tạo git worktree tách biệt và đồng bộ tệp môi trường cục bộ
#
# Usage: scripts/new-worktree.sh <branch-name> [base-ref]
#   branch-name: tên nhánh cục bộ của worktree mới (đồng thời dùng làm tên thư mục)
#   base-ref:    tùy chọn, ref gốc để tạo (ví dụ origin/feature/xxx), mặc định HEAD

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <branch-name> [base-ref]"
  echo "  branch-name: tên thư mục worktree và tên nhánh cục bộ"
  echo "  base-ref:    tạo từ ref nào (mặc định HEAD)"
  exit 1
fi

BRANCH_NAME="$1"
BASE_REF="${2:-HEAD}"
ROOT=$(git rev-parse --show-toplevel)
TARGET="$ROOT/.worktrees/$BRANCH_NAME"

# --- Tạo worktree ---
if [ -d "$TARGET" ]; then
  echo "✗ Thư mục đã tồn tại: $TARGET"
  exit 1
fi

if [ "$BASE_REF" = "HEAD" ]; then
  git worktree add "$TARGET" -b "$BRANCH_NAME"
else
  git worktree add "$TARGET" --track -b "$BRANCH_NAME" "$BASE_REF"
fi
echo "✓ Đã tạo worktree: $TARGET"

# --- Đồng bộ tệp môi trường cục bộ ---
echo ""
echo "Đang đồng bộ tệp môi trường cục bộ..."

# .claude/settings.local.json
if [ -f "$ROOT/.claude/settings.local.json" ]; then
  mkdir -p "$TARGET/.claude"
  cp "$ROOT/.claude/settings.local.json" "$TARGET/.claude/settings.local.json"
  echo "  ✓ .claude/settings.local.json"
else
  echo "  - .claude/settings.local.json không tồn tại, đã bỏ qua"
fi

# .env
if [ -f "$ROOT/.env" ]; then
  cp "$ROOT/.env" "$TARGET/.env"
  echo "  ✓ .env"
else
  echo "  - .env không tồn tại, đã bỏ qua"
fi

# projects/ — liên kết tượng trưng để dùng chung dữ liệu
if [ -d "$ROOT/projects" ]; then
  rm -rf "$TARGET/projects"
  ln -s "$ROOT/projects" "$TARGET/projects"
  git -C "$TARGET" ls-files projects/ | xargs -r git -C "$TARGET" update-index --skip-worktree
  echo "  ✓ projects/ → $ROOT/projects (symlink)"
else
  echo "  - projects/ không tồn tại, đã bỏ qua"
fi

# .vscode/
if [ -d "$ROOT/.vscode" ]; then
  cp -r "$ROOT/.vscode" "$TARGET/.vscode"
  echo "  ✓ .vscode/"
else
  echo "  - .vscode/ không tồn tại, đã bỏ qua"
fi

# --- Cài đặt phụ thuộc ---
echo ""
echo "Đang cài phụ thuộc dự án..."

if [ -f "$TARGET/pyproject.toml" ]; then
  (cd "$TARGET" && uv sync)
  echo "  ✓ Phụ thuộc Python (uv sync)"
fi

if [ -f "$TARGET/frontend/package.json" ]; then
  (cd "$TARGET/frontend" && pnpm install)
  echo "  ✓ Phụ thuộc frontend (pnpm install)"
fi

# --- Hoàn tất ---
echo ""
echo "========================================="
echo "Worktree đã sẵn sàng: $TARGET"
echo "Nhánh: $BRANCH_NAME"
echo "========================================="
