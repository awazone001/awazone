from django.urls import path
from . import views

#admin manage aiboearn urls
urlpatterns = [
    path('admin/launch-sector',views.add_sector,name='add_sector'),
    path('admin/update-sector/<sector_id>/',views.update_sector,name='update_sector'),
    path('admin/views-assets',views.view_asset,name='view_assets'),
    path('admin/launch-asset',views.add_asset,name='add_asset'),
    path('admin/update-asset/<asset_id>/',views.update_asset,name='update_asset'),
    path('dashboard',views.aiboearn_dashboard,name='aiboearn_dashboard'),
    path('sales/<purchase_id>/',views.aiboearn_asset_sales,name='aiboearn_sales'),
    path('sell/<purchase_id>/',views.aiboearn_sell_asset,name='aiboearn_sell'),
    path('sectors/',views.user_view_sector,name='user_view_sector'),
    path('assets/',views.user_view_asset,name='user_view_asset'),
    path('<aibo_sector>/assets/',views.user_view_sector_asset,name='user_view_sector_asset'),
    path('purchase-asset/',views.aiboearn_asset_purchase,name='aiboearn_asset_purchase'),  
    path('ajax_load_assets/',views.ajax_load_assets,name='ajax_load_assets'),
    path('monthly-licence-purchase/',views.purchase_monthly_license,name='purchase_monthly_license'),
    path('monthly-licence-purchase/complete',views.monthly_yearly_license_complete,name='purchase_monthly_license_complete'),
    path('yearly-licence-purchase/',views.purchase_yearly_license,name='purchase_yearly_license'),
    path('yearly-licence-purchase/complete',views.purchase_yearly_license_complete,name='purchase_yearly_license_complete'),
]