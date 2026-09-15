import pytest
from sqlalchemy.orm import Session
from test_auth import client, bearer
from app.core.security import create_access_token
from app.models.company import Company
from app.models.user import Membership


def headers(tenant='t1'):
    return bearer(create_access_token('u1', tenant))


def test_company_lifecycle_and_isolation(client):
    api, engine = client
    with Session(engine) as db:
        db.add(Membership(user_id='u1', tenant_id='t2'))
        db.commit()
    first = api.post('/api/v1/companies', headers=headers(), json={'name': '  Previum  '})
    assert first.status_code == 201
    company = first.json()
    assert company['name'] == 'Previum'
    assert company['tenant_id'] == 't1'
    assert company['is_active'] is True
    other = api.post('/api/v1/companies', headers=headers('t2'), json={'name': 'Outra'})
    assert other.status_code == 201
    assert api.get('/api/v1/companies', headers=headers()).json() == [company]
    assert api.get('/api/v1/companies', headers=headers('t2')).json() == [other.json()]
    path = '/api/v1/companies/' + company['id']
    assert api.patch(path, headers=headers('t2'), json={'name': 'Invadida'}).status_code == 404
    assert api.patch('/api/v1/companies/missing', headers=headers(), json={'name': 'X'}).status_code == 404
    with Session(engine) as db:
        assert db.get(Company, company['id']).name == 'Previum'
    changed = api.patch(path, headers=headers(), json={'is_active': False})
    assert changed.status_code == 200
    assert changed.json()['name'] == 'Previum'
    assert changed.json()['is_active'] is False
    renamed = api.patch(path, headers=headers(), json={'name': 'Novo nome'})
    assert renamed.status_code == 200
    assert renamed.json()['name'] == 'Novo nome'
    assert renamed.json()['is_active'] is False
    assert api.get('/api/v1/companies?offset=1&limit=1', headers=headers()).json() == []


@pytest.mark.parametrize('payload', [{'name': ''}, {'name': '  '}, {'name': 'x' * 201},
                                      {'name': 'X', 'tenant_id': 't2'}, {'name': None}])
def test_invalid_create(client, payload):
    api, _ = client
    assert api.post('/api/v1/companies', headers=headers(), json=payload).status_code == 422


@pytest.mark.parametrize('payload', [{}, {'name': None}, {'is_active': None},
                                      {'name': ' '}, {'tenant_id': 't2'}, {'id': 'new'}])
def test_invalid_update(client, payload):
    api, _ = client
    assert api.patch('/api/v1/companies/any', headers=headers(), json=payload).status_code == 422


@pytest.mark.parametrize('method,path,payload', [('GET', '/api/v1/companies', None),
    ('GET', '/api/v1/companies/any', None),
    ('POST', '/api/v1/companies', {'name': 'X'}),
    ('PATCH', '/api/v1/companies/any', {'name': 'X'})])
def test_auth_required_and_revoked(client, method, path, payload):
    api, engine = client
    assert api.request(method, path, json=payload).status_code == 401
    with Session(engine) as db:
        db.get(Membership, ('u1', 't1')).is_active = False
        db.commit()
    assert api.request(method, path, headers=headers(), json=payload).status_code == 401


@pytest.mark.parametrize('query', ['offset=-1', 'limit=0', 'limit=101'])
def test_pagination_limits(client, query):
    api, _ = client
    assert api.get('/api/v1/companies?' + query, headers=headers()).status_code == 422


def test_get_company(client):
    api, engine = client
    with Session(engine) as db:
        db.add(Membership(user_id='u1', tenant_id='t2'))
        db.commit()
    company = api.post('/api/v1/companies', headers=headers(), json={'name': 'Individual'}).json()
    path = '/api/v1/companies/' + company['id']
    assert api.get(path, headers=headers()).json() == company
    assert api.get(path, headers=headers('t2')).status_code == 404
    assert api.get('/api/v1/companies/missing', headers=headers()).status_code == 404
    api.patch(path, headers=headers(), json={'is_active': False})
    assert api.get(path, headers=headers()).json()['is_active'] is False
    assert api.get('/api/v1/companies', headers=headers()).json()[0]['is_active'] is False


@pytest.mark.parametrize('operation', ['create', 'update'])
@pytest.mark.parametrize('failure', ['flush', 'commit'])
def test_transaction_rollback(client, monkeypatch, operation, failure):
    from sqlalchemy import select
    from sqlalchemy.exc import SQLAlchemyError
    from app.schemas.company import CompanyCreate, CompanyUpdate
    from app.services.company_service import CompanyService

    _, engine = client
    with Session(engine) as db:
        db.add(Company(id='existing', tenant_id='t1', name='Original'))
        db.commit()
        service = CompanyService(db)

        def fail(*args, **kwargs):
            raise SQLAlchemyError('simulated failure')

        with monkeypatch.context() as patch:
            patch.setattr(db, failure, fail)
            with pytest.raises(SQLAlchemyError):
                if operation == 'create':
                    service.create('t1', CompanyCreate(name='Temporary'))
                else:
                    service.update('existing', 't1', CompanyUpdate(name='Changed'))
        assert not db.in_transaction()
        assert db.get(Company, 'existing').name == 'Original'
        assert len(db.scalars(select(Company)).all()) == 1
        assert service.create('t1', CompanyCreate(name='Recovered')).name == 'Recovered'
