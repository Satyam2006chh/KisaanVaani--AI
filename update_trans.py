import json
import os

filepath = r"c:\Users\ASUS\OneDrive\Desktop\KisaanVaani\KisaanVaani--AI\frontend\src\translations.json"

with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

new_keys = {
    "en-IN": {
        "hero_namaste": "Hello",
        "hero_ji": "",
        "hero_subtitle": "AI-powered weather, market, and crop info — just for you.",
        "hero_mic_rec": "🔴 RECORDING — PRESS AGAIN TO STOP",
        "hero_mic_proc": "⚙️ AI IS PREPARING THE ANSWER...",
        "hero_mic_speak": "🔊 AI IS SPEAKING...",
        "hero_mic_idle": "🎙️ TAP TO SPEAK",
        "hero_img_change": "Change Photo",
        "hero_img_upload": "Crop Photo",
        "hero_img_hint": "📸 AI will analyze the crop photo",
        "chat_you": "🎤 YOU SAID",
        "chat_ai_think": "AI is thinking...",
        "chat_ai": "🤖 AI REPLY"
    },
    "hi-IN": {
        "hero_namaste": "नमस्ते",
        "hero_ji": "जी",
        "hero_subtitle": "मौसम, मंडी, और फसल की AI-पॉवर्ड जानकारी — सिर्फ आपके लिए।",
        "hero_mic_rec": "🔴 रिकॉर्डिंग — बंद करने के लिए दोबारा दबाएं",
        "hero_mic_proc": "⚙️ AI जवाब तैयार कर रहा है...",
        "hero_mic_speak": "🔊 AI बोल रहा है...",
        "hero_mic_idle": "🎙️ बोलने के लिए दबाएं",
        "hero_img_change": "फोटो बदलें",
        "hero_img_upload": "फसल की फोटो",
        "hero_img_hint": "📸 AI फसल की फोटो का विश्लेषण करेगा",
        "chat_you": "🎤 आपने कहा",
        "chat_ai_think": "AI सोच रहा है...",
        "chat_ai": "🤖 AI का जवाब"
    },
    "pa-IN": {
        "hero_namaste": "ਸਤਿ ਸ਼੍ਰੀ ਅਕਾਲ",
        "hero_ji": "ਜੀ",
        "hero_subtitle": "ਮੌਸਮ, ਮੰਡੀ ਅਤੇ ਫਸਲ ਦੀ AI-ਪਾਵਰਡ ਜਾਣਕਾਰੀ — ਸਿਰਫ਼ ਤੁਹਾਡੇ ਲਈ।",
        "hero_mic_rec": "🔴 ਰਿਕਾਰਡਿੰਗ — ਬੰਦ ਕਰਨ ਲਈ ਦੁਬਾਰਾ ਦਬਾਓ",
        "hero_mic_proc": "⚙️ AI ਜਵਾਬ ਤਿਆਰ ਕਰ ਰਿਹਾ ਹੈ...",
        "hero_mic_speak": "🔊 AI ਬੋਲ ਰਿਹਾ ਹੈ...",
        "hero_mic_idle": "🎙️ ਬੋਲਣ ਲਈ ਦਬਾਓ",
        "hero_img_change": "ਫੋਟੋ ਬਦਲੋ",
        "hero_img_upload": "ਫਸਲ ਦੀ ਫੋਟੋ",
        "hero_img_hint": "📸 AI ਫਸਲ ਦੀ ਫੋਟੋ ਦਾ ਵਿਸ਼ਲੇਸ਼ਣ ਕਰੇਗਾ",
        "chat_you": "🎤 ਤੁਸੀਂ ਕਿਹਾ",
        "chat_ai_think": "AI ਸੋਚ ਰਿਹਾ ਹੈ...",
        "chat_ai": "🤖 AI ਦਾ ਜਵਾਬ"
    },
    "bn-IN": {
        "hero_namaste": "নমস্কার",
        "hero_ji": "মশাই",
        "hero_subtitle": "আবহাওয়া, বাজার এবং ফসলের AI-চালিত তথ্য — শুধুমাত্র আপনার জন্য।",
        "hero_mic_rec": "🔴 রেকর্ডিং — বন্ধ করতে আবার চাপুন",
        "hero_mic_proc": "⚙️ AI উত্তর তৈরি করছে...",
        "hero_mic_speak": "🔊 AI কথা বলছে...",
        "hero_mic_idle": "🎙️ কথা বলতে চাপুন",
        "hero_img_change": "ছবি পরিবর্তন করুন",
        "hero_img_upload": "ফসলের ছবি",
        "hero_img_hint": "📸 AI ফসলের ছবি বিশ্লেষণ করবে",
        "chat_you": "🎤 আপনি বলেছেন",
        "chat_ai_think": "AI ভাবছে...",
        "chat_ai": "🤖 AI উত্তর"
    },
    "ta-IN": {
        "hero_namaste": "வணக்கம்",
        "hero_ji": "அவர்களே",
        "hero_subtitle": "வானிலை, சந்தை மற்றும் பயிர் குறித்த AI தகவல்கள் — உங்களுக்காகவே.",
        "hero_mic_rec": "🔴 பதிவு செய்யப்படுகிறது — நிறுத்த மீண்டும் அழுத்தவும்",
        "hero_mic_proc": "⚙️ AI பதிலை தயார் செய்கிறது...",
        "hero_mic_speak": "🔊 AI பேசுகிறது...",
        "hero_mic_idle": "🎙️ பேச அழுத்தவும்",
        "hero_img_change": "புகைப்படத்தை மாற்று",
        "hero_img_upload": "பயிர் புகைப்படம்",
        "hero_img_hint": "📸 AI பயிர் புகைப்படத்தை பகுப்பாய்வு செய்யும்",
        "chat_you": "🎤 நீங்கள் கூறியது",
        "chat_ai_think": "AI யோசிக்கிறது...",
        "chat_ai": "🤖 AI பதில்"
    },
    "te-IN": {
        "hero_namaste": "నమస్కారం",
        "hero_ji": "గారు",
        "hero_subtitle": "వాతావరణం, మార్కెట్ మరియు పంటల AI సమాచారం — మీ కోసమే.",
        "hero_mic_rec": "🔴 రికార్డింగ్ — ఆపడానికి మళ్లీ నొక్కండి",
        "hero_mic_proc": "⚙️ AI సమాధానం సిద్ధం చేస్తోంది...",
        "hero_mic_speak": "🔊 AI మాట్లాడుతోంది...",
        "hero_mic_idle": "🎙️ మాట్లాడటానికి నొక్కండి",
        "hero_img_change": "ఫోటో మార్చండి",
        "hero_img_upload": "పంట ఫోటో",
        "hero_img_hint": "📸 AI పంట ఫోటోను విశ్లేషిస్తుంది",
        "chat_you": "🎤 మీరు చెప్పారు",
        "chat_ai_think": "AI ఆలోచిస్తోంది...",
        "chat_ai": "🤖 AI సమాధానం"
    },
    "kn-IN": {
        "hero_namaste": "ನಮಸ್ಕಾರ",
        "hero_ji": "ಅವರೇ",
        "hero_subtitle": "ಹವಾಮಾನ, ಮಾರುಕಟ್ಟೆ ಮತ್ತು ಬೆಳೆಯ AI ಮಾಹಿತಿ — ನಿಮಗಾಗಿ ಮಾತ್ರ.",
        "hero_mic_rec": "🔴 ರೆಕಾರ್ಡಿಂಗ್ — ನಿಲ್ಲಿಸಲು ಮತ್ತೆ ಒತ್ತಿರಿ",
        "hero_mic_proc": "⚙️ AI ಉತ್ತರ ಸಿದ್ಧಪಡಿಸುತ್ತಿದೆ...",
        "hero_mic_speak": "🔊 AI ಮಾತನಾಡುತ್ತಿದೆ...",
        "hero_mic_idle": "🎙️ ಮಾತನಾಡಲು ಒತ್ತಿರಿ",
        "hero_img_change": "ಫೋಟೋ ಬದಲಾಯಿಸಿ",
        "hero_img_upload": "ಬೆಳೆಯ ಫೋಟೋ",
        "hero_img_hint": "📸 AI ಬೆಳೆಯ ಫೋಟೋವನ್ನು ವಿಶ್ಲೇಷಿಸುತ್ತದೆ",
        "chat_you": "🎤 ನೀವು ಹೇಳಿದ್ದೀರಿ",
        "chat_ai_think": "AI ಯೋಚಿಸುತ್ತಿದೆ...",
        "chat_ai": "🤖 AI ಉತ್ತರ"
    },
    "ml-IN": {
        "hero_namaste": "നമസ്കാരം",
        "hero_ji": "",
        "hero_subtitle": "കാലാവസ്ഥ, മാർക്കറ്റ്, വിളകൾ എന്നിവയുടെ AI വിവരങ്ങൾ — നിങ്ങൾക്കായി.",
        "hero_mic_rec": "🔴 റെക്കോർഡിംഗ് — നിർത്താൻ വീണ്ടും അമർത്തുക",
        "hero_mic_proc": "⚙️ AI മറുപടി തയ്യാറാക്കുന്നു...",
        "hero_mic_speak": "🔊 AI സംസാരിക്കുന്നു...",
        "hero_mic_idle": "🎙️ സംസാരിക്കാൻ അമർത്തുക",
        "hero_img_change": "ഫോട്ടോ മാറ്റുക",
        "hero_img_upload": "വിളയുടെ ഫോട്ടോ",
        "hero_img_hint": "📸 AI വിളയുടെ ഫോട്ടോ വിശകലനം ചെയ്യും",
        "chat_you": "🎤 നിങ്ങൾ പറഞ്ഞു",
        "chat_ai_think": "AI ചിന്തിക്കുന്നു...",
        "chat_ai": "🤖 AI മറുപടി"
    },
    "mr-IN": {
        "hero_namaste": "नमस्कार",
        "hero_ji": "जी",
        "hero_subtitle": "हवामान, बाजार आणि पिकांची AI-आधारित माहिती — फक्त तुमच्यासाठी.",
        "hero_mic_rec": "🔴 रेकॉर्डिंग — थांबवण्यासाठी पुन्हा दाबा",
        "hero_mic_proc": "⚙️ AI उत्तर तयार करत आहे...",
        "hero_mic_speak": "🔊 AI बोलत आहे...",
        "hero_mic_idle": "🎙️ बोलण्यासाठी दाबा",
        "hero_img_change": "फोटो बदला",
        "hero_img_upload": "पिकाचा फोटो",
        "hero_img_hint": "📸 AI पिकाच्या फोटोचे विश्लेषण करेल",
        "chat_you": "🎤 तुम्ही म्हणालात",
        "chat_ai_think": "AI विचार करत आहे...",
        "chat_ai": "🤖 AI चे उत्तर"
    },
    "gu-IN": {
        "hero_namaste": "નમસ્તે",
        "hero_ji": "જી",
        "hero_subtitle": "હવામાન, બજાર અને પાકની AI-આધારિત માહિતી — માત્ર તમારા માટે.",
        "hero_mic_rec": "🔴 રેકોર્ડિંગ — બંધ કરવા ફરીથી દબાવો",
        "hero_mic_proc": "⚙️ AI જવાબ તૈયાર કરી રહ્યું છે...",
        "hero_mic_speak": "🔊 AI બોલી રહ્યું છે...",
        "hero_mic_idle": "🎙️ બોલવા માટે દબાવો",
        "hero_img_change": "ફોટો બદલો",
        "hero_img_upload": "પાકનો ફોટો",
        "hero_img_hint": "📸 AI પાકના ફોટાનું વિશ્લેષણ કરશે",
        "chat_you": "🎤 તમે કહ્યું",
        "chat_ai_think": "AI વિચારી રહ્યું છે...",
        "chat_ai": "🤖 AI નો જવાબ"
    },
    "od-IN": {
        "hero_namaste": "ନମସ୍କାର",
        "hero_ji": "ଆଜ୍ଞା",
        "hero_subtitle": "ପାଣିପାଗ, ବଜାର ଏବଂ ଫସଲର AI-ଆଧାରିତ ସୂଚନା — କେବଳ ଆପଣଙ୍କ ପାଇଁ।",
        "hero_mic_rec": "🔴 ରେକର୍ଡିଂ — ବନ୍ଦ କରିବାକୁ ପୁଣି ଦବାନ୍ତୁ",
        "hero_mic_proc": "⚙️ AI ଉତ୍ତର ପ୍ରସ୍ତୁତ କରୁଛି...",
        "hero_mic_speak": "🔊 AI କହୁଛି...",
        "hero_mic_idle": "🎙️ କହିବାକୁ ଦବାନ୍ତୁ",
        "hero_img_change": "ଫଟୋ ବଦଳାନ୍ତୁ",
        "hero_img_upload": "ଫସଲର ଫଟୋ",
        "hero_img_hint": "📸 AI ଫସଲ ଫଟୋ ବିଶ୍ଳେଷଣ କରିବ",
        "chat_you": "🎤 ଆପଣ କହିଲେ",
        "chat_ai_think": "AI ଭାବୁଛି...",
        "chat_ai": "🤖 AI ର ଉତ୍ତର"
    },
    "as-IN": {
        "hero_namaste": "নমস্কাৰ",
        "hero_ji": "ডাঙৰীয়া",
        "hero_subtitle": "বতৰ, বজাৰ আৰু শস্যৰ AI-ভিত্তিক তথ্য — কেৱল আপোনাৰ বাবে।",
        "hero_mic_rec": "🔴 ৰেকৰ্ডিং — বন্ধ কৰিবলৈ আকৌ টিপক",
        "hero_mic_proc": "⚙️ AI উত্তৰ প্ৰস্তুত কৰি আছে...",
        "hero_mic_speak": "🔊 AI কৈ আছে...",
        "hero_mic_idle": "🎙️ ক'বলৈ টিপক",
        "hero_img_change": "ফটো সলনি কৰক",
        "hero_img_upload": "শস্যৰ ফটো",
        "hero_img_hint": "📸 AI শস্যৰ ফটো বিশ্লেষণ কৰিব",
        "chat_you": "🎤 আপুনি ক'লে",
        "chat_ai_think": "AI ভাবি আছে...",
        "chat_ai": "🤖 AI ৰ উত্তৰ"
    }
}

for lang, keys in new_keys.items():
    if lang not in data:
        data[lang] = {}
    for k, v in keys.items():
        data[lang][k] = v

with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Translations updated successfully.")
