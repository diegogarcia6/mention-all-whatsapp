from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Necesaria para usar flash

# Token de autenticación (reemplazar por el tuyo real)
TOKEN = os.getenv("TOKEN")

def obtener_grupos(token):
    url = f"https://gate.whapi.cloud/groups?token={token}"
    response = requests.get(url)
    if response.status_code == 200:
        try:
            data = response.json()
            grupos = data.get("groups", [])
            return grupos
        except ValueError:
            flash("La respuesta no es un JSON válido.", "danger")
            return []
    else:
        flash("No se pudo obtener la lista de grupos.", "danger")
        return []

def enviar_mensaje(token, id_grupo, mensaje, participantes):
    # Crear menciones y texto con menciones
    menciones = []
    texto_con_menciones = mensaje + "\n\n"
    for miembro in participantes:
        numero = miembro["id"]
        menciones.append(numero)
        texto_con_menciones += f"@{numero} "
    
    url_mensaje = f"https://gate.whapi.cloud/messages/text?token={token}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "to": id_grupo,
        "body": texto_con_menciones,
        "mentions": menciones
    }
    
    try:
        response = requests.post(url_mensaje, headers=headers, json=payload)
        response.raise_for_status()  # Para detectar errores HTTP
        if response.status_code == 200:
            flash("Mensaje enviado correctamente.", "success")
        else:
            flash(f"No se pudo enviar el mensaje. Código de estado: {response.status_code}", "danger")
    except requests.exceptions.RequestException as e:
        flash(f"Error al enviar el mensaje: {e}", "danger")

@app.route('/', methods=["GET", "POST"])
def index():
    grupos = obtener_grupos(TOKEN)
    if request.method == "POST":
        id_grupo = request.form.get("grupo")
        mensaje = request.form.get("mensaje")
        if not id_grupo or not mensaje:
            flash("Selecciona un grupo e ingresa un mensaje.", "warning")
            return redirect(url_for("index"))
        
        # Buscar el grupo seleccionado para obtener los participantes
        grupo = next((g for g in grupos if g["id"] == id_grupo), None)
        if grupo:
            participantes = grupo.get("participants", [])
            enviar_mensaje(TOKEN, id_grupo, mensaje, participantes)
        else:
            flash("No se encontró el grupo seleccionado.", "danger")
        return redirect(url_for("index"))
    
    return render_template("index.html", grupos=grupos)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
