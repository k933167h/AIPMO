"""OIDC JWT verification using issuer JWKS, RS256 and audience validation."""
import os
import jwt
from jwt import PyJWKClient
from fastapi import HTTPException

def verify_oidc(token, required_role="SME"):
    issuer=os.environ.get("PMO_OIDC_ISSUER","").rstrip("/")
    audience=os.environ.get("PMO_OIDC_AUDIENCE","")
    jwks_url=os.environ.get("PMO_OIDC_JWKS_URL","")
    if not issuer or not audience or not jwks_url:
        raise HTTPException(503,"OIDC not configured")
    if not token: raise HTTPException(403,"OIDC token required")
    if not jwks_url.startswith("https://"):
        raise HTTPException(503,"OIDC JWKS URL must be HTTPS")
    try:
        key=PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
        claims=jwt.decode(token,key.key,algorithms=["RS256"],issuer=issuer,audience=audience,
                          options={"require":["exp","iat","iss","aud","sub"]})
    except (jwt.PyJWTError,ValueError,OSError) as exc:
        raise HTTPException(403,"invalid OIDC token") from exc
    roles=claims.get("roles",[])
    if not isinstance(roles,list) or required_role not in roles:
        raise HTTPException(403,"insufficient OIDC role")
    return claims["sub"]
