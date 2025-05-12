import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List

class ActionOllamaChat(Action):
    def name(self) -> Text:
        return "action_ollama_chat"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_message = tracker.latest_message.get("text")

        try:
            response = requests.post(
                "http://ollama:11434/api/generate",
                json={"model": "llama3", "prompt": user_message, "stream": False},
                timeout=60
            )
            if response.status_code == 200:
                result = response.json().get("response", "Lo siento, no pude entender.")
            else:
                result = "Hubo un error al comunicarse con el modelo."
        except requests.exceptions.RequestException as e:
            result = f"Error de conexión con Ollama: {e}"

        dispatcher.utter_message(text=result)
        return []