# diagnostics_debugger.py

import os
import time
import hashlib

WATCHED_FILE = os.path.join("knowledge", "ml_output.json")


def get_hash(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        print(f"❌ Error reading file for hash: {e}")
        return None


def run_diagnostics():
    print("\n🚀 Running ML Output Watcher Diagnostics...")
    print(f"📍 Watching: {WATCHED_FILE}")

    if not os.path.exists(WATCHED_FILE):
        print("❌ File does not exist. Create or generate it first.")
        return

    previous_hash = get_hash(WATCHED_FILE)
    print(f"🔁 Initial hash: {previous_hash}")

    print("🕵️‍♂️ Waiting for external changes (modify the file externally)...")
    try:
        while True:
            time.sleep(2)
            current_hash = get_hash(WATCHED_FILE)
            if current_hash != previous_hash:
                print(f"\n📂 Detected external change in {WATCHED_FILE} at {time.strftime('%H:%M:%S')}")
                print(f"   Previous hash: {previous_hash}")
                print(f"   Current hash:  {current_hash}")
                print("✅ File change successfully detected — this confirms watcher should trigger.")
                previous_hash = current_hash
            else:
                print("⏳ No change detected...")
    except KeyboardInterrupt:
        print("\n👋 Stopping diagnostics.")


if __name__ == "__main__":
    run_diagnostics()
