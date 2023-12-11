import base64
import io
import os
import re
import json
import time
from datetime import datetime

import qrcode
import requests


from django.http import (
    JsonResponse,
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseBadRequest,
)
from django.template import loader
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

from .forms import EmailForm
from .models import Verification, SessionState

import logging

logger = logging.getLogger(__name__)

AGENT_URL = os.environ.get("AGENT_URL")
API_KEY = os.environ.get("AGENT_ADMIN_API_KEY", "")

def index(request):
    template = loader.get_template("index.html")
    return HttpResponse(template.render({"form": EmailForm()}, request))


def submit(request):
    if request.method == "POST":
        form = EmailForm(request.POST)
        if form.is_valid():

            response = requests.post(f"{AGENT_URL}/connections/create-invitation",headers={"x-api-key": API_KEY})
            invite = response.json()

            connection_id = invite["connection_id"]
            invite_url = invite["invitation_url"]

            form.instance.connection_id = connection_id
            form.instance.invite_url = invite_url
            form.save()

            email = form.instance.email

            redirect_url = f"{os.environ.get('SITE_URL')}/verify/{connection_id}"

            template = loader.get_template("email.html")
            email_html = template.render({"redirect_url": redirect_url}, request)

            send_mail(
                "Invitation du Service de vérification de courriel du CQEN",
                (
                    "Follow this link to connect with our "
                    f"verification service: {redirect_url}"
                ),
                "Service de vérification de courriel du CQEN <ne-pas-repondre@cqen.ca>",
                [email],
                fail_silently=False,
                html_message=email_html,
            )

            SessionState.objects.get_or_create(
                connection_id=connection_id, state="invite-created"
            )

            return HttpResponseRedirect(f"/thanks?email={form.instance.email}")
        else:
            return HttpResponseBadRequest()


def thanks(request):
    try:
        email = request.GET["email"]
    except Exception:
        return HttpResponseBadRequest()

    template = loader.get_template("thanks.html")
    return HttpResponse(template.render({"email": email}, request))


def state(request, connection_id):
    state = SessionState.objects.get(connection_id=connection_id)
    resp = {"state": state.state}
    try:
        attendee = Verification.objects.get(connection_id=connection_id)
        resp["email"] = attendee.email
    except Exception:
        pass

    return JsonResponse(resp)


def in_progress(request, connection_id):
    state = SessionState.objects.get(connection_id=connection_id)
    template = loader.get_template("in_progress.html")
    return HttpResponse(
        template.render({"connection_id": connection_id, state: state.state}, request)
    )


def verify_redirect(request, connection_id):
    verification = get_object_or_404(Verification, connection_id=connection_id)
    invitation_url = verification.invite_url

    didcomm_url = re.sub(r"^https?:\/\/\S*\?", "didcomm://invite?", invitation_url)

    template = loader.get_template("verify.html")

    stream = io.BytesIO()
    qr_png = qrcode.make(invitation_url)
    qr_png.save(stream, "PNG")
    qr_png_b64 = base64.b64encode(stream.getvalue()).decode("utf-8")

    return HttpResponse(
        template.render(
            {
                "qr_png": qr_png_b64,
                "didcomm_url": didcomm_url,
                "invitation_url": invitation_url,
                "connection_id": verification.connection_id,
            },
            request,
        )
    )


@csrf_exempt
def webhooks(request, topic):

    print("****************************** Waypoint 1 ******************************")
    message = json.loads(request.body)
    print("****************************** Waypoint 2 ******************************")
    logger.info(f"webhook recieved - topic: {topic} body: {request.body}")

    print("****************************** Waypoint 3 ******************************")
    if topic == "connections" and message["state"] == "request":
        print("****************************** Waypoint 3A ******************************")
        connection_id = message["connection_id"]
        print("****************************** Waypoint 3B ******************************")
        SessionState.objects.filter(connection_id=connection_id).update(state="connection-request-received")

    # Handle new invites, send cred offer
    print("****************************** Waypoint 4 ******************************")
    if topic == "connections" and message["state"] == "response":
        print("****************************** Waypoint 4A ******************************")
        print("****************************** Waypoint 4B ******************************")
        credential_definition_id = cache.get("credential_definition_id")
        print("****************************** Waypoint 4C ******************************")
        assert credential_definition_id is not None
        print("****************************** Waypoint 4D ******************************")
        connection_id = str(message["connection_id"])

        print("****************************** Waypoint 4F ******************************")
        SessionState.objects.filter(connection_id=connection_id).update(state="connection-formed")

        time.sleep(5)

        print("****************************** Waypoint 4G ******************************")
        logger.info(
            f"Sending credential offer for connection {connection_id} "
            f"and credential definition {credential_definition_id}"
        )

        print("****************************** Waypoint 4H ******************************")
        verification = get_object_or_404(Verification, connection_id=connection_id)

        print("****************************** Waypoint 4I ******************************")
        request_body = {
            "auto_issue": True,
            "connection_id": connection_id,
            "cred_def_id": credential_definition_id,
            "credential_preview": {
                "attributes": [
                    {
                        "name": "email",
                        "value": verification.email,
                        "mime-type": "text/plain",
                    },
                    {
                        "name": "time",
                        "value": str(datetime.utcnow()),
                        "mime-type": "text/plain",
                    },
                ]
            },
        }

        print("****************************** Waypoint 4J ******************************")
        print(request_body)
        print("****************************** Waypoint 4K ******************************")

        try:
            print("****************************** Waypoint 5A ******************************")
            response = requests.post(f"{AGENT_URL}/issue-credential/send-offer",headers={"x-api-key": API_KEY}, json=request_body)
            print("****************************** Waypoint 5B ******************************")
            print(response)
            response.raise_for_status()
            print("****************************** Waypoint 5C ******************************")
            print(response.raise_for_status())
        except Exception:
            print("****************************** Waypoint 5D ******************************")
            logger.exception("Error sending credential offer:")
            print("****************************** Waypoint 5E ******************************")
            SessionState.objects.filter(connection_id=connection_id).update(state="offer-error")
            print("****************************** Waypoint 5F ******************************")
        else:
            print("****************************** Waypoint 5G ******************************")
            SessionState.objects.filter(connection_id=connection_id).update(state="offer-sent")
            print("****************************** Waypoint 5H ******************************")

        print("****************************** Waypoint 6 ******************************")
        return HttpResponse()

    # Handle completion of credential issue
    print("****************************** Waypoint 7 ******************************")
    if topic == "issue_credential" and message["state"] == "credential_issued":
        print("****************************** Waypoint 7A ******************************")
        credential_exchange_id = message["credential_exchange_id"]
        print("****************************** Waypoint 7B ******************************")
        connection_id = message["connection_id"]

        print("****************************** Waypoint 7C ******************************")
        logger.info(
            "Completed credential issue for credential exchange "
            f"{credential_exchange_id} and connection {connection_id}"
        )

        print("****************************** Waypoint 7D ******************************")
        SessionState.objects.filter(connection_id=connection_id).update(
            state="credential-issued"
        )

        print("****************************** Waypoint 7E ******************************")
        return HttpResponse()

    print("****************************** Waypoint 8 ******************************")
    logger.warning(f"Webhook for topic {topic} and state {message['state']} is not implemented")
    return HttpResponse()
    