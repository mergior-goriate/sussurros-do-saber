from flask import Flask, Response, g, jsonify, redirect, render_template, request, session, url_for
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from xml.sax.saxutils import escape
import requests
import gzip
import hashlib
import os
import re
import secrets
import time
from functools import lru_cache
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from html import escape as html_escape, unescape as html_unescape
from urllib.parse import parse_qs, quote, unquote, urlparse
import bleach
import click
import markdown
from article_notes import render_notes_markdown, allowed_markdown_attribute, decorate_notes
import math
from markupsafe import Markup
from sqlalchemy import case, inspect, or_, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import load_only
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import safe_join
from journal_article import ARTICLE_FIELD_LIMITS, structured_article_content
from journal_metadata import journal_authors
from scientific_search import metadata_match, doi_url
from clarity_tracking import project_id as clarity_project_id
from smart_search import article_search
from editorial_content import DROP_CAP_MARKER, DROP_CAP_PATTERN, prepare_guidelines
from admin import admin_bp, login_required, slugify, validate_csrf
from extensions import limiter
from request_values import DatabaseIdConverter, pagination_page
from models import AdminUser, Article, Author, Category, Comment, ContactMessage, Journal, Subscriber, EditorialPolicy, db, utcnow

app = Flask(__name__)
app.jinja_env.globals["drop_cap_pattern"] = DROP_CAP_PATTERN
app.jinja_env.filters['doi_url'] = doi_url
app.url_map.converters['int'] = DatabaseIdConverter
def trusted_proxy_hops(name, default):
    value = int(os.getenv(name, str(default)))
    if not 0 <= value <= 5:
        raise RuntimeError(f"{name} deve estar entre 0 e 5.")
    return value


app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=trusted_proxy_hops("PROXY_FIX_X_FOR", 1),
    x_proto=trusted_proxy_hops("PROXY_FIX_X_PROTO", 1),
    x_host=trusted_proxy_hops("PROXY_FIX_X_HOST", 0),
)
with open(os.path.join(app.static_folder, 'css', 'tailwind.css'), 'rb') as built_css:
    TAILWIND_VERSION = hashlib.sha256(built_css.read()).hexdigest()[:12]


@lru_cache(maxsize=512)
def _static_digest(path, modified, size):
    with open(path, 'rb') as asset:
        return hashlib.sha256(asset.read()).hexdigest()[:16]


def static_asset_version(filename):
    path = safe_join(app.static_folder, filename)
    if path:
        try:
            stat = os.stat(path)
            if os.path.isfile(path):
                return _static_digest(path, stat.st_mtime_ns, stat.st_size)
        except OSError:
            pass
    return None


@app.url_defaults
def version_static_urls(endpoint, values):
    if endpoint == 'static' and isinstance(values.get('filename'), str):
        version = static_asset_version(values['filename'])
        if version:
            values['v'] = version

IS_PRODUCTION = (
    os.getenv("RENDER", "").lower() == "true"
    or os.getenv("FLASK_ENV", "").lower() == "production"
)
DEVELOPMENT_SECRET_KEY = "local-development-only-change-me"
secret_key = os.getenv("SECRET_KEY", "").strip()
if IS_PRODUCTION and (not secret_key or secret_key == DEVELOPMENT_SECRET_KEY):
    raise RuntimeError("SECRET_KEY forte e exclusiva é obrigatória em produção.")
if not secret_key:
    secret_key = DEVELOPMENT_SECRET_KEY

database_url = os.getenv("DATABASE_URL", "sqlite:///sussurros.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config.update(
    SQLALCHEMY_DATABASE_URI=database_url,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=secret_key,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=IS_PRODUCTION or os.getenv("SESSION_COOKIE_SECURE", "").lower() == "true",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
    SESSION_REFRESH_EACH_REQUEST=False,
    MAX_CONTENT_LENGTH=60 * 1024 * 1024,
    BOOTSTRAP_ON_STARTUP=os.getenv("BOOTSTRAP_ON_STARTUP", "true").lower() == "true",
    PUBLISH_SCHEDULED_ON_REQUEST=os.getenv("PUBLISH_SCHEDULED_ON_REQUEST", "true").lower() == "true",
)
CANONICAL_ORIGIN = "https://www.sussurrosdosaber.com"
_configured_site_url = os.getenv("SITE_URL", CANONICAL_ORIGIN).rstrip("/")
_configured_host = (urlparse(_configured_site_url).hostname or "").lower()
# A origem pública oficial usa www. Normalize também configurações antigas do Render
# para impedir que canonical, Open Graph, sitemap e dados estruturados divirjam.
SITE_URL = CANONICAL_ORIGIN if _configured_host == "sussurrosdosaber.com" else _configured_site_url

db.init_app(app)
limiter.init_app(app)
from submissions import submissions_bp, install_submission_cli
from governance import staff_bp, public_team_bp, install_staff_cli
app.register_blueprint(staff_bp)
app.register_blueprint(public_team_bp)
install_staff_cli(app)
from news import news_bp
import news_admin  # Register the news routes on the existing admin blueprint.
from videos import videos_bp
import video_admin  # Register editorial routes on the existing admin blueprint.
import automation.admin
from automation.engine import install_cli as install_automation_cli
install_automation_cli(app)
app.register_blueprint(admin_bp)
app.register_blueprint(news_bp)
app.config["SCIENCE_VIDEO_SITE_URL"] = SITE_URL
app.register_blueprint(videos_bp)
from article_history import history_bp
app.register_blueprint(history_bp)
app.register_blueprint(submissions_bp)
from reader_accounts import reader_bp
app.register_blueprint(reader_bp)
from premium import premium_bp, premium_admin_bp
app.register_blueprint(premium_bp)
app.register_blueprint(premium_admin_bp)
from billing import billing_bp, finance_bp, install_billing_cli
app.register_blueprint(billing_bp)
app.register_blueprint(finance_bp)
from scientific_metrics import metrics_bp, register_cli as register_metrics_cli
app.register_blueprint(metrics_bp)
register_metrics_cli(app)
from dissemination import centre_bp, tracking_bp, register_cli as register_dissemination_cli
from dissemination import access as dissemination_access, can as dissemination_can
from dissemination_video import install as install_video
app.config['DISSEMINATION_SITE_URL'] = SITE_URL
install_video(app,centre_bp,dissemination_access,dissemination_can)
app.register_blueprint(centre_bp)
app.register_blueprint(tracking_bp)
register_dissemination_cli(app)
from translation_admin import translations_bp, register_cli as register_translation_cli
app.register_blueprint(translations_bp)
register_translation_cli(app)
install_billing_cli(app)
install_submission_cli(app)
from google_auth import google_bp, install_google_cli
app.register_blueprint(google_bp)
install_google_cli(app)
from newsletter_service import install_newsletter
install_newsletter(app)


@app.get("/diretrizes-para-autores")
def author_guidelines():
    from internationalization import ui
    policy = EditorialPolicy.query.first()
    custom_content = (policy.author_guidelines or "").strip() if policy else ""
    content = render_markdown(ui(custom_content)) if custom_content else render_template("partials/author_guidelines_default.html")
    guidelines_content, manuscript_types_id = prepare_guidelines(content)
    return render_template("author_guidelines.html", policy=policy, guidelines_content=guidelines_content,
                           manuscript_types_id=manuscript_types_id)


@app.get("/790c8a9d2960414f923b2ccf49e86d72.txt")
@limiter.exempt
def indexnow_key():
    """Disponibiliza a chave de verificação IndexNow na raiz pública."""
    with open(os.path.join(app.root_path, "790c8a9d2960414f923b2ccf49e86d72.txt"), encoding="utf-8") as key_file:
        return Response(
            key_file.read(),
            mimetype="text/plain",
            headers={"Cache-Control": "public, max-age=3600"},
        )


@app.get("/favicon.ico")
@limiter.exempt
def favicon():
    """Serve the institutional icon at the conventional discovery URL."""
    response = app.send_static_file("icons/favicon.ico")
    response.headers["Cache-Control"] = "public, no-cache, max-age=0, must-revalidate"
    return response


@app.get("/ads.txt")
def ads_txt():
    """Publica a declaração Authorized Digital Sellers do Google AdSense."""
    return Response(
        "google.com, pub-7920973591685812, DIRECT, f08c47fec0942fa0\n",
        status=200,
        mimetype="text/plain",
        headers={"Cache-Control": "public, max-age=3600"},
    )

@app.before_request
def publish_due_scheduled_articles():
    """Publica aprovações pendentes e agendamentos cujo horário já chegou."""
    if not app.config["PUBLISH_SCHEDULED_ON_REQUEST"]:
        return
    if request.endpoint != "static" and request.path not in {"/favicon.ico", "/healthz", "/ads.txt", "/robots.txt", "/790c8a9d2960414f923b2ccf49e86d72.txt"}:
        Article.publish_due_scheduled()


@app.before_request
def assign_csp_nonce():
    """Cria um nonce imprevisível e exclusivo para cada resposta."""
    g.csp_nonce = secrets.token_urlsafe(24)


@app.before_request
def redirect_bare_domain_to_www():
    """Consolida sinais de indexação e ligações no único host canónico."""
    request_host = request.host.split(":", 1)[0].lower()
    if request_host == "sussurrosdosaber.com":
        target = CANONICAL_ORIGIN + request.full_path
        return redirect(target.rstrip("?"), code=308)
    return None


IMAGE_DIRECTIVE = re.compile(r"!\[([^\]]*)\]\((https?://[^\s)]+)\)", re.I)
VIDEO_DIRECTIVE = re.compile(r"^\[video:\s*([^\]]*)\]\((https?://[^\s)]+)\)\s*$", re.I | re.M)
CHART_DIRECTIVE = re.compile(r"^\[chart:\s*(bar|line|pie)\|([^\]\n]{1,180})\|([^\]\n]{1,1200})\]\s*$", re.I | re.M)


def safe_video_embed(url, title):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    label = (title or "Vídeo incorporado").strip()[:180]
    embed_url = None
    if host in {"youtube.com", "m.youtube.com", "youtube-nocookie.com"}:
        video_id = parsed.path.split("/embed/", 1)[1].split("/", 1)[0] if "/embed/" in parsed.path else parse_qs(parsed.query).get("v", [""])[0]
        if re.fullmatch(r"[A-Za-z0-9_-]{6,20}", video_id):
            embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}"
    elif host == "youtu.be":
        video_id = parsed.path.strip("/").split("/", 1)[0]
        if re.fullmatch(r"[A-Za-z0-9_-]{6,20}", video_id):
            embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}"
    elif host in {"vimeo.com", "player.vimeo.com"}:
        match = re.search(r"(?:video/)?(\d{5,12})", parsed.path)
        if match:
            embed_url = f"https://player.vimeo.com/video/{match.group(1)}"

    safe_label = html_escape(label, quote=True)
    if embed_url:
        return (
            '<figure class="article-video"><div class="article-video-frame">'
            f'<iframe src="{embed_url}" title="{safe_label}" loading="lazy" '
            'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
            'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>'
            f'<figcaption>{safe_label}</figcaption></figure>'
        )
    if parsed.scheme in {"http", "https"} and parsed.path.lower().endswith((".mp4", ".webm", ".ogg")):
        safe_url = html_escape(url, quote=True)
        return (
            f'<figure class="article-video"><video controls preload="metadata" aria-label="{safe_label}">'
            f'<source src="{safe_url}">O navegador não suporta este vídeo.</video>'
            f'<figcaption>{safe_label}</figcaption></figure>'
        )
    return None


from cover_media import native_video_url, cover_delivery_url
app.add_template_filter(native_video_url, "native_cover_video")
app.add_template_filter(cover_delivery_url, "cover_delivery_url")


@app.template_filter("article_cover_video")
def article_cover_video(url, title):
    try:
        parsed = urlparse(url or "")
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
            return Markup("")
        return Markup(safe_video_embed(url, title) or "")
    except ValueError:
        return Markup("")


def safe_chart_embed(chart_type, title, raw_data):
    chart_type = chart_type.lower()
    title = (title or "Gráfico").strip()[:180]
    points = []
    for item in raw_data.split(";")[:12]:
        if "=" not in item:
            continue
        label, raw_value = item.rsplit("=", 1)
        label = label.strip()[:40]
        try:
            value = float(raw_value.strip().replace(",", "."))
        except ValueError:
            continue
        if label and math.isfinite(value) and value >= 0:
            points.append((label, value))
    if not points or max(value for _, value in points) <= 0:
        return None

    safe_title = html_escape(title, quote=True)
    colours = ["#087f72", "#e85d4a", "#2f6db0", "#d69e2e", "#805ad5", "#319795",
               "#c05621", "#4a5568", "#38a169", "#b83280", "#718096", "#dd6b20"]
    svg = [f'<svg viewBox="0 0 800 440" role="img" aria-label="{safe_title}">',
           f"<title>{safe_title}</title>", '<rect width="800" height="440" fill="#fff"/>']

    if chart_type in {"bar", "line"}:
        maximum = max(value for _, value in points)
        left, top, width, height = 80, 45, 680, 285
        svg.extend([
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + height}" class="chart-axis"/>',
            f'<line x1="{left}" y1="{top + height}" x2="{left + width}" y2="{top + height}" class="chart-axis"/>',
        ])
        for tick in range(5):
            value = maximum * tick / 4
            y = top + height - (height * tick / 4)
            svg.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + width}" y2="{y:.1f}" class="chart-grid"/>')
            svg.append(f'<text x="{left - 10}" y="{y + 5:.1f}" text-anchor="end" class="chart-value">{value:g}</text>')
        step = width / len(points)
        if chart_type == "bar":
            bar_width = min(58, step * .65)
            for index, (label, value) in enumerate(points):
                x = left + index * step + (step - bar_width) / 2
                bar_height = height * value / maximum
                y = top + height - bar_height
                safe_label = html_escape(label)
                svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" rx="5" fill="{colours[index % len(colours)]}"/>')
                svg.append(f'<text x="{x + bar_width / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" class="chart-value">{value:g}</text>')
                svg.append(f'<text x="{x + bar_width / 2:.1f}" y="{top + height + 24}" text-anchor="middle" class="chart-label">{safe_label}</text>')
        else:
            coords = []
            for index, (label, value) in enumerate(points):
                x = left + (width / max(1, len(points) - 1)) * index
                y = top + height - height * value / maximum
                coords.append(f"{x:.1f},{y:.1f}")
                safe_label = html_escape(label)
                svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{colours[index % len(colours)]}"/>')
                svg.append(f'<text x="{x:.1f}" y="{y - 12:.1f}" text-anchor="middle" class="chart-value">{value:g}</text>')
                svg.append(f'<text x="{x:.1f}" y="{top + height + 24}" text-anchor="middle" class="chart-label">{safe_label}</text>')
            svg.insert(-len(points) * 3, f'<polyline points="{" ".join(coords)}" class="chart-line"/>')
    else:
        total = sum(value for _, value in points)
        cx, cy, radius = 275, 220, 145
        start = -math.pi / 2
        if len(points) == 1:
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{colours[0]}"/>')
        else:
            for index, (_, value) in enumerate(points):
                end = start + 2 * math.pi * value / total
                x1, y1 = cx + radius * math.cos(start), cy + radius * math.sin(start)
                x2, y2 = cx + radius * math.cos(end), cy + radius * math.sin(end)
                large = 1 if end - start > math.pi else 0
                svg.append(f'<path d="M {cx} {cy} L {x1:.2f} {y1:.2f} A {radius} {radius} 0 {large} 1 {x2:.2f} {y2:.2f} Z" fill="{colours[index % len(colours)]}"/>')
                start = end
        for index, (label, value) in enumerate(points):
            safe_label = html_escape(label)
            percent = value / total * 100
            y = 75 + index * 27
            svg.append(f'<rect x="500" y="{y - 13}" width="16" height="16" rx="3" fill="{colours[index % len(colours)]}"/>')
            svg.append(f'<text x="526" y="{y}" class="chart-legend">{safe_label}: {value:g} ({percent:.1f}%)</text>')

    svg.append("</svg>")
    return (
        '<figure class="article-chart">'
        + "".join(svg)
        + f"<figcaption>{safe_title}</figcaption></figure>"
    )


@app.template_filter("markdown")
def render_markdown(value, *, article=False, heading_prefix="sec"):
    embeds = {}

    def store_embed(prefix, embed):
        token = f"{prefix}EMBEDTOKEN{len(embeds)}"
        embeds[token] = embed
        return token

    def image_placeholder(match):
        parsed = urlparse(match.group(2))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return match.group(0)
        source_url = match.group(2)
        safe_url = html_escape(responsive_image_url(source_url, 1200), quote=True)
        safe_small = html_escape(responsive_image_url(source_url, 480), quote=True)
        safe_medium = html_escape(responsive_image_url(source_url, 768), quote=True)
        safe_alt = html_escape((match.group(1) or "").strip(), quote=True)
        image = (
            '<figure class="article-inline-image">'
            f'<img src="{safe_url}" srcset="{safe_small} 480w, {safe_medium} 768w, {safe_url} 1200w" '
            f'sizes="(max-width: 760px) 100vw, 760px" alt="{safe_alt}" loading="lazy" decoding="async">'
            '</figure>'
        )
        return store_embed("IMAGE", image)

    def video_placeholder(match):
        embed = safe_video_embed(match.group(2), match.group(1))
        return store_embed("VIDEO", embed) if embed else match.group(0)

    def chart_placeholder(match):
        embed = safe_chart_embed(match.group(1), match.group(2), match.group(3))
        return store_embed("CHART", embed) if embed else match.group(0)

    def pullquote_placeholder(match):
        text, _, author = match.group(1).partition("|")
        return store_embed("PULLQUOTE", '<figure class="article-pullquote">'
                           f'<blockquote><p>{html_escape(text.strip())}</p></blockquote>'
                           f'<figcaption>{html_escape(author.strip())}</figcaption></figure>')

    def portrait_placeholder(match):
        parts = match.group(1).split("|", 2)
        parts += [""] * (3 - len(parts))
        alt, caption, credit = [html_escape(part.strip(), quote=True) for part in parts]
        url = match.group(2)
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return match.group(0)
        safe_url = html_escape(responsive_image_url(url, 768), quote=True)
        return store_embed("PORTRAIT", '<figure class="article-portrait">'
                           f'<img src="{safe_url}" alt="{alt}" loading="lazy" decoding="async">'
                           f'<figcaption>{caption}<small>{credit}</small></figcaption></figure>')

    from explanatory_boxes import prepare_explanatory_boxes
    value = prepare_explanatory_boxes(value, store_embed)
    prepared = re.sub(r"\[portrait:\s*([^\]\n]+)\]\((https?://[^\s)]+)\)",
                      portrait_placeholder, value or "", flags=re.I)
    prepared = re.sub(r"^\[destaque:\s*([^\]\n]+)\]\s*$",
                      pullquote_placeholder, prepared, flags=re.M)
    prepared = IMAGE_DIRECTIVE.sub(image_placeholder, prepared)
    prepared = VIDEO_DIRECTIVE.sub(video_placeholder, prepared)
    prepared = CHART_DIRECTIVE.sub(chart_placeholder, prepared)
    rendered, note_info = render_notes_markdown(prepared, strict_headings=article)
    if note_info['notes']:
        rendered = rendered.replace('&#160;', '\u00a0').replace('&nbsp;', '\u00a0')
    # Torna URLs HTTP(S) escritas como texto em links clicáveis, sem alterar
    # URLs que já estejam dentro de atributos HTML ou links Markdown.
    url_pattern = re.compile(r'''(?<!["'=])(https?://[^\s<]+)''', re.I)
    parts = re.split(r'(<[^>]+>)', rendered)
    inside_anchor = False
    code_depth = 0
    for index, part in enumerate(parts):
        if part.startswith("<"):
            if re.match(r'<(?:pre|code)\b', part, re.I):
                code_depth += 1
            elif re.match(r'</(?:pre|code)\s*>', part, re.I):
                code_depth = max(0, code_depth - 1)
            if re.match(r'<a\b', part, re.I):
                inside_anchor = True
            elif re.match(r'</a\s*>', part, re.I):
                inside_anchor = False
            continue
        if inside_anchor or code_depth:
            continue
        def linkify(match):
            raw = match.group(1)
            url = raw.rstrip('.,;:!?)]}')
            suffix = raw[len(url):]
            safe_url = html_escape(html_unescape(url), quote=True)
            safe_label = html_escape(html_unescape(url))
            return f'<a href="{safe_url}" rel="noopener noreferrer">{safe_label}</a>{html_escape(suffix)}'
        parts[index] = url_pattern.sub(linkify, part)
    rendered = "".join(parts)
    allowed = set(bleach.sanitizer.ALLOWED_TAGS).union({"p", "h1", "h2", "h3", "h4", "h5", "h6", "br", "blockquote", "pre", "code", "ul", "ol", "li", "hr", "table", "thead", "tbody", "tr", "th", "td", "img", "sup", "div"})
    cleaned = bleach.clean(
        rendered,
        tags=allowed,
        attributes=lambda tag,name,value: allowed_markdown_attribute(note_info,tag,name,value),
        protocols=["http", "https", "mailto"],
        strip=True,
    )
    cleaned = decorate_notes(cleaned, note_info)
    cleaned = re.sub(r"<p>" + DROP_CAP_MARKER + r"(?=\s|<)\s*", '<p class="article-dropcap">', cleaned)
    for token, embed in embeds.items():
        cleaned = cleaned.replace(f"<p>{token}</p>", embed).replace(token, embed)
    if article:
        from article_headings import prepare_article_headings
        cleaned = prepare_article_headings(cleaned, prefix=heading_prefix)
    return Markup(cleaned)


@app.template_filter("article_markdown")
def render_article_markdown(value, prefix="sec"):
    return render_markdown(value, article=True, heading_prefix=prefix)


@app.after_request
def security_headers(response):
    clarity_connect = ' https://*.clarity.ms https://c.bing.com' if clarity_project_id() else ''
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Content-Language", "pt-MZ")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'; "
        "object-src 'none'; img-src 'self' data: blob: https:; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://accounts.google.com/gsi/style; "
        f"script-src 'nonce-{getattr(g, 'csp_nonce', '')}' 'strict-dynamic' 'self' https:; "
        "script-src-attr 'none'; "
        f"frame-src https://challenges.cloudflare.com https://www.youtube-nocookie.com https://player.vimeo.com https://*.doubleclick.net https://*.googlesyndication.com https://*.google.com https://fundingchoicesmessages.google.com; media-src 'self' blob: https:; connect-src 'self' https://challenges.cloudflare.com https://*.google-analytics.com https://*.analytics.google.com https://*.googletagmanager.com https://*.googlesyndication.com https://*.doubleclick.net https://*.google.com https://fundingchoicesmessages.google.com{clarity_connect}; upgrade-insecure-requests",
    )
    if request.is_secure:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if request.path.startswith("/static/") or request.endpoint == "favicon":
        filename = (request.view_args or {}).get('filename', '')
        version = static_asset_version(filename) if filename else None
        if response.status_code == 200 and version and request.args.get('v') == version:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"] = "public, no-cache, max-age=0, must-revalidate"
    else:
        # Páginas de artigos contêm um token CSRF individual do formulário de
        # comentários e nunca podem ser guardadas por caches partilhadas.
        private_response = (
            request.method != "GET"
            or getattr(g, 'language', 'pt') == 'en'
            or request.path in {'/', '/idioma/pt', '/idioma/en'}
            or request.endpoint in {"news.index", "news.detail", "videos.index", "videos.detail"}
            or bool(response.headers.get('Set-Cookie'))
            or request.path.startswith(("/admin", "/api/", "/artigo/", "/submissoes"))
            or response.status_code >= 400
        )
        if private_response:
            response.headers["Cache-Control"] = "no-store"
        elif request.endpoint in {"home", "articles", "author_detail", "feed", "sitemap"}:
            # Revalidate lists on every visit so a publication is immediately visible.
            response.headers["Cache-Control"] = "public, no-cache, max-age=0, must-revalidate"
        elif not response.headers.get("Cache-Control"):
            response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    if request.path.startswith("/admin") or response.status_code >= 400:
        response.headers.setdefault("X-Robots-Tag", "noindex, nofollow")
    elif request.path in {"/favoritos", "/en/favoritos"} or request.endpoint == "favorites":
        response.headers.setdefault("X-Robots-Tag", "noindex, follow")

    compressible = {
        "text/html", "text/css", "text/plain", "text/xml",
        "application/json", "application/javascript", "text/javascript", "application/xml",
    }
    accepts_gzip = request.accept_encodings["gzip"] > 0
    eligible_for_compression = (
        request.method == "GET" and response.status_code == 200
        and not request.headers.get("Range")
        and response.mimetype in compressible
        and not response.headers.get("Content-Encoding")
    )
    if eligible_for_compression:
        response.vary.add("Accept-Encoding")
        # send_file uses direct passthrough; only materialize small text assets.
        if (accepts_gzip and response.direct_passthrough and request.endpoint == "static"
                and response.content_length is not None and response.content_length <= 1024 * 1024):
            response.direct_passthrough = False
    if (
        accepts_gzip
        and eligible_for_compression
        and not response.direct_passthrough
        and not response.headers.get("Content-Encoding")
        and response.mimetype in compressible
    ):
        payload = response.get_data()
        if len(payload) >= 1024:
            response.set_data(gzip.compress(payload, compresslevel=5))
            response.headers["Content-Encoding"] = "gzip"
            response.headers["Content-Length"] = len(response.get_data())
            etag, _ = response.get_etag()
            if etag:
                response.set_etag(etag + "-gzip", weak=True)
            response.vary.add("Accept-Encoding")
    return response


def google_site_verification_token():
    default_token = "MBbrCatBKLtKz2UmAJQsYlJ95ZEpNQ3CJvRMTo6aGwE"
    raw_value = os.getenv("GOOGLE_SITE_VERIFICATION", default_token).strip()
    content_match = re.search(
        r"""content\s*=\s*["']([^"']+)["']""",
        raw_value,
        re.I,
    )
    if content_match:
        raw_value = content_match.group(1)
    token = raw_value.strip().strip(chr(34) + chr(39))
    return token if re.fullmatch(r"[A-Za-z0-9_-]{20,}", token) else default_token


@app.context_processor
def site_context():
    return {
        "clarity_project_id": clarity_project_id(),
        "google_cmp_enabled": (
            os.getenv("GOOGLE_CMP_ENABLED", "false").strip().lower() == "true"
            and request.method == "GET"
            and (request.endpoint in {"home", "privacy", "advertising_policy"}
                 or getattr(g, "google_cmp_public_content", False))
        ),
        "site_url": SITE_URL,
        "google_login_client_id": __import__("google_auth").client_id(),
        "tailwind_version": TAILWIND_VERSION,
        "csp_nonce": getattr(g, "csp_nonce", ""),
        "google_site_verification": google_site_verification_token(),
        "gtm_container_id": os.getenv("GTM_CONTAINER_ID", "GTM-PQSZGPQQ").strip(),
        "social_links": {
            "facebook": os.getenv("SOCIAL_FACEBOOK_URL", "https://web.facebook.com/profile.php?id=61584597102517"),
            "instagram": os.getenv("SOCIAL_INSTAGRAM_URL", "https://www.instagram.com/sussurros_do_saber/"),
            "youtube": os.getenv("SOCIAL_YOUTUBE_URL", "https://www.youtube.com/channel/UCMxbh7jSRUxxX48JSWszc8g"),
            "linkedin": os.getenv("SOCIAL_LINKEDIN_URL", "").strip(),
            "x": os.getenv("SOCIAL_X_URL", "https://x.com/sussurrodosaber"),
            "whatsapp": os.getenv("SOCIAL_WHATSAPP_URL", "https://wa.me/258852130099"),
        },
    }


def cloudinary_cloud_name():
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
    if cloud_name:
        return cloud_name
    try:
        return urlparse(os.getenv("CLOUDINARY_URL", "").strip()).hostname or ""
    except ValueError:
        return ""


app.add_template_global(cloudinary_cloud_name, "cover_cloud_name")


@app.template_filter("safe_image_url")
def safe_image_url(url):
    """Normaliza URLs de imagem sem as encaminhar por proxies externos."""
    value = html_unescape(str(url or "")).strip().strip(chr(34) + chr(39))
    if value.startswith("//"):
        value = "https:" + value
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return value


@app.template_filter("image_variant")
def responsive_image_url(url, width=1200):
    """Otimiza imagens do Cloudinary e redimensiona raster do Wikimedia Commons.

    As outras imagens externas permanecem no endereço original. Encaminhá-las pelo
    image/fetch do Cloudinary fazia capas e imagens do corpo quebrarem quando
    o fetch remoto estava desativado ou a origem recusava o crawler.
    """
    value = safe_image_url(url)
    if not value:
        return ""
    try:
        requested_width = max(160, min(2000, int(width)))
    except (TypeError, ValueError):
        requested_width = 1200
    transformation = f"f_auto,q_auto:eco,w_{requested_width},c_limit"
    if "res.cloudinary.com/" in value and "/upload/" in value:
        return value.replace("/upload/", f"/upload/{transformation}/", 1)
    parsed = urlparse(value)
    if (
        parsed.hostname == "commons.wikimedia.org"
        and unquote(parsed.path).endswith("/E._coli_Bacteria_(7316101966).jpg")
    ):
        if requested_width <= 330:
            return "/static/img/e-coli-niaid-330.jpg?v=d52ba80e29c6"
        return "/static/img/e-coli-niaid-960.jpg?v=1a529a99b76b"
    if (
        parsed.hostname == "commons.wikimedia.org"
        and parsed.path.startswith("/wiki/Special:FilePath/")
        and re.search(r"\.(?:jpe?g|png|webp)$", parsed.path, re.I)
    ):
        filename = parsed.path.split("/wiki/Special:FilePath/", 1)[1]
        return f"https://commons.wikimedia.org/wiki/Special:Redirect/file/{filename}?width={requested_width}"
    return value


@app.template_filter("image_srcset")
def image_srcset(url, widths):
    """Descreve a largura real da imagem local e variantes das outras origens."""
    value = responsive_image_url(url, 960)
    if value.startswith("/static/img/e-coli-niaid-960.jpg"):
        return "/static/img/e-coli-niaid-330.jpg?v=d52ba80e29c6 330w, " + f"{value} 960w"
    return ", ".join(f"{responsive_image_url(url, width)} {width}w" for width in widths)


@app.template_filter("absolute_url")
def absolute_url(value):
    address = html_unescape(str(value or "")).strip().strip(chr(34) + chr(39))
    if address.startswith(("http://", "https://")):
        return address
    if address.startswith("//"):
        return "https:" + address
    return SITE_URL + "/" + address.lstrip("/")


@app.template_filter("social_image")
def social_image_url(url):
    value = safe_image_url(url)
    if not value:
        return SITE_URL + "/static/img/logo-sussurros-horizontal.png"

    transformation = "f_jpg,q_auto:good,w_1200,h_630,c_fill,g_auto,fl_force_strip"
    if "res.cloudinary.com/" in value and "/upload/" in value:
        return value.replace("/upload/", f"/upload/{transformation}/", 1)

    # O endereço original é mais fiável do que Cloudinary image/fetch:
    # muitas origens bloqueiam o fetch e algumas contas não o têm ativado.
    return value



@app.errorhandler(500)
def internal_server_error(error):
    db.session.rollback()
    if request.is_json or request.path.startswith(("/api/", "/admin/api/", "/conta/")):
        message = "O serviço está temporariamente indisponível. Tente novamente."
        return jsonify(ok=False, message=message, error=message, answer=message), 500
    return render_template("500.html"), 500


@app.errorhandler(429)
def rate_limited(error):
    if request.path.startswith(("/api/", "/admin/api/", "/conta/")):
        message = "Limite temporário atingido. Aguarde antes de tentar novamente."
        response = jsonify(ok=False, message=message, error=message, answer=message)
        response.status_code = 429
        response.headers["Retry-After"] = str(max(1, int(getattr(error, "retry_after", None) or 60)))
        return response
    return render_template("429.html"), 429


@app.errorhandler(413)
def upload_too_large(error):
    message = "O carregamento excede o limite do pedido. Cada vídeo pode ter até 50 MB e cada imagem até 8 MB. Carregue os ficheiros separadamente."
    if request.path.startswith(("/api/", "/admin/api/", "/conta/")):
        return jsonify(ok=False, message=message, error=message, answer=message), 413
    return render_template("413.html", message=message), 413

SEED_ARTICLES = [
    {"id": 1, "category": "Biologia", "title": "Bactérias endofíticas: os microrganismos invisíveis que protegem as plantas", "summary": "Dentro das plantas vivem comunidades capazes de produzir compostos com potencial antibacteriano.", "author": "Mergior Goriate", "date": "10 Setembro 2026", "read_time": "7 min", "image": "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?auto=format&fit=crop&w=1400&q=85", "featured": True},
    {"id": 2, "category": "Saúde", "title": "Por que sentimos sono depois de comer?", "summary": "A digestão, as hormonas e o relógio biológico explicam a queda de energia após as refeições.", "author": "Redacção", "date": "8 Setembro 2026", "read_time": "5 min", "image": "https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&w=1000&q=85"},
    {"id": 3, "category": "Ambiente", "title": "Plantas medicinais de Nampula e o futuro da investigação local", "summary": "Conhecimento tradicional e métodos laboratoriais podem abrir caminhos para novas descobertas.", "author": "Mergior Goriate", "date": "6 Setembro 2026", "read_time": "9 min", "image": "https://images.unsplash.com/photo-1531058240690-006c446962d8?auto=format&fit=crop&w=1000&q=85"},
    {"id": 4, "category": "Espaço", "title": "Como os radiotelescópios africanos observam o universo", "summary": "A radioastronomia transforma África num ponto estratégico para estudar galáxias distantes.", "author": "Redacção", "date": "4 Setembro 2026", "read_time": "6 min", "image": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?auto=format&fit=crop&w=1000&q=85"},
    {"id": 5, "category": "Educação", "title": "Cinco estratégias para aprender Biologia com rigor científico", "summary": "Da observação à explicação: um método simples para estudar processos biológicos.", "author": "Mergior Goriate", "date": "1 Setembro 2026", "read_time": "4 min", "image": "https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&w=1000&q=85"},
    {"id": 6, "category": "Tecnologia", "title": "Python na investigação: da folha de cálculo à análise reprodutível", "summary": "Como estudantes podem automatizar tarefas, explorar dados e documentar melhor as suas análises.", "author": "Mergior Goriate", "date": "28 Agosto 2026", "read_time": "8 min", "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1000&q=85"},
]

DEFAULT_JOURNALS = [
    {"slug": "cadernos-de-biodiversidade", "title": "Cadernos de Biodiversidade", "abbr": "CBIO", "field": "Biologia e Ecologia", "description": "Estudos sobre biodiversidade, conservação, ecologia e recursos naturais, com atenção aos contextos africanos.", "frequency": "Semestral", "issue": "Vol. 1 · N.º 1", "status": "Recebendo artigos"},
    {"slug": "saude-e-comunidade", "title": "Saúde & Comunidade", "abbr": "SACO", "field": "Saúde Pública", "description": "Investigação e práticas sobre saúde comunitária, nutrição, prevenção e determinantes sociais da saúde.", "frequency": "Semestral", "issue": "Vol. 1 · N.º 1", "status": "Em preparação"},
    {"slug": "educacao-cientifica", "title": "Educação Científica", "abbr": "EDCI", "field": "Ensino e Aprendizagem", "description": "Pesquisa e experiências sobre ensino de Ciências e Biologia, formação docente e inovação pedagógica.", "frequency": "Anual", "issue": "Vol. 1 · N.º 1", "status": "Recebendo artigos"},
]

LEARNING_RESOURCES = [
    {"id": 1, "type": "Interactivo", "topic": "Biologia Celular", "level": "Universitário", "title": "Explore a célula", "description": "Identifique organelos e relacione estruturas com as suas funções.", "icon": "◉"},
    {"id": 2, "type": "Laboratório Virtual", "topic": "Fisiologia", "level": "Secundário", "title": "Osmose em células", "description": "Teste concentrações e observe o movimento previsto da água.", "icon": "⌁", "url": "/laboratorio/osmose"},
    {"id": 3, "type": "Actividade", "topic": "Genética", "level": "Universitário", "title": "Heredogramas passo a passo", "description": "Pratique a identificação de padrões de herança em famílias.", "icon": "◇"},
    {"id": 4, "type": "Explicador", "topic": "Microbiologia", "level": "Secundário", "title": "O mundo invisível dos microrganismos", "description": "Uma introdução visual à diversidade microbiana.", "icon": "▶"},
    {"id": 5, "type": "Dados", "topic": "Ecologia", "level": "Universitário", "title": "Diversidade de espécies", "description": "Conjunto demonstrativo para calcular riqueza e abundância.", "icon": "▥"},
    {"id": 6, "type": "Explicador", "topic": "Bioquímica", "level": "Universitário", "title": "Do DNA à proteína", "description": "Uma sequência guiada por replicação, transcrição e tradução.", "icon": "↝"},
    {"id":7,"type":"Actividade","topic":"Método Científico","level":"Secundário","title":"Hipóteses e variáveis","description":"Distinga a variável manipulada, a resposta medida e os factores controlados.","icon":"?"},
    {"id":8,"type":"Actividade","topic":"Estatística","level":"Secundário","title":"Média e mediana","description":"Compare duas medidas de tendência central com um exemplo resolvido.","icon":"Σ"},
    {"id":9,"type":"Actividade","topic":"Probabilidade","level":"Secundário","title":"Probabilidade em experiências simples","description":"Calcule probabilidades e reconheça acontecimentos independentes.","icon":"½"},
]

@app.get("/")
def home():
    from news import latest_news
    from internationalization import language

    hero = Article.public_card_query().options(db.undefer(Article.cover_mode), db.undefer(Article.cover_video)).order_by(Article.featured.desc(), Article.published_at.desc(), Article.id.desc()).first()
    items = ([hero] + Article.public_card_query().filter(Article.id != hero.id)
             .order_by(Article.published_at.desc(), Article.id.desc()).limit(9).all()) if hero else []
    return render_template("index.html", articles=items, home_news=latest_news(language()), journals=Journal.query.filter_by(published=True).order_by(Journal.publication_date.desc().nullslast(), Journal.updated_at.desc(), Journal.id.desc()).limit(4).all())

@app.get("/artigos")
def articles():
    category = request.args.get("categoria", "").strip().lower()
    if getattr(g,'language','pt')=='en':
        from i18n_catalog import EN
        category=next((pt.lower() for pt,en in EN.items() if en.lower()==category),category)
    query = request.args.get("q", "").strip()[:120]
    results = Article.public_card_query()
    relevance = []
    if category or query:
        results = results.join(Category)
    if category:
        results = results.filter(db.func.lower(Category.name) == category)
    if query:
        match, score = article_search(query, english=getattr(g, "language", "pt") == "en")
        results = results.join(Author).filter(match)
        relevance = [score.desc()]
    page = pagination_page()
    pagination = results.order_by(*relevance, Article.published_at.desc(), Article.id.desc()).paginate(page=page, per_page=12, error_out=False)
    return render_template(
        "articles.html",
        articles=pagination.items,
        pagination=pagination,
        query=request.args.get("q", ""),
        scientific_biography=category == "biografia científica",
    )

def comment_csrf_token():
    token = session.get("comment_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["comment_csrf_token"] = token
    return token


@app.get("/artigo/<slug>")
def article(slug):
    selected = Article.public_query().filter_by(slug=slug).first()
    if not selected:
        legacy_match = re.fullmatch(r"artigo-(\d+)", slug)
        legacy = Article.public_query().filter_by(id=int(legacy_match.group(1))).first() if legacy_match else None
        if legacy:
            return redirect(url_for("article", slug=legacy.slug), code=301)
        return render_template("404.html"), 404
    if getattr(g, 'language', 'pt') == 'en':
        from translation_service import published
        if not published('article', selected.id)[1]:
            return render_template('i18n/unavailable.html', original=selected), 404
    g.google_cmp_public_content = True
    related = (
        Article.public_card_query()
        .filter(Article.id != selected.id)
        .order_by(
            case((Article.category_id == selected.category_id, 0), else_=1),
            Article.published_at.desc(), Article.id.desc(),
        )
        .limit(3).all()
    )
    from videos import public_article_video
    from cover_media import effective_cover_mode
    science_video_for_article = (
        public_article_video(selected, getattr(g, 'language', 'pt'))
        if effective_cover_mode(selected.cover_mode, selected.cover_video) != 'image' and selected.cover_video
        else None
    )
    comments = Comment.query.filter_by(article_id=selected.id, approved=True).order_by(Comment.created_at.desc()).limit(100).all()
    return render_template(
        "article.html",
        article=selected,
        related=related,
        comments=comments,
        comment_csrf_token=comment_csrf_token(),
        article_video=science_video_for_article,
    )


@app.post("/artigo/<slug>/comentarios")
@limiter.limit("5 per hour")
def submit_comment(slug):
    selected = Article.public_query().filter_by(slug=slug).first()
    if not selected:
        return render_template("404.html"), 404

    success_url = url_for("article", slug=selected.slug, comentario="recebido") + "#comentarios"
    if request.form.get("website", "").strip():
        return redirect(success_url, code=303)

    sent_token = request.form.get("csrf_token", "")
    expected_token = session.get("comment_csrf_token", "")
    if not expected_token or not secrets.compare_digest(sent_token, expected_token):
        return redirect(url_for("article", slug=selected.slug, comentario="invalido") + "#comentarios", code=303)

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    body = request.form.get("body", "").strip()
    if not 2 <= len(name) <= 80 or not valid_email(email) or not 10 <= len(body) <= 2000:
        return redirect(url_for("article", slug=selected.slug, comentario="invalido") + "#comentarios", code=303)

    db.session.add(Comment(article_id=selected.id, name=name, email=email, body=body))
    db.session.commit()
    session["comment_csrf_token"] = secrets.token_urlsafe(32)
    return redirect(success_url, code=303)


@app.get("/artigo/<int:article_id>")
def article_legacy(article_id):
    selected = Article.public_query().filter_by(id=article_id).first()
    if not selected:
        return render_template("404.html"), 404
    return redirect(url_for("article", slug=selected.slug), code=301)

@app.get("/sobre")
def about():
    return render_template("about.html")

@app.get("/autores")
def authors():
    editorial_team = (
        Author.query.filter_by(active=True)
        .order_by(Author.display_order.asc(), Author.name.asc())
        .all()
    )
    return render_template("authors.html", authors=editorial_team)


def profile_lines(value):
    return [line.strip().lstrip("-• ").strip() for line in (value or "").splitlines() if line.strip()]


@app.get("/autor/<slug>")
def author_detail(slug):
    author = Author.query.filter_by(slug=slug, active=True).first()
    if not author:
        return render_template("404.html"), 404
    page = pagination_page('pagina')
    pagination = (
        Article.public_card_query()
        .filter(Article.author_id == author.id)
        .order_by(Article.published_at.desc(), Article.id.desc())
        .paginate(page=page, per_page=9, error_out=False)
    )
    return render_template(
        "author.html",
        author=author,
        articles=pagination.items,
        pagination=pagination,
        interests=profile_lines(author.interests),
        projects=profile_lines(author.projects),
        publications=profile_lines(author.publications),
        academic_background=profile_lines(author.academic_background),
        editorial_experience=profile_lines(author.editorial_experience),
    )


@app.get("/autor/<int:author_id>")
def legacy_author(author_id):
    author = db.session.get(Author, author_id)
    if not author or not author.active:
        return render_template("404.html"), 404
    return redirect(url_for("author_detail", slug=author.slug), code=301)


@app.get("/contacto")
def contact():
    return render_template("contact.html")

@app.get("/termos-e-condicoes")
def terms():
    return render_template("terms.html")

@app.get("/politica-de-publicidade")
def advertising_policy():
    return render_template("advertising_policy.html")

@app.get("/politica-de-privacidade")
def privacy():
    return render_template("privacy.html")

@app.get("/politica-editorial")
@app.get("/politicas-editoriais")
def editorial_policy():
    from internationalization import ui
    policy = EditorialPolicy.query.first()
    fields = (
        ("author_guidelines", "Diretrizes para Autores"),
        ("reviewer_guidelines", "Diretrizes para Revisores"),
        ("ethics_policy", "Ética e Integridade Científica"),
        ("ai_policy", "Política de Inteligência Artificial"),
        ("data_policy", "Política de Dados de Investigação"),
        ("fees_policy", "Taxas / APC"),
        ("open_access_policy", "Acesso Aberto e Licenciamento"),
    )
    sections = []
    if policy:
        for field, title in fields:
            content = (getattr(policy, field, "") or "").strip()
            if content:
                sections.append({"id": field.replace("_", "-"), "title": ui(title), "content": render_markdown(ui(content))})
    return render_template("editorial_policy.html", policy_sections=sections,
                           page_title=ui((getattr(policy, "page_title", "") or "").strip() or "Políticas Editoriais"),
                           page_description=ui((getattr(policy, "page_description", "") or "").strip()),
                           page_content=render_markdown(ui(getattr(policy, "page_content", "") or "")))

@app.get("/politica-de-correcoes")
def corrections_policy():
    return render_template("corrections_policy.html")

@app.get("/acessibilidade")
def accessibility():
    return render_template("accessibility.html")

@app.get("/servicos")
def services():
    return render_template("services.html")

@app.get("/servicos/edicao-cientifica")
def scientific_editing():
    return render_template("scientific_editing.html")

@app.get("/revistas")
def journals():
    query = request.args.get('q', '').strip()[:120]
    results = Journal.query.filter_by(published=True)
    if query:
        results = results.filter(metadata_match(query,
            Journal.title, Journal.article_title, Journal.article_title_en,
            Journal.field, Journal.description, Journal.summary, Journal.abstract,
            Journal.keywords, Journal.abstract_keywords, Journal.authors_data,
            Journal.authors_orcid, Journal.doi, Journal.current_issue))
    return render_template(
        "journals.html",
        journals=results.order_by(Journal.title, Journal.id).all(),
        query=query,
    )


@app.get("/revistas/<slug>")
def journal_detail(slug):
    journal = Journal.query.filter_by(slug=slug, published=True).first()
    if not journal:
        return render_template("404.html"), 404
    from scientific_metrics_collection import record
    return record(journal, 'view', app.make_response(render_journal(journal)))


@app.post("/admin/revistas/previsualizar-markdown")
@login_required
@limiter.limit("120 per minute")
def journal_markdown_preview():
    validate_csrf()
    content = request.form.get("content", "")
    references = request.form.get("references", "")
    from types import SimpleNamespace
    extra = {name: request.form.get(name, "") for name in ARTICLE_FIELD_LIMITS}
    if any(len(value) > ARTICLE_FIELD_LIMITS[name] for name, value in extra.items()):
        return jsonify({"error": "Um dos campos do artigo excede o limite permitido."}), 400
    if len(content) + len(references) + sum(map(len, extra.values())) > 750000:
        return jsonify({"error": "Conteúdo demasiado extenso para pré-visualização."}), 400
    source = SimpleNamespace(**extra)
    references_html = str(render_markdown(references))
    if source.notes.strip():
        references_html += "<h2>Notas</h2>" + str(render_markdown(source.notes))
    return jsonify({"html": structured_article_content(source, str(render_markdown(content)), render_markdown), "references": references_html})


@app.get("/admin/revistas/<int:journal_id>/previsualizar")
@login_required
def journal_preview(journal_id):
    from governance import journal_access
    journal_access(journal_id,viewing=True)
    return render_journal(db.get_or_404(Journal, journal_id))


def journal_article_content(journal):
    content = str(render_markdown(journal.content_markdown or journal.guidelines or ""))
    title_heading = re.match(r"\s*<h1>(.*?)</h1>\s*", content, re.S)
    article_title = journal.title
    if title_heading:
        article_title = html_unescape(bleach.clean(title_heading.group(1), tags=[], strip=True))
        content = content[title_heading.end():]
    article_title = (getattr(journal, "article_title", "") or "").strip() or article_title
    return article_title, structured_article_content(journal, content, render_markdown)


def render_journal(journal):
    g.google_cmp_public_content = request.endpoint == "journal_detail" and journal.published
    article_title, content = journal_article_content(journal)
    from scientific_metrics_collection import scientific
    from scientific_metrics import article_metrics, SOURCES, STATES
    eligible = request.endpoint in {'journal_detail', 'journal_preview'} and bool((journal.content_markdown or '').strip())
    metrics_data, metrics_options = article_metrics(journal) if eligible and scientific(journal) else (None, None)
    return render_template("journal.html", metrics_data=metrics_data, metrics_options=metrics_options,
                           metrics_sources=SOURCES, metrics_states=STATES, scientific_eligible=eligible, journal=journal,
                           article_title=article_title, journal_content=Markup(content), journal_authors=journal_authors(journal),
                           public_url=SITE_URL + url_for("journal_detail", slug=journal.slug))

@app.get("/revistas/<slug>/baixar.pdf")
@limiter.limit("10 per minute; 60 per hour")
def journal_download_pdf(slug):
    journal = Journal.query.filter_by(slug=slug, published=True).first()
    if not journal:
        return render_template("404.html"), 404
    from scientific_metrics_collection import record
    return record(journal, 'download', app.make_response(render_journal_pdf(journal)))


@app.get("/admin/revistas/<int:journal_id>/baixar.pdf")
@login_required
@limiter.limit("10 per minute; 60 per hour")
def journal_preview_pdf(journal_id):
    from governance import journal_access
    journal_access(journal_id,viewing=True)
    return render_journal_pdf(db.get_or_404(Journal, journal_id))


def render_journal_pdf(journal):
    from pdf_cache import cached_pdf_response
    return cached_pdf_response(journal, build_journal_pdf)


def build_journal_pdf(journal):

    from journal_pdf import article_flowables, pdf_styles, page_footer, editorial_header
    image_deadline = time.monotonic() + 20
    article_title, content = journal_article_content(journal)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=8*mm, bottomMargin=18*mm,
                            title=article_title, author="Sussurros do Saber")
    styles = pdf_styles()
    story = [editorial_header(journal, doc.width), Spacer(1, 9),
             Paragraph("Artigo científico", styles["PaperType"]),
             Paragraph(html_escape(article_title), styles["Title"])]
    english_title = (getattr(journal, "article_title_en", "") or "").strip()
    if english_title:
        story += [Paragraph(html_escape(english_title), styles["EnglishTitle"]), Spacer(1, 4)]
    authors = journal_authors(journal)
    if authors:
        author_names = []
        for author in authors:
            name = html_escape(author["name"] or author["orcid"])
            author_names.append("<b>" + name + "</b>")
        story += [Paragraph(", ".join(author_names), styles["Metadata"])]
        for author in authors:
            if author["orcid"]:
                url = html_escape(author["orcid"], quote=True)
                story.append(Paragraph(html_escape(author["name"]) + f' - ORCID: <link href="{url}">{url}</link>', styles["Metadata"]))
    history = getattr(journal, "submission_history", "") or ""
    if history:
        plain_history = html_unescape(bleach.clean(str(render_markdown(history)), tags=[], strip=True)).strip()
        story.append(Paragraph(html_escape(plain_history).replace("\n", "<br/>"), styles["Metadata"]))
    publication_date = getattr(journal, "publication_date", None)
    if publication_date:
        story.append(Paragraph("Publicado em: " + publication_date.strftime("%d/%m/%Y"), styles["Metadata"]))
    correspondence = (getattr(journal, "corresponding_author", "") or "").strip()
    if correspondence:
        story.append(Paragraph("<b>Autor para correspondência:</b> " + html_escape(correspondence).replace("\n", "<br/>"), styles["Metadata"]))
    story += [Spacer(1, 8)]
    story += article_flowables(content,
                               doc.width, doc.height, app.static_folder, CANONICAL_ORIGIN,
                               title=article_title, start_body_new_page=True, image_deadline=image_deadline)
    if journal.references:
        story += [Spacer(1, 12), Paragraph("Referências bibliográficas", styles["Heading2"])]
        story += article_flowables(render_markdown(journal.references), doc.width, doc.height,
                                   app.static_folder, CANONICAL_ORIGIN, image_deadline=image_deadline)
    if getattr(journal, "notes", ""):
        story += [Spacer(1, 12), Paragraph("Notas", styles["Heading2"])]
        story += article_flowables(render_markdown(journal.notes), doc.width, doc.height,
                                   app.static_folder, CANONICAL_ORIGIN, image_deadline=image_deadline)
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

@app.get("/recursos")
def resources():
    return render_template("resources.html")

from learning_content import LEARNING_LESSONS

@app.get("/aprender")
def learn():
    resource_type = request.args.get("tipo", "").strip().lower()
    topic = request.args.get("tema", "").strip().lower()
    items = LEARNING_RESOURCES
    if resource_type:
        items = [item for item in items if item["type"].lower() == resource_type]
    if topic:
        items = [item for item in items if item["topic"].lower() == topic]
    return render_template("learn.html", resources=items, all_resources=LEARNING_RESOURCES,
                           lessons=LEARNING_LESSONS)

@app.get("/laboratorio/osmose")
def osmosis_lab():
    return render_template("osmosis_lab.html")

@app.get("/api/recursos")
def api_resources():
    response = jsonify(LEARNING_RESOURCES)
    response.headers["Cache-Control"] = "public, max-age=600, stale-while-revalidate=3600"
    return response

@app.get("/favoritos")
def favorites():
    return redirect(url_for("reader.library"), code=302)

@app.get("/api/artigos")
def api_articles():
    query = request.args.get("q", "").strip().lower()[:120]
    raw_ids = request.args.get("ids", "")[:512]
    requested_ids = list(dict.fromkeys(
        int(value) for value in raw_ids.split(",")
        if re.fullmatch(r"[0-9]{1,10}", value.strip()) and int(value) <= 2147483647
    ))[:50]
    limit = max(1, min(50, request.args.get("limit", 24, type=int)))

    items = Article.public_card_query()
    if "ids" in request.args:
        items = items.filter(Article.id.in_(requested_ids))
        limit = min(50, len(requested_ids))
    relevance = []
    if query:
        match, score = article_search(query, english=getattr(g, "language", "pt") == "en")
        items = items.join(Category).join(Author).filter(match)
        relevance = [score.desc()]
    articles = items.order_by(*relevance, Article.published_at.desc(), Article.id.desc()).limit(limit).all()
    response = jsonify([
        {
            "id": article.id,
            "slug": article.slug,
            "category": article.category,
            "title": article.title,
            "summary": article.summary,
            "author": article.author,
            "date": article.date,
            "read_time": article.read_time,
            "image": article.cover_poster,
        }
        for article in articles
    ])
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response

@app.get("/feed.xml")
def feed():
    articles = Article.public_card_query().order_by(Article.published_at.desc()).all()
    items = "".join(f"<item><title>{escape(a.title)}</title><link>{SITE_URL}{url_for('article', slug=a.slug)}</link><guid isPermaLink=\"true\">{SITE_URL}{url_for('article', slug=a.slug)}</guid><pubDate>{format_datetime((a.published_at or a.created_at).replace(tzinfo=timezone.utc))}</pubDate><description>{escape(a.summary)}</description></item>" for a in articles)
    last_build = format_datetime(datetime.now(timezone.utc))
    xml = f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Sussurros do Saber</title><link>{SITE_URL}/</link><description>Ciência que se compreende</description><language>pt-MZ</language><lastBuildDate>{last_build}</lastBuildDate>{items}</channel></rss>'
    return Response(xml, mimetype="application/rss+xml")

@app.get("/sitemap.xml")
def sitemap():
    from internationalization import alternate_links, path_alternates, sitemap_content_alternates, sitemap_extras
    from news import sitemap_entries
    from videos import sitemap_entries as video_sitemap_entries
    public_articles = Article.public_card_query().order_by(Article.updated_at.desc()).all()
    public_journals = (
        Journal.query.filter_by(published=True)
        .options(load_only(Journal.id, Journal.slug, Journal.updated_at, Journal.field, Journal.frequency))
        .order_by(Journal.updated_at.desc()).all()
    )
    public_authors = Author.query.filter_by(active=True).order_by(Author.name).all()
    localized_content = sitemap_content_alternates(public_articles, public_journals)
    static_paths = [
        url_for("home"), url_for("articles"), url_for("resources"), url_for("learn"),
        url_for("osmosis_lab"), url_for("about"), url_for("authors"), url_for("contact"),
        url_for("terms"), url_for("privacy"), url_for("editorial_policy"), url_for("news.index"), url_for("videos.index"),
        url_for("corrections_policy"), url_for("accessibility"), url_for("services"),
        url_for("scientific_editing"), url_for("journals"), url_for("author_guidelines"),
    ]
    static_urls = "".join(
        f"<url><loc>{escape(SITE_URL + path)}</loc>{path_alternates(path)}</url>"
        for path in static_paths
    )
    journal_urls = "".join(
        f"<url><loc>{escape(SITE_URL + url_for('journal_detail', slug=journal.slug))}</loc>"
        f"<lastmod>{journal.updated_at.strftime('%Y-%m-%d')}</lastmod>"
        f"{localized_content.get(('journal_detail', journal.slug), '')}</url>"
        for journal in public_journals
    )
    author_urls = "".join(
        f"<url><loc>{escape(SITE_URL + url_for('author_detail', slug=author.slug))}</loc>{alternate_links('author_detail', slug=author.slug)}</url>"
        for author in public_authors if author.slug
    )
    author_paths = [url_for("author_detail", slug=author.slug) for author in public_authors if author.slug]
    article_entries = []
    for article in public_articles:
        article_url = escape(SITE_URL + url_for("article", slug=article.slug))
        cover_url = safe_image_url(article.cover_poster)
        image_xml = ""
        if cover_url:
            image_xml = (
                f"<image:image><image:loc>{escape(cover_url)}</image:loc>"
                f"<image:title>{escape(article.title)}</image:title></image:image>"
            )
        article_entries.append(
            f"<url><loc>{article_url}</loc>"
            f"<lastmod>{article.updated_at.strftime('%Y-%m-%d')}</lastmod>"
            f"{localized_content.get(('article', article.slug), '')}{image_xml}</url>"
        )
    response = Response(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">'
        + static_urls + journal_urls + author_urls + "".join(article_entries)
        + sitemap_extras(static_paths + author_paths, localized_content) + sitemap_entries(SITE_URL)
        + video_sitemap_entries(SITE_URL) + "</urlset>",
        mimetype="application/xml",
    )
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response

@app.get("/robots.txt")
def robots():
    return Response(f"User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/\nSitemap: {SITE_URL}/sitemap.xml\nSitemap: {SITE_URL}/video-sitemap.xml\n", mimetype="text/plain")


@app.get("/healthz")
@limiter.exempt
def healthcheck():
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.error("Healthcheck: database unavailable")
        return jsonify({"ok": False}), 503
    return jsonify({"ok": True})


def valid_email(value):
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value)) and len(value) <= 254


def json_text_fields(*names):
    """Reject non-object payloads and non-text fields before accessing them."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or any(not isinstance(data.get(name, ""), str) for name in names):
        return None
    return {name: data.get(name, "").strip() for name in names}

@app.post("/api/newsletter")
@limiter.limit("5 per hour")
def newsletter():
    data = json_text_fields("email")
    if data is None:
        return jsonify(ok=False, message="Introduza um endereço de e-mail válido."), 400
    email = data["email"].lower()
    if not valid_email(email) or len(email) > 180:
        return jsonify({"ok": False, "message": "Introduza um endereço de e-mail válido."}), 400
    subscriber = Subscriber.query.filter_by(email=email).first()
    if subscriber:
        subscriber.active = True
    else:
        db.session.add(Subscriber(email=email))
    db.session.commit()
    from newsletter_service import smtp_ready
    message = "Inscrição confirmada. Pode cancelar através da ligação incluída em cada boletim."
    if not smtp_ready():
        message += " O envio de e-mails ainda aguarda activação no servidor."
    return jsonify({"ok": True, "message": message})

@app.post("/api/assistente")
@limiter.limit("5 per minute; 20 per hour")
def assistant():
    payload = request.get_json(silent=True)
    english = isinstance(payload, dict) and payload.get("language") == "en"
    def reply(pt, en):
        return en if english else pt
    data = json_text_fields("message")
    if data is None:
        return jsonify(ok=False, answer=reply("Escreva uma pergunta em texto.", "Enter a question as text.")), 400
    message = data["message"]
    if not message:
        return jsonify({"ok": False, "answer": reply("Escreva uma pergunta para eu poder ajudar.", "Enter a question so I can help.")}), 400
    if len(message) > 800:
        return jsonify({"ok": False, "answer": reply("Utilize até 800 caracteres por pergunta.", "Use up to 800 characters per question.")}), 400

    # Contexto temporário recebido do navegador, sem persistência.
    raw_history = payload.get("history", []) if isinstance(payload, dict) else []
    if not isinstance(raw_history, list):
        return jsonify(ok=False, answer=reply("Histórico inválido.", "Invalid history.")), 400
    history = []
    for item in raw_history[-16:]:
        if (isinstance(item, dict) and item.get("role") in ("user", "assistant")
                and isinstance(item.get("content"), str)):
            content = item["content"].strip()[:1200]
            if content:
                history.append({"role": item["role"], "content": content})

    # Consultar apenas artigos publicados, sem guardar perguntas.
    sources = []
    try:
        terms = list(dict.fromkeys(re.findall(r'[^\W_]{4,}', message.lower(), re.UNICODE)))[:8]
        if terms:
            filters = [db.or_(Article.title.ilike('%' + t + '%'), Article.summary.ilike('%' + t + '%'), Article.keywords.ilike('%' + t + '%'), Article.body.ilike('%' + t + '%')) for t in terms]
            candidates = Article.public_query().filter(db.or_(*filters)).limit(30).all()
            ranked = []
            for article in candidates:
                title, summary, keywords = article.title or '', article.summary or '', article.keywords or ''
                body = re.sub(r'<[^>]+>', ' ', article.body or '')
                score = sum(5 * (t in title.lower()) + 3 * (t in keywords.lower()) + 2 * (t in summary.lower()) + (t in body.lower()) for t in terms)
                if score >= 2:
                    excerpt = next((body[max(0, body.lower().find(t) - 100):body.lower().find(t) + 550] for t in terms if t in body.lower()), body[:550])
                    source_title = title
                    source_excerpt = (summary[:500] + ' ' + excerpt[:650]).strip()
                    if english:
                        # Prefer the reviewed, published English translation, never a guessed title.
                        from translation_service import published
                        _, translated_version = published('article', article.id)
                        translated = translated_version.content if translated_version else {}
                        if isinstance(translated, dict):
                            source_title = translated.get('title') or title
                            source_excerpt = (translated.get('summary') or source_excerpt)[:1200]
                    ranked.append((score, {'title': source_title[:240], 'url': url_for('article', slug=article.slug, _external=True), 'excerpt': source_excerpt}))
            sources = [item for _, item in sorted(ranked, key=lambda pair: pair[0], reverse=True)[:3]]
    except Exception:
        app.logger.exception('Assistant article search failed')

    try:
        headers = {}
        if os.getenv("ASSISTANT_SHARED_KEY"):
            headers["X-Assistant-Key"] = os.environ["ASSISTANT_SHARED_KEY"]
        worker_response = requests.post(
            os.getenv("ASSISTANT_WORKER_URL", "https://assistente-sussurros.geniospurificado.workers.dev"),
            json={"message": message, "language": "en" if english else "pt", "history": history, "sources": sources},
            headers=headers,
            timeout=25,
        )
        worker_response.raise_for_status()
        result = worker_response.json()
        if not isinstance(result, dict) or not isinstance(result.get("answer"), str):
            raise ValueError("Invalid assistant response")
        return jsonify(result), 200 if result.get("ok") else 502
    except (requests.RequestException, ValueError):
        return jsonify({
            "ok": False,
            "answer": reply("O assistente está temporariamente indisponível. Tente novamente dentro de alguns instantes.", "The assistant is temporarily unavailable. Please try again shortly."),
            "links": [],
        }), 502

@app.post("/api/contacto")
@limiter.limit("10 per hour")
def submit_contact():
    data = json_text_fields("name", "email", "subject", "message", "website")
    if data is None:
        return jsonify(ok=False, message="Preencha correctamente todos os campos."), 400
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    subject = data.get("subject", "").strip()
    message = data.get("message", "").strip()
    website = data.get("website", "").strip()
    if website:
        return jsonify({"ok": True, "message": "Mensagem recebida."})
    if not 2 <= len(name) <= 120 or not valid_email(email) or not 3 <= len(subject) <= 220 or not 10 <= len(message) <= 5000:
        return jsonify({"ok": False, "message": "Preencha correctamente todos os campos."}), 400
    db.session.add(ContactMessage(name=name, email=email, subject=subject, message=message))
    db.session.commit()
    return jsonify({"ok": True, "message": "Mensagem recebida. Obrigado por contactar o Sussurros do Saber."})


def ensure_admin_columns():
    inspector = inspect(db.engine)
    if "admin_user" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("admin_user")}
    additions = {
        "is_superadmin": "BOOLEAN DEFAULT FALSE NOT NULL",
        "two_factor_enabled": "BOOLEAN DEFAULT FALSE NOT NULL",
        "totp_secret": "VARCHAR(64)",
        "recovery_code_hashes": "TEXT DEFAULT '' NOT NULL",
        "security_version": "INTEGER DEFAULT 1 NOT NULL",
        "governance_managed": "BOOLEAN DEFAULT FALSE NOT NULL",
    }
    changed = False
    for name, definition in additions.items():
        if name not in existing:
            db.session.execute(text(
                f'ALTER TABLE admin_user ADD COLUMN "{name}" {definition}'
            ))
            changed = True
    if changed:
        db.session.commit()

    administrators = AdminUser.query.order_by(AdminUser.created_at, AdminUser.id).all()
    configured_primary = bool(os.getenv("ADMIN_USERNAME"))
    if configured_primary:
        changed = False
        for administrator in administrators:
            if administrator.is_superadmin:
                administrator.is_superadmin = False
                changed = True
        if changed:
            db.session.commit()
        return

    if administrators:
        active = [administrator for administrator in administrators if administrator.active]
        primary = next(
            (administrator for administrator in administrators if administrator.is_superadmin and administrator.active),
            active[0] if active else administrators[0],
        )
        changed = False
        for administrator in administrators:
            should_be_primary = administrator.id == primary.id
            if administrator.is_superadmin != should_be_primary:
                administrator.is_superadmin = should_be_primary
                changed = True
        if changed:
            db.session.commit()


def ensure_author_columns():
    inspector = inspect(db.engine)
    if "author" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("author")}
    additions = {
        "slug": "VARCHAR(160)",
        "role": "VARCHAR(140) DEFAULT ''",
        "headline": "VARCHAR(220) DEFAULT ''",
        "academic_background": "TEXT DEFAULT ''",
        "institution": "VARCHAR(220) DEFAULT ''",
        "bio": "TEXT DEFAULT ''",
        "interests": "TEXT DEFAULT ''",
        "projects": "TEXT DEFAULT ''",
        "orcid": "VARCHAR(19) DEFAULT ''",
        "google_scholar": "VARCHAR(600) DEFAULT ''",
        "researchgate": "VARCHAR(600) DEFAULT ''",
        "publications": "TEXT DEFAULT ''",
        "editorial_experience": "TEXT DEFAULT ''",
        "photo": "VARCHAR(600) DEFAULT ''",
        "display_order": "INTEGER DEFAULT 100",
    }
    changed = False
    for column, definition in additions.items():
        if column not in existing:
            db.session.execute(text(f'ALTER TABLE author ADD COLUMN {column} {definition}'))
            changed = True
    if changed:
        db.session.commit()

    used_slugs = set()
    profiles_changed = False
    for author in Author.query.order_by(Author.id).all():
        base = slugify(author.slug or author.name) or f"autor-{author.id}"
        candidate, number = base, 2
        while candidate in used_slugs:
            candidate, number = f"{base}-{number}", number + 1
        if author.slug != candidate:
            author.slug = candidate
            profiles_changed = True
        used_slugs.add(candidate)
        if author.display_order is None:
            author.display_order = 100
            profiles_changed = True
        if author.name.casefold() == "mergior alfredo goriate":
            if not author.role:
                author.role = "Fundador e Editor-Chefe"
                profiles_changed = True
            if not author.headline:
                author.headline = "Investigador, autor e fundador do Sussurros do Saber."
                profiles_changed = True
            if author.display_order != 1:
                author.display_order = 1
                profiles_changed = True
    if profiles_changed:
        db.session.commit()
    db.session.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_author_slug ON author (slug)"
    ))
    db.session.commit()



def ensure_journal_columns():
    """Mantém o schema Journal compatível antes de qualquer consulta ORM."""
    additions = {
        "abbreviation": "VARCHAR(30) DEFAULT ''",
        "field": "VARCHAR(140) DEFAULT '' NOT NULL",
        "description": "TEXT DEFAULT '' NOT NULL",
        "issn": "VARCHAR(9) DEFAULT ''",
        "frequency": "VARCHAR(80) DEFAULT ''",
        "current_issue": "VARCHAR(120) DEFAULT ''",
        "doi": "VARCHAR(180) DEFAULT ''",
        "publication_date": "DATE",
        "authors_orcid": "TEXT DEFAULT ''",
        "authors_data": "TEXT DEFAULT ''",
        "submission_history": "TEXT DEFAULT ''",
        "acknowledgements": "TEXT DEFAULT ''",
        "funding": "TEXT DEFAULT ''",
        "license_info": "TEXT DEFAULT ''",
        "summary": "TEXT DEFAULT ''",
        "keywords": "TEXT DEFAULT ''",
        "abstract": "TEXT DEFAULT ''",
        "abstract_keywords": "TEXT DEFAULT ''",
        "author_contributions": "TEXT DEFAULT ''",
        "conflicts_of_interest": "TEXT DEFAULT ''",
        "ethics_approval": "TEXT DEFAULT ''",
        "informed_consent": "TEXT DEFAULT ''",
        "data_availability": "TEXT DEFAULT ''",
        "notes": "TEXT DEFAULT ''",
        "article_title": "VARCHAR(300) DEFAULT ''",
        "article_title_en": "VARCHAR(300) DEFAULT ''",
        "corresponding_author": "TEXT DEFAULT ''",
        "content_markdown": "TEXT DEFAULT ''",
        "references": "TEXT DEFAULT ''",
        "guidelines": "TEXT DEFAULT ''",
        "aims_scope": "TEXT DEFAULT ''",
        "editorial_policy": "TEXT DEFAULT ''",
        "peer_review": "TEXT DEFAULT ''",
        "publication_ethics": "TEXT DEFAULT ''",
        "submission_guidelines": "TEXT DEFAULT ''",
        "article_types": "TEXT DEFAULT ''",
        "open_access_policy": "TEXT DEFAULT ''",
        "copyright_policy": "TEXT DEFAULT ''",
        "fees_policy": "TEXT DEFAULT ''",
        "editorial_board": "TEXT DEFAULT ''",
        "contact_info": "TEXT DEFAULT ''",
        "cover_image": "VARCHAR(600) DEFAULT ''",
        "cover_alt": "VARCHAR(300) DEFAULT ''",
        "published": "BOOLEAN DEFAULT TRUE NOT NULL",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    }
    inspector = inspect(db.engine)
    if "journal" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("journal")}
    # Compatível com PostgreSQL em produção e SQLite nos testes. A verificação
    # prévia pelo Inspector torna o DDL idempotente sem depender de
    # "ADD COLUMN IF NOT EXISTS", que não é suportado por todas as versões SQLite.
    with db.engine.begin() as connection:
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(text(
                    f'ALTER TABLE journal ADD COLUMN "{name}" {definition}'
                ))
                existing.add(name)
    db.session.remove()


def ensure_editorial_policy_columns():
    """Adiciona os campos da página sem alterar políticas existentes."""
    inspector = inspect(db.engine)
    if "editorial_policy" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("editorial_policy")}
    with db.engine.begin() as connection:
        for name in ("page_title", "page_description", "page_content"):
            if name not in existing:
                connection.execute(text(f"ALTER TABLE editorial_policy ADD COLUMN \"{name}\" TEXT DEFAULT '' NOT NULL"))
    db.session.remove()


def ensure_article_columns():
    existing = {column["name"] for column in inspect(db.engine).get_columns("article")}
    additions = {"cover_mode": "VARCHAR(24) DEFAULT 'auto' NOT NULL", "background": "VARCHAR(20) DEFAULT 'default' NOT NULL", "cover_video": "VARCHAR(1000) DEFAULT ''", "references": "TEXT DEFAULT '' NOT NULL", "keywords": "VARCHAR(500) DEFAULT ''", "doi": "VARCHAR(180) DEFAULT ''"}
    for name, definition in additions.items():
        if name not in existing:
            db.session.execute(text(f'ALTER TABLE article ADD COLUMN "{name}" {definition}'))
    db.session.commit()


def ensure_article_slugs():
    articles = Article.query.order_by(Article.id).all()
    fixed_slugs = {
        article.slug for article in articles
        if article.slug and not re.fullmatch(r"(?:artigo-)?\d+", article.slug)
    }
    changed = False
    for article in articles:
        if article.slug and not re.fullmatch(r"(?:artigo-)?\d+", article.slug):
            continue
        base = slugify(article.title) or f"artigo-{article.id}"
        candidate, number = base, 2
        while candidate in fixed_slugs:
            candidate, number = f"{base}-{number}", number + 1
        article.slug = candidate
        fixed_slugs.add(candidate)
        changed = True
    if changed:
        db.session.commit()


def ensure_notification_columns():
    columns = {column['name'] for column in inspect(db.engine).get_columns('editorial_notification')}
    if 'html_body' not in columns:
        db.session.execute(text('ALTER TABLE editorial_notification ADD COLUMN html_body TEXT'))
        db.session.commit()
    from mail_schema import upgrade_mail_schema
    upgrade_mail_schema(db.session.connection())
    db.session.commit()


def upgrade_legacy_schema():
    if os.getenv("AUTO_SCHEMA_UPGRADE", "true").lower() == "true":
        # IMPORTANTE: db.create_all() só cria tabelas; não adiciona colunas a tabelas
        # existentes. As migrações leves precisam ocorrer antes de qualquer SELECT
        # ORM de Journal/Article que já inclua colunas recém-adicionadas.
        db.create_all()
        from billing_schema import upgrade_billing_schema
        upgrade_billing_schema(db.session.connection())
        db.session.commit()
        from premium_schema import upgrade_premium_schema
        upgrade_premium_schema(db.session.connection())
        from premium_commercial_schema import upgrade_commercial_schema
        upgrade_commercial_schema(db.session.connection())
        db.session.commit()
        from workflow_schema import upgrade_workflow_schema
        upgrade_workflow_schema(db.session.connection())
        db.session.commit()
        from scientific_metrics_schema import upgrade_scientific_metrics
        upgrade_scientific_metrics(db.session.connection())
        db.session.commit()
        ensure_admin_columns()
        ensure_author_columns()
        ensure_journal_columns()
        ensure_editorial_policy_columns()
        ensure_article_columns()
        ensure_notification_columns()


def seed_database():
    upgrade_legacy_schema()
    prepare_initial_data()


@app.cli.command("preparar-dados")
def prepare_data_command():
    """Prepara os dados iniciais depois de aplicar as migrações."""
    prepare_initial_data()
    click.echo("Dados iniciais preparados.")


def prepare_initial_data():
    from governance import seed_roles
    seed_roles()
    from automation.engine import seed_operators
    seed_operators()
    # Keep the editorial category available on existing installations as well.
    if not Category.query.filter(db.or_(
        Category.name == "Biografia Científica",
        Category.slug == "biografia-cientifica",
    )).first():
        db.session.add(Category(name="Biografia Científica", slug="biografia-cientifica"))
        db.session.commit()
    has_articles = db.session.query(Article.id).first() is not None
    if has_articles:
        ensure_article_slugs()
    if IS_PRODUCTION:
        return
    if not Journal.query.first():
        default_guidelines = (
            "Aceitamos manuscritos originais, revisões e relatos fundamentados. "
            "As submissões devem respeitar princípios de ética, transparência, "
            "atribuição de fontes e revisão editorial."
        )
        for item in DEFAULT_JOURNALS:
            db.session.add(Journal(
                title=item["title"],
                slug=item["slug"],
                abbreviation=item["abbr"],
                field=item["field"],
                description=item["description"],
                frequency=item["frequency"],
                current_issue=item["issue"],
                guidelines=default_guidelines,
                published=True,
            ))
        db.session.commit()
    if has_articles:
        return
    author_names = sorted({item["author"] for item in SEED_ARTICLES})
    authors = {}
    for name in author_names:
        author = Author(
            name=name,
            slug=slugify(name),
            role=("Fundador e Editor-Chefe" if name.casefold() == "mergior alfredo goriate" else "Autor"),
            headline=(
                "Investigador, autor e fundador do Sussurros do Saber."
                if name.casefold() == "mergior alfredo goriate"
                else "Autor do Sussurros do Saber."
            ),
            display_order=(1 if name.casefold() == "mergior alfredo goriate" else 100),
            bio="Autor do Sussurros do Saber.",
        )
        db.session.add(author)
        authors[name] = author
    category_names = sorted({item["category"] for item in SEED_ARTICLES})
    categories = {}
    for name in category_names:
        category = Category(name=name, slug=name.lower().replace("ú", "u").replace("ç", "c").replace("ã", "a").replace(" ", "-"))
        db.session.add(category)
        categories[name] = category
    db.session.flush()
    from content_audit import DEMO_ARTICLE_BODY
    default_body = DEMO_ARTICLE_BODY
    month_numbers = {"Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12}
    for item in SEED_ARTICLES:
        day, month_name, year = item["date"].split()
        published_at = datetime(int(year), month_numbers[month_name], int(day))
        db.session.add(Article(
            title=item["title"], slug=slugify(item["title"]), summary=item["summary"], body=default_body,
            image=item["image"], status="published", read_minutes=int(item["read_time"].split()[0]),
            featured=item.get("featured", False), published_at=published_at, author_rel=authors[item["author"]], category_rel=categories[item["category"]],
        ))
    db.session.commit()


from internationalization import install as install_internationalization
install_internationalization(app)

from indexnow_service import install_indexnow

if app.config["BOOTSTRAP_ON_STARTUP"]:
    with app.app_context():
        seed_database()

install_indexnow(app, SITE_URL)

if __name__ == "__main__":
    app.run(
        debug=(not IS_PRODUCTION and os.getenv("FLASK_DEBUG", "").lower() == "true"),
        host="127.0.0.1",
        port=5000,
    )






