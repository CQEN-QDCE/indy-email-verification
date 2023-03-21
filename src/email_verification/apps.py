import os
import logging

from django.apps import AppConfig
from django.core.cache import cache
from django.db.utils import ProgrammingError

import requests

logger = logging.getLogger(__name__)

AGENT_URL = os.environ.get("AGENT_URL")

API_KEY = os.environ.get("AGENT_ADMIN_API_KEY", "")

class EmailVerificationConfig(AppConfig):
    name = "email_verification"

    def ready(self):

        # Hack to let the manage command to create the cache table through...
        try:
            cache.get("")
        except ProgrammingError:
            return

        logger.info(f"adresse agent: {AGENT_URL}")

        # test phil
        #credential_definition_id = "FUKLxsjrYSHgScLbHuPTo4:3:CL:30685:RegistreAccesVirtuelCQEN"

        if cache.get("credential_definition_id") is None:

            print("**********************Goodbye 1, cruel world!**********************")
            # https://exp-port-e-issuer-flihp-agent-admin.apps.exp.openshift.cqen.ca/schemas/created?schema_name={{schemaName}}&schema_version={{schemaVersion}}
            schema_response = requests.get(f"{AGENT_URL}/schemas/created?schema_name=CQENDroitAccesVirtuel&schema_version=0.1.10", headers={"x-api-key": API_KEY})

            logger.info(schema_response.text)
            schema_response_body = schema_response.json()
            schema_id = schema_response_body["schema_ids"]
            credential_definition_body = {"schema_id": schema_id[0]}

            print("**********************Goodbye 2, cruel world!**********************")
            if len(schema_id) == 0:
                print("**********************Goodbye 2A, cruel world!**********************")
                schema_body = {
                    "schema_name": "CQENDroitAccesVirtuel",
                    "schema_version": "0.1.10",
                    "attributes": ["email", "time"]
                }

                schema_response = requests.post(f"{AGENT_URL}/schemas", headers={"x-api-key": API_KEY}, json=schema_body)

                logger.info(schema_response.text)
                print(schema_response.text)
                schema_response_body = schema_response.json()
                schema_id = schema_response_body["schema_id"]
                credential_definition_body = {"schema_id": schema_id}


            print("**********************Goodbye 3, cruel world!**********************")
            # https://exp-port-e-issuer-flihp-agent-admin.apps.exp.openshift.cqen.ca/credential-definitions/created?schema_id={{schemaId}}
            credential_definition_response = requests.get(f"{AGENT_URL}/credential-definitions/created?schema_id={schema_id}", headers={"x-api-key": API_KEY})
            logger.info(credential_definition_response.text)
            credential_definition_response_body = credential_definition_response.json()
            credential_definition_id = credential_definition_response_body[
                "credential_definition_id"
            ]

            print("**********************Goodbye 4, cruel world!**********************")
            if len(credential_definition_id) == 0:
                print("**********************Goodbye 4A, cruel world!**********************")
                credential_definition_response = requests.post(
                    f"{AGENT_URL}/credential-definitions", headers={"x-api-key": API_KEY}, json=credential_definition_body
                )

                logger.info(credential_definition_response.text)
                credential_definition_response_body = credential_definition_response.json()
                credential_definition_id = credential_definition_response_body[
                    "credential_definition_id"
                ]

            print("**********************Goodbye 5, cruel world!**********************")
            logger.info(f"cred def id: {credential_definition_id}")
            print("**********************Goodbye 6, cruel world!**********************")

            cache.set("credential_definition_id", credential_definition_id, None)
            print("**********************Goodbye 7, cruel world!**********************")
