import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Box,
} from '@mui/material';
import {
  TrendingUp,
  ShoppingCart,
  Restaurant,
  AccessTime,
} from '@mui/icons-material';
import { ordersApi, setupApi } from '../services/api';
import { Order } from '../services/api';

const Dashboard: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [setupStatus, setSetupStatus] = useState<string>('');
  const [restaurantId, setRestaurantId] = useState<number>(1);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const ordersData = await ordersApi.getOrders(restaurantId);
      setOrders(ordersData);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSetupDemo = async () => {
    try {
      const result = await setupApi.setupDemo();
      setSetupStatus(result.message);
      setRestaurantId(result.restaurant_id);
      setTimeout(() => {
        loadDashboardData();
      }, 1000);
    } catch (error) {
      console.error('Error setting up demo:', error);
      setSetupStatus('Error al configurar los datos de demostración');
    }
  };

  const getOrderStats = () => {
    const today = new Date().toDateString();
    const todayOrders = orders.filter(order => 
      new Date(order.created_at).toDateString() === today
    );
    
    const totalSales = orders.reduce((sum, order) => sum + order.total, 0);
    const pendingOrders = orders.filter(order => order.status === 'pending').length;
    
    return {
      totalOrders: orders.length,
      todayOrders: todayOrders.length,
      totalSales,
      pendingOrders,
    };
  };

  const stats = getOrderStats();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Dashboard - Agente de Ventas
      </Typography>
      
      {setupStatus && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {setupStatus}
        </Alert>
      )}

      <Box sx={{ mb: 3 }}>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={handleSetupDemo}
          sx={{ mr: 2 }}
        >
          Configurar Datos de Demostración
        </Button>
        <Button 
          variant="outlined" 
          onClick={loadDashboardData}
        >
          Actualizar Datos
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Stats Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <ShoppingCart color="primary" sx={{ mr: 2 }} />
                <div>
                  <Typography color="textSecondary" gutterBottom>
                    Total Pedidos
                  </Typography>
                  <Typography variant="h5">
                    {stats.totalOrders}
                  </Typography>
                </div>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <AccessTime color="secondary" sx={{ mr: 2 }} />
                <div>
                  <Typography color="textSecondary" gutterBottom>
                    Pedidos Hoy
                  </Typography>
                  <Typography variant="h5">
                    {stats.todayOrders}
                  </Typography>
                </div>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrendingUp color="success" sx={{ mr: 2 }} />
                <div>
                  <Typography color="textSecondary" gutterBottom>
                    Ventas Totales
                  </Typography>
                  <Typography variant="h5">
                    ${stats.totalSales.toLocaleString()}
                  </Typography>
                </div>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Restaurant color="warning" sx={{ mr: 2 }} />
                <div>
                  <Typography color="textSecondary" gutterBottom>
                    Pendientes
                  </Typography>
                  <Typography variant="h5">
                    {stats.pendingOrders}
                  </Typography>
                </div>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Orders */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Pedidos Recientes
            </Typography>
            {orders.length === 0 ? (
              <Typography color="textSecondary">
                No hay pedidos registrados. Usa el bot de Telegram para crear pedidos de prueba.
              </Typography>
            ) : (
              <div>
                {orders.slice(0, 5).map((order) => (
                  <Box key={order.id} sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Grid container spacing={2} alignItems="center">
                      <Grid item xs={12} sm={3}>
                        <Typography variant="subtitle1">
                          Pedido #{order.id}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {order.customer_name}
                        </Typography>
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <Typography variant="body2">
                          {order.items.length} productos
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Total: ${order.total.toLocaleString()}
                        </Typography>
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <Typography 
                          variant="body2" 
                          color={order.status === 'pending' ? 'warning.main' : 'success.main'}
                        >
                          {order.status}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {order.payment_status}
                        </Typography>
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <Typography variant="body2" color="textSecondary">
                          {new Date(order.created_at).toLocaleDateString()}
                        </Typography>
                      </Grid>
                    </Grid>
                  </Box>
                ))}
              </div>
            )}
          </Paper>
        </Grid>
      </Grid>
    </div>
  );
};

export default Dashboard;