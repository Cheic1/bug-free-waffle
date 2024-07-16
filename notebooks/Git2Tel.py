import os
import requests
import time
import telebot
from github import Github
import re

# Configurazione
REPO_OWNER = "Cheic1"
REPO_NAME = "RL"
FILE_PERCORSI = "Test.txt"
FIRMWARE_PREFIX = "firmware_"
FIRMWARE_SUFFIX = ".bin"
FOLDER_PATH = "Irrigatore/FW"
TOKEN_BOT = "7422920725:AAG9RiNmdzPwYlXkMtKuv5j7FQx8aOY-jXs"
CHAT_ID = "217950359"
GITHUB_TOKEN = "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"
CHECK_INTERVAL = 60  # Intervallo di controllo in secondi

bot = telebot.TeleBot(TOKEN_BOT)
g = Github(GITHUB_TOKEN)

def salva_percorso(sha):
    with open(FILE_PERCORSI, "w") as file:
        file.write(sha)

def leggi_ultimo_sha():
    if os.path.exists(FILE_PERCORSI):
        with open(FILE_PERCORSI, "r") as file:
            return file.read().strip()
    return ""

def parse_version(filename):
    match = re.search(r'firmware_(\d+)\.(\d+)\.(\d+)\.bin', filename)
    if match:
        return tuple(map(int, match.groups()))
    return (0, 0, 0)

def invia_file_telegram(file_content):
    try:
        current_sha = file_content.sha
        url = file_content.download_url
        response = requests.get(url)
        if response.status_code == 200:
            with open(file_content.name, 'wb') as file:
                file.write(response.content)
            with open(file_content.name, 'rb') as file:
                bot.send_document(CHAT_ID, file)
            os.remove(file_content.name)  # Rimuove il file temporaneo
            print(f"File inviato con successo: {file_content.name}")
            salva_percorso(current_sha)
        else:
            print(f"Errore nel download del file: {response.status_code}")
    except Exception as e:
        print(f"Errore nell'invio del file: {e}")

def controlla_firmware():
    repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
    try:
        contents = repo.get_contents(FOLDER_PATH)
        firmware_files = [content for content in contents if content.name.startswith(FIRMWARE_PREFIX) and content.name.endswith(FIRMWARE_SUFFIX)]
        
        if not firmware_files:
            print(f"Nessun file firmware trovato nella cartella {FOLDER_PATH}.")
            return

        latest_firmware = max(firmware_files, key=lambda x: parse_version(x.name))
        current_sha = latest_firmware.sha
        last_sha = leggi_ultimo_sha()

        if current_sha != last_sha:
            print(f"Nuova versione del firmware rilevata: {latest_firmware.name}")
            invia_file_telegram(latest_firmware)
        else:
            print(f"Nessuna modifica al firmware più recente: {latest_firmware.name}")

    except Exception as e:
        print(f"Errore nel controllo del file: {e}")

def main():
    ultimo_controllo = 0
    
    while True:
        try:
            if time.time() - ultimo_controllo >= CHECK_INTERVAL:
                print("Controllo del firmware...")
                controlla_firmware()
                ultimo_controllo = time.time()
            time.sleep(1)  # Breve pausa per evitare un utilizzo eccessivo della CPU
        except Exception as e:
            print(f"Si è verificato un errore: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()