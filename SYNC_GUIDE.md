# Guía de Sincronización de Inventario

El sistema de ventas ahora incluye sincronización automática de inventario desde múltiples fuentes: PDFs, archivos Excel, CSV y Google Sheets.

## Características Implementadas

### ✅ **Sincronización desde Archivos**
- **PDF**: Extrae menús con formato "Producto - Descripción $Precio"
- **Excel (.xlsx, .xls)**: Lee hojas de cálculo con columnas estructuradas
- **CSV**: Procesa archivos CSV con la misma estructura que Excel
- **Validación automática**: Verifica y limpia los datos antes de importar

### ✅ **Sincronización Programada**
- **Horarios flexibles**: Sincronización diaria u horaria
- **Múltiples fuentes**: Soporta archivos locales y Google Sheets
- **Ejecución automática**: El scheduler ejecuta las tareas en segundo plano
- **Sincronización manual**: Opción para ejecutar sync inmediatamente

### ✅ **Google Sheets Integration**
- **API de Google Sheets**: Conecta directamente con hojas de cálculo
- **Credenciales seguras**: Usa archivos JSON de autenticación
- **Rangos personalizables**: Especifica qué parte de la hoja leer

## Estructura de Datos Requerida

### Columnas Obligatorias
- **nombre**: Nombre del producto
- **precio**: Precio en pesos colombianos (número)

### Columnas Opcionales
- **categoria**: Categoría del producto (entradas, platos principales, bebidas, postres)
- **descripcion**: Descripción detallada del producto
- **disponible**: Si el producto está disponible (true/false, sí/no, 1/0)

### Ejemplo de Estructura

```csv
nombre,descripcion,precio,categoria,disponible
Empanadas de Pollo,Deliciosas empanadas caseras,8000,entradas,true
Bandeja Paisa,Plato tradicional completo,28000,platos principales,true
Limonada de Coco,Bebida refrescante,8000,bebidas,true
```

## Cómo Usar la Sincronización

### 1. Sincronización Manual (Dashboard Web)

1. Ve a la sección **"Sincronización"** en el dashboard
2. **Subir Archivo**:
   - Haz clic en "Seleccionar Archivo"
   - Elige tu PDF, Excel o CSV
   - Haz clic en "Sincronizar Ahora"
3. **Resultado**: El sistema te mostrará cuántos productos se crearon, actualizaron o tuvieron errores

### 2. Sincronización Programada

1. En la sección **"Sincronización Programada"**:
   - Ingresa la ruta completa del archivo
   - Selecciona la hora (formato 24h: "09:30")
   - Elige la frecuencia (diario u horario)
   - Haz clic en "Programar Sincronización"

2. **Ejemplo de configuración**:
   - Archivo: `/home/restaurant/menu.xlsx`
   - Hora: `09:00` (9:00 AM)
   - Frecuencia: `daily`

### 3. API Endpoints para Sincronización

#### Subir y Sincronizar Archivo
```bash
POST /api/v1/inventory/upload-file/{restaurant_id}
Content-Type: multipart/form-data

# Respuesta
{
  "success": true,
  "message": "Sincronización completada",
  "stats": {
    "created": 5,
    "updated": 3,
    "errors": 0
  }
}
```

#### Programar Sincronización de Archivo
```bash
POST /api/v1/sync/schedule/file
{
  "restaurant_id": 1,
  "file_path": "/path/to/menu.xlsx",
  "schedule_time": "09:00",
  "schedule_type": "daily"
}
```

#### Sincronización Manual Inmediata
```bash
POST /api/v1/sync/schedule/{restaurant_id}/sync-now?sync_type=all
```

#### Ver Sincronizaciones Programadas
```bash
GET /api/v1/sync/schedule/{restaurant_id}
```

#### Eliminar Programación
```bash
DELETE /api/v1/sync/schedule/{restaurant_id}?sync_type=file
```

## Formatos de Archivo Soportados

### PDF
El sistema busca patrones como:
- `Empanadas de Pollo - Deliciosas empanadas caseras $8000`
- `Bandeja Paisa $28000`

### Excel/CSV
Acepta variaciones en nombres de columnas:
- **Nombre**: name, product, producto, item, nombre
- **Precio**: price, cost, costo, valor, precio
- **Categoría**: category, categoría, tipo, categoria
- **Descripción**: description, descripción, desc, descripcion
- **Disponible**: available, disponible, activo, stock

## Google Sheets (Configuración Avanzada)

### 1. Configurar API de Google Sheets

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la "Google Sheets API"
4. Crea credenciales de "Service Account"
5. Descarga el archivo JSON de credenciales

### 2. Preparar la Hoja de Cálculo

1. Crea una hoja con la estructura requerida
2. Comparte la hoja con el email del service account
3. Copia el ID de la hoja (de la URL)

### 3. Usar la Sincronización

```bash
POST /api/v1/inventory/sync-google-sheets
Content-Type: multipart/form-data

{
  "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "range_name": "A:Z",
  "restaurant_id": 1
}
# + archivo credentials.json
```

## Casos de Uso Comunes

### 1. Restaurante con Menú en Excel
- **Situación**: El chef mantiene el menú en Excel
- **Solución**: Configurar sync diario a las 9:00 AM
- **Archivo**: `/shared/restaurant/menu_daily.xlsx`

### 2. Cadena con Google Sheets Central
- **Situación**: Oficina central mantiene menús en Google Sheets
- **Solución**: Sync cada hora desde la hoja compartida
- **Beneficio**: Actualizaciones inmediatas en todos los bots

### 3. Proveedor con Catálogo PDF
- **Situación**: Proveedor envía catálogo PDF actualizado
- **Solución**: Subida manual cuando llegue el nuevo catálogo
- **Proceso**: Guardar PDF → Subir desde dashboard → Sincronizar

## Manejo de Errores y Validaciones

### Validaciones Automáticas
- **Precio válido**: Debe ser número positivo
- **Nombre requerido**: No puede estar vacío
- **Longitud máxima**: Nombres hasta 200 caracteres
- **Categoría**: Normaliza a minúsculas

### Productos Duplicados
- **Criterio**: Mismo nombre (búsqueda parcial)
- **Acción**: Actualiza precio, descripción y disponibilidad
- **Preserva**: ID original y relaciones con pedidos

### Logs y Reportes
- **Estadísticas**: Creados, actualizados, errores
- **Logs del sistema**: Registra todas las operaciones
- **Notificaciones**: Éxito/error de sincronizaciones programadas

## Consideraciones de Rendimiento

### Archivos Grandes
- **Límite recomendado**: 1000 productos por archivo
- **Procesamiento**: Por lotes para evitar timeouts
- **Memoria**: Optimizado para archivos hasta 10MB

### Frecuencia de Sync
- **Diario**: Recomendado para la mayoría de casos
- **Horario**: Solo para operaciones con cambios frecuentes
- **Manual**: Para actualizaciones esporádicas

### Base de Datos
- **Transacciones**: Cambios atómicos (todo o nada)
- **Índices**: Optimizado para búsquedas por nombre
- **Backup**: Los datos originales se preservan

## Troubleshooting

### Error: "Formato no soportado"
- **Causa**: Extensión de archivo no válida
- **Solución**: Usar .pdf, .xlsx, .xls, o .csv

### Error: "No se pudieron extraer datos"
- **Causa**: Archivo vacío o formato incorrecto
- **Solución**: Verificar que el archivo tenga datos y estructura correcta

### Error: "Los datos no tienen el formato correcto"
- **Causa**: Faltan columnas obligatorias (nombre, precio)
- **Solución**: Agregar columnas faltantes o verificar nombres

### Sync Programado No Ejecuta
- **Causa**: Archivo no existe o sin permisos
- **Solución**: Verificar ruta completa y permisos de lectura

### Google Sheets "Credenciales no encontradas"
- **Causa**: Archivo de credenciales incorrecto
- **Solución**: Regenerar credenciales de service account

## Monitoreo y Mantenimiento

### Dashboard de Sincronización
- **Estado del scheduler**: Running/Stopped
- **Últimas sincronizaciones**: Timestamp y resultados
- **Programaciones activas**: Lista de tareas programadas

### Logs del Sistema
- **Ubicación**: Logs de la aplicación FastAPI
- **Nivel**: INFO para éxitos, ERROR para fallos
- **Formato**: Timestamp, restaurant_id, tipo, resultado

### Backup de Configuraciones
- **Programaciones**: Se almacenan en memoria (temporal)
- **Recomendación**: Documentar configuraciones importantes
- **Restauración**: Reconfigurar después de reiniciar

## Próximas Mejoras

### Planificadas
- [ ] Persistencia de configuraciones en base de datos
- [ ] Notificaciones por email/WhatsApp de sync fallidos
- [ ] Interface web para cargar credenciales de Google
- [ ] Versionado de menús (historial de cambios)
- [ ] Sincronización bidireccional (exportar cambios)

### Integraciones Futuras
- [ ] Dropbox/OneDrive para archivos en la nube
- [ ] APIs de sistemas POS (Toast, Square, etc.)
- [ ] Webhooks para notificaciones en tiempo real
- [ ] Machine learning para categorización automática