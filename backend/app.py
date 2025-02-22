from api import create_app  # Import the app factory

# Create the app instance by calling the create_app function
app = create_app(config_class='config.Config')

if __name__ == "__main__":
    app.run()
