from app import app, db, User, UserPreference
with app.app_context():
    print("Total Users:", User.query.count(), "\n") #total user
    
    users = User.query.all()
    for user in users:
        print(f"User: {user.username}") # user name + prefs
        if user.preferences:
            print(f"Preferences: {user.preferences.categories}")
            print(f"Sources: {user.preferences.sources}")
            print(f"Countries: {user.preferences.countries}")
            print()
