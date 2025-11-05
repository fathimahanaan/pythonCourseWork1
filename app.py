from flask import Flask,send_from_directory
from blueprints.recipes.recipes import recipes_bp
 
from blueprints.reviews.reviews import reviews_bp
from blueprints.auth.auth import auth_bp

app = Flask(__name__, static_folder='foodImages', static_url_path='/foodImages')

app.register_blueprint(recipes_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(auth_bp)

#df = pd.read_csv("recipe.csv")
 
@app.route('/test')
def test():
    return '''
    <h1>Image Test</h1>
    <img src="/foodImages/thanksgiving-mac-and-cheese-erick-williams.jpg" width="500">
    <p>If you see the image above, it's working!</p>
    '''


if __name__ == "__main__":
    app.run(debug=True)
 

 