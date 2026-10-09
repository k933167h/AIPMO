"""Simple identity-bound RBAC using deployment-configured token hashes.

PMO_IDENTITIES_JSON maps opaque bearer tokens to {user_id, roles}. Keep tokens
in a secret manager and use OIDC/JWT identity provider for production.
"""
import hmac
import json
import os
from fastapi import HTTPException

def resolve_identity(token, required_role):
    try:
        identities=json.loads(os.environ.get("PMO_IDENTITIES_JSON","{}"))
    except (ValueError,TypeError):
        raise HTTPException(503,"identity configuration invalid")
    if not isinstance(identities,dict) or not token:
        raise HTTPException(403,"identity credential required")
    for credential,principal in identities.items():
        if isinstance(credential,str) and hmac.compare_digest(token,credential):
            if not isinstance(principal,dict) or not isinstance(principal.get("user_id"),str) or not principal["user_id"]:
                break
            if required_role not in principal.get("roles",[]):
                raise HTTPException(403,"insufficient role")
            return principal["user_id"]
    raise HTTPException(403,"identity credential invalid")
