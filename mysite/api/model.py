from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UserState(db.Model):
    wa_id = db.Column(db.String, primary_key=True)
    state = db.Column(db.String)
    voice_translate = db.Column(db.Boolean)
    translate = db.Column(db.Boolean)
    awaiting_language = db.Column(db.Boolean)
    awaiting_translation_text = db.Column(db.Boolean)
    send_to_someone = db.Column(db.Boolean)
    language = db.Column(db.String)
    awaiting_number = db.Column(db.Boolean)
    message_body = db.Column(db.String)
    recipient_number = db.Column(db.String)
