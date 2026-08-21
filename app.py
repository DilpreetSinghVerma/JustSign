# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, Response, send_from_directory, g, jsonify
from urllib.parse import quote_plus, unquote_plus
from nltk.tokenize import sent_tokenize
import os
import re
import json
import datetime
import logging
import pickle
import numpy as np
from collections import Counter

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from logics.chunker import chunkerserver
from logics.converter import complexToSimple
from logics.compoundconverter import compoundToSimple
from logics.simpleconverter import simpleToISL
from logics.discover import getSentenceType
from logics.sigml.sigml import hamNoSysToSigml
from logics.punjabi.punjabi import punjabiToISL
from logics.isldictionary import getCategories, getElements, searchElements
from logics.announcements.listAnnouncements import staticAnnouncements, airportStaticAnnouncements
from logics import providers
import logics
from logics import users

# ---- Config ----
enable_registerations = False  # matches how register_page uses it

from flask_cors import CORS

app: Flask = Flask(__name__)
CORS(app)  # Enable CORS for all routes to fix React integration
# secrets should come from env in production
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "thisissomethingsecret")
app.jinja_env.filters['quote_plus'] = lambda u: quote_plus(u)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure NLTK punkt is available. If it's not, attempt to download it, and fall back gracefully later.
try:
    # Try a small sample to force resource usage/lookup
    sent_tokenize("Test sentence.")
except LookupError:
    import nltk

    try:
        nltk.download('punkt')
        logger.info("Downloaded NLTK punkt tokenizer.")
    except Exception as e:
        logger.warning("Could not download NLTK punkt tokenizer automatically: %s", e)


# ---- Helpers ----
def safe_sent_tokenize(text):
    """
    Use nltk.sent_tokenize if available; otherwise fall back to a simple split by punctuation.
    Returns list of sentences (stripped).
    """
    if not text:
        return []
    try:
        sents = sent_tokenize(text)
        return [s.strip() for s in sents if s.strip()]
    except Exception:
        # fallback: split on . ? ! and newlines
        parts = re.split(r'[.!?\n]+', text)
        return [p.strip() for p in parts if p.strip()]


# ---- Routes ----
@app.route('/')
def homepage():
    users.logged_in()
    return render_template("homepage.html")


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    users.logged_in()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username and password:
            users.login(username, password)
            if users.logged_in():
                flash("You have successfully logged in.", "success")
                return redirect(url_for("homepage"))
            else:
                flash("Invalid Email or Password.", "danger")
        else:
            flash("Kindly fill in your Email Address and Password.", "danger")
    return render_template("login.html")


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    users.logged_in()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirmpassword = request.form.get("confirmpassword", "")
        if username and password and confirmpassword:
            if password == confirmpassword:
                users.register(username, password)
            else:
                flash("Passwords do not match.", "danger")
        else:
            flash("Kindly fill in your Email Address, Password and Confirm Password.", "danger")
    return render_template("register.html", disabled=not enable_registerations)


@app.route('/logout')
def logout_page():
    return users.logout()  # logout() already redirects


@app.route('/about')
def about():
    users.logged_in()
    return render_template("about.html")


@app.route('/chunker', methods=['GET', 'POST'])
@users.login_required
def chunker():
    if request.method == "POST":
        rawtext = request.form.get('rawtext', '')
        result = chunkerserver(rawtext)
        return render_template("chunker.html", input=result["text"].split('\n'), results=result["result"].split('\n'))
    return render_template("chunker.html")


prereplacements = {
    "’": "'",
    "‘": "'",
    "\u00A0": " ",
    "“": "\"",
    "”": "\"",
    ";": ",",
    "\"": "",
}


@app.route('/convert', methods=['GET', 'POST'])
@users.login_required
def converter():
    if request.method == "POST":
        rawtext = request.form.get('rawtext', '')
        for old, new in prereplacements.items():
            rawtext = rawtext.replace(old, new)
        raw = rawtext.split("\r\n")
        partial = [x.strip() for x in raw if x.strip()]
        preprocessed = []
        for x in partial:
            preprocessed.extend(safe_sent_tokenize(x))
        result = None
        typeof = request.form.get('submit', "ComplexToSimple")
        if typeof == "AutoDetectToISL":
            result = []
            for x in preprocessed:
                if x.strip():
                    complexResult = complexToSimple(x.strip())
                    if complexResult[1]:
                        result.append("Simple: \t" + complexResult[0])
                        result.append("ISL: \t\t" + simpleToISL(complexResult[0])[0])
                    else:
                        compoundResult = compoundToSimple(x.strip())
                        if compoundResult[1]:
                            result.append("Simple: \t" + compoundResult[0])
                            result.append("ISL: \t\t" + simpleToISL(compoundResult[0])[0])
                        else:
                            result.append("Simple: \t" + x.strip())
                            result.append("ISL: \t\t" + simpleToISL(x.strip())[0])
                    result.append("======================")
        elif typeof == "ComplexToSimple":
            result = [complexToSimple(x.strip(), debug=True)[0] for x in preprocessed if x.strip()]
        elif typeof == "compoundToSimple":
            result = [compoundToSimple(x.strip(), debug=True)[0] for x in preprocessed if x.strip()]
        elif typeof == "CompoundToISL":
            result = [simpleToISL(compoundToSimple(x.strip())[0])[0] for x in preprocessed if x.strip()]
        elif typeof == "ComplexToISL":
            result = [simpleToISL(complexToSimple(x.strip())[0])[0] for x in preprocessed if x.strip()]
        elif typeof == "SimpleToISL":
            result = [simpleToISL(x.strip())[0] for x in preprocessed if x.strip()]
        elif typeof == "GetSentenceType":
            result = [getSentenceType(x.strip()) for x in preprocessed if x.strip()]

        if result:
            return render_template("converter.html", input="\r\n".join(raw), results="\r\n".join(result), type=typeof)
        else:
            flash(f"Method {typeof} not Supported yet.", "danger")
            return render_template("converter.html", input="\r\n".join(raw))
    return render_template("converter.html")


@app.route('/announcements')
@users.login_required
def announcements():
    return render_template("player.html", frame="announcement-text")


@app.route('/airports')
@users.login_required
def airports():
    return render_template("player.html", frame="airport-text")


@app.route('/player')
@users.login_required
def player():
    return render_template("player.html", frame="player-text")


@app.route('/dictionary')
@users.login_required
def dictionary():
    return render_template("player.html", frame="dictionary-text")


@app.route('/dictionarywithvideo')
@users.login_required
def dictionarywithvideo():
    return render_template("playervideo.html", frame="dictionary-text-video")


@app.route('/player-applet')
def playerApplet():
    return render_template("player-applet.html")


@app.route('/player-video')
def playerVideo():
    return render_template("player-video.html")


@app.route('/dictionary-text', methods=['GET', 'POST'])
def dictionaryText():
    q = request.args.get("search", None)
    cat = request.args.get("category", None)
    if q:
        search = searchElements(q)
        if search:
            return render_template("dictionary-text.html", search=search, searchTerm=q)
        else:
            return render_template("dictionary-text.html", categories=getCategories(), searchTerm=q)
    elif cat:
        if cat in getCategories():
            return render_template("dictionary-text.html", category=cat, elements=getElements(cat))
        else:
            flash("Invalid Category.", "danger")
    return render_template("dictionary-text.html", categories=getCategories())


@app.route('/dictionary-text-video', methods=['GET', 'POST'])
def dictionaryTextVideo():
    q = request.args.get("search", None)
    cat = request.args.get("category", None)
    if q:
        search = searchElements(q)
        if search:
            return render_template("dictionary-text.html", search=search, searchTerm=q, video=True)
        else:
            return render_template("dictionary-text.html", categories=getCategories(), searchTerm=q, video=True)
    elif cat:
        if cat in getCategories():
            return render_template("dictionary-text.html", category=cat, elements=getElements(cat), video=True)
        else:
            flash("Invalid Category.", "danger")
    return render_template("dictionary-text.html", categories=getCategories(), video=True)


@app.route('/announcement-text', methods=['GET', 'POST'])
def announcementText():
    if request.method == "POST":
        special = request.form.get("special", None)
        if special:
            announcement = f"{special}"
        else:
            announcement_type = request.form.get("Annoucements", None)
            announcement_platform = request.form.get("number", None)
            announcement_hour = request.form.get("hour", None)
            announcement_minute = request.form.get("minute", None)
            if not all([announcement_type, announcement_platform, announcement_hour, announcement_minute]):
                flash("Kindly fill all the required data for Dynamic Announcements", "danger")
                return render_template("announcement-text.html", static_announcements=staticAnnouncements())
            announcement = (f"announcement_type:{announcement_type.strip()}-"
                            f"announcement_platform:{announcement_platform.strip()}-"
                            f"announcement_hour:{announcement_hour.strip()}-"
                            f"announcement_minute:{announcement_minute.strip()}")
        return render_template("announcement-text.html", static_announcements=staticAnnouncements(),
                               announcement=announcement)
    return render_template("announcement-text.html", static_announcements=staticAnnouncements())


@app.route('/airport-text', methods=['GET', 'POST'])
def airportText():
    if request.method == "POST":
        special = request.form.get("special", None)
        if special:
            announcement = f"{special}"
            return render_template("airport-text.html", static_announcements=airportStaticAnnouncements(),
                                   announcement=announcement)
        else:
            if not request.form.get("announcement", None):
                flash("Please Select Announcement to Continue.", "danger")
            else:
                with open("static/airport-dynamic"
                          ".json", encoding="utf-8") as inpf:
                    data = json.load(inpf)
                announcement = None
                for d in data:
                    if d.get("eng-dynamic") == request.form["announcement"]:
                        announcement = d
                        break
                if not announcement:
                    flash("Invalid Announcement.", "danger")
                    return render_template("airport-text.html", static_announcements=airportStaticAnnouncements())
                else:
                    depends = announcement.get("depends", [])
                    for d in depends:
                        if request.form.get(d, "").strip() == "":
                            flash("Kindly fill all the required details by announcement.", "danger")
                            return render_template("airport-text.html",
                                                   static_announcements=airportStaticAnnouncements())
                    announcement_isl = announcement.get("isl-dynamic", "").lower()
                    for d in depends:
                        announcement_isl = re.sub(r"\{\{\s*%s\s*\}\}" % re.escape(d), request.form[d].strip(),
                                                  announcement_isl)
                    announcement_isl = re.sub(r"[\\/]+", " ", announcement_isl)
                    return render_template("airport-text.html", static_announcements=airportStaticAnnouncements(),
                                           announcement=announcement_isl)
    return render_template("airport-text.html", static_announcements=airportStaticAnnouncements())


@app.route('/player-text', methods=['GET', 'POST'])
def playerText():
    if request.method == "POST":
        rawtext = request.form.get('rawtext', '')
        for old, new in prereplacements.items():
            rawtext = rawtext.replace(old, new)
        raw = rawtext.split("\r\n")
        partial = [x.strip() for x in raw if x.strip()]
        preprocessed = []
        for x in partial:
            preprocessed.extend(safe_sent_tokenize(x))
        result = None
        typeof = request.form.get('submit', "ComplexToSimple")
        if typeof == "AutoDetectToISL":
            result = []
            for x in preprocessed:
                if x.strip():
                    complexResult = complexToSimple(x.strip())
                    if complexResult[1]:
                        result.append(simpleToISL(complexResult[0])[0])
                    else:
                        compoundResult = compoundToSimple(x.strip())
                        if compoundResult[1]:
                            result.append(simpleToISL(compoundResult[0])[0])
                        else:
                            result.append(simpleToISL(x.strip())[0])
        elif typeof == "CompoundToISL":
            result = [simpleToISL(compoundToSimple(x.strip())[0])[0] for x in preprocessed if x.strip()]
        elif typeof == "ComplexToISL":
            result = [simpleToISL(complexToSimple(x.strip())[0])[0] for x in preprocessed if x.strip()]
        elif typeof == "SimpleToISL":
            result = [simpleToISL(x.strip())[0] for x in preprocessed if x.strip()]
        if result:
            return render_template("player-text.html", input="\r\n".join(raw), results="\r\n".join(result), type=typeof)
        else:
            flash(f"Method {typeof} not Supported yet.", "danger")
            return render_template("player-text.html", input="\r\n".join(raw))
    return render_template("player-text.html")


@app.route("/api/v1/converter", methods=['GET', 'POST'])
def apiv1():
    response = {}
    if request.method == "POST":
        data = request.get_json(silent=True) or dict(request.form)
        if data:
            text = data.get("text", None)
            action = data.get("action", None)
            result = None
            if text and action:
                raw = text.split("\r\n") if "\r\n" in text else text.split("\n")
                partial = [x.strip() for x in raw if x.strip()]
                preprocessed = []
                for x in partial:
                    preprocessed.extend(safe_sent_tokenize(x))
                if action == "AutoDetectToISL":
                    result = []
                    for x in preprocessed:
                        if x.strip():
                            complexResult = complexToSimple(x.strip())
                            if complexResult[1]:
                                result.append(simpleToISL(complexResult[0])[0])
                            else:
                                compoundResult = compoundToSimple(x.strip())
                                if compoundResult[1]:
                                    result.append(simpleToISL(compoundResult[0])[0])
                                else:
                                    result.append(simpleToISL(x.strip())[0])
                elif action == "ComplexToSimple":
                    result = [complexToSimple(x.strip(), debug=True)[0] for x in preprocessed if x.strip()]
                elif action == "compoundToSimple":
                    result = [compoundToSimple(x.strip(), debug=True)[0] for x in preprocessed if x.strip()]
                elif action == "CompoundToISL":
                    result = [simpleToISL(compoundToSimple(x.strip())[0])[0] for x in preprocessed if x.strip()]
                elif action == "ComplexToISL":
                    result = [simpleToISL(complexToSimple(x.strip())[0])[0] for x in preprocessed if x.strip()]
                elif action == "SimpleToISL":
                    result = [simpleToISL(x.strip())[0] for x in preprocessed if x.strip()]
                elif action == "GetSentenceType":
                    result = [getSentenceType(x.strip()) for x in preprocessed if x.strip()]

                if result:
                    response["text"] = text
                    response["action"] = action
                    response["result"] = "\n".join(result).strip()
                    response["timestamp"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                else:
                    response["error"] = f"The action {action} doesn't exist."
                    response["timestamp"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    if not response:
        response["error"] = "Kindly use the documentation to query this API."
        response["timestamp"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    res = jsonify(response)
    # Allow cross origin requests for API
    res.headers["Access-Control-Allow-Origin"] = "*"
    return res

# Load ML Model
sign_model = None
try:
    model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sign_model.pkl")
    if os.path.exists(model_path):
        with open(model_path, "rb") as f:
            sign_model = pickle.load(f)
        logger.info("Successfully loaded ML model from sign_model.pkl")
except Exception as e:
    logger.error("Could not load sign_model.pkl: %s", e)

@app.route("/api/v1/recognize_sign", methods=['POST'])
def recognize_sign():
    data = request.get_json(silent=True)
    if not data or "landmarks" not in data or len(data["landmarks"]) == 0:
        return jsonify({"error": "No landmarks provided"}), 400
    
    predicted_word = "Unknown"
    
    if sign_model:
        predictions = []
        for frame in data["landmarks"]:
            features = np.zeros(126)
            for idx, hand in enumerate(frame):
                if idx >= 2: break
                offset = idx * 63
                for lm_idx, lm in enumerate(hand):
                    pos = offset + (lm_idx * 3)
                    features[pos] = lm.get('x', 0)
                    features[pos+1] = lm.get('y', 0)
                    features[pos+2] = lm.get('z', 0)
            pred = sign_model.predict([features])[0]
            predictions.append(pred)
            
        most_common = Counter(predictions).most_common(1)
        if most_common:
            predicted_word = most_common[0][0].capitalize()
    else:
        # Fallback if model not trained
        predicted_word = "Hello (Mock)"
    
    response = jsonify({
        "recognized": predicted_word,
        "confidence": 0.95,
        "timestamp": datetime.datetime.now().isoformat()
    })
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.route("/api/v1/dictionary", methods=['GET'])
def get_dictionary_words():
    sign_dir = os.path.join(os.path.dirname(__file__), "SignFiles")
    if not os.path.exists(sign_dir):
        sign_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "SignFiles")
    words = []
    if os.path.exists(sign_dir):
        for f in os.listdir(sign_dir):
            if f.endswith(".sigml"):
                # Clean up filename for display
                words.append(f.replace(".sigml", "").replace("_", " "))
    
    response = jsonify({"words": sorted(words)})
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.route('/punjabi', methods=['GET', 'POST'])
@users.login_required
def punjabihome():
    if request.method == "POST":
        rawtext = request.form.get('rawtext', '')
        raw = rawtext.split("\r\n")
        preprocessed = [x.strip() for x in raw if x.strip()]
        result = [punjabiToISL(x.strip()) for x in preprocessed if x.strip()]
        if result:
            return render_template("punjabi.html", input="\r\n".join(raw), results="\r\n".join(result),
                                   type="punjabiToISL")
        else:
            flash("Error Processing Document.", "danger")
            return render_template("punjabi.html", input="\r\n".join(raw))
    return render_template("punjabi.html")


@app.route('/languages/<string:filename>')
def punjabilanguage(filename):
    # Serve files for download (attachment)
    return send_from_directory("static/languages", filename, as_attachment=True)


@app.route('/sigmlprovider/<string:text>')
def sigmlProvider(text):
    return providers.sigmlProvider(unquote_plus(text))


@app.route('/railwayprovider/<string:text>')
def railwayProvider(text):
    return providers.railwayProvider(unquote_plus(text))


@app.route('/airportprovider/<string:text>')
def airportProvider(text):
    return providers.airportProvider(unquote_plus(text))


@app.route('/dictionaryprovider/<string:text>')
def dictionaryProvider(text):
    return providers.dictionaryProvider(unquote_plus(text))


@app.route('/dictionarvideoyprovider/<string:text>')
def dictionaryVideoProvider(text):
    return providers.dictionaryVideoProvider(unquote_plus(text))


@app.route('/favicon.ico')
def favicon():
    # Do not force attachment for favicon
    return send_from_directory("static/favicon", "favicon.ico", as_attachment=False)


@app.route('/sigml', methods=['GET', 'POST'])
@users.login_required
def sigml():
    if request.method == "POST":
        rawtext = request.form.get('rawtext', '')
        result = hamNoSysToSigml(rawtext)
        return render_template("sigml.html", input=rawtext.split("\n"), results=result.split("\n"))
    return render_template("sigml.html")


@app.route('/ar-interpreter')
@users.login_required
def ar_interpreter():
    return render_template("ar-interpreter.html")


if __name__ == "__main__":
    # Set host/port/debug via env for production
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),
            debug=os.environ.get("FLASK_DEBUG", "False") == "True")
