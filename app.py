from flask import Flask, request, jsonify
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_model import Response, RequestEnvelope
from ask_sdk_model.ui import SimpleCard, AskForPermissionsConsentCard
from ask_sdk_model.services import ServiceException
from ask_sdk_core.exceptions import SerializationException
import db
import logging
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.message import EmailMessage
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def load_strings():
    with open("strings.json", "r", encoding="utf-8") as f:
        return json.load(f)

STRINGS = load_strings()

app = Flask(__name__)
sb = CustomSkillBuilder(api_client=DefaultApiClient())
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("skill.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Handlers ---

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speech_text = STRINGS["WELCOME_MESSAGE"]
        handler_input.response_builder.speak(speech_text).ask(speech_text).set_card(
            SimpleCard(STRINGS["CARD_TITLE"], speech_text))
        return handler_input.response_builder.response

class ScriviIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("ScriviIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["is_recording"] = True
        session_attr["recording_text"] = ""
        
        speech_text = STRINGS["START_DICTATION"]
        return handler_input.response_builder.speak(speech_text).ask(STRINGS["LISTENING"]).response

class DictationIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("DictationIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        
        if not session_attr.get("is_recording"):
            speech_text = STRINGS["NOT_RECORDING_START"]
            return handler_input.response_builder.speak(speech_text).ask(speech_text).response

        slots = handler_input.request_envelope.request.intent.slots
        dictation_text = slots["dictation"].value if slots["dictation"] and slots["dictation"].value else ""
        
        current_text = session_attr.get("recording_text", "")
        if current_text:
            current_text += " " + dictation_text
        else:
            current_text = dictation_text
        
        session_attr["recording_text"] = current_text
        
        speech_text = STRINGS["CONTINUE_OR_FINISH"]
        return handler_input.response_builder.speak(speech_text).ask(STRINGS["LISTENING"]).response

class FinishIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("FinishIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        
        if session_attr.get("is_recording"):
            user_id = handler_input.request_envelope.session.user.user_id
            text = session_attr.get("recording_text", "")
            if text:
                db.save_note(user_id, text)
                msg = STRINGS["SAVED"]
            else:
                msg = STRINGS["NO_TEXT_RECORDED"]
            
            session_attr["is_recording"] = False
            session_attr["recording_text"] = ""
            
            speech_text = f"{msg} {STRINGS['WHAT_TO_DO_NEXT']}"
            return handler_input.response_builder.speak(speech_text).ask(STRINGS["WRITE_OR_CLOSE"]).response
        else:
            speech_text = STRINGS["NOT_RECORDING_WHAT_NEXT"]
            return handler_input.response_builder.speak(speech_text).ask(STRINGS["WRITE_OR_CLOSE"]).response

class ChiudiIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("ChiudiIntent")(handler_input)

    def handle(self, handler_input):
        speech_text = STRINGS["GOODBYE"]
        return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response

class InviaIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("InviaIntent")(handler_input)

    def handle(self, handler_input):
        try:
            # Check permissions explicitly
            perms = handler_input.request_envelope.context.system.user.permissions
            if not perms or not perms.consent_token:
                logger.info("No permissions found in request context")
                return (
                    handler_input.response_builder
                        .speak(STRINGS["EMAIL_PERMISSION_NEEDED"])
                        .set_card(AskForPermissionsConsentCard(permissions=["alexa::profile:email:read"]))
                        .response
                )

            user_id = handler_input.request_envelope.session.user.user_id
            notes = db.get_all_notes(user_id)
            
            if not notes:
                speech_text = STRINGS["NO_NOTES_TO_SEND"]
                return handler_input.response_builder.speak(speech_text).response

            # Format notes
            date_format = os.getenv("DATE_FORMAT", "%d/%m/%Y %H:%M")
            email_body = ""
            for i, (content, timestamp) in enumerate(notes, 1):
                try:
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    formatted_date = dt.strftime(date_format)
                except ValueError:
                    formatted_date = timestamp 

                email_body += f"{i} - {formatted_date} - {content}\n"

            # Send email
            smtp_server = os.getenv("EMAIL_SMTP_SERVER")
            smtp_port = int(os.getenv("EMAIL_SMTP_PORT", 587))
            sender_email = os.getenv("EMAIL_SENDER") or "alexa@local.test"
            password = os.getenv("EMAIL_PASSWORD") or None
            
            # Get user email from profile
            svc_client_fact = handler_input.service_client_factory
            ups_service = svc_client_fact.get_ups_service()
            
            try:
                recipient = ups_service.get_profile_email()
            except (SerializationException, ServiceException) as e:
                error_str = str(e)
                if "ACCESS_DENIED" in error_str or isinstance(e, ServiceException):
                     logger.info(f"Permission missing or access denied: {e}")
                     return (
                        handler_input.response_builder
                            .speak(STRINGS["EMAIL_PERMISSION_NEEDED"])
                            .set_card(AskForPermissionsConsentCard(permissions=["alexa::profile:email:read"]))
                            .response
                     )
                else:
                    logger.error(f"Error fetching email: {e}", exc_info=True)
                    raise e

            if not recipient:
                return (
                    handler_input.response_builder
                        .speak(STRINGS["EMAIL_NOT_FOUND"])
                        .response
                )



            # recipient = None
            # try:
            #     if not handler_input.service_client_factory:
            #         logger.info("Service client factory is None. Requesting permissions.")
            #         recipient = None
            #     else:
            #         client = handler_input.service_client_factory.get_ups_service()
            #         recipient = client.get_profile_email()
            # except Exception as e:
            #     error_str = str(e)
            #     if "'ACCESS_DENIED' is not a valid ErrorCode" in error_str or "ACCESS_DENIED" in error_str:
            #         logger.info("Profile email access denied (permissions missing).")
            #     else:
            #         logger.error(f"Error getting profile email: {e}", exc_info=True)
            #     recipient = None

            # if not recipient:
            #     logger.info("Recipient is None. Sending AskForPermissionsConsentCard.")
            #     speech_text = STRINGS["EMAIL_PERMISSION_NEEDED"]
            #     permissions = ["alexa::profile:email:read"]
            #     try:
            #         return handler_input.response_builder.speak(speech_text).set_card(
            #             AskForPermissionsConsentCard(permissions=permissions)
            #         ).response
            #     except Exception as e:
            #         logger.error(f"Error creating permission card response: {e}", exc_info=True)
            #         return handler_input.response_builder.speak(STRINGS["EMAIL_ERROR"]).response

            try:
                msg = EmailMessage()
                msg.set_content(email_body)
                msg["Subject"] = "Le tue note di Alexa"
                msg["From"] = sender_email
                msg["To"] = recipient
                
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    if os.getenv("EMAIL_USE_TLS", "True").lower() == "true":
                        server.starttls()
                    
                    if os.getenv("EMAIL_USE_AUTH", "True").lower() == "true":
                        server.login(sender_email, password)
                    
                    server.send_message(msg)
                
                speech_text = STRINGS["EMAIL_SENT"]
            except Exception as e:
                logger.error(f"Error sending email: {e}", exc_info=True)
                speech_text = STRINGS["EMAIL_ERROR"]

            return handler_input.response_builder.speak(speech_text).response
        except Exception as e:
            logger.error(f"Critical error in InviaIntentHandler: {e}", exc_info=True)
            return handler_input.response_builder.speak(STRINGS["EMAIL_ERROR"]).response

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speech_text = STRINGS["HELP_MESSAGE"]
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speech_text = STRINGS["GOODBYE"]
        return handler_input.response_builder.speak(speech_text).set_should_end_session(True).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        logger.info(f"Session ended reason: {handler_input.request_envelope.request.reason}")
        if handler_input.request_envelope.request.error:
            logger.info(f"Session ended error: {handler_input.request_envelope.request.error}")
        return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        speech_text = STRINGS["ERROR_MESSAGE"]
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

# --- Register Handlers ---
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(ScriviIntentHandler())
sb.add_request_handler(DictationIntentHandler())
sb.add_request_handler(FinishIntentHandler())
sb.add_request_handler(InviaIntentHandler())
sb.add_request_handler(ChiudiIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

skill = sb.create()

@app.route("/", methods=['POST'])
def invoke_skill():
    payload = request.data
    request_envelope = skill.serializer.deserialize(payload=payload, obj_type=RequestEnvelope)
    response_envelope = skill.invoke(request_envelope=request_envelope, context=None)
    response_json = skill.serializer.serialize(response_envelope)
    logger.info(f"Response JSON: {json.dumps(response_json)}")
    return jsonify(response_json)

if __name__ == '__main__':
    db.init_db()
    app.run(debug=True)

