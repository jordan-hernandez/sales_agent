import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Product {
  id: number;
  name: string;
  description: string | null;
  price: number;
  category: string;
  available: boolean;
  image_url: string | null;
}

export interface OrderItem {
  id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  notes: string | null;
}

export interface Order {
  id: number;
  customer_name: string;
  customer_phone: string;
  delivery_address: string | null;
  subtotal: number;
  delivery_fee: number;
  total: number;
  status: string;
  payment_status: string;
  created_at: string;
  items: OrderItem[];
}

export const menuApi = {
  getMenu: (restaurantId: number): Promise<Product[]> =>
    api.get(`/menu/restaurant/${restaurantId}/menu`).then(res => res.data),
  
  getCategories: (restaurantId: number): Promise<{categories: string[]}> =>
    api.get(`/menu/restaurant/${restaurantId}/menu/categories`).then(res => res.data),
  
  createSampleMenu: (restaurantId: number): Promise<{message: string}> =>
    api.post(`/menu/restaurant/${restaurantId}/menu/sample`).then(res => res.data),
};

export const ordersApi = {
  getOrders: (restaurantId: number): Promise<Order[]> =>
    api.get(`/orders/restaurant/${restaurantId}/orders`).then(res => res.data),
  
  getOrder: (orderId: number): Promise<Order> =>
    api.get(`/orders/orders/${orderId}`).then(res => res.data),
  
  updateOrderStatus: (orderId: number, status: string): Promise<{message: string}> =>
    api.patch(`/orders/orders/${orderId}/status`, { status }).then(res => res.data),
};

export const setupApi = {
  setupDemo: (): Promise<{message: string, restaurant_id: number, restaurant_name: string}> =>
    api.post('/setup').then(res => res.data),
};

export default api;