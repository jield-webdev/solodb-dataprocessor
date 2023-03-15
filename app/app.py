from flask import Flask
from endpoints import blueprint as endpoints

app = Flask(__name__)
app.config['RESTPLUS_MASK_SWAGGER'] = False

app.register_blueprint(endpoints)

if __name__ == "__main__":
    app.run(
      host='0.0.0.0', 
      port=8000)
