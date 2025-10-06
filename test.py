import socketio
import time

# --- Server URL ---
# Change this to your deployed backend or local server
SERVER_URL = "http://127.0.0.1:5000"  

# --- Create client instance ---
sio = socketio.Client()

# --- Event handlers ---
@sio.event
def connect():
    print("✅ Connected to server!")
    # Wait 2 seconds before sending the first message
    time.sleep(2)
    sio.emit("message", "Hello AI bot, can you hear me?")
    print("📤 Sent: Hello AI bot, can you hear me?")

@sio.event
def disconnect():
    print("❌ Disconnected from server.")

@sio.on("response")
def on_response(data):
    """Handles AI responses streamed from the server."""
    text = data.get("text", "")
    print(f"🤖 AI: {text}", end="", flush=True)

@sio.on("connected")
def on_connected(data):
    print(f"🔗 Server says: {data['message']}")

# --- Main run ---
if __name__ == "__main__":
    try:
        # Connect to server
        print(f"Connecting to {SERVER_URL} ...")
        sio.connect(SERVER_URL)

        # After 10 seconds, send another message
        time.sleep(10)
        sio.emit("message", "Tell me something about FRA claims process.")
        print("\n📤 Sent: Tell me something about FRA claims process.")

        # Keep the client running to listen for streamed replies
        sio.wait()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user.")
        sio.disconnect()
    except Exception as e:
        print(f"⚠️ Error: {e}")