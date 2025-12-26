from flask import Flask, render_template, request
from services.roast_service import roast_url

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    roast_result = None
    error = None

    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not url:
            error = "Please enter a URL"
        else:
            roast_result = roast_url(url)
            if "error" in roast_result:
                error = roast_result["error"]
                roast_result = None

    return render_template("index.html", roast=roast_result, error=error)

if __name__ == "__main__":
    app.run(debug=True)
