from flask import Flask, request, jsonify
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from flask.views import MethodView
import mysql.connector as ms
import os
from concurrent.futures import ThreadPoolExecutor, wait
from dotenv import load_dotenv
import time, datetime
from threading import Lock
import json
import requests
import threading
import multiprocessing

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
        return jsonify({'msg': 'Wrong username or userkey'}), 401
    else:
        access_token = create_access_token(identity=userid)
        return jsonify({ "token": access_token, "user_id": userid })
    

class ChannelsView(MethodView):
    threads = 0
    priority = dict()
    chunks = float('inf')
    schedule = {}
    temp_priority = {}
    lock = Lock() 

    @jwt_required()
    def post(self):
        auth_header = request.headers.get('Authorization')
        jwt_token = auth_header.split("Bearer ")[1] if auth_header and auth_header.startswith("Bearer ") else None
        current_user_id = str(get_jwt_identity()[0])
        json_data = request.get_json()
        if request.path == '/settings':
            return self.handle_settings_post(current_user_id, json_data)
        elif request.path == '/status':
            return self.handle_status_post(current_user_id, json_data)
        else:
            channel_payload = json_data.get('channels')
            channel_priority = json_data.get('channel_priority')
            get_threads = json_data.get('threads')
            settings_save = json_data.get('save_settings')
            proceed = bool(channel_priority==None or get_threads==None)
            match proceed:
                case True:
                    db_cursor.execute(f'select * from settings where UserId={current_user_id}')
                    result = db_cursor.fetchone()
                    with self.lock:
                        self.threads = result[1]
                        self.temp_priority = result[2]
                    self.temp_priority = json.loads(self.temp_priority)
                    for processes in self.temp_priority:
                        values = list(processes.values())
                        self.priority[values[0]] = values[1]
                        self.schedule[values[0]] = values[2]
                case _:
                    with self.lock:
                        self.threads = get_threads
                        self.temp_priority = channel_priority
                    for processes in self.temp_priority:
                        values = list(processes.values())
                        self.priority[values[0]] = values[1]
                        self.schedule[values[0]] = values[2]
                    if settings_save == "yes":
                        db_cursor.execute(f"INSERT INTO settings (UserId, threads, channel_priority) VALUES ({current_user_id}, {self.threads}, '{channel_priority}')")
                        mydb.commit()
            
            db_cursor.execute(f"SELECT username FROM customers WHERE userid={current_user_id}")
            user = db_cursor.fetchone()[0]
            status_channels = []
            return_status = dict()
            if user is not None:
                grouped_channels = {}
                for channel, priority in self.priority.items():
                    if priority not in grouped_channels:
                        grouped_channels[priority] = []
                    grouped_channels[priority].append(channel)
                    status_channels.append(channel)

                execution_list = list(grouped_channels.values())
                return_status = {key:0 for key in status_channels}
                return_status =json.dumps(return_status)
                db_cursor.execute(f"INSERT INTO status VALUES ({current_user_id}, '{return_status}')")
                mydb.commit()
                with ThreadPoolExecutor(max_workers=self.threads) as executor:
                    for group in execution_list:
                        futures = []
                        for channel in group:
                            if channel in self.priority and hasattr(self, channel):
                                func = getattr(self, channel)
                                schedule = self.schedule[channel]
                                if schedule == "0":
                                    futures.append(executor.submit(func, channel_payload[channel]))
                                else:
                                    executor.submit(self.execute_with_schedule, func, channel, current_user_id,channel_payload[channel], schedule)
                        print(futures)
                        threading.Thread(target=wait, args=(futures,)).start()
                    return jsonify({"msg": "Execution started"})

            else:
                return jsonify({'msg': 'Please register your user settings'})


    def execute_with_schedule(self, func, channel, current_user_id, payload, schedule):
        current_time = datetime.datetime.now()
        start_hour, start_minute = map(int, schedule.split(':'))
        scheduled_time = current_time.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        
        if current_time < scheduled_time:
            time.sleep((scheduled_time - current_time).total_seconds())

        process = multiprocessing.Process(target=func, args=(payload,))
        process.start()

        db_cursor.execute(f"select status_code from status where Userid={current_user_id}")
        status_code = json.loads(db_cursor.fetchone()[0])
        status_code = int(status_code[channel])
        while process.is_alive():
            if status_code == 1:
                process.terminate()
                break  

        time.sleep(1) 
        
    def handle_status_post(self, current_user_id, json_data):
        db_cursor.execute(f"select status_code from status where Userid={current_user_id}")
        status_code = json.loads(db_cursor.fetchone()[0])
        payload_status_codes = json_data["status_code"]
        for channel in status_code:
            if channel in payload_status_codes:
                status_code[channel] = 1
            else:
                status_code[channel] = 0
        update_status_code = json.dumps(status_code)
        db_cursor.execute(f"update status set status_code='{update_status_code}' where Userid={current_user_id}")
        mydb.commit()
        return update_status_code

    def handle_settings_post(self, current_user_id, json_data):
        threads = json_data.get('threads')
        channels_priority = json_data.get('channel_priority')
        channels_str = json.dumps(channels_priority)
        try:
            db_cursor.execute(f"INSERT INTO settings (UserId, threads, channel_priority) VALUES ({current_user_id}, {threads}, '{channels_str}')")
            mydb.commit()
            return jsonify({'msg': 'Added record successfully'})
        except (ms.IntegrityError, ms.DataError) as err:
            return jsonify({"msg": str(err)})
        except ms.ProgrammingError as err:
            return jsonify({"msg": str(err)})
        except ms.Error as err:
            return jsonify({"msg": str(err)})
        

    def Whatsapp(self, method):
        response = requests.get('endpoint')
        if response.status_code != 200:
            return
        print("Whatsapp ->", method)

    def Sms(self, method):
        response = requests.get('endpoint')
        if response.status_code != 200:
            return
        print("Sms ->", method)

    def Rcs(self, method):
        response = requests.get('endpoint')
        if response.status_code != 200:
            return
        print("Rcs ->", method)

    def Email(self, method):
        response = requests.get('endpoint')
        if response.status_code != 200:
            return
        print("Email ->", method)
        
    
app.add_url_rule('/channels', view_func=ChannelsView.as_view('channels'), methods=['POST'])
app.add_url_rule('/settings', view_func=ChannelsView.as_view('post'), methods=['POST'])
app.add_url_rule('/status', view_func=ChannelsView.as_view('status'), methods=['POST'])


if __name__=="__main__":
    app.run(debug=True)