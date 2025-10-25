# Chinoin AI Consultorio Manager 🏥

Kit de herramientas de gestión médica con inteligencia artificial para médicos, ofrecido gratuitamente por **CHINOIN®**.

## 🚀 Características Principales

### 1. 🎤 Transcriptor de Consultas (IA)
Convierte automáticamente las conversaciones médico-paciente en **notas clínicas SOAP** estructuradas:
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

1. **Accede al Dashboard** → Haz clic en "Iniciar Transcripción de Consulta"
2. **Pega el diálogo** → Copia la conversación entre médico y paciente
3. **Procesa con IA** → La inteligencia artificial genera las notas SOAP automáticamente
4. **Copia las notas** → Integra las notas a tu sistema de expedientes

### Ejemplo de Diálogo:

```
Médico: Buenos días Sra. Pérez, ¿qué la trae por aquí hoy?
Paciente: Doctor, me duele mucho la garganta y tengo fiebre desde hace dos días.
Médico: Déjeme revisarla. Abra la boca por favor...
[...]
```

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
