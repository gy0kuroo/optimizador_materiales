"""Formularios CutLess por dominio."""

from .optimization import TableroForm, PiezaForm
from .materials import MaterialForm
from .clients import ClienteForm
from .budgets import PresupuestoForm
from .projects import ProyectoForm
from .plantillas import PlantillaForm

__all__ = [
    'TableroForm', 'PiezaForm', 'MaterialForm', 'ClienteForm',
    'PresupuestoForm', 'ProyectoForm', 'PlantillaForm',
]
