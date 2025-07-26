import React, { useState, useRef } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  Alert,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
} from '@mui/material';
import {
  CloudUpload,
  Schedule,
  Sync,
  Delete,
  Description,
  TableChart,
  PictureAsPdf,
} from '@mui/icons-material';
import api from '../services/api';

interface SyncResult {
  success: boolean;
  message: string;
  stats?: {
    created: number;
    updated: number;
    errors: number;
  };
  error?: string;
}

const InventorySync: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string>('');
  const [messageType, setMessageType] = useState<'success' | 'error'>('success');
  const [schedules, setSchedules] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const restaurantId = 1; // For MVP

  // File upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Schedule state
  const [scheduleTime, setScheduleTime] = useState('09:00');
  const [scheduleType, setScheduleType] = useState('daily');
  const [filePath, setFilePath] = useState('');

  // Google Sheets state
  const [spreadsheetId, setSpreadsheetId] = useState('');
  const [rangeValue, setRangeValue] = useState('A:Z');

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setMessage('');
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) {
      setMessage('Por favor selecciona un archivo');
      setMessageType('error');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setLoading(true);
      const response = await api.post(`/inventory/upload-file/${restaurantId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const result: SyncResult = response.data;
      
      if (result.success) {
        setMessage(`${result.message}. Creados: ${result.stats?.created}, Actualizados: ${result.stats?.updated}, Errores: ${result.stats?.errors}`);
        setMessageType('success');
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      } else {
        setMessage(result.error || 'Error durante la sincronización');
        setMessageType('error');
      }
    } catch (error: any) {
      setMessage(error.response?.data?.detail || 'Error subiendo archivo');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const handleScheduleFileSync = async () => {
    if (!filePath) {
      setMessage('Por favor ingresa la ruta del archivo');
      setMessageType('error');
      return;
    }

    try {
      setLoading(true);
      const response = await api.post('/sync/schedule/file', {
        restaurant_id: restaurantId,
        file_path: filePath,
        schedule_time: scheduleTime,
        schedule_type: scheduleType
      });

      if (response.data.success) {
        setMessage(response.data.message);
        setMessageType('success');
        loadSchedules();
      } else {
        setMessage(response.data.error || 'Error programando sincronización');
        setMessageType('error');
      }
    } catch (error: any) {
      setMessage(error.response?.data?.detail || 'Error programando sincronización');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const loadSchedules = async () => {
    try {
      const response = await api.get(`/sync/schedule/${restaurantId}`);
      const scheduleData = response.data.schedules;
      const scheduleArray = Object.values(scheduleData) as any[];
      setSchedules(scheduleArray);
    } catch (error) {
      console.error('Error loading schedules:', error);
    }
  };

  const handleRemoveSchedule = async (syncType: string) => {
    try {
      const response = await api.delete(`/sync/schedule/${restaurantId}?sync_type=${syncType}`);
      if (response.data.success) {
        setMessage(response.data.message);
        setMessageType('success');
        loadSchedules();
      }
    } catch (error: any) {
      setMessage(error.response?.data?.detail || 'Error eliminando programación');
      setMessageType('error');
    }
  };

  const handleManualSync = async () => {
    try {
      setLoading(true);
      const response = await api.post(`/sync/schedule/${restaurantId}/sync-now`);
      if (response.data.success) {
        setMessage(response.data.message);
        setMessageType('success');
      }
    } catch (error: any) {
      setMessage(error.response?.data?.detail || 'Error ejecutando sincronización manual');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    loadSchedules();
  }, []);

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Sincronización de Inventario
      </Typography>

      {message && (
        <Alert severity={messageType} sx={{ mb: 2 }}>
          {message}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* File Upload Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <CloudUpload sx={{ mr: 1, verticalAlign: 'middle' }} />
                Subir Archivo
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Soporta PDF, Excel (.xlsx, .xls) y CSV
              </Typography>

              <Box sx={{ mt: 2 }}>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  accept=".pdf,.xlsx,.xls,.csv"
                  style={{ display: 'none' }}
                />
                <Button
                  variant="outlined"
                  onClick={() => fileInputRef.current?.click()}
                  sx={{ mb: 2 }}
                  fullWidth
                >
                  Seleccionar Archivo
                </Button>

                {selectedFile && (
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    Archivo seleccionado: {selectedFile.name}
                  </Typography>
                )}

                <Button
                  variant="contained"
                  onClick={handleFileUpload}
                  disabled={!selectedFile || loading}
                  fullWidth
                  startIcon={loading ? <CircularProgress size={20} /> : <CloudUpload />}
                >
                  {loading ? 'Procesando...' : 'Sincronizar Ahora'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Scheduled Sync Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Schedule sx={{ mr: 1, verticalAlign: 'middle' }} />
                Sincronización Programada
              </Typography>

              <Box sx={{ mt: 2 }}>
                <TextField
                  fullWidth
                  label="Ruta del Archivo"
                  value={filePath}
                  onChange={(e) => setFilePath(e.target.value)}
                  placeholder="/path/to/your/menu.xlsx"
                  sx={{ mb: 2 }}
                />

                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Hora"
                      type="time"
                      value={scheduleTime}
                      onChange={(e) => setScheduleTime(e.target.value)}
                      InputLabelProps={{ shrink: true }}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <FormControl fullWidth>
                      <InputLabel>Frecuencia</InputLabel>
                      <Select
                        value={scheduleType}
                        label="Frecuencia"
                        onChange={(e) => setScheduleType(e.target.value)}
                      >
                        <MenuItem value="daily">Diario</MenuItem>
                        <MenuItem value="hourly">Cada Hora</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>

                <Button
                  variant="contained"
                  onClick={handleScheduleFileSync}
                  disabled={loading}
                  fullWidth
                  sx={{ mb: 2 }}
                >
                  Programar Sincronización
                </Button>

                <Button
                  variant="outlined"
                  onClick={handleManualSync}
                  disabled={loading}
                  fullWidth
                  startIcon={<Sync />}
                >
                  Sincronizar Manualmente
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Supported Formats Info */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Formatos Soportados
              </Typography>

              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <PictureAsPdf color="error" />
                  </ListItemIcon>
                  <ListItemText
                    primary="PDF"
                    secondary="Formato: 'Producto - Descripción $Precio'"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <TableChart color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Excel (.xlsx, .xls)"
                    secondary="Columnas: nombre, precio, categoria, descripcion"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Description color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="CSV"
                    secondary="Mismas columnas que Excel"
                  />
                </ListItem>
              </List>

              <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                <strong>Columnas requeridas:</strong> nombre, precio<br />
                <strong>Columnas opcionales:</strong> categoria, descripcion, disponible
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Current Schedules */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Sincronizaciones Programadas
              </Typography>

              {schedules.length === 0 ? (
                <Typography color="textSecondary">
                  No hay sincronizaciones programadas
                </Typography>
              ) : (
                <List>
                  {schedules.map((schedule, index) => (
                    <ListItem key={index}>
                      <ListItemText
                        primary={`${schedule.sync_type === 'file' ? 'Archivo' : 'Google Sheets'}: ${schedule.schedule_type}`}
                        secondary={`Hora: ${schedule.schedule_time} - Última sync: ${schedule.last_sync || 'Nunca'}`}
                      />
                      <IconButton
                        edge="end"
                        onClick={() => handleRemoveSchedule(schedule.sync_type)}
                        color="error"
                      >
                        <Delete />
                      </IconButton>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Google Sheets Section */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Google Sheets (Próximamente)
              </Typography>
              <Typography variant="body2" color="textSecondary">
                La integración con Google Sheets estará disponible en la siguiente versión.
                Necesitarás configurar las credenciales de la API de Google Sheets.
              </Typography>
              
              <Box sx={{ mt: 2 }}>
                <TextField
                  fullWidth
                  label="ID de la Hoja de Cálculo"
                  value={spreadsheetId}
                  onChange={(e) => setSpreadsheetId(e.target.value)}
                  placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
                  disabled
                  sx={{ mb: 2 }}
                />
                <TextField
                  fullWidth
                  label="Rango"
                  value={rangeValue}
                  onChange={(e) => setRangeValue(e.target.value)}
                  placeholder="A:Z"
                  disabled
                  sx={{ mb: 2 }}
                />
                <Button variant="outlined" disabled fullWidth>
                  Sincronizar desde Google Sheets (Próximamente)
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </div>
  );
};

export default InventorySync;