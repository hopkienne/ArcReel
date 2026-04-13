#!/usr/bin/env python3
"""
Script di chuyển dữ liệu: chuyển characters của dự án hiện có từ kịch bản sang project.json

Cách dùng:
    python scripts/migrate_to_project_json.py <ten_du_an>
    python scripts/migrate_to_project_json.py --all  # Di chuyển tất cả dự án
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Thêm thư mục lib vào Python path
lib_path = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from project_manager import ProjectManager


def migrate_project(pm: ProjectManager, project_name: str, dry_run: bool = False) -> bool:
    """
    Di chuyển một dự án

    Args:
        pm: instance ProjectManager
        project_name: tên dự án
        dry_run: chỉ xem trước, không thực thi

    Returns:
        Có thành công hay không
    """
    print(f"\n{'=' * 50}")
    print(f"Di chuyển dự án: {project_name}")
    print("=" * 50)

    try:
        project_dir = pm.get_project_path(project_name)
    except FileNotFoundError:
        print(f"  ❌ Dự án không tồn tại: {project_name}")
        return False

    # Kiểm tra project.json đã tồn tại chưa
    project_file = project_dir / "project.json"
    if project_file.exists():
        print("  ⚠️  project.json đã tồn tại, bỏ qua di chuyển")
        print(f"  Nếu muốn di chuyển lại, hãy xóa trước {project_file}")
        return True

    # Thu thập nhân vật từ tất cả kịch bản
    scripts_dir = project_dir / "scripts"
    all_characters = {}
    episodes = []
    script_files = list(scripts_dir.glob("*.json")) if scripts_dir.exists() else []

    if not script_files:
        print("  ⚠️  Không tìm thấy tệp kịch bản")

    for script_file in sorted(script_files):
        print(f"\n  📖 Đang xử lý kịch bản: {script_file.name}")

        with open(script_file, encoding="utf-8") as f:
            script = json.load(f)

        # Trích xuất nhân vật
        characters = script.get("characters", {})
        for name, char_data in characters.items():
            if name not in all_characters:
                all_characters[name] = char_data.copy()
                print(f"      👤 Phát hiện nhân vật: {name}")
            else:
                # Gộp dữ liệu (ưu tiên bản có ảnh thiết kế)
                if char_data.get("character_sheet") and not all_characters[name].get("character_sheet"):
                    all_characters[name] = char_data.copy()
                    print(f"      👤 Cập nhật nhân vật: {name} (có ảnh thiết kế)")

        # Trích xuất thông tin tập
        novel_info = script.get("novel", {})
        scenes_count = len(script.get("scenes", []))

        # Thử suy ra số tập từ tên file hoặc nội dung
        episode_num = 1
        filename_lower = script_file.stem.lower()
        for i in range(1, 100):
            if f"episode_{i:02d}" in filename_lower or f"episode{i}" in filename_lower:
                episode_num = i
                break
            if f"chapter_{i:02d}" in filename_lower or f"chapter{i}" in filename_lower:
                episode_num = i
                break
            if f"_{i:02d}_" in filename_lower or f"_{i}_" in filename_lower:
                episode_num = i
                break

        # Thêm thông tin tập (không gồm trường thống kê, StatusCalculator sẽ tính lúc đọc)
        episodes.append(
            {
                "episode": episode_num,
                "title": novel_info.get("chapter", script_file.stem),
                "script_file": f"scripts/{script_file.name}",
            }
        )
        print(f"      📺 Tập {episode_num}: {scenes_count} cảnh")

    # Khử trùng lặp và sắp xếp tập
    seen_episodes = {}
    for ep in episodes:
        if ep["episode"] not in seen_episodes:
            seen_episodes[ep["episode"]] = ep
    episodes = sorted(seen_episodes.values(), key=lambda x: x["episode"])

    # Dựng project.json
    project_title = project_name
    if script_files:
        with open(script_files[0], encoding="utf-8") as f:
            first_script = json.load(f)
            project_title = first_script.get("novel", {}).get("title", project_name)

    # Dựng project.json (không gồm trường status, StatusCalculator sẽ tính lúc đọc)
    project_data = {
        "title": project_title,
        "style": "",
        "episodes": episodes,
        "characters": all_characters,
        "clues": {},
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "migrated_from": "script_based_characters",
        },
    }

    # Thống kê ảnh thiết kế nhân vật đã hoàn thành (chỉ dùng để in log)
    completed_chars = 0
    for name, char_data in all_characters.items():
        sheet = char_data.get("character_sheet")
        if sheet:
            sheet_path = project_dir / sheet
            if sheet_path.exists():
                completed_chars += 1

    # Tạo thư mục clues
    clues_dir = project_dir / "clues"
    if not clues_dir.exists():
        if not dry_run:
            clues_dir.mkdir(parents=True, exist_ok=True)
        print("\n  📁 Tạo thư mục: clues/")

    print("\n  📊 Tóm tắt di chuyển:")
    print(f"      - Nhân vật: {len(all_characters)} ({completed_chars} có ảnh thiết kế)")
    print(f"      - Tập: {len(episodes)}")
    print("      - Manh mối: 0 (chờ bổ sung)")

    if dry_run:
        print("\n  🔍 Chế độ xem trước - sẽ không ghi tệp thực tế")
        print("\n  Sẽ tạo project.json:")
        print(json.dumps(project_data, ensure_ascii=False, indent=2)[:500] + "...")
    else:
        # Ghi project.json
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
        print("\n  ✅ Đã tạo project.json")

        # Tùy chọn: xóa trường characters khỏi kịch bản (giữ bản sao lưu tệp gốc)
        # Ở đây giữ lại trường characters trong kịch bản để đảm bảo tương thích ngược
        print("  ℹ️  Giữ trường characters trong kịch bản để đảm bảo tương thích ngược")

    return True


def main():
    parser = argparse.ArgumentParser(description="Di chuyển dữ liệu dự án sang project.json")
    parser.add_argument("project", nargs="?", help="Tên dự án, hoặc dùng --all để di chuyển tất cả dự án")
    parser.add_argument("--all", action="store_true", help="Di chuyển tất cả dự án")
    parser.add_argument("--dry-run", action="store_true", help="Chế độ xem trước, không thực thi thực tế")
    parser.add_argument("--projects-root", default=None, help="Thư mục gốc dự án")

    args = parser.parse_args()

    if not args.project and not args.all:
        parser.print_help()
        print("\n❌ Vui lòng chỉ định tên dự án hoặc dùng --all")
        sys.exit(1)

    # Khởi tạo ProjectManager
    pm = ProjectManager(projects_root=args.projects_root)

    print("🚀 Bắt đầu di chuyển...")
    print(f"   Thư mục gốc dự án: {pm.projects_root}")

    if args.dry_run:
        print("   📋 Đã bật chế độ xem trước")

    success_count = 0
    fail_count = 0

    if args.all:
        projects = pm.list_projects()
        print(f"   Phát hiện {len(projects)} dự án")

        for project_name in projects:
            if migrate_project(pm, project_name, dry_run=args.dry_run):
                success_count += 1
            else:
                fail_count += 1
    else:
        if migrate_project(pm, args.project, dry_run=args.dry_run):
            success_count = 1
        else:
            fail_count = 1

    print("\n" + "=" * 50)
    print("Di chuyển hoàn tất!")
    print(f"   ✅ Thành công: {success_count}")
    print(f"   ❌ Thất bại: {fail_count}")
    print("=" * 50)

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
