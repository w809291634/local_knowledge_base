# -*- coding: utf-8 -*-
"""Strict, generic template-inheritance document builder.

The builder intentionally does not invent facts. All project values arrive in
the supplied facts/config file; templates remain read-only.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx_ops import (apply_substitutions, convert_doc_to_docx, ensure_cover_page_break,
                      fill_table, open_template, paragraph_text, set_paragraph,
                      insert_paragraphs_after, trim_cover_spacers)
from release_ops import (apply_xml_substitutions, find_phrase_parts, iter_document_paragraphs,
                         load_structured, now_iso, package_text, sha256_file, write_manifest)


def fail(message: str):
    raise RuntimeError(message)


def normalize_files(files: dict) -> dict[str, dict]:
    result = {}
    for key, value in files.items():
        if isinstance(value, list) and len(value) == 2:
            result[key] = {"template": value[0], "output": value[1], "scope": "default"}
        elif isinstance(value, dict) and "template" in value and "output" in value:
            result[key] = dict(value)
            result[key].setdefault("scope", "default")
        else:
            fail(f"files.{key} must be [template, output] or a mapping with template/output.")
    return result


def open_template_readonly(template: Path, temp_dir: Path):
    if template.suffix.lower() == ".docx":
        return open_template(str(template)), template
    if template.suffix.lower() != ".doc":
        fail(f"Unsupported template extension: {template}")
    converted = temp_dir / (template.stem + ".docx")
    convert_doc_to_docx(str(template), str(converted))
    return open_template(str(converted)), converted


def replace_mapped_paragraphs(doc, mapping, substitutions):
    """Apply exact paragraph mappings to body/table paragraphs; all must match."""
    used: set[int] = set()
    for paragraph in iter_document_paragraphs(doc, include_headers=False, include_footers=False):
        text = paragraph_text(paragraph)
        if not text.strip():
            continue
        for index, item in enumerate(mapping):
            if index in used:
                continue
            match, label, replacement = item[0], item[1], item[2]
            extras = item[3] if len(item) > 3 else []
            if match in text:
                set_paragraph(paragraph, replacement, label)
                if extras:
                    insert_paragraphs_after(paragraph, extras)
                used.add(index)
                break
    missing = [str(item[0]) for index, item in enumerate(mapping) if index not in used]
    if missing:
        fail("Paragraph slot(s) not found: " + "; ".join(missing))
    for paragraph in iter_document_paragraphs(doc):
        apply_substitutions(paragraph, substitutions)


def apply_table_mappings(doc, mappings):
    for item in mappings:
        index, header_rows, rows = item[0], item[1], item[2]
        if index < 0 or index >= len(doc.tables):
            fail(f"Configured table index {index} does not exist; document has {len(doc.tables)} tables.")
        header_texts = item[3] if len(item) > 3 else None
        row0 = item[4] if len(item) > 4 else None
        fill_table(doc, index, header_rows, rows, header_texts, row0)


def build_one(key, spec, cfg, temp_dir: Path, force: bool):
    template = Path(cfg["tpl_dir"]) / spec["template"]
    if not template.exists():
        fail(f"Template not found: {template}")
    output = Path(cfg["out_dir"]) / spec["output"]
    if output.resolve() == template.resolve():
        fail(f"Output cannot overwrite template: {template}")
    if output.exists() and not force:
        fail(f"Output exists; use a new version directory or --force: {output}")
    doc, effective_template = open_template_readonly(template, temp_dir)
    substitutions = [tuple(value) for value in cfg.get("global_subs", [])]
    mapping = cfg.get("paras", {}).get(key, [])
    replace_mapped_paragraphs(doc, mapping, substitutions)
    apply_table_mappings(doc, cfg.get("tables", {}).get(key, []))
    trim_cover_spacers(doc, cfg.get("cover_first_cell", "文件编号"))
    ensure_cover_page_break(doc, cfg.get("cover_first_cell", "文件编号"))
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output))

    # python-docx cannot reliably enumerate inherited header/footer parts and
    # floating text boxes.  The registered global replacements are therefore
    # repeated on all Word XML parts after save; this closes those blind spots
    # while preserving the paragraph-level replacement path for normal text.
    xml_slots = [tuple(value) for value in cfg.get("xml_subs", {}).get(key, [])]
    xml_replacements = substitutions + xml_slots
    xml_counts = apply_xml_substitutions(output, xml_replacements) if xml_replacements else {}
    strict = cfg.get("strict", {})
    required = list(strict.get("required_text", {}).get(key, []))
    required += list(spec.get("required_text", []))
    forbidden = list(strict.get("forbidden_text", []))
    forbidden += list(spec.get("forbidden_text", []))
    figures = cfg.get("figures", {}).get(key, [])
    required += [item["caption"] for item in figures if item.get("caption")]
    full_text, _ = package_text(output)
    missing = [phrase for phrase in required if phrase not in full_text]
    bad = find_phrase_parts(output, forbidden)
    if missing:
        fail(f"Required text missing in {output.name}: " + "; ".join(missing))
    if bad:
        fail(f"Forbidden residual text in {output.name}: " + "; ".join(bad))
    return {
        "key": key,
        "scope": spec.get("scope", "default"),
        "template": str(template),
        "effective_template": str(effective_template),
        "template_sha256": sha256_file(effective_template),
        "output": str(output),
        "output_sha256": sha256_file(output),
        "xml_slot_counts": xml_counts,
        "required_text": required,
        "forbidden_text": forbidden,
        "figures": figures,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="JSON/YAML project configuration")
    parser.add_argument("--only", action="append", help="document key; repeatable")
    parser.add_argument("--force", action="store_true", help="allow overwriting outputs in the selected new version directory")
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    cfg = load_structured(config_path)
    if not isinstance(cfg.get("files"), dict) or not cfg.get("files"):
        fail("config.files must be a non-empty mapping")
    if not cfg.get("tpl_dir") or not cfg.get("out_dir"):
        fail("config.tpl_dir and config.out_dir are required")
    cfg["tpl_dir"] = str((config_path.parent / cfg["tpl_dir"]).resolve()) if not Path(cfg["tpl_dir"]).is_absolute() else cfg["tpl_dir"]
    cfg["out_dir"] = str((config_path.parent / cfg["out_dir"]).resolve()) if not Path(cfg["out_dir"]).is_absolute() else cfg["out_dir"]
    if Path(cfg["tpl_dir"]).resolve() == Path(cfg["out_dir"]).resolve():
        fail("tpl_dir and out_dir must be different")
    specs = normalize_files(cfg["files"])
    keys = args.only or list(specs)
    unknown = [key for key in keys if key not in specs]
    if unknown:
        fail("Unknown document key(s): " + ", ".join(unknown))
    facts_file = cfg.get("facts_file")
    facts_path = (config_path.parent / facts_file).resolve() if facts_file and not Path(facts_file).is_absolute() else (Path(facts_file) if facts_file else None)
    if facts_path and not facts_path.exists():
        fail(f"facts_file not found: {facts_path}")
    with tempfile.TemporaryDirectory(prefix="pems_doc_convert_") as temp:
        results = [build_one(key, specs[key], cfg, Path(temp), args.force) for key in keys]
    manifest = {
        "generated_at_utc": now_iso(),
        "tool": "build_docs.py",
        "config": str(config_path),
        "config_sha256": sha256_file(config_path),
        "facts_file": str(facts_path) if facts_path else None,
        "facts_sha256": sha256_file(facts_path) if facts_path else None,
        "documents": results,
    }
    manifest_path = Path(cfg["out_dir"]) / "manifest.json"
    write_manifest(manifest_path, manifest)
    print(json.dumps({"status": "ok", "manifest": str(manifest_path), "documents": [r["output"] for r in results]}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
