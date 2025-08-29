import os
from flask import Flask, render_template_string
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

app = Flask(__name__)

# ------------------ Key Vault ------------------
KEY_VAULT_NAME = "mypractice-kv"   # Replace with your vault name
KV_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net/"
credential = DefaultAzureCredential()
kv_client = SecretClient(vault_url=KV_URI, credential=credential)

@app.route('/')
def index():
    try:
        # Fetch secret from Key Vault
        secret_value = kv_client.get_secret("DBPassword").value
        dummy_db_connection = f"Connected to database using password of length {len(secret_value)}"
    except Exception as e:
        dummy_db_connection = f"Could not access Key Vault: {str(e)}"

    # Display safe info only
    return render_template_string("""
        <h1>Secure Web App</h1>
        <p>{{ connection_info }}</p>
    """, connection_info=dummy_db_connection)

if __name__ == '__main__':
    # Use Azure-assigned port if available
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
