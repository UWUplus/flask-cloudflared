from flask import Flask
from flask_cloudflared import run_with_cloudflared

app = Flask(__name__)
run_with_cloudflared(app)  # Open a Cloudflare Tunnel when app is run

@app.route("/")
def home(): 
    return "Hello World!" # Serve Hello World

if __name__ == '__main__':
    # app.run(port=1337, metrics_port=1338) # Run the app on port 1337 and metrics on port 1338
    app.run()