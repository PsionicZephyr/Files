# Installation:
# pkg update -y
# pkg install python -y
# pip install flask flask-cors
# pkg install termux-tools -y
# pkg install termux-api -y
# python android_server.py

import subprocess
import mimetypes
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Global Settings ---
AUTO_APPROVE = False

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

@app.route('/execute', methods=['POST'])
def execute_command():
    try:
        data = request.get_json()
        command = data.get('command')

        if not command:
            return "Error: No command provided", 400

        print(f"Received command: {command}")

        if not AUTO_APPROVE:
            print("\n--- Awaiting User Approval ---")
            print(f"The LLM wants to execute the following command:\n\n{command}\n")
            approval = input("Do you want to allow this? (y/n): ").lower().strip()
            if approval != 'y':
                print("User rejected the command.")
                return "Command execution rejected by the user.", 200
            print("User approved the command.")

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Combine stdout and stderr for a unified text response, similar to the C++ server
        output = result.stdout
        if result.stderr:
            output += "\n--- STDERR ---\n" + result.stderr

        print(f"Command finished with code {result.returncode}")
        return output, 200

    except Exception as e:
        print(f"Error executing command: {str(e)}")
        return f"Server Error: {str(e)}", 500

@app.route('/execute_trusted', methods=['POST'])
def execute_trusted_command():
    try:
        data = request.get_json()
        command = data.get('command')

        if not command:
            return "Error: No command provided", 400

        print(f"Received trusted command: {command}")

        # Execute without approval
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )

        output = result.stdout
        if result.stderr:
            output += "\n--- STDERR ---\n" + result.stderr

        print(f"Trusted command finished with code {result.returncode}")
        return output, 200

    except Exception as e:
        print(f"Error executing trusted command: {str(e)}")
        return f"Server Error: {str(e)}", 500

@app.route('/readfile', methods=['POST'])
def read_file():
    try:
        data = request.get_json()
        file_path = data.get('path')

        if not file_path:
            return jsonify({"error": "No path provided"}), 400

        print(f"Received request to read file: {file_path}")

        # Guess the mime type of the file
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'

        response_json = {
            "mime_type": mime_type
        }

        # Check if it's a text-based format
        if mime_type.startswith('text/') or mime_type in ['application/json', 'application/xml', 'application/javascript']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                response_json["content"] = content
                response_json["encoding"] = "utf-8"
                print(f"Successfully read text file. Size: {len(content)} chars.")
            except Exception as e:
                # Fallback for non-utf8 text files could be added here if needed
                print(f"Error reading text file: {str(e)}")
                return jsonify({"error": f"Could not read file as text: {str(e)}"}), 500
        else:
            # Handle as a binary file (image, audio, etc.)
            try:
                with open(file_path, 'rb') as f:
                    binary_content = f.read()
                base64_content = base64.b64encode(binary_content).decode('utf-8')
                response_json["content"] = base64_content
                response_json["encoding"] = "base64"
                print(f"Successfully read and encoded binary file. Size: {len(binary_content)} bytes.")
            except FileNotFoundError:
                return jsonify({"error": f"File not found: {file_path}"}), 404
            except Exception as e:
                print(f"Error reading binary file: {str(e)}")
                return jsonify({"error": f"Could not read binary file: {str(e)}"}), 500
        
        return jsonify(response_json)

    except Exception as e:
        print(f"Error processing /readfile request: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    PORT = 9999
    print("=========================================")
    print(" Android Local Command Executor")
    print(" (CORS Enabled)")
    print(f" Listening on http://127.0.0.1:{PORT}")
    print("=========================================")
    print("!!! RUN THIS ONLY ON THE DEVICE YOU ARE USING TO BROWSE !!!")
    
    # Ask for auto-approval setting at startup
    choice = input("Auto-approve command execution? (y/n): ").lower().strip()
    if choice == 'y':
        AUTO_APPROVE = True
        print("--> Auto-approval ENABLED.")
    else:
        AUTO_APPROVE = False
        print("--> Auto-approval DISABLED. You will be prompted for each command.")
    
    app.run(host='127.0.0.1', port=PORT)
