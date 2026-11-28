"""Locale routes, immutable sources, approval gates and bounded translation worker."""
import copy
import os
import secrets
import tempfile
import time
import unittest
from datetime import timedelta
from unittest.mock import patch
import test_platform
from app import app
from models import db, Article, Author, Category, Journal, utcnow
from extensions import limiter
from security_test_support import authenticate_test_session
from translation_models import (ContentTranslation as Translation, TranslationVersion as Version,
    TranslationJob as Job, TranslationEvent as Event, TranslationQuota, TranslationWorker, InterfaceTranslation, InterfaceBatch,
    TranslationLimitSetting, TranslationLimitChange)
from dissemination_ai import GenerationError
import translation_service as service
from internationalization import preferred


class InternationalizationTests(unittest.TestCase):
    def setUp(self):
        self.ctx=app.app_context();self.ctx.push();self.previous=limiter.enabled;limiter.enabled=False
        self.env=patch.dict(os.environ,dict(OPENAI_API_KEY='fixture',TRANSLATION_TEXT_MODEL='fixture',TRANSLATION_REVIEW_MODEL='fixture',TRANSLATION_DAILY_UNITS='100',I18N_ENABLED='true'))
        self.env.start()
        for model in (Event,Job,Version,Translation,TranslationQuota,TranslationWorker,InterfaceBatch,InterfaceTranslation,
                      TranslationLimitChange,TranslationLimitSetting):model.query.delete()
        token=secrets.token_hex(5)
        self.article=Article(title='Plantas '+token,slug='i18n-'+token,summary='As plantas utilizam luz.',
            body='## Método\nAs plantas utilizam luz. $x=2$ [Fonte](https://example.org/paper).\n\n![Planta](https://example.org/plant.png)',
            references='Autor (2020). Referência original.',keywords='plantas',status='published',
            author_rel=Author.query.first(),category_rel=Category.query.first())
        db.session.add(self.article);db.session.commit()
        self.client=app.test_client()
        with self.client.session_transaction() as s:
            s.update(admin_authenticated=True,admin_superuser=True,admin_last_activity_at=time.time(),csrf_token='i18n-test')
            authenticate_test_session(s)

    def tearDown(self):
        db.session.rollback()
        TranslationLimitChange.query.delete();TranslationLimitSetting.query.delete();db.session.commit()
        self.env.stop();limiter.enabled=self.previous;self.ctx.pop()

    def test_daily_limit_saved_in_panel_is_persistent_audited_and_used_by_queue(self):
        from translation_limits import daily_limit, quota_summary
        response=self.client.post('/admin/internacionalizacao/limite-diario',data=dict(
            csrf_token='i18n-test',daily_units='1',limit_version='0'))
        self.assertEqual(response.status_code,302)
        change=TranslationLimitChange.query.one()
        self.assertEqual((change.previous_units,change.daily_units),(100,1))
        article_id=self.article.id
        db.session.remove()
        with patch.dict(os.environ,{'TRANSLATION_DAILY_UNITS':'999'}):
            self.assertEqual(daily_limit(),1)
            service.queue('article',article_id);db.session.commit()
            self.assertEqual(quota_summary()['remaining'],0)
            Job.query.one().state='done';db.session.commit()
            with self.assertRaisesRegex(GenerationError,'Limite diário'):
                service.queue('article',article_id)
            db.session.rollback()
        self.assertEqual(TranslationQuota.query.one().reserved_units,1)

    def test_daily_limit_update_preserves_reservations_and_blocks_stale_forms(self):
        from translation_limits import quota_summary
        db.session.add(TranslationQuota(day=utcnow().date(),reserved_units=6));db.session.commit()
        for value,version in [('18',0),('3',1)]:
            response=self.client.post('/admin/internacionalizacao/limite-diario',data=dict(
                csrf_token='i18n-test',daily_units=value,limit_version=version))
            self.assertEqual(response.status_code,302)
        self.assertEqual(quota_summary()['remaining'],0)
        self.assertEqual(TranslationQuota.query.one().reserved_units,6)
        response=self.client.post('/admin/internacionalizacao/limite-diario',data=dict(
            csrf_token='i18n-test',daily_units='50',limit_version='1'))
        self.assertEqual(response.status_code,409)
        self.assertEqual(TranslationLimitSetting.query.one().daily_units,3)
        self.assertEqual(TranslationLimitChange.query.count(),2)

    def test_daily_limit_rejects_invalid_values_and_requires_primary_admin_and_csrf(self):
        for value in ['', '0', '-1', '1.5', '1000001', 'abc']:
            response=self.client.post('/admin/internacionalizacao/limite-diario',data=dict(
                csrf_token='i18n-test',daily_units=value,limit_version='0'))
            self.assertEqual(response.status_code,409)
        self.assertEqual(TranslationLimitChange.query.count(),0)
        self.assertEqual(self.client.post('/admin/internacionalizacao/limite-diario',
            data=dict(daily_units='18',limit_version='0')).status_code,400)
        self.assertEqual(app.test_client().post('/admin/internacionalizacao/limite-diario',
            data=dict(daily_units='18',limit_version='0')).status_code,302)
        with self.client.session_transaction() as session:
            session['admin_superuser']=False
            session.pop('admin_id',None)
            authenticate_test_session(session)
        with patch('translation_admin.can',return_value=True):
            response=self.client.post('/admin/internacionalizacao/limite-diario',data=dict(
                csrf_token='i18n-test',daily_units='18',limit_version='0'))
            self.assertEqual(response.status_code,403)
            page=self.client.get('/admin/internacionalizacao/')
            self.assertNotIn('id="translation-daily-units"',page.text)

    def test_daily_limit_can_repair_invalid_environment_without_resetting_usage(self):
        from translation_limits import quota_summary
        with patch.dict(os.environ,{'TRANSLATION_DAILY_UNITS':'invalid'}):
            page=self.client.get('/admin/internacionalizacao/')
            self.assertEqual(page.status_code,200)
            self.assertIn('O limite definido no servidor é inválido',page.text)
            response=self.client.post('/admin/internacionalizacao/limite-diario',data=dict(
                csrf_token='i18n-test',daily_units='18',limit_version='0'))
            self.assertEqual(response.status_code,302)
            self.assertEqual(quota_summary()['limit'],18)

    def test_daily_limit_schema_upgrade_is_idempotent(self):
        from sqlalchemy import create_engine, inspect
        from translation_schema import upgrade_translation_limits
        engine=create_engine('sqlite://')
        with engine.begin() as connection:
            upgrade_translation_limits(connection);upgrade_translation_limits(connection)
            self.assertEqual(set(inspect(connection).get_table_names()),
                {'translation_limit_setting','translation_limit_change'})
        engine.dispose()

    def make(self,publish=False):
        original=service.source('article',self.article.id)
        content=dict(original,title='Plants and sunlight',summary='Plants use light.',keywords='plants',
            body=original['body'].replace('Método','Method').replace('As plantas utilizam luz.','Plants use light.').replace('![Planta]','![Plant]'))
        item=Translation(kind='article',source_id=self.article.id);db.session.add(item);db.session.flush()
        service.add_version(item,original,content,dict(ready=True,faithful=True,issues=[]))
        if publish:
            item.state='published';item.approved_version=1;item.published_version=1;item.reviewed_at=utcnow()
        db.session.commit();return item

    def post(self,item,action,**data):
        return self.client.post(f'/admin/internacionalizacao/{item.id}/accao',data=dict(csrf_token='i18n-test',version=item.version,action=action,**data))

    def test_negotiation_manual_cookie_country_browser_and_untrusted_country(self):
        with patch.dict(os.environ,{'TRUST_CLOUDFLARE_COUNTRY':'true'}):
            self.assertEqual(preferred({'CF-IPCountry':'MZ','Accept-Language':'en'},{}),'pt')
            self.assertEqual(preferred({'CF-IPCountry':'US','Accept-Language':'pt'},{}),'en')
            self.assertEqual(preferred({'CF-IPCountry':'US'},{'sds_language':'pt'}),'pt')
            self.assertEqual(preferred({'CF-IPCountry':'FR','Accept-Language':'en-GB,en;q=0.8'},{}),'en')
        with patch.dict(os.environ,{'TRUST_CLOUDFLARE_COUNTRY':'false'}):
            self.assertEqual(preferred({'CF-IPCountry':'US'},{}),'pt')

    def test_initial_redirect_only_home_and_explicit_paths_are_stable(self):
        response=self.client.get('/',headers={'Accept-Language':'en','User-Agent':'Mozilla/5.0'})
        self.assertEqual(response.status_code,302);self.assertEqual(response.location,'/en/')
        self.assertEqual(self.client.get('/sobre',headers={'Accept-Language':'en'}).status_code,200)
        self.assertEqual(self.client.get('/',headers={'Accept-Language':'en','User-Agent':'Googlebot'}).status_code,200)
        self.assertEqual(self.client.get('/en/').status_code,200)

    def test_multilingual_country_respects_supported_browser_languages(self):
        cases = [
            ('CA', 'pt-BR,pt;q=0.9,en;q=0.5', 'pt'),
            ('ZA', 'pt-MZ,en;q=0.8', 'pt'),
            ('NG', 'en-NG,en;q=0.8,pt;q=0.2', 'en'),
            ('IN', 'pt-PT', 'pt'), ('SG', 'en-SG', 'en'),
            ('PH', '', 'en'), ('CA', 'fr-CA,fr;q=0.9', 'en'),
            ('ZA', 'en;q=0,pt;q=0.8', 'pt'),
            ('MZ', 'en-US', 'pt'), ('PT', 'en', 'pt'),
            ('US', 'pt', 'en'), ('AU', 'pt', 'en'),
            ('XX', 'pt-PT;q=0.5,en-GB;q=0.9', 'en'),
            ('T1', '', 'pt'), ('', '', 'pt'),
            (' ca ', 'pt', 'pt'),
        ]
        with patch.dict(os.environ, {'TRUST_CLOUDFLARE_COUNTRY': 'true'}):
            for country, browser, expected in cases:
                with self.subTest(country=country, browser=browser):
                    headers={'CF-IPCountry': country, 'Accept-Language': browser}
                    self.assertEqual(preferred(headers, {}), expected)
                    for manual in ('pt', 'en'):
                        self.assertEqual(preferred(headers, {'sds_language': manual}), manual)

    def test_untrusted_country_is_ignored_even_with_invalid_language_cookie(self):
        for flag in ('false', '', 'TRUE'):
            with patch.dict(os.environ, {'TRUST_CLOUDFLARE_COUNTRY': flag}):
                self.assertEqual(preferred({'CF-IPCountry': 'US'}, {'sds_language': 'invalid'}), 'pt')
                self.assertEqual(preferred({'CF-IPCountry': 'MZ', 'Accept-Language': 'en-US'}, {}), 'en')

    def test_assistant_receives_selected_locale_and_only_published_source_titles(self):
        # Other tests retain published articles in the shared database. A unique
        # search term keeps this fixture inside the assistant's bounded results.
        search_term='assistantfixture'+secrets.token_hex(8)
        self.article.keywords=search_term
        db.session.commit()
        self.make(publish=True)
        for locale, expected_title in [('en', 'Plants and sunlight'), ('pt', self.article.title)]:
            with self.subTest(locale=locale):
                self.client.get('/idioma/'+locale)
                with patch('app.requests.post') as worker:
                    worker.return_value.json.return_value={'ok':True,'answer':'fixture','links':[]}
                    response=self.client.post('/api/assistente',json={'message':search_term,'language':locale})
                self.assertEqual(response.status_code,200)
                payload=worker.call_args.kwargs['json']
                self.assertEqual(payload['language'],locale)
                self.assertTrue(any(source['title']==expected_title for source in payload['sources']))
                source=next(source for source in payload['sources'] if source['title']==expected_title)
                self.assertIn(('/en/artigo/' if locale=='en' else '/artigo/')+self.article.slug,source['url'])

    def test_country_redirect_and_manual_choice_are_private_and_stable(self):
        client=app.test_client()
        with patch.dict(os.environ, {'TRUST_CLOUDFLARE_COUNTRY': 'true'}):
            headers={'CF-IPCountry':'ZA', 'Accept-Language':'pt-MZ,en;q=0.7'}
            response=client.get('/', headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Content-Language'], 'pt-MZ')
            self.assertIn('Accept-Language', response.vary)
            self.assertIn('CF-IPCountry', response.vary)
            self.assertIn('no-store', response.headers['Cache-Control'])
            response=client.get('/idioma/en')
            self.assertIn('Max-Age=31536000', response.headers['Set-Cookie'])
            self.assertIn('HttpOnly', response.headers['Set-Cookie'])
            self.assertIn('SameSite=Lax', response.headers['Set-Cookie'])
            response=client.get('/', headers=headers, follow_redirects=True)
            self.assertEqual(response.headers['Content-Language'], 'en')
            self.assertEqual(client.get('/en/', headers={'CF-IPCountry':'MZ'}).status_code, 200)
            client.get('/idioma/pt')
            response=client.get('/', headers={'CF-IPCountry':'US','Accept-Language':'en'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Content-Language'], 'pt-MZ')

    def test_switch_preserves_query_and_rejects_open_redirects(self):
        r=self.client.get('/idioma/en',query_string={'next':'/artigos?q=plantas&page=2'})
        self.assertEqual(r.location,'/en/artigos?q=plantas&page=2')
        self.assertIn('sds_language=en',r.headers['Set-Cookie'])
        for target in ['https://evil.test','//evil.test','/\\evil.test']:
            self.assertEqual(self.client.get('/idioma/en',query_string={'next':target}).status_code,400)

    def test_untranslated_article_switch_has_clear_existing_alternative(self):
        r=self.client.get('/idioma/en',query_string={'next':'/artigo/'+self.article.slug})
        self.assertIn('/en/artigos?original=',r.location)
        page=self.client.get('/en/artigo/'+self.article.slug)
        self.assertEqual(page.status_code,404);self.assertIn('Read the Portuguese original',page.text)

    def test_english_article_uses_only_published_version_and_self_canonical(self):
        item=self.make()
        self.assertEqual(self.client.get('/en/artigo/'+self.article.slug).status_code,404)
        self.assertEqual(self.post(item,'publish').status_code,409)
        self.assertEqual(self.post(item,'approve',reviewed='yes').status_code,302)
        self.assertEqual(self.post(item,'publish').status_code,302)
        page=self.client.get('/en/artigo/'+self.article.slug)
        self.assertEqual(page.status_code,200);self.assertIn('Plants and sunlight',page.text)
        self.assertIn('lang="en"',page.text);self.assertIn('/en/artigo/'+self.article.slug,page.text)
        from bs4 import BeautifulSoup
        preferred = BeautifulSoup(page.text, 'html.parser').select_one('.article-author-line [google-add-preferred-source-btn]')
        self.assertIsNotNone(preferred)
        self.assertEqual(preferred['data-lang'], 'en')
        self.assertEqual(page.headers['Content-Language'],'en');self.assertIn('no-store',page.headers['Cache-Control'])
        self.assertEqual(self.article.title.split()[0],'Plantas')
        self.assertIn('## Método',self.article.body)

    def test_update_preserves_published_translation_and_blocks_stale_approval(self):
        item=self.make(publish=True)
        self.article.body+='\nNovo resultado.';db.session.commit()
        self.assertEqual(service.state(item),'outdated')
        self.assertEqual(item.published_version,1)
        page=self.client.get('/en/artigo/'+self.article.slug)
        self.assertEqual(page.status_code,200);self.assertIn('awaiting an editorial update',page.text)
        self.assertEqual(self.post(item,'approve',reviewed='yes').status_code,409)

    def test_manual_edit_invalidates_approval_and_queues_review(self):
        item=self.make(publish=True)
        content=dict(service.version(item).content,title='Plants and light')
        self.assertEqual(self.post(item,'edit',**content).status_code,302)
        self.assertEqual(item.published_version,1);self.assertIsNone(item.approved_version)
        self.assertEqual(Job.query.one().mode,'review')
        self.assertEqual(self.post(item,'publish').status_code,409)

    def test_source_references_formula_links_and_heading_integrity_are_checked(self):
        item=self.make();row=service.version(item)
        for field,replacement in [('references','Invented reference'),('body',row.content['body'].replace('$x=2$','$x=7$')),
                                  ('body',row.content['body'].replace('https://example.org/paper','https://evil.test')),
                                  ('body',row.content['body'].replace('## Method','# Method'))]:
            content=dict(row.content);content[field]=replacement
            with self.assertRaises(GenerationError):service.validate(row.source,content)

    def test_masked_translation_restores_exact_formula_and_code(self):
        source='## Teste\n$x=2$ e `x = 2` [Fonte](https://example.org) (Autor, 2020).'
        protected,tokens=service.protect(source)
        self.assertNotIn('$x=2$',protected)
        self.assertEqual(service.restore(protected,tokens),source)
        with self.assertRaises(GenerationError):service.restore(protected+next(iter(tokens)),tokens)

    def test_dropcap_marker_survives_translation_and_legacy_alias_is_valid(self):
        source = {'body': '[capitular] Texto inicial.\n\nOutro parágrafo.'}
        protected, tokens = service.protect(source['body'])
        self.assertNotIn('[capitular]', protected)
        self.assertIn('[capitular]', tokens.values())
        self.assertEqual(service.restore(protected, tokens), source['body'])
        def provider(model, instruction, data):
            if 'original' in data:
                return {'faithful': True, 'issues': []}
            self.assertNotIn('[capitular]', data['body'])
            return {'body': data['body'].replace('Texto inicial.', 'Opening paragraph.').replace('Outro parágrafo.', 'Second paragraph.')}
        with patch('translation_service.call', side_effect=provider):
            translated, report = service.translate(source)
        self.assertTrue(report['ready'])
        self.assertTrue(translated['body'].startswith('[capitular] Opening'))
        for alias in ('[drop cap]', '[drop_cap]', '[DROP_CAP]', '[letra_capitular]'):
            value = f'{alias} Opening paragraph.\n\nSecond paragraph.'
            service.validate(source, {'body': value})
            masked, tokens = service.protect(value)
            self.assertNotIn(alias, masked)
            self.assertEqual(service.restore(masked, tokens), value)
        for invalid in ('Opening paragraph.', 'Opening paragraph. [capitular]', '[capitular] Opening.\n\n[capitular] Second.'):
            with self.assertRaises(service.ProtectedContentError):
                service.validate(source, {'body': invalid})

    def test_published_legacy_english_dropcap_is_rendered_without_retranslation(self):
        from bs4 import BeautifulSoup
        self.article.body = '[capitular] As plantas utilizam luz.\n\nOutro parágrafo.'
        db.session.commit()
        item = self.make(publish=True)
        row = service.version(item)
        row.content = dict(row.content, body='[drop_cap] Plants use light.\n\nSecond paragraph.')
        db.session.commit()
        for prefix, text in [('', 'As plantas utilizam luz.'), ('/en', 'Plants use light.')]:
            response = self.client.get(prefix + '/artigo/' + self.article.slug)
            self.assertEqual(response.status_code, 200)
            doc = BeautifulSoup(response.text, 'html.parser')
            paragraph = doc.select_one('.article-markdown p.article-dropcap')
            self.assertIsNotNone(paragraph)
            self.assertEqual(paragraph.get_text(), text)
            self.assertEqual(len(doc.select('.article-markdown p.article-dropcap')), 1)
        self.assertTrue(service.version(item).content['body'].startswith('[drop_cap]'))

    def test_batch_is_async_prioritized_and_can_pause_cancel_pending(self):
        with patch('translation_service.translate') as translator:
            r=self.client.post('/admin/internacionalizacao/lote',data=dict(csrf_token='i18n-test',kind='article',source_ids=[self.article.id],priority='3'))
        self.assertEqual(r.status_code,302);translator.assert_not_called()
        job=Job.query.one();self.assertEqual(job.priority,3)
        self.assertEqual(self.client.post(f'/admin/internacionalizacao/tarefas/{job.id}',data=dict(csrf_token='i18n-test',action='pause')).status_code,302)
        self.assertEqual(job.state,'paused')
        self.assertFalse(service.process_one())
        self.client.post(f'/admin/internacionalizacao/tarefas/{job.id}',data=dict(csrf_token='i18n-test',action='cancel'))
        self.assertEqual(job.state,'cancelled')

    def test_worker_reviews_without_publishing_and_releases_global_slot(self):
        with app.test_request_context('/'):
            item=service.queue('article',self.article.id);db.session.commit()
        original=service.source('article',self.article.id)
        with patch('translation_service.translate',return_value=(original,dict(ready=True,faithful=True,issues=[]))):
            self.assertTrue(service.process_one())
        self.assertEqual(item.state,'review');self.assertIsNone(item.published_version)
        self.assertIsNone(db.session.get(TranslationWorker,1).lease)
        self.assertFalse(service.process_one())

    def test_worker_failure_is_terminal_and_does_not_expose_secrets(self):
        with app.test_request_context('/'):
            item=service.queue('article',self.article.id);db.session.commit()
        with patch('translation_service.translate',side_effect=RuntimeError('secret-key')):service.process_one()
        self.assertEqual(item.state,'error');self.assertNotIn('secret-key',item.error)
        self.assertFalse(service.process_one())

    def test_scientific_journal_translation_excludes_manuscript_pdf_and_doi(self):
        token=secrets.token_hex(5)
        journal=Journal(title='Revista '+token,article_title='Plantas',slug='i18n-journal-'+token,field='Biologia',
            description='Descrição',summary='Resumo',keywords='plantas',content_markdown='MANUSCRITO IMUTÁVEL',published=True,doi='10.9999/'+token)
        db.session.add(journal);db.session.commit()
        source=service.source('journal',journal.id)
        self.assertNotIn('content_markdown',source);self.assertNotIn('doi',source)
        self.assertNotIn('MANUSCRITO IMUTÁVEL',str(source))
        self.assertEqual(journal.content_markdown,'MANUSCRITO IMUTÁVEL')

    def test_interface_catalogue_is_escaped_and_incomplete_public_pages_are_indexable(self):
        row=InterfaceTranslation(key='a'*64,source='Pesquisar',english='<script>alert(1)</script>',published=True)
        db.session.add(row);db.session.commit()
        with patch.dict('internationalization.EN',{'Todos os artigos':''}):
            page=self.client.get('/en/artigos')
        self.assertIn('&lt;script&gt;',page.text);self.assertNotIn('<script>alert(1)</script>',page.text)
        self.assertNotIn('noindex',page.headers.get('X-Robots-Tag',''))

    def test_article_listing_translates_headings_categories_and_search_labels(self):
        from bs4 import BeautifulSoup
        page=self.client.get('/en/artigos')
        soup=BeautifulSoup(page.text,'html.parser')
        self.assertEqual(soup.select_one('h1').get_text(strip=True),'All articles')
        self.assertEqual(soup.select_one('.section-rule span').get_text(strip=True),'Explore content')
        self.assertEqual([a.get_text(strip=True) for a in soup.select('.filter-row a')],
                         ['All','Biology','Health','Environment','Education','Technology','Space','Scientific Biography'])
        links=soup.select('.filter-row a')
        self.assertTrue(all('/en/artigos' in a['href'] for a in links))
        page=self.client.get('/en/artigos',query_string={'q':'<science>'})
        self.assertIn('Results for',page.text)
        self.assertIn('&lt;science&gt;',page.text)
        original=self.client.get('/artigos')
        self.assertIn('Todos os artigos',original.text)
        self.assertIn('Explorar conteúdos',original.text)

    def test_missing_translation_notice_links_to_portuguese_original(self):
        from bs4 import BeautifulSoup
        page=self.client.get('/en/artigos',query_string={'original':self.article.slug})
        soup=BeautifulSoup(page.text,'html.parser')
        link=soup.select_one('.translation-notice a')
        self.assertIsNotNone(link)
        self.assertEqual(link['href'],'/artigo/'+self.article.slug+'?lang=pt')
        self.client.get('/idioma/en')
        original=self.client.get(link['href'],follow_redirects=True)
        self.assertEqual(original.status_code,200)
        self.assertEqual(original.headers['Content-Language'],'pt-MZ')
        self.assertIn('not yet published',soup.select_one('.translation-notice').get_text())

    def test_english_query_matches_published_translated_content(self):
        self.make(publish=True)
        page=self.client.get('/en/artigos?q=sunlight')
        self.assertEqual(page.status_code,200);self.assertIn('Plants and sunlight',page.text)

    def test_editorial_routes_require_authentication_and_csrf(self):
        self.assertEqual(app.test_client().get('/admin/internacionalizacao/').status_code,302)
        self.assertEqual(self.client.post('/admin/internacionalizacao/lote',data=dict(source_ids=[self.article.id])).status_code,400)
        self.assertEqual(self.client.get('/admin/internacionalizacao/').status_code,200)
        self.assertEqual(self.client.get('/admin/internacionalizacao/interface').status_code,200)

    def test_disable_switch_keeps_portuguese_and_hides_language_selector(self):
        with patch.dict(os.environ,{'I18N_ENABLED':'false'}):
            self.assertEqual(self.client.get('/en/').status_code,404)
            page=self.client.get('/')
            self.assertEqual(page.status_code,200);self.assertNotIn('class="language-selector"',page.text)

    def test_ai_translation_keeps_protected_parts_and_translates_alt_text(self):
        original=service.source('article',self.article.id)
        def provider(model,instruction,data):
            if 'original' in data:
                return {'faithful':True,'issues':[]}
            return {key:text.replace('Método','Method').replace('Planta','Plant').replace('plantas','plants').replace('As plants utilizam luz.','Plants use light.') for key,text in data.items()}
        with patch('translation_service.call',side_effect=provider):
            translated,report=service.translate(original)
        self.assertTrue(report['ready']);self.assertIn('![Plant]',translated['body'])
        self.assertIn('$x=2$',translated['body']);self.assertEqual(translated['references'],original['references'])

    def test_single_worker_lease_prevents_parallel_provider_calls(self):
        with app.test_request_context('/'):
            service.queue('article',self.article.id);db.session.commit()
        db.session.add(TranslationWorker(id=1,lease='occupied',expires_at=utcnow()+timedelta(minutes=10)));db.session.commit()
        with patch('translation_service.translate') as provider:
            self.assertFalse(service.process_one())
        provider.assert_not_called();self.assertEqual(Job.query.one().state,'queued')

    def test_interface_batch_requires_review_and_publication_to_change_ui(self):
        row=InterfaceTranslation(key='b'*64,source='Pesquisar',english='',published=False)
        batch=InterfaceBatch(keys=[row.key]);db.session.add_all([row,batch]);db.session.flush()
        item=Translation(kind='interface',source_id=batch.id);db.session.add(item);db.session.flush()
        service.add_version(item,{row.key:row.source},{row.key:'Search reviewed'},dict(ready=True,faithful=True,issues=[]));db.session.commit()
        self.assertFalse(row.published)
        self.assertEqual(self.post(item,'publish').status_code,409)
        self.assertEqual(self.post(item,'approve',reviewed='yes').status_code,302)
        self.assertEqual(self.post(item,'publish').status_code,302)
        self.assertTrue(row.published);self.assertEqual(row.english,'Search reviewed')

    def test_source_update_records_outdated_event_without_deleting_published_version(self):
        item=self.make(publish=True)
        self.article.summary+=' Actualização.';db.session.commit()
        self.assertEqual(item.state,'outdated');self.assertEqual(item.published_version,1)
        self.assertTrue(Event.query.filter_by(translation_id=item.id,action='source_updated').first())

    def test_english_dissemination_uses_reviewed_current_translation(self):
        from dissemination_service import snapshot
        self.make(publish=True)
        source=snapshot('portal_en',self.article.id)
        self.assertEqual(source['language'],'en');self.assertEqual(source['title'],'Plants and sunlight')
        self.article.body+=' Mudança.';db.session.commit()
        with self.assertRaises(GenerationError):snapshot('portal_en',self.article.id)

    def test_public_premium_translation_changes_only_presentation(self):
        from premium_models import PremiumPlan
        import hashlib
        name='Plano público '+secrets.token_hex(4)
        plan=PremiumPlan(name=name,interval='monthly',price_minor=12345,currency='MZN',description='Descrição pública.',benefits=['Benefício público'],active=True)
        row=InterfaceTranslation(key=hashlib.sha256(name.encode()).hexdigest(),source=name,english='Reviewed monthly plan',published=True)
        db.session.add_all([plan,row]);db.session.commit()
        page=self.client.get('/en/premium')
        self.assertEqual(page.status_code,200);self.assertIn('Reviewed monthly plan',page.text)
        self.assertEqual(plan.name,name);self.assertEqual(plan.price_minor,12345);self.assertEqual(plan.benefits,['Benefício público'])

    def test_premium_format_cards_follow_the_language_selector(self):
        from bs4 import BeautifulSoup

        portuguese = BeautifulSoup(self.client.get('/premium/').text, 'html.parser')
        english_link = portuguese.select_one('.language-selector a[lang="en"]')
        response = self.client.get(english_link['href'], follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request.path, '/en/premium/')
        english = BeautifulSoup(response.text, 'html.parser')
        cards = []
        for card in english.select('.premium-format-card'):
            link = card.select_one('h3 a')
            cards.append((link.get_text(strip=True).removesuffix('↗'), card.p.get_text(strip=True), link['href']))
        self.assertEqual(cards, [
            ('Specialised courses', 'Learning paths organised by topic.', '/en/premium/biblioteca?tipo=course'),
            ('Educational series', 'Content sequences to explore a subject.', '/en/premium/biblioteca?tipo=series'),
            ('Events', 'Meetings and training sessions.', '/en/premium/biblioteca?tipo=event'),
            ('Interviews', 'In-depth conversations about science and research.', '/en/premium/biblioteca?tipo=interview'),
        ])

        portuguese_link = english.select_one('.language-selector a[lang="pt-MZ"]')
        response = self.client.get(portuguese_link['href'], follow_redirects=True)
        restored = BeautifulSoup(response.text, 'html.parser')
        self.assertEqual(response.request.path, '/premium/')
        self.assertEqual(
            [card.get_text(' ', strip=True) for card in restored.select('.premium-format-card')],
            [card.get_text(' ', strip=True) for card in portuguese.select('.premium-format-card')],
        )

    def test_new_draft_can_be_translated_and_approved_but_not_published_before_original(self):
        self.article.status='draft';db.session.commit()
        item=self.make()
        self.assertEqual(self.post(item,'approve',reviewed='yes').status_code,302)
        self.assertEqual(self.post(item,'publish').status_code,409)
        self.assertEqual(self.client.get('/en/artigo/'+self.article.slug).status_code,404)
        self.article.status='published';db.session.commit()
        self.assertEqual(item.state,'approved')
        self.assertEqual(self.post(item,'publish').status_code,302)
        self.assertEqual(self.client.get('/en/artigo/'+self.article.slug).status_code,200)


    def test_manual_english_choice_persists_across_unprefixed_public_links(self):
        response=self.client.get('/idioma/en',query_string={'next':'/sobre'})
        self.assertEqual(response.location,'/en/sobre')
        for path in ['/sobre','/servicos','/contacto','/aprender','/submissoes/entrar']:
            with self.subTest(path=path):
                response=self.client.get(path)
                self.assertEqual(response.status_code,302)
                self.assertEqual(response.location,'/en'+path)
                self.assertIn('Cookie',response.headers.get('Vary',''))
                page=self.client.get(response.location)
                self.assertEqual(page.status_code,200)
                self.assertEqual(page.headers['Content-Language'],'en')
        response=self.client.get('/artigos?q=science&page=2')
        self.assertEqual(response.location,'/en/artigos?q=science&page=2')
        self.client.get('/idioma/pt',query_string={'next':'/en/sobre'})
        self.assertEqual(self.client.get('/sobre').status_code,200)
        self.assertIn('Quem somos',self.client.get('/sobre').text)

    def test_english_public_pages_and_author_forms_use_complete_interface_copy(self):
        from bs4 import BeautifulSoup
        cases={'/en/sobre':'Who we are','/en/contacto':'Send message',
               '/en/servicos':'Services for authors and researchers',
               '/en/politica-de-privacidade':'Privacy Policy',
               '/en/aprender':'Explore, experiment, understand.',
               '/en/submissoes/entrar':'Sign in'}
        for path,text in cases.items():
            with self.subTest(path=path):
                response=self.client.get(path)
                self.assertEqual(response.status_code,200)
                soup=BeautifulSoup(response.text,'html.parser')
                self.assertEqual(soup.html['lang'],'en')
                self.assertIn(text,soup.get_text(' ',strip=True))
        page=self.client.get('/en/aprender')
        self.assertIn('Explore the cell',page.text)
        self.assertNotIn('>Explore a célula<',page.text)
        self.assertIn('js/pages.js',self.client.get('/en/contacto').text)

    def test_english_client_catalogue_covers_interactive_messages(self):
        from i18n_client import KEYS
        from i18n_catalog import EN
        for key in KEYS:
            self.assertIn(key,EN,key)
        page=self.client.get('/en/recursos')
        self.assertIn('Sending',page.text)
        self.assertIn('Correct answer',page.text)
        self.assertIn('Mean',page.text)
        original=self.client.get('/recursos')
        self.assertIn('Calculadora descritiva',original.text)

    def test_cookie_locale_does_not_redirect_admin_api_or_modify_post_payloads(self):
        self.client.get('/idioma/en',query_string={'next':'/'})
        self.assertEqual(self.client.get('/admin/internacionalizacao/').status_code,200)
        response=self.client.post('/api/contacto',json={})
        self.assertNotEqual(response.status_code,302)
        self.assertEqual(response.headers['Content-Language'],'en')
        self.assertNotIn('/en/api/',response.headers.get('Location',''))
        self.assertEqual(self.article.body.splitlines()[0],'## Método')

    def test_bootstrap_catalogue_covers_public_templates_without_database_generation(self):
        from pathlib import Path
        from i18n_templates import PublicTranslationExtension, TEMPLATE_SOURCES
        from i18n_catalog import EN
        extension=PublicTranslationExtension(app.jinja_env)
        for path in Path(app.template_folder).rglob('*.html'):
            extension.preprocess(path.read_text(),str(path.relative_to(app.template_folder)))
        self.assertEqual({text for text in TEMPLATE_SOURCES if text not in EN and ' '.join(text.split()) not in EN},set())


    def test_published_custom_institutional_copy_uses_english_without_mutating_source(self):
        import hashlib
        from models import EditorialPolicy
        source='## Política própria\nConteúdo institucional original.'
        translated='## Custom policy\nReviewed institutional content.'
        policy=EditorialPolicy.query.first()
        created=policy is None
        if created:
            policy=EditorialPolicy();db.session.add(policy)
        previous=policy.page_content
        policy.page_content=source
        entry=InterfaceTranslation(key=hashlib.sha256(source.encode()).hexdigest(),source=source,english=translated,published=True)
        db.session.add(entry);db.session.commit()
        try:
            page=self.client.get('/en/politicas-editoriais')
            self.assertEqual(page.status_code,200)
            self.assertIn('Reviewed institutional content.',page.text)
            self.assertEqual(policy.page_content,source)
        finally:
            if created:db.session.delete(policy)
            else:policy.page_content=previous
            db.session.commit()


if __name__=='__main__':unittest.main()


