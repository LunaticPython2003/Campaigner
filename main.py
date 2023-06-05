from flask import Flask, request, jsonify
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from flask.views import MethodView
import mysql.connector as ms
import os
from dotenv import load_dotenv
import threading

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
    

    
class ChannelsView(MethodView):
    threads = 10
    priority = {"Sms": 1, "Whatsapp": 2, "Email": 3, "Rcs": 4}
    chunks = float('inf')
    channel_methods = []

    @jwt_required()
    def post(self):
        auth_header = request.headers.get('Authorization')
        jwt_token = auth_header.split("Bearer ")[1] if auth_header and auth_header.startswith("Bearer ") else None
        current_user_id = str(get_jwt_identity()[0])
        json_data = request.get_json()
        if request.path == '/settings':
            return self.handle_settings_post(current_user_id, json_data)
        else:
            db_cursor.execute(f"SELECT username FROM customers WHERE userid={current_user_id}")
            user = db_cursor.fetchone()[0]
            channels = json_data.get('channels')
            self.channel_methods = sorted(channels.keys(), key=lambda x: self.priority[x])
            chunks = json_data.get('chunks')
            self.chunks = chunks
            if user is not None:
                threads = []
                for process in self.channel_methods:
                    if hasattr(self, process):
                        func = getattr(self, process)
                        thread = threading.Thread(target=func, args=(channels[process],))  # Capitalize key
                        threads.append(thread)
                        thread.start()

                for thread in threads:
                    thread.join()

                return jsonify({'msg': 'Processing completed'})

            else:
                return jsonify({'msg': 'Access forbidden'}), 403
            
    def handle_settings_post(self, current_user_id, json_data):
        threads = json_data.get('threads')
        priority = json_data.get('priority')
        chunks = json_data.get('chunks')
        try:
            db_cursor.execute(f'INSERT INTO settings (UserId, threads, priority, chunks) VALUES ({current_user_id}, {threads}, "{priority}", {chunks})')
            mydb.commit()
            return jsonify(message='Added record successfully')
        except ms.errors.IntegrityError as err:
            return jsonify(message=str(err))

    @staticmethod
    def Whatsapp(method):
        print(method)

    @staticmethod
    def Sms(method):
        print(method)

    @staticmethod
    def Rcs(method):
        print(method)

    @staticmethod
    def Email(method):
        print(method)
        
    
app.add_url_rule('/channels', view_func=ChannelsView.as_view('channels'), methods=['POST'])
app.add_url_rule('/settings', view_func=ChannelsView.as_view('post'), methods=['POST'])


if __name__=="__main__":
    app.run(debug=True)