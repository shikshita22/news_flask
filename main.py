from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os
from textblob import TextBlob
import spacy
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

app = Flask(__name__, template_folder=".")
app.secret_key = "supersecretkey"

nlp = spacy.load("en_core_web_sm")

@app.route("/style.css")
def style():
    return send_from_directory(os.path.dirname(__file__), "style.css")

@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    next_page = request.args.get("next", url_for("home"))
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "123":
            session["authenticated"] = True
            return redirect(next_page)
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    if not session.get("authenticated"):
        return redirect(url_for("login", next=url_for("analyze")))

    mode = request.args.get("mode", "sentiment")
    result = None
    text = ""

    if request.method == "POST":
        text = request.form.get("news_content", "")
        session["last_text"] = text  # store text in session

        # --- Sentiment ---
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # value between -1 and 1
        if polarity > 0:
            sentiment_result = "Positive"
        elif polarity < 0:
            sentiment_result = "Negative"
        else:
            sentiment_result = "Neutral"

        # --- Keywords ---
        doc = nlp(text)
        keywords_result = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop]


        # --- Summary ---
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary_sentences = summarizer(parser.document, sentences_count=3)
        summary_result = " ".join(str(sentence) for sentence in summary_sentences)

        # ✅ Include polarity in result
        result = {
            "sentiment": sentiment_result,
            "polarity": polarity,  # <--- ADDED THIS
            "keywords": ", ".join(keywords_result),
            "summary": summary_result
        }

        session["last_result"] = result  # store results in session

    elif session.get("last_text") and session.get("last_result"):
        # If GET request and user clicks mode, use last analyzed result
        result = session["last_result"]

    return render_template("analyze.html", result=result, mode=mode, news_content=text)


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/logout")
def logout():
    session.pop("authenticated", None)
    session.pop("last_text", None)
    session.pop("last_result", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
