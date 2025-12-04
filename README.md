# Alexa Voice Memo App

This is a local Alexa Skill application that records dictated text into a local SQLite database.

## Prerequisites
- Python 3.8+
- [ngrok](https://ngrok.com/) (for local tunneling)
- Amazon Developer Account (for Alexa Console)

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Initialize Database**:
    The database will be automatically initialized on the first run of `app.py`.

3.  **Run the Application**:
    ```bash
    python app.py
    ```
    The app will run on `http://127.0.0.1:5000`.

4.  **Expose to Internet**:
    Open a new terminal and run:
    ```bash
    ngrok http 5000
    ```
    Copy the HTTPS URL (e.g., `https://<random-id>.ngrok.io`).

## Alexa Developer Console Configuration

1.  Go to [developer.amazon.com/alexa/console/ask](https://developer.amazon.com/alexa/console/ask).
2.  **Create Skill**:
    -   Name: "Voice Memo" (or your choice).
    -   Locale: Italian (IT).
    -   Model: Custom.
    -   Hosting: Provision your own.
3.  **Interaction Model**:
    -   Go to **JSON Editor**.
    -   Copy content from `interaction_model.json` and paste it there.
    -   Click **Save Model** and **Build Model**.
4.  **Endpoint**:
    -   Go to **Endpoint**.
    -   Select **HTTPS**.
    -   Paste your ngrok HTTPS URL into "Default Region".
    -   Select "My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority".
    -   Click **Save Endpoints**.

## Testing

1.  Go to the **Test** tab in the Alexa Console.
2.  Enable "Development" testing.
3.  Type or say: "apri voice memo".
4.  Follow the prompts: "scrivi", "finish", "chiudi".
