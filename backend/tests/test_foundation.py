import pytest
from pydantic import ValidationError
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from test_auth import client
from app.api.deps import get_db
from app.core.config import Settings
from app.main import app


def test_health_and_ready(client):
    api, _ = client
    for route in ('health', 'ready'):
        response = api.get('/api/v1/' + route)
        assert response.status_code == 200
        assert response.json() == {'status': 'ok'}


def test_ready_unavailable(client):
    api, _ = client

    class Unavailable:
        def execute(self, statement):
            assert str(statement) == 'SELECT 1'
            raise OperationalError('private server details', {}, Exception('private'))

    app.dependency_overrides[get_db] = lambda: Unavailable()
    response = api.get('/api/v1/ready')
    assert response.status_code == 503
    assert response.json() == {'status': 'unavailable'}
    assert api.get('/api/v1/health').json() == {'status': 'ok'}


@pytest.mark.parametrize('minutes', [0, -1])
def test_positive_expiration(minutes):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ACCESS_TOKEN_EXPIRE_MINUTES=minutes)


def test_postgres_url_and_precedence(monkeypatch):
    monkeypatch.delenv('DATABASE_URL')
    password = 'synthetic@:/?#% password'
    config = Settings(_env_file=None, POSTGRES_PASSWORD=password,
                      POSTGRES_HOST='localhost', POSTGRES_PORT=5434)
    url = make_url(config.DATABASE_URL)
    assert url.password == password
    assert url.host == 'localhost'
    assert url.port == 5434
    assert config.ACCESS_TOKEN_EXPIRE_MINUTES == 1500
    explicit = Settings(_env_file=None, DATABASE_URL='sqlite://', POSTGRES_PASSWORD=password)
    assert explicit.DATABASE_URL == 'sqlite://'
