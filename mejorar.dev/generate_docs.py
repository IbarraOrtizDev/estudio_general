#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Documentación Técnica Profesional para mejorar.dev (Markdown a HTML)
Convierte todos los archivos Markdown de mejorar.dev en un sitio web
estático navegable, responsive y basado en Bootstrap 5 + Pygments + Mermaid.js dentro de `dist_html`.
Soporta `python-markdown` si está disponible o incluye un motor Markdown completo en Python puro.
"""

import html
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path

EXTRA_SITE_PACKAGES = [
    r"C:\Users\PC\AppData\Local\Python\pythoncore-3.15-64\Lib\site-packages",
    r"C:\Program Files\Microsoft SDKs\Azure\CLI2\Lib\site-packages",
]
for sp in EXTRA_SITE_PACKAGES:
    if os.path.isdir(sp) and sp not in sys.path:
        sys.path.append(sp)

try:
    import pygments
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name, TextLexer
except ImportError:
    az_py = r"C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe"
    if os.path.isfile(az_py) and os.path.normcase(sys.executable) != os.path.normcase(az_py):
        import subprocess
        sys.exit(subprocess.call([az_py, "-B", __file__, *sys.argv[1:]]))
    raise

HAS_MARKDOWN = False
try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent
DIST_DIR = ROOT_DIR / "dist_html"
EXCLUDED_DIRS = {"dist_html", ".git", ".venv", "__pycache__", "node_modules"}

FOLDER_LABELS = {
    ".": "Inicio / Raíz",
    "modulo-01-patrones-diseno": "01 · Patrones de Diseño",
    "modulo-02-arquitectura": "02 · Arquitectura",
    "modulo-07-redes": "07 · Redes (Networking)",
    "modulo-03-observabilidad": "03 · Observabilidad",
    "modulo-04-gobernabilidad": "04 · Gobernabilidad",
    "modulo-05-cicd-azure-devops": "05 · CI/CD Azure DevOps",
    "modulo-06-microsoft-entra": "06 · Microsoft Entra",
    "proyecto-integrador": "Proyecto Integrador",
}

FOLDER_ORDER = [
    ".",
    "modulo-01-patrones-diseno",
    "modulo-02-arquitectura",
    "modulo-07-redes",
    "modulo-03-observabilidad",
    "modulo-04-gobernabilidad",
    "modulo-05-cicd-azure-devops",
    "modulo-06-microsoft-entra",
    "proyecto-integrador",
]


def slugify_heading(value: str, separator: str = "-") -> str:
    """Genera IDs consistentes y limpios para encabezados y anclajes."""
    clean_val = re.sub(r"<[^>]+>", "", value)
    normalized = unicodedata.normalize("NFKD", clean_val)
    ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^\w\s-]", "", ascii_str).strip().lower()
    slug = re.sub(r"[-\s]+", separator, cleaned).strip(separator)
    return slug or "section"


def discover_files(root: Path):
    """Descubre todos los archivos Markdown y otros recursos del proyecto."""
    md_files = []
    other_files = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIRS)
        rel_dir = Path(dirpath).relative_to(root)

        for fname in sorted(filenames):
            if fname == "generate_docs.py":
                continue
            rel_path = rel_dir / fname if str(rel_dir) != "." else Path(fname)
            if fname.lower().endswith(".md"):
                md_files.append(rel_path)
            else:
                other_files.append(rel_path)

    def sort_key(p: Path):
        parts = p.parts
        folder = "." if len(parts) == 1 else parts[0]
        folder_rank = FOLDER_ORDER.index(folder) if folder in FOLDER_ORDER else 99
        if len(parts) == 1:
            if parts[0].lower() == "readme.md":
                return (0, 0, parts[0])
            return (0, 1, parts[0].lower())
        return (1, folder_rank, str(p).lower())

    md_files.sort(key=sort_key)
    return md_files, other_files


def extract_title(md_text: str, rel_path: Path) -> str:
    """Extrae el título principal (H1) del archivo Markdown o genera uno legible."""
    in_code = False
    lines = md_text.splitlines()
    start_idx = 0

    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start_idx = i + 1
                break

    for line in lines[start_idx:]:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^#\s+(.+)$", stripped)
        if m:
            title = re.sub(r"`([^`]+)`", r"\1", m.group(1)).strip()
            return title

    return rel_path.stem


def highlight_code_block(code: str, lang: str) -> str:
    """Resalta un bloque de código usando Pygments."""
    lang_clean = (lang or "").strip().lower()
    alias_map = {
        "csharp": "csharp",
        "cs": "csharp",
        "c#": "csharp",
        "bicep": "terraform",
        "http": "http",
        "jsonc": "json",
        "promql": "text",
        "kql": "sql",
        "dockerfile": "docker",
    }
    lexer_name = alias_map.get(lang_clean, lang_clean)
    try:
        lexer = get_lexer_by_name(lexer_name, stripall=False) if lexer_name else TextLexer()
    except Exception:
        lexer = TextLexer()
    formatter = HtmlFormatter(cssclass="codehilite", wrapcode=True)
    return pygments.highlight(code, lexer, formatter)


def render_inline_md(text: str) -> str:
    """Procesa formato inline de Markdown: código, enlaces, negritas, cursivas."""
    code_spans = []

    def save_code(m):
        idx = len(code_spans)
        code_spans.append(f"<code>{html.escape(m.group(1))}</code>")
        return f"\x00CODE{idx}\x00"

    text = re.sub(r"`([^`]+)`", save_code, text)
    text = html.escape(text, quote=False)

    # Enlaces [texto](url)
    def repl_link(m):
        label = m.group(1)
        url = html.unescape(m.group(2).strip())
        return f'<a href="{html.escape(url, quote=True)}">{label}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl_link, text)

    # Autolinks <https://...> o URLs sueltas
    text = re.sub(
        r"&lt;(https?://[^&\s]+)&gt;",
        lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>',
        text,
    )

    # Negrita + cursiva, Negrita, Cursiva, Tachado
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)

    for idx, span_html in enumerate(code_spans):
        text = text.replace(f"\x00CODE{idx}\x00", span_html)

    return text


def convert_markdown_fallback(md_text: str) -> tuple[str, str]:
    """
    Motor de conversión Markdown a HTML en Python puro con soporte para:
    - Encabezados H1..H6 con IDs únicos y generación de TOC
    - Bloques de código cercados con resaltado Pygments
    - Tablas GFM
    - Blockquotes
    - Listas ordenadas, desordenadas, anidadas y checklists
    - Reglas horizontales y párrafos
    """
    lines = md_text.splitlines()
    html_out = []
    toc_items = []
    used_ids = set()

    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Placeholder de Mermaid
        if stripped.startswith('<div data-mermaid-id="') and stripped.endswith("</div>"):
            html_out.append(stripped)
            i += 1
            continue

        # Bloque de código ```
        fence_m = re.match(r"^(\s*)(`{3,}|~{3,})(.*)$", line)
        if fence_m:
            marker = fence_m.group(2)[0] * len(fence_m.group(2))
            lang = fence_m.group(3).strip()
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith(marker):
                code_lines.append(lines[i])
                i += 1
            i += 1  # saltar cierre
            html_out.append(highlight_code_block("\n".join(code_lines), lang))
            continue

        # Regla horizontal
        if re.match(r"^(\*{3,}|-{3,}|_{3,})$", stripped):
            html_out.append("<hr>")
            i += 1
            continue

        # Encabezados # .. ######
        h_m = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if h_m:
            level = len(h_m.group(1))
            raw_title = h_m.group(2).strip()
            inline_title = render_inline_md(raw_title)
            base_slug = slugify_heading(raw_title)
            slug = base_slug
            counter = 1
            while slug in used_ids:
                slug = f"{base_slug}_{counter}"
                counter += 1
            used_ids.add(slug)
            html_out.append(f'<h{level} id="{slug}">{inline_title}</h{level}>')
            if level in (2, 3):
                clean_toc_label = re.sub(r"<[^>]+>", "", inline_title)
                toc_items.append((level, slug, clean_toc_label))
            i += 1
            continue

        # Tablas GFM
        if "|" in stripped and i + 1 < n and re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1]):
            def split_row(r_str):
                s = r_str.strip()
                if s.startswith("|"):
                    s = s[1:]
                if s.endswith("|"):
                    s = s[:-1]
                # No dividir por \| escapado ni dentro de `...`
                cells = []
                cur = []
                in_tick = False
                for ch in s:
                    if ch == "`":
                        in_tick = not in_tick
                        cur.append(ch)
                    elif ch == "|" and not in_tick:
                        cells.append("".join(cur).strip())
                        cur = []
                    else:
                        cur.append(ch)
                cells.append("".join(cur).strip())
                return cells

            headers = split_row(lines[i])
            i += 2  # saltar encabezado y separador
            rows = []
            while i < n and "|" in lines[i].strip() and lines[i].strip():
                rows.append(split_row(lines[i]))
                i += 1

            tbl = ["<table>", "<thead><tr>"]
            for h_cell in headers:
                tbl.append(f"<th>{render_inline_md(h_cell)}</th>")
            tbl.append("</tr></thead><tbody>")
            for r_cells in rows:
                tbl.append("<tr>")
                for c_idx in range(len(headers)):
                    val = r_cells[c_idx] if c_idx < len(r_cells) else ""
                    tbl.append(f"<td>{render_inline_md(val)}</td>")
                tbl.append("</tr>")
            tbl.append("</tbody></table>")
            html_out.append("".join(tbl))
            continue

        # Blockquote >
        if stripped.startswith(">"):
            bq_lines = []
            while i < n and (lines[i].strip().startswith(">") or (lines[i].strip() and bq_lines)):
                if not lines[i].strip().startswith(">"):
                    break
                content_part = re.sub(r"^\s*>\s?", "", lines[i])
                bq_lines.append(content_part)
                i += 1
            inner_html, _ = convert_markdown_fallback("\n".join(bq_lines))
            html_out.append(f"<blockquote>{inner_html}</blockquote>")
            continue

        # Listas (ordenadas y desordenadas)
        list_m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", line)
        if list_m:
            list_lines = []
            while i < n:
                cur_line = lines[i]
                cur_str = cur_line.strip()
                if not cur_str:
                    # Mirar si la siguiente línea continúa la lista
                    if i + 1 < n and re.match(r"^(\s*)([-*+]|\d+\.)\s+", lines[i + 1]):
                        i += 1
                        continue
                    break
                if re.match(r"^(\s*)([-*+]|\d+\.)\s+", cur_line) or cur_line.startswith("  "):
                    list_lines.append(cur_line)
                    i += 1
                else:
                    break

            def render_list_group(items_lines):
                if not items_lines:
                    return ""
                first_m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", items_lines[0])
                is_ol = bool(first_m and first_m.group(2).endswith("."))
                tag = "ol" if is_ol else "ul"
                base_indent = len(first_m.group(1)) if first_m else 0
                out = [f"<{tag}>"]
                idx_l = 0
                while idx_l < len(items_lines):
                    lm = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", items_lines[idx_l])
                    if not lm:
                        idx_l += 1
                        continue
                    item_text = lm.group(3)
                    idx_l += 1
                    sub_lines = []
                    while idx_l < len(items_lines):
                        nxt_m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", items_lines[idx_l])
                        if nxt_m:
                            if len(nxt_m.group(1)) > base_indent:
                                sub_lines.append(items_lines[idx_l])
                                idx_l += 1
                            else:
                                break
                        else:
                            sub_lines.append(items_lines[idx_l])
                            idx_l += 1
                    sub_html = render_list_group(sub_lines) if sub_lines else ""
                    out.append(f"<li>{render_inline_md(item_text)}{sub_html}</li>")
                out.append(f"</{tag}>")
                return "".join(out)

            html_out.append(render_list_group(list_lines))
            continue

        # Párrafo normal
        para_lines = []
        while i < n:
            cur_l = lines[i]
            cur_s = cur_l.strip()
            if (
                not cur_s
                or cur_s.startswith(("#", ">", "```", "~~~", '<div data-mermaid-id="'))
                or re.match(r"^(\*{3,}|-{3,}|_{3,})$", cur_s)
                or re.match(r"^(\s*)([-*+]|\d+\.)\s+", cur_l)
                or ("|" in cur_s and i + 1 < n and re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1]))
            ):
                break
            para_lines.append(cur_s)
            i += 1
        if para_lines:
            html_out.append(f"<p>{render_inline_md(' '.join(para_lines))}</p>")
        else:
            i += 1

    # Construir TOC HTML
    toc_html = ""
    if toc_items:
        toc_parts = ['<div class="toc"><ul>']
        for lvl, slug, label in toc_items:
            indent_cls = ' class="ms-3"' if lvl == 3 else ""
            toc_parts.append(f'<li{indent_cls}><a href="#{slug}">{html.escape(label)}</a></li>')
        toc_parts.append("</ul></div>")
        toc_html = "".join(toc_parts)

    return "\n".join(html_out), toc_html


def preprocess_markdown(md_text: str) -> tuple[str, dict[str, str]]:
    """Extrae bloques ```mermaid``` en placeholders y normaliza listas."""
    lines = md_text.splitlines()
    out_lines = []
    idx = 0
    mermaid_blocks: dict[str, str] = {}

    if lines and lines[0].strip() == "---":
        end_fm = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_fm = i
                break
        if end_fm is not None:
            fm_content = lines[1:end_fm]
            out_lines.append("> **Metadatos Frontmatter (YAML)**")
            out_lines.append("")
            out_lines.append("```yaml")
            out_lines.extend(fm_content)
            out_lines.append("```")
            out_lines.append("")
            idx = end_fm + 1

    in_code = False
    in_mermaid = False
    mermaid_lines: list[str] = []
    code_fence_marker = ""

    for i in range(idx, len(lines)):
        line = lines[i]
        stripped = line.strip()

        fence_match = re.match(r"^(\s*)(`{3,}|~{3,})(.*)$", line)
        if fence_match:
            marker = fence_match.group(2)
            lang = fence_match.group(3).strip().lower()
            if not in_code and not in_mermaid:
                if lang == "mermaid":
                    in_mermaid = True
                    mermaid_lines = []
                    code_fence_marker = marker[0] * len(marker)
                    continue
                else:
                    in_code = True
                    code_fence_marker = marker[0] * len(marker)
                    out_lines.append(line)
                    continue
            elif in_mermaid and stripped.startswith(code_fence_marker):
                in_mermaid = False
                code_fence_marker = ""
                key = f"MERMAID_PLACEHOLDER_{len(mermaid_blocks)}"
                mermaid_blocks[key] = "\n".join(mermaid_lines)
                out_lines.append("")
                out_lines.append(f'<div data-mermaid-id="{key}"></div>')
                out_lines.append("")
                continue
            elif in_code and stripped.startswith(code_fence_marker):
                in_code = False
                code_fence_marker = ""
                out_lines.append(line)
                continue

        if in_mermaid:
            mermaid_lines.append(line)
            continue

        out_lines.append(line)

    return "\n".join(out_lines), mermaid_blocks


def postprocess_html(
    html_content: str,
    current_md_rel: Path,
    all_heading_ids: dict,
    mermaid_blocks: dict[str, str],
) -> tuple[str, int, int]:
    """Reemplaza .md por .html, estiliza tablas/citas/checklists y embebe diagramas Mermaid."""
    md_links_fixed = 0
    anchors_fixed = 0

    local_ids = set(re.findall(r'\bid="([^"]+)"', html_content))
    all_heading_ids[str(current_md_rel).replace("\\", "/")] = local_ids

    def fix_href(match):
        nonlocal md_links_fixed, anchors_fixed
        prefix, href, suffix = match.group(1), match.group(2).strip(), match.group(3)

        if href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:", "data:")):
            return f'{prefix}{href}{suffix} target="_blank" rel="noopener noreferrer"'

        if "#" in href:
            path_part, frag_part = href.split("#", 1)
            has_frag = True
        else:
            path_part, frag_part = href, ""
            has_frag = False

        if path_part.lower().endswith(".md"):
            path_part = path_part[:-3] + ".html"
            md_links_fixed += 1

        if has_frag and frag_part:
            if not path_part:
                if frag_part not in local_ids:
                    candidate = slugify_heading(frag_part, "-")
                    if candidate in local_ids:
                        frag_part = candidate
                        anchors_fixed += 1
                    else:
                        matched = next(
                            (lid for lid in local_ids if candidate in lid or lid in candidate),
                            candidate,
                        )
                        if matched != frag_part:
                            frag_part = matched
                            anchors_fixed += 1
            else:
                candidate = slugify_heading(frag_part, "-")
                if candidate != frag_part:
                    frag_part = candidate
                    anchors_fixed += 1

        new_href = f"{path_part}#{frag_part}" if has_frag else path_part
        return f"{prefix}{new_href}{suffix}"

    html_content = re.sub(r'(<a\s+[^>]*?href=")([^"]+)(")', fix_href, html_content)

    html_content = re.sub(
        r"<table>",
        '<div class="table-responsive shadow-sm rounded-3 my-4"><table class="table table-hover table-striped table-bordered align-middle mb-0">',
        html_content,
    )
    html_content = re.sub(r"</table>", "</table></div>", html_content)

    html_content = re.sub(
        r"<blockquote>",
        '<blockquote class="blockquote doc-blockquote shadow-sm my-3">',
        html_content,
    )

    html_content = re.sub(
        r"<li>\s*\[\s\]\s*",
        '<li class="task-list-item"><input type="checkbox" class="form-check-input me-2" disabled aria-label="Pendiente">',
        html_content,
    )
    html_content = re.sub(
        r"<li>\s*\[[xX]\]\s*",
        '<li class="task-list-item"><input type="checkbox" class="form-check-input me-2" checked disabled aria-label="Completado">',
        html_content,
    )

    for key, code in mermaid_blocks.items():
        escaped_code = html.escape(code)
        mermaid_html = (
            '<div class="diagram-wrapper shadow-sm rounded-3 my-4">'
            '<div class="diagram-header d-flex align-items-center justify-content-between px-3 py-2 border-bottom">'
            '<span class="d-flex align-items-center gap-2">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="#38bdf8" viewBox="0 0 16 16" aria-hidden="true">'
            '<path fill-rule="evenodd" d="M6 3.5A1.5 1.5 0 0 1 7.5 2h1A1.5 1.5 0 0 1 10 3.5v1A1.5 1.5 0 0 1 8.5 6v1H14a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0v-1A.5.5 0 0 1 2 7h5.5V6A1.5 1.5 0 0 1 6 4.5v-1z"/>'
            '<path d="M1 11.5A1.5 1.5 0 0 1 2.5 10h1A1.5 1.5 0 0 1 5 11.5v1A1.5 1.5 0 0 1 3.5 14h-1A1.5 1.5 0 0 1 1 12.5v-1zm5 0A1.5 1.5 0 0 1 7.5 10h1a1.5 1.5 0 0 1 1.5 1.5v1A1.5 1.5 0 0 1 8.5 14h-1A1.5 1.5 0 0 1 6 12.5v-1zm5 0a1.5 1.5 0 0 1 1.5-1.5h1a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5v-1z"/>'
            '</svg>'
            '<span class="small fw-semibold text-uppercase">Diagrama de Arquitectura / Flujo</span>'
            '</span>'
            '<span class="badge bg-info-subtle text-info-emphasis border border-info-subtle" style="font-size:0.68rem;">Mermaid SVG</span>'
            '</div>'
            f'<div class="diagram-svg-body"><pre class="mermaid mb-0">{escaped_code}</pre></div>'
            '</div>'
        )
        html_content = html_content.replace(f'<div data-mermaid-id="{key}"></div>', mermaid_html)

    return html_content, md_links_fixed, anchors_fixed


def build_sidebar_html(current_html_rel: Path, grouped_docs: dict) -> str:
    """Construye el menú lateral (Sidebar) agrupando los archivos por carpeta."""
    current_dir = current_html_rel.parent
    sidebar_parts = []

    for group_idx, (folder_key, items) in enumerate(grouped_docs.items()):
        folder_label = FOLDER_LABELS.get(folder_key, folder_key)
        collapse_id = f"submenu-{slugify_heading(folder_key)}-{group_idx}"

        is_group_active = any(item["html_rel"] == current_html_rel for item in items)
        expanded_attr = "true"
        show_class = "show"

        sidebar_parts.append('<div class="sidebar-group mb-2">')
        sidebar_parts.append(
            f'<button class="btn btn-toggle d-flex align-items-center justify-content-between w-100 px-3 py-2 text-start fw-semibold {"group-active" if is_group_active else ""}" '
            f'type="button" data-bs-toggle="collapse" data-bs-target="#{collapse_id}" '
            f'aria-expanded="{expanded_attr}" aria-controls="{collapse_id}">'
            f'<span class="d-flex align-items-center gap-2">'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16" aria-hidden="true">'
            f'<path d="M.54 3.87.5 3a2 2 0 0 1 2-2h3.672a2 2 0 0 1 1.414.586l.828.828A2 2 0 0 0 9.828 3h3.982a2 2 0 0 1 1.992 2.181l-.637 7A2 2 0 0 1 13.174 14H2.826a2 2 0 0 1-1.991-1.819l-.637-7a1.99 1.99 0 0 1 .342-1.31zM2.19 4a1 1 0 0 0-.996 1.09l.637 7a1 1 0 0 0 .995.91h10.348a1 1 0 0 0 .995-.91l.637-7A1 1 0 0 0 13.81 4H2.19z"/>'
            f"</svg>"
            f"<span>{folder_label}</span>"
            f"</span>"
            f'<span class="badge rounded-pill bg-secondary-subtle text-secondary-emphasis">{len(items)}</span>'
            f"</button>"
        )
        sidebar_parts.append(f'<div class="collapse {show_class}" id="{collapse_id}">')
        sidebar_parts.append('<ul class="nav flex-column sidebar-submenu ps-2 py-1">')

        for item in items:
            target_rel = item["html_rel"]
            rel_href = os.path.relpath(target_rel, start=current_dir).replace("\\", "/")
            is_active = target_rel == current_html_rel
            active_class = " active" if is_active else ""
            aria_current = ' aria-current="page"' if is_active else ""

            display_label = html.escape(item["sidebar_label"])
            file_hint = html.escape(item["file_hint"])
            hint_html = (
                f'<small class="d-block text-muted text-truncate" style="font-size:0.72rem;">{file_hint}</small>'
                if file_hint
                else ""
            )

            sidebar_parts.append(
                f'<li class="nav-item">'
                f'<a class="nav-link sidebar-link{active_class} py-1 px-3 rounded-2" href="{rel_href}"{aria_current} title="{html.escape(target_rel.as_posix())}">'
                f'<span class="d-block text-truncate">{display_label}</span>'
                f"{hint_html}"
                f"</a>"
                f"</li>"
            )

        sidebar_parts.append("</ul>")
        sidebar_parts.append("</div>")
        sidebar_parts.append("</div>")

    return "\n".join(sidebar_parts)


def get_pygments_css() -> str:
    """Genera las reglas CSS de Pygments para el resaltado de sintaxis."""
    formatter = HtmlFormatter(style="friendly")
    return formatter.get_style_defs(".codehilite")


def render_page_template(
    title: str,
    body_html: str,
    toc_html: str,
    sidebar_html: str,
    current_html_rel: Path,
    pygments_css: str,
    prev_item: dict | None,
    next_item: dict | None,
) -> str:
    """Construye el documento HTML5 completo con diseño Bootstrap 5 y Mermaid.js."""
    current_dir = current_html_rel.parent
    root_readme_href = os.path.relpath(Path("README.html"), start=current_dir).replace("\\", "/")
    plan_href = os.path.relpath(Path("00-plan-de-estudio.html"), start=current_dir).replace("\\", "/")
    glosario_href = os.path.relpath(Path("01-glosario.html"), start=current_dir).replace("\\", "/")
    portal_href = os.path.relpath(ROOT_DIR.parent / "index.html", start=(DIST_DIR / current_dir)).replace("\\", "/")

    parts = current_html_rel.parts
    breadcrumb_items = [
        f'<li class="breadcrumb-item"><a href="{portal_href}" class="text-decoration-none">Portal</a></li>',
        f'<li class="breadcrumb-item"><a href="{root_readme_href}" class="text-decoration-none">mejorar.dev</a></li>',
    ]
    if len(parts) > 1:
        for p in parts[:-1]:
            breadcrumb_items.append(f'<li class="breadcrumb-item text-muted">{p}</li>')
    breadcrumb_items.append(
        f'<li class="breadcrumb-item active fw-semibold" aria-current="page">{parts[-1]}</li>'
    )
    breadcrumb_html = "\n".join(breadcrumb_items)

    pager_parts = []
    if prev_item:
        prev_href = os.path.relpath(prev_item["html_rel"], start=current_dir).replace("\\", "/")
        pager_parts.append(
            f'<a href="{prev_href}" class="btn btn-outline-primary btn-sm d-inline-flex align-items-center gap-2 shadow-sm">'
            f"<span>&larr; {html.escape(prev_item['sidebar_label'])}</span></a>"
        )
    else:
        pager_parts.append("<span></span>")

    if next_item:
        next_href = os.path.relpath(next_item["html_rel"], start=current_dir).replace("\\", "/")
        pager_parts.append(
            f'<a href="{next_href}" class="btn btn-outline-primary btn-sm d-inline-flex align-items-center gap-2 shadow-sm">'
            f"<span>{html.escape(next_item['sidebar_label'])} &rarr;</span></a>"
        )
    else:
        pager_parts.append("<span></span>")

    pager_html = "\n".join(pager_parts)
    safe_title = html.escape(title)

    has_toc = bool(toc_html and "<li>" in toc_html)
    toc_block = ""
    if has_toc:
        toc_block = f"""
        <div class="card border-0 shadow-sm mb-4 toc-card">
          <div class="card-body py-2 px-3">
            <button class="btn btn-sm btn-link text-decoration-none text-dark fw-semibold p-0 d-flex align-items-center gap-2 w-100 justify-content-between" type="button" data-bs-toggle="collapse" data-bs-target="#pageTocCollapse" aria-expanded="false" aria-controls="pageTocCollapse">
              <span class="d-flex align-items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="currentColor" viewBox="0 0 16 16" aria-hidden="true">
                  <path fill-rule="evenodd" d="M5 11.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm-3 1a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm0 4a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm0 4a1 1 0 1 0 0-2 1 1 0 0 0 0 2z"/>
                </svg>
                Contenido de esta página
              </span>
              <span class="small text-muted">Mostrar / Ocultar</span>
            </button>
            <div class="collapse mt-2" id="pageTocCollapse">
              {toc_html}
            </div>
          </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_title} — mejorar.dev (.NET &amp; Cloud Architecture)</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
  <style>
    :root {{
      --sidebar-width: 310px;
      --navbar-height: 58px;
      --brand-primary: #6366f1;
      --brand-dark: #0f172a;
      --bg-soft: #f8fafc;
    }}

    body {{
      font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background-color: var(--bg-soft);
      color: #1e293b;
      padding-top: var(--navbar-height);
      line-height: 1.65;
    }}

    .doc-navbar {{
      height: var(--navbar-height);
      background-color: var(--brand-dark);
      z-index: 1040;
    }}

    .doc-sidebar {{
      position: fixed;
      top: var(--navbar-height);
      left: 0;
      bottom: 0;
      width: var(--sidebar-width);
      overflow-y: auto;
      background-color: #ffffff;
      border-right: 1px solid #e2e8f0;
      z-index: 1030;
      transition: transform 0.25s ease, width 0.25s ease;
    }}

    body.sidebar-collapsed .doc-sidebar {{
      transform: translateX(-100%);
    }}

    .doc-main {{
      margin-left: var(--sidebar-width);
      transition: margin-left 0.25s ease;
      min-height: calc(100vh - var(--navbar-height));
    }}

    body.sidebar-collapsed .doc-main {{
      margin-left: 0;
    }}

    .btn-toggle {{
      color: #334155;
      background-color: #f1f5f9;
      border: none;
      border-radius: 0.375rem;
      font-size: 0.85rem;
    }}

    .btn-toggle:hover {{
      background-color: #e2e8f0;
      color: #0f172a;
    }}

    .btn-toggle.group-active {{
      background-color: #eef2ff;
      color: #4338ca;
    }}

    .sidebar-link {{
      color: #475569;
      font-size: 0.86rem;
      border-left: 3px solid transparent;
      transition: all 0.15s ease;
    }}

    .sidebar-link:hover {{
      color: var(--brand-primary);
      background-color: #f1f5f9;
    }}

    .sidebar-link.active {{
      color: #4f46e5 !important;
      background-color: #eef2ff !important;
      border-left-color: #4f46e5;
      font-weight: 600;
    }}

    .doc-content-card {{
      background-color: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 0.75rem;
    }}

    .doc-body h1 {{
      font-size: 2rem;
      font-weight: 700;
      color: #0f172a;
      border-bottom: 2px solid #e2e8f0;
      padding-bottom: 0.6rem;
      margin-bottom: 1.25rem;
    }}

    .doc-body h2 {{
      font-size: 1.45rem;
      font-weight: 600;
      color: #1e293b;
      margin-top: 2.2rem;
      margin-bottom: 1rem;
      padding-bottom: 0.35rem;
      border-bottom: 1px solid #f1f5f9;
      scroll-margin-top: 75px;
    }}

    .doc-body h3 {{
      font-size: 1.2rem;
      font-weight: 600;
      color: #334155;
      margin-top: 1.6rem;
      margin-bottom: 0.75rem;
      scroll-margin-top: 75px;
    }}

    .doc-body h4, .doc-body h5, .doc-body h6 {{
      font-weight: 600;
      color: #475569;
      margin-top: 1.25rem;
      scroll-margin-top: 75px;
    }}

    .doc-blockquote {{
      border-left: 4px solid #6366f1;
      background-color: #f8fafc;
      padding: 0.9rem 1.15rem;
      border-radius: 0 0.5rem 0.5rem 0;
      font-size: 0.95rem;
      color: #334155;
    }}

    .doc-blockquote p:last-child {{
      margin-bottom: 0;
    }}

    .codehilite {{
      background-color: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 0.5rem;
      padding: 0.9rem 1rem;
      margin: 1rem 0;
      overflow-x: auto;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }}

    .codehilite pre, pre {{
      margin: 0;
      font-family: 'Cascadia Mono', 'Consolas', 'SFMono-Regular', Menlo, Monaco, monospace;
      font-size: 0.875rem;
      line-height: 1.5;
    }}

    .diagram-wrapper {{
      background-color: #ffffff;
      border: 1px solid #cbd5e1;
      overflow: hidden;
    }}

    .diagram-header {{
      background-color: #0f172a;
      color: #e2e8f0;
      border-color: #334155 !important;
    }}

    .diagram-svg-body {{
      padding: 1.25rem 1rem;
      overflow-x: auto;
      text-align: center;
      background-color: #ffffff;
    }}

    code {{
      font-family: 'Cascadia Mono', 'Consolas', monospace;
      font-size: 0.875em;
      color: #0f172a;
      background-color: #f1f5f9;
      padding: 0.15em 0.38em;
      border-radius: 0.25rem;
    }}

    pre code {{
      background-color: transparent;
      padding: 0;
      color: inherit;
    }}

    .task-list-item {{
      list-style-type: none;
      margin-left: -1.25rem;
    }}

    .toc-card ul {{
      margin-bottom: 0;
      padding-left: 1.2rem;
      font-size: 0.88rem;
    }}

    .toc-card a {{
      text-decoration: none;
      color: #334155;
    }}

    .toc-card a:hover {{
      color: #4f46e5;
      text-decoration: underline;
    }}

    @media (max-width: 991.98px) {{
      .doc-sidebar {{
        position: relative;
        top: 0;
        width: 100%;
        max-height: 420px;
        border-right: none;
        border-bottom: 1px solid #cbd5e1;
        transform: none !important;
      }}

      body.sidebar-collapsed .doc-sidebar {{
        display: none;
      }}

      .doc-main {{
        margin-left: 0 !important;
        width: 100% !important;
      }}
    }}

    {pygments_css}
  </style>
</head>
<body>

  <nav class="navbar navbar-dark doc-navbar fixed-top shadow-sm px-3">
    <div class="container-fluid">
      <div class="d-flex align-items-center gap-2">
        <button class="btn btn-outline-light btn-sm d-flex align-items-center gap-1" id="sidebarToggle" type="button" title="Ocultar o mostrar barra lateral" aria-label="Alternar barra lateral">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16" aria-hidden="true">
            <path fill-rule="evenodd" d="M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5z"/>
          </svg>
          <span class="d-none d-sm-inline small">Menú</span>
        </button>
        <a class="navbar-brand fw-bold d-flex align-items-center gap-2 mb-0 ms-1" href="{root_readme_href}">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="#818cf8" viewBox="0 0 16 16" aria-hidden="true">
            <path d="M11.251.068a.5.5 0 0 1 .227.58L9.677 6.5H13a.5.5 0 0 1 .364.843l-8 8.5a.5.5 0 0 1-.842-.49L6.323 9.5H3a.5.5 0 0 1-.364-.843l8-8.5a.5.5 0 0 1 .615-.09z"/>
          </svg>
          <span>mejorar.dev · .NET &amp; Cloud</span>
        </a>
      </div>
      <div class="d-flex align-items-center gap-2">
        <a href="{portal_href}" class="btn btn-sm btn-outline-light d-none d-lg-inline-block">&larr; Portal</a>
        <a href="{plan_href}" class="btn btn-sm btn-outline-info d-none d-md-inline-block">Plan 27 semanas</a>
        <a href="{glosario_href}" class="btn btn-sm btn-outline-warning d-none d-md-inline-block">Glosario</a>
        <span class="badge bg-primary-subtle text-primary-emphasis border border-primary-subtle">{current_html_rel.as_posix()}</span>
      </div>
    </div>
  </nav>

  <aside class="doc-sidebar shadow-sm p-3" id="docSidebar" aria-label="Navegación de documentación">
    <div class="mb-3">
      <div class="input-group input-group-sm">
        <span class="input-group-text bg-light border-end-0">
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="currentColor" viewBox="0 0 16 16" aria-hidden="true">
            <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
          </svg>
        </span>
        <input type="search" id="sidebarFilter" class="form-control bg-light border-start-0" placeholder="Filtrar módulos..." aria-label="Filtrar módulos">
      </div>
    </div>
    <nav id="sidebarNav">
      {sidebar_html}
    </nav>
  </aside>

  <main class="doc-main p-3 p-md-4 p-lg-5">
    <div class="container-xxl">
      <nav aria-label="breadcrumb" class="mb-3">
        <ol class="breadcrumb bg-white px-3 py-2 rounded-3 shadow-sm border mb-0 small">
          {breadcrumb_html}
        </ol>
      </nav>

      {toc_block}

      <article class="doc-content-card shadow-sm p-4 p-md-5 doc-body">
        {body_html}
      </article>

      <div class="d-flex justify-content-between align-items-center mt-4 pt-3 border-top">
        {pager_html}
      </div>

      <footer class="text-center text-muted small mt-5 pt-3 border-top">
        mejorar.dev &middot; Plan de crecimiento para desarrolladores .NET &middot; Bootstrap 5 + Mermaid.js
      </footer>
    </div>
  </main>

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: true, theme: 'default', securityLevel: 'loose' }});
  </script>
  <script>
    document.addEventListener('DOMContentLoaded', function () {{
      const toggleBtn = document.getElementById('sidebarToggle');
      if (toggleBtn) {{
        toggleBtn.addEventListener('click', function () {{
          document.body.classList.toggle('sidebar-collapsed');
        }});
      }}

      const currentPath = decodeURIComponent(window.location.pathname).replace(/\\\\/g, '/').toLowerCase();
      const sidebarLinks = document.querySelectorAll('#sidebarNav a.sidebar-link');
      let matchedLink = null;

      sidebarLinks.forEach(function (link) {{
        try {{
          const resolved = new URL(link.getAttribute('href'), window.location.href);
          const linkPath = decodeURIComponent(resolved.pathname).replace(/\\\\/g, '/').toLowerCase();
          if (currentPath && linkPath === currentPath) {{
            matchedLink = link;
          }}
        }} catch (e) {{}}
      }});

      if (matchedLink) {{
        sidebarLinks.forEach(function (l) {{ l.classList.remove('active'); }});
        matchedLink.classList.add('active');
        matchedLink.setAttribute('aria-current', 'page');
        const parentCollapse = matchedLink.closest('.collapse');
        if (parentCollapse && !parentCollapse.classList.contains('show')) {{
          parentCollapse.classList.add('show');
        }}
        matchedLink.scrollIntoView({{ block: 'nearest' }});
      }} else {{
        const presetActive = document.querySelector('#sidebarNav a.sidebar-link.active');
        if (presetActive) {{
          presetActive.scrollIntoView({{ block: 'nearest' }});
        }}
      }}

      const filterInput = document.getElementById('sidebarFilter');
      if (filterInput) {{
        filterInput.addEventListener('input', function () {{
          const query = this.value.trim().toLowerCase();
          const groups = document.querySelectorAll('.sidebar-group');
          groups.forEach(function (group) {{
            const items = group.querySelectorAll('.nav-item');
            let visibleCount = 0;
            items.forEach(function (item) {{
              const text = item.textContent.toLowerCase();
              const match = !query || text.includes(query);
              item.style.display = match ? '' : 'none';
              if (match) visibleCount++;
            }});
            group.style.display = visibleCount > 0 ? '' : 'none';
            if (query && visibleCount > 0) {{
              const collapseEl = group.querySelector('.collapse');
              if (collapseEl) collapseEl.classList.add('show');
            }}
          }});
        }});
      }}
    }});
  </script>
</body>
</html>
"""


def validate_output(md_files: list[Path], other_files: list[Path], all_heading_ids: dict) -> dict:
    """Verifica que dist_html contiene todos los HTML esperados y sin enlaces rotos."""
    missing_html = []
    empty_html = []
    broken_links = []
    broken_anchors = []
    unconverted_md_hrefs = []

    for md_rel in md_files:
        html_rel = md_rel.with_suffix(".html")
        html_full = DIST_DIR / html_rel
        if not html_full.is_file():
            missing_html.append(str(html_rel))
            continue
        content = html_full.read_text(encoding="utf-8")
        if len(content.strip()) < 200:
            empty_html.append(str(html_rel))

        for m in re.finditer(r'<a\s+[^>]*?href="([^"]+)"', content):
            href = m.group(1).strip()
            if href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:", "data:")):
                continue
            if ".md" in href.split("#")[0].lower():
                unconverted_md_hrefs.append((str(html_rel), href))

            path_part, _, frag_part = href.partition("#")
            if path_part:
                target_path = (html_full.parent / path_part).resolve()
                if not target_path.exists():
                    broken_links.append((str(html_rel), href))
                elif frag_part and target_path.suffix.lower() == ".html":
                    try:
                        target_rel_key = str(target_path.relative_to(DIST_DIR.resolve()).with_suffix(".md")).replace("\\", "/")
                        target_ids = all_heading_ids.get(target_rel_key, set())
                        if target_ids and frag_part not in target_ids:
                            broken_anchors.append((str(html_rel), href))
                    except ValueError:
                        pass
            elif frag_part:
                local_key = str(md_rel).replace("\\", "/")
                local_ids = all_heading_ids.get(local_key, set())
                if frag_part not in local_ids:
                    broken_anchors.append((str(html_rel), f"#{frag_part}"))

    missing_assets = []
    for asset_rel in other_files:
        if not (DIST_DIR / asset_rel).exists():
            missing_assets.append(str(asset_rel))

    return {
        "expected_html": len(md_files),
        "found_html": len(md_files) - len(missing_html),
        "missing_html": missing_html,
        "empty_html": empty_html,
        "missing_assets": missing_assets,
        "unconverted_md_hrefs": unconverted_md_hrefs,
        "broken_links": broken_links,
        "broken_anchors": broken_anchors,
    }


def main():
    print("=" * 72)
    print(" GENERADOR DE DOCUMENTACIÓN MEJORAR.DEV (MARKDOWN -> HTML BOOTSTRAP 5)")
    print("=" * 72)

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    md_files, other_files = discover_files(ROOT_DIR)
    print(f"[*] Archivos Markdown detectados : {len(md_files)}")
    print(f"[*] Archivos auxiliares          : {len(other_files)}")

    for asset_rel in other_files:
        src = ROOT_DIR / asset_rel
        dst = DIST_DIR / asset_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    docs_info = []
    grouped_docs = {}

    for md_rel in md_files:
        raw_text = (ROOT_DIR / md_rel).read_text(encoding="utf-8")
        title = extract_title(raw_text, md_rel)
        html_rel = md_rel.with_suffix(".html")

        parts = md_rel.parts
        folder_key = "." if len(parts) == 1 else parts[0]
        file_hint = "/".join(parts[1:]) if len(parts) > 2 else ""

        item = {
            "md_rel": md_rel,
            "html_rel": html_rel,
            "title": title,
            "sidebar_label": title,
            "file_hint": file_hint,
            "folder_key": folder_key,
            "raw_text": raw_text,
        }
        docs_info.append(item)
        grouped_docs.setdefault(folder_key, []).append(item)

    pygments_css = get_pygments_css()
    total_md_links_fixed = 0
    total_anchors_fixed = 0
    all_heading_ids = {}

    for idx, doc in enumerate(docs_info):
        md_rel = doc["md_rel"]
        html_rel = doc["html_rel"]
        out_path = DIST_DIR / html_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)

        preprocessed, mermaid_blocks = preprocess_markdown(doc["raw_text"])

        if HAS_MARKDOWN:
            md_parser = markdown.Markdown(
                extensions=["extra", "toc", "codehilite", "tables"],
                extension_configs={
                    "toc": {
                        "slugify": slugify_heading,
                        "permalink": False,
                    },
                    "codehilite": {
                        "guess_lang": False,
                        "use_pygments": True,
                        "css_class": "codehilite",
                    },
                },
            )
            raw_html = md_parser.convert(preprocessed)
            toc_html = getattr(md_parser, "toc", "")
        else:
            raw_html, toc_html = convert_markdown_fallback(preprocessed)

        processed_html, md_fixed, anc_fixed = postprocess_html(
            raw_html, md_rel, all_heading_ids, mermaid_blocks
        )
        total_md_links_fixed += md_fixed
        total_anchors_fixed += anc_fixed

        sidebar_html = build_sidebar_html(html_rel, grouped_docs)
        prev_item = docs_info[idx - 1] if idx > 0 else None
        next_item = docs_info[idx + 1] if idx + 1 < len(docs_info) else None

        full_page = render_page_template(
            title=doc["title"],
            body_html=processed_html,
            toc_html=toc_html,
            sidebar_html=sidebar_html,
            current_html_rel=html_rel,
            pygments_css=pygments_css,
            prev_item=prev_item,
            next_item=next_item,
        )

        out_path.write_text(full_page, encoding="utf-8", newline="\n")

    report = validate_output(md_files, other_files, all_heading_ids)

    print("\n" + "-" * 72)
    print(" RESUMEN DE CONVERSIÓN Y VALIDACIÓN")
    print("-" * 72)
    print(f" [OK] Carpeta destino            : {DIST_DIR}")
    print(f" [OK] Archivos MD convertidos    : {report['found_html']} / {report['expected_html']}")
    print(f" [OK] Grupos en menú lateral     : {len(grouped_docs)} submenús")
    print(f" [OK] Enlaces .md -> .html       : {total_md_links_fixed} reemplazados")
    print(f" [OK] Anclajes # corregidos      : {total_anchors_fixed} normalizados")
    print(f" [OK] Enlaces .md sin convertir  : {len(report['unconverted_md_hrefs'])}")
    print(f" [OK] Enlaces internos rotos     : {len(report['broken_links'])}")
    print(f" [OK] Anclajes internos rotos    : {len(report['broken_anchors'])}")

    if (
        report["missing_html"]
        or report["empty_html"]
        or report["unconverted_md_hrefs"]
        or report["broken_links"]
        or report["broken_anchors"]
    ):
        print("\n[!] Se encontraron advertencias durante la validación:")
        for k in ("missing_html", "empty_html", "unconverted_md_hrefs", "broken_links", "broken_anchors"):
            if report[k]:
                print(f"  - {k}: {report[k]}")
        sys.exit(1)
    else:
        print("\n [EXITO] Validación completada: 100% de integridad estructural y de enlaces.")
        print("=" * 72)


if __name__ == "__main__":
    main()
