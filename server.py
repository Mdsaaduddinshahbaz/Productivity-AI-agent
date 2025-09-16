import eventlet
eventlet.monkey_patch()
import eventlet.wsgi
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sock import Sock
import json
import sys, os
from database import login_existing_user,create_new_user,update_user_info,return_saved_fields,delete_user_info
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

app = Flask(__name__)
CORS(app)
sock = Sock(app)

selected_url = None
form_fill_active = False
ws_clients = []   # keep connected websocket clients

webpagesearch=False
@app.route("/login",methods=["POST"])
def login():
    data=request.get_json()
    print(data)
    val=login_existing_user(data)
    print(val)
    if (val==-1):
        print("im in success=False")
        return({"success":False})
    elif (val==404):
        return({"success":"not found"})
    else:
        return({"success":True})

@app.route("/signup",methods=["POST"])
def store_info():
    data=request.json
    val=create_new_user(data)
    print(f"val={val}")
    if (val==0):
        print("already exists")
        return({"success":False})
    else:
        print(f"Datastored in the database")
    print("signup called")
    return({"success":True})

@app.route("/return_existing_fields",methods=["POST"])
def existing_fields():
    fields=return_saved_fields()
    print("fields returned=",fields)
    return({"fields":fields})

@app.route("/storeUserInfo",methods=["POST"])
def store_new_info():
    print("store_user_info")
    data=request.get_json()
    print("data=",data["formdata"])
    val=update_user_info(data["formdata"])
    if(val["success"]):
        return ({"success":True})
    return({"success":False})

@app.route("/deleteUserInfo", methods=["POST"])
def delete_field():
    data = request.json
    val=delete_user_info(data["fields"])
    print("val in api",val)
    if(val["success"]):
        print("true value deleted")
        return({"success":True})
    else:
        print("return value not deleted")
    return({"success":False})


# @app.route("/match", methods=["POST"])
# def match():
#     data = request.json
#     fields = data.get("fields", [])
#     print("\n📋 Fields received for autofill on backend:")
#     print(fields)

#     from pathfetcher import return_values
#     filled_fields, mapping = return_values(fields)

#     return jsonify({
#         "fields": filled_fields,
#         "mapping": mapping
#     })

@app.route("/togglestatus", methods=["POST"])
def toggle_status():
    global form_fill_active
    data = request.json
    form_fill_active = data.get("active", False)
    print("Got status of fill form", form_fill_active)

    # 🔥 Broadcast to all connected websocket clients
    msg = json.dumps({
        "action": "toggleFormFill",
        "active": form_fill_active,
        "webpageactive":webpagesearch
    })
    for ws in ws_clients[:]:
        try:
            ws.send(msg)
        except Exception:
            ws_clients.remove(ws)

    return jsonify({"success": True, "active": form_fill_active})

@app.route("/setwebpageinactive", methods=["POST"])
def set_webpage_inactive():
    global webpagesearch
    data = request.json
    webpagesearch = data.get("active", False)
    print("Got websearch inactive status in server", webpagesearch)
    return {"success": True, "active": webpagesearch}

@app.route("/setwebpageactive", methods=["POST"])
def toggle_statuss():
    global webpagesearch
    data = request.json
    webpagesearch = data.get("active", False)
    print("Got status", webpagesearch)

    # 🔥 Broadcast to all connected websocket clients
    msg = json.dumps({
        "action": "setwebpageactive",
        "active": webpagesearch
    })
    for ws in ws_clients[:]:
        try:
            ws.send(msg)
        except Exception:
            ws_clients.remove(ws)

    return jsonify({"success": True, "active": webpagesearch})

# @app.route("/store_text", methods=["POST"])
# def store_text():
#     data = request.get_json()
#     text = data.get("text", "")
#     if not text.strip():
#         return jsonify({"error": "No text received"}), 400

#     chunks_count = rag.store_text_qdrant(text)
#     return jsonify({"status": "stored", "chunks": chunks_count})

# @app.route("/query", methods=["POST"])
# def query():
#     data = request.get_json()
#     query = data.get("query", "")
#     if not query.strip():
#         return jsonify({"error": "No query received"}), 400

#     results = rag.query_text(query,3)   # 👈 call rag.py function
#     return jsonify(results)
# --- WebSocket endpoint ---
@sock.route('/ws')
def ws(ws):
    print("✅ WebSocket client connected")
    ws_clients.append(ws)
    try:
        while True:
            eventlet.sleep(10)  # keep alive
    except Exception as e:
        print("❌ WebSocket closed:", e)
    finally:
        if ws in ws_clients:
            ws_clients.remove(ws)

if __name__ == "__main__":
    listener = eventlet.listen(("127.0.0.1", 5000))
    eventlet.wsgi.server(listener, app)
