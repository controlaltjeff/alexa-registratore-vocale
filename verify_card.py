from ask_sdk_model.ui import AskForPermissionsConsentCard
import json

try:
    card = AskForPermissionsConsentCard(permissions=["alexa::profile:email:read"])
    print("Card created successfully")
    print(card)
except Exception as e:
    print(f"Error creating card: {e}")
