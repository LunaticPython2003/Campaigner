from flask import Flask, request, jsonify
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from flask.views import MethodView
from concurrent.futures import ThreadPoolExecutor
import mysql.connector as ms
import os
from dotenv import load_dotenv

load_dotenv()

secret_key = os.getenv('secret_key')
HOST = os.getenv('HOST')
DATABASE = os.getenv('database')
USER = os.getenv('USER')

# Configure the Flask App
app = Flask(__name__)
jwt = JWTManager(app)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config["JWT_SECRET_KEY"] = secret_key
# app.config['CACHE_TYPE'] = 'simple'
app.debug = True


#SQL connectivity
mydb = ms.connect(host=HOST, user=USER, database=DATABASE, password='')
db_cursor = mydb.cursor()

@app.route('/user')
def validate():
    query = request.args.values()
    username = next(query)
    userkey = next(query)
    db_cursor.execute(f'select userid from customers where username={username} and userkey={userkey}')
    userid = db_cursor.fetchone()
    if userid is None:
        return jsonify({'msg': 'Wrong username or userid'}), 401
    else:
        access_token = create_access_token(identity=userid)
        return jsonify({ "token": access_token, "user_id": userid })
    

@app.route('/settings')
def settings():
    pass

    
class ChannelsView(MethodView):
    # threads = 10
    # priority = {"SMS": 1, "WhatsApp": 2, "email": 3, "RCS": 4}
    # chunks = float('inf')
    # channel_methods = []

    @jwt_required
    def settings_post(self):
        auth_header = request.headers.get('Authorization')
        jwt_token = auth_header.split("Bearer ")[1] if auth_header and auth_header.startswith("Bearer ") else None
        current_user_id = str(get_jwt_identity()[0])

        json_data = request.get_json()
        

    @jwt_required()
    def post(self):
        auth_header = request.headers.get('Authorization')
        jwt_token = auth_header.split("Bearer ")[1] if auth_header and auth_header.startswith("Bearer ") else None
        current_user_id = str(get_jwt_identity()[0])

        json_data = request.get_json()
        db_cursor.execute(f"SELECT username FROM customers WHERE userid={current_user_id}")
        user = db_cursor.fetchone()[0]
        channels = json_data.get('channels')
        channel_methods = [x for x in channels.keys()]
        self.channel_methods = sorted(channel_methods, key=lambda x: self.priority[x])
        chunks = json_data.get('chunks')
        self.chunks = chunks
        if user is not None:
            # executor = ThreadPoolExecutor(max_workers = self.threads)
            # for task in channels:
            #     executor.submit(self.task, methods[task])
            for process in channel_methods:
                if hasattr(self, process):
                    func = getattr(self, process)
                    return func(channels[process])
            
        else:
            return jsonify({'msg': 'Access forbidden'}), 403
        
    def whatsapp(self, method):
        print(method)
        return jsonify(method)

    def SMS(self, method):
        print(method)
        return jsonify(method)

    def RCS(self, method):
        print(method)
        return jsonify(method)

    def email(self, method):
        print(method)
        return jsonify(method)
    
app.add_url_rule('/channels', view_func=ChannelsView.as_view('channels'))

if __name__=="__main__":
    app.run(debug=True)