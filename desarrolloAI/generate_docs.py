#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Documentación Técnica Profesional (Markdown a HTML)
Convierte todos los archivos Markdown del repositorio en un sitio web
estático navegable, responsive y basado en Bootstrap 5 dentro de `dist_html`.
"""

import html
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path

# Asegurar acceso a las librerías markdown y pygments en el entorno local
EXTRA_SITE_PACKAGES = [
    r"C:\Users\PC\AppData\Local\Python\pythoncore-3.15-64\Lib\site-packages",
    r"C:\Program Files\Microsoft SDKs\Azure\CLI2\Lib\site-packages",
]
for sp in EXTRA_SITE_PACKAGES:
    if os.path.isdir(sp) and sp not in sys.path:
        sys.path.append(sp)

HAS_MARKDOWN = False
try:
    import markdown
    from markdown.extensions.toc import slugify as md_slugify
    from pygments.formatters import HtmlFormatter
    HAS_MARKDOWN = True
except ImportError:
    az_py = r"C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe"
    if os.path.isfile(az_py) and os.path.normcase(sys.executable) != os.path.normcase(az_py):
        import subprocess
        sys.exit(subprocess.call([az_py, "-B", __file__, *sys.argv[1:]]))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT_DIR = Path(__file__).resolve().parent
DIST_DIR = ROOT_DIR / "dist_html"
EXCLUDED_DIRS = {"dist_html", ".git", ".venv", "__pycache__", "node_modules"}

FOLDER_LABELS = {
    ".": "Inicio / Raíz",
    "01-fundamentos": "01-fundamentos",
    "02-flujos-de-trabajo": "02-flujos-de-trabajo",
    "03-herramientas": "03-herramientas",
    "04-extensibilidad": "04-extensibilidad",
    "05-mcp": "05-mcp",
    "06-spec-driven": "06-spec-driven",
    "07-testing": "07-testing",
    "08-proyecto-integrador": "08-proyecto-integrador",
    "09-avanzado": "09-avanzado",
    "plantillas": "plantillas",
    "referencia": "referencia",
}


def slugify_heading(value: str, separator: str = "-") -> str:
    """Genera IDs consistentes y limpios para encabezados y anclajes."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^\w\s-]", "", ascii_str).strip().lower()
    slug = re.sub(r"[-\s]+", separator, cleaned).strip(separator)
    return slug or "section"


def discover_files(root: Path):
    """Descubre todos los archivos Markdown y otros recursos del proyecto."""
    md_files = []
    other_files = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Filtrar carpetas excluidas (pero permitir carpetas ocultas de plantillas como .claude y .opencode)
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIRS)
        rel_dir = Path(dirpath).relative_to(root)

        for fname in sorted(filenames):
            if fname == "generate_docs.py":
                continue
            full_path = Path(dirpath) / fname
            rel_path = rel_dir / fname if str(rel_dir) != "." else Path(fname)
            if fname.lower().endswith(".md"):
                md_files.append(rel_path)
            else:
                other_files.append(rel_path)

    # Ordenar archivos raíz primero (README.md, 00-ruta-de-aprendizaje.md) y luego el resto
    def sort_key(p: Path):
        parts = p.parts
        if len(parts) == 1:
            if parts[0].lower() == "readme.md":
                return (0, "", parts[0])
            return (0, "z", parts[0])
        return (1, parts[0], str(p).lower())

    md_files.sort(key=sort_key)
    return md_files, other_files


def extract_title(md_text: str, rel_path: Path) -> str:
    """Extrae el título principal (H1) del archivo Markdown o genera uno legible."""
    in_code = False
    lines = md_text.splitlines()
    start_idx = 0

    # Saltar frontmatter YAML si existe
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

    # Fallback: usar el nombre de archivo
    stem = rel_path.stem
    if len(rel_path.parts) > 2 and rel_path.parts[0] == "plantillas":
        sub = "/".join(rel_path.parts[1:])
        return f"{stem} ({sub})"
    return stem


def preprocess_markdown(md_text: str) -> str:
    """
    Preprocesa el contenido Markdown garantizando cero pérdida:
    1. Convierte frontmatter YAML inicial en un bloque de código YAML estilizado.
    2. Asegura línea en blanco antes de listas precedidas inmediatamente por texto.
    3. Normaliza listas anidadas de 2 espacios a 4 espacios para Python-Markdown.
    4. Convierte URLs sueltas en enlaces clicables fuera de bloques de código.
    """
    lines = md_text.splitlines()
    out_lines = []
    idx = 0

    # 1. Preservar frontmatter YAML si está al inicio del archivo
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
    code_fence_marker = ""
    in_list = False

    url_outside_links_re = re.compile(
        r"(?<![(\[<`\"'])(https?://[^\s<>()\"'`]+)(?![)\]>\"'`])"
    )

    for i in range(idx, len(lines)):
        line = lines[i]
        stripped = line.strip()

        # Detectar apertura/cierre de bloques de código
        fence_match = re.match(r"^(\s*)(`{3,}|~{3,})", line)
        if fence_match:
            marker = fence_match.group(2)
            if not in_code:
                in_code = True
                code_fence_marker = marker[0] * len(marker)
                in_list = False
            elif stripped.startswith(code_fence_marker):
                in_code = False
                code_fence_marker = ""
            out_lines.append(line)
            continue

        if in_code:
            out_lines.append(line)
            continue

        # Detectar elementos de lista
        list_match = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", line)
        if list_match:
            indent, marker, rest = list_match.groups()
            # Si la línea previa no está vacía y no es lista/cita/encabezado/tabla, insertar línea en blanco
            if out_lines:
                prev = out_lines[-1].strip()
                if (
                    prev
                    and not re.match(r"^([-*+]|\d+\.|>|#|\|)", prev)
                    and not prev.startswith("---")
                ):
                    out_lines.append("")

            # Normalizar sangría de listas anidadas (2 espacios -> 4 espacios por nivel)
            indent_len = len(indent.replace("\t", "    "))
            if indent_len > 0 and indent_len % 4 != 0 and indent_len % 2 == 0:
                indent = "    " * (indent_len // 2)
            line = f"{indent}{marker} {rest}"
            in_list = True
        else:
            if not stripped:
                in_list = False
            elif in_list and line.startswith("  ") and not line.startswith("    "):
                # Continuación de elemento de lista anidado con 2 espacios
                leading = len(line) - len(line.lstrip(" "))
                if leading % 2 == 0:
                    line = ("    " * (leading // 2)) + line.lstrip(" ")

        # Escapar marcadores tipo <NOMBRE> o <...> fuera de código inline (preservando <http...> y etiquetas HTML/SVG válidas)
        if "<" in line and ">" in line:
            valid_html_tags = {
                "svg", "/svg", "path", "/path", "g", "/g", "circle", "rect", "line",
                "polyline", "polygon", "text", "/text", "defs", "/defs", "img", "br",
                "hr", "sub", "/sub", "sup", "/sup", "kbd", "/kbd", "mark", "/mark",
                "details", "/details", "summary", "/summary",
            }
            parts = re.split(r"(`[^`]*`)", line)
            for p_idx in range(0, len(parts), 2):
                def _escape_placeholder(m):
                    inner = m.group(1).strip()
                    if inner.startswith(("http://", "https://", "mailto:")):
                        return m.group(0)
                    tag_name = inner.split()[0].rstrip("/").lower() if inner else ""
                    if tag_name in valid_html_tags:
                        return m.group(0)
                    return f"&lt;{m.group(1)}&gt;"

                parts[p_idx] = re.sub(r"<([^<>]+)>", _escape_placeholder, parts[p_idx])
            line = "".join(parts)

        # Autolink de URLs sueltas fuera de código inline `...`
        if "http://" in line or "https://" in line:
            parts = re.split(r"(`[^`]*`)", line)
            for p_idx in range(0, len(parts), 2):
                def _wrap_url(m):
                    url = m.group(1)
                    trailing = ""
                    while url and url[-1] in ".,;:":
                        trailing = url[-1] + trailing
                        url = url[:-1]
                    return f"<{url}>{trailing}"

                parts[p_idx] = url_outside_links_re.sub(_wrap_url, parts[p_idx])
            line = "".join(parts)

        out_lines.append(line)

    return "\n".join(out_lines)


def postprocess_html(html_content: str, current_md_rel: Path, all_heading_ids: dict) -> tuple[str, int, int]:
    """
    Realiza el post-procesamiento HTML:
    - Reemplaza extensiones .md por .html en atributos href.
    - Corrige anclajes internos (#...) para que coincidan con los IDs generados.
    - Aplica clases de Bootstrap 5 a tablas, citas, checklists y diagramas.
    """
    md_links_fixed = 0
    anchors_fixed = 0

    # Extraer todos los IDs presentes en el documento actual
    local_ids = set(re.findall(r'\bid="([^"]+)"', html_content))
    all_heading_ids[str(current_md_rel).replace("\\", "/")] = local_ids

    def fix_href(match):
        nonlocal md_links_fixed, anchors_fixed
        prefix, href, suffix = match.group(1), match.group(2).strip(), match.group(3)

        # Ignorar enlaces externos o esquemas especiales
        if href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:", "data:")):
            return f'{prefix}{href}{suffix} target="_blank" rel="noopener noreferrer"'

        # Separar ruta y fragmento (#anclaje)
        if "#" in href:
            path_part, frag_part = href.split("#", 1)
            has_frag = True
        else:
            path_part, frag_part = href, ""
            has_frag = False

        # Reemplazar .md por .html en la ruta
        if path_part.lower().endswith(".md"):
            path_part = path_part[:-3] + ".html"
            md_links_fixed += 1

        # Corregir anclaje (#...)
        if has_frag and frag_part:
            if not path_part:
                # Anclaje interno dentro de la misma página
                if frag_part not in local_ids:
                    candidate = slugify_heading(frag_part, "-")
                    if candidate in local_ids:
                        frag_part = candidate
                        anchors_fixed += 1
                    else:
                        # Buscar coincidencia parcial en local_ids
                        matched = next(
                            (lid for lid in local_ids if candidate in lid or lid in candidate),
                            candidate,
                        )
                        if matched != frag_part:
                            frag_part = matched
                            anchors_fixed += 1
            else:
                # Anclaje hacia otra página: normalizar con la misma función slugify
                candidate = slugify_heading(frag_part, "-")
                if candidate != frag_part:
                    frag_part = candidate
                    anchors_fixed += 1

        new_href = f"{path_part}#{frag_part}" if has_frag else path_part
        return f"{prefix}{new_href}{suffix}"

    html_content = re.sub(r'(<a\s+[^>]*?href=")([^"]+)(")', fix_href, html_content)

    # Estilizar tablas con Bootstrap 5 y contenedor responsive con shadow-sm
    html_content = re.sub(
        r"<table>",
        '<div class="table-responsive shadow-sm rounded-3 my-4"><table class="table table-hover table-striped table-bordered align-middle mb-0">',
        html_content,
    )
    html_content = re.sub(r"</table>", "</table></div>", html_content)

    # Estilizar blockquotes
    html_content = re.sub(
        r"<blockquote>",
        '<blockquote class="blockquote doc-blockquote shadow-sm my-3">',
        html_content,
    )

    # Convertir checklists ([ ] y [x]) en checkboxes estilizados
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

    # Identificar bloques de diagramas y reemplazarlos por diagramas vectoriales SVG sin perder información
    def style_pre_blocks(match):
        block = match.group(0)
        clean_text = html.unescape(re.sub(r"<[^>]+>", "", block)).strip()
        svg_result = convert_diagram_block_if_applicable(clean_text)
        if svg_result is not None:
            header_title, svg_markup = svg_result
            svg_badge = (
                '<div class="diagram-header d-flex align-items-center justify-content-between px-3 py-1 border-bottom">'
                '<span class="d-flex align-items-center gap-2">'
                '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="#38bdf8" viewBox="0 0 16 16" aria-hidden="true">'
                '<path fill-rule="evenodd" d="M6 3.5A1.5 1.5 0 0 1 7.5 2h1A1.5 1.5 0 0 1 10 3.5v1A1.5 1.5 0 0 1 8.5 6v1H14a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0v-1A.5.5 0 0 1 2 7h5.5V6A1.5 1.5 0 0 1 6 4.5v-1z"/>'
                '<path d="M1 11.5A1.5 1.5 0 0 1 2.5 10h1A1.5 1.5 0 0 1 5 11.5v1A1.5 1.5 0 0 1 3.5 14h-1A1.5 1.5 0 0 1 1 12.5v-1zm5 0A1.5 1.5 0 0 1 7.5 10h1a1.5 1.5 0 0 1 1.5 1.5v1A1.5 1.5 0 0 1 8.5 14h-1A1.5 1.5 0 0 1 6 12.5v-1zm5 0a1.5 1.5 0 0 1 1.5-1.5h1a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5v-1z"/>'
                "</svg>"
                f'<span class="small fw-semibold text-uppercase">{html.escape(header_title)}</span>'
                "</span>"
                '<span class="badge bg-info-subtle text-info-emphasis border border-info-subtle" style="font-size:0.68rem;">SVG</span>'
                "</div>"
            )
            return (
                f'<div class="diagram-wrapper shadow-sm rounded-3 my-3" data-diagram-source="{_esc_svg(clean_text)}">'
                f"{svg_badge}"
                f'<div class="diagram-svg-body">{svg_markup}</div>'
                f"</div>"
            )
        return block

    html_content = re.sub(
        r'<div class="codehilite"><pre>.*?</pre></div>|<pre>.*?</pre>',
        style_pre_blocks,
        html_content,
        flags=re.DOTALL,
    )

    return html_content, md_links_fixed, anchors_fixed


def _esc_svg(text: str) -> str:
    return html.escape(text, quote=True)


def _svg_wrap(viewbox_w: int, viewbox_h: int, aria_label: str, inner: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {viewbox_w} {viewbox_h}" '
        f'width="100%" style="max-width:{viewbox_w}px;height:auto;" '
        f'role="img" aria-label="{_esc_svg(aria_label)}">'
        f"<defs>"
        f'<marker id="arrow-sky" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M 0 1 L 9 5 L 0 9 z" fill="#38bdf8"/>'
        f"</marker>"
        f'<marker id="arrow-emerald" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M 0 1 L 9 5 L 0 9 z" fill="#34d399"/>'
        f"</marker>"
        f'<marker id="arrow-amber" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M 0 1 L 9 5 L 0 9 z" fill="#fbbf24"/>'
        f"</marker>"
        f'<marker id="arrow-violet" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M 0 1 L 9 5 L 0 9 z" fill="#a78bfa"/>'
        f"</marker>"
        f'<marker id="arrow-slate" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M 0 1 L 9 5 L 0 9 z" fill="#94a3b8"/>'
        f"</marker>"
        f"</defs>"
        f"{inner}"
        f"</svg>"
    )


def _draw_box(
    x: float,
    y: float,
    w: float,
    h: float,
    lines: list[str],
    stroke: str = "#38bdf8",
    fill: str = "#1e293b",
    title_first: bool = True,
    font_size: int = 13,
    sub_size: int = 12,
    rx: int = 8,
    mono_title: bool = False,
) -> str:
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
    ]
    n = len(lines)
    if n == 0:
        return "".join(parts)
    line_gap = 18
    total_h = (n - 1) * line_gap
    start_y = y + (h - total_h) / 2 + 4
    cx = x + w / 2
    title_ff = (
        "Cascadia Mono, Consolas, monospace"
        if mono_title
        else "Segoe UI, Roboto, sans-serif"
    )
    for i, line in enumerate(lines):
        ly = start_y + i * line_gap
        if i == 0 and title_first:
            parts.append(
                f'<text x="{cx}" y="{ly}" text-anchor="middle" fill="#f8fafc" '
                f'font-family="{title_ff}" font-size="{font_size}" font-weight="700">{_esc_svg(line)}</text>'
            )
        else:
            parts.append(
                f'<text x="{cx}" y="{ly}" text-anchor="middle" fill="#cbd5e1" '
                f'font-family="Segoe UI, Roboto, sans-serif" font-size="{sub_size}" font-weight="500">{_esc_svg(line)}</text>'
            )
    return "".join(parts)


def _draw_arrow(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: str = "#38bdf8",
    marker: str = "arrow-sky",
    bidir: bool = False,
    label: str = "",
) -> str:
    m_start = f' marker-start="url(#{marker})"' if bidir else ""
    m_end = f' marker-end="url(#{marker})"'
    parts = [
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2"{m_start}{m_end}/>'
    ]
    if label:
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2 - 7
        parts.append(
            f'<text x="{mx}" y="{my}" text-anchor="middle" fill="{color}" '
            f'font-family="Cascadia Mono, Consolas, monospace" font-size="11.5" font-weight="600">{_esc_svg(label)}</text>'
        )
    return "".join(parts)


def _draw_ortho_arrow(
    points: list[tuple[float, float]],
    color: str = "#38bdf8",
    marker: str = "arrow-sky",
    dashed: bool = False,
) -> str:
    d = "M " + " L ".join(f"{px} {py}" for px, py in points)
    dash = ' stroke-dasharray="5,4"' if dashed else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"{dash} marker-end="url(#{marker})"/>'


def render_tree_svg(clean_text: str) -> tuple[str, str]:
    """Convierte un diagrama de estructura de carpetas/archivos (├──, └──, │) en un SVG vectorial."""
    raw_lines = [l.rstrip() for l in clean_text.strip().splitlines() if l.strip()]
    row_h = 30
    pad_x = 24
    pad_y = 22
    indent_w = 24

    parsed_rows = []
    max_name_end = 0
    tree_prefix_re = re.compile(r"^([│├└─\s]+)(.*)$")

    for line in raw_lines:
        m = tree_prefix_re.match(line)
        if m:
            prefix = m.group(1)
            rest = m.group(2)
        else:
            prefix = ""
            rest = line

        note = ""
        if "←" in rest:
            idx_arrow = rest.index("←")
            name_part = rest[:idx_arrow].strip()
            note = rest[idx_arrow:].strip()
        else:
            m_note = re.match(r"^(\S+)\s{2,}(.+)$", rest)
            if m_note:
                name_part = m_note.group(1).strip()
                note = m_note.group(2).strip()
            else:
                name_part = rest.strip()

        depth = len(prefix) // 4
        connectors = []
        for lvl in range(depth):
            chunk = prefix[lvl * 4 : (lvl + 1) * 4]
            if "├" in chunk:
                connectors.append((lvl, "branch"))
            elif "└" in chunk:
                connectors.append((lvl, "last"))
            elif "│" in chunk:
                connectors.append((lvl, "vert"))

        is_dir = (
            name_part.endswith("/")
            or name_part.endswith("...")
            or "/{" in name_part
            or (depth == 0 and "." not in name_part)
        )

        icon_x = pad_x + depth * indent_w
        text_x = icon_x + 22
        est_name_w = len(name_part) * 8.2
        if text_x + est_name_w > max_name_end:
            max_name_end = text_x + est_name_w

        parsed_rows.append(
            {
                "depth": depth,
                "connectors": connectors,
                "name": name_part,
                "note": note,
                "is_dir": is_dir,
                "icon_x": icon_x,
                "text_x": text_x,
            }
        )

    note_col_x = int(max(max_name_end + 28, 280))
    max_total_w = max_name_end + 36
    for r in parsed_rows:
        if r["note"]:
            note_w = len(r["note"]) * 7.5 + 28
            if note_col_x + note_w + 24 > max_total_w:
                max_total_w = note_col_x + note_w + 24

    vb_w = int(max(680, max_total_w + 12))
    vb_h = int(pad_y * 2 + len(parsed_rows) * row_h)

    svg_els = []
    for idx, r in enumerate(parsed_rows):
        cy = pad_y + idx * row_h + row_h / 2
        top_y = pad_y + idx * row_h
        bot_y = top_y + row_h

        if idx % 2 == 1:
            svg_els.append(
                f'<rect x="10" y="{top_y}" width="{vb_w - 20}" height="{row_h}" rx="4" fill="#1e293b" fill-opacity="0.35"/>'
            )

        for lvl, ctype in r["connectors"]:
            cx = pad_x + lvl * indent_w + 7
            if ctype == "vert":
                svg_els.append(
                    f'<line x1="{cx}" y1="{top_y}" x2="{cx}" y2="{bot_y}" stroke="#475569" stroke-width="1.5"/>'
                )
            elif ctype == "branch":
                svg_els.append(
                    f'<line x1="{cx}" y1="{top_y}" x2="{cx}" y2="{bot_y}" stroke="#475569" stroke-width="1.5"/>'
                )
                svg_els.append(
                    f'<line x1="{cx}" y1="{cy}" x2="{r["icon_x"] - 4}" y2="{cy}" stroke="#475569" stroke-width="1.5"/>'
                )
            elif ctype == "last":
                svg_els.append(
                    f'<path d="M {cx} {top_y} L {cx} {cy} L {r["icon_x"] - 4} {cy}" fill="none" stroke="#475569" stroke-width="1.5"/>'
                )

        ix = r["icon_x"]
        iy = cy - 7
        if r["is_dir"]:
            svg_els.append(
                f'<path d="M {ix} {iy+2} a 1.5 1.5 0 0 1 1.5 -1.5 h 4 l 1.5 2 h 6.5 a 1.5 1.5 0 0 1 1.5 1.5 v 7.5 a 1.5 1.5 0 0 1 -1.5 1.5 h -12 a 1.5 1.5 0 0 1 -1.5 -1.5 z" fill="#38bdf8" fill-opacity="0.22" stroke="#38bdf8" stroke-width="1.3"/>'
            )
        else:
            svg_els.append(
                f'<rect x="{ix+1}" y="{iy}" width="12" height="14" rx="2" fill="#94a3b8" fill-opacity="0.18" stroke="#94a3b8" stroke-width="1.2"/>'
            )

        text_color = "#38bdf8" if r["is_dir"] else "#f8fafc"
        font_weight = "700" if r["is_dir"] else "500"
        svg_els.append(
            f'<text x="{r["text_x"]}" y="{cy + 4.5}" fill="{text_color}" '
            f'font-family="Cascadia Mono, Consolas, monospace" font-size="13" font-weight="{font_weight}">{_esc_svg(r["name"])}</text>'
        )

        if r["note"]:
            pill_w = int(len(r["note"]) * 7.5 + 24)
            svg_els.append(
                f'<rect x="{note_col_x}" y="{cy - 10.5}" width="{pill_w}" height="21" rx="6" fill="#0f172a" stroke="#334155" stroke-width="1"/>'
            )
            svg_els.append(
                f'<text x="{note_col_x + 10}" y="{cy + 4}" fill="#94a3b8" '
                f'font-family="Segoe UI, Roboto, sans-serif" font-size="12">{_esc_svg(r["note"])}</text>'
            )

    root_label = parsed_rows[0]["name"] if parsed_rows else "Estructura"
    return (
        "Diagrama SVG · Estructura de Directorios y Archivos",
        _svg_wrap(vb_w, vb_h, f"Estructura de archivos: {root_label}", "".join(svg_els)),
    )


def render_custom_flow_svg(clean_text: str) -> tuple[str, str] | None:
    """Identifica cada uno de los 14 diagramas de arquitectura/flujo y devuelve su SVG vectorial."""
    t = clean_text.strip()

    # 1. 00-ruta-de-aprendizaje: Mapa del conocimiento
    if "01 Fundamentos" in t and "09 Avanzado: aislamiento" in t:
        els = [
            _draw_box(230, 16, 360, 62, ["01 Fundamentos", "agentes · LLMs · contexto"], "#38bdf8"),
            _draw_arrow(410, 78, 410, 108),
            _draw_box(230, 108, 360, 62, ["02 Flujos de trabajo", "+ seguridad y buenas prácticas"], "#38bdf8"),
            _draw_arrow(410, 170, 410, 200),
            _draw_box(195, 200, 430, 52, ["03 Herramientas: Claude Code · OpenCode"], "#818cf8"),
            _draw_arrow(410, 252, 410, 282),
            _draw_box(185, 282, 450, 62, ["04 Extensibilidad: skills · agentes ·", "hooks · comandos · plugins"], "#a78bfa"),
            _draw_ortho_arrow([(300, 344), (300, 364), (235, 364), (235, 386)], "#34d399", "arrow-emerald"),
            _draw_ortho_arrow([(520, 344), (520, 364), (585, 364), (585, 386)], "#fbbf24", "arrow-amber"),
            _draw_box(85, 386, 300, 64, ["05 MCP", "Python · Node · C#"], "#34d399"),
            _draw_box(435, 386, 300, 64, ["06 OpenSpec", "spec-driven development"], "#fbbf24"),
            _draw_ortho_arrow([(235, 450), (235, 470), (310, 470), (310, 492)], "#38bdf8"),
            _draw_ortho_arrow([(585, 450), (585, 470), (510, 470), (510, 492)], "#38bdf8"),
            _draw_box(205, 492, 410, 64, ["07 Testing: unitarias · E2E", "Playwright · Playwright MCP"], "#f472b6"),
            _draw_arrow(410, 556, 410, 586),
            _draw_box(230, 586, 360, 50, ["08 Proyecto integrador"], "#fb923c"),
            _draw_arrow(410, 636, 410, 666),
            _draw_box(220, 666, 380, 82, ["09 Avanzado: aislamiento ·", "evals/observabilidad · RAG y", "memoria"], "#2dd4bf"),
        ]
        return (
            "Diagrama SVG · Mapa de la Ruta de Aprendizaje",
            _svg_wrap(820, 766, "Mapa del conocimiento: 01 Fundamentos a 09 Avanzado", "".join(els)),
        )

    # 2. 01-fundamentos/01-que-es-el-desarrollo-agentico: El loop agéntico
    if "OBJETIVO" in t and "LLAMADA A TOOL" in t and "OBSERVACIÓN" in t:
        els = [
            _draw_box(220, 16, 420, 64, ["OBJETIVO", '"Añade paginación al endpoint /tareas"'], "#fbbf24"),
            _draw_arrow(430, 80, 430, 122, "#fbbf24", "arrow-amber"),
            _draw_box(35, 122, 210, 96, ["CONTEXTO", "prompt,", "archivos,", "historial"], "#38bdf8"),
            _draw_arrow(245, 170, 305, 170, "#38bdf8", "arrow-sky"),
            _draw_box(305, 122, 250, 96, ["MODELO (LLM)", "razona y decide", "el siguiente paso"], "#a78bfa"),
            _draw_arrow(555, 170, 615, 170, "#34d399", "arrow-emerald"),
            _draw_box(615, 122, 210, 96, ["LLAMADA A TOOL", "Read, Grep, Bash,", "Edit, MCP..."], "#34d399"),
            _draw_box(305, 258, 250, 92, ["OBSERVACIÓN", "salida, errores,", "resultados de tests"], "#fb923c"),
            _draw_ortho_arrow([(720, 218), (720, 304), (555, 304)], "#34d399", "arrow-emerald"),
            _draw_ortho_arrow([(305, 304), (140, 304), (140, 218)], "#38bdf8", "arrow-sky"),
            '<text x="430" y="384" text-anchor="middle" fill="#94a3b8" font-family="Segoe UI, Roboto, sans-serif" font-size="13" font-style="italic">(se repite hasta cumplir el objetivo o pedir ayuda)</text>',
        ]
        return (
            "Diagrama SVG · El Loop Agéntico",
            _svg_wrap(860, 404, "El loop agéntico: Objetivo, Contexto, Modelo LLM, Llamada a Tool, Observación", "".join(els)),
        )

    # 3. 01-fundamentos/02-llms-contexto-y-tokens: Ventana de contexto
    if "ventana de contexto" in t and "system prompt" in t:
        els = [
            '<rect x="20" y="26" width="820" height="162" rx="12" fill="#0f172a" stroke="#38bdf8" stroke-width="2" stroke-dasharray="6,4"/>',
            '<rect x="310" y="12" width="240" height="28" rx="14" fill="#0284c7"/>',
            '<text x="430" y="31" text-anchor="middle" fill="#ffffff" font-family="Segoe UI, Roboto, sans-serif" font-size="13" font-weight="700">ventana de contexto</text>',
            _draw_box(42, 54, 195, 52, ["system prompt"], "#38bdf8", "#1e293b", True, 13),
            _draw_box(252, 54, 240, 52, ["CLAUDE.md/AGENTS.md"], "#818cf8", "#1e293b", True, 13, 12, 8, True),
            _draw_box(507, 54, 310, 52, ["descripciones de tools/MCP/skills"], "#a78bfa", "#1e293b", True, 13),
            _draw_box(42, 118, 245, 52, ["historial de conversación"], "#34d399", "#1e293b", True, 13),
            _draw_box(302, 118, 185, 52, ["archivos leídos"], "#fbbf24", "#1e293b", True, 13),
            _draw_box(502, 118, 215, 52, ["salidas de comandos"], "#fb923c", "#1e293b", True, 13),
            _draw_box(732, 118, 85, 52, ["..."], "#94a3b8", "#1e293b", True, 15),
        ]
        return (
            "Diagrama SVG · Composición de la Ventana de Contexto",
            _svg_wrap(860, 206, "Elementos que compiten por la ventana de contexto", "".join(els)),
        )

    # 4. 02-flujos-de-trabajo/01-flujos-de-trabajo-agenticos: SDD lineal
    if "/opsx:explore" in t and "crea proposal" not in t and "revisión humana" in t:
        els = [
            _draw_box(16, 22, 145, 52, ["/opsx:explore"], "#38bdf8", "#1e293b", True, 13, 12, 8, True),
            _draw_arrow(161, 48, 193, 48),
            _draw_box(193, 22, 145, 52, ["/opsx:propose"], "#818cf8", "#1e293b", True, 13, 12, 8, True),
            _draw_arrow(338, 48, 370, 48),
            _draw_box(370, 22, 160, 52, ["revisión humana"], "#fbbf24", "#1e293b", True, 13),
            _draw_arrow(530, 48, 562, 48),
            _draw_box(562, 22, 140, 52, ["/opsx:apply"], "#34d399", "#1e293b", True, 13, 12, 8, True),
            _draw_arrow(702, 48, 734, 48),
            _draw_box(734, 22, 145, 52, ["/opsx:archive"], "#a78bfa", "#1e293b", True, 13, 12, 8, True),
        ]
        return (
            "Diagrama SVG · Flujo Spec-Driven Development (SDD)",
            _svg_wrap(895, 96, "Flujo SDD: explore, propose, revisión humana, apply, archive", "".join(els)),
        )

    # 5. 04-extensibilidad/02-agentes-y-subagentes: Delegación en subagentes
    if "Agente principal (tu sesión)" in t and 'subagente "explorador"' in t:
        els = [
            _draw_box(24, 18, 270, 48, ["Agente principal (tu sesión)"], "#38bdf8"),
            _draw_ortho_arrow([(60, 66), (60, 108), (110, 108)], "#38bdf8", "arrow-sky"),
            _draw_ortho_arrow([(60, 66), (60, 168), (110, 168)], "#34d399", "arrow-emerald"),
            _draw_ortho_arrow([(60, 66), (60, 228), (110, 228)], "#a78bfa", "arrow-violet"),
            _draw_box(110, 84, 220, 48, ['subagente "explorador"'], "#38bdf8"),
            _draw_arrow(330, 108, 375, 108, "#38bdf8", "arrow-sky"),
            _draw_box(375, 84, 485, 48, ['"Los pagos se procesan en src/pagos/... (resumen)"'], "#475569", "#0f172a", False, 12, 12.5),
            _draw_box(110, 144, 220, 48, ['subagente "test-writer"'], "#34d399"),
            _draw_arrow(330, 168, 375, 168, "#34d399", "arrow-emerald"),
            _draw_box(375, 144, 485, 48, ['"Añadí 8 tests, todos pasan"'], "#475569", "#0f172a", False, 12, 12.5),
            _draw_box(110, 204, 220, 48, ['subagente "revisor"'], "#a78bfa"),
            _draw_arrow(330, 228, 375, 228, "#a78bfa", "arrow-violet"),
            _draw_box(375, 204, 485, 48, ['"2 hallazgos altos, 1 medio"'], "#475569", "#0f172a", False, 12, 12.5),
        ]
        return (
            "Diagrama SVG · Delegación en Subagentes",
            _svg_wrap(880, 272, "Agente principal delegando en subagentes explorador, test-writer y revisor", "".join(els)),
        )

    # 6. 05-mcp/01-mcp-conceptos: Arquitectura MCP
    if "HOST (Claude Code, OpenCode, VS Code, tu app)" in t and "Cliente MCP A" in t:
        els = [
            '<rect x="18" y="24" width="864" height="224" rx="12" fill="#0f172a" stroke="#38bdf8" stroke-width="2"/>',
            '<rect x="40" y="10" width="390" height="28" rx="8" fill="#0284c7"/>',
            '<text x="235" y="29" text-anchor="middle" fill="#ffffff" font-family="Segoe UI, Roboto, sans-serif" font-size="13" font-weight="700">HOST (Claude Code, OpenCode, VS Code, tu app)</text>',
            _draw_box(42, 60, 110, 166, ["LLM"], "#a78bfa", "#1e293b", True, 16),
            _draw_arrow(156, 84, 224, 84, "#a78bfa", "arrow-violet", True),
            _draw_box(228, 60, 165, 48, ["Cliente MCP A"], "#38bdf8"),
            _draw_arrow(397, 84, 536, 84, "#34d399", "arrow-emerald", True, "stdio"),
            _draw_box(540, 60, 320, 48, ['Servidor MCP "tareas" (local)'], "#34d399"),
            _draw_arrow(156, 143, 224, 143, "#a78bfa", "arrow-violet", True),
            _draw_box(228, 119, 165, 48, ["Cliente MCP B"], "#38bdf8"),
            _draw_arrow(397, 143, 536, 143, "#fbbf24", "arrow-amber", True, "HTTP"),
            _draw_box(540, 119, 320, 48, ['Servidor MCP "github" (remoto)'], "#fbbf24"),
            _draw_arrow(156, 202, 224, 202, "#a78bfa", "arrow-violet", True),
            _draw_box(228, 178, 165, 48, ["Cliente MCP C"], "#38bdf8"),
            _draw_arrow(397, 202, 536, 202, "#34d399", "arrow-emerald", True, "stdio"),
            _draw_box(540, 178, 320, 48, ['Servidor MCP "playwright"'], "#34d399"),
        ]
        return (
            "Diagrama SVG · Arquitectura Host – Cliente – Servidor MCP",
            _svg_wrap(900, 266, "Arquitectura MCP: Host, LLM, Clientes MCP y Servidores MCP por stdio y HTTP", "".join(els)),
        )

    # 7. 06-spec-driven/01-openspec (Block #3): El ciclo OpenSpec detallado
    if "/opsx:explore" in t and "crea proposal" in t and "fusiona deltas" in t:
        els = [
            _draw_box(15, 20, 150, 50, ["/opsx:explore"], "#38bdf8", "#1e293b", True, 13, 12, 8, True),
            '<text x="90" y="92" text-anchor="middle" fill="#94a3b8" font-family="Segoe UI, Roboto, sans-serif" font-size="12">(opcional)</text>',
            _draw_arrow(165, 45, 198, 45),
            _draw_box(198, 20, 155, 50, ["/opsx:propose"], "#818cf8", "#1e293b", True, 13, 12, 8, True),
            '<text x="275" y="92" text-anchor="middle" fill="#cbd5e1" font-family="Segoe UI, Roboto, sans-serif" font-size="12">crea proposal,</text>',
            '<text x="275" y="110" text-anchor="middle" fill="#cbd5e1" font-family="Segoe UI, Roboto, sans-serif" font-size="12">specs, design,</text>',
            '<text x="275" y="128" text-anchor="middle" fill="#cbd5e1" font-family="Segoe UI, Roboto, sans-serif" font-size="12">tasks</text>',
            _draw_arrow(353, 45, 386, 45),
            _draw_box(386, 20, 165, 50, ["(revisión humana)"], "#fbbf24", "#1e293b", True, 13),
            _draw_arrow(551, 45, 584, 45),
            _draw_box(584, 20, 150, 50, ["/opsx:apply"], "#34d399", "#1e293b", True, 13, 12, 8, True),
            '<text x="659" y="92" text-anchor="middle" fill="#cbd5e1" font-family="Segoe UI, Roboto, sans-serif" font-size="12">implementa</text>',
            '<text x="659" y="110" text-anchor="middle" fill="#cbd5e1" font-family="Segoe UI, Roboto, sans-serif" font-size="12">tareas y las</text>',
            '<text x="659" y="128" text-anchor="middle" fill="#cbd5e1" font-family="Segoe UI, Roboto, sans-serif" font-size="12">marca [x]</text>',
            _draw_arrow(734, 45, 767, 45),
            _draw_box(767, 20, 150, 50, ["/opsx:archive"], "#a78bfa", "#1e293b", True, 13, 12, 8, True),
            '<text x="842" y="92" text-anchor="middle" fill="#cbd5e1" font-family="Segoe UI, Roboto, sans-serif" font-size="12">fusiona deltas</text>',
            '<text x="842" y="110" text-anchor="middle" fill="#cbd5e1" font-family="Segoe UI, Roboto, sans-serif" font-size="12">en specs/ y</text>',
            '<text x="842" y="128" text-anchor="middle" fill="#cbd5e1" font-family="Segoe UI, Roboto, sans-serif" font-size="12">archiva</text>',
        ]
        return (
            "Diagrama SVG · Ciclo OpenSpec (Perfil Core)",
            _svg_wrap(932, 150, "Ciclo OpenSpec: explore, propose, revisión humana, apply, archive", "".join(els)),
        )

    # 8. 07-testing/01-pruebas-unitarias-con-ia: Especificación -> Tests -> Implementación -> Verificación
    if "Especificación (OpenSpec / prompt)" in t and "Tests (contrato)" in t:
        els = [
            _draw_box(16, 20, 235, 56, ["Especificación", "(OpenSpec / prompt)"], "#38bdf8"),
            _draw_arrow(251, 48, 285, 48),
            _draw_box(285, 20, 175, 56, ["Tests", "(contrato)"], "#fbbf24"),
            _draw_arrow(460, 48, 494, 48),
            _draw_box(494, 20, 190, 56, ["Implementación", "(agente)"], "#a78bfa"),
            _draw_arrow(684, 48, 718, 48),
            _draw_box(718, 20, 185, 56, ["Verificación", "automática"], "#34d399"),
        ]
        return (
            "Diagrama SVG · Flujo de Verificación y TDD con IA",
            _svg_wrap(920, 96, "Especificación (OpenSpec / prompt) -> Tests (contrato) -> Implementación (agente) -> Verificación automática", "".join(els)),
        )

    # 9. 07-testing/03-playwright-con-ia-mcp-y-test-agents (Block #6): planner -> specs -> generator -> tests -> healer
    if "planner" in t and "specs/*.md" in t and "tests/*.spec.ts" in t and "OpenSpec" not in t:
        els = [
            _draw_box(16, 22, 125, 52, ["planner"], "#38bdf8", "#1e293b", True, 13, 12, 8, True),
            _draw_arrow(141, 48, 173, 48),
            _draw_box(173, 22, 145, 52, ["specs/*.md"], "#94a3b8", "#0f172a", True, 13, 12, 8, True),
            _draw_arrow(318, 48, 350, 48),
            _draw_box(350, 22, 135, 52, ["generator"], "#34d399", "#1e293b", True, 13, 12, 8, True),
            _draw_arrow(485, 48, 517, 48),
            _draw_box(517, 22, 165, 52, ["tests/*.spec.ts"], "#94a3b8", "#0f172a", True, 13, 12, 8, True),
            _draw_arrow(682, 48, 714, 48),
            _draw_box(714, 22, 190, 52, ["healer (cuando fallan)"], "#a78bfa", "#1e293b", True, 13),
        ]
        return (
            "Diagrama SVG · Pipeline de Test Agents de Playwright",
            _svg_wrap(920, 96, "planner -> specs/*.md -> generator -> tests/*.spec.ts -> healer (cuando fallan)", "".join(els)),
        )

    # 10. 07-testing/03-playwright-con-ia-mcp-y-test-agents (Block #13): Integración con el resto del flujo
    if "OpenSpec (escenarios WHEN/THEN)" in t and "Playwright MCP (verificación interactiva" in t:
        els = [
            _draw_box(24, 18, 380, 50, ["OpenSpec (escenarios WHEN/THEN)"], "#fbbf24"),
            _draw_arrow(140, 68, 140, 96, "#fbbf24", "arrow-amber"),
            _draw_box(24, 96, 380, 50, ["planner (plan Markdown alineado con los escenarios)"], "#38bdf8"),
            _draw_arrow(140, 146, 140, 174, "#38bdf8", "arrow-sky"),
            _draw_box(24, 174, 220, 50, ["generator (tests E2E)"], "#34d399"),
            _draw_arrow(244, 199, 282, 199, "#34d399", "arrow-emerald"),
            _draw_box(282, 174, 150, 50, ["CI (Playwright)"], "#38bdf8"),
            _draw_arrow(432, 199, 470, 199, "#fb923c", "arrow-amber"),
            _draw_box(470, 174, 95, 50, ["fallo"], "#fb923c"),
            _draw_arrow(565, 199, 603, 199, "#a78bfa", "arrow-violet"),
            _draw_box(603, 174, 105, 50, ["healer"], "#a78bfa"),
            _draw_arrow(708, 199, 746, 199, "#34d399", "arrow-emerald"),
            _draw_box(746, 174, 160, 50, ["revisión humana"], "#34d399"),
            _draw_arrow(140, 256, 140, 224, "#818cf8", "arrow-violet"),
            _draw_box(24, 256, 460, 50, ["Playwright MCP (verificación interactiva mientras implementas la UI)"], "#818cf8"),
        ]
        return (
            "Diagrama SVG · Integración de OpenSpec, Playwright MCP y Test Agents",
            _svg_wrap(925, 326, "Flujo integrado OpenSpec, planner, generator, Playwright MCP, CI, healer y revisión humana", "".join(els)),
        )

    # 11. 09-avanzado/01-aislamiento-sandbox-devcontainers-docker: Espectro Autonomía vs Aislamiento
    if "Más autonomía" in t and "Más aislamiento" in t and "microVM" in t:
        els = [
            '<rect x="20" y="18" width="900" height="36" rx="18" fill="#1e293b" stroke="#334155" stroke-width="1"/>',
            '<text x="42" y="41" fill="#38bdf8" font-family="Segoe UI, Roboto, sans-serif" font-size="13" font-weight="700">Más autonomía</text>',
            _draw_arrow(160, 36, 765, 36, "#38bdf8", "arrow-sky"),
            '<text x="898" y="41" text-anchor="end" fill="#34d399" font-family="Segoe UI, Roboto, sans-serif" font-size="13" font-weight="700">Más aislamiento</text>',
            _draw_box(20, 70, 140, 92, ["default/ask", "(preguntas)"], "#38bdf8"),
            _draw_box(172, 70, 140, 92, ["accept edits", "(rama propia)"], "#60a5fa"),
            _draw_box(324, 70, 140, 92, ["auto mode", "(clasificador)"], "#818cf8"),
            _draw_box(476, 70, 140, 92, ["sandbox Bash", "(SO limita FS", "y red)"], "#a78bfa"),
            _draw_box(628, 70, 140, 92, ["Dev Container", "(contenedor +", "firewall)"], "#2dd4bf"),
            _draw_box(780, 70, 140, 92, ["microVM / VM / nube", "(kernel propio,", "desechable)"], "#34d399"),
        ]
        return (
            "Diagrama SVG · Espectro de Autonomía vs. Aislamiento",
            _svg_wrap(940, 180, "Espectro desde Más autonomía (default/ask) hasta Más aislamiento (microVM / VM / nube)", "".join(els)),
        )

    # 12. 09-avanzado/02-evaluacion-y-observabilidad: Bucle de mejora y observabilidad
    if "bucle de mejora" in t and "nuevos casos desde fallos reales" in t:
        els = [
            _draw_ortho_arrow([(500, 86), (500, 32), (125, 32), (125, 86)], "#fbbf24", "arrow-amber", True),
            '<rect x="235" y="18" width="150" height="26" rx="13" fill="#1e293b" stroke="#fbbf24" stroke-width="1.2"/>',
            '<text x="310" y="35" text-anchor="middle" fill="#fbbf24" font-family="Segoe UI, Roboto, sans-serif" font-size="12" font-weight="600">bucle de mejora</text>',
            _draw_box(20, 86, 210, 54, ["Cambio (prompt, skill, tool)"], "#38bdf8"),
            _draw_arrow(230, 113, 265, 113),
            _draw_box(265, 86, 145, 54, ["Evals (offline)"], "#818cf8"),
            _draw_arrow(410, 113, 445, 113),
            _draw_box(445, 86, 110, 54, ["¿Mejor?"], "#fbbf24"),
            _draw_arrow(555, 113, 590, 113),
            _draw_box(590, 86, 120, 54, ["Despliegue"], "#34d399"),
            _draw_arrow(710, 113, 745, 113),
            _draw_box(745, 86, 175, 54, ["Observabilidad (online)"], "#a78bfa"),
            _draw_ortho_arrow([(832, 140), (832, 196), (337, 196), (337, 140)], "#a78bfa", "arrow-violet", True),
            '<rect x="455" y="182" width="260" height="26" rx="13" fill="#1e293b" stroke="#a78bfa" stroke-width="1.2"/>',
            '<text x="585" y="199" text-anchor="middle" fill="#e2e8f0" font-family="Segoe UI, Roboto, sans-serif" font-size="12" font-weight="600">nuevos casos desde fallos reales</text>',
        ]
        return (
            "Diagrama SVG · Ciclo de Evaluación Offline y Observabilidad Online",
            _svg_wrap(940, 224, "Ciclo: Cambio -> Evals (offline) -> ¿Mejor? -> Despliegue -> Observabilidad (online)", "".join(els)),
        )

    # 13. 09-avanzado/03-rag-y-memoria-persistente (Block #0): Pipeline RAG
    if "INDEXACIÓN (offline)" in t and "CONSULTA (online)" in t:
        els = [
            '<rect x="16" y="14" width="908" height="118" rx="10" fill="#0f172a" stroke="#334155" stroke-width="1.5"/>',
            '<rect x="30" y="24" width="180" height="24" rx="6" fill="#0284c7"/>',
            '<text x="120" y="40" text-anchor="middle" fill="#ffffff" font-family="Segoe UI, Roboto, sans-serif" font-size="12" font-weight="700">INDEXACIÓN (offline)</text>',
            _draw_box(30, 58, 120, 54, ["Documentos"], "#38bdf8"),
            _draw_arrow(150, 85, 178, 85),
            _draw_box(178, 58, 110, 54, ["Limpieza"], "#38bdf8"),
            _draw_arrow(288, 85, 316, 85),
            _draw_box(316, 58, 110, 54, ["Chunking"], "#38bdf8"),
            _draw_arrow(426, 85, 454, 85),
            _draw_box(454, 54, 220, 62, ["Embeddings", "(+ metadatos: fuente, fecha, sección)"], "#818cf8", "#1e293b", True, 13, 11),
            _draw_arrow(674, 85, 702, 85),
            _draw_box(702, 54, 205, 62, ["Base vectorial", "(+ índice BM25)"], "#34d399"),
            '<rect x="16" y="148" width="908" height="118" rx="10" fill="#0f172a" stroke="#334155" stroke-width="1.5"/>',
            '<rect x="30" y="158" width="165" height="24" rx="6" fill="#7c3aed"/>',
            '<text x="112" y="174" text-anchor="middle" fill="#ffffff" font-family="Segoe UI, Roboto, sans-serif" font-size="12" font-weight="700">CONSULTA (online)</text>',
            _draw_box(30, 192, 100, 56, ["Pregunta"], "#a78bfa"),
            _draw_arrow(130, 220, 152, 220, "#a78bfa", "arrow-violet"),
            _draw_box(152, 192, 115, 56, ["(reescritura)"], "#a78bfa"),
            _draw_arrow(267, 220, 289, 220, "#a78bfa", "arrow-violet"),
            _draw_box(289, 190, 205, 60, ["Búsqueda híbrida", "(vectorial + palabras clave)"], "#38bdf8", "#1e293b", True, 12, 11),
            _draw_arrow(494, 220, 516, 220, "#38bdf8", "arrow-sky"),
            _draw_box(516, 192, 100, 56, ["Reranking"], "#fbbf24"),
            _draw_arrow(616, 220, 638, 220, "#fbbf24", "arrow-amber"),
            _draw_box(638, 192, 120, 56, ["Top-k", "fragmentos"], "#fbbf24"),
            _draw_arrow(758, 220, 780, 220, "#34d399", "arrow-emerald"),
            _draw_box(780, 190, 130, 60, ["LLM responde", "CITANDO fuentes"], "#34d399", "#1e293b", True, 12, 11),
        ]
        return (
            "Diagrama SVG · Pipeline RAG (Indexación y Consulta)",
            _svg_wrap(940, 280, "Pipeline RAG: Indexación offline y Consulta online", "".join(els)),
        )

    # 14. 09-avanzado/03-rag-y-memoria-persistente (Block #14): Arquitectura de referencia
    if "Agente (Claude Code / OpenCode / propio)" in t and 'MCP "docs"' in t:
        els = [
            _draw_box(18, 62, 110, 48, ["Usuario"], "#38bdf8"),
            _draw_arrow(128, 86, 168, 86, "#38bdf8", "arrow-sky"),
            '<rect x="168" y="24" width="734" height="222" rx="12" fill="#0f172a" stroke="#38bdf8" stroke-width="2"/>',
            '<rect x="190" y="10" width="350" height="28" rx="8" fill="#0284c7"/>',
            '<text x="365" y="29" text-anchor="middle" fill="#ffffff" font-family="Segoe UI, Roboto, sans-serif" font-size="13" font-weight="700">Agente (Claude Code / OpenCode / propio)</text>',
            _draw_box(192, 50, 215, 42, ["Instrucciones (AGENTS.md)"], "#38bdf8"),
            _draw_box(425, 50, 120, 42, ["Skills"], "#818cf8"),
            _draw_box(563, 50, 315, 42, ["Búsqueda agéntica en el repo"], "#a78bfa"),
            _draw_ortho_arrow([(250, 92), (250, 124), (295, 124)], "#34d399", "arrow-emerald"),
            _draw_ortho_arrow([(250, 92), (250, 168), (295, 168)], "#fbbf24", "arrow-amber"),
            _draw_ortho_arrow([(250, 92), (250, 212), (295, 212)], "#38bdf8", "arrow-sky"),
            _draw_box(295, 104, 145, 38, ['MCP "docs"'], "#34d399", "#1e293b", True, 12, 11, 6, True),
            _draw_arrow(440, 123, 475, 123, "#34d399", "arrow-emerald"),
            _draw_box(475, 104, 403, 38, ["RAG sobre documentación (Chroma/pgvector)"], "#34d399", "#1e293b", False, 12, 12.5, 6),
            _draw_box(295, 148, 145, 38, ['MCP "memoria"'], "#fbbf24", "#1e293b", True, 12, 11, 6, True),
            _draw_arrow(440, 167, 475, 167, "#fbbf24", "arrow-amber"),
            _draw_box(475, 148, 403, 38, ["grafo/archivos de memoria del proyecto"], "#fbbf24", "#1e293b", False, 12, 12.5, 6),
            _draw_box(295, 192, 145, 38, ['MCP "tareas"'], "#38bdf8", "#1e293b", True, 12, 11, 6, True),
            _draw_arrow(440, 211, 475, 211, "#38bdf8", "arrow-sky"),
            _draw_box(475, 192, 403, 38, ["API del negocio"], "#38bdf8", "#1e293b", False, 12, 12.5, 6),
            _draw_ortho_arrow([(250, 246), (250, 276), (295, 276)], "#f472b6", "arrow-slate"),
            _draw_ortho_arrow([(250, 246), (250, 318), (295, 318)], "#2dd4bf", "arrow-slate"),
            _draw_box(295, 258, 450, 36, ["trazas y métricas (OTel) → observabilidad (09.2)"], "#f472b6", "#1e293b", False, 12, 12.5, 6),
            _draw_box(295, 300, 450, 36, ["ejecución aislada (09.1)"], "#2dd4bf", "#1e293b", False, 12, 12.5, 6),
        ]
        return (
            "Diagrama SVG · Arquitectura de Referencia: Agente con RAG y Memoria",
            _svg_wrap(920, 350, "Arquitectura de referencia: Usuario, Agente, MCP docs/memoria/tareas, OTel y ejecución aislada", "".join(els)),
        )

    return None


def convert_diagram_block_if_applicable(clean_text: str) -> tuple[str, str] | None:
    """
    Evalúa si el texto de un bloque <pre> corresponde a un diagrama
    (arquitectura/flujo o estructura de directorios) y devuelve (header_title, svg_html).
    """
    custom = render_custom_flow_svg(clean_text)
    if custom is not None:
        return custom
    if "├──" in clean_text or "└──" in clean_text:
        return render_tree_svg(clean_text)
    return None



def build_sidebar_html(current_html_rel: Path, grouped_docs: dict) -> str:
    """
    Construye el menú lateral (Sidebar) agrupando los archivos por carpeta,
    con enlaces relativos desde `current_html_rel` y clase `.active` en el archivo actual.
    """
    current_dir = current_html_rel.parent
    sidebar_parts = []

    for group_idx, (folder_key, items) in enumerate(grouped_docs.items()):
        folder_label = FOLDER_LABELS.get(folder_key, folder_key)
        collapse_id = f"submenu-{slugify_heading(folder_key)}-{group_idx}"

        # Determinar si este grupo contiene la página activa
        is_group_active = any(item["html_rel"] == current_html_rel for item in items)
        # Mantener expandido el grupo activo y los grupos principales para facilitar la navegación
        expanded_attr = "true"
        show_class = "show"

        sidebar_parts.append(f'<div class="sidebar-group mb-2">')
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

            # Etiqueta descriptiva limpia
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
    """Construye el documento HTML5 completo con diseño Bootstrap 5 y UX responsive."""
    current_dir = current_html_rel.parent
    root_readme_href = os.path.relpath(Path("README.html"), start=current_dir).replace("\\", "/")
    ruta_href = os.path.relpath(Path("00-ruta-de-aprendizaje.html"), start=current_dir).replace("\\", "/")

    # Breadcrumbs
    parts = current_html_rel.parts
    breadcrumb_items = [
        f'<li class="breadcrumb-item"><a href="{root_readme_href}" class="text-decoration-none">Inicio</a></li>'
    ]
    if len(parts) > 1:
        for p in parts[:-1]:
            breadcrumb_items.append(f'<li class="breadcrumb-item text-muted">{p}</li>')
    breadcrumb_items.append(
        f'<li class="breadcrumb-item active fw-semibold" aria-current="page">{parts[-1]}</li>'
    )
    breadcrumb_html = "\n".join(breadcrumb_items)

    # Navegación inferior Anterior / Siguiente
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
  <title>{safe_title} — Documentación Desarrollo IA</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
  <style>
    :root {{
      --sidebar-width: 310px;
      --navbar-height: 58px;
      --brand-primary: #0d6efd;
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

    /* Top Navbar */
    .doc-navbar {{
      height: var(--navbar-height);
      background-color: var(--brand-dark);
      z-index: 1040;
    }}

    /* Sidebar fija en escritorio */
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

    /* Contenedor principal con margen izquierdo para la sidebar */
    .doc-main {{
      margin-left: var(--sidebar-width);
      transition: margin-left 0.25s ease;
      min-height: calc(100vh - var(--navbar-height));
    }}

    body.sidebar-collapsed .doc-main {{
      margin-left: 0;
    }}

    /* Estilos del menú lateral */
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
      background-color: #e0f2fe;
      color: #0369a1;
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
      color: #0d6efd !important;
      background-color: #eff6ff !important;
      border-left-color: #0d6efd;
      font-weight: 600;
    }}

    /* Contenido del documento */
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
      border-left: 4px solid #0d6efd;
      background-color: #f8fafc;
      padding: 0.9rem 1.15rem;
      border-radius: 0 0.5rem 0.5rem 0;
      font-size: 0.95rem;
      color: #334155;
    }}

    .doc-blockquote p:last-child {{
      margin-bottom: 0;
    }}

    /* Bloques de código y resaltado de sintaxis */
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

    /* Diagramas Vectoriales SVG */
    .diagram-wrapper {{
      background-color: #0f172a;
      color: #e2e8f0;
      border: 1px solid #334155;
      overflow: hidden;
    }}

    .diagram-header {{
      background-color: #1e293b;
      color: #94a3b8;
      border-color: #334155 !important;
    }}

    .diagram-svg-body {{
      padding: 1.25rem 1rem;
      overflow-x: auto;
      text-align: center;
      background: radial-gradient(circle at top, #1e293b 0%, #0f172a 100%);
    }}

    .diagram-svg-body svg {{
      max-width: 100%;
      height: auto;
      display: block;
      margin: 0 auto;
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
      color: #0d6efd;
      text-decoration: underline;
    }}

    /* Responsive: en dispositivos móviles la sidebar pasa a posición relativa/apilada y el contenido ocupa 100% */
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

  <!-- Barra de navegación superior fija (fixed-top) -->
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
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="#38bdf8" viewBox="0 0 16 16" aria-hidden="true">
            <path d="M6 12.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5ZM3 8.062C3 6.76 4.235 5.765 5.53 5.886a26.58 26.58 0 0 0 4.94 0C11.765 5.765 13 6.76 13 8.062v1.157a.933.933 0 0 1-.765.935c-.845.147-2.34.346-4.235.346-1.895 0-3.39-.2-4.235-.346A.933.933 0 0 1 3 9.219V8.062Zm4.542-.827a.25.25 0 0 0-.217.068l-.92.9a24.767 24.767 0 0 1-1.871-.183.25.25 0 0 0-.068.495c.55.076 1.232.149 2.02.193a.25.25 0 0 0 .189-.071l.754-.736.847 1.71a.25.25 0 0 0 .404.062l.932-.97a25.286 25.286 0 0 0 1.922-.188.25.25 0 0 0-.068-.495c-.538.074-1.207.145-1.98.189a.25.25 0 0 0-.166.076l-.754.785-.842-1.7a.25.25 0 0 0-.182-.135Z"/>
            <path d="M8.5 1.866a1 1 0 1 0-1 0V3h-2A4.5 4.5 0 0 0 1 7.5V8a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1v-.5A4.5 4.5 0 0 0 10.5 3h-2V1.866ZM14 7.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7.5A3.5 3.5 0 0 1 5.5 4h5A3.5 3.5 0 0 1 14 7.5Z"/>
          </svg>
          <span>Desarrollo Agéntico con IA</span>
        </a>
      </div>
      <div class="d-flex align-items-center gap-2">
        <a href="{ruta_href}" class="btn btn-sm btn-outline-info d-none d-md-inline-block">Ruta de aprendizaje</a>
        <span class="badge bg-primary-subtle text-primary-emphasis border border-primary-subtle">{current_html_rel.as_posix()}</span>
      </div>
    </div>
  </nav>

  <!-- Barra lateral fija (Sidebar) -->
  <aside class="doc-sidebar shadow-sm p-3" id="docSidebar" aria-label="Navegación de documentación">
    <div class="mb-3">
      <div class="input-group input-group-sm">
        <span class="input-group-text bg-light border-end-0">
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="currentColor" viewBox="0 0 16 16" aria-hidden="true">
            <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
          </svg>
        </span>
        <input type="search" id="sidebarFilter" class="form-control bg-light border-start-0" placeholder="Filtrar documentos..." aria-label="Filtrar documentos">
      </div>
    </div>
    <nav id="sidebarNav">
      {sidebar_html}
    </nav>
  </aside>

  <!-- Contenedor principal de contenido -->
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
        Sitio de documentación generado automáticamente &middot; Bootstrap 5 &middot; Cero pérdida de contenido
      </footer>
    </div>
  </main>

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
  <script>
    document.addEventListener('DOMContentLoaded', function () {{
      // 1. Botón Toggle para ocultar/mostrar la barra lateral
      const toggleBtn = document.getElementById('sidebarToggle');
      if (toggleBtn) {{
        toggleBtn.addEventListener('click', function () {{
          document.body.classList.toggle('sidebar-collapsed');
        }});
      }}

      // 2. Detectar URL actual dinámicamente y aplicar clase .active al enlace correspondiente
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

      // 3. Filtro rápido en barra lateral
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
    """
    Verifica que la carpeta dist_html contiene todos los archivos HTML esperados,
    que la estructura espejo coincide y que ningún enlace interno está roto.
    """
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

        # Verificar todos los href en el HTML generado
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
                    target_rel_key = str(target_path.relative_to(DIST_DIR.resolve()).with_suffix(".md")).replace("\\", "/")
                    target_ids = all_heading_ids.get(target_rel_key, set())
                    if target_ids and frag_part not in target_ids:
                        broken_anchors.append((str(html_rel), href))
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


def upgrade_existing_html_diagrams(dist_dir: Path) -> None:
    """
    Actualiza in-place todos los archivos HTML en dist_html:
    1. Actualiza el bloque CSS de diagramas a la versión SVG vectorial.
    2. Desenvuelve antiguos bloques .diagram-wrapper con <pre> (restaurando bloques de código reales).
    3. Identifica todos los diagramas (arquitectura, flujo y estructura de directorios) y los reemplaza
       por diagramas vectoriales <svg> sin perder ninguna información.
    """
    old_css_pattern = re.compile(
        r"/\*\s*Diagramas (?:ASCII / Unicode|Vectoriales SVG)\s*\*/.*?\.diagram-wrapper\s+(?:pre|\.diagram-svg-body\s+svg)\s*\{[^}]*\}",
        flags=re.DOTALL,
    )
    new_css_block = """/* Diagramas Vectoriales SVG */
    .diagram-wrapper {
      background-color: #0f172a;
      color: #e2e8f0;
      border: 1px solid #334155;
      overflow: hidden;
    }

    .diagram-header {
      background-color: #1e293b;
      color: #94a3b8;
      border-color: #334155 !important;
    }

    .diagram-svg-body {
      padding: 1.25rem 1rem;
      overflow-x: auto;
      text-align: center;
      background: radial-gradient(circle at top, #1e293b 0%, #0f172a 100%);
    }

    .diagram-svg-body svg {
      max-width: 100%;
      height: auto;
      display: block;
      margin: 0 auto;
    }"""

    old_wrapper_re = re.compile(
        r'<div class="diagram-wrapper[^"]*">\s*<div class="diagram-header[^"]*">.*?</div>\s*(<div class="codehilite"><pre>.*?</pre></div>|<pre>.*?</pre>)\s*</div>',
        flags=re.DOTALL,
    )
    svg_wrapper_re = re.compile(
        r'<div class="diagram-wrapper[^"]*"\s+data-diagram-source="([^"]*)">\s*<div class="diagram-header[^"]*">.*?</div>\s*<div class="diagram-svg-body">.*?</div>\s*</div>',
        flags=re.DOTALL,
    )

    files_modified = []
    total_svgs = 0

    for html_path in sorted(dist_dir.rglob("*.html")):
        content = html_path.read_text(encoding="utf-8")
        # 1. Actualizar CSS
        content = old_css_pattern.sub(new_css_block, content)
        # 2. Desenvolver antiguos wrappers ASCII/pre o SVG previos si existen
        content = old_wrapper_re.sub(r"\1", content)
        content = svg_wrapper_re.sub(
            lambda m: f"<pre><code>{m.group(1)}</code></pre>", content
        )

        file_svgs = 0

        def replace_pre_with_svg(match):
            nonlocal file_svgs
            block = match.group(0)
            clean_text = html.unescape(re.sub(r"<[^>]+>", "", block)).strip()
            svg_result = convert_diagram_block_if_applicable(clean_text)
            if svg_result is not None:
                file_svgs += 1
                header_title, svg_markup = svg_result
                svg_badge = (
                    '<div class="diagram-header d-flex align-items-center justify-content-between px-3 py-1 border-bottom">'
                    '<span class="d-flex align-items-center gap-2">'
                    '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="#38bdf8" viewBox="0 0 16 16" aria-hidden="true">'
                    '<path fill-rule="evenodd" d="M6 3.5A1.5 1.5 0 0 1 7.5 2h1A1.5 1.5 0 0 1 10 3.5v1A1.5 1.5 0 0 1 8.5 6v1H14a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0v-1A.5.5 0 0 1 2 7h5.5V6A1.5 1.5 0 0 1 6 4.5v-1z"/>'
                    '<path d="M1 11.5A1.5 1.5 0 0 1 2.5 10h1A1.5 1.5 0 0 1 5 11.5v1A1.5 1.5 0 0 1 3.5 14h-1A1.5 1.5 0 0 1 1 12.5v-1zm5 0A1.5 1.5 0 0 1 7.5 10h1a1.5 1.5 0 0 1 1.5 1.5v1A1.5 1.5 0 0 1 8.5 14h-1A1.5 1.5 0 0 1 6 12.5v-1zm5 0a1.5 1.5 0 0 1 1.5-1.5h1a1.5 1.5 0 0 1 1.5 1.5v1a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5v-1z"/>'
                    "</svg>"
                    f'<span class="small fw-semibold text-uppercase">{html.escape(header_title)}</span>'
                    "</span>"
                    '<span class="badge bg-info-subtle text-info-emphasis border border-info-subtle" style="font-size:0.68rem;">SVG</span>'
                    "</div>"
                )
                return (
                    f'<div class="diagram-wrapper shadow-sm rounded-3 my-3" data-diagram-source="{_esc_svg(clean_text)}">'
                    f"{svg_badge}"
                    f'<div class="diagram-svg-body">{svg_markup}</div>'
                    f"</div>"
                )
            return block

        content = re.sub(
            r'<div class="codehilite"><pre>.*?</pre></div>|<pre>.*?</pre>',
            replace_pre_with_svg,
            content,
            flags=re.DOTALL,
        )
        html_path.write_text(content, encoding="utf-8", newline="\n")

        if file_svgs > 0:
            rel_p = html_path.relative_to(dist_dir).as_posix()
            files_modified.append((rel_p, file_svgs))
            total_svgs += file_svgs

    print(f"[*] Archivos HTML con diagramas convertidos a SVG: {len(files_modified)}")
    print(f"[*] Total de diagramas SVG generados             : {total_svgs}")
    for rel_p, count in files_modified:
        print(f"    - {rel_p} ({count} diagrama{'s' if count > 1 else ''} SVG)")


def main():
    print("=" * 72)
    print(" GENERADOR DE DOCUMENTACIÓN TÉCNICA (MARKDOWN -> HTML BOOTSTRAP 5)")
    print("=" * 72)

    if (not HAS_MARKDOWN or "--svg-only" in sys.argv) and DIST_DIR.exists():
        upgrade_existing_html_diagrams(DIST_DIR)
        return

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    md_files, other_files = discover_files(ROOT_DIR)
    print(f"[*] Archivos Markdown detectados : {len(md_files)}")
    print(f"[*] Archivos auxiliares/plantilla: {len(other_files)}")

    # Copiar archivos auxiliares (JSON, TS, PY en plantillas/) manteniendo la estructura espejo
    for asset_rel in other_files:
        src = ROOT_DIR / asset_rel
        dst = DIST_DIR / asset_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    # Preparar metadatos de documentos y agrupación por carpeta para el Sidebar
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

    # Convertir cada archivo Markdown a HTML
    for idx, doc in enumerate(docs_info):
        md_rel = doc["md_rel"]
        html_rel = doc["html_rel"]
        out_path = DIST_DIR / html_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)

        preprocessed = preprocess_markdown(doc["raw_text"])

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

        processed_html, md_fixed, anc_fixed = postprocess_html(
            raw_html, md_rel, all_heading_ids
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

    # Ejecutar validación final
    report = validate_output(md_files, other_files, all_heading_ids)

    print("\n" + "-" * 72)
    print(" RESUMEN DE CONVERSIÓN Y VALIDACIÓN")
    print("-" * 72)
    print(f" [OK] Carpeta destino            : {DIST_DIR}")
    print(f" [OK] Archivos MD convertidos    : {report['found_html']} / {report['expected_html']}")
    print(f" [OK] Archivos auxiliares espejo : {len(other_files) - len(report['missing_assets'])} / {len(other_files)}")
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
