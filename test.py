from quart import Quart, render_template, request, session, redirect, url_for
from quart_discord import DiscordOAuth2Session
from dotenv import load_dotenv
import os

app = Quart(__name__)

app.config["SECRET_KEY"] = "key"
app.config["DISCORD_CLIENT_ID"] = os.getenv("discord_client_id")  # Discord client ID.
app.config["DISCORD_CLIENT_SECRET"] = os.getenv("discord_client_secret")  # Discord client secret.
app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback"   

discord = DiscordOAuth2Session(app)

@app.route("/")
async def home():
	return await render_template("index.html", authorized = await discord.authorized)

@app.route("/login")
async def login():
	return await discord.create_session()

@app.route("/callback")
async def callback():
	try:
		await discord.callback()
	except Exception:
		pass

	return redirect(url_for("logged_in"))

if __name__ == "__main__":
	app.run(debug=True)