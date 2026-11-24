#!/usr/bin/env python3
"""Build the Codex and WorkBuddy skill archives with Python's standard library."""

from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "easydash-theme"
SOURCE = ROOT / "skills" / SKILL_NAME
FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "assets/preview.png",
    "assets/starter.json",
    "references/chat-to-theme.html",
    "references/theme-format.md",
    "references/通用对话提示词.txt",
    "scripts/pack_theme.py",
    "使用与提示词.md",
)
WORKBUDDY_FIELDS = """\
display_name: EasyDash 仪表主题生成器
display_name_en: EasyDash Dashboard Theme Generator
description_zh: 根据文字、参考图或旧主题生成可编辑的 EasyDash 汽车仪表主题。
description_en: Create editable EasyDash automotive dashboard themes from a prompt, reference image, or existing theme.
version: "1.0.0"
author: mbwscn-design
"""


def workbuddy_definition(source):
    """Insert market metadata while preserving the shared frontmatter and body."""
    lines = source.splitlines(keepends=True)
    if not lines or lines[0] not in (b"---\n", b"---\r\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    newline = lines[0][3:]
    try:
        closing = source.splitlines().index(b"---", 1)
    except ValueError:
        raise ValueError("SKILL.md is missing the closing YAML delimiter") from None
    fields = WORKBUDDY_FIELDS.encode("utf-8").replace(b"\n", newline)
    lines.insert(closing, fields)
    return b"".join(lines)


def build_zip(files):
    data = BytesIO()
    with ZipFile(data, "w") as archive:
        for name, contents in sorted(files.items()):
            # Fixed timestamp (ZipInfo defaults to 1980-01-01) and permissions.
            entry = ZipInfo(f"{SKILL_NAME}/{name}")
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, contents, compress_type=ZIP_DEFLATED)
    return data.getvalue()


def main():
    files = {name: (SOURCE / name).read_bytes() for name in FILES}
    files["LICENSE"] = (ROOT / "LICENSE").read_bytes()
    codex = build_zip(files)

    del files["agents/openai.yaml"]
    files["SKILL.md"] = workbuddy_definition(files["SKILL.md"])
    workbuddy = build_zip(files)

    dest = ROOT / "downloads"
    dest.mkdir(exist_ok=True)
    (dest / f"{SKILL_NAME}.zip").write_bytes(codex)
    (dest / f"{SKILL_NAME}.skill").write_bytes(codex)
    (dest / f"{SKILL_NAME}-workbuddy.zip").write_bytes(workbuddy)


if __name__ == "__main__":
    main()
