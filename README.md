# flask-cloudflared

![PyPI - Downloads](https://img.shields.io/pypi/dm/flask-cloudflared) [![Run it button](https://img.shields.io/badge/-Run%20it%20now-brightgreen.svg?longCache=true&style=flat&logo=data:image/png;base64,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)](https://colab.research.google.com/github/UWUplus/flask-cloudflared/blob/main/examples/flask_cloudflared_example.ipynb)

Start a [TryCloudflare](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/trycloudflare) tunnel to your flask app right from code.  
This requires at least `Python 3.6`

## Behavior
The Flask app will run on port 5000 by default and start the Cloudflared metrics page on a random port between 8100 and 9000.  
This can be changed by passing the `port` and `metrics_port` arguments to the `app.run()` function after using the `run_with_cloudflared` decorator.

### Custom tunnel domain
By default, the tunnel will be created with a random subdomain of `trycloudflare.com`.  
To use custom domains, follow [this tutorial by Cloudflare](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/local/) and pass either the `tunnel_id` or `config_path` arguments to the `app.run()` function after using the `run_with_cloudflared` decorator. For an example check out [examples/flask_cloudflared_example.py](https://github.com/UWUplus/flask-cloudflared/blob/main/examples/flask_cloudflared_example.py#L13-L14).

### Users on Apple Silicon
Because [cloudflared](https://github.com/cloudflare/cloudflared) doesn't support Darwin arm64 natively yet, Rosetta 2 is used to create a compatibility layer. If you don't have Rosetta 2 installed yet, please check [Apple's support page](https://support.apple.com/en-us/HT211861).

## Acknowledgements

This project is based on [flask-ngrok](https://github.com/gstaff/flask-ngrok).
