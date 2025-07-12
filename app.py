from flask import Flask, render_template, request
from openai import OpenAI
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# Načti .env proměnné
load_dotenv()

# Načti OpenAI API klíč bezpečně
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Načti Google Credentials
SCOPES = ["https://www.googleapis.com/auth/calendar"]
import json
from google.oauth2 import service_account
import os

credentials_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = service_account.Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
calendar_service = build("calendar", "v3", credentials=creds)
calendar_id = "primary"  # nebo konkrétní ID kalendáře

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        text = request.form["text"]
        today = datetime.now().strftime("%Y-%m-%d")

        system_message = {
            "role": "system",
            "content": (
                f"Dnešní datum je {today}. Převeď následující českou větu na JSON s formátem: "
                "{\"summary\": \"název\", \"start\": \"YYYY-MM-DD HH:MM\", \"end\": \"YYYY-MM-DD HH:MM\"}. "
                "Nepřidávej komentář, jen čistý JSON. Vycházej z uvedeného data."
            )
        }

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[system_message, {"role": "user", "content": text}]
            )

            json_text = response.choices[0].message.content.strip("```json").strip("```").strip()
            event_data = json.loads(json_text)

            start_iso = datetime.strptime(event_data["start"], "%Y-%m-%d %H:%M").isoformat()
            end_iso = datetime.strptime(event_data["end"], "%Y-%m-%d %H:%M").isoformat()

            event = {
                "summary": event_data["summary"],
                "start": {"dateTime": start_iso, "timeZone": "Europe/Prague"},
                "end": {"dateTime": end_iso, "timeZone": "Europe/Prague"},
            }

            created_event = calendar_service.events().insert(calendarId=calendar_id, body=event).execute()
            result = {"success": True, "url": created_event.get("htmlLink")}

        except Exception as e:
            result = {"success": False, "message": str(e)}

    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
