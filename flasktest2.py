from flask import Flask, render_template,request
from flask_socketio import SocketIO,join_room,leave_room,send,emit
from collections import namedtuple
import sqlite3
import colorsys
import json
import datetime
app = Flask(__name__)
socketio = SocketIO(app)
database = sqlite3.connect("C:\\Users\\emile\\Documents\\kolory\\db.db",  check_same_thread=False)
db_c = database.cursor()
Answer = namedtuple("Answer",["selections","answer","date"])
TrainingAnswer = namedtuple("TrainingAnswer",["color","feedback","date"])
import random
r = lambda: random.randint(0,255)
random_color = lambda:'#%02X%02X%02X' % (r(),r(),r())
class Client:
    @staticmethod
    def print_all():
        for a in active_clients:print(vars(a))
    @staticmethod
    def get_by_id(id:int):
        return [x for x in active_clients if x.id == id][0]
    def update_alive_status(self):
        self.is_alive=False
        emit("aliveCheck", room=self.id,callback=self.__alive_callback)
    def __alive_callback(self):
        self.is_alive=True
    def __init__(self, id, name,hash = id, source=None):
        self.id = id
        self.is_alive=True
        self.hash = hash
        self.name = name
        self.source=source
        self.answers = []
        self.start = datetime.datetime.now()
        self.end=None
    def get_training_asnwers_as_json(self):
        answers = []
        for c in self.answers:
            answers.append({"color":c.color,"feedback":c.feedback})
        a=json.dumps(answers)
        with open("/results/"+self.id,"w") as f:
            f.write(a)
active_clients = []
def save_client_to_database(client:Client):
    print("saving")
    for answer in client.answers:
        db_c.execute("INSERT INTO Answers(session, h, s, v, feedback, date) VALUES (?,?,?,?,?,?)",(client.id, answer.color[0], answer.color[1], answer.color[2],answer.feedback,datetime.datetime.now()))
    db_c.execute("INSERT INTO Sessions(hash,start,end,answers_count) VALUES (?,?,?,?)", (client.id, client.start, datetime.datetime.now(), len(client.answers)))
    database.commit()
    print("saved a client")
@app.route('/')
def hello_world():
    return render_template("trenowanie.html")

@socketio.on("connect")
def handle_connection():
    new_client = Client(request.sid,"unnamed")
    join_room(request.sid)
    active_clients.append(new_client)
    Client.print_all()
    send_new_random_color(new_client.id)
    #new_client.update_alive_status()
    #print(new_client.is_alive)
@socketio.on("disconnect")
def handle_disconnect():
    print("disconnected")
    id = request.sid
    client = Client.get_by_id(id)
    #client.get_training_asnwers_as_json()
    #save_client_to_database(client)
    for answer in client.answers:
        db_c.execute("INSERT INTO Answers(session, h, s, v, feedback, date) VALUES (?,?,?,?,?,?)", (
        client.id, answer.color[0], answer.color[1], answer.color[2], answer.feedback, datetime.datetime.now()))
    db_c.execute("INSERT INTO Sessions(id,hash,start,end,answers_count) VALUES (?,?,?,?,?)", (0,client.id, client.start, datetime.datetime.now(), len(client.answers)))
    database.commit()

    active_clients.remove(client)
    Client.print_all()

@socketio.on("selection")
def handle_selection(data):

    #zabezpieczenie zeby przyjmowalo tylko kolory ktore byly wyslane. temp field w clinet?
    color_hex = data["color"].lstrip("#")
    color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2 ,4))
    color_hsv = colorsys.rgb_to_hsv(color_rgb[0],color_rgb[1],color_rgb[2])

    selections_hex = [x.lstrip("#") for x in data["selections"]]
    selections_hsv=[]
    for s in selections_hex:
        rgb = tuple(int(s[i:i+2], 16) for i in (0, 2 ,4))
        selections_hsv.append(colorsys.rgb_to_hsv(rgb[0], rgb[1], rgb[2]))
    answer_object = Answer(selections_hsv,color_hsv,datetime.datetime.now())
    client = Client.get_by_id(request.sid)
    client.answers.append(answer_object)
    #skomplikowany algorytm
    new_color = random_color()
    emit("changeColors",[new_color])
    print(vars(client))
@socketio.on("selectionTraining")
def handle_selection_training(data):
    color_hex = data["color"].lstrip("#")
    color_rgb = tuple(int(color_hex[i:i + 2], 16) for i in (0, 2, 4))
    color_hsv = colorsys.rgb_to_hsv(color_rgb[0], color_rgb[1], color_rgb[2])
    answer_object = TrainingAnswer(color_hsv,data["feedback"],datetime.datetime.now())
    client = Client.get_by_id(request.sid)
    client.answers.append(answer_object)
    # skomplikowany algorytm
    send_new_random_color(client.id)
@socketio.on("test1")
def test():
    print("recv")
def send_new_random_color(roomId):
    new_color = random_color()
    emit("changeColors", [new_color],room=roomId)
def determine_next_color(prev_answers:list)->str:
    pass
def save_client_to_database(client:Client):
    pass
if __name__ == '__main__':
    socketio.run(app)