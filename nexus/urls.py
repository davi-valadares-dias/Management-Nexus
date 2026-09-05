from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views  # <-- Importe as views de autenticação
from estoque import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Rotas de Login e Logout nativas do Django
    path('login/', auth_views.LoginView.as_view(template_name='estoque/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Suas rotas protegidas
    path('', views.dashboard, name='dashboard'),
    path('movimentacao/', views.nova_movimentacao, name='nova_movimentacao'),
    path('produto/novo/', views.novo_produto, name='novo_produto'),
    path('historico/', views.historico_movimentacoes, name='historico'),
    path('relatorio/excel/', views.exportar_relatorio_csv, name='exportar_csv'),
    path('produto/editar/<int:id>/', views.editar_produto, name='editar_produto'),
    path('produto/excluir/<int:id>/', views.excluir_produto, name='excluir_produto'),
    path('relatorio/pdf/', views.exportar_relatorio_pdf, name='exportar_pdf'),
    path('categoria/nova/', views.nova_categoria, name='nova_categoria'),
    path('fornecedor/novo/', views.novo_fornecedor, name='novo_fornecedor'),
    path('relatorio/pdf/', views.exportar_relatorio_pdf, name='exportar_pdf'),
    path('relatorio/graficos/', views.relatorio_graficos, name='relatorio_graficos'), # <-- NOVA LINHA
]