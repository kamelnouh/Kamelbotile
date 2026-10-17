const express = require('express');
const login = require('fca-unofficial');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// 1. خادم Web لضمان بقاء البوت شغالاً على Replit بدون توقف (Uptime)
app.get('/', (req, res) => {
  res.send('Server is running! FB Bot is Active.');
});

app.listen(PORT, () => {
  console.log(`[SERVER] Web server started on port ${PORT}`);
});

// 2. التحقق من وجود ملف الجلسة appstate.json
if (!fs.existsSync('./appstate.json')) {
  console.error('[ERROR] File appstate.json is missing! Please add your Facebook session.');
  process.exit(1);
}

let appState;
try {
  appState = JSON.parse(fs.readFileSync('./appstate.json', 'utf8'));
} catch (err) {
  console.error('[ERROR] Failed to parse appstate.json. Make sure it is valid JSON format.');
  process.exit(1);
}

// 3. خيارات الاتصال المتوافقة مع أحدث حمايات فيسبوك
const loginOptions = {
  appState: appState
};

// 4. تسجيل الدخول وتشغيل البوت
login(loginOptions, (err, api) => {
  if (err) {
    console.error('[FB LOGIN ERROR] Connection failed:', err);
    console.log('[TIP] Extract a new fresh appstate.json from your browser and confirm "This was me" on Facebook.');
    return;
  }

  // ضبط إعدادات الاستماع للرسائل
  api.setOptions({
    listenEvents: true,
    selfListen: false,
    logLevel: "silent"
  });

  console.log('[FB BOT] Successfully connected to Facebook Messenger!');

  // الاستماع للرسائل الواردة والرد عليها
  api.listenMqtt((err, event) => {
    if (err) {
      console.error('[MQTT ERROR]', err);
      return;
    }

    // التعامل مع الرسائل النصية
    if (event.type === "message" && event.body) {
      const messageText = event.body.toLowerCase().trim();

      // تجربة رد بسيط عند كتابة ping أو ping/
      if (messageText === 'ping' || messageText === '/ping') {
        api.sendMessage('Pong! 🏓 البوت شغال بنجاح على Replit.', event.threadID, event.messageID);
      }
    }
  });
});
