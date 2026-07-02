import http.server
import socketserver
import json
import urllib.request
import urllib.parse
import re
import random

PORT = 8080

HTML = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Search Chatbot</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        
        .chat-container {
            background: #2d2d2d;
            border-radius: 10px;
            width: 100%;
            max-width: 700px;
            height: 85vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .chat-header {
            background: #404040;
            color: #00ff88;
            padding: 15px;
            border-radius: 10px 10px 0 0;
            font-size: 18px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .status {
            font-size: 12px;
            color: #888;
            font-weight: normal;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .message {
            max-width: 80%;
            padding: 10px 15px;
            border-radius: 18px;
            word-wrap: break-word;
            animation: fadeIn 0.3s;
            line-height: 1.4;
        }
        
        .user-message {
            background: #0084ff;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 5px;
        }
        
        .bot-message {
            background: #404040;
            color: #e0e0e0;
            align-self: flex-start;
            border-bottom-left-radius: 5px;
        }
        
        .source-info {
            font-size: 11px;
            color: #888;
            margin-top: 5px;
            font-style: italic;
        }
        
        .chat-input {
            display: flex;
            padding: 15px;
            background: #363636;
            border-radius: 0 0 10px 10px;
            gap: 10px;
        }
        
        .chat-input input {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 5px;
            background: #4a4a4a;
            color: white;
            font-size: 14px;
            outline: none;
        }
        
        .chat-input button {
            padding: 10px 20px;
            background: #0084ff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }
        
        .chat-input button:hover {
            background: #0066cc;
        }
        
        .typing-indicator {
            display: none;
            padding: 10px 15px;
            background: #404040;
            border-radius: 18px;
            align-self: flex-start;
            color: #888;
            font-size: 13px;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .chat-messages::-webkit-scrollbar {
            width: 6px;
        }
        
        .chat-messages::-webkit-scrollbar-track {
            background: #2d2d2d;
        }
        
        .chat-messages::-webkit-scrollbar-thumb {
            background: #555;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            Web Search Bot
            <span class="status" id="status">Bereit</span>
        </div>
        <div class="chat-messages" id="messages">
            <div class="message bot-message">
                Hallo! Ich durchsuche mehrere Quellen im Web nach Antworten. Was mochtest du wissen?
            </div>
        </div>
        <div class="typing-indicator" id="typing">
            Suche im Web...
        </div>
        <div class="chat-input">
            <input type="text" id="userInput" placeholder="Frag mich etwas..." onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()">Senden</button>
        </div>
    </div>

    <script>
        function addMessage(text, isUser, source) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + (isUser ? 'user-message' : 'bot-message');
            
            if (source && !isUser) {
                messageDiv.innerHTML = text + '<div class="source-info">Quelle: ' + source + '</div>';
            } else {
                messageDiv.textContent = text;
            }
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const query = input.value.trim();
            
            if (!query) return;
            
            addMessage(query, true);
            input.value = '';
            
            const typingDiv = document.getElementById('typing');
            const statusDiv = document.getElementById('status');
            typingDiv.style.display = 'block';
            statusDiv.textContent = 'Suche...';
            
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: query })
                });
                
                const data = await response.json();
                typingDiv.style.display = 'none';
                statusDiv.textContent = 'Bereit';
                addMessage(data.answer, false, data.source);
                
            } catch (error) {
                typingDiv.style.display = 'none';
                statusDiv.textContent = 'Fehler';
                addMessage('Verbindungsfehler. Bitte versuche es erneut.', false);
            }
        }
    </script>
</body>
</html>"""

class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(HTML.encode('utf-8'))
    
    def do_POST(self):
        if self.path == '/search':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            query = data.get('query', '')
            answer, source = self.search_multiple_sources(query)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({'answer': answer, 'source': source})
            self.wfile.write(response.encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def search_duckduckgo(self, query):
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                answer = data.get('AbstractText', '')
                if answer:
                    source_url = data.get('AbstractURL', 'DuckDuckGo')
                    return answer[:500], source_url
                
                related = data.get('RelatedTopics', [])
                if related:
                    text = related[0].get('Text', '')
                    clean_text = re.sub(r'<[^>]+>', '', text)[:500]
                    if clean_text:
                        return clean_text, "DuckDuckGo"
                
                return None, None
                
        except Exception as e:
            print(f"DuckDuckGo Fehler: {e}")
            return None, None
    
    def search_wikipedia(self, query):
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://de.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&format=json&srlimit=3"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                search_results = data.get('query', {}).get('search', [])
                if search_results:
                    snippet = search_results[0].get('snippet', '')
                    clean_snippet = re.sub(r'<[^>]+>', '', snippet)
                    title = search_results[0].get('title', '')
                    source = f"Wikipedia: {title}"
                    return clean_snippet[:500], source
                
                return None, None
                
        except Exception as e:
            print(f"Wikipedia Fehler: {e}")
            return None, None
    
    def search_brave(self, query):
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://search.brave.com/api/suggest?q={encoded_query}"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            })
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                results = data.get('results', [])
                if results:
                    description = results[0].get('description', '')
                    if description:
                        return description[:500], "Brave Search"
                
                return None, None
                
        except Exception as e:
            print(f"Brave Fehler: {e}")
            return None, None
    
    def search_mozilla(self, query):
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://developer.mozilla.org/api/v1/search?q={encoded_query}&locale=de"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                documents = data.get('documents', [])
                if documents:
                    summary = documents[0].get('summary', '')
                    title = documents[0].get('title', '')
                    if summary:
                        clean_summary = re.sub(r'<[^>]+>', '', summary)
                        return clean_summary[:500], f"MDN: {title}"
                
                return None, None
                
        except Exception as e:
            print(f"Mozilla Fehler: {e}")
            return None, None
    
    def search_github(self, query):
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.github.com/search/repositories?q={encoded_query}&per_page=1"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/vnd.github.v3+json'
            })
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                items = data.get('items', [])
                if items:
                    repo = items[0]
                    description = repo.get('description', '')
                    name = repo.get('full_name', '')
                    if description:
                        return f"{description}. Repository: {name}", f"GitHub: {name}"
                
                return None, None
                
        except Exception as e:
            print(f"GitHub Fehler: {e}")
            return None, None
    
    def search_stackoverflow(self, query):
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance&q={encoded_query}&site=stackoverflow&pagesize=1"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                items = data.get('items', [])
                if items:
                    title = items[0].get('title', '')
                    if title:
                        return f"Stack Overflow Frage: {title}", "Stack Overflow"
                
                return None, None
                
        except Exception as e:
            print(f"StackOverflow Fehler: {e}")
            return None, None
    
    def search_multiple_sources(self, query):
        sources = [
            ("Wikipedia", self.search_wikipedia),
            ("DuckDuckGo", self.search_duckduckgo),
            ("Mozilla Developer", self.search_mozilla),
            ("Brave Search", self.search_brave),
        ]
        
        random.shuffle(sources)
        
        results = []
        
        for source_name, search_func in sources:
            print(f"Suche auf {source_name}...")
            answer, source = search_func(query)
            if answer and len(answer.strip()) > 20:
                results.append((answer, source, source_name))
                print(f"Erfolg auf {source_name}!")
        
        if results:
            best_result = max(results, key=lambda x: len(x[0]))
            return best_result[0], best_result[1]
        
        return "Leider konnte ich in keiner Quelle Informationen zu deiner Frage finden. Bitte versuche es mit einer anderen Formulierung.", "Keine Quelle"

print(f"Server startet auf Port {PORT}")
print(f"Offne http://localhost:{PORT}")
print("Durchsucht DuckDuckGo, Mozilla und Brave Search")

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    httpd.serve_forever()
