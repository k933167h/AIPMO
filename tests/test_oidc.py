import pytest
from fastapi import HTTPException
from app.oidc import verify_oidc

def test_oidc_configuration_required(monkeypatch):
    for key in ("PMO_OIDC_ISSUER","PMO_OIDC_AUDIENCE","PMO_OIDC_JWKS_URL"):
        monkeypatch.delenv(key,raising=False)
    with pytest.raises(HTTPException) as err: verify_oidc("token")
    assert err.value.status_code==503

def test_oidc_token_required(monkeypatch):
    monkeypatch.setenv("PMO_OIDC_ISSUER","https://issuer.example")
    monkeypatch.setenv("PMO_OIDC_AUDIENCE","pmo")
    monkeypatch.setenv("PMO_OIDC_JWKS_URL","https://issuer.example/jwks")
    with pytest.raises(HTTPException) as err: verify_oidc("")
    assert err.value.status_code==403

def test_https_jwks_required(monkeypatch):
    monkeypatch.setenv("PMO_OIDC_ISSUER","https://issuer.example")
    monkeypatch.setenv("PMO_OIDC_AUDIENCE","pmo")
    monkeypatch.setenv("PMO_OIDC_JWKS_URL","http://issuer.example/jwks")
    with pytest.raises(HTTPException) as err: verify_oidc("token")
    assert err.value.status_code==503
