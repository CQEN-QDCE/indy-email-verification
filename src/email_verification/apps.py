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


        if cache.get("credential_definition_id") is None:
    
            # Est-ce que votre schéma existe sur la chaîne de blocs
            # Does your schema exist on the blockchain
            schema_id = {"FUKLxsjrYSHgScLbHuPTo4:2:CQENDroitAccesVirtuel:0.1"}
            logger.info(schema_id)
            schema_response = requests.get(f"{AGENT_URL}/schemas/{schema_id}", headers={"x-api-key": API_KEY})
            logger.info(schema_response.text)
            print("******************* Goodbye, Cruel World! 1A *******************")
            print(schema_response.text)
            print("******************* Goodbye, Cruel World! 1F *******************")
            schema_response_body = schema_response.json()
            print("******************* Goodbye, Cruel World! 2A *******************")
            print(schema_response_body)
            print("******************* Goodbye, Cruel World! 2F *******************")
            schema_id = schema_response_body["schema"]
            print("******************* Goodbye, Cruel World! 3A *******************")
            print(schema_id)
            print("******************* Goodbye, Cruel World! 3F *******************")
            
            # Sinon, créer le schéma avec votre agent
            # If not, create the schema with your agent
#            if len(schema_id) == 0:
#                # N'oubliez pas de changer les attributs pour votre cas d'utilisation
#                # Don't forget to change the attributes for your use case
#                schema_body = {
#                    "schema_name": "CQENDroitAccesVirtuel",
#                    "schema_version": "0.1",
#                    "attributes": ["email", "time"]
#                }

#                schema_response = requests.post(f"{AGENT_URL}/schemas", headers={"x-api-key": API_KEY}, json=schema_body)
#                logger.info(schema_response.text)

#                schema_response_body = schema_response.json()
#                schema_id = schema_response_body["schema_id"]
#                credential_definition_body = {"schema_id": schema_id}
#            else:
#                credential_definition_body = {"schema_id": schema_id[0]}

#            payload = {'schema_id': schema_id}
#            logger.info(payload)

#            credential_definition_response = requests.get(f"{AGENT_URL}/credential-definitions/created", headers={"x-api-key": API_KEY}, params=payload)
#            logger.info(credential_definition_response.text)
            
#            credential_definition_response_body = credential_definition_response.json()
#            tmp_credential_definition_id = credential_definition_response_body["credential_definition_ids"]

#            if len(tmp_credential_definition_id) == 0:
#                credential_definition_response = requests.post(f"{AGENT_URL}/credential-definitions", headers={"x-api-key": API_KEY}, json=credential_definition_body)
#                logger.info(credential_definition_response.text)

#                credential_definition_response_body = credential_definition_response.json()
#                credential_definition_id = credential_definition_response_body["credential_definition_id"]
#            else:
#                credential_definition_id = tmp_credential_definition_id[0]
            credential_definition_id = "FUKLxsjrYSHgScLbHuPTo4:3:CL:30781:default"
            logger.info(f"cred def id: {credential_definition_id}")

            cache.set("credential_definition_id", credential_definition_id, None)
