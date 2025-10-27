# -*- coding: utf-8 -*-
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

class ConsultaDB:
    def __init__(self, db_path: str = "consultas.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos y crea las tablas necesarias"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS consultas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_consulta DATETIME DEFAULT CURRENT_TIMESTAMP,
                    medico_id TEXT DEFAULT 'default',
                    paciente_nombre TEXT,
                    transcripcion TEXT NOT NULL,
                    soap_subjetivo TEXT,
                    soap_objetivo TEXT,
                    soap_analisis TEXT,
                    soap_plan TEXT,
                    diagnostico TEXT,
                    tratamiento TEXT,
                    cumplimiento_estado TEXT,
                    audio_duracion INTEGER,
                    notas_adicionales TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices para búsquedas rápidas
            conn.execute('CREATE INDEX IF NOT EXISTS idx_fecha ON consultas(fecha_consulta)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_medico ON consultas(medico_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_diagnostico ON consultas(diagnostico)')
            
            conn.commit()
    
    def guardar_consulta(self, consulta_data: Dict) -> int:
        """Guarda una nueva consulta y retorna el ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO consultas (
                    medico_id, paciente_nombre, transcripcion,
                    soap_subjetivo, soap_objetivo, soap_analisis, soap_plan,
                    diagnostico, tratamiento, cumplimiento_estado,
                    audio_duracion, notas_adicionales
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                consulta_data.get('medico_id', 'default'),
                consulta_data.get('paciente_nombre', ''),
                consulta_data.get('transcripcion', ''),
                consulta_data.get('soap_subjetivo', ''),
                consulta_data.get('soap_objetivo', ''),
                consulta_data.get('soap_analisis', ''),
                consulta_data.get('soap_plan', ''),
                consulta_data.get('diagnostico', ''),
                consulta_data.get('tratamiento', ''),
                consulta_data.get('cumplimiento_estado', ''),
                consulta_data.get('audio_duracion', 0),
                consulta_data.get('notas_adicionales', '')
            ))
            return cursor.lastrowid
    
    def obtener_consultas(self, medico_id: str = 'default', limite: int = 50) -> List[Dict]:
        """Obtiene las consultas más recientes de un médico"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM consultas 
                WHERE medico_id = ? 
                ORDER BY fecha_consulta DESC 
                LIMIT ?
            ''', (medico_id, limite))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def obtener_consulta(self, consulta_id: int) -> Optional[Dict]:
        """Obtiene una consulta específica por ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM consultas WHERE id = ?', (consulta_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def actualizar_consulta(self, consulta_id: int, datos: Dict) -> bool:
        """Actualiza una consulta existente"""
        campos = []
        valores = []
        
        for campo, valor in datos.items():
            if campo in ['soap_subjetivo', 'soap_objetivo', 'soap_analisis', 'soap_plan', 
                        'diagnostico', 'tratamiento', 'notas_adicionales', 'paciente_nombre']:
                campos.append(f"{campo} = ?")
                valores.append(valor)
        
        if not campos:
            return False
        
        campos.append("updated_at = CURRENT_TIMESTAMP")
        valores.append(consulta_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f'''
                UPDATE consultas 
                SET {', '.join(campos)}
                WHERE id = ?
            ''', valores)
            return cursor.rowcount > 0
    
    def buscar_consultas(self, termino: str, medico_id: str = 'default') -> List[Dict]:
        """Busca consultas por término en transcripción, diagnóstico o notas SOAP"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM consultas 
                WHERE medico_id = ? AND (
                    transcripcion LIKE ? OR 
                    diagnostico LIKE ? OR 
                    soap_subjetivo LIKE ? OR 
                    soap_analisis LIKE ?
                )
                ORDER BY fecha_consulta DESC
            ''', (medico_id, f'%{termino}%', f'%{termino}%', f'%{termino}%', f'%{termino}%'))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def obtener_estadisticas(self, medico_id: str = 'default') -> Dict:
        """Obtiene estadísticas básicas de consultas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_consultas,
                    COUNT(DISTINCT DATE(fecha_consulta)) as dias_activos,
                    AVG(audio_duracion) as duracion_promedio
                FROM consultas 
                WHERE medico_id = ?
            ''', (medico_id,))
            
            stats = cursor.fetchone()
            
            # Top 5 diagnósticos más frecuentes
            cursor = conn.execute('''
                SELECT diagnostico, COUNT(*) as frecuencia
                FROM consultas 
                WHERE medico_id = ? AND diagnostico != ''
                GROUP BY diagnostico
                ORDER BY frecuencia DESC
                LIMIT 5
            ''', (medico_id,))
            
            top_diagnosticos = cursor.fetchall()
            
            return {
                'total_consultas': stats[0] or 0,
                'dias_activos': stats[1] or 0,
                'duracion_promedio': round(stats[2] or 0, 1),
                'top_diagnosticos': [{'diagnostico': d[0], 'frecuencia': d[1]} for d in top_diagnosticos]
            }
    
    def eliminar_consulta(self, consulta_id: int) -> bool:
        """Elimina una consulta (usar con cuidado)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('DELETE FROM consultas WHERE id = ?', (consulta_id,))
            return cursor.rowcount > 0