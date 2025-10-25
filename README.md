# Chinoin AI Consultorio Manager 🏥

Kit de herramientas de gestión médica con inteligencia artificial para médicos, ofrecido gratuitamente por **CHINOIN®**.

## 🚀 Características Principales

### 1. 🎤 Transcriptor de Consultas (IA) - CON GRABACIÓN DE AUDIO REAL
**¡Graba tu consulta con un clic!** El sistema automáticamente:
1. **Graba el audio** → Haz clic en el botón del micrófono para grabar la consulta
2. **Transcribe con IA** → Gemini convierte el audio a texto automáticamente
3. **Genera notas SOAP** → Crea notas clínicas estructuradas:
   - **S** (Subjetivo): Síntomas reportados por el paciente
   - **O** (Objetivo): Hallazgos de la exploración física
   - **A** (Análisis): Diagnóstico probable
   - **P** (Plan): Tratamiento, medicamentos y seguimiento

### 2. ⚖️ Asistente Legal/Contable
Responde preguntas sobre normativas fiscales mexicanas:
- Deducibilidad de gastos médicos
- Facturación electrónica (CFDI)
- ISR e IVA para honorarios médicos
- Cumplimiento legal (NOM-004, avisos de privacidad)

### 3. 📊 Dashboard de Gestión
- Resumen financiero rápido
- Alertas de cumplimiento
- Estadísticas de consultas procesadas
- Acceso al portal CHINOIN

## 🛠️ Tecnología

- **Backend:** Flask (Python 3.11)
- **IA:** Google Gemini 2.0 Flash Exp
- **Frontend:** HTML5, CSS3, JavaScript
- **Diseño:** Responsive, branding CHINOIN

## 📖 Cómo Usar

1. **Accede al Transcriptor** → Haz clic en "Iniciar Transcripción de Consulta"
2. **Graba la consulta** → Haz clic en el botón del micrófono (🎤) para iniciar la grabación
3. **Detén cuando termines** → Haz clic en ⏹️ para parar y procesar
4. **¡Listo!** → La IA transcribe el audio, genera notas SOAP automáticamente
5. **Copia las notas** → Integra las notas a tu sistema de expedientes

### Flujo Real:
- **Médico hace clic en grabar** → El navegador pide permiso para usar el micrófono
- **Conversa normalmente** → La consulta se graba en tiempo real con visualización de audio
- **Detiene la grabación** → El audio se envía a Gemini para transcripción
- **Recibe transcripción + notas SOAP** → Todo aparece automáticamente en pantalla

## ⚠️ Importante

- Esta herramienta requiere **consentimiento informado** del paciente para grabar consultas (NOM-004-SSA3-2012)
- Las respuestas del asistente legal/contable son orientativas, no sustituyen asesoría profesional
- Los datos se almacenan temporalmente solo durante la sesión

## 🔐 Seguridad

- Las claves API están protegidas en Replit Secrets
- Validación de datos en todas las entradas
- No se almacenan datos permanentemente (privacidad por diseño)

## 📱 Soporte

Este es un MVP (Producto Mínimo Viable). Las funcionalidades avanzadas vendrán en próximas versiones:
- Base de datos persistente
- Generación automática de CFDI
- Calculadora de impuestos
- App móvil

---

**Desarrollado para CHINOIN®**  
Powered by Google Gemini AI
