from flask import Flask 
 
 

from blueprints.recipes.recipes import recipes_bp
from blueprints.reviews.reviews import reviews_bp
from blueprints.auth.auth import auth_bp

app = Flask(__name__)
 

app.register_blueprint(recipes_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(auth_bp)

 
 
 
#df = pd.read_csv("recipe.csv")



if __name__ == "__main__":
    app.run(debug=True)
 

 