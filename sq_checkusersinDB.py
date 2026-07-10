from pulsefeed import create_app, db
from pulsefeed.models import User, UserPreference

app = create_app()

with app.app_context():
    print("Total Users:", User.query.count(), "\n")

    users = User.query.all()
    for user in users:
        print(f"User: {user.username}")
        if user.preferences:
            print(f"Preferences: {user.preferences.categories}")
            print(f"Sources: {user.preferences.sources}")
            print(f"Countries: {user.preferences.countries}")
            print()
