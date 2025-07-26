import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Chip,
  Button,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import { menuApi, Product } from '../services/api';

const Menu: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string>('');
  const restaurantId = 1; // For MVP

  useEffect(() => {
    loadMenuData();
  }, []);

  const loadMenuData = async () => {
    try {
      setLoading(true);
      const [productsData, categoriesData] = await Promise.all([
        menuApi.getMenu(restaurantId),
        menuApi.getCategories(restaurantId)
      ]);
      setProducts(productsData);
      setCategories(categoriesData.categories);
    } catch (error) {
      console.error('Error loading menu data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSampleMenu = async () => {
    try {
      const result = await menuApi.createSampleMenu(restaurantId);
      setMessage(result.message);
      setTimeout(() => {
        loadMenuData();
        setMessage('');
      }, 2000);
    } catch (error) {
      console.error('Error creating sample menu:', error);
      setMessage('Error al crear el menú de muestra');
    }
  };

  const filteredProducts = selectedCategory === 'all' 
    ? products 
    : products.filter(product => product.category === selectedCategory);

  const formatPrice = (price: number) => {
    return `$${price.toLocaleString()}`;
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
        Gestión del Menú
      </Typography>

      {message && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {message}
        </Alert>
      )}

      <Box sx={{ mb: 3 }}>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={handleCreateSampleMenu}
          sx={{ mr: 2 }}
        >
          Crear Menú de Muestra
        </Button>
        <Button 
          variant="outlined" 
          onClick={loadMenuData}
        >
          Actualizar Menú
        </Button>
      </Box>

      {/* Category Filter */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Filtrar por Categoría
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip
            label="Todas"
            onClick={() => setSelectedCategory('all')}
            color={selectedCategory === 'all' ? 'primary' : 'default'}
            variant={selectedCategory === 'all' ? 'filled' : 'outlined'}
          />
          {categories.map((category) => (
            <Chip
              key={category}
              label={category.charAt(0).toUpperCase() + category.slice(1)}
              onClick={() => setSelectedCategory(category)}
              color={selectedCategory === category ? 'primary' : 'default'}
              variant={selectedCategory === category ? 'filled' : 'outlined'}
            />
          ))}
        </Box>
      </Box>

      {/* Products Grid */}
      {filteredProducts.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="textSecondary">
            No hay productos en el menú. Crea un menú de muestra para comenzar.
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {filteredProducts.map((product) => (
            <Grid item xs={12} sm={6} md={4} key={product.id}>
              <Card>
                {product.image_url && (
                  <CardMedia
                    component="img"
                    height="200"
                    image={product.image_url}
                    alt={product.name}
                  />
                )}
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {product.name}
                  </Typography>
                  {product.description && (
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      {product.description}
                    </Typography>
                  )}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
                    <Typography variant="h6" color="primary">
                      {formatPrice(product.price)}
                    </Typography>
                    <Chip
                      label={product.available ? 'Disponible' : 'No Disponible'}
                      color={product.available ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                  <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                    Categoría: {product.category}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </div>
  );
};

export default Menu;