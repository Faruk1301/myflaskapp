from flask import Flask, render_template_string
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

app = Flask(__name__)

# ------------------ Key Vault ------------------
KEY_VAULT_NAME = "mypractice-kv"   # Replace with your vault name
KV_URI = f"https://mypractice-kv.vault.azure.net/"
credential = DefaultAzureCredential()
kv_client = SecretClient(vault_url=KV_URI, credential=credential)

@app.route('/')
def index():
    # Fetch secret from Key Vault (used internally)
    secret_value = kv_client.get_secret("DBPassword").value

    # Example: use secret internally (simulate DB/API usage)
    dummy_db_connection = f"Connected to database using password of length {len(secret_value)}"

    # Only display safe info (not the secret itself)
    return render_template_string("""
        <h1>Secure Web App</h1>
        <p>{{ connection_info }}</p>
    """, connection_info=dummy_db_connection)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)



