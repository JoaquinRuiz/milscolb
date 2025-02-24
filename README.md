# 🔐 Misco-LB
## Latch + Blink: Integración de Seguridad para Cámaras Blink

Este proyecto permite **automatizar y securizar la activación y desactivación de una cámara Blink** mediante **Latch y Alexa**.

---

## 🚀 **Flujo de Funcionamiento**
1️⃣ Mediante **Herramienta de Localización detecto que llegaste o te fuiste** de casa y envía un webhook al **Middleware**.  
2️⃣ **El Middleware llama a Latch** para bloquear/desbloquear la operación.  
3️⃣ **Latch notifica al Middleware** el cambio de estado.  
4️⃣ **El Middleware llama a Blink** (a través de Alexa) para **activar o desactivar** la cámara.  

---

## 📌 **Requisitos Previos**
✅ Cuenta en [Latch](https://latch.tu.com/) y acceso al portal de desarrolladores.  
✅ Alexa configurada con una rutina con la cámara Blink.  
✅ Cuenta en [Amazon Developer](https://developer.amazon.com/) para los accesos a la API.  
✅ **Python 3** y **Ngrok** instalado en tu sistema.  

---

## 🛠 **Configuración Paso a Paso**
### 1️⃣ **Configurar Latch**
#### 🔹 **Crear una Aplicación en Latch**
1. Accede a [Latch Developer Portal](https://latch.tu.com/developers).
2. Crea una nueva aplicación y obtén:
   - **Application ID**
   - **Secret Key**
3. Añade una **operación** llamada `"Control Cámara"` y guarda su **operationId**.

#### 🔹 **Configurar el Webhook en Latch**
1. En el panel de desarrolladores de Latch, busca la opción **"Webhooks"**.
2. Introduce la URL del Middleware:
```https://TU_DOMINIO_O_IP/latch_webhook```
- Si estás en **localhost**, usa `ngrok` para exponer el servidor:
  ```bash
  ngrok http 3000
  ```

---

### 2️⃣ **Configurar Herramienta de localización**
#### 🔹 En este caso, puedes usar Automate o IFTTT para que me geolocalice, y llamar al webhook. 
1. En tu herramienta de localización, configura el siguiente webhook cuando salgas de la zona de tu casa:
```bash 
curl -X POST "http://TU_DOMINIO_O_IP/webhook" -H "Content-Type: application/json" -d '{"action": "left"}'
```
2. En tu herramienta de localización, configura el siguiente webhook cuando entres en la zona de tu casa:
```bash 
curl -X POST "http://TU_DOMINIO_O_IP/webhook" -H "Content-Type: application/json" -d '{"action": "arrived"}'
```
### 3️⃣ **Configurar Alexa/Blink**
#### 🔹 Necesitas un Access Token de Alexa para autenticarte. 
1. Dentro de Amazon Developers, crea una APP "Login with Amazon"
2. Ve a "Security Profile" en la aplicación de Login with Amazon, y añade una URL de redirección:
```bash 
https://TU_DOMINIO_O_IP/callback 
```
3. Obtén el **Access Token** usando ask-cli.
```bash
ask util generate-lwa-tokens --scopes alexa::ask:skills:readwrite
```
4. Usando ese access-token, saca el **EndpointID** de Blink.
```bash
curl -X GET "https://api.amazonalexa.com/v2/endpoints?owner=~caller&expand=all" \
     -H "Authorization: Bearer TU_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -H "Accept: application/json"
```

---

### 4️⃣ **Configurar el Proyecto**
#### 🔹 **Clona el repositorio y entra en la carpeta**
```bash
git clone https://github.com/JoaquinRuiz/misco-lb.git
cd misco-lb
```
#### 🔹 Instala las dependencias
```bash
pip install -r requirements.txt
```
#### 🔹 Crea el archivo .env y añade tus credenciales
```bash
touch .env
nano .env
```
##### 📌 Ejemplo de .env
```env
LATCH_APP_ID = "XXX" 
LATCH_SECRET_KEY = "XXX"
ACCOUNT_ID = "XXX"
CONTROL_CAMARA_ID = "XXX"
ALEXA_ACCESS_TOKEN = "xxx"
BLINK_ENDPOINT_ID = "xxx"
```
## Cómo Ejecutar el Proyecto
```bash
python miscolb.py
```
Si es la primera vez, Latch pedirá un código de pareado.
Genera un código en la app móvil de Latch y parealo con:
```bash
curl -X POST "http://localhost:3000/pair" -H "Content-Type: application/json" -d '{"pair_code": "ABC123"}'
```
## 🚀 Cómo Probarlo   
### 🔹 Simular que Alexa detecta que has llegado
```bash
curl -X POST "http://localhost:3000/webhook" -H "Content-Type: application/json" -d '{"action": "arrived"}'
```
✔️ Debería bloquear Latch y apagar Blink.
### 🔹 Simular que Alexa detecta que te has ido
```bash
curl -X POST "http://localhost:3000/webhook" -H "Content-Type: application/json" -d '{"action": "left"}'
```
✔️ Debería activar Latch y encender Blink.

### 🔹 Simular que Latch cambia de estado
```bash
curl -X POST "http://localhost:3000/latch_webhook" -H "Content-Type: application/json" -d '{
    "t": XXX,
    "accounts": {
        "TU_ACCOUNT_ID": [
            {
                "type": "UPDATE",
                "source": "DEVELOPER_UPDATE",
                "id": "XXX",
                "new_status": "off"
            }
        ]
    }
}'
```
✔️ Alexa debería recibir el evento y desactivar Blink.

## 🛠 Estructura del Código
```bash
/alexa-latch-blink
│── miscolb.py        # Código principal del Middleware
│── .env               # Archivo con credenciales
│── requirements.txt   # Librerías necesarias
│── README.md          # Este archivo
│── account_id.txt     # ID pareado de Latch (se genera tras el pareo)
```
### 📜 Explicación del Código   
#### 📌 Archivo miscolb.py

- /pair → Realiza el pareado con Latch usando un código de la App móvil.   
- load_account_id() → Carga tu account_id pareado con Latch
- save_account_id(account_id) → Guarda el account_id que acabas de parear

- /webhook → Alexa avisa al Middleware cuando llegas o te vas.   
- lock_latch() → Bloquea Latch cuando llegas.   
- unlock_latch() → Desbloquea Latch cuando te vas.   

- /latch_webhook → Latch avisa al Middleware cuando cambia de estado.   
- trigger_alexa_routine(activate) → Llama a Alexa. 

## 🚀 Mejoras Futuras
✅ Añadir soporte para múltiples cámaras en una misma cuenta de Latch.

### 🏆 Créditos   
🔹 Desarrollado por: Joaquín Ruiz [Web](https://jokiruiz.com)   
🔹 GitHub: [Profile](https://github.com/JoaquinRuiz)   
🔹 Fecha: Febrero 2025

## ⚠️ Notas de Seguridad   
⚠️ No subas el archivo .env a GitHub.   
⚠️ Usa gitignore para excluir .env y account_id.txt.

```bash
echo ".env" >> .gitignore
echo "account_id.txt" >> .gitignore
```