from flask import Flask,send_from_directory
from flask_cors import CORS
from blueprints.recipes.recipes import recipes_bp
from blueprints.reviews.reviews import reviews_bp
from blueprints.auth.auth import auth_bp

app = Flask(__name__, static_folder='foodImages', static_url_path='/foodImages')
CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}}, supports_credentials=True)

app.register_blueprint(recipes_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(auth_bp)

#df = pd.read_csv("recipe.csv")
 
@app.route('/test')
def test():
    return '''
    <h1>Image Test</h1>
    <img src="/foodImages/thanksgiving-mac-and-cheese-erick-williams.jpg" width="500">
    
    '''


if __name__ == "__main__":
    app.run(debug=True)
 

 