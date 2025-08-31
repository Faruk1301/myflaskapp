from flask import Flask, redirect, url_for, session, request, render_template_string
from flask_session import Session
import msal
import uuid
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

app = Flask(__name__)
app.config["SECRET_KEY"] = "a_strong_random_secret_key_here"   # 🔑 Change to something secure
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# ------------------ Key Vault Setup ------------------
KEY_VAULT_NAME = "mypractice-kv"
KV_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net/"
credential = DefaultAzureCredential()
kv_client = SecretClient(vault_url=KV_URI, credential=credential)

# ------------------ Load Azure AD App Credentials ------------------
CLIENT_ID = kv_client.get_secret("ClientId").value
CLIENT_SECRET = kv_client.get_secret("ClientSecret").value   # ✅ Secret *Value* from Azure
TENANT_ID = kv_client.get_secret("TenantId").value

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/getAToken"   # must exactly match Azure App Registration
SCOPE = ["User.Read"]

# MSAL Confidential Client
msal_app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)

# ------------------ Routes ------------------

@app.route("/")
def index():
    if not session.get("user"):
        return redirect(url_for("login"))

    return render_template_string("""
        <h1>🔐 Secure Web App</h1>
        <p>Welcome <b>{{ user }}</b></p>
        <a href="{{ url_for('logout') }}">Logout</a>
    """, user=session["user"]["name"])


@app.route("/login")
def login():
    state = str(uuid.uuid4())
    session["state"] = state
    auth_url = msal_app.get_authorization_request_url(
        SCOPE,
        state=state,
        # ✅ Always use deployed Azure redirect URI
        redirect_uri="https://mydemo1-dnd3cza2dxafc8bu.centralindia-01.azurewebsites.net/getAToken"
    )
    return redirect(auth_url)


@app.route(REDIRECT_PATH)
def authorized():
    if request.args.get("state") != session.get("state"):
        return redirect(url_for("index"))

    if "error" in request.args:
        return f"Login error: {request.args['error_description']}"

    result = msal_app.acquire_token_by_authorization_code(
        request.args['code'],
        scopes=SCOPE,
        # ✅ Again, deployed Azure redirect URI
        redirect_uri="https://mydemo1-dnd3cza2dxafc8bu.centralindia-01.azurewebsites.net/getAToken"
    )

    if "id_token_claims" in result:
        session["user"] = result["id_token_claims"]

    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        f"{AUTHORITY}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri=https://mydemo1-dnd3cza2dxafc8bu.centralindia-01.azurewebsites.net/"
    )


if __name__ == "__main__":
    # ✅ Azure App Service expects the app to listen on 0.0.0.0 and a dynamic port
    import os
    port = int(os.environ.get("PORT", 8000))  # Default to 8000 if PORT not set
    app.run(host="0.0.0.0", port=port)

