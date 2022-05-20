import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="flask_cloudflared",
    version="0.0.9",
    author="Ralf Rademacher",
    description="Start a TryCloudflare Tunnel from your flask app.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/UWUplus/flask-cloudflared",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    keywords='flask cloudflared',
    install_requires=['Flask>=0.8', 'requests'],
    py_modules=['flask_cloudflared']
)