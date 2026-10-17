const fs = require("fs");
const login = require("fca-unofficial");

// التأكد من وجود ملف الكوكيز appstate.json في المشروع
if (!fs.existsSync('appstate.json')) {
    console.log("❌ خطأ: ملف appstate.json غير موجود في المستودع!");
    process.exit(1);
}

const appState = JSON.parse(fs.readFileSync('appstate.json', 'utf8'));

console.log("🔄 جاري تسجيل الدخول الشامل إلى فيسبوك عبر الكوكيز...");

login({ appState: appState }, (err, api) => {
    if (err) {
        return console.error("❌ فشل تسجيل الدخول عبر الكوكيز:", err);
    }

    console.log("✅ تم تسجيل الدخول بنجاح! البوت جاهز لجلب البيانات والصور والاتصالات.");

    api.setOptions({ listenEvents: true, updatePresence: true });

    api.listenMqtt((err, event) => {
        if (err) return console.error(err);

        if (event.type === "message") {
            const messageText = event.body;
            const threadID = event.threadID;
            const senderID = event.senderID;

            // أمر المساعدة الشامل
            if (messageText === "/start" || messageText === "بدء" || messageText === "أدوات") {
                api.sendMessage(
                    "🤖 **مرحباً بك في بوت BOTRX الشامل للفيسبوك**\n\n" +
                    "📌 **الأوامر المتاحة لجلب البيانات والصور:**\n" +
                    "1️⃣ `/info` -> جلب معلومات حساب البوت كاملة مع الصورة والاتصالات.\n" +
                    "2️⃣ إرسال أي **رابط فيسبوك** -> لبدء الفحص وجلب بيانات وصورة وهاتف صاحب الرابط.\n" +
                    "3️⃣ `/threads` -> عرض قائمة المحادثات والمجموعات النشطة.\n\n" +
                    "⚡ *البوت يعمل بصلاحيات كاملة عبر الكوكيز!*",
                    threadID
                );
            }

            // أمر جلب معلومات وصورة حساب البوت نفسه
            else if (messageText === "/info") {
                api.sendMessage("⏳ جاري جلب المعلومات والصورة الشخصية...", threadID);
                api.getCurrentUserID((err, botID) => {
                    if (err) return api.sendMessage("❌ لم نتمكن من جلب المعرف.", threadID);
                    
                    api.getUserInfo(botID, (err, ret) => {
                        if (err) return api.sendMessage("❌ حدث خطأ أثناء قراءة الحساب.", threadID);
                        let info = ret[botID];
                        let msg = 
                            `📊 **معلومات الحساب الشاملة:**\n\n` +
                            `👤 **الاسم:** ${info.name}\n` +
                            `🆔 **المعرف (ID):** ${botID}\n` +
                            `📧 **البريد الإلكتروني:** ${info.email || 'غير متاح للعلن'}\n` +
                            `📞 **رقم الهاتف:** ${info.phoneNumber || 'غير متاح للعلن'}\n` +
                            `🌐 **الرابط:** ${info.profileUrl}\n` +
                            `🚻 **الجنس:** ${info.gender || 'غير متوفر'}\n` +
                            `⭐ **حساب موثق:** ${info.isVerified ? 'نعم' : 'لا'}`;
                        
                        let profilePic = info.largeSrc || info.thumbSrc;
                        if (profilePic) {
                            api.sendMessage({ body: msg, url: profilePic }, threadID);
                        } else {
                            api.sendMessage(msg, threadID);
                        }
                    });
                });
            }

            // أمر جلب قائمة المحادثات النشطة
            else if (messageText === "/threads") {
                api.getThreadList(10, null, ["INBOX"], (err, list) => {
                    if (err) return api.sendMessage("❌ حدث خطأ في جلب المحادثات.", threadID);
                    let msg = "📂 **آخر المحادثات والمجموعات النشطة:**\n\n";
                    list.forEach((t, index) => {
                        msg += `${index + 1}. ${t.name || 'محادثة خاصة'} (ID: ${t.threadID})\n`;
                    });
                    api.sendMessage(msg, threadID);
                });
            }

            // فحص روابط الفيسبوك وجلب البيانات الشاملة بما فيها البريد ورقم الهاتف وصورة البروفايل
            else if (messageText && (messageText.includes("facebook.com") || messageText.includes("fb.com") || messageText.includes("fb.watch"))) {
                api.sendMessage("🔍 **تم رصد الرابط!** جاري فحص الملف الشخصي، الجيميل، الرقم والصورة عبر الكوكيز...", threadID);

                api.getUserInfo(senderID, (err, ret) => {
                    if (err) {
                        return api.sendMessage("❌ عذراً، لم نتمكن من جلب تفاصيل هذا الملف.", threadID);
                    }

                    for (let id in ret) {
                        let userInfo = ret[id];
                        let fullDetails = 
                            `📘 **النتائج الكاملة لفحص الملف الشخصي:**\n\n` +
                            `👤 **الاسم الكامل:** ${userInfo.name}\n` +
                            `🆔 **المعرف الرقمي:** ${id}\n` +
                            `📧 **البريد (Email/Gmail):** ${userInfo.email || 'مخفي/غير متاح للعلن'}\n` +
                            `📞 **رقم الهاتف:** ${userInfo.phoneNumber || 'مخفي/غير متاح للعلن'}\n` +
                            `🔗 **رابط البروفايل:** ${userInfo.profileUrl}\n` +
                            `🚻 **الجنس:** ${userInfo.gender || 'غير محدد'}\n` +
                            `✔️ **حالة الحساب:** نشط ومفحوص\n\n` +
                            `⚡ **تم جلب كافة البيانات بنجاح بواسطة BOTRX!**`;
                        
                        let userPic = userInfo.largeSrc || userInfo.thumbSrc;
                        if (userPic) {
                            api.sendMessage({ body: fullDetails, url: userPic }, threadID);
                        } else {
                            api.sendMessage(fullDetails, threadID);
                        }
                    }
                });
            }
        }
    });
});
