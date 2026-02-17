from collections import defaultdict
from datetime import datetime
from decimal import Decimal

def monthly_sales_by_product(detalle_qs):
    """
    Input: Queryset de DetalleVenta.
    Output: dict -> { producto_id: { (year,month): total_sales_amount } }
    """
    data = defaultdict(lambda: defaultdict(Decimal))
    for d in detalle_qs:
        yr = d.venta.fecha.year
        mo = d.venta.fecha.month
        data[d.producto.id][(yr, mo)] += d.subtotal
    return data

def expected_sales_same_month_last_year(product_month_map, producto_id, target_year, target_month):
    """
    Predict using average of same month across previous years (if available).
    """
    hist = []
    for (yr, mo), val in product_month_map.get(producto_id, {}).items():
        if mo == target_month and yr < target_year:
            hist.append(float(val))
    if not hist:
        
        fallback = []
        for (yr, mo), val in product_month_map.get(producto_id, {}).items():
            if (yr == target_year and mo < target_month) or (yr < target_year):
                fallback.append(float(val))
        if fallback:
            return sum(fallback) / len(fallback)
        return 0.0
    return sum(hist) / len(hist)
