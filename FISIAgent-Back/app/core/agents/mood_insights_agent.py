"""
Agente de Análisis de Bienestar Emocional.

Funcionalidad 2: Agente especializado en generar un análisis narrativo
elaborado del estado de ánimo del estudiante usando IA, a partir de sus
estadísticas, su evolución mensual y las notas que dejó en cada registro.

Es un endpoint aparte y explícito (no se llama automáticamente al cargar el
Dashboard) para no gastar cupo de Gemini en cada visita a la página -- mismo
criterio que las sugerencias de organización del Planificador (Funcionalidad 3).
"""
import logging
from typing import List
from app.core.domain.agent import Agent, AgentRole, AgentTask, AgentResult
from app.core.domain.models import Message
from app.core.domain.mood_models import MoodEntry, MoodStatistics, MonthlyMoodSummary

logger = logging.getLogger(__name__)


class MoodInsightsAgent(Agent):
    """
    Agente especializado en analizar el historial emocional del estudiante
    y generar un diagnóstico elaborado, recomendaciones y recursos.
    """

    SYSTEM_INSTRUCTION = """
Eres un asistente de bienestar emocional para estudiantes universitarios.
Analizas su historial de estado de ánimo (registros diarios con notas) para
darles un panorama honesto, empático y útil de cómo han estado.

PRINCIPIOS:
- No eres un psicólogo real ni das diagnósticos médicos.
- Sé empático pero directo: identifica patrones reales, no generes texto vacío
  ni repitas los números que ya se te dieron.
- Si detectas señales preocupantes (varios días muy malos seguidos, notas que
  mencionan agobio o crisis), dalo a entender con delicadeza y prioriza sugerir
  ayuda profesional (Oficina de Bienestar Estudiantil, Línea 113).

TONO: Cálido, honesto, sin ser alarmista ni condescendiente.
"""

    def __init__(self, llm_service):
        super().__init__(AgentRole.MOOD_ANALYST)
        self.llm_service = llm_service

    def can_handle(self, task: AgentTask) -> bool:
        return task.agent_role == AgentRole.MOOD_ANALYST

    async def execute(self, task: AgentTask) -> AgentResult:
        try:
            return await self._elaborate_insights(task.input_data)
        except Exception as e:
            logger.error(f"Error en MoodInsightsAgent: {e}")
            return AgentResult(agent_role=self.role, success=False, data=None, error_message=str(e))

    async def _call_llm(self, prompt: str) -> str:
        """Helper centralizado para llamar al LLM con un prompt de texto plano."""
        return await self.llm_service.generate_response(
            history=[Message(role="user", text=prompt)],
            system_instruction=""
        )

    async def _elaborate_insights(self, data: dict) -> AgentResult:
        stats: MoodStatistics = data["statistics"]
        history: List[MonthlyMoodSummary] = data.get("monthly_history", [])
        entries: List[MoodEntry] = data.get("entries", [])

        prompt = f"""
{self.SYSTEM_INSTRUCTION}

ESTADÍSTICAS DEL PERÍODO ({stats.period_start.strftime('%d/%m/%Y')} - {stats.period_end.strftime('%d/%m/%Y')}):
- Total de registros: {stats.total_entries}
- Promedio de ánimo: {stats.avg_mood:.1f}/3.0 (0=muy bien, 3=muy mal)
- Tendencia: {stats.mood_trend}
- Estado más frecuente: {stats.most_common_mood.label}

DISTRIBUCIÓN:
"""
        for level, count in stats.mood_distribution.items():
            prompt += f"  - {level.label}: {count} días\n"

        if len(history) >= 2:
            prompt += "\nEVOLUCIÓN MENSUAL (promedio por mes, valores bajos = mejor):\n"
            for h in history:
                prompt += f"  - {h.month_label}: {h.avg_mood:.1f} ({h.entry_count} registros)\n"

        notes = [e for e in entries if e.note]
        if notes:
            prompt += "\nÚLTIMOS REGISTROS CON NOTAS (más reciente primero):\n"
            for e in notes[:15]:
                prompt += f"  - {e.timestamp.strftime('%d/%m')}: {e.mood.label} — \"{e.note}\"\n"

        prompt += """

TAREA:
Analiza este historial y proporciona una respuesta elaborada, no genérica ni superficial:

1. Un diagnóstico desarrollado (3-4 oraciones): identifica patrones concretos
   (ej. relación entre lo que dicen las notas y los días malos, si el estrés
   parece puntual o sostenido, si hay mejoría o deterioro real). Usa las notas
   del estudiante como evidencia, no solo repitas los números.
2. 3-5 recomendaciones específicas y desarrolladas (2-3 oraciones cada una):
   qué hacer, por qué ayuda en su caso concreto, y cómo aplicarlo hoy mismo.
3. 2-4 recursos o técnicas reales y conocidas que pueda investigar por su
   cuenta en internet (nombres de técnicas/metodologías/tipos de apps que
   existen de verdad, ej. "técnica de respiración 4-7-8", "mindfulness para
   estudiantes", "apps de meditación guiada tipo Insight Timer"). NO inventes
   URLs ni enlaces específicos -- da el nombre/término exacto para buscar.

FORMATO DE RESPUESTA (sigue este formato exacto):
DIAGNOSTICO: [tu análisis desarrollado]
RECOMENDACION_1: [primera recomendación elaborada]
RECOMENDACION_2: [segunda recomendación elaborada]
RECOMENDACION_3: [tercera recomendación elaborada]
RECOMENDACION_4: [cuarta recomendación opcional]
RECOMENDACION_5: [quinta recomendación opcional]
RECURSO_1: [nombre de técnica/metodología/tipo de app para buscar]
RECURSO_2: [nombre de técnica/metodología/tipo de app para buscar]
RECURSO_3: [nombre de técnica/metodología/tipo de app para buscar opcional]
RECURSO_4: [nombre de técnica/metodología/tipo de app para buscar opcional]
"""

        response = await self._call_llm(prompt)

        lines = response.strip().split('\n')
        diagnosis = ""
        recommendations = []
        resources = []

        for line in lines:
            line = line.strip()
            if line.startswith("DIAGNOSTICO:"):
                diagnosis = line.replace("DIAGNOSTICO:", "").strip()
            elif line.startswith("RECOMENDACION_"):
                rec = line.split(":", 1)[1].strip() if ":" in line else line
                if rec:
                    recommendations.append(rec)
            elif line.startswith("RECURSO_"):
                res = line.split(":", 1)[1].strip() if ":" in line else line
                if res:
                    resources.append(res)

        result = {
            "diagnosis": diagnosis or "No se pudo generar un análisis en este momento.",
            "recommendations": recommendations,
            "resources": resources,
        }

        return AgentResult(agent_role=self.role, success=True, data=result)
