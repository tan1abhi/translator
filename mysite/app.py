from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['GET', 'POST'])
def handle_webhook():
    if request.method == 'GET':
        # Handle the GET request challenge verification
        challenge = request.args.get('hub.challenge')
        return challenge if challenge else 'No challenge found'
    
    elif request.method == 'POST':
        # Handle the actual webhook data
        data = request.json
        if 'challenge' in data:
            challenge = data['challenge']
            return jsonify({"challenge": challenge})
        
        # Your logic for processing WhatsApp messages or other events
        return 'OK'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
