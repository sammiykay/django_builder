# Social Sphere 🌐

A modern social media platform built with Django that enables users to connect, share, and engage through rich media content and real-time interactions.

![Social Sphere Demo](docs/images/demo.png)

## ✨ Features

- **User Profiles**
  - Customizable avatars and bio
  - Activity timeline
  - Following system

- **Rich Content Sharing**
  - Text, image, and video support
  - Image filters and cropping
  - Rich text editor
  - Hashtag support
  - User mentions (@username)

- **Engagement**
  - Interactive likes with animations
  - Nested comment threads
  - Post sharing
  - Bookmarks
  - Real-time notifications

- **Discovery**
  - Personalized news feed
  - Infinite scroll
  - Advanced search functionality
  - Trending hashtags

- **Management**
  - Content moderation tools
  - User reporting system
  - Admin dashboard

## 🚀 Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Redis
- Node.js & npm
- Cloudinary account
- Elasticsearch (optional)

## 📦 Installation

1. Clone the repository
git clone https://github.com/yourusername/social_sphere.git
cd social_sphere

2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

3. Install dependencies
pip install -r requirements.txt
npm install

4. Configure environment variables
cp .env.example .env
# Edit .env with your configuration

5. Set up database
python manage.py migrate

6. Compile Tailwind CSS
npm run build

7. Start required services
# Start Redis server
redis-server

# Start Celery worker
celery -A social_sphere worker -l info

8. Run development server
python manage.py runserver

## 💻 Usage

Visit `http://localhost:8000` to access the platform.

### Key Actions

- Create account/Login
- Set up profile
- Create posts
- Follow users
- Engage with content
- Manage notifications
- Search content

## 🔌 API Documentation

API documentation is available at `/api/docs/` when running the server.

Key endpoints:
- `/api/posts/`
- `/api/users/`
- `/api/comments/`
- `/api/notifications/`

Full API documentation: [API.md](docs/API.md)

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/yourusername/social_sphere/issues)
- Email: support@socialsphere.com
- Discord: [Join our community](https://discord.gg/socialsphere)

## 🙏 Acknowledgments

- Django community
- All contributors
- Open source packages used in this project

---

Made with ❤️ by [Your Name]

[⬆ Back to top](#social-sphere-)