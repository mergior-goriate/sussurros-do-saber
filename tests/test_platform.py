import os
import tempfile
import unittest
from unittest.mock import patch
import re
import time
from pathlib import Path


database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
database_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{database_file.name}"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_TOTP_SECRET"] = "JBSWY3DPEHPK3PXP"
os.environ["ADMIN_PASSWORD"] = "a-strong-test-password"

from app import app, image_srcset, render_markdown, responsive_image_url, safe_image_url, social_image_url  # noqa: E402
from admin import csv_safe_cell, generate_recovery_codes, totp_code, verify_totp  # noqa: E402
from sqlalchemy import inspect
from models import AdminUser, Article, Author, Comment, Journal, db  # noqa: E402


from security_test_support import authenticate_test_session

class PlatformTests(unittest.TestCase):
    def test_google_cmp_is_explicitly_enabled_and_excludes_private_and_error_pages(self):
        from unittest.mock import patch
        with patch.dict(os.environ, {"GOOGLE_CMP_ENABLED": "true"}):
            client = app.test_client()
            for path in ["/", "/politica-de-privacidade", "/politica-de-publicidade"]:
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("js/google-cmp.js", response.get_data(as_text=True))
                self.assertIn('id="googleCmpSettings"', response.get_data(as_text=True))
                self.assertIn("fundingchoicesmessages.google.com", response.headers["Content-Security-Policy"])
            with app.app_context():
                published = Article.public_query().first()
                public_path = "/artigo/" + published.slug
            self.assertIn("js/google-cmp.js", client.get(public_path).get_data(as_text=True))
            for path in ["/artigo/nao-existe-cmp", "/admin/login", "/conta/biblioteca", "/contacto", "/artigos?q=privado"]:
                self.assertNotIn("js/google-cmp.js", client.get(path).get_data(as_text=True))
        with patch.dict(os.environ, {"GOOGLE_CMP_ENABLED": "false"}):
            self.assertNotIn("js/google-cmp.js", app.test_client().get("/").get_data(as_text=True))

    def test_adsense_verification_without_automatic_advertising(self):
        client = app.test_client()
        for path in ["/", "/politica-de-privacidade", "/politica-de-publicidade", "/pagina-inexistente-adsense"]:
            response = client.get(path)
            html = response.get_data(as_text=True)
            if response.status_code == 200:
                self.assertIn('name="google-adsense-account" content="ca-pub-7920973591685812"', html)
            self.assertNotIn("adsbygoogle.js", html)
            self.assertNotIn("googletagmanager.com/ns.html", html)
        response = client.get("/ads.txt")
        self.assertEqual(response.status_code, 200)
        self.assertIn("google.com, pub-7920973591685812, DIRECT, f08c47fec0942fa0", response.get_data(as_text=True))
        self.assertIn("CMP", client.get("/politica-de-privacidade").get_data(as_text=True))


    def test_primary_can_publish_managed_article_directly_via_form(self):
        client = app.test_client()
        with app.app_context():
            author = Author.query.first()
            from models import Category
            category = Category.query.first()
            form = {"title": "Ensaio do fluxo editorial", "summary": "Resumo para verificar a revisão editorial.",
                    "body": "Conteúdo científico revisto e completo. " * 4,
                    "author_id": author.id, "category_id": category.id, "csrf_token": "editorial-csrf"}
        with client.session_transaction() as session:
            session["admin_authenticated"] = True
            session["admin_2fa_verified"] = True
            session["admin_last_activity_at"] = time.time()
            session["admin_superuser"] = True
            authenticate_test_session(session)
            session["csrf_token"] = "editorial-csrf"
        response = client.post("/admin/artigos/novo", data=dict(form, status="review"))
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            article = Article.query.filter_by(title=form["title"]).one()
            identifier, slug = article.id, article.slug
            self.assertEqual(article.status, "review")
        for state, expected_status in [("review", 302)]:
            response = client.post(f"/admin/artigos/{identifier}/editar", data=dict(form, status=state))
            self.assertEqual(response.status_code, expected_status)
            self.assertEqual(client.get(f"/artigo/{slug}").status_code, 404)
            self.assertNotIn(slug.encode(), client.get("/sitemap.xml").data)
            self.assertNotIn(slug.encode(), client.get("/feed.xml").data)
        self.assertEqual(client.post(f"/admin/artigos/{identifier}/editar", data=dict(form, status="published")).status_code, 302)
        self.assertEqual(client.get(f"/artigo/{slug}").status_code, 200)
        with app.app_context():
            from governance_models import ArticleWorkflow
            flow=db.session.get(ArticleWorkflow, identifier)
            self.assertTrue(flow.primary_owned)
            self.assertEqual(flow.stage, 'published')
            self.assertIsNotNone(flow.approved_at)
            self.assertIsNone(flow.reviewed_at)
            db.session.delete(flow)
            db.session.delete(db.session.get(Article, identifier))
            db.session.commit()

    def test_primary_session_requires_configured_and_verified_2fa(self):
        client = app.test_client()
        with client.session_transaction() as session:
            session["admin_authenticated"] = True
            session["admin_superuser"] = True
            session["admin_last_activity_at"] = time.time()
            session["admin_2fa_verified"] = False
        self.assertIn("/admin/login", client.get("/admin").location)
        with client.session_transaction() as session:
            session["admin_authenticated"] = True
            session["admin_last_activity_at"] = time.time()
            session["admin_2fa_verified"] = True
        with patch.dict(os.environ, {"ADMIN_TOTP_SECRET": ""}):
            self.assertIn("/admin/login", client.get("/admin").location)

    def test_expired_two_factor_challenge_is_cleared(self):
        client = app.test_client()
        with client.session_transaction() as session:
            session["pending_2fa_username"] = "admin"
            session["pending_2fa_expires_at"] = time.time() - 1
        response = client.get("/admin/verificar-2fa")
        self.assertIn("/admin/login", response.location)
        with client.session_transaction() as session:
            self.assertNotIn("pending_2fa_username", session)

    def test_database_outage_healthcheck_returns_503_without_details(self):
        from sqlalchemy.exc import OperationalError
        with patch.object(db.session, "execute", side_effect=OperationalError("SELECT 1", {}, Exception("private database details"))):
            response = app.test_client().get("/healthz")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {"ok": False})
        self.assertNotIn(b"private database", response.data)

    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True, RATELIMIT_ENABLED=False)
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        os.unlink(database_file.name)

    def test_cookie_consent_controls_and_policy_are_available(self):
        response = self.client.get("/")
        self.assertIn(b'id="cookieConsent"', response.data)
        self.assertIn(b'id="cookieAccept"', response.data)
        self.assertIn(b'id="cookieReject"', response.data)
        self.assertIn(b'id="cookieSettingsLink"', response.data)
        policy = self.client.get("/politica-de-privacidade")
        self.assertIn("Cookies e consentimento".encode(), policy.data)

    def test_google_search_console_verification_and_discovery(self):
        previous = os.environ.get("GOOGLE_SITE_VERIFICATION")
        os.environ["GOOGLE_SITE_VERIFICATION"] = '"google-test-verification-token"'
        try:
            response = self.client.get("/")
            self.assertIn(
                b'<meta name="google-site-verification" content="google-test-verification-token">',
                response.data,
            )
            self.assertNotIn(b"&quot;google-test-verification-token&quot;", response.data)

            os.environ["GOOGLE_SITE_VERIFICATION"] = (
                '<meta name="google-site-verification" '
                'content="google-complete-tag-verification" />'
            )
            response = self.client.get("/")
            self.assertIn(
                b'<meta name="google-site-verification" content="google-complete-tag-verification">',
                response.data,
            )
        finally:
            if previous is None:
                os.environ.pop("GOOGLE_SITE_VERIFICATION", None)
            else:
                os.environ["GOOGLE_SITE_VERIFICATION"] = previous

        sitemap = self.client.get("/sitemap.xml")
        self.assertEqual(sitemap.status_code, 200)
        self.assertIn(b"<urlset", sitemap.data)
        self.assertIn(b"<lastmod>", sitemap.data)
        self.assertIn("must-revalidate", sitemap.headers.get("Cache-Control", ""))

        robots = self.client.get("/robots.txt")
        self.assertIn(b"Sitemap: https://www.sussurrosdosaber.com/sitemap.xml", robots.data)
        self.assertIn(b"Disallow: /admin", robots.data)

    def test_indexing_directives_distinguish_public_and_private_pages(self):
        homepage = self.client.get("/")
        self.assertIn(
            b'<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">',
            homepage.data,
        )
        filtered = self.client.get("/artigos?categoria=Biologia")
        self.assertIn(b'<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">', filtered.data)
        self.assertNotIn('noindex', filtered.headers.get('X-Robots-Tag', ''))
        favorites = self.client.get("/favoritos")
        self.assertEqual(favorites.status_code, 302)
        self.assertEqual(favorites.location, '/conta/biblioteca')
        self.assertIn('noindex', self.client.get(favorites.location).headers['X-Robots-Tag'])
        missing = self.client.get("/artigo/nao-existe")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.headers["X-Robots-Tag"], "noindex, nofollow")

    def test_sitemap_contains_canonical_articles_and_cover_images(self):
        with app.app_context():
            article = Article.public_card_query().filter(Article.image != "").first()
            self.assertIsNotNone(article)
            article_url = f"https://www.sussurrosdosaber.com/artigo/{article.slug}"
            cover_url = safe_image_url(article.image)
        response = self.client.get("/sitemap.xml")
        self.assertIn(b'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"', response.data)
        self.assertIn(article_url.encode(), response.data)
        self.assertIn(b"<image:image>", response.data)
        self.assertIn(cover_url.replace("&", "&amp;").encode(), response.data)

    def test_website_schema_and_content_language_are_present(self):
        response = self.client.get("/")
        self.assertEqual(response.headers["Content-Language"], "pt-MZ")
        self.assertIn(b'"@type":"WebSite"', response.data)
        self.assertIn(b'"@type":"SearchAction"', response.data)
        self.assertIn(b'<html lang="pt-MZ">', response.data)

    def test_google_tag_manager_consent_mode_and_events(self):
        previous = os.environ.get("GTM_CONTAINER_ID")
        os.environ["GTM_CONTAINER_ID"] = "GTM-TEST123"
        try:
            response = self.client.get("/")
            self.assertIn(b"https://www.googletagmanager.com/gtm.js?id=", response.data)
            self.assertIn(b"GTM-TEST123", response.data)
            self.assertIn(b"analytics_storage:'denied'", response.data)
            self.assertIn("'strict-dynamic'", response.headers["Content-Security-Policy"])
            javascript = self.client.get("/static/js/main.js").data
            for event in [b"article_view", b"search", b"share", b"scroll_depth", b"outbound_click", b"consent_update"]:
                self.assertIn(event, javascript)
        finally:
            if previous is None:
                os.environ.pop("GTM_CONTAINER_ID", None)
            else:
                os.environ["GTM_CONTAINER_ID"] = previous

    def test_footer_publication_family_links_in_both_languages(self):
        from bs4 import BeautifulSoup
        for path, expected, label in [
            ('/', ['/', '/noticias', '/revistas'], 'Publicações da Sussurros do Saber'),
            ('/en/', ['/en/', '/en/news', '/en/revistas'], 'Sussurros do Saber publications'),
            ('/noticias', ['/', '/noticias', '/revistas'], 'Publicações da Sussurros do Saber'),
            ('/en/news', ['/en/', '/en/news', '/en/revistas'], 'Sussurros do Saber publications'),
        ]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            doc = BeautifulSoup(response.get_data(as_text=True), 'html.parser')
            nav = doc.select_one('.site-footer .footer-editions')
            self.assertEqual(nav['aria-label'], label)
            self.assertEqual([a['href'] for a in nav.select('a')], expected)
            self.assertEqual(len(nav.select('img[alt]')), 3)
            for img in nav.select('img'):
                with self.client.get(img['src']) as asset:
                    self.assertEqual(asset.status_code, 200)
                    self.assertEqual(asset.mimetype, 'image/webp')
            self.assertIsNotNone(doc.select_one('.site-footer .footer-layout'))
            self.assertIsNotNone(doc.select_one('.site-footer .footer-bottom'))
            self.assertIsNotNone(doc.select_one('.site-footer-adjacent'))
        doc = BeautifulSoup(self.client.get('/revistas').get_data(as_text=True), 'html.parser')
        self.assertIn('mt-20', doc.select_one('.site-footer')['class'])

    def test_footer_contains_accessible_social_links(self):
        response = self.client.get("/")
        for network in ["Facebook", "Instagram", "YouTube", "X", "WhatsApp"]:
            self.assertIn(f'aria-label="'.encode(), response.data)
            self.assertIn(network.encode(), response.data)
        self.assertNotIn(b'aria-label="Siga-nos no LinkedIn"', response.data)
        previous = os.environ.get("SOCIAL_LINKEDIN_URL")
        os.environ["SOCIAL_LINKEDIN_URL"] = "https://www.linkedin.com/company/sussurros-do-saber/"
        try:
            configured_response = self.client.get("/")
            self.assertIn(b'aria-label="Siga-nos no LinkedIn"', configured_response.data)
            self.assertIn(b"https://www.linkedin.com/company/sussurros-do-saber/", configured_response.data)
        finally:
            if previous is None:
                os.environ.pop("SOCIAL_LINKEDIN_URL", None)
            else:
                os.environ["SOCIAL_LINKEDIN_URL"] = previous
        for address in [
            "https://x.com/sussurrodosaber",
            "https://www.instagram.com/sussurros_do_saber/",
            "https://www.youtube.com/channel/UCMxbh7jSRUxxX48JSWszc8g",
            "https://wa.me/258852130099",
            "https://web.facebook.com/profile.php?id=61584597102517",
        ]:
            self.assertIn(address.replace("&", "&amp;").encode(), response.data)

    def test_about_page_does_not_duplicate_founder_profile(self):
        response = self.client.get("/sobre")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"A miss\xc3\xa3o", response.data)
        self.assertIn(b"A vis\xc3\xa3o editorial", response.data)
        self.assertNotIn(b"Fundador e editor", response.data)
        self.assertNotIn(b"Estudante de Ensino de Biologia", response.data)

    def test_public_routes_and_discovery_files(self):
        for path in ["/", "/artigos", "/autores", "/revistas", "/contacto", "/feed.xml", "/sitemap.xml", "/robots.txt", "/healthz"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_article_sharing_uses_cover_image(self):
        with app.app_context():
            article = Article.public_query().first()
            slug = article.slug
            expected_image = social_image_url(article.image)
        response = self.client.get(f"/artigo/{slug}")
        self.assertEqual(response.status_code, 200)
        escaped_image = expected_image.replace("&", "&amp;")
        self.assertIn(f'<meta property="og:image" content="{escaped_image}">'.encode(), response.data)
        self.assertIn(f'<meta property="og:image:url" content="{escaped_image}">'.encode(), response.data)
        self.assertIn(f'<meta name="twitter:image" content="{escaped_image}">'.encode(), response.data)
        self.assertIn(b'<meta name="twitter:card" content="summary_large_image">', response.data)
        self.assertIn(b'<meta property="og:title" content=', response.data)
        self.assertIn(b'<meta property="og:description" content=', response.data)
        self.assertIn(b'<meta name="twitter:title" content=', response.data)
        self.assertIn(b'<meta name="twitter:description" content=', response.data)
        self.assertIn(f'<link rel="canonical" href="https://www.sussurrosdosaber.com/artigo/{slug}">'.encode(), response.data)
        self.assertNotIn(b'?share=', response.data)

    def test_article_comments_are_moderated_and_escaped(self):
        with app.app_context():
            article = Article.public_query().first()
            slug = article.slug
            article_id = article.id

        page = self.client.get(f"/artigo/{slug}")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'id="comentarios"', page.data)
        self.assertIn(b'class="comments-heading"', page.data)
        self.assertIn(b'class="comment-form-row"', page.data)
        self.assertIn(b'class="comments-list-heading"', page.data)
        token_match = re.search(rb'name="csrf_token" value="([^"]+)"', page.data)
        self.assertIsNotNone(token_match)

        response = self.client.post(
            f"/artigo/{slug}/comentarios",
            data={
                "csrf_token": token_match.group(1).decode(),
                "name": "Leitor Teste",
                "email": "leitor@example.com",
                "body": "<script>alert(1)</script> Comentário científico válido.",
                "website": "",
            },
        )
        self.assertEqual(response.status_code, 303)

        with app.app_context():
            comment = Comment.query.filter_by(article_id=article_id, email="leitor@example.com").first()
            self.assertIsNotNone(comment)
            self.assertFalse(comment.approved)
            comment.approved = True
            db.session.commit()

        published = self.client.get(f"/artigo/{slug}")
        self.assertIn(b"Leitor Teste", published.data)
        self.assertIn(b"&lt;script&gt;alert(1)&lt;/script&gt;", published.data)
        self.assertNotIn(b"<script>alert(1)</script>", published.data)

        with app.app_context():
            Comment.query.filter_by(article_id=article_id, email="leitor@example.com").delete()
            db.session.commit()

    def test_comment_submission_rejects_invalid_csrf(self):
        with app.app_context():
            slug = Article.public_query().first().slug
        response = self.client.post(
            f"/artigo/{slug}/comentarios",
            data={"csrf_token": "invalid", "name": "Teste", "email": "teste@example.com", "body": "Comentário suficientemente longo."},
        )
        self.assertEqual(response.status_code, 303)
        self.assertIn("comentario=invalido", response.location)

    def test_comment_moderation_requires_admin_authentication(self):
        with self.client.session_transaction() as session:
            session.clear()
        response = self.client.get("/admin/comentarios")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login", response.location)

    def test_external_images_keep_their_original_reliable_url(self):
        previous = os.environ.get("CLOUDINARY_CLOUD_NAME")
        os.environ["CLOUDINARY_CLOUD_NAME"] = "demo"
        try:
            source = "https://commons.wikimedia.org/wiki/Special:FilePath/Neuron_Hand-tuned.svg"
            self.assertEqual(social_image_url(source), source)
            self.assertEqual(responsive_image_url(source, 480), source)
            raster = "https://commons.wikimedia.org/wiki/Special:FilePath/E._coli_Bacteria_%287316101966%29.jpg"
            self.assertEqual(
                responsive_image_url(raster, 480),
                "/static/img/e-coli-niaid-960.jpg?v=1a529a99b76b",
            )
            self.assertEqual(responsive_image_url(raster, 330), "/static/img/e-coli-niaid-330.jpg?v=d52ba80e29c6")
            self.assertEqual(image_srcset(raster, [480, 768, 1200]), "/static/img/e-coli-niaid-330.jpg?v=d52ba80e29c6 330w, /static/img/e-coli-niaid-960.jpg?v=1a529a99b76b 960w")
            other_raster = "https://commons.wikimedia.org/wiki/Special:FilePath/Other_photo.jpg"
            self.assertEqual(responsive_image_url(other_raster, 480), "https://commons.wikimedia.org/wiki/Special:Redirect/file/Other_photo.jpg?width=480")
        finally:
            if previous is None:
                os.environ.pop("CLOUDINARY_CLOUD_NAME", None)
            else:
                os.environ["CLOUDINARY_CLOUD_NAME"] = previous

    def test_image_urls_are_normalized_and_unsafe_values_rejected(self):
        self.assertEqual(
            safe_image_url("  //images.example.org/photo.jpg  "),
            "https://images.example.org/photo.jpg",
        )
        self.assertEqual(
            safe_image_url("https://images.example.org/photo.jpg?a=1&amp;b=2"),
            "https://images.example.org/photo.jpg?a=1&b=2",
        )
        self.assertEqual(safe_image_url("javascript:alert(1)"), "")
        self.assertEqual(responsive_image_url("not-a-url", 480), "")

    def test_accented_category_links_are_url_encoded(self):
        homepage = self.client.get("/")
        self.assertIn(b"categoria=Sa%C3%BAde", homepage.data)
        self.assertIn(b"categoria=Educa%C3%A7%C3%A3o", homepage.data)
        self.assertIn(b"categoria=Espa%C3%A7o", homepage.data)
        self.assertNotIn("categoria=Saúde".encode(), homepage.data)

    def test_cache_policy_separates_public_pages_from_comment_tokens(self):
        homepage = self.client.get("/")
        self.assertIn("no-store", homepage.headers.get("Cache-Control", ""))
        with app.app_context():
            slug = Article.public_query().first().slug
        article = self.client.get(f"/artigo/{slug}")
        self.assertEqual(article.headers.get("Cache-Control"), "no-store")

    def test_admin_templates_do_not_use_csp_blocked_inline_handlers(self):
        templates = [
            "articles.html",
            "journals.html",
            "contacts.html",
            "comments.html",
            "administrators.html",
        ]
        for filename in templates:
            source = Path(app.root_path, "templates", "admin", filename).read_text(encoding="utf-8")
            self.assertNotIn("onsubmit=", source)
            self.assertNotIn("onclick=", source)
        self.assertIn(
            "data-confirm=",
            Path(app.root_path, "templates", "admin", "comments.html").read_text(encoding="utf-8"),
        )

    def test_csv_exports_neutralize_spreadsheet_formulas(self):
        self.assertEqual(csv_safe_cell("=HYPERLINK(\"https://example.test\")"), "'=HYPERLINK(\"https://example.test\")")
        self.assertEqual(csv_safe_cell("+123"), "'+123")
        self.assertEqual(csv_safe_cell("texto normal"), "texto normal")

    def test_static_assets_have_long_immutable_cache(self):
        from flask import url_for
        with app.test_request_context():
            asset_url = url_for('static', filename='css/style.css')
        response = self.client.get(asset_url)
        self.assertIn("max-age=31536000", response.headers.get("Cache-Control", ""))
        self.assertIn("immutable", response.headers.get("Cache-Control", ""))

    def test_static_assets_without_current_fingerprint_must_revalidate(self):
        for path in ['/static/css/style.css', '/static/css/style.css?v=old-release', '/static/missing-audit.js']:
            response = self.client.get(path)
            self.assertNotIn('immutable', response.headers['Cache-Control'])
            self.assertIn('must-revalidate', response.headers['Cache-Control'])

    def test_static_url_changes_when_asset_contents_change(self):
        from flask import url_for
        from urllib.parse import parse_qs, urlsplit
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder, patch.object(app, '_static_folder', folder):
            path = Path(folder, 'audit.css')
            path.write_text('body{color:black}')
            with app.test_request_context():
                first = url_for('static', filename='audit.css', v='old-manual-version')
                self.assertEqual(first, url_for('static', filename='audit.css'))
                path.write_text('body{color:white;background:black}')
                second = url_for('static', filename='audit.css')
            self.assertNotEqual(first, second)
            self.assertRegex(parse_qs(urlsplit(second).query)['v'][0], r'^[0-9a-f]{16}$')

    def test_static_gzip_respects_negotiation_ranges_and_cache(self):
        import gzip
        path = '/static/css/style.css'
        plain = self.client.get(path)
        encoded = self.client.get(path, headers={'Accept-Encoding': 'gzip'})
        self.assertEqual(encoded.headers.get('Content-Encoding'), 'gzip')
        self.assertEqual(gzip.decompress(encoded.data), plain.data)
        self.assertLess(len(encoded.data), len(plain.data) // 2)
        self.assertIn('Accept-Encoding', plain.headers['Vary'])
        self.assertIn('Accept-Encoding', encoded.headers['Vary'])
        self.assertNotEqual(plain.headers.get('ETag'), encoded.headers.get('ETag'))
        refused = self.client.get(path, headers={'Accept-Encoding': 'gzip;q=0'})
        self.assertNotIn('Content-Encoding', refused.headers)
        partial = self.client.get(path, headers={'Accept-Encoding': 'gzip', 'Range': 'bytes=0-99'})
        self.assertEqual(partial.status_code, 206)
        self.assertNotIn('Content-Encoding', partial.headers)
        self.assertEqual(partial.data, plain.data[:100])
        for response in (plain, encoded, refused, partial):
            response.close()
        script = self.client.get('/static/js/reader-accounts.js', headers={'Accept-Encoding': 'gzip'})
        self.assertEqual(script.headers.get('Content-Encoding'), 'gzip')
        self.assertIn(b'const dialog', gzip.decompress(script.data))
        script.close()

    def test_articles_are_paginated(self):
        response = self.client.get("/artigos?page=1")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(response.data.count(b'class="story-card group relative"'), 12)

    def test_cloudinary_images_get_responsive_variants(self):
        source = "https://res.cloudinary.com/demo/image/upload/sample.webp"
        self.assertIn(
            "/upload/f_auto,q_auto:eco,w_480,c_limit/",
            responsive_image_url(source, 480),
        )
        self.assertEqual(
            responsive_image_url("https://example.org/image.jpg", 480),
            "https://example.org/image.jpg",
        )

    def test_dropcap_preserves_inline_formatting_and_limits_it_to_one_paragraph(self):
        rendered = str(render_markdown("[capitular] À medida que **observamos** o céu.\n\nOutro parágrafo."))
        self.assertIn('<p class="article-dropcap">À medida que <strong>observamos</strong> o céu.</p>', rendered)
        self.assertIn("<p>Outro parágrafo.</p>", rendered)
        self.assertEqual(rendered.count('class="article-dropcap"'), 1)

    def test_english_dropcap_aliases_render_only_at_paragraph_start(self):
        for marker in ('[drop cap]', '[dropcap]', '[drop-cap]', '[drop_cap]', '[DROP_CAP]',
                       '[ drop  cap ]', '[letra capitular]', '[letra_capitular]', '[DROP CAP]'):
            rendered = str(render_markdown(
                f'{marker} An **opening** paragraph.\n\nA literal {marker} mention.\n\n`{marker}`'))
            self.assertIn('<p class="article-dropcap">An <strong>opening</strong> paragraph.</p>', rendered)
            self.assertIn(f'A literal {marker} mention.', rendered)
            self.assertIn(f'<code>{marker}</code>', rendered)
            self.assertEqual(rendered.count('class="article-dropcap"'), 1)
        self.assertIn('[other_marker] Opening', str(render_markdown('[other_marker] Opening')))
        self.assertIn('<a href="https://example.org">drop cap</a>',
                      str(render_markdown('[drop cap](https://example.org)')))
        code = str(render_markdown('```\n[drop cap] Literal code\n```'))
        self.assertNotIn('class="article-dropcap"', code)

    def test_dropcap_does_not_bypass_sanitization_or_format_code(self):
        rendered = str(render_markdown('[capitular] Texto <img src="x" onerror="alert(1)">'))
        self.assertNotIn("onerror", rendered)
        code = str(render_markdown("\x60\x60\x60\n[capitular] Texto literal\n\x60\x60\x60"))
        self.assertNotIn('class="article-dropcap"', code)
        self.assertIn("[capitular]", code)

    def test_markdown_renders_tables_and_safe_charts(self):
        table = render_markdown("| Grupo | Valor |\n| --- | --- |\n| A | 12 |")
        self.assertIn("<table>", str(table))
        chart = render_markdown("[chart: bar|Participantes|Grupo A=12; Grupo B=8]")
        self.assertIn('class="article-chart"', str(chart))
        self.assertIn("<svg", str(chart))
        self.assertIn("Participantes", str(chart))

    def test_invalid_chart_data_is_not_embedded(self):
        chart = render_markdown("[chart: pie|Teste|A=texto]")
        self.assertNotIn('class="article-chart"', str(chart))

    def test_markdown_linkifies_bare_http_urls_without_nesting_links(self):
        rendered = str(render_markdown(
            "Fonte: https://example.org/estudo.\n\n"
            "[DOI](https://doi.org/10.1000/teste)"
        ))
        self.assertIn(
            '<a href="https://example.org/estudo" rel="noopener noreferrer">https://example.org/estudo</a>.',
            rendered,
        )
        self.assertEqual(rendered.count('href="https://doi.org/10.1000/teste"'), 1)
        self.assertNotIn("<a href=\"<a", rendered)

    def test_markdown_preserves_url_labels_code_and_query_parameters(self):
        rendered = str(render_markdown(
            "# Título\n\n[https://example.org](https://example.org)\n\n"
            "`https://example.org/code`\n\nhttps://example.org/?a=1&b=2"
        ))
        self.assertIn("<h1>Título</h1>", rendered)
        self.assertEqual(rendered.count('href="https://example.org"'), 1)
        self.assertIn('<code>https://example.org/code</code>', rendered)
        self.assertIn('href="https://example.org/?a=1&amp;b=2"', rendered)
        self.assertNotIn("&amp;amp;", rendered)

    def test_dropcap_typography_is_shared_by_public_pages_and_journals(self):
        from bs4 import BeautifulSoup
        with app.app_context():
            journal = Journal(title='Revista de ensaio de capitular', slug='journal-dropcap-regression',
                              field='Biologia', description='Conteúdo de ensaio.', published=True,
                              content_markdown='[drop_cap] Texto inicial.\n\nSegundo parágrafo.')
            db.session.add(journal)
            db.session.commit()
        for path in ('/', '/en/', '/noticias', '/en/news', '/revistas/journal-dropcap-regression', '/premium/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            doc = BeautifulSoup(response.text, 'html.parser')
            self.assertIsNotNone(doc.select_one('link[href*="css/dropcap.css"]'), path)
            if 'journal-dropcap' in path:
                self.assertEqual(doc.select_one('.article-dropcap').get_text(), 'Texto inicial.')

    def test_journal_title_is_rendered_without_removing_introduction(self):
        with app.app_context():
            journal = Journal(title="Revista editorial", slug="titulo-regressao", field="Biologia",
                              description="Uma revista com conteúdo de teste.", published=True,
                              content_markdown="# Título do artigo\n\n## Introdução\n\nPrimeiro parágrafo.")
            db.session.add(journal)
            db.session.commit()
        response = self.client.get("/revistas/titulo-regressao")
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="journal-article-title">Título do artigo</h1>'.encode(), response.data)
        self.assertIn("<h2>Introdução</h2>".encode(), response.data)
        self.assertNotIn(b"heading.remove()", response.data)
        with app.app_context():
            journal = Journal.query.filter_by(slug="titulo-regressao").first()
            journal.content_markdown = "## Introdução\n\nPrimeiro parágrafo."
            db.session.commit()
        response = self.client.get("/revistas/titulo-regressao")
        self.assertIn('id="journal-article-title">Revista editorial</h1>'.encode(), response.data)
        self.assertIn("<h2>Introdução</h2>".encode(), response.data)

    def test_journal_draft_preview_and_pdf_require_administrator(self):
        with app.app_context():
            journal = Journal(title="Revista rascunho", slug="rascunho-regressao", field="Biologia",
                              description="Uma revista ainda em preparação.", published=False,
                              content_markdown="## Introdução\n\nConteúdo reservado.")
            db.session.add(journal)
            db.session.commit()
            identifier = journal.id
        self.assertEqual(self.client.get("/revistas/rascunho-regressao").status_code, 404)
        self.assertEqual(self.client.get("/revistas/rascunho-regressao/baixar.pdf").status_code, 404)
        with self.client.session_transaction() as session:
            session.clear()
        preview = f"/admin/revistas/{identifier}/previsualizar"
        pdf = f"/admin/revistas/{identifier}/baixar.pdf"
        self.assertEqual(self.client.get(preview).status_code, 302)
        self.assertEqual(self.client.get(pdf).status_code, 302)
        with self.client.session_transaction() as session:
            session["admin_authenticated"] = True
            session["admin_last_activity_at"] = time.time()
            authenticate_test_session(session)
        response = self.client.get(preview)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        response = self.client.get(pdf)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.startswith(b"%PDF-"))
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_static_and_health_requests_do_not_update_editorial_database(self):
        with patch("app.Article.publish_due_scheduled") as publish:
            self.client.get("/static/css/style.css").close()
            self.client.get("/healthz")
            publish.assert_not_called()
            self.client.get("/artigos")
            publish.assert_called_once()

    def test_journal_cover_url_with_s_is_accepted_and_long_metadata_rejected(self):
        with self.client.session_transaction() as session:
            session["admin_authenticated"] = True
            session["admin_last_activity_at"] = time.time()
            session["csrf_token"] = "cover-csrf"
            authenticate_test_session(session)
        data = {"csrf_token": "cover-csrf", "title": "Revista de capa", "slug": "capa-regressao",
                "description": "Uma descrição suficientemente longa para validação.",
                "field": "Biologia", "cover_image": "https://images.example.org/cover.webp"}
        self.assertEqual(self.client.post("/admin/revistas/nova", data=data).status_code, 302)
        with app.app_context():
            self.assertEqual(Journal.query.filter_by(slug="capa-regressao").first().cover_image, data["cover_image"])
        data.update(slug="metadata-invalida", doi="x" * 181)
        response = self.client.post("/admin/revistas/nova", data=data)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertIsNone(Journal.query.filter_by(slug="metadata-invalida").first())

    def test_journal_markdown_preview_requires_login_and_csrf(self):
        with self.client.session_transaction() as session:
            session.clear()
        endpoint = "/admin/revistas/previsualizar-markdown"
        self.assertEqual(self.client.post(endpoint).status_code, 302)
        with self.client.session_transaction() as session:
            session["admin_authenticated"] = True
            session["admin_last_activity_at"] = time.time()
            session["csrf_token"] = "preview-token"
            authenticate_test_session(session)
        self.assertEqual(self.client.post(endpoint, data={"content": "# Título"}).status_code, 400)
        response = self.client.post(endpoint, data={
            "csrf_token": "preview-token", "content": "# Título\n\n| A | B |\n| --- | --- |\n| 1 | 2 |",
            "references": "https://example.org/fonte",
            "summary": "Resumo da pré-visualização.", "abstract": "English preview.",
            "author_contributions": "Contributos no preview.", "notes": "Nota do preview.",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("<table>", response.json["html"])
        self.assertIn("Resumo da pré-visualização.", response.json["html"])
        self.assertIn("English preview.", response.json["html"])
        self.assertIn("Contributos no preview.", response.json["html"])
        self.assertIn("Nota do preview.", response.json["references"])
        self.assertIn("<h1>Título</h1>", response.json["html"])
        self.assertIn('href="https://example.org/fonte"', response.json["references"])
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_journal_explicit_draft_and_invalid_form_preserve_input(self):
        with self.client.session_transaction() as session:
            session.clear()
            session["admin_authenticated"] = True
            session["admin_last_activity_at"] = time.time()
            session["csrf_token"] = "draft-token"
            authenticate_test_session(session)
        data = {"csrf_token": "draft-token", "title": "Revista em preparação",
                "slug": "editor-rascunho", "field": "Biologia",
                "description": "Descrição científica com dimensão suficiente.",
                "content_markdown": "## Introdução", "published": "on", "save_mode": "draft"}
        response = self.client.post("/admin/revistas/nova", data=data)
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            self.assertFalse(Journal.query.filter_by(slug="editor-rascunho").first().published)
        data.update(title="Título preservado", slug="editor-invalido", description="Curta")
        response = self.client.post("/admin/revistas/nova", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('value="Título preservado"'.encode(), response.data)
        self.assertIn("## Introdução".encode(), response.data)

    def test_journal_template_uses_references_and_notes_after_content(self):
        template = Path(app.root_path, "templates", "journal.html").read_text(encoding="utf-8")
        content_position = template.index('id="conteudo-revista"')
        references_position = template.index('id="referencias"')
        self.assertGreater(references_position, content_position)
        self.assertIn("<h2>Referências bibliográficas</h2>", template)
        self.assertIn("<h2>Notas</h2>", template)
        self.assertGreater(template.index('id="notas"'), references_position)

    def test_gzip_compression_for_public_html(self):
        response = self.client.get("/", headers={"Accept-Encoding": "gzip"})
        self.assertEqual(response.headers.get("Content-Encoding"), "gzip")
        self.assertIn("Accept-Encoding", response.headers.get("Vary", ""))

    def test_bare_domain_redirects_permanently_to_www(self):
        response = self.client.get(
            "/artigos?page=2",
            base_url="https://sussurrosdosaber.com",
        )
        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.location,
            "https://www.sussurrosdosaber.com/artigos?page=2",
        )

    def test_canonical_metadata_uses_www(self):
        response = self.client.get(
            "/",
            base_url="https://www.sussurrosdosaber.com",
        )
        self.assertIn(
            b'<link rel="canonical" href="https://www.sussurrosdosaber.com/">',
            response.data,
        )

    def test_tailwind_is_local_and_cdn_is_not_loaded(self):
        response = self.client.get("/")
        self.assertIn(b"/static/css/tailwind.css", response.data)
        self.assertNotIn(b"cdn.tailwindcss.com", response.data)

    def test_local_image_fallback_is_available(self):
        response = self.client.get("/static/img/image-fallback.svg")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Imagem temporariamente indispon", response.data)
        script = self.client.get("/static/js/main.js")
        self.assertIn(b"image-fallback.svg", script.data)

    def test_strict_csp_uses_unique_nonce_and_no_inline_handlers(self):
        first = self.client.get("/")
        second = self.client.get("/")
        first_policy = first.headers["Content-Security-Policy"]
        second_policy = second.headers["Content-Security-Policy"]
        first_nonce = re.search(r"script-src 'nonce-([^']+)'", first_policy)
        second_nonce = re.search(r"script-src 'nonce-([^']+)'", second_policy)
        self.assertIsNotNone(first_nonce)
        self.assertIsNotNone(second_nonce)
        self.assertNotEqual(first_nonce.group(1), second_nonce.group(1))
        self.assertIn("'strict-dynamic'", first_policy)
        self.assertIn("script-src-attr 'none'", first_policy)
        self.assertNotIn("'unsafe-inline'", first_policy.split("script-src", 1)[1].split(";", 1)[0])
        self.assertIn(
            f'nonce="{first_nonce.group(1)}"'.encode(),
            first.data,
        )
        self.assertNotIn(b"onclick=", first.data)
        self.assertNotIn(b"onload=", first.data)

    def test_security_headers(self):
        response = self.client.get("/", base_url="https://www.sussurrosdosaber.com")
        self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        self.assertNotIn("cdn.tailwindcss.com", response.headers["Content-Security-Policy"])
        self.assertNotIn("'unsafe-eval'", response.headers["Content-Security-Policy"])
        self.assertIn("max-age=31536000", response.headers["Strict-Transport-Security"])
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")

    def test_input_validation(self):
        self.assertEqual(self.client.post("/api/newsletter", json={"email": "invalido"}).status_code, 400)
        self.assertEqual(self.client.post("/api/contacto", json={}).status_code, 400)
        self.assertEqual(self.client.post("/api/assistente", json={"message": ""}).status_code, 400)

    def test_admin_is_protected_and_not_indexed(self):
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["X-Robots-Tag"], "noindex, nofollow")

    def test_admin_docs_requires_login_and_is_available_to_editors(self):
        with self.client.session_transaction() as session:
            session.clear()
        unauthenticated = self.client.get("/admin/docs")
        self.assertEqual(unauthenticated.status_code, 302)
        self.assertIn("/admin/login", unauthenticated.location)
        with self.client.session_transaction() as session:
            session["admin_authenticated"] = True
            session["admin_2fa_verified"] = True
            session["admin_last_activity_at"] = time.time()
            session["admin_superuser"] = False
            authenticate_test_session(session)
        response = self.client.get("/admin/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<meta name="robots" content="noindex,nofollow">', response.data)
        self.assertIn(b'href="/admin/docs"', response.data)
        self.assertIn("Documentação do site".encode(), response.data)
        self.assertEqual(response.headers["X-Robots-Tag"], "noindex, nofollow")
        with self.client.session_transaction() as session:
            session.clear()

    def test_administrator_can_be_created_and_sign_in(self):
        with self.client.session_transaction() as session:
            session["admin_authenticated"] = True
            session["admin_2fa_verified"] = True
            session["admin_superuser"] = True
            session["admin_last_activity_at"] = time.time()
            session["csrf_token"] = "test-csrf"
            authenticate_test_session(session)
        response = self.client.post("/admin/administradores", data={
            "csrf_token": "test-csrf",
            "display_name": "Editor Científico",
            "username": "editor.cientifico",
            "email": "editor@example.org",
            "password": "uma-palavra-passe-segura",
            "password_confirmation": "uma-palavra-passe-segura",
        })
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            self.assertIsNotNone(AdminUser.query.filter_by(username="editor.cientifico").first())
        with self.client.session_transaction() as session:
            session.clear()
            session["csrf_token"] = "login-csrf"
        response = self.client.post("/admin/login", data={"csrf_token": "login-csrf", "username": "editor.cientifico", "password": "uma-palavra-passe-segura"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/admin"))
        with self.client.session_transaction() as session:
            self.assertFalse(session["admin_superuser"])
            session.clear()
            session["admin_authenticated"] = True
            session["admin_2fa_verified"] = True
            session["admin_superuser"] = True
            session["admin_last_activity_at"] = time.time()
            session["csrf_token"] = "manage-csrf"
            authenticate_test_session(session)
        with app.app_context():
            administrator = AdminUser.query.filter_by(username="editor.cientifico").first()
            administrator_id = administrator.id
        response = self.client.post(f"/admin/administradores/{administrator_id}/editar", data={
            "csrf_token": "manage-csrf",
            "display_name": "Editor Atualizado",
            "username": "editor.atualizado",
            "email": "atualizado@example.org",
            "password": "",
            "password_confirmation": "",
            "active": "on",
        })
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            self.assertIsNotNone(AdminUser.query.filter_by(username="editor.atualizado").first())
        response = self.client.post(
            f"/admin/administradores/{administrator_id}/eliminar",
            data={"csrf_token": "manage-csrf", "confirm": "yes"},
        )
        self.assertEqual(response.status_code, 303)
        with app.app_context():
            self.assertFalse(db.session.get(AdminUser, administrator_id).active)

    def test_secondary_admin_without_2fa_is_forced_to_enrol(self):
        from werkzeug.security import generate_password_hash

        with app.app_context():
            administrator = AdminUser.query.filter_by(username="sem.2fa").first()
            if administrator is None:
                administrator = AdminUser(
                    username="sem.2fa",
                    display_name="Administrador sem 2FA",
                    email="sem.2fa@example.org",
                    password_hash=generate_password_hash("palavra-passe-2fa-obrigatoria"),
                    active=True,
                    two_factor_enabled=False,
                )
                db.session.add(administrator)
                db.session.commit()
            administrator_id = administrator.id

        with self.client.session_transaction() as session:
            session.clear()
            session["admin_authenticated"] = True
            session["admin_2fa_verified"] = True
            session["admin_id"] = administrator_id
            session["admin_superuser"] = False
            session["admin_2fa_verified"] = False
            session["admin_last_activity_at"] = time.time()
            authenticate_test_session(session)
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/admin/seguranca/2fa"))

    def test_totp_algorithm_and_recovery_code_format(self):
        secret = "JBSWY3DPEHPK3PXP"
        code = totp_code(secret)
        self.assertEqual(len(code), 6)
        self.assertTrue(verify_totp(secret, code, window=0))
        recovery_codes = generate_recovery_codes()
        self.assertEqual(len(recovery_codes), 8)
        self.assertTrue(all(re.fullmatch(r"[A-Z2-9]{4}(?:-[A-Z2-9]{4}){2}", item) for item in recovery_codes))

    def test_two_factor_login_requires_second_step(self):
        from werkzeug.security import generate_password_hash

        secret = "JBSWY3DPEHPK3PXP"
        with app.app_context():
            administrator = AdminUser.query.filter_by(username="dois.fatores").first()
            if administrator is None:
                administrator = AdminUser(
                    username="dois.fatores",
                    display_name="Administrador 2FA",
                    email="dois.fatores@example.org",
                    password_hash=generate_password_hash("palavra-passe-2fa-segura"),
                    active=True,
                    two_factor_enabled=True,
                    totp_secret=secret,
                )
                db.session.add(administrator)
                db.session.commit()

        with self.client.session_transaction() as session:
            session.clear()
            session["csrf_token"] = "first-step-csrf"
        first = self.client.post("/admin/login", data={
            "csrf_token": "first-step-csrf",
            "username": "dois.fatores",
            "password": "palavra-passe-2fa-segura",
        })
        self.assertEqual(first.status_code, 302)
        self.assertTrue(first.location.endswith("/admin/verificar-2fa"))
        with self.client.session_transaction() as session:
            self.assertFalse(session.get("admin_authenticated", False))
            second_csrf = session["csrf_token"]

        second = self.client.post("/admin/verificar-2fa", data={
            "csrf_token": second_csrf,
            "code": totp_code(secret),
        })
        self.assertEqual(second.status_code, 302)
        self.assertTrue(second.location.endswith("/admin"))
        with self.client.session_transaction() as session:
            self.assertTrue(session["admin_authenticated"])
            self.assertTrue(session["admin_2fa_verified"])

    def test_author_photo_url_is_saved_and_rendered(self):
        with self.client.session_transaction() as session:
            session.clear()
            session["admin_authenticated"] = True
            session["admin_2fa_verified"] = True
            session["admin_last_activity_at"] = time.time()
            session["csrf_token"] = "author-csrf"
            authenticate_test_session(session)
        response = self.client.post("/admin/autores", data={
            "csrf_token": "author-csrf",
            "name": "Autora com Fotografia",
            "email": "autora.foto@example.org",
            "bio": "Investigadora e divulgadora científica.",
            "photo_url": "https://images.example.org/autora.webp",
        })
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            author = Author.query.filter_by(email="autora.foto@example.org").first()
            self.assertEqual(author.photo, "https://images.example.org/autora.webp")
        response = self.client.get("/autores")
        self.assertIn(b"https://images.example.org/autora.webp", response.data)

    def test_author_profile_is_public_clickable_and_indexed(self):
        with self.client.session_transaction() as session:
            session.clear()
            session["admin_authenticated"] = True
            session["admin_2fa_verified"] = True
            session["admin_last_activity_at"] = time.time()
            session["csrf_token"] = "author-profile-csrf"
            authenticate_test_session(session)
        response = self.client.post("/admin/autores", data={
            "csrf_token": "author-profile-csrf",
            "name": "Investigadora Perfil",
            "slug": "investigadora-perfil",
            "role": "Editora Científica — Biologia",
            "headline": "Investigadora e autora do Sussurros do Saber.",
            "academic_background": "Licenciatura em Ensino de Biologia",
            "institution": "Universidade de Teste",
            "email": "perfil@example.org",
            "bio": "Biografia pública da investigadora.",
            "interests": "Ciência aberta\nEducação",
            "projects": "Projecto Saber",
            "orcid": "0000-0002-1825-0097",
            "google_scholar": "https://scholar.google.com/citations?user=teste",
            "researchgate": "https://www.researchgate.net/profile/Investigadora-Perfil",
            "publications": "Uma publicação científica",
            "editorial_experience": "Revisão científica e edição de conteúdos",
            "display_order": "2",
            "active_present": "1",
            "active": "on",
        })
        self.assertEqual(response.status_code, 302)

        profile = self.client.get("/autor/investigadora-perfil")
        self.assertEqual(profile.status_code, 200)
        for expected in [
            b"Investigadora Perfil", b"Editora Cient\xc3\xadfica",
            b"Investigadora e autora", b"Licenciatura em Ensino de Biologia",
            b"Universidade de Teste", b"Biografia p\xc3\xbablica",
            b"Ci\xc3\xaancia aberta", b"Projecto Saber",
            b"0000-0002-1825-0097", b"Google Scholar", b"ResearchGate",
            b"Uma publica\xc3\xa7\xc3\xa3o cient\xc3\xadfica",
            b"Experi\xc3\xaancia editorial",
            b'"@type": "ProfilePage"',
        ]:
            self.assertIn(expected, profile.data)

        directory = self.client.get("/autores")
        self.assertIn(b"Equipa editorial", directory.data)
        self.assertIn(b"Editora Cient\xc3\xadfica", directory.data)
        self.assertIn(b'href="/autor/investigadora-perfil"', directory.data)

        sitemap = self.client.get("/sitemap.xml")
        self.assertIn(
            b"https://www.sussurrosdosaber.com/autor/investigadora-perfil",
            sitemap.data,
        )

        with app.app_context():
            article = Article.public_query().filter(
                Article.author_id.is_not(None)
            ).first()
            article_slug = article.slug
            author_slug = article.author_rel.slug
        article_page = self.client.get(f"/artigo/{article_slug}")
        self.assertIn(f'href="/autor/{author_slug}"'.encode(), article_page.data)

    def test_author_profile_rejects_duplicate_slug_and_invalid_orcid(self):
        with self.client.session_transaction() as session:
            session.clear()
            session["admin_authenticated"] = True
            session["admin_2fa_verified"] = True
            session["admin_last_activity_at"] = time.time()
            session["csrf_token"] = "author-validation-csrf"
            authenticate_test_session(session)
        response = self.client.post("/admin/autores", data={
            "csrf_token": "author-validation-csrf",
            "name": "Perfil ORCID inválido",
            "slug": "investigadora-perfil",
            "orcid": "orcid-invalido",
        }, follow_redirects=True)
        self.assertIn(b"Esta URL de autor j\xc3\xa1 est\xc3\xa1 em uso.", response.data)

    def test_author_guidelines_custom_content_has_working_anchors(self):
        from types import SimpleNamespace
        with patch("app.EditorialPolicy") as model:
            model.query.first.return_value = SimpleNamespace(author_guidelines="## Tipos de manuscritos\n\n- Investigação original\n- Revisão\n\n## Estrutura\n\n| Campo | Requisito |\n| --- | --- |\n| Resumo | 250 palavras |")
            response = self.client.get("/diretrizes-para-autores")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="#tipos"', response.data)
        self.assertIn(b'<h2 id="tipos">Tipos de manuscritos</h2>', response.data)
        self.assertIn(b'class="article-markdown"', response.data)
        self.assertIn(b"<table>", response.data)
        self.assertIn(b"/diretrizes-para-autores", self.client.get("/sitemap.xml").data)

    def test_editorial_page_migration_preserves_existing_policies(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        from sqlalchemy import create_engine, text
        from app import ensure_editorial_policy_columns
        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.execute(text("CREATE TABLE editorial_policy (id INTEGER PRIMARY KEY, ethics_policy TEXT)"))
                connection.execute(text("INSERT INTO editorial_policy (ethics_policy) VALUES ('Preservar ética')"))
            with patch("app.db", SimpleNamespace(engine=engine, session=Mock())):
                ensure_editorial_policy_columns()
                ensure_editorial_policy_columns()
            with engine.connect() as connection:
                row = connection.execute(text("SELECT ethics_policy, page_title, page_description, page_content FROM editorial_policy")).one()
                self.assertEqual(tuple(row), ("Preservar ética", "", "", ""))
        finally:
            engine.dispose()

    def test_editorial_policies_public_routes_show_admin_content(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        policy = SimpleNamespace(page_title="Política configurada", page_description="Descrição configurada.", page_content="## Missão editável\n\nTexto geral gerido no painel.", author_guidelines="Autores configurados.", reviewer_guidelines="## Avaliação\n\nRevisão configurada.", ethics_policy="Ética configurada.", ai_policy="<script>alert(1)</script>", data_policy="", fees_policy="Sem taxas configuradas.", open_access_policy="Licença configurada.")
        with patch("app.EditorialPolicy") as model:
            model.query.first.return_value = policy
            for path in ("/politica-editorial", "/politicas-editoriais"):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertIn("Revisão configurada.", html)
                self.assertIn("Política configurada", html)
                self.assertIn("Descrição configurada.", html)
                self.assertIn("Texto geral gerido no painel.", html)
                self.assertIn("Autores configurados.", html)
                self.assertNotIn("Missão e independência", html)
                self.assertNotIn("Os princípios que orientam", html)
                self.assertIn("Licença configurada.", html)
                self.assertIn("/diretrizes-para-autores", html)
                self.assertNotIn("<script>alert(1)</script>", html)
            model.query.first.return_value = None
            empty = self.client.get("/politicas-editoriais")
            self.assertEqual(empty.status_code, 200)
            self.assertNotIn("Missão e independência", empty.get_data(as_text=True))
            self.assertNotIn('id="author-guidelines"', empty.get_data(as_text=True))

    def test_author_guidelines_without_types_use_a_valid_content_link(self):
        from types import SimpleNamespace
        with patch("app.EditorialPolicy") as model:
            model.query.first.return_value = SimpleNamespace(author_guidelines="## Preparação\n\nTexto personalizado.")
            response = self.client.get("/diretrizes-para-autores")
        self.assertIn(b'href="#diretrizes-conteudo"', response.data)
        self.assertIn(b'id="diretrizes-conteudo"', response.data)
        self.assertIn(b"Consultar diretrizes", response.data)
        with patch("app.EditorialPolicy") as model:
            model.query.first.return_value = None
            default = self.client.get("/diretrizes-para-autores")
        self.assertEqual(default.status_code, 200)
        self.assertIn(b'<h2 id="tipos">Tipos de manuscrito</h2>', default.data)

    def test_editorial_guidelines_save_and_validate_without_writes_on_get(self):
        from models import EditorialPolicy
        with app.app_context():
            EditorialPolicy.query.delete()
            db.session.commit()
        with self.client.session_transaction() as session:
            session.clear()
        self.assertEqual(self.client.get("/admin/politicas-editoriais").status_code, 302)
        with self.client.session_transaction() as session:
            session["admin_authenticated"] = True
            session["admin_last_activity_at"] = time.time()
            session["csrf_token"] = "guidelines-csrf"
            authenticate_test_session(session)
        form = self.client.get("/admin/politicas-editoriais")
        self.assertEqual(form.status_code, 200)
        self.assertNotIn(b">None</textarea>", form.data)
        self.assertIn(b'/admin/politicas-editoriais', form.data)
        with app.app_context():
            self.assertEqual(EditorialPolicy.query.count(), 0)
        self.assertEqual(self.client.post("/admin/politicas-editoriais", data={"author_guidelines": "invalid csrf"}).status_code, 400)
        with app.app_context():
            self.assertEqual(EditorialPolicy.query.count(), 0)
        content = "## Tipos de manuscritos\n\nTexto guardado pelo painel."
        response = self.client.post("/admin/politicas-editoriais", data={"csrf_token": "guidelines-csrf", "author_guidelines": content, "page_title": "Título editável", "page_description": "Descrição editável", "page_content": "## Política geral\n\nInformações guardadas."})
        self.assertEqual(response.status_code, 302)
        self.assertIn("Informações guardadas.", self.client.get("/politicas-editoriais").get_data(as_text=True))
        self.assertIn(b"Texto guardado pelo painel.", self.client.get("/diretrizes-para-autores").data)
        invalid = self.client.post("/admin/politicas-editoriais", data={"csrf_token": "guidelines-csrf", "author_guidelines": "x" * 100001})
        self.assertEqual(invalid.status_code, 200)
        self.assertIn(b"100000 caracteres", invalid.data)
        with app.app_context():
            self.assertEqual(EditorialPolicy.query.first().author_guidelines, content)
        preview = self.client.post("/admin/politicas-editoriais/previsualizar", data={"csrf_token": "guidelines-csrf", "author_guidelines": "## Tipos de manuscritos\n\n<script>alert(1)</script>"})
        self.assertEqual(preview.status_code, 200)
        self.assertIn('id="tipos"', preview.json["html"])
        self.assertNotIn("<script>", preview.json["html"])
        self.assertEqual(self.client.post("/admin/politicas-editoriais/previsualizar", data={"author_guidelines": "test"}).status_code, 400)
        self.assertEqual(self.client.post("/admin/politicas-editoriais/previsualizar", data={"csrf_token": "guidelines-csrf", "author_guidelines": "x" * 100001}).status_code, 400)
        default_preview = self.client.post("/admin/politicas-editoriais/previsualizar", data={"csrf_token": "guidelines-csrf"})
        self.assertTrue(default_preview.json["default"])
        self.assertIn("Princípios gerais", default_preview.json["html"])
        with app.app_context():
            EditorialPolicy.query.first().reviewer_guidelines = "Preservar revisão"
            db.session.commit()
        self.client.post("/admin/politicas-editoriais", data={"csrf_token": "guidelines-csrf", "author_guidelines": content})
        with app.app_context():
            self.assertEqual(EditorialPolicy.query.first().reviewer_guidelines, "Preservar revisão")
        self.client.post("/admin/politicas-editoriais", data={"csrf_token": "guidelines-csrf", "author_guidelines": "   "})
        self.assertIn("Princípios gerais".encode(), self.client.get("/diretrizes-para-autores").data)

    def test_journal_schema_contains_all_management_columns(self):
        with app.app_context():
            columns = {column["name"] for column in inspect(db.engine).get_columns("journal")}
        self.assertTrue({
            "issn", "frequency", "current_issue", "guidelines",
            "cover_image", "cover_alt", "published", "created_at", "updated_at",
        }.issubset(columns))

    def test_journal_article_migration_preserves_legacy_content(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from sqlalchemy import create_engine, text
        from app import ensure_journal_columns
        from journal_article import ARTICLE_FIELD_LIMITS
        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.execute(text("CREATE TABLE journal (id INTEGER PRIMARY KEY, content_markdown TEXT, \"references\" TEXT, acknowledgements TEXT, funding TEXT)"))
                connection.execute(text("INSERT INTO journal VALUES (1, 'Conteúdo original', 'Referências originais', 'Agradecimentos originais', 'Financiamento original')"))
            with patch("app.db", SimpleNamespace(engine=engine, session=Mock())):
                ensure_journal_columns()
                ensure_journal_columns()
            with engine.connect() as connection:
                row = connection.execute(text("SELECT * FROM journal")).mappings().one()
                self.assertEqual(row["content_markdown"], "Conteúdo original")
                self.assertEqual(row["references"], "Referências originais")
                self.assertEqual(row["acknowledgements"], "Agradecimentos originais")
                self.assertEqual(row["funding"], "Financiamento original")
                self.assertEqual(row["article_title"], "")
                for name in set(ARTICLE_FIELD_LIMITS) - {"acknowledgements", "funding"}:
                    self.assertEqual(row[name], "")
        finally:
            engine.dispose()

    def test_separate_article_title_keeps_legacy_fallback_and_pdf_title(self):
        from types import SimpleNamespace
        from app import journal_article_content, render_journal_pdf
        from unittest.mock import patch
        journal = SimpleNamespace(title="Nome da revista", article_title="Título explícito",
                                  content_markdown="# Título antigo\n\n## Introdução\n\nTexto preservado.",
                                  guidelines="", slug="titulo-separado", description="Descrição",
                                  cover_image="", references="", notes="")
        title, body = journal_article_content(journal)
        self.assertEqual(title, "Título explícito")
        self.assertNotIn("Título antigo", body)
        self.assertIn("Texto preservado.", body)
        from reportlab.platypus import SimpleDocTemplate
        with app.test_request_context(), patch("app.SimpleDocTemplate", wraps=SimpleDocTemplate) as document:
            response = render_journal_pdf(journal)
        self.assertTrue(response.data.startswith(b"%PDF-"))
        self.assertEqual(document.call_args.kwargs["title"], "Título explícito")
        journal.article_title = ""
        self.assertEqual(journal_article_content(journal)[0], "Título antigo")
        journal.content_markdown = "## Introdução\n\nTexto preservado."
        self.assertEqual(journal_article_content(journal)[0], "Nome da revista")

    def test_journal_structured_article_round_trip_order_optional_and_limits(self):
        from bs4 import BeautifulSoup
        from journal_article import ARTICLE_FIELD_LIMITS
        with self.client.session_transaction() as session:
            session.clear()
            session["admin_authenticated"] = True
            session["admin_last_activity_at"] = time.time()
            session["csrf_token"] = "article-fields-csrf"
            authenticate_test_session(session)
        fields = {name: "Texto " + name for name in ARTICLE_FIELD_LIMITS}
        fields.update({"csrf_token": "article-fields-csrf", "title": "Revista estruturada",
                       "article_title": "Título do artigo separado",
                       "article_title_en": "Separate article title", "corresponding_author": "Autora, contacto@example.org",
                       "slug": "artigo-estruturado", "field": "Biologia", "published": "on",
                       "description": "Descrição completa da revista de artigo estruturado.",
                       "content_markdown": "# Título científico\n\n## Introdução\n\nTexto científico.",
                       "references": "Referência verificável."})
        response = self.client.post("/admin/revistas/nova", data=fields)
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            journal = Journal.query.filter_by(slug="artigo-estruturado").one()
            identifier = journal.id
            self.assertEqual(journal.article_title_en, "Separate article title")
            self.assertEqual(journal.corresponding_author, "Autora, contacto@example.org")
            for name in ARTICLE_FIELD_LIMITS:
                self.assertEqual(getattr(journal, name), fields[name])
        page = self.client.get("/revistas/artigo-estruturado")
        soup = BeautifulSoup(page.data, "html.parser")
        self.assertEqual(soup.select_one("#journal-article-title").get_text(), "Título do artigo separado")
        self.assertNotIn("Título científico", soup.select_one(".journal-sections").get_text())
        headings = [item.get_text() for item in soup.select(".journal-sections h2")]
        self.assertEqual(headings, ["Resumo", "Palavras-chave", "Abstract", "Keywords", "Introdução",
                                   "Contribuição dos autores", "Agradecimentos", "Financiamento",
                                   "Conflitos de interesse", "Aprovação ética", "Consentimento informado",
                                   "Disponibilidade de dados", "Referências bibliográficas", "Notas"])
        form = self.client.get(f"/admin/revistas/{identifier}/editar")
        editor = BeautifulSoup(form.data, "html.parser")
        for name in ARTICLE_FIELD_LIMITS:
            controls = editor.select(f'[name="{name}"]')
            self.assertEqual(len(controls), 1)
            self.assertFalse(controls[0].has_attr("required"))
            self.assertEqual(controls[0].get_text(), fields[name])
        invalid = dict(fields, keywords="x" * 2001)
        response = self.client.post(f"/admin/revistas/{identifier}/editar", data=invalid)
        self.assertEqual(response.status_code, 200)
        self.assertIn("2000", response.get_data(as_text=True))
        with app.app_context():
            self.assertEqual(db.session.get(Journal, identifier).keywords, fields["keywords"])
        # Empty optional declarations remove their public sections without removing the body.
        cleared = dict(fields, **{name: "" for name in ARTICLE_FIELD_LIMITS})
        self.assertEqual(self.client.post(f"/admin/revistas/{identifier}/editar", data=cleared).status_code, 302)
        soup = BeautifulSoup(self.client.get("/revistas/artigo-estruturado").data, "html.parser")
        self.assertEqual([item.get_text() for item in soup.select(".journal-sections h2")], ["Introdução", "Referências bibliográficas"])

    def test_journal_can_be_managed_and_published(self):
        with self.client.session_transaction() as session:
            session.clear()
            session["admin_authenticated"] = True
            session["admin_2fa_verified"] = True
            session["admin_last_activity_at"] = time.time()
            session["csrf_token"] = "journal-csrf"
            authenticate_test_session(session)
        response = self.client.post("/admin/revistas/nova", data={
            "csrf_token": "journal-csrf",
            "title": "Revista de Teste Científico",
            "description": "Uma descrição suficientemente completa para a revista científica.",
            "field": "Ciências Biológicas",
            "abbreviation": "RTC",
            "issn": "1234-567X",
            "frequency": "Semestral",
            "current_issue": "Vol. 1 · N.º 1",
            "guidelines": "Diretrizes editoriais da revista.",
            "published": "on",
        })
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            journal = Journal.query.filter_by(slug="revista-de-teste-cientifico").first()
            self.assertIsNotNone(journal)
            self.assertTrue(journal.published)
        response = self.client.get("/revistas/revista-de-teste-cientifico")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Revista de Teste Científico".encode(), response.data)

    def test_journal_authors_and_editorial_information_round_trip(self):
        from journal_metadata import journal_authors
        with self.client.session_transaction() as session:
            session.clear()
            session["admin_authenticated"] = True
            session["admin_last_activity_at"] = time.time()
            session["csrf_token"] = "journal-metadata-csrf"
            authenticate_test_session(session)
        fields = {
            "csrf_token": "journal-metadata-csrf", "title": "Revista metadata regressao",
            "description": "Descrição científica completa para verificar as informações editoriais.",
            "field": "Biologia", "slug": "metadata-regressao", "published": "on",
            "content_markdown": "# Artigo com autores\n\n## Resultados\n\nConteúdo.",
            "authors_structured": "1", "author_name": ["Autora Um", "Autor Dois"],
            "author_orcid": ["http://orcid.org/0000-0002-1825-0097", ""],
            "author_description": ["Investigadora de Biologia.", "Contribuição: análise dos resultados."],
            "copyright_policy": "Direitos confirmados pelos autores.",
            "submission_history": "Submetido em 01/10/2026.",
            "acknowledgements": "Agradecemos à equipa de laboratório.",
            "funding": "Financiamento do projeto de teste.",
            "license_info": "[Licença de teste](https://example.org/licenca)",
            "cover_image": "https://example.org/capa.png"
        }
        response = self.client.post("/admin/revistas/nova", data=fields)
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            journal = Journal.query.filter_by(slug="metadata-regressao").one()
            identifier = journal.id
            authors = journal_authors(journal)
            self.assertEqual(len(authors), 2)
            self.assertEqual(authors[0]["orcid"], "https://orcid.org/0000-0002-1825-0097")
            self.assertEqual(authors[1]["description"], fields["author_description"][1])
            self.assertIn("Autora Um", journal.authors_orcid)
            self.assertEqual(journal.funding, fields["funding"])
        public = self.client.get("/revistas/metadata-regressao")
        self.assertEqual(public.status_code, 200)
        for value in ("Autora Um", "Autor Dois", "Investigadora de Biologia.", "fa-brands fa-orcid",
                      "https://orcid.org/0000-0002-1825-0097", "Direitos autorais", "Histórico de submissões",
                      "Agradecimentos", "Financiamento", "Informações sobre a licença",
                      "Financiamento do projeto de teste.", 'href="https://example.org/licenca"'):
            self.assertIn(value.encode(), public.data)
        editor = self.client.get(f"/admin/revistas/{identifier}/editar")
        self.assertIn(b"Investigadora de Biologia.", editor.data)
        self.assertIn(b"Financiamento do projeto de teste.", editor.data)
        fields.update(author_name=["Autora Atualizada"], author_orcid=[""], author_description=["Descrição atualizada."])
        self.assertEqual(self.client.post(f"/admin/revistas/{identifier}/editar", data=fields).status_code, 302)
        with app.app_context():
            journal = db.session.get(Journal, identifier)
            self.assertEqual(len(journal_authors(journal)), 1)
            self.assertEqual(journal_authors(journal)[0]["name"], "Autora Atualizada")
        fields.update(author_name=[""], author_orcid=["https://orcid.org.evil.test/0000-0002-1825-0097"], author_description=[""])
        invalid = self.client.post(f"/admin/revistas/{identifier}/editar", data=fields)
        self.assertEqual(invalid.status_code, 200)
        self.assertIn("Informe uma URL ORCID válida".encode(), invalid.data)
        with app.app_context():
            self.assertEqual(journal_authors(db.session.get(Journal, identifier))[0]["name"], "Autora Atualizada")
        fields.update(author_name=[], author_orcid=[], author_description=[])
        self.assertEqual(self.client.post(f"/admin/revistas/{identifier}/editar", data=fields).status_code, 302)
        with app.app_context():
            self.assertEqual(journal_authors(db.session.get(Journal, identifier)), [])

    def test_secondary_administrator_cannot_manage_accounts(self):
        with self.client.session_transaction() as session:
            session.clear()
            session["admin_authenticated"] = True
            session["admin_2fa_verified"] = True
            session["admin_superuser"] = False
            session["admin_last_activity_at"] = time.time()
            session["csrf_token"] = "secondary-csrf"
            authenticate_test_session(session)
        self.assertEqual(self.client.get("/admin/administradores").status_code, 403)

    def test_homepage_uses_four_most_read_and_nine_latest_discoveries(self):
        template = Path(app.root_path, "templates", "index.html").read_text(encoding="utf-8")
        self.assertIn("articles[1:5]", template)
        self.assertIn("articles[1:10]", template)
        response = self.client.get("/")
        self.assertLessEqual(response.data.count(b'class="number-story group"'), 4)
        self.assertLessEqual(response.data.count(b'class="story-card group"'), 9)

    def test_z_homepage_supports_empty_database(self):
        with app.app_context():
            Article.query.delete()
            try:
                response = self.client.get("/")
                self.assertEqual(response.status_code, 200)
                self.assertIn("Novos artigos estão a ser preparados".encode(), response.data)
            finally:
                db.session.rollback()


if __name__ == "__main__":
    unittest.main()













