# LA PROVINCIAL - RESTAURANTE & FAST FOOD
### Sistema de Gestión Comercial, Control Policial PNP, Egresos y Consolidado Financiero

Aplicación de escritorio profesional nativa para Windows construida con **Python 3.12**, **PySide6 (Qt6)**, **SQLite** y motor de reportes multiformato (**openpyxl**, **ReportLab**). Diseñada para administrar dos locales comerciales independientes (**LA PROVINCIAL RESTAURANTE** y **LA PROVINCIAL FAST FOOD**) junto con un **CONSOLIDADO GENERAL** unificado en tiempo real.

---

## 🚀 Características y Módulos Principales

### 1. Gestión Multi-Local y Consolidado General
- **Local 1:** `LA PROVINCIAL RESTAURANTE`
- **Local 2:** `LA PROVINCIAL FAST FOOD`
- **Consolidado:** Vista combinada que totaliza ventas, tickets policiales, egresos y saldos de ambos locales sin mezclar la persistencia individual en base de datos.
- Selector rápido en la barra superior: `[🏢 RESTAURANTE | 🍔 FAST FOOD | 🌐 CONSOLIDADO GENERAL]`.

### 2. Base de Datos Maestra de Policías (BD)
- Identificador único estricto: **Código del Policía** (ej. `APF-25`, `AIN-01`, `DEP-01`).
- Registro único: un efectivo registrado en BD se propaga automáticamente a todos los meses de operación sin reescribir nombres ni áreas.
- Desactivación lógica (`ACTIVO` / `INACTIVO`): conserva intacto el historial de tickets consumidos en períodos pasados.

### 3. Matriz Mensual de Tickets por Policía
- Control visual por días (1 al 31) con checkbox / marcas `X`.
- Suma automática e inmutable del total de tickets por efectivo.
- Soporte para migración y persistencia batch en menos de 1 segundo.

### 4. Calendario Policial Diario
- Registro diario discriminando: `Para Unidad` y `Local`.
- **Fórmula Matemática Estricta:**  
  $$\text{Total Tickets} = \text{Para Unidad} + \text{Local}$$
- Los **Vales** se controlan en su propio módulo y nunca se suman a los tickets de consumo.

### 5. Consumo Local Fast Food
- Módulo específico para `LA PROVINCIAL FAST FOOD`.
- Registro de `Tickets consumidos en local` + `Vales consumidos en local` $\rightarrow$ `Total Consumido`.

### 6. Control de Vales y Pagos
- Registro de `Vales Entregados` vs `Vales Canjeados` $\rightarrow$ $\text{Saldo} = \text{Entregados} - \text{Canjeados}$ con alerta visual si es negativo.
- Control de pagos de tickets: `Tickets Pagados`, `Tickets Debidos` y estados automáticos (`PAGADO`, `PENDIENTE`, `PARCIAL`).

### 7. Ventas Diarias y Lógica Financiera
- Entradas del software de ventas: `Efectivo` y `Yape`.
- Cálculos automáticos:
  - $\text{Venta Sin Tickets} = \text{Efectivo} + \text{Yape}$
  - $\text{Venta Tickets Policiales} = \text{Cantidad Tickets} \times \text{Precio Unitario}$ (por defecto S/ 12.00 con preservación histórica por mes)
  - $\text{Venta Total} = \text{Venta Sin Tickets} + \text{Venta Tickets Policiales}$ (configurable)

### 8. Gestión Completa de Egresos
- **Compras / Insumos:** Registro por proveedor, categoría (carnes, verduras, abarrotes), cantidad, precio unitario y medio de pago.
- **Gastos Operativos:** Servicios (luz, agua, gas, alquiler, transporte, mantenimiento).
- **Pagos al Personal:** Sueldos, adelantos, horas extras, bonos por trabajador y cargo.
- Total de Egresos:
  $$\text{Total Egresos} = \text{Compras} + \text{Gastos} + \text{Pagos Personal}$$

### 9. Calendario Financiero y Saldo Diario
- Resumen día por día: `Venta Total` vs `Total Egresos` $\rightarrow$ $\text{Saldo del Día} = \text{Venta Total} - \text{Total Egresos}$.
- Semáforo de rentabilidad (verde positivo, rojo negativo).

### 10. Reportes y Exportación Multiformato
- **Reportes Mensuales y Diarios:** En **Excel (.xlsx)** y **PDF (.pdf)** oficial.
- **Reporte Anual de 12 Meses:** Comparativa mes a mes de ingresos, egresos y utilidad neta.
- **Exportación CSV (.csv)** para auditoría externa.

### 11. Copias de Seguridad y Auditoría
- Generación y restauración de copias de seguridad SQLite con verificación de integridad (`PRAGMA quick_check`).
- Copia de protección automática pre-restauración.
- Bitácora de auditoría con fecha, usuario, acción y local asociado.

---

## 📂 Estructura del Código

```text
Apuyectos 2026/
├── main.py                       # Punto de entrada de la aplicación
├── requirements.txt              # Librerías necesarias (PySide6, openpyxl, reportlab, etc.)
├── build.bat                     # Compilador de ejecutable EXE
├── run.bat                       # Script de ejecución directa en Windows
├── control_policial.db           # Base de datos SQLite normalizada
├── database/                     # Gestión de conexión y esquema SQL DDL
├── models/                       # Clases de datos (Policía, Mes, Ticket, Venta, Compra, Gasto, etc.)
├── repositories/                 # Capa de persistencia SQL con soporte multi-local
├── services/                     # Lógica de negocio, cálculos financieros y auditoría
├── views/                        # Interfaz gráfica moderna en PySide6
│   ├── main_window.py            # Ventana principal con barra superior y selector de local
│   ├── dashboard_view.py         # Dashboard con métricas y gráficos
│   ├── policias_view.py          # Módulo de Base de Datos de Policías
│   ├── calendario_view.py        # Calendario Policial diario
│   ├── tickets_policia_view.py   # Matriz de tickets por policía
│   ├── vales_view.py             # Control de vales
│   ├── pagos_view.py             # Pagos y deudas
│   ├── ventas_view.py            # Ventas diarias
│   ├── egresos_view.py           # Compras, gastos operativos y personal
│   ├── calendario_financiero_view.py # Saldo del día y balance diario
│   ├── fast_food_view.py         # Consumos de Fast Food
│   ├── observaciones_view.py     # Bitácora de incidencias
│   ├── reportes_view.py          # Generador de reportes Excel/PDF
│   ├── configuracion_view.py     # Parámetros y auditoría
│   └── backup_view.py            # Copias de seguridad
├── reports/                      # Motores de exportación Excel y PDF
├── imports/                      # Importador de archivos Excel existentes
└── tests/                        # 37 pruebas automatizadas (pytest)
```

---

## 🧪 Pruebas Automatizadas (37/37 PASSED)

Para ejecutar la suite completa de pruebas unitarias, de integración y de especificación:

```powershell
.\.python\python.exe -m pytest tests -v
```

### Pruebas verificadas:
1. `test_1_crear_policia_aparece_en_meses_futuros`
2. `test_2_no_duplicar_codigo_policia`
3. `test_3_historial_policia_invariable_al_modificar_datos`
4. `test_4_inactivar_policia_desaparece_de_nuevos_meses_pero_conserva_historial`
5. `test_5_reactivar_policia`
6. `test_6_total_tickets_unidad_mas_local`
7. `test_7_vales_no_se_suman_a_tickets`
8. `test_8_calculo_venta_sin_tickets_efectivo_mas_yape`
9. `test_9_calculo_venta_tickets_policiales_por_precio_historico`
10. `test_10_calculo_venta_total_segun_configuracion`
11. `test_11_consumo_local_fast_food`
12. `test_12_separacion_total_dos_locales`
13. `test_13_consolidado_ambos_locales`
14. `test_14_compras_por_local_y_consolidado`
15. `test_15_gastos_por_local_y_consolidado`
16. `test_16_pagos_personal_por_local_y_consolidado`
17. `test_17_total_egresos`
18. `test_18_saldo_del_dia`
19. `test_19_control_vales_saldo_y_alertas`
20. `test_20_control_pagos_tickets_estados`
21. `test_21_reporte_mensual_excel`
22. `test_22_reporte_mensual_pdf`
23. `test_23_reporte_anual_12_meses`
24. `test_24_copias_seguridad`
25. `test_25_rendimiento_carga_100_policias_sub_segundo`
... y las pruebas de importación, backup y exportación PDF/Excel.

---

## 📦 Ejecución y Compilación

### Ejecutar la aplicación en modo desarrollo:
```bat
run.bat
```

### Compilar a ejecutable autónomo para Windows (.EXE):
```bat
build.bat
```
El archivo final generado se encuentra listo para distribución en:
```text
dist\LaProvincial\LaProvincial.exe
```
