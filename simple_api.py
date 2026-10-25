#!/usr/bin/env python3
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sqlite3
import uuid
from datetime import datetime

class SmartAssistHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self._set_headers()
            response = {"message": "SmartAssist API is running", "version": "1.0.0"}
            self.wfile.write(json.dumps(response).encode())
        elif path == '/health':
            self._set_headers()
            response = {"status": "healthy"}
            self.wfile.write(json.dumps(response).encode())
        elif path == '/reminders':
            conn = sqlite3.connect('smartassist.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reminders ORDER BY date, time")
            reminders = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self._set_headers()
            self.wfile.write(json.dumps(reminders).encode())
        elif path == '/chat/history':
            conn = sqlite3.connect('smartassist.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chat_history ORDER BY created_at DESC LIMIT 10")
            history = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self._set_headers()
            self.wfile.write(json.dumps(history).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            data = {}
        
        if path == '/reminders':
            conn = sqlite3.connect('smartassist.db')
            cursor = conn.cursor()
            reminder_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO reminders (id, title, description, date, time) VALUES (?, ?, ?, ?, ?)",
                (reminder_id, data.get('title', ''), data.get('description', ''), data.get('date', ''), data.get('time', ''))
            )
            conn.commit()
            conn.close()
            self._set_headers(201)
            self.wfile.write(json.dumps({"id": reminder_id, "message": "Reminder created successfully"}).encode())
        elif path == '/simplify':
            text = data.get('text', '')
            language = data.get('language', 'en')
            action = data.get('action', 'simplify')
            
            if language == 'ta':
                if action == 'simplify':
                    result = "இந்த ஆவணம் எளிமையான மொழியில் விளக்கப்பட்டுள்ளது:\n\nமுக்கியமான தகவல்கள் மற்றும் தேவையான நடவடிக்கைகள் எளிமையாக வழங்கப்பட்டுள்ளன. சிக்கலான சொற்கள் எளிமையாக்கப்பட்டுள்ளன."
                elif action == 'summarize':
                    result = "சுருக்கம்:\n- முக்கிய புள்ளி 1: ஆவணத்தின் முக்கிய நோக்கம்\n- முக்கிய புள்ளி 2: தேவையான தேவைகள்\n- முக்கிய புள்ளி 3: செய்ய வேண்டிய நடவடிக்கைகள்"
                else:
                    result = "நிலுவை தேதிகள் மற்றும் தேவையான ஆவணங்கள்:\n- நிலுவை தேதி: XX/XX/XXXX\n- தேவைப்படும் ஆவணங்கள்: அடையாள அட்டை, முகவரி சான்று\n- நடவடிக்கை: விண்ணப்பத்தை பூர்த்தி செய்து சமர்ப்பிக்கவும்"
            else:
                if action == 'simplify':
                    result = "This document has been simplified in plain language:\n\nThe key information has been explained clearly. Complex terms have been broken down into easier words. All important details from your document are presented here."
                elif action == 'summarize':
                    result = "Summary:\n- Key Point 1: Main purpose of the document\n- Key Point 2: Important requirements\n- Key Point 3: Actions you need to take"
                else:
                    result = "Deadlines and Required Documents:\n- Deadline: XX/XX/XXXX\n- Required Documents: ID proof, Address proof, Application form\n- Action Items: Complete form and submit with documents"
            
            self._set_headers()
            self.wfile.write(json.dumps({"result": result, "action": action, "language": language}).encode())
        elif path == '/chat':
            message = data.get('message', '')
            language = data.get('language', 'en')
            
            if language == 'ta':
                responses = [
                    "வணக்கம்! நான் SmartAssist உதவியாளர். நான் உங்களுக்கு எப்படி உதவ முடியும்?",
                    "நிச்சயமாக உதவுகிறேன். உங்கள் கேள்வியை மேலும் விளக்க முடியுமா?",
                    "இந்த விஷயத்தில் நான் உங்களுக்கு உதவலாம். மேலும் விவரங்களை சொல்லுங்கள்.",
                    "உங்கள் தேவையை புரிந்துகொண்டேன். நான் இதற்கான தீர்வை கண்டறிய உதவுகிறேன்."
                ]
                response = responses[hash(message) % len(responses)]
            else:
                responses = [
                    "Hello! I'm SmartAssist. How can I help you today?",
                    "I'd be happy to help. Could you tell me more details?",
                    "I can assist you with that. Let me explain it simply.",
                    "I understand your question. Here's what I can tell you..."
                ]
                response = responses[hash(message) % len(responses)]
            
            conn = sqlite3.connect('smartassist.db')
            cursor = conn.cursor()
            chat_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO chat_history (id, message, response, language) VALUES (?, ?, ?, ?)",
                (chat_id, message, response, language)
            )
            conn.commit()
            conn.close()
            
            self._set_headers()
            self.wfile.write(json.dumps({"response": response, "language": language}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path.startswith('/reminders/'):
            reminder_id = path.split('/')[-1]
            conn = sqlite3.connect('smartassist.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            conn.commit()
            conn.close()
            self._set_headers()
            self.wfile.write(json.dumps({"message": "Reminder deleted successfully"}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

def init_db():
    conn = sqlite3.connect('smartassist.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id TEXT PRIMARY KEY,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized")

if __name__ == '__main__':
    os.chdir('/Users/mtahalishyam/Documents/Default Project/backend')
    init_db()
    server = HTTPServer(('127.0.0.1', 8000), SmartAssistHandler)
    print('SmartAssist API server running on http://127.0.0.1:8000')
    server.serve_forever()
