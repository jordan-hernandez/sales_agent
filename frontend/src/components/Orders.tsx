import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  CircularProgress,
} from '@mui/material';
import { ordersApi, Order } from '../services/api';

const Orders: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const restaurantId = 1; // For MVP

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const ordersData = await ordersApi.getOrders(restaurantId);
      setOrders(ordersData);
    } catch (error) {
      console.error('Error loading orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewOrder = (order: Order) => {
    setSelectedOrder(order);
    setOpenDialog(true);
  };

  const handleUpdateStatus = async (orderId: number, newStatus: string) => {
    try {
      await ordersApi.updateOrderStatus(orderId, newStatus);
      loadOrders(); // Reload orders
      setOpenDialog(false);
    } catch (error) {
      console.error('Error updating order status:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'warning';
      case 'confirmed': return 'info';
      case 'in_preparation': return 'primary';
      case 'ready': return 'success';
      case 'delivered': return 'success';
      case 'cancelled': return 'error';
      default: return 'default';
    }
  };

  const getPaymentStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'warning';
      case 'paid': return 'success';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

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
        Gestión de Pedidos
      </Typography>

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Cliente</TableCell>
                <TableCell>Productos</TableCell>
                <TableCell>Total</TableCell>
                <TableCell>Estado</TableCell>
                <TableCell>Pago</TableCell>
                <TableCell>Fecha</TableCell>
                <TableCell>Acciones</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {orders.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Typography color="textSecondary">
                      No hay pedidos registrados
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                orders.map((order) => (
                  <TableRow key={order.id}>
                    <TableCell>{order.id}</TableCell>
                    <TableCell>
                      <div>
                        <Typography variant="body2">{order.customer_name}</Typography>
                        <Typography variant="caption" color="textSecondary">
                          {order.customer_phone}
                        </Typography>
                      </div>
                    </TableCell>
                    <TableCell>{order.items.length}</TableCell>
                    <TableCell>${order.total.toLocaleString()}</TableCell>
                    <TableCell>
                      <Chip 
                        label={order.status} 
                        color={getStatusColor(order.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={order.payment_status} 
                        color={getPaymentStatusColor(order.payment_status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {new Date(order.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Button 
                        size="small" 
                        onClick={() => handleViewOrder(order)}
                      >
                        Ver Detalles
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Order Details Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Detalles del Pedido #{selectedOrder?.id}
        </DialogTitle>
        <DialogContent>
          {selectedOrder && (
            <div>
              <Typography variant="h6" gutterBottom>
                Información del Cliente
              </Typography>
              <Typography>Nombre: {selectedOrder.customer_name}</Typography>
              <Typography>Teléfono: {selectedOrder.customer_phone}</Typography>
              {selectedOrder.delivery_address && (
                <Typography>Dirección: {selectedOrder.delivery_address}</Typography>
              )}

              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Productos
              </Typography>
              <List>
                {selectedOrder.items.map((item) => (
                  <ListItem key={item.id}>
                    <ListItemText
                      primary={`${item.product_name} x${item.quantity}`}
                      secondary={`$${item.unit_price.toLocaleString()} c/u = $${(item.quantity * item.unit_price).toLocaleString()}`}
                    />
                  </ListItem>
                ))}
              </List>

              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Resumen
              </Typography>
              <Typography>Subtotal: ${selectedOrder.subtotal.toLocaleString()}</Typography>
              <Typography>Costo de envío: ${selectedOrder.delivery_fee.toLocaleString()}</Typography>
              <Typography variant="h6">Total: ${selectedOrder.total.toLocaleString()}</Typography>

              <Box sx={{ mt: 2 }}>
                <FormControl size="small" sx={{ minWidth: 200 }}>
                  <InputLabel>Estado del Pedido</InputLabel>
                  <Select
                    value={selectedOrder.status}
                    label="Estado del Pedido"
                    onChange={(e) => handleUpdateStatus(selectedOrder.id, e.target.value)}
                  >
                    <MenuItem value="pending">Pendiente</MenuItem>
                    <MenuItem value="confirmed">Confirmado</MenuItem>
                    <MenuItem value="in_preparation">En Preparación</MenuItem>
                    <MenuItem value="ready">Listo</MenuItem>
                    <MenuItem value="delivered">Entregado</MenuItem>
                    <MenuItem value="cancelled">Cancelado</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </div>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cerrar</Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default Orders;