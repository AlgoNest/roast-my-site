from flask import Flask, render_template, request
from services.roast_service import roast_url

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not url:
            return render_template("index.html", error="Please enter a URL")

        roast_result = roast_url(url)
        if "error" in roast_result:
            return render_template("index.html", error=roast_result["error"])

        return render_template("result.html", url=url, roast=roast_result)

    return render_template("index.html")
