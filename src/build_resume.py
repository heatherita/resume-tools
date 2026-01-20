#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def norm_tags(tags: Any) -> set[str]:
    if tags is None:
        return set()
    if isinstance(tags, str):
        return {tags.lower().strip()}
    if isinstance(tags, list):
        return {str(t).lower().strip() for t in tags}
    return {str(tags).lower().strip()}


def bullet_included(
    bullet_tags: set[str],
    include: set[str],
    exclude: set[str],
    mode: str,
) -> bool:
    # Exclude always wins
    if exclude and (bullet_tags & exclude):
        return False

    # If no include filter, keep everything (except excluded)
    if not include:
        return True

    if mode == "any":
        return bool(bullet_tags & include)
    if mode == "all":
        return include.issubset(bullet_tags)
    raise ValueError(f"Unknown mode: {mode}")


def md_escape(s: str) -> str:
    return s.replace("\r\n", "\n").strip()


def render_header(data: dict[str, Any]) -> str:
    lines = []
    lines.append(f"# {md_escape(data.get('name',''))}".strip())
    lines.extend(["", "----", "\n"])

    contact_bits = []
    for k in ("location", "phone", "email"):
        v = data.get(k)
        if v:
            contact_bits.append(md_escape(str(v)))
    if contact_bits:
        lines.append(f"### {" • ".join(contact_bits)}")
    lines.append("")
    return "\n".join(lines)


def render_summary(data: dict[str, Any]) -> str:
    summary = data.get("summary")
    if not summary:
        return ""
    return "\n".join([md_escape(summary), "\n"])


def render_skills(data: dict[str, Any]) -> str:
    skills = data.get("skills") or []
    if not skills:
        return ""
    lines = ["## Technical Skills", "", "----", "\n"]
    for s in skills:
        header = md_escape(s.get("header"))
        skill = md_escape(s.get("skill"))
        lines.append(f"- **{md_escape(str(header))}** {md_escape(str(skill))}")
    lines.append("")
    return "\n".join(lines)


def render_experience(
    data: dict[str, Any],
    include: set[str],
    exclude: set[str],
    mode: str,
) -> str:
    exp = data.get("experience") or []
    if not exp:
        return ""
    out = ["## Professional Experience", "", "----", "\n"]
    for role in exp:
        company = md_escape(str(role.get("company","")))
        title = md_escape(str(role.get("title","")))
        location = md_escape(str(role.get("location","")))
        dates = md_escape(str(role.get("dates","")))
        heading_company = f"**{company} — {title}**".strip()
        heading_location =f"{location} ({dates})".strip()
        out.extend([heading_company, heading_location,""])

        kept = []
        for b in role.get("bullets") or []:
            text = md_escape(str(b.get("text","")))
            tags = norm_tags(b.get("tags"))
            if text and bullet_included(tags, include, exclude, mode):
                kept.append(text)

        if kept:
            for t in kept:
                out.append(f"- {t}")
        else:
            out.append("- (No bullets matched selected tags.)")

        out.append("")
    return "\n".join(out)


def render_projects(
    data: dict[str, Any],
    include: set[str],
    exclude: set[str],
    mode: str,
) -> str:
    projects = data.get("projects") or []
    if not projects:
        return ""
    out = ["## Projects", "", "----", "\n"]
    for p in projects:
        name = md_escape(str(p.get("name","")))
        dates = md_escape(str(p.get("dates","")))
        out.extend([f"**{name}** ({dates})".strip(),""])

        kept = []
        for b in p.get("bullets") or []:
            text = md_escape(str(b.get("text","")))
            tags = norm_tags(b.get("tags"))
            if text and bullet_included(tags, include, exclude, mode):
                kept.append(text)

        if kept:
            for t in kept:
                out.append(f"- {t}")
        else:
            out.append("- (No bullets matched selected tags.)")
        out.append("")
    return "\n".join(out)


def render_education(data: dict[str, Any]) -> str:
    edu = data.get("education") or []
    if not edu:
        return ""
    out = ["## Education", "", "----", "\n"]
    for e in edu:
        school = md_escape(str(e.get("school","")))
        detail = md_escape(str(e.get("detail","")))
        year = md_escape(str(e.get("year","")))
        bits = [b for b in [school, detail, year] if b]
        out.append("- " + ", ".join(bits))
    out.append("")
    return "\n".join(out)


def build_md(data: dict[str, Any], include: set[str], exclude: set[str], mode: str) -> str:
    parts = [
        render_header(data),
        render_summary(data),
        render_skills(data),
        render_experience(data, include, exclude, mode),
        render_projects(data, include, exclude, mode),
        render_education(data),
    ]
    return "\n".join([p for p in parts if p]).strip() + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a Markdown resume from YAML with tagged bullets.")
    ap.add_argument("--in", dest="inp", required=True, help="Input YAML file (e.g., resume.yaml)")
    ap.add_argument("--out", dest="out", required=True, help="Output Markdown file (e.g., resume.java.md)")
    ap.add_argument("--include", default="", help="Comma-separated tags to include (e.g., java,devops)")
    ap.add_argument("--exclude", default="", help="Comma-separated tags to exclude")
    ap.add_argument("--mode", choices=["any", "all"], default="any",
                    help="Tag match mode when include is provided (any=OR, all=AND)")

    args = ap.parse_args()

    include = {t.strip().lower() for t in args.include.split(",") if t.strip()}
    exclude = {t.strip().lower() for t in args.exclude.split(",") if t.strip()}

    data = load_yaml(Path(args.inp))
    md = build_md(data, include, exclude, args.mode)
    Path(args.out).write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
