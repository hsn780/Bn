from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # للسماح بطلبات من نطاقات أخرى

# تخزين البيانات في الذاكرة (يمكن استبدالها بقاعدة بيانات)
users = {}
messages = {}

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
      <meta charset="UTF-8">
      <title>viv - دردشة خاصة</title>
      <style>
        body {
          background: #f0f2f5;
          font-family: Arial, sans-serif;
          margin: 0;
          padding: 0;
        }
        .container {
          max-width: 800px;
          margin: 50px auto;
          padding: 20px;
          background: #fff;
          border-radius: 8px;
          box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        }
        .auth-section {
          text-align: center;
        }
        .auth-section h2 {
          margin-bottom: 20px;
          color: #333;
        }
        .auth-section input {
          width: 80%;
          padding: 10px;
          margin: 10px 0;
          border: 1px solid #ddd;
          border-radius: 4px;
          outline: none;
          transition: border-color 0.3s ease;
        }
        .auth-section input:focus {
          border-color: #888;
        }
        .auth-section button {
          padding: 10px 20px;
          margin: 10px 5px;
          border: none;
          border-radius: 4px;
          background: linear-gradient(45deg, #4facfe, #00f2fe);
          color: #fff;
          cursor: pointer;
          transition: opacity 0.3s ease;
        }
        .auth-section button:hover {
          opacity: 0.9;
        }
        .users-list {
          display: none;
          margin-top: 20px;
          padding: 15px;
          border: 1px solid #ddd;
          border-radius: 8px;
          background: #fafafa;
        }
        .user-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 10px;
          cursor: pointer;
          border-bottom: 1px solid #eee;
        }
        .user-item:last-child {
          border-bottom: none;
        }
        .user-item:hover {
          background: #f5f5f5;
        }
        .user-avatar {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          object-fit: cover;
          margin-left: 10px;
        }
        /* تنسيق النقطة الخضراء للمستخدم النشط */
        .status-indicator {
          display: inline-block;
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background-color: #4CAF50;
          margin-left: 5px;
        }
        .chat-section {
          display: none;
          margin-top: 20px;
          padding: 15px;
          border: 1px solid #ddd;
          border-radius: 8px;
          background: #fafafa;
        }
        .chat-section h3 {
          margin-bottom: 10px;
          color: #333;
        }
        #messages {
          max-height: 400px;
          overflow-y: auto;
          margin-bottom: 10px;
          padding: 10px;
          background: #fff;
          border: 1px solid #ddd;
          border-radius: 8px;
        }
        .message {
          padding: 10px;
          margin: 5px;
          border-radius: 8px;
          max-width: 70%;
          word-wrap: break-word;
          display: flex;
          align-items: flex-start;
        }
        .sent {
          background: #DCF8C6;
          margin-left: auto;
          flex-direction: row-reverse;
        }
        .received {
          background: #E8E8E8;
          margin-right: auto;
        }
        .message-avatar {
          width: 30px;
          height: 30px;
          border-radius: 50%;
          object-fit: cover;
          margin: 0 10px;
        }
        .message-text {
          flex: 1;
        }
        #messageInput {
          width: calc(100% - 90px);
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
          outline: none;
        }
        #chatSection button {
          padding: 10px 20px;
          border: none;
          border-radius: 4px;
          background: linear-gradient(45deg, #4facfe, #00f2fe);
          color: #fff;
          cursor: pointer;
          margin-left: 5px;
          transition: opacity 0.3s ease;
        }
        #chatSection button:hover {
          opacity: 0.9;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <!-- قسم المصادقة -->
        <div class="auth-section">
          <h2>مرحبًا في viv</h2>
          <input type="text" id="username" placeholder="اسم المستخدم">
          <input type="password" id="password" placeholder="كلمة المرور">
          <input type="file" id="avatar" accept="image/*">
          <button onclick="register()">تسجيل جديد</button>
          <button onclick="login()">تسجيل الدخول</button>
        </div>
        <!-- قائمة المستخدمين -->
        <div class="users-list" id="usersList">
          <h3>المستخدمون المتاحون:</h3>
          <div id="usersContainer"></div>
        </div>
        <!-- قسم الدردشة -->
        <div class="chat-section" id="chatSection">
          <h3 id="chatWith"></h3>
          <div id="messages"></div>
          <input type="text" id="messageInput" placeholder="اكتب رسالتك...">
          <button onclick="sendMessage()">إرسال</button>
          <button onclick="closeChat()">إغلاق الدردشة</button>
        </div>
      </div>
      <script>
        let currentUser = null;
        let selectedUser = null;
        let messageInterval = null; // لمتابعة التحديث التلقائي للرسائل
        const apiUrl = window.location.origin;  // استخدام نفس عنوان الخادم

        // تسجيل مستخدم جديد
        async function register() {
          const username = document.getElementById('username').value;
          const password = document.getElementById('password').value;
          const avatarFile = document.getElementById('avatar').files[0];

          if (!username || !password || !avatarFile) {
            alert('يرجى إدخال جميع الحقول.');
            return;
          }

          const reader = new FileReader();
          reader.onload = async function (e) {
            const response = await fetch(`${apiUrl}/register`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                username,
                password,
                avatar: e.target.result
              })
            });

            if (response.ok) {
              const userData = await response.json();
              currentUser = { uid: userData.userId, ...userData };
              showUsersList();
            } else {
              alert('حدث خطأ أثناء التسجيل.');
            }
          };

          reader.readAsDataURL(avatarFile);
        }

        // تسجيل الدخول
        async function login() {
          const username = document.getElementById('username').value;
          const password = document.getElementById('password').value;

          const response = await fetch(`${apiUrl}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
          });

          if (response.ok) {
            const userData = await response.json();
            currentUser = { uid: userData.userId, ...userData };
            showUsersList();
          } else {
            alert('بيانات تسجيل الدخول غير صحيحة.');
          }
        }

        // عرض قائمة المستخدمين
        async function showUsersList() {
          const response = await fetch(`${apiUrl}/users`);
          const users = await response.json();

          const usersContainer = document.getElementById('usersContainer');
          usersContainer.innerHTML = '';

          Object.entries(users).forEach(([userId, userData]) => {
            if (userId !== currentUser.uid) {
              const userDiv = document.createElement('div');
              userDiv.className = 'user-item';
              
              // إضافة نقطة الحالة إذا كان المستخدم نشطاً
              let statusIndicator = '';
              if (userData.online) {
                statusIndicator = '<span class="status-indicator"></span>';
              }
              
              userDiv.innerHTML = `
                <div style="display: flex; align-items: center;">
                  <img src="${userData.avatar}" alt="${userData.username}" class="user-avatar">
                  <span>${userData.username}</span>
                  ${statusIndicator}
                </div>
              `;
              userDiv.onclick = () => openChat(userId, userData.username, userData.avatar);
              usersContainer.appendChild(userDiv);
            }
          });

          document.querySelector('.auth-section').style.display = 'none';
          document.getElementById('usersList').style.display = 'block';
        }

        // فتح الدردشة مع مستخدم
        function openChat(userId, username, avatar) {
          selectedUser = { uid: userId, username, avatar };
          document.getElementById('usersList').style.display = 'none';
          document.getElementById('chatSection').style.display = 'block';
          document.getElementById('chatWith').innerHTML = `
            <img src="${avatar}" alt="${username}" class="user-avatar" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 10px;">
            ${username}
          `;
          loadMessages();
          // بدء التحديث التلقائي للرسائل كل ثانيتين
          messageInterval = setInterval(loadMessages, 2000);
        }

        // إرسال رسالة
        async function sendMessage() {
          const message = document.getElementById('messageInput').value.trim();
          if (!message || !selectedUser) return;

          const response = await fetch(`${apiUrl}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              sender: currentUser.uid,
              receiver: selectedUser.uid,
              text: message
            })
          });

          if (response.ok) {
            document.getElementById('messageInput').value = '';
            loadMessages();
          } else {
            alert('حدث خطأ أثناء إرسال الرسالة.');
          }
        }

        // تحميل الرسائل
        async function loadMessages() {
          const chatId = [currentUser.uid, selectedUser.uid].sort().join('_');
          const response = await fetch(`${apiUrl}/messages/${chatId}`);
          const messages = await response.json();

          const messagesDiv = document.getElementById('messages');
          messagesDiv.innerHTML = '';

          messages.forEach(message => {
            const isSent = message.sender === currentUser.uid;
            const avatar = isSent ? currentUser.avatar : selectedUser.avatar;

            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isSent ? 'sent' : 'received'}`;
            messageDiv.innerHTML = `
              <img src="${avatar}" alt="Avatar" class="message-avatar">
              <div class="message-text">${message.text}</div>
            `;
            messagesDiv.appendChild(messageDiv);
          });

          messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        // إغلاق الدردشة
        function closeChat() {
          document.getElementById('chatSection').style.display = 'none';
          document.getElementById('usersList').style.display = 'block';
          selectedUser = null;
          document.getElementById('messages').innerHTML = '';
          if (messageInterval) {
            clearInterval(messageInterval);
            messageInterval = null;
          }
        }
      </script>
    </body>
    </html>
    '''

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    avatar = data.get('avatar')

    if not username or not password or not avatar:
        return jsonify({'error': 'يرجى إدخال جميع الحقول'}), 400

    if username in (u['username'] for u in users.values()):
        return jsonify({'error': 'اسم المستخدم مسجل بالفعل'}), 400

    user_id = f'user_{len(users) + 1}'
    users[user_id] = {
        'username': username,
        'password': password,
        'avatar': avatar,
        'online': True
    }

    return jsonify({'userId': user_id, 'username': username, 'avatar': avatar}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = next((u for u in users.values() if u['username'] == username and u['password'] == password), None)

    if not user:
        return jsonify({'error': 'بيانات تسجيل الدخول غير صحيحة'}), 400

    user_id = next((uid for uid, u in users.items() if u['username'] == username), None)
    return jsonify({'userId': user_id, 'username': username, 'avatar': user['avatar']}), 200

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify(users), 200

@app.route('/messages', methods=['POST'])
def send_message():
    data = request.json
    sender = data.get('sender')
    receiver = data.get('receiver')
    text = data.get('text')

    if not sender or not receiver or not text:
        return jsonify({'error': 'بيانات غير كافية'}), 400

    chat_id = '_'.join(sorted([sender, receiver]))
    if chat_id not in messages:
        messages[chat_id] = []

    messages[chat_id].append({
        'sender': sender,
        'text': text,
        'timestamp': len(messages[chat_id]) + 1
    })

    return jsonify({'message': 'تم إرسال الرسالة بنجاح'}), 200

@app.route('/messages/<chat_id>', methods=['GET'])
def get_messages(chat_id):
    return jsonify(messages.get(chat_id, [])), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)