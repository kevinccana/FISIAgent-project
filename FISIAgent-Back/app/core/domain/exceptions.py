"""Excepciones del dominio"""


class DomainException(Exception):
    """Base para todas las excepciones de dominio"""
    pass


class RiskClassificationError(DomainException):
    """Error al clasificar riesgo"""
    pass


class LLMServiceError(DomainException):
    """Error al comunicarse con el servicio LLM"""
    pass


class VideoSelectionError(DomainException):
    """Error al seleccionar video de apoyo"""
    pass
