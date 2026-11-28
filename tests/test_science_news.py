"""Public and editorial integration tests for Science News."""
from datetime import date, timedelta
import secrets
import time
import unittest
from xml.etree import ElementTree

from bs4 import BeautifulSoup

import test_platform  # Set up the isolated application database before importing it.
from app import app, SITE_URL
from extensions import limiter
from governance_models import GovernanceAudit, TeamAppointment, TeamMember, TeamRole
from models import AdminUser, Article, Author, Category, db, utcnow
from news_models import NewsStory, NewsVersion
from security_test_support import authenticate_test_session


class ScienceNewsTests(unittest.TestCase):
    def setUp(self):
        self.context = app.app_context()
        self.context.push()
        self.previous_limiter = limiter.enabled
        limiter.enabled = False
        self.addCleanup(self.context.pop)
        self.addCleanup(setattr, limiter, 'enabled', self.previous_limiter)
        self.token = secrets.token_hex(4)
        self.author = Author(name='Autoria de ensaio', slug='autor-news-' + self.token)
        self.topic = Category.query.filter_by(name='Saúde').one()
        self.other_topic = Category.query.filter_by(name='Ambiente').one()
        db.session.add(self.author)
        db.session.commit()
        self.client = app.test_client()
        self.addCleanup(self.remove_stories)

    def remove_stories(self):
        db.session.rollback()
        NewsVersion.query.delete()
        NewsStory.query.delete()
        db.session.commit()

    def story(self, title, *, locale='pt', story=None, offset=0, status='published', featured=False, topic=None, with_image=False):
        if story is None:
            story = NewsStory()
            db.session.add(story)
            db.session.flush()
        item = NewsVersion(
            story_id=story.id, language=locale, title=title, slug='news-' + secrets.token_hex(5),
            summary='Test summary' if locale == 'en' else 'Resumo de ensaio',
            body='Text for the test story' if locale == 'en' else 'Texto da notícia de ensaio',
            image='https://example.org/news-cover.jpg' if with_image else '',
            image_alt='Imagem de ensaio' if with_image else '',
            author=self.author, category=topic or self.topic, status=status, featured=featured,
            sources=[{'label': 'Primary source', 'url': 'https://example.org/research'}],
            published_at=utcnow() + timedelta(days=offset) if status == 'published' else None,
        )
        db.session.add(item)
        db.session.commit()
        return story, item

    def soup(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        return BeautifulSoup(response.text, 'html.parser')

    def select_language(self, document, locale):
        language = 'pt-MZ' if locale == 'pt' else 'en'
        link = document.select_one(f'.language-selector a[lang="{language}"]')
        return self.client.get(link['href'], follow_redirects=True)

    def headings(self, soup, container):
        return [card.select_one('h2, h3').get_text(strip=True)
                for card in soup.select(container + ' .news-card')]

    def test_dropcap_alias_is_rendered_in_news_in_both_languages(self):
        story, pt = self.story('Notícia de ensaio da capitular')
        _, en = self.story('Drop cap news fixture', locale='en', story=story)
        pt.body = '[capitular] Parágrafo inicial.'
        en.body = '[drop_cap] Opening paragraph.'
        db.session.commit()
        for prefix, item, expected in [('/noticias/', pt, 'Parágrafo inicial.'), ('/en/news/', en, 'Opening paragraph.')]:
            doc = self.soup(prefix + item.slug)
            self.assertEqual(doc.select_one('.news-body .article-dropcap').get_text(), expected)
            self.assertIsNotNone(doc.select_one('link[href*="css/dropcap.css"]'))
            self.assertNotIn('[drop_cap]', doc.select_one('.news-body').get_text())

    def test_feature_home_visibility_order_and_theme_navigation(self):
        self.assertIsNone(self.soup('/').select_one('#home-news-title'))
        self.story('Notícia escolhida', offset=-4, featured=True, with_image=True)
        _, current = self.story('Notícia mais recente', offset=-1, with_image=True)
        self.story('Notícia intermédia', offset=-2)
        self.story('Notícia de outro tema', offset=-3, topic=self.other_topic)
        self.story('Notícia futura', offset=1)
        self.story('Rascunho privado', status='draft')
        self.story('English headline', locale='en', offset=-1)

        home = self.soup('/')
        self.assertEqual(self.headings(home, '[aria-labelledby="home-news-title"]'),
                         ['Notícia mais recente', 'Notícia intermédia', 'Notícia de outro tema'])
        self.assertEqual(len(home.select('.home-news-feature .news-card')), 1)
        self.assertEqual(len(home.select('.home-news-rail .news-card')), 2)
        self.assertEqual(home.select_one('.home-news-feature h3').text.strip(), 'Notícia mais recente')
        self.assertEqual([x.text.strip() for x in home.select('.home-news-rail h3')],
                         ['Notícia intermédia', 'Notícia de outro tema'])
        for card in home.select('[aria-labelledby="home-news-title"] .news-card'):
            cover = card.select_one('a.news-cover-link')
            if card.select_one('img.news-cover'):
                self.assertIsNotNone(cover)
                self.assertEqual(cover['href'], card.select_one('.news-card-copy h3 a')['href'])
            else:
                self.assertIsNone(cover)
        index = self.soup('/noticias')
        newsletter = index.select_one('.news-page-newsletter')
        self.assertIsNotNone(newsletter)
        self.assertIsNotNone(newsletter.select_one('#newsletterForm input[name="email"][type="email"]'))
        self.assertEqual(newsletter.select_one('#newsletterForm button')['type'], 'submit')
        self.assertEqual(newsletter.select_one('#newsletterMessage')['role'], 'status')
        self.assertEqual(len(index.select('#newsletterForm')), 1)
        self.assertIsNotNone(index.select_one('link[href*="news-page-newsletter.css"]'))
        self.assertIsNone(index.select_one('.sn-africa'))
        english_news = self.soup('/en/news')
        self.assertIsNone(english_news.select_one('.sn-africa'))
        self.assertIsNotNone(english_news.select_one('.news-page-newsletter #newsletterForm'))
        self.assertEqual(english_news.select_one('.news-page-newsletter #newsletter-email')['type'], 'email')
        lead_cover = index.select_one('.news-lead a.news-cover-link')
        self.assertIsNotNone(lead_cover)
        self.assertEqual(lead_cover['href'], index.select_one('.news-lead h2 a')['href'])
        self.assertEqual(self.headings(index, '.news-lead'), ['Notícia escolhida'])
        self.assertEqual(self.headings(index, '.news-grid'),
                         ['Notícia mais recente', 'Notícia intermédia', 'Notícia de outro tema'])
        self.assertEqual(index.select_one('#mainNav [href="/noticias"]').text.strip(), 'Notícias')
        self.assertEqual(self.select_language(index, 'en').request.path, '/en/news')
        self.assertEqual(self.headings(self.soup('/en/'), '[aria-labelledby="home-news-title"]'),
                         ['English headline'])
        self.client = app.test_client()
        filtered = self.soup('/noticias?tema=' + self.topic.slug)
        self.assertIsNone(filtered.select_one('.news-lead'))
        self.assertEqual(self.headings(filtered, '.news-grid'),
                         ['Notícia mais recente', 'Notícia intermédia', 'Notícia escolhida'])
        detail = self.soup(filtered.find('a', string=current.title)['href'])
        self.assertEqual(detail.select_one('.news-back')['href'], '/noticias?tema=' + self.topic.slug)
        self.assertIsNotNone(self.soup('/noticias?tema=outro').select_one('.empty-state'))
        self.assertEqual(self.client.get('/noticias').headers['Cache-Control'], 'no-store')

    def test_ss_news_masthead_and_hyperlinks_follow_locale_and_topics(self):
        _, pt = self.story('Destaque de ensaio', featured=True, with_image=True)
        _, en = self.story('Featured fixture', locale='en', featured=True, with_image=True)
        self.story('Outra notícia de ensaio', topic=self.other_topic)
        for route, item, tagline, home in [
            ('/noticias', pt, 'Notícias de ciência e investigação', '/'),
            ('/en/news', en, 'Science and research news', '/en/'),
        ]:
            listing = self.soup(route)
            self.assertEqual(listing.select_one('.sn-brand-link')['href'], route)
            self.assertEqual(listing.select_one('.sn-brand-link img')['alt'], 'SS News')
            self.assertEqual(listing.select_one('.sn-brand-copy p').text, tagline)
            self.assertEqual(listing.select_one('.sn-breadcrumb a')['href'], home)
            self.assertEqual(listing.select_one('.sn-topic-nav [aria-current="page"]')['href'], route)
            topic = listing.select_one(f'.sn-topic-nav [href="{route}?tema={self.topic.slug}"]')
            self.assertIsNotNone(topic)
            selected = self.soup(topic['href'])
            self.assertEqual(selected.select_one('.sn-topic-nav [aria-current="page"]')['href'], topic['href'])
            lead = listing.select_one('.news-lead .news-card')
            self.assertEqual(lead.select_one('.sn-read-link')['href'], route + '/' + item.slug)
            self.assertEqual(lead.select_one('.news-cover-link')['href'], route + '/' + item.slug)
        self.assertIsNone(self.soup('/').select_one('.sn-masthead'))
        with self.client.get('/static/img/ss-news-logo.webp') as logo:
            self.assertEqual(logo.status_code, 200)

    def test_filter_and_page_survive_language_switch_and_detail_links(self):
        for i in range(13):
            self.story(f'Notícia {i:02d}', offset=-i - 1)
            self.story(f'Story {i:02d}', locale='en', offset=-i - 1)
        path = '/noticias?tema=' + self.topic.slug
        page = self.soup(path)
        page_two = page.select_one('a[rel=next]')['href']
        self.assertEqual(page_two, path + '&page=2')
        page = self.soup(page_two)
        self.assertEqual(self.headings(page, '.news-grid'), ['Notícia 12'])
        visible = page.find('a', string='Notícia 12')
        self.assertEqual(self.soup(visible['href']).select_one('.news-back')['href'], page_two)
        english = self.select_language(page, 'en')
        self.assertEqual(english.request.full_path, '/en/news?tema=' + self.topic.slug + '&page=2')
        self.assertEqual(self.headings(BeautifulSoup(english.text, 'html.parser'), '.news-grid'), ['Story 12'])

    def test_direct_english_route_switch_and_private_versions_in_sitemap(self):
        story, pt = self.story('Notícia em português', offset=-2)
        _, en = self.story('Science story in English', locale='en', story=story, status='draft')
        en_path = '/en/news/' + en.slug
        pt_path = '/noticias/' + pt.slug
        self.assertEqual(self.client.get(en_path).status_code, 404)
        index = self.soup('/en/news')
        self.assertEqual(index.h1.text.strip(), 'Science News')
        self.assertEqual(index.select_one('#mainNav [href="/en/news"]').text.strip(), 'News')
        self.assertEqual(index.select_one('label[for="news-topic"]').text, 'Topic')
        self.assertNotIn(en.title, index.get_text())
        notice = self.select_language(self.soup(pt_path), 'en')
        self.assertEqual(notice.request.path, pt_path)
        page = BeautifulSoup(notice.text, 'html.parser')
        self.assertEqual(page.h1.text, pt.title)
        self.assertIn('This article is not yet available in English', page.select_one('.news-language-notice').text)
        self.assertNotIn(en_path, self.client.get('/sitemap.xml').text)

        en.status, en.published_at = 'published', utcnow()
        db.session.commit()
        response = self.select_language(self.soup(pt_path), 'en')
        self.assertEqual(response.request.path, en_path)
        page = BeautifulSoup(response.text, 'html.parser')
        self.assertEqual(page.h1.text, en.title)
        self.assertIn(en.summary, page.select_one('.article-summary').text)
        self.assertIn(en.body, page.select_one('.news-body').text)
        self.assertEqual(page.select_one('link[rel=canonical]')['href'], SITE_URL + en_path)
        self.assertEqual(page.select_one('link[hreflang=pt-MZ]')['href'], SITE_URL + pt_path)
        self.assertEqual(page.select_one('.news-sources a')['href'], en.sources[0]['url'])
        namespace = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        sitemap = ElementTree.fromstring(self.client.get('/sitemap.xml').data)
        urls = [node.text for node in sitemap.findall('s:url/s:loc', namespace)]
        self.assertIn(SITE_URL + en_path, urls)
        self.assertIn(SITE_URL + '/en/news', urls)
        self.assertEqual(self.select_language(page, 'pt').request.path, pt_path)

        pt.status = 'withdrawn'
        db.session.commit()
        response = self.select_language(self.soup(en_path), 'pt')
        self.assertEqual(response.request.path, en_path)
        page = BeautifulSoup(response.text, 'html.parser')
        link = page.select_one('.news-language-notice a')
        self.assertEqual(link.text, 'Ver Notícias de Ciência em português')
        self.assertEqual(self.client.get(link['href'], follow_redirects=True).request.path, '/noticias')
        self.assertEqual(self.client.get(pt_path).status_code, 404)
        self.assertNotIn(pt_path, self.client.get('/sitemap.xml').text)

    def test_google_preferred_source_button_only_on_individual_publications(self):
        story, pt = self.story('Notícia de ensaio')
        _, en = self.story('Test story', locale='en', story=story)
        article = Article.public_query().first()
        script_url = 'https://news.google.com/swg/js/v1/publisher.js'
        fallback_url = 'https://www.google.com/preferences/source?q=www.sussurrosdosaber.com'
        for path, locale in [
            ('/noticias/' + pt.slug, 'pt'), ('/en/news/' + en.slug, 'en'),
            ('/artigo/' + article.slug, 'pt'),
        ]:
            with self.subTest(path=path):
                response = app.test_client().get(path)
                self.assertEqual(response.status_code, 200)
                page = BeautifulSoup(response.text, 'html.parser')
                scripts = page.select(f'script[src="{script_url}"]')
                self.assertEqual(len(scripts), 1)
                self.assertTrue(scripts[0].has_attr('async'))
                self.assertIn("'nonce-" + scripts[0]['nonce'] + "'", response.headers['Content-Security-Policy'])
                buttons = page.select('[google-add-preferred-source-btn]')
                self.assertEqual(len(buttons), 1)
                self.assertEqual(buttons[0]['data-lang'], locale)
                fallback = page.select_one('.google-preferred-source .google-preferred-source-fallback')
                self.assertEqual(fallback['href'], fallback_url)
                self.assertEqual(fallback.get_text(strip=True), 'Add as preferred source' if locale == 'en' else 'Adicionar como fonte preferida')
                self.assertFalse(fallback.has_attr('hidden'))
                self.assertIsNotNone(page.select_one('.author-preferred-row .google-preferred-source'))
                info = page.select_one('.google-preferred-source-info-button')
                tooltip = page.select_one('#google-preferred-source-tooltip')
                self.assertEqual(info['aria-describedby'], tooltip['id'])
                self.assertEqual(info['aria-expanded'], 'false')
                self.assertEqual(tooltip['role'], 'tooltip')
                self.assertTrue(tooltip.has_attr('hidden'))
                self.assertEqual(info['aria-label'], 'About Google preferred sources' if locale == 'en' else 'Sobre as fontes preferidas da Google')
                self.assertIn('By adding Sussurros do Saber' if locale == 'en' else 'Ao adicionar a Sussurros do Saber', tooltip.get_text(strip=True))
        for path in ['/', '/en/', '/artigos', '/en/artigos', '/noticias', '/en/news',
                     '/contacto', '/admin/login', '/artigo/nao-existe-preferred-source']:
            with self.subTest(path=path):
                page = BeautifulSoup(app.test_client().get(path).text, 'html.parser')
                self.assertIsNone(page.select_one('.google-preferred-source'))
                self.assertIsNone(page.select_one('[google-add-preferred-source-btn]'))
                self.assertIsNone(page.select_one(f'script[src="{script_url}"]'))
                self.assertIsNone(page.select_one('script[src*="js/google-preferred-source.js"]'))
                self.assertIsNone(page.select_one('link[href*="css/google-preferred-source.css"]'))

    def test_related_article_requires_public_content_in_the_requested_language(self):
        story, pt = self.story('Notícia de ensaio')
        _, en = self.story('Test story', locale='en', story=story)
        related = Article.query.filter_by(status='published').first()
        pt.related_article_id = en.related_article_id = related.id
        db.session.commit()
        self.assertIsNotNone(self.soup('/noticias/' + pt.slug).select_one('.news-related a'))
        self.assertIsNone(self.soup('/en/news/' + en.slug).select_one('.news-related a'))

    def auth(self, role=None):
        account_id = None
        if role:
            username = 'news-' + secrets.token_hex(5)
            account = AdminUser(username=username, display_name=username, password_hash='fixture',
                                governance_managed=True, two_factor_enabled=True, totp_secret='JBSWY3DPEHPK3PXP')
            member = TeamMember(name=username, email=username + '@example.org', admin=account,
                                status='active', accepted_at=utcnow())
            db.session.add(TeamAppointment(member=member, role=TeamRole.query.filter_by(code=role).one(),
                                           starts_on=date.today()))
            db.session.commit()
            account_id = account.id
        with self.client.session_transaction() as state:
            state.clear()
            state.update(admin_authenticated=True, admin_id=account_id, admin_superuser=not role,
                         admin_last_activity_at=time.time(), admin_2fa_verified=True, csrf_token='news-csrf')
            authenticate_test_session(state)
        return member if role else None

    def form(self, locale='pt', **overrides):
        fields = dict(action='save', language=locale, title='Ensaio ' + self.token,
                      slug='editorial-' + self.token, author_id=self.author.id, category_id=self.topic.id,
                      summary='Resumo editorial', body='Texto com um facto de ensaio.',
                      image='https://example.org/cover.jpg', image_alt='Descrição da capa',
                      image_credit='Arquivo de ensaio', sources_text='Estudo original | https://example.org/research',
                      evidence='preprint', evidence_note='A revisão por pares está pendente.')
        return dict(fields, **overrides)

    def post(self, path, **fields):
        return self.client.post(path, data=dict(csrf_token='news-csrf', **fields))

    def action(self, item, action, **fields):
        db.session.refresh(item)
        return self.post('/admin/noticias/' + str(item.id), action=action, revision=item.revision, **fields)

    def test_editorial_roles_validation_feature_withdraw_and_revisions(self):
        self.assertEqual(self.client.get('/admin/noticias').status_code, 302)
        self.auth('secretariat')
        self.assertEqual(self.client.get('/admin/noticias').status_code, 403)
        self.assertEqual(self.post('/admin/noticias/nova', **self.form()).status_code, 403)

        reviewer = self.auth('portal_reviewer')
        self.auth('portal_editor')
        self.assertEqual(self.post('/admin/noticias/nova', **self.form(sources_text='http://example.org')).status_code, 400)
        self.assertEqual(self.post('/admin/noticias/nova', **self.form()).status_code, 303)
        item = NewsVersion.query.filter_by(title='Ensaio ' + self.token).one()
        self.assertEqual(self.client.get('/admin/noticias/' + str(item.id)).status_code, 200)
        self.assertEqual(self.action(item, 'assign', reviewer_id=reviewer.id).status_code, 303)
        reviewer_id = reviewer.admin_id
        with self.client.session_transaction() as state:
            state['admin_id'] = reviewer_id
            authenticate_test_session(state)
        self.assertEqual(self.action(item, 'reviewed', review_note='Fontes e atribuição verificadas.').status_code, 303)
        self.auth('portal_editor')
        self.assertEqual(self.action(item, 'approve').status_code, 303)
        self.assertEqual(self.action(item, 'publish').status_code, 403)
        self.auth('publisher')
        self.assertEqual(self.action(item, 'publish').status_code, 303)
        _, other = self.story('Outro destaque', offset=-2, featured=True)
        self.assertEqual(self.action(item, 'feature').status_code, 303)
        db.session.refresh(other)
        self.assertFalse(other.featured)
        self.assertEqual(self.headings(self.soup('/noticias'), '.news-lead'), [item.title])

        db.session.refresh(item)
        response = self.post('/admin/noticias/' + str(item.id), revision=item.revision,
                             **self.form(body='Texto actualizado após verificação.'))
        self.assertEqual(response.status_code, 303)
        article = self.soup('/noticias/' + item.slug)
        self.assertIn('Actualizado em', article.text)
        self.assertIn('Arquivo de ensaio', article.select_one('.news-figure figcaption').text)
        self.assertEqual(article.select_one('.news-figure img')['alt'], 'Descrição da capa')
        self.assertEqual(article.select_one('.news-author-credit a').text.strip(), item.author.name)
        self.assertEqual(article.select_one('.news-author-credit a')['href'],
                         '/autor/' + item.author.slug)
        self.assertEqual(article.select_one('.news-publication-details time')['datetime'],
                         item.published_date.isoformat())
        self.assertIsNone(article.select_one('.news-evidence'))
        self.assertEqual(self.action(item, 'withdraw').status_code, 303)
        self.assertEqual(self.client.get('/noticias/' + item.slug).status_code, 404)
        self.assertEqual(self.headings(self.soup('/noticias'), '.news-lead'), [other.title])
        self.assertTrue(GovernanceAudit.query.filter_by(action='news.withdraw', entity_id=item.id).count())

    def test_publish_missing_fields_are_named_and_linked_without_losing_draft(self):
        self.auth()
        form = self.form(category_id='', sources_text='', summary='')
        self.assertEqual(self.post('/admin/noticias/nova', **form).status_code, 303)
        item = NewsVersion.query.filter_by(title='Ensaio ' + self.token).one()
        self.assertEqual(item.status, 'draft')
        before_revision = item.revision
        response = self.action(item, 'publish')
        self.assertEqual(response.status_code, 400)
        page = BeautifulSoup(response.text, 'html.parser')
        error = page.select_one('.news-editor-error')
        self.assertIsNotNone(error)
        self.assertNotIn('Antes de publicar, preencha: Tema', error.get_text(' ', strip=True))
        self.assertNotIn('Fontes', error.get_text(' ', strip=True))
        self.assertIn('Resumo', error.get_text(' ', strip=True))
        links = {link['href'] for link in error.select('.news-editor-missing-list a')}
        self.assertNotIn('#news-category', links)
        self.assertNotIn('#news-sources-text', links)
        self.assertIn('#news-summary', links)
        db.session.refresh(item)
        self.assertEqual(item.status, 'draft')
        self.assertEqual(item.revision, before_revision)
        self.assertEqual(item.title, form['title'])

    def test_scheduled_news_uses_local_time_and_remains_private_until_due(self):
        from datetime import datetime, timezone
        from news_admin import is_scheduled
        self.auth()
        self.assertEqual(self.post('/admin/noticias/nova', **self.form()).status_code, 303)
        item = NewsVersion.query.filter_by(title='Ensaio ' + self.token).one()
        target = (datetime.now(timezone.utc) + timedelta(days=2)).replace(
            second=0, microsecond=0)
        local_value = (target + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M')
        self.assertEqual(self.action(
            item, 'schedule', schedule_timezone='Africa/Maputo',
            scheduled_at=local_value).status_code, 303)
        db.session.refresh(item)
        self.assertTrue(is_scheduled(item))
        self.assertEqual(item.published_at, target.replace(tzinfo=None))
        edit = self.soup('/admin/noticias/' + str(item.id))
        self.assertEqual(edit.select_one('.news-editor-status').text.strip(), 'Programada')
        self.assertEqual(edit.select_one('#news-scheduled-at')['value'], local_value)
        self.assertEqual(self.client.get('/noticias/' + item.slug).status_code, 404)
        self.assertNotIn(item.title, self.soup('/noticias').text)
        self.assertNotIn('/noticias/' + item.slug, self.client.get('/sitemap.xml').text)

        self.assertEqual(self.action(item, 'cancel_schedule').status_code, 303)
        db.session.refresh(item)
        self.assertEqual(item.status, 'draft')
        self.assertIsNone(item.published_at)
        self.assertEqual(self.client.get('/noticias/' + item.slug).status_code, 404)

        self.assertEqual(self.action(item, 'schedule', schedule_timezone='UTC',
                                     scheduled_at=target.strftime('%Y-%m-%dT%H:%M')).status_code, 303)
        item.published_at = utcnow() - timedelta(minutes=1)
        db.session.commit()
        self.assertEqual(self.client.get('/noticias/' + item.slug).status_code, 200)
        self.assertIn(item.title, self.soup('/noticias').text)

    def test_schedule_requires_future_valid_time_and_permission(self):
        self.auth()
        self.assertEqual(self.post('/admin/noticias/nova', **self.form()).status_code, 303)
        item = NewsVersion.query.filter_by(title='Ensaio ' + self.token).one()
        for zone, value in [('Africa/Maputo', ''), ('Invalid/Zone', '2030-01-01T10:00'),
                            ('UTC', '2000-01-01T10:00')]:
            response = self.action(item, 'schedule', schedule_timezone=zone, scheduled_at=value)
            self.assertEqual(response.status_code, 400)
            db.session.refresh(item)
            self.assertEqual(item.status, 'draft')
        self.auth('portal_editor')
        self.assertEqual(self.action(item, 'schedule', schedule_timezone='UTC',
                                     scheduled_at='2030-01-01T10:00').status_code, 403)

    def test_news_can_publish_without_sources(self):
        self.auth()
        form = self.form(sources_text='')
        self.assertEqual(self.post('/admin/noticias/nova', **form).status_code, 303)
        item = NewsVersion.query.filter_by(title='Ensaio ' + self.token).one()
        self.assertFalse(item.sources)
        self.assertEqual(self.action(item, 'publish').status_code, 303)
        self.assertIsNone(self.soup('/noticias/' + item.slug).select_one('.news-sources'))

    def test_bibliographic_references_without_urls_and_dois(self):
        self.auth()
        references = (
            'Silva, A. (2024). A ciência em Moçambique. Revista Académica, 12(2), 15–28.\n'
            'Santos, B. (2025). Investigação científica. | 10.1234/estudo.2025\n'
            'Relatório institucional (2026). | https://example.org/relatorio\n'
            'https://example.org/documento'
        )
        self.assertEqual(self.post('/admin/noticias/nova',
                                   **self.form(sources_text=references)).status_code, 303)
        item = NewsVersion.query.filter_by(title='Ensaio ' + self.token).one()
        self.assertEqual(len(item.sources), 4)
        self.assertEqual(item.sources[0]['url'], '')
        self.assertTrue(item.sources[0]['label'].startswith('Silva'))
        self.assertEqual(item.sources[1]['url'], 'https://doi.org/10.1234/estudo.2025')
        self.assertEqual(item.sources[2]['url'], 'https://example.org/relatorio')
        self.assertEqual(self.action(item, 'publish').status_code, 303)
        page = self.soup('/noticias/' + item.slug)
        entries = page.select('.news-reference-list > li')
        self.assertEqual(len(entries), 4)
        self.assertIn('Silva', entries[0].get_text())
        self.assertIsNone(entries[0].select_one('a'))
        self.assertEqual(entries[1].select_one('a')['href'],
                         'https://doi.org/10.1234/estudo.2025')
        self.assertEqual(entries[3].select_one('a')['href'], 'https://example.org/documento')
        editor = self.soup('/admin/noticias/' + str(item.id))
        self.assertIn('Silva', editor.select_one('#news-sources-text').text)
        self.assertIn('10.1234/estudo.2025',
                      editor.select_one('#news-sources-text').text)

    def test_bibliographic_reference_with_attached_url(self):
        self.auth()
        line = ('Bloomberg (19 November 2026). Apple Is Working on AI Agent for '
                'Device Control, Apps, Browsing and Coding.'
                'https://bloomberg.com/news/articles/2026-11-19/'
                'apple-is-working-on-ai-agent-for-device-control-apps-browsing-and-coding')
        self.assertEqual(self.post('/admin/noticias/nova',
                                   **self.form(sources_text=line)).status_code, 303)
        item = NewsVersion.query.filter_by(title='Ensaio ' + self.token).one()
        self.assertEqual(len(item.sources), 1)
        self.assertTrue(item.sources[0]['label'].startswith('Bloomberg (19 November 2026)'))
        self.assertEqual(item.sources[0]['url'],
                         'https://bloomberg.com/news/articles/2026-11-19/'
                         'apple-is-working-on-ai-agent-for-device-control-apps-browsing-and-coding')
        self.assertEqual(self.action(item, 'publish').status_code, 303)
        entry = self.soup('/noticias/' + item.slug).select_one('.news-reference-list li')
        self.assertIn('Bloomberg', entry.text)
        self.assertEqual(entry.select_one('a')['href'], item.sources[0]['url'])

    def test_markdown_bibliography_with_anchors_multiple_links_and_credits(self):
        from news_admin import parse_news_sources, format_news_sources
        self.auth()
        sources = """## Referências
<a id="ref-1"></a>

1. Autor de teste (2026). *Revista de teste*. [https://doi.org/10.1234/teste](https://doi.org/10.1234/teste).

<a id="ref-2"></a>
2. Outro autor (2026). *Revista de teste*. [DOI](https://doi.org/10.1234/outro). [Texto integral](https://example.org/texto).

## Créditos e licenças das imagens
As imagens remetem para a origem.

<a id="imagem-1"></a>
- **Figura 1:** Autor. *Fotografia de ensaio*. [Wikimedia Commons](https://example.org/image). [Licença](https://example.org/license).
"""
        self.assertEqual(self.post('/admin/noticias/nova', **self.form(sources_text=sources)).status_code, 303)
        item = NewsVersion.query.filter_by(title='Ensaio ' + self.token).one()
        self.assertEqual(len(item.sources), 3)
        self.assertEqual(item.sources[0]['url'], 'https://doi.org/10.1234/teste')
        self.assertIn('Revista de teste', item.sources[0]['label'])
        self.assertEqual(item.sources[1]['links'], [{'label':'Texto integral','url':'https://example.org/texto'}])
        self.assertEqual(item.sources[2]['links'], [{'label':'Licença','url':'https://example.org/license'}])
        self.assertIn('Figura 1:', item.sources[2]['label'])
        editor = self.soup('/admin/noticias/' + str(item.id))
        self.assertEqual(parse_news_sources(editor.select_one('#news-sources-text').text), item.sources)
        self.assertEqual(parse_news_sources(format_news_sources(item.sources)), item.sources)
        self.assertEqual(self.action(item, 'publish').status_code, 303)
        entries = self.soup('/noticias/' + item.slug).select('.news-reference-list > li')
        self.assertEqual(len(entries), 3)
        self.assertEqual([a['href'] for a in entries[1].select('a')],
                         ['https://doi.org/10.1234/outro', 'https://example.org/texto'])
        self.assertEqual([a['href'] for a in entries[2].select('a')],
                         ['https://example.org/image', 'https://example.org/license'])

    def test_escaped_markdown_bibliography_and_line_specific_errors(self):
        from news_admin import parse_news_sources
        escaped = r"""\<a id="ref-1">\</a>
\
1\. Autor (2026). \*Revista\*. [https\://doi.org/10.1234/teste]\(https\://doi.org/10.1234/teste).
"""
        self.assertEqual(parse_news_sources(escaped)[0]['url'], 'https://doi.org/10.1234/teste')
        self.auth()
        response = self.post('/admin/noticias/nova', **self.form(sources_text='## Referências\n1. Fonte [Texto](http://example.org/teste)'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('Fontes, linha 2', response.get_data(as_text=True))
        response = self.post('/admin/noticias/nova', **self.form(
            sources_text='Ensaio [Fonte](https://example.org/teste) [Complemento](http://example.org/outro)'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('Fontes, linha 1', response.get_data(as_text=True))
        self.assertEqual(len(parse_news_sources('\n'.join(
            f'<a id="ref-{i}"></a>\n{i}. Referência de teste {i}' for i in range(1,41)))), 40)
        with self.assertRaisesRegex(ValueError, '40 referências'):
            parse_news_sources('\n'.join(f'{i}. Referência de teste {i}' for i in range(1,42)))

    def test_insecure_reference_urls_still_rejected(self):
        self.auth()
        for unsafe in ('http://example.org/source',
                       'Estudo | http://example.org/source',
                       'Estudo | javascript:alert(1)'):
            response = self.post('/admin/noticias/nova',
                                 **self.form(sources_text=unsafe))
            self.assertEqual(response.status_code, 400)

    def test_news_without_topic_can_be_published_and_read(self):
        self.auth()
        form = self.form(category_id='')
        self.assertEqual(self.post('/admin/noticias/nova', **form).status_code, 303)
        item = NewsVersion.query.filter_by(title='Ensaio ' + self.token).one()
        self.assertIsNone(item.category_id)
        self.assertEqual(self.action(item, 'publish').status_code, 303)
        db.session.refresh(item)
        self.assertEqual(item.status, 'published')
        article = self.soup('/noticias/' + item.slug)
        self.assertIn('Ciência', article.select_one('.article-header .eyebrow').text)
        listing = self.soup('/noticias')
        self.assertIn(item.title, listing.get_text(' ', strip=True))
        self.assertTrue(listing.select_one('.news-card .eyebrow'))
        new_page = self.soup('/admin/noticias/nova')
        self.assertEqual(new_page.select_one('#news-category option')['value'], '')
        self.assertIn('admin-news-topic.js', str(new_page))

    def test_news_editor_markdown_toolbar_is_available_for_new_and_saved_news(self):
        self.auth()
        new_page = self.soup('/admin/noticias/nova')
        toolbar = new_page.select_one('.news-markdown-toolbar')
        self.assertIsNotNone(toolbar)
        expected = {'h2', 'h3', 'h4', 'h5', 'h6', 'bold', 'italic',
                    'quote', 'list', 'reference', 'footnote', 'dropcap',
                    'explainer', 'pullquote', 'image', 'video', 'table', 'chart'}
        self.assertEqual({button['data-news-md'] for button in toolbar.select('button[data-news-md]')},
                         expected)
        self.assertTrue(all(button.get('type') == 'button' for button in toolbar.select('button')))
        self.assertIsNotNone(new_page.select_one('textarea#news-body[name="body"]'))
        self.assertTrue(new_page.select_one('script[src*="admin-news-markdown.js"]'))

        self.assertEqual(self.post('/admin/noticias/nova', **self.form()).status_code, 303)
        item = NewsVersion.query.filter_by(title='Ensaio ' + self.token).one()
        saved_page = self.soup('/admin/noticias/' + str(item.id))
        self.assertIsNotNone(saved_page.select_one('.news-markdown-toolbar'))
        self.assertEqual(saved_page.select_one('#news-body').text, item.body)

    def test_evidence_note_removed_from_editor_but_existing_note_is_preserved(self):
        self.auth()
        self.assertEqual(self.post('/admin/noticias/nova', **self.form()).status_code, 303)
        item = NewsVersion.query.filter_by(title='Ensaio ' + self.token).one()
        page = self.soup('/admin/noticias/' + str(item.id))
        self.assertIsNone(page.select_one('#news-evidence-note'))

        original_note = item.evidence_note
        form = self.form()
        form.pop('evidence_note')
        self.assertEqual(self.post('/admin/noticias/' + str(item.id),
                                   revision=item.revision, **form).status_code, 303)
        db.session.refresh(item)
        self.assertEqual(item.evidence_note, original_note)

        self.assertEqual(self.action(item, 'publish').status_code, 303)
        article = self.soup('/noticias/' + item.slug)
        self.assertIsNone(article.select_one('.news-evidence'))
        self.assertNotIn(original_note, article.select_one('.news-reading-main').get_text())

    def test_new_preliminary_news_does_not_require_removed_note(self):
        self.auth()
        form = self.form(evidence='preliminary')
        form.pop('evidence_note')
        self.assertEqual(self.post('/admin/noticias/nova', **form).status_code, 303)
        item = NewsVersion.query.filter_by(title='Ensaio ' + self.token).one()
        self.assertFalse(item.evidence_note)
        self.assertEqual(self.action(item, 'publish').status_code, 303)

    def test_independent_english_publication_and_version_conflicts(self):
        self.auth()
        response = self.post('/admin/noticias/nova', **self.form('en', title='English first', summary=''))
        self.assertEqual(response.status_code, 303)
        en = NewsVersion.query.filter_by(title='English first').one()
        self.assertEqual(self.action(en, 'publish').status_code, 400)
        self.assertEqual(self.post('/admin/noticias/' + str(en.id), revision='0', **self.form('en')).status_code, 409)
        self.assertEqual(self.action(en, 'feature').status_code, 409)
        group = '/admin/noticias/grupo/' + str(en.story_id) + '/nova'
        self.assertEqual(self.post(group, **self.form('en')).status_code, 409)
        self.assertEqual(self.post('/admin/noticias/' + str(en.id), revision=en.revision,
                                   **self.form('en', title='English first')).status_code, 303)
        self.assertEqual(self.action(en, 'publish').status_code, 303)
        self.assertIn('English first', self.soup('/en/news').text)
        self.assertEqual(self.post(group, **self.form()).status_code, 303)
        self.assertEqual(self.client.get('/noticias/' + en.slug).status_code, 404)
