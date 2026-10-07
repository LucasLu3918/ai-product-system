"""Verify GitHub-issued OIDC identity before exact branch cleanup."""

from __future__ import annotations

import base64
import json
import os
import time
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

ISSUER = "https://token.actions.githubusercontent.com"


class IdentityError(ValueError):
    pass


def decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_json(request: str | Request) -> dict[str, Any]:
    # Reject redirects before an Authorization header can leave its original host.
    with build_opener(NoRedirect()).open(request, timeout=20) as response:
        requested = request.full_url if isinstance(request, Request) else request
        if urlparse(response.geturl()).hostname != urlparse(requested).hostname:
            raise IdentityError("identity request redirected outside its trusted host")
        value = response.read(1_000_001)
    if len(value) > 1_000_000:
        raise IdentityError("identity response is oversized")
    data = json.loads(value)
    if not isinstance(data, dict):
        raise IdentityError("identity response must be an object")
    return data


def verify_token(token: str, keys: dict[str, Any], *, repository: str, baseline: str,
                 audience: str, now: float | None = None) -> dict[str, Any]:
    """Fixture keys are test evidence only; production keys come from the fixed issuer."""
    try:
        if len(token) > 32_000:
            raise ValueError("oversized token")
        header_part, body_part, signature = token.split(".")
        header, claims = json.loads(decode(header_part)), json.loads(decode(body_part))
        if header.get("alg") != "RS256":
            raise ValueError("unsupported algorithm")
        key = next(key for key in keys["keys"] if key.get("kid") == header.get("kid") and key.get("kty") == "RSA"
                   and key.get("use", "sig") == "sig" and key.get("alg", "RS256") == "RS256")
        public = rsa.RSAPublicNumbers(int.from_bytes(decode(key["e"]), "big"), int.from_bytes(decode(key["n"]), "big")).public_key()
        if public.key_size < 2048:
            raise ValueError("weak signing key")
        public.verify(decode(signature), f"{header_part}.{body_part}".encode(), padding.PKCS1v15(), hashes.SHA256())
        instant = time.time() if now is None else now
        expected = {"iss": ISSUER, "aud": audience, "repository": repository, "ref": "refs/heads/main",
                    "sha": baseline, "workflow_sha": baseline, "event_name": "workflow_dispatch",
                    "workflow_ref": f"{repository}/.github/workflows/branch-hygiene.yml@refs/heads/main"}
        if any(claims.get(key) != value for key, value in expected.items()):
            raise ValueError("claim mismatch")
        if claims.get("ref_protected") not in (True, "true"):
            raise ValueError("unprotected ref")
        if not all(type(claims[key]) in (int, float) for key in ("nbf", "exp", "iat")):
            raise ValueError("invalid timestamp types")
        if not (claims["nbf"] <= instant < claims["exp"] and claims["iat"] <= instant + 30
                and 0 < claims["exp"] - claims["iat"] <= 900):
            raise ValueError("invalid token lifetime")
        if not str(claims.get("run_id", "")).isdigit() or not claims.get("actor"):
            raise ValueError("missing execution identity")
        return claims
    except Exception as exc:
        raise IdentityError("GitHub execution identity verification failed") from exc


def cleanup_identity(repository: str, baseline: str, binding: str) -> dict[str, Any]:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise IdentityError("cleanup requires a protected-main workflow dispatch")
    audience = f"aips:branch-cleanup:{repository}:{baseline}:{binding}"
    endpoint, credential = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL", ""), os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not (parsed.hostname or "").endswith(".actions.githubusercontent.com") or not credential:
        raise IdentityError("GitHub OIDC request credentials are unavailable")
    query = dict(parse_qsl(parsed.query)); query["audience"] = audience
    endpoint = urlunparse(parsed._replace(query=urlencode(query)))
    try:
        response = fetch_json(Request(endpoint, headers={"Authorization": f"bearer {credential}"}))
        claims = verify_token(response["value"], fetch_json(ISSUER + "/.well-known/jwks"),
                              repository=repository, baseline=baseline, audience=audience)
        if claims["run_id"] != os.environ.get("GITHUB_RUN_ID"):
            raise IdentityError("execution run ID mismatch")
        return {"actor": claims["actor"], "run_id": claims["run_id"], "issuer": ISSUER}
    except Exception as exc:
        raise IdentityError("GitHub execution identity is unavailable or invalid") from exc
