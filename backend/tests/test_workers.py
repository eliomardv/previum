import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from test_auth import client
from test_companies import headers
from app.models.company import Company
from app.models.user import Membership
from app.models.worker import Worker
from app.schemas.worker import WorkerCreate, WorkerUpdate
from app.services.worker_service import WorkerService


@pytest.fixture
def setup(client):
    api, engine = client
    with Session(engine) as db:
        db.add(Membership(user_id='u1', tenant_id='t2'))
        db.add_all([Company(id='c1', tenant_id='t1', name='One'),
                    Company(id='c2', tenant_id='t1', name='Two'),
                    Company(id='other', tenant_id='t2', name='Other')])
        db.commit()
    return api, engine


def payload(**changes):
    return {'company_id': 'c1', 'name': '  Ana  ', 'registration': '  001  ', **changes}


def test_lifecycle(setup):
    api, _ = setup
    response = api.post('/api/v1/workers', headers=headers(), json=payload())
    assert response.status_code == 201
    worker = response.json()
    assert worker == {**worker, 'name': 'Ana', 'registration': '001', 'tenant_id': 't1',
                      'company_id': 'c1', 'is_active': True}
    path = '/api/v1/workers/' + worker['id']
    assert api.get(path, headers=headers()).json() == worker
    assert api.get('/api/v1/workers?company_id=c1', headers=headers()).json() == [worker]
    assert api.get('/api/v1/workers?company_id=c2', headers=headers()).json() == []
    response = api.patch(path, headers=headers(), json={
        'company_id': 'c2', 'name': 'Bia', 'registration': '002', 'is_active': False})
    assert response.status_code == 200
    assert response.json()['company_id'] == 'c2'
    assert response.json()['registration'] == '002'
    assert response.json()['name'] == 'Bia'
    assert response.json()['is_active'] is False
    assert api.get(path, headers=headers()).json() == response.json()
    assert api.get('/api/v1/workers?company_id=c2', headers=headers()).json() == [response.json()]
    assert api.get('/api/v1/workers?offset=1&limit=1', headers=headers()).json() == []
    assert api.delete(path, headers=headers()).status_code == 405


def test_isolation(setup):
    api, engine = setup
    worker = api.post('/api/v1/workers', headers=headers(), json=payload()).json()
    path = '/api/v1/workers/' + worker['id']
    assert api.get('/api/v1/workers', headers=headers('t2')).json() == []
    assert api.get(path, headers=headers('t2')).status_code == 404
    assert api.patch(path, headers=headers('t2'), json={'name': 'Intruder'}).status_code == 404
    for company in ('other', 'missing'):
        assert api.post('/api/v1/workers', headers=headers(), json=payload(company_id=company)).status_code == 404
        assert api.patch(path, headers=headers(), json={'company_id': company}).status_code == 404
        assert api.get('/api/v1/workers?company_id=' + company, headers=headers()).status_code == 404
    for method in ('get', 'patch'):
        kwargs = {'json': {'name': 'X'}} if method == 'patch' else {}
        assert getattr(api, method)('/api/v1/workers/missing', headers=headers(), **kwargs).status_code == 404
    with Session(engine) as db:
        assert db.get(Worker, worker['id']).company_id == 'c1'
        assert len(db.scalars(select(Worker)).all()) == 1


@pytest.mark.parametrize('method,path,data', [
    ('GET', '/api/v1/workers', None),
    ('GET', '/api/v1/workers/any', None),
    ('POST', '/api/v1/workers', payload()),
    ('PATCH', '/api/v1/workers/any', {'is_active': False}),
])
def test_authentication(setup, method, path, data):
    api, engine = setup
    assert api.request(method, path, json=data).status_code == 401
    token_headers = headers()
    with Session(engine) as db:
        db.get(Membership, ('u1', 't1')).is_active = False
        db.commit()
    assert api.request(method, path, headers=token_headers, json=data).status_code == 401


@pytest.mark.parametrize('changes', [
    {'name': ''}, {'name': ' '}, {'name': 'x' * 201}, {'registration': ''},
    {'registration': 'x' * 101}, {'company_id': ''}, {'name': None},
    {'registration': None}, {'tenant_id': 't2'}, {'id': 'injected'},
])
def test_create_validation(setup, changes):
    api, _ = setup
    assert api.post('/api/v1/workers', headers=headers(), json=payload(**changes)).status_code == 422


@pytest.mark.parametrize('data', [{}, {'name': None}, {'registration': None},
    {'company_id': None}, {'is_active': None}, {'tenant_id': 't2'}, {'name': ' '}])
def test_patch_validation(setup, data):
    api, _ = setup
    assert api.patch('/api/v1/workers/any', headers=headers(), json=data).status_code == 422


@pytest.mark.parametrize('query', ['offset=-1', 'limit=0', 'limit=101'])
def test_pagination(setup, query):
    api, _ = setup
    assert api.get('/api/v1/workers?' + query, headers=headers()).status_code == 422


@pytest.mark.parametrize('operation', ['create', 'update'])
@pytest.mark.parametrize('failure', ['flush', 'commit'])
def test_rollback(setup, monkeypatch, operation, failure):
    _, engine = setup
    with Session(engine) as db:
        service = WorkerService(db)
        original = service.create('t1', WorkerCreate(**payload()))
        def fail(*args, **kwargs):
            raise SQLAlchemyError('simulated')
        with monkeypatch.context() as patch:
            patch.setattr(db, failure, fail)
            with pytest.raises(SQLAlchemyError):
                if operation == 'create':
                    service.create('t1', WorkerCreate(**payload()))
                else:
                    service.update(original.id, 't1', WorkerUpdate(name='Changed'))
        assert not db.in_transaction()
        assert db.get(Worker, original.id).name == 'Ana'
        assert len(db.scalars(select(Worker)).all()) == 1
        assert service.update(original.id, 't1', WorkerUpdate(name='Recovered')).name == 'Recovered'
