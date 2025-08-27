from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from newsapi import NewsApiClient
import pandas as pd
from sqlalchemy import or_
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'x9f3j2k7h5l1m4n8p0q6r3s'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
newsapi = NewsApiClient(api_key='40613cc4acdc4a409f8d7ee6c4a62f1f')


# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    preferences = db.relationship('UserPreference', backref='user', uselist=False)
    saved_articles = db.relationship('SavedArticle', backref='user', lazy=True)

class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    categories = db.Column(db.String(255))
    sources = db.Column(db.String(255))
    countries = db.Column(db.String(100))

class SavedArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    url = db.Column(db.String(255))
    urlToImage = db.Column(db.String(255))
    publishedAt = db.Column(db.String(100))
    source = db.Column(db.String(100))
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def fetch_personalized_news(preferences):
    categories = preferences.categories.split(',') if preferences.categories else []
    sources = preferences.sources.split(',') if preferences.sources else []
    country = preferences.countries if preferences.countries else "us"

    all_articles = []
    
    # Fetch from sources with category filtering
    if sources:
        sources_param = ",".join([src.strip() for src in sources])
        top_headlines = newsapi.get_top_headlines(
            sources=sources_param,
            language='en'
        )
        articles = top_headlines.get('articles', [])
        
        # Filter by category if both sources and categories are selected
        if categories:
            for article in articles:
                title = article.get('title')
                description = article.get('description')

                title_lower = title.lower() if isinstance(title, str) else ''
                description_lower = description.lower() if isinstance(description, str) else ''

                # Skip filtering for specific sources
                if any(src in ["espn", "techcrunch", "business-insider"] for src in sources):
                    all_articles.append(article)
                # Otherwise filter by category keywords
                elif any(cat.lower() in title_lower or cat.lower() in description_lower for cat in categories):
                    all_articles.append(article)
        else:
            all_articles.extend(articles)
    
    # If only categories are selected, fetch category-based news
    elif categories:
        for category in categories:
            top_headlines = newsapi.get_top_headlines(
                category=category.strip(),
                language='en',
                country=country
            )
            all_articles.extend(top_headlines.get('articles', []))

    # Convert to structured format
    df = pd.DataFrame(all_articles) if all_articles else pd.DataFrame()
    if not df.empty:
        df = df[['title', 'description', 'url', 'urlToImage', 'publishedAt', 'source']]
        df['source'] = df['source'].apply(lambda x: x['name'])
        return df.to_dict('records')

    return []

# Routes
@app.route('/')
@login_required
def index():
    if not current_user.preferences:
        return redirect(url_for('set_preferences'))
    return render_template('index.html')

@app.route('/get_news')
@login_required
def get_news():
    try:
        if not current_user.preferences:
            return jsonify({'error': 'Set preferences first'})
        
        news = fetch_personalized_news(current_user.preferences)
        
        if not news:
            return jsonify({'error': 'No news articles found for selected preferences.'})
        
        return jsonify(news)
    
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return jsonify({'error': 'Failed to fetch news. Please try again later.'}), 500

@app.route('/set_preferences', methods=['GET', 'POST'])
@login_required
def set_preferences():
    if request.method == 'POST':
        categories = request.form.getlist('categories')
        sources = request.form.getlist('sources')
        country = request.form.get('country')

        # Create strings from lists
        categories_str = ",".join(categories) if categories else ""
        sources_str = ",".join(sources) if sources else ""

        # Update preferences
        existing_pref = UserPreference.query.filter_by(user_id=current_user.id).first()
        if existing_pref:
            db.session.delete(existing_pref)
            db.session.commit()

        new_pref = UserPreference(
            user_id=current_user.id,
            categories=categories_str,
            sources=sources_str,
            countries=country
        )
        db.session.add(new_pref)
        db.session.commit()

        flash('Preferences updated successfully!', 'success')
        return redirect(url_for('index')) 

    return render_template('preferences.html')

@app.route('/search_news')
@login_required
def search_news():
    try:
        query = request.args.get('query', '')
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
            
        if not current_user.preferences:
            return jsonify({'error': 'Set preferences first'})
        
        # Get news and filter
        news = fetch_personalized_news(current_user.preferences)
        
        if not news:
            return jsonify({'error': 'No news articles found for your preferences.'})
        
        query = query.lower()
        filtered_news = [
            article for article in news 
            if (query in article.get('title', '').lower() or 
                query in (article.get('description', '') or '').lower() or 
                query in article.get('source', '').lower())
        ]
        
        return jsonify(filtered_news)
    
    except Exception as e:
        print(f"Error searching news: {str(e)}")
        return jsonify({'error': 'Failed to search news. Please try again later.'}), 500

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        
        flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Saved articles routes
@app.route('/saved')
@login_required
def saved():
    return render_template('saved.html')

@app.route('/save_article', methods=['POST'])
@login_required
def save_article():
    try:
        data = request.json
        
        # Check required fields
        required_fields = ['title', 'description', 'url', 'urlToImage', 'publishedAt', 'source']
        if not all(field in data and data[field] for field in required_fields):
            missing = [field for field in required_fields if field not in data or not data[field]]
            return jsonify({'success': False, 'message': f'Missing fields: {", ".join(missing)}'}), 400
        
        # Check if already saved
        existing = SavedArticle.query.filter_by(user_id=current_user.id, url=data.get('url')).first()
        if existing:
            return jsonify({'success': False, 'message': 'Article already saved'}), 400
        
        # Save article
        article = SavedArticle(
            user_id=current_user.id,
            title=data.get('title'),
            description=data.get('description'),
            url=data.get('url'),
            urlToImage=data.get('urlToImage'),
            publishedAt=data.get('publishedAt'),
            source=data.get('source')
        )
        
        db.session.add(article)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Article saved successfully'})
    
    except Exception as e:
        db.session.rollback()
        print(f"Error saving article: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to save article'}), 500

@app.route('/get_saved_articles')
@login_required
def get_saved_articles():
    try:
        articles = SavedArticle.query.filter_by(user_id=current_user.id).order_by(SavedArticle.saved_at.desc()).all()
        
        result = []
        for article in articles:
            result.append({
                'id': article.id,
                'title': article.title,
                'description': article.description,
                'url': article.url,
                'urlToImage': article.urlToImage,
                'publishedAt': article.publishedAt,
                'source': article.source,
                'saved_at': article.saved_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error fetching saved articles: {str(e)}")
        return jsonify({'error': 'Failed to retrieve saved articles'}), 500

@app.route('/delete_saved_article/<int:article_id>', methods=['DELETE'])
@login_required
def delete_saved_article(article_id):
    try:
        article = SavedArticle.query.filter_by(id=article_id, user_id=current_user.id).first()
        
        if not article:
            return jsonify({'success': False, 'message': 'Article not found'}), 404
        
        db.session.delete(article)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Article removed from saved'})
    
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting saved article: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to delete article'}), 500
    
@app.route('/search_saved_articles')
@login_required
def search_saved_articles():
    try:
        query = request.args.get('query', '')
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Search in saved articles
        search_filter = or_(
            SavedArticle.title.ilike(f'%{query}%'),
            SavedArticle.description.ilike(f'%{query}%'),
            SavedArticle.source.ilike(f'%{query}%')
        )
        
        articles = SavedArticle.query.filter(
            SavedArticle.user_id == current_user.id,
            search_filter
        ).order_by(SavedArticle.saved_at.desc()).all()
        
        # Format results
        result = []
        for article in articles:
            result.append({
                'id': article.id,
                'title': article.title,
                'description': article.description,
                'url': article.url,
                'urlToImage': article.urlToImage,
                'publishedAt': article.publishedAt,
                'source': article.source,
                'saved_at': article.saved_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error searching saved articles: {str(e)}")
        return jsonify({'error': 'Failed to search saved articles'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)