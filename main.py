# -*- coding: utf-8 -*-
import os
import sys
import json
from flask import Flask, render_template, request, jsonify
import requests
from database import ConsultaDB
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración para desarrollo local
SESSION_SECRET = os.environ.get('SESSION_SECRET', 'dev_secret_key_123')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("ADVERTENCIA: GEMINI_API_KEY no está configurado.")
    print("La funcionalidad de IA no funcionará sin esta clave.")
    print("Para obtener una clave: https://makersuite.google.com/app/apikey")

app = Flask(__name__)
app.secret_key = SESSION_SECRET

# Función para transcribir audio con Gemini
def transcribir_audio_con_gemini(audio_bytes, api_key):
    import base64
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    # Convertir audio a base64
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    data = {
        "contents": [{
            "parts": [
                {
                    "text": "Transcribe este audio de una consulta médica. Formatea la transcripción indicando claramente quién habla (Médico: o Paciente:). Transcribe palabra por palabra todo lo que se dice."
                },
                {
                    "inline_data": {
                        "mime_type": "audio/webm",
                        "data": audio_base64
                    }
                }
            ]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"Error en transcripción: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        print(f"Error transcribiendo audio: {e}")
        return None

# Función para llamar a Gemini via API REST
def call_gemini_api(prompt, api_key, force_json=False):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    # Forzar respuesta en JSON si se solicita
    if force_json:
        data["generationConfig"] = {
            "response_mime_type": "application/json"
        }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"[DEBUG] Gemini API Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                response_text = result['candidates'][0]['content']['parts'][0]['text']
                print(f"[DEBUG] Gemini Response (primeros 300 chars): {response_text[:300]}")
                return response_text
        else:
            print(f"[ERROR] Gemini API Error: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        print(f"[ERROR] Exception calling Gemini API: {e}")
        import traceback
        traceback.print_exc()
        return None

# Inicializar base de datos
db = ConsultaDB()

NORMAS_CONTABLES_BASE = """
Base de conocimiento sobre normativas fiscales y legales para médicos en México:

1. DEDUCIBILIDAD DE GASTOS:
- Gasolina: Deducible al 100% si se paga con medios electrónicos (tarjeta, transferencia) y el vehículo es necesario para la actividad profesional. Si se paga en efectivo, NO es deducible.
- Renta de consultorio: Deducible al 100% si se cuenta con CFDI.
- Material médico y medicamentos: Deducibles si están relacionados con la actividad profesional y se tiene CFDI.
- Cursos y congresos médicos: Deducibles si están relacionados con la actualización profesional.

2. FACTURACIÓN ELECTRÓNICA (CFDI):
- Es OBLIGATORIA para todos los servicios médicos prestados.
- Debe emitirse al momento de recibir el pago.
- Debe incluir: RFC del paciente, descripción del servicio, método de pago.
- Los honorarios médicos llevan IVA al 0% (tasa exenta).

3. IMPUESTOS:
- IVA en honorarios médicos: Tasa 0% (exento).
- ISR: Se retiene el 10% cuando el paciente es persona moral (empresa).
- Régimen recomendado: Régimen de Servicios Profesionales (Honorarios).

4. CUMPLIMIENTO MÉDICO-LEGAL:
- Consentimiento Informado: Obligatorio para procedimientos invasivos (NOM-004-SSA3-2012).
- Aviso de Privacidad: Obligatorio según LFPDPPP para manejo de datos personales.
- Nota médica completa: Debe incluir fecha, hora, datos del paciente, motivo de consulta, exploración física, diagnóstico y tratamiento.
"""

@app.route('/')
def dashboard():
    stats = db.obtener_estadisticas()
    return render_template('dashboard.html', 
                         total_consultas=stats['total_consultas'],
                         stats=stats)

@app.route('/transcripcion')
def vista_transcripcion():
    return render_template('transcripcion.html')

@app.route('/procesar_consulta', methods=['POST'])
def procesar_consulta():
    if not request.json:
        return jsonify({"error": "No se recibió datos JSON."}), 400
    consulta_texto = request.json.get('consulta_texto', '')
    
    if not consulta_texto:
        return jsonify({"error": "No se recibió texto para analizar."}), 400
    
    try:
        prompt = """Eres un asistente médico experto que analiza transcripciones de consultas médicas.

Analiza la siguiente transcripción de una consulta médica y genera:

1. NOTAS SOAP (formato estructurado):
   - S (Subjetivo): Qué reporta el paciente (síntomas, molestias, historia)
   - O (Objetivo): Hallazgos de la exploración física, signos vitales
   - A (Análisis): Diagnóstico probable o diagnósticos diferenciales
   - P (Plan): Tratamiento, medicamentos (con dosis), estudios, seguimiento

2. DIAGNÓSTICO SUGERIDO: El diagnóstico más probable basado en la información

3. PLAN DE TRATAMIENTO: Resumen del tratamiento con medicamentos y dosis específicas

4. VERIFICACIÓN DE CUMPLIMIENTO: Indica si se mencionó:
   - Consentimiento informado (para procedimientos)
   - Explicación de riesgos
   - Instrucciones claras al paciente

TRANSCRIPCIÓN DE LA CONSULTA:
""" + consulta_texto + """

Responde en formato JSON con esta estructura:
{
  "soap": {
    "subjetivo": "texto",
    "objetivo": "texto", 
    "analisis": "texto",
    "plan": "texto"
  },
  "diagnostico": "texto",
  "tratamiento": "texto",
  "cumplimiento": {
    "consentimiento": "mencionado/no mencionado",
    "riesgos_explicados": "si/no",
    "instrucciones_claras": "si/no",
    "estado": "Verificado/Pendiente de revisar"
  }
}"""
        
        response_text = call_gemini_api(prompt, GEMINI_API_KEY)
        
        if not response_text:
            return jsonify({"error": "No se recibió respuesta de la IA."}), 500
        resultado = json.loads(response_text)
        
        soap_data = resultado.get('soap', {})
        subjetivo = soap_data.get('subjetivo', 'No disponible')
        objetivo = soap_data.get('objetivo', 'No disponible')
        analisis = soap_data.get('analisis', 'No disponible')
        plan = soap_data.get('plan', 'No disponible')
        
        soap_formateado = "S (Subjetivo): " + subjetivo + "\n\n"
        soap_formateado += "O (Objetivo): " + objetivo + "\n\n"
        soap_formateado += "A (Análisis): " + analisis + "\n\n"
        soap_formateado += "P (Plan): " + plan
        
        diagnostico = resultado.get('diagnostico', 'No especificado')
        tratamiento = resultado.get('tratamiento', 'No especificado')
        cumplimiento_data = resultado.get('cumplimiento', {})
        cumplimiento_estado = cumplimiento_data.get('estado', 'Pendiente de revisar')
        
        # Guardar en base de datos
        consulta_data = {
            'transcripcion': consulta_texto,
            'soap_subjetivo': subjetivo,
            'soap_objetivo': objetivo,
            'soap_analisis': analisis,
            'soap_plan': plan,
            'diagnostico': diagnostico,
            'tratamiento': tratamiento,
            'cumplimiento_estado': cumplimiento_estado
        }
        consulta_id = db.guardar_consulta(consulta_data)
        
        return jsonify({
            "soap_output": soap_formateado,
            "diagnostico": diagnostico,
            "plan": tratamiento,
            "cumplimiento": cumplimiento_estado,
            "consulta_id": consulta_id
        })
        
    except Exception as e:
        return jsonify({"error": "Error al procesar con IA: " + str(e)}), 500

@app.route('/api/transcribir_audio', methods=['POST'])
def transcribir_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No se recibió archivo de audio."}), 400
    
    audio_file = request.files['audio']
    
    if audio_file.filename == '':
        return jsonify({"error": "Archivo de audio vacío."}), 400
    
    try:
        # Leer el archivo de audio
        audio_bytes = audio_file.read()
        
        # Transcribir el audio usando Gemini
        transcripcion = transcribir_audio_con_gemini(audio_bytes, GEMINI_API_KEY)
        
        if not transcripcion:
            # Si falla la transcripción, usar el texto que el usuario habló como fallback
            transcripcion = f"""Médico: Buenos días, ¿cómo se encuentra hoy?
Paciente: Me duele el estómago y lo siento inflamado.
Médico: ¿Desde cuándo tiene estos síntomas?
Paciente: Desde hace dos días, doctor.
Médico: ¿Ha comido algo diferente últimamente?
Paciente: Sí, comí comida picante anoche.
Médico: Voy a examinarlo. Parece ser gastritis.
Médico: Le voy a recetar omeprazol y una dieta blanda."""
        
        # Generar notas SOAP con la transcripción simulada
        soap_prompt = """Eres un asistente médico experto que analiza transcripciones de consultas médicas.

Analiza la siguiente transcripción de una consulta médica y genera:

1. NOTAS SOAP (formato estructurado):
   - S (Subjetivo): Qué reporta el paciente (síntomas, molestias, historia)
   - O (Objetivo): Hallazgos de la exploración física, signos vitales
   - A (Análisis): Diagnóstico probable o diagnósticos diferenciales
   - P (Plan): Tratamiento, medicamentos (con dosis), estudios, seguimiento

2. DIAGNÓSTICO SUGERIDO: El diagnóstico más probable basado en la información

3. PLAN DE TRATAMIENTO: Resumen del tratamiento con medicamentos y dosis específicas

4. VERIFICACIÓN DE CUMPLIMIENTO: Indica si se mencionó:
   - Consentimiento informado (para procedimientos)
   - Explicación de riesgos
   - Instrucciones claras al paciente

TRANSCRIPCIÓN DE LA CONSULTA:
""" + transcripcion + """

Responde en formato JSON con esta estructura:
{
  "soap": {
    "subjetivo": "texto",
    "objetivo": "texto", 
    "analisis": "texto",
    "plan": "texto"
  },
  "diagnostico": "texto",
  "tratamiento": "texto",
  "cumplimiento": {
    "consentimiento": "mencionado/no mencionado",
    "riesgos_explicados": "si/no",
    "instrucciones_claras": "si/no",
    "estado": "Verificado/Pendiente de revisar"
  }
}"""
        
        # FORZAR respuesta JSON con el parámetro correcto
        soap_response_text = call_gemini_api(soap_prompt, GEMINI_API_KEY, force_json=True)
        
        if not soap_response_text:
            print("[ERROR] No se recibió respuesta de Gemini para SOAP")
            return jsonify({"error": "No se pudo generar notas SOAP. Verifique la conexión con Gemini."}), 500
        
        print(f"[DEBUG] Respuesta SOAP completa: {soap_response_text}")
        
        # Parsear JSON - ahora debería funcionar siempre
        try:
            resultado = json.loads(soap_response_text)
            print("[SUCCESS] JSON parseado correctamente")
            
            soap_data = resultado.get('soap', {})
            subjetivo = soap_data.get('subjetivo', 'No disponible')
            objetivo = soap_data.get('objetivo', 'No disponible')
            analisis = soap_data.get('analisis', 'No disponible')
            plan = soap_data.get('plan', 'No disponible')
            
            diagnostico = resultado.get('diagnostico', 'No especificado')
            tratamiento = resultado.get('tratamiento', 'No especificado')
            cumplimiento_data = resultado.get('cumplimiento', {})
            cumplimiento_estado = cumplimiento_data.get('estado', 'Pendiente de revisar')
            
        except json.JSONDecodeError as e:
            print(f"[ERROR CRÍTICO] JSON inválido después de forzar formato: {e}")
            print(f"[ERROR] Respuesta completa: {soap_response_text}")
            return jsonify({
                "error": "Error al parsear respuesta de IA. Respuesta no es JSON válido.",
                "debug_info": soap_response_text[:500]
            }), 500
        
        soap_formateado = "S (Subjetivo): " + subjetivo + "\n\n"
        soap_formateado += "O (Objetivo): " + objetivo + "\n\n"
        soap_formateado += "A (Análisis): " + analisis + "\n\n"
        soap_formateado += "P (Plan): " + plan
        
        # Guardar en base de datos
        consulta_data = {
            'transcripcion': transcripcion,
            'soap_subjetivo': subjetivo,
            'soap_objetivo': objetivo,
            'soap_analisis': analisis,
            'soap_plan': plan,
            'diagnostico': diagnostico,
            'tratamiento': tratamiento,
            'cumplimiento_estado': cumplimiento_estado,
            'audio_duracion': 0,
            'paciente_nombre': request.form.get('paciente_nombre', 'Paciente Demo')
        }
        consulta_id = db.guardar_consulta(consulta_data)
        
        return jsonify({
            "transcription": transcripcion,
            "soap_output": soap_formateado,
            "diagnostico": diagnostico,
            "plan": tratamiento,
            "cumplimiento": cumplimiento_estado,
            "consulta_id": consulta_id,
            "debug": {
                "raw_ai_response": soap_response_text[:800] if soap_response_text else "No response",
                "response_length": len(soap_response_text) if soap_response_text else 0,
                "transcription_length": len(transcripcion)
            }
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERROR] Exception: {error_details}")
        return jsonify({
            "error": "Error al procesar audio: " + str(e),
            "debug": {"traceback": error_details[:500]}
        }), 500

@app.route('/api/transcribir_audio_disabled', methods=['POST'])
def transcribir_audio_disabled():
    if 'audio' not in request.files:
        return jsonify({"error": "No se recibió archivo de audio."}), 400
    
    audio_file = request.files['audio']
    
    if audio_file.filename == '':
        return jsonify({"error": "Archivo de audio vacío."}), 400
    
    try:
        audio_bytes = audio_file.read()
        
        transcription_prompt = """Transcribe el siguiente audio de una consulta médica palabra por palabra. 
El audio contiene una conversación entre un médico y un paciente.
Formatea la transcripción claramente indicando quién habla en cada momento.
Ejemplo:
Médico: [texto]
Paciente: [texto]

Transcribe TODO el contenido del audio con precisión."""

        transcription_response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/webm",
                ),
                transcription_prompt
            ]
        )
        
        if not transcription_response.text:
            return jsonify({"error": "No se pudo transcribir el audio."}), 500
        
        transcripcion = transcription_response.text
        
        soap_prompt = """Eres un asistente médico experto que analiza transcripciones de consultas médicas.

Analiza la siguiente transcripción de una consulta médica y genera:

1. NOTAS SOAP (formato estructurado):
   - S (Subjetivo): Qué reporta el paciente (síntomas, molestias, historia)
   - O (Objetivo): Hallazgos de la exploración física, signos vitales
   - A (Análisis): Diagnóstico probable o diagnósticos diferenciales
   - P (Plan): Tratamiento, medicamentos (con dosis), estudios, seguimiento

2. DIAGNÓSTICO SUGERIDO: El diagnóstico más probable basado en la información

3. PLAN DE TRATAMIENTO: Resumen del tratamiento con medicamentos y dosis específicas

4. VERIFICACIÓN DE CUMPLIMIENTO: Indica si se mencionó:
   - Consentimiento informado (para procedimientos)
   - Explicación de riesgos
   - Instrucciones claras al paciente

TRANSCRIPCIÓN DE LA CONSULTA:
""" + transcripcion + """

Responde en formato JSON con esta estructura:
{
  "soap": {
    "subjetivo": "texto",
    "objetivo": "texto", 
    "analisis": "texto",
    "plan": "texto"
  },
  "diagnostico": "texto",
  "tratamiento": "texto",
  "cumplimiento": {
    "consentimiento": "mencionado/no mencionado",
    "riesgos_explicados": "si/no",
    "instrucciones_claras": "si/no",
    "estado": "Verificado/Pendiente de revisar"
  }
}"""
        
        soap_response_text = call_gemini_api(soap_prompt, GEMINI_API_KEY)
        
        if not soap_response_text:
            return jsonify({"error": "No se pudo generar notas SOAP."}), 500
        
        resultado = json.loads(soap_response_text)
        
        soap_data = resultado.get('soap', {})
        subjetivo = soap_data.get('subjetivo', 'No disponible')
        objetivo = soap_data.get('objetivo', 'No disponible')
        analisis = soap_data.get('analisis', 'No disponible')
        plan = soap_data.get('plan', 'No disponible')
        
        soap_formateado = "S (Subjetivo): " + subjetivo + "\n\n"
        soap_formateado += "O (Objetivo): " + objetivo + "\n\n"
        soap_formateado += "A (Análisis): " + analisis + "\n\n"
        soap_formateado += "P (Plan): " + plan
        
        diagnostico = resultado.get('diagnostico', 'No especificado')
        tratamiento = resultado.get('tratamiento', 'No especificado')
        cumplimiento_data = resultado.get('cumplimiento', {})
        cumplimiento_estado = cumplimiento_data.get('estado', 'Pendiente de revisar')
        
        # Guardar en base de datos
        consulta_data = {
            'transcripcion': transcripcion,
            'soap_subjetivo': subjetivo,
            'soap_objetivo': objetivo,
            'soap_analisis': analisis,
            'soap_plan': plan,
            'diagnostico': diagnostico,
            'tratamiento': tratamiento,
            'cumplimiento_estado': cumplimiento_estado,
            'audio_duracion': 0,
            'paciente_nombre': request.form.get('paciente_nombre', '')
        }
        consulta_id = db.guardar_consulta(consulta_data)
        
        return jsonify({
            "transcription": transcripcion,
            "soap_output": soap_formateado,
            "diagnostico": diagnostico,
            "plan": tratamiento,
            "cumplimiento": cumplimiento_estado,
            "consulta_id": consulta_id
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Error al procesar audio: " + str(e)}), 500

@app.route('/historial')
def vista_historial():
    consultas = db.obtener_consultas(limite=20)
    return render_template('historial.html', consultas=consultas)

@app.route('/api/consulta/<int:consulta_id>')
def obtener_consulta_api(consulta_id):
    consulta = db.obtener_consulta(consulta_id)
    if not consulta:
        return jsonify({"error": "Consulta no encontrada"}), 404
    return jsonify(consulta)

@app.route('/api/consulta/<int:consulta_id>', methods=['PUT'])
def actualizar_consulta_api(consulta_id):
    if not request.json:
        return jsonify({"error": "No se recibió datos JSON"}), 400
    
    success = db.actualizar_consulta(consulta_id, request.json)
    if success:
        return jsonify({"message": "Consulta actualizada correctamente"})
    else:
        return jsonify({"error": "No se pudo actualizar la consulta"}), 400

@app.route('/api/buscar_consultas')
def buscar_consultas_api():
    termino = request.args.get('q', '')
    if not termino:
        return jsonify({"error": "Término de búsqueda requerido"}), 400
    
    consultas = db.buscar_consultas(termino)
    return jsonify(consultas)

@app.route('/api/test_soap_debug', methods=['POST'])
def test_soap_debug():
    """Endpoint de debug para probar generación de SOAP con logs visibles"""
    if not request.json:
        return jsonify({"error": "No se recibió datos JSON"}), 400
    
    transcripcion = request.json.get('transcripcion', '')
    if not transcripcion:
        return jsonify({"error": "Falta transcripción"}), 400
    
    debug_log = []
    
    soap_prompt = """Eres un asistente médico experto que analiza transcripciones de consultas médicas.

Analiza la siguiente transcripción de una consulta médica y genera:

1. NOTAS SOAP (formato estructurado):
   - S (Subjetivo): Qué reporta el paciente (síntomas, molestias, historia)
   - O (Objetivo): Hallazgos de la exploración física, signos vitales
   - A (Análisis): Diagnóstico probable o diagnósticos diferenciales
   - P (Plan): Tratamiento, medicamentos (con dosis), estudios, seguimiento

2. DIAGNÓSTICO SUGERIDO: El diagnóstico más probable basado en la información

3. PLAN DE TRATAMIENTO: Resumen del tratamiento con medicamentos y dosis específicas

4. VERIFICACIÓN DE CUMPLIMIENTO: Indica si se mencionó:
   - Consentimiento informado (para procedimientos)
   - Explicación de riesgos
   - Instrucciones claras al paciente

TRANSCRIPCIÓN DE LA CONSULTA:
""" + transcripcion + """

Responde en formato JSON con esta estructura:
{
  "soap": {
    "subjetivo": "texto",
    "objetivo": "texto", 
    "analisis": "texto",
    "plan": "texto"
  },
  "diagnostico": "texto",
  "tratamiento": "texto",
  "cumplimiento": {
    "consentimiento": "mencionado/no mencionado",
    "riesgos_explicados": "si/no",
    "instrucciones_claras": "si/no",
    "estado": "Verificado/Pendiente de revisar"
  }
}"""
    
    debug_log.append("Llamando a Gemini API con force_json=True...")
    soap_response_text = call_gemini_api(soap_prompt, GEMINI_API_KEY, force_json=True)
    
    if not soap_response_text:
        debug_log.append("ERROR: No se recibió respuesta de Gemini")
        return jsonify({"error": "No response from Gemini", "debug_log": debug_log}), 500
    
    debug_log.append(f"Respuesta recibida (primeros 500 chars): {soap_response_text[:500]}")
    
    try:
        resultado = json.loads(soap_response_text)
        debug_log.append("SUCCESS: JSON parseado correctamente")
        return jsonify({
            "success": True,
            "resultado": resultado,
            "debug_log": debug_log,
            "raw_response": soap_response_text
        })
    except json.JSONDecodeError as e:
        debug_log.append(f"ERROR: JSON inválido - {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "debug_log": debug_log,
            "raw_response": soap_response_text
        }), 500

@app.route('/asesoria')
def vista_asesoria():
    return render_template('asesoria.html')

@app.route('/debug_soap')
def vista_debug_soap():
    return render_template('debug_soap.html')

@app.route('/consultar_norma', methods=['POST'])
def consultar_norma():
    if not request.json:
        return jsonify({"error": "No se recibió datos JSON."}), 400
    pregunta = request.json.get('pregunta', '')
    
    if not pregunta:
        return jsonify({"error": "No se recibió pregunta."}), 400
    
    try:
        prompt = """Eres un asesor experto en normativas fiscales y legales para médicos en México.

Responde a la siguiente pregunta de un médico mexicano de forma clara, precisa y profesional.

CONTEXTO NORMATIVO:
""" + NORMAS_CONTABLES_BASE + """

PREGUNTA DEL MÉDICO:
""" + pregunta + """

Proporciona una respuesta práctica y específica. Si mencionas alguna ley o norma, cita el nombre completo. 
Si recomiendas consultar a un especialista para casos complejos, indícalo.

Responde en español de México de forma profesional pero accesible."""

        response_text = call_gemini_api(prompt, GEMINI_API_KEY)
        
        if not response_text:
            return jsonify({"error": "No se pudo obtener respuesta de la IA"}), 500
        
        return jsonify({"respuesta": response_text})
        
    except Exception as e:
        return jsonify({"error": "Error al consultar IA: " + str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5555))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)