================================================================================
   LA PROVINCIAL - RESTAURANTE & FAST FOOD
   Sistema de Gestión Comercial, Control Policial PNP y Consolidado Financiero
   GUÍA PASO A PASO PARA COPIAR EN USB E INSTALAR EN OTRA LAPTOP / PC
================================================================================

¡IMPORTANTE! El programa ya está empaquetado de forma 100% portable y autónoma.
NO necesitas instalar Python ni descargar nada de internet en la otra laptop.
Todos los datos actuales (efectivos PNP, meses, ventas, tickets y egresos) viajan
incluidos dentro del archivo "control_policial.db".

--------------------------------------------------------------------------------
OPCIÓN A: ¿QUÉ COPIAR AL USB? (Elige la forma que prefieras)
--------------------------------------------------------------------------------

1. FORMA RÁPIDA Y LIGERA (Recomendada - Solo ~178 MB, copia en pocos segundos):
   - Entra a la carpeta:  dist\LaProvincial
   - Copia únicamente la carpeta "LaProvincial" a tu memoria USB.
   - (Dentro de esa carpeta ya van incluidos el programa "LaProvincial.exe",
     tu base de datos actual "control_policial.db" y el instalador automático
     "INSTALAR_EN_LAPTOP.bat").

2. FORMA COMPLETA (Con código fuente incluido - ~1.1 GB):
   - Copia toda la carpeta del proyecto ("Apuyectos 2026") a tu memoria USB.
   - Nota: Demorará unos minutos más en copiarse al USB porque incluye el
     entorno completo de desarrollo (.python).

--------------------------------------------------------------------------------
PASO A PASO: CÓMO INSTALAR EN LA OTRA LAPTOP
--------------------------------------------------------------------------------

PASO 1: Conecta el USB en la laptop donde deseas instalar el programa.

PASO 2: Abre la carpeta que copiaste en el USB y haz DOBLE CLIC en el archivo:
        -->  INSTALAR_EN_LAPTOP.bat

PASO 3: Se abrirá una ventana de instalación con dos opciones:
        - Presiona la tecla [1] y luego [ENTER] (Opción Recomendada).
        - El instalador hará todo automáticamente:
          a) Copiará el programa y tu base de datos al disco de la laptop
             (en la carpeta C:\LaProvincial).
          b) Creará el icono "LA PROVINCIAL" directamente en el Escritorio
             de la laptop.
          c) Creará la carpeta de respaldos automáticos (C:\LaProvincial\backups_db).

PASO 4: Al finalizar te preguntará si deseas abrir el programa. Presiona [ENTER]
        y el sistema se abrirá inmediatamente.
        ¡Ya puedes retirar tu memoria USB de forma segura!

--------------------------------------------------------------------------------
INSTALACIÓN MANUAL (Alternativa sin usar el instalador automático)
--------------------------------------------------------------------------------

Si prefieres hacerlo manualmente sin ejecutar "INSTALAR_EN_LAPTOP.bat":

1. Copia la carpeta "LaProvincial" (que está dentro de "dist\LaProvincial")
   desde tu USB hacia el Escritorio o al Disco C:\ de la nueva laptop.
2. Entra a esa carpeta en la laptop, busca el archivo "LaProvincial.exe"
   (el que tiene el tipo "Aplicación").
3. Haz clic derecho sobre "LaProvincial.exe" -> "Enviar a" ->
   "Escritorio (crear acceso directo)".
4. Abre el programa haciendo doble clic en el nuevo acceso directo del Escritorio.

--------------------------------------------------------------------------------
SOLUCIÓN A AVISOS COMUNES EN WINDOWS 10 / 11
--------------------------------------------------------------------------------

1. Aviso "Windows protegió su PC" (Microsoft Defender SmartScreen):
   - Como es un programa propio de uso interno, la primera vez que lo abras
     Windows puede mostrar una ventana azul de confirmación.
   - Solución: Haz clic en el texto subrayado "Más información" y luego en el
     botón "Ejecutar de todas formas". No volverá a preguntarte.

2. ¿Dónde se guardan mis datos y copias de seguridad en la nueva laptop?
   - Base de datos principal:
     C:\LaProvincial\control_policial.db  (o junto a LaProvincial.exe)
   - Copias de seguridad (generadas desde el menú "Copias de Seguridad"):
     C:\LaProvincial\backups_db\

3. ¿Cómo llevar mis datos actualizados de una PC a otra en el futuro?
   - Solo debes copiar el archivo "control_policial.db" (o generar un backup
     desde el módulo "Copias de Seguridad" dentro del programa) y reemplazarlo
     en la otra PC.
================================================================================
