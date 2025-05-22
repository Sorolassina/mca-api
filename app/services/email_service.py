import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
import traceback

class EmailService:
    def __init__(self):
        print("\n🚀 Initialisation du service EmailService")
        try:
            # Affichage des paramètres SMTP depuis settings
            print("\n📋 Paramètres SMTP depuis settings:")
            print(f"  - SMTP_SERVER: {settings.SMTP_SERVER}")
            print(f"  - SMTP_PORT: {settings.SMTP_PORT}")
            print(f"  - SMTP_TLS: {settings.SMTP_TLS}")
            print(f"  - EMAIL_SENDER: {settings.EMAIL_SENDER}")
            print(f"  - EMAIL_PASSWORD: {'✅ Configuré' if settings.EMAIL_PASSWORD else '❌ Non configuré'}")
            
            self.smtp_server = settings.SMTP_SERVER
            self.smtp_port = settings.SMTP_PORT
            self.smtp_username = settings.EMAIL_SENDER
            self.smtp_password = settings.EMAIL_PASSWORD
            self.sender_email = settings.EMAIL_SENDER
            
            if not self.smtp_password:
                raise ValueError("❌ EMAIL_PASSWORD n'est pas configuré dans les paramètres")
            
            print("\n📧 Configuration SMTP finale:")
            print(f"  - Serveur: {self.smtp_server}")
            print(f"  - Port: {self.smtp_port}")
            print(f"  - Expéditeur: {self.sender_email}")
            print(f"  - Mot de passe configuré: {'✅' if self.smtp_password else '❌'}")
        except Exception as e:
            print(f"\n❌ Erreur lors de l'initialisation du service email: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            raise

    async def send_signature_link(self, to_email: str, signature_url: str, evenement_titre: str) -> bool:
        """
        Envoie un email contenant le lien de signature pour un émargement
        
        Args:
            to_email (str): L'adresse email du destinataire
            signature_url (str): L'URL de signature générée
            evenement_titre (str): Le titre de l'événement
            
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        print(f"\n=== 📧 DÉBUT ENVOI EMAIL DE SIGNATURE ===")
        print(f"📨 Destinataire: {to_email}")
        print(f"🔗 URL de signature: {signature_url}")
        print(f"📝 Événement: {evenement_titre}")
        
        try:
            # Création du message
            print("\n📝 Création du message...")
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = f"Lien de signature pour l'événement : {evenement_titre}"

            # Corps du message en HTML
            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c3e50;">Signature d'émargement</h2>
                        <p>Bonjour,</p>
                        <p>Vous avez été invité à signer l'émargement pour l'événement : <strong>{evenement_titre}</strong></p>
                        <p>Pour signer, veuillez cliquer sur le lien ci-dessous :</p>
                        <div style="margin: 30px 0;">
                            <a href="{signature_url}" 
                               style="background-color: #3498db; 
                                      color: white; 
                                      padding: 12px 24px; 
                                      text-decoration: none; 
                                      border-radius: 4px;
                                      display: inline-block;">
                                Signer l'émargement
                            </a>
                        </div>
                        <p style="color: #7f8c8d; font-size: 0.9em;">
                            Ce lien est valable pendant 30 minutes. 
                            Si vous ne pouvez pas cliquer sur le bouton, 
                            copiez et collez ce lien dans votre navigateur :<br>
                            <span style="color: #34495e;">{signature_url}</span>
                        </p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                        <p style="color: #7f8c8d; font-size: 0.8em;">
                            Cet email a été envoyé automatiquement, merci de ne pas y répondre.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            print("✅ Message créé avec succès")

            # Connexion au serveur SMTP
            print(f"\n🔌 Connexion au serveur SMTP {self.smtp_server}:{self.smtp_port}...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                print("✅ Connexion établie")
                
                print("\n🔐 Activation de TLS...")
                server.starttls()
                print("✅ TLS activé")
                
                print("\n🔑 Authentification...")
                server.login(self.smtp_username, self.smtp_password)
                print("✅ Authentification réussie")
                
                # Envoi de l'email
                print("\n📤 Envoi de l'email...")
                server.send_message(msg)
                print("✅ Email envoyé avec succès")
                
            print("\n=== FIN ENVOI EMAIL DE SIGNATURE ===\n")
            return True

        except smtplib.SMTPAuthenticationError as e:
            print(f"\n❌ Erreur d'authentification SMTP: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            return False
        except smtplib.SMTPException as e:
            print(f"\n❌ Erreur SMTP: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            return False
        except Exception as e:
            print(f"\n❌ Erreur inattendue lors de l'envoi de l'email: {str(e)}")
            print(f"📋 Traceback:\n{traceback.format_exc()}")
            return False 