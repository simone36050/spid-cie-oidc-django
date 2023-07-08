import logging

from djagger.decorators import schema
from django.http import HttpResponseRedirect
from django.urls import reverse

from ..models import OidcAuthenticationToken
from ..oauth2 import *
from ..oidc import *

from . import SpidCieOidcRp
from django.views import View

from spid_cie_oidc.entity.jwtse import (
    unpad_jwt_payload,
)

from django.shortcuts import render

logger = logging.getLogger(__name__)


@schema(
    summary="OIDC Relying party refresh token request",
    methods=['GET'],
    external_docs={
        "alt_text": "AgID SPID OIDC Guidelines",
        "url": "https://www.agid.gov.it/it/agenzia/stampa-e-comunicazione/notizie/2021/12/06/openid-connect-spid-adottate-linee-guida"
    },
    tags=['Relying Party']
)
class SpidCieOidcRpIntrospection(SpidCieOidcRp, View):
    error_template = "rp_error.html"
    template = "rp_introspection.html"

    def get(self, request, *args, **kwargs):
        """
            Call the token endpoint of the op
        """
        auth_tokens = OidcAuthenticationToken.objects.filter(
            user=request.user
        ).filter(revoked__isnull=True)

        default_logout_url = getattr(
            settings, "LOGOUT_REDIRECT_URL", None
        ) or reverse("spid_cie_rp_landing")
        if not auth_tokens:
            logger.warning(
                "Token request failed: not found any authentication session"
            )

        auth_token = auth_tokens.last()

        try:
            token_response = self.get_token_request(auth_token, request, "introspection")
            introspection_token_response = json.loads(token_response.content.decode())
            data = {"introspection": introspection_token_response}
            return render(request, self.template, data)

        except Exception as e:  # pragma: no cover
            logger.warning(f"Refresh Token request failed: {e}")
