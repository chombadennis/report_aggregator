import os
import logging
import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL")

# Default fallback JWKS URL for Clerk if not set
if not CLERK_JWKS_URL:
    logger.warning("CLERK_JWKS_URL is not set in environment variables.")

class ClerkVerifier:
    def __init__(self, jwks_url: str = None):
        self.jwks_url = jwks_url or CLERK_JWKS_URL
        self.jwk_client = None
        if self.jwks_url:
            try:
                self.jwk_client = PyJWKClient(self.jwks_url)
                logger.info(f"ClerkVerifier initialized with JWKS URL: {self.jwks_url}")
            except Exception as e:
                logger.error(f"Failed to initialize PyJWKClient: {e}")

    def verify_token(self, token: str) -> dict:
        if not self.jwk_client:
            # Re-read CLERK_JWKS_URL if it was set dynamically after import
            jwks_url = os.getenv("CLERK_JWKS_URL")
            if not jwks_url:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Clerk Authentication is misconfigured. CLERK_JWKS_URL is missing in .env."
                )
            try:
                self.jwk_client = PyJWKClient(jwks_url)
            except Exception as e:
                logger.error(f"Failed to initialize PyJWKClient on-demand: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to initialize Clerk JWK Client. Check CLERK_JWKS_URL configuration."
                )

        try:
            # Fetch the public key from the JWKS matching the kid in JWT header
            signing_key = self.jwk_client.get_signing_key_from_jwt(token)
            
            # Decode the token, verifying signature and expiration with a 120s leeway for clock skew
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                leeway=120,
                options={"verify_exp": True, "verify_aud": False}
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please sign in again."
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed. Please ensure you are logged in."
            )

# Global verifier instance
clerk_verifier = ClerkVerifier()
