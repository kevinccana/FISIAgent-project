from fastapi import APIRouter
from app.models.chat import ChatRequest, ChatResponse
from app.M04_GestorRecursos import ResourceManager

router = APIRouter(prefix="/chat", tags=["Chat"])
resource_manager = ResourceManager()
palabras_crisis = [
    "suicidio",
    "morir",
    "morirme",
    "matarme",
    "no quiero vivir",
    "acabar con todo"
]

palabras_recursos = [
    "ayuda",
    "necesito ayuda",
    "donde puedo llamar",
    "dónde puedo llamar",
    "psicologo",
    "psicólogo",
    "centro de salud",
    "recursos",
    "linea de ayuda",
    "línea de ayuda",
    "sjl",
    "san juan",
    "lurigancho",
    "comas",
    "cono norte",
    "lima centro",
    "centro de lima",
    "cercado"
]

def contiene_palabra_clave(texto: str, palabras_clave: list[str]) -> bool:
    """
    Verifica si el mensaje del usuario contiene alguna palabra clave.
    """
    return any(palabra in texto for palabra in palabras_clave)

@router.post("/")
def chat(req: ChatRequest):
    texto = req.message.lower()

    # 1. Primero: detección de crisis
    if contiene_palabra_clave(texto, palabras_crisis):
        return ChatResponse(
            response=(
                "Lo que sientes es muy importante. Por favor llama ya a la "
                "Línea 113 opción 5 (salud mental) o acude al centro de salud "
                "más cercano. No estás solo/a."
            ),
            emotion="crisis",
            crisis=True,
            resources=[
                {
                    "tipo": "linea_ayuda",
                    "nombre": "Línea 113 Salud Mental",
                    "direccion": "Atención telefónica nacional",
                    "telefono": "113 opción 5",
                    "horario": "24/7"
                }
            ]
        )

    # 2. Segundo: activación de recursos por palabra clave
    if contiene_palabra_clave(texto, palabras_recursos):
        recursos = resource_manager.buscar_por_distrito(texto)

        if recursos:
            return ChatResponse(
                response="Aquí tienes algunos recursos de ayuda disponibles según tu mensaje.",
                emotion="ayuda",
                crisis=False,
                resources=recursos
            )

        return ChatResponse(
            response=(
                "Aquí tienes una opción gratuita disponible desde cualquier lugar del país: "
                "Línea 113 - Salud Mental. Marca 113 y pide la opción 5. "
                "También puedes acudir al centro de salud más cercano."
            ),
            emotion="ayuda",
            crisis=False,
            resources=[
                {
                    "tipo": "linea_ayuda",
                    "nombre": "Línea 113 Salud Mental",
                    "direccion": "Atención telefónica nacional",
                    "telefono": "113 opción 5",
                    "horario": "24/7"
                }
            ]
        )

    # 3. Tercero: respuestas emocionales normales
    if "triste" in texto:
        return ChatResponse(
            response="Lamento que te sientas así. ¿Quieres contarme más?",
            emotion="tristeza",
            crisis=False
        )

    # 4. Respuesta por defecto
    return ChatResponse(
        response="Estoy aquí para escucharte.",
        emotion="neutral",
        crisis=False
    )