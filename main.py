import os
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'chinoin-dev-secret-key')

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

consultas_memoria = []

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
    return render_template('dashboard.html', 
                         total_consultas=len(consultas_memoria))

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
        prompt = f"""Eres un asistente médico experto que analiza transcripciones de consultas médicas.

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
{consulta_texto}

Responde en formato JSON con esta estructura:
{{
  "soap": {{
    "subjetivo": "texto",
    "objetivo": "texto",
    "analisis": "texto",
    "plan": "texto"
  }},
  "diagnostico": "texto",
  "tratamiento": "texto",
  "cumplimiento": {{
    "consentimiento": "mencionado/no mencionado",
    "riesgos_explicados": "si/no",
    "instrucciones_claras": "si/no",
    "estado": "Verificado/Pendiente de revisar"
  }}
}}
"""
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        import json
        if not response.text:
            return jsonify({"error": "No se recibió respuesta de la IA."}), 500
        resultado = json.loads(response.text)
        
        soap_formateado = f"""S (Subjetivo): {resultado['soap']['subjetivo']}

O (Objetivo): {resultado['soap']['objetivo']}

A (Análisis): {resultado['soap']['analisis']}

P (Plan): {resultado['soap']['plan']}"""
        
        consultas_memoria.append({
            'texto': consulta_texto,
            'soap': soap_formateado,
            'diagnostico': resultado['diagnostico'],
            'tratamiento': resultado['tratamiento']
        })
        
        return jsonify({
            "soap_output": soap_formateado,
            "diagnostico": resultado['diagnostico'],
            "plan": resultado['tratamiento'],
            "cumplimiento": resultado['cumplimiento']['estado']
        })
        
    except Exception as e:
        return jsonify({"error": f"Error al procesar con IA: {str(e)}"}), 500

@app.route('/asesoria')
def vista_asesoria():
    return render_template('asesoria.html')

@app.route('/consultar_norma', methods=['POST'])
def consultar_norma():
    if not request.json:
        return jsonify({"error": "No se recibió datos JSON."}), 400
    pregunta = request.json.get('pregunta', '')
    
    if not pregunta:
        return jsonify({"error": "No se recibió pregunta."}), 400
    
    try:
        prompt = f"""Eres un asesor experto en normativas fiscales y legales para médicos en México.

Responde a la siguiente pregunta de un médico mexicano de forma clara, precisa y profesional.

CONTEXTO NORMATIVO:
{NORMAS_CONTABLES_BASE}

PREGUNTA DEL MÉDICO:
{pregunta}

Proporciona una respuesta práctica y específica. Si mencionas alguna ley o norma, cita el nombre completo. 
Si recomiendas consultar a un especialista para casos complejos, indícalo.

Responde en español de México de forma profesional pero accesible."""

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        
        return jsonify({"respuesta": response.text})
        
    except Exception as e:
        return jsonify({"error": f"Error al consultar IA: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
