import os
import logging
import random
from datetime import datetime

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
            schema_response = requests.get(f"{AGENT_URL}/schemas/FUKLxsjrYSHgScLbHuPTo4:2:CQENDroitAccesVirtuel:0.2.3", headers={"x-api-key": API_KEY})
            logger.info(schema_response.text)
            logger.info(f"Does your schema exist on the blockchain: {schema_response.text}")
            schema_response_body = schema_response.json()
            schema_id = schema_response_body["schema"]

            # Sinon, créer le schéma avec votre agent
            # If not, create the schema with your agent
            #if len(schema_id) == 0:
            if schema_id is None:
                logger.info("******** JE SUIS DANS LA BOUCLE ********")
                # N'oubliez pas de changer les attributs pour votre cas d'utilisation
                # Don't forget to change the attributes for your use case
                schema_body = {
                    "schema_name": "CQENDroitAccesVirtuel",
                    "schema_version": "0.2.3",
                    "attributes": ["email", "time"]
                }

                schema_response = requests.post(f"{AGENT_URL}/schemas", headers={"x-api-key": API_KEY}, json=schema_body)
                logger.info(schema_response.text)

                schema_response_body = schema_response.json()
                schema_id = schema_response_body["schema_id"]
                payload = {"schema_id": schema_id}
            else:
                payload = {"schema_id": schema_id['id']}

            # Est-ce que votre credential definition existe sur votre agent aries
            # Does your credential definition exist on your aries agent
            logger.info(payload)
            credential_definition_response = requests.get(f"{AGENT_URL}/credential-definitions/created", headers={"x-api-key": API_KEY}, params=payload)
            logger.info(credential_definition_response.text)
            
            credential_definition_response_body = credential_definition_response.json()
            tmp_credential_definition_id = credential_definition_response_body["credential_definition_ids"]

            logger.info(f"tmp cred def id: {tmp_credential_definition_id}")

            # Sinon, créer le credential definition avec votre agent
            # Otherwise, create the credential definition with your agent
            if len(tmp_credential_definition_id) == 0:
                # N'oubliez pas de changer les attributs pour votre cas d'utilisation
                # Don't forget to change the attributes for your use case
                # changez le numéro sequentiel du tag, 
                random.seed(datetime.now().timestamp());
                randSeq = random.randint(100000,999999); 
                tag = "RegistreAccesVirtuelCQEN-"+ str(randSeq) +"-prod";
                credential_definition_body = {
                    # "revocation_registry_size": 10000,
                    "schema_id": "FUKLxsjrYSHgScLbHuPTo4:2:CQENDroitAccesVirtuel:0.2.3",
                    "support_revocation": "false",
                    "tag": tag
                }
                credential_definition_response = requests.post(f"{AGENT_URL}/credential-definitions", headers={"x-api-key": API_KEY}, json=credential_definition_body)
                logger.info(credential_definition_response.text)
                logger.info(f"credential_definition_response.status_code(): {credential_definition_response.status_code()}")
                if credential_definition_response.status_code() == 200:
                    credential_definition_response_body = credential_definition_response.json()
                    credential_definition_id = credential_definition_response_body["credential_definition_id"]
                else:
                    logger.info("The credential definition already exist on the ledger")
            else:
                credential_definition_id = tmp_credential_definition_id[0]

            logger.info(f"cred def id: {credential_definition_id}")

            cache.set("credential_definition_id", credential_definition_id, None)
