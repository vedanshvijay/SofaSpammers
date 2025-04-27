# Office IP Messenger

A secure, real-time messaging application for office environments.

## Tech Stack

- **Frontend**: Flet (>=0.10.0)
- **Backend**: FastAPI + Uvicorn
- **Security**: Cryptography (>=40.0.0), Argon2-cffi (>=23.1.0)
- **Media**: Pillow (>=9.5.0), Playsound (>=1.3.0)
- **Networking**: HTTPX, WebSockets
- **Storage**: JSON-based file system
- **Environment**: Python 3.x

## Features

- Real-time messaging
- File sharing
- Audio notifications
- End-to-end encryption
- Dark/light theme support
- User authentication

## Installation

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Security

- Password hashing with Argon2
- End-to-end encryption
- Secure file handling
- Environment variable protection

## License

MIT License - See LICENSE file for details

## Support

For support, please open an issue in the GitHub repository (and hope someone actually reads it).

---

*Disclaimer: This app is not responsible for any lost productivity, awkward office moments, or your boss finding out about your secret meme channel. Use at your own risk.* 