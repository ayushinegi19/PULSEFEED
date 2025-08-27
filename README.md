PulseFeed 📰✨

A personalized news aggregator web application that delivers news based on user interests, categories, and preferences. Built with Flask, NewsAPI integration, and a clean, user-friendly interface.

🚀 Features

User registration & login

Personalized feed based on categories, sources, and countries

Breaking News, For You, and Categories sections

Save articles to read later (bookmark feature)

Share news articles

Trending section with carousels for smooth navigation

🛠️ Tech Stack

Backend: Flask (Python)

Frontend: HTML, CSS, JavaScript

Database: SQLite (can be swapped with PostgreSQL/MySQL)

APIs: NewsAPI (for live news data)

📂 Project Structure
PulseFeed/
│── app.py                # Main Flask app  
│── static/               # CSS, JS, images  
│── templates/            # HTML templates  
│── instance/             # database
│── README.md             # Documentation  

⚙️ Installation & Setup

Create a virtual environment:

python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows


Install dependencies:

pip install -r requirements.txt


Set up your environment variables (create a .env file):

NEWS_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key

Run the app:
flask run
