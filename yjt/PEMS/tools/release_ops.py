# -*- coding: utf-8 -*-
"""Generic release helpers for template-based PEMS document generation."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from docx import Document


WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_structured(path: str | Path) -> dict:
    path = Path(path)
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("YAML requires PyYAML; install it or use JSON.") from exc
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Structured facts/config root must be a mapping.")
        return value
    raise ValueError(f"Unsupported config format: {path.suffix}")


def iter_container_paragraphs(container, seen: set[int]):
    """Yield paragraphs in a python-docx container and nested table cells once."""
    for paragraph in container.paragraphs:
        key = id(paragraph._p)
        if key not in seen:
            seen.add(key)
            yield paragraph
    for table in container.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from iter_container_paragraphs(cell, seen)


def iter_document_paragraphs(doc: Document, include_headers=True, include_footers=True):
    """Yield body/table/header/footer paragraphs without duplicated linked parts."""
    seen: set[int] = set()
    yield from iter_container_paragraphs(doc, seen)
    parts_seen: set[str] = set()
    for section in doc.sections:
        candidates = []
        if include_headers:
            candidates.extend([section.header, section.first_page_header, section.even_page_header])
        if include_footers:
            candidates.extend([section.footer, section.first_page_footer, section.even_page_footer])
        for container in candidates:
            partname = str(container.part.partname)
            if partname in parts_seen:
                continue
            parts_seen.add(partname)
            yield from iter_container_paragraphs(container, seen)


def package_text(path: str | Path) -> tuple[str, dict[str, str]]:
    """Extract visible OOXML text from body/header/footer/textbox XML parts."""
    parts: dict[str, str] = {}
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not (name.startswith("word/") and name.endswith(".xml")):
                continue
            try:
                root = ET.fromstring(archive.read(name))
            except ET.ParseError:
                continue
            strings = []
            for element in root.iter():
                if element.tag in {WORD_NS + "t", WORD_NS + "instrText"} and element.text:
                    strings.append(element.text)
            if strings:
                parts[name] = "".join(strings)
    return "\n".join(parts.values()), parts


def find_phrase_parts(path: str | Path, phrases: Iterable[str]) -> dict[str, list[str]]:
    _, parts = package_text(path)
    result: dict[str, list[str]] = {}
    for phrase in phrases:
        hits = [name for name, text in parts.items() if phrase and phrase in text]
        if hits:
            result[phrase] = hits
    return result


def write_manifest(path: str | Path, manifest: dict) -> None:
    path = Path(path)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def apply_xml_substitutions(path: str | Path, substitutions: list[tuple[str, str]]) -> dict[str, int]:
    """Apply explicit raw XML replacements and report counts.

    Intended only for registered text-box/header slots. Each old phrase must be
    contiguous XML text; otherwise generation must fail and the project needs a
    dedicated safe slot handler.
    """
    path = Path(path)
    counts = {old: 0 for old, _ in substitutions}
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".docx", delete=False) as handle:
        temp = Path(handle.name)
    try:
        with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as target:
            for info in source.infolist():
                data = source.read(info.filename)
                if info.filename.startswith("word/") and info.filename.endswith(".xml"):
                    text = data.decode("utf-8")
                    for old, new in substitutions:
                        hit = text.count(old)
                        if hit:
                            counts[old] += hit
                            text = text.replace(old, new)
                    data = text.encode("utf-8")
                target.writestr(info, data)
        missing = [old for old, count in counts.items() if count == 0]
        if missing:
            raise RuntimeError("XML slot text not found: " + ", ".join(missing))
        os.replace(temp, path)
        return counts
    finally:
        if temp.exists():
            temp.unlink()
