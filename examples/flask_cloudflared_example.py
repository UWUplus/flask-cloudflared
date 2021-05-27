from flask import Flask
from flask_cloudflared import run_with_cloudflared

app = Flask(__name__)
run_with_cloudflared(app)  # Open a Cloudflare Tunnel when app is run

@app.route("/")
def home(): 
    return "Hello World!" # Serve Hello World

if __name__ == '__main__':
    app.run()