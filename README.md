# flask_cloudflared

![PyPI - Downloads](https://img.shields.io/pypi/dm/flask-cloudflared)

Start a [TryCloudflare](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/trycloudflare) tunnel to your flask app right from code.  
This requires at least `Python 3.6`

### Users on Apple Silicon
Because [cloudflared](https://github.com/cloudflare/cloudflared) doesn't support Darwin arm64 natively yet, Rosetta 2 is used to create a compatibility layer. If you don't have Rosetta 2 installed yet, please check [Apple's support page](https://support.apple.com/en-us/HT211861).

## Acknowledgements

This project is based on [flask-ngrok](https://github.com/gstaff/flask-ngrok).
