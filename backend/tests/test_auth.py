import os
os.environ['JWT_SECRET_KEY'] = 'test-only-secret-key-with-at-least-32-bytes'
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['ACCESS_TOKEN_EXPIRE_MINUTES'] = '1500'

from datetime import datetime, timedelta, timezone
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import Base, Membership, User
from app.models.tenant import Tenant


@pytest.fixture
def client():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([User(id='u1', email='user@example.com', password_hash=hash_password('correct-password')),
                    Tenant(id='t1', name='One'), Tenant(id='t2', name='Two')])
        db.flush()
        db.add(Membership(user_id='u1', tenant_id='t1'))
        db.commit()
    def override_db():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client, engine
    app.dependency_overrides.clear()
    engine.dispose()


def bearer(token):
    return {'Authorization': f'Bearer {token}'}


def test_login_and_isolation(client):
    api, _ = client
    result = api.post('/api/v1/auth/login', json={'email': 'USER@example.com', 'password': 'correct-password', 'tenant_id': 't1'})
    assert result.status_code == 200
    assert result.headers['cache-control'] == 'no-store'
    headers = bearer(result.json()['access_token'])
    me = api.get('/api/v1/auth/me', headers=headers)
    assert me.status_code == 200
    assert me.json() == {'user': {'id': 'u1', 'email': 'user@example.com', 'is_active': True}, 'tenant_id': 't1'}
    assert api.get('/api/v1/tenants/t1', headers=headers).status_code == 200
    assert api.get('/api/v1/tenants/t2', headers=headers).status_code == 404


@pytest.mark.parametrize('email,password,tenant', [('user@example.com','wrong','t1'), ('missing@example.com','correct-password','t1'), ('user@example.com','correct-password','t2')])
def test_invalid_login(client, email, password, tenant):
    api, _ = client
    assert api.post('/api/v1/auth/login', json={'email':email,'password':password,'tenant_id':tenant}).status_code == 401


@pytest.mark.parametrize('kind', ['missing','invalid','expired','signature','tenant','missing-claim','bad-claim','algorithm','issuer','audience'])
def test_invalid_tokens(client, kind):
    api, _ = client
    token = create_access_token('u1', 't1')
    claims = jwt.decode(token, options={'verify_signature':False})
    secret = settings.JWT_SECRET_KEY.get_secret_value()
    algorithm = 'HS256'
    if kind == 'expired':
        claims['exp'] = datetime.now(timezone.utc) - timedelta(seconds=1)
    elif kind == 'signature':
        secret = 'wrong-secret-with-more-than-thirty-two-bytes'
    elif kind == 'tenant':
        claims['tenant_id'] = 't2'
    elif kind == 'missing-claim':
        del claims['tenant_id']
    elif kind == 'bad-claim':
        claims['tenant_id'] = []
    elif kind == 'issuer':
        claims['iss'] = 'other'
    elif kind == 'audience':
        claims['aud'] = 'other'
    elif kind == 'algorithm':
        algorithm = 'HS384'
    token = jwt.encode(claims, secret, algorithm=algorithm)
    headers = {} if kind == 'missing' else bearer('invalid' if kind == 'invalid' else token)
    result = api.get('/api/v1/auth/me', headers=headers)
    assert result.status_code == 401
    assert result.headers['www-authenticate'] == 'Bearer'


@pytest.mark.parametrize('entity', ['user','tenant','membership','deleted-membership'])
def test_revoked_access(client, entity):
    api, engine = client
    token = create_access_token('u1','t1')
    with Session(engine) as db:
        obj = db.get(User, 'u1') if entity == 'user' else db.get(Tenant,'t1') if entity == 'tenant' else db.get(Membership,('u1','t1'))
        if entity == 'deleted-membership':
            db.delete(obj)
        else:
            obj.is_active = False
        db.commit()
    assert api.get('/api/v1/auth/me', headers=bearer(token)).status_code == 401
    assert api.post('/api/v1/auth/login', json={'email':'user@example.com','password':'correct-password','tenant_id':'t1'}).status_code == 401


def test_argon2():
    hashed = hash_password('secret')
    assert hashed.startswith('$argon2id$')
    assert verify_password('secret',hashed)
    assert not verify_password('wrong',hashed)


def test_token_lifetime(client):
    from app.core.security import decode_access_token
    api, _ = client
    result = api.post('/api/v1/auth/login', json={
        'email': 'user@example.com', 'password': 'correct-password', 'tenant_id': 't1'})
    assert result.status_code == 200
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 1500
    assert result.json()['expires_in'] == 90000
    claims = decode_access_token(result.json()['access_token'])
    assert claims['exp'] - claims['iat'] == 90000
