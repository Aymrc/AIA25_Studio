from flask import Flask, request
import time

app = Flask(__name__)

@app.route("/rhino_data", methods=["POST"])
def receive_data():
    data = request.json
    print(f"📥 Received data from Rhino at {time.ctime()}:")
    print(data)
    return {"status": "received"}

if __name__ == "__main__":
    app.run(port=5050)
