"""
Agente de Planificación Inteligente.

Funcionalidad 3: Agente especializado en priorización de tareas
y sugerencias de planificación usando IA.
"""

import logging
from typing import List
from app.core.domain.agent import Agent, AgentRole, AgentTask, AgentResult
from app.core.domain.models import Message
from app.core.domain.task_models import Task, TaskSuggestion, TaskPriority, DailySchedule
from app.ports.outbound.llm_service import LLMServicePort
from datetime import date

logger = logging.getLogger(__name__)


class PlannerAgent(Agent):
    """
    Agente especializado en planificación inteligente de tareas.

    Funcionalidades:
    - Sugerir prioridades basadas en contexto
    - Analizar carga de trabajo
    - Recomendar reorganización de tareas
    - Detectar sobrecarga y sugerir delegación/aplazamiento
    """

    SYSTEM_INSTRUCTION = """
Eres un asistente inteligente de planificación para estudiantes universitarios.
Tu objetivo es ayudarles a gestionar sus tareas académicas y personales de manera efectiva.

RESPONSABILIDADES:
1. Analizar la carga de trabajo del estudiante
2. Sugerir prioridades realistas basadas en fechas límite y complejidad
3. Detectar sobrecarga y recomendar estrategias
4. Dar consejos prácticos de productividad

PRINCIPIOS:
- Sé empático: Entiende que los estudiantes tienen límites
- Sé realista: No sobrecargues al estudiante
- Sé específico: Da consejos accionables
- Considera bienestar: Si hay muchas tareas urgentes, sugiere pausas

TONO: Amigable, motivador y práctico.
"""

    def __init__(self, llm_service: LLMServicePort):
        """
        Inicializa el agente.

        Args:
            llm_service: Servicio de LLM (Gemini)
        """
        super().__init__(AgentRole.PLANNER)
        self.llm_service = llm_service

    def can_handle(self, task: AgentTask) -> bool:
        """Verifica si este agente puede manejar la tarea."""
        return task.agent_role == AgentRole.PLANNER

    async def execute(self, task: AgentTask) -> AgentResult:
        """
        Ejecuta la tarea de planificación.

        Args:
            task: Tarea del agente (debe contener "action" y datos relevantes)

        Returns:
            Resultado con sugerencias de planificación
        """
        try:
            action = task.input_data.get("action")

            if action == "suggest_priority":
                return await self._suggest_task_priority(task.input_data)
            elif action == "analyze_schedule":
                return await self._analyze_daily_schedule(task.input_data)
            elif action == "suggest_organization":
                return await self._suggest_task_organization(task.input_data)
            else:
                return AgentResult(
                    agent_role=self.role,
                    success=False,
                    data=None,
                    error_message=f"Acción desconocida: {action}"
                )

        except Exception as e:
            logger.error(f"Error en PlannerAgent: {e}")
            return AgentResult(
                agent_role=self.role,
                success=False,
                data=None,
                error_message=str(e)
            )

    async def _call_llm(self, prompt: str) -> str:
        """
        Helper centralizado para llamar al LLM, adaptando el prompt de texto
        plano de este agente a la firma real de LLMServicePort
        (history: List[Message], system_instruction: str).
        """
        return await self.llm_service.generate_response(
            history=[Message(role="user", text=prompt)],
            system_instruction=""
        )

    async def _suggest_task_priority(self, data: dict) -> AgentResult:
        """
        Sugiere la prioridad de una nueva tarea usando IA.

        Args:
            data: Dict con "task" (Task) y "existing_tasks" (List[Task])

        Returns:
            AgentResult con TaskSuggestion
        """
        new_task: Task = data["task"]
        existing_tasks: List[Task] = data.get("existing_tasks", [])

        # Construir contexto
        context = self._build_task_context(new_task, existing_tasks)

        prompt = f"""
{self.SYSTEM_INSTRUCTION}

NUEVA TAREA A PRIORIZAR:
- Título: {new_task.title}
- Descripción: {new_task.description}
- Fecha límite: {new_task.due_date.strftime('%d/%m/%Y %H:%M')}
- Categoría: {new_task.category}
- Horas estimadas: {new_task.estimated_hours}

CONTEXTO DEL ESTUDIANTE:
{context}

NIVELES DE PRIORIDAD:
- URGENT (0): Urgente e importante - debe hacerse inmediatamente
- HIGH (1): Alta prioridad - hacerse pronto
- MEDIUM (2): Prioridad media - puede esperar algunos días
- LOW (3): Baja prioridad - no es urgente

TAREA:
1. Analiza la nueva tarea en el contexto de las tareas existentes
2. Sugiere un nivel de prioridad (0, 1, 2, o 3)
3. Explica tu razonamiento en 2-3 oraciones
4. Da 2-3 consejos prácticos para completarla

FORMATO DE RESPUESTA (IMPORTANTE - debe ser exactamente este formato):
PRIORIDAD: [número del 0 al 3]
RAZONAMIENTO: [tu explicación]
CONSEJO_1: [primer consejo]
CONSEJO_2: [segundo consejo]
CONSEJO_3: [tercer consejo opcional]
"""

        # Llamar a LLM
        response = await self._call_llm(prompt)

        # Parsear respuesta
        suggestion = self._parse_priority_response(response, new_task)

        return AgentResult(agent_role=self.role, success=True, data=suggestion)

    async def _analyze_daily_schedule(self, data: dict) -> AgentResult:
        """
        Analiza la carga de trabajo de un día y da recomendaciones.

        Args:
            data: Dict con "target_date" (date) y "tasks" (List[Task])

        Returns:
            AgentResult con DailySchedule
        """
        target_date: date = data["target_date"]
        tasks: List[Task] = data["tasks"]

        total_hours = sum(task.estimated_hours for task in tasks)
        is_feasible = total_hours <= 8.0  # 8 horas es un día de trabajo razonable

        prompt = f"""
{self.SYSTEM_INSTRUCTION}

ANÁLISIS DE CARGA DIARIA: {target_date.strftime('%d/%m/%Y')}

TAREAS DEL DÍA ({len(tasks)} tareas, {total_hours:.1f} horas estimadas):
"""

        for i, task in enumerate(tasks, 1):
            prompt += f"\n{i}. {task.title} ({task.priority.emoji} {task.priority.label})"
            prompt += f" - {task.estimated_hours}h"
            if task.is_overdue:
                prompt += " ⚠️ VENCIDA"

        prompt += f"""

¿ES FACTIBLE? {'SÍ' if is_feasible else 'NO - SOBRECARGA'}

TAREA:
Analiza la carga del día y da 3-5 recomendaciones específicas.
Si hay sobrecarga, sugiere qué tareas posponer o dividir.
Si hay horas libres, sugiere tiempo para descanso o estudio adicional.

FORMATO DE RESPUESTA:
RECOMENDACION_1: [primera recomendación]
RECOMENDACION_2: [segunda recomendación]
RECOMENDACION_3: [tercera recomendación]
RECOMENDACION_4: [cuarta recomendación opcional]
RECOMENDACION_5: [quinta recomendación opcional]
"""

        response = await self._call_llm(prompt)

        recommendations = self._parse_recommendations(response)

        schedule = DailySchedule(
            date=target_date,
            tasks=tasks,
            total_estimated_hours=total_hours,
            is_feasible=is_feasible,
            recommendations=recommendations
        )

        return AgentResult(agent_role=self.role, success=True, data=schedule)

    async def _suggest_task_organization(self, data: dict) -> AgentResult:
        """
        Analiza todas las tareas del usuario y sugiere reorganización.

        Args:
            data: Dict con "tasks" (List[Task]) y "user_context" (str)

        Returns:
            AgentResult con dict de sugerencias
        """
        tasks: List[Task] = data["tasks"]
        user_context: str = data.get("user_context", "")

        # Agrupar tareas por estado y prioridad
        pending_urgent = [t for t in tasks if t.status.value in [0, 1] and t.priority.value == 0]
        pending_high = [t for t in tasks if t.status.value in [0, 1] and t.priority.value == 1]
        overdue = [t for t in tasks if t.is_overdue]

        prompt = f"""
{self.SYSTEM_INSTRUCTION}

CONTEXTO DEL ESTUDIANTE:
{user_context}

ANÁLISIS DE TAREAS:
- Total de tareas: {len(tasks)}
- Tareas vencidas: {len(overdue)}
- Tareas urgentes pendientes: {len(pending_urgent)}
- Tareas alta prioridad: {len(pending_high)}

TAREAS CRÍTICAS (vencidas o urgentes):
"""

        critical_tasks = overdue + pending_urgent
        for i, task in enumerate(critical_tasks[:5], 1):  # Mostrar máximo 5
            status_emoji = "⚠️ VENCIDA" if task.is_overdue else "🔴 URGENTE"
            prompt += f"\n{i}. {task.title} - {status_emoji}"
            prompt += f" (vence: {task.due_date.strftime('%d/%m/%Y')})"

        prompt += """

TAREA:
Analiza la situación general del estudiante y proporciona:
1. Un diagnóstico de su gestión de tareas (1-2 oraciones)
2. 3-5 recomendaciones específicas para mejorar su organización
3. Consejos de priorización y bienestar

FORMATO DE RESPUESTA:
DIAGNOSTICO: [tu análisis]
RECOMENDACION_1: [primera recomendación]
RECOMENDACION_2: [segunda recomendación]
RECOMENDACION_3: [tercera recomendación]
RECOMENDACION_4: [cuarta recomendación opcional]
RECOMENDACION_5: [quinta recomendación opcional]
"""

        response = await self._call_llm(prompt)

        # Parsear
        lines = response.strip().split('\n')
        diagnosis = ""
        recommendations = []

        for line in lines:
            if line.startswith("DIAGNOSTICO:"):
                diagnosis = line.replace("DIAGNOSTICO:", "").strip()
            elif line.startswith("RECOMENDACION_"):
                rec = line.split(":", 1)[1].strip() if ":" in line else line
                if rec:
                    recommendations.append(rec)

        result = {
            "diagnosis": diagnosis or "Necesitas mejorar tu organización de tareas.",
            "recommendations": recommendations or ["Prioriza las tareas vencidas primero."],
            "critical_tasks_count": len(critical_tasks),
            "overdue_count": len(overdue)
        }

        return AgentResult(agent_role=self.role, success=True, data=result)

    def _build_task_context(self, new_task: Task, existing_tasks: List[Task]) -> str:
        """Construye contexto sobre las tareas existentes."""
        if not existing_tasks:
            return "El estudiante no tiene otras tareas registradas."

        pending = [t for t in existing_tasks if t.status.value in [0, 1]]
        overdue = [t for t in existing_tasks if t.is_overdue]
        urgent = [t for t in pending if t.priority.value == 0]

        context = f"El estudiante tiene {len(existing_tasks)} tareas totales:\n"
        context += f"- {len(pending)} tareas pendientes\n"
        context += f"- {len(overdue)} tareas vencidas\n"
        context += f"- {len(urgent)} tareas urgentes\n"

        if overdue:
            context += "\nTareas vencidas recientes:\n"
            for task in overdue[:3]:
                context += f"  • {task.title} (vencía: {task.due_date.strftime('%d/%m')})\n"

        return context

    def _parse_priority_response(self, response: str, task: Task) -> TaskSuggestion:
        """Parsea la respuesta del LLM para extraer la sugerencia de prioridad."""
        lines = response.strip().split('\n')

        suggested_priority = TaskPriority.MEDIUM  # Default
        reasoning = ""
        tips = []

        for line in lines:
            line = line.strip()
            if line.startswith("PRIORIDAD:"):
                try:
                    priority_val = int(line.replace("PRIORIDAD:", "").strip())
                    suggested_priority = TaskPriority(priority_val)
                except (ValueError, IndexError):
                    pass
            elif line.startswith("RAZONAMIENTO:"):
                reasoning = line.replace("RAZONAMIENTO:", "").strip()
            elif line.startswith("CONSEJO_"):
                tip = line.split(":", 1)[1].strip() if ":" in line else line
                if tip:
                    tips.append(tip)

        # Fallback si no se parseó bien
        if not reasoning:
            reasoning = "Se recomienda esta prioridad basándose en la fecha límite y el contexto."

        if not tips:
            tips = ["Divide la tarea en pasos más pequeños.", "Dedica tiempo diario a avanzar."]

        return TaskSuggestion(
            task_id=task.id or 0,
            suggested_priority=suggested_priority,
            reasoning=reasoning,
            confidence=0.8,  # Confianza fija por ahora
            tips=tips
        )

    def _parse_recommendations(self, response: str) -> List[str]:
        """Extrae recomendaciones de la respuesta del LLM."""
        lines = response.strip().split('\n')
        recommendations = []

        for line in lines:
            if line.startswith("RECOMENDACION_"):
                rec = line.split(":", 1)[1].strip() if ":" in line else line
                if rec:
                    recommendations.append(rec)

        # Fallback
        if not recommendations:
            recommendations = [
                "Organiza tus tareas por prioridad y fecha límite.",
                "Dedica las primeras horas del día a tareas importantes.",
                "Toma descansos regulares para mantener la concentración."
            ]

        return recommendations