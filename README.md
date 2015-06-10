# SOHOVeT
Gestión de una clínica veterinaria con Odoo

SOHOVet contiene un conjunto de módulos para Odoo (www.odoo.com) que permite la gestión de una clínica veterinaria.

Versión inicial:
 - Compras a proveedores.
 - Gestión de precios basados en margen sobre el precio final.
 - Exportación e importación de productos en formato xlsx para facilitar la modificación o incorporación de productos en lote.
 - Gestión de propietarios y animales.
 - Módulo de vacunación con posibilidad de definir reglas de vacunación y generar recordatorios de vacunas pendientes.
 - Permite la conexión con el proveedor TextLocal para el envío de SMS con los recordatorios de vacunación.

## Instalación
> **Nota:**

> Se instalarán también los siguientes módulos de python mediante `pip`_:
> - boto: Interfaz en python para Amazon AWS http://docs.pythonboto.org/
> - xlsxwriter: Librería para escribir ficheros XLSX en python. https://xlsxwriter.readthedocs.org/ 

Para empezar a utilizar SOHOVet deberá partir de una instalación de Odoo.


1. Descargar los módulos e instalar las dependencias.

.. code-block:: sh

    $ git clone https://github.com/sohovet/sohovet.git
    $ pip install -r requirements.txt


.. _pip: http://www.pip-installer.org/
