"""Disposable draft and published article for drop-cap rendering checks."""
import json,sys,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from app import app
from models import db,Article,Author,Category,utcnow
from translation_models import ContentTranslation
from translation_service import add_version, source
with app.app_context():
    token=uuid.uuid4().hex
    author=Author(name='Autor de teste de tipografia',slug='dropcap-'+token)
    category=Category.query.first()
    if not category:
        category=Category(name='Teste de tipografia',slug='dropcap-'+token)
        db.session.add(category)
    db.session.add(author);db.session.flush()
    body='À medida que observamos o céu, aprendemos a formular novas perguntas. **Texto em destaque** e uma [ligação](https://example.org) continuam no mesmo parágrafo.\n\nEste segundo parágrafo mantém a apresentação normal.'
    draft=Article(title='Teste isolado de capitular no editor',slug='dropcap-draft-'+token,author_id=author.id,category_id=category.id,summary='Registo isolado de teste da ferramenta de capitular.',body=body,status='draft')
    public=Article(title='Teste isolado de capitular publicada',slug='dropcap-public-'+token,author_id=author.id,category_id=category.id,summary='Registo isolado de teste da apresentação de capitulares.',body='[capitular] '+body,status='published',published_at=utcnow())
    db.session.add_all([draft,public]);db.session.commit()
    original=source('article',public.id)
    english=dict(original,title='Drop-cap rendering fixture',summary='A synthetic typography fixture.',
                 body='[drop_cap] An opening paragraph with **emphasis**.\n\nA second paragraph.')
    translation=ContentTranslation(kind='article',source_id=public.id)
    db.session.add(translation);db.session.flush()
    add_version(translation,original,english,dict(ready=True,faithful=True,issues=[]))
    translation.state='published';translation.approved_version=1;translation.published_version=1
    db.session.commit()
    print(json.dumps(dict(article_id=draft.id,slug=public.slug,body=body)))
